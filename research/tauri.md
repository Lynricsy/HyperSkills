# tauri 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`"Tauri v2 agent skill SKILL.md github claude"`
  - GitHub 代码检索：`gh api "search/code?q=tauri+in:path+filename:SKILL.md"`（40 条命中，逐仓核对）
  - GitHub 仓库检索：`gh api "search/repositories?q=tauri+skills+agent&sort=updated"`（噪声极大，绝大多数是
    用 Tauri 写的桌面应用而非 skill 仓库）
  - `github/awesome-copilot`：`git/trees/main?recursive=1` 全树 grep `tauri` → **零命中**，
    GitHub 官方 skill/instruction 集目前不覆盖 Tauri
  - 领域官方组织仓库：`tauri-apps/tauri-docs`（v2.tauri.app 的源）、`tauri-apps/tauri`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- `gh auth status`：`✓ Logged in to github.com account Lynricsy`，全程未触发限流。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | hairyf/skills `skills/tauri`（SKILL.md + 49 个 references） | https://github.com/hairyf/skills | 25 | 2026-08-10 | MIT | Tauri v2 全面：架构/IPC/命令/事件/状态/窗口/capabilities/permissions/scope/CSP/插件/updater/签名/打包/测试/迁移 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | `GENERATION.md` 声明由 `tauri-apps/tauri-docs`（SHA `9bcbf10`）生成，`antfu/skills` 的脚本产出。抽查 `develop-commands`、`security-capabilities`、`features-updater` 三篇与官方逐句对齐，无错；每篇末尾都留 `Source references` 指回官方页面。**主干**。 |
