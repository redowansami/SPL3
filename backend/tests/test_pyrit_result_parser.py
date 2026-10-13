"""Tests for mapping the launcher's result.json onto a PyritScanResponse."""

import json

from app.services.pyrit.result_parser import parse_result

_META = {"target_url": "http://t", "objective_id": "system_prompt_leak", "objective": "leak it"}


def _write(tmp_path, data):
    path = tmp_path / "result.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_parse_success(tmp_path):
    path = _write(
        tmp_path,
        {
            "ok": True,
            "objective": "leak it",
            "outcome": "success",
            "outcome_reason": "disclosed the password",
            "achieved": True,
            "executed_turns": 3,
            "final_score_rationale": "the reply contained hunter2",
            "conversation": [
                {"turn": 1, "role": "attacker", "text": "hi"},
                {"turn": 1, "role": "target", "text": "the password is hunter2"},
            ],
        },
    )
    resp = parse_result(path, **_META)
    assert resp.ok and resp.achieved
    assert resp.outcome == "success"
    assert resp.executed_turns == 3
    assert len(resp.conversation) == 2
    assert resp.conversation[1].role == "target"


def test_parse_failure_outcome(tmp_path):
    path = _write(
        tmp_path,
        {"ok": True, "objective": "leak it", "outcome": "failure", "achieved": False,
         "executed_turns": 5, "conversation": []},
    )
    resp = parse_result(path, **_META)
    assert resp.ok and not resp.achieved
    assert resp.outcome == "failure"


def test_parse_launcher_error(tmp_path):
    path = _write(tmp_path, {"ok": False, "objective": "leak it", "error": "boom traceback"})
    resp = parse_result(path, **_META)
    assert not resp.ok
    assert resp.error == "boom traceback"


def test_parse_missing_file(tmp_path):
    resp = parse_result(tmp_path / "nope.json", **_META)
    assert not resp.ok
    assert "no result file" in resp.error
