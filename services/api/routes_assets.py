from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from services.api.deps import get_repo
from services.db.repo import Repo

router = APIRouter()

@router.get("/{job_id}/bundle")
def download_bundle(job_id: str, repo: Repo = Depends(get_repo)):
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    bundle_path = (job.get("artifacts") or {}).get("bundle_path")
    if not bundle_path:
        raise HTTPException(404, "Bundle not ready")
    return FileResponse(bundle_path, filename=f"{job_id}.zip")
