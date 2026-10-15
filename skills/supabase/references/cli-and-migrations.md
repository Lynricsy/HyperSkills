# Supabase CLI, local stack and migrations

Verified against: Supabase CLI 2.121.

## Contents

- [Which environment am I talking to](#which-environment-am-i-talking-to)
- [The local stack](#the-local-stack)
- [Two schema workflows](#two-schema-workflows)
- [Declarative schemas](#declarative-schemas)
- [What the diff engine misses](#what-the-diff-engine-misses)
- [Deploying and rolling back](#deploying-and-rolling-back)
- [Credentials for CI, scripts and agents](#credentials-for-ci-scripts-and-agents)
- [Seed data and generated types](#seed-data-and-generated-types)
- [Branching](#branching)
- [Moving a project](#moving-a-project)
- [Discovering commands](#discovering-commands)

## Which environment am I talking to

Three environments share vocabulary and do not share commands. Establish which one the task means
before running anything:

| Environment | How you know | What is safe |
|---|---|---|
| Local stack | `supabase status` answers; ports on 54321+ | anything, including `db reset` |
| Linked remote project | `supabase/.temp/project-ref` exists, `supabase projects list` shows the link | migrations and pushes; **never** `db reset` |
| Neither | no `supabase/` directory | run `supabase init` first |

Pass `--local` or `--linked` explicitly wherever a command accepts them. Defaults differ between
commands, and the cost of guessing wrong is asymmetric.

The local stack is a development environment: default credentials, no TLS, no production rate
limiting. Do not expose it, and do not treat "it works locally" as evidence about production
configuration.

## The local stack

```bash
supabase init                 # creates supabase/config.toml
supabase start                # brings up Postgres, Auth, Storage, Realtime, Studio; needs Docker
supabase status               # URLs plus the local publishable and secret keys
supabase stop                 # add --no-backup to discard local data
```

First `supabase start` pulls images and takes minutes. A function or service that will not start
is almost always Docker not running, or a port held by another local stack — `supabase stop` then
`supabase start`.

## Two schema workflows

A project uses one or the other, and mixing them produces empty or conflicting diffs.

- **Declarative** — `supabase/schemas/` exists, or `config.toml` sets `[db.migrations] schema_paths`.
  You edit the desired end state; the CLI generates the migration.
- **Imperative** — no `supabase/schemas/`. You write the migration by hand:
  `supabase migration new <name>` first, then edit the generated file. Never invent a migration
  filename; the timestamp prefix has to come from the CLI.

Detect which one before touching anything, and say which you found.

Then detect the **diff engine**, because the same command behaves differently on each. A current
`supabase init` writes `[experimental.pgdelta] enabled = true` into `config.toml`, so new projects
use **pg-delta**; projects without that section stay on the legacy **migra** engine until someone
adds it. `SUPABASE_EXPERIMENTAL_PG_DELTA=1` has the same effect for `db diff` and `db pull`, and
`db diff --use-pg-delta` / `--use-migra` override it for one run.

While iterating on either, run SQL directly against the local database (`supabase db query`, `psql`,
or the MCP `execute_sql` tool if the project has the Supabase MCP server configured) so you can try
things freely. Do **not** iterate with `apply_migration`-style calls that write a migration history
entry per attempt: after the first one, `db diff` and `db pull` produce empty or conflicting
output and you are stuck with whatever SQL you passed first.

## Declarative schemas

On **pg-delta** (any project with `[experimental.pgdelta] enabled = true`):

```bash
# 1. edit supabase/schemas/<file>.sql — this is the source of truth
# 2. generate the migration (--no-apply: write the file only, no prompt)
supabase db schema declarative sync --name add_discount_pct --no-apply
# 3. read the generated SQL in supabase/migrations/
# 4. apply locally
supabase migration up        # pending migrations only
supabase db reset            # replay everything from scratch, then seed
```

On pg-delta, **`supabase db diff` never reads `supabase/schemas/`** — it diffs the live database
against a shadow built from the migrations, so running it in a declarative project captures
whatever was clicked into Studio and ignores the files. File order is resolved from dependencies;
`schema_paths` is ignored (the CLI warns if it lists paths). `supabase db schema declarative
generate` exports an existing database into per-object files; on a project with no migrations, run
`supabase db pull` first for a baseline, or the first `sync` regenerates the whole schema as one
migration that then fails on `db push`.

On the legacy **migra** engine, `supabase db diff` is the generator, and it reads the schema files
only while they exist:

```bash
supabase stop                       # generate with the local stack stopped
supabase db diff -f add_discount_pct
supabase start && supabase migration up
```

The trap that costs the most time is the same on both: **the generator compares the schema files
against the migrations. It does not read the live database.** A column added in Studio, the SQL
editor or `psql` is invisible to it — the command reports "No schema changes found" and the change
is silently dropped on the next `db reset`. Edit the file, always.

Two more rules that come straight from how diffs are produced:

- **Append new columns at the end of the table.** Views and enums depend on column order, so an
  insertion in the middle produces a noisy diff or a recreated view.
- On migra only, **schema files run in lexicographic order**, which matters for foreign keys — the
  parent table must exist first. Control it explicitly when it stops being true:

  ```toml
  [db.migrations]
  schema_paths = ["./schemas/accounts.sql", "./schemas/*.sql"]
  ```

Views and functions are the real payoff: edit them in place instead of restating the whole body in
a migration.

To adopt declarative schemas on an existing migra project, `supabase db dump >
supabase/schemas/prod.sql` and split it up from there. Do not run `supabase db pull --declarative`
on migra: it writes a per-object tree for pg-delta and points `schema_paths` at it, and the next
`db diff` fails on file order.

## What the diff engine misses

Read every generated migration. Both engines miss:

- DML: `insert`, `update`, `delete`, and anything seed-like — including storage buckets, which are
  rows in `storage.buckets`. On pg-delta a DML statement in a schema file is an error; named
  `pg_cron` jobs declared with `cron.schedule(...)` are the exception, tracked as extension
  configuration.
- grants duplicated out of default privileges (safe to delete if you never customised them)

**pg-delta** models tables, views, materialized views, functions, triggers, RLS policies, grants,
comments, domains, partitions and publications. It does not track casts, operators and operator
classes, text-search objects, statistics objects, languages, transforms or parameter ACLs; it
reports those as warnings rather than dropping them, and `--strict-coverage` turns the warnings into
failures for CI. Objects owned by an extension are excluded and changed through that extension's
API.

**migra** silently omits, in addition — hand-write these into a versioned migration:

- view owner and grants, `security_invoker` on views, indexes on a recreated materialized view
- `alter policy` statements, and column-level privileges
- comments and roles
- `alter publication … add table …`, `create domain`

If you changed RLS policies in the dashboard, assume a migra diff did not capture it.

## Deploying and rolling back

```bash
supabase migration list       # local versus remote, side by side
supabase db push --dry-run    # exactly what would run remotely
supabase db push
```

`supabase migration up` applies migrations locally. It is not a deployment; only `db push` touches
the remote database. Never `db reset --linked`, and never `db push --include-seed` against
production.

Rolling back has two different answers:

- **Still iterating locally** — `supabase db reset --version <timestamp>` to drop back, then edit
  and regenerate a single clean migration. Only for versions that have never been deployed.
- **Already deployed** — revert the change in the schema files and generate a *new forward*
  migration containing the down change. Production history only rolls forward. Down migrations are
  usually destructive: read every statement before pushing, because a generated `drop column` takes
  the data with it.

Before committing a schema change, run `supabase db advisors` (or the MCP `get_advisors` tool) and
fix what it reports, particularly after touching views, functions, triggers, policies or storage.
Commit the schema file and the generated migration **together** — either one alone breaks the next
person's diff.

## Credentials for CI, scripts and agents

The CLI, the Management API and the hosted MCP server authenticate with a personal access token.
The browser flow of `supabase login` mints a **classic** one: everything the account can do, on
every organization and project it belongs to now *or joins later*. A token saved by that login
and copied into a CI secret is therefore the owner's whole account, whatever the job does.

For CI, scripts and agents, create a **scoped** token (prefix `sbp_fc`) per job from the
account's access-token settings, limited to the project and the permissions that job's commands
or MCP tools are documented to need, and pass it as `SUPABASE_ACCESS_TOKEN` — the variable takes
precedence over any saved login, so a stale `supabase login` on the runner cannot widen it. For
the MCP server in CI, send the same kind of token as an `Authorization: Bearer` header.

The token does not bound everything. Commands that connect with the database password —
`supabase db push` with `SUPABASE_DB_PASSWORD` or `--password` — are not limited by the token's
permissions at all. In a migrate job the production database password is the real write
credential: keep it in an environment-protected secret, and rotate it as well as revoking the
classic token when either has been exposed to jobs that run untrusted code.

## Seed data and generated types

`supabase/seed.sql` runs after migrations on `db reset`. Keep it idempotent (`on conflict do
nothing`) so a partial reset does not fail on the second run.

Regenerate types after every applied schema change, from the environment you actually migrated:

```bash
supabase gen types typescript --local > src/database.types.ts
supabase gen types typescript --project-id "$PROJECT_REF" --schema public > src/database.types.ts
```

Then `createClient<Database>(...)` and run the project's type check — a stale generated file is how
a renamed column reaches production. Do not hand-edit the generated file; layer overrides with a
separate type that merges into it.

## Branching

Preview branches get their own project ref and their own keys, so `supabase projects api-keys
--project-ref <branch-ref>` is required — omitting the flag returns the *parent* project's keys,
which is a quiet way to point a preview environment at production.

## Moving a project

A Supabase project is more than its database. When migrating between projects or off a hosted
wrapper, the full surface is:

- schema and data (`supabase db dump`, plus a data-only dump)
- `auth.users` and identities
- Storage objects, bucket definitions and their policies
- Edge Functions and their secrets
- scheduled jobs (`pg_cron`) and any queue state
- project settings: providers, redirect URLs, SMTP, Auth hooks

Treat password hashes as **not portable** unless you have verified you can read and re-import them:
the default plan is a password-reset flow for migrated users. Promising a seamless cutover and then
discovering the hashes did not come across is the failure mode worth avoiding.

## Discovering commands

The CLI's command surface changes between versions. Discover it rather than recalling it:

```bash
supabase --help
supabase db --help
supabase db diff --help
supabase --version
```

When a command in a guide does not exist in the installed CLI, say so and name the command the
project actually has, rather than substituting a plausible one.

<!-- sources: supabase-official-skill, supabase-docs, tushar-skills, magnus-agent-skills, lovable-migration -->
