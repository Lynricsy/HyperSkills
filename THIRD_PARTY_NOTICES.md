# Third-party notices

HyperSkills 的所有自有内容以 MIT 许可发布（见 `LICENSE`）。
每个 skill 都是对上游材料的精编重写，下列条目记录了各 skill 的上游来源、
许可与合入时固定的 commit。本文件由 `tools/build_catalog.py` 生成，请勿手工编辑。

# NOTICE — apple

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- twostraws/SwiftUI-Agent-Skill (MIT) — https://github.com/twostraws/SwiftUI-Agent-Skill @ be297ff80dddec529af1f9b1f1f114aab6c9d11c — paths: swiftui-pro — Nine-step review order, core instructions (iOS 26 default target, Swift 6.2+, no unsolicited third-party frameworks, one type per file), the review output format with worked examples, and rules for views, data flow, navigation, design, accessibility, performance, Swift style and hygiene.
- AvdLee/SwiftUI-Agent-Skill (MIT) — https://github.com/AvdLee/SwiftUI-Agent-Skill @ 4c6a97d15aa5e023538c3cb06b5192f241dd451d — paths: skills/swiftui-expert-skill — Correctness checklist of always-a-bug invariants, the topic-router pattern, the read-first deprecated-API index, localization and scroll/focus/animation guidance, and the Instruments record-and-analyse workflow with its trace interpretation rules.
- YordiLorenzo/liquid-glass-skills (MIT) — https://github.com/YordiLorenzo/liquid-glass-skills @ a6bac94c5a7a65ac42207452e3e63bb4eb7518e8 — paths: liquid-glass, liquid-glass-motion, apple-motion-feel — Liquid Glass hard rules with per-symbol availability floors and confidence tags, the corrected availability table, the fabricated-API list, glass migration hygiene, morph preconditions, Reduce Motion gating, and Metal shader constraints.
- superagents-lab/xcode27-skills (NONE) — https://github.com/superagents-lab/xcode27-skills @ 6f9ff8d5ad6000491cb0f483a776b7062e41cd97 — paths: swiftui-specialist, swiftui-whats-new-27, uikit-app-modernization, test-modernizer — Apple-authored guidance used as the correctness oracle: view structure and invalidation boundaries, data-flow granularity, environment comparison, ForEach identity, conditional-modifier ban, soft-deprecation behaviour rules, iOS 27 SDK breakages, and UIKit scene-lifecycle modernization.
- AvdLee/Swift-Concurrency-Agent-Skill (MIT) — https://github.com/AvdLee/Swift-Concurrency-Agent-Skill @ 45fa49e4e0b2af4d43b1cb458903f8030ac993bd — paths: skills/swift-concurrency — Build-settings intake table, task entry isolation against the synchronous prefix, the smallest-safe-fix ladder, the concurrency tool-selection table, and the Swift 6 migration validation loop.
- twostraws/Swift-Concurrency-Agent-Skill (MIT) — https://github.com/twostraws/Swift-Concurrency-Agent-Skill @ bee3f69ba17142da148d3c5406f148ed62592b69 — paths: swift-concurrency-pro — Concurrency grep targets, the failure-mode catalogue (actor reentrancy, continuation misuse, swallowed errors, unbounded streams), the strict-concurrency diagnostic-to-fix mapping, and Swift 6.2 behaviour changes.
- twostraws/SwiftData-Agent-Skill (MIT) — https://github.com/twostraws/SwiftData-Agent-Skill @ 922d989473a9914210b41529a1ac5636aff4b8c1 — paths: swiftdata-pro — SwiftData model and relationship rules, temporary persistent identifiers, the predicate subset including the compile-clean patterns that crash at runtime, indexing, CloudKit constraints, and iOS 26 model inheritance.
- twostraws/Swift-Testing-Agent-Skill (MIT) — https://github.com/twostraws/Swift-Testing-Agent-Skill @ 2d6bba14a3c8bf3694f218b92fffe617c41ae43e — paths: swift-testing-pro — Swift Testing conventions (structs over classes, no redundant @Suite, init over setUp), the expectation rules including why a leading bang defeats macro expansion, parameterised-test pitfalls, withKnownIssue semantics, and the XCTest mapping table.
- AvdLee/Swift-Testing-Agent-Skill (MIT) — https://github.com/AvdLee/Swift-Testing-Agent-Skill @ 798e9b1a2bcac164d4f0c781908199e754f0bab6 — paths: swift-testing-expert — Async testing and waiting patterns, parallelization and isolation constraints, traits and tags usage, and the boundary where XCTest remains required for UI tests.
- https://developer.apple.com/documentation/ (NONE) — https://developer.apple.com/documentation/ — Correctness oracle for every version floor, API spelling, and accessibility figure in this skill, including the iOS/iPadOS release notes used to fix the default deployment target at iOS 26 with iOS 27 at RC.

