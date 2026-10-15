# Wrangler or `cf`: which CLI a project uses

Verified against: the Cloudflare CLI documentation (`developers.cloudflare.com/cf/`, pages
dated 2026-09-29/30) and the wrangler CHANGELOG through 4.151.0. `cf` was not run locally, so
everything here is `[official]`. `cf` is in **beta**: commands, configuration and Build Output
can change before the stable release, so retrieve its documentation instead of recalling it.

## Choose the CLI from the project, not from habit

| Project state | CLI for dev, build and deploy |
|---|---|
| `wrangler.jsonc`, `wrangler.json` or `wrangler.toml`, and no `cloudflare.config.ts` | Wrangler. Every wrangler command in this skill applies as written. `cf` resource commands may run alongside; migration happens only when the user asks |
| `cloudflare.config.ts` present | `cf` |
| New project, or no Cloudflare configuration at all | `cf` — Cloudflare's guidance for coding agents. Do not install Wrangler or create a Wrangler configuration file |
| The user explicitly asks for Wrangler | Wrangler |

The platform rules do not depend on the CLI: limits, the isolate model, bindings, storage
consistency, Durable Object semantics and compatibility dates are the same either way. Where
this skill names a wrangler command or a `wrangler.jsonc` field, find the `cf` equivalent with
`cf cli search "<task>"` or the Wrangler-to-cf reference page instead of translating from
memory. `cf cli search` runs locally without credentials, takes the whole task as **one quoted
argument**, and returns up to five JSON matches, best first. `cf schema <group> <command>`
describes the API request a generated command sends; `--help` covers the rest.

Some Wrangler commands have no `cf` equivalent yet. The reference page lists them; run those
with `npx wrangler` and pass the Worker name, because Wrangler does not read
`cloudflare.config.ts`.

## Setting up cf

- Install globally (`npm install --global cf`) **and** as a development dependency of a `cf`
  project. Inside a project that has `cf` as a dependency, the global command runs the
  project's copy — the same pinning discipline as wrangler, and more important for a beta tool.
- `cf auth login` signs in through a browser approval the user completes. `cf` does **not**
  reuse a Wrangler login. In CI, `CLOUDFLARE_API_TOKEN` takes priority over any stored login,
  and both tools read `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.
- Project configuration is `cloudflare.config.ts`, TypeScript with typed bindings and triggers.
  `cf dev`, `cf build` and `cf deploy` run the framework's own command, the Cloudflare Vite
  plugin (2.0 beta) or Wrangler, depending on the project; builds write Build Output to
  `.cloudflare/output/v0/`. `cf build` uploads nothing and needs no credentials.

## What changes from Wrangler

| Area | Wrangler | `cf` |
|---|---|---|
| Environments | `env.<name>` blocks, `--env <name>` | Modes: a function-form `cloudflare.config.ts` switches on `ctx.mode`; pass `--mode <name>` |
| Resource identifiers | Names for many resources (`wrangler d1 execute my-db`) | The IDs the API expects (`cf d1 query <DATABASE_ID>`) |
| Data commands | Some default to local state | Remote. `--local` works only for supported KV, D1 (`cf d1 raw`, migrations list/apply) and R2 commands; others error instead of calling the API |
| Account | `account_id` in the configuration | Resource commands do not read the Wrangler file; set `CLOUDFLARE_ACCOUNT_ID` or choose when asked |
| Output | Tables, `--json` on some commands | JSON on stdout, messages and errors on stderr |
| Durable Object lifecycle | `exports` or legacy `migrations` | `worker.exports`; `cf migrate` does not convert a `migrations` history |

## Unmigrated Wrangler projects

`cf dev`, `cf build` and `cf deploy` read only `cloudflare.config.ts`. In a project that has a
Wrangler configuration file but no `cloudflare.config.ts` they fail, or auto-generate a
configuration without the Worker's entrypoint and bindings and rewrite `package.json` (the
`deploy` script included), the lockfile, `.gitignore` and `vite.config.ts` — without asking
when there is no terminal, as in CI. So the project keeps `wrangler dev`/`wrangler deploy`
until it is migrated, and migration is the user's call: `cf migrate --dry-run`, then
`cf migrate` (clean working tree; Wrangler 4.136.0+ in the project for the Wrangler bundler),
then resolve every `TODO(@cloudflare)` item in the generated `cloudflare.config.ts` and change
`--env` to `--mode` in scripts and CI. If a `cf` project command already ran, restore the
changed files and delete the new `cloudflare.config.ts`, `wrangler.config.ts` and `.cloudflare/`
before migrating.

Wrangler 4.150+ guards the other direction: `wrangler deploy`, `versions upload` and `preview`
stop when they find `.cloudflare/output` and point at `cf deploy`. If that directory is a stale
leftover, deleting it restores Wrangler deploys.

<!-- sources: cloudflare-skills, cloudflare-docs, workers-sdk -->
