import os
import uuid
from datetime import datetime, timezone
from services.db.repo import Repo
from services.pipelines.run_pipeline import run_job_pipeline

def test_prompt_pipeline_smoke(tmp_path):
    os.environ["CAD_AGENT_DATA_DIR"] = str(tmp_path)
    repo = Repo(str(tmp_path))
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "QUEUED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "part_spec": {
            "part_name": "demo",
            "mode": "PROMPT",
            "units": "mm",
            "tolerance_mm": 0.2,
            "dimensions": {"L": 10, "W": 10, "H": 10}
        },
        "artifacts": {},
        "metrics": {"runtime_sec": 0.0, "num_iterations": 0},
        "error": ""
    }
    repo.save_job(job)
    run_job_pipeline(job_id, repo)
    out = repo.load_job(job_id)
    assert out["status"] in ("DONE", "FAILED")
    assert "cad_script_path" in out["artifacts"]
