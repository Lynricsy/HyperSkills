# Scoping an audit and proving coverage

## Contents

- [Why scoping decides the result](#why-scoping-decides-the-result)
- [Pass 1 — context before code](#pass-1--context-before-code)
- [Pass 2 — the attack surface inventory](#pass-2--the-attack-surface-inventory)
- [Ordering the surface](#ordering-the-surface)
- [The coverage ledger](#the-coverage-ledger)
- [Depth bounds](#depth-bounds)
- [Cheap passes that go first](#cheap-passes-that-go-first)
- [Stating what you did not cover](#stating-what-you-did-not-cover)
- [Re-auditing a surface you have seen before](#re-auditing-a-surface-you-have-seen-before)

## Why scoping decides the result

An audit that opens files in whatever order the grep returned finds whatever happens to be
near the top. Four passes, in order, and the third is the only one that looks like bug hunting:

```
1. context        what does this system protect, and from whom?
2. attack surface where does untrusted input enter, and what can it reach?
3. hunt           trace specific bug classes along the reachable paths
4. verify         establish exploitability before writing a finding down
```

Skipping to pass 3 is the single most common way an audit produces a long list of nothing.
Pattern matches without a reachability story are not findings; they are grep output.

## Pass 1 — context before code

Answer these from the repository, not from assumption. Each answer either narrows the audit or
raises its stakes:

- What does this code protect? Money, personal data, credentials, integrity of a build
  artifact, availability of a shared service.
- Who are the principals? Anonymous internet, authenticated tenant user, another tenant,
  an internal service, an operator, CI.
- How does it run? Public HTTP service, internal service, CLI, library consumed by others,
  worker on a queue. A library's threat model is its callers' inputs, not a network.
- What is multi-tenant? Any store reachable by more than one tenant is a cross-tenant
  question until proven otherwise.
- What is already known broken? A `SECURITY.md`, an open issue list, a previous report. Do not
  spend the audit rediscovering tracked gaps; spend it on what they missed.

Separate runtime from CI and developer tooling before going further. A debug flag in a
devcontainer and the same flag in a production manifest are different findings with different
severity, and mixing them is how a report loses its reader.

## Pass 2 — the attack surface inventory

Enumerate entry points mechanically, then read them. Typical generators:

| Surface | How to enumerate |
|---|---|
| HTTP routes | Router registrations; framework decorators; the reverse-proxy or ALB rules, which can expose a service the code believes is private |
| Queue and event consumers | Subscription setup, handler registries; the message body is untrusted input |
| Scheduled jobs | Cron definitions, whose input is usually config but whose output often skips authorization |
| Parsers and decoders | Anything taking bytes: uploads, archives, images, XML, protobuf, template strings |
| Deserialization points | Pickle, YAML, Java object streams, PHP `unserialize`, `node-serialize`, signed-cookie decoders |
| CLI and IPC | Argument parsing, stdin, unix sockets, local HTTP on loopback |
| Admin and internal tooling | Frequently unauthenticated because "it is internal" |
| Templates and rendering | Server-side template evaluation with any caller-supplied part |
| Webhooks in | Third-party callbacks; check signature verification, not just the route |
| Webhooks out | Caller-supplied destinations; this is the SSRF generator |

Two entry points are missed most often. The first is a **second route into the same code**: a
resume, retry, replay, batch or migration path that reaches the same sink with a different
guard. The second is a **network rule that contradicts the code's belief about its own
exposure** — a proxy rule, a load-balancer listener, a service mesh route, a port published in
a compose file. Read the deployment config as part of the surface, not as background.

## Ordering the surface

When the audit cannot cover everything — the normal case — order by this and write the
ordering down:

1. Unauthenticated entry points before authenticated ones.
2. Boundaries protecting the most valuable outcome: credential theft, cross-tenant data,
   code execution, release or deploy authority, money movement.
3. Code that changed since the last audit, and gaps the last audit recorded.
4. Sensitive paths with weak ownership. A security-critical module whose git history shows one
   author who has left is both more likely to be wrong and less likely to be fixed correctly;
   `git shortlog -sn -- <path>` and the last-touched date are enough signal for ranking.

Speculative classes go last. "Let me check for prototype pollution everywhere" is not a
priority claim.

## The coverage ledger

Keep an explicit list of units — one per (subsystem, boundary) pair — with a disposition each.
A plain table in the report is enough; the point is that nothing disappears silently.

| State | Meaning |
|---|---|
| `planned` | In scope, not yet read |
| `in_progress` | Being read now |
| `covered` | Read to the chosen depth; invariant settled either way |
| `candidate` | Produced a finding awaiting validation |
| `blocked` | Cannot be settled from source; names the exact missing fact |
| `deferred` | Out of budget; names why it was ranked below what was done |

A unit that is neither `covered` nor explicitly `deferred` is a hole in the report. The failure
mode this prevents is the audit that reads three interesting files, finds two bugs, and implies
the rest is fine.

## Depth bounds

Trace only paths that reach an in-scope boundary, or whose guarantees that boundary relies on.
Stop a line of investigation the moment the invariant is settled in either direction, and
record which way. Useful sizing signal from `git ls-files | wc -l`:

- Under ~20 source files: read the dependencies' relevant code too.
- ~20–200: follow one hop out from each entry point.
- 200+: walk only the paths reachable from the ranked entry points, and say so.

## Cheap passes that go first

Three passes cost minutes each and routinely outrank a day of reading. Do them before the deep
read, because a live credential or a fail-open default changes the threat model of everything
you are about to analyse.

**1. Dependency manifests.** Every manifest and lockfile in the tree, plus install-time
scripts.

**2. Secret sweep.** Every file, not just source: config, IaC, CI definitions, Dockerfiles,
fixtures, committed `.env`.

**3. Configuration sweep.** Read every rendered config, manifest and IaC file against these
six classes. They are the ones that are wrong in production most often, and each one changes
the severity of application-layer findings rather than standing alone:

| Class | What to look for |
|---|---|
| Debug features left on | `debug: true`, verbose log levels, request-body logging, interactive debuggers, profiling endpoints, stack traces returned to clients |
| Default credentials | Shipped admin accounts, seeded passwords, unauthenticated management ports left at their defaults |
| Fail-open error handling | A missing check treated as a pass, an exception swallowed into an allow, a wildcard that makes an allowlist inert (`allowed_events: ["*"]`) |
| Fallback secrets | `os.environ.get("SECRET_KEY", "dev-secret")` — a live credential in every environment that forgets the variable, failing open silently |
| Permissive access | `s3:*` on `*`, CORS `*` with credentials, `trusted_proxies: 0.0.0.0/0`, `allow_all_outbound`, security groups open to the world, `sslmode: disable` |
| Weak cryptography by default | `alg: none`, unverified audience, legacy TLS versions, a fast hash where a KDF belongs, a fixed IV or nonce |

Pair each application-layer finding with the configuration control that would have contained
it. That pairing is what tells the reader which single change buys the most.

## Stating what you did not cover

Every report ends with the limits, in the same detail as the findings:

- Units `deferred` or `blocked`, each with its reason.
- Facts that source cannot settle — which IAM policy is actually attached, whether a proxy rule
  is still live, whether a dependency is imported at all — and the exact check that would
  settle each.
- Whether the pass was whole-surface or scoped, and to what.

A pass that found nothing and says so, with its coverage stated, is a valid result. Padding it
with informational observations to look thorough makes the next reader distrust the severities
that matter.

## Re-auditing a surface you have seen before

Rebuild incrementally rather than from zero. Carry forward the prior ledger and prior findings,
then:

- Re-verify any previously confirmed finding whose source has not changed before repeating it;
  a report that lists a fixed bug loses the reader's trust for the rest of the list.
- Diff the architecture, not just the code: a new proxy rule, a new consumer, a new external
  integration each add boundaries that were not in the prior model.
- Keep the prior dismissals with their reasons. Re-litigating a dismissed candidate without new
  evidence is wasted budget; contradicting a dismissal with new evidence is a real finding.

<!-- sources: cloudflare-audit, trilwu-audit, openai-ownership, copilot-secreview, tob-insecure-defaults -->
