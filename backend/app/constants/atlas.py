"""Shared MITRE ATLAS catalog: the dataclasses and canonical mitigation objects
used by both the garak probe mapping (`app/mitigations.py`) and the PyRIT
objective mapping (`app/pyrit_mitigations.py`).

Technique IDs (`AML.Txxxx`) and mitigation IDs (`AML.M00xx`) are from the MITRE
ATLAS knowledge base (atlas.mitre.org). Mitigation names/descriptions are the
official short descriptions from atlas.mitre.org/mitigations/<id>. ATLAS content
can shift between releases; re-verify before relying on this for compliance
reporting.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AtlasTechnique:
    id: str
    name: str


@dataclass(frozen=True)
class AtlasMitigation:
    id: str
    name: str
    # Official short description from atlas.mitre.org/mitigations/<id>.
    description: str


# Canonical ATLAS mitigations, keyed by id, so the text is defined once even
# though several probes/objectives share the same mitigation.
M0004 = AtlasMitigation(
    "AML.M0004",
    "Restrict Number of ML Model Queries",
    "Add rate limiting on model queries, as capping how many requests a single user or key "
    "can make (and how fast) starves out the high-volume probing that extraction and "
    "membership-inference attacks depend on.",
)
M0007 = AtlasMitigation(
    "AML.M0007",
    "Sanitize Training Data",
    "Sanitize training data before it's ingested, as filtering out poisoned, sensitive, or "
    "policy-violating content up front (and re-running the filter for any active/continual "
    "learning pipeline) stops that content from ever being memorized or reproducible later.",
)
M0015 = AtlasMitigation(
    "AML.M0015",
    "Adversarial Input Detection",
    "Add adversarial input detection in front of the model, as flagging or blocking queries "
    "that deviate from normal usage or match known attack patterns catches manipulated "
    "inputs before they ever reach inference.",
)
M0019 = AtlasMitigation(
    "AML.M0019",
    "Control Access to ML Models and Data in Production",
    "Lock down production access, as requiring authentication on every API endpoint and "
    "monitoring queries against usage policy stops unverified or malicious callers from "
    "reaching the model or its data in the first place.",
)
M0020 = AtlasMitigation(
    "AML.M0020",
    "Generative AI Guardrails",
    "Add generative AI guardrails, as placing a safety layer (filters, rule-based logic, "
    "regex, classifiers, or LLM/NER-based checks) between the model and the user catches "
    "undesired inputs and outputs that slip past the model's own judgment.",
)
M0021 = AtlasMitigation(
    "AML.M0021",
    "Generative AI Guidelines",
    "Add generative AI guidelines, as steering the model with explicit instructions — "
    "appended to user prompts or baked into the system prompt — directs it toward desired "
    "outputs and away from undesired ones before generation even happens.",
)
M0022 = AtlasMitigation(
    "AML.M0022",
    "Generative AI Model Alignment",
    "Invest in model alignment, as fine-tuning with techniques like supervised fine-tuning "
    "or RLHF/RLAIF trains the safety behavior into the model itself, rather than relying "
    "solely on external filters to catch what it produces.",
)
M0024 = AtlasMitigation(
    "AML.M0024",
    "AI Telemetry Logging",
    "Log model inputs and outputs, as continuous telemetry on what goes in and comes out "
    "gives you the visibility to detect an attack in progress and the evidence to "
    "investigate and respond after the fact.",
)
