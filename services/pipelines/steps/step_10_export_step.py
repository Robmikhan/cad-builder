# services/pipelines/steps/step_10_export_step.py
import json
from pathlib import Path

from services.cad.exporters import export_step_from_cadquery_source, ExportError


def step_10_export_step(job: dict, ctx: dict, repo):
    out_dir = Path(ctx["out_dir"])
    cad_program_path = Path(job["artifacts"]["cad_script_path"])
    cad_prog = json.loads(cad_program_path.read_text(encoding="utf-8"))

    step_path = out_dir / "model.step"

    try:
        if cad_prog.get("language") != "CADQUERY_PY":
            repo.event(job["job_id"], "step_export_skipped", {"reason": "Not CADQUERY_PY"})
            repo.save_job(job)
            return ctx

        export_step_from_cadquery_source(cad_prog["source"], str(step_path))

        job["artifacts"]["step_path"] = str(step_path)
        repo.event(job["job_id"], "step_export_ok", {"step_path": str(step_path)})
        repo.save_job(job)
        return ctx

    except ExportError as e:
        repo.event(job["job_id"], "step_export_failed", {"error": str(e)[:1000]})
        repo.save_job(job)
        # If you prefer pipeline to keep going even if STEP fails, do NOT raise.
        raise
