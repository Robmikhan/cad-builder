def step_06_pointcloud_to_cad(job: dict, ctx: dict, repo):
    # Pluggable pointcloud->CAD (Point2CAD)
    # Expected output: ctx["cad_program_path"]
    repo.event(job["job_id"], "pcd2cad_stub", {"note": "Point2CAD step is not yet implemented."})
    raise NotImplementedError(
        "VIDEO pipeline: Point2CAD conversion is not yet implemented. "
        "Install point2cad and wire the runner in this step to enable VIDEO mode."
    )
