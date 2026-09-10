# Supabase Edge Functions

Verified against: Supabase CLI 2.117, `@supabase/server` 1.x, Deno runtime.

## Contents

- [Runtime shape](#runtime-shape)
- [Auth modes and verify_jwt](#auth-modes-and-verify_jwt)
- [Secrets and injected variables](#secrets-and-injected-variables)
- [CORS](#cors)
- [Limits that shape the design](#limits-that-shape-the-design)
- [Local development](#local-development)
- [Deploying](#deploying)
- [Deno-specific traps](#deno-specific-traps)
- [Old patterns](#old-patterns)

## Runtime shape

Functions are TypeScript on Deno — there is no other language option. The current entry point is
a default export with a `fetch` handler wrapped by `withSupabase`, which is what
`supabase functions new <name>` scaffolds:

```ts
import { withSupabase } from 'npm:@supabase/server'

export default {
  fetch: withSupabase({ auth: 'user' }, async (req, ctx) => {
    // ctx.supabase       — scoped to the caller's RLS policies
    // ctx.supabaseAdmin  — bypasses RLS
    // ctx.userClaims     — id, email, role from the verified JWT
    // ctx.jwtClaims      — the full claim set
    // ctx.authMode       — which declared mode matched
    return Response.json({ email: ctx.userClaims?.email })
  }),
}
```

`withSupabase` earns its place by doing three things you would otherwise hand-roll: it verifies
the caller's credentials against the declared mode, it builds both clients without any key
appearing in your source, and it answers CORS preflight.

For a bespoke 401 body, use `createSupabaseContext(req, { auth: 'user' })`, which returns
`{ data, error }` and leaves the response to you. When the SDK is not an option at all, fall back
to `export default { fetch }` plus explicit CORS headers.

## Auth modes and verify_jwt

Two independent checks run: the platform's `verify_jwt` gate (before your code) and the SDK's
`auth` mode (inside it). They must agree.

| `auth` | Accepts | `verify_jwt` |
|---|---|---|
| `'user'` | user JWT on `Authorization` | `true` (default) |
| `'secret'` | secret key on `apikey` | `false` |
| `'publishable'` | publishable key on `apikey` | `true` or `false` |
| `'none'` | anyone, no check | `false` |

- **User-facing function** — called through `supabase.functions.invoke` from a signed-in client.
  Keep `verify_jwt = true` and use `auth: 'user'`.
- **Service-to-service** — cron, a worker, `pg_net`, another function. These send a secret key on
  `apikey` and no user JWT, so `verify_jwt = true` rejects them before your handler runs. Set
  `verify_jwt = false` and `auth: 'secret'`. Narrow it to one named key with `auth: 'secret:jobs'`.
- **External webhook** (Stripe, GitHub) — the provider sends its own signature and no Supabase
  credentials. `auth: 'none'` plus `verify_jwt = false`, and then **your handler is solely
  responsible for authenticating the caller** by verifying the provider signature. Never leave
  `auth: 'none'` on an endpoint that reads or writes real data without such a check.
- **Both** — pass an array, `auth: ['user', 'secret']`; modes are tried in order, first match
  wins, and `ctx.authMode` tells you which.

```toml
# supabase/config.toml
[functions.stripe-webhook]
verify_jwt = false
```

Per-function config lives under `[functions.<name>]`. A function with no entry inherits
`verify_jwt = true`, which is why webhooks "fail with 401 before the function runs".

## Secrets and injected variables

Read with `Deno.env.get(...)`. The platform injects:

| Variable | Contents |
|---|---|
| `SUPABASE_URL` | project API gateway |
| `SUPABASE_PUBLISHABLE_KEYS` | JSON object of named publishable keys |
| `SUPABASE_SECRET_KEYS` | JSON object of named secret keys |
| `SUPABASE_JWKS` | key set used to verify user JWTs |
| `SUPABASE_DB_URL` | direct Postgres connection string |
| `SB_REGION`, `SB_EXECUTION_ID`, `DENO_DEPLOYMENT_ID` | hosted-only request/isolate metadata |

The key variables are **dictionaries**, so a hand-built client indexes into them:

```ts
const secretKeys = JSON.parse(Deno.env.get('SUPABASE_SECRET_KEYS')!)
const admin = createClient(Deno.env.get('SUPABASE_URL')!, secretKeys['default'])
```

`SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_ROLE_KEY` still exist but carry the legacy keys; reading
them keeps a new function on the deprecated path. Inside a function, preferring `ctx.supabaseAdmin`
from `withSupabase` avoids the question entirely.

Your own secrets:

```bash
supabase secrets set STRIPE_SECRET_KEY=sk_live_…   # one at a time
supabase secrets set --env-file .env                # or a whole file
supabase secrets list
```

Secrets apply immediately — no redeploy needed. Locally they come from
`supabase/functions/.env` (loaded by `supabase start`) or `--env-file`. A local `.env` never
reaches the deployed function; that is the usual reason a secret is "missing in production".
Keep every such file out of git.

## CORS

A browser call to a function that does not answer `OPTIONS` fails **before** the handler runs, so
the function looks broken while its logs stay empty. `withSupabase` handles preflight. Otherwise
import the header set from the SDK so it tracks what the clients actually send:

```ts
import { corsHeaders } from 'npm:@supabase/supabase-js@^2/cors'

export default {
  fetch: async (req) => {
    if (req.method === 'OPTIONS') return Response.json({ ok: true }, { headers: corsHeaders })
    return Response.json({ ok: true }, { headers: corsHeaders })
  },
}
```

A hand-written allow-list must cover `authorization`, `apikey`, `x-client-info`, `content-type`,
`x-retry-count` (postgrest-js retries idempotent requests) and, if any client opts into trace
propagation, `traceparent`, `tracestate`, `baggage`. Importing from the SDK means a redeploy picks
up newly added headers instead of breaking on them.

## Limits that shape the design

| Limit | Value |
|---|---|
| Memory | 256 MB |
| **CPU time per request** | ~2 s |
| Wall clock | 150 s on the free plan, 400 s on paid plans |
| Request idle timeout | 150 s — no response by then returns 504 |

CPU time excludes async I/O, so waiting on a third-party API does not consume it — but parsing a
large payload, hashing, or image work does. **CPU time is usually what you hit first**, and it is
the limit people misdiagnose as a network timeout. Anything genuinely long-running belongs behind
a queue with the function returning immediately.

## Local development

```bash
supabase start                                    # whole stack; needs Docker
supabase functions serve <name>                   # hot reload
supabase functions serve <name> --env-file .env.local
```

The function answers at `http://127.0.0.1:54321/functions/v1/<name>`; the local publishable key is
in `supabase status`. If a function will not start, the answer is almost always Docker not running
or a port already held by another local stack (`supabase stop`, then `supabase start`).

Shared code goes in `supabase/functions/_shared/`; directories starting with `_` are not deployed
as functions.

## Deploying

```bash
supabase functions deploy <name>      # one function
supabase functions deploy             # every function
supabase functions deploy <name> --use-api   # skip the Docker build path explicitly
```

Deployment falls back to API-based deploy automatically when Docker is unavailable. The deployed
URL is `https://<project-ref>.supabase.co/functions/v1/<name>`.

## Deno-specific traps

- **A request body can be read once.** Calling `req.json()` and then `req.text()` gives the second
  reader nothing. Webhook handlers need the raw text for signature verification, so read
  `await req.text()` once and `JSON.parse` it yourself.
- **Stripe's synchronous `constructEvent` cannot work here.** Deno has no synchronous Node crypto,
  so it throws `SubtleCryptoProvider cannot be used in a synchronous context`. Use
  `constructEventAsync` with `Stripe.createSubtleCryptoProvider()`.
- Prefer `npm:` specifiers over `https://esm.sh/…`: they resolve through the runtime's own
  resolver, pin cleanly and cache better.
- Log the reason when signature verification fails. Otherwise a configuration mistake and a forged
  payload are indistinguishable in the logs.

## Old patterns

<details>
<summary>Shapes you will find in existing functions</summary>

- `serve()` imported from `https://deno.land/std@…/http/server.ts`, then `Deno.serve(handler)` —
  both predate the `withSupabase` default export. They still run; new functions should not use
  them.
- `createClient(url, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'))` — legacy key path. Use
  `ctx.supabaseAdmin`, or `SUPABASE_SECRET_KEYS['default']` when building the client by hand.
- `--no-verify-jwt` on `functions deploy` / `functions serve` — superseded by `verify_jwt` under
  `[functions.<name>]` in `config.toml`, which is checked in and reviewable.
- A hand-copied `_shared/cors.ts` — fine before `@supabase/supabase-js` 2.95, stale after it.

</details>

<!-- sources: supabase-docs, supabase-server-sdk, supabase-official-skill, quinto-realtime -->
