from fastapi import APIRouter, HTTPException

from app.mitigations import get_mitigation
from backend.app.schemas.schemas import ProbeMitigationOut

router = APIRouter(prefix="/api/mitigations", tags=["mitigations"])


@router.get("/{garak_probe:path}", response_model=ProbeMitigationOut)
def get_probe_mitigation(garak_probe: str) -> ProbeMitigationOut:
    mitigation = get_mitigation(garak_probe)
    if mitigation is None:
        raise HTTPException(status_code=404, detail=f"No mitigation data for probe '{garak_probe}'")
    return mitigation
