"""Static map from PyRIT objectives (see `app/pyrit_objectives.py`) to MITRE
ATLAS techniques and mitigations.

Keyed by `objective_id`, mirroring how `app/mitigations.py` keys garak probes by
`garak_probe`. The mapping is intentionally rule-based, not derived from the
(dynamic) conversation: ATLAS techniques classify the adversary's *intent*, which
is fixed by the chosen objective — the exact wording the attacker LLM improvises
doesn't change the technique category. Every preset also cites AML.T0054 (LLM
Jailbreak) because each PyRIT attack is delivered as a multi-turn jailbreak.

Custom free-text objectives (no `objective_id`) have no preset key, so they fall
back to a generic LLM-abuse mitigation set.

ATLAS IDs/mitigation objects are shared via `app/atlas.py`. Re-verify against
atlas.mitre.org before relying on this for compliance reporting.
"""

from dataclasses import dataclass, field

from backend.app.constants.atlas import (
    AtlasMitigation,
    AtlasTechnique,
    M0019,
    M0020,
    M0021,
    M0022,
    M0024,
)

# ATLAS techniques referenced below (defined once, shared across objectives).
_T0051_000 = AtlasTechnique("AML.T0051.000", "LLM Prompt Injection: Direct")
_T0054 = AtlasTechnique("AML.T0054", "LLM Jailbreak")
_T0048 = AtlasTechnique("AML.T0048", "External Harms")
_T0043 = AtlasTechnique("AML.T0043", "Craft Adversarial Data")


@dataclass(frozen=True)
class ObjectiveMitigation:
    objective_id: str
    atlas_techniques: list[AtlasTechnique]
    atlas_mitigations: list[AtlasMitigation]
    # Concrete, objective-specific actions that operationalize the ATLAS
    # mitigations above.
    strategies: list[str] = field(default_factory=list)


PYRIT_MITIGATION_REGISTRY: dict[str, ObjectiveMitigation] = {
    "system_prompt_leak": ObjectiveMitigation(
        objective_id="system_prompt_leak",
        atlas_techniques=[_T0051_000, _T0054],
        atlas_mitigations=[M0020, M0021, M0019, M0024],
        strategies=[
            "Never place secrets in the system prompt; keep credentials server-side, out of model context",
            "Add an output guardrail that blocks replies echoing system-prompt or secret content",
            "Enforce a delimiter-based instruction hierarchy so user turns can't override system instructions",
            "Log prompts/outputs to detect multi-turn extraction attempts in progress",
        ],
    ),
    "harmful_instructions": ObjectiveMitigation(
        objective_id="harmful_instructions",
        atlas_techniques=[_T0054, _T0048],
        atlas_mitigations=[M0020, M0021, M0022, M0024],
        strategies=[
            "Run an output guardrail/classifier that blocks actionable dangerous or illegal instructions",
            "Align the model (RLHF/SFT) for consistent refusal under multi-turn pressure and roleplay framing",
            "Bake explicit refusal guidelines into the system prompt for dangerous-activity requests",
            "Monitor for escalation patterns across turns that steer toward disallowed content",
        ],
    ),
    "malware_generation": ObjectiveMitigation(
        objective_id="malware_generation",
        atlas_techniques=[_T0054, _T0048, _T0043],
        atlas_mitigations=[M0020, M0021, M0022, M0024],
        strategies=[
            "Enforce a refusal policy for malicious-code requests (malware, exploits, keyloggers, ransomware)",
            "Scan generated code (static/behavioral) for malicious intent before returning it",
            "Align the model to refuse malicious-code framings even when split across benign-looking turns",
            "Monitor for abuse patterns across repeated malware-adjacent queries",
        ],
    ),
    "hate_toxicity": ObjectiveMitigation(
        objective_id="hate_toxicity",
        atlas_techniques=[_T0054, _T0048],
        atlas_mitigations=[M0020, M0022, M0024],
        strategies=[
            "Run an output toxicity/hate-speech classifier on generated content",
            "Apply RLHF/alignment tuning against toxic and harassing completions",
            "Log flagged outputs for monitoring, alerting, and future retraining",
        ],
    ),
    "misinformation": ObjectiveMitigation(
        objective_id="misinformation",
        atlas_techniques=[_T0054, _T0048],
        atlas_mitigations=[M0020, M0022, M0024],
        strategies=[
            "Guardrail high-stakes topics (health, elections, science) toward sourced, hedged answers",
            "Align the model to correct false premises instead of elaborating on them",
            "Add retrieval/grounding so factual claims are backed by a trusted source",
        ],
    ),
}


# Used for custom free-text objectives (no objective_id) or any id not in the
# registry — the broad guardrails/guidelines/alignment/telemetry set applies to
# essentially any LLM-abuse objective.
_GENERIC_FALLBACK = ObjectiveMitigation(
    objective_id="",
    atlas_techniques=[_T0054],
    atlas_mitigations=[M0020, M0021, M0022, M0024],
    strategies=[
        "Place safety guardrails (input + output filters/classifiers) around the model",
        "Steer behavior with explicit safety guidelines in the system prompt",
        "Invest in model alignment (RLHF/SFT) for consistent refusal under multi-turn pressure",
        "Log model inputs and outputs to detect and investigate abuse",
    ],
)


def get_objective_mitigation(objective_id: str | None) -> ObjectiveMitigation:
    """Look up the ATLAS mapping for a PyRIT objective.

    Never returns None: an unknown or custom (None) objective_id gets the generic
    LLM-abuse fallback so the UI always has mitigation guidance to show.
    """
    if not objective_id:
        return _GENERIC_FALLBACK
    return PYRIT_MITIGATION_REGISTRY.get(objective_id, _GENERIC_FALLBACK)
