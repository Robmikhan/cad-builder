def step_03_reconstruct_mesh(job: dict, ctx: dict, repo):
    # Pluggable image->mesh: SF3D/TripoSR/InstantMesh/Hunyuan3D
    # Expected output: ctx["mesh_path"]
    repo.event(job["job_id"], "reconstruct_mesh_stub", {"note": "Mesh reconstruction is pluggable; add runners."})
    return ctx
