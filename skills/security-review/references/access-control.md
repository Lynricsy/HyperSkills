# Authentication and authorization defects

Verified against: OWASP Top 10 2025, ASVS 5.0.0

## Contents

- [The two questions](#the-two-questions)
- [Object-level authorization (IDOR / BOLA)](#object-level-authorization-idor--bola)
- [Finding the missing check](#finding-the-missing-check)
- [Function-level and role checks](#function-level-and-role-checks)
- [Trusting the client](#trusting-the-client)
- [Multi-tenancy](#multi-tenancy)
- [Sessions](#sessions)
- [Tokens](#tokens)
- [OAuth and OIDC edges](#oauth-and-oidc-edges)
- [Authentication flows](#authentication-flows)
- [Severity calibration](#severity-calibration)

## The two questions

Authentication answers *who is calling*. Authorization answers *may this caller do this to
this object*. Almost every serious access-control bug is the second question never being asked,
on a route where the first question was answered correctly — which is why "the endpoint is
behind auth" is not an answer to an access-control finding.

Broken Access Control is A01:2025, and note that CWE-918 (SSRF) now lives in that category
rather than in its own. `[official]`

## Object-level authorization (IDOR / BOLA)

The pattern: an identifier arrives from the caller, the object is loaded by that identifier,
and nothing compares the object's owner with the caller.

```js
// The session is valid. Nothing establishes that this order is the caller's.
const { rows } = await pool.query("SELECT * FROM orders WHERE id = $1", [req.params.id]);
res.json(rows[0]);
```

The query is parameterized, so an injection scanner is satisfied. The bug is the missing
predicate. Two fixes, and the second is the one that scales:

```js
// Scoped read: ownership is part of the query, so there is no window between check and use.
const { rows } = await pool.query(
  "SELECT * FROM orders WHERE id = $1 AND customer_id = $2",
  [req.params.id, req.session.customerId],
);
```

Load-then-compare works, but it reintroduces the mistake every time a new handler is written.
Scoping at the data-access layer — a repository that takes the principal, or row-level security
in the database — makes the omission impossible rather than merely noticed.

Identifier shape is not a control. Replacing a sequential id with a UUID raises the cost of
enumeration and changes nothing about authorization; the id still leaks through
exports, emails, webhooks and referrers.

Non-obvious places the same bug lives:

- **Nested and sibling routes.** `/orders/:id` gets the check; `/orders/:id/invoice.pdf`,
  `/orders/:id/events`, `/orders/:id.csv` do not.
- **Bulk endpoints.** A list of ids where the check runs on the first one, or on none.
- **Search and filter.** A filter parameter that reaches the query unscoped is a read of
  everything.
- **Cursors and continuation tokens.** An opaque cursor that encodes a tenant or an offset and
  is not signed is an authorization parameter the client controls.
- **File paths derived from ids.** Object storage keyed by id with no policy on the prefix.
- **Second-order writes.** A queue message carrying an id, consumed by a worker that trusts the
  producer. The producer was the web tier; the publisher is now anyone who can publish.

## Finding the missing check

Absence is invisible to grep, so look for it differentially:

1. Enumerate handlers that take an object identifier.
2. For each, find the authorization predicate — in the query, in a guard, in middleware, in a
   policy object.
3. The handlers with no predicate are the candidates. Then find the sibling handler that
   **does** have one and cite it. An in-repository example of the correct pattern turns
   "you should check ownership" into "this file already knows how; three routes forgot", which
   is both harder to dismiss and cheaper to fix.

If every handler omits the check, the finding is architectural: the data-access layer takes no
principal, so the omission is the default. Report it once at that level rather than once per
route.

## Function-level and role checks

- A route whose only protection is that no UI links to it is unprotected.
- Admin, export, impersonation, replay and debug routes get audited individually; they are
  written under deadline and reviewed least.
- A role check that reads the role from the request — a header, a body field, a query
  parameter, an unsigned cookie — is not a check.
- A role check in the client is a UX affordance.
- Route registration order can make a guard unreachable: a generic `/:id` pattern registered
  before a literal `/export` swallows it. Verify the route that actually matches.

## Trusting the client

```js
// The caller sets this header. The proxy does not strip it.
if (req.headers["x-internal-role"] !== "support") return res.status(403).end();
```

The pattern generalises to anything the client can set and the infrastructure does not
overwrite: `X-Forwarded-For` used for allowlisting when the proxy chain appends rather than
replaces, a tenant id taken from a body field, `X-User-Id` injected by a gateway that also
accepts it from outside, an unsigned cookie carrying entitlements.

Two questions settle it: who else can reach this listener directly, and does something on the
path unconditionally overwrite the header? If the answer to the second is "the proxy config
probably", it is unverified, and the finding stands with that noted.

## Multi-tenancy

Tenant isolation is an invariant, not a filter. Check every store the tenant's data can reach:

- **Relational**: is the tenant predicate in every query, or enforced by row-level security?
  Ad-hoc filtering means one missing `WHERE` is a cross-tenant read.
- **Object storage**: one prefix per tenant with no policy restricting the prefix is a naming
  convention, not isolation.
- **Cache and session stores**: keys without a tenant namespace collide, and a key an attacker
  can influence is a cross-tenant write.
- **Search indexes**: a shared index needs a tenant filter applied server-side, never from the
  client's query.
- **Background jobs**: a job that reads "all rows" to build a report is a cross-tenant read
  waiting for its output to become reachable.

Cross-tenant access is the highest-impact class in most SaaS codebases and the least likely to
have a test, because tests usually run as one tenant.

## Sessions

- Cookies: `HttpOnly`, `Secure`, and `SameSite` appropriate to the flow. `SameSite=None`
  without `Secure` is rejected by browsers; `SameSite=None` **with** `Secure` is a deliberate
  choice to permit cross-site sending and needs a CSRF story.
- Rotate the session identifier on privilege change — login, step-up, impersonation — or
  session fixation survives authentication.
- Lifetime: a long absolute lifetime with no idle timeout means a stolen cookie is valid for
  that whole window. Ninety days is a decision about how long a theft stays useful.
- Invalidation must be server-side. Deleting the cookie logs out a cooperative client.
- Logout, password change and permission revocation must each terminate existing sessions;
  check all three, not just logout.

## Tokens

Self-contained tokens are ASVS 5.0.0 V9; OAuth and OIDC are V10. `[official]` What to check:

- **Algorithm.** `alg: none` accepted anywhere is authentication bypass. Accepting `alg` from
  the token at all, rather than pinning the expected algorithm, permits the classic
  HMAC-versus-RSA confusion where the public key is used as an HMAC secret.
- **Signature verification actually happening.** A decode helper that parses without verifying
  is a different function from the verify helper, and the names are usually one word apart.
- **Claims.** Issuer, audience and expiry all verified. `verify_audience: false` means a token
  minted for another service is accepted here — a confused-deputy primitive.
- **Clock skew.** A generous leeway extends every expired token's life by that much.
- **Revocation.** A stateless token cannot be revoked before expiry. A thirty-day access token
  is a thirty-day window after any compromise; that is a design finding, not a config nit.
- **Key management.** A shared symmetric secret across services means any of them can mint
  tokens for all of them. Rotation needs overlapping key ids to be possible at all.
- **Anything self-contained and unsigned.** Cursors, state parameters, resume blobs and
  "opaque" ids that the server parses are tokens whether or not they are called tokens.

## OAuth and OIDC edges

- `state` must be present, unguessable and bound to the session, or the callback is forgeable.
- PKCE for any public client; without it an intercepted code is redeemable.
- Redirect URI matching must be exact. Prefix or wildcard matching is an open-redirect-driven
  code theft.
- Scope granted must be the scope requested; check the server does not widen it.
- The token endpoint's response must be validated, not trusted because it came over TLS.

## Authentication flows

Beyond the login form itself:

- **Password reset** is a parallel authentication path: single-use token, short expiry, bound to
  the account, invalidated on use and on password change. Token in a URL ends up in logs and
  referrers.
- **Email change** must verify the new address before it becomes the recovery address, or it is
  an account-takeover primitive.
- **Multi-factor step-up** must be enforced server-side at the sensitive operation, not at the
  screen that leads to it.
- **Enumeration**: differing responses, status codes or timings between "no such user" and
  "wrong password" leak account existence. This is usually low impact alone and material when
  combined with credential stuffing.
- **Rate limiting** on login, reset and MFA verification. Per-account and per-IP, because each
  alone is trivially evaded.
- **Password storage**: a memory-hard KDF with per-password salt. A fast hash, no salt, or a
  reversible encryption is a finding regardless of what else is right.

## Severity calibration

| Situation | Typical severity |
|---|---|
| Unauthenticated read or write of another principal's data | Critical |
| Authenticated cross-tenant read | Critical, in a multi-tenant product |
| Authenticated horizontal read of one other user's record | High |
| Missing role check on an admin action reachable by any authenticated user | High |
| Ownership check present but done after a side effect | High |
| Enumeration or timing leak with no further access | Low |
| Missing `HttpOnly` where no XSS path is demonstrated | Low, and say why it is not higher |

Every entry assumes the path was shown reachable. Without a reachability argument the severity
is a guess.

<!-- sources: openai-secbase, sentry-secreview, owasp-asvs, owasp-top10, cloudflare-audit -->
