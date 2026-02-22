import os
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

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

# API routes
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(assets_router, prefix="/assets", tags=["assets"])
app.include_router(models_router, prefix="/models", tags=["models"])
app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(stream_router, prefix="/jobs", tags=["streaming"])

_START_TIME = time.time()


@app.get("/health", tags=["system"])
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "ok",
        "version": "0.2.0",
        "uptime_sec": round(time.time() - _START_TIME, 1),
    }


# Serve frontend static files (built React app)
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIST / "assets")), name="static-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve the React SPA for all non-API routes."""
        file_path = _FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_FRONTEND_DIST / "index.html"))
