# Configuration and secrets

Verified against: Node.js 24 LTS

## Contents

- [Read once, validate, freeze](#read-once-validate-freeze)
- [Loading .env without a dependency](#loading-env-without-a-dependency)
- [Units and types](#units-and-types)
- [One variable per concern, not NODE_ENV](#one-variable-per-concern-not-node_env)
- [What NODE_ENV still legitimately controls](#what-node_env-still-legitimately-controls)
- [Secret delivery](#secret-delivery)
- [.env files in the repository](#env-files-in-the-repository)
- [Configuration in tests](#configuration-in-tests)

## Read once, validate, freeze

Configuration is boot-time input. Read it in one module, validate the whole set
against a schema, and export one frozen typed object. Everything else imports
that object and never touches `process.env`.

```ts
import { z } from 'zod'

const Schema = z.object({
  PORT: z.coerce.number().int().positive().default(3000),
  DATABASE_URL: z.url(),
  DATABASE_POOL_MAX: z.coerce.number().int().positive().default(10),
  LOG_LEVEL: z.enum(['trace', 'debug', 'info', 'warn', 'error']).default('info'),
  LOG_PRETTY: z.stringbool().default(false),
  DRAIN_TIMEOUT_MS: z.coerce.number().int().positive().default(25_000),
})

const parsed = Schema.safeParse(process.env)
if (!parsed.success) {
  // One message listing every problem beats one-at-a-time discovery.
  console.error('invalid configuration', z.treeifyError(parsed.error))
  process.exit(1)
}

export const config = Object.freeze({
  port: parsed.data.PORT,
  logging: { level: parsed.data.LOG_LEVEL, pretty: parsed.data.LOG_PRETTY },
  database: { url: parsed.data.DATABASE_URL, poolMax: parsed.data.DATABASE_POOL_MAX },
  drainTimeoutMs: parsed.data.DRAIN_TIMEOUT_MS,
})
```

Why each part matters:

- **One module.** `process.env.FEATURE_X` scattered through handlers cannot be
  inventoried, typed or tested, and a typo reads as `undefined` forever.
- **Validate everything at once.** Reporting all failures in one message turns
  a five-deploy discovery loop into one fix.
- **Exit non-zero on failure.** A service that boots with half its
  configuration fails later, in a request, with an error that describes a
  symptom rather than the cause.
- **Freeze.** Configuration that code can mutate is global mutable state and
  will be mutated by a test.

`env-schema` with TypeBox is the equivalent in a JSON-Schema project, and
NestJS's `ConfigModule` takes a `validationSchema` — use whichever the project
already has. The invariant is boot-time validation, not the library.

## Loading .env without a dependency

Node loads env files natively; no `dotenv` needed:

```bash
node --env-file=.env src/main.ts                       # Node 20.6+
node --env-file=.env --env-file=.env.local src/main.ts # later files win
node --env-file-if-exists=.env.local src/main.ts       # Node 22.9+, no failure if absent
```

Programmatically, `process.loadEnvFile([path])` does the same thing (Node
20.12+). Both only *add* to `process.env`; neither validates, so the schema
above still runs.

In production the file usually does not exist — the platform injects the
variables — which is why `--env-file-if-exists` matters in a shared start
script.

## Units and types

Everything in `process.env` is a string. Two consequences worth encoding in the
schema:

- **Coerce and constrain.** `z.coerce.number()` turns `"3000"` into `3000`;
  without the constraint, `PORT=abc` becomes `NaN` and the server binds to a
  random port.
- **Booleans are not `Boolean(string)`.** `Boolean('false')` is `true`. Parse
  explicitly (`z.stringbool()`, or a compare against `'true'`), never
  `!!process.env.FLAG`, which is true for `"0"` and `"false"` alike.

Put units in the variable name (`DRAIN_TIMEOUT_MS`, `CACHE_TTL_S`,
`MAX_BODY_BYTES`). A bare `TIMEOUT=30` is a factor-of-1000 outage waiting for
the first person to assume the other unit.

## One variable per concern, not NODE_ENV

`NODE_ENV` collapses unrelated decisions into one string:

```ts
if (process.env.NODE_ENV === 'development') {
  enableVerboseLogging()   // logging
  disableRateLimiting()    // security
  useMockPaymentGateway()  // infrastructure
}
```

Now a staging environment that wants verbose logging also gets rate limiting
off, and nobody notices until it is public. Split them:

```ts
logging.level        // LOG_LEVEL
security.rateLimit   // RATE_LIMIT_ENABLED
payments.gateway     // PAYMENTS_GATEWAY=stripe|mock
```

Each flag is then independently settable, discoverable in the schema, and
switchable in a test without pretending to be a different environment.

## What NODE_ENV still legitimately controls

Do not delete it — several things outside your code read it:

- Package managers install without dev dependencies when it is `production`.
- Some libraries switch off development-only checks and warnings based on it.
- Framework defaults key off it (for example, whether stack traces appear in
  error pages of frameworks that do that).

So keep `NODE_ENV=production` set in production images, and hang no application
behaviour on it. The test is simple: if changing `NODE_ENV` alone would change
what your API returns, that is a bug.

## Secret delivery

Secrets reach the process at runtime, as environment variables or as files
mounted into the container. Whichever the platform provides — cloud secret
manager, Vault, orchestrator secrets, CI variables — the application's job is
the same: read at boot, validate presence, never persist.

Rules that are cheap to follow and expensive to skip:

- Never bake a secret into an image or commit one, including in a test fixture
  or a comment. Assume anything committed is public forever.
- Never log configuration wholesale. `log.info({ config }, 'starting')` prints
  the database password. Log a redacted summary, or nothing.
- Never return configuration from an endpoint, including a debug or health
  endpoint.
- Never use a secret, a token or a user id as a metric label — that is both a
  leak and one time series per value.
- Rotate by re-reading at boot, not by hot-reloading a live value; a process
  that re-reads secrets mid-flight has two versions in memory and no way to tell
  which a given request used.

For a file-mounted secret, read it once at boot into the config object. Reading
it per request turns every request into a filesystem call, and reading it
synchronously breaks rule 21.

## .env files in the repository

- `.env.example` is committed, lists every variable with a safe placeholder,
  and is the actual documentation for the schema.
- `.env` is local and git-ignored.
- `.env.test` may be committed only if it contains no real credentials.

Keeping `.env.example` in step with the schema is not busywork: it is what makes
a new environment reproducible, and the schema will fail the boot when they
diverge.

## Configuration in tests

A test that needs different configuration should get it by constructing the
component with different values (rule 17), not by mutating `process.env` in a
hook. Mutating the environment leaks into every later test in the same process
and makes ordering significant.

Where a module reads `config` at import time, the seam is the factory: pass the
config object into `buildApp(config)` so a test can build an app with a stub
gateway and a two-connection pool without touching the environment at all.

<!-- sources: mcollina-skills, kadajett-nestjs, nodejs-docs, nestjs-docs -->
