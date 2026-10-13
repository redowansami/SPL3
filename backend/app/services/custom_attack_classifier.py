"""Classifies a Custom Attack's free-text objective into one of the known PyRIT
preset objective ids (or ``None``), so it can reuse the exact same ATLAS
mitigation lookup PyRIT presets already have (``get_objective_mitigation`` in
``pyrit_mitigations.py``) instead of always falling back to the generic entry.

Uses `sentence-transformers` (already a backend dependency — see
`nli_verifier.py`) for local, offline sentence-embedding cosine similarity: no
network/LLM call at request time. Unlike bag-of-words/keyword matching, this
genuinely captures paraphrases ("leak internal configuration" ~ "reveal system
prompt") because the embedding model was trained on sentence meaning, not exact
word overlap.
"""

from functools import lru_cache

from app.constants.pyrit_objectives import PYRIT_OBJECTIVES

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Cosine similarity below this is "no good match" -> caller falls back to the
# generic ATLAS mitigation. Tunable, same convention as HIT_SCORE_THRESHOLD in
# app/core/config.py. Calibrated empirically: MiniLM cosine similarity between a
# genuinely related objective and its preset's reference text lands at ~0.35-0.65,
# while an unrelated objective's best match stays below ~0.05.
_SIMILARITY_THRESHOLD = 0.3


def _reference_text(preset) -> str:
    return f"{preset.label}. {preset.description} {preset.objective} {preset.success_criteria}"


@lru_cache(maxsize=1)
def _get_model_and_embeddings():
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(_MODEL_NAME)
    texts = [_reference_text(preset) for preset in PYRIT_OBJECTIVES]
    embeddings = model.encode(texts, normalize_embeddings=True)
    return model, embeddings


def classify_custom_objective(objective: str) -> str | None:
    """Returns the best-matching preset's id if its similarity to `objective`
    clears the threshold, else None (caller should use the generic mitigation)."""
    from sentence_transformers import util

    model, preset_embeddings = _get_model_and_embeddings()
    objective_embedding = model.encode([objective], normalize_embeddings=True)
    scores = util.cos_sim(objective_embedding, preset_embeddings)[0]

    best_idx = int(scores.argmax())
    if float(scores[best_idx]) < _SIMILARITY_THRESHOLD:
        return None
    return PYRIT_OBJECTIVES[best_idx].id
