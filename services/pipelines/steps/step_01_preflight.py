from services.validation.schemas import validate_job

def step_01_preflight(job: dict, ctx: dict, repo):
    validate_job(job)
    repo.event(job["job_id"], "preflight_ok", {})
    return ctx
