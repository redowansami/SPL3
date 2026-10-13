"""Manual "Custom Attack" endpoints: the user drives the conversation by hand
(no auto-attacker), then can ask PyRIT's scorer to judge the transcript against
an objective they type in. Both endpoints respond synchronously — there's no
run_id/job lifecycle like garak/pyrit scans have.
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import (
    DEFAULT_REQUEST_TEMPLATE,
    DEFAULT_RESPONSE_FIELD,
    PYRIT_API_KEY_ENV,
    PYRIT_DEFAULT_REQUEST_TIMEOUT_SECONDS,
    PYRIT_EVALUATE_TIMEOUT_SECONDS,
)
from app.core.security import get_current_user
from app.db import repository
from app.db.models import User
from app.schemas.schemas_custom import (
    CustomChatRequest,
    CustomChatResponse,
    CustomEvaluateRequest,
    CustomEvaluateResponse,
)
from app.services.custom_attack_classifier import classify_custom_objective
from app.services.pyrit.runner import build_evaluate_command, prepare_evaluate_run_dir
from app.services.pyrit.runtime.request_body import extract_response, render_request_body

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/custom", tags=["custom-attack"])


@router.post("/chat", response_model=CustomChatResponse)
async def custom_chat(
    req: CustomChatRequest, current_user: User = Depends(get_current_user)
) -> CustomChatResponse:
    template = req.request_template or DEFAULT_REQUEST_TEMPLATE
    response_field = req.response_field or DEFAULT_RESPONSE_FIELD
    timeout = req.request_timeout or PYRIT_DEFAULT_REQUEST_TIMEOUT_SECONDS

    body = render_request_body(template, req.message)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            http_response = await client.post(
                req.target_url,
                json=body,
                headers={"Content-Type": "application/json", **(req.auth_headers or {})},
            )
            http_response.raise_for_status()
            reply = extract_response(http_response.json(), response_field)
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=502, detail=f"Target did not respond within {timeout}s (timed out)."
        ) from None
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Target request failed: {exc}") from None
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Could not read target response: {exc}") from None

    return CustomChatResponse(reply=reply)


@router.post("/evaluate", response_model=CustomEvaluateResponse)
async def evaluate_custom_attack(
    req: CustomEvaluateRequest, current_user: User = Depends(get_current_user)
) -> CustomEvaluateResponse:
    if not os.environ.get(PYRIT_API_KEY_ENV):
        raise HTTPException(
            status_code=400,
            detail=f"Evaluation needs a scorer LLM: set the {PYRIT_API_KEY_ENV} environment variable.",
        )

    success_criteria = (req.success_criteria or req.objective).strip()
    run_id, run_dir, run_config_path, result_path = prepare_evaluate_run_dir(req, success_criteria)
    command = build_evaluate_command(run_config_path, result_path)

    started_at = datetime.now(timezone.utc).replace(tzinfo=None)
    result = await asyncio.to_thread(_run_evaluate_subprocess, command, run_dir, result_path)
    if result.ok:
        objective_id = await asyncio.to_thread(classify_custom_objective, req.objective)
        result = result.model_copy(update={"objective_id": objective_id})
    ended_at = datetime.now(timezone.utc).replace(tzinfo=None)

    persisted = repository.save_custom_attack(
        run_id=run_id,
        target_url=req.target_url or "",
        req=req,
        artifact_dir=str(run_dir),
        started_at=started_at,
        ended_at=ended_at,
        result=result,
        user_id=current_user.id,
    )
    if not persisted:
        logger.error("Custom attack evaluate %s finished but was NOT persisted to the database.", run_id)

    return result


def _run_evaluate_subprocess(command: list[str], run_dir: Path, result_path: Path) -> CustomEvaluateResponse:
    try:
        proc = subprocess.run(
            command,
            cwd=run_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PYRIT_EVALUATE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return CustomEvaluateResponse(
            ok=False, error=f"Evaluation exceeded the {PYRIT_EVALUATE_TIMEOUT_SECONDS}s timeout limit."
        )

    if not result_path.exists():
        error_tail = (proc.stderr or proc.stdout or "").strip()[-2000:]
        return CustomEvaluateResponse(ok=False, error=error_tail or "Evaluation produced no result file.")

    data = json.loads(result_path.read_text(encoding="utf-8"))
    if not data.get("ok"):
        error_tail = (data.get("error") or proc.stderr or "").strip()[-2000:]
        return CustomEvaluateResponse(ok=False, error=error_tail or "Evaluation failed.")

    return CustomEvaluateResponse(ok=True, achieved=bool(data.get("achieved")), rationale=data.get("rationale"))
