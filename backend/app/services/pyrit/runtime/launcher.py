"""Entry point run as a subprocess by the PyRIT job manager.

    python launcher.py <run_config.json> <result.json>

Reads the run config, runs a single RedTeamingAttack to completion, and writes a
result.json the parent process (app.services.pyrit.result_parser) turns into a
PyritScanResponse. On any failure it writes an error result.json AND exits non-zero
so the job manager reports FAILED with the stderr tail.

Invoked by file path (not `-m`) so it only needs `pyrit`, `httpx`, and the pure
`app.services.pyrit.runtime.request_body` module on sys.path — not FastAPI.
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


def _role_label(api_role: str) -> str | None:
    # The attacker's prompts arrive at the target as "user"; the target's replies
    # are "assistant". System prompts and anything else aren't part of the transcript.
    if api_role == "user":
        return "attacker"
    if api_role == "assistant":
        return "target"
    return None


async def _run(cfg: dict) -> dict:
    from pyrit.memory import CentralMemory
    from pyrit.setup import IN_MEMORY, initialize_pyrit_async

    from app.services.pyrit.runtime.attack_factory import build_attack

    await initialize_pyrit_async(IN_MEMORY)

    attack, objective = build_attack(cfg)
    result = await attack.execute_async(objective=objective)

    memory = CentralMemory.get_memory_instance()
    messages = memory.get_conversation_messages(conversation_id=result.conversation_id)

    conversation = []
    turn = 0
    for message in messages:
        role = _role_label(message.api_role)
        if role is None:
            continue
        if role == "attacker":
            turn += 1
        conversation.append({"turn": turn, "role": role, "text": message.get_value()})

    last_score = result.last_score
    return {
        "ok": True,
        "objective": objective,
        "outcome": result.outcome.value if result.outcome is not None else None,
        "outcome_reason": result.outcome_reason,
        "achieved": result.outcome is not None and result.outcome.value == "success",
        "executed_turns": result.executed_turns,
        "final_score_rationale": last_score.score_rationale if last_score is not None else None,
        "conversation": conversation,
    }


def main() -> int:
    config_path, result_path = Path(sys.argv[1]), Path(sys.argv[2])
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    try:
        result = asyncio.run(_run(cfg))
    except Exception:
        tb = traceback.format_exc()
        result_path.write_text(
            json.dumps({"ok": False, "objective": cfg.get("objective", ""), "error": tb}),
            encoding="utf-8",
        )
        sys.stderr.write(tb)
        return 1

    result_path.write_text(json.dumps(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
