"""Prepares the run directory and subprocess command for one PyRIT attack.

Mirrors the role of `garak_runner.py` for the PyRIT engine: it only writes inputs
and builds the command line. Process lifecycle lives in `pyrit/job_manager.py`.
"""

import json
import uuid
from pathlib import Path

from backend.app.core.config import (
    DEFAULT_REQUEST_TEMPLATE,
    DEFAULT_RESPONSE_FIELD,
    PYRIT_API_KEY_ENV,
    PYRIT_ATTACKER_MODEL,
    PYRIT_DEFAULT_MAX_TURNS,
    PYRIT_DEFAULT_REQUEST_TIMEOUT_SECONDS,
    PYRIT_OPENAI_ENDPOINT,
    PYRIT_PYTHON_EXECUTABLE,
    PYRIT_SCORER_MODEL,
    SCAN_WORK_DIR,
)
from backend.app.schemas.schemas_pyrit import PyritScanRequest

_LAUNCHER = Path(__file__).parent / "runtime" / "launcher.py"


def prepare_run_dir(
    req: PyritScanRequest, objective: str, success_criteria: str
) -> tuple[str, Path, Path, Path]:
    """Creates the run dir and writes run_config.json.

    Returns (run_id, run_dir, run_config_path, result_path). The API key is NOT
    written here — only the name of its env var — so the secret never hits disk.
    """
    run_id = "pyrit-" + uuid.uuid4().hex[:12]
    run_dir = SCAN_WORK_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    run_config = {
        "target_url": req.target_url,
        "request_template": req.request_template or DEFAULT_REQUEST_TEMPLATE,
        "response_field": req.response_field or DEFAULT_RESPONSE_FIELD,
        "request_timeout": req.request_timeout or PYRIT_DEFAULT_REQUEST_TIMEOUT_SECONDS,
        "objective": objective,
        "success_criteria": success_criteria,
        "max_turns": req.max_turns or PYRIT_DEFAULT_MAX_TURNS,
        "openai_endpoint": PYRIT_OPENAI_ENDPOINT,
        "api_key_env": PYRIT_API_KEY_ENV,
        "attacker_model": PYRIT_ATTACKER_MODEL,
        "scorer_model": PYRIT_SCORER_MODEL,
    }
    run_config_path = run_dir / "run_config.json"
    run_config_path.write_text(json.dumps(run_config), encoding="utf-8")

    result_path = run_dir / "result.json"
    return run_id, run_dir, run_config_path, result_path


def build_command(run_config_path: Path, result_path: Path) -> list[str]:
    return [
        PYRIT_PYTHON_EXECUTABLE,
        str(_LAUNCHER),
        str(run_config_path),
        str(result_path),
    ]
