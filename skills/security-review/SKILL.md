---
name: security-review
description: "Audits codebases for security vulnerabilities, access-control flaws and trust-boundary risks."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: task
---

Paths below are relative to this skill's directory.

## Scope

Defensive security auditing of a whole codebase, a feature, or a named threat surface: scoping
and coverage, threat modelling, access control, injection and deserialization, SSRF and trust
between services, secrets and their rotation, dependency and supply-chain risk, turning findings
into semgrep rules, severity, and keeping false positives out of the report.

Reviewing a diff for general correctness and style is the `code-review` skill's job; auditing a
whole codebase, feature or threat surface is this skill's. That skill already carries the
delta-shaped security pass — risk-classifying changed files, blaming removed guards, sizing
blast radius — so a pull request under review goes there and comes back here when the question
becomes "is this whole surface sound".

The evidence boundary is source reading plus, where genuinely needed, a bounded local
reproduction: a unit test, a small harness, a malformed fixture, a locally rendered policy.
Sending crafted requests at a deployed system, a provider API, a shared environment or another
user's data is out of scope, as is anything intended to evade detection. A fact that only a
running system can settle is reported as a validation blocker with the safe check its owner can
perform.

Not covered, with where it belongs: hardening GitHub Actions and the CI supply chain —
permissions blocks, action pinning, workflow expression injection, `pull_request_target` — is
the `github` skill's; language- and framework-specific correctness belongs to the ecosystem
skill for that stack (`python`, `typescript`, `go`, `java-spring`, `csharp-dotnet`, `laravel`,
`nodejs-backend`, `fastapi`, `react`, `android`, `apple` and the rest); database-side controls
such as row-level security syntax and performance belong to `postgres` or `supabase`; container
and Kubernetes hardening to `containers`; cloud IAM and network policy detail to `aws`, `azure`,
`gcp` or `cloudflare`; production signal analysis to `observability`. MCP-protocol threats —
tool poisoning, prompt injection arriving through a tool's return value, over-broad scopes,
a server acting as a confused deputy — belong to `mcp-server`; audit the whole surface here and
get the protocol detail there. Smart-contract auditing — reentrancy, proxy storage collisions,
oracle manipulation, Foundry and Slither — belongs to `solidity-web3`; the threat-modelling,
severity and reporting method here still applies to that work.

## Core rules

1. **Four passes, in order: context, attack surface, hunt, verify.** Starting at the hunt finds
   whatever the first grep returned; the ranking that makes a report useful comes from the two
   passes before it.
2. **Establish reachability before assigning severity.** A pattern with no path from a named
   lower-trust principal is a candidate, not a finding. Most of the audit's value is in deciding
   which candidates are reachable.
3. **Read the deployment config as part of the attack surface.** A proxy or load-balancer rule,
   an ingress, a published port or a mesh route routinely contradicts what the code believes
   about its own exposure, and the deployment wins.
4. **Every finding names the control that should have stopped it.** That sentence is the one a
   reviewer disputes; without it the finding is an observation.
5. **Likelihood and impact are separate judgements, each with a reason.** Reporting only the
   combined label hides which half is weak, and the weak half is where the argument is.
6. **Overall severity never exceeds demonstrated impact.** "Could lead to full compromise" with
   no path shown is not Critical.
7. **A candidate you could not establish is needs-validation with no severity, never a
   low-severity finding.** Downgrading an unproven claim to keep it in the report is how the
   report loses its reader.
8. **A needs-validation blocker names a fact and the check that settles it.** "Needs further
   investigation" is an unfinished finding.
9. **Run every candidate through the dismissal tests and record the dismissals with reasons.**
   Two false positives and the reader starts checking your work instead of fixing bugs.
10. **Server-controlled values are not attacker input.** A URL, path or query from settings,
    environment or a constant is not SSRF, traversal or injection — check it, then say you
    checked it. Reporting it costs the reader's trust in the findings that are real.
11. **Framework protection counts only where the code path uses it.** Verify on the route —
    middleware order, decorators, per-route exemptions — not on the presence of an import.
12. **Cite the codebase's own correct pattern next to the omission.** A sibling handler that
    does scope by tenant turns "you should check ownership" into "three routes forgot", which is
    harder to dismiss and cheaper to fix.
