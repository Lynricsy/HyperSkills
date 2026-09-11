# Dependencies and supply chain

Verified against: OWASP Top 10 2025

## Contents

- [Two different questions](#two-different-questions)
- [Reachability before severity](#reachability-before-severity)
- [Reading the manifests](#reading-the-manifests)
- [Install-time code](#install-time-code)
- [Risk signals that are not CVEs](#risk-signals-that-are-not-cves)
- [Lockfiles and pinning](#lockfiles-and-pinning)
- [Transitive dependencies and overrides](#transitive-dependencies-and-overrides)
- [The build and release path](#the-build-and-release-path)
- [Reporting dependency findings](#reporting-dependency-findings)
- [What belongs to other skills](#what-belongs-to-other-skills)

## Two different questions

Software Supply Chain Failures is A03:2025 — promoted from A06:2021's narrower "Vulnerable and
Outdated Components" precisely because the old framing missed most of the category. `[official]`
So ask both questions:

1. **Does a dependency have a known vulnerability that this code can reach?**
2. **Is the dependency itself a risk** — unmaintained, recently transferred, running code at
   install time, resolved from somewhere unexpected?

An audit that only runs the advisory scanner answers the first and misses the second, which is
where the incidents of the last few years actually came from.

## Reachability before severity

A scanner reports every advisory that matches a version. An audit reports what is exploitable
here. For each advisory:

- **Is the package imported at all?** A transitive dependency of a build tool that never runs in
  production is not a production finding. `grep -rn "require('pkg')\|from 'pkg'\|^import pkg"`
  and the lockfile's dependency graph settle it.
- **Is the vulnerable function reached?** A prototype-pollution bug in a utility function the
  code never calls is lower than the advisory's score implies.
- **Does attacker-controlled data reach it?** The usual severity driver. A YAML parser bug
  matters when the YAML comes from a request, not when it comes from the repository.
- **Is it dev-only, build-only, or runtime?** Each has a different attacker. A build-time RCE is
  a CI compromise, which may be worse than a runtime one — say which you mean.

Report the version, the advisory, the reachability finding, and the fixed version. Report
honestly when reachability could not be determined from what you read.

## Reading the manifests

Worth flagging on sight, before any advisory lookup:

- A package whose entire purpose is to execute serialized code (`node-serialize`,
  `serialize-javascript` used with `eval`, `funcster`). Its presence usually means a
  deserialization sink exists somewhere.
- A crypto or JWT library pinned to a major version behind current, next to configuration that
  permits a weak algorithm — those two facts together are one finding, not two.
- A template engine with known prototype-pollution-to-RCE history on an old patch version.
- Duplicate implementations of the same job (two HTTP clients, three validators): more surface,
  and usually one of them is unmaintained.
- A package resolved from a URL, a git ref, or a private registry. A git dependency on a branch
  is unpinned code from a third party.
- `0.x` versions of anything security-relevant, and any `*`, `latest` or unbounded range.
- Version ranges in a published library's manifest that permit a future major of a security
  dependency.

## Install-time code

```json
"postinstall": "node scripts/fetch-geoip.js https://cdn.example/geoip.mmdb"
```

Install scripts run with the developer's or CI's privileges, before any test or review. A
postinstall that fetches a remote artifact is arbitrary code from a network location on every
install, in every environment, including CI where the credentials are. What to check:

- Does it fetch anything? Over what transport, with what integrity check?
- Is the URL pinned to a digest, or does the content behind it change?
- Could the fetched artifact reach a build output?
- Can installs run with scripts disabled (`npm ci --ignore-scripts`, `pip install --no-build-isolation`
  with wheels only, `--frozen-lockfile`), and does the build still work?

The same applies to dependencies' install scripts, not just your own. Enumerate them before
trusting a lockfile: an audit that only reads the top-level manifest has not looked at the
install surface.

## Risk signals that are not CVEs

For each dependency in a security-relevant position — crypto, auth, parsing, serialization,
the request path, the build:

| Signal | Why it matters |
|---|---|
| No release in a long time, open security issues | Nobody will ship the fix you need |
| Very few maintainers, or a recent ownership transfer | The classic account-takeover vector |
| A sudden release with a large diff and no changelog | The shape of a compromised publish |
| Published artifact does not match the tagged source | No provenance; the registry artifact is what runs |
| A name one character from a popular package | Typosquat; check what is actually resolved |
| Vendored copy of another library inside it | Advisories for the inner library will never match |
| Minified or generated code committed as source | Nobody is reviewing what ships |

These are prioritisation signals, not findings on their own. The finding is "this
security-critical dependency is unmaintained and here is what depends on it", with the
alternative or the mitigation.

## Lockfiles and pinning

- A lockfile is required for an application. Without one, two builds from the same commit can
  install different code, and no advisory statement is meaningful.
- A lockfile that is in the repository but not used by CI (`npm install` rather than `npm ci`,
  no `--frozen-lockfile`, no `--locked`) is decoration.
- Integrity hashes present and verified. `--require-hashes` for pip; check the resolver actually
  enforces `integrity` fields.
- Registry configuration: a private registry combined with a public fallback is dependency
  confusion. An internal package name that is unclaimed publicly is the bug.
- Container images pinned by digest rather than by a moving tag; `FROM node:20` changes under
  you, `FROM node@sha256:...` does not.

## Transitive dependencies and overrides

An `overrides` / `resolutions` / `constraints` block pins a transitive package. Read it as
carefully as the direct dependencies, because it is a deliberate statement about a version that
nothing else will update:

```json
"overrides": { "semver": "5.7.1" }
```

This forces every transitive consumer onto that version, including consumers that had already
moved past a known issue. An override added to fix one build error silently freezes a security
dependency; check each override against current advisories and note why it exists.

## The build and release path

Software or Data Integrity Failures is A08:2025, and it is about this. `[official]`

- Who can publish? A single long-lived token, or short-lived federated credentials with an
  environment approval?
- Is what gets published built from a known commit, or from a developer's machine?
- Are artifacts signed or attested, and does any consumer verify?
- Can a pull request from a fork reach the credentials that publish? This is where CI
  configuration becomes a supply-chain question.
- Is the container base image, the toolchain and the CI runner image pinned?

## Reporting dependency findings

Group by outcome, not by package, so the reader sees the shape:

```
Reachable, fix available
  node-serialize 0.0.4 — unserialize() with caller data is code execution (CVE-2017-5941).
    Imported at services/api/state.js:12; reached from POST /state/resume.
    No maintained release exists; replace with JSON plus a schema.

Reachable, mitigation only
  jsonwebtoken 8.5.1 — algorithm-confusion class; the config also permits alg: none.
    One finding with the config, not two. Pin the algorithm at the verify call and upgrade.

Present, not reached from the audited surface
  lodash 4.17.20 — prototype pollution in zipObjectDeep (CVE-2021-23337); that function is
    not called. Upgrade with the next routine bump.

Could not determine
  handlebars 4.7.6 — advisories require a caller-controlled template; no template source was
    visible in the files reviewed. Check whether templates are ever read from the database.
```

CVE identifiers here are `[official]` — from public advisories, not verified by running a
scanner against a real install. When the tree is available, run the ecosystem's own auditor and
quote its output rather than recalling advisory numbers.

## What belongs to other skills

- Hardening the CI workflows themselves — permissions blocks, action SHA pinning, script
  injection through workflow expressions, `pull_request_target`, self-hosted runner exposure —
  is the `github` skill's job. Note in the report that the CI configuration is a supply-chain
  surface and hand it over; do not restate that skill's rules here.
- Container image hardening beyond pinning, and Kubernetes-side controls, belong to
  `containers`.
- Cloud-side artifact registries and their IAM belong to `aws`, `azure`, `gcp` or `cloudflare`.

<!-- sources: tob-supplychain, copilot-secreview, owasp-top10, cloudflare-audit, openai-secbase -->
