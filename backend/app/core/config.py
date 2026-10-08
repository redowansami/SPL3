import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env (if present) before reading any env var below. This puts keys
# like OPENROUTER_API_KEY into os.environ for both the API process (the PyRIT
# router's pre-check) and the PyRIT subprocess, which inherits this environment.
# Real env vars already set take precedence (override=False).
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Root temp directory where per-scan work dirs (generator config + garak report) are created.
SCAN_WORK_DIR = Path(__file__).resolve().parent.parent / ".scan_runs"

# Python interpreter used to invoke `garak` as `python -m garak`.
# Using sys.executable (rather than relying on a `garak` script on PATH) keeps this
# working the same way inside whatever venv the backend itself was started with.
PYTHON_EXECUTABLE = sys.executable

# Detector score at/above this is treated as a "hit" (attack succeeded / target failed).
# This matches garak's own default ThresholdEvaluator boundary.
HIT_SCORE_THRESHOLD = 0.5

# Generations per prompt. Kept at 1 for demo runs so a scan finishes in a reasonable time.
GENERATIONS_PER_PROMPT = 1

# Upper bound on how many prompts a single probe run will generate/send. Garak calls
# this the "soft probe prompt cap" — probes that build large prompt sets (e.g.
# promptinject.HijackHateHumans, which combines multiple attack x rogue-string
# templates into 250+ prompts) truncate/sample down to this count. Keeps demo runs
# fast; there's no CLI flag for this, it must be passed via a `--config` run-config
# file (see garak_runner.py).
SOFT_PROBE_PROMPT_CAP = 10

# Hard ceiling on how long a single garak subprocess run may take.
SCAN_TIMEOUT_SECONDS = 1500

# Default request body template when a scan doesn't specify its own. "$INPUT" is
# garak's placeholder for the attack prompt text.
DEFAULT_REQUEST_TEMPLATE: dict = {"message": "$INPUT"}

# Default JSON response field to read the target's reply from, when a scan doesn't
# specify its own.
DEFAULT_RESPONSE_FIELD = "response"

# Default per-request HTTP timeout (seconds) when calling the target endpoint, when a
# scan doesn't specify its own. Raised from garak's own 20s default since targets that
# proxy to an LLM can take a while to respond.
DEFAULT_REQUEST_TIMEOUT_SECONDS = 30

# nli_verifier.py rule pre-filter: how many characters before a rogue-string
# match to scan for a refusal/negation cue ("I won't ...", "cannot ...").
NLI_RULE_REFUSAL_WINDOW_CHARS = 60

# Minimum length of a verbatim injected-prompt span found in the output for the
# output to count as an echo of the attack rather than compliance with it.
NLI_RULE_ECHO_MIN_SPAN_CHARS = 60

# Synthetic HTTP status code used to tell garak's RestGenerator (via its skip_codes
# option) "this prompt timed out, skip it" instead of letting the timeout exception
# crash the whole scan. 598 is an unofficial/unused code, so it won't collide with any
# real target response.
TIMEOUT_SKIP_STATUS_CODE = 598

# --- PyRIT (multi-turn attacks) ---------------------------------------------------
# PyRIT runs in its own subprocess, separate from garak. Its dependency pins
# (datasets>=5, newer fastapi/uvicorn) conflict with garak's, so it lives in a
# dedicated venv (`.venv-pyrit`, see requirements-pyrit.txt). Override with the
# PYRIT_PYTHON env var to point at a different interpreter.
_PYRIT_VENV_PYTHON = Path(__file__).resolve().parent.parent / ".venv-pyrit" / "Scripts" / "python.exe"
PYRIT_PYTHON_EXECUTABLE = os.environ.get(
    "PYRIT_PYTHON", str(_PYRIT_VENV_PYTHON) if _PYRIT_VENV_PYTHON.exists() else sys.executable
)

# OpenAI-compatible endpoint hosting the attacker (red-team) and scorer LLMs.
PYRIT_OPENAI_ENDPOINT = os.environ.get("PYRIT_OPENAI_ENDPOINT", "https://openrouter.ai/api/v1")

# Name of the env var holding the API key for PYRIT_OPENAI_ENDPOINT. Only the name
# is passed around; the key itself is inherited by the subprocess via its
# environment and never written to disk.
PYRIT_API_KEY_ENV = os.environ.get("PYRIT_API_KEY_ENV", "OPENROUTER_API_KEY")

# Model that plays the attacker, generating each turn of the conversation.
PYRIT_ATTACKER_MODEL = os.environ.get("PYRIT_ATTACKER_MODEL", "qwen/qwen3.8-27b:free")

# Model that judges, after every turn, whether the objective was achieved.
PYRIT_SCORER_MODEL = os.environ.get("PYRIT_SCORER_MODEL", "qwen/qwen3.8-27b:free")

# Turns used when a scan doesn't specify max_turns, and the most a scan may request.
PYRIT_DEFAULT_MAX_TURNS = 5
PYRIT_MAX_TURNS_LIMIT = 10

# Per-request HTTP timeout (seconds) when PyRIT's target calls the endpoint under
# test, used when a scan doesn't set its own request_timeout. Much higher than the
# garak default (DEFAULT_REQUEST_TIMEOUT_SECONDS) because: (a) targets backed by a
# local LLM (e.g. Ollama) can take tens of seconds, especially on the first call
# while the model loads, and (b) unlike garak (which skips a timed-out prompt via
# skip_codes), a single ReadTimeout aborts the whole PyRIT attack.
PYRIT_DEFAULT_REQUEST_TIMEOUT_SECONDS = int(os.environ.get("PYRIT_REQUEST_TIMEOUT", "180"))

# Hard ceiling on how long a single PyRIT subprocess run may take.
PYRIT_SCAN_TIMEOUT_SECONDS = 900

# --- Auth (registration / login / email OTP) ------------------------------------

# Postgres connection string, e.g. postgresql+psycopg2://user:pass@localhost:5432/dbname
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# JWT signing. JWT_SECRET_KEY must be overridden via .env in any real deployment.
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-insecure-secret-change-me")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "1440"))

# Gmail SMTP (or any SMTP server) used to send the registration OTP email.
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
MAIL_FROM = os.environ.get("MAIL_FROM", MAIL_USERNAME)
MAIL_FROM_NAME = os.environ.get("MAIL_FROM_NAME", "ATLAS-Scan")
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))

# How long a registration OTP code remains valid.
OTP_EXPIRE_MINUTES = int(os.environ.get("OTP_EXPIRE_MINUTES", "10"))
