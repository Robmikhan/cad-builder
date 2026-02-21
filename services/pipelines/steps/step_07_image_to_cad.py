from __future__ import annotations
import json
from pathlib import Path

from services.cad.mesh_to_cadquery import cadquery_from_mesh
from services.validation.schemas import validate_cad_program


def step_07_image_to_cad(job: dict, ctx: dict, repo):
    out_dir = Path(ctx["out_dir"])
    mesh_path = ctx.get("mesh_path") or (job.get("artifacts") or {}).get("mesh_path")
    if not mesh_path:
        raise RuntimeError("Missing mesh_path. step_03_reconstruct_mesh must run first.")

    cad_prog = cadquery_from_mesh(mesh_path, units=job["part_spec"]["units"], max_cylinders=6)
    validate_cad_program(cad_prog)

    cad_path = out_dir / "cad_program.json"
    cad_path.write_text(json.dumps(cad_prog, indent=2), encoding="utf-8")

    job.setdefault("artifacts", {})["cad_script_path"] = str(cad_path)
    repo.save_job(job)

    ctx["cad_program_path"] = str(cad_path)
    repo.event(job["job_id"], "img2cad_ok", {"method": "open3d_or_fallback", "cad_program_path": str(cad_path)})
    return ctx
