"""In-memory registry that runs a Garak probe as a background subprocess and
tracks its lifecycle so the API can report status and support real cancellation.

Route handlers stay synchronous `def`s (FastAPI runs them in its threadpool);
the actual subprocess is launched via `Popen` and watched by a dedicated
background thread, so `POST /api/scan` can return a run_id immediately instead
of blocking for the whole scan.

Cancellation tree-kills the process (`taskkill /F /T`) rather than just
terminating the direct child: Garak's own probe runner can spawn a
`multiprocessing.Pool` of worker processes for probes/generators that support
parallel attempts, and `Popen.terminate()` on Windows only signals the direct
child, not its descendants.
"""

import logging
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import SCAN_TIMEOUT_SECONDS
from app.db import repository
from app.schemas.schemas import JobStatus, ScanRequest, ScanResponse, ScanStatusResponse
from app.services.garak_runner import build_garak_command, prepare_run_dir
from app.services.hitlog_parser import parse_hitlog
from app.services.nli_verifier import verify_promptinject_hits
from app.services.process_utils import kill_process_tree
from app.services.report_parser import parse_report

logger = logging.getLogger(__name__)

# Probe whose hits get a second NLI-based semantic verification pass on top of
# garak's own string-matching detector (see services/nli_verifier.py).
_NLI_VERIFIED_PROBE = "promptinject.HijackHateHumans"


@dataclass
class ScanJob:
    run_id: str
    process: subprocess.Popen
    probe_id: str
    garak_probe: str
    target_url: str
    report_path: Path
    hitlog_path: Path
    start_time: float
    started_at_wall: datetime
    user_id: int
    status: JobStatus = JobStatus.RUNNING
    result: ScanResponse | None = None
    end_time: float | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


_jobs: dict[str, ScanJob] = {}
_jobs_lock = threading.Lock()


def start_scan_job(scan_request: ScanRequest, probe_id: str, garak_probe: str, user_id: int) -> str:
    run_id, run_dir, generator_config_path, run_config_path, report_prefix = prepare_run_dir(scan_request)
    command = build_garak_command(generator_config_path, run_config_path, garak_probe, report_prefix)
    report_path = Path(f"{report_prefix}.report.jsonl")
    hitlog_path = Path(f"{report_prefix}.hitlog.jsonl")

    process = subprocess.Popen(
        command,
        cwd=run_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )

    job = ScanJob(
        run_id=run_id,
        process=process,
        probe_id=probe_id,
        garak_probe=garak_probe,
        target_url=scan_request.target_url,
        report_path=report_path,
        hitlog_path=hitlog_path,
        start_time=time.monotonic(),
        started_at_wall=datetime.now(timezone.utc).replace(tzinfo=None),
        user_id=user_id,
    )
    with _jobs_lock:
        _jobs[run_id] = job

    threading.Thread(target=_watch_job, args=(job,), daemon=True).start()
    return run_id


def get_job(run_id: str) -> ScanJob | None:
    with _jobs_lock:
        return _jobs.get(run_id)


def cancel_job(run_id: str) -> ScanJob | None:
    job = get_job(run_id)
    if job is None:
        return None

    with job.lock:
        if job.status != JobStatus.RUNNING:
            return job  # already terminal: idempotent no-op
        job.status = JobStatus.CANCELLED

    kill_process_tree(job.process.pid)
    return job


def to_status_response(job: ScanJob) -> ScanStatusResponse:
    with job.lock:
        end = job.end_time if job.end_time is not None else time.monotonic()
        payload = {
            "run_id": job.run_id,
            "status": job.status,
            "elapsed_seconds": round(end - job.start_time, 1),
        }
        if job.result is not None:
            payload.update(job.result.model_dump())
        return ScanStatusResponse(**payload)


def _watch_job(job: ScanJob) -> None:
    try:
        stdout, stderr = job.process.communicate(timeout=SCAN_TIMEOUT_SECONDS)
        returncode = job.process.returncode
        timed_out = False
    except subprocess.TimeoutExpired:
        kill_process_tree(job.process.pid)
        stdout, stderr = job.process.communicate()  # drain buffered output after kill
        returncode = -1
        timed_out = True

    with job.lock:
        if job.status != JobStatus.RUNNING:
            # Cancel endpoint already claimed this job; don't clobber its status.
            if job.result is None:
                job.result = _build_error_response(job, "Scan was cancelled.")
                job.end_time = time.monotonic()
        else:
            job.end_time = time.monotonic()
            if timed_out:
                job.status = JobStatus.TIMED_OUT
                job.result = _build_error_response(
                    job, f"Scan exceeded the {SCAN_TIMEOUT_SECONDS}s timeout limit and was stopped automatically."
                )
            elif returncode == 0:
                failures, summary, attempts_evaluated = parse_report(job.report_path)
                attack_paths = parse_hitlog(job.hitlog_path)

                nli_filtered_hits = []
                if job.garak_probe == _NLI_VERIFIED_PROBE:
                    attack_paths, nli_filtered_hits = verify_promptinject_hits(attack_paths)
                    # AttackPathStep (hitlog) and FailureItem (report) come from two
                    # different garak output files with no shared id; correlate them
                    # by prompt text so a filtered hit's matching failure entry is
                    # dropped in lockstep.
                    filtered_prompts = {
                        "\n".join(step.prompt_turns) for step in nli_filtered_hits
                    }
                    failures = [f for f in failures if f.prompt not in filtered_prompts]
                    verdict_by_prompt = {
                        "\n".join(step.prompt_turns): step.nli_verdict for step in attack_paths
                    }
                    failures = [
                        f.model_copy(update={"nli_verdict": verdict_by_prompt.get(f.prompt)})
                        for f in failures
                    ]

                job.status = JobStatus.COMPLETED
                job.result = ScanResponse(
                    ok=True,
                    probe_id=job.probe_id,
                    garak_probe=job.garak_probe,
                    target_url=job.target_url,
                    attempts_evaluated=attempts_evaluated,
                    failure_count=len(failures),
                    failures=failures,
                    summary=summary,
                    attack_paths=attack_paths,
                    nli_filtered_count=len(nli_filtered_hits),
                    nli_filtered_hits=nli_filtered_hits,
                    error=None,
                )
            else:
                job.status = JobStatus.FAILED
                error_tail = (stderr or stdout or "").strip()[-2000:]
                job.result = _build_error_response(job, error_tail or "Garak run failed with no output.")

        final_status, final_result = job.status, job.result

    ended_at_wall = datetime.now(timezone.utc).replace(tzinfo=None)
    persisted = repository.save_garak_scan(
        run_id=job.run_id,
        status=final_status,
        target_url=job.target_url,
        probe_id=job.probe_id,
        garak_probe=job.garak_probe,
        artifact_dir=str(job.report_path.parent),
        started_at=job.started_at_wall,
        ended_at=ended_at_wall,
        result=final_result,
        user_id=job.user_id,
    )
    if not persisted:
        logger.error("Scan %s finished but was NOT persisted to the database.", job.run_id)


def _build_error_response(job: ScanJob, error: str) -> ScanResponse:
    return ScanResponse(
        ok=False,
        probe_id=job.probe_id,
        garak_probe=job.garak_probe,
        target_url=job.target_url,
        attempts_evaluated=0,
        failure_count=0,
        failures=[],
        summary=[],
        attack_paths=[],
        error=error,
    )