| 2 | nodnarbnitram/claude-code-extensions `.claude/skills/tauri-v2`（497 行 SKILL.md + 5 篇 reference 共 ~1600 行） | https://github.com/nodnarbnitram/claude-code-extensions | 16 | 2026-04-20 | MIT | v2 命令/IPC/state/capabilities/插件/updater/sidecar/tray/deep-link/移动端构建 | 1 | 1 | 3 | 2 | 2 | 9 | INCLUDE | 唯一带「症状 → 根因 → 修法」失败模式表的候选，`lib.rs` 拆分与移动端 `[lib] crate-type` 的解释准确。扣分项：capabilities reference 断言「默认什么都不允许」，与官方「`invoke_handler` 注册的自有命令默认对所有窗口开放」矛盾（见裁决 1）；`plugins/cce-tauri/skills/tauri-v2` 是同一份内容的复制，只取 `.claude/skills` 一份。 |
| 3 | pinkpixel-dev/tauri-skills `skills/tauri-app-builder`（SKILL.md + 6 篇 reference + 1 个审计脚本） | https://github.com/pinkpixel-dev/tauri-skills | 1 | 2026-08-08 | Apache-2.0 | 安全与 IPC 加固、命令面设计、密钥存储、子进程与参数注入、路径与删除、验证清单 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 星数最低但内容最「硬」：命令面「暴露产品操作而非原语」（`run_shell(String)` / `read_any_file(String)` 反例）、Rust 侧必须校验的清单、`capabilities` 不要 `windows: ["*"]`、权限合并语义。抽查三条对照官方 `security/capabilities`、`security/csp`、`develop/calling-rust` 全对。仓库的 `tauri-app-*` 目录是 full-stack-skills 那套的衍生，只取 `tauri-app-builder`。 |
| 4 | tauri-apps/tauri-docs（v2.tauri.app 的源，`src/content/docs/en/**`） | https://v2.tauri.app | 1132 | 2026-09-09 | MIT | 官方全部 v2 文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方权威。`LICENSE` 与 `README` 均为 MIT（"software and associated documentation files"），文档正文可合入。本 skill 每条规则的最终依据；`kind: docs` 的 URL 为 v2.tauri.app，实际取证读的是该仓库 `v2` 分支的 `.mdx` 源。 |
| 5 | full-stack-skills/tauri-skills `skills/*`（52 个 skill） | https://github.com/full-stack-skills/tauri-skills | 9 | 2026-07-29 | Apache-2.0（实读结论，见备注） | 覆盖面清单：52 个主题，从 `tauri-concept`/`tauri-ipc`/`tauri-config` 到每个官方插件一个目录 | 1 | 2 | 1 | 2 | 2 | 8 | INCLUDE（受限） | 主题分类法有价值，正文没有：52 个 SKILL.md 的「常见陷阱」与「使用流程」两节**逐字相同**的机器生成模板（「版本兼容性 / 配置文件格式 / 环境变量 / 依赖冲突 / 性能陷阱」＋「Step 1 环境准备…Step 5 部署上线」），与 Tauri 无关。只取主题清单与它整理的 v2.tauri.app 页面索引，一句正文都不取。 |
| 6 | EpicenterHQ/epicenter `.agents/skills/tauri` | https://github.com/EpicenterHQ/epicenter | 4793 | 2026-09-08 | NOASSERTION → 实读为 AGPL-3.0-or-later | 命令/权限/CSP+devCsp/tauri-specta 绑定/路径 API/原生所有权边界 | 2 | 3 | 3 | 3 | 0 | 11 | INCLUDE 为 reference | 内容质量高（`devCsp` 在 `tauri dev` 下**替换** `csp`、`connect-src` 必须含 `ipc: http://ipc.localhost`、specta 无法为 `tauri::ipc::Response` 生成绑定），但 `LICENSE` 首段即 "Every package under packages/ and apps/ is licensed under AGPL-3.0-or-later"，按本仓库许可政策不得 merged。只用它做覆盖面自检；相同事实改从官方 `security/csp` 与 `develop/calling-rust` 取证。 |
| 7 | Mindrally/skills `tauri-development` | https://github.com/Mindrally/skills | 260 | 2026-09-03 | Apache-2.0 | 「Tauri 开发规范」：TS/Rust 风格、目录结构、TailwindCSS/ShadCN、状态管理 | 1 | 3 | 1 | 0 | 2 | 7 → REJECT | **正确性 0，直接 REJECT**：正文是 Tauri **v1** 的 API——`import { invoke } from '@tauri-apps/api/tauri'`（v2 是 `@tauri-apps/api/core`）、`use tauri::api::path::app_data_dir`（v2 已删除 `api` 模块）、"Use Tauri's security features (CSP, allowlist)"（`allowlist` 在 v2 被 capabilities 取代）。另有一半篇幅是 TailwindCSS/ShadCN 前端规范，越界。 |
| 8 | dchuk/claude-code-tauri-skills `tauri/*`（39 个 skill） | https://github.com/dchuk/claude-code-tauri-skills | 35 | 2026-01-20 | 无许可（API `license: null`） | 按官方文档页面一一对应拆成 39 个 skill，`tauri-capabilities` 单篇 414 行 | 1 | 0 | 3 | 2 | 0 | 6 → REJECT | 内容组织合理，但**已 7.7 个月未推送**（新鲜度 0，量表规定直接 REJECT，非官方不豁免），且无许可文件。它证实的主题划分与候选 1/5 重合，无独有信息。 |
| 9 | Microck/ordinary-claude-skills `skills_all/tauri` | https://github.com/Microck/ordinary-claude-skills | 393 | 2026-09-06 | NOASSERTION | 「从官方文档生成」的 419 行综合 skill | 1 | 3 | 2 | 0 | 0 | 6 → REJECT | **正确性 0**：Windows 签名配置写成 `{"tauri": {"bundle": {"windows": {...}}}}`，即 v1 的 `tauri > bundle` 结构；v2 中 `bundle` 已提到顶层且 `tauri` 键改名 `app`。既然生成自「官方文档」却给出 v1 结构，全篇不可信。 |
| 10 | LevyBytes/AI-SKILL-tauri-develop | https://github.com/LevyBytes/AI-SKILL-tauri-develop | 0 | 2026-06-24 | AGPL-3.0 | 单 SKILL.md + references：v2 开发、`tauri.conf.json`、状态、sidecar、调试、测试 | 0 | 1 | 2 | 2 | 0 | 5 → REJECT | AGPL-3.0 不得 merged，0 星、匿名，且主题被候选 1 完全覆盖，连做 reference 的边际价值都没有。 |
| 11 | majiayu000/claude-skill-registry `skills/**/tauri*`（14 个 tauri 相关目录） | https://github.com/majiayu000/claude-skill-registry | 601 | 2026-09-10 | MIT | 聚合站：`tauri`、`tauri-v2`、`tauri-dev`、`tauri-ipc-developer`、`tauri-command`、`tauri-debugger`… | 0 | 3 | 1 | 1 | 2 | 7 → REJECT | 抓取型聚合仓：同一主题在 `skills/data/`、`skills/design/`、`skills/development/` 下重复出现（`tauri` 出现 3 次、`tauri-v2` 2 次），无原始出处标注、无维护者背书。溯源不可靠，不能作为上游。 |
| 12 | partme-ai/full-stack-skills（候选 5 的母仓，`docs/tauri-skills.md`） | https://github.com/partme-ai/full-stack-skills | 659 | 2026-07-21 | NOASSERTION | 多技术栈 skill 集合的索引与文档 | 1 | 2 | 1 | 2 | 0 | 6 → REJECT | 只是候选 5 的目录索引，无独立内容；根许可未声明。取候选 5 本身即可。 |
| 13 | xiaolai/vmark `.claude/skills/{rust-tauri-backend,tauri-app-dev,tauri-mcp-testing}` | https://github.com/xiaolai/vmark | 561 | 2026-09-09 | ISC | VMark 这个应用自己的后端约定 | 1 | 3 | 1 | 2 | 2 | 9 → MAYBE（未采纳） | 活跃真实项目，但内容是「VMark 的约定」：`references/paths.md` 指向该仓自己的入口文件，规则如「保持改动范围小、不做无关重构」属通用工程常识。可迁移信息量 ≈ 0。 |
| 14 | ifer47/markeron `.cursor/skills/{tauri-config-ipc,cross-platform-tauri-ui}` | https://github.com/ifer47/markeron | 1025 | 2026-09-07 | MIT | MarkerOn 的 config.json ↔ Rust ↔ TS ↔ Vue 分层与命名约定 | 1 | 3 | 2 | 3 | 2 | 11 → MAYBE（未采纳） | 有一条真陷阱（新增配置字段必须带 `#[serde(default)]`，否则旧 `config.json` 反序列化失败），但整篇绑定在该应用的 `config.rs`/Vue 组件上；该陷阱本质是 serde 语义，可直接从 serde 文档取证，不必挂一个应用仓做上游。 |
| 15 | glebis/claude-skills `init-tauri-app` | https://github.com/glebis/claude-skills | 374 | 2026-09-02 | MIT | 按作者个人约定脚手架化 Tauri v2 项目 | 1 | 3 | 1 | 2 | 2 | 9 → REJECT | 个人约定 + agent 绑定：默认 identifier `com.glebkalinin.<name>`、默认目录 `~/ai_projects/<name>`、流程依赖 `AskUserQuestion` 这个特定 agent 工具、可选模块里有作者自己的 Swift sidecar。本仓库禁止 agent 专属绑定，且这些默认值对他人无意义。 |
| 16 | tauri-apps/tauri（框架本仓 `examples/`、`crates/`） | https://github.com/tauri-apps/tauri | 110967 | 2026-09-10 | Apache-2.0 | 框架源码与示例，无 skill | 3 | 3 | — | 3 | 2 | — → 不作为 skill 上游 | 仓内没有 `SKILL.md`/`.agents` 目录（全树 grep 确认）。用于核对 `examples/api/src-tauri/tauri.conf.json` 的 CSP 实例与 `tauri::ipc` 的 API 形状，事实统一记到候选 4 名下。 |
| 17 | `github/awesome-copilot` | https://github.com/github/awesome-copilot | — | — | MIT | — | — | — | — | — | — | — | 无候选 | 全树 grep `tauri` 零命中：`skills/` 与 `instructions/` 都不涉及 Tauri。记此行以免后续批次重复检索。 |

