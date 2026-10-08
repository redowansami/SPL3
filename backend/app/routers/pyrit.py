"""PyRIT multi-turn attack endpoints, parallel to the garak `scan` router."""

import os

from fastapi import APIRouter, HTTPException, status

from backend.app.core.config import PYRIT_API_KEY_ENV
from app.pyrit_mitigations import get_objective_mitigation
from app.pyrit_objectives import PYRIT_OBJECTIVES, PYRIT_OBJECTIVES_BY_ID
from app.schemas_pyrit import (
    PyritMitigationOut,
    PyritObjectiveInfo,
    PyritScanRequest,
    PyritScanStartResponse,
    PyritScanStatusResponse,
)
from app.services.pyrit import job_manager

router = APIRouter(prefix="/api/pyrit", tags=["pyrit"])


@router.get("/objectives", response_model=list[PyritObjectiveInfo])
def list_objectives() -> list[PyritObjectiveInfo]:
    return PYRIT_OBJECTIVES


@router.get("/mitigations/{objective_id}", response_model=PyritMitigationOut)
def get_pyrit_mitigation(objective_id: str) -> PyritMitigationOut:
    # Never 404s: unknown / custom objective ids get the generic fallback mapping.
    return get_objective_mitigation(objective_id)


@router.post("/scan", response_model=PyritScanStartResponse, status_code=status.HTTP_202_ACCEPTED)
def start_pyrit_scan(req: PyritScanRequest) -> PyritScanStartResponse:
    preset = None
    if req.objective_id is not None:
        preset = PYRIT_OBJECTIVES_BY_ID.get(req.objective_id)
        if preset is None:
            raise HTTPException(status_code=400, detail=f"Unknown objective_id '{req.objective_id}'.")

    objective = (req.objective or (preset.objective if preset else "")).strip()
    success_criteria = (
        req.success_criteria
        or (preset.success_criteria if preset else None)
        or objective
    )

    if not os.environ.get(PYRIT_API_KEY_ENV):
        raise HTTPException(
            status_code=400,
            detail=f"PyRIT needs an attacker/scorer LLM: set the {PYRIT_API_KEY_ENV} environment variable.",
        )

    run_id = job_manager.start_pyrit_job(req, req.objective_id, objective, success_criteria)
    return PyritScanStartResponse(run_id=run_id)


@router.get("/scan/{run_id}", response_model=PyritScanStatusResponse)
def get_pyrit_scan_status(run_id: str) -> PyritScanStatusResponse:
    job = job_manager.get_job(run_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Unknown run_id '{run_id}'.")
    return job_manager.to_status_response(job)


@router.post("/scan/{run_id}/cancel", response_model=PyritScanStatusResponse)
def cancel_pyrit_scan(run_id: str) -> PyritScanStatusResponse:
    job = job_manager.cancel_job(run_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Unknown run_id '{run_id}'.")
    return job_manager.to_status_response(job)
