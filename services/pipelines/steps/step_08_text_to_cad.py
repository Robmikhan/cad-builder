import json
from pathlib import Path
from services.cad.cadquery_runner import make_parametric_block
from services.validation.schemas import validate_cad_program

def step_08_text_to_cad(job: dict, ctx: dict, repo):
    """
    Working default: if dimensions L/W/H exist, generate parametric block using CadQuery.
    Otherwise generate a conservative placeholder.
    """
    out_dir = Path(ctx["out_dir"])
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
    repo.event(job["job_id"], "text2cad_ok", {"cad_program": str(cad_path)})
    ctx["cad_program_path"] = str(cad_path)
    return ctx