Reference-only sources (no content copied):

- AvdLee/SwiftUI-Agent-Skill (MIT) — https://github.com/AvdLee/SwiftUI-Agent-Skill/tree/main/.agents/skills/update-swiftui-apis
- dadederk/iOS-Accessibility-Agent-Skill (MIT) — https://github.com/dadederk/iOS-Accessibility-Agent-Skill
- Dimillian/Skills (MIT) — https://github.com/Dimillian/Skills
- dpearson2699/swift-ios-skills (NOASSERTION) — https://github.com/dpearson2699/swift-ios-skills
- rshankras/claude-code-apple-skills (MIT) — https://github.com/rshankras/claude-code-apple-skills

---

# NOTICE — code-review

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- obra/superpowers (MIT) — https://github.com/obra/superpowers @ b36e0829c6d0140e93cfef2ca599b1b07d4a7797 — paths: skills/requesting-code-review — Base-SHA pinning and the context argument for dispatching a reviewer instead of reading the diff inline, plus the reviewer prompt template: read-only guard, the no-nested-dispatch rule and its reasoning, the Strengths / Critical / Important / Minor / Recommendations / Assessment output contract with a worked example, and the calibration rules.
- obra/superpowers (MIT) — https://github.com/obra/superpowers/tree/main/skills/receiving-code-review @ b36e0829c6d0140e93cfef2ca599b1b07d4a7797 — paths: skills/receiving-code-review — The whole responding direction: the six-step response pattern, the ban on content-free agreement, clarify-every-unclear-item-before-implementing-any, source-graded scepticism with its five verification questions, the YAGNI grep, blocking-then-simple-then-structural ordering, evidence-backed pushback, graceful self-correction, and inline-thread replies.
- obra/superpowers (MIT) — https://github.com/obra/superpowers/tree/main/skills/verification-before-completion @ b36e0829c6d0140e93cfef2ca599b1b07d4a7797 — paths: skills/verification-before-completion — The evidence-before-claim completion gate shared verbatim across this repository's engineering-practice skills, and the verify-the-verification review step: which command the author ran and what its output showed.
- mattpocock/skills (MIT) — https://github.com/mattpocock/skills/tree/main/skills/engineering/code-review @ 3cca18b368ae95cdbdebbff572ccafa662551015 — paths: skills/engineering/code-review — Fixed-point pinning with a git rev-parse fail-fast and a three-dot diff, the spec-source priority order, separate gathering of the Standards and Spec axes with the ban on cross-axis reranking, and the twelve-smell Fowler baseline together with its three meta-rules (repo standards override, every smell is a judgement call, skip what tooling enforces).
- mattpocock/skills (MIT) — https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling @ 3cca18b368ae95cdbdebbff572ccafa662551015 — paths: skills/productivity/grilling — The stop-and-ask format used when review feedback is ambiguous: ask every open question in one round, number each and attach a recommended answer, look facts up yourself and put only decisions to the user.
- addyosmani/agent-skills (MIT) — https://github.com/addyosmani/agent-skills/tree/main/skills/code-review-and-quality @ 6ca0cd7db39b41b1c37e26d335c507ee92382c6d — paths: skills/code-review-and-quality — The five quality lenses and their question lists, the severity prefix taxonomy, lead-with-what-matters, the eight structural remedies, change sizing with the four splitting strategies, review-the-tests-first, verify-the-verification, the honesty and anti-sycophancy rules, the disagreement hierarchy, dead-code hygiene, and the dependency and upgrade discipline.
- trailofbits/skills (CC-BY-SA-4.0) — https://github.com/trailofbits/skills/tree/main/plugins/differential-review/skills/differential-review @ 321ccfe628eca0d314b0ee4eaffcdd8a05639aaf — paths: plugins/differential-review/skills/differential-review — Security-mode structure only: risk-class triggers, depth chosen from codebase size, git blame on removed guards and the regression pattern, caller-counted blast radius crossed with risk, test-coverage severity elevation, the escalation trigger list, and the rule that the report is written to a file with its coverage limits stated.

