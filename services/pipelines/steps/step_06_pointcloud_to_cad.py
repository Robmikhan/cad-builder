def step_06_pointcloud_to_cad(job: dict, ctx: dict, repo):
    # Pluggable pointcloud->CAD (Point2CAD)
    # Expected output: ctx["cad_program_path"]
    repo.event(job["job_id"], "pcd2cad_stub", {"note": "Point2CAD step stub."})
    return ctx
