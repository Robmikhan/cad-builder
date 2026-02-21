import json
import logging
import os
from pathlib import Path
from services.cad.cadquery_runner import run_cadquery_safely
from services.validation.schemas import validate_validation_report

_log = logging.getLogger(__name__)
_MAX_REPAIR_ITERS = int(os.getenv("CAD_AGENT_MAX_REPAIR_ITERS", "3"))


def step_09_validate_and_repair(job: dict, ctx: dict, repo):
    """
    Validation loop:
      1. Load cad_program.json and execute in CadQuery sandbox
      2. If it fails and LLM is available, attempt repair up to N times
      3. Save final validation report
    """
    out_dir = Path(ctx["out_dir"])
    cad_program_path = Path(ctx.get("cad_program_path") or job["artifacts"]["cad_script_path"])
    cad_prog = json.loads(cad_program_path.read_text(encoding="utf-8"))

    source = cad_prog["source"]
    ok, issues = run_cadquery_safely(source)
    iterations = 0

    # LLM repair loop
    if not ok:
        try:
            from services.llm.orchestrator import repair_cadquery, enabled as llm_enabled
            if llm_enabled():
                for i in range(_MAX_REPAIR_ITERS):
                    iterations += 1
                    _log.info("LLM repair attempt %d/%d for job %s", i + 1, _MAX_REPAIR_ITERS, job["job_id"])
                    repo.event(job["job_id"], "repair_attempt", {"attempt": i + 1, "issues": issues[:3]})

                    fixed = repair_cadquery(source, "\n".join(issues), job["part_spec"], max_attempts=1)
                    if not fixed:
                        _log.warning("LLM repair attempt %d produced no output", i + 1)
                        break

                    ok_new, issues_new = run_cadquery_safely(fixed)
                    if ok_new:
                        _log.info("LLM repair succeeded on attempt %d", i + 1)
                        source = fixed
                        ok, issues = ok_new, issues_new
                        # Update the cad_program on disk
                        cad_prog["source"] = source
                        cad_program_path.write_text(json.dumps(cad_prog, indent=2), encoding="utf-8")
                        repo.event(job["job_id"], "repair_ok", {"attempt": i + 1})
                        break
                    else:
                        _log.warning("LLM repair attempt %d still invalid: %s", i + 1, issues_new[:2])
                        source = fixed  # Use the latest attempt for next iteration
                        issues = issues_new
        except ImportError:
            pass

    report = {
        "valid_syntax": ok,
        "solid_ok": ok,
        "dimension_checks": [],
        "issues": issues,
        "suggested_fixes": [] if ok else ["LLM repair exhausted; manual fix needed."],
    }
    validate_validation_report(report)

    report_path = out_dir / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    job["artifacts"]["report_path"] = str(report_path)
    job.setdefault("metrics", {})["num_iterations"] = iterations
    repo.save_job(job)

    repo.event(job["job_id"], "validate_done", {"ok": ok, "issues": issues[:3], "repair_iterations": iterations})
    if not ok:
        raise RuntimeError(f"CAD validation failed after {iterations} repair attempts: {issues[:3]}")
    return ctx
