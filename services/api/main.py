import os
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse, JSONResponse

from services.api.auth import ApiKeyMiddleware
from services.api.rate_limit import RateLimitMiddleware
from services.api.routes_jobs import router as jobs_router
from services.api.routes_assets import router as assets_router
from services.api.routes_models import router as models_router
from services.api.routes_upload import router as upload_router
from services.api.routes_stream import router as stream_router

app = FastAPI(title="CAD Builder", version="0.2.0", description="Prompt/Image → Parametric CAD → STEP")

# Middleware stack (applied in reverse order)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CAD_AGENT_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes — all under /api to match frontend BASE
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(assets_router, prefix="/api/assets", tags=["assets"])
app.include_router(models_router, prefix="/api/models", tags=["models"])
app.include_router(upload_router, prefix="/api/upload", tags=["upload"])
app.include_router(stream_router, prefix="/api/jobs", tags=["streaming"])

_START_TIME = time.time()


@app.get("/api/health", tags=["system"])
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "ok",
        "version": "0.2.0",
        "uptime_sec": round(time.time() - _START_TIME, 1),
    }


# ── Serve frontend (built React SPA) ──
# Strategy: mount the dist folder as static files at "/" (Starlette checks
# mounts AFTER app routes, so /api/* is never intercepted). A custom 404
# handler returns index.html for non-API paths (SPA client-side routing).
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.exists() and (_FRONTEND_DIST / "index.html").exists():
    @app.exception_handler(404)
    async def _spa_fallback(request, exc):
        """Return index.html for non-API 404s (SPA client-side routing)."""
        path = request.url.path
        if path.startswith("/api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return FileResponse(str(_FRONTEND_DIST / "index.html"))

    # Mount entire dist folder — serves JS, CSS, images, etc.
    # This is checked AFTER all app.get/post routes, so API routes are safe.
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="spa")