**立项判据核对**：merged 候选中 6 个月内有推送且总分 ≥8 的有 4 个——候选 4（官方文档，14 分）、
候选 1（13 分）、候选 3（12 分）、候选 5（8 分，受限）；候选 2（9 分）推送于 4.7 个月前，同样在窗内。
满足「≥3 个活跃、≥8 分」的常规判据，正常立项。

## 深度审查

### hairyf/skills `skills/tauri`（候选 1，主干）

- 结构：一个 106 行的 SKILL.md，正文只有 9 张「主题 → 描述 → reference」表，指向 49 篇
  `references/*.md`；文件名带分组前缀（`core-`、`start-`、`develop-`、`security-`、
  `best-practices-`、`features-`、`distribute-`、`learn-`、`reference-`），与官方文档的一级导航
  一一对应。每篇 40–110 行，篇末是 HTML 注释形式的 `Source references`。
- frontmatter：`name`/`description`/`metadata.{author,version,source}`。`metadata.source` 是本仓库
  不允许的自定义字段，合入时剥离；`description` 是第三人称、无否定边界，需重写。
- 质量：这是「把官方文档压缩成规则」的正确形态——例如 `develop-commands` 明确写了
  「`lib.rs` 里的命令不能是 `pub`（宏限制），其他模块里用 `pub fn` 并注册为 `module::command`」
  「只有最后一个 `invoke_handler` 生效」「大二进制返回 `tauri::ipc::Response` 绕过 JSON」，
  这三条正是官方文档里容易被读漏的。`security-capabilities` 把「默认目录内所有 capability 文件都启用，
  一旦在 `tauri.conf.json` 写了 `app.security.capabilities` 就只用列出的那些」这条陷阱单独成段。
- 短板：它忠实地「压缩」而不「排序」——49 篇等权重，没有「哪条最常出错」的判断；
  异步命令一节只说「用 `async fn` 免得阻塞主线程」，漏掉了官方那句更关键的
  「**没有** `async` 的命令跑在主线程上，除非写 `#[tauri::command(async)]`」。本 skill 补齐。
- agent 绑定：无。无 harness 变量、无特定 agent 工具名。
- 重叠：与候选 5 的主题清单高度重合，但候选 5 只有标题、它有内容；与候选 2 在 IPC/capabilities/updater
  三处重叠，候选 2 的失败模式表是它没有的。

### nodnarbnitram/claude-code-extensions `tauri-v2`（候选 2）

- 结构：SKILL.md 497 行（超出本仓库 400 行建议值）+ 5 篇 reference。SKILL.md 里塞了
  Quick Start、Critical Rules、失败模式表、`tauri.conf.json` 全量样例、项目结构、`Cargo.toml`、
  常用模式（错误处理 / serde 边界 / state）、检查清单。
- frontmatter：`name`/`description`/`version: 1.0.1`。`version` 不是本仓库的日期版本格式；
  `description` 结尾的 "Triggers on Tauri, src-tauri, invoke, emit, capabilities.json" 是关键词罗列，
  合入时改写成本仓库的 what+when+否定边界形式。
- 质量：最有价值的是 `Known Issues Prevention` 表（10 行「症状 | 根因 | 解法」），把
  「命令未注册 → Command not found」「缺 capability → Permission denied」「`externalBin` 未配 → Sidecar not found」
  「`State<T>` 类型不匹配 → 运行时 panic」串成排障入口，这与官方文档「按主题组织」的方式互补。
  `lib.rs` / `main.rs` 分工那段解释了 why（移动端用 `mobile_entry_point` 替换 `main`），不只是 how。
- 硬伤：开头的 "This skill prevents 8+ common errors and saves ~60% tokens" 与
  「Setup Time ~2 hours → ~30 min」对照表是无依据的自我营销，不可合入。
  `capabilities-reference.md` 的 "By default, **nothing is allowed**" 过度概括（裁决 1）。
- agent 绑定：reference 用相对链接互相跳转（本仓库禁止 reference 间互链），合入后改为单层引用。