Reference-only sources (no content copied):

- mattpocock/skills (MIT) — https://github.com/mattpocock/skills/tree/main/skills/engineering/codebase-design
- anthropics/claude-code (Proprietary) — https://github.com/anthropics/claude-code/tree/main/plugins/code-review

---

# NOTICE — debugging

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- mattpocock/skills (MIT) — https://github.com/mattpocock/skills @ 3cca18b368ae95cdbdebbff572ccafa662551015 — paths: skills/engineering/diagnosing-bugs, skills/productivity/grilling — Loop-first phase architecture: the ten loop constructions, the tighten-the-loop properties, the red-capable / deterministic / fast / agent-runnable completion gate, minimisation to load-bearing elements, three-to-five ranked falsifiable hypotheses shown before testing, one probe per prediction, tagged instrumentation with a grep cleanup, the performance-measure-first branch, the correct-seam rule and its absence-is-a-finding corollary, secret redaction, the cleanup checklist, and the one-round numbered question format used by When to stop and ask.
- obra/superpowers (MIT) — https://github.com/obra/superpowers @ b36e0829c6d0140e93cfef2ca599b1b07d4a7797 — paths: skills/systematic-debugging, skills/verification-before-completion — The Iron Law (no fix without a root cause), read-the-whole-error and check-recent-changes as cheap pre-steps, per-boundary instrumentation for multi-component systems, one variable per change, the three-strikes rule and the architecture question behind it, the user-redirection stop signals, backward call-chain tracing with stack-capture probes, the test-polluter bisection, layered guards after the fix, condition-based waiting instead of arbitrary delays, and the evidence-before-claim completion gate.
- addyosmani/agent-skills (MIT) — https://github.com/addyosmani/agent-skills @ 6ca0cd7db39b41b1c37e26d335c507ee92382c6d — paths: skills/debugging-and-error-recovery — Stop-the-line before triage, the four-branch non-reproducible tree (timing / environment / state / rate), the test, build and runtime failure trees, git bisect run, instrumentation keep-or-remove rules, and error output treated as untrusted data that is never executed or followed.

Reference-only sources (no content copied):

- pproenca/dot-skills (MIT) — https://github.com/pproenca/dot-skills

---

