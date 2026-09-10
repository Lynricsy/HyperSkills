# Row-level security

Verified against: PostgreSQL 18.6

Pure SQL. The tenant key here is a session/transaction GUC (`app.tenant_id`); wherever a
platform supplies its own claim function, substitute it — the policy mechanics are the same.

## Contents

- The three switches
- USING versus WITH CHECK
- Permissive, restrictive and how policies combine
- Carrying request context safely
- Policy performance: the Filter versus Index Cond split
- Subqueries in policies
- SECURITY DEFINER helper functions
- Views and RLS
- Verifying a policy set

## The three switches

```sql
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;   -- policies now apply
ALTER TABLE documents FORCE  ROW LEVEL SECURITY;   -- ...to the table's owner too
```

- `ENABLE` with no policy defined is a **default deny** for every non-owner role. That is the
  correct order (enable, then add policies), but it means the window between the two
  statements is an outage if they are not in one transaction.
- The table's **owner is exempt** from its own policies unless `FORCE` is set. This is the
  single most common way a policy suite passes in development and leaks in production: tests
  run as the owner, the application does not.
- A role with `BYPASSRLS` ignores policies even with `FORCE`, and so does a superuser. Audit
  who has it:

  ```sql
  SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolsuper OR rolbypassrls;
  ```

Observed on 18.6 with a non-superuser owner: without `FORCE` the owner saw all rows despite a
restrictive-looking policy; with `FORCE` it saw none; a superuser saw all rows in both cases.

RLS is also not a substitute for privileges. Revoke first, then add policies:

```sql
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON documents TO app_user;
```

## USING versus WITH CHECK

- `USING` is applied to rows **already in the table**: it decides what `SELECT` returns and
  which rows `UPDATE` and `DELETE` are allowed to touch. Rows failing it are invisible, not
  an error.
- `WITH CHECK` is applied to the row **being written**: `INSERT` values and the post-update
  image of an `UPDATE`. Failing it raises
  `ERROR: new row violates row-level security policy for table "..."`.

| Command | `USING` applies to | `WITH CHECK` applies to |
|---|---|---|
| `SELECT` | the row read | — |
| `INSERT` | — | the new row |
| `UPDATE` | the old row | the new row |
| `DELETE` | the row deleted | — |
| `ALL` | reads and old rows | new rows; **defaults to the `USING` expression** |

That default is what makes `FOR ALL USING (...)` deceptively safe and then deceptively
narrow. Verified on 18.6: with a single `FOR ALL USING (owner = current_user)` policy, both
an `INSERT` of another user's row and an `UPDATE` moving a row out of the predicate were
rejected. Splitting into `FOR SELECT USING (true)` plus `FOR INSERT WITH CHECK (owner =
current_user)` opened reads while keeping writes constrained — and a `SELECT`-only policy
does not enable `INSERT` at all, so writes then fail closed until an insert policy exists.

Write one policy per command. It costs a few more lines and makes the read predicate and the
write predicate reviewable independently.

## Permissive, restrictive and how policies combine

Policies are `PERMISSIVE` by default, and permissive policies for the same command are
**OR-ed**. Adding a policy can therefore only widen access. This is the mechanism behind the
classic multi-tenant leak:

```sql
CREATE POLICY documents_tenant ON documents FOR ALL
  USING (tenant_id = (SELECT current_tenant()));

-- intended as "editors get a bit more", actually "anything in any tenant I edit"
CREATE POLICY documents_editor ON documents FOR ALL
  USING (EXISTS (SELECT 1 FROM tenant_members m
                 WHERE m.user_id = (SELECT current_user_id())
                   AND m.tenant_id = documents.tenant_id
                   AND m.role = 'editor'));
```

Because the second policy's `USING` doubles as its `WITH CHECK`, an editor can `UPDATE
documents SET tenant_id = <another tenant they edit>` and the write passes. Two fixes, use
both:

```sql
-- 1. pin the write predicate explicitly rather than inheriting USING
CREATE POLICY documents_write ON documents FOR UPDATE
  USING      (tenant_id = (SELECT current_tenant()))
  WITH CHECK (tenant_id = (SELECT current_tenant()));

-- 2. an invariant that no permissive policy can widen
CREATE POLICY documents_same_tenant ON documents AS RESTRICTIVE FOR ALL
  USING      (tenant_id = (SELECT current_tenant()))
  WITH CHECK (tenant_id = (SELECT current_tenant()));
```

Restrictive policies are AND-ed with the OR-ed permissive set. A table with only restrictive
policies grants nothing — there must be at least one permissive policy for the row to be
visible at all.

## Carrying request context safely

```sql
-- per request, inside the transaction
SELECT set_config('app.tenant_id', $1, true);   -- true = transaction-local
-- or
SET LOCAL app.tenant_id = '42';
```

Session-level `SET` does not survive a transaction-mode connection pooler: the next
transaction may land on a different backend, and worse, a backend may inherit a previous
client's value. `SET LOCAL` and `set_config(..., true)` are reset at the end of the
transaction, which is exactly the request boundary.

Read it with the two-argument form so an unset parameter is `NULL` instead of an error:

```sql
CREATE FUNCTION current_tenant() RETURNS bigint
LANGUAGE sql STABLE AS $$
  SELECT nullif(current_setting('app.tenant_id', true), '')::bigint
