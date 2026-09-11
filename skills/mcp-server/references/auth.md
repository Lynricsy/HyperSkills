# Authorization for an MCP server

Verified against: MCP specification revision 2026-07-28
(`basic/authorization/{index,security-considerations,client-registration}.mdx`).

Confidence note: the rules in this file are `[official]` — they come from the specification and the
RFCs it normatively references. They were not exercised end to end against a live authorization
server while writing this skill, so treat the flow diagrams as the specification's, not as
measured behaviour.

## Contents

- Where authorization applies
- The server is a resource server
- Audience validation is the whole job
- No token passthrough
- Scope: ask for less
- Scope challenges and step-up
- Client registration: CIMD, not DCR
- The confused deputy
- Tokens the server holds
- stdio servers and secrets
- A review checklist

## Where authorization applies

The authorization specification applies to HTTP-based transports. A stdio server **should not**
follow it: it is launched by the user as a subprocess and inherits its credentials from the
environment, so bolting OAuth onto it adds a browser dance without adding a trust boundary.
Alternative transports must follow established security practice for their channel.

## The server is a resource server

An MCP server over HTTP is an OAuth 2.1 protected resource. Its obligations:

1. Implement OAuth 2.0 Protected Resource Metadata (RFC 9728) so clients can discover the
   authorization server.
2. Validate the bearer token on **every** request — authorization is per request, and under
   2026-07-28 there is no session to carry a prior decision forward.
3. Return `401` with a `WWW-Authenticate` header on an invalid or expired token, `403` on
   insufficient scope.
4. Serve every authorization endpoint over HTTPS; redirect URIs are HTTPS or `localhost`.

The authorization server is a separate role and may be someone else's. What the MCP server owns is
token validation and scope enforcement.

## Audience validation is the whole job

The defect that gets configurations bounced is validating the signature and stopping there:

```yaml
verify:
  signature: true
  audience: null              # accepts any token this issuer ever minted
  issuer_allowlist: ["https://login.example.com"]
```

Every other service behind the same identity provider now has a token that opens this server.
Anyone who can get a token for the low-value service has one for the high-value one.

The specification is explicit: a server **must** validate that a token was issued specifically for
it, **must** reject tokens that do not name it in the audience, and **must not** accept or transit
any other token. Clients must send the RFC 8707 `resource` parameter naming the canonical server
URI in both the authorization request and the token request, so the audience is there to check.

Write the canonical URI down and compare against it: lowercase scheme and host, no trailing slash
unless it is semantically meaningful, most specific path the client can name.

## No token passthrough

```yaml
upstream:
  auth_mode: passthrough      # forbidden
```

If the MCP server calls an upstream API, it acts as an OAuth client to that API and uses a
*separate* token issued by that API's authorization server. It **must not** forward the token it
received from the MCP client. Passthrough means the upstream cannot tell your server from any other
holder of that token, audience binding is defeated in one hop, and a compromise of your server
yields credentials for systems you do not own.

Exchange the token, or use the server's own credentials, and scope those credentials to what the
server needs.

## Scope: ask for less

A scope list is a blast radius. A notes server asking for `drive.readwrite.all`, `mail.send` and
`notes.admin` is asking the user to grant three unrelated systems so that one feature works, and
"the user only sees one consent screen" is not a security argument — it is the cost of the design
being wrong.

Follow least privilege: request the narrowest scopes the current operation needs. The server's
`WWW-Authenticate` challenge should name the scopes that would satisfy the request; clients must
treat those as the ones to ask for, and must not assume any set relationship between the challenged
scopes and the authorization server's `scopes_supported`.

Also: a protected resource **should not** put `offline_access` in the scopes it asks clients for.
Refresh-token lifetime is the authorization server's decision, and clients must not assume a
refresh token will be issued at all.

## Scope challenges and step-up

When an authenticated call needs a scope the presented token lacks, answer `403` with a
`WWW-Authenticate` challenge naming the required scope rather than failing opaquely. A
user-delegated client should then run a step-up authorization flow for the larger scope set; a
`client_credentials` client cannot and must surface the error.

