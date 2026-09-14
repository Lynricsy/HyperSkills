---
name: frontend-design
description: "Designs and audits web interfaces for visual quality, usability and accessibility."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.15"
  category: task
---

# Frontend Design

Paths below are relative to this skill's directory.

## Scope

Covered, for any framework or none:

- Visual direction: palette, type, layout, spacing, elevation, motion, and the taste calls that decide them.
- Recognizing and removing the traits that make an interface read as machine-generated.
- Reviewing existing UI code against interface guidelines: accessibility, focus, forms, content handling, images, animation, performance, navigation state, touch, dark mode, locale, copy.
- Modern CSS and HTML platform features, their Baseline support level, and fallback policy.
- Core Web Vitals as a design constraint.

Not covered, and do not improvise here:

- React, Next.js, Vue, Svelte or Astro APIs, hooks, rendering models and bundling. Those are the `react`, `vue`, `svelte` and `astro` skills.
- Native mobile UI (UIKit, SwiftUI, Jetpack Compose, React Native). Platform target sizes and idioms differ; the `apple` skill covers Apple platforms, `android` and `react-native` cover theirs.
- Print, poster and canvas design, and brand identity systems.
- Backend, data modelling, and query performance.
- Search engine optimization: crawling, indexing, sitemaps, canonical URLs, structured data and search metadata. Those are content and crawler concerns rather than interface quality.

## Core rules

- State a one-line design read (kind, audience, visual language) before writing markup. The audience picks the aesthetic, not your taste.
- Set the three dials (variance, motion, density) from that read, then judge every layout and motion choice against them. Unstated dials drift toward the same page every time.
- Run the plan past the five generated-design clusters before building. Those traits are legitimate for some briefs but they are defaults rather than choices, and they show up whatever the subject.
- Where the brief pins a direction, the brief wins, including when it asks for one of those clusters. Only free axes get calibrated.
- One accent color and one neutral temperature per project. A second accent reads as a decision nobody made.
- One radius scale, concentric when nested (outer radius = inner radius + padding). A single radius on every element erases hierarchy.
- One layout family per section, reused at most once per page, and never three consecutive image-and-text splits. Eight sections need at least four distinct families.
- Small uppercase tracked labels above headings stay within `ceil(sections / 3)`, hero included. One above every section is the most reliable template signature there is.
- Past about five items, a bulleted list or a row-per-item divider stack is the wrong component rather than a long one. Tidying the hairlines does not fix a ten-row spec table.
- One theme for the whole page. Sections do not invert; tints within the same family are how a page varies.
- Semantic tokens in components (`--surface`, `--text-muted`, `--accent`), never raw hex. Raw values make dark mode and rebrands impossible.
- Design light and dark together and re-check contrast in both. An inverted palette is not a dark theme.
- Text contrast at least 4.5:1, large text 3:1, non-text UI and state indicators 3:1 `[official]` (WCAG 2.2 SC 1.4.3, 1.4.11).
- Pointer targets at least 24x24 CSS px unless a documented SC 2.5.8 exception applies `[official]`. 44x44 is SC 2.5.5 (AAA) and platform guidance, not the AA floor.
- Every interactive element keeps a visible `:focus-visible` indicator. `outline: none` without a replacement makes the page unusable by keyboard.
- One or two type families, measure under about 80 characters, and no reflex defaults (Inter as the sans, Fraunces or Instrument Serif as the display face). Give one sentence of reason per family.
- Ask whether a thing should animate before asking how. Anything a person triggers dozens of times a day, and anything keyboard-initiated, should not animate.
- Animate `transform` and `opacity` only, and list properties explicitly. `transition: all` animates layout properties and drops frames.
- Give every animation beyond hover and active a `prefers-reduced-motion` variant: fewer and gentler, not zero.
- Declare `width` and `height` (or `aspect-ratio`) on images, video and embeds. Missing intrinsic size is the most common source of layout shift.
- Zero em dash (U+2014) and en dash (U+2013) in visible copy. The spaced dash label is the most reliable text tell, and a hyphen, comma, colon or line break always replaces it.
- Use real content: plausible names, organic numbers, a real product name. Placeholder copy hides the wrapping and overflow problems real content exposes.
- Format dates, numbers and currency with `Intl.DateTimeFormat` and `Intl.NumberFormat`, never a hardcoded pattern.
- Check Baseline before using a platform feature instead of asserting support from memory: `npx -y modern-web-guidance@latest search "<goal>"`.
- Spend boldness in one place. Let one element be the memorable thing and cut decoration that does not serve the brief.

## Workflows

### design-direction

Use when the deliverable is a look, not a fix.