13. **An identifier position in SQL cannot be parameterized.** `ORDER BY`, column and table
    names need an allowlist that maps input to values the code owns; a bound parameter there is
    a syntax error, not a fix.
14. **Keys taken from a request body are injection and mass assignment at once.** Bound values
    with interpolated column names still let a caller write `status`, `total_cents` or
    `customer_id`.
15. **A format that reconstructs objects is remote code execution when it decodes caller
    bytes.** Signing the blob moves the problem to key management; a schema-checked format
    removes it.
16. **Revocation is the only step that makes a leaked credential stop working.** Revoke, then
    rotate, then deal with history — rewriting history invalidates nothing, and every fork,
    mirror and clone holds a working credential until revocation. `.gitignore` does nothing for
    a file already tracked.
17. **Scope a leak per credential, and treat each as compromised from its commit date.** Four
    secrets in one file usually need four different responses; provider-side logs decide whether
    this is a rotation or an incident, and a clean log is weak evidence rather than proof.
18. **Triage dependencies by reachability, not by advisory count.** Whether the package is
    imported, whether the vulnerable function is called, and whether attacker data arrives there
    decide the severity; a scanner's severity is about the rule, not about this system.
19. **A dependency is a risk in its own right, not only when it has a CVE.** Unmaintained,
    recently transferred, or running code at install time are findings with no advisory attached.
20. **A semgrep rule ships with an annotated test file and a passing `semgrep --test`.**
    `missed lines` are false negatives, `incorrect lines` are false positives, and both are bugs
    in the rule (semgrep 1.x).
21. **Read the `N/M` line, not the exit code.** `semgrep --test` over a directory pairs
    `<rule-id>.yaml` with `<rule-id>.<ext>` by basename and prints "No unit tests found" while
    still exiting 0 when they do not match (semgrep 1.177+).
22. **A rule whose finding count drops after an edit is guilty until the test file clears it.**
    A sanitizer broader than intended can match the source itself and silently turn the rule
    into a no-op that reports a clean file.
23. **Cite OWASP with a year.** In the 2025 edition A01 is Broken Access Control, A02 Security
    Misconfiguration, A03 Software Supply Chain Failures, A04 Cryptographic Failures,
    A05 Injection; SSRF is no longer a standalone category because CWE-918 sits inside A01:2025.
    A bare "A03 Injection" is 2021 numbering. `[official]`
24. **Use ASVS 5.0 chapter numbers, not 4.0.x.** Authorization is V8, Authentication V6,
    Session Management V7, Self-contained Tokens V9; "V4 Access Control" from 4.0.x points a 5.0
    reader at API and Web Service. `[official]`
25. **Say what you did not cover, in the same detail as what you did.** Zero confirmed findings
    is a valid result; padding it with informational observations to look thorough devalues every
    severity in the report.

## Workflows

### audit-surface

A whole repository, a feature, or a named threat surface.

- [ ] Pass 1 — context: what this protects, from whom, how it runs, what is multi-tenant, what
      is already tracked as broken. Separate runtime from CI and developer tooling.
- [ ] Pass 2 — enumerate the attack surface: routes, queue consumers, scheduled jobs, parsers,
      deserialization points, CLI and IPC, admin tooling, inbound and outbound webhooks. Read
      the proxy, ingress and container port config as part of this, not as background.
- [ ] Rank the surface and write the order down: unauthenticated before authenticated, then by
      what the boundary protects, then by what changed since the last audit, then by weak
      ownership of sensitive paths (`git shortlog -sn -- <path>`).
- [ ] Run the three cheap passes first — dependency manifests, secret sweep, configuration
      sweep. A live credential changes the threat model of everything after it.
- [ ] Open a coverage ledger: one row per (subsystem, boundary), each ending `covered`,
      `candidate`, `blocked` or `deferred` with a reason.
- [ ] Pass 3 — hunt along the reachable paths, using the topic references for the classes each
      surface actually has. For each candidate: name the principal, the accepted value, the
      control that should have rejected it, the path after that decision, and the smallest
      observable effect. Stop there.
- [ ] Pass 4 — verify: re-read every cited location, run the dismissal tests, and settle each
      candidate as confirmed, needs-validation or rejected. Re-check your own findings as if
      someone else had written them.
- [ ] Assign likelihood and impact separately to the confirmed set, then overall severity.
      Collapse links that form one chain into a single finding at the chain's severity.