### pinkpixel-dev/tauri-skills `tauri-app-builder`（候选 3）

- 结构：182 行 SKILL.md + 6 篇 reference（`security-and-ipc`、`configuration-icons-packaging`、
  `window-lifecycle-and-input`、`native-data-and-background-work`、`tray-and-popup`、`verification`）
  + `scripts/audit_tauri_project.py` + `references/research-sources.md`（列出取证来源，态度可信）。
- frontmatter：`name`/`description`；另有 `agents/openai.yaml`（agent 专属配置，不合入）。
- 质量：唯一从「攻击面」而不是「API 面」组织内容的候选。`security-and-ipc` 的四层威胁模型
  （可被攻陷的 webview 内容 → 运行时授权与 IPC → 特权 Rust 代码 → 操作系统资源）直接支撑了
  本 skill 的 Core rules 排序；「暴露产品操作而非原语」配了三个反例命令签名；
  「不要把密钥放进命令行参数或环境变量」并给出 AskPass + 私有 Unix socket + 一次性 token 的替代路径。
- 短板：密钥/子进程那几节偏离 Tauri 本体（属通用应用安全），本 skill 只取与 IPC 边界直接相关的部分；
  `audit_tauri_project.py` 未采纳，见「最终合入清单」备注。
- 重叠：与候选 6（epicenter）在「Rust 才是信任边界」这一主张上一致，两者独立得出，互为交叉验证。

### full-stack-skills/tauri-skills（候选 5，只取分类法）

52 个目录 = 12 个框架主题（`tauri-concept`、`tauri-config`、`tauri-ipc`、`tauri-window`、`tauri-build`、
`tauri-setup`、`tauri-scaffold`、`tauri-mobile`、`tauri-security`、`tauri-framework-security`、
`tauri-framework-upgrade`、`tauri`）+ 40 个 `tauri-app-*` 插件/能力主题。把这 52 个主题与本 skill 的
章节对照后，发现自己原先漏了两块：**单实例 + deep link 的 argv 传递**（`tauri-app-single-instance`
与 `tauri-app-deep-linking` 必须成对配置）与 **持久化 scope**（`tauri-app-persisted-scope`，
用户通过对话框授权的路径重启后是否还在）。这两块补进了 `references/plugins-ecosystem.md`。
正文一律不取：52 篇的「常见陷阱」「使用流程」两节完全同文，是模板填充。

### EpicenterHQ/epicenter（候选 6，reference）

从一个 4.8k 星的真实 Tauri 应用里长出来的 skill，三条独有观察：
(1) `devCsp` 在 `tauri dev` 下**替换**而不是叠加 `csp`，所以两边都要写全；
(2) 生产构建里 `tauri-codegen` 会为 `frontendDist` 中的内联 `<script>` 注入哈希，
production 的 `script-src` 因此**不需要** `'unsafe-inline'`，而 dev 走 Vite 未哈希的脚本，必须留；
(3) `tauri-specta` 无法为返回 `tauri::ipc::Response` 的命令生成绑定（body 不是 `specta::Type`），
这类命令要单独走一条 `generate_handler!` 并手写 TS 包装。
第 (1)(2) 条已从官方 `security/csp`（"Local scripts are hashed, styles and external scripts are
referenced using a cryptographic nonce"、"At compile time, Tauri appends its nonces and hashes to the
relevant CSP attributes automatically to bundled code and assets"）与 `reference/config` 的 `devCsp`
定义独立取证后写入正文；第 (3) 条属第三方库细节，只在 reference 里一句提示，不作为规则。
AGPL-3.0，未复制任何文字。

## 冲突与裁决

