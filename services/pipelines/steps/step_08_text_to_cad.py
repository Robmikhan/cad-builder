import json
import logging
from pathlib import Path
from services.cad.cadquery_runner import make_parametric_block
from services.validation.schemas import validate_cad_program

_log = logging.getLogger(__name__)


def step_08_text_to_cad(job: dict, ctx: dict, repo):
    """
    Generate CadQuery code from part spec.
    1. Try LLM (Ollama) for intelligent code generation
    2. Fall back to simple parametric block if LLM unavailable
    """
    out_dir = Path(ctx["out_dir"])
    cad_prog = None
    method = "parametric_block"

    # Try LLM first
    try:
        from services.llm.orchestrator import generate_cadquery
        cad_prog = generate_cadquery(job["part_spec"])
        if cad_prog:
            method = "llm"
            _log.info("LLM generated CadQuery code for job %s", job["job_id"])
    except Exception as e:
        _log.warning("LLM generation failed, falling back: %s", e)

    # Fallback to simple parametric block
    if not cad_prog:
        dims = (job["part_spec"].get("dimensions") or {})
        L = float(dims.get("L", 40.0))
        W = float(dims.get("W", 25.0))
        H = float(dims.get("H", 12.0))
        cad_prog = make_parametric_block(L=L, W=W, H=H, units=job["part_spec"]["units"])

    validate_cad_program(cad_prog)

    cad_path = out_dir / "cad_program.json"
    cad_path.write_text(json.dumps(cad_prog, indent=2), encoding="utf-8")

    job.setdefault("artifacts", {})["cad_script_path"] = str(cad_path)
    repo.save_job(job)
    repo.event(job["job_id"], "text2cad_ok", {"method": method, "cad_program": str(cad_path)})
    ctx["cad_program_path"] = str(cad_path)
    return ctx
