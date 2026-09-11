<h1 align="center">HyperSkills</h1>

<p align="center">
整合型 Agent Skill 集合：一个技术生态或一类任务 = 一个 skill，由 450 个上游精编重写合成，全部固定 commit。
</p>

<p align="center">
<a href="LICENSE"><img alt="许可: MIT" src="https://img.shields.io/github/license/Lynricsy/HyperSkills"></a>
<a href="skills/"><img alt="skill 数量" src="https://img.shields.io/github/directory-file-count/Lynricsy/HyperSkills/skills?type=dir&label=skills"></a>
<a href="https://github.com/Lynricsy/HyperSkills/commits/main"><img alt="最近提交时间" src="https://img.shields.io/github/last-commit/Lynricsy/HyperSkills"></a>
</p>

<p align="center">
<a href="#安装">安装</a> ·
<a href="#skill-目录">skill 目录</a> ·
<a href="docs/skill-standard.md">编写标准</a> ·
<a href="docs/workflow.md">五阶段流水线</a> ·
<a href="https://github.com/Lynricsy/HyperSkills/issues">反馈</a>
</p>

> **skill 会以 agent 的全部权限运行。** 装之前把 `SKILL.md` 和 `scripts/` 读一遍——
> 这条对本仓库和任何第三方 skill 都一样。

