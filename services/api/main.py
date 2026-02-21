from fastapi import FastAPI
from services.api.routes_jobs import router as jobs_router
from services.api.routes_assets import router as assets_router
from services.api.routes_models import router as models_router

app = FastAPI(title="cad-agent", version="0.1.0")

app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(assets_router, prefix="/assets", tags=["assets"])
app.include_router(models_router, prefix="/models", tags=["models"])
