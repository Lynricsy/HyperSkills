---
name: cloudflare
description: "Builds on Cloudflare Workers, Durable Objects, storage services and Wrangler."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: platform
---

# cloudflare

## Scope

Covers the Cloudflare developer platform as a control plane and a runtime: the Workers
isolate model and its limits, `wrangler` configuration and CLI, bindings, Durable Objects
(runtime semantics and class lifecycle), the storage products and how to choose between them
on consistency and quota grounds, Workers static assets and the migration off Pages,
Cloudflare's own observability surface, Workers testing, and Cloudflare One — Access, Gateway,
the device client and Tunnel.

Verified against **wrangler 4.131.0** with **workerd 1.20260910.1**. Rules that need a newer
tool than the 4.x line carry a gate such as `(Wrangler 4.107+)`. Limits and defaults were
re-read from the official documentation rather than recalled; every claim is marked
`[verified]` (reproduced locally, see `## Environment`), `[official]` (documentation only) or
`[community]`.

Not covered:

- General web performance, Core Web Vitals and visual design. Use the `frontend-design`
  skill. This skill covers only the Cloudflare-side levers (asset caching headers, Smart
  Placement, `cacheTtl`).
- React and Next.js themselves. Use the `react` skill. On Cloudflare, Next.js deploys as a
  Worker with static assets through an adapter, not to Pages; the adapter is the only part of
  that which belongs here.
- Node.js server frameworks (Express, Fastify, Hono routing design). Use the
  `nodejs-backend` skill. The `nodejs_compat` flag and what it does to imports belongs here.
- AWS, Azure and Google Cloud. Use the `aws`, `azure` and `gcp` skills. Cross-cloud
  comparison gets a sentence at most.
- OpenTelemetry instrumentation, semantic conventions, Collector configuration, RED/USE
  metrics, SLOs and alert design. Use the `observability` skill. What belongs here is the
  Cloudflare product surface: Workers Logs, traces, Tail Workers, Logpush, `wrangler tail`
  and their quotas and configuration fields.
- HCL, Terraform modules and state. Use the `terraform` skill. Cloudflare's native
  declarations (`wrangler.jsonc`, the `exports` map, the Access and Gateway APIs) belong here.
- Dockerfiles, Compose, Kubernetes manifests and Helm. Use the `containers` skill.
- The Cloudflare Agents SDK, Workers AI, AI Gateway, Vectorize and building MCP servers on
  Workers. No skill in this library covers them yet; say so rather than improvising.
- The network and security product surface — CDN cache rules, WAF, DDoS, Bot Management,
  Turnstile, Stream, Zaraz. Not covered here either.

Paths below are relative to this skill's directory.

## Read first

`references/limits-and-versions.md` is the quota and version-gate index. Read it before
quoting any number or any "since version X" claim — most Cloudflare regressions in agent
output are a stale limit or a retired plan name, not a wrong API call.

## Core rules

1. Establish the toolchain before quoting anything: the project's own wrangler version
   (`npx wrangler --version`), its `compatibility_date` and `compatibility_flags`, and
   `node_modules/wrangler/config-schema.json` for which configuration fields exist. A field
   that is not in the installed schema does not exist for this project, whatever the docs say.
2. Prefer retrieval over recall for API surface and limits. Cloudflare ships runtime changes
   several times a week; the installed `wrangler --help` and the generated
   `worker-configuration.d.ts` are the project's truth, and `developers.cloudflare.com` is the
   platform's.
3. Nothing request-scoped may live in module scope. Isolates are reused across requests from
   different users, so a module-level `let` assigned inside a handler leaks one user's data to
   the next and, if it holds an I/O object, fails outright: `Cannot perform I/O on behalf of a
   different request` `[verified]` (`references/workers-runtime.md`).
4. Every promise is awaited, returned, or handed to `ctx.waitUntil()`. A floating promise is
   cancelled when the response completes and its rejection is swallowed. `waitUntil` extends
   execution for up to 30 seconds after the response or a client disconnect `[official]`.
5. Never destructure `ctx`. `const { waitUntil } = ctx` loses the receiver and throws
   `Illegal invocation` at call time `[verified]`.
6. CPU time is not wall time, and the numbers are: Workers Free is fixed at 10 ms; Workers
   Paid defaults to 30 s and can be raised to 5 minutes with `limits.cpu_ms: 300000`. Time
   spent waiting on `fetch`, KV, D1 or R2 does not count. Wall time is unlimited for HTTP
   requests and 15 minutes for Cron Triggers, Queue consumers and Durable Object alarms
   `[official]`. The retired Bundled/Unbound usage-model names are not an answer.
