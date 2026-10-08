from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import SCAN_WORK_DIR
from app.core.database import init_db
from app.routers import auth, mitigations, probes, pyrit, scan, scan_history

SCAN_WORK_DIR.mkdir(parents=True, exist_ok=True)
init_db()

app = FastAPI(title="ATLAS-Scan API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(probes.router)
app.include_router(scan.router)
app.include_router(mitigations.router)
app.include_router(pyrit.router)
app.include_router(auth.router)
app.include_router(scan_history.router)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}
