# Keeping false positives out

## Contents

- [Why this is the hard part](#why-this-is-the-hard-part)
- [The dismissal tests](#the-dismissal-tests)
- [Attacker-controlled versus server-controlled](#attacker-controlled-versus-server-controlled)
- [Framework-mitigated patterns](#framework-mitigated-patterns)
- [Check the context before reporting](#check-the-context-before-reporting)
- [What never becomes a finding](#what-never-becomes-a-finding)
- [Hardening notes are a separate section](#hardening-notes-are-a-separate-section)
- [Triaging scanner output](#triaging-scanner-output)
- [Recording a dismissal](#recording-a-dismissal)
- [The opposite failure](#the-opposite-failure)

## Why this is the hard part

Finding candidate patterns is cheap; deciding which are real is the whole job. A report with
twenty findings of which six are wrong is worse than a report with six correct ones, because
after the second false positive the reader starts checking your work instead of fixing bugs —
and the real findings go down with the noise.

So every candidate has to survive an explicit set of tests before it is written down.

## The dismissal tests

Run each candidate through all of these. Failing any one is a dismissal, recorded with the
reason.

**1. No finding without a threat model.** The candidate must name who the attacker is, what
capability they start with, how they reach the behaviour, and what harm results. A description
of code behaviour with no attacker attached is not a finding.

**2. No attacker who already has more than the bug gives.** If exploiting it requires
capabilities that equal or exceed its impact, it is not a vulnerability. "An attacker with
database write access can corrupt the table" describes an attacker who has already won.

**3. Nothing outside real usage.** The path must be reachable in how the software is actually
used and deployed. Dead code, an unregistered handler, a code path behind a feature flag that
is off everywhere, a debug-only branch: dismiss, and say which one applies.

**4. Nothing that is correct implementation of a specification.** If the behaviour is what the
protocol or format requires, the issue is in the specification, not in this code. Report it as
a design or hardening note if it matters, not as a defect here.

**5. Nothing already documented with its security implications.** Behaviour the project
documents as unsafe, with the conditions, is a known trade-off. It can still be a finding if
the documentation is wrong or the conditions are not met — say which.

**6. No cure worse than the disease.** If the remediation causes more harm than the bug —
breaking every consumer, disabling a needed feature, adding a larger attack surface — the
finding must come with a proportionate fix or be reported as an accepted risk with reasoning.

**7. A CVE is neither necessary nor sufficient.** An advisory does not prove the code is
vulnerable here, and the absence of one does not prove it is safe. Evaluate the code path, not
the identifier.

## Attacker-controlled versus server-controlled

Most false positives in injection, SSRF, traversal and redirect classes come from treating a
server-controlled value as attacker input.

| Attacker-controlled — trace it | Server-controlled — not input |
|---|---|
| `request.GET`, `request.POST`, `req.query`, `req.params`, `req.body` | `settings.X`, `app.config['X']`, framework settings |
| `request.json`, `request.data`, raw body | `os.environ.get('X')`, `process.env.X` |
| Most request headers, and the URL path | Values from a config file the operator deploys |
| Unsigned cookies, and any client-held cursor or token the server parses | Compile-time constants and literals |
| Uploaded file contents, names and content types | Internal service URLs assembled from config |
| Rows written by another user | Signed session data, after verification |
| Queue and webhook payloads | Rows written only by an operator or the system |
| WebSocket messages | Build-time generated values |

```python
requests.post(body["callback_url"], json=report)      # trace this
requests.post(f"{settings.BILLING_URL}/events", ...)  # not a finding; say you checked
```

The middle case needs the trace, not a verdict: `f"{settings.BASE}/{x}"` is a finding if and
only if `x` is attacker-influenced. Answer that question before writing anything.

Two refinements:

- A value from the environment is server-controlled **unless** the environment is attacker
  influenced — a CI job that a fork's pull request can trigger, or a container whose env is
  built from request data.
- "Rows written only by an operator" needs checking rather than assuming. If any user-facing
  path writes that column, the row is user input arriving later.

## Framework-mitigated patterns

| Pattern | Usually safe because | Becomes a finding when |
|---|---|---|
| `{{ value }}` in Django, Jinja with autoescape, Vue, Angular | Auto-escaped for HTML text | `\|safe`, `mark_safe(...)`, `{% autoescape off %}`, `v-html` |
| `{value}` in React/JSX | Auto-escaped | `dangerouslySetInnerHTML`, or the value lands in `href`/`src`/`style` |
| ORM filters — `Model.objects.filter(id=x)`, `where({ id: x })` | Parameterized | `.raw()`, `.extra()`, `RawSQL()`, `queryRaw`, builder `.where()` with interpolation |
| `cursor.execute("… %s", (x,))`, `pool.query(sql, [x])` | Bound parameters | Interpolation into identifiers, or the whole SQL built by concatenation |
| CSRF middleware enabled globally | Token enforced on state-changing methods | A route or view exempted, or an API path excluded wholesale |
| `innerHTML = "<b>Loading…</b>"` | Constant string | Any concatenated untrusted value |
| A password hashed with a memory-hard KDF | Correct by construction | The KDF's cost parameters are at library defaults from years ago, or a fast hash is used instead |

Framework protection is present when the code path in question uses it. Verify on the route —
middleware order, decorators, per-route exemptions — rather than on the presence of the import.
The escape hatches in the right column are where real findings live, because someone reached for
them deliberately.

## Check the context before reporting

Four classes are wrong more often than they are right, and each turns on one question:

```python
# SSRF — is the URL from a request?
requests.get(request.GET["url"])        # finding
requests.get(settings.API_URL)          # not a finding
requests.get(f"{settings.BASE}/{x}")    # depends entirely on x

# Path traversal — is the path from a request?
open(request.GET["file"])               # finding
open(settings.LOG_PATH)                 # not a finding
open(f"{BASE_DIR}/{name}")              # depends on name, and on normalisation

# Open redirect — is the destination from a request?
redirect(request.GET["next"])           # finding unless validated against an allowlist
redirect(settings.LOGIN_URL)            # not a finding

# Weak hash — is it protecting anything?
hashlib.md5(file_bytes)                 # cache key or ETag: not a finding
hashlib.md5(password)                   # finding
secrets.token_urlsafe()                 # correct for tokens
random.random()                         # fine for sampling, a finding for a token or a nonce
```

## What never becomes a finding

- Test files, fixtures and example code, unless the audit is specifically about them or a
  fixture holds a live credential.
- Commented-out code, dead code, and documentation examples.
- A pattern whose inputs are all constants or configuration.
- Missing defence in depth with no demonstrated path: a missing header, a verbose error, a
  weak algorithm in a non-security position. These go in the hardening section.
- Anything the repository's own tooling already enforces and fails the build on.
- Pre-existing issues outside the audit's stated scope, beyond a one-line note that they exist.
- Style, dependency freshness for its own sake, or architectural preference restated as risk.

## Hardening notes are a separate section

The instinct to include everything observed is right; the instinct to label it all a finding is
not. Split the report: confirmed findings with paths and severities, then hardening notes with
no severities. The hardening list is where missing headers, long token lifetimes with no
demonstrated theft, absent rate limits and the CSP live. Readers who want the full picture get
it; readers who need to know what to fix this week are not diluted.

Also record the **positive** patterns found — the routes that do scope by tenant, the queries
that are bound, the signature verification that is correct. It tells the reader what the
codebase's own good pattern looks like, and it makes the findings read as specific omissions
rather than as a general accusation.

## Triaging scanner output

A scanner's output is a candidate list, never a findings list. For each hit:

1. Is the flagged input actually attacker-controlled here? Most dismissals end at this step.
2. Does the framework or a control on the path mitigate it?
3. Is the code reachable in real usage?
4. Does the rule's assumed sink match what this code does?

Run the same dismissal tests on the scanner's hits as on your own candidates, and never paste a
scanner's severity into the report. Its severity is about the rule; yours is about this system.

## Recording a dismissal

One line each, kept in the report:

```
Claim: SSRF in notify_billing (report_service.py:57)
Test failed: attacker-controlled input — the URL is settings.BILLING_URL, from deployment
config; no request path writes it.

Claim: md5 usage in cache.py:22
Test failed: no threat model — the digest is an ETag, not a security control.

Claim: prototype pollution via lodash 4.17.20
Test failed: not in real usage — zipObjectDeep is not called anywhere in the tree.
```

Two reasons this matters: the reader can dispute the dismissal, and the next audit does not
re-raise it. A dismissal that later turns out wrong is normal — with the reason recorded, new
evidence reopens it cleanly instead of arriving as a contradiction.

## The opposite failure

Precision discipline turns into missing real bugs when it becomes a reason not to look:

- "The framework probably handles it" is not a verification. Check the route.
- "It requires authentication" lowers likelihood; it does not dismiss a finding, because any
  authenticated user is an attacker in a multi-tenant product.
- "No one would do that" is not a control.
- "It is internal" is a claim about the network that needs reading the network config.
- A candidate you could not settle is needs-validation, not dismissed. Dismissal requires a
  reason; uncertainty is not one.

<!-- sources: tob-brocards, sentry-secreview, cloudflare-audit, openai-secbase, trilwu-audit -->
