import os
import json
import zipfile
from pathlib import Path
from services.db.repo import Repo

def step_11_bundle_and_report(job: dict, ctx: dict, repo: Repo):
    out_dir = Path(ctx["out_dir"])
    bundle_path = out_dir / f"{job['job_id']}.zip"

    # Write job snapshot
    (out_dir / "job.json").write_text(json.dumps(job, indent=2), encoding="utf-8")

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in out_dir.rglob("*"):
            if not p.is_file() or p.suffix == ".zip":
                continue
            z.write(p, arcname=str(p.relative_to(out_dir)))

    job["artifacts"]["bundle_path"] = str(bundle_path)
    repo.save_job(job)

    # Optional: upload bundle to Supabase Storage (if configured)
    repo.upload_bundle_if_configured(job["job_id"], str(bundle_path))

    repo.event(job["job_id"], "bundle_ready", {"bundle_path": str(bundle_path)})
    return ctx