状态：活跃开发中，53 个 skill 已过静态门与行为评测；仓库暂无 CI。维护者
[@Lynricsy](https://github.com/Lynricsy)，问题走 [Issues](https://github.com/Lynricsy/HyperSkills/issues)。

## 这是什么

一个 skill 对应 agent 真正会遇到的一整类任务，而不是对某个上游仓库的搬运。

- **一个生态一个 skill。** `apple` 一个 skill 同时覆盖 SwiftUI 数据流、Swift 6 严格并发、
  SwiftData 与 Instruments，不切成 `swiftui` / `swift-concurrency` / `swiftdata` 三个——
  它们属于同一次任务，应当同时在场。
- **精编重写，不是聚合。** 53 个 `SOURCES.yaml` 里共 581 条上游记录（436 条内容重写合入、
  145 条仅阅读对齐），分布在 450 个不同仓库。合入时统一术语、裁决冲突、删掉模型本来就会的
  常识，只留边缘情况、静默失败、版本差异与易错点。
- **先有评测再有正文。** 动笔前先写评测场景（每个 skill ≥3 个，含 ≥1 个「近似但不该触发」
  的负例）并跑无 skill 基线；skill 必须让至少一条基线未达成的行为达成，否则判为无效、回炉重写。
  当前 244 个场景。
- **上游可追溯。** 每条上游记录固定合入时的 40 位 commit，`tools/check_upstream.py` 能列出
  自那次 commit 以来上游在被引用路径下的全部变更，区分「仓库动了但引用路径没动」和「真的变了」。

## 不做什么

- **不建嵌套分类目录。** `skills/` 保持扁平（`skills/<name>/SKILL.md`），因为主流 agent 的
  skill 发现是一级扫描；分类只在 frontmatter 的 `metadata.category` 与下方目录表里表达。
- **不收陈旧或空洞的上游。** 6 个月内无推送、或正确性抽查两条以上对不上官方文档的候选直接
  REJECT，连理由留在 `research/<skill>.md`，避免下一批重复讨论同一个候选。
- **不碰专有许可的内容。** Anthropic 的 docx / pptx / xlsx / pdf skill 只作参考基准
  （`relation: reference`），未复制任何文字、脚本或数据文件。
- **不给多选项。** 正文只写裁决后的一种做法加一个逃生口，不罗列可选库；裁决过程留在
  `research/`，不进 skill。
- **没有 CI。** 下面两条质量门命令要在本地跑；红了不会有人自动告诉你。
- **正文英文。** `SKILL.md`、`references/`、`scripts/` 注释一律英文（给模型读），
  README、`docs/`、`research/` 一律中文（给人读）。

## 安装

### npx skills（任意 agent）

```bash
# 装一个
npx skills@latest add Lynricsy/HyperSkills --skill technical-writing --agent universal --copy --yes

# 装全部 53 个
npx skills@latest add Lynricsy/HyperSkills --skill '*' --agent universal --copy --yes
```

两条都装到项目内的 `./.agents/skills/`；加 `-g` 改装到用户级。

### Claude Code 插件市场

```
/plugin marketplace add Lynricsy/HyperSkills
/plugin install technical-writing@hyperskills
/plugin install all@hyperskills
```

插件名与 skill 目录名一致，`all` 是全部 53 个。清单是 `.claude-plugin/marketplace.json`。

### 手工复制

```bash
git clone https://github.com/Lynricsy/HyperSkills.git
cp -r HyperSkills/skills/technical-writing ~/.agents/skills/
```

目标目录换成你的 agent 自己的 skill 目录也可以，skill 是自包含的。

## 装完之后确认它在

```console
$ npx skills@latest ls
Project Skills

technical-writing ./.agents/skills/technical-writing
  Agents: Amp, Codex, Cursor, Droid, Gemini CLI +4 more  Source: Lynricsy/HyperSkills
```

`--agent universal` 会把 skill 写进 `./.agents/skills/`，再链接到本机识别到的 agent 目录；
上面那次运行识别到 9 个（Amp、Codex、Cursor、Droid、Gemini CLI、GitHub Copilot、
Kimi Code CLI、OpenCode、Zed），`npx skills@latest ls --json` 会列全。

之后不需要手动指定：skill 靠 frontmatter 的 `description` 触发，触发关键词与否定边界
（`Do not use for …`）都写在里面。

## skill 目录

53 个：框架 20、平台 17、任务 15、元技能 1。下表由 `tools/build_catalog.py` 生成。

<!-- catalog:start -->

| Skill | 类别 | 说明 | 版本 | 上游数 |
|---|---|---|---|---|
| [`ai-engineering`](skills/ai-engineering/) | 任务 | Builds and reviews code that calls a language model: prompts separating instructions from retrieved or tool-supplied data, provider-enforced… | 2026.09.11 | 13 |
| [`android`](skills/android/) | 平台 | Guides native Android work end to end: Kotlin with coroutines and Flow, Jetpack Compose (state, side effects, stability, recomposition and scroll… | 2026.09.11 | 11 |
| [`api-design`](skills/api-design/) | 任务 | Designs and reviews HTTP API contracts independently of any framework: resource modelling and URI structure, HTTP method semantics and idempotency… | 2026.09.11 | 19 |
| [`apple`](skills/apple/) | 平台 | Guides Apple platform development in Swift — SwiftUI views, data flow and @Observable, ForEach identity, navigation, animation, Liquid Glass (iOS… | 2026.09.10 | 15 |
| [`astro`](skills/astro/) | 框架 | Engineers Astro 7 sites: project and route structure including dynamic routes and getStaticPaths, island boundaries and the client:* hydration… | 2026.09.11 | 6 |
| [`aws`](skills/aws/) | 平台 | Guides AWS architecture and control-plane work: IAM policy evaluation, permissions boundaries, trust policies and PassRole escalation; Lambda, API… | 2026.09.11 | 8 |
| [`azure`](skills/azure/) | 平台 | Guides Azure control-plane and architecture work: Bicep and Azure Verified Modules, what-if preflight, deployment stacks, azd projects, CAF naming… | 2026.09.11 | 13 |
| [`chrome-extension`](skills/chrome-extension/) | 平台 | Guides Chrome and Chromium browser extension work end to end: Manifest V3 manifests, the permissions and host-permissions model, activeTab and… | 2026.09.11 | 10 |
| [`cloudflare`](skills/cloudflare/) | 平台 | Guides building and operating on the Cloudflare developer platform: the Workers isolate model and its CPU and memory limits, waitUntil and… | 2026.09.11 | 8 |
| [`code-review`](skills/code-review/) | 任务 | Reviews code in both directions | 2026.09.10 | 9 |
| [`containers`](skills/containers/) | 平台 | Guides container artefacts: Dockerfiles and multi-stage builds, base-image choice, BuildKit cache mounts and build secrets, .dockerignore… | 2026.09.11 | 13 |
| [`csharp-dotnet`](skills/csharp-dotnet/) | 框架 | Guides C# and .NET application work end to end: C# language rules (nullable reference types and the nullability attributes, records, pattern… | 2026.09.11 | 10 |
| [`debugging`](skills/debugging/) | 任务 | Diagnoses broken behaviour and fixes it at the root cause: builds a red-capable feedback loop before theorising, reproduces and minimises, localises… | 2026.09.10 | 4 |
| [`elasticsearch`](skills/elasticsearch/) | 框架 | Guides Elasticsearch index and query work: mapping and field-type choice, text versus keyword and multi-fields, analyzers and tokenization, Query DSL… | 2026.09.11 | 9 |
| [`fastapi`](skills/fastapi/) | 框架 | Guides FastAPI service work: APIRouter organisation, Annotated dependency injection including yield-dependency lifetime and exit scope, Pydantic v2… | 2026.09.11 | 12 |
| [`flutter`](skills/flutter/) | 平台 | Guides Flutter and Dart work end to end: widgets and responsive layout, state management (Riverpod 3 Notifier, Bloc/Cubit, ChangeNotifier MVVM)… | 2026.09.10 | 7 |
| [`frontend-design`](skills/frontend-design/) | 任务 | Guides visual and UX quality for web UIs: design direction (typography, color and tokens, layout, spacing, motion), avoiding generic AI-looking… | 2026.09.10 | 12 |
| [`gcp`](skills/gcp/) | 平台 | Guides Google Cloud control-plane and architecture work: gcloud CLI discipline and its silent defaults, the organization/folder/project hierarchy and… | 2026.09.11 | 7 |
| [`git-workflow`](skills/git-workflow/) | 任务 | Guides local git work: branch strategy and naming, worktrees for parallel development, choosing between rebase and merge and paying for the choice… | 2026.09.11 | 12 |
| [`github`](skills/github/) | 平台 | Guides work that needs GitHub the platform | 2026.09.11 | 15 |
| [`go`](skills/go/) | 框架 | Guides Go work end to end: idiomatic language use and useful zero values, interfaces and composition, goroutine lifetime, context cancellation… | 2026.09.11 | 12 |
| [`godot`](skills/godot/) | 平台 | Guides Godot 4 work in GDScript: the scene tree and node lifetime, queue_free versus free and when an instance really becomes invalid, _ready running… | 2026.09.11 | 11 |
| [`graphql`](skills/graphql/) | 框架 | Guides GraphQL schema and operation work: nullability and the non-null error propagation that turns one failing field into a null response, type and… | 2026.09.11 | 12 |
| [`harmonyos`](skills/harmonyos/) | 平台 | Guides HarmonyOS NEXT app work in ArkTS and ArkUI: the arkts-* language restrictions that make legal TypeScript fail to compile, build() purity… | 2026.09.11 | 12 |
| [`java-spring`](skills/java-spring/) | 框架 | Guides Spring Boot work end to end: auto-configuration and configuration properties, Spring MVC versus WebFlux and RFC 9457 error contracts… | 2026.09.11 | 8 |
| [`laravel`](skills/laravel/) | 框架 | Guides Laravel application work on Laravel 12 and 13 with modern PHP: Eloquent modelling and loading strategy (N+1, eager loading, scopes, casts… | 2026.09.11 | 9 |
| [`mcp-server`](skills/mcp-server/) | 任务 | Guides designing and reviewing a Model Context Protocol server: whether a capability is a tool, a resource or a prompt; tool names, schemas and… | 2026.09.11 | 9 |
| [`ml-training`](skills/ml-training/) | 任务 | Trains and fine-tunes models whose weights you control: choosing between SFT, DPO and GRPO from the data actually available, computing the GPU memory… | 2026.09.11 | 9 |
| [`mongodb`](skills/mongodb/) | 框架 | Guides MongoDB work: document modelling (embed versus reference, array growth, bucketing, subset and extended-reference tradeoffs, schema versioning… | 2026.09.11 | 6 |
| [`nodejs-backend`](skills/nodejs-backend/) | 框架 | Engineers Node.js HTTP services: process and request lifecycle, graceful shutdown and connection draining, schema validation at every boundary, error… | 2026.09.11 | 13 |
| [`observability`](skills/observability/) | 任务 | Guides observability for systems already running in production: OpenTelemetry traces, metrics and logs and how they correlate, SDK instrumentation… | 2026.09.11 | 15 |
| [`office`](skills/office/) | 任务 | Creates, edits, reads and converts Word (.docx), PowerPoint (.pptx), Excel (.xlsx) and PDF files — reports, memos, letters, decks, slides… | 2026.09.10 | 19 |
| [`planning`](skills/planning/) | 任务 | Turns a vague request into a plan that can be executed and verified: clarifying requirements into acceptance criteria that are either true or false… | 2026.09.11 | 8 |
| [`postgres`](skills/postgres/) | 框架 | Guides self-managed PostgreSQL work: schema and type selection, constraints, index choice and composite column order, reading EXPLAIN (ANALYZE… | 2026.09.11 | 12 |
| [`python`](skills/python/) | 框架 | Guides modern Python work: uv for projects, tools and PEP 723 single-file scripts; ruff as the single linter and formatter; pyproject.toml… | 2026.09.11 | 17 |
| [`react`](skills/react/) | 框架 | Engineers React 19+ and Next.js App Router (15/16+) code: component architecture and composition, state selection, rendering / re-render / bundle /… | 2026.09.10 | 8 |
| [`react-native`](skills/react-native/) | 平台 | Engineers React Native and Expo apps at the runtime and native boundary: New Architecture (Fabric, Turbo Native Module specs, codegen, the interop… | 2026.09.11 | 7 |
| [`redis`](skills/redis/) | 框架 | Guides Redis itself: choosing a data structure from the access pattern, key-space and TTL design, what each maxmemory-policy really does when memory… | 2026.09.11 | 7 |
| [`security-review`](skills/security-review/) | 任务 | Audits a codebase, feature or threat surface for security defects, defensively and from source | 2026.09.11 | 17 |
| [`skill-authoring`](skills/skill-authoring/) | 元技能 | Authors, reviews, evaluates and publishes Agent Skills — the SKILL.md frontmatter and body plus bundled references/, scripts/ and assets/ | 2026.09.10 | 14 |
| [`solidity-web3`](skills/solidity-web3/) | 框架 | Writes, reviews and hardens Solidity contracts defensively, and proves the result with Foundry | 2026.09.11 | 20 |
| [`supabase`](skills/supabase/) | 框架 | Guides work on Supabase projects: Auth sessions and JWTs, the publishable/secret key split and the legacy anon/service_role pair, @supabase/ssr… | 2026.09.11 | 12 |
| [`svelte`](skills/svelte/) | 框架 | Engineers Svelte 5 and SvelteKit 2 code: runes and the reactivity model ($state, $state.raw, $derived, and the ways $effect gets misused), snippets… | 2026.09.11 | 11 |
| [`tauri`](skills/tauri/) | 平台 | Guides Tauri v2 desktop and mobile application work end to end: tauri.conf.json and platform-specific config overrides, the capabilities and… | 2026.09.11 | 6 |
| [`technical-writing`](skills/technical-writing/) | 任务 | Writes and repairs the documents a project ships to human readers: READMEs, documentation pages, tutorials, how-to guides, reference pages… | 2026.09.11 | 20 |
| [`terraform`](skills/terraform/) | 框架 | Guides Terraform and OpenTofu configuration work: HCL style and expressions, variable, output and local design, module interfaces and version… | 2026.09.11 | 11 |
| [`test-driven-development`](skills/test-driven-development/) | 任务 | Drives implementation and bug fixes test-first in any language or framework: discovers the repository's own test commands before writing anything… | 2026.09.10 | 5 |
| [`typescript`](skills/typescript/) | 框架 | Engineers TypeScript at the type layer and the build layer: modelling a domain so illegal states do not compile (discriminated unions, branded types… | 2026.09.11 | 9 |
| [`unity`](skills/unity/) | 平台 | Guides Unity 6 game work in C#: MonoBehaviour lifecycle and execution order, what Unity's serializer stores and silently drops (Dictionary only from… | 2026.09.11 | 7 |
| [`unreal`](skills/unreal/) | 平台 | Guides Unreal Engine 5 gameplay work in C++ and Blueprint: the UCLASS/UPROPERTY/UFUNCTION reflection contract and what the garbage collector can and… | 2026.09.11 | 10 |
| [`vue`](skills/vue/) | 框架 | Engineers Vue 3 applications: the Composition API with `script setup` SFCs, the reactivity system and every way it silently detaches (reactive… | 2026.09.11 | 10 |
| [`web-testing`](skills/web-testing/) | 任务 | Guides end-to-end testing of web applications in real browsers with Playwright: accessibility-first locators and strict mode, auto-waiting and why a… | 2026.09.11 | 11 |
| [`wechat-miniprogram`](skills/wechat-miniprogram/) | 平台 | Guides WeChat Mini Program work: the two-thread runtime, exparser vs glass-easel frameworks, WebView vs Skyline renderers, the data-update cost model… | 2026.09.11 | 11 |

<!-- catalog:end -->

## 规模

| 项 | 数量 | 数字来自 |
|---|--:|---|
| skill | 53 | `skills/*/SKILL.md` |
| 上游记录（合入 / 仅参考） | 581（436 / 145） | `skills/*/SOURCES.yaml` 的 `upstreams` |
| 不同上游仓库 | 450 | 同上，按 `repo` 去重 |
| references 文件 | 482 | `skills/*/references/*.md` |
| 评测场景 | 244 | `skills/*/evals/evals.json` |
| 自包含脚本 | 20 | `skills/*/scripts/` |

## 仓库结构

```
HyperSkills/
├── skills/<name>/              # 扁平的 skill 目录
│   ├── SKILL.md                # frontmatter + 正文（英文，≤500 行）
│   ├── SOURCES.yaml            # 上游溯源，手工维护
│   ├── NOTICE.md               # 生成，勿改
│   ├── references/*.md         # 按需加载的深度内容（≤600 行，>100 行须带 Contents）
│   ├── evals/evals.json        # 行为评测场景
│   ├── evals/files/            # 评测夹具（不得命名为 SKILL.md）
│   ├── scripts/                # 可选，PEP 723 自包含
│   └── assets/                 # 可选
├── docs/
│   ├── skill-standard.md       # 结构 / 写作 / 溯源规范，校验器逐条对应
│   ├── workflow.md             # 新增与更新 skill 的五阶段流水线
│   └── roadmap.md              # 后续批次主题路线图
├── research/<name>.md          # 候选调研、冲突裁决、基线缺口、评测结果（中文）
├── templates/                  # skill 与 research 脚手架
├── tools/                      # 校验 / 上游检查 / 目录生成 / 评测运行
├── .claude-plugin/             # 生成的 Claude Code 市场清单
└── THIRD_PARTY_NOTICES.md      # 生成的上游许可与署名汇总
```

## 参与维护

新增或更新一个 skill 必须依次走完 [`docs/workflow.md`](docs/workflow.md) 的五个阶段，
跳阶段的产物不接受：

| 阶段 | 做什么 | 产物 |
|---|---|---|
| A 调研 | ≥12 个候选，用 `gh api` 核对 stars / `pushed_at` / license，读原始 `SKILL.md` 再打分 | `research/<name>.md` 候选表，含 REJECT 行与理由 |
| B 审查 + 评测先行 | 通读前 5–8 名、裁决冲突、定合入清单，然后先写评测并跑无 skill 基线 | 合入清单、`evals/evals.json`、基线缺口 |
| C 重写 | 按标准写 `SKILL.md` 与 `references/`，脚本本机跑通，`--pin` 固定上游 commit | skill 正文、`SOURCES.yaml` |
| D 校验 | 静态校验 + 安装冒烟 + 有 skill 评测，与基线逐条对照 | 评测结果表；缺口未填补则回 C |
| E 记录与提交 | 记录「选了谁、拒了谁、冲突怎么裁」，单 skill 单次提交 | 日志 + commit |

常用命令：

```bash
uv run tools/new_skill.py <name> --category platform   # 脚手架（platform|framework|task|meta）
uv run tools/run_evals.py <name> --baseline            # 无 skill 基线
uv run tools/run_evals.py <name>                       # 有 skill
uv run tools/validate_skills.py                        # 静态质量门
uv run tools/check_upstream.py                         # 上游漂移
uv run tools/check_upstream.py --pin <name>            # 固定 commit
uv run tools/build_catalog.py                          # 生成目录与 NOTICE
```

提交前这两条必须绿：

```console
$ uv run tools/validate_skills.py | tail -1
53 skill(s): 0 error(s), 0 warning(s)
$ uv run tools/build_catalog.py --check
catalog is current (53 skill(s))
```

`NOTICE.md`、`THIRD_PARTY_NOTICES.md`、`.claude-plugin/marketplace.json` 与本页的目录表区块
都由 `tools/build_catalog.py` 生成，手工编辑会在 `--check` 处报 stale。

## 许可

- 本仓库自有内容：[MIT](LICENSE)。
- 上游材料的许可与署名：见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与各
  `skills/<name>/NOTICE.md`。
- 专有许可的上游只作参考基准，未复制任何文字、脚本或数据文件。
