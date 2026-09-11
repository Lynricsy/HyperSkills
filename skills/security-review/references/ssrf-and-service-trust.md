# SSRF and trust between services

Verified against: OWASP Top 10 2025

## Contents

- [Why this is an access-control bug](#why-this-is-an-access-control-bug)
- [Where the URL comes from](#where-the-url-comes-from)
- [What makes an SSRF severe](#what-makes-an-ssrf-severe)
- [Cloud metadata](#cloud-metadata)
- [Why blocklists fail](#why-blocklists-fail)
- [What an actual fix looks like](#what-an-actual-fix-looks-like)
- [Partial-URL and path SSRF](#partial-url-and-path-ssrf)
- [Blind SSRF](#blind-ssrf)
- [Service-to-service trust](#service-to-service-trust)
- [Confused deputy](#confused-deputy)
- [Webhooks in both directions](#webhooks-in-both-directions)
- [Egress as a control](#egress-as-a-control)

## Why this is an access-control bug

SSRF makes the server perform a request the caller could not perform themselves. The server's
network position and its ambient credentials are the privilege being borrowed — which is why
the 2025 Top 10 folds CWE-918 into A01 Broken Access Control rather than keeping it as its own
category. `[official]` Report it with the same reasoning an authorization finding gets: which
principal, which resource they reached, what they got.

## Where the URL comes from

The whole finding turns on provenance, so establish it before anything else:

| Origin | Verdict |
|---|---|
| Request body, query, path, header, cookie | Attacker-controlled. Candidate. |
| A field the user set earlier and the server stored | Attacker-controlled, second order. Candidate. |
| Deployment configuration, environment variable, constant | Server-controlled. Not a finding; say you checked. |
| A record written by an admin or another system | Depends on who can write that record. Trace it. |
| A URL assembled from config plus a caller-supplied path segment | Partial — see below. |

```python
requests.post(body["callback_url"], json=report)      # candidate
requests.post(f"{settings.BILLING_URL}/events", ...)  # server-controlled, not a finding
```

Reporting the second one costs the reader's trust in the first one. Name it explicitly as
checked and excluded.

## What makes an SSRF severe

The request itself is rarely the impact. Look for what the position buys:

1. **Credentials from a metadata service.** The usual escalation to "this is critical".
2. **Internal services with no authentication.** Admin panels, unauthenticated databases,
   Elasticsearch, Redis, Kubernetes API, Consul, Prometheus, internal deploy hooks.
3. **The loopback interface**, where debug and management endpoints live.
4. **Non-HTTP schemes.** `file://` reads files, `gopher://` and `dict://` allow crafted bytes to
   a TCP service, `ftp://`, and in some clients `redis://`. Check which schemes the HTTP client
   accepts by default.
5. **Response reflection.** If the body comes back to the caller, the SSRF is also a read
   primitive. If not, it is blind, which lowers but does not eliminate impact.
6. **The request as a side effect.** A POST to an internal endpoint that changes state needs no
   response to be damaging.

## Cloud metadata

Reaching the link-local metadata address returns credentials for the workload's identity, which
turns SSRF into "attacker holds the service's cloud role". The severity therefore depends on
the role's policy, not on the SSRF alone: a role with `s3:*` on `*` plus `sts:AssumeRole` on
`*` makes it an account-level compromise.

Mitigations to check for, in order of how much they help:

- **IMDSv2 required** (token-based, and the token request needs a PUT with a header most SSRF
  primitives cannot send) with IMDSv1 disabled. If IMDSv1 is still reachable, a plain GET is
  enough. `[official]`
- Metadata endpoint blocked at the network or proxy layer for workloads that never need it.
- The workload identity scoped to what it actually uses, so a stolen token is worth less.

The report should chain these facts: caller-controlled destination, plus IMDSv1 reachable, plus
a broad role policy, equals credential theft. Three separate medium findings for the same chain
understate it; one critical finding with the chain written out is the accurate report.

## Why blocklists fail

Every one of these defeats a check that inspects the string the caller supplied:

- Alternate encodings of the loopback and link-local addresses: decimal, octal, hex,
  IPv6-mapped, `0`, shortened forms.
- A hostname under attacker control whose A record points inside — no encoding trick needed.
- DNS rebinding: resolve to a public address for the check, to an internal one for the request.
  Any check that resolves separately from the connection has this hole.
- Redirects: the first URL passes, the 302 goes anywhere. Following redirects re-opens the
  check unless each hop is validated.
- Parser disagreements between the validator and the HTTP client over userinfo (`@`),
  fragments, backslashes, unicode, and embedded credentials.

So: report a URL blocklist as insufficient, with which of the above defeats it.

## What an actual fix looks like

Ordered by strength:

1. **Do not take a destination from the caller.** Register callback URLs out of band, or push to
   a queue the caller polls. Most callback features do not need caller-supplied URLs.
2. **Allowlist by resolved address, at connect time.** Validate the scheme and host, resolve,
   check every resulting address against the allowlist, then connect to that address with the
   hostname pinned — this is what closes the rebinding window. Redirects disabled, or each hop
   re-validated.
3. **Egress network policy.** Deny by default, allow the destinations the service needs, and
   deny the metadata address. This survives code changes, which nothing in the application layer
   does.
4. **A dedicated egress proxy** with the allowlist, so the rule lives in one place.

## Partial-URL and path SSRF

```python
requests.get(f"{settings.WAREHOUSE_URL}/query?q={spec['query']}")
```

The host is fixed, so this is not classic SSRF — but the caller controls the path and query sent
to an internal service that has no authentication. What the caller can make that service do is
the finding. If the segment can contain `../` or a `@`, or if the client normalizes in a way
that lets the path escape the intended prefix, the host may not be fixed after all: url-encode
segments and check the client's normalization behaviour.

## Blind SSRF

No response body does not mean no impact. Timing differences enumerate internal hosts and ports;
a POST to an internal endpoint is a write; and DNS resolution alone is an exfiltration channel
for whatever can be embedded in a hostname. Report it a step lower than a reflected SSRF, with
the reason.

## Service-to-service trust

The audit question is what each service assumes about its callers, and whether the network
enforces it:

- **"Private subnet" is a claim, not a control.** Check the actual listener and every routing
  rule — proxy, ALB, ingress, mesh, published container port. A rule added for one team's
  convenience is the usual way a private service becomes public.
- **Network position is not identity.** If reaching the service is sufficient authorization,
  then anything with SSRF, a compromised pod, or a misrouted rule is an authorized caller. Use
  mTLS or a signed token per call.
- **Propagate the user's identity, do not re-assert it.** A downstream that accepts a
  caller-supplied user id trusts its caller with impersonation.
- **Internal endpoints need the same input validation as public ones.** They receive
  attacker-influenced data the moment any upstream has an injection or SSRF bug.
- **Internal traffic in the clear** is a finding when the network is shared, and a Low when the
  threat model genuinely excludes on-path attackers — say which.

## Confused deputy

A service with more authority than its caller, performing actions on the caller's behalf without
checking the caller may have them. SSRF is one instance; the general pattern also covers a
report generator that reads any tenant's rows because it runs as a privileged identity, an
admin tool that proxies requests, and a token minted without an audience so any service accepts
it.

The check: for every action the service performs on behalf of a caller, is there a point where
the *caller's* authority is evaluated, or only the service's?

The MCP-specific forms of this — tool poisoning, prompt injection arriving through a tool's
return value, over-broad scopes granted to a server, a server acting as deputy for its host —
belong to the `mcp-server` skill, which covers the protocol. Audit the whole surface here; get
the protocol detail there.

## Webhooks in both directions

**Inbound**: verify the signature before parsing the body, compare with a constant-time
comparison, enforce a timestamp window against replay, and check the handler does not trust a
`type` field to route to a privileged path. A signature check that is skipped when the header is
absent is not a check.

**Outbound**: the destination is caller data (see above); redirects off; a per-tenant egress
allowlist; timeouts and response size limits; and the response body treated as untrusted input
rather than parsed into a trusted structure.

## Egress as a control

`allow_all_outbound: true` with an empty block list, next to a feature that posts to
caller-supplied URLs, is the configuration that turns a medium SSRF into a critical one. When
auditing configuration, pair each application-layer finding with the network control that would
have contained it, and report the pair — that is what tells the reader which single change buys
the most.

<!-- sources: sentry-secreview, openai-secbase, cloudflare-audit, owasp-top10, tob-insecure-defaults -->
