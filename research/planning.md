# planning 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`agent skill "SKILL.md" implementation plan spec-driven development planning github`
  - 种子仓库直接列树：`gh api repos/<o>/<r>/git/trees/<ref>?recursive=1`，再按
    `plan|brainstorm|spec|prd|requirement|triage|decompos|breakdown|adr|decision|roadmap|scope`
    过滤路径，避免凭记忆写路径。
  - 领域官方组织仓库：`github/awesome-copilot`（418 个 `skills/*/SKILL.md`）、`github/spec-kit`、
    `anthropics/skills`
  - 公认专家：`obra/superpowers`、`mattpocock/skills`、`addyosmani/agent-skills`
  - `VoltAgent/awesome-agent-skills`（索引型，只用于发现，不作上游）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 通过，账号 Lynricsy，5000 次/小时配额；全程未用匿名 API）
- 许可**实读 LICENSE 文件**而非只信 `spdx_id`：
  - `obra/superpowers` → `LICENSE` 首行 `MIT License / Copyright (c) 2025 Jesse Vincent` ✅
  - `mattpocock/skills` → `MIT License / Copyright (c) 2026 Matt Pocock` ✅
  - `github/awesome-copilot` → `MIT License / Copyright GitHub, Inc.` ✅
  - `github/spec-kit` → API `MIT`，仓库根 `LICENSE` 实读为 MIT ✅
  - `addyosmani/agent-skills` → `MIT License` ✅
  - `NeoLabHQ/context-engineering-kit` → `COPYING`/`LICENSE` 实读为 **GNU GPL v3**
    → 按 `docs/roadmap.md` 许可规则，**只能 `relation: reference`**，不得复制任何文字。
  - `anthropics/skills` → 仓库根无统一 LICENSE（API `license: null`），每个 skill 目录自带
    `LICENSE.txt`，多为专有。本 skill 最终**没有**采用该仓库任何路径（它没有 planning 类
    skill，见候选表 #23），因此不涉及专有许可复制风险。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | obra/superpowers `skills/writing-plans` | https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md | 284825 | 2026-09-11 | MIT | 计划文档的形状：文件结构先行、任务右尺寸、每步带命令与预期输出、Interfaces 的 Consumes/Produces、No-Placeholders 清单、自审三查 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 全仓最具体的「计划长什么样」来源。`No Placeholders` 与 `Interfaces` 两节是可证伪的产物形状，直接构成本 skill 的核心不变量 |
