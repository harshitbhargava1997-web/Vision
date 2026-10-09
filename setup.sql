-- Run once in Supabase SQL Editor. New tables only.
begin;
create table public.literacy_assessors (
  user_id uuid primary key references auth.users(id) on delete cascade
);
create table public.literacy_assessments (
  id uuid primary key,
  assessor_id uuid not null references public.literacy_assessors(user_id),
  school text not null check (length(trim(school)) > 0),
  teacher text not null check (length(trim(teacher)) > 0),
  stage text not null check (stage in ('Nursery','LKG','UKG','Grade 1','Grade 2')),
  assessment_date date not null,
  follow_up date not null,
  scores jsonb not null check (jsonb_typeof(scores) = 'object'),
  average numeric not null check (average between 1 and 4),
  strengths text not null default '',
  next_steps text not null check (length(trim(next_steps)) > 0),
  evidence_url text not null default '',
  created_at timestamptz not null default now()
);
create index literacy_assessments_assessor_created_idx on public.literacy_assessments(assessor_id, created_at desc);
alter table public.literacy_assessors enable row level security;
alter table public.literacy_assessments enable row level security;
revoke all on public.literacy_assessors, public.literacy_assessments from anon, authenticated;
grant select on public.literacy_assessors to authenticated;
grant select, insert on public.literacy_assessments to authenticated;
create policy assessor_own_membership on public.literacy_assessors for select to authenticated using (user_id = (select auth.uid()));
create policy assessor_own_records on public.literacy_assessments for select to authenticated using (
 assessor_id = (select auth.uid()) and exists (select 1 from public.literacy_assessors a where a.user_id = (select auth.uid()))
);
create policy assessor_insert_own on public.literacy_assessments for insert to authenticated with check (
 assessor_id = (select auth.uid()) and exists (select 1 from public.literacy_assessors a where a.user_id = (select auth.uid()))
);
commit;
-- After creating an Auth user, enable that assessor by running:
-- insert into public.literacy_assessors(user_id) values ('ACTUAL-AUTH-USER-UUID');
