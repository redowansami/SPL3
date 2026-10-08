"""Parses a Garak report.jsonl file into the failures/summary shape the API returns.

Report row shapes (relevant subset, per Garak's `Attempt.as_dict()` / evaluator):

  {"entry_type": "attempt", "status": 2, "probe_classname": "...",
   "prompt": {"text": "..."}, "outputs": [{"text": "..."}, ...],
   "detector_results": {"<detector_name>": [<score>, ...]}}   # scores align with outputs

  {"entry_type": "eval", "probe": "...", "detector": "...",
   "passed": <int>, "total": <int>}

A generation is a "hit" (i.e. the target failed the probe) when its detector score is
>= HIT_SCORE_THRESHOLD, mirroring garak's own default ThresholdEvaluator.
"""

import json
from pathlib import Path

from backend.app.core.config import HIT_SCORE_THRESHOLD
from app.schemas import FailureItem, ProbeSummary

ATTEMPT_COMPLETE = 2


def parse_report(report_path: Path) -> tuple[list[FailureItem], list[ProbeSummary], int]:
    failures: list[FailureItem] = []
    summaries: list[ProbeSummary] = []
    attempts_evaluated = 0

    if not report_path.exists():
        return failures, summaries, attempts_evaluated

    with report_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = row.get("entry_type")

            if entry_type == "attempt" and row.get("status") == ATTEMPT_COMPLETE:
                attempts_evaluated += 1
                probe = row.get("probe_classname", "unknown")
                turns = (row.get("prompt") or {}).get("turns") or []
                prompt_text = "\n".join((turn.get("content") or {}).get("text", "") for turn in turns)
                outputs = row.get("outputs") or []
                detector_results = row.get("detector_results") or {}

                for detector, scores in detector_results.items():
                    for i, score in enumerate(scores):
                        if score is None or score < HIT_SCORE_THRESHOLD:
                            continue
                        output_entry = outputs[i] if i < len(outputs) else None
                        output_text = (output_entry or {}).get("text", "") if output_entry else ""
                        failures.append(
                            FailureItem(
                                probe=probe,
                                detector=detector,
                                prompt=prompt_text,
                                output=output_text or "",
                                score=float(score),
                            )
                        )

            elif entry_type == "eval":
                summaries.append(
                    ProbeSummary(
                        probe=row.get("probe", "unknown"),
                        detector=row.get("detector", "unknown"),
                        passed=row.get("passed", 0),
                        total=row.get("total", row.get("total_evaluated", 0)),
                    )
                )

    return failures, summaries, attempts_evaluated
