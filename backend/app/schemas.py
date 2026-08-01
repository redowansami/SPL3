from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class ProbeInfo(BaseModel):
    id: str
    label: str
    garak_probe: str
    description: str


class ScanRequest(BaseModel):
    target_url: str = Field(..., description="Target REST endpoint to attack.")
    probe_id: str = Field(..., description="id from GET /api/probes to run.")
    engine: str = Field(default="garak", description="Only 'garak' is currently supported.")
    request_template: dict[str, Any] | None = Field(
        default=None,
        description='JSON body template for the target request; must include "$INPUT" '
        "somewhere as the attack-prompt placeholder. Defaults to {'message': '$INPUT'}.",
    )
    response_field: str | None = Field(
        default=None,
        description="JSON field in the target's response containing the model's reply. "
        "Defaults to 'response'.",
    )
    request_timeout: int | None = Field(
        default=None,
        description="Per-request HTTP timeout in seconds when calling the target endpoint. "
        "Raise this if your target is slow to respond (e.g. it calls an LLM). Defaults to 60.",
    )


class FailureItem(BaseModel):
    probe: str
    detector: str
    prompt: str
    output: str
    score: float
    nli_verdict: str | None = None


class AttackPathStep(BaseModel):
    attempt_seq: int
    goal: str
    probe: str
    detector: str
    prompt_turns: list[str]
    output: str
    triggers: list[str]
    score: float
    nli_verdict: str | None = None


class ProbeSummary(BaseModel):
    probe: str
    detector: str
    passed: int
    total: int


class ScanResponse(BaseModel):
    ok: bool
    probe_id: str
    garak_probe: str
    target_url: str
    attempts_evaluated: int
    failure_count: int
    failures: list[FailureItem]
    summary: list[ProbeSummary]
    attack_paths: list[AttackPathStep]
    nli_filtered_count: int = 0
    nli_filtered_hits: list[AttackPathStep] = []
    error: str | None = None


class ScanStartResponse(BaseModel):
    run_id: str


class ScanStatusResponse(BaseModel):
    run_id: str
    status: JobStatus
    elapsed_seconds: float
    # Populated only once status is terminal; mirrors ScanResponse's fields 1:1 so
    # the frontend's existing result.ok/result.failures/... access keeps working.
    ok: bool | None = None
    probe_id: str | None = None
    garak_probe: str | None = None
    target_url: str | None = None
    attempts_evaluated: int | None = None
    failure_count: int | None = None
    failures: list[FailureItem] = []
    summary: list[ProbeSummary] = []
    attack_paths: list[AttackPathStep] = []
    nli_filtered_count: int = 0
    nli_filtered_hits: list[AttackPathStep] = []
    error: str | None = None