7. Memory is 128 MB per isolate, not per request. Buffering an unbounded body with
   `await response.text()` or `request.arrayBuffer()` is how Workers OOM; pass `response.body`
   through or use a `TransformStream` `[official]`.
8. Reach for the binding, never the Cloudflare REST API, for anything a binding exposes. A
   binding is in-process, needs no token, and does not consume the account-level credential
   that an API call would have to carry.
9. Six connections may be waiting for response headers at once. A seventh queues. Fan-out
   past six concurrent `fetch`/KV/R2/Queues calls serialises silently rather than erroring
   `[official]`.
10. Keep `compatibility_date` current on new Workers and treat advancing it on an existing
    Worker as a behaviour change: read the intervening compatibility flags and test. A Worker
    uploaded through the API without a date defaults to **2021-11-02**, before any flag took
    effect `[official]`.
11. Secrets never appear in `vars`. Configuration files are committed and `vars` are plaintext
    on the deployed Worker. Use `wrangler secret put`, a Secrets Store binding, or
    `--secrets-file`; local values go in `.dev.vars` or `.env`, both gitignored. A leaked value
    is rotated, not edited out (`references/wrangler.md`).
12. `wrangler secret put` and `secret delete` create a version **and deploy it immediately**.
    When a change must be staged, use `wrangler versions secret put` and then
    `wrangler versions deploy` `[official]`.
13. Bindings and `vars` are non-inheritable: an environment that does not redeclare them does
    not have them. An environment also deploys a *separate* Worker named
    `<name>-<environment>`, so a service binding aimed at an environment must name
    `<target>-<environment>` `[official]`.
14. Generate `Env` with `wrangler types`, never by hand. It writes
    `worker-configuration.d.ts` from the configuration plus the runtime types for the
    configured compatibility date and flags, and re-running it is how a renamed binding
    becomes a type error instead of a runtime `undefined` `[verified]`.
15. Declare resource ids explicitly. An omitted id can trigger automatic provisioning, which
    creates a *new* empty resource instead of binding the existing one `[community]`.
16. `wrangler dev` is local by default (`--remote` defaults to false) and needs no account:
    workerd serves the Worker and KV, D1, R2, Durable Object and Cache state persists as
    SQLite under `.wrangler/state/v3/` `[verified]`. Local KV is read-after-write consistent,
    so an eventual-consistency bug cannot reproduce there — that is a property of the
    simulator, not evidence the code is correct.
17. Choose storage by consistency requirement, not by familiarity. KV is an eventually
    consistent read cache: a write is usually visible immediately where it was made but takes
    **up to 60 seconds or more** elsewhere, negative lookups are cached the same way, and the
    same key accepts **1 write per second**. It cannot implement a counter, a lock or a queue
    (`references/storage-selection.md`).
18. Anything needing atomicity or ordering goes to a Durable Object, sharded by the entity it
    coordinates. One object is single-threaded and serialises its own requests; it has a soft
    limit of about 1,000 requests per second and returns `overloaded` beyond that, so the shard
    key decides whether the design scales.
19. In a Durable Object, persist before caching: write to `ctx.storage` and only then update
    the in-memory copy. Use `blockConcurrencyWhile()` for constructor-time schema setup only —
    holding it across a `fetch` or per request destroys throughput.
20. One alarm per object. `setAlarm()` replaces any pending alarm, and the handler is retried
    on failure, so it must be idempotent and must record its own progress in the same storage
    write (`references/durable-objects.md`).
21. Declare Durable Object class lifecycle with the `exports` map (Wrangler 4.107+):
    `state: "created" | "deleted" | "renamed" | "transferred" | "expecting-transfer"`.
    `exports` and the legacy `migrations` array are mutually exclusive — a configuration with
    both is rejected at validation `[verified]` — and once a Worker has deployed with
    `exports` it cannot go back (`references/do-lifecycle.md`).
22. A rename is a rename. Deleting a class destroys its namespace and every object's data
    permanently, with no trash; expressing a rename as delete-plus-create is data loss that
    deploys cleanly. Rename over three deploys so the class pointer and the code never
    disagree.
23. New Durable Object namespaces are SQLite-backed (`storage: "sqlite"`). The key-value
    backend is unavailable to accounts without an existing key-value namespace, storage type is
    immutable once provisioned, and `storage_type_mismatch` is the error for trying `[official]`.
