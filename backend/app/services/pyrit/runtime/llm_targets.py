"""Shared OpenAI-compatible chat target construction, used by both the automated
attacker/scorer (`attack_factory.py`) and the manual-evaluate scorer
(`evaluate_launcher.py`). The API key is read from the environment inside
whichever subprocess calls this, never from the config dict.
"""

import os

from pyrit.prompt_target import OpenAIChatTarget


def openai_chat_target(cfg: dict, model: str) -> OpenAIChatTarget:
    api_key = os.environ.get(cfg["api_key_env"])
    if not api_key:
        raise RuntimeError(
            f"Environment variable {cfg['api_key_env']} is not set; cannot reach the attacker/scorer LLM."
        )
    return OpenAIChatTarget(
        endpoint=cfg["openai_endpoint"],
        api_key=api_key,
        model_name=model,
    )
