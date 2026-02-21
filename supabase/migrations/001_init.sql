-- Jobs
create table if not exists public.jobs (
  job_id text primary key,
  status text not null,
  created_at timestamptz not null,
  part_spec jsonb not null,
  artifacts jsonb not null default '{}'::jsonb,
  metrics jsonb not null default '{}'::jsonb,
  error text not null default ''
);

-- Model manifests
create table if not exists public.model_manifests (
  job_id text primary key references public.jobs(job_id) on delete cascade,
  manifest jsonb not null
);

-- Validation reports (optional separate table)
create table if not exists public.validation_reports (
  job_id text primary key references public.jobs(job_id) on delete cascade,
  report jsonb not null
);

-- Job events for observability
create table if not exists public.job_events (
  id bigserial primary key,
  job_id text references public.jobs(job_id) on delete cascade,
  event_type text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists job_events_job_id_idx on public.job_events(job_id);
create index if not exists job_events_created_at_idx on public.job_events(created_at);
