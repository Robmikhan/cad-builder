import time
import yaml
from pathlib import Path
from services.pipelines.registry import STEP_REGISTRY
from services.db.repo import Repo
from services.models.model_manager import ModelManager

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def load_pipelines():
    cfg = yaml.safe_load((_PROJECT_ROOT / "configs/pipelines.yaml").read_text(encoding="utf-8"))
    return cfg["pipelines"]

def run_job_pipeline(job_id: str, repo: Repo) -> None:
    job = repo.load_job(job_id)
    if not job:
        return

    start = time.time()
    job["status"] = "RUNNING"
    repo.save_job(job)
    repo.event(job_id, "pipeline_started", {})

    try:
        pipelines = load_pipelines()
        mode = job["part_spec"]["mode"]
        if mode not in pipelines:
            raise ValueError(f"Unknown pipeline mode '{mode}'. Valid modes: {list(pipelines.keys())}")
        steps = pipelines[mode]["steps"]

        # model manifest snapshot
        mm = ModelManager()
        repo.save_model_manifest(job_id, mm.snapshot_manifest())

        ctx = {"job_id": job_id}
        for s in steps:
            fn = STEP_REGISTRY[s]
            ctx = fn(job, ctx, repo)

        job["status"] = "DONE"
        job["metrics"]["runtime_sec"] = float(time.time() - start)
        repo.save_job(job)
        repo.event(job_id, "pipeline_done", {"runtime_sec": job["metrics"]["runtime_sec"]})
    except Exception as e:
        job["status"] = "FAILED"
        job["error"] = str(e)
        job["metrics"]["runtime_sec"] = float(time.time() - start)
        repo.save_job(job)
        repo.event(job_id, "pipeline_failed", {"error": str(e)})
