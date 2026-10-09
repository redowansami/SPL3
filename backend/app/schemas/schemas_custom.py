"""Request/response models for the manual "Custom Attack" flow (`/api/custom/...`).

The user drives the conversation themselves (no auto-attacker), then optionally
asks PyRIT's scorer to judge the transcript against an objective they type in.
Kept separate from `schemas_pyrit.py` since there's no run_id/job lifecycle here —
both endpoints respond synchronously.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class CustomChatRequest(BaseModel):
    target_url: str = Field(..., description="Target REST endpoint to chat with.")
    message: str = Field(..., description="The message to send as the attacker's next turn.")
    request_template: dict[str, Any] | None = Field(
        default=None,
        description='JSON body template for the target request; must include "$INPUT" '
        "somewhere as the message placeholder. Defaults to {'message': '$INPUT'}.",
    )
    response_field: str | None = Field(
        default=None,
        description="JSON field in the target's response containing the model's reply. "
        "Defaults to 'response'.",
    )
    request_timeout: int | None = Field(
        default=None, description="Per-request HTTP timeout in seconds when calling the target endpoint."
    )


class CustomChatResponse(BaseModel):
    reply: str


class CustomTurn(BaseModel):
    role: Literal["attacker", "target"]
    text: str


class CustomEvaluateRequest(BaseModel):
    target_url: str | None = Field(default=None, description="The target endpoint the conversation was run against.")
    objective: str = Field(..., description="What the user was trying to get the target to do.")
    success_criteria: str | None = Field(
        default=None,
        description="What the transcript must contain/do for the scorer to count the objective "
        "as achieved. Defaults to the objective itself.",
    )
    conversation: list[CustomTurn] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _require_objective(self) -> "CustomEvaluateRequest":
        if not self.objective.strip():
            raise ValueError("'objective' must be a non-empty string.")
        return self


class CustomEvaluateResponse(BaseModel):
    ok: bool
    achieved: bool = False
    rationale: str | None = None
    objective_id: str | None = None
    error: str | None = None
