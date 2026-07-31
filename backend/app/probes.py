"""Curated, fixed list of Garak probes exposed as buttons in the UI.

This is intentionally a small hand-picked subset (not the full Garak probe catalog)
to keep the MVP's scan times short and its surface area predictable. Each entry maps
a UI-friendly id/label to the exact `--probes` class path Garak expects.
"""

from app.schemas import ProbeInfo

PROBE_REGISTRY: list[ProbeInfo] = [
    ProbeInfo(
        id="dan",
        label="DAN",
        garak_probe="dan.Dan_11_0",
        description="Classic 'Do Anything Now' jailbreak prompt.",
    ),
    ProbeInfo(
        id="promptinject",
        label="Prompt Injection",
        garak_probe="promptinject.HijackHateHumans",
        description="PromptInject-style goal hijacking attack.",
    ),
    ProbeInfo(
        id="encoding",
        label="Encoding",
        garak_probe="encoding.InjectBase64",
        description="Smuggles payloads past filters via Base64 encoding.",
    ),
    ProbeInfo(
        id="malwaregen",
        label="Malware Generation",
        garak_probe="malwaregen.TopLevel",
        description="Attempts to get the target to author malware.",
    ),
    ProbeInfo(
        id="leakreplay",
        label="Data Leak Replay",
        garak_probe="leakreplay.LiteratureCloze",
        description="Probes for verbatim reproduction of training data.",
    ),
]

PROBES_BY_ID = {p.id: p for p in PROBE_REGISTRY}
