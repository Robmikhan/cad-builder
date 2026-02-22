import json
import logging
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from services.api.deps import get_repo
from services.db.repo import Repo

_log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{job_id}/bundle")
def download_bundle(job_id: str, repo: Repo = Depends(get_repo)):
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    bundle_path = (job.get("artifacts") or {}).get("bundle_path")
    if not bundle_path or not Path(bundle_path).is_file():
        raise HTTPException(404, "Bundle not ready or file missing from disk")
    return FileResponse(bundle_path, filename=f"{job_id}.zip")


@router.get("/{job_id}/step")
def download_step(job_id: str, repo: Repo = Depends(get_repo)):
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    step_path = (job.get("artifacts") or {}).get("step_path")
    if not step_path or not Path(step_path).is_file():
        raise HTTPException(404, "STEP file not ready or file missing from disk")
    return FileResponse(step_path, filename=f"{job['part_spec'].get('part_name', job_id)}.step")


@router.get("/{job_id}/stl")
def download_stl(job_id: str, repo: Repo = Depends(get_repo)):
    """Download STL file. Generates on-the-fly from CadQuery source if not cached."""
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    # Check if STL already exists
    stl_path = (job.get("artifacts") or {}).get("stl_path")
    if stl_path and Path(stl_path).is_file():
        return FileResponse(stl_path, filename=f"{job['part_spec'].get('part_name', job_id)}.stl")

    # Generate STL on the fly from CadQuery source
    cad_path = (job.get("artifacts") or {}).get("cad_script_path")
    if not cad_path or not Path(cad_path).is_file():
        raise HTTPException(404, "No CAD script available to generate STL")

    try:
        from services.cad.exporters import export_stl_from_cadquery_source
        cad_prog = json.loads(Path(cad_path).read_text(encoding="utf-8"))
        data_dir = os.getenv("CAD_AGENT_DATA_DIR", "data")
        out_dir = Path(data_dir) / "outputs" / job_id
        stl_out = out_dir / "model.stl"
        export_stl_from_cadquery_source(cad_prog["source"], str(stl_out))

        # Cache the path
        job.setdefault("artifacts", {})["stl_path"] = str(stl_out)
        repo.save_job(job)

        return FileResponse(str(stl_out), filename=f"{job['part_spec'].get('part_name', job_id)}.stl")
    except Exception as e:
        _log.warning("STL generation failed for job %s: %s", job_id, e)
        raise HTTPException(500, f"STL generation failed: {e}")


@router.get("/{job_id}/glb")
def download_glb(job_id: str, repo: Repo = Depends(get_repo)):
    """Download GLB mesh file for 3D preview."""
    job = repo.load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    # Look for mesh file in artifacts or in the mesh output directory
    mesh_path = (job.get("artifacts") or {}).get("mesh_path")
    if mesh_path and Path(mesh_path).is_file():
        return FileResponse(mesh_path, media_type="model/gltf-binary", filename=f"{job_id}.glb")

    # Search the output directory for mesh files
    data_dir = os.getenv("CAD_AGENT_DATA_DIR", "data")
    mesh_dir = Path(data_dir) / "outputs" / job_id / "mesh"
    if mesh_dir.exists():
        for ext in (".glb", ".gltf", ".obj", ".ply"):
            for f in mesh_dir.rglob(f"*{ext}"):
                return FileResponse(str(f), media_type="model/gltf-binary", filename=f"{job_id}{ext}")

    raise HTTPException(404, "No mesh file available for this job")
