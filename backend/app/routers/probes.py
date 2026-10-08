from fastapi import APIRouter

from app.constants.probes import PROBE_REGISTRY
from app.schemas.schemas import ProbeInfo

router = APIRouter(prefix="/api/probes", tags=["probes"])


@router.get("", response_model=list[ProbeInfo])
def list_probes() -> list[ProbeInfo]:
    return PROBE_REGISTRY
