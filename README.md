# HyperSkills

整合型 Agent Skill 集合：**每个技术生态 / 每类常见任务 = 一个独立 skill**。
每个 skill 都不是对某个上游仓库的搬运，而是把该领域多个高质量上游 skill **全部精编重写**
合成的一份内容——去重、消歧、裁决冲突、补齐缺口，并在 `SOURCES.yaml` 中固定 commit
记录全部上游，便于后续追踪上游更新。

## 设计原则

1. **扁平**。所有 skill 平铺在 `skills/<name>/`。所有主流 agent（Claude Code / Codex /
   Cursor / OMP）的 skill 发现都是一级扫描，嵌套分类目录不会被发现；分类只用 frontmatter
   的 `metadata.category` 与本页目录表表达。
2. **一个生态一个 skill**。不做 `swiftui` / `swift-concurrency` / `swiftdata` 这种碎片化
   切分——它们属于同一次任务，应当同时在场。
3. **精编重写，不是聚合**。上游内容一律重写：统一术语、统一章节结构、删掉模型本来就会的
   常识、只留下边缘情况与易错点。代码示例按需调整并在本机跑通。
4. **上游可追溯**。`SOURCES.yaml` 记录每个上游的 repo、路径、分支、合入时的 commit、许可与
   贡献内容；`tools/check_upstream.py` 可以列出自那次 commit 以来上游的全部变更。
5. **只收活跃高质量上游**。知名、认可度高、6 个月内有推送；陈旧 / 低质 / 无人维护的一律不
   合入，并在 `research/<skill>.md` 中留下 REJECT 记录与理由。
6. **评测先行**。动笔前先写 ≥3 个评测场景（含 ≥1 负例）并跑无 skill 基线；skill 必须填补
   基线暴露出的缺口，否则视为无效。

## 目录

<!-- catalog:start -->

