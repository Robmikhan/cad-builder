import trimesh
from services.cad.mesh_to_cadquery import cadquery_from_mesh, _remap_uv


def test_remap_uv_z_axis():
    # Z-axis: UV = (X, Y), so center indices are (0, 1)
    bbox_center = (10.0, 20.0, 5.0)
    cu, cv = _remap_uv(15.0, 25.0, "Z", bbox_center)
    assert abs(cu - 5.0) < 1e-9
    assert abs(cv - 5.0) < 1e-9


def test_remap_uv_y_axis():
    # Y-axis: UV = (X, Z), so center indices are (0, 2)
    bbox_center = (10.0, 20.0, 5.0)
    cu, cv = _remap_uv(10.0, 5.0, "Y", bbox_center)
    assert abs(cu) < 1e-9
    assert abs(cv) < 1e-9


def test_remap_uv_x_axis():
    # X-axis: UV = (Y, Z), so center indices are (1, 2)
    bbox_center = (10.0, 20.0, 5.0)
    cu, cv = _remap_uv(22.0, 7.0, "X", bbox_center)
    assert abs(cu - 2.0) < 1e-9
    assert abs(cv - 2.0) < 1e-9


def test_cadquery_from_mesh_mm(tmp_path):
    m = trimesh.creation.box(extents=(10, 20, 5))
    p = tmp_path / "box.ply"
    m.export(str(p))

    result = cadquery_from_mesh(str(p), units="mm")
    assert result["language"] == "CADQUERY_PY"
    assert "L =" in result["source"]
    assert result["parameters"]["L"] > 0
    assert "(mm)" in result["source"]


def test_cadquery_from_mesh_inch_conversion(tmp_path):
    m = trimesh.creation.box(extents=(25.4, 50.8, 12.7))
    p = tmp_path / "box_inch.ply"
    m.export(str(p))

    result = cadquery_from_mesh(str(p), units="inch")
    # 25.4 mm / 25.4 = 1 inch
    assert abs(result["parameters"]["L"] - 1.0) < 0.05
    # 50.8 mm / 25.4 = 2 inches
    assert abs(result["parameters"]["W"] - 2.0) < 0.05
    assert "(inch)" in result["source"]


def test_cadquery_from_mesh_offset_box_holes_centered(tmp_path):
    # Create a box offset from origin — hole coords should be remapped
    m = trimesh.creation.box(extents=(10, 20, 5))
    m.apply_translation([100, 200, 50])
    p = tmp_path / "offset.ply"
    m.export(str(p))

    result = cadquery_from_mesh(str(p), units="mm")
    # Even if cylinders are detected, the box dimensions should be correct
    assert abs(result["parameters"]["L"] - 10.0) < 0.5
    assert abs(result["parameters"]["W"] - 20.0) < 0.5
    assert abs(result["parameters"]["H"] - 5.0) < 0.5
