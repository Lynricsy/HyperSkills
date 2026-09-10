# Releases and tags

## Contents

- [Tags are the source of truth, Releases are a layer](#tags-are-the-source-of-truth-releases-are-a-layer)
- [Finding the previous version](#finding-the-previous-version)
- [Deciding the new version](#deciding-the-new-version)
- [Writing the notes](#writing-the-notes)
- [Publishing](#publishing)
- [Immutable releases and attestations](#immutable-releases-and-attestations)
- [Releasing from a workflow](#releasing-from-a-workflow)
- [Pre-releases and latest](#pre-releases-and-latest)

## Tags are the source of truth, Releases are a layer

A GitHub Release is an optional object attached to a git tag. Plenty of projects tag versions and
never create Releases, so `gh release list` can come back empty on a repository with a decade of
tags. Read tags, not releases, when you need the previous version. [official]

## Finding the previous version

```bash
git fetch --tags
PREV_TAG=$(git tag --sort=-version:refname \
  | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+' | head -1)
PREV_SHA=$(git rev-list -n 1 "$PREV_TAG")
git ls-remote --tags origin "refs/tags/$PREV_TAG"     # is it actually pushed?
```

`--sort=-version:refname` is the point: alphabetical sorting puts `1.9.0` above `1.10.0`, so a
plain `git tag | head -1` picks the wrong baseline on any project that has reached a two-digit
minor.

Two edge cases with different answers:

- No tags at all: baseline is the first commit (`git rev-list --max-parents=0 HEAD`) and the
  first version is whatever the project declares — commonly `0.1.0` or `1.0.0`. Ask.
- The tag exists locally but not on the remote: the published history is not what it looks like.
  Say so before doing anything else; a release cut on that assumption will collide.

Preserve the tag's exact form (`v1.4.2` vs `1.4.2`) when naming things, and strip the `v` only
for arithmetic.

## Deciding the new version

The diff is the primary signal and commit messages are supporting evidence, in that order —
messages describe intent, and intent is frequently wrong about whether a change is breaking.

```bash
git diff "$PREV_SHA"..HEAD -- <public-source-paths> \
  ':(exclude)tests/' ':(exclude)docs/' ':(exclude)*.lock' ':(exclude)*-lock.json'
git log "$PREV_SHA"..HEAD --oneline
```

Look at the public surface only: exported symbols, HTTP routes and payloads, CLI flags, config
keys, database schema, file formats. A removed or renamed public symbol, a changed default, a
narrowed accepted input and a new required config key are all breaking regardless of how the
commit was labelled.

Confirm the number with the user before writing anything. Everything up to this point is
read-only; a wrong version number is expensive to undo once a tag is pushed, and impossible with
immutable releases.

## Writing the notes

Group by what a consumer needs to act on: breaking changes first with the migration step for
each, then added, changed, fixed, and finally anything security-relevant with its advisory
reference. Name the user-visible effect, not the internal refactor that produced it. Omit
dependency bumps that change nothing observable, and omit internal churn entirely.

`--generate-notes` produces a commit- and PR-derived list. It is a starting point and a decent
"full changelog" appendix, but it cannot tell a consumer what broke; write the breaking-change
section by hand.

## Publishing

```bash
gh release create v1.5.0 --draft \
  --title 'v1.5.0' \
  --notes-file /tmp/notes.md \
  --target "$(git rev-parse HEAD)"

gh release upload v1.5.0 dist/*.tar.gz dist/*.sha256
gh release edit v1.5.0 --draft=false
```

Draft first, attach every asset, then publish. With immutable releases enabled the assets and
the tag lock the moment you publish, so publishing before the artifacts are ready forces a
delete-and-recreate — and the tag name cannot be reused. [official]

`--target` accepts a branch or a commit SHA and creates the tag if it does not exist; pass a SHA
to avoid a race where the branch moves between the decision and the release. `--generate-notes`
replaces `--notes-file` when you want the derived list; `--latest`/`--latest=false` overrides
which release GitHub marks as latest.

## Immutable releases and attestations

When immutable releases are enabled for the repository or organisation:

- the tag is locked to its commit and cannot be moved or deleted while the release exists;
- release assets cannot be modified or deleted;
- title, notes, pre-release flag and latest flag remain editable — only the tag and assets lock;
- deleting the release frees the tag for deletion but the **name can never be reused**, including
  after deleting and recreating the repository, which is what defeats resurrection attacks;
- publishing generates a release attestation over the tag, commit SHA and assets, which
  consumers can verify to confirm the artifact they downloaded is the one that was published.

Build provenance for artifacts produced in a workflow is a separate mechanism
(`actions/attest-build-provenance`, requiring `attestations: write` and `id-token: write`); it
attests how the artifact was built, whereas the release attestation attests what was published.

## Releasing from a workflow

```yaml
on:
  push:
    tags: ["v*.*.*"]

permissions:
  contents: write        # required to create the release
  attestations: write    # only if attesting build provenance
  id-token: write        # only if attesting, or authenticating by OIDC

jobs:
  release:
    runs-on: ubuntu-latest
    environment: release     # required reviewers + release-scoped secrets
    steps:
      - uses: actions/checkout@<sha>
      - run: make dist
      - uses: actions/attest-build-provenance@<sha>
        with: { subject-path: 'dist/*' }
      - env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          TAG: ${{ github.ref_name }}
        run: gh release create "$TAG" --generate-notes dist/*
```

Points that bite:

- `github.ref_name` is the tag on a tag push; do not re-derive it from the branch.
- A release created by `GITHUB_TOKEN` does not trigger other workflows, by design, so a
  `release: published` workflow will not fire. Use a GitHub App token when a downstream workflow
  must run.
- Registry publishing (npm, PyPI, crates.io, container registries) should use that registry's
  trusted-publishing or OIDC flow rather than a long-lived token in secrets. What each registry
  expects belongs to its own documentation.
- Gate the job with an environment so the publishing credential is only issued after approval.

## Pre-releases and latest

Mark a pre-release with `--prerelease`; it is excluded from "latest" and from the default
`gh release view` target, which is what makes release-candidate tags safe to publish. A
pre-release still creates a real tag, so version it distinguishably (`v1.5.0-rc.1`) — with
immutable releases the name is spent either way.

<!-- sources: awesome-copilot, github-docs, gh-cli -->
