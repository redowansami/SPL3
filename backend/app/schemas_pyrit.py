"""Request/response models for PyRIT multi-turn attacks (`/api/pyrit/...`).

Kept separate from `schemas.py` (garak) on purpose: a PyRIT run is a single
attacker-vs-target conversation judged by PyRIT's own LLM scorer, not a set of
garak attempts/detectors, so its result has a different shape.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from backend.app.core.config import PYRIT_MAX_TURNS_LIMIT
from app.schemas import AtlasMitigationOut, AtlasTechniqueOut, JobStatus


class PyritObjectiveInfo(BaseModel):
    id: str
    label: str
    description: str
    objective: str
    success_criteria: str


class PyritMitigationOut(BaseModel):
    objective_id: str
    atlas_techniques: list[AtlasTechniqueOut]
    atlas_mitigations: list[AtlasMitigationOut]
    strategies: list[str]


class PyritScanRequest(BaseModel):
    target_url: str = Field(..., description="Target REST endpoint to attack.")
    objective_id: str | None = Field(
        default=None, description="id from GET /api/pyrit/objectives to use as the attack goal."
    )
    objective: str | None = Field(
        default=None,
        description="Free-text attack goal. Overrides the preset's objective when both are given.",
    )
    success_criteria: str | None = Field(
        default=None,
        description="What a target response must contain/do for the scorer to count the objective "
        "as achieved. Defaults to the preset's criteria, or to the objective itself.",
    )
    max_turns: int | None = Field(
        default=None,
        ge=1,
        le=PYRIT_MAX_TURNS_LIMIT,
        description="Maximum attacker turns before giving up.",
    )
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
        default=None, description="Per-request HTTP timeout in seconds when calling the target endpoint."
    )

    @model_validator(mode="after")
    def _require_objective(self) -> "PyritScanRequest":
        if not self.objective_id and not (self.objective and self.objective.strip()):
            raise ValueError("Provide either 'objective_id' or a non-empty 'objective'.")
        return self


class ConversationTurn(BaseModel):
    turn: int
    role: Literal["attacker", "target"]
    text: str


class PyritScanResponse(BaseModel):
    ok: bool
    target_url: str
    objective_id: str | None = None
    objective: str
    # PyRIT's AttackOutcome: "success" | "failure" | "undetermined" | "error".
    outcome: str | None = None
    outcome_reason: str | None = None
    achieved: bool = False
    executed_turns: int = 0
    final_score_rationale: str | None = None
    conversation: list[ConversationTurn] = []
    error: str | None = None


class PyritScanStartResponse(BaseModel):
    run_id: str


class PyritScanStatusResponse(BaseModel):
    run_id: str
    status: JobStatus
    elapsed_seconds: float
    # Populated only once status is terminal; mirrors PyritScanResponse's fields.
    ok: bool | None = None
    target_url: str | None = None
    objective_id: str | None = None
    objective: str | None = None
    outcome: str | None = None
    outcome_reason: str | None = None
    achieved: bool = False
    executed_turns: int = 0
    final_score_rationale: str | None = None
    conversation: list[ConversationTurn] = []
    error: str | None = None