| Skill | 类别 | 说明 | 版本 | 上游数 |
|---|---|---|---|---|
| [`android`](skills/android/) | 平台 | Guides native Android work end to end: Kotlin with coroutines and Flow, Jetpack Compose (state, side effects, stability, recomposition and scroll… | 2026.09.11 | 11 |
| [`api-design`](skills/api-design/) | 任务 | Designs and reviews HTTP API contracts independently of any framework: resource modelling and URI structure, HTTP method semantics and idempotency… | 2026.09.11 | 19 |
| [`apple`](skills/apple/) | 平台 | Guides Apple platform development in Swift — SwiftUI views, data flow and @Observable, ForEach identity, navigation, animation, Liquid Glass (iOS… | 2026.09.10 | 15 |
| [`astro`](skills/astro/) | 框架 | Engineers Astro 7 sites: project and route structure including dynamic routes and getStaticPaths, island boundaries and the client:* hydration… | 2026.09.11 | 6 |
| [`chrome-extension`](skills/chrome-extension/) | 平台 | Guides Chrome and Chromium browser extension work end to end: Manifest V3 manifests, the permissions and host-permissions model, activeTab and… | 2026.09.11 | 10 |
| [`code-review`](skills/code-review/) | 任务 | Reviews code in both directions | 2026.09.10 | 9 |
| [`containers`](skills/containers/) | 平台 | Guides container artefacts: Dockerfiles and multi-stage builds, base-image choice, BuildKit cache mounts and build secrets, .dockerignore… | 2026.09.11 | 13 |
| [`csharp-dotnet`](skills/csharp-dotnet/) | 框架 | Guides C# and .NET application work end to end: C# language rules (nullable reference types and the nullability attributes, records, pattern… | 2026.09.11 | 10 |
| [`debugging`](skills/debugging/) | 任务 | Diagnoses broken behaviour and fixes it at the root cause: builds a red-capable feedback loop before theorising, reproduces and minimises, localises… | 2026.09.10 | 4 |
| [`elasticsearch`](skills/elasticsearch/) | 框架 | Guides Elasticsearch index and query work: mapping and field-type choice, text versus keyword and multi-fields, analyzers and tokenization, Query DSL… | 2026.09.11 | 9 |
| [`fastapi`](skills/fastapi/) | 框架 | Guides FastAPI service work: APIRouter organisation, Annotated dependency injection including yield-dependency lifetime and exit scope, Pydantic v2… | 2026.09.11 | 12 |
| [`flutter`](skills/flutter/) | 平台 | Guides Flutter and Dart work end to end: widgets and responsive layout, state management (Riverpod 3 Notifier, Bloc/Cubit, ChangeNotifier MVVM)… | 2026.09.10 | 7 |
| [`frontend-design`](skills/frontend-design/) | 任务 | Guides visual and UX quality for web UIs: design direction (typography, color and tokens, layout, spacing, motion), avoiding generic AI-looking… | 2026.09.10 | 12 |
| [`github`](skills/github/) | 平台 | Guides work that needs GitHub the platform | 2026.09.11 | 15 |
| [`go`](skills/go/) | 框架 | Guides Go work end to end: idiomatic language use and useful zero values, interfaces and composition, goroutine lifetime, context cancellation… | 2026.09.11 | 12 |
| [`graphql`](skills/graphql/) | 框架 | Guides GraphQL schema and operation work: nullability and the non-null error propagation that turns one failing field into a null response, type and… | 2026.09.11 | 12 |
| [`java-spring`](skills/java-spring/) | 框架 | Guides Spring Boot work end to end: auto-configuration and configuration properties, Spring MVC versus WebFlux and RFC 9457 error contracts… | 2026.09.11 | 8 |
| [`laravel`](skills/laravel/) | 框架 | Guides Laravel application work on Laravel 12 and 13 with modern PHP: Eloquent modelling and loading strategy (N+1, eager loading, scopes, casts… | 2026.09.11 | 9 |
| [`mongodb`](skills/mongodb/) | 框架 | Guides MongoDB work: document modelling (embed versus reference, array growth, bucketing, subset and extended-reference tradeoffs, schema versioning… | 2026.09.11 | 6 |
| [`nodejs-backend`](skills/nodejs-backend/) | 框架 | Engineers Node.js HTTP services: process and request lifecycle, graceful shutdown and connection draining, schema validation at every boundary, error… | 2026.09.11 | 13 |
| [`office`](skills/office/) | 任务 | Creates, edits, reads and converts Word (.docx), PowerPoint (.pptx), Excel (.xlsx) and PDF files — reports, memos, letters, decks, slides… | 2026.09.10 | 19 |
| [`postgres`](skills/postgres/) | 框架 | Guides self-managed PostgreSQL work: schema and type selection, constraints, index choice and composite column order, reading EXPLAIN (ANALYZE… | 2026.09.11 | 12 |
| [`python`](skills/python/) | 框架 | Guides modern Python work: uv for projects, tools and PEP 723 single-file scripts; ruff as the single linter and formatter; pyproject.toml… | 2026.09.11 | 17 |
| [`react`](skills/react/) | 框架 | Engineers React 19+ and Next.js App Router (15/16+) code: component architecture and composition, state selection, rendering / re-render / bundle /… | 2026.09.10 | 8 |
| [`react-native`](skills/react-native/) | 平台 | Engineers React Native and Expo apps at the runtime and native boundary: New Architecture (Fabric, Turbo Native Module specs, codegen, the interop… | 2026.09.11 | 7 |
| [`redis`](skills/redis/) | 框架 | Guides Redis itself: choosing a data structure from the access pattern, key-space and TTL design, what each maxmemory-policy really does when memory… | 2026.09.11 | 7 |
| [`skill-authoring`](skills/skill-authoring/) | 元技能 | Authors, reviews, evaluates and publishes Agent Skills — the SKILL.md frontmatter and body plus bundled references/, scripts/ and assets/ | 2026.09.10 | 14 |
| [`supabase`](skills/supabase/) | 框架 | Guides work on Supabase projects: Auth sessions and JWTs, the publishable/secret key split and the legacy anon/service_role pair, @supabase/ssr… | 2026.09.11 | 12 |
| [`svelte`](skills/svelte/) | 框架 | Engineers Svelte 5 and SvelteKit 2 code: runes and the reactivity model ($state, $state.raw, $derived, and the ways $effect gets misused), snippets… | 2026.09.11 | 11 |
| [`tauri`](skills/tauri/) | 平台 | Guides Tauri v2 desktop and mobile application work end to end: tauri.conf.json and platform-specific config overrides, the capabilities and… | 2026.09.11 | 6 |
| [`terraform`](skills/terraform/) | 框架 | Guides Terraform and OpenTofu configuration work: HCL style and expressions, variable, output and local design, module interfaces and version… | 2026.09.11 | 11 |
| [`test-driven-development`](skills/test-driven-development/) | 任务 | Drives implementation and bug fixes test-first in any language or framework: discovers the repository's own test commands before writing anything… | 2026.09.10 | 5 |
| [`typescript`](skills/typescript/) | 框架 | Engineers TypeScript at the type layer and the build layer: modelling a domain so illegal states do not compile (discriminated unions, branded types… | 2026.09.11 | 9 |
| [`vue`](skills/vue/) | 框架 | Engineers Vue 3 applications: the Composition API with `script setup` SFCs, the reactivity system and every way it silently detaches (reactive… | 2026.09.11 | 10 |

<!-- catalog:end -->

## 安装

### `npx skills`（任意 agent）

```bash
npx skills@latest add Lynricsy/HyperSkills --skill apple
npx skills@latest add Lynricsy/HyperSkills --skill '*'     # 全部
```

### Claude Code 插件市场

```
/plugin marketplace add Lynricsy/HyperSkills
/plugin install apple@hyperskills
/plugin install all@hyperskills
```

### 手工安装

```bash
git clone https://github.com/Lynricsy/HyperSkills.git
cp -r HyperSkills/skills/apple ~/.agents/skills/
```

## 仓库结构

```
HyperSkills/
├── skills/<name>/          # 扁平的 skill 目录
│   ├── SKILL.md            # frontmatter + 正文（英文）
│   ├── SOURCES.yaml        # 上游溯源，手工维护
│   ├── NOTICE.md           # 生成，勿改
│   ├── references/*.md     # 按需加载的深度内容
│   ├── evals/evals.json    # 行为评测场景
│   ├── scripts/            # 可选，自包含
│   └── assets/             # 可选
├── docs/
│   ├── skill-standard.md   # 结构 / 写作 / 溯源规范
│   ├── workflow.md         # 新增与更新 skill 的五阶段流水线
│   └── roadmap.md          # 后续批次主题路线图
├── research/<name>.md      # 候选调研、冲突裁决、评测结果（中文）
├── templates/              # 脚手架
└── tools/                  # 校验 / 上游检查 / 目录生成 / 评测运行
```

## 维护

新增或更新 skill 必须走 `docs/workflow.md` 的五个阶段。常用命令：

```bash
uv run tools/new_skill.py <name> --category platform   # 脚手架
uv run tools/run_evals.py <name> --baseline            # 无 skill 基线
uv run tools/validate_skills.py                        # 质量门
uv run tools/check_upstream.py                         # 上游漂移
uv run tools/check_upstream.py --pin <name>            # 固定 commit
uv run tools/build_catalog.py                          # 生成目录与 NOTICE
```

提交前必须通过：

```bash
uv run tools/validate_skills.py && uv run tools/build_catalog.py --check
```

## 许可

- 本仓库自有内容：[MIT](LICENSE)。
- 上游材料的许可与署名：见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与各
  `skills/<name>/NOTICE.md`。
- 专有许可的上游（如 Anthropic 的 docx/pptx/xlsx/pdf skill）仅作为**参考基准**，
  `relation: reference`，未复制任何文字、脚本或数据文件。
