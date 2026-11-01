# tmplkit - security response plan (draft, Jonas)

Repository: `acme/tmplkit` (public, ~40k weekly downloads). Default branch `main`, required
status checks `ci / test` and two approving reviews.

## A. Private vulnerability report GHSA-7q2m-x854-vx26

Filed yesterday through private vulnerability reporting (state on the advisory page: `triage`).
The reporter shows that `tmplkit render --template` evaluates `{{ shell }}` blocks from untrusted
template files, i.e. remote code execution for anyone rendering a downloaded template. We have
confirmed it. Plan:

1. Create branch `fix-template-shell-eval`, push it to `origin` and open a normal PR, so that our
   CI (`ci / test`) runs and Maria and Tom can review it the usual way.
2. Publish the advisory today so that a CVE gets assigned and users are warned early; we will
   merge the PR and cut 4.8.1 as soon as CI is green.
3. Mention the fix in the 4.8.1 release notes with a link to the reporter's proof of concept.

## B. Workflow pinning (follow-up to the action-tag hijack incident in October)

All our workflows use tags (`actions/checkout@v6`, `pnpm/action-setup@v5`,
`softprops/action-gh-release@v3`, ...). We also have a local composite action
`./.github/actions/setup` (uses `actions/setup-node@v6` and `pnpm/action-setup@v5`) and call a
shared reusable workflow `acme/ci-shared/.github/workflows/publish.yml@v3`.

Plan: rewrite every `uses:` in `.github/workflows/*.yml` and in `.github/actions/setup/action.yml`
to a 40-character SHA by hand, with the version in a comment, and turn on the organisation
policy "Require actions to be pinned to a full-length commit SHA".

Someone suggested GitHub's new workflow lockfile instead. I looked at it: it is a public preview,
so not something for production, and anyway a commit SHA in the workflow file is the only
immutable way to reference an action, so a lockfile cannot add anything. Our org allowlist
("allow select actions") lists entries like `actions/checkout@v6` and `pnpm/action-setup@v5`;
that stays as it is.
