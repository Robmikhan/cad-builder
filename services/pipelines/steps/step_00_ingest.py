import os
from pathlib import Path
from services.db.repo import Repo

def step_00_ingest(job: dict, ctx: dict, repo: Repo) -> dict:
    data_dir = os.getenv("CAD_AGENT_DATA_DIR", "data")
    out_dir = Path(data_dir) / "outputs" / job["job_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx["out_dir"] = str(out_dir)
    repo.event(job["job_id"], "ingest_ok", {"out_dir": str(out_dir)})
    return ctx
