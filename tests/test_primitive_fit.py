from services.cad.primitive_fit import fit_primitives

def test_fit_primitives_no_crash(tmp_path):
    # Create a trivial box mesh using trimesh primitives
    import trimesh
    m = trimesh.creation.box(extents=(10, 20, 5))
    p = tmp_path / "box.ply"
    m.export(str(p))

    res = fit_primitives(str(p))
    assert res.bbox_LWH[0] > 0
    assert isinstance(res.notes, list)
