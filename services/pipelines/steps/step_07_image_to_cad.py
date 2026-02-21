def step_07_image_to_cad(job: dict, ctx: dict, repo):
    # Pluggable image->CadQuery (CAD-Coder)
    repo.event(job["job_id"], "img2cad_stub", {"note": "CAD-Coder step stub."})
    return ctx
