# RLS in the Supabase auth context, and Data API exposure

Verified against: Supabase platform (PostgREST-backed Data API), PostgreSQL 15+.

Policy *syntax* and policy *performance* belong to the `postgres` skill. This file covers what is
specific to Supabase: which auth context a policy sees, how a table becomes reachable in the first
place, and how to prove a policy works.

## Contents

- [Two gates, not one](#two-gates-not-one)
- [The auth context inside a policy](#the-auth-context-inside-a-policy)
- [Custom claims and RBAC](#custom-claims-and-rbac)
- [Supabase-specific bypass routes](#supabase-specific-bypass-routes)
- [Proving a policy: audit by request](#proving-a-policy-audit-by-request)
- [Request context available in SQL](#request-context-available-in-sql)

## Two gates, not one

Postgres evaluates **grants** first and **row-level security** second, and the two failures look
different:

| Failure | What the client sees |
|---|---|
| Role has no `GRANT` on the object | `42501 permission denied for table …` — including for `service_role` |
| RLS policy matches no rows | `200` with `[]` |

So "the API cannot see my table" and "the API returns nothing" are different bugs. Check the grant
before debugging the policy.

Being *in an exposed schema* is a third, separate condition. `public` is exposed by default, and
depending on the project's Data API settings a newly created table may not be reachable until
`anon` / `authenticated` are granted access explicitly. This is not RLS: RLS decides which rows are
visible once the table is reachable at all.

```sql
-- Make the object reachable, minimally
grant select on table public.projects to anon;
grant select, insert, update, delete on table public.projects to authenticated;
grant execute on function public.search_projects(text) to authenticated;

-- Then decide which rows
alter table public.projects enable row level security;
```

Bundle the grants and the RLS setup in the **same migration**. A migration that adds a table and
its policies but forgets the grant ships an endpoint that 42501s; one that adds the grant without
RLS ships an open table.

Two related platform facts worth knowing:

- On existing projects, tables created in `public` receive full CRUD grants for
  `anon`/`authenticated`/`service_role` automatically, which makes new objects reachable before
  anyone intended. `alter default privileges … revoke …` turns that off so exposure becomes opt-in.
- A dedicated schema (`api`) makes the exposed surface auditable: internal tables and helper
  functions stay in schemas that are not exposed at all.

Enable RLS on **every** table in an exposed schema, and prefer it as defence in depth in private
schemas too. Then write policies that match the real access model instead of pasting the same
`auth.uid() = user_id` onto every table — ownership, membership, tenancy and public-read are
different models and deserve different policies.

## The auth context inside a policy

| Helper | Returns | When it is `null` |
|---|---|---|
| `auth.uid()` | `sub` claim of the request's JWT, as `uuid` | No JWT on the request |
| `auth.jwt()` | the whole verified claim set as `jsonb` | never, but is `{}`-ish without a JWT |

Wrap both in a scalar subquery — `(select auth.uid())` — as the default form. It is never wrong,
and in the bad case it is orders of magnitude faster. The mechanics of *why* (whether the predicate
lands in a `Filter` node or an `Index Cond`) are the `postgres` skill's subject.

Rules that follow from the auth context:

- **Target the role with `TO`, never with a role check in `USING`.** `to authenticated` /
  `to anon` is the supported form. `auth.role() = 'authenticated'` is deprecated *and* silently
  wrong once anonymous sign-ins are enabled, because anonymous users carry the `authenticated`
  Postgres role. If "signed in for real" is the requirement, test
  `(select auth.jwt() ->> 'is_anonymous') = 'false'` or an application-level claim.
- **`TO authenticated` alone is authentication, not authorization.** It says "somebody is signed
  in", not "this row is theirs" — the classic BOLA/IDOR shape. Combine it with an ownership or
  membership predicate.
- **Write `USING` and `WITH CHECK` explicitly on `UPDATE` and `ALL` policies.** `USING` decides
  which existing rows you may target; `WITH CHECK` decides what the row may look like afterwards.
  Postgres reuses `USING` as `WITH CHECK` when the latter is omitted, so an omitted `WITH CHECK`
  is *not* an open door — but it does mean the two can never differ, and they usually should. "You
  may edit any row in your workspace, but you may not move a row into another workspace" needs two
  different expressions, and a policy that leans on the default silently forbids that distinction.
  Some upstream guidance claims that omitting `WITH CHECK` lets a user reassign `user_id` to
  somebody else; that is wrong on any supported Postgres, because the reused `USING` expression
  rejects the new row. Write both anyway, for intent.
- **`UPDATE` also needs a `SELECT` policy.** Postgres has to read the row before it can update it,
  so an update with no `SELECT` policy affects 0 rows and returns no error.
- **`DELETE` events in Realtime are not filtered by RLS**, because Postgres cannot check access to
  a row that no longer exists. Do not put anything in a deleted row that subscribers must not see.

```sql
create policy "members read project"
  on public.projects for select
  to authenticated
  using (
    exists (
      select 1 from public.project_members m
      where m.project_id = projects.id
        and m.user_id = (select auth.uid())
    )
  );

create policy "owner updates project"
  on public.projects for update
  to authenticated
  using ((select auth.uid()) = owner_id)
  with check ((select auth.uid()) = owner_id);
```

## Custom claims and RBAC

Roles that policies can read cheaply come from a **custom access token hook**: a Postgres function
that runs before each token is issued and edits the claim set.

```sql
create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb language plpgsql stable as $$
declare
  claims jsonb := event -> 'claims';
  user_role public.app_role;
begin
  select role into user_role from public.user_roles
   where user_id = (event ->> 'user_id')::uuid;
  claims := jsonb_set(claims, '{user_role}', coalesce(to_jsonb(user_role), 'null'::jsonb));
  return jsonb_set(event, '{claims}', claims);
end;
$$;

grant usage on schema public to supabase_auth_admin;
grant execute on function public.custom_access_token_hook to supabase_auth_admin;
revoke execute on function public.custom_access_token_hook from authenticated, anon, public;
```

Then the hook must be selected in the dashboard's Auth hooks section (locally, in `config.toml`) —
creating the function is not enough. The role table itself must be readable by
`supabase_auth_admin` and by nobody else.

Two consequences that surprise people:

- The hook edits the **access token only**, not the auth API response. Client code reads the claim
  by decoding `session.access_token`, not from the `user` object.
- A claim change takes effect at the next token refresh, so a permission you just granted is not
  live until then.

Read the claim in policies through a `stable security definer` helper with
`set search_path = ''`, and call it as `(select authorize('messages.delete'))` so it evaluates once.

## Supabase-specific bypass routes

Each of these hands out data while every table still shows "RLS enabled".

- **Views bypass RLS by default.** On PostgreSQL 15+ create them
  `with (security_invoker = true)`; otherwise the view runs as its owner. On older servers, revoke
  access from `anon`/`authenticated` or keep the view out of an exposed schema.
- **`SECURITY DEFINER` functions bypass RLS** by running as their creator, typically a role with
  `BYPASSRLS`. Never add `SECURITY DEFINER` to make a permission error go away — that removes the
  check instead of fixing it. Prefer `SECURITY INVOKER`.
- **A `SECURITY DEFINER` function in `public` is a public endpoint.** Postgres grants `EXECUTE` to
  `PUBLIC` on every new function, and `anon`/`authenticated` inherit from `PUBLIC`. When one is
  genuinely needed (reading an internal lookup table, say), keep it in an unexposed schema, revoke
  the default `EXECUTE`, and put the ownership check inside the body.
- **The secret / `service_role` key bypasses everything.** It is not an escalation path for a
  policy you cannot get right, and it must never be reachable from a client.
- **Materialized views** are not covered by RLS on their source tables.

Run `supabase db advisors` (or the MCP `get_advisors` tool) after any change to policies, views,
functions, triggers or storage. It catches the structural cases; the rest of this file is for the
ones it cannot see.

## Proving a policy: audit by request

Reading policy files is not verification. Reproduce what an outsider can do, using the
**publishable key** — it is public by design, already in every shipped bundle.

Never audit with the secret key: it bypasses RLS, so everything comes back readable and the audit
means nothing.

1. **Build the table list from the repository, not the API.** The PostgREST OpenAPI root now
   answers only to `service_role`, and `pg_graphql` introspection depends on an extension. Grep
   what the app actually queries and union it with the migrations:

   ```bash
   grep -rhoE '\.from\(\s*["'"'"'`][a-zA-Z0-9_]+' src \
     --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' |
     sed -E 's/.*["'"'"'`]//' | sort -u > /tmp/tables.txt
   grep -rhoiE 'create table (if not exists )?"?public"?\.?"?[a-z0-9_]+' supabase/migrations |
     sed -E 's/.*[."]([a-z0-9_]+)"?$/\1/' | sort -u >> /tmp/tables.txt
   ```

   Say out loud that this list comes from the code: a table that exists but is never queried in
   the repo will not be tested. Dashboard-created tables are exactly the ones missing from
   migrations, which is why the code grep comes first.

2. **Probe each table** and read the result honestly:

   ```bash
   while IFS= read -r t; do
     code=$(curl -s -o /tmp/body -w '%{http_code}' \
       "$SUPABASE_URL/rest/v1/$t?select=*&limit=1" \
       -H "apikey: $PUBLISHABLE_KEY" -H "Authorization: Bearer $PUBLISHABLE_KEY")
     printf '%s\t%s\t%s\n' "$t" "$code" "$(head -c 80 /tmp/body)"
   done < /tmp/tables.txt
   ```

   | Result | Meaning |
   |---|---|
   | `200` with rows | Exposed — an anonymous stranger reads this |
   | `200` with `[]` | **Inconclusive.** An empty table and a locked table are identical from outside; check whether the table has rows before claiming it is safe |
   | `401` / `403` / `42501` | Protected |
   | `404` | Not exposed through the API |

3. **Size any real finding.** `-H 'Prefer: count=exact' -H 'Range: 0-0'` and read
   `Content-Range`: "all 4,182 rows are readable" is a decision, "some rows are readable" is a
   shrug.

4. **Test the write side too**, and test as a *second* signed-in user. A policy that scopes reads
   but leaves `INSERT`/`UPDATE`/`DELETE` open, or one that lets user B target user A's row, passes
   every read-only audit.

5. **Look for the logic advisors cannot see**: paid content readable without a subscription check,
   a multi-tenant table missing its tenant predicate, an ownership column the client is allowed to
   set. Anything the advisors already reported goes in the report as a one-line pointer, not a
   duplicate finding.

Never print a key or a token in the report. Read them from the environment and reference them by
variable name.

## Request context available in SQL

Policies and helper functions can read the request through `current_setting`:

```sql
select current_setting('request.jwt.claims', true)::json ->> 'email';
select current_setting('request.headers', true)::json ->> 'user-agent';
select split_part(current_setting('request.headers', true)::json ->> 'x-forwarded-for', ',', 1);
```

`request.method`, `request.path`, `request.headers`, `request.cookies` and `request.jwt` are all
available. `pgrst.db_pre_request` (rate limits, quota checks, extra API keys) applies to the Data
API only — Realtime, Storage and the rest never call it, so a check that must hold everywhere goes
into the policies themselves.

<!-- sources: supabase-official-skill, supabase-docs, postgres-docs, rls-audit, supabase-security-audit, tushar-skills -->
