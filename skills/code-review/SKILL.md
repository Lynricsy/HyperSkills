---
name: code-review
description: "Reviews code changes and pull-request diffs, or evaluates review feedback."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: task
---

Paths below are relative to this skill's directory.

## Scope

Review of a bounded set of changes — a diff, a commit range, a branch, a pull request — and the
other half of the job: acting on review feedback you received. Applies to code written by a
human, by another agent, or by you.

Not covered: auditing a whole codebase for vulnerabilities. Reviewing a diff for general
correctness and style is the `code-review` skill's job; auditing a whole codebase, feature or
threat surface is the `security-review` skill's. Also not covered: redesigning an
architecture, and language- or framework-specific correctness, which
belongs to the ecosystem skill for that stack — `android`, `apple`, `csharp-dotnet`, `flutter`,
`go`, `java-spring`, `python`, `react`, `react-native`, `typescript` and the rest. Team process
— review SLAs, round cadence, approval bureaucracy — is out of scope by design.

The mechanics of moving a review through GitHub — creating the pull request, writing its
description, fetching review threads, posting replies, merging — are the `github` skill's job.
This skill supplies the opinion; that one supplies the plumbing.

Reviewing a REST contract or an OpenAPI document as a design — resource modelling, status
codes, pagination style, the error schema, what counts as a breaking change — is the
`api-design` skill's job. This skill reviews the diff that implements it.

Writing the change itself is not review work: use the `test-driven-development` skill for that,
and the `debugging` skill when a review finding turns out to need a diagnosis rather than a fix.

## Core rules

1. **Route before you read the diff.** Reviewing, or responding to a review? Standard, or
   security-sensitive (auth, crypto, external calls, value transfer, removed validation,
   dependency bumps)? The three workflows below do different jobs; a blended pass does none
   of them.
2. **Pin the fixed point before anything else.** Confirm it resolves with
   `git rev-parse <base>`, then take the diff three-dot: `git diff <base>...HEAD` plus
   `git log <base>..HEAD --oneline`. An unpinned review drifts as the branch moves. A bad ref or
   an empty diff stops the review here — say so rather than silently reviewing the working tree,
   and never let it fail inside a reviewer you already dispatched.
3. **Review the tests before the implementation.** They state what the author believes the
   change does, and a weakened assertion is the most expensive thing a review can miss.
4. **Gather Standards and Spec findings separately, report them in separate sections, and never
   rerank across axes.** Code can honour every standard and implement the wrong thing; one axis
   masks the other the moment they are merged.
5. **Lead with the highest-leverage finding.** One structural problem plus ten nits is a review
   about the structural problem.
6. **Every finding carries `file:line`, what is wrong, why it matters, and the fix.** A finding
   nobody can act on is deleted, not softened.
7. **Verify each finding before reporting it, and drop what you cannot substantiate.** False
   positives cost the author more than a missed nit. Skip what the repo's tooling already
   enforces, anything pre-existing outside the diff, and points a senior engineer would not
   raise.
8. **Label every comment with a severity.** Unlabelled feedback makes the author treat optional
   polish as blocking.
9. **End with an explicit verdict: Ready to merge — Yes, No, or With fixes.** A review without
   a verdict hands the decision back to the author.
10. **A reviewer is read-only.** Never touch the working tree, index, HEAD or branch state; to
    inspect another revision use `git worktree add /tmp/review-<sha> <sha>`.
11. **The orchestrator may fan out; a reviewer never re-delegates.** Standards, Spec and
    Security can run as parallel reviewers, each doing its own full pass. A reviewer that spawns
    another reviewer duplicates a seat at full cost and its verdict counts for nothing.
12. **The approval bar depends on whose work it is.** Reviewing someone else's change: approve
    when it definitely improves overall code health, even if imperfect — blocking on non-Critical
    findings is obstruction. Reviewing your own work before claiming it is done: every Critical
    and Important finding is fixed first.
13. **Do not rubber-stamp and do not soften.** "LGTM" without evidence of reading helps nobody,
    and calling a production bug "a minor concern" is dishonest. Quantify where you can, and
    comment on the code rather than on the person who wrote it.
14. **Cleanup refactors (no behaviour change, tests stay green) belong inside the TDD loop.
    Structural refactors are raised by review and land as their own change.**
15. **Propose the move, not just the problem** — name the restructuring
    (`references/smell-baseline.md`), because "this is complex" leaves the author guessing.
16. **Dead code is listed, not silently deleted.** Enumerate what the change orphaned and ask
    before removing it.
17. **A dependency bump is a behaviour change you did not write.** Read the changelog, one
    package per change, green suite before and after, and review the lockfile diff.
