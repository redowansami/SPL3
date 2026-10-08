"""In-memory registry that runs a PyRIT attack as a background subprocess.

Same lifecycle pattern as the garak `job_manager` (Popen in a new process group,
a watcher thread, communicate-with-timeout, tree-kill on cancel/timeout) but it
drives PyRIT's launcher and parses its result.json. Kept as a separate module so
the two engines never entangle.
"""

import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from backend.app.core.config import PYRIT_SCAN_TIMEOUT_SECONDS
from backend.app.schemas.schemas import JobStatus
from backend.app.schemas.schemas_pyrit import PyritScanRequest, PyritScanResponse, PyritScanStatusResponse
from app.services.pyrit.result_parser import parse_result
from app.services.pyrit.runner import build_command, prepare_run_dir
from app.services.process_utils import kill_process_tree


@dataclass
class PyritJob:
    run_id: str
    process: subprocess.Popen
    target_url: str
    objective_id: str | None
    objective: str
    result_path: Path
    start_time: float
    status: JobStatus = JobStatus.RUNNING
    result: PyritScanResponse | None = None
    end_time: float | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


_jobs: dict[str, PyritJob] = {}
_jobs_lock = threading.Lock()


def start_pyrit_job(
    req: PyritScanRequest, objective_id: str | None, objective: str, success_criteria: str
) -> str:
    run_id, run_dir, run_config_path, result_path = prepare_run_dir(req, objective, success_criteria)
    command = build_command(run_config_path, result_path)

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

    job = PyritJob(
        run_id=run_id,
        process=process,
        target_url=req.target_url,
        objective_id=objective_id,
        objective=objective,
        result_path=result_path,
        start_time=time.monotonic(),
    )
    with _jobs_lock:
        _jobs[run_id] = job

    threading.Thread(target=_watch_job, args=(job,), daemon=True).start()
    return run_id


def get_job(run_id: str) -> PyritJob | None:
    with _jobs_lock:
        return _jobs.get(run_id)


def cancel_job(run_id: str) -> PyritJob | None:
    job = get_job(run_id)
    if job is None:
        return None

    with job.lock:
        if job.status != JobStatus.RUNNING:
            return job  # already terminal: idempotent no-op
        job.status = JobStatus.CANCELLED

    kill_process_tree(job.process.pid)
    return job


def to_status_response(job: PyritJob) -> PyritScanStatusResponse:
    with job.lock:
        end = job.end_time if job.end_time is not None else time.monotonic()
        payload = {
            "run_id": job.run_id,
            "status": job.status,
            "elapsed_seconds": round(end - job.start_time, 1),
        }
        if job.result is not None:
            payload.update(job.result.model_dump())
        return PyritScanStatusResponse(**payload)


def _watch_job(job: PyritJob) -> None:
    try:
        stdout, stderr = job.process.communicate(timeout=PYRIT_SCAN_TIMEOUT_SECONDS)
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
                job.result = _error_response(job, "Scan was cancelled.")
                job.end_time = time.monotonic()
            return

        job.end_time = time.monotonic()
        if timed_out:
            job.status = JobStatus.TIMED_OUT
            job.result = _error_response(
                job, f"Scan exceeded the {PYRIT_SCAN_TIMEOUT_SECONDS}s timeout limit and was stopped automatically."
            )
        elif returncode == 0:
            job.status = JobStatus.COMPLETED
            job.result = parse_result(
                job.result_path,
                target_url=job.target_url,
                objective_id=job.objective_id,
                objective=job.objective,
            )
        else:
            job.status = JobStatus.FAILED
            error_tail = (stderr or stdout or "").strip()[-2000:]
            job.result = _error_response(job, error_tail or "PyRIT run failed with no output.")


def _error_response(job: PyritJob, error: str) -> PyritScanResponse:
    return PyritScanResponse(
        ok=False,
        target_url=job.target_url,
        objective_id=job.objective_id,
        objective=job.objective,
        error=error,
    )