24. Workers serves static assets **before** the Worker script; Pages ran Functions first. An
    authentication check that ran as Pages middleware stops running on asset paths after the
    migration unless `assets.run_worker_first` is set, and `not_found_handling` must be
    declared because Workers infers nothing from `index.html` or `404.html`
    (`references/static-assets.md`).
25. `_headers` and `_redirects` do not apply to responses generated by Worker code. Under SSR
    or `run_worker_first`, security headers and redirects have to be set in the Worker as well,
    or the migration drops them silently `[official]`.
26. A rollback replaces code, not data: connected resources are untouched, only the 100 most
    recent versions are reachable, and a rollback cannot cross a Durable Object lifecycle
    change. Design the schema change to be backward compatible instead of relying on rollback.
27. Enable observability before the incident: `observability.enabled` does **not** enable
    traces — `observability.traces.enabled` is a separate field — and log as structured JSON
    so the entries are queryable (`references/observability.md`).
28. Test in the runtime, not in Node: `@cloudflare/vitest-plugin` (v1; it replaces
    `@cloudflare/vitest-pool-workers`) runs tests inside workerd with real bindings, and
    `createTestHarness()` exercises whole Workers `[official]`
    (`references/testing.md`).

## Workflows

### review-a-worker-for-production

- [ ] Read the configuration first: `compatibility_date` and flags, `limits`, `observability`,
      whether secrets sit in `vars`, whether every `env.X` in the code has a binding and every
      binding is declared per environment (`references/wrangler.md`).
- [ ] Scan module scope. Any mutable `let`/`var` assigned inside a handler is a cross-request
      leak; any cached stream, `Request`, `Response` or socket is a
      `Cannot perform I/O on behalf of a different request` waiting to happen.
- [ ] Trace every promise to an `await`, a `return`, or `ctx.waitUntil()`, and check `ctx` is
      never destructured.
- [ ] Check the byte paths: unbounded `text()`/`json()`/`arrayBuffer()` against the 128 MB
      isolate limit, and value sizes against the target store's limit
      (`references/limits-and-versions.md`).
- [ ] Check the boundaries: REST API calls that a binding would do better, more than six
      concurrent subrequests, `Math.random()` for anything security-bearing, secret comparison
      without `crypto.subtle.timingSafeEqual` over equal-length digests.
- [ ] Check the failure posture: `passThroughOnException()` is fail-open to the origin and
      hides the bug being investigated; errors should be caught and returned structured.
- [ ] **Gate — the change type-checks against generated types and packages:**
      `npx wrangler types` then the project's typecheck, and
      `npx wrangler deploy --dry-run --outdir=dist` exits 0 and prints the expected binding
      table. A dry run proves the bundle and the configuration, not the runtime.

### choose-a-storage-product

- [ ] Write down the access pattern in numbers: writes per second to the *same* key, reads per
      second, value size, total size, and whether a reader may see a stale value
      (`references/storage-selection.md`).
- [ ] Eliminate on consistency first. Read-modify-write, counters, locks, leases and ordering
      rule out KV and R2 regardless of volume; they need a Durable Object.
- [ ] Eliminate on quota second: KV value 25 MiB, D1 database 10 GB and one query at a time,
      Durable Object 10 GB per object with key+value ≤ 2 MB, R2 object 5 TiB but 1 write per
      second to the same key, Queues message 128 KB.
- [ ] Pick the shard key before the product. "One Durable Object per team" and "one D1 per
      tenant" are the designs that scale; one global instance of either is the design that
      returns `overloaded`.
- [ ] Keep the read-heavy configuration lookups in KV where it is genuinely the right tool,
      and raise `cacheTtl` above its 60-second default for values that change rarely.
- [ ] **Gate — the design states its staleness budget:** for each read path, say how stale a
      value may be and which product's documented guarantee provides it. An unstated staleness
      budget is how a KV counter gets shipped.

### add-or-change-a-durable-object-class

- [ ] Identify the coordination atom and make it the object: a room, a match, a tenant, a
      user. Not a service (`references/durable-objects.md`).
- [ ] Decide the lifecycle route explicitly. A Worker already on `migrations` either stays
      there or converts the whole map to `exports` — the conversion needs no data migration but
      is one-way (`references/do-lifecycle.md`).
- [ ] Write the `exports` entry and the binding together. A class exported by the code but
      absent from `exports` is never provisioned, and `storage: "sqlite"` is required on live
      entries.
- [ ] For a rename, sequence three deploys: alias the old name to the new class, apply the
      `renamed` tombstone while the alias is live, then remove the alias.
