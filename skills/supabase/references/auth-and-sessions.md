# Supabase Auth, sessions and keys

Verified against: `@supabase/supabase-js` 2.x, `@supabase/ssr` 0.7+, `@supabase/server` 1.x.

## Contents

- [API keys and what they authenticate](#api-keys-and-what-they-authenticate)
- [Reading identity: getClaims, getUser, getSession](#reading-identity-getclaims-getuser-getsession)
- [SSR: the cookie contract](#ssr-the-cookie-contract)
- [Framework wiring](#framework-wiring)
- [Where the session goes missing](#where-the-session-goes-missing)
- [Providers, MFA and session controls](#providers-mfa-and-session-controls)
- [Error handling](#error-handling)
- [Old patterns](#old-patterns)

## API keys and what they authenticate

A key says *what* is calling the project; Auth says *who*. Both are needed, and RLS matches on
the Postgres role the key resolves to. [official]

| Key | Format | Postgres role | Where it may appear |
|---|---|---|---|
| Publishable | `sb_publishable_…` | `anon` (no session) / `authenticated` (with session) | Anything you ship: browser, mobile, CLI, source |
| Secret | `sb_secret_…` | `service_role`, which has `BYPASSRLS` | Servers, Edge Functions, cron, workers only |
| `anon` | JWT, starts `eyJ` | same as publishable | Legacy; being retired |
| `service_role` | JWT, starts `eyJ` | same as secret | Legacy; being retired |

- The new keys are short opaque strings, not JWTs. **A snippet telling you to paste a long key
  beginning `eyJ` was written for the legacy pair.** Both systems work at once, and creating new
  keys does not revoke the old ones — that is a separate step in the dashboard.
- A secret key sent with a browser `User-Agent` is rejected with 401. That is a guard, not a
  licence: it does not make the key safe to ship.
- `supabase start` mints local publishable and secret keys unrelated to the hosted project's.
  `supabase status` prints them again.
- Rotation order for a leaked secret key: fix the leak, create the replacement, cut every consumer
  over, confirm, and only then delete the old key. Legacy `anon`/`service_role` keys get
  *deactivated* (reversible) rather than deleted.

## Reading identity: getClaims, getUser, getSession

Three functions, three jobs. Picking the wrong one is the single most common Supabase auth defect.

- `getClaims()` — **use this to protect pages and data.** New projects sign with asymmetric keys,
  so it verifies the JWT signature locally through WebCrypto against a cached JWKS. Claims come
  from decoding the verified token, so there is no per-request round trip.
- `getUser()` — a network call to the Auth server for the freshest user record. Use it when you
  need current user *state* (email confirmed, metadata just changed), not merely identity.
- `getSession()` — returns the raw access token, refresh token and expiry. Use it to forward a
  token to another service. The session is read from storage and **not** revalidated, so its
  embedded `user` object must not drive authorization.

```ts
// Server-side guard
const { data, error } = await supabase.auth.getClaims()
if (error || !data?.claims) return unauthorized()
const userId = data.claims.sub
```

Never make an authorization decision from `user_metadata` / `raw_user_meta_data`: the user can
edit it and it can surface in `auth.jwt()`. Authorization data belongs in `app_metadata`
(`raw_app_meta_data`) or in a custom claim minted by an access-token hook.

Deleting a user does **not** invalidate tokens already issued. Sign the user out or revoke their
sessions, keep the JWT expiry short, and for hard guarantees check `session_id` against
`auth.sessions` on sensitive operations. Likewise, changes to `app_metadata` or custom claims are
not visible until the user's token is refreshed.

## SSR: the cookie contract

Use `@supabase/ssr`. It needs a cookie adapter because it is framework-agnostic, and the adapter
has exactly two methods:

```ts
createServerClient(url, publishableKey, {
  cookies: {
    getAll() {
      return requestCookies.getAll()
    },
    setAll(cookiesToSet, headers) {
      // headers carries Cache-Control / Expires / Pragma — apply them to the response
      for (const { name, value, options } of cookiesToSet) {
        responseCookies.set(name, value, options)
      }
      for (const [name, value] of Object.entries(headers)) {
        response.headers.set(name, value)
      }
    },
  },
})
```

- `setAll` fires whenever the library writes cookies, which is mostly after a token refresh. Its
  second argument is the set of cache headers that must land on the HTTP response; dropping them
  lets a CDN cache a response containing someone's session and serve it to the next visitor.
- The session cookie is named `sb-<project_ref>-auth-token` by default.
- Create a **new server client per request**. On the server the client is essentially a configured
  `fetch` bound to this request's cookies; reusing one across requests hands one user's session to
  another. `createBrowserClient` is already a singleton, so calling it repeatedly is free.

## Framework wiring

The refresh has to happen somewhere that is allowed to write cookies.

- **Next.js** — Server Components cannot write cookies, so a proxy (`proxy.ts`; called middleware
  in older versions) does three things per request: call `supabase.auth.getClaims()` to refresh,
  `request.cookies.set(...)` so Server Components in this render see the fresh token, and
  `response.cookies.set(...)` so the browser replaces the old one. In Server Components, wrap the
  `setAll` body in try/catch and ignore the failure — the proxy is the one that persists it.
- **SvelteKit** — `src/hooks.server.ts` builds a request-scoped client from the request cookies,
  guards protected routes, and exposes it on `event.locals`; the root `+layout.ts` builds the
  client used by both sides.
- **Astro** — static output has no request, session or cookies at build time, so `output: 'server'`
  is a prerequisite before any of this works.
- **Express / Hono / React Router / TanStack Start / Nuxt** — same shape: a per-request client, an
  adapter over that framework's cookie API, and one place that writes refreshed cookies back.

Await the framework's cookie API where it is async (recent Next.js) — a non-awaited cookie store
yields an adapter that silently reads nothing.

## Where the session goes missing

Symptom: policies using `auth.uid()` return no rows through the SDK while the same query works in
the SQL editor. Check in this order, cheapest first.

1. **Is the SQL editor a control?** No. It runs as `postgres`, which has `BYPASSRLS`. A query
   succeeding there proves nothing about `anon` or `authenticated`.
2. **Does the request carry a user at all?** Through the same client, run
   `select auth.uid(), auth.jwt()` (an RPC or a one-row view). `null` means no JWT arrived, and an
   owner-equality policy then matches zero rows without erroring.
3. **Reproduce outside the app.** `curl` the REST endpoint with the publishable key alone, then
   again with `-H "Authorization: Bearer <access_token>"`. If the second call returns rows, the
   policy is fine and the app is not sending the session.
4. **Then look at the adapter.** Legacy per-cookie `get`/`set`/`remove`, a missing proxy, a client
   built once at module scope, or an unawaited cookie store all produce a server client with no
   session.
5. **Distinguish the failure modes.** A missing `GRANT` returns `42501 permission denied`, even for
   `service_role`. A policy that matches nothing returns `200` with `[]`. An empty array is a
   policy or session problem, never a grant problem.

Do not "fix" this by moving the call to a secret key. That disables row-level authorization for
the endpoint rather than repairing the session.

## Providers, MFA and session controls

- OAuth and OIDC providers are configured per project; the redirect target must be in the allowed
  redirect list or the flow fails after the provider, which reads as a provider problem and is not.
- Anonymous sign-ins issue a real session whose Postgres role is `authenticated`. Any check that
  means "is a real user" must test something else — the `is_anonymous` claim, or an
  application-level claim.
- MFA: the enrollment, challenge/verify and list-factors APIs are separate. The result surfaces in
  the JWT `aal` claim — `aal1` for one factor, `aal2` after a second. A token with no `aal` claim
  is `aal1`. Enforce the policy off that claim in the client, the server *and* the database rather
  than in one layer.
- Third-party auth (Clerk and the other supported providers) needs the native integration
  configured so the project verifies that issuer's tokens. Writing an RLS expression against the
  provider's `sub` does not configure verification; without the integration the token is simply
  not trusted.
- Sessions last indefinitely by default. Time-boxing, inactivity timeout and single-session-per-user
  are project settings (Pro and above) enforced at the next refresh, so the effective duration is
  the configured window *plus* the JWT expiry. Keep JWT expiry at 5 minutes or more.

## Error handling

Every `supabase.auth.*` failure is an `AuthError`. Use the `isAuthApiError` helper rather than
`instanceof` (bundling can produce two copies of the class), and branch on the `code` property,
not on the message string — messages are localised and reworded, codes are the contract. `status`
carries the HTTP status.

## Old patterns

<details>
<summary>Patterns you will meet in existing projects, and what replaces them</summary>

- `@supabase/auth-helpers-*` — replaced by `@supabase/ssr`. There is no compatible cookie adapter
  between them; port the client factories rather than shimming.
- The per-cookie adapter `{ get, set, remove }` — replaced by `{ getAll, setAll }`. The old form
  cannot express a multi-cookie write, so chunked sessions get corrupted.
- `getUser()` used purely as a page guard — `getClaims()` does the same verification without the
  round trip. Keep `getUser()` where the fresh record matters.
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY` — legacy JWT keys. New code reads
  `…_PUBLISHABLE_KEY` and `SUPABASE_SECRET_KEY`.
- `auth.role() = 'authenticated'` inside a policy — deprecated, and broken once anonymous
  sign-ins are on. Use the `TO` clause.

</details>

<!-- sources: supabase-official-skill, supabase-docs, tushar-skills, magnus-agent-skills -->
