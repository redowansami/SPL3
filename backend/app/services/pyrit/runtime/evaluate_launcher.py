"""Entry point run as a subprocess to score a manually-driven "Custom Attack"
conversation against a user-supplied objective.

    python evaluate_launcher.py <run_config.json> <result.json>

Unlike `launcher.py` (which runs a full PyRIT RedTeamingAttack), this only calls
PyRIT's self-ask true/false scorer on a transcript the user already produced by
hand. Reads the run config, scores it, and writes a result.json the parent
process (app.routers.custom_attack) turns into a CustomEvaluateResponse. On any
failure it writes an error result.json AND exits non-zero so the caller can
report the stderr tail.

Invoked by file path (not `-m`) so it only needs `pyrit` on sys.path — not FastAPI.
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

# backend/ on sys.path so `import app.services.pyrit.runtime...` resolves when run by path.
_BACKEND_ROOT = Path(__file__).resolve().parents[4]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


def _transcript(conversation: list[dict]) -> str:
    lines = []
    for turn in conversation:
        label = "Attacker" if turn["role"] == "attacker" else "Target"
        lines.append(f"{label}: {turn['text']}")
    return "\n".join(lines)


async def _run(cfg: dict) -> dict:
    from pyrit.score import SelfAskTrueFalseScorer, TrueFalseQuestion
    from pyrit.setup import IN_MEMORY, initialize_pyrit_async

    from app.services.pyrit.runtime.llm_targets import chat_target_with_fallback

    await initialize_pyrit_async(IN_MEMORY)

    scoring_target = chat_target_with_fallback(cfg, "scorer")
    objective_scorer = SelfAskTrueFalseScorer.from_question(
        chat_target=scoring_target,
        question=TrueFalseQuestion(true_description=cfg["success_criteria"]),
    )

    transcript = _transcript(cfg["conversation"])
    scores = await objective_scorer.score_text_async(text=transcript, objective=cfg["objective"])
    score = scores[0] if scores else None

    return {
        "ok": True,
        "achieved": bool(score.get_value()) if score is not None else False,
        "rationale": score.score_rationale if score is not None else None,
    }


def main() -> int:
    config_path, result_path = Path(sys.argv[1]), Path(sys.argv[2])
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    try:
        result = asyncio.run(_run(cfg))
    except Exception:
        tb = traceback.format_exc()
        result_path.write_text(json.dumps({"ok": False, "error": tb}), encoding="utf-8")
        sys.stderr.write(tb)
        return 1

    result_path.write_text(json.dumps(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