- [ ] Make alarms idempotent and re-arm them in one place. Re-arming on every incoming request
      pushes the deadline out forever, because `setAlarm()` replaces rather than adds.
- [ ] For WebSockets, use the Hibernation API (`ctx.acceptWebSocket()`,
      `ctx.getWebSockets()`, `serializeAttachment`) so an idle room stops accruing duration
      charges, and keep the constructor cheap because hibernation re-runs it.
- [ ] **Gate — lifecycle changes go out alone:** `wrangler deploy` (not
      `wrangler versions upload`, which refuses lifecycle changes), one lifecycle change per
      deploy, and the reconciliation block in the output says what you intended.

### migrate-pages-to-workers-static-assets

- [ ] Count the build output against the hard limits first, because they fail a deploy rather
      than throttle it: 20,000 asset files per Worker version on Free and 100,000 on Paid,
      25 MiB per individual file (`references/static-assets.md`).
- [ ] Replace `pages_build_output_dir` with `assets.directory`, add a `compatibility_date`
      (carrying over the Pages Functions date if one was set), and turn on observability in the
      same edit — `observability.enabled` plus `observability.traces.enabled`, per environment.
- [ ] Declare serving behaviour that Pages used to infer: `not_found_handling` as
      `single-page-application` or `404-page`, and `run_worker_first` if anything must run
      before assets are served.
- [ ] Convert the Functions directory: `wrangler pages functions build --outdir=...` to
      compile it, or rewrite it as a Worker entry. `_routes.json` has no equivalent —
      `run_worker_first` is the replacement.
- [ ] Re-apply `_headers` and `_redirects` inside the Worker for every path the Worker itself
      answers, and keep both files in the asset directory for the paths it does not.
- [ ] Add `.assetsignore` for anything that must not be uploaded — a `_worker.js` inside the
      asset directory, plus the `node_modules`, `.git` and `.DS_Store` entries Pages excluded
      for you.
- [ ] Re-declare bindings and `vars` for every environment: they do not inherit, so a Pages
      project that only set `env.preview.vars` loses its other bindings in preview.
- [ ] **Gate — the acceptance criteria are exercised, not assumed:** run `wrangler dev` and
      curl an asset path, a deep SPA route, each redirect, and a protected path with and
      without credentials, asserting the headers and status codes you claimed.

### diagnose-a-production-only-failure

- [ ] Separate "not reproducible locally" from "works locally". Local KV is read-after-write
      consistent, local D1 and Durable Objects are single-process, and there is no global
      propagation — so consistency, contention and quota failures cannot appear there
      `[verified]`.
- [ ] Get the invocation outcome before theorising: `exceededCpu`, `exceededMemory`,
      `scriptNotFound`, `canceled`, `exception`. It is in Workers Logs, in the Trace Events
      Logpush dataset, and in the dashboard's Invocation Statuses
      (`references/observability.md`).
- [ ] Match the outcome to a limit rather than to the code: `exceededCpu` against
      `limits.cpu_ms`, `exceededMemory` against buffering, `1027` against the Free daily
      request cap, `429` from a store against its per-key write rate.
- [ ] Check what changed in the deployment, not only in the code: a gradual deployment serving
      two versions, a dashboard edit that `wrangler deploy` overwrote or is about to overwrite,
      a secret that deployed itself when it was set.
- [ ] Where only production signals exist, stay in the signals: `wrangler tail` for a live
      stream, Workers Logs for the query, a Tail Worker or the OTel export for retention. Use
      the `debugging` skill once there is a local reproduction, and the `observability` skill
      for the instrumentation and alerting pipeline itself.
- [ ] **Gate — the diagnosis names a signal:** every conclusion cites a log field, an
      invocation outcome, or a documented limit with its number. "Probably the isolate" is not
      a diagnosis.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Every quota, default and version gate in one table: CPU and wall time, memory, subrequests, asset and store limits, the wrangler/compat-date gates, retired names | Before quoting any number or any "since version X" claim | `references/limits-and-versions.md` |
