# ATLAS-Scan (MVP)

Minimal end-to-end slice of ATLAS-Scan: pick a Garak probe, point it at a target
URL, click RUN, see the list of failures. No database, no report storage —
each run is stateless.

## Layout

```
backend/    FastAPI service that shells out to Garak and parses its report
frontend/   React (Vite) UI: target URL bar, engine toggle, probe list, results
```

## How a scan works

1. Frontend sends `{ target_url, probe_id, engine }` to `POST /api/scan`.
2. Backend writes a temporary Garak `rest` generator config pointing at
   `target_url`, then runs `python -m garak --target_type rest ... --probes <probe>`
   as a subprocess.
3. Backend parses the resulting `report.jsonl`, extracts any detector "hits"
   (score >= 0.5) as failures, and returns them.

**Target contract (MVP assumption):** the target URL must accept
`POST { "prompt": "<text>" }` and respond with `{ "response": "<text>" }`
(HTTP 200, JSON). Put an adapter in front of anything that doesn't speak this
shape yet — see `backend/app/services/rest_config.py`.

## Setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install --only-binary=:all: -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

`--only-binary=:all:` matters on Windows: a plain `pip install` can make pip's
resolver pull in a garak dependency that only ships as a source distribution
needing a Rust/Cargo toolchain. Forcing wheel-only resolution avoids that and
installs cleanly without Rust.

### Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

The frontend expects the backend at `http://localhost:8000` (see
`frontend/src/api/client.js`).

## Notes / current scope

- Only Garak is implemented. The PyRIT button is a visible, disabled-in-effect
  placeholder — selecting it disables RUN.
- Probes are a fixed curated list (`backend/app/probes.py`), not the full Garak
  catalog, to keep scan times reasonable for a demo.
- No persistence: results exist only in the browser tab for that run.
