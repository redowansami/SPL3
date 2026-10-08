from fastapi import APIRouter, Depends, HTTPException, status

from app.constants.probes import PROBES_BY_ID
from app.core.security import get_current_user
from app.db.models import User
from app.schemas.schemas import ScanRequest, ScanStartResponse, ScanStatusResponse
from app.services import job_manager

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("", response_model=ScanStartResponse, status_code=status.HTTP_202_ACCEPTED)
def start_scan(scan_request: ScanRequest, current_user: User = Depends(get_current_user)) -> ScanStartResponse:
    if scan_request.engine != "garak":
        raise HTTPException(
            status_code=400,
            detail="Only the 'garak' engine is implemented in this MVP. PyRIT is a demo-only placeholder.",
        )

    probe = PROBES_BY_ID.get(scan_request.probe_id)
    if probe is None:
        raise HTTPException(status_code=400, detail=f"Unknown probe_id '{scan_request.probe_id}'.")

    run_id = job_manager.start_scan_job(scan_request, probe.id, probe.garak_probe, user_id=current_user.id)
    return ScanStartResponse(run_id=run_id)


@router.get("/{run_id}", response_model=ScanStatusResponse)
def get_scan_status(run_id: str, current_user: User = Depends(get_current_user)) -> ScanStatusResponse:
    job = job_manager.get_job(run_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"Unknown run_id '{run_id}'.")
    return job_manager.to_status_response(job)


@router.post("/{run_id}/cancel", response_model=ScanStatusResponse)
def cancel_scan(run_id: str, current_user: User = Depends(get_current_user)) -> ScanStatusResponse:
    job = job_manager.get_job(run_id)
    if job is None or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"Unknown run_id '{run_id}'.")
    job = job_manager.cancel_job(run_id)
    return job_manager.to_status_response(job)
