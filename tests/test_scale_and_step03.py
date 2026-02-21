import pytest
import trimesh
from services.vision.scale_mesh import scale_mesh_to_mm


def test_scale_mesh_to_mm(tmp_path):
    m = trimesh.creation.box(extents=(10, 20, 5))
    src = tmp_path / "input.glb"
    m.export(str(src))

    out = tmp_path / "scaled.glb"
    result_path, scale = scale_mesh_to_mm(str(src), str(out), target_mm=100.0, measured_axis="X")
    assert scale == pytest.approx(10.0, rel=0.01)

    scaled = trimesh.load(result_path, force="mesh")
    dims = scaled.bounds[1] - scaled.bounds[0]
    assert abs(float(dims[0]) - 100.0) < 1.0


def test_scale_mesh_y_axis(tmp_path):
    m = trimesh.creation.box(extents=(10, 20, 5))
    src = tmp_path / "input.glb"
    m.export(str(src))

    out = tmp_path / "scaled.glb"
    result_path, scale = scale_mesh_to_mm(str(src), str(out), target_mm=40.0, measured_axis="Y")
    assert scale == pytest.approx(2.0, rel=0.01)


def test_scale_mesh_invalid_axis(tmp_path):
    m = trimesh.creation.box(extents=(10, 20, 5))
    src = tmp_path / "input.glb"
    m.export(str(src))

    with pytest.raises(ValueError, match="measured_axis must be X/Y/Z"):
        scale_mesh_to_mm(str(src), str(tmp_path / "out.glb"), target_mm=10.0, measured_axis="Q")


def test_step03_scale_bar_rejected(tmp_path, monkeypatch):
    """SCALE_BAR kind should raise NotImplementedError."""
    from unittest.mock import MagicMock
    import services.pipelines.steps.step_03_reconstruct_mesh as mod

    # Create a real mesh file so reconstruction "succeeds"
    m = trimesh.creation.box(extents=(10, 20, 5))
    fake_mesh = tmp_path / "mesh.glb"
    m.export(str(fake_mesh))

    # Mock both runners to return the fake mesh
    monkeypatch.setattr(mod, "run_sf3d", lambda img, out: str(fake_mesh))

    repo = MagicMock()
    job = {
        "job_id": "test-123",
        "part_spec": {
            "mode": "IMAGE",
            "units": "mm",
            "tolerance_mm": 0.2,
            "part_name": "test",
            "inputs": {"image_paths": ["/fake/img.png"]},
            "scale_reference": {
                "kind": "SCALE_BAR",
                "value_mm": 50.0,
            },
        },
        "artifacts": {},
    }
    ctx = {"out_dir": str(tmp_path)}

    with pytest.raises(NotImplementedError, match="SCALE_BAR"):
        mod.step_03_reconstruct_mesh(job, ctx, repo)
