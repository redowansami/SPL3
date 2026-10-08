"""Tests for the PyRIT objective -> MITRE ATLAS mitigation mapping."""

from fastapi.testclient import TestClient

from app.main import app
from app.pyrit_mitigations import (
    PYRIT_MITIGATION_REGISTRY,
    get_objective_mitigation,
)
from app.pyrit_objectives import PYRIT_OBJECTIVES

client = TestClient(app)


def test_every_objective_has_a_mitigation_entry():
    """Fail-fast guard: adding a new objective must come with a mapping."""
    missing = [o.id for o in PYRIT_OBJECTIVES if o.id not in PYRIT_MITIGATION_REGISTRY]
    assert missing == [], f"objectives without a mitigation mapping: {missing}"


def test_unknown_objective_returns_fallback():
    fb = get_objective_mitigation("does-not-exist")
    assert fb.atlas_mitigations  # non-empty
    assert {m.id for m in fb.atlas_mitigations} >= {"AML.M0020", "AML.M0024"}


def test_none_objective_returns_fallback():
    fb = get_objective_mitigation(None)
    assert fb.atlas_mitigations
    assert any(t.id == "AML.T0054" for t in fb.atlas_techniques)


def test_router_returns_mapping_for_known_objective():
    resp = client.get("/api/pyrit/mitigations/system_prompt_leak")
    assert resp.status_code == 200
    data = resp.json()
    assert data["objective_id"] == "system_prompt_leak"
    assert any(t["id"] == "AML.T0054" for t in data["atlas_techniques"])
    assert len(data["atlas_mitigations"]) > 0
    assert all({"id", "name", "description"} <= m.keys() for m in data["atlas_mitigations"])
    assert len(data["strategies"]) > 0


def test_router_falls_back_for_custom_objective():
    resp = client.get("/api/pyrit/mitigations/some_custom_objective")
    assert resp.status_code == 200
    assert len(resp.json()["atlas_mitigations"]) > 0
