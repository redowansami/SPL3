"""Static map from curated Garak probes (see `app/probes.py`) to MITRE ATLAS
techniques and mitigations.

Curated by hand against the MITRE ATLAS knowledge base (atlas.mitre.org) —
techniques (`AML.Txxxx`) and mitigations (`AML.M00xx`) — per the analysis in
`probe-mitigation.md`. Mitigation names/descriptions are the official short
descriptions from atlas.mitre.org/mitigations/<id>. ATLAS content can shift
between releases; re-verify before relying on this for compliance reporting.

Keyed by the same `garak_probe` string used in `ProbeInfo.garak_probe`.
"""

from dataclasses import dataclass, field


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


@dataclass(frozen=True)
class ProbeMitigation:
    garak_probe: str
    atlas_techniques: list[AtlasTechnique]
    atlas_mitigations: list[AtlasMitigation]
    # Concrete, probe-specific actions that operationalize the ATLAS
    # mitigations above (the "applied meaning" column in probe-mitigation.md).
    strategies: list[str] = field(default_factory=list)


# Canonical ATLAS mitigations referenced below, keyed by id, so the text is
# defined once even though several probes share the same mitigation.
_M0004 = AtlasMitigation(
    "AML.M0004",
    "Restrict Number of ML Model Queries",
    "Add rate limiting on model queries, as capping how many requests a single user or key "
    "can make (and how fast) starves out the high-volume probing that extraction and "
    "membership-inference attacks depend on.",
)
_M0007 = AtlasMitigation(
    "AML.M0007",
    "Sanitize Training Data",
    "Sanitize training data before it's ingested, as filtering out poisoned, sensitive, or "
    "policy-violating content up front (and re-running the filter for any active/continual "
    "learning pipeline) stops that content from ever being memorized or reproducible later.",
)
_M0015 = AtlasMitigation(
    "AML.M0015",
    "Adversarial Input Detection",
    "Add adversarial input detection in front of the model, as flagging or blocking queries "
    "that deviate from normal usage or match known attack patterns catches manipulated "
    "inputs before they ever reach inference.",
)
_M0019 = AtlasMitigation(
    "AML.M0019",
    "Control Access to ML Models and Data in Production",
    "Lock down production access, as requiring authentication on every API endpoint and "
    "monitoring queries against usage policy stops unverified or malicious callers from "
    "reaching the model or its data in the first place.",
)
_M0020 = AtlasMitigation(
    "AML.M0020",
    "Generative AI Guardrails",
    "Add generative AI guardrails, as placing a safety layer (filters, rule-based logic, "
    "regex, classifiers, or LLM/NER-based checks) between the model and the user catches "
    "undesired inputs and outputs that slip past the model's own judgment.",
)
_M0021 = AtlasMitigation(
    "AML.M0021",
    "Generative AI Guidelines",
    "Add generative AI guidelines, as steering the model with explicit instructions — "
    "appended to user prompts or baked into the system prompt — directs it toward desired "
    "outputs and away from undesired ones before generation even happens.",
)
_M0022 = AtlasMitigation(
    "AML.M0022",
    "Generative AI Model Alignment",
    "Invest in model alignment, as fine-tuning with techniques like supervised fine-tuning "
    "or RLHF/RLAIF trains the safety behavior into the model itself, rather than relying "
    "solely on external filters to catch what it produces.",
)
_M0024 = AtlasMitigation(
    "AML.M0024",
    "AI Telemetry Logging",
    "Log model inputs and outputs, as continuous telemetry on what goes in and comes out "
    "gives you the visibility to detect an attack in progress and the evidence to "
    "investigate and respond after the fact.",
)


