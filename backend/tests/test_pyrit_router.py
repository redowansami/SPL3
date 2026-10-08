"""Router tests for /api/pyrit, with the subprocess launch monkeypatched out."""

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import PYRIT_API_KEY_ENV
from app.main import app
from app.services.pyrit import job_manager

client = TestClient(app)


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv(PYRIT_API_KEY_ENV, "test-key")


@pytest.fixture
def no_subprocess(monkeypatch):
    """Capture the job args instead of actually spawning the PyRIT subprocess."""
    captured = {}

    def fake_start(req, objective_id, objective, success_criteria):
        captured.update(
            objective_id=objective_id, objective=objective, success_criteria=success_criteria
        )
        return "pyrit-test123"

    monkeypatch.setattr(job_manager, "start_pyrit_job", fake_start)
    return captured


def test_list_objectives():
    resp = client.get("/api/pyrit/objectives")
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()]
    assert "system_prompt_leak" in ids


def test_start_scan_with_preset(api_key, no_subprocess):
    resp = client.post(
        "/api/pyrit/scan",
        json={"target_url": "http://127.0.0.1:7000/chat", "objective_id": "system_prompt_leak"},
    )
    assert resp.status_code == 202
    assert resp.json() == {"run_id": "pyrit-test123"}
    # preset objective + criteria were resolved and passed through
    assert "system prompt" in no_subprocess["objective"].lower()
    assert no_subprocess["success_criteria"]


def test_custom_objective_overrides_preset(api_key, no_subprocess):
    resp = client.post(
        "/api/pyrit/scan",
        json={"target_url": "http://t", "objective_id": "system_prompt_leak", "objective": "do X"},
    )
    assert resp.status_code == 202
    assert no_subprocess["objective"] == "do X"


def test_unknown_objective_id_is_400(api_key):
    resp = client.post("/api/pyrit/scan", json={"target_url": "http://t", "objective_id": "nope"})
    assert resp.status_code == 400
    assert "nope" in resp.json()["detail"]


def test_missing_api_key_is_400(monkeypatch, no_subprocess):
    monkeypatch.delenv(PYRIT_API_KEY_ENV, raising=False)
    resp = client.post("/api/pyrit/scan", json={"target_url": "http://t", "objective_id": "system_prompt_leak"})
    assert resp.status_code == 400
    assert PYRIT_API_KEY_ENV in resp.json()["detail"]


def test_no_objective_at_all_is_422(api_key):
    # neither objective_id nor objective -> model validator rejects before the route body
    resp = client.post("/api/pyrit/scan", json={"target_url": "http://t"})
    assert resp.status_code == 422


def test_status_unknown_run_is_404():
    resp = client.get("/api/pyrit/scan/does-not-exist")
    assert resp.status_code == 404