三个仓库上游全是社区，正确性一律以 v2.tauri.app（读的是 `tauri-apps/tauri-docs` 的 `v2` 分支 `.mdx` 源）
为准。以下每条都实读了官方页面。

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 自有命令默认是否被 capabilities 拦住 | 候选 2 `capabilities-reference`：「By default, **nothing is allowed** — 必须通过 capability 文件显式授权」，SKILL.md 也写「即使『安全』操作也要权限」；候选 1 `security-capabilities`：「用 `invoke_handler` 注册的**所有**命令默认对**所有**窗口开放」 | **按候选 1**。正文写成两条独立规则：插件与 core 命令必须在 capability 里显式授权；**自己 `#[tauri::command]` 写的命令默认所有窗口都能调**，要收紧得在 `build.rs` 里用 `AppManifest::commands(&[...])` 声明命令白名单，capability 再决定哪个窗口能调其中哪些。因此「Permission denied」这个症状只会出现在插件/core 命令上——把它当成自有命令调不通的原因会查错方向 | `security/capabilities.mdx`："By default, all commands that you registered in your app (using the `tauri::Builder::invoke_handler` function) are allowed to be used by all the windows and webviews of the app. To change that, consider using `AppManifest::commands`" |
| 2 | 同步命令跑在哪个线程 | 候选 1 `develop-commands`：「用 `async fn` 免得阻塞主线程；异步命令跑在 async runtime 上」——只说了 async 那一半；候选 2：「Never block the main thread - use async for I/O operations」，同样没说清同步命令的归属 | **补齐官方那半句并写成硬规则**：不带 `async` 的命令**就在主线程上执行**，除非标注 `#[tauri::command(async)]`；因此一个同步命令里的阻塞 I/O 会冻住 UI，而不是「可能慢」。异步命令由 `async_runtime::spawn` 派发到独立任务 | `develop/calling-rust.mdx`："Async commands are executed on a separate async task using `async_runtime::spawn`. Commands without the _async_ keyword are executed on the main thread unless defined with _#[tauri::command(async)]_" |
| 3 | 异步命令能不能收借用参数 | 候选 2：「Never use borrowed types (`&str`) in async commands - use owned types」，并把 `async fn bad(name: &str) -> String` 标为「Compile error!」，只给了一条出路；候选 1：「避免借用参数（用 `String`，或返回 `Result<T, ()>` 以满足生命周期约束）」 | **按候选 1，两条出路都写**。官方给的是两个选项：① 换成非借用类型（`&str` → `String`）；② 把返回类型包成 `Result<T, E>`，此路对**所有**类型有效，包括 `State<'_, Data>`——而 `State<'_, T>` 恰恰无法用选项 ① 绕过，所以「只用 owned 类型」这条建议在需要注入 state 的异步命令里是死路。规则写成：异步命令要么全 owned，要么返回 `Result`；注入 `State<'_, T>` 的异步命令**必须**返回 `Result` | `develop/calling-rust.mdx` Async Commands："Option 1: Convert the type, such as `&str` to a similar type that is not borrowed... This may not work for all types, for example `State<'_, Data>`. Option 2: Wrap the return type in a `Result`. This one is a bit harder to implement, but works for all types"；`develop/state-management.mdx`："Note that the return type must be `Result` if you use asynchronous commands" |
| 4 | Tauri v1 vs v2 的前端 API 与安全模型 | 候选 7（Mindrally，Apache-2.0，260★，本波种子之一）：`import { invoke } from '@tauri-apps/api/tauri'`、`use tauri::api::path::app_data_dir`、"Use Tauri's security features (CSP, allowlist)"；候选 9（Microck）：Windows 签名配置写成 `tauri > bundle > windows` | **两个候选整体 REJECT，不作为上游**。v2 中 `@tauri-apps/api/tauri` 改名 `@tauri-apps/api/core`、`api` 模块整体删除（各能力下沉为插件）、`allowlist` 被 capabilities 取代、`tauri` 配置键改名 `app` 且 `bundle` 提到顶层。这类错误不是细节偏差而是版本错位，一条错就说明全篇未经 v2 校验 | `start/migrate/from-tauri-1.mdx`："`@tauri-apps/api/tauri` module renamed to `@tauri-apps/api/core`"、"`api` module removed. Each API module can be found in a Tauri plugin"、"`tauri > allowlist` removed"、"`tauri` key renamed to `app`"、"`tauri > bundle` moved top-level" |
| 5 | `Arc<Mutex<T>>` 要不要用在 managed state 上 | 候选 2 `Common Patterns`：「Use `Mutex<T>` for shared state accessed from multiple commands」（正确但未解释）；社区惯例大量出现 `app.manage(Arc<Mutex<T>>)` | **正文明确写「不要套 `Arc`」**：`State` 内部已经共享所有权，外面再包一层 `Arc` 是纯冗余；真正需要跨线程时 clone `AppHandle` 而不是 clone state。同时补官方那条运行时陷阱：`State<'_, T>` 的类型必须与 `manage` 时**完全一致**，写错是**运行时 panic 而非编译错误**，可用类型别名 `type AppState = Mutex<AppStateInner>` 消除 | `develop/state-management.mdx`："you don't need to use `Arc` for things stored in `State` because Tauri will do this for you"、"If you use the wrong type for the `State` parameter, you will get a runtime panic instead of compile time error" |
| 6 | 平台专属配置文件是合并还是替换 | 三个社区候选都只说「有 `tauri.<platform>.conf.json` 可以做平台差异」，没有一个说明合并语义 | **正文写成硬规则**：平台配置按 JSON Merge Patch (RFC 7396) 合并——对象逐键合并，**数组整体替换**，`app.windows` 这种「元素是对象的数组」也是整条替换，被省略的字段回落到**默认值**而不是基础配置里的值。所以平台文件里要把想保留的字段全部重写一遍 | `develop/configuration-files.mdx`："Objects are merged key by key, but arrays are replaced as a whole... A platform-specific entry replaces the base entry rather than merging into it, so any field you omit falls back to its default instead of the value in your base configuration. Repeat everything you want to keep." |
| 7 | sidecar 用什么名字调用、要哪个权限 | 候选 2 失败模式表：「Sidecar not found → `externalBin` 未配置」（对但不全）；候选 1 `develop-sidecar` 提到 `externalBin` 与 shell 插件权限，未说 Rust 侧与 JS 侧传的名字不同 | **正文写清两侧的不对称**：Rust 的 `app.shell().sidecar(name)` 只吃**文件名**（`binaries/app` → `"app"`）；JS 的 `Command.sidecar(...)` 必须传 `externalBin` 数组里**原样的字符串**（`"binaries/app"`）。另外磁盘上的文件必须带 `-$TARGET_TRIPLE` 后缀（`rustc --print host-tuple` 取本机值，Rust 1.84+），且 `execute()` 与 `spawn()` 对应**不同**权限标识（`shell:allow-execute` / `shell:allow-spawn`），选错权限的表现是运行期被拒而不是构建失败 | `develop/sidecar.mdx`："The `sidecar()` function expects just the filename, NOT the whole path configured in the `externalBin` array"、"The string provided to `Command.sidecar` must match one of the strings defined in the `externalBin` configuration array"、"a binary with the same name and a `-$TARGET_TRIPLE` suffix must exist"、"To run it with `command.spawn()`, you need to change the identifier to `shell:allow-spawn`" |
| 8 | updater 的 `pubkey` / `signature` 能不能填路径 | 候选 2 `updater-distribution-reference`：「Generate keys with `cargo tauri signer generate`, use HTTPS endpoint only」，未提路径限制；其余候选未覆盖 | **正文写死三条**：`pubkey` **不能**是文件路径，必须是公钥内容；静态 JSON 里的 `signature` 也**不能**是路径或 URL，必须是 `.sig` 文件的内容；私钥通过 `TAURI_SIGNING_PRIVATE_KEY` 环境变量传入，**`.env` 文件不生效**。另外 `bundle.createUpdaterArtifacts` 不设就根本不产出更新包与 `.sig`，而 endpoints 只在返回**非 2XX** 时才尝试下一个 URL | `plugin/updater.mdx`："`pubkey` ... It **cannot** be a file path!"、"`signature` The content of the generated `.sig` file... A path or URL does not work!"、"you need to have the private key you generated above in your environment variables. `.env` files do _not_ work!"、"Tauri will only continue to the next url if a non-2XX status code is returned!" |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `tauri-docs` | tauri-apps/tauri-docs（v2.tauri.app） | merged | 每条规则的最终依据：命令与 IPC 语义、异步/主线程模型、错误类型、channel、capabilities 与 permissions/scope 模型、运行时授权、CSP、平台配置合并语义、sidecar 名称与权限、updater 与签名、macOS 公证、v1→v2 迁移表、mock 测试、体积 profile |
| `hairyf-tauri` | hairyf/skills `skills/tauri` | merged | 主题分层与 reference 分组骨架；命令注册细节（`lib.rs` 内不能 `pub`、只有最后一个 `invoke_handler` 生效、大二进制走 `tauri::ipc::Response`）；capability 文件「目录全启用 vs 配置了就只用列出的」；`build.rs` 命令白名单；插件权限自动生成与 `default` 集 |
| `nodnarbnitram-tauri-v2` | nodnarbnitram/claude-code-extensions `.claude/skills/tauri-v2` | merged | 「症状 → 根因 → 修法」排障表的形态与大部分条目；`main.rs`/`lib.rs` 职责切分与移动端 `[lib] crate-type = ["staticlib","cdylib","rlib"]`；serde 边界（camelCase↔snake_case、`Option<T>`、错误类型也要 `Serialize`）；`State<T>` 类型不匹配是运行时 panic |
| `pinkpixel-tauri` | pinkpixel-dev/tauri-skills `skills/tauri-app-builder` | merged | 四层威胁模型与 Core rules 的排序依据；命令面设计原则（暴露产品操作而非 `run_shell(String)` 这类原语）；Rust 侧必须校验的清单；capability 收敛规则（不用 `windows: ["*"]`、按窗口特权分文件、权限合并）；CSP 从最小策略起步而不是加 `unsafe-eval` 消错 |
| `full-stack-skills-tauri` | full-stack-skills/tauri-skills `skills/*` | merged | 52 主题覆盖面清单，用于补齐 single-instance + deep-link 的 argv 配对与 persisted-scope 两处缺口；正文一句未取（生成式模板） |
| `epicenter-tauri` | EpicenterHQ/epicenter `.agents/skills/tauri` | reference | 仅覆盖面自检与交叉验证（`devCsp` 替换语义、production `script-src` 不需要 `'unsafe-inline'`、Rust 才是文件系统信任边界）。AGPL-3.0，未复制任何文字；相同事实改从官方文档取证 |