18. **When receiving feedback, verify before implementing. If any item is unclear, clarify every
    unclear item and wait for the answers before touching any item, the clear ones included.**
    Items relate to each other, so an answer can change what an apparently clear item should do.
19. **Never performative agreement.** No "You're absolutely right", no "Great point", no thanks.
    `Good catch — <specific issue>. Fixed in <location>.` is fine: it carries information.
20. **Security is a standing axis, escalation is triggered.** Every review runs the security
    lens; only the high-risk triggers pull in `security-review-delta`. Full adversarial
    modelling on a low-risk diff is wasted effort.
21. **Evidence before claim: state the command you ran, its output, and what that output proves.
    "Should work", "looks right" and a passing build you did not watch are not evidence.**
22. A seam is a place where behaviour can be substituted without editing the code under test.
    Agree on the seam before writing the test: the seam decides what the test can observe.

## Workflows

### review-changes

- [ ] Pin the base and validate it: `git rev-parse <base>`, then
      `git diff <base>...HEAD --stat` and `git log <base>..HEAD --oneline`. Stop on a bad ref
      or an empty diff.
- [ ] Decide scope from the stat: review inline only when the diff is small. Otherwise dispatch
      reviewers with `references/reviewer-prompt.md` — the diff and the reasoning stay in their
      context and only findings come back, which is the difference between one review and a
      spent context window.
- [ ] Find the **spec** in this order: issue references in the commit messages, a path the user
      gave, a spec file under `docs/` or `specs/` matching the branch, then ask. No spec at all:
      report "no spec available" on that axis rather than inventing requirements.
- [ ] Find the **standards**: whatever the repo documents (`CONTRIBUTING.md`,
      `CODING_STANDARDS.md`, house style), plus the always-on smell baseline in
      `references/smell-baseline.md`. A documented repo rule overrides the baseline.
- [ ] Review the tests first: do they exist, do they test behaviour, are edge cases covered,
      and would they fail if the changed behaviour broke? A deleted or neutered assertion is a
      Critical finding, not a nit.
- [ ] Collect **Spec** findings: requirements missing or partial, behaviour nobody asked for
      (scope creep), requirements implemented wrongly. Quote the spec line for each.
- [ ] Collect **Standards** findings through the five lenses — correctness, readability and
      simplicity, architecture, security, performance — citing the documented rule or the named
      smell. Keep the two collections apart.
- [ ] Size the change: around 100 changed lines reviews cleanly, ~300 is acceptable for one
      logical change, ~1000 is too large. Oversized: name the split strategy instead of
      pretending to have read it all.
- [ ] Verify the author's verification: which commands were run, what the output was, whether
      the build and suite actually passed. "Tested locally" with no output is not a verification
      story.
- [ ] Verify each finding against the code once more, drop the unsubstantiated ones, assign
      severity, and write the report in the output format below.
- [ ] Close the loop on hygiene: list dead code the change orphaned (ask before deleting) and
      apply the dependency rules to any bump.
- [ ] **Gate — verdict backed by findings:** every finding has `file:line`, an impact and a fix;
      the two axes are in separate sections; the report ends with Ready to merge — Yes, No, or
      With fixes, and the reasoning names the findings that drove it.

### security-review-delta

Runs on top of `review-changes` when a high-risk trigger fires. Full detail, including the
escalation triggers and the report skeleton, in `references/security-review.md`.

- [ ] Risk-classify every changed file: HIGH for auth, crypto, external calls, value transfer or
      removed validation; MEDIUM for business logic, state changes, new public API; LOW for
      comments, tests, UI, logging. Classify by risk, never by diff size — a two-line change
      removed a guard once and became a CVE.
- [ ] Set the depth from the codebase size (`git ls-files | wc -l`): under 20 files read the
      dependencies too, 20–200 follow one hop from the changed code, 200+ walk only the paths
      the change can reach.
- [ ] Blame everything the change removed: `git log -S '<removed expression>' --oneline` and
      `git blame <base> -- <file>`. A guard deleted in a commit whose history says "fix",
      "security" or "CVE" is Critical until the author proves otherwise; code added, removed for
      safety, then re-added is a regression.
- [ ] Size the blast radius: count the callers of each changed symbol
      (`grep -rn '<symbol>(' <source-dirs> | wc -l`) and cross it with the risk class. A
      high-risk change with many callers is the first thing you review, not the last.
- [ ] Check coverage of the changed lines. A new function with no test, or modified validation
      whose tests did not change, raises the severity — an untested change is a riskier change.
