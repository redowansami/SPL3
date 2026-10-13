"""Pure helpers for shaping requests to / reading replies from the target endpoint.

No `pyrit` import, so this is usable (and unit-testable) from either venv.
Uses the same "$INPUT" placeholder convention as the garak REST config.
"""

from typing import Any

PROMPT_PLACEHOLDER = "$INPUT"


def render_request_body(template: Any, prompt: str) -> Any:
    """Returns a copy of `template` with every "$INPUT" occurrence in string
    values replaced by `prompt`, recursing into dicts and lists."""
    if isinstance(template, str):
        return template.replace(PROMPT_PLACEHOLDER, prompt)
    if isinstance(template, dict):
        return {key: render_request_body(value, prompt) for key, value in template.items()}
    if isinstance(template, list):
        return [render_request_body(item, prompt) for item in template]
    return template


def template_has_placeholder(template: Any) -> bool:
    if isinstance(template, str):
        return PROMPT_PLACEHOLDER in template
    if isinstance(template, dict):
        return any(template_has_placeholder(v) for v in template.values())
    if isinstance(template, list):
        return any(template_has_placeholder(v) for v in template)
    return False


def extract_response(data: Any, field: str) -> str:
    """Reads the reply text from a JSON response. `field` may be dotted
    ("choices.0.message.content") to reach nested values."""
    value = data
    for part in field.split("."):
        if isinstance(value, list) and part.isdigit():
            value = value[int(part)]
        elif isinstance(value, dict) and part in value:
            value = value[part]
        else:
            raise KeyError(f"Response field '{field}' not found in target response.")
    return value if isinstance(value, str) else str(value)
