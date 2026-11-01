# NOTICE — react

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- vercel-labs/agent-skills (MIT) — https://github.com/vercel-labs/agent-skills @ 1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62 — paths: skills/react-best-practices, skills/composition-patterns — Impact-ordered React performance rules with their stable ids, plus the composition and state-contract rules.
- addyosmani/agent-skills (MIT) — https://github.com/addyosmani/agent-skills @ 8bfcc1f9916f2eea55494d8c1fa7f4bde867dd9e — paths: skills/frontend-ui-engineering — Colocated file layout, composition over configuration, container/presentation split, the state-location ladder, prop-drilling limit, and loading/empty/error state requirements.
- vercel/next.js (MIT) — https://github.com/vercel/next.js/tree/canary/skills @ 3bccd4df910c984ca60f796e50b8d43db3227162 — paths: skills/next-cache-components-optimizer, skills/next-cache-components-adoption, skills/next-partial-prefetching-adoption, skills/next-dev-loop, skills/next-bundle-optimizer — Cache Components adoption sequence and the instant-navigation loop: phases and gates, the blocking-shape fixes, the instant() guard, loading-UI reuse, and the post-optimization prefetching check. next-bundle-optimizer surfaced the 16.4 rename of the bundle analyzer command (`next analyze`, with `experimental-analyze` kept as an alias).
- openai/plugins (NONE) — https://github.com/openai/plugins @ 0722921d5542fc593105c27bd52630babd8b8c2a — paths: plugins/vercel/skills/nextjs — App Router API semantics: file conventions, RSC boundary validity, async request APIs, runtime choice, directives, error handling, data-pattern selection, route handlers, metadata, image, font, scripts, hydration, suspense bailout, parallel routes, bundling, self-hosting and dev-server debugging.
- shadcn-ui/ui (MIT) — https://github.com/shadcn-ui/ui @ c0d63c339d6cd2fc26135590a54cf1f362269451 — paths: skills/shadcn — The shadcn workflow (info, docs, search, add, review), the styling and Tailwind conventions, form and composition rules, icon rules, base-vs-radix API differences, registry rules and theming.
- https://github.com/facebook/react/security/advisories (MIT) — https://github.com/facebook/react/security/advisories — The RSC security-release section in references/nextjs-ops-and-debug.md and core rule 21: every RSC advisory since December 2025 patches `react-server-dom-webpack`/`-turbopack`/`-parcel` on all supported lines at once (19.0.x, 19.1.x, 19.2.x and, from October 2026, 19.3.x).
- https://react.dev/reference (CC-BY-4.0) — https://react.dev/reference — Correctness arbiter and version floors; the sole source for the Actions form-state section (useActionState, useFormStatus, useOptimistic).
- https://nextjs.org/docs (MIT) — https://nextjs.org/docs — Arbiter for data-fetching and caching semantics, and for the cacheComponents and instant-navigation version facts.

Reference-only sources (no content copied):

- anthropics/skills (NOASSERTION) — https://github.com/anthropics/skills
- TerminalSkills/skills (Apache-2.0) — https://github.com/TerminalSkills/skills/tree/main/skills/react
