"""Tests for the scan-result persistence layer (app/db/repository.py).

Follows the same SQLite in-memory + StaticPool + Base.metadata.create_all
pattern as test_auth.py, with one deviation: save_garak_scan/save_pyrit_scan
open SessionLocal() directly (they run from a background thread, not a
request), so app.dependency_overrides[get_db] has no effect on them — we
monkeypatch app.db.repository.SessionLocal instead.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import get_current_user
from app.db import repository
from app.db.models import ScanRun, User
from app.main import app
from app.schemas.schemas import (
    AttackPathStep,
    FailureItem,
    JobStatus,
    ProbeSummary,
    ScanResponse,
)
from app.schemas.schemas_pyrit import ConversationTurn, PyritScanResponse

_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)


@event.listens_for(_engine, "connect")
def _enable_sqlite_fk_enforcement(dbapi_connection, connection_record):
    # SQLite ignores ON DELETE CASCADE unless foreign key enforcement is turned
    # on per-connection; Postgres (production) enforces it unconditionally.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestingSessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=_engine)


def _override_get_db():
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_user(username: str, email: str) -> int:
    db = _TestingSessionLocal()
    user = User(username=username, email=email, hashed_password="x", is_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user.id


_USER_A_ID = _create_user("history-alice", "history-alice@example.com")
_USER_B_ID = _create_user("history-bob", "history-bob@example.com")


def _override_current_user_a():
    db = _TestingSessionLocal()
    try:
        yield db.get(User, _USER_A_ID)
    finally:
        db.close()


def _override_current_user_b():
    db = _TestingSessionLocal()
    try:
        yield db.get(User, _USER_B_ID)
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
app.dependency_overrides[get_current_user] = _override_current_user_a
client = TestClient(app)

_NOW = datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture(autouse=True)
def _patch_session_local(monkeypatch):
    monkeypatch.setattr(repository, "SessionLocal", _TestingSessionLocal)


@pytest.fixture(autouse=True)
def _clean_db():
    db = _TestingSessionLocal()
    db.query(ScanRun).delete()
    db.commit()
    db.close()
    yield


def _garak_result(**overrides) -> ScanResponse:
    defaults = dict(
        ok=True,
        probe_id="promptinject-hijack",
        garak_probe="promptinject.HijackHateHumans",
        target_url="http://localhost:8000/chat",
        attempts_evaluated=10,
        failure_count=2,
        failures=[
            FailureItem(probe="promptinject.HijackHateHumans", detector="d1", prompt="p1", output="o1", score=1.0),
            FailureItem(probe="promptinject.HijackHateHumans", detector="d1", prompt="p2", output="o2", score=1.0),
        ],
        summary=[ProbeSummary(probe="promptinject.HijackHateHumans", detector="d1", passed=8, total=10)],
        attack_paths=[
            AttackPathStep(
                attempt_seq=1, goal="g1", probe="promptinject.HijackHateHumans", detector="d1",
                prompt_turns=["p1"], output="o1", triggers=["t1"], score=1.0,
            ),
        ],
        nli_filtered_count=1,
        nli_filtered_hits=[
            AttackPathStep(
                attempt_seq=2, goal="g2", probe="promptinject.HijackHateHumans", detector="d1",
                prompt_turns=["p2"], output="o2", triggers=["t2"], score=1.0, nli_verdict="echo",
            ),
        ],
        error=None,
    )
    defaults.update(overrides)
    return ScanResponse(**defaults)


def _pyrit_result(**overrides) -> PyritScanResponse:
    defaults = dict(
        ok=True,
        target_url="http://localhost:8000/chat",
        objective_id="obj-1",
        objective="Get the target to reveal its system prompt",
        outcome="success",
        outcome_reason="Target leaked the secret",
        achieved=True,
        executed_turns=3,
        final_score_rationale="Matched the secret string",
        conversation=[
            ConversationTurn(turn=1, role="attacker", text="turn one"),
            ConversationTurn(turn=2, role="target", text="turn two"),
            ConversationTurn(turn=3, role="attacker", text="turn three"),
        ],
        error=None,
    )
    defaults.update(overrides)
    return PyritScanResponse(**defaults)


def _save_garak(run_id="run-garak-1", status=JobStatus.COMPLETED, result=None, user_id=None):
    return repository.save_garak_scan(
        run_id=run_id,
        status=status,
        target_url="http://localhost:8000/chat",
        probe_id="promptinject-hijack",
        garak_probe="promptinject.HijackHateHumans",
        artifact_dir=f"/scan_runs/{run_id}",
        started_at=_NOW,
        ended_at=_NOW,
        result=result if result is not None else _garak_result(),
        user_id=user_id if user_id is not None else _USER_A_ID,
    )


def _save_pyrit(run_id="run-pyrit-1", status=JobStatus.COMPLETED, result=None, user_id=None):
    return repository.save_pyrit_scan(
        run_id=run_id,
        status=status,
        target_url="http://localhost:8000/chat",
        objective_id="obj-1",
        objective="Get the target to reveal its system prompt",
        artifact_dir=f"/scan_runs/{run_id}",
        started_at=_NOW,
        ended_at=_NOW,
        result=result if result is not None else _pyrit_result(),
        user_id=user_id if user_id is not None else _USER_A_ID,
    )


def test_save_garak_scan_persists_run_and_children_atomically():
    assert _save_garak() is True

    db = _TestingSessionLocal()
    run = db.query(ScanRun).filter_by(run_id="run-garak-1").first()
    assert run is not None
    assert run.engine == "garak"
    assert run.status == "completed"
    assert run.ok is True
    assert len(run.findings) == 2
    assert len(run.probe_summaries) == 1
    assert len(run.attack_path_steps) == 2
    assert sum(1 for s in run.attack_path_steps if s.is_nli_filtered) == 1
    assert sum(1 for s in run.attack_path_steps if not s.is_nli_filtered) == 1
    db.close()


def test_save_pyrit_scan_persists_run_and_turns():
    assert _save_pyrit() is True

    db = _TestingSessionLocal()
    run = db.query(ScanRun).filter_by(run_id="run-pyrit-1").first()
    assert run is not None
    assert run.engine == "pyrit"
    assert run.achieved is True
    assert [t.turn for t in run.conversation_turns] == [1, 2, 3]
    db.close()


def test_save_failed_scan_still_persists_row():
    result = _garak_result(
        ok=False, failures=[], summary=[], attack_paths=[], nli_filtered_hits=[],
        nli_filtered_count=0, error="boom",
    )
    assert _save_garak(run_id="run-garak-failed", status=JobStatus.FAILED, result=result) is True

    db = _TestingSessionLocal()
    run = db.query(ScanRun).filter_by(run_id="run-garak-failed").first()
    assert run is not None
    assert run.status == "failed"
    assert run.ok is False
    assert run.error == "boom"
    assert len(run.findings) == 0
    db.close()


def test_save_cancelled_scan_still_persists_row():
    result = _garak_result(
        ok=False, failures=[], summary=[], attack_paths=[], nli_filtered_hits=[],
        nli_filtered_count=0, error="Scan was cancelled.",
    )
    assert _save_garak(run_id="run-garak-cancelled", status=JobStatus.CANCELLED, result=result) is True

    db = _TestingSessionLocal()
    run = db.query(ScanRun).filter_by(run_id="run-garak-cancelled").first()
    assert run is not None
    assert run.status == "cancelled"
    db.close()


def test_duplicate_run_id_does_not_crash():
    assert _save_garak(run_id="run-garak-dup") is True
    assert _save_garak(run_id="run-garak-dup") is False

    db = _TestingSessionLocal()
    count = db.query(ScanRun).filter_by(run_id="run-garak-dup").count()
    assert count == 1
    db.close()


def test_atomicity_on_failure_leaves_no_partial_rows(monkeypatch):
    from app.db import models as scan_models

    def _boom(*args, **kwargs):
        raise RuntimeError("simulated failure while building child rows")

    monkeypatch.setattr(scan_models.ScanFinding, "__init__", _boom)

    assert _save_garak(run_id="run-garak-atomic") is False

    db = _TestingSessionLocal()
    count = db.query(ScanRun).filter_by(run_id="run-garak-atomic").count()
    assert count == 0
    db.close()


def test_list_scans_endpoint_returns_persisted_runs():
    assert _save_garak(run_id="run-list-1") is True
    assert _save_pyrit(run_id="run-list-2") is True

    resp = client.get("/api/scans")
    assert resp.status_code == 200
    body = resp.json()
    run_ids = {r["run_id"] for r in body["runs"]}
    assert {"run-list-1", "run-list-2"} <= run_ids


def test_get_scan_by_run_id_404_for_unknown():
    resp = client.get("/api/scans/does-not-exist")
    assert resp.status_code == 404


def test_get_scan_by_run_id_returns_persisted_run():
    assert _save_pyrit(run_id="run-detail-1") is True

    resp = client.get("/api/scans/run-detail-1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == "run-detail-1"
    assert body["engine"] == "pyrit"


def test_get_scan_detail_returns_full_garak_shape():
    assert _save_garak(run_id="run-detail-garak") is True

    resp = client.get("/api/scans/run-detail-garak/detail")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == "run-detail-garak"
    assert body["garak_probe"] == "promptinject.HijackHateHumans"
    assert len(body["failures"]) == 2
    assert len(body["summary"]) == 1
    assert len(body["attack_paths"]) == 1
    assert body["attack_paths"][0]["attempt_seq"] == 1
    assert len(body["nli_filtered_hits"]) == 1
    assert body["nli_filtered_hits"][0]["attempt_seq"] == 2


def test_get_scan_detail_returns_full_pyrit_shape():
    assert _save_pyrit(run_id="run-detail-pyrit") is True

    resp = client.get("/api/scans/run-detail-pyrit/detail")
    assert resp.status_code == 200
    body = resp.json()
    assert body["run_id"] == "run-detail-pyrit"
    assert body["achieved"] is True
    assert [t["turn"] for t in body["conversation"]] == [1, 2, 3]


def test_get_scan_detail_404_for_unknown():
    resp = client.get("/api/scans/does-not-exist/detail")
    assert resp.status_code == 404


def test_user_can_only_see_own_scans():
    assert _save_garak(run_id="run-owned-by-a", user_id=_USER_A_ID) is True
    assert _save_garak(run_id="run-owned-by-b", user_id=_USER_B_ID) is True

    resp_a = client.get("/api/scans")
    assert resp_a.status_code == 200
    ids_a = {r["run_id"] for r in resp_a.json()["runs"]}
    assert "run-owned-by-a" in ids_a
    assert "run-owned-by-b" not in ids_a

    app.dependency_overrides[get_current_user] = _override_current_user_b
    try:
        resp_b = client.get("/api/scans")
        assert resp_b.status_code == 200
        ids_b = {r["run_id"] for r in resp_b.json()["runs"]}
        assert "run-owned-by-b" in ids_b
        assert "run-owned-by-a" not in ids_b
    finally:
        app.dependency_overrides[get_current_user] = _override_current_user_a


def test_get_scan_404_for_non_owner():
    assert _save_garak(run_id="run-only-a", user_id=_USER_A_ID) is True

    app.dependency_overrides[get_current_user] = _override_current_user_b
    try:
        resp = client.get("/api/scans/run-only-a")
        assert resp.status_code == 404
        resp_detail = client.get("/api/scans/run-only-a/detail")
        assert resp_detail.status_code == 404
    finally:
        app.dependency_overrides[get_current_user] = _override_current_user_a