| 2 | obra/superpowers `skills/brainstorming` | https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md | 284825 | 2026-09-11 | MIT | spike/bounded/architectural 三档分流、单向棘轮、approval gate、2-3 approaches、spec 自审 4 查、一次一个问题 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 唯一把「该做多少流程」写成可判定分类器的候选；`bounded` 的判据（要改的 flow 是否已在本仓可读）是可证伪的 |
| 3 | addyosmani/agent-skills `skills/planning-and-task-breakdown` | https://github.com/addyosmani/agent-skills/blob/main/skills/planning-and-task-breakdown/SKILL.md | 93429 | 2026-09-08 | MIT | 依赖图、纵向切片 vs 横向切片、任务模板（验收 + 验证命令 + 依赖 + 文件）、XS–XL 尺寸表与拆分触发条件、并行度三分类、不覆盖未完成计划 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 并行度判定（safe / sequential / needs-coordination）与「先定契约再并行」是本 skill 要求的判断；覆盖未完成计划那条是真实事故模式 |
| 4 | addyosmani/agent-skills `skills/spec-driven-development` | https://github.com/addyosmani/agent-skills/blob/main/skills/spec-driven-development/SKILL.md | 93429 | 2026-09-08 | MIT | Phase 0 capability map（模块表 + 构建顺序 + 无环）、ASSUMPTIONS 显式清单、Boundaries 三档（always / ask first / never） | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | `ASSUMPTIONS I'M MAKING` 是本 skill 最重要的一条产物形状：未声明的假设是返工头号来源 |
| 5 | github/awesome-copilot `skills/create-implementation-plan` | https://github.com/github/awesome-copilot/blob/main/skills/create-implementation-plan/SKILL.md | 38883 | 2026-09-10 | MIT | 标识符体系（REQ/CON/TASK/ALT/DEP/RISK/ASSUMPTION）、声明唯一性与引用的区分、可 grep 的唯一性检查、Alternatives 节 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 官方（GitHub）。「每个标识符声明恰好一次，引用不限」这条可用 `grep \| sort \| uniq -d` 机械验证——正好是本 skill 需要的可证伪性 |
| 6 | github/awesome-copilot `skills/create-architectural-decision-record` | https://github.com/github/awesome-copilot/blob/main/skills/create-architectural-decision-record/SKILL.md | 38883 | 2026-09-10 | MIT | ADR 结构：Status/Context/Decision/正负后果/Alternatives 带 Rejection Reason、`supersedes`/`superseded_by`、`adr-NNNN-slug.md` | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 「被否方案必须写驳回理由」是把取舍记录变成可检查产物的关键；supersede 链解决 ADR 过期问题 |
| 7 | github/spec-kit `docs/guides/evolving-specs.md`、`docs/concepts/spec-persistence.md`、`docs/concepts/complex-features.md` | https://github.com/github/spec-kit | 135262 | 2026-09-10 | MIT | 三种 spec 持久化模型（flow-forward / living / flow-back）、改 spec 必须回流下游产物、`analyze` 式一致性检查在恢复实现前跑 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 官方。本 skill「计划修订」一节的骨架：把「发现与计划不一致时先改哪份文件」写成三种明确策略而不是随缘 |
| 8 | obra/superpowers `skills/verification-before-completion` | https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md | 284825 | 2026-09-11 | MIT | Evidence-before-claim 门；`Requirements met` 需逐行清单而非「测试过了」；不信任子代理的成功自述，查 VCS diff | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 执行跟踪一节的收尾门。`Agent completed → VCS diff shows changes` 对并行执行计划是硬需求 |
| 9 | mattpocock/skills `skills/engineering/to-spec` | https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md | 259035 | 2026-09-04 | MIT | spec 模板（Problem/Solution/User Stories/Implementation Decisions/Testing Decisions/Out of Scope）、**禁止在 spec 写文件路径与代码片段**（会过期）、seam 先行、原型片段例外 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE | 「spec 不写路径、plan 才写路径」这条与候选 1 形成清晰分层，是本 skill 的裁决点之一 |
| 10 | mattpocock/skills `skills/engineering/triage` | https://github.com/mattpocock/skills/blob/main/skills/engineering/triage/SKILL.md | 259035 | 2026-09-04 | MIT | needs-info/ready-for-agent 状态机、**冗余检查**（按领域概念搜是否已实现）、**先前驳回检查**（`.out-of-scope/`）、bug 必须先复现再澄清、needs-info 模板保存已确立事实 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE | 「澄清之前先查是否已实现 / 是否已被驳回」是最省返工的一步，其他候选都没有。状态机本身按边界归 `github` |
| 11 | obra/superpowers `skills/executing-plans` | https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md | 284825 | 2026-09-11 | MIT | 执行前批判性复读计划、遇阻立即停（缺依赖/测试失败/指令不明/反复验证失败）、什么情况回到重新规划 | 2 | 3 | 2 | 3 | 2 | 12 | INCLUDE | 「什么时候必须停下来重新规划」的四个触发条件来源；其余（worktree、finishing-branch）按边界归 `git-workflow` |
| 12 | obra/superpowers `skills/subagent-driven-development` | https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md | 284825 | 2026-09-11 | MIT | 每任务一个新鲜子代理、任务间审查、子代理只见自己那一个任务因此计划必须自包含 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 只取一条推论：**执行者只读自己那一段**，所以计划的每个任务必须自带接口签名与验收命令。其余调度机制不合入（本仓 `task` 工具语义不同） |
| 13 | github/awesome-copilot `skills/create-specification` | https://github.com/github/awesome-copilot/blob/main/skills/create-specification/SKILL.md | 38883 | 2026-09-10 | MIT | AC-NNN 用 Given-When-Then、要求/约束/建议三者显式区分、自包含不依赖外部上下文 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 只取两条：Given-When-Then 形式的验收标准、以及「requirement / constraint / guideline 必须分开标注」 |
| 14 | github/awesome-copilot `skills/update-implementation-plan` | https://github.com/github/awesome-copilot/blob/main/skills/update-implementation-plan/SKILL.md | 38883 | 2026-09-10 | MIT | 在既有计划上做增量修订（保留已完成任务的标记与日期，只追加/改写未完成项） | 3 | 3 | 2 | 2 | 2 | 12 | MAYBE | 与候选 7 重叠且更机械；只取「修订不得清空已完成记录」一条，其余用 spec-kit 的三模型 |
| 15 | github/awesome-copilot `skills/structured-autonomy-plan` | https://github.com/github/awesome-copilot/blob/main/skills/structured-autonomy-plan/SKILL.md | 38883 | 2026-09-10 | MIT | 计划步骤 = PR 内的单个 commit；`[NEEDS CLARIFICATION]` 标记 + 强制暂停等反馈；研究到 80% 置信度即停 | 3 | 3 | 2 | 2 | 2 | 12 | MAYBE | 只取 `[NEEDS CLARIFICATION]` 标记法（把未知留在产物里而不是脑子里）。`#tool:runSubagent` / ResizeMe 等 harness 与项目残留必须剥离 |
| 16 | NeoLabHQ/context-engineering-kit `plugins/sdd` | https://github.com/NeoLabHQ/context-engineering-kit | 1685 | 2026-08-26 | **GPL-3.0** | create-ideas → brainstorm → plan-task → add-task → implement-task → review 的 skill 切分，`.specs/{analysis,reports,research}` 目录布局 | 1 | 2 | 2 | 2 | 0 | 7 | MAYBE → **reference** | 许可 GPL-3.0，与本仓 MIT 不兼容：**只读主题清单判断覆盖面**，不复制任何文字。它的 skill 切分证明「澄清/计划/执行跟踪」确实是同一条链，支持本 skill 不拆分的决定 |
| 17 | github/awesome-copilot `skills/breakdown-plan` | https://github.com/github/awesome-copilot/blob/main/skills/breakdown-plan/SKILL.md | 38883 | 2026-09-10 | MIT | Epic>Feature>Story>Enabler>Test 层级、GitHub issue 模板、里程碑、story points、Kanban 自动化 | 3 | 3 | 1 | 2 | 2 | 11 | REJECT | 范围冲突：这是项目管理排期 + 在 GitHub 上批量建 issue，本 skill 的 `description` 明确排除前者，后者归 `github`。另外 509 行里绝大多数是 issue 模板样板，不是判断 |
| 18 | github/awesome-copilot `skills/breakdown-feature-prd` | https://github.com/github/awesome-copilot/blob/main/skills/breakdown-feature-prd/SKILL.md | 38883 | 2026-09-10 | MIT | 产品 PRD：用户画像、业务价值、KPI、`/docs/ways-of-work/plan/` 目录约定 | 3 | 3 | 1 | 2 | 2 | 11 | REJECT | 产品需求文档与路线图，不是工程计划。`description` 已显式排除产品路线图 |
| 19 | github/awesome-copilot `skills/prd` | https://github.com/github/awesome-copilot/blob/main/skills/prd/SKILL.md | 38883 | 2026-09-10 | MIT | 同上，更偏市场与阶段划分 | 3 | 3 | 1 | 1 | 2 | 10 | REJECT | 同 #18。且与 #18 内容高度重复 |
| 20 | github/awesome-copilot `skills/breakdown-epic-arch` | https://github.com/github/awesome-copilot/blob/main/skills/breakdown-epic-arch/SKILL.md | 38883 | 2026-09-10 | MIT | Epic 级系统架构文档模板 | 3 | 3 | 1 | 2 | 2 | 11 | REJECT | 架构文档模板，66 行几乎全是标题占位；无可证伪规则 |
| 21 | mariano-aguero/spec-driven-development-skill | https://github.com/mariano-aguero/spec-driven-development-skill | 7 | 2026-08-06 | MIT | constitution → specify → plan → tasks → implement → validate，MoSCoW、drift detection | 0 | 2 | 2 | 1 | 2 | 7 | REJECT | 7 stars 匿名级权威；内容是 `github/spec-kit` 的复述，抽查 `drift detection` 一节与 spec-kit 的 `analyze` 说法不一致且更含糊。取原始上游（#7）即可 |
| 22 | H2Sxxa/spec-coding-skills `skills/spec-plan` | https://github.com/H2Sxxa/spec-coding-skills | 3 | 2026-07-21 | MIT | 验收标准驱动的计划、从真实反馈自纠 | 0 | 1 | 2 | 2 | 2 | 7 | REJECT | 3 stars；191 行里可执行规则不足，`acceptance criteria` 一节比候选 3 的模板更弱 |
| 23 | janfrl/spec-driven-development | https://github.com/janfrl/spec-driven-development | 1 | 2026-04-20 | **无（null）** | brainstorm → spec → tests → code | 0 | 0 | 1 | 1 | 0 | 2 | REJECT | 无许可文件 → 不得合入；>4 个月未推送；1 star |
| 24 | anthropics/skills（全仓 19 个 skill） | https://github.com/anthropics/skills | 175703 | 2026-09-10 | 逐目录，多为专有 | `skill-creator`、`doc-coauthoring`、`mcp-builder`、`webapp-testing` 等，**无 planning / spec / plan 类 skill** | 3 | 3 | — | — | 0 | — | N/A（无候选） | 实读 `gh api .../git/trees/main?recursive=1` 后确认：19 个 skill 目录里没有任何规划类主题。因此本 skill 不从该仓取任何内容，也就不触发专有许可问题 |
| 25 | joelparkerhenderson/architecture-decision-record | https://github.com/joelparkerhenderson/architecture-decision-record | 16884 | 2026-09-05 | **NOASSERTION** | ADR 模板集合（Nygard、MADR、Tyree-Akerman 等） | 1 | 3 | 2 | 3 | 0 | 9 | REJECT（作 reference 也不必） | `license.spdx_id = NOASSERTION`，实读仓库根无标准 LICENSE 文件 → 不得作 merged。ADR 结构已由候选 6（GitHub 官方 MIT）覆盖，无需冒险 |
| 26 | VoltAgent/awesome-agent-skills | https://github.com/VoltAgent/awesome-agent-skills | 34046 | 2026-09-07 | MIT | 索引型 awesome 列表 | 1 | 3 | 0 | — | 2 | — | REJECT | 生成式链接索引，本身无规则内容。按「许可通过 ≠ 内容值得合入」，连 reference 都不列，只作检索途径记录在上面 |

