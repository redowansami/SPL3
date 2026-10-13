"""Assembles the PyRIT RedTeamingAttack from a run config dict.

Three LLM/target pieces:
  * objective target  -> JsonRestTarget (the endpoint under test)
  * adversarial target -> OpenAIChatTarget (the attacker; writes each turn)
  * scoring target     -> OpenAIChatTarget (the scorer; judges each reply)

Attacker and scorer each use OpenAI as primary and OpenRouter as fallback (see
`llm_targets.chat_target_with_fallback`). API keys are read from the environment
inside this subprocess, never from the config.
"""

from pyrit.executor.attack import (
    AttackAdversarialConfig,
    AttackScoringConfig,
    RedTeamingAttack,
)
from pyrit.score import SelfAskTrueFalseScorer, TrueFalseQuestion

from app.services.pyrit.runtime.llm_targets import chat_target_with_fallback
from app.services.pyrit.runtime.rest_target import JsonRestTarget


def build_attack(cfg: dict) -> tuple[RedTeamingAttack, str]:
    """Returns (attack, objective). Run with `attack.execute_async(objective=objective)`."""
    objective_target = JsonRestTarget(
        target_url=cfg["target_url"],
        request_template=cfg["request_template"],
        response_field=cfg["response_field"],
        request_timeout=cfg["request_timeout"],
        auth_headers=cfg.get("auth_headers"),
    )

    adversarial_target = chat_target_with_fallback(cfg, "attacker")
    scoring_target = chat_target_with_fallback(cfg, "scorer")

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
