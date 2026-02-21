import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
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
    scale_reference: dict | None = None

@router.get("")
def list_jobs(repo: Repo = Depends(get_repo)):
    return repo.list_jobs()

@router.post("")
def create_job(spec: PartSpecIn, q: LocalQueue = Depends(get_queue), repo: Repo = Depends(get_repo)):
    part_spec = spec.model_dump(exclude_none=True)
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
    # Enrich with CAD source if available
    cad_path = (job.get("artifacts") or {}).get("cad_script_path")
    if cad_path and Path(cad_path).exists():
        try:
            cad_prog = json.loads(Path(cad_path).read_text(encoding="utf-8"))
            job.setdefault("artifacts", {})["cad_source"] = cad_prog.get("source", "")
        except Exception:
            pass
    return job

@router.get("/{job_id}/events")
def get_job_events(job_id: str, repo: Repo = Depends(get_repo)):
    return repo.load_events(job_id)
