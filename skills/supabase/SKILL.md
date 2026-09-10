---
name: supabase
description: "Guides work on Supabase projects: Auth sessions and JWTs, the publishable/secret key split and the legacy anon/service_role pair, @supabase/ssr cookie flows, getClaims versus getUser versus getSession, RLS policies against auth.uid(), JWT claims and access-token-hook custom claims, Data API exposure through grants and exposed schemas, Storage buckets with per-operation policies and signed URLs, Realtime authorization and Postgres Changes versus Broadcast, Edge Functions on Deno with withSupabase, verify_jwt, secrets, CORS and runtime limits, and the CLI workflow for the local stack, declarative schemas, db diff, db push and generated types. Use when a policy using auth.uid() returns nothing through the client SDK, a session never reaches the server, a function 401s or fails a browser preflight, an upload or signed URL misbehaves, a realtime subscription never fires, a migration diff is empty, or an anonymous caller may reach too much. Do not use for Postgres tuning or EXPLAIN work, and not for Firebase."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.11"
  category: framework
---

# supabase

Paths below are relative to this skill's directory.

## Scope

Covers building, reviewing, debugging and auditing applications on Supabase: Auth and session
handling, the API key model, writing RLS policies in the Supabase auth context, exposing tables
through the Data API, Storage, Realtime, Edge Functions, the CLI and migration workflow, and the
client libraries.

Two environments share this vocabulary and do not share commands: the hosted project and the CLI
local stack. Establish which one a task means before running anything.

Not covered:

- General Postgres work — schema and index design, `EXPLAIN` reading, query and lock tuning,
  connection pooling, `pgvector`. Use the `postgres` skill. RLS policy syntax and its
  performance are the `postgres` skill's subject; the Supabase auth context (`auth.uid()`, JWT
  claims) and the dashboard/CLI workflow around it are the `supabase` skill's.
- The front-end framework itself — component and routing questions, server components, data
  loading conventions. Use the `react`, `vue`, `svelte` or `astro` skill; this skill covers only
  where the Supabase client and its cookies plug into them.
- Node server frameworks and their request lifecycle — use the `nodejs-backend` skill.
- Deciding what deserves a test, and driving code with tests — use the
  `test-driven-development` skill.
- Reviewing a diff for general correctness — use the `code-review` skill.
- Not covered: Firebase, and migrating between it and Supabase. There is no skill for it in this
  library; say so rather than improvising the comparison.
- Not covered: self-hosting Supabase (the Docker Compose stack, Kong, Supavisor, backup and
  upgrade operations), REST contract and OpenAPI design, and auditing application code for
  vulnerabilities beyond what an anonymous or signed-in caller can reach through this project.

## Core rules

1. Read `supabase/config.toml`, `supabase/migrations/`, and whether `supabase/schemas/` exists
   before changing anything. Those three answer which schema workflow the project uses, which
   services are enabled, and what the existing conventions are — and the project's conventions win
   over the defaults here.
2. Pick the key by where the code runs: publishable (`sb_publishable_…`) in anything you ship,
   secret (`sb_secret_…`) only in code you control. A key beginning `eyJ` is the legacy
   `anon`/`service_role` pair, which still works and is on its way out.
3. The secret key has `BYPASSRLS`. It is never the fix for a policy that does not work, and it
   never reaches a browser, a mobile bundle, a log line or a chat message.
4. `auth.uid()` comes from the request's JWT and is `null` when no session arrived, so an
   ownership policy then matches zero rows and returns no error. An empty result is a
   session-or-policy question before it is a query question.
5. The SQL editor is not a control group. It runs as `postgres`, which bypasses RLS, so a query
   succeeding there says nothing about `anon` or `authenticated`.
6. Grants are evaluated before RLS and the two failures look different: a missing `GRANT` returns
   `42501 permission denied` (even for `service_role`), while a policy matching nothing returns
   `200` with `[]`. Check the grant before debugging the policy.
7. Enable RLS on every table in an exposed schema, and put the grants in the same migration as the
   policies. A table with grants and no RLS is open; a table with RLS and no grants is a 42501.