# NOTICE — flutter

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- flutter/agent-plugins (BSD-3-Clause) — https://github.com/flutter/agent-plugins @ 9b8106dbf09fcc1d0bda0010acc67914e6dab5e5 — paths: skills, rules — Task-shaped workflows and checklists, layered architecture baseline, responsive layout and layout-error decoding, widget/integration testing, declarative routing with native deep-link configuration, localization, JSON serialization and http usage.
- dart-lang/skills (BSD-3-Clause) — https://github.com/dart-lang/skills @ c530d2c728b0e6c37a4cbbe032e65b824799b37d — paths: skills — Dart 3 language surface (pattern matching, primary constructors), analyzer configuration and dart fix, runtime error triage, test mocks and coverage, ffigen and FFI asset setup.
- evanca/flutter-ai-rules (MIT) — https://github.com/evanca/flutter-ai-rules @ b75d63131c2a0423d90c7b80a0b3c45de3e41423 — paths: skills — State-management backbone (Riverpod, Bloc, Provider/ChangeNotifier), feature-first folder policy, test validity rules, mocktail and patrol usage, common Flutter error catalogue.
- sgruhier/superpowers-flutter (MIT) — https://github.com/sgruhier/superpowers-flutter @ 4c0034f267c4e79d2f5e04200c18d4adf9d347fc — paths: skills/riverpod, skills/bloc, skills/go-router, skills/auto-route, skills/flutter-widget-rules, skills/flutter-analyze, skills/flutter-clean-architecture, skills/dart — Riverpod 3 correctness (legacy provider list, provider selection table, autoDispose/family discipline), sealed state with value equality, go_router and auto_route patterns, numbered widget rules.
- Jeffallan/claude-skills (MIT) — https://github.com/Jeffallan/claude-skills @ 882ef55e377dbf9a4dbe496bb41ac6ccd0e555cf — paths: skills/flutter-expert/references/performance.md — Performance checklist seed: const widgets, selective watching, RepaintBoundary, image cache sizing, compute for heavy work, frame budget.
- Harishwarrior/flutter-claude-skills (MIT) — https://github.com/Harishwarrior/flutter-claude-skills @ 114379ad2864d024eb11369e0d28b57e55b2c066 — paths: flutter-tester/references — Layered testing patterns, Riverpod provider testing with fresh containers and dependency overrides, widget testing depth (keys, deterministic surface size, pump vs pumpAndSettle).
- https://docs.flutter.dev/platform-integration/platform-channels (CC-BY-4.0) — https://docs.flutter.dev/platform-integration/platform-channels — Platform channel architecture, standard codec type mapping, threading and background-isolate rules, Pigeon workflow; and the current internationalization setup that supersedes the synthetic-package pattern.

---