候选 26 行，其中 INCLUDE 11、MAYBE 3（含 1 个降为 reference）、REJECT 8、N/A 1。

## 深度审查

### obra/superpowers `writing-plans`（171 行）

- **结构**：无 `## Scope`，直接 Overview → Scope Check → File Structure → Task
  Right-Sizing → Bite-Sized Granularity → 计划头模板 → 任务模板 → No Placeholders →
  Self-Review → Execution Handoff。
- **frontmatter**：只有 `name` + `description`，缺 `license` / `metadata`，不合本仓 schema。
- **质量**：最高。三处是可证伪的产物形状：
  1. `Interfaces: Consumes / Produces` —— 显式写出上下游签名，理由写得很清楚：
     「A task's implementer sees only their own task」。
  2. `No Placeholders` 的六条禁式（TBD、"add appropriate error handling"、
     "Write tests for the above"、"Similar to Task N"、无代码块的代码步骤、
     引用了任何任务都没定义的类型）——每条都能机械检查。
  3. `Self-Review` 三查：spec 覆盖率、占位符扫描、**类型一致性**
     （`clearLayers()` vs `clearFullLayers()` 举例非常具体）。
- **agent 绑定**：重度。`superpowers:using-git-worktrees`、
  `superpowers:subagent-driven-development`、`superpowers:executing-plans`
  三处跨 skill 引用，`docs/superpowers/plans/` 路径约定，以及
  "Announce at start: I'm using the writing-plans skill" 这种播报。全部剥离。
- **重叠**：与候选 3 在任务模板上重叠；与候选 5 在「计划要有 Alternatives/Dependencies」上重叠。
- **要修的**：`Bite-Sized Task Granularity` 把 TDD 五步硬编码进计划步骤
  （"Write the failing test" / "Run it to make sure it fails" / …）。本仓 TDD 循环归
  `test-driven-development`，计划里重述循环是重复。裁决见冲突表 #2。

### obra/superpowers `brainstorming`（250 行）

- **结构**：三档路径分类器是全部价值所在。`Spike / Bounded / Architectural` 三档
  各自有终态，且写了单向棘轮（"Nothing downgrades mid-task"）。
- **质量**：`Red Flags` 表七行全是真实的自欺句式，并给了反驳。其中
  "I understand this kind of app, so it's bounded" → "Bounded measures the repo,
  not your familiarity" 是本 skill 要保留的判据：**bounded 的定义是要改的流程已在本仓可读**，
  而不是「我熟」。这是可证伪的。
- **要删的**：
  - 149 行的 Graphviz `digraph`（按标准第 3 节必须删或转 ASCII）。
  - `<HARD-GATE>` XML 标签（标准 1.3 禁止正文 XML 注入式标签）。
  - Visual Companion 整节（依赖上游自带的浏览器伴侣服务，本仓没有）。
  - `elements-of-style:writing-clearly-and-concisely`、`docs/superpowers/specs/` 等残留。
- **重叠**：与候选 4 的 Phase 0 重叠，但角度不同：brainstorming 问「要多少流程」，
  addyosmani 问「是不是多个能力捆在一起」。两者都保留，前者是分流器，后者是分解触发条件。

### addyosmani/agent-skills `planning-and-task-breakdown`（257 行）

- **结构**：最接近本仓标准的一个（有 Overview / When NOT to use / 尺寸表 /
  Rationalizations / Red Flags / Verification 清单）。
- **质量**：任务模板包含 `Verification: Tests pass: [the repository's focused-test command]`
  ——**验收命令是模板的必填格**，而不是「记得验证」。这正是本 skill 要的形状。
  并行度三分类（safe to parallelize / must be sequential / needs coordination，
  后者要求「先定契约再并行」）是其他候选都没有的判断。
