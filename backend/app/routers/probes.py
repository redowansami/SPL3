from fastapi import APIRouter

from backend.app.constants.probes import PROBE_REGISTRY
from backend.app.schemas.schemas import ProbeInfo

router = APIRouter(prefix="/api/probes", tags=["probes"])


@router.get("", response_model=list[ProbeInfo])
def list_probes() -> list[ProbeInfo]:
    return PROBE_REGISTRY
