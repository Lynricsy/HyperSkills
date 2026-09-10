# Repository governance

## Contents

- [Audit before changing anything](#audit-before-changing-anything)
- [Rulesets and branch protection](#rulesets-and-branch-protection)
- [Rules worth knowing in detail](#rules-worth-knowing-in-detail)
- [Creating a ruleset from the API](#creating-a-ruleset-from-the-api)
- [CODEOWNERS](#codeowners)
- [Dependabot](#dependabot)
- [Secret scanning and push protection](#secret-scanning-and-push-protection)
- [Actions policies](#actions-policies)
- [Environments and deployment approvals](#environments-and-deployment-approvals)
- [Applying changes safely](#applying-changes-safely)

## Audit before changing anything

```bash
gh auth status
gh api user --jq .login                                  # which account will act
gh repo view --json nameWithOwner,visibility,isArchived,isFork,defaultBranchRef
gh api repos/{owner}/{repo}/rulesets --jq '.[] | {id, name, target, enforcement}'
gh api repos/{owner}/{repo}/branches/{branch}/protection  # 404 = none
gh label list --limit 200
gh api repos/{owner}/{repo}/contents/.github --jq '.[].path'
gh api repos/{owner}/{repo}/codeowners/errors
```

Two preflight facts change everything downstream: an archived or forked repository takes no
writes, and an organisation-owned repository needs organisation membership on top of token
scopes. Check both and report rather than discovering it halfway through.

```bash
gh api "orgs/{org}/memberships/$(gh api user --jq .login)" --jq .role   # admin | member | 404
```

Never accept a token pasted into the conversation; if one appears, say it should be revoked.

## Rulesets and branch protection

Both protect refs, and **both apply at once**. Rulesets are the current mechanism and are better
in four specific ways:

- several rulesets can target the same branch, while only one branch protection rule ever
  applies;
- enforcement can be set to `disabled`, `evaluate` (report without blocking) or `active` without
  deleting the rule;
- anyone with read access can see which rulesets apply, so contributors and auditors do not need
  admin;
- rulesets can also restrict commit metadata, file paths, file sizes and tag names.

**Rules aggregate and there is no priority.** If two rulesets, or a ruleset and a legacy
protection rule, define the same rule differently, the most restrictive version wins: a ruleset
requiring three approvals plus a protection rule requiring two means three. A permissive ruleset
therefore never loosens anything, and reading only one of the two sources misstates what is
enforced. Read both before telling a user what their branch requires. [official]

Targeting uses `fnmatch` patterns (`releases/**/*`) or the built-in `~DEFAULT_BRANCH` and
`~ALL`. Limits: 75 rulesets per repository and 75 per organisation.

Bypass lists are the usual reason a "protected" branch is not: a ruleset that lists repository
admins as bypass actors does not stop an admin from pushing straight to `main`. Leave the bypass
list empty unless a specific bot needs it, and put the bot there rather than weakening the rule.

## Rules worth knowing in detail

- **Require a pull request before merging** is what blocks direct pushes. On its own it does not
  require approval — required approvals is an additional setting.
- **Require review from Code Owners** is the setting that turns CODEOWNERS from a notification
  into a gate. It sits on top of required reviews.
- **Require status checks to pass**: strict mode ("require branches to be up to date before
  merging") forces the head branch to be current, which costs extra builds; loose mode does not.
  Also note that anyone with write access can set the state of *any* status check, so for a check
  that matters, select the specific GitHub App as its expected source.
- A required status check on a path-filtered workflow deadlocks merges when the filter does not
  match, because the check never reports at all.
- **Require linear history** forces squash or rebase merges; it rejects merge commits, so a
  repository that also disables squash merging has made merging impossible.
- **Require signed commits**: rulesets verify only commits not reachable from other branches
  when a branch is created, while protection rules verify differently — the same repository can
  behave differently depending on which mechanism is in play.
- **Metadata restrictions** (commit message, author email, branch name patterns) block the *ref
  update*, not the push. The rejected commits still land in the repository as unreachable
  objects, and the contributor has to rewrite them because commit metadata is immutable. Apply
  these to `main` only; on topic branches they are daily friction.
- **Merge queue** is repository-level only, not available in organisation rulesets.

## Creating a ruleset from the API

```bash
gh api repos/{owner}/{repo}/rulesets -X POST --input - <<'JSON'
{
  "name": "main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "bypass_actors": [],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "require_code_owner_review": true,
        "dismiss_stale_reviews_on_push": true,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false,
        "allowed_merge_methods": ["squash", "rebase"]
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [{ "context": "test" }]
      }
    }
  ]
}
JSON
```

Create it with `"enforcement": "evaluate"` first on a busy repository: it reports what would have
been blocked without blocking anyone, which is the cheapest way to find out that a required check
name is wrong. `PUT` on `repos/{owner}/{repo}/rulesets/{id}` replaces the ruleset wholesale, so
read it first and send the merged object.

## CODEOWNERS

Location: `CODEOWNERS` in `.github/`, the repository root, or `docs/`. If it exists in more than
one, GitHub uses the first in that order. The file that matters is the one **on the base branch
of the pull request** — a CODEOWNERS added on the topic branch changes nothing about that PR.
Each branch has its own owners.

Owners must have explicit `write` access. A team must additionally be visible, and must have
write access even when every member already has it individually. A user or team that does not
exist, or lacks access, is dropped silently: no owner is assigned, and with code-owner review
required the PR simply cannot be satisfied.

Syntax is *most* of gitignore, and the differences fail silently:

- Negation does not work: a leading bang, as in `!src/generated/**`, is not honoured. There is no
  "exclude" — the way to remove ownership from a subtree is a line with a pattern and **no
  owner** after it.
- `[ ]` character ranges do not work, so `[Dd]ocs/` never matches. Paths are case sensitive
  regardless of the local filesystem.
- Escaping a leading `#` with `\` does not work; such a line is a comment.
- **The last matching pattern wins** — not the most specific one. A general `/src/**` placed
  after `/src/ui/` takes ownership back from the UI owners. Order general to specific.
- Co-owners of one pattern must be on **one line**. The same pattern repeated on two lines keeps
  only the last owner and silently drops the first.
- Any line with invalid syntax is skipped, and the rest of the file still applies. Check with
  `gh api repos/{owner}/{repo}/codeowners/errors`, and note the errors are also highlighted when
  viewing the file on GitHub.
- Size limit 3 MB; over that the whole file is ignored.

```text
# general first
*                      @acme/platform
/src/**                @acme/platform

# no owner: this subtree needs no code-owner approval
/src/**/generated/

# specific last, co-owners on one line
/src/ui/**             @acme/web @jsmith
/.github/workflows/    @acme/release-eng

# own the ownership file, or anyone with write can rewrite the gate
/.github/CODEOWNERS    @acme/platform
```

Owners on one line are an OR: any one of them approving satisfies the requirement. Code owners
are not requested on draft pull requests; marking the PR ready notifies them.

Because `.github/workflows/` is executable configuration, giving it a code owner is a real
control: a workflow change then needs a designated reviewer.

## Dependabot

One file, `.github/dependabot.yml`, on the default branch. GitHub reads no other location, and
there is no per-directory config.

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directories: ["/", "/.github/actions/*"]
    schedule: { interval: "weekly" }
    groups:
      actions: { patterns: ["*"] }

  - package-ecosystem: "npm"
    directories: ["/", "/apps/*", "/packages/*"]
    schedule: { interval: "weekly" }
    labels: ["dependencies"]
    groups:
      dev-deps:
        dependency-type: "development"
        patterns: ["*"]
```

- `directory` (singular) takes no glob; `directories` (plural) does. The wrong one validates and
  monitors nothing.
- Ecosystem values are exact strings: `npm` covers pnpm and yarn, `pip` covers pipenv and poetry
  (prefer `uv` when there is a `uv.lock`), plus `github-actions`, `docker`,
  `docker-compose`, `gomod`, `bundler`, `cargo`, `composer`, `nuget`, `dotnet-sdk`, `maven`,
  `gradle`, `terraform`, `helm`, `mix`, `swift`, `pub`, `bun`, `devcontainers`, `gitsubmodule`,
  `pre-commit`.
- Group updates, or the weekly PR count is what makes teams switch Dependabot off. Grouping also
  cuts CI minutes, since one PR runs the suite once.
- Alerts and security updates are repository settings, not config file entries; version updates
  are the part this file controls.

## Secret scanning and push protection

Alerts tell you a secret already leaked; push protection stops the push that would leak it, which
is the only one of the two that prevents the incident. Both are repository or organisation
settings.

When push protection blocks a push, the fix is to remove the secret from the *commit*, not to add
a new commit on top — the blocked content is still in the history being pushed. Bypassing
requires a reason and is audited; delegated bypass routes the request to a reviewer instead of
letting the pusher self-approve.

A secret that reached the remote is compromised. Rotate it; deleting the commit does not.

Rulesets can additionally require that secret-scanning alerts are resolved before a pull request
merges, and can require code-scanning results — that is where these features become gates rather
than dashboards.

## Actions policies

Repository- and organisation-level Actions settings that no amount of workflow review replaces:

- Default `GITHUB_TOKEN` permissions: set to read-only, so a workflow with no `permissions:`
  block inherits something harmless.
- "Allow GitHub Actions to create and approve pull requests": off unless a bot needs it.
  Otherwise a compromised workflow can open and approve its own PR.
- Required SHA pinning: the policy that makes unpinned third-party actions fail, rather than
  something a reviewer has to catch.
- Allowed actions: restrict to actions created by GitHub plus a verified-creator or explicit
  allow list.
- Workflow execution protections: restrict which events and actors can trigger workflows. If the
  repository has no legitimate use for `pull_request_target`, disabling the event removes the
  entire pwn-request class regardless of how workflows are written.

## Environments and deployment approvals

An environment (`environment: production` on a job) carries required reviewers, a wait timer,
branch/tag restrictions and environment-scoped secrets. The job pauses until a reviewer
approves, and the secrets are only issued after that — which is how a long-lived credential that
cannot be replaced by OIDC is still protected.

Restrict deployment branches so a fork PR or a topic branch cannot target the production
environment, and keep production credentials only in the production environment rather than at
repository level.

## Applying changes safely

1. Audit, then show a plan as a table of create / update / skip.
2. Get explicit confirmation for rulesets, protection changes, branch deletion and anything
   organisation-level.
3. Apply in an order that cannot lock you out: CODEOWNERS and workflows before the rules that
   require them.
4. Make every step idempotent — re-read, then create or update — so a re-run reconciles drift
   instead of duplicating labels and rulesets.
5. Re-query afterwards and print applied / skipped / failed, including
   `gh api repos/{owner}/{repo}/codeowners/errors` for a CODEOWNERS change and a `rulesets` read
   for a rule change.

<!-- sources: awesome-copilot, github-docs, getsentry-skills, gh-cli, secure-repo -->