- [ ] Name the subject, the audience and the page's primary job. If the brief does not say, propose one concrete answer and confirm it.
- [ ] State the design read in one line: `Reading this as: <kind> for <audience>, with a <vibe> language, leaning toward <aesthetic family>.`
- [ ] Set the dials. Tooling surfaces (devtools, dashboards, app shells) start at variance 2-3, motion 2-3, density 7-9. Marketing surfaces (landing, portfolio, product) start at variance 7-8, motion 5-7, density 3-4. Override only from the read.
- [ ] Write the design plan, four parts: **Color** as 4-6 named hex values with a role each; **Type** as one or two families with roles and a reason; **Layout** as a one-sentence concept plus an ASCII wireframe plus stated alignment; **Principles** as what makes this page specific to this brief.
- [ ] Cliché gate. Re-read the plan against `references/ai-tells-and-calibration.md`. For each trait that matches a cluster, either revise it or justify it from the brief, and say what changed. Ask whether a similar prompt would have produced the same plan; if yes, the plan is a default.
- [ ] Build to the revised plan. Watch CSS specificity: a type-based selector (`.section`) and an element-based one cancel each other out, which usually shows up as missing space between sections.
- [ ] Self-critique. Remove one accessory. Confirm the quality floor: reflows at 320 CSS px, visible focus, reduced motion honored, contrast met, real content in place.

Gate: the plan lists 4-6 hex values, contains at least one ASCII wireframe, and contains a paragraph naming what the cliché gate changed. No component code before that gate passes.

### review-ui

Use when UI code already exists.

- [ ] Fix the file set and read each file end to end. Guessing from names produces wrong line numbers.
- [ ] Walk `references/review-checklist.md` category by category. Do not stop after accessibility; the later categories (content handling, locale, touch) are where most real defects hide.
- [ ] Count before judging: eyebrow labels against `ceil(sections / 3)`, layout families against the section count, grid cells against items, and runs of consecutive same-split sections. These are the findings a read-through misses, because each section looks fine on its own.
- [ ] Walk `references/ai-tells-and-calibration.md` as a separate axis. No linter sees this one, so it is the axis worth your attention.
- [ ] Skip what the project's own tooling already enforces (formatter, `eslint-plugin-jsx-a11y`, stylelint). Say once that it was skipped.
- [ ] Write each finding as `path:line - problem` plus the concrete replacement. A finding without a replacement is not actionable.
- [ ] Keep replacements to shape, never to fact. Flagging invented precision and then supplying a measurement protocol, a full name and employer, or a delivery date is the same defect rewritten. Give the form and name the input the project has to supply.
- [ ] Order findings by impact within each file: broken for keyboard or assistive tech, then broken on small screens, then visual-tell, then polish.
- [ ] Give a file with no findings a `✓ pass` line so the reader knows it was checked.

Gate: every finding carries a `path:line` and a replacement, every reviewed file appears in the output, the output opens with the first file heading rather than a summary, and no replacement asserts a fact that could only come from the project.

### modernize-css

Use when picking or replacing a CSS or HTML platform feature.

- [ ] Phrase the goal as an action, for example "change layout based on the component's own width" rather than "use container queries".
- [ ] `npx -y modern-web-guidance@latest search "<goal>"` and read the returned ids, categories and similarity scores.
- [ ] `npx -y modern-web-guidance@latest retrieve "<id>"` for the best match. Multiple ids can be passed comma-separated. If the output is truncated, redirect it to a file and read the file.
- [ ] Apply the fallback policy: Baseline Widely available features are used directly; features that are not Widely available ship the fallback the guide prescribes.
- [ ] If the project states a browser-support policy (in `AGENTS.md` or similar), use the guide's compatibility data to decide whether the fallback can be dropped. If no policy exists and you had to assume one, say so and propose one line for the project to adopt.
- [ ] Do not adopt a feature the goal did not ask for. The guides describe options, not requirements.

Gate: every modern feature introduced is either Baseline Widely available or ships the guide's fallback, and the change description cites the retrieved guide id.

### redesign-ui

Use when a UI already exists and the deliverable is a new look rather than a list of defects.

- [ ] Classify the mode first: **preserve** (modernize without breaking the brand) or **overhaul** (new visual language over existing content and information architecture). If the brief does not settle it, ask exactly once.
- [ ] Audit in writing before proposing anything: existing brand tokens (accent, neutrals, type stack, radii, logo treatment), the page tree and primary conversion paths, which content blocks carry load and which are filler, and the dial reading of the site as it stands. That reading is the starting point, not the baseline for its kind.
- [ ] State what will not change without explicit approval: URL and slug structure, anchor ids, primary navigation labels, form field names and their order, the logo, and legal or consent copy. Renaming a field or a section id breaks analytics and autofill silently.
- [ ] Extract the brand accent before applying any palette rule. A brand that is already purple stays purple; the reflex-accent tell is about unbriefed choices, not about existing brand equity.
- [ ] Apply the levers in order of visual lift per unit of risk and stop when the brief is satisfied: type, then spacing and rhythm, then color recalibration that keeps the brand accent, then a motion layer, then recomposition of the hero and key sections, then block replacement. Full replacement is the last lever rather than the opening move.
- [ ] Keep every accessibility behavior that already works: focus visibility, alt text, keyboard paths, contrast. A redesign that regresses these has failed whatever it looks like.

Gate: the mode is named, the audit exists in writing, the do-not-change list is stated, and the proposed work is ordered by lever rather than by section.

## Topic router

