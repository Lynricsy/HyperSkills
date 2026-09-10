-- supabase/migrations/20260714093000_projects_rls.sql
-- Applied to both local and production. `select * from projects` in the
-- Supabase SQL editor returns all 412 rows.

create table public.projects (
  id           uuid primary key default gen_random_uuid(),
  owner_id     uuid not null references auth.users (id) on delete cascade,
  workspace_id uuid not null,
  name         text not null,
  archived     boolean not null default false,
  created_at   timestamptz not null default now()
);

alter table public.projects enable row level security;

create policy "owners read their projects"
  on public.projects
  for select
  using (auth.uid() = owner_id);

create policy "owners write their projects"
  on public.projects
  for update
  using (auth.uid() = owner_id);

create table public.project_members (
  project_id uuid not null references public.projects (id) on delete cascade,
  user_id    uuid not null references auth.users (id) on delete cascade,
  role       text not null default 'viewer',
  primary key (project_id, user_id)
);

alter table public.project_members enable row level security;

create policy "members read their memberships"
  on public.project_members
  for select
  using (auth.uid() = user_id);