# NOTICE — frontend-design

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- anthropics/skills (Apache-2.0) — https://github.com/anthropics/skills @ 41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f — paths: skills/frontend-design — Five generated-design clusters, the two-pass design process (plan, review against the brief, build, self-critique), typographic direction principles, and the interface-copy doctrine.
- vercel-labs/web-interface-guidelines (MIT) — https://github.com/vercel-labs/web-interface-guidelines @ e3d624baaf29dc1fc645aff3e38f03e564d2d6b1 — paths: command.md — The mechanically checkable UI review rule set across accessibility, focus, forms, animation, typography, content handling, images, performance, navigation, touch, theming, locale and copy, plus the group-by-file `path:line` output contract.
- addyosmani/agent-skills (MIT) — https://github.com/addyosmani/agent-skills @ 6ca0cd7db39b41b1c37e26d335c507ee92382c6d — paths: skills/frontend-ui-engineering, references/accessibility-checklist.md — The AI-default to production-quality mapping for palette, radius, shadow, padding and card grids; spacing-scale discipline; semantic color tokens; ARIA live-region table; empty and error state patterns.
- addyosmani/agent-skills (MIT) — https://github.com/addyosmani/agent-skills @ 6ca0cd7db39b41b1c37e26d335c507ee92382c6d — paths: skills/performance-optimization, references/performance-checklist.md — The measure, identify, fix, verify, guard loop; the by-symptom bottleneck triage tree; synthetic versus field measurement split; regression guarding.
- antfu/skills (MIT) — https://github.com/antfu/skills @ a74f281a27dadc02397bc1a174b0f2c97531b6ae — paths: skills/antfu-design — Design read plus tooling and marketing dial baselines, the anti-slop hard list (dash ban, generic names, fake-perfect numbers, filler verbs, decoration tells), bias correction for type, color, layout and materiality, micro-interaction polish (concentric radius, optical alignment, borders versus shadows), and the pattern vocabulary.
- leonxlnx/taste-skill (MIT) — https://github.com/leonxlnx/taste-skill @ ccbc15639c97057cbfcf32ecebc38ef716e4bb37 — paths: skills/taste-skill — Origin of the VARIANCE / MOTION / DENSITY dial system and the one-line design read, which the antfu-design references credit to it.
- emilkowalski/skills (MIT) — https://github.com/emilkowalski/skills @ d23d7f88a2e21c9e4b1418c7abe420f5c1052ba7 — paths: skills/review-animations, skills/emil-design-eng — The should-it-animate frequency table, easing decision order with strong custom curves, per-element duration bands and the sub-300ms ceiling, physicality rules (never scale(0), origin-aware popovers, press feedback), interruptibility and @starting-style, stagger range, and reduced-motion nuance.
- nextlevelbuilder/ui-ux-pro-max-skill (MIT) — https://github.com/nextlevelbuilder/ui-ux-pro-max-skill @ 7f69fed6a2717900085f1bc3b263721f8ba025e2 — paths: .claude/skills/ui-ux-pro-max/references/quick-reference.md, .claude/skills/ui-ux-pro-max/references/pro-rules.md — Deduplicated UX judgement calls that the Vercel rule set does not cover: compact-label and overflow semantics, disabled versus read-only, focusable error summaries, waiting-feedback matching, and the chart accessibility set.
- GoogleChrome/modern-web-guidance (Apache-2.0) — https://github.com/GoogleChrome/modern-web-guidance @ bfd8c8dded770f3ba07a518e28991a32df40f902 — paths: skills/modern-web-guidance — Baseline verdict interpretation and fallback policy negotiation, the search / retrieve / list workflow, and the goal-to-guide mapping over the published guide corpus.
- https://www.w3.org/TR/WCAG22/ (W3C-20150513) — https://www.w3.org/TR/WCAG22/ — Authoritative source for every accessibility number and conformance level used, including SC 2.5.8 (AA, 24 by 24 CSS px) and SC 2.5.5 (AAA, 44 by 44 CSS px), contrast, reflow, text spacing, focus and authentication criteria.
- https://web.dev/articles/vitals (CC-BY-4.0) — https://web.dev/articles/vitals — Core Web Vitals thresholds (LCP 2.5s, INP 200ms, CLS 0.1) and the 75th-percentile, mobile-and-desktop-segmented evaluation method.

Reference-only sources (no content copied):

- wshobson/agents (MIT) — https://github.com/wshobson/agents

---

