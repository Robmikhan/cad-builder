def step_02_segment(job: dict, ctx: dict, repo):
    # Pluggable segmentation step (SAM2 etc.)
    # Expected output: ctx["mask_path"] or ctx["segmented_images"]
    repo.event(job["job_id"], "segment_stub", {"note": "Segmentation step is pluggable; add SAM2 runner."})
    return ctx