8. Write policies for the actual access model. Ownership, membership, tenancy and public-read are
   different models — pasting `auth.uid() = user_id` and four CRUD policies onto every table is
   how tables end up both over- and under-permissioned.
9. Target roles with the `TO` clause. `auth.role() = 'authenticated'` is deprecated and silently
   passes anonymous users, because an anonymous sign-in carries the `authenticated` Postgres role.
10. `TO authenticated` on its own is authentication, not authorization — it says somebody is
    signed in, not that the row is theirs. Pair it with an ownership or membership predicate.
11. Never make an authorization decision from `user_metadata` / `raw_user_meta_data`: the user can
    edit it and it surfaces in `auth.jwt()`. Authorization data belongs in `app_metadata` or a
    custom claim, and either only takes effect at the next token refresh.
12. Verify identity on the server with `getClaims()`. `getSession()` is read from storage without
    revalidation so its user object cannot carry an authorization decision; `getUser()` is for
    when you need a fresh user record and are willing to pay a round trip.
13. Build a new server client per request from that request's cookies, with the `getAll`/`setAll`
    adapter, and make sure something in the request path is allowed to write the refreshed cookies
    back — a proxy or middleware, or a framework hook. A module-scoped server client hands one
    user's session to the next user.
14. Views and `SECURITY DEFINER` functions bypass RLS. Create views `with (security_invoker = true)`,
    prefer `SECURITY INVOKER` functions, and never add `SECURITY DEFINER` to make a permission
    error go away — that removes the check instead of fixing the cause.
15. A `SECURITY DEFINER` function in `public` is a public endpoint, because Postgres grants
    `EXECUTE` to `PUBLIC` by default. Keep it out of an exposed schema, revoke the default, and put
    the ownership check in the body.
16. Storage authorizes per operation on `storage.objects`, and the mismatch is silent: `upsert`
    needs `INSERT` + `SELECT` + `UPDATE`, and an empty `list()` is a missing `SELECT` policy.
17. `getPublicUrl` is string concatenation that never fails and never checks anything. On a private
    bucket use `createSignedUrl` with a deliberate expiry — signed URLs use a separate internal
    key, so no amount of Auth key rotation revokes one early.
18. Choose Realtime deliberately: Postgres Changes authorizes every event against every subscriber
    and is processed single-threaded, so a large fan-out belongs in
    `realtime.broadcast_changes()` on a private channel instead. Nothing in Realtime is durable.
19. Private channels need both halves: RLS policies on `realtime.messages` and
    `config: { private: true }` on the client. Miss either and the client quietly joins a public
    channel with no policy check.
20. Edge Functions run on Deno. Use the `withSupabase` wrapper — it verifies the caller, answers
    CORS preflight, and hands back clients on `ctx` so no key appears in your code. A browser call
    to a function that does not answer `OPTIONS` fails before your handler runs, with empty logs.
21. Match `verify_jwt` to the caller. Anything without a user JWT — a webhook, cron, `pg_net`,
    another function — is rejected at the gate while `verify_jwt = true`, and once it is `false`
    the handler is solely responsible for authenticating the caller.
22. Edge Function limits are 256 MB of memory, roughly 2 s of CPU time per request, a wall clock
    ceiling that depends on the plan, and a 150 s idle timeout. CPU time is usually what you hit
    first, and it is routinely misdiagnosed as a network timeout.
23. In a declarative project, `supabase/schemas/*.sql` is the source of truth and `db diff` never
    reads the live database. A change made in Studio or the SQL editor is invisible to the diff,
    reported as "No schema changes found", and silently dropped on the next reset.
24. Read every generated migration before applying it. The diff engine does not capture DML, view
    grants and `security_invoker`, `alter policy`, column privileges, comments or partitions — and
    a generated down migration takes data with it.
25. `supabase-js` never throws for an API failure; it returns `{ data, error }`. Handle `error` on
    every call, and destructure to the value you want — `const { data: session }` from
    `getSession()` binds a truthy `{ session: null }` and turns "not signed in" into "RLS blocked
    me".

## Workflows

### implement-a-feature-on-supabase