| Topic | Read when | File |
|---|---|---|
| Generated-look calibration | Starting any design plan, or auditing why a UI feels templated | `references/ai-tells-and-calibration.md` |
| Type families, scale, measure | Choosing or fixing typography | `references/typography.md` |
| Palette, tokens, dark mode | Choosing colors, or a theme has drifted | `references/color-and-tokens.md` |
| Layout, density, elevation, motion values | Composing a page, or tuning spacing, shadows, easing and duration | `references/layout-density-motion.md` |
| Interface copy | Writing labels, buttons, errors, empty states | `references/ux-writing.md` |
| WCAG criteria and numbers | Any accessibility claim, target size, contrast, focus question | `references/accessibility.md` |
| Forms and inputs | Building or reviewing any form | `references/forms-and-inputs.md` |
| Core Web Vitals and asset cost | The UI is slow, janky, or shifts while loading | `references/performance-core-web-vitals.md` |
| Modern CSS and HTML features | Reaching for a newer platform feature, or negotiating fallbacks | `references/modern-css-platform.md` |
| Full review checklist | Running `review-ui` | `references/review-checklist.md` |
| Extra UX judgement calls | Reviewing overflow, disabled states, error summaries, charts | `references/ux-guidelines-catalog.md` |

## Output format

`review-ui` output. Use exactly this shape: group by file, one finding per line, no preamble and no closing summary.

```text
## src/Button.tsx

src/Button.tsx:42 - icon-only button has no accessible name; add aria-label="Close"
src/Button.tsx:55 - `outline: none` on :focus with no replacement; use :focus-visible with a 2px ring at 3:1 contrast
src/Button.tsx:67 - `transition: all .3s`; list `transform, opacity`
src/Button.tsx:71 - entrance animation has no reduced variant; wrap in @media (prefers-reduced-motion: reduce)

## src/Hero.tsx

src/Hero.tsx:18 - `<img>` has no width/height; declare intrinsic size or aspect-ratio to stop layout shift
src/Hero.tsx:24 - tracked ALL-CAPS eyebrow above the heading is template chrome; drop it or make it a real category link
src/Hero.tsx:31 - "Ship faster — effortlessly" uses an em dash in visible copy; rewrite as "Ship faster, effortlessly"

## src/Card.tsx

✓ pass
```

State the issue and its location. Skip the explanation when the fix is obvious from the replacement.

`design-direction` output. Sensible default, adapt to the brief: the design read line, then the four
plan parts, then the cliché-gate paragraph. The wireframe stays ASCII so it survives in any
transcript. A worked shape, for a brief about a workshop that hand-brazes steel touring frames.
Copy the shape, never the contents: this palette, this type pairing and this section order are
themselves a default now, so a plan that arrives at them for the same brief has skipped the gate.

```text
Reading this as: a portfolio-shaped product page for buyers who need proof of craft,
with a workshop-document language, leaning toward drawing-office typography.

Color   #E9EAE6 drafting paper / #17191A ink text / #565C59 muted / #78858B hairline rules /
        #2B5566 blueprint accent, single CTA only
Type    Display: a compressed grotesque with drawing-office roots (reason: the subject's own
        documents are engineering drawings, not editorial pages).
        Body: the same family at 400. Numbers: a mono face with tabular figures, because the
        geometry table is itself the proof.
Layout  Left-aligned throughout on an exposed 12-column grid, hairline rules as the only divider,
        spec notes set in the outer margin.

        +------------------------------------------------------+
        | wordmark                                nav   nav    |
        +----------------------------+-------------------------+
        | one-sentence claim         |  macro photo of a       |
        | 2 lines, 42ch measure      |  brazed lug, full bleed |
        | [ Book a fitting ]         |  to the right edge      |
        +----------------------------+-------------------------+
        | geometry table, mono, tabular figures                |
        +------------------------------------------------------+

Principles  Evidence over atmosphere. One accent, used once. No card containers.

Cliché gate  The first pass had a #F4F1EA ground with a high-contrast serif display and a
             terracotta accent, which is cluster 1 almost exactly. The second pass moved the
             accent to brass over an oxide CTA, which is its own default: beige plus brass plus
             oxblood is what every premium-consumer brief gets. Third pass keeps the cooler
             paper ground and the grotesque, and takes the accent to a blueprint blue drawn from
             the subject's own drawings, with no second accent behind it. The centered hero
             became a left-aligned split, since variance sits at 6 here.
```

## Environment

- `modern-web-guidance` runs through `npx` and needs outbound network access; nothing is installed into the project. Where `~/.npm` is read-only, set `NPM_CONFIG_CACHE=/tmp/npm-cache`. Prefer `pnpx modern-web-guidance@latest ...` when `pnpm` is present (no `-y` flag there). Request network approval before the first call in gated environments.
- Automated accessibility checks catch a subset only: `axe-core` 4.8+ implements the WCAG 2.2 `target-size` rule; Lighthouse's tap-target audit still uses an older heuristic and is not a SC 2.5.8 verdict.
- Contrast, focus order and reduced-motion behavior need a real render. Where a browser is available, check both themes and at 320 CSS px width.