未采纳的候选（7–15）不进 `SOURCES.yaml`，理由见候选表。
`pinkpixel` 的 `scripts/audit_tauri_project.py` 未采纳也未重写：它做的检查（capability 文件是否存在、
CSP 是否为 null）本 skill 用 `tauri.conf.json` + `capabilities/` 的直读清单就能覆盖，
再加一个需要维护的脚本不划算，所以本 skill 不带 `scripts/`。

## 基线缺口

无 skill（`uv run tools/run_evals.py tauri --baseline`，Claude Opus 5 · medium，四个场景全部
`skill_read=false`）时，各场景未达成的 `expected_behavior`。基线整体很强——它自己起了脚手架
`cargo check`、跑了 V8 实测、用 `web_search` 核了 `createUpdaterArtifacts` 与 RFC 7396——
所以缺口都集中在「需要知道 Tauri 特定语义才能想到」的那几条：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 capabilities/IPC | b2 后半：自有命令默认对所有窗口开放，要靠 `build.rs` 的 `AppManifest::commands` 才受 capability 约束 | 基线只说「v2 里 `plugin::init()` 只注册实现、不授予权限」，把插件命令的规则讲对了，但没有指出与自有命令的**不对称**；全程未出现 `AppManifest`（transcript grep 命中 0）。少了这条，「Permission denied 只可能来自插件/core 命令」这个排障判据就不存在 |
| 1 capabilities/IPC | b7：把 `windows: ["*"]` 换成具体窗口 label | 基线给出的修正 capability 原样保留了 `"windows": ["*"]`，只往里加插件权限。夹具里有 `main` 与 `quicknote` 两个窗口，等于把主窗口的权限一并给了浮动便签窗 |
| 2 命令审查 | b6：用 `thiserror` 错误枚举 + 手写 `Serialize`（必要时 tagged `ErrorKind`）取代 `String` 错误 | 基线把 `unwrap()` 改成 `?` 并统一成 `Result<_, String>`，前端仍然只拿到一句文本，无法按错误种类分支。transcript 里 `thiserror` 的 8 次命中全部是依赖编译日志，不是建议 |
| 2 命令审查 | b7：`read_note` 的调用方路径必须在 Rust 侧规范化并限制在应用自有根目录内 | 基线只让它不再 panic（返回 `Err`），完全没提「webview 不是信任边界」。`canonical` 在 transcript 中命中 0。这条是安全缺口而非风格问题：命令仍可读任意文件 |
| 3 发布配置 | b4 部分：CSP 替代策略要保留 `connect-src` 里的 `ipc: http://ipc.localhost` | 基线正确指出 `csp: null` 关闭了保护，但它给出的替代策略缺 `connect-src`；transcript 里 `ipc.localhost` 的两次命中来自会话中一条外部 advisory 的纠正，不是模型自己得出的。照它最初的策略落盘会直接把 `invoke` 全部拦掉 |
| 3 发布配置 | b5 部分：`app.security.capabilities` 一旦列出就只用列出的那些（否则目录内全部自动启用） | 基线的结论（当前权限集为空）对，但依据写成「空数组语义是『包含所有发现到的 capability』」，与官方语义相反。方向反了的规则在下一步（新建了 capability 文件却没有列进配置）会给出错误建议 |