# NOTICE — office

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- openai/skills (Apache-2.0) — https://github.com/openai/skills @ 49f948faa9258a0c61caceaf225e179651397431 — paths: skills/.curated/pdf — The render-inspect-fix loop as the delivery gate, the reportlab/pdfplumber/pypdf split, and the rule that nothing ships until a page render shows zero defects.
- github/awesome-copilot (MIT) — https://github.com/github/awesome-copilot @ 7568a482ce2df38f8965ab5336a3220db796a4ba — paths: skills/md-to-docx — The zero-native-dependency Markdown to Word approach: docx plus marked, YAML front matter driving a title page, a generated contents list, and images sized from their file headers.
- SlideSpeak/slide-design-skill (MIT) — https://github.com/SlideSpeak/slide-design-skill @ 5e87d8ae71f6306e0c88f4910e6c09114581d91b — paths: SKILL.md — Deck design stance taken into references/pptx-design.md: derive the visual style from the brief instead of picking a theme, and enforce readable type, no empty bands, no invented numbers as hard rules.
- ourarash/markdown-docx-tool (MIT) — https://github.com/ourarash/markdown-docx-tool @ 4456f8254482d11feb425bb7e2adc636be377d48 — paths: skills/markdown-to-docx — The pandoc-with-reference-document path as the escape hatch for house templates, including named custom-style callouts and the rule that a missing style degrades silently.
- https://docx.js.org/ (MIT) — https://docx.js.org/ — docx-js API surface for documents, sections, paragraphs, runs, tables, images and fields; the basis of references/docx.md.
- https://gitbrent.github.io/PptxGenJS/docs/ (MIT) — https://gitbrent.github.io/PptxGenJS/docs/ — pptxgenjs API for masters, text, tables, charts, images and notes.
- https://openpyxl.readthedocs.io/ (MIT) — https://openpyxl.readthedocs.io/ — openpyxl behaviour for formulas, data_only loading, merged cells, number formats, charts, keep_vba and the read-only and write-only modes.
- https://python-docx.readthedocs.io/ (MIT) — https://python-docx.readthedocs.io/ — python-docx and python-pptx object models, used for the library round-trip gate and for template filling.
- https://pypdf.readthedocs.io/ (BSD-3-Clause) — https://pypdf.readthedocs.io/ — pypdf reader and writer semantics: append, clone_from, page transforms, metadata, encryption and AcroForm field updates.
- https://github.com/jsvine/pdfplumber (MIT) — https://github.com/jsvine/pdfplumber — Positional text extraction and the table-detection strategies, tolerances and explicit-line settings.
- https://docs.reportlab.com/ (BSD-3-Clause) — https://docs.reportlab.com/ — reportlab canvas and platypus: coordinate origin, paragraph markup, table styles, font registration and AcroForm creation.
- https://pandoc.org/MANUAL.html (GPL-2.0-or-later) — https://pandoc.org/MANUAL.html — Reading docx, the track-changes modes, and the reference-document style mapping including custom-style divs.
- https://help.libreoffice.org/ (MPL-2.0) — https://help.libreoffice.org/ — Headless conversion, --convert-to filters, recalculation on load, and the private user-profile flag both bundled scripts rely on.
- https://ecma-international.org/publications-and-standards/standards/ecma-376/ (NONE) — https://ecma-international.org/publications-and-standards/standards/ecma-376/ — Normative OOXML markup semantics for w:ins, w:del, w:delText, paragraph-mark revisions, rPrChange, comment parts, content types and relationships.

Reference-only sources (no content copied):

- anthropics/skills (Proprietary) — https://github.com/anthropics/skills
- anthropics/skills (Proprietary) — https://github.com/anthropics/skills
- anthropics/skills (Proprietary) — https://github.com/anthropics/skills
- anthropics/skills (Proprietary) — https://github.com/anthropics/skills
- nexu-io/open-design (Apache-2.0) — https://github.com/nexu-io/open-design

---

# NOTICE — react

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- vercel-labs/agent-skills (MIT) — https://github.com/vercel-labs/agent-skills @ 063bee94c3f4df8453406c830b0a7df0f2860278 — paths: skills/react-best-practices, skills/composition-patterns — Impact-ordered React performance rules with their stable ids, plus the composition and state-contract rules.
- addyosmani/agent-skills (MIT) — https://github.com/addyosmani/agent-skills @ 6ca0cd7db39b41b1c37e26d335c507ee92382c6d — paths: skills/frontend-ui-engineering — Colocated file layout, composition over configuration, container/presentation split, the state-location ladder, prop-drilling limit, and loading/empty/error state requirements.
- vercel/next.js (MIT) — https://github.com/vercel/next.js/tree/canary/skills @ 1329212686c9558afc37589106618d7382542d24 — paths: skills/next-cache-components-optimizer, skills/next-cache-components-adoption, skills/next-partial-prefetching-adoption, skills/next-dev-loop — Cache Components adoption sequence and the instant-navigation loop: phases and gates, the blocking-shape fixes, the instant() guard, loading-UI reuse, and the post-optimization prefetching check.
- openai/plugins (NONE) — https://github.com/openai/plugins @ d416fd5a43426019986b1e489506db3db66dee3d — paths: plugins/vercel/skills/nextjs — App Router API semantics: file conventions, RSC boundary validity, async request APIs, runtime choice, directives, error handling, data-pattern selection, route handlers, metadata, image, font, scripts, hydration, suspense bailout, parallel routes, bundling, self-hosting and dev-server debugging.
- shadcn-ui/ui (MIT) — https://github.com/shadcn-ui/ui @ 3ba91b1cc83e1bbe4ab35a422ff2a694849c5048 — paths: skills/shadcn — The shadcn workflow (info, docs, search, add, review), the styling and Tailwind conventions, form and composition rules, icon rules, base-vs-radix API differences, registry rules and theming.
- https://react.dev/reference (CC-BY-4.0) — https://react.dev/reference — Correctness arbiter and version floors; the sole source for the Actions form-state section (useActionState, useFormStatus, useOptimistic).
- https://nextjs.org/docs (MIT) — https://nextjs.org/docs — Arbiter for data-fetching and caching semantics, and for the cacheComponents and instant-navigation version facts.