MITIGATION_REGISTRY: dict[str, ProbeMitigation] = {
    "dan.Dan_11_0": ProbeMitigation(
        garak_probe="dan.Dan_11_0",
        atlas_techniques=[
            AtlasTechnique("AML.T0054", "LLM Jailbreak"),
            AtlasTechnique("AML.T0051.000", "LLM Prompt Injection: Direct"),
        ],
        atlas_mitigations=[_M0020, _M0021, _M0022, _M0024],
        strategies=[
            "Detect persona/roleplay jailbreak patterns (e.g. 'DAN', 'do anything now') before generation",
            "Fine-tune / align the model for refusal consistency against jailbreak framings",
            "Log jailbreak-pattern prompts for monitoring, alerting, and future retraining",
        ],
    ),
    "realtoxicityprompts.RTPBlank": ProbeMitigation(
        garak_probe="realtoxicityprompts.RTPBlank",
        atlas_techniques=[
            AtlasTechnique("AML.T0048", "External Harms"),
        ],
        atlas_mitigations=[_M0022, _M0020, _M0024],
        strategies=[
            "Run an output moderation/toxicity classifier on generated continuations",
            "Apply RLHF/alignment tuning against toxic completions",
            "Note: this probe measures baseline alignment rather than a deliberate adversary "
            "technique — ATLAS's adversary-tactic framing is a loose fit; consider pairing "
            "with an OWASP LLM Top 10 (LLM09: Overreliance / harmful content) cross-reference",
        ],
    ),
    "promptinject.HijackHateHumans": ProbeMitigation(
        garak_probe="promptinject.HijackHateHumans",
        atlas_techniques=[
            AtlasTechnique("AML.T0051.000", "LLM Prompt Injection: Direct"),
        ],
        atlas_mitigations=[_M0019, _M0020, _M0021, _M0015, _M0024],
        strategies=[
            "Enforce delimiter-based instruction hierarchy between system and user content",
            "Validate model output against the original task/goal (goal-consistency check)",
            "Restrict production access so a hijacked prompt can't reach privileged actions",
        ],
    ),
    "encoding.InjectBase64": ProbeMitigation(
        garak_probe="encoding.InjectBase64",
        atlas_techniques=[
            AtlasTechnique("AML.T0051", "LLM Prompt Injection"),
            AtlasTechnique("AML.T0015", "Evade AI Model"),
        ],
        atlas_mitigations=[_M0020, _M0021, _M0015, _M0024],
        strategies=[
            "Decode known encodings (Base64 and similar) *before* running the safety "
            "classifier, not after — running it on the still-encoded payload lets it slip past",
            "Detect encoded/obfuscated payloads as an adversarial-input signal in itself",
        ],
    ),
    "malwaregen.TopLevel": ProbeMitigation(
        garak_probe="malwaregen.TopLevel",
        atlas_techniques=[
            AtlasTechnique("AML.T0048", "External Harms"),
            AtlasTechnique("AML.T0043", "Craft Adversarial Data"),
        ],
        atlas_mitigations=[_M0021, _M0020, _M0024],
        strategies=[
            "Enforce a refusal policy for malicious-code generation requests",
            "Run static/behavioral scans on generated code before returning it to the user",
            "Monitor for abuse patterns across repeated malware-adjacent queries",
        ],
    ),
    "leakreplay.LiteratureCloze": ProbeMitigation(
        garak_probe="leakreplay.LiteratureCloze",
        atlas_techniques=[
            AtlasTechnique("AML.T0024", "Exfiltration via AI Inference API Endpoint"),
            AtlasTechnique("AML.T0024.000", "Infer Training Data Membership"),
        ],
        atlas_mitigations=[_M0019, _M0004, _M0024, _M0007],
        strategies=[
            "Rate-limit and monitor query patterns typical of extraction/membership-inference probing",
            "Deduplicate and scrub memorized/sensitive text from training data upstream",
            "Check generated output for high similarity against known copyrighted/sensitive source text",
        ],
    ),
}


def get_mitigation(garak_probe: str) -> ProbeMitigation | None:
    """Look up the ATLAS mitigation mapping for a given `garak_probe` value."""
    return MITIGATION_REGISTRY.get(garak_probe)
