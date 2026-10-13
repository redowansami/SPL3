"""Shared OpenAI-compatible chat target construction, used by both the automated
attacker/scorer (`attack_factory.py`) and the manual-evaluate scorer
(`evaluate_launcher.py`). API keys are read from the environment inside whichever
subprocess calls this, never from the config dict.

Each role ("attacker" or "scorer") has a primary provider (OpenAI) and a fallback
provider (OpenRouter, unchanged from the original single-provider setup). When both
are configured, calls go to the primary first and only fall over to the fallback if
every primary call for a request raises (missing/invalid key, rate limit, network
error, ...).
"""

import os

from pyrit.prompt_target import OpenAIChatTarget

from app.services.pyrit.runtime.fallback_target import PrimaryWithFallbackTarget


def _build_target(*, endpoint: str, api_key: str, model_name: str, underlying_model: str) -> OpenAIChatTarget:
    return OpenAIChatTarget(
        endpoint=endpoint,
        api_key=api_key,
        model_name=model_name,
        underlying_model=underlying_model,
    )


def chat_target_with_fallback(cfg: dict, role: str) -> OpenAIChatTarget:
    """Builds the chat target for `role` ("attacker" or "scorer"): OpenAI primary,
    OpenRouter fallback.

    Both targets are given the same `underlying_model` (the primary/OpenAI model
    name) so PyRIT's RoundRobinTarget accepts them as behaviorally equivalent for
    fallback/scoring purposes, even though their provider-specific `model_name`
    differs (e.g. OpenAI's "gpt-4o-mini" vs OpenRouter's "openai/gpt-4o-mini").
    """
    primary_model = cfg[f"{role}_primary_model"]
    primary_key = os.environ.get(cfg[f"{role}_primary_api_key_env"])
    fallback_key = os.environ.get(cfg[f"{role}_fallback_api_key_env"])

    targets = []
    if primary_key:
        targets.append(
            _build_target(
                endpoint=cfg[f"{role}_primary_endpoint"],
                api_key=primary_key,
                model_name=primary_model,
                underlying_model=primary_model,
            )
        )
    if fallback_key:
        targets.append(
            _build_target(
                endpoint=cfg[f"{role}_fallback_endpoint"],
                api_key=fallback_key,
                model_name=cfg[f"{role}_fallback_model"],
                underlying_model=primary_model,
            )
        )

    if not targets:
        raise RuntimeError(
            f"Neither {cfg[f'{role}_primary_api_key_env']} nor {cfg[f'{role}_fallback_api_key_env']} "
            f"is set; cannot reach the {role} LLM."
        )
    if len(targets) == 1:
        return targets[0]
    return PrimaryWithFallbackTarget(targets=targets)
