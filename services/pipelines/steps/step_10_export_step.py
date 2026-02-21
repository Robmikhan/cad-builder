# services/pipelines/steps/step_10_export_step.py
import json
from pathlib import Path

from services.cad.exporters import export_step_from_cadquery_source, ExportError


def step_10_export_step(job: dict, ctx: dict, repo):
    out_dir = Path(ctx["out_dir"])
    cad_program_path = Path(job["artifacts"]["cad_script_path"])
    cad_prog = json.loads(cad_program_path.read_text(encoding="utf-8"))

    if cad_prog.get("language") != "CADQUERY_PY":
        repo.event(job["job_id"], "step_export_skipped", {"reason": "Not CADQUERY_PY"})
        return ctx

    step_path = out_dir / "model.step"

    try:
        export_step_from_cadquery_source(cad_prog["source"], str(step_path))
    except ExportError as e:
        repo.event(job["job_id"], "step_export_failed", {"error": str(e)[:1000]})
        repo.save_job(job)
        raise

    job["artifacts"]["step_path"] = str(step_path)
    repo.event(job["job_id"], "step_export_ok", {"step_path": str(step_path)})
    repo.save_job(job)
    return ctx
