# Smell baseline and structural remedies

Read when collecting Standards findings.

## Contents

- [How to use the baseline](#how-to-use-the-baseline)
- [The twelve smells](#the-twelve-smells)
- [Structural remedies](#structural-remedies)
- [Change sizing and splitting](#change-sizing-and-splitting)
- [Dead code and dependencies](#dead-code-and-dependencies)
- [Rationalizations](#rationalizations)

## How to use the baseline

The Standards axis is whatever the repo documents, plus this baseline for everything it does
not. Three rules bind it:

- **The repo overrides.** A documented standard always wins. Where the repo endorses something
  the baseline would flag, the smell is suppressed — do not relitigate house style.
- **Every smell is a judgement call.** Report it as one ("possible Feature Envy here"), never as
  a violation. The documented rules are where hard violations come from.
- **Skip what tooling enforces.** Formatting, import order, lint rules and type errors are the
  formatter's and the compiler's findings, not yours. Spending review attention there is how
  real problems get buried.

The smells are matched against the diff, not against the whole file. A pre-existing smell the
change merely touched is context, not a finding; say so if it matters, as a Recommendation.

## The twelve smells

Each reads *what it is* → *how to fix it*.

1. **Mysterious name** — a function, variable or type whose name does not say what it does or
   holds. → Rename it. If no honest name presents itself, the design is unclear and that is the
   real finding.
2. **Duplicated code** — the same logic shape in two hunks or two files of this change. →
   Extract the shape once and call it from both sites.
3. **Feature envy** — a method that reaches into another object's data more than its own. →
   Move the method to the data it envies.
4. **Data clumps** — the same few fields or parameters keep travelling together. → They are a
   type waiting to be born; bundle them and pass the one thing.
5. **Primitive obsession** — a string or number standing in for a domain concept with its own
   rules. → Give the concept a small type so the rules have somewhere to live.
6. **Repeated switches** — the same `switch` or `if` cascade over the same type appears in
   several places in the change. → Replace with polymorphism, or one lookup both sites share.
7. **Shotgun surgery** — one logical change forces scattered edits across many files. → Gather
   what changes together into one module.
8. **Divergent change** — one module is edited in this diff for several unrelated reasons. →
   Split it so each module changes for one reason.
9. **Speculative generality** — abstraction, parameters or hooks added for needs the spec does
   not have. → Delete it and inline back until a real need appears.
10. **Message chains** — long `a.b().c().d()` navigation that couples the caller to a structure
    it should not know. → Hide the walk behind one method on the first object.
11. **Middle man** — a class or function that mostly delegates onward. → Remove it and call the
    real target.
12. **Refused bequest** — a subclass or implementer that ignores or overrides most of what it
    inherits. → Drop the inheritance and compose instead.

Four additions that catch what the classic list misses in agent-written code:

13. **Bolted-on conditional** — a new branch welded onto a flow that has nothing to do with it.
    A "temporary" branch is permanent debt. → Push the decision into its own helper, state or
    policy object.
14. **Relocated complexity** — a refactor that moves code without reducing the number of
    concepts a reader must hold at once. → Prefer the restructuring where a branch, mode or
    layer disappears; deleting an abstraction beats polishing one.
15. **Leaked feature logic** — feature-specific behaviour added to a shared or general-purpose
    module, or a bespoke near-duplicate of an existing canonical helper. → Keep logic in the
    layer that owns the concept and reuse the canonical helper.
16. **Papered-over boundary** — gratuitous `any`, `unknown`, optionality, casts, or a silent
    fallback that hides an unclear invariant. → Make the boundary explicit; the surrounding
    control flow usually simplifies as a result.

## Structural remedies

When you flag a structural problem, name the move. A review that says only "this is complex"
leaves the author guessing, and guessing produces another round.

- Replace a chain of conditionals with a typed model or an explicit dispatcher.
- Collapse duplicate branches into one clearer flow.
- Separate orchestration from business logic so each reads on its own.
- Move feature-specific logic out of the shared module into the package that owns the concept.
- Reuse the canonical helper instead of a near-duplicate.
- Make a type boundary explicit so downstream branching disappears.
- Delete a pass-through wrapper that adds indirection without clarifying the API.
- Extract a helper, or split an oversized file into focused modules.

Prefer the remedy that removes moving pieces over the one that spreads the same complexity
around.

## Change sizing and splitting

| Changed lines | Verdict |
|---|---|
| ~100 | Good. Reviewable in one sitting. |
| ~300 | Acceptable if it is one logical change. |
| ~1000 | Too large. Name a split strategy instead of skim-reading it. |

Watch resulting file size too, not only diff size: a small diff can push a file past the point
where anyone can hold it, and around a thousand total lines in one file is a signal worth
raising — a signal, not a cap. When a change materially grows an already-large file, ask for the
extraction first and the addition second.

One change means one self-contained modification, with its tests, leaving the system working.
One part of a feature, not the whole feature. Refactoring and behaviour change are two changes;
a rename carried along with a feature is fine at the reviewer's discretion.

| Split strategy | How | When |
|---|---|---|
| Stack | Land a small change, base the next on it | Sequential dependencies |
| By file group | Separate changes for areas needing different reviewers | Cross-cutting work |
| Horizontal | Shared code and stubs first, consumers after | Layered architecture |
| Vertical | Smaller full-stack slices of the feature | Feature work |

Large is acceptable when the reviewer only needs to verify intent: whole-file deletions and
mechanical, tool-driven refactors.

## Dead code and dependencies

Dead code: enumerate what the change orphaned, name what replaced each item, and ask before
deleting. Silent deletion is how a still-referenced helper disappears.

```text
Now unused after this change:
- formatLegacyDate() in src/utils/date.ts — superseded by formatDate()
- LEGACY_API_URL in src/config.ts — no remaining references
Remove these in this change, or leave them for a follow-up?
```

Adding a dependency: does the existing stack already do this, how big is it, is it maintained,
does it have known advisories, and is the licence compatible? Prefer the standard library and
the helpers already in the repo; every dependency is a liability.

Upgrading a dependency is a behaviour change nobody in the diff wrote, and bulk bumps are the
riskiest changes that routinely merge unread:

1. Read the changelog, not the version number. A patch release can carry behaviour changes; for
   a major, read the migration notes and find what breaks.
2. One package per change. When a bulk bump breaks the build you have lost which package did it;
   one package keeps the cause obvious and the revert clean.
3. Let the tests decide. Green before and after, not "it installed". Thin coverage around the
   dependency's behaviour is itself the finding.
4. Review the lockfile diff, not just the manifest. One direct bump can pull dozens of
   transitive changes.
5. Commit the lockfile and never hand-edit it. It is the thing that pins what ships.

## Rationalizations

| Rationalization | Reality |
|---|---|
| "It works, that's good enough" | Working code that is unreadable, unsafe or misplaced creates debt that compounds. |
| "I wrote it, so I know it is correct" | Authors are blind to their own assumptions; that is what the review is for. |
| "We'll clean it up later" | Later does not arrive. Require the cleanup now, or a filed issue with an owner. |
| "Agent-generated code is probably fine" | It is confident and plausible even when wrong, so it needs more scrutiny, not less. |
| "The tests pass, so it is good" | Tests do not catch architecture, security or readability problems — and a test can be weakened to pass. |
| "The refactor makes it cleaner" | Relocating complexity is not reducing it. Count the concepts the reader must hold. |
| "It is only a small addition to this file" | Judge the resulting structure, not the diff size. |
| "It is just a version bump" | It is a behaviour change you did not write. |
| "One PR for all the bumps saves time" | Until it breaks and nobody knows which package did it. |

<!-- sources: mattpocock-review, addyosmani-review, mattpocock-codebase-design -->
