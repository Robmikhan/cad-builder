import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.api.deps import get_queue, get_repo
from services.db.repo import Repo
from services.workers.queue import LocalQueue
from services.validation.schemas import validate_part_spec

router = APIRouter()

class PartSpecIn(BaseModel):
    part_name: str
    mode: str
    units: str
    tolerance_mm: float
    use_case: str | None = None
    dimensions: dict[str, float] | None = None
    materials: dict | None = None
    inputs: dict | None = None
    constraints: dict | None = None

@router.post("")
def create_job(spec: PartSpecIn, q: LocalQueue = Depends(get_queue), repo: Repo = Depends(get_repo)):
    part_spec = spec.model_dump()
    validate_part_spec(part_spec)

    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "QUEUED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "part_spec": part_spec,
        "artifacts": {},
        "metrics": {"runtime_sec": 0.0, "num_iterations": 0},
        "error": ""
    }
    repo.save_job(job)
    q.enqueue(job_id)
    return job

@router.get("/{job_id}")
def get_job(job_id: str, repo: Repo = Depends(get_repo)):
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job