- [ ] **Gate — every confirmed finding has a principal, a `file:line` path, the control that
      failed, a demonstrated result and a fix; every needs-validation entry has a named
      blocker and its check; the ledger accounts for every unit; the report states its limits.**

### threat-model

- [ ] Inventory components, data stores, integrations, entry points and assets, each cited to a
      file or a deployment definition. Mark inferences as inferred.
- [ ] Write one row per trust boundary edge with protocol, authentication, authorization,
      encryption, validation and rate limiting. The empty cells are the findings.
- [ ] Look for the invalidated assumption: where the documentation, the code and the deployment
      disagree about exposure or trust. This is usually the highest-value output.
- [ ] State each principal's capabilities **and** non-capabilities. An unstated worst case
      inflates every severity below.
- [ ] Apply STRIDE per edge, not per system. Most edges yield nothing for most categories.
- [ ] Rank with likelihood and impact apart, tie every threat to a named component or edge, and
      name the one assumption whose reversal would most change the ranking.
- [ ] Record the assumption register with what changes if each assumption is wrong, and mark
      dependent conclusions conditional.
- [ ] **Gate — no threat without a component and an edge from the inventory; capabilities and
      non-capabilities both stated; the assumption register present; any OWASP mapping uses
      2025 numbering.**

### triage-findings

Scanner output, an inherited report, a reported vulnerability, or your own candidate list.

- [ ] For each item: is the input attacker-controlled here, does a control on the path mitigate
      it, is the code reachable in real usage, and does the rule's assumed sink match what this
      code does?
- [ ] Run the dismissal tests. Failing one is a dismissal; record which test and why.
- [ ] Never carry a scanner's severity into the report. Re-derive it from likelihood and impact
      for this system.
- [ ] Promote what survives to a full finding with its path and evidence; demote what is blocked
      on an external fact to needs-validation.
- [ ] **Gate — every input has one of three dispositions, every dismissal has a reason on
      record, and no severity was inherited from a tool.**

### leaked-credential

- [ ] Inventory every secret in the file and the tree: config, IaC, CI definitions, Dockerfiles,
      fixtures, committed keys, `.env`. Distinguish real secrets from public identifiers and
      placeholders, and treat a fallback default as live.
- [ ] Establish the exposure window per secret from `git log --diff-filter=A -- <path>` and
      `git log -S '<fragment>'`, counted to revocation rather than to discovery.
- [ ] Revoke at the provider, every secret, first. Where revoking breaks production, issue the
      replacement first and revoke immediately after — not at the next maintenance window.
- [ ] Issue replacements into a secret store and redeploy from there.
- [ ] Pull provider-side audit logs over the window per credential and say what they do and do
      not show.
- [ ] Purge the secondary locations: CI job logs (a script that echoes a token puts it there),
      container image layers, issues and chat, error trackers.
- [ ] Decide whether history rewriting is still warranted, knowing what it does not achieve —
      forks keep their copies, old objects stay reachable by SHA until support purges the cache,
      and a stale clone can push the blob back.
- [ ] Add the recurrence control and verify it fires on a test commit.
- [ ] **Gate — revocation precedes rewriting in the written plan, each credential has its own
      blast radius and audit-log question, and the recurrence control was verified rather than
      recommended.**

### rule-ize

Turn a repeated finding into a semgrep rule.

- [ ] State the bug as an invariant, in the form "X must never reach Y".
- [ ] Write the test file first from the real call sites: `# ruleid: <id>` above each expected
      match, `# ok: <id>` above each safe call site. Include the already-fixed form, the
      configuration-derived form, and the safe sibling API.
- [ ] Choose the mode deliberately: pattern mode when the call itself is the bug, taint mode
      when the same call is fine or not depending on where its argument came from.
- [ ] Write the rule. One rule per YAML file, a severity semgrep accepts, no `todoruleid:` or
      `todook:`, and a message that says what to do instead.
- [ ] Run `semgrep --test --config <rule-id>.yaml <rule-id>.<ext>` and iterate until it reports
      all tests passing. Keep sanitizers narrow, and re-run the tests after every sanitizer
      change.
- [ ] Run the rule over the real tree and read every hit before proposing it for CI.
- [ ] **Gate — `semgrep --test` reports `N/N` passing (not just exit 0), both failure
      directions are clear, and the rule was run over real code with every hit triaged.**