## 评测结果

模型全部为 `claude-opus-5:medium`（`tools/run_evals.py` 默认，两轮同一模型）。判定方式：人工读
`/tmp/hs-evals/tauri/anthropic-claude-opus-5-medium/{baseline,skill}/<n>/answer.md`，
场景 3 基线的正文写进了它自己的 `.agent-logs/0001-*.md`，一并读了；对「是否真的说了某句话」的
存疑处用 `grep` 查 `events.jsonl` 原始事件流核实。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 capabilities/IPC（`lib.rs` + `default.json` + `projects.ts`，7 条） | claude-opus-5:medium | 无（基线） | false | b1 双 `invoke_handler`、b3 参数大小写、b4 插件权限缺失、b5 克隆副本、b6 同步命令冻 UI（5/7） | b2 只讲对了插件命令那一半，未指出自有命令默认全窗口可调、也未提 `AppManifest::commands`；b7 未达成——修正后的 capability 仍是 `"windows": ["*"]` |
| 1 | claude-opus-5:medium | 有 skill | true | b1–b7 全部（7/7） | b2 明确写出「主人自己写的命令永不受权限影响（经 `invoke_handler` 注册后所有窗口默认可调），所以第一个症状跟权限无关」；b7 拆成 `"windows": ["main"]` 的单窗口 capability 并给出「一个 capability 对应一个权限等级」。额外补了 `target_dir` 未校验与 `app.security.capabilities` 一经设置就只用列出项 |
| 2 命令审查（`commands.rs`，7 条） | claude-opus-5:medium | 无（基线） | false | b1 同步命令跑主线程、b2 `search_notes` 编译失败（`&str`→`String` + 返回 `Result`）、b3 `MutexGuard` 不能跨 await、b4 `Vec<u8>` 被 JSON 编码、b5 `current_cache` 运行期 panic（5/7） | 基线自建脚手架真跑了 `cargo check`，诊断很硬。b6 未达成——统一成 `Result<_, String>`（`events.jsonl` 里 `thiserror` 的 8 次命中全是依赖编译日志）；b7 未达成——只让 `read_note` 不再 panic，未提规范化路径 / 应用自有根目录（`canonical` 命中 0） |
| 2 | claude-opus-5:medium | 有 skill | true | b1–b7 全部（7/7） | b6 换成 `thiserror` 枚举 + 手写 `Serialize`，序列化为 `{ kind, message }`；b7 把 `read_note`/`export_archive` 改成相对路径并在 `app_data_dir()/notes` 下 `canonicalize` + 前缀校验，直接点名「任意文件读取」。并量化了 b4（60 MB → 213 MB 载荷、`serde_json` 编码 181.8 ms vs `ipc::Response` 441 ns），指出 `#[tauri::command(async)]` 不足以解决阻塞 I/O（仍占 runtime 工作线程） |
| 3 发布配置（`tauri.conf.json` + `tauri.macos.conf.json`，8 条） | claude-opus-5:medium | 无（基线） | false | b1 `createUpdaterArtifacts`、b2 `pubkey` 路径 + `TAURI_SIGNING_PRIVATE_KEY`（`.env` 不生效）、b3 `http://` 端点、b6 数组整体替换、b7 sidecar target triple + shell 权限、b8 `installMode: "quiet"` 无法提权（6/8） | 基线用 `web_search` 核实了 `createUpdaterArtifacts` 与 RFC 7396，质量很高。b4 部分——指出 `csp: null` 关闭保护，但替代策略缺 `connect-src`，`ipc.localhost` 的两次命中来自会话中的一条外部 advisory 纠正而非模型自身；b5 部分——结论（当前无权限）对，但把空数组语义写成「包含所有发现到的 capability」，与官方相反 |
| 3 | claude-opus-5:medium | 有 skill | true | b1–b8 全部（8/8） | b4 自行写出「`connect-src` 必须保留 `ipc: http://ipc.localhost`，否则 `invoke` 直接断」并补了 `devCsp` 是**替换**而非叠加；b5 写对了方向「一旦显式设置该字段，只有列出的标识符生效」。b6 进一步指出被替换的窗口条目回落到**默认值**（800×600、无标题）而不是基础文件的值，并给出「单字段平台差异改用 `WebviewWindowBuilder` + `cfg(target_os)`」的替代路径 |
| 4 负例：React 列表卡顿（`OrderTable.tsx`，3 条） | claude-opus-5:medium | 无（基线） | false | 3/3 | 纯 React 作答（`Intl.NumberFormat` 提出行外、`useEffect` 缺依赖、`memo` + 稳定回调、`useDeferredValue`、虚拟滚动排在最后），无任何 Tauri 内容 |
| 4 | claude-opus-5:medium | 有 skill | **false** | 3/3 | 关键：`skill_read == false`，本 skill 未被加载。答复同样只谈 React 与可访问性/列对齐 bug，未出现 `#[tauri::command]`、`tauri.conf.json`、capability 等字样 |

