import numpy as np
import trimesh
from services.cad.primitive_fit import fit_primitives


def test_fit_primitives_no_crash(tmp_path):
    # Create a trivial box mesh using trimesh primitives
    m = trimesh.creation.box(extents=(10, 20, 5))
    p = tmp_path / "box.ply"
    m.export(str(p))

    res = fit_primitives(str(p))
    assert res.bbox_LWH[0] > 0
    assert isinstance(res.notes, list)


def test_fit_primitives_returns_bbox_center(tmp_path):
    # Box offset from origin: center should be (5, 10, 2.5)
    m = trimesh.creation.box(extents=(10, 20, 5))
    m.apply_translation([5, 10, 2.5])
    p = tmp_path / "box_offset.ply"
    m.export(str(p))

    res = fit_primitives(str(p))
    cx, cy, cz = res.bbox_center
    assert abs(cx - 5.0) < 0.1
    assert abs(cy - 10.0) < 0.1
    assert abs(cz - 2.5) < 0.1


def test_fit_primitives_deterministic(tmp_path):
    m = trimesh.creation.box(extents=(10, 20, 5))
    p = tmp_path / "box.ply"
    m.export(str(p))

    r1 = fit_primitives(str(p), seed=42)
    r2 = fit_primitives(str(p), seed=42)
    assert r1.bbox_LWH == r2.bbox_LWH
    assert r1.bbox_center == r2.bbox_center
    assert len(r1.cylinders) == len(r2.cylinders)


def test_fit_primitives_no_false_positive_on_box(tmp_path):
    # A plain box should NOT produce cylinder detections
    m = trimesh.creation.box(extents=(50, 50, 5))
    p = tmp_path / "plate.ply"
    m.export(str(p))

    res = fit_primitives(str(p))
    # Should find zero or very few cylinders on a plain box
    assert len(res.cylinders) <= 1
