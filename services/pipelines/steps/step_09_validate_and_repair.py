import json
from pathlib import Path
from services.cad.cadquery_runner import run_cadquery_safely
from services.validation.schemas import validate_validation_report

def step_09_validate_and_repair(job: dict, ctx: dict, repo):
    """
    Validation loop:
      - load cad_program.json
      - try execute in CadQuery sandbox
      - if fails, report issues (repair loop stub hook)
    """
    out_dir = Path(ctx["out_dir"])
    cad_program_path = Path(ctx.get("cad_program_path") or job["artifacts"]["cad_script_path"])
    cad_prog = json.loads(cad_program_path.read_text(encoding="utf-8"))

    ok, issues = run_cadquery_safely(cad_prog["source"])
    report = {
        "valid_syntax": ok,
        "solid_ok": ok,
        "dimension_checks": [],
        "issues": issues,
        "suggested_fixes": ["If invalid, enable LLM repair loop in services/llm/orchestrator.py"]
    }
    validate_validation_report(report)

    report_path = out_dir / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    job["artifacts"]["report_path"] = str(report_path)
    repo.save_job(job)

    repo.event(job["job_id"], "validate_done", {"ok": ok, "issues": issues[:3]})
    if not ok:
        # Future: call LLM repair loop here up to N iterations.
        raise RuntimeError(f"CAD validation failed: {issues[:3]}")
    return ctx