- **真实事故模式**：「Never overwrite an incomplete plan」——发现 `tasks/plan.md`
  还有未勾选项且属于**另一件工作**时必须停下来问，因为那些未勾选项可能正在另一个
  会话里执行中，覆盖会销毁只存在于该文件里的工作状态。这条可证伪、后果具体，保留。
- **agent 绑定**：`tasks/plan.md`、`tasks/todo.md`、`/build` 命令、
  `../../references/definition-of-done.md`（跨 skill 相对路径，单 skill 安装时不存在）。
  路径约定改为「项目自己的位置优先」，`See Also` 的跨目录链接删除。
- **要修的**：`Estimated scope` 用「2+ 小时的 agent 工作」作阈值——时间估算不可证伪
  且对 agent 无意义。改为以「文件数 + 是否跨独立子系统 + 验收标准能否 ≤3 条说完」为判据。

### addyosmani/agent-skills `spec-driven-development`（245 行）

- `ASSUMPTIONS I'M MAKING` 块是全部候选里最省返工的一条产物形状：在写任何 spec
  内容之前先列出 4 条左右的假设并要求纠正。它可证伪（产物里有没有这个块，一眼可见），
  后果具体（假设错了就是整份 spec 白写）。
- Phase 0 capability map 的三条约束（稳定 kebab-case 模块 id、依赖方向无环、
  「两个模块互相需要就是一个模块」）都可机械检查。
- `Boundaries` 三档（always do / ask first / never do）是把「越界」变成可判定的清单。
- **要修的**：`Commands` 一节示例写死 `npm run build` 等，改为「读仓库自己的命令」；
  `api-and-interface-design` 跨 skill 引用改为本仓的 `api-design`。

### github/awesome-copilot `create-implementation-plan`（185 行）

- 官方，但文风是 "AI-to-AI communication"、"zero ambiguity"、
  "No task should require human interpretation" 这类断言式套话，具体性只给 2。
- 真正有价值的是两处：
  1. **标识符声明唯一性**：区分「声明」（表格首格或 `- **REQ-001**:` 加粗前缀）与
     「引用」（任务正文里引 REQ、Dependencies 节指向上游 DEP），并给出
     `grep -oE ... | sort | uniq -d` 的三条检查，前两条必须返回空行。
     这是全部候选里唯一自带机械验证命令的规则。**本机已实测该 grep 管线可用**（见「事实核查」）。
  2. 模板必有 `3. Alternatives`（ALT-NNN）与 `7. Risks & Assumptions`
     （RISK-NNN / ASSUMPTION-NNN）两节——把「为什么不选另外两种」固化成产物格位。
- **要修的**：`${input:PlanPurpose}` 占位语法、`/plan/` 与 `/spec/` 绝对目录约定、
  `img.shields.io` 状态徽章（与内容无关的装饰）全部剥离。
  `Tasks within phases must be executable in parallel unless dependencies are specified`
  这条与候选 3 的并行度三分类冲突，见冲突表 #4。

### github/spec-kit `evolving-specs.md` / `spec-persistence.md` / `complex-features.md`

- 官方（GitHub），135k stars。它的价值不是命令（`/speckit.*` 是它自己 CLI 的斜杠命令，
  本仓无法引用），而是**三种 spec 持久化模型**：
  - flow-forward：每次新增一个 feature 目录，旧目录作历史记录；
  - living：`spec.md` 是契约，`plan.md` / `tasks.md` 从它派生，改 spec 必须回流重生成下游；
  - flow-back：允许实现中的发现先落在最靠近工作的产物上，之后把整套产物拉回一致。
- 三条都带一句硬约束：`Do not leave a lower-level change in tasks.md or code if
  spec.md still says something different`；以及「替换派生产物之前先把仍然重要的
  实现理由搬出来」。这两条可证伪且后果具体。
- `living` 模型第 5 步「在恢复实现之前跑一致性检查」是本 skill「执行跟踪」一节的门。
- **要剥离的**：所有 `/speckit.*` 命令名、`.specify/` 目录、`specify init --here --force`。

### obra/superpowers `verification-before-completion`（120 行）

- 与本仓 `test-driven-development` / `debugging` / `code-review` 已共用同一条
  evidence-before-claim 门（见那三个 skill 的 SOURCES.yaml notes）。本 skill 只取两行：
  - `Requirements met` → 需要**逐行清单核对**，"tests passing" 不够；
  - `Agent completed` → 需要**看 VCS diff**，子代理自述 success 不算。
- 第二条对本 skill 特别重要：计划的并行执行必然涉及委派，而「委派者报告成功」
  是计划执行里最常见的假完成。
- 其余（Iron Law 的措辞、红旗表）已在 `test-driven-development` 里，不重复。

### mattpocock/skills `to-spec`（75 行）

- 最有用的一条是**否定式**：`Do NOT include specific file paths or code snippets.
  They may end up being outdated very quickly.` 例外是原型产出的、比散文更精确地
  编码了某个决定的片段（状态机、reducer、schema、类型形状）。
- 与候选 1 直接冲突（候选 1 的任务模板要求 `Modify: exact/path/to/existing.py:123-145`）。
  这是本 skill 最重要的一次裁决，见冲突表 #1。
- `disable-model-invocation: true` 是 agent 专属字段，剥离。
- seam 先行（「现有 seam 优于新 seam，理想数量是 1」）属于 `test-driven-development`
  的 seam 概念，本 skill 不重复，只在澄清阶段保留「先确认要测的边界在哪」。

### mattpocock/skills `triage`（112 行）

- 唯一提出**在澄清之前先做两项检查**的候选：
  (a) 冗余检查——按领域概念（不是按请求的措辞）搜是否已实现，并报告搜了哪里；
  (b) 先前驳回检查——读 `.out-of-scope/*.md`，看是否有相似请求已被拒绝过。
  两条都直接消灭返工，且可证伪（有没有报告搜索位置）。
- 第 3 步「先验证主张再澄清」：bug 先按报告步骤复现，PR 先 checkout 跑测试。
  「确认过的验证能写出强得多的 brief」。
- needs-info 模板要求把已确立的事实写进 "What we've established so far"，
  否则澄清轮次之间的成果会丢失——这是多轮澄清的真实失败模式。
