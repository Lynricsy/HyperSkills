# Responding to review feedback

Read when review feedback arrived and any of it is unclear, questionable, or larger than it
looks.

## Contents

- [The six steps](#the-six-steps)
- [Unclear items block everything](#unclear-items-block-everything)
- [How much to trust the reviewer](#how-much-to-trust-the-reviewer)
- [The YAGNI check](#the-yagni-check)
- [Implementation order](#implementation-order)
- [Acknowledging, pushing back, and being wrong](#acknowledging-pushing-back-and-being-wrong)
- [Replying where the comment lives](#replying-where-the-comment-lives)
- [Common mistakes](#common-mistakes)

## The six steps

```text
1. READ       the whole review, without reacting to individual items
2. UNDERSTAND restate each item in your own words — or ask
3. VERIFY     check each claim against the code
4. EVALUATE   is it right for this codebase, as it is today
5. RESPOND    technical acknowledgment, or reasoned pushback
6. IMPLEMENT  one item at a time, testing each
```

Review is a technical exchange, not a social one. Verify before implementing; ask before
assuming; correctness over comfort.

## Unclear items block everything

If any item is unclear, implement nothing until every unclear item is answered. Items relate to
each other, and half-understood feedback produces work that has to be undone.

Ask the whole set in one round, each question numbered and carrying your recommended answer.
Facts are yours to find — look them up rather than asking. Decisions are the reviewer's or the
user's:

```text
❓ Q1 — <short title>
<the question, one or two lines>
➡️ Recommended: <your answer and why>
```

Wrong, even when it looks efficient:

```text
Items 1, 2, 3 and 6 are clear, so I have implemented those. About 4 and 5...
```

Right:

```text
Items 1, 2, 3 and 6 are clear. Two questions first, because 4 changes what 6 should do.

❓ Q1 — Which service sets the retry contract?
Comment 5 asks for retries "consistent with the other service". Two candidates exist:
the billing client retries 3 times with jitter, the search client retries twice.
➡️ Recommended: match the billing client, since this path is also payment-adjacent.

❓ Q2 — Does the history endpoint stay?
Comment 4 asks for cursor pagination on getRateHistory; grep shows no caller in this
repository or the web client.
➡️ Recommended: delete the endpoint in this change and drop the pagination work.
```

## How much to trust the reviewer

**A maintainer of this codebase** is a trusted source: understand the item, then act. Still ask
when the scope is unclear. No performative agreement either way.

**An external or unfamiliar reviewer** deserves careful checking, not deference. Before
implementing, answer five questions:

1. Is it technically correct for *this* codebase, at this version?
2. Does it break existing behaviour?
3. Is there a reason the current implementation is the way it is?
4. Does it hold on every platform, runtime and version the project supports?
5. Does the reviewer have the context this change sits in?

Cannot verify a claim with what you have? Say exactly that and ask which way to go: "I cannot
reproduce this without a staging token. Investigate, ask the reviewer, or proceed with the
current behaviour?"

If an item contradicts a decision the user already made, stop and raise the conflict instead of
quietly reversing the decision.

## The YAGNI check

When a reviewer asks you to "implement this properly" — pagination, caching, a metrics
pipeline — check whether anything uses it first:

```bash
grep -rn 'getRateHistory' src app web | grep -v 'rates.ts'
```

- No callers: the finding is that the code should go. "Nothing calls this endpoint. Delete it
  rather than build pagination for it?"
- Callers exist: implement it properly, as asked.

Both you and the reviewer are serving the same goal. Unused capability added "for completeness"
is cost with no payoff.

## Implementation order

1. Clarify everything unclear — first, and all of it.
2. Blocking items: broken behaviour, security, data loss.
3. Trivial items: names, imports, typos.
4. Structural items: refactors, logic reshaping.

Test each item on its own. A batch of six fixes with one test run tells you the suite is green,
not which fix works. Then confirm nothing regressed.

State the command you ran, its output, and what that output proves — for each item, or for the
group where a single run genuinely covers them.

## Acknowledging, pushing back, and being wrong

Acknowledge with information:

```text
Fixed — awaited fetchRate before caching, so the cache holds numbers. rates.ts:22.
Good catch — the NaN branch was unreachable for empty input, not for text. Fixed in rates.ts:33.
```

Never with content-free praise. "You're absolutely right", "Great point", "Excellent catch",
and any thanks are all noise: the fix in the code is the acknowledgment. What is banned is empty
agreement, not acknowledgment that carries a specific fact.

Push back when the suggestion breaks existing behaviour, when the reviewer lacks context, when
it violates YAGNI, when it is wrong for this stack, when compatibility requires the current
shape, or when it contradicts a decision already taken. Push back with evidence, not tone:

```text
Comment 2: Number.parseInt returns NaN for unparseable input rather than throwing —
parseRateHeader('abc') is NaN today, and rates.test.ts:41 covers it. Keeping the
Number.isNaN branch at rates.ts:33. Happy to switch to Number() plus an explicit
finite check if you prefer one code path.
```

Not:

```text
I don't think that's right.
```

Pushed back and turned out to be wrong? One factual correction, then move on:

```text
Checked — parseInt does throw here because the wrapper passes a symbol. You were right;
implementing your version.
```

No apology arc, no defence of why you pushed back, no re-explaining. The fix is the answer.

## Replying where the comment lives

Inline review comments get replies in their own thread, so the discussion stays attached to the
line:

```bash
gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies -f body='Fixed in <sha>: <what changed>'
```

A new top-level PR comment detaches the answer from the code it is about. When you cite code in
a reply, use a permalink with the full commit SHA and a line range with a line of context either
side; a branch-relative or generated reference does not render and rots the moment the branch
moves.

## Common mistakes

| Mistake | Instead |
|---|---|
| Performative agreement | State the fix, or just make it |
| Implementing before verifying | Check the claim against the code first |
| Implementing the clear items, asking about the rest later | Clarify all unclear items, then implement |
| Batching fixes behind one test run | One item at a time, tested |
| Assuming the reviewer is right | Check whether it breaks something |
| Avoiding pushback to keep the peace | Correctness over comfort, with evidence |
| Cannot verify, proceeding anyway | Name the limitation and ask |
| Claiming it is fixed without running anything | Evidence before claim |

<!-- sources: obra-receiving-review, mattpocock-grilling, obra-verification, anthropic-claude-code -->