Reference-only sources (no content copied):

- anthropics/skills (NOASSERTION) — https://github.com/anthropics/skills

---

# NOTICE — skill-authoring

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- anthropics/skills (Apache-2.0) — https://github.com/anthropics/skills @ 41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f — paths: skills/skill-creator, template/SKILL.md — Description triggering strategy for capability skills, the 20-query trigger set with near-miss negatives and the 60/40 held-out split, the baseline-and-with-skill evaluation loop, grading and benchmark field names, organising references by variant, the transcript signal that justifies bundling a script, and the lack-of-surprise safety rule.
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (NONE) — https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices — Core authoring principles, the three degrees of freedom, the three progressive-disclosure patterns and the partial-read reason for one-level references, workflow checklists and validation loops, template / examples / conditional-workflow patterns, evaluation-driven development and the evals.json shape, the two-agent iteration loop and the four navigation signals, script rules (solve rather than defer, no voodoo constants, explicit dependencies), the anti-pattern list, and the pre-release checklist.
- obra/superpowers (MIT) — https://github.com/obra/superpowers @ b36e0829c6d0140e93cfef2ca599b1b07d4a7797 — paths: skills/writing-skills — Baseline-first discipline for authoring, the rule that a workflow skill's description carries triggering conditions only, load-frequency token budgets, verb-first naming, the ban on path syntaxes that force-load a file, the match-the-form-to-the-failure table with its head-to-head wording evidence, rationalisation tables and red-flag lists, and micro-testing wording against a no-guidance control.
- https://agentskills.io/specification (Apache-2.0) — https://agentskills.io/specification — The normative frontmatter field table with exact limits, the five name construction rules and the directory-match requirement, the optional directory conventions, the three progressive-disclosure tiers and their budgets, the file-reference rules, and the reference validator command.
- vercel-labs/skills (MIT) — https://github.com/vercel-labs/skills @ 80feb48868972d518436f26711509bc78595b5cb — paths: README.md — Installer source formats, subcommands and flags, the download and extraction limits, the container-directory list with its three-level walk and shallow-shadows-deep rule, plugin manifest discovery, the single reserved metadata key, project versus user install scope, symlink versus copy, and the per-host capability matrix.
- https://code.claude.com/docs/en/skills (NONE) — https://code.claude.com/docs/en/skills — The full table of that host's non-standard frontmatter fields, its 1536-character listing truncation, its inverted enterprise-over-personal-over-project precedence, its reserved directory name, and its own warning that only specification fields may be used elsewhere.
- https://cursor.com/docs/skills (NONE) — https://cursor.com/docs/skills — That host's path-scoping field and its legacy name, its invocation-control, icon and colour fields, and its recursive discovery with automatic scoping of skills in nested project directories.
- https://learn.chatgpt.com/docs/build-skills (NONE) — https://learn.chatgpt.com/docs/build-skills — The initial-listing budget of 2% of the context window or 8000 characters with descriptions shortened first, which is the evidence for front-loading the key use case; the sibling agents/openai.yaml interface, policy and dependency schema; and the repository, user, admin and system discovery scopes.
- grafana/skills (Apache-2.0) — https://github.com/grafana/skills @ 51d33e71e191b409bbd25fc7be2684c610d18166 — paths: skills/grafana-core/skill-authoring — The four review dimensions (conciseness, actionability, workflow clarity, progressive disclosure) as review semantics, the observation that a model grading quality swings widely between runs so a threshold must hold across consecutive runs, and the rule that a deliberately routing body must stay independently executable rather than being inlined back.
- getsentry/skills (Apache-2.0) — https://github.com/getsentry/skills @ c2f99a5b04b4cd992ec3022d7c2c3e23e938d241 — paths: skills/skill-writer — The one-reason-per-row open-when routing table as the shape of a router body, the discipline of naming which existing rule or section is narrowed or removed before adding new guidance, and a four-part output contract of summary, changes, validation results and open gaps.
- mgechev/skills-best-practices (NONE) — https://github.com/mgechev/skills-best-practices @ a0bfa56bbcd676383f6ca57bb7e344d0856bc38e — paths: skill — Scanning a finished draft for the points where it forces the agent to guess, the rule that a skill directory contains nothing written for human readers, and designing a bundled validator so its error output drives a self-correcting loop.
- Lynricsy/HyperSkills (MIT) — https://github.com/Lynricsy/HyperSkills @ 7aa1586ce7a3b9b269241a79f01e492f1294bb98 — paths: docs/skill-standard.md, docs/workflow.md, tools — The provenance record schema and generated attribution format, the mechanically checkable validation list used in continuous integration, and the evaluation-runner shape of scenario file plus measured no-skill baseline that the publishing and evaluation references describe.

