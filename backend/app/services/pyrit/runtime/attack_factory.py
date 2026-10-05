"""Assembles the PyRIT RedTeamingAttack from a run config dict.

Three LLM/target pieces:
  * objective target  -> JsonRestTarget (the endpoint under test)
  * adversarial target -> OpenAIChatTarget (the attacker; writes each turn)
  * scoring target     -> OpenAIChatTarget (the scorer; judges each reply)

Attacker and scorer share one OpenAI-compatible endpoint (e.g. OpenRouter). The
API key is read from the environment inside this subprocess, never from the config.
"""

import os

from pyrit.executor.attack import (
    AttackAdversarialConfig,
    AttackScoringConfig,
    RedTeamingAttack,
)
from pyrit.prompt_target import OpenAIChatTarget
from pyrit.score import SelfAskTrueFalseScorer, TrueFalseQuestion

from app.services.pyrit.runtime.rest_target import JsonRestTarget


def _openai_chat_target(cfg: dict, model: str) -> OpenAIChatTarget:
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


def build_attack(cfg: dict) -> tuple[RedTeamingAttack, str]:
    """Returns (attack, objective). Run with `attack.execute_async(objective=objective)`."""
    objective_target = JsonRestTarget(
        target_url=cfg["target_url"],
        request_template=cfg["request_template"],
        response_field=cfg["response_field"],
        request_timeout=cfg["request_timeout"],
    )

    adversarial_target = _openai_chat_target(cfg, cfg["attacker_model"])
    scoring_target = _openai_chat_target(cfg, cfg["scorer_model"])

    objective_scorer = SelfAskTrueFalseScorer.from_question(
        chat_target=scoring_target,
        question=TrueFalseQuestion(true_description=cfg["success_criteria"]),
    )

    attack = RedTeamingAttack(
        objective_target=objective_target,
        attack_adversarial_config=AttackAdversarialConfig(target=adversarial_target),
        attack_scoring_config=AttackScoringConfig(objective_scorer=objective_scorer),
        max_turns=cfg["max_turns"],
    )
    return attack, cfg["objective"]
