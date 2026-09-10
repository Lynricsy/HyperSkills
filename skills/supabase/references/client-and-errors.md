# Client libraries, the Data API and reading its errors

Verified against: `@supabase/supabase-js` 2.x, PostgREST-backed Data API.

## Contents

- [Never ignore error](#never-ignore-error)
- [Reading the error you get](#reading-the-error-you-get)
- [Typed clients](#typed-clients)
- [Embedded resources](#embedded-resources)
- [Filters and modifiers worth knowing](#filters-and-modifiers-worth-knowing)
- [Where the client runs](#where-the-client-runs)

## Never ignore `error`

`supabase-js` does not throw for API failures. Every call resolves to `{ data, error }`, and
`error` is the only place the failure exists.

```ts
const { data, error } = await supabase.from('projects').select('id, name')
if (error) throw error   // or handle it; never fall through
```

Two consequences that produce most "it silently does nothing" reports:

- **`data` is `[]` for both "no matching rows" and "RLS hid everything".** An empty array is not
  evidence of an empty table. When a list comes back empty and you expected rows, that is a
  policy-or-session question, not a query question.
- **Destructuring the wrong level is a real bug.** `auth.getSession()` resolves to
  `{ data: { session }, error }`, so `const { data: session } = await …` binds
  `{ session: null }` — a truthy object. A guard written as `if (!session)` then never fires and an
  unauthenticated request proceeds as `anon`. Destructure to the value:
  `const { data: { session } } = …`.

`.single()` errors when the result is not exactly one row; `.maybeSingle()` returns `null` data
instead. Pick by whether zero rows is a bug or a normal outcome, and check `error` either way.

## Reading the error you get

The `code` is the contract; the message is not. Branch on codes.

| Code / status | Meaning | First move |
|---|---|---|
| `42501` | Postgres permission denied — the role has no `GRANT` | Add the grant; the hint names the exact statement |
| `200` with `[]` | reachable, but no row passed RLS | Check whether a session arrived at all |
| `PGRST116` | `.single()` got zero or multiple rows | Use `.maybeSingle()`, or fix the filter |
| `PGRST202` | function not found in the schema cache | Wrong name/arg types, or the schema is not exposed |
| `PGRST205` | table not found in the schema cache | Table missing, not in an exposed schema, or the cache is stale |
| `PGRST301` | JWT rejected | Expired or wrong-issuer token |
| `23505` | unique violation | Real constraint conflict; consider `upsert` |
| `23503` | foreign key violation | Insert order, or a deleted parent |
| `401` from a function URL | `verify_jwt` rejected the caller before your code ran | Set `verify_jwt = false` for that function and authenticate the caller yourself |

The Data API keeps a **schema cache**, so a table or function created moments ago can be reported
as not existing. `notify pgrst, 'reload schema'` (config changes use `reload config`) refreshes it;
the dashboard and the CLI do this for you on migration, which is why the stale-cache case shows up
mainly after ad-hoc SQL.

"Not found in the schema cache" and "permission denied" are different problems. Before assuming
either, confirm the object is in a schema the Data API exposes at all.

## Typed clients

Generate the types and parameterise the client — an untyped client makes every column name a
string literal nobody checks:

```ts
import type { Database } from './database.types'
const supabase = createClient<Database>(url, publishableKey)
```

For a query whose result shape you need as a named type, derive it from the query rather than
hand-writing it, so it cannot drift:

```ts
import type { QueryData } from '@supabase/supabase-js'

const projectsWithMembers = supabase.from('projects').select('id, name, project_members(user_id)')
type ProjectsWithMembers = QueryData<typeof projectsWithMembers>
```

Regenerate after every applied migration. Do not edit the
generated file; layer overrides in a separate type.

## Embedded resources

`select('*, customer:customers(*)')` embeds a related row and is resolved through the **foreign
key**, not through a name convention. That has consequences:

- No foreign key, no embed. Add the constraint; do not work around it with two round trips.
- With more than one foreign key between the same pair of tables, the embed is ambiguous and must
  name the constraint or column: `scans!scan_id_start(id)`.
- Embeds are a **left join by default**, so a parent row survives with an empty or null child.
  `customers!inner(*)` makes it an inner join, which is also how you filter parents by a child's
  column.
- `select('*')` on an embed pulls every column of both tables. Name the columns you need; this is
  the difference between a 2 KB and a 2 MB response on wide rows.
- RLS applies to the embedded table too. An embed that always returns `null` is usually a missing
  policy on the child, not a broken relationship.

## Filters and modifiers worth knowing

- `.eq()`, `.in()`, `.contains()` and friends compose; `.or()` takes a PostgREST filter string
  (`'plan.eq.pro,plan.eq.team'`) and is easy to get subtly wrong — prefer `.in()` where it fits.
- `.range(from, to)` is inclusive at both ends. Combine with
  `select('*', { count: 'exact' })` when you need a total, and be aware that an exact count costs a
  full count on every request; `'planned'` or `'estimated'` are the cheaper options.
- Text search is `.textSearch(column, query, { type: 'websearch', config: 'english' })`; the query
  syntax and the index behind it are the `postgres` skill's subject.
- `.rpc('fn', args)` calls a Postgres function. It needs `EXECUTE` granted to the calling role, and
  a `SECURITY DEFINER` function reached this way bypasses RLS, so it must carry its own ownership
  check.
- `.abortSignal(signal)` is how you cancel; without it a navigated-away page keeps its request.

## Where the client runs

- **Browser / mobile** — publishable key, `createBrowserClient` (already a singleton). Never a
  secret key: it bypasses RLS, and shipping it is a total compromise of the project's data.
- **Server, per request** — build a new client per request from that request's cookies; a
  module-scoped server client leaks one user's session into
  another user's request.
- **Server, privileged** — secret key, no user context, and your code is then solely responsible
  for authorization. Anything reached this way must check ownership itself.
- **Edge Functions** — do not read a key from the environment at all; take the client off the
  handler's `ctx`.

Pin the Supabase package versions and commit the lockfile. These libraries move quickly, and a
floating range means a dependency update changes the auth or cookie behaviour of a deployed app
without any change of your own.

<!-- sources: supabase-docs, supabase-official-skill, tushar-skills -->
