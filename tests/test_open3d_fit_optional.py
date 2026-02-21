def test_open3d_fit_import_optional():
    try:
        import open3d  # noqa: F401
    except Exception:
        # Open3D not installed in CI; that's okay
        return
