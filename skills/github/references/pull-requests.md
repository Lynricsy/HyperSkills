# Pull requests with `gh`

## Contents

- [Establishing the coordinates](#establishing-the-coordinates)
- [Titles](#titles)
- [Body shapes](#body-shapes)
- [Reviewer aids](#reviewer-aids)
- [Creating and updating](#creating-and-updating)
- [Linking an issue](#linking-an-issue)
- [CI checks](#ci-checks)
- [Fetching review feedback](#fetching-review-feedback)
- [Replying and resolving](#replying-and-resolving)
- [Requesting review](#requesting-review)
- [Merging](#merging)
- [`gh` and API quirks](#gh-and-api-quirks)

## Establishing the coordinates

```bash
git branch --show-current
git status --porcelain
gh pr view --json number,url,title,body,baseRefName,headRefName,isDraft,reviewDecision,mergeable
gh repo view --json defaultBranchRef,nameWithOwner
```

`gh pr view` failing with "no pull requests found" means this is a create. For an existing PR the
base is its `baseRefName`; for a new one it is whatever you pass to `--base`, defaulting to the
repository's default branch — which is why `--base` must be explicit whenever the target is a
release or integration branch. Being on `main` with uncommitted work means a branch has to exist
first; that part is local git.

Then read the whole branch, never the last commit:

```bash
BASE=origin/<base>
git log "$BASE"..HEAD --oneline
git diff "$BASE"...HEAD          # three-dot: against the merge base
gh pr diff <number>              # for an existing PR
```

## Titles

`<type>(<scope>): <subject>` or `<type>: <subject>`, with types `feat`, `fix`, `refactor`,
`perf`, `docs`, `test`, `build`, `ci`, `chore`, `style`, `revert`.

- Describe the dominant change of the whole branch with the narrowest accurate type and scope.
- A breaking-change marker (`feat!:`) only when an external contract breaks, and then explain the
  surface in the body.
- No vague subjects — `update`, `cleanup`, `misc`, `address feedback` — and no trailing period.
- Keep an existing title only while it still describes the whole diff.

## Body shapes

The body is a cover note for reviewers: what changed, what it affects, where to start. Pick the
smallest shape that does that.

| Change | Include |
|---|---|
| Small or obvious | One paragraph, no headings. |
| Feature, fix, refactor | Changed behaviour and its effect; add root cause, unchanged behaviour, or the non-obvious part of the approach when relevant. |
| Contract or breaking change | The affected API, schema, payload, config, permission, storage or CLI surface, plus compatibility and migration guidance. |
| Operational or visual change | Operator effect, measured impact, failure modes. |
| Broad or generated change | The organising principle, why the breadth is necessary, and where review should start. |

What to leave out, always: a `Summary` / `Changes` / `Test Plan` scaffold added because the
template has one, an exhaustive file list, pasted command output or CI logs, commit logs,
unchecked checklist items, and internal process vocabulary. Reviewers get the file list and the
test results from the diff and the checks; repeating them costs attention and hides the two
sentences that matter.

Routine validation is omitted unless it changes the risk assessment. Never include customer or
organisation names, user emails, support-ticket contents, secrets or personal data.

When a follow-up round rewrites the PR, describe the resulting change as a whole. A body that
narrates the review history ("addressed feedback, then reverted, then …") is unreadable to the
next reviewer.

## Reviewer aids

Add one only when it saves the reviewer reconstruction work: a compact before/after for a changed
contract, a small diagram for an async flow or state machine, a screenshot when visual evidence
exists, or a rollout and review-order note. Introduce it with one sentence saying what to notice.

## Creating and updating

```bash
gh pr create --draft \
  --base release/2.x \
  --head fix/cache-key \
  --title 'fix(cache): normalise header casing before hashing the key' \
  --body-file /tmp/pr-body.md
```

Always `--body-file`. An inline `--body` with multi-line markdown loses newlines to shell
quoting, and the damage only becomes visible on the rendered PR. Create as a draft when CI has
not run yet, then `gh pr ready` once it is green.

Updating an existing PR:

```bash
gh pr view <n> --json body --jq .body > /tmp/current-body.md   # read before you write
gh pr edit <n> --title '<title>' --body-file /tmp/new-body.md
```

Reading first is not ceremony: teams keep bot-maintained sections, checklists and issue blocks in
the body, and a blind `--body-file` deletes them. Append or replace a specific section instead.

Refresh the title and body when follow-up commits materially change scope, approach, breaking
behaviour, risk or migration. Skip typo-, formatting- and rename-only follow-ups.

## Linking an issue

Closing keywords — `close`/`closes`/`closed`, `fix`/`fixes`/`fixed`,
`resolve`/`resolves`/`resolved` — go in the PR body or a commit message:

```
Closes #412
Fixes octo-org/other-repo#100
Resolves #10, resolves #123
```

Each issue needs its own keyword; `Closes #10, #11` links only the first. Keywords may be
capitalised or followed by a colon.

**The keywords are interpreted only when the pull request targets the repository's default
branch.** On a PR into `release/2.x` or any other branch they are ignored outright: no link is
created and merging closes nothing. There, link the issue from the PR sidebar (up to ten, same
repository) or leave a reference on the issue, and tell the user the keyword would have been
inert. A keyword in a commit message still closes the issue when the commit reaches the default
branch, but the PR is not listed as a linked pull request.

`Refs #412` and a bare `#412` create a cross-reference, not a link, and close nothing. Use them
when the PR advances an issue without finishing it — and only when the issue number is verified
from the user, the branch name, the commits or the tracker, never guessed.

## CI checks

```bash
gh pr checks                      # current state
gh pr checks --watch              # block until they settle
gh pr checks --json name,state,bucket,link,workflow
gh run view <run-id> --log-failed
gh run rerun <run-id> --failed
```

Wait only for checks that can change on their own. Review bots that post findings are worth
waiting for; approval, `isDraft`, `REVIEW_REQUIRED` and coverage reporters resolve only when a
human acts, so waiting on them is a hang. When every remaining pending item is a human gate,
report that and stop.

A failing check with a details URL that is not an Actions run belongs to another CI platform:
report the URL and do not investigate it.

`gh`'s `--json` field sets drift between versions. When a field is rejected, rerun with the
fields `gh` names in the error rather than guessing; and confirm any unfamiliar subcommand with
`gh help <command>` before putting it in guidance.

Fixing a failure: read the whole log, trace from the assertion, exception or lint rule to the
source, state the cause before editing ("fails because X, affected by Y"), search for other
instances of the same pattern, fix the root cause, and re-run the specific test locally before
pushing. After the same check fails twice, stop and ask rather than pushing a third guess.

## Fetching review feedback

Top-level comments and review bodies:

```bash
gh pr view <n> --comments
gh api repos/{owner}/{repo}/pulls/{n}/reviews
```

Inline threads need GraphQL, paginated. `reviewThreads` is the only view that carries resolution
state:

```bash
gh api graphql -f owner=OWNER -f repo=REPO -F pr=123 -f query='
query($owner:String!, $repo:String!, $pr:Int!, $cursor:String) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$pr) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 20) {
            nodes { databaseId body path line author { login } }
          }
        }
      }
    }
  }
}'
```

Three traps:

- **Do not use `latestReviews`.** It is a "latest per user" projection with stale-cache
  behaviour: a freshly submitted review can be missing from it for minutes. Use
  `reviews(last: 100)` when you need to know whether a new review exists, and filter client-side.
- **Do not filter on `isOutdated`.** A thread can be `isOutdated: true` and `isResolved: false`
  at the same time — commonly because your own fix moved the lines it cites. Filtering those out
  leaves the PR's conversation list non-empty after the code is already fixed.
- Paginate. `reviewThreads(first: 100)` on an active PR silently truncates.

Bucket what comes back: blocking, worth fixing, and declinable. Fix the first two; for a review
bot, fix what is real and explain what is a false positive. Whether a comment is correct is the
`code-review` skill's subject — this file covers getting it fetched, answered and closed.

## Replying and resolving

A reply belongs on the thread, not at the top of the PR:

```bash
gh api repos/{owner}/{repo}/pulls/{n}/comments/{comment_id}/replies \
  -f body='Fixed in <sha> — the key now normalises headers before hashing.'
```

The GraphQL equivalents, needed when you already hold thread ids:

```graphql
mutation($tid: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: { pullRequestReviewThreadId: $tid, body: $body }) {
    comment { id }
  }
}
mutation($tid: ID!) {
  resolveReviewThread(input: { threadId: $tid }) { thread { isResolved } }
}
```

Reply first, resolve second, so the resolution carries a reason. Cite the commit; link code with
a full-SHA permalink, because a branch-relative or shortened ref does not render reliably.

Reply text carries information or is omitted. `Good catch — the header normalisation ran after
hashing. Fixed in <sha>.` is a reply; "You're absolutely right" is not.

## Requesting review

```bash
gh pr edit <n> --add-reviewer <login>,<org>/<team>
gh pr review <n> --approve                    # or --request-changes / --comment
gh pr review <n> --comment --body-file /tmp/review.md
gh api notifications --paginate               # your own review queue
gh api repos/{owner}/{repo}/pulls/{n}/requested_reviewers
```

`gh pr review` takes only `--approve`, `--request-changes`, `--comment`, `--body` and
`--body-file`; anything richer (inline comments in one review payload) goes through
`POST /repos/{owner}/{repo}/pulls/{n}/reviews` with a `comments` array.

Re-request review only after the round is fully answered, and before declaring convergence
confirm the new review's `commit.oid` equals the current head — a review of an older commit is
not a review of the current PR.

## Merging

```bash
gh pr merge <n> --squash --delete-branch
gh pr merge <n> --merge        # preserve the branch's commits
gh pr merge <n> --rebase
gh pr merge <n> --auto --squash   # merge when required checks pass
```

Use the strategy the repository allows — a repository can disable any of the three, and
`--rebase` is refused when the ruleset requires linear history in a way the branch cannot
satisfy. `--auto` needs auto-merge enabled on the repository, and only fires once every required
check and approval is satisfied.

After merging, close the linked issue by hand if the closing keyword was inert on a non-default
base branch.

## `gh` and API quirks

- `gh api graphql -F key=value` applies type inference: a value that parses as an integer,
  boolean or null is sent as that JSON literal. For a variable declared as a non-null String —
  `body`, `owner`, `repo`, a thread id — use `-f`. A reply body of `"true"` or `"12345"`
  otherwise fails with a type error.
- `gh api` exits 0 for an HTTP 200 whose GraphQL body carries a top-level `errors` array. Check
  the body, not just the exit code.
- Quote the whole `-f 'labels[]=bug'` pair. `[]` is a glob in zsh and the argument never reaches
  `gh`.
- Bot reviewers cannot be added with `gh pr edit --add-reviewer`; the REST
  `requested_reviewers` endpoint can return 201 while dropping them. Bot reviewer requests go
  through the GraphQL `requestReviewsByLogin` mutation with `botLogins`, using the app slug
  rather than the display name.

<!-- sources: awesome-copilot, getsentry-skills, github-docs, coderabbit-skills, octocat, openai-skills, gh-pr-reviews, gh-cli -->