Be consistent about which scopes you include in challenges, and account for hierarchies — a broader
scope implies the narrower ones it contains, so do not reject a caller who holds the superset.
Clients should cap step-up attempts; a server that returns the same challenge after a successful
upgrade creates an authorization loop.

## Client registration: CIMD, not DCR

Dynamic Client Registration (RFC 7591) was **deprecated in 2026-07-28** in favour of **Client ID
Metadata Documents**: the client publishes its metadata at an HTTPS URL and uses that URL as its
`client_id`; the authorization server fetches and validates the document. No registration endpoint,
no stored client records, no new client on every fresh connection.

| | CIMD | DCR |
|---|---|---|
| Status in 2026-07-28 | preferred | deprecated, kept for backward compatibility |
| Advertise with | `client_id_metadata_document_supported: true` | `registration_endpoint` |

Client-side priority order: pre-registered credentials, then CIMD if advertised, then DCR if a
registration endpoint exists, then prompt the user.

Two rules that catch people out: an authorization server fetching a metadata document is making an
outbound request to a URL an attacker chose, so SSRF defences apply; and client credentials are
bound to the authorization server that issued them — persist them keyed by issuer, never reuse them
with a different authorization server, and re-register when it changes.

Also validate the authorization response before redeeming the code: record the issuer from the
validated metadata, and if the response carries `iss` (RFC 9207), compare it byte-for-byte against
the recorded value with no case folding, port elision, trailing-slash or percent-encoding
normalisation. This applies to error responses too — on mismatch, do not act on or display the
error fields. And require PKCE with `S256`, refusing to proceed if the authorization server's
metadata does not advertise `code_challenge_methods_supported`.

## The confused deputy

The shape: your MCP server fronts a third-party authorization server using a **static** client id,
and clients register dynamically behind it. The third party sees one well-known client and may skip
its consent screen, so an attacker with a stolen authorization code can obtain a token without the
user ever consenting.

The requirement: an MCP proxy server using a static client id **must** obtain user consent for each
dynamically registered client before forwarding to the third-party authorization server. Do not
inherit the proxy's consent.

If you are designing this now, prefer not to be a proxy at all. Being a resource server with its
own authorization server and its own upstream credentials removes the deputy.

## Tokens the server holds

| Deployment | Where tokens live |
|---|---|
| Remote, stateless | nowhere; the client presents a bearer on each request |
| Remote, needs upstream credentials | a server-side store keyed by the authenticated subject, not by anything connection-scoped |
| Local / bundled | the OS keychain — never plaintext on disk |

Short-lived access tokens limit the damage from theft; public clients must get rotating refresh
tokens. Never log the `Authorization` header — `logging: { level: debug, include_authorization_header: true }`
puts live credentials in whatever aggregates your logs, and `destination: stdout` on a stdio server
also corrupts the protocol stream (see `references/transports.md`).

A hardcoded fallback credential in a configuration file is a finding regardless of whether the
value is real: it is the mechanism that gets a real one committed later.

## A review checklist

- [ ] Tokens validated on every request, not once per connection
- [ ] Audience checked against this server's canonical URI; tokens for other resources rejected
- [ ] No path that forwards the inbound token upstream
- [ ] Scope list justified operation by operation; nothing unrelated to the protected resource
- [ ] `403` + `WWW-Authenticate` naming required scopes, with a step-up path
- [ ] CIMD supported and advertised; DCR only as a documented fallback
- [ ] Static-client-id proxying either removed or gated behind per-client consent
- [ ] PKCE `S256` required; `code_challenge_methods_supported` verified
- [ ] `iss` compared without normalisation when present
- [ ] Origin validated; loopback binding for local deployments
- [ ] No credentials in config files, no `Authorization` header in logs

For auditing a whole codebase or threat surface rather than this one configuration, use the
`security-review` skill.

<!-- sources: mcp-spec, anthropic-mcp-server-dev, awesome-copilot-mcp -->
