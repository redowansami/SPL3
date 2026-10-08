"""Persists completed scan results to Postgres, atomically.

Called from the background watcher threads in services/job_manager.py and
services/pyrit/job_manager.py, never from a request-scoped route — hence a
manually opened SessionLocal() rather than Depends(get_db). The two save_*
functions never raise: there is no caller on a background thread to
propagate an exception to, so failures are logged and reported back as a
bool instead. The in-memory job result/status (already finalized before the
call) remain the source of truth for the live status endpoints regardless
of DB outcome.
"""

import logging
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.db.models import (
    ScanAttackPathStep,
    ScanConversationTurn,
    ScanFinding,
    ScanProbeSummary,
    ScanRun,
)
from app.schemas.schemas import JobStatus, ScanResponse
from app.schemas.schemas_pyrit import PyritScanResponse

logger = logging.getLogger(__name__)


def save_garak_scan(
    *,
    run_id: str,
    status: JobStatus,
    target_url: str,
    probe_id: str,
    garak_probe: str,
    artifact_dir: str,
    started_at: datetime,
    ended_at: datetime,
    result: ScanResponse,
    user_id: int,
) -> bool:
    """Persists one garak ScanRun plus its findings/attack-path-steps/summaries
    as a single atomic transaction. Returns True on success, False if
    persistence failed (including on a duplicate run_id)."""

    db = SessionLocal()
    try:
        run = ScanRun(
            run_id=run_id,
            user_id=user_id,
            engine="garak",
            status=status.value,
            target_url=target_url,
            probe_id=probe_id,
            garak_probe=garak_probe,
            ok=result.ok,
            error=result.error,
            attempts_evaluated=result.attempts_evaluated,
            failure_count=result.failure_count,
            nli_filtered_count=result.nli_filtered_count,
            artifact_dir=artifact_dir,
            started_at=started_at,
            ended_at=ended_at,
        )
        run.findings = [
            ScanFinding(
                probe=f.probe,
                detector=f.detector,
                prompt=f.prompt,
                output=f.output,
                score=f.score,
                nli_verdict=f.nli_verdict,
            )
            for f in result.failures
        ]
        run.probe_summaries = [
            ScanProbeSummary(probe=s.probe, detector=s.detector, passed=s.passed, total=s.total)
            for s in result.summary
        ]
        run.attack_path_steps = [
            ScanAttackPathStep(
                attempt_seq=a.attempt_seq,
                goal=a.goal,
                probe=a.probe,
                detector=a.detector,
                prompt_turns=a.prompt_turns,
                output=a.output,
                triggers=a.triggers,
                score=a.score,
                nli_verdict=a.nli_verdict,
                is_nli_filtered=False,
            )
            for a in result.attack_paths
        ] + [
            ScanAttackPathStep(
                attempt_seq=a.attempt_seq,
                goal=a.goal,
                probe=a.probe,
                detector=a.detector,
                prompt_turns=a.prompt_turns,
                output=a.output,
                triggers=a.triggers,
                score=a.score,
                nli_verdict=a.nli_verdict,
                is_nli_filtered=True,
            )
            for a in result.nli_filtered_hits
        ]

        db.add(run)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        logger.warning("Scan run %s already persisted (duplicate run_id); skipping.", run_id)
        return False
    except Exception:
        db.rollback()
        logger.exception("Failed to persist garak scan run %s to the database.", run_id)
        return False
    finally:
        db.close()


def save_pyrit_scan(
    *,
    run_id: str,
    status: JobStatus,
    target_url: str,
    objective_id: str | None,
    objective: str,
    artifact_dir: str,
    started_at: datetime,
    ended_at: datetime,
    result: PyritScanResponse,
    user_id: int,
) -> bool:
    """Persists one PyRIT ScanRun plus its conversation turns as a single
    atomic transaction. Returns True on success, False if persistence
    failed (including on a duplicate run_id)."""

    db = SessionLocal()
    try:
        run = ScanRun(
            run_id=run_id,
            user_id=user_id,
            engine="pyrit",
            status=status.value,
            target_url=target_url,
            objective_id=objective_id,
            objective=objective,
            ok=result.ok,
            error=result.error,
            outcome=result.outcome,
            outcome_reason=result.outcome_reason,
            achieved=result.achieved,
            executed_turns=result.executed_turns,
            final_score_rationale=result.final_score_rationale,
            artifact_dir=artifact_dir,
            started_at=started_at,
            ended_at=ended_at,
        )
        run.conversation_turns = [
            ScanConversationTurn(turn=t.turn, role=t.role, text=t.text) for t in result.conversation
        ]

        db.add(run)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        logger.warning("Scan run %s already persisted (duplicate run_id); skipping.", run_id)
        return False
    except Exception:
        db.rollback()
        logger.exception("Failed to persist pyrit scan run %s to the database.", run_id)
        return False
    finally:
        db.close()


def list_scan_runs(
    db: Session, *, user_id: int, engine: str | None = None, limit: int = 50, offset: int = 0
) -> list[ScanRun]:
    query = db.query(ScanRun).filter(ScanRun.user_id == user_id).order_by(ScanRun.started_at.desc())
    if engine:
        query = query.filter(ScanRun.engine == engine)
    return query.offset(offset).limit(limit).all()


def get_scan_run(db: Session, run_id: str, user_id: int) -> ScanRun | None:
    return db.query(ScanRun).filter(ScanRun.run_id == run_id, ScanRun.user_id == user_id).first()
