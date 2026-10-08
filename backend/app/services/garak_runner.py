"""Builds the working directory, generator config, and CLI command for a single
Garak probe run against a target.

Each call gets its own working directory under SCAN_WORK_DIR so concurrent scans
(and their generator config + report files) never collide. Process lifecycle
(launching, watching, killing) lives in `job_manager.py` — this module only
prepares what's needed to invoke `garak`.
"""

import json
import uuid
from pathlib import Path

from backend.app.core.config import (
    GENERATIONS_PER_PROMPT,
    PYTHON_EXECUTABLE,
    SCAN_WORK_DIR,
    SOFT_PROBE_PROMPT_CAP,
)
from backend.app.schemas.schemas import ScanRequest
from app.services.rest_config import build_rest_generator_config


def prepare_run_dir(scan_request: ScanRequest) -> tuple[str, Path, Path, Path, Path]:
    """Creates run_dir, writes generator.json and run_config.json.

    Returns (run_id, run_dir, generator_config_path, run_config_path, report_prefix).
    """
    run_id = uuid.uuid4().hex[:12]
    run_dir = SCAN_WORK_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    generator_config_path = run_dir / "generator.json"
    generator_config_path.write_text(
        json.dumps(build_rest_generator_config(scan_request)), encoding="utf-8"
    )

    # Garak has no CLI flag for soft_probe_prompt_cap; it's only settable via a
    # `--config` run-config file (JSON or YAML), merged under the "run" key.
    run_config_path = run_dir / "run_config.json"
    run_config_path.write_text(
        json.dumps({"run": {"soft_probe_prompt_cap": SOFT_PROBE_PROMPT_CAP}}),
        encoding="utf-8",
    )

    report_prefix = run_dir / "run"

    return run_id, run_dir, generator_config_path, run_config_path, report_prefix


GARAK_LAUNCHER = Path(__file__).with_name("garak_launcher.py")


def build_garak_command(
    generator_config_path: Path, run_config_path: Path, garak_probe: str, report_prefix: Path
) -> list[str]:
    return [
        PYTHON_EXECUTABLE,
        str(GARAK_LAUNCHER),
        "--target_type",
        "rest",
        "--generator_option_file",
        str(generator_config_path),
        "--config",
        str(run_config_path),
        "--probes",
        garak_probe,
        "--generations",
        str(GENERATIONS_PER_PROMPT),
        "--report_prefix",
        str(report_prefix),
        "--parallel_requests",
        "1",
        "--parallel_attempts",
        "1",
        "--narrow_output",
    ]