Reference-only sources (no content copied):

- openai/skills (NONE) — https://github.com/openai/skills
- Ronifue/skill-authoring (MIT) — https://github.com/Ronifue/skill-authoring

---

# NOTICE — test-driven-development

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- obra/superpowers (MIT) — https://github.com/obra/superpowers @ b36e0829c6d0140e93cfef2ca599b1b07d4a7797 — paths: skills/test-driven-development — The Iron Law and the mandatory watch-it-fail step, the rationalization and red-flag tables, the when-stuck table, the delete-code-written-first rule, and writing-good-tests.md: the name-the-break and exercise-the-real-thing gates, independent expected values, the change-detector and mock-assertion bans, and the mutation check.
- obra/superpowers (MIT) — https://github.com/obra/superpowers @ b36e0829c6d0140e93cfef2ca599b1b07d4a7797 — paths: skills/verification-before-completion — The evidence-before-claim completion gate and the red-green procedure that proves a regression test is real: write, pass, revert the fix, confirm it fails, restore, pass again.
- mattpocock/skills (MIT) — https://github.com/mattpocock/skills @ 3cca18b368ae95cdbdebbff572ccafa662551015 — paths: skills/engineering/tdd — The seam vocabulary and the agree-the-seam-first step, vertical slices and tracer bullets against horizontal slicing, the tautological-test definition, and the verify-through-the-interface-not-a-side-channel example.
- mattpocock/skills (MIT) — https://github.com/mattpocock/skills @ 3cca18b368ae95cdbdebbff572ccafa662551015 — paths: skills/productivity/grilling — The one-round question format used when a seam is genuinely ambiguous: ask every open question at once, numbered, each with a recommended answer, and look facts up rather than asking for them.
- addyosmani/agent-skills (MIT) — https://github.com/addyosmani/agent-skills @ 6ca0cd7db39b41b1c37e26d335c507ee92382c6d — paths: skills/test-driven-development — Discover-the-stack-first (find this repository's real focused and full-suite commands before RED), the prove-it bug-fix flow, the pyramid and the Small/Medium/Large resource model, DAMP over DRY, the real > fake > stub > mock ladder, arrange-act-assert, and the anti-pattern table.