| Isolate lifecycle, request-scoped I/O, `waitUntil` and `passThroughOnException`, streaming, crypto, service bindings and RPC, Smart Placement, Cron Triggers, `nodejs_compat` | Writing or reviewing Worker code, or explaining a runtime error | `references/workers-runtime.md` |
| Configuration shape and schema, compatibility dates and flags, binding declarations, environments and non-inheritable keys, secrets and `.dev.vars`/`.env`, `limits`, `observability`, `wrangler types`, auto-provisioning | Editing `wrangler.jsonc`/`wrangler.toml` or adding a binding | `references/wrangler.md` |
| Local versus remote dev and where state lives, data commands, `deploy --dry-run`, versions and gradual deployments, rollback constraints, secret commands, diagnostics | Running wrangler, deploying, or recovering a deployment | `references/wrangler.md` |
| Durable Object modelling and sharding, stub creation, SQLite and key-value storage APIs, input/output gates and `blockConcurrencyWhile`, alarms, WebSocket hibernation, RPC | Writing or reviewing Durable Object code | `references/durable-objects.md` |
| The `exports` lifecycle map, each `state` and its required fields, safe rename and transfer sequences, storage backends, reconciliation output, legacy `migrations` and converting off it | Adding, renaming, deleting or moving a Durable Object class | `references/do-lifecycle.md` |
| KV, R2, D1, Durable Object storage, Queues and Hyperdrive side by side: consistency guarantee, per-key write rate, size ceilings, failure mode, and the decision table | Choosing a store, or explaining why the current one cannot work | `references/storage-selection.md` |
| `assets` configuration, routing modes, `_headers` and `_redirects` semantics and limits, `.assetsignore`, default asset headers, Pages-to-Workers migration and the compatibility matrix | Serving static assets, or migrating off Pages | `references/static-assets.md` |
| Workers Logs and traces configuration and sampling, invocation outcomes, `wrangler tail`, Tail Workers, Logpush datasets, the OTel export, and where the boundary with the `observability` skill falls | Instrumenting a Worker, or diagnosing from production signals | `references/observability.md` |
| `@cloudflare/vitest-plugin` setup and the rename from `vitest-pool-workers`, isolated storage, testing Durable Objects and queues, mocking outbound requests, `createTestHarness()` | Writing or fixing tests for a Worker | `references/testing.md` |
| Access applications and policies, Gateway policy types and order of enforcement, device profiles and split tunnel, service tokens, `cloudflared` quick and named tunnels, log surfaces | Configuring or troubleshooting Zero Trust access or a tunnel | `references/cloudflare-one.md` |

## Output format

When reviewing Worker code or configuration, group findings by file and lead with the
consequence, not the rule name:

```
src/index.ts:10 - cross-request leak - `let cachedUser` is module scope, so the isolate
  serves the first user's session to every later request it handles. Measured locally:
  /cache?u=alice then ?u=bob both return {"id":"alice"}. Move it inside fetch().

wrangler.toml:11 - throughput - limits.cpu_ms = 50 caps CPU at 50 ms against a Paid default
  of 30000 ms, so /report terminates with exceededCpu (Error 1102) as the table grows.
  Remove the override or raise it; the 5 min ceiling is 300000.
```

Order findings by blast radius: data leaks and credential exposure first, then anything that
already returns 5xx, then quota ceilings that will be hit, then maintainability. Quote the
evidence — the exact runtime error string, the invocation outcome, the documented limit with
its number — rather than asserting it. When a number is involved, give the number.

Say explicitly when something is fine as written. `wrangler.toml` versus `wrangler.jsonc`, a
`for await` versus `pipeTo`, `getByName()` versus `idFromName()` plus `get()` — these are two
spellings of the same thing, and reporting them buries the findings that matter.

## Environment

- `npx wrangler --version` is the first command of any diagnosis; pin wrangler in
  `devDependencies` and run it through the project's package manager so CI and the laptop
  agree.
- Local development needs no Cloudflare account and no real resource ids. `wrangler dev`
  simulates KV, R2, D1, Durable Objects and the Cache in workerd and persists them under
  `.wrangler/state/v3/`, which must be gitignored. `--persist-to` moves that directory.
- `wrangler deploy --dry-run --outdir=dist` builds, validates the configuration, prints
  `Total Upload` and the binding table, and never contacts the API — this is the check a pull
  request can run.
- `npx wrangler types` writes `worker-configuration.d.ts` containing both the binding
  interface and the runtime types for the configured compatibility date and flags. It is
  generated output: re-run it after any binding change instead of editing it.
- `wrangler kv`, `wrangler d1` and `wrangler r2` data commands take `--local` and `--remote`.
  Pass the one you mean: with no flag and no login they operate on the local state directory,
  which looks like success while touching nothing real.
- `cloudflared` is a separate binary from wrangler and is required for Tunnel work; check for
  it with `cloudflared --version` before writing tunnel instructions.
