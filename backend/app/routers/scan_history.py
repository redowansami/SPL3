"""Read-only access to persisted scan history (backed by the scan_runs table)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.db import repository
from app.db.models import User
from app.schemas.schemas import AttackPathStep, FailureItem, JobStatus, ProbeSummary, ScanStatusResponse
from app.schemas.schemas_db import ScanRunListResponse, ScanRunSummaryOut
from app.schemas.schemas_pyrit import ConversationTurn, PyritScanStatusResponse

router = APIRouter(prefix="/api/scans", tags=["scan-history"])


@router.get("", response_model=ScanRunListResponse)
def list_scans(
    engine: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanRunListResponse:
    runs = repository.list_scan_runs(db, user_id=current_user.id, engine=engine, limit=limit, offset=offset)
    return ScanRunListResponse(
        total_returned=len(runs), runs=[ScanRunSummaryOut.model_validate(r) for r in runs]
    )


@router.get("/{run_id}", response_model=ScanRunSummaryOut)
def get_scan(
    run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ScanRunSummaryOut:
    run = repository.get_scan_run(db, run_id, user_id=current_user.id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No persisted scan run '{run_id}'.")
    return ScanRunSummaryOut.model_validate(run)


@router.get("/{run_id}/detail", response_model=ScanStatusResponse | PyritScanStatusResponse)
def get_scan_detail(
    run_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ScanStatusResponse | PyritScanStatusResponse:
    """Full stored result for one run, shaped exactly like the live-poll status
    responses (ScanStatusResponse / PyritScanStatusResponse) so the frontend can
    reuse its live-result components unmodified for history detail views."""

    run = repository.get_scan_run(db, run_id, user_id=current_user.id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No persisted scan run '{run_id}'.")

    elapsed_seconds = (run.ended_at - run.started_at).total_seconds()

    if run.engine == "garak":
        return ScanStatusResponse(
            run_id=run.run_id,
            status=JobStatus(run.status),
            elapsed_seconds=elapsed_seconds,
            engine=run.engine,
            started_at=run.started_at,
            ended_at=run.ended_at,
            ok=run.ok,
            probe_id=run.probe_id,
            garak_probe=run.garak_probe,
            target_url=run.target_url,
            attempts_evaluated=run.attempts_evaluated,
            failure_count=run.failure_count,
            failures=[
                FailureItem(
                    probe=f.probe, detector=f.detector, prompt=f.prompt,
                    output=f.output, score=f.score, nli_verdict=f.nli_verdict,
                )
                for f in run.findings
            ],
            summary=[
                ProbeSummary(probe=s.probe, detector=s.detector, passed=s.passed, total=s.total)
                for s in run.probe_summaries
            ],
            attack_paths=[
                AttackPathStep(
                    attempt_seq=a.attempt_seq, goal=a.goal, probe=a.probe, detector=a.detector,
                    prompt_turns=a.prompt_turns, output=a.output, triggers=a.triggers,
                    score=a.score, nli_verdict=a.nli_verdict,
                )
                for a in run.attack_path_steps if not a.is_nli_filtered
            ],
            nli_filtered_count=run.nli_filtered_count or 0,
            nli_filtered_hits=[
                AttackPathStep(
                    attempt_seq=a.attempt_seq, goal=a.goal, probe=a.probe, detector=a.detector,
                    prompt_turns=a.prompt_turns, output=a.output, triggers=a.triggers,
                    score=a.score, nli_verdict=a.nli_verdict,
                )
                for a in run.attack_path_steps if a.is_nli_filtered
            ],
            error=run.error,
        )

    return PyritScanStatusResponse(
        run_id=run.run_id,
        status=JobStatus(run.status),
        elapsed_seconds=elapsed_seconds,
        engine=run.engine,
        started_at=run.started_at,
        ended_at=run.ended_at,
        ok=run.ok,
        target_url=run.target_url,
        objective_id=run.objective_id,
        objective=run.objective,
        outcome=run.outcome,
        outcome_reason=run.outcome_reason,
        achieved=run.achieved or False,
        executed_turns=run.executed_turns or 0,
        final_score_rationale=run.final_score_rationale,
        conversation=[
            ConversationTurn(turn=t.turn, role=t.role, text=t.text) for t in run.conversation_turns
        ],
        error=run.error,
    )
