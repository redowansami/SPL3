"""Read-side shapes for persisted scan history (GET /api/scans*).

Kept separate from schemas.py / schemas_pyrit.py, which are the live
scan-engine wire contracts (request/response for an in-flight run); these
shapes describe the stored ScanRun rows instead.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.schemas import JobStatus


class ScanRunSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    engine: str
    status: JobStatus
    target_url: str
    probe_id: str | None = None
    garak_probe: str | None = None
    objective_id: str | None = None
    ok: bool
    started_at: datetime
    ended_at: datetime
    attempts_evaluated: int | None = None
    failure_count: int | None = None
    achieved: bool | None = None
    executed_turns: int | None = None


class ScanRunListResponse(BaseModel):
    total_returned: int
    runs: list[ScanRunSummaryOut]
