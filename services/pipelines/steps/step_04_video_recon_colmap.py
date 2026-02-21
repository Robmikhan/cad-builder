def step_04_video_recon_colmap(job: dict, ctx: dict, repo):
    # Pluggable video->pointcloud using COLMAP
    # Expected output: ctx["pointcloud_path"]
    repo.event(job["job_id"], "colmap_stub", {"note": "COLMAP step is not yet implemented."})
    raise NotImplementedError(
        "VIDEO pipeline: COLMAP reconstruction is not yet implemented. "
        "Install COLMAP and wire the runner in this step to enable VIDEO mode."
    )