## Topic router

| Topic | Read when | File |
|---|---|---|
| Four-pass loop, attack-surface enumeration, ranking, coverage ledger, depth bounds, the three cheap passes, stating limits | Starting any audit, or deciding what to leave out | `references/scoping-and-coverage.md` |
| Boundaries as edges, assets, capabilities and non-capabilities, STRIDE per edge, OWASP 2025 and ASVS 5.0 numbering, assumption register | Threat modelling, or using a standard as a coverage checklist | `references/threat-modelling.md` |
| IDOR and object-level authorization, finding a missing check differentially, client-trusted roles, multi-tenancy, sessions, tokens, OAuth edges, auth flows | Auditing routes, handlers, tenancy or anything holding a session | `references/access-control.md` |
| SQL including non-parameterizable positions, mass assignment, NoSQL, command, template, deserialization, traversal, output context, second-order | Untrusted data reaches a second interpreter | `references/injection-and-deserialization.md` |
| URL provenance, metadata services, why blocklists fail, real fixes, partial-URL SSRF, service-to-service trust, confused deputy, webhooks, egress | The code makes outbound requests, or services trust each other by network position | `references/ssrf-and-service-trust.md` |
| Where secrets hide, what counts as one, per-credential blast radius, exposure window, response order, history rewriting, recurrence | A credential is in the repository, in a log, or in a URL | `references/secrets-and-credentials.md` |
| Reachability-first triage, install-time code, non-CVE risk signals, lockfiles and pinning, overrides, the release path | Reading manifests, lockfiles or the build | `references/dependencies-and-supply-chain.md` |
| Test-file-first loop, `--test` output, the silent-zero traps, pattern versus taint, sanitizer backfire, severity values, CI wiring | Writing or fixing a semgrep rule | `references/semgrep-rules.md` |
| Deriving severity, the three dispositions, exploitability arguments, chains, CVSS caution, report template, writing the fix | Assigning severity or writing the report | `references/severity-and-reporting.md` |
| The dismissal tests, attacker- versus server-controlled inputs, framework-mitigated patterns, hardening-not-findings, scanner triage | Before writing any finding down | `references/false-positive-governance.md` |

## Output format

One Markdown report. Skip empty sections; order findings by severity within each section. The
full template, with a worked finding, is in `references/severity-and-reporting.md`.

```markdown
# Security review — <scope>

**Scope.** <what was audited, at what depth, against which revision>
**Method.** Source review; <bounded local checks, if any>. No requests were made to any
deployed system.
**Result.** <n> confirmed (<n> critical, <n> high, …), <n> needs validation, <n> rejected.

## Confirmed findings
| # | Severity | Title | Boundary | Observed result |

### <n>. <title> — <severity>
- **Location** `path:line`
- **Principal** <who, with what starting capability>
- **Path** <each hop, ending at the sink>
- **Control that should have stopped it** <and why it does not>
- **Likelihood** <High/Medium/Low> — <reason>
- **Impact** <High/Medium/Low> — <reason, including the identity involved>
- **Result observed** <the smallest concrete effect>
- **Fix** <the named change> — **Regression test** <what would fail before the fix>

## Needs validation
| # | Title | Blocker | Check that would settle it |

## Rejected
| Claim | Why it was rejected |

## Hardening, not findings
- <defence in depth with no demonstrated path, no severities>

## Coverage
- Covered / Deferred / Blocked / Not examined, each with its reason
```

Asked to fix rather than to audit? Same rules and the same order of work; edit the files, then
report what changed, how it was verified, and which findings remain open.

## Environment

- `git` is required. `semgrep` is needed only for the `rule-ize` workflow:
  `uv tool install semgrep`, or `pipx install semgrep`. The claims in
  `references/semgrep-rules.md` were measured against 1.177.0.
- Use the ecosystem's own auditor when the tree is really available — `npm audit`,
  `pip-audit`, `osv-scanner`, `cargo audit`, `govulncheck` — and quote its output instead of
  recalling advisory numbers from memory.
- Secret history scanning (`gitleaks`, `trufflehog`) is optional; when it is unavailable,
  `git log -S` over the candidate fragments is the fallback and is worth saying so.
- Nothing here substitutes for the repository's own tests and tooling. When you did not run
  something, say so rather than implying the result.
