# Writing semgrep rules that survive CI

Verified against: semgrep 1.177.0

## Contents

- [When a finding deserves a rule](#when-a-finding-deserves-a-rule)
- [The loop](#the-loop)
- [The test file is the specification](#the-test-file-is-the-specification)
- [Reading `--test` output](#reading---test-output)
- [The silent-zero trap](#the-silent-zero-trap)
- [Pattern mode versus taint mode](#pattern-mode-versus-taint-mode)
- [Sanitizers, and the way they backfire](#sanitizers-and-the-way-they-backfire)
- [Severity values](#severity-values)
- [Rule hygiene](#rule-hygiene)
- [Messages](#messages)
- [Putting it in CI](#putting-it-in-ci)

## When a finding deserves a rule

Turn a finding into a rule when the bug is a **shape** the codebase can reproduce: a
project-specific dangerous sink, a house rule about which helper may receive request data, a
pattern the audit found three times. Do not write a rule for a one-off logic bug, and do not
write a rule for something the ecosystem's own rulesets already cover well.

A rule is a permanent obligation: every false positive it produces is paid by every developer
who touches the file afterwards. That is why the test file is not optional.

## The loop

```
1. State the bug as an invariant      "request data must never reach db.raw_query()"
2. Write the test file first          real call sites, vulnerable and safe, annotated
3. Look at the AST if a pattern misses   semgrep --dump-ast
4. Write the rule
5. semgrep --test until 1/1 passes    not "most tests pass"
6. Simplify, then re-run the tests
7. Run it over the real tree and read every hit
```

Steps 2 and 5 are what separate a rule from a guess. A pattern that looks right and matches the
one example in front of you routinely has both a false positive and a false negative.

## The test file is the specification

Annotations go on the line **immediately above** the line that should or should not match:

```python
def a():
    sort = request.args.get("sort", "created_at")
    # ruleid: no-tainted-raw-query
    return db.raw_query("SELECT 1 ORDER BY " + sort)


def b():
    sort = request.args.get("sort", "created_at")
    column = ALLOWED.get(sort, "created_at")
    # ok: no-tainted-raw-query
    return db.raw_query("SELECT 1 ORDER BY " + column)
```

Populate it from the real call sites the audit collected, not from invented minimal examples.
The safe cases are the ones that matter: a rule that catches the bug and also fires on the three
correct call sites next to it will be disabled within a week.

The safe cases worth including every time:

- The already-fixed form of the bug — the allowlisted, bound-parameter, escaped variant.
- The same sink reached from configuration or a constant instead of a request.
- The safe sibling API (`db.query` next to `db.raw_query`).
- A variable that passes through the project's own validation helper.

## Reading `--test` output

```
$ semgrep --test --config no-tainted-raw-query.yaml no-tainted-raw-query.py ; echo rc=$?
0/1: 1 unit tests did not pass:
	✖ no-tainted-raw-query
	missed lines: [10], incorrect lines: []
rc=1
```

- `missed lines` — a `ruleid:` annotation the rule did not match. **False negative.**
- `incorrect lines` — a match on a line with no `ruleid:` annotation. **False positive.**
- Exit code 1 on any failure, 0 when everything passes.

Both failure directions are real bugs in the rule. A rule shipped with a known
`incorrect lines` entry teaches developers to ignore the rule.

## The silent-zero trap

Two ways `semgrep` exits 0 while proving nothing:

**Basename mismatch in directory mode.** Directory mode pairs `<rule-id>.yaml` with
`<rule-id>.<ext>`; anything else is not discovered as a test:

```
$ ls                                  # cases.py, no-tainted-raw-query.yaml
$ semgrep --test --metrics=off . ; echo rc=$?
No unit tests found. See https://semgrep.dev/docs/writing-rules/testing-rules
rc=0

$ mv cases.py no-tainted-raw-query.py
$ semgrep --test --metrics=off . ; echo rc=$?
1/1: ✓ All tests passed
rc=0
```

Read the `N/M` line, not the exit code. With an explicit `--config <rule>.yaml <testfile>` the
basenames need not match, so that form is the safer one in a script.

**An over-sanitised rule.** Covered below: it reports zero findings on a file with a real bug,
which looks exactly like a clean scan.

## Pattern mode versus taint mode

Pattern mode matches syntax. Use it when the bug is the call itself, independent of what flows
into it: `pickle.loads(...)`, `yaml.load($X)` with no `SafeLoader`, `jwt.decode` without
verification, `shell=True`.

Taint mode tracks data flow from sources to sinks. Use it when the same call is fine or not
depending on where its argument came from — which is every injection class. Compare:

```yaml
# Flags every call, including the one whose value comes from settings.
pattern: db.raw_query(...)
```

```yaml
mode: taint
pattern-sources:
  - pattern: request.$A
pattern-sinks:
  - pattern: db.raw_query(...)
```

The taint version leaves the configuration-derived call alone, which is the difference between
a rule developers keep and a rule they mute.

Taint mode does not understand *semantic* validation. Measured on a call site that validates
with an allowlist and then reassigns:

```python
sort = request.args.get("sort", "created_at")
if sort not in ALLOWED_SORTS:
    sort = "created_at"
return db.raw_query("SELECT * FROM orders ORDER BY " + sort)   # still flagged
```

The value is still request-derived on the path where the guard does not fire, so taint is
technically right and practically a false positive. Resolve it deliberately: add a narrow
sanitizer, or change the call site to select from a map the code owns so the tainted value never
reaches the sink at all. The second is usually the better outcome of the audit.

## Sanitizers, and the way they backfire

A sanitizer that is broader than intended can match the **source** and neutralise the rule.
Measured on a three-case file — `a()` concatenates request data directly, `b()` goes through a
literal-valued dictionary, `c()` goes through a validation helper:

| `pattern-sanitizers` | Findings |
|---|---|
| none | `a`, `b`, `c` — two false positives |
| `pattern: $D.get(...)` | **none at all** |
| `pattern: safe_column(...)` | `a`, `b` — correct for `c` |
| both | none at all |

The middle row is the trap. The source is `request.$A`, and `request.args.get("sort")` itself
matches `$D.get(...)`, so the sanitizer removes the taint at its origin. The rule goes from
three findings to zero and reports a clean file.

Rules to keep from this:

- Sanitize the **specific validation helper**, never a generic method shape.
- After adding a sanitizer, re-run `--test`. The annotated vulnerable case is what catches the
  over-sanitisation; without the test file this failure is invisible.
- A rule whose finding count drops after an edit is guilty until the test file says otherwise.

## Severity values

`semgrep --validate` accepts nine values, and the error message names them:

```
$ semgrep --validate --config sev-banana.yaml
'BANANA' is not one of ['ERROR', 'WARNING', 'INFO', 'INVENTORY', 'EXPERIMENT',
                        'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
[ERROR] Rule parse error in rule sev-banana:
 Bad severity: BANANA (expected ERROR, WARNING or INFO)
```

Both `ERROR` and `HIGH` validate cleanly on their own. Note the second line of that output
mentions only three values: the schema and the rule parser disagree about which set is
canonical, so pick from the nine and do not assume the older triple is the only legal one.
`ERROR` is the one that makes a rule blocking in most integrations.

## Rule hygiene

- **One rule per YAML file**, named after the rule id. Bundling makes `--test` pairing
  ambiguous and makes a single rule impossible to disable.
- **No `todoruleid:` or `todook:`.** They record a known gap as passing. If a case is not
  handled, either handle it or delete the case and say so in the rule's comment.
- **Avoid `languages: [generic]`** when targeting a real language: generic mode matches text and
  loses every structural guarantee that makes the rule precise.
- **No `$FUNC(...)`-shaped patterns.** Matching any call is not a detection.
- Same metavariable twice means the same code twice: `$A == $A` matches `x == x`, not `x == y`.
  Useful for real rules, surprising if unintended.
- Reuse the rule id in the message, the file name and the test file so a CI failure is
  greppable.

## Messages

The message is read by a developer who did not write the rule, in a CI log, with no context.
Make it say what to do:

```yaml
# Unhelpful
message: no-tainted-raw-query

# Useful
message: >-
  Request data reaches db.raw_query(), which does not bind parameters.
  Use db.query() with bound parameters, or map the value through an
  allowlist the code owns before interpolating an identifier.
```

## Putting it in CI

Two commands, doing different jobs:

```sh
# 1. The rules still do what their tests say. Run this on changes to the rules.
semgrep --test --config rules/ rules/

# 2. The codebase is clean. Exclude the rule directory, or its deliberate
#    bad examples fail the build.
semgrep scan --config rules/ --exclude rules/ --error .
```

`--error` makes findings a non-zero exit. Without it the scan reports and passes. Keep the
rule directory out of the scan target, and keep the test command in the pipeline — a rule that
silently stops matching after a refactor is worse than no rule, because the team believes it is
covered.

<!-- sources: tob-semgrep-rules, semgrep-skills, cloudflare-audit -->