- [ ] Establish the environment (hosted project or local stack) and the schema workflow
      (declarative or imperative) from `config.toml` and the presence of `supabase/schemas/`.
- [ ] Model the data from the domain, then decide the access model per table before writing any
      policy: who owns a row, who may read it, who may change what
      (`references/rls-and-data-api.md`).
- [ ] Write the migration with grants, `enable row level security`, and the policies together. Use
      `(select auth.uid())` in predicates, and spell out both `USING` and `WITH CHECK` on `UPDATE`
      and `ALL` policies so the two can differ where they should — Postgres reuses `USING` as
      `WITH CHECK` when it is absent, so omitting it narrows intent rather than opening a hole.
- [ ] Wire the client for where it runs: publishable key and per-request server clients with the
      `getAll`/`setAll` adapter plus a refresh path (`references/auth-and-sessions.md`).
- [ ] Apply locally, regenerate types, and fix what the type check finds
      (`references/cli-and-migrations.md`).
- [ ] Run `supabase db advisors` and resolve its findings.
- [ ] **Gate — the policy is proven, not assumed:** exercise the feature as an anonymous caller, as
      its owner, and as a *different* signed-in user; each of the three gets the intended result,
      including on the write path. A `200` is not authorization proof, and a run with the secret
      key proves nothing at all.

### debug-authorization-and-empty-results

- [ ] Name the symptom precisely: an error code, or a `200` with an empty body. They have disjoint
      causes.
- [ ] For an error, read the code — `42501` is a missing grant, `PGRST205` is a schema-cache or
      exposure problem, `PGRST301` is a rejected JWT (`references/client-and-errors.md`).
- [ ] For an empty result, find out whether a user reached Postgres at all: run
      `select auth.uid(), auth.jwt()` through the same client, or `curl` the REST endpoint with and
      without an `Authorization: Bearer <access token>` header.
- [ ] `auth.uid()` null → the failure is in session transport, not the policy. Check the cookie
      adapter, the refresh path, whether the server client is per-request, and whether the guard
      that was supposed to reject the anonymous request actually fires
      (`references/auth-and-sessions.md`).
- [ ] `auth.uid()` populated but still no rows → now read the policy, and check for the silent
      cases: an `UPDATE` with no `SELECT` policy, a view without `security_invoker`, an embed
      blocked by the child table's policy.
- [ ] Do not reach for the secret key, `SECURITY DEFINER`, or disabling RLS to make the symptom go
      away.
- [ ] **Gate — the cause is named and reproduced:** state which layer failed (exposure, grant,
      policy, session) and show the same request succeeding for the intended role and still
      failing for the unintended one.

### audit-what-an-outsider-can-reach

- [ ] Run `supabase db advisors` first. Everything it reports goes in the report as a one-line
      pointer, not as your finding.
- [ ] Build the table list from the repository: grep the application for `.from('…')` calls and
      union it with `create table` in the migrations. The PostgREST OpenAPI root answers only to
      `service_role`, so it cannot enumerate for you — and dashboard-created tables are exactly
      the ones missing from migrations (`references/rls-and-data-api.md`).
- [ ] Probe each table with the publishable key and read the results honestly: rows returned means
      exposed, `401`/`403`/`42501` means protected, and an empty array is **inconclusive** because
      an empty table and a locked table look identical from outside.
- [ ] Size every real finding with an exact count, and flag the sensitive columns in it by name.
- [ ] Repeat on the write path and as a second signed-in user: a policy that scopes reads but
      leaves `INSERT`/`UPDATE`/`DELETE` open passes every read-only audit.
- [ ] Check the bypass routes explicitly: views without `security_invoker`, `SECURITY DEFINER`
      functions in `public`, materialized views, Storage policies missing a `bucket_id` predicate,
      and any public Realtime channel carrying private data (`references/storage.md`,
      `references/realtime.md`).
- [ ] Look for what a linter cannot: paid content readable without a subscription check, a
      multi-tenant table with no tenant predicate, a client permitted to set its own ownership
      column.
- [ ] **Gate — every finding is reproducible and no secret leaked:** each one has the request that
      demonstrates it and the migration that fixes it; no key or token appears anywhere in the
      report.

