"""Parses a Garak run.hitlog.jsonl file into AttackPathStep entries.

Hitlog row shape (one line per successful "hit", written by garak's evaluator —
see garak/evaluators/base.py):

  {"goal": "...", "prompt": {"turns": [{"role": "user", "content": {"text": "..."}}, ...]},
   "output": {"text": "..."}, "triggers": [...], "score": <float>,
   "attempt_seq": <int>, "probe": "...", "detector": "...", ...}

This file only exists when a probe produced >=1 hit; a missing file means zero
hits, not an error.
"""

import json
from pathlib import Path

from app.schemas.schemas import AttackPathStep


def parse_hitlog(hitlog_path: Path) -> list[AttackPathStep]:
    attack_paths: list[AttackPathStep] = []

    if not hitlog_path.exists():
        return attack_paths

    with hitlog_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            try:
                turns = (row.get("prompt") or {}).get("turns") or []
                prompt_turns = [(turn.get("content") or {}).get("text", "") for turn in turns]
                attack_paths.append(
                    AttackPathStep(
                        attempt_seq=row.get("attempt_seq", 0),
                        goal=row.get("goal", ""),
                        probe=row.get("probe", "unknown"),
                        detector=row.get("detector", "unknown"),
                        prompt_turns=prompt_turns,
                        output=(row.get("output") or {}).get("text", ""),
                        triggers=row.get("triggers") or [],
                        score=float(row.get("score", 0.0)),
                    )
                )
            except (TypeError, ValueError):
                continue  # malformed row; skip rather than fail the whole scan

    return attack_paths
