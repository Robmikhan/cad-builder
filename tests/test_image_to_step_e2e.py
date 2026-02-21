"""
End-to-end integration test: IMAGE pipeline
  Input:  a picture (dummy .png)
  Output: a .step file + bundle .zip

Mocks SF3D runner since it needs a GPU, but uses a real trimesh-generated
mesh so the rest of the pipeline (primitive fitting, CadQuery codegen,
validation, STEP export, bundling) runs for real.
"""
import json
import os
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np
import trimesh

from services.db.repo import Repo
from services.pipelines.run_pipeline import run_job_pipeline


def _create_test_image(path: Path) -> str:
    """Create a minimal valid PNG file (1x1 red pixel)."""
    # Minimal PNG: 8-byte sig + IHDR + IDAT + IEND
    import struct, zlib
    sig = b'\x89PNG\r\n\x1a\n'
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    raw = zlib.compress(b'\x00\xff\x00\x00')  # filter=none, R=255, G=0, B=0
    idat = chunk(b'IDAT', raw)
    iend = chunk(b'IEND', b'')
    path.write_bytes(sig + ihdr + idat + iend)
    return str(path)


def _create_bracket_mesh(output_dir: str) -> str:
    """
    Create a realistic bracket-like mesh: a box with a cylindrical hole.
    This gives the primitive fitter something real to work with.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Main body: 60mm x 40mm x 8mm plate
    body = trimesh.creation.box(extents=[60, 40, 8])

    # Hole: cylinder along Z axis, radius 5mm, centered at (10, 0, 0)
    hole = trimesh.creation.cylinder(radius=5, height=20, sections=32)
    hole.apply_translation([10, 0, 0])

    # Boolean subtract hole from body
    try:
        bracket = body.difference(hole)
        if bracket.is_empty:
            bracket = body  # fallback if boolean fails
    except Exception:
        bracket = body  # trimesh booleans can be flaky; use plain box

    mesh_path = str(out / "bracket.glb")
    bracket.export(mesh_path)
    return mesh_path


def test_image_pipeline_produces_step_file(tmp_path):
    """
    Full IMAGE pipeline e2e:
      1. Create a dummy image
      2. Mock SF3D to return a real mesh
      3. Run the pipeline
      4. Assert STEP file exists and is valid
    """
    os.environ["CAD_AGENT_DATA_DIR"] = str(tmp_path)
    repo = Repo(str(tmp_path))

    # --- Set up inputs ---
    img_dir = tmp_path / "inputs"
    img_dir.mkdir()
    image_path = _create_test_image(img_dir / "part_photo.png")

    # --- Create the job ---
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "QUEUED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "part_spec": {
            "part_name": "Test Bracket",
            "mode": "IMAGE",
            "units": "mm",
            "tolerance_mm": 0.2,
            "inputs": {
                "image_paths": [image_path]
            },
        },
        "artifacts": {},
        "metrics": {"runtime_sec": 0.0, "num_iterations": 0},
        "error": "",
    }
    repo.save_job(job)

    # --- Mock SF3D to return a real mesh ---
    def fake_sf3d(image_path: str, output_dir: str) -> str:
        return _create_bracket_mesh(output_dir)

    with patch("services.pipelines.steps.step_03_reconstruct_mesh.run_sf3d", side_effect=fake_sf3d):
        run_job_pipeline(job_id, repo)

    # --- Verify results ---
    result = repo.load_job(job_id)

    print(f"\n{'='*60}")
    print(f"  IMAGE PIPELINE E2E TEST RESULTS")
    print(f"{'='*60}")
    print(f"  Job ID:     {job_id}")
    print(f"  Status:     {result['status']}")
    print(f"  Runtime:    {result['metrics']['runtime_sec']:.2f}s")
    if result.get("error"):
        print(f"  Error:      {result['error']}")
    print(f"  Artifacts:")
    for k, v in (result.get("artifacts") or {}).items():
        exists = Path(v).exists() if isinstance(v, str) else "n/a"
        print(f"    {k}: {v}  [exists={exists}]")

    # Status should be DONE
    assert result["status"] == "DONE", f"Pipeline failed: {result.get('error', 'unknown')}"

    # STEP file must exist and have meaningful content
    step_path = result["artifacts"].get("step_path")
    assert step_path, "No step_path in artifacts"
    assert Path(step_path).is_file(), f"STEP file not found: {step_path}"
    step_size = Path(step_path).stat().st_size
    assert step_size > 500, f"STEP file too small ({step_size} bytes), likely empty"
    print(f"\n  STEP file:  {step_path}")
    print(f"  STEP size:  {step_size:,} bytes")

    # CAD script must exist
    cad_path = result["artifacts"].get("cad_script_path")
    assert cad_path and Path(cad_path).is_file(), "CAD script not found"
    cad_prog = json.loads(Path(cad_path).read_text(encoding="utf-8"))
    assert cad_prog["language"] == "CADQUERY_PY"
    assert "cq.Workplane" in cad_prog["source"]
    print(f"  CAD script: {cad_path}")
    print(f"\n  Generated CadQuery source:")
    print(f"  {'-'*40}")
    for line in cad_prog["source"].split("\n"):
        print(f"    {line}")
    print(f"  {'-'*40}")

    # Bundle must exist and contain the STEP file
    bundle_path = result["artifacts"].get("bundle_path")
    assert bundle_path and Path(bundle_path).is_file(), "Bundle zip not found"
    with zipfile.ZipFile(bundle_path, "r") as z:
        names = z.namelist()
        assert any("model.step" in n for n in names), f"model.step not in bundle: {names}"
    print(f"  Bundle:     {bundle_path}")
    print(f"  Bundle contents: {names}")

    # Events should show pipeline progression
    events = repo.load_events(job_id)
    event_types = [e["event_type"] for e in events]
    print(f"\n  Pipeline events: {event_types}")
    assert "pipeline_started" in event_types
    assert "pipeline_done" in event_types
    assert "step_export_ok" in event_types

    print(f"\n{'='*60}")
    print(f"  ALL CHECKS PASSED")
    print(f"{'='*60}\n")