- **归属**：状态机与标签词汇表本身是 GitHub issue 操作，按契约归 `github`；
  本 skill 只取两项前置检查、先复现再澄清、以及澄清成果必须落盘这三条。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 规划产物里到不到要写确切文件路径 | mattpocock `to-spec`：**不要**写路径与代码片段，会迅速过期；obra `writing-plans`：任务必须写 `Create: exact/path/to/file.py`、`Modify: existing.py:123-145` | **按产物分层**：需求/验收层（spec）不写路径，写行为与验收标准；实施计划层（plan）必须写路径，因为路径就是它的分解结论。两者不是冲突而是两份不同产物。写成本 skill 的一条规则：路径出现在计划里而不是在需求里；若某条需求只能用路径表达，说明它其实是设计决定，挪到计划 | 两方都是公认专家，但主张的对象不同（to-spec 产出 spec 并发布到 issue tracker，长期存活；writing-plans 产出一次性执行文档）。生命周期决定要不要写易变细节 |
| 2 | 计划的步骤粒度要不要写成 TDD 五步 | obra `writing-plans`：每个任务展开为「写失败测试 / 跑它看失败 / 最小实现 / 跑通 / 提交」五步，每步 2-5 分钟；addyosmani `planning-and-task-breakdown`：任务是纵向切片，带验收标准 + 验证命令，不规定内部循环 | 取 addyosmani。计划规定**每步的验收命令与预期输出**，不规定实现循环；实现循环是 `test-driven-development` 的内容，计划里重述它既重复又会在非 TDD 场景（迁移、配置、调研）下变成噪声 | 本仓已有 `test-driven-development`，标准第 3 节要求一个概念只在一处写。且 obra 的五步在「升级依赖」「改 CI」这类任务上不可执行，本身不通用 |
| 3 | 计划文档存哪 | obra：`docs/superpowers/plans/YYYY-MM-DD-<feature>.md`；addyosmani：`tasks/plan.md` + `tasks/todo.md`；awesome-copilot：`/plan/<purpose>-<component>-<version>.md`；spec-kit：`specs/<feature>/{spec,plan,tasks}.md` | **项目自己的约定优先**：先找仓库里已有的计划目录（`docs/plans/`、`specs/`、`tasks/`、`.specs/`、ADR 目录），找到就沿用；没有就写在仓库已有的文档目录下。四家各有约定说明没有事实标准，硬推一个会和用户仓库打架 | 「更新 > 更旧」在此无效（四家都是最近一个月推送）。标准第 3 节「只给一个默认方案 + 一个逃生口」：默认沿用仓库约定，逃生口是问用户 |
| 4 | 同一阶段内的任务默认能不能并行 | awesome-copilot `create-implementation-plan`：`Tasks within phases must be executable in parallel unless dependencies are specified`（默认可并行）；addyosmani：三分类，共享 API 契约的必须**先定契约再并行**，迁移与共享状态必须串行 | 取 addyosmani。默认可并行是危险默认：**未声明的依赖不会因为没声明就不存在**。改成：并行度必须逐条论证，论证不出就串行 | 「具体 > 断言」。awesome-copilot 这条是为自动化执行方便而设的假设，不是对代码现实的判断；它自己也承认依赖要 explicitly declared，但把举证责任放错了方向 |
| 5 | 未知与不确定怎么处理 | awesome-copilot `structured-autonomy-plan`：在计划里打 `[NEEDS CLARIFICATION]` 标记并强制暂停等反馈；obra `brainstorming`：一次一个问题，问到清楚再写；addyosmani `spec-driven-development`：先列 `ASSUMPTIONS` 让人纠正 | **三者互补，按未知的种类分**：能自己查的（代码现状、库行为、默认值）自己查，不问；必须由人决定的（取舍、优先级、外部约束）一次性成组问；查不到又不影响本轮分解的，写成显式假设留在产物里并标注「若此假设为假，受影响的步骤是 N 和 M」 | 标准「只给一个默认方案 + 一个逃生口」。三者都对，但「不加区分地问」会把可查的事实推给用户，「不加区分地假设」会把决定偷偷替用户做了 |
| 6 | 计划与实现发生分歧时先改哪份 | spec-kit：三种持久化模型（flow-forward / living / flow-back），必须先选一种；awesome-copilot `update-implementation-plan`：在原计划上增量修订，保留已完成项；obra `executing-plans`：遇阻停下来找人 | 取 spec-kit 的 living 为默认（需求文档是契约，计划从它派生，改需求必须回流下游并在恢复实现前做一致性检查），flow-back 作逃生口（实现中的发现先落在最近的产物上，之后把整套拉回一致）。两者都吸收 awesome-copilot 的「修订不清空已完成记录」 | 官方（GitHub）> 社区，且 spec-kit 是唯一把「先改哪份」写成明确策略而不是随缘的候选。flow-forward 在单仓单 feature 场景下会堆出一堆历史目录，不作默认 |
| 7 | ADR 用哪个模板 | awesome-copilot `create-architectural-decision-record`（Status/Context/Decision/正负后果/Alternatives 带驳回理由/supersedes 链）；joelparkerhenderson 的模板集合（Nygard、MADR、Tyree-Akerman…） | 取 awesome-copilot。除结构相近外，决定性因素是许可：joelparkerhenderson 是 `NOASSERTION`，不得作 merged | 「官方厂商 > 社区」+ 许可硬约束。MADR 等模板的多样性对本 skill 无增量，只会变成「罗列多个可选」，违反标准第 3 节 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| obra-writing-plans | obra/superpowers `skills/writing-plans` | merged | 计划头（Goal/Architecture/Spec 指针/Global Constraints）、Interfaces 的 Consumes/Produces 块、No-Placeholders 六条禁式、自审三查（spec 覆盖率 / 占位符 / 类型一致性）、任务右尺寸的「审查者能否单独否掉它」判据 |
| obra-brainstorming | obra/superpowers `skills/brainstorming` | merged | spike/bounded/architectural 分流器与单向棘轮、bounded 的「要改的流程已在本仓可读」判据、2-3 方案取舍、spec 自审四查、澄清阶段的自欺句式表 |
| obra-executing | obra/superpowers `skills/executing-plans` + `skills/verification-before-completion` + `skills/subagent-driven-development` | merged | 执行前批判性复读、必须停下来重新规划的四个触发条件、evidence-before-claim 的两行（逐行清单核对需求、委派结果查 diff 不信自述）、以及「执行者只读自己那一段」这条推论 |
| addy-planning | addyosmani/agent-skills `skills/planning-and-task-breakdown` + `skills/spec-driven-development` | merged | 依赖图与纵向切片、任务模板里验收命令是必填格、拆分触发条件、并行度三分类与「先定契约再并行」、不覆盖未完成计划、ASSUMPTIONS 显式块、capability map 三约束、Boundaries 三档 |
| copilot-plan | github/awesome-copilot `skills/create-implementation-plan` + `skills/create-specification` + `skills/create-architectural-decision-record` + `skills/update-implementation-plan` + `skills/structured-autonomy-plan` | merged | 标识符声明唯一性与可 grep 的检查、Alternatives/Risks/Assumptions 作必填格位、Given-When-Then 验收标准、requirement/constraint/guideline 分标、ADR 结构与 supersede 链、修订不清空已完成记录、`[NEEDS CLARIFICATION]` 标记法 |
| speckit-docs | github/spec-kit `docs/concepts` + `docs/guides` | merged | 三种持久化模型（living 作默认、flow-back 作逃生口）、改上游产物必须回流下游、替换派生产物前先搬出仍然重要的理由、恢复实现前的一致性检查 |
| mattpocock-spec | mattpocock/skills `skills/engineering/to-spec` + `skills/engineering/triage` | merged | 需求层不写路径与代码片段（含原型片段例外）、Out of Scope 作必填节、澄清前的冗余检查与先前驳回检查、bug 先复现再澄清、澄清成果必须落盘 |
| neolab-sdd | NeoLabHQ/context-engineering-kit `plugins/sdd` | reference | GPL-3.0，未复制任何文字。只读其 skill 切分（create-ideas / brainstorm / plan-task / add-task / implement-task / review）确认覆盖面，并据此决定本 skill 不再细拆 |

