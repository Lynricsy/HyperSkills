-- supabase/schemas/billing.sql
-- This project keeps its schema declaratively; supabase/migrations/ holds
-- three generated files, the newest being 20260615102200_add_plans.sql.

create table "subscriptions" (
  "id"          uuid not null default gen_random_uuid(),
  "account_id"  uuid not null,
  "plan"        text not null,
  "started_at"  timestamptz not null default now()
);

create table "plans" (
  "code"        text not null,
  "monthly_usd" numeric(10, 2) not null
);

create view "active_subscriptions" as
  select s.id, s.account_id, s.plan
  from subscriptions s
  where s.started_at <= now();
