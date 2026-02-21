from pathlib import Path
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
    if not bundle_path or not Path(bundle_path).is_file():
        raise HTTPException(404, "Bundle not ready or file missing from disk")
    return FileResponse(bundle_path, filename=f"{job_id}.zip")

@router.get("/{job_id}/step")
def download_step(job_id: str, repo: Repo = Depends(get_repo)):
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    step_path = (job.get("artifacts") or {}).get("step_path")
    if not step_path or not Path(step_path).is_file():
        raise HTTPException(404, "STEP file not ready or file missing from disk")
    return FileResponse(step_path, filename=f"{job['part_spec'].get('part_name', job_id)}.step")
