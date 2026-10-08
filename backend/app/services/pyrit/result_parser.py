"""Turns the launcher's result.json into a PyritScanResponse."""

import json
from pathlib import Path

from backend.app.schemas.schemas_pyrit import ConversationTurn, PyritScanResponse


def parse_result(
    result_path: Path, *, target_url: str, objective_id: str | None, objective: str
) -> PyritScanResponse:
    if not result_path.exists():
        return PyritScanResponse(
            ok=False,
            target_url=target_url,
            objective_id=objective_id,
            objective=objective,
            error="PyRIT run produced no result file.",
        )

    data = json.loads(result_path.read_text(encoding="utf-8"))

    if not data.get("ok"):
        return PyritScanResponse(
            ok=False,
            target_url=target_url,
            objective_id=objective_id,
            objective=data.get("objective") or objective,
            error=data.get("error") or "PyRIT run failed.",
        )

    conversation = [ConversationTurn(**turn) for turn in data.get("conversation", [])]
    return PyritScanResponse(
        ok=True,
        target_url=target_url,
        objective_id=objective_id,
        objective=data.get("objective") or objective,
        outcome=data.get("outcome"),
        outcome_reason=data.get("outcome_reason"),
        achieved=bool(data.get("achieved")),
        executed_turns=data.get("executed_turns", 0),
        final_score_rationale=data.get("final_score_rationale"),
        conversation=conversation,
    )
