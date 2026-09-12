<h1>
  <picture>
    <source media="(max-width: 600px)" srcset="docs/assets/hero-mobile.svg">
    <img src="docs/assets/hero.svg" width="1000" alt="HyperSkills：把零散经验，编成完整技能。给 AI 编程助手的整合型技能库，精编重写、评测先行、来源可溯。">
  </picture>
</h1>

<p align="center">
  <a href="#skill-目录"><img src="docs/assets/badge-skills.svg" height="28" alt="技能数量"></a>
  <a href="THIRD_PARTY_NOTICES.md"><img src="docs/assets/badge-upstreams.svg" height="28" alt="上游记录数量，包含重写合入与参考对齐"></a>
  <a href="THIRD_PARTY_NOTICES.md"><img src="docs/assets/badge-repos.svg" height="28" alt="去重后的来源仓库数量"></a>
</p>

<p align="center">
  <strong><a href="#安装">开始安装</a></strong> &nbsp; / &nbsp;
  <strong><a href="#skill-目录">浏览技能</a></strong> &nbsp; / &nbsp;
  <a href="docs/skill-standard.md">编写标准</a> &nbsp; / &nbsp;
  <a href="docs/workflow.md">五阶段流水线</a>
</p>

<p align="center">
  <sub>活跃开发中，暂无 CI。<a href="LICENSE">MIT 许可</a> · 由 <a href="https://github.com/Lynricsy">@Lynricsy</a> 维护 · <a href="https://github.com/Lynricsy/HyperSkills/issues">反馈问题</a></sub>
</p>

> **skill 会以 agent 的全部权限运行。** 装之前把 `SKILL.md` 和 `scripts/` 读一遍——
> 这条对本仓库和任何第三方 skill 都一样。

## 这是什么

一个 skill 对应 agent 真正会遇到的一整类任务，而不是对某个上游仓库的搬运。

- **一个生态一个 skill。** `apple` 一个 skill 同时覆盖 SwiftUI 数据流、Swift 6 严格并发、
  SwiftData 与 Instruments，不切成 `swiftui` / `swift-concurrency` / `swiftdata` 三个——
  它们属于同一次任务，应当同时在场。
- **精编重写，不是聚合。** 60 个 `SOURCES.yaml` 里共 695 条上游记录（485 条内容重写合入、
  210 条仅阅读对齐）：514 条仓库型来自 370 个不同仓库，另有 181 条官方文档与 RFC。合入时统一
  术语、裁决冲突、删掉模型本来就会的常识，只留边缘情况、静默失败、版本差异与易错点。
- **先有评测再有正文。** 动笔前先写评测场景（每个 skill ≥3 个，含 ≥1 个「近似但不该触发」
  的负例）并跑无 skill 基线；默认以填补真实基线缺口作为增益门，没有差异就不宣称有效。
  当前 277 个场景；波次11在强基线后按用户明确决定继续建设，内容交付与增益结论分开记录。
- **上游可追溯。** 514 条仓库型记录各自固定合入时的 40 位 commit，`tools/check_upstream.py`
  能列出自那次 commit 以来上游在被引用路径下的全部变更，区分「仓库动了但引用路径没动」和
  「真的变了」；181 条文档型（`kind: docs`）只记 URL，工具报 `manual check`，靠人工比对。

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

# 装全部 60 个
npx skills@latest add Lynricsy/HyperSkills --skill '*' --agent universal --copy --yes
```

两条都装到项目内的 `./.agents/skills/`；加 `-g` 改装到用户级。

### Claude Code 插件市场

```
/plugin marketplace add Lynricsy/HyperSkills
/plugin install technical-writing@hyperskills
/plugin install all@hyperskills
```

插件名与 skill 目录名一致，`all` 是全部 60 个。清单是 `.claude-plugin/marketplace.json`。

### 手工复制

```bash
git clone https://github.com/Lynricsy/HyperSkills.git
mkdir -p ~/.agents/skills
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