- [ ] For each HIGH finding write one concrete attack scenario: goal, preconditions, steps, why
      it works (pointing at the changed lines), impact. Generic warnings are not findings.
- [ ] Write the review to a file and say where it is. State plainly what you could not examine
      at the depth you chose.
- [ ] **Gate — every security finding cites evidence:** a line reference, plus a commit, caller
      count, coverage gap or attack path. No evidence, no finding.

### respond-to-review

Expanded, with worked replies, in `references/receiving-review.md`.

- [ ] Read the whole review before touching anything. Reacting item by item produces work you
      will undo.
- [ ] Count the unclear items. **One or more unclear: no file is edited this turn.** Ask about
      all of them in one round and wait, the clear items included — an answer can change what
      an apparently clear item should do. Look up facts yourself; only decisions go to the
      reviewer or the user:

      ```
      ❓ Q1 — <short title>
      <the question, one or two lines>
      ➡️ Recommended: <your answer and why>
      ```

- [ ] Verify each item against the code. Trust a maintainer who knows the codebase; be
      sceptical of an external reviewer but check carefully — does it hold for this codebase,
      does it break something, is there a reason for the current shape, does the reviewer have
      the full context?
- [ ] Evaluate before implementing. Asked to "do it properly"? Grep for callers first: if
      nothing calls it, the finding is that it should go, not that it needs cursor pagination.
- [ ] Respond with a technical acknowledgment or a reasoned pushback that cites the code, a test
      or a version constraint. If you cannot verify a claim, say so and ask which way to go.
- [ ] Implement in order — blocking first, then trivial fixes, then anything structural — and
      test each item on its own so a failure names its cause.
- [ ] Pushed back and turned out wrong? State the correction and move on: no apology arc, no
      defence of the pushback.
- [ ] Reply where the comment lives: inline review comments get thread replies
      (`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies -f body='<reply>'`), not a
      new top-level PR comment. Link code with a full-SHA permalink; a shortened or generated
      ref does not render.
- [ ] **Gate — evidence before claim:** for every item, either the command output that shows it
      fixed, or the reasoning and code reference for why it was not.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Dispatchable reviewer prompt, read-only guard, output contract | Dispatching a reviewer for anything non-trivial | `references/reviewer-prompt.md` |
| Fowler smell baseline, structural remedies, judgement-call rules | Collecting Standards findings | `references/smell-baseline.md` |
| Risk triage, blame on removed guards, blast radius, attack scenarios, report skeleton | A high-risk trigger fired | `references/security-review.md` |
| Responding to feedback, source scepticism, pushback and correction examples | Feedback arrived and something is unclear or looks wrong | `references/receiving-review.md` |

## Output format

Use this shape. Skip empty sections; keep the two axes apart; order within each section by
severity. Comment prefixes map onto the section headings: Critical stays Critical, an unprefixed
required change is Important, Nit and Optional are Minor, FYI becomes a Recommendation.

```markdown
### Strengths
- Specific, and only what you actually verified.

### Spec findings
#### Critical
1. **Order total ignores discounts** — `src/checkout/total.ts:44`
   - Spec (`docs/specs/checkout.md:18`) requires discounts applied before tax.
   - Impact: every discounted order overcharges.
   - Fix: apply `discount(order)` before `tax(order)`, and cover it with a test.
#### Minor
1. **Nit: unused `legacyRate` parameter** — `src/checkout/total.ts:12`

### Standards findings
#### Critical
1. **Query built by concatenation** — `src/orders/handler.js:31`
   - Breaks `CONTRIBUTING.md` "SQL is always parameterized".
   - Impact: `customerId` reaches the database as SQL; any caller can read other customers.
   - Fix: `pool.query('… WHERE customer_id = $1', [customerId])`.
#### Important
1. **Validation removed with no replacement** — `src/orders/validate.js` deleted
   - `git log -S assertPositiveQuantity` points at the commit that added the guard; the
     quantity check is now gone from every path.
   - Fix: keep the boundary check, or state here why it is safe to drop.

### Recommendations
- FYI: the handler module is nearing the size where splitting it pays off.

### Assessment
**Ready to merge: No**
**Reasoning:** two Critical findings — the concatenated query and the neutered quantity test —
both in code paths this change introduces.
```

Asked to fix rather than to review? Same rules, same order; edit the files and report what
changed and how you verified it, instead of returning a report.

## Environment

- `git` is required; every command above is plain `git`. `gh` is only needed for pull-request
  threads and is optional otherwise.
- Nothing here substitutes for running the repo's own suite. When you did not run it, say so
  rather than implying the change is verified.
- If the project exposes a GitHub MCP server, prefer its tools for posting inline comments over
  shelling out.
