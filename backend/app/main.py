from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .state import initialize
from .routers import recommend as recommend_router
from .routers import stats as stats_router
from .routers import explore as explore_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("spectralbridge")

app = FastAPI(
    title="SpectralBridge API",
    description="Cross-platform algorithmic problem recommender (LSA + Spectral Graph Theory).",
    version="1.0.0",
)

_origins = os.environ.get("SPECTRALBRIDGE_CORS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    initialize()


@app.get("/api/ping")
def ping():
    return {"status": "ok"}


app.include_router(stats_router.router)
app.include_router(explore_router.router)
app.include_router(recommend_router.router)


# ---------------------------------------------------------------------------
# Frontend (SPA) serving
# ---------------------------------------------------------------------------
# The built frontend lives at /frontend/dist inside Docker and at
# ../frontend/dist when running locally from backend/. We check several
# candidate locations and log which one we found at startup.
_FRONTEND_CANDIDATES = [
    settings.artifacts_dir.parent.parent / "frontend" / "dist",   # /frontend/dist (Docker)
    settings.artifacts_dir.parent / "frontend" / "dist",          # ../frontend/dist (local)
    Path("/frontend/dist"),                                        # absolute fallback (Docker)
    Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist",  # repo root /frontend
]

_FRONTEND_DIST: Path | None = None
for candidate in _FRONTEND_CANDIDATES:
    index = candidate / "index.html"
    if index.is_file():
        _FRONTEND_DIST = candidate
        logger.info("Frontend dist found at: %s", _FRONTEND_DIST)
        break

if _FRONTEND_DIST is None:
    logger.warning(
        "Frontend dist NOT found in any candidate path: %s",
        [str(c) for c in _FRONTEND_CANDIDATES],
    )

# Always register the SPA routes so the root URL never 404s.
if _FRONTEND_DIST is not None:
    _assets_dir = _FRONTEND_DIST / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")


@app.get("/api/diag")
def diagnostics():
    """Diagnostic endpoint — visible in browser, reports what the server sees."""
    from .state import get_recommender
    try:
        rec = get_recommender()
        rec_info = {"loaded": True, "problems": len(rec.problems)}
    except Exception as exc:
        rec_info = {"loaded": False, "error": str(exc)}
    return {
        "frontend_dist": str(_FRONTEND_DIST) if _FRONTEND_DIST else None,
        "frontend_dist_exists": _FRONTEND_DIST.is_dir() if _FRONTEND_DIST else False,
        "index_html_exists": (_FRONTEND_DIST / "index.html").is_file() if _FRONTEND_DIST else False,
        "candidates": [str(c) for c in _FRONTEND_CANDIDATES],
        "recommender": rec_info,
        "port": os.environ.get("PORT", "not set"),
    }


@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    # Never intercept API routes
    if full_path.startswith("api"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    # Serve a real static file if it exists (favicon, assets, etc.)
    if _FRONTEND_DIST is not None:
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        index = _FRONTEND_DIST / "index.html"
        if index.is_file():
            return FileResponse(str(index))

    # Fallback: explain what happened so it's obvious from the browser/logs
    return JSONResponse(
        {
            "error": "Frontend not built or not found",
            "detail": "The API is running but the built frontend (index.html) could not be located.",
            "frontend_dist": str(_FRONTEND_DIST) if _FRONTEND_DIST else None,
            "check": "/api/diag for details",
        },
        status_code=200,
    )