## 基线缺口

无 skill（`uv run tools/run_evals.py planning --baseline`，Claude Opus 5 · medium，2026-09-11，
5 场景全部 `ok`，用时 97–155 s）时，各场景未达成的 `expected_behavior`：

**先说结论：基线不是零区分度，但非常接近。** 4 个正例里基线拿下 27/35 条，
缺的 8 条集中在**产物形状**上——判断质量本身很高（它自己就发现了 fire-and-forget
事件总线接不住「不许重发」、`make client` 会打断 mobile strict 构建、
`setTimeout` 重试是伪修复、"Tests pass" 没有证据），但**它交出的东西不是一份可执行的计划**。
这正好是本 skill 的价值所在，也说明评测设计对了：陷阱是可被发现的，形状是会被跳过的。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 澄清 | 把需求改写成可判定的验收标准 | 它把「instant but not spammy」变成了「请给我 P95 数字」这个**提问**，但从没写出一条能判真假的标准。交付物是「阻塞性输入 6 条 + 最小范围 5 条」，不是需求 |
| 1 澄清 | 把「可取回」当成独立可交付的能力 | 它把留痕折进同一张 `notifications` 表（"同时解决去重和留痕"），只把「保留期策略」列为非目标。合规留存与通知投递被绑成一件事，两者之后只能一起发布 |
| 2 计划审查 | 「没有任何一条任务写出证明它完成的命令」这个总体缺陷 | 它单点指出了 Task 7「跑测试」和 DoD 不可验证，并给出 4 条全局 DoD 命令，但没有把「每个任务都缺验收命令」作为缺陷提出，重写结构里也只有 `Phase 4 验证：每阶段的具体验收命令`——验收仍然按阶段而不是按步骤 |
| 2 计划审查 | 计划未声明任何假设 / 非目标 / mobile 耦合的负责人 | 它列出了 Task 5 的凭据依赖，但没有把「计划里没有假设节、没有非目标、没人负责 api-client 耦合」当成缺陷 |
| 3 分解并行 | 每个任务带仓库自己的验收命令与预期结果 | 表格只有任务名 + `0.5d` / `0.5–1d` 的**工期估算**；`make test-one` / `make typecheck` 只在「协作红线」里出现一次，作为「别拿全局 typecheck 当门禁」的提醒，没有一条任务带验收行 |
| 3 分解并行 | 把最大的未知前置成一次廉价调查 | T0 是「决策 + 事件清单」。至于「at-least-once + 进程内总线到底能不能做到不重发」，它**直接自己下了结论**（唯一约束），没有安排任何验证步骤；结论虽然对，但整条计划押在一个没验证过的判断上 |
| 3 分解并行 | 检查 `docs/plans/` 现状，不覆盖仍有 6/11 未勾选的 `2026-07-search.md` | 它直接写入 `docs/plans/2026-09-notifications.md` 并说「遵循仓库约定」，对同目录下那份未完成的计划**一字未提**。（场景 1 和 2 的答案里它反而提到了 6/11，说明这不是没读到，而是写文件时没做这项检查） |
| 4 执行跟踪 | 以修订（保留已完成记录与变更原因）而不是重写的方式改计划 | 它的「下一步」第 7 条是「计划迁到 `docs/plans/2026-09-notifications.md`，标注依赖，DoD 换成可验证条目」——即重新生成一份好计划。已完成 1.5 个任务的事实、schema 为何偏离、Task 3 为何被跳过，这些记录没有任何要保留的安排 |

另外两点基线做得比预期好，记录下来避免下次误判：

- **负例干净**：场景 5 `skill_read=false`，直接给 `gh` 命令，还实测了三个真陷阱
  （`--label` 不会自动建标签、`gh` 无 milestone 子命令只能走 REST、
  `blocked_by` 要的是全局 `issue_id` 而非 issue number），完全没有产出计划文档。
  说明「已签字的计划 → 机械建 issue」这个负例的边界切得准，不需要收紧 `description`。
- **场景 4 拿到 8/9**：进展报告与计划矛盾这类题基线本来就强。它唯一漏的就是「修订 vs 重写」。

因此**没有改写 `expected_behavior`**：缺口真实存在且全部落在形状上，
不需要靠提高难度制造缺口。

