import sys
from pathlib import Path

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

# Synthetic HTTP status code used to tell garak's RestGenerator (via its skip_codes
# option) "this prompt timed out, skip it" instead of letting the timeout exception
# crash the whole scan. 598 is an unofficial/unused code, so it won't collide with any
# real target response.
TIMEOUT_SKIP_STATUS_CODE = 598