### ship-a-schema-change

- [ ] Determine the workflow. Declarative (`supabase/schemas/` or `schema_paths`) → edit the schema
      file. Imperative → `supabase migration new <name>` and edit the generated file; never invent
      a migration filename.
- [ ] While iterating, run SQL directly against the local database rather than writing a migration
      history entry per attempt — that is what makes `db diff` come back empty afterwards.
- [ ] Append new columns at the end of the table: views and enums depend on column order.
- [ ] `supabase db diff -f <name>`, then read the generated SQL and hand-write anything the engine
      misses (`references/cli-and-migrations.md`).
- [ ] Apply locally with `migration up`, or `db reset` when the local database already drifted, and
      regenerate types.
- [ ] `supabase db advisors`, then commit the schema file and the migration together.
- [ ] Deploy with `migration list` → `db push --dry-run` → `db push`. Never `db reset --linked` or
      `db push --include-seed` against production.
- [ ] **Gate — the change replays from scratch:** `supabase db reset` reproduces the intended
      schema from migrations plus seed, `migration list` shows local and remote agreeing, and the
      regenerated types type-check against the application.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Key types and rotation, `getClaims`/`getUser`/`getSession`, the `getAll`/`setAll` cookie adapter and its cache headers, per-framework refresh wiring, where a session goes missing, providers, MFA and `aal`, session lifetime settings | Anything touching sign-in, sessions, SSR, or a server that cannot see the user | `references/auth-and-sessions.md` |
| Grants versus RLS and the two failure shapes, Data API exposure, `auth.uid()`/`auth.jwt()` in policies, `TO` clause rules, custom claims via the access-token hook, views and `SECURITY DEFINER` bypasses, auditing by real request, `current_setting` request context | Writing or reviewing a policy, or working out why a row is or is not visible | `references/rls-and-data-api.md` |
| Public versus private buckets, the privilege each SDK call needs, signed URLs and their independent signing key, image transformations, resumable and S3 uploads | An upload, replace, list or URL misbehaves | `references/storage.md` |
| Channels and topics, Postgres Changes versus Broadcast versus Presence, RLS on `realtime.messages`, `private: true`, `realtime.send` and `realtime.broadcast_changes`, connection and slot budgets | Building or debugging a live-updating feature | `references/realtime.md` |
| The `withSupabase` entry point, auth modes against `verify_jwt`, injected variables and `supabase secrets`, CORS, the four runtime limits, local serve and deploy, Deno traps | Writing, deploying or debugging an Edge Function | `references/edge-functions.md` |
| Local stack commands, declarative versus imperative workflows, `db diff` blind spots, deploy and rollback, seed data, `gen types`, preview branches, moving a project | Any migration, CLI or environment question | `references/cli-and-migrations.md` |
| `{ data, error }` handling, error codes and the schema cache, typed clients and `QueryData`, embedded resources and their foreign keys, filters and `rpc`, which client belongs where | Writing queries, or an error code needs interpreting | `references/client-and-errors.md` |

## Environment

- The Supabase CLI plus a Docker-compatible runtime for `supabase start` and
  `supabase functions serve`. Install per the platform instructions rather than assuming a package
  manager, and check with `supabase --version`.
- Application packages: `@supabase/supabase-js`, plus `@supabase/ssr` for any server-rendered app.
  Pin the versions and commit the lockfile — these libraries move quickly, and a floating range
  lets a dependency update change a deployed app's auth behaviour with no change of your own.
- The CLI's command surface changes between versions. Discover it with `supabase <group> --help`
  rather than recalling flags, and when a command named in a guide does not exist in the installed
  CLI, say so instead of substituting a plausible one.
- If the project has the Supabase MCP server configured, its `execute_sql`, `get_advisors` and
  `search_docs` tools are equivalent entry points to the CLI commands named here. Nothing in this
  skill requires it.
- Supabase ships breaking changes with some regularity. When a fact here disagrees with the
  project's installed versions or with the current documentation, the documentation wins; fetch
  the relevant page (any docs URL serves plain text with `.md` appended) rather than working from
  memory.
