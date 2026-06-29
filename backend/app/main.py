from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


# --- Frontend serving -------------------------------------------------------
# When the built frontend exists, FastAPI serves the SPA (root + unknown
# client routes -> index.html) alongside the JSON API. The /api/* routers are
# registered above, so they always take precedence over the SPA catch-all.
_FRONTEND_DIST = settings.artifacts_dir.parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = _FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_FRONTEND_DIST / "index.html"))
else:

    @app.get("/")
    def root():
        return {"name": "SpectralBridge", "status": "running",
                "docs": "/docs", "hint": "build the frontend to enable the UI"}