## 评测结果

模型固定 Claude Opus 5 · medium（`tools/run_evals.py` 默认，两组同一模型）。
基线 2026-09-11 跑完，用时 610 s；有 skill 同日跑完，用时 987 s。5 场景两组均 `status: ok`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 澄清 #412 | claude-opus-5 medium | 无（基线） | false | 7 / 9 | 缺「可判定验收标准」与「留痕是独立能力」。交付物是「阻塞输入 6 条 + 最小范围 5 条」，没有一条能判真假的需求 |
| 1 澄清 #412 | claude-opus-5 medium | 有 | **true** | 9 / 9 | 按 `## What I checked` → `Requirements (decidable)` → `Non-goals` → `Assumptions` → `Decisions I need` 的输出契约走。R1–R5 全是 Given-When-Then；A1–A4 各自写了「若为假则哪几步重写」；Q1–Q7 一轮问完且每条带推荐答案。两项前置检查做了并**如实标注「previously rejected」查不全，因为没有 checkout**——这比假装查过更有用 |
| 2 审查 plan-draft | claude-opus-5 medium | 无（基线） | false | 7 / 9 | 缺「每个任务都没有验收命令」这个总体缺陷（只单点打了 Task 7 与 DoD），也没把「无假设 / 无非目标 / mobile 耦合无责任人」当缺陷 |
| 2 审查 plan-draft | claude-opus-5 medium | 有 | **true** | 9 / 9 | 严格用 `plan-draft.md:<line> — <defect> / Fails as / Fix` 格式给出 10 条 findings，判定 `not executable` 前置，另有 `## Missing`（投递保证、可判定需求文档、计划落位）与 `## 非缺陷（不计入判定）`。开头明说「没有直接动手重写，按 skill 规则：静默修好的计划会掩盖它原本错到什么程度」 |
| 3 分解 + 并行度 | claude-opus-5 medium | 无（基线） | false | 5 / 8 | 最弱的一场。任务表只有 `0.5d` 工期估算、零验收命令；最大未知（at-least-once 能否不重发）自己拍了结论没安排验证；直接写入 `docs/plans/2026-09-notifications.md` 且对同目录 6/11 未勾选的 `2026-07-search.md` 一字未提 |
| 3 分解 + 并行度 | claude-opus-5 medium | 有 | **true** | 8 / 8 | 产出 481 行 `docs/plans/2026-09-notifications.md`，12 个步骤。Step 1–3 是三个 spike（各只回答一个问题，Accept 写明「A restated plan is not an answer」「'Probably deduplicates' is not an answer」）；Step 4 是契约冻结且 Accept 要求两位工程师书面确认可依此开工；每步都有 `Depends on:` / `Accept: make test-one FILE=… → <预期输出>`；`Parallel with:` 逐对给理由（Step 9 明写「disjoint file trees」并把 `make typecheck` 全局红标成 serialisation boundary）；Rollback point 写「before Step 5 (`make migrate`)，adr-0009 forward-only，恢复只能新写前向迁移」。并且明说「`2026-07-search.md` 还有 6/11 未勾选 —— 没动它，新建了 `2026-09-notifications.md`」 |
| 4 进展报告与计划矛盾 | claude-opus-5 medium | 无（基线） | false | 8 / 9 | 判断几乎全中（setTimeout 伪修复、手写 fetch 违反单一真源、"Tests pass" 无证据、schema 已上 staging 不可回退），但「下一步」第 7 条是「计划迁到 docs/plans/… 换成可验证条目」= 重新生成，没有保留已完成记录与变更原因的安排 |
| 4 进展报告与计划矛盾 | claude-opus-5 medium | 有 | **true** | 9 / 9 | 逐条对上 `execution-tracking.md` 的 stop triggers（前提为假 / 只能靠违反约束通过 / 出现无步骤覆盖的工作 + 回滚点失效 / 计划外阻塞），并明写「用 amend 而非 regenerate：checkbox 状态与「为什么代码长这样」只存在于该文档」，同时禁止复用仍有 6/11 未勾选的 `2026-07-search.md`。「按有验收命令输出才算完成的标准，7 个任务中 0 个可判定完成」 |
| 5 负例：把已签字的 6 项建成 GitHub issue | claude-opus-5 medium | 无（基线） | **false** | 3 / 3 | 直接给 `gh` 命令，无计划文档 |
| 5 负例：同上 | claude-opus-5 medium | 有 | **false** ✅ | 3 / 3 | **未读取 `skills/planning/SKILL.md`**。只输出建单脚本，还实测出三个真陷阱：`--label` 不会自动建标签；`gh` 无 milestone 子命令须走 REST；`blocked_by` 的 `issue_id` 要 blocker 的数值 id 且必须用大写 `-F` 才发成 JSON 整数（小写 `-f` 发字符串会 422）。没有重新论证范围、没有重画依赖图、没有产出计划文档 |

结论：**是。** 基线未达成的 8 条行为在有 skill 时全部达成，无一回退：

| 基线缺口 | 有 skill 时 |
|---|---|
| 需求没被改写成可判定标准（S1） | R1–R5 全部 Given-When-Then |
| 留痕被折进通知表（S1） | 单列为 R3 + Q5（保留期）+ A4（若有 WORM 要求则不再是单 cycle 改动），并把 admin/合规导出列为非目标 |
| 「每个任务都没有验收命令」未被当成缺陷（S2） | 作为独立 finding 提出，并给出 `make test-one FILE=<具体路径>` 的修法 |
| 无假设 / 无非目标 / 无回滚点未被当成缺陷（S2） | 作为 `plan-draft.md:1` 一条 finding，附 forward-only 的具体后果 |
| 任务无验收命令，只有工期估算（S3） | 12 步每步一条 `Accept:` 行，命令全部取自 inventory 的 Makefile |
| 最大未知没有前置调查（S3） | Step 1–3 三个 spike 排在最前，每个只回答一个问题并写了停止条件 |
| 未检查同目录未完成的计划（S3） | 明确声明「没动它」 |
| 改计划用重写而非修订（S4） | 明写 amend 而非 regenerate，并给出理由 |

## 备注

### 这个 skill 相比不加载它，到底多产生了什么可观察的差别

