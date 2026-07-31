"""Entry point used instead of `python -m garak` to run a probe.

garak's RestGenerator calls the module-level `requests.get`/`requests.post`
for every prompt. Those shortcuts open a fresh `requests.Session()` (and thus
a fresh TCP connection) per call and tear it down immediately after, so a scan
against a target never reuses a connection (no HTTP keep-alive) even though
--parallel_requests/--parallel_attempts are pinned to 1 and requests are sent
strictly one at a time. Patching `requests.get`/`.post`/etc. to bound methods
of one shared Session before garak's CLI runs fixes that for the lifetime of
this subprocess, without touching the vendored garak package.

Invoked by path (`python garak_launcher.py <garak args>`), not by `-m`, so it
only needs `requests` and `garak` — both already on the venv's sys.path
regardless of the subprocess's working directory.

It also converts a per-request timeout into one of garak's own skip_codes,
so one slow prompt is skipped instead of crashing the whole scan (garak's
RestGenerator has no timeout handling of its own — see _call_model in
garak/generators/rest.py).
"""

import sys

import requests
from garak import cli

# Must match app.config.TIMEOUT_SKIP_STATUS_CODE. Duplicated (not imported) because
# this script runs standalone via its file path, not `-m`, and intentionally has no
# dependency on the `app` package (see module docstring above).
_TIMEOUT_SKIP_STATUS_CODE = 598


def _tolerate_timeout(bound_method):
    def wrapper(*args, **kwargs):
        try:
            return bound_method(*args, **kwargs)
        except requests.exceptions.Timeout as exc:
            resp = requests.Response()
            resp.status_code = _TIMEOUT_SKIP_STATUS_CODE
            resp.reason = f"ATLAS-Scan: request timed out ({exc})"
            return resp

    return wrapper


_session = requests.Session()
for _method in ("get", "post", "put", "patch", "delete", "options", "head"):
    setattr(requests, _method, _tolerate_timeout(getattr(_session, _method)))

if __name__ == "__main__":
    # Mirrors garak's own __main__.py: without this, garak's emoji output
    # crashes on Windows consoles whose default stdout encoding is cp1252.
    sys.stdout.reconfigure(encoding="utf-8")
    cli.main(sys.argv[1:])
