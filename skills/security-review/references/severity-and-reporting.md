# Severity, evidence and the report

## Contents

- [Severity is derived, not chosen](#severity-is-derived-not-chosen)
- [Likelihood](#likelihood)
- [Impact](#impact)
- [Combining them](#combining-them)
- [The three dispositions](#the-three-dispositions)
- [What an exploitability argument contains](#what-an-exploitability-argument-contains)
- [Chains](#chains)
- [CVSS](#cvss)
- [Report template](#report-template)
- [Writing the fix](#writing-the-fix)
- [Tone rules](#tone-rules)

## Severity is derived, not chosen

A severity label that cannot be reconstructed from the evidence is an opinion, and the reader
will either accept all of them or none of them. Derive every label from two judgements made
separately, each with its own one-line reason. Reporting only the combined number hides which
half is weak, and the weak half is where the argument usually is.

## Likelihood

What the attacker needs before the bug is useful:

| Factor | Raises likelihood | Lowers it |
|---|---|---|
| Exposure | Reachable pre-authentication from the internet | Requires a privileged role, or local access |
| Preconditions | None | A specific state, a race, a victim action, a second bug |
| Discoverability | Visible in a response, a public route, an error message | Requires reading source or brute force |
| Controls | None on the path | A partial mitigation (WAF, rate limit, network policy) |

State the exposure fact you relied on. "Reachable pre-auth because of the `/reports/*` proxy
rule" is a likelihood argument; "likely" is not.

## Impact

What was **demonstrated**, not what is imaginable:

| Impact | Means |
|---|---|
| Code execution | Attacker-chosen code runs, with the identity that process holds |
| Full data compromise | Every tenant's records, or the credential that grants them |
| Cross-tenant access | One tenant reads or writes another's data |
| Single-record access | One other principal's record |
| Integrity | State changed that should not be — balance, entitlement, audit trail |
| Availability | The service is down or degraded for others |
| Information leak | Data that helps another attack but is not itself sensitive |

Impact includes the identity involved. Code execution in a process holding a cloud role with
`s3:*` on `*` is a different finding from code execution in a sandboxed worker with no
credentials, and the policy is the evidence for the difference.

## Combining them

| | Low impact | Medium | High | Critical impact |
|---|---|---|---|---|
| **High likelihood** | Low | Medium | High | Critical |
| **Medium** | Low | Medium | High | High |
| **Low likelihood** | Info | Low | Medium | High |

Two hard rules:

1. **Overall severity never exceeds demonstrated impact.** "Could lead to full compromise" with
   no path shown is not Critical.
2. **A finding you could not establish is not a low-severity finding.** It goes to
   needs-validation with no severity at all. Downgrading an unproven claim to Medium to keep it
   in the report is how a report loses its reader.

## The three dispositions

Every candidate ends in exactly one, and the disposition decides which section it appears in:

| Disposition | Requirements | Gets a severity? |
|---|---|---|
| `confirmed` | Complete path from a named lower-trust principal to a demonstrated effect, every cited location re-read | Yes |
| `needs-validation` | Real path in source, blocked by one specific fact outside source, plus the exact check that would settle it | No |
| `rejected` | Source, a visible control, real usage or missing impact refutes it | No — kept with its reason |

Keep the rejected ones in the report's appendix with why. It stops the next pass re-raising
them and it shows the reader what was considered and dismissed, which is itself coverage
information.

A `needs-validation` entry must name a fact, not a feeling: "which IAM policy is attached to
`reporting-service`", "whether the proxy strips `x-internal-role`", "whether `node-serialize`
is imported anywhere". "Needs more investigation" is not a blocker; it is an unfinished
finding.

## What an exploitability argument contains

For every confirmed finding:

1. **Principal** — who, with what starting capability.
2. **Entry** — the exact interface and input shape.
3. **Path** — each hop with `file:line`, ending at the sink or the boundary effect.
4. **Control that should have stopped it** — and why it does not. This is the sentence a
   reviewer disputes, so make it explicit.
5. **Result** — the smallest concrete effect. One dummy record read, one state transition, one
   command executed. Stop there.
6. **Identity** — what the affected process or credential can reach.

The evidence boundary for a defensive audit is source reading plus, where genuinely needed, a
bounded local reproduction: a unit test, a small harness, a malformed fixture, a locally
rendered policy. Not a request to a deployed service, a provider API, a shared environment or
another user's data. When a fact can only come from a running system, it is a
needs-validation blocker with a safe check the owner can perform — not a reason to go and try
it.

## Chains

When several weak facts combine into one strong outcome, report the chain as one finding at the
chain's severity, with each link cited. Three separate mediums for the same path understate it
and let each link be dismissed individually.

Chains also need their weakest link tested honestly. A callback that only issues POST requests
does not read a metadata service that answers GET; saying so, and noting that a single
redirect-following code path would complete the chain, is a stronger report than asserting the
credential theft. Getting one link wrong invalidates the finding and the reader's trust in the
rest of it.

## CVSS

Use a CVSS vector only if the recipient's process needs one, and treat it as output rather than
reasoning: the base score has no notion of your deployment, so a vector produced without the
environmental metrics will disagree with the severity you derived. When both appear, the
narrative severity governs and the vector is labelled as the base score.

## Report template

One Markdown file. Skip empty sections. Findings ordered by severity within each section.

```markdown
# Security review — <scope>

**Scope.** <what was audited, at what depth, against which revision>
**Method.** Source review; <bounded local checks, if any>. No requests were made to any
deployed system.
**Result.** <n> confirmed (<n> critical, <n> high, …), <n> needs validation, <n> rejected.

## Confirmed findings

| # | Severity | Title | Boundary | Observed result |
|---|---|---|---|---|
| 1 | Critical | Unauthenticated RCE through report resume | proxy → reporting | pickle payload executes as the reporting service |

### 1. Unauthenticated RCE through report resume — Critical

- **Location** `services/reporting/app.py:38`
- **Principal** anonymous internet, via the `/reports/*` proxy rule
- **Path** request body `.cursor` → `base64.b64decode` (`app.py:37`) →
  `pickle.loads` (`app.py:38`)
- **Control that should have stopped it** none; the cursor is neither signed nor schema-checked,
  and the comment asserting it is "the cursor we gave them" is not enforced anywhere
- **Likelihood** High — one unauthenticated request, no state required
- **Impact** Critical — code execution as an identity holding `s3:*` and `sts:AssumeRole` on `*`
- **Result observed** a local harness reconstructing the same call executes the payload's
  `__reduce__`
- **Fix** replace the client-held cursor with a server-side state id, or JSON validated against
  an explicit schema; delete the pickle path rather than signing it
- **Regression test** posting a pickle payload to `/internal/reports/resume` returns 400

## Needs validation

| # | Title | Blocker | Check that would settle it |
|---|---|---|---|
| 5 | Metadata credential theft via callback | the callback path only issues POST; no GET or redirect-following path was found in the files reviewed | grep the service for redirect-following clients; confirm whether IMDSv1 is enabled on the cluster |

## Rejected

| Claim | Why it was rejected |
|---|---|
| SSRF in `notify_billing` | the URL comes from `settings.BILLING_URL`, set from deployment config, not from a request |

## Hardening, not findings

- <defence-in-depth items with no demonstrated path, clearly separated from findings>

## Coverage

- Covered: <units>
- Deferred: <units, and why they ranked below what was done>
- Blocked: <units, and the missing fact>
- Not examined: <explicit>
```

## Writing the fix

- Name the change, not the goal. "Add `AND customer_id = $2` to the order lookups in
  `routes/orders.js:19` and `:26`" beats "enforce authorization".
- Prefer the fix that makes the class impossible over the fix that patches the instance: a
  data-access layer that requires a principal, row-level security, an egress policy. Say which
  of the two you are proposing.
- Give the regression test with the fix. A fix with no test comes back.
- When the fix has a cost — a breaking API change, a migration, session invalidation — say so.
  A recommendation that hides its cost gets silently dropped.

## Tone rules

- No finding without a location. A finding nobody can act on is deleted, not softened.
- No severity inflation to get attention, and no softening of a real production bug into "a
  minor concern". Both are dishonest in the same way.
- Zero confirmed findings is a valid result. Report it with the coverage statement and resist
  padding with informational observations.
- Say what you did not check, in the same detail as what you did.

<!-- sources: cloudflare-audit, tob-brocards, sentry-secreview, openai-threatmodel, copilot-secreview -->