$$;
```

A `NULL` tenant then matches no rows, which fails closed. `current_setting('app.tenant_id')`
without the second argument raises `unrecognized configuration parameter`, which surfaces as
a 500 rather than an empty result — pick deliberately.

## Policy performance: the Filter versus Index Cond split

A policy predicate is ANDed into every query on the table, so its cost is paid per statement.
Where it ends up in the plan decides how much.

Measured on 18.6, 200k rows, a `STABLE` plpgsql function in the policy, **no usable index** so
the predicate stays a `Filter`:

| Policy | Plan | Time |
|---|---|---|
| `USING (tenant = current_tenant())` | `Filter: (tenant = current_tenant())` | 1223 ms |
| `USING (tenant = (SELECT current_tenant()))` | `InitPlan 1` + `Filter: (tenant = (InitPlan 1).col1)` | 11 ms |

`STABLE` guarantees the function returns the same value within one statement; it does **not**
make Postgres cache the result. In a bare `Filter` the function is called once per row. The
scalar subquery turns it into an `InitPlan`, evaluated once.

The caveat every version of this advice omits: when the predicate can be pushed down into an
index condition, the planner already evaluates the stable function once. With an index on
`tenant`, both forms produced the identical plan and the identical 2068 buffers:

```
 Bitmap Heap Scan on t_rls
   Recheck Cond: (tenant = current_tenant())
   ->  Bitmap Index Scan on t_rls_tenant
         Index Cond: (tenant = current_tenant())
```

So the order of work is: **index the policy's columns first**, confirm the plan shows
`Index Cond`, and use `(SELECT ...)` for the predicates that still land in a `Filter`. Wrapping
everything unconditionally is harmless but is not where the win comes from, and it will not
save an unindexed policy from a sequential scan.

## Subqueries in policies

A correlated subquery in a policy is re-planned as part of every query on the table. Postgres
often flattens a simple `EXISTS` into a hashed subplan — but the outer scan usually loses its
index, because the predicate is no longer a comparison on an indexed column:

```
 Seq Scan on t_rls
   Filter: (ANY (tenant = (hashed SubPlan 2).col1))
   Rows Removed by Filter: 188000
   SubPlan 2
     ->  Seq Scan on members m   (actual rows=3.00 loops=1)
```

Prefer a shape where the tenant set is computed once and compared against an indexed column:

```sql
CREATE POLICY documents_member ON documents FOR SELECT
  USING (tenant_id IN (SELECT m.tenant_id FROM tenant_members m
                       WHERE m.user_id = (SELECT current_user_id())));
```

and index both `documents(tenant_id)` and `tenant_members(user_id, tenant_id)`. Membership
tables are small and hot, so this stays a cheap hashed subplan feeding an index condition.

## SECURITY DEFINER helper functions

When the check is genuinely complex, move it into a function so the policy is one call — but
understand what you are turning off. A `SECURITY DEFINER` function runs as its owner and
therefore **bypasses RLS on every table it touches**.

```sql
CREATE SCHEMA private;
REVOKE ALL ON SCHEMA private FROM PUBLIC;

CREATE FUNCTION private.is_team_member(team bigint) RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = ''          -- non-negotiable: blocks search_path hijacking
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.team_members
    WHERE team_id = $1
      AND user_id = nullif(current_setting('app.user_id', true), '')::bigint
  );
$$;

REVOKE EXECUTE ON FUNCTION private.is_team_member(bigint) FROM PUBLIC;
GRANT  EXECUTE ON FUNCTION private.is_team_member(bigint) TO app_user;

CREATE POLICY documents_team ON documents FOR SELECT
  USING ((SELECT private.is_team_member(team_id)));
```

Four properties make this safe: it lives in a schema nobody can reach, `search_path` is
empty so every reference is schema-qualified, the caller's identity is re-derived *inside*
the body rather than passed in, and `EXECUTE` is granted to exactly one role. Drop any of
the four and it becomes a privilege-escalation primitive.

Note that a function called per row is still per row; the same `(SELECT ...)` rule applies,
and a helper whose argument is a column (`team_id`) genuinely cannot be hoisted — index the
column and keep the function cheap.

## Views and RLS

Before PG 15 a view always executed with the view owner's permissions, silently bypassing the
caller's policies. From PG 15:

```sql
CREATE VIEW active_documents WITH (security_invoker = true) AS
  SELECT * FROM documents WHERE archived_at IS NULL;
```

`security_invoker = true` makes the underlying table's policies apply to whoever queries the
view. Audit existing views for the default before relying on RLS behind one.

## Verifying a policy set

Prove it from the application's role, not the owner's:

```sql
SET ROLE app_user;
SELECT set_config('app.tenant_id', '42', false);

SELECT count(*) FROM documents;                              -- only tenant 42
INSERT INTO documents (tenant_id, title) VALUES (99, 'x');   -- must be rejected
UPDATE documents SET tenant_id = 99 WHERE id = <own row>;    -- must be rejected
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM documents WHERE ...; -- predicate as Index Cond

RESET ROLE;
```

All four checks matter: the read is filtered, the insert fails closed, the update cannot move
a row across the boundary, and the policy is not costing a sequential scan. List what is
actually in force with:

```sql
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies WHERE tablename = 'documents';
```

A `with_check` of `NULL` on an `ALL` policy is the inherited-`USING` case, not "no check".

<!-- sources: postgresql-docs, microsoft-postgres-skills, supabase-postgres-bp, neon-postgres-skills -->
