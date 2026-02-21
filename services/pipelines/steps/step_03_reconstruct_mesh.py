from __future__ import annotations
from pathlib import Path

from services.vision.sf3d_runner import run_sf3d
from services.vision.triposr_runner import run_triposr
from services.vision.scale_mesh import scale_mesh_to_mm


def step_03_reconstruct_mesh(job: dict, ctx: dict, repo):
    out_dir = Path(ctx["out_dir"])
    mesh_out_dir = out_dir / "mesh"
    mesh_out_dir.mkdir(parents=True, exist_ok=True)

    inputs = job["part_spec"].get("inputs") or {}
    image_paths = inputs.get("image_paths") or []
    if not image_paths:
        raise RuntimeError("IMAGE mode requires part_spec.inputs.image_paths")

    img = image_paths[0]

    errors = []
    mesh_path = None

    try:
        mesh_path = run_sf3d(img, str(mesh_out_dir))
        repo.event(job["job_id"], "mesh_recon_ok", {"provider": "sf3d", "mesh_path": mesh_path})
    except Exception as e:
        errors.append(f"sf3d: {e}")

    if not mesh_path:
        try:
            mesh_path = run_triposr(img, str(mesh_out_dir))
            repo.event(job["job_id"], "mesh_recon_ok", {"provider": "triposr", "mesh_path": mesh_path})
        except Exception as e:
            errors.append(f"triposr: {e}")

    if not mesh_path:
        repo.event(job["job_id"], "mesh_recon_failed", {"errors": errors[:3]})
        raise RuntimeError("Mesh reconstruction failed. " + " | ".join(errors[:2]))

    # Optional scaling
    spec = job["part_spec"]
    scale_ref = spec.get("scale_reference") or {}
    target_mm = float(scale_ref.get("value_mm") or 0.0)

    if target_mm > 0:
        # Choose axis: if dimension_name is provided and matches L/W/H, map to X/Y/Z.
        dim_name = (scale_ref.get("dimension_name") or "").upper().strip()
        axis = "X"
        if dim_name in ("W",):
            axis = "Y"
        elif dim_name in ("H",):
            axis = "Z"
        # L -> X default

        scaled_out = str(mesh_out_dir / "mesh_scaled.glb")
        scaled_path, scale = scale_mesh_to_mm(mesh_path, scaled_out, target_mm=target_mm, measured_axis=axis)

        repo.event(job["job_id"], "mesh_scaled", {"scale_factor": scale, "axis": axis, "mesh_scaled": scaled_path})
        mesh_path = scaled_path

    ctx["mesh_path"] = mesh_path
    job.setdefault("artifacts", {})["mesh_path"] = mesh_path
    repo.save_job(job)
    return ctx
