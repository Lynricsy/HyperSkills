# READMEs

## Contents

- [What a README is for](#what-a-readme-is-for)
- [Where it lives](#where-it-lives)
- [The minimum content set](#the-minimum-content-set)
- [Order](#order)
- [What does not belong](#what-does-not-belong)
- [The quick start](#the-quick-start)
- [One home per fact](#one-home-per-fact)
- [Package READMEs inside a monorepo](#package-readmes-inside-a-monorepo)
- [Badges](#badges)
- [Review checklist](#review-checklist)

## What a README is for

A README orients a reader who has just arrived at a directory and does not yet
know whether this code is what they want. It answers: what is this, is it alive,
can I use it, and where do I go next. Everything else on the page is competing
with those four answers.

It is not the documentation. In most repositories it became the documentation
because it is the only file people see, and the result is a mixed page: install
steps interrupted by a design discussion, an options table, and a tutorial.
Fixing that is moving material out, not reorganising it in place.

## Where it lives

The README sits at the top level of the code it describes — not inside the
documentation directory. `docs/README.md` is a file nobody browsing the code
will see, and forges render `README.md` at the directory root. [official]

Every top-level directory of a shipped package should have one. This matters
most for directories that other teams consume: they are the ones whose readers
have no other context. [official]

## The minimum content set

A package-level README must contain, or point to, all of these. The first three
cannot be delegated to another file, because a reader who does not know the
answers will not go looking. [official]

1. **What this is and what it is for**, in one paragraph, in the reader's
   vocabulary rather than the implementation's.
2. **Status**, when it is anything other than "supported": deprecated, not for
   general release, pre-1.0, or maintained but not developed. A deprecated
   package whose README does not say so costs its next reader a day.
3. **Who owns it** — a team, a channel, an issue tracker. "Points of contact"
   is what turns an abandoned-looking repository into a usable one.
4. **How to use it**: install, and a quick start that runs.
5. **Links onward**: the docs site or `docs/` directory, the changelog, the
   contributing guide, the licence.

Items 4 and 5 may be one line each pointing elsewhere. Items 1–3 belong on the
page.

## Order

Readers stop early, so the order is a ranking, not a template:

```
# name
one-paragraph what-and-why
status banner, if not plainly supported
install
quick start that runs
a short table of contents or links onward
```

Anything below the links onward is read by almost nobody; put nothing there
that a reader needs.

## What does not belong

- **Reference tables.** Options, flags, environment variables, error codes.
  They belong in reference, where they can be complete and uniform. A partial
  copy in the README is the copy that goes stale, and the one people find
  first.
- **Tutorials.** "Let's build a scraper" is a lesson; it needs its own page and
  its own prerequisites.
- **Design discussion.** Why the architecture is the way it is belongs in
  explanation or an ADR.
- **The full contributing process and the licence text.** Those have their own
  files; link them. Do link them: a reader who cannot find the licence assumes
  there is not one.

## The quick start

A quick start is a promise that these commands work on a clean machine, in
order, with nothing else known. It is the most-copied text in the repository
and the most reliably wrong.

- Install the dependency set the quick start actually needs, including extras.
  A quick start that uses an optional backend and installs only the base
  package fails on the reader's first run and on nobody's CI.
- Declare credentials and environment variables before the first block, with
  the real variable names read by the code.
- Declare services the reader must have running.
- Show the output, or the one observable thing that proves it worked.
- Keep it to one path. A quick start with a choice in it is a how-to guide.

Verify it the only way that counts: run it, in a clean environment, in the
order the page gives.

## One home per fact

Install instructions in two places drift within one release: the second copy is
edited, the first is not, and readers hit whichever they scrolled to. This is
the single most common README defect after the mixed page. When you find a fact
twice, delete one copy — do not reconcile both.

The same applies across files. If `docs/reference.md` lists the options, the
README does not list a subset of them "for convenience". If it must show one,
say in one line that reference is authoritative, and keep the README's copy to
the two or three options a first run needs.

## Package READMEs inside a monorepo

Each published package gets its own README, because that is what the package
registry renders. The root README describes the repository and links the
packages; it does not try to be the union of them. A package README that
documents the whole monorepo is the wrong page for the only reader who will
ever see it: someone who just installed that one package.

## Badges

Badges are for facts a reader needs before reading: build state, released
version, licence. A wall of them pushes the first paragraph below the fold, and
a badge pointing at a dead service says the project is unmaintained more loudly
than anything in the prose. Check each one resolves, or remove it.

## Review checklist

- [ ] The first paragraph says what this is without naming the implementation.
- [ ] Status is stated whenever it is not plainly supported, and an owner or
      channel is named.
- [ ] Install appears exactly once.
- [ ] Every command was run, in order, as written, on a checkout with nothing
      else installed.
- [ ] Every symbol, keyword argument, method name, exception name and
      environment variable in the examples exists in the current source.
- [ ] Every referenced path and link resolves, including the ones pointing into
      `docs/`.
- [ ] No option, flag or environment-variable table that reference also has.
- [ ] No tutorial and no design discussion.
- [ ] Nothing a reader needs sits below the links onward.

<!-- sources: google-styleguide, mblode-docs-writing, copilot-docs, addyosmani-skills -->