**判断力没变，产物形状变了——而这个差别是可观察、可验收的。**

不加载时，Opus 5 自己就能发现所有埋进夹具的陷阱：进程内 `EventEmitter` 接不住
「不许重发」、`make client` 会打断 mobile strict 构建、`setTimeout` 重试是伪修复、
"Tests pass" 没有命令输出。这些都不是这个 skill 教会它的。

差别在于:**不加载时它产出的是一段很好的分析，加载后它产出的是一份能被执行和被验收的产物。**
四处可直接对比:

1. **验收命令从 0 条变成每步 1 条。** 基线 S3 的任务表是「任务名 + `0.5d`」;有 skill 是
   12 步 × `Accept: make test-one FILE=<路径> → <预期输出>`,而且预期输出里写了
   「A restated plan is not an answer」这种反作弊条款。工期估算对 agent 执行者毫无意义，
   验收命令是唯一能判真假的东西。
2. **未知从「自己拍结论」变成「先花二十分钟验证」。** 基线直接断言唯一约束能解决重发问题
   ——结论恰好是对的，但整条计划押在一个没验证过的判断上。有 skill 时它把三个最贵的未知
   排成 Step 1–3 三个 spike,其中 Step 3 的 Accept 是
   `make client && make typecheck` → 贴出 mobile strict 报错数，并注明「零错误也是有效发现，
   该风险就此退役」。
3. **并行度从一句断言变成逐对论证。** 基线给了两条 lane;有 skill 时每步都有
   `Parallel with: … — disjoint file trees (…here; …there)`,还把「Step 9 在飞时全局
   `make typecheck` 是红的，别拿它当门禁」写成 serialisation boundary。
4. **改计划从重写变成修订。** 这条差别最贵:基线的「迁到新文件 + 换成可验证条目」会把
   「已完成 1.5 个任务」「schema 为何偏离计划」「Task 3 为何被跳过」这三条只存在于该文档里的
   记录一并抹掉，而这些恰好是下一个人唯一能靠的东西。

还有一个意外收获:负例两组都 `skill_read=false`,且有 skill 组答得更细
(多查出 `-F` vs `-f` 会导致 422 这一条)。说明 `description` 末尾的
`Do not use for … the mechanical creation of GitHub issues or pull requests` 切得准，
没有把「已签字的计划 → 机械建单」误吸进来，也没有因为存在这个 skill 而污染无关任务。

### 未达成项与已知不足

- **Phase A 的 anthropics/skills 没有可用候选。** 实读 `git/trees` 确认 19 个 skill 目录
  里没有任何规划类主题(候选表 #23)。这是好事(不涉及专有许可复制)，但意味着本 skill
  没有 Anthropic 官方的规划类对照物，`create-implementation-plan` / `spec-kit` 这两个
  GitHub 官方来源是权威性最高的输入。
- **`joelparkerhenderson/architecture-decision-record` 是 `NOASSERTION`**,实读仓库根
  确认无标准 LICENSE 文件，因此连 reference 都没列。ADR 结构取自 GitHub 官方(MIT)。
  若将来该仓库补上明确许可，它的 MADR / Tyree-Akerman 模板可作为补充——但按标准第 3 节
  「不罗列多个可选」，大概仍然不该合入。
- **有 skill 的场景 3 用时 486 s**,接近 900 s 超时的一半，因为它连跑了 r1 → r2 → r3 三轮
  自我修订(第三轮才发现 r2 把合规检索端点放进了「可裁剪」区)。这是 skill 起作用的证据，
  但也说明本 skill 在「分解 + 并行」这类任务上成本偏高。**没有为此降低要求**:
  三轮修订发现的是一个真实的合规事故(在审计窗口里发邮件却不留可检索记录)。
- **`scripts/` 目录没有创建。** 唯一候选是 `create-implementation-plan` 的标识符唯一性
  grep 管线，它是三行 shell、依赖具体计划文件路径，做成脚本不如内联在
  `references/plan-document.md` 里让读者直接抄。本机已实测该管线可用(见下)。
- **未在真实 GitHub 仓库上验证负例的 `gh` 命令**:评测环境的 token 解析不到 `acme/notify`
  (这是虚构仓库，预期如此)。这不影响本 skill 的任何规则。

### 事实核查

- 标识符声明唯一性的 grep 管线 **[verified]**:在本机用一份含重复 `TASK-001` 与重复
  `REQ-001` 声明、另有一处 `TASK-001` 纯引用的夹具实测，check 1 输出 `TASK-001`、
  check 2 输出 `REQ-001`,纯引用未被误报。写进
  `references/plan-document.md` 时标了 `[verified]` 与前置条件(POSIX shell + GNU 兼容
  `grep`/`sed`/`sort`/`uniq`)。
- 其余内容是方法论而非 API,没有版本号或 CLI 旗标需要复核;引用到的具体命令
  (`make test` / `make client` 等)全部来自评测夹具自身的 Makefile 段，不是对某个
  真实工具的断言。
- 安装冒烟 **[verified]**:`npx skills@latest add … --skill planning --agent universal
  --copy --yes` 在 `/tmp/hs-smoke-planning` 装出 `.agents/skills/planning/`,
  SKILL.md 350 行 + 9 个 references + SOURCES.yaml + evals 与 5 份夹具齐全。
- `validate_skills.py skills/planning` **[verified]**:1 error(`NOTICE.md is missing`,
  按约定由主代理的 `build_catalog.py` 生成)、0 warning。

### 未来同步时要盯的上游

- `obra/superpowers`:推送极频繁(每日)，`skills/writing-plans` 与 `skills/brainstorming`
  是本 skill 的主干，`check_upstream.py` 报 `behind` 时必须实读 diff。
- `github/spec-kit`:它的 `docs/concepts/spec-persistence.md` 是「先改哪份产物」这条规则的
  唯一来源，该文件改动需要重新裁决默认模型(现为 living)。
- `github/awesome-copilot`:418 个 skill 的大仓，`paths` 已收窄到 5 个目录，
  `repo moved, tracked paths unchanged` 是常态。
- `NeoLabHQ/context-engineering-kit`:GPL-3.0,**永远只能是 reference**。同步时只看它有没有
  新增规划类主题以判断覆盖面，不读正文。