之后不需要手动指定：agent 根据 skill 名称和一句简短的 `description` 选择技能。
description 只写任务与关键技术名；详细能力、适用范围和否定边界留在选中后才加载的正文，
不让全部技能的使用说明常驻上下文。篇幅要求见[编写标准](docs/skill-standard.md#11-字段约束)。

## skill 目录

60 个：框架 23、平台 18、任务 18、元技能 1。下表由 `tools/build_catalog.py` 生成。

<!-- catalog:start -->

| Skill | 类别 | 说明 | 版本 | 上游数 |
|---|---|---|---|---|
| [`ai-engineering`](skills/ai-engineering/) | 任务 | Builds LLM applications, prompts, tool-using agents, RAG pipelines and model evaluations | 2026.09.12 | 13 |
| [`android`](skills/android/) | 平台 | Develops native Android apps with Kotlin, Jetpack Compose and Gradle | 2026.09.12 | 11 |
| [`api-design`](skills/api-design/) | 任务 | Designs REST API contracts, resource models, pagination and OpenAPI specifications | 2026.09.12 | 19 |
| [`apple`](skills/apple/) | 平台 | Develops Apple platform apps with Swift, SwiftUI and UIKit | 2026.09.12 | 15 |
| [`astro`](skills/astro/) | 框架 | Builds Astro sites with islands, content collections and server rendering | 2026.09.12 | 6 |
| [`aws`](skills/aws/) | 平台 | Manages AWS architecture, IAM, cloud services, deployments and costs | 2026.09.12 | 8 |
| [`azure`](skills/azure/) | 平台 | Manages Azure architecture, Bicep deployments, identity and cloud services | 2026.09.12 | 13 |
| [`chrome-extension`](skills/chrome-extension/) | 平台 | Builds Chrome extensions with Manifest V3, service workers and content scripts | 2026.09.12 | 10 |
| [`cloudflare`](skills/cloudflare/) | 平台 | Builds on Cloudflare Workers, Durable Objects, storage services and Wrangler | 2026.09.12 | 8 |
| [`code-review`](skills/code-review/) | 任务 | Reviews code changes and pull-request diffs, or evaluates review feedback | 2026.09.12 | 9 |
| [`containers`](skills/containers/) | 平台 | Builds Docker images and configures Compose, Kubernetes, Helm and container security | 2026.09.12 | 13 |
| [`cpp`](skills/cpp/) | 框架 | Develops C++ code with CMake, ownership, concurrency and memory safety | 2026.09.12 | 10 |
| [`csharp-dotnet`](skills/csharp-dotnet/) | 框架 | Develops C# and .NET applications with ASP.NET Core, Blazor and Entity Framework | 2026.09.12 | 10 |
| [`data-analysis`](skills/data-analysis/) | 任务 | Analyzes tabular datasets with pandas, Polars and DuckDB for reliable conclusions | 2026.09.12 | 14 |
| [`debugging`](skills/debugging/) | 任务 | Diagnoses and fixes reproducible bugs, regressions, failures and performance problems | 2026.09.12 | 4 |
| [`elasticsearch`](skills/elasticsearch/) | 框架 | Designs and tunes Elasticsearch mappings, queries, search relevance and indexes | 2026.09.12 | 9 |
| [`fastapi`](skills/fastapi/) | 框架 | Builds Python APIs with FastAPI, Pydantic, dependency injection and async request handling | 2026.09.12 | 12 |
| [`flutter`](skills/flutter/) | 平台 | Develops cross-platform Flutter apps with Dart, widgets and state management | 2026.09.12 | 7 |
| [`frontend-design`](skills/frontend-design/) | 任务 | Designs and audits web interfaces for visual quality, usability and accessibility | 2026.09.12 | 12 |
| [`gcp`](skills/gcp/) | 平台 | Manages Google Cloud architecture, IAM, Cloud Run, GKE and cloud services | 2026.09.12 | 7 |
| [`generative-media`](skills/generative-media/) | 任务 | Integrates AI image, video, speech and music generation or transcription models | 2026.09.12 | 14 |
| [`git-workflow`](skills/git-workflow/) | 任务 | Manages local Git branches, worktrees, commits, merges, conflicts and history recovery | 2026.09.12 | 12 |
| [`github`](skills/github/) | 平台 | Manages GitHub pull requests, issues, Actions workflows, releases and repository settings | 2026.09.12 | 15 |
| [`go`](skills/go/) | 框架 | Develops Go code with goroutines, modules, testing and performance profiling | 2026.09.12 | 12 |
| [`godot`](skills/godot/) | 平台 | Develops Godot games with GDScript, scenes, nodes and engine APIs | 2026.09.12 | 11 |
| [`graphql`](skills/graphql/) | 框架 | Designs GraphQL schemas, operations, resolvers, federation and query controls | 2026.09.12 | 12 |
| [`harmonyos`](skills/harmonyos/) | 平台 | Develops HarmonyOS NEXT apps with ArkTS, ArkUI and DevEco tooling | 2026.09.12 | 12 |
| [`java-spring`](skills/java-spring/) | 框架 | Develops Java services with Spring Boot, Spring Security and Spring Data JPA | 2026.09.12 | 8 |
| [`laravel`](skills/laravel/) | 框架 | Develops Laravel PHP applications with Eloquent, queues, Blade and Livewire | 2026.09.12 | 9 |
| [`linux-ops`](skills/linux-ops/) | 平台 | Operates Linux hosts with systemd, permissions, networking, storage and backup recovery | 2026.09.12 | 13 |
| [`mcp-server`](skills/mcp-server/) | 任务 | Builds Model Context Protocol servers with tools, resources, transports and authorization | 2026.09.12 | 9 |
| [`media-processing`](skills/media-processing/) | 任务 | Processes existing video, audio and images with ffmpeg and deterministic image tools | 2026.09.12 | 24 |
| [`ml-training`](skills/ml-training/) | 任务 | Trains and fine-tunes model weights with LoRA, distributed training and GPU optimization | 2026.09.12 | 9 |
| [`mongodb`](skills/mongodb/) | 框架 | Designs and tunes MongoDB documents, aggregations, indexes and cluster operations | 2026.09.12 | 6 |
| [`nodejs-backend`](skills/nodejs-backend/) | 框架 | Builds Node.js HTTP services with Fastify, NestJS, Hono or Express | 2026.09.12 | 13 |
| [`observability`](skills/observability/) | 任务 | Instruments production systems with OpenTelemetry traces, metrics, logs, SLOs and alerts | 2026.09.12 | 15 |
| [`office`](skills/office/) | 任务 | Creates, edits and converts Word, PowerPoint, Excel and PDF documents | 2026.09.12 | 19 |
| [`planning`](skills/planning/) | 任务 | Turns requirements into executable plans with dependencies and verifiable acceptance criteria | 2026.09.12 | 8 |
| [`postgres`](skills/postgres/) | 框架 | Designs and tunes PostgreSQL schemas, queries, indexes, transactions and operations | 2026.09.12 | 12 |
| [`python`](skills/python/) | 框架 | Develops Python code with uv, pytest, typing, asyncio and packaging | 2026.09.12 | 17 |
| [`react`](skills/react/) | 框架 | Develops React and Next.js web applications, components and server rendering | 2026.09.12 | 8 |
| [`react-native`](skills/react-native/) | 平台 | Develops React Native and Expo mobile apps, navigation and native integrations | 2026.09.12 | 7 |
| [`redis`](skills/redis/) | 框架 | Designs and operates Redis data structures, caching, streams and clusters | 2026.09.12 | 7 |
| [`rust`](skills/rust/) | 框架 | Develops Rust code with ownership, lifetimes, async, Cargo and safe FFI | 2026.09.12 | 17 |
| [`security-review`](skills/security-review/) | 任务 | Audits codebases for security vulnerabilities, access-control flaws and trust-boundary risks | 2026.09.12 | 17 |
| [`skill-authoring`](skills/skill-authoring/) | 元技能 | Authors, reviews and evaluates Agent Skills and their SKILL.md files | 2026.09.12 | 14 |
| [`solidity-web3`](skills/solidity-web3/) | 框架 | Develops and audits Solidity smart contracts with Foundry security testing | 2026.09.12 | 20 |
| [`sqlite`](skills/sqlite/) | 框架 | Designs and operates embedded SQLite databases, transactions, WAL and backups | 2026.09.12 | 22 |
| [`supabase`](skills/supabase/) | 框架 | Builds Supabase applications with Auth, RLS, Storage, Realtime and Edge Functions | 2026.09.12 | 12 |
| [`svelte`](skills/svelte/) | 框架 | Develops Svelte and SvelteKit applications with runes, routing and server data flows | 2026.09.12 | 11 |
| [`tauri`](skills/tauri/) | 平台 | Builds Tauri apps with Rust IPC, capabilities, plugins and desktop packaging | 2026.09.12 | 6 |
| [`technical-writing`](skills/technical-writing/) | 任务 | Writes and edits READMEs, documentation, tutorials, architecture decisions and changelogs | 2026.09.12 | 20 |
| [`terraform`](skills/terraform/) | 框架 | Manages infrastructure as code with Terraform or OpenTofu modules, state and providers | 2026.09.12 | 11 |
| [`test-driven-development`](skills/test-driven-development/) | 任务 | Drives implementation and bug fixes through test-first red-green-refactor cycles | 2026.09.12 | 5 |
| [`typescript`](skills/typescript/) | 框架 | Designs TypeScript types, fixes type errors and configures typed package builds | 2026.09.12 | 9 |
| [`unity`](skills/unity/) | 平台 | Develops Unity games with C#, engine APIs, rendering and asset workflows | 2026.09.12 | 7 |
| [`unreal`](skills/unreal/) | 平台 | Develops Unreal Engine gameplay with C++, Blueprints and engine APIs | 2026.09.12 | 10 |
| [`vue`](skills/vue/) | 框架 | Develops Vue and Nuxt applications with Composition API, Pinia and routing | 2026.09.12 | 10 |
| [`web-testing`](skills/web-testing/) | 任务 | Tests web applications in real browsers with Playwright end-to-end automation | 2026.09.12 | 11 |
| [`wechat-miniprogram`](skills/wechat-miniprogram/) | 平台 | Develops WeChat Mini Programs with WXML, WXSS, Skyline, uni-app and Taro | 2026.09.12 | 11 |

<!-- catalog:end -->

## 规模

| 项 | 数量 | 数字来自 |
|---|--:|---|
| skill | 60 | `skills/*/SKILL.md` |
| 上游记录（合入 / 仅参考） | 695（485 / 210） | `skills/*/SOURCES.yaml` 的 `upstreams` |
| 其中仓库型（固定 commit） | 514 | 同上，`kind: repo` |
| 不同上游仓库 | 370 | 同上，按 `repo` 去重 |
| 其中文档型（人工比对） | 181 | 同上，`kind: docs` |
| references 文件 | 514 | `skills/*/references/*.md` |
| 评测场景 | 277 | `skills/*/evals/evals.json` |
| 脚本入口 | 12 | `skills/*/scripts/` 根目录的 `.py`、`.sh`、`.mjs`，不含依赖文件或辅助模块 |

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
│   ├── roadmap.md              # 后续批次主题路线图
│   └── assets/logo.svg         # README 首屏标记（透明底，单份资产适配明暗主题）
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

波次11范围：`rust`、`data-analysis`、`linux-ops`、`sqlite`、`cpp`。此前共复核75个候选、
运行25个无skill场景；用户获知强基线后明确要求正式构建。有skill对照仍使用
`openai/gpt-5.6-sol`、`medium`，保留原场景与原始故障，不把基线已具备的能力重述为增益。
各主题随正文、4份参考和固定版本来源逐项提交；来源、逐项证据与本批决策见
[波次11建设记录](docs/roadmap.md)。已纳入目录的主题只在 `skills/<name>/evals/` 维护评测。

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
60 skill(s): 0 error(s), 0 warning(s)
$ uv run tools/build_catalog.py --check
catalog is current (60 skill(s))
```

`NOTICE.md`、`THIRD_PARTY_NOTICES.md`、`.claude-plugin/marketplace.json`、本页的目录表区块
与 `docs/assets/badge-*.svg` 统计徽章都由 `tools/build_catalog.py` 生成，
手工编辑会在 `--check` 处报 stale。徽章分别统计 skill 数量、上游记录总数与去重后的来源仓库数。

## 许可

- 本仓库自有内容：[MIT](LICENSE)。
- 上游材料的许可与署名：见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与各
  `skills/<name>/NOTICE.md`。
- 专有许可的上游只作参考基准，未复制任何文字、脚本或数据文件。