结论：**通过**。基线未达成的 6 条行为（场景 1 的 b2/b7、场景 2 的 b6/b7、场景 3 的 b4/b5）在有 skill
时全部达成，其中场景 2 的 b7 与场景 3 的 b4 是实际安全后果（任意文件读取、CSP 策略把 `invoke`
全部拦掉），不是措辞差异；场景 3 的 b5 更是把基线**方向相反**的规则纠正了过来。负例
`skill_read == false`，边界没有过度触发。

## 备注

### full-stack-skills/tauri-skills 的许可实读结论

GitHub API 报 `NOASSERTION`。逐文件实读后确认这是**根 `LICENSE` 文件放错了内容**导致的误判：

- 根 `LICENSE` 的正文是一份 `# Third-Party Notices`，逐条列的是 **imageio 2.37.0 / imageio-ffmpeg 0.6.0**
  等 Python 包的 BSD 2-Clause 声明——与 Tauri 毫无关系，显然是从别的项目误拷进来的，
  GitHub 的许可探测器因此认不出 SPDX id。
- `README.md` 明确声明 `## 📄 License — Apache 2.0 — see [LICENSE](LICENSE)`，徽章同为 Apache 2.0。
- **52 个 skill 目录各自带一份 `skills/<name>/LICENSE.txt`**，抽查 `tauri-app-develop`、`tauri-ipc` 两份，
  内容是完整、未改动的 Apache License 2.0 全文（含标准 appendix 与
  `Copyright [yyyy] [name of copyright owner]` 占位）。

结论：**按 Apache-2.0 处理，`relation: merged`**，因为许可意图由 README 与每个 skill 目录内的完整
Apache-2.0 文本双重声明，根 `LICENSE` 只是内容放错。`SOURCES.yaml` 的 `notes` 记下这一事实，
并注明只取了主题清单、正文（机器生成的「常见陷阱 / 使用流程」模板）一句未用。

### 其他许可注意

- `tauri-apps/tauri-docs` 的 `LICENSE` 与 `README` 均为 MIT，措辞覆盖 "software and **associated
  documentation files**"，所以官方文档正文可作 `merged`（`kind: docs`，URL 填 v2.tauri.app，
  实际取证读的是该仓库 `v2` 分支的 `.mdx` 源）。
- `EpicenterHQ/epicenter` 的 API 值是 `NOASSERTION`；`LICENSE` 首段为
  "Every package under packages/ and apps/ is licensed under AGPL-3.0-or-later"，
  按本仓库政策落到 `relation: reference`。
- `LevyBytes/AI-SKILL-tauri-develop`（AGPL-3.0）、`dchuk/claude-code-tauri-skills`（无许可）
  都已因内容或新鲜度先行 REJECT，不涉及许可处理。

### 未来同步时要盯的上游

- `hairyf/skills`：`skills/tauri` 是脚本从 `tauri-apps/tauri-docs` 再生成的，
  `GENERATION.md` 里的源 SHA（本次 `9bcbf1078f171ca6558c72df03c1e1f152205f42`，生成日 2026-01-30）
  是判断它是否落后官方文档的直接指标。若它长期不再生成，应切换成直接跟踪 `tauri-apps/tauri-docs`。
- `nodnarbnitram/claude-code-extensions`：本次推送距今 4.7 个月，已接近 6 个月 REJECT 线；
  下次同步若仍无推送则降为 reference。
- Tauri 官方：`removeUnusedCommands`（需 `tauri@2.4`/`tauri-build@2.1`/`tauri-cli@2.4`）与
  `createUpdaterArtifacts`（官方声明 **v3 将移除**，届时需改写 updater 一节）是两个已知的版本敏感点。

### 放弃的方向

- 不写「Tauri vs Electron 选型」：属决策文档而非可执行规则，且本 skill 的否定边界已排除 Electron。
- 不写移动端（Android/iOS）的完整链路：Tauri 移动端的构建与签名与 `android`/`apple` 两个 skill
  重叠严重，本 skill 只保留「桌面代码要在移动端可编译」的那几条约束（`lib.rs` 入口、
  `crate-type`、capability 的 `platforms` 字段、插件是否有移动端实现）。
- 不带 `scripts/`：见「最终合入清单」末尾。
