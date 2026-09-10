# test-driven-development 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-10（种子调研由主会话完成，本文件为转录 + 当日复核）
- 复核日期：2026-09-10（GitHub API 逐仓库重取 `stargazers_count` / `pushed_at` / `license.spdx_id`）
- 检索途径：
  - 种子：主会话调研归档 `local://research-practice.md`（AREA 1，22 行候选）
  - `web_search`：`"test-driven-development" agent skill SKILL.md github red-green-refactor`
    ——补出 6 个种子清单里没有的候选（cloudflare/computer、vibeeval/vibecosystem、
    arjunprabhulal、SkillMedev、rbaumier、woojubb），全部读过原文后处理
  - 上游原文：`raw.githubusercontent.com` 直接取 8 份 SKILL.md / reference 全文
    （obra 三份、mattpocock 四份、addyosmani 一份）
  - 领域官方组织仓库：`anthropics/skills` 目录清单——**确认官方仓库没有 TDD skill**，
    最接近的 `webapp-testing` 是浏览器验证，不是 TDD，只能作为路由目标
- GitHub API 核对方式：`https://api.github.com/repos/<owner>/<repo>`，本次 21 个仓库全部
  取到真实值（仅 `woojubb/robota` 触发匿名限流，见候选表 28 行备注）

### 当日复核结果（与种子调研的差异）

| 仓库 | 种子记录 | 今日 API | 差异 |
|---|---|---|---|
| obra/superpowers | 284,338★ / 2026-09-10 / MIT | 284,403★ / 2026-09-10T06:44Z / MIT | stars +65 |
| mattpocock/skills | 258,274★ / 2026-09-04 / MIT | 258,397★ / 2026-09-04T08:45Z / MIT | stars +123 |
| addyosmani/agent-skills | 93,312★ / 2026-09-08 / MIT | 93,324★ / 2026-09-08T07:21Z / MIT | stars +12 |
| anthropics/skills | ~176k / n/a（API 403） | 175,553★ / 2026-09-03T16:37Z / license 为 null | 本次 API 通了；仓库根无许可，逐 skill 各带 LICENSE.txt |

四个 merged 上游全部落在「≤1 月内有推送」的最高新鲜档，许可全部为 MIT，无一例许可风险。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。
「正确」列为抽查 3 条规则对照上游原文与官方文档的结果；未读原文的不打分（记 `-`）。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | obra/superpowers `skills/test-driven-development/SKILL.md`（320 行） | https://github.com/obra/superpowers | 284,403 | 2026-09-10 | MIT | Iron Law + 反合理化的 TDD 循环 | 2 | 3 | 3 | 3 | 2 | 13 | **INCLUDE（主干）** | 全生态唯一把「亲眼看到 RED」写成强制步骤并逐条点名规避话术的 skill；行为压强最高 |
| 2 | obra/superpowers `skills/test-driven-development/writing-good-tests.md`（198 行） | 同上 | 284,403 | 2026-09-10 | MIT | 什么不该测 + 变异检查 | 2 | 3 | 3 | 3 | 2 | 13 | **INCLUDE** | 两条 Gate Function（命名 break / 跑真东西）+ mutation check，是唯一成体系的「反假测试」材料 |
| 3 | mattpocock/skills `skills/engineering/tdd/SKILL.md`（38 行） | https://github.com/mattpocock/skills | 258,397 | 2026-09-04 | MIT | seam、垂直切片、同义反复 | 2 | 3 | 3 | 3 | 2 | 13 | **INCLUDE** | 提供 seam 词汇与「先确认 seam」步骤、水平切片反模式、同义反复测试的精确定义 |
| 4 | mattpocock/skills `skills/engineering/tdd/tests.md`（77 行） | 同上 | 258,397 | 2026-09-04 | MIT | 好/坏测试对照 | 2 | 3 | 3 | 3 | 2 | 13 | **INCLUDE** | 紧凑的正反对照，含「经接口验证而非查库旁路」与同义反复两组示例 |
| 5 | mattpocock/skills `skills/engineering/tdd/mocking.md`（59 行） | 同上 | 258,397 | 2026-09-04 | MIT | 边界 mock、DI、SDK 形接口 | 2 | 3 | 3 | 3 | 2 | 13 | **INCLUDE** | 唯一给出「为可 mock 而设计」的上游：DI + 每个外部操作一个具名函数 |
| 6 | addyosmani/agent-skills `skills/test-driven-development/SKILL.md`（398 行） | https://github.com/addyosmani/agent-skills | 93,324 | 2026-09-08 | MIT | 发现栈、金字塔、规模、反模式 | 2 | 3 | 3 | 3 | 2 | 13 | **INCLUDE** | 「Discover the Stack First」把整个 skill 去 JavaScript 化；反模式表是 smell 目录的种子 |
| 7 | obra/superpowers `skills/verification-before-completion/SKILL.md`（120 行） | 同 #1 | 284,403 | 2026-09-10 | MIT | 先证据后声明 | 2 | 3 | 3 | 3 | 2 | 13 | **INCLUDE（局部）** | 只取「回归测试红绿证明」与完成门；其余属独立 skill，另批处理 |
| 8 | mattpocock/skills `skills/productivity/grilling/SKILL.md`（28 行） | 同 #3 | 258,397 | 2026-09-04 | MIT | 一轮问完前沿问题 | 2 | 3 | 2 | 3 | 2 | 12 | **INCLUDE（仅格式）** | 只取提问格式（编号 + 推荐答案 + 事实自己查）；design-tree 面谈循环不合入 |
| 9 | mattpocock/skills `skills/engineering/implement/SKILL.md` | 同 #3 | 258,397 | 2026-09-04 | MIT | 8 行编排桩 | 2 | 3 | 0 | - | 2 | 7 | **REJECT** | 纯路由（先 tdd 再 code-review），无可合入内容；其「技能串联」的想法体现在正文的路由句里 |
| 10 | anthropics/skills `skills/webapp-testing/` | https://github.com/anthropics/skills | 175,553 | 2026-09-03 | 逐 skill LICENSE.txt（根无许可） | 浏览器驱动的应用验证 | 3 | 3 | - | - | 0 | - | **REJECT（合入）** | 不是 TDD 而是浏览器验证；许可为逐 skill 专有文本，按仓库策略不得 merged。作为 UI 验证的路由目标在正文提名 |
| 11 | addyosmani/agent-skills `skills/browser-testing-with-devtools/` | 同 #6 | 93,324 | 2026-09-08 | MIT | DevTools MCP 验证 | 2 | 3 | - | - | 2 | - | **REJECT（合入）** | 独立任务类型，合入会把 TDD skill 变成浏览器工具手册；作为 UI 验证路由目标提名 |
| 12 | addyosmani/agent-skills `skills/incremental-implementation/` | 同 #6 | 93,324 | 2026-09-08 | MIT | 小步交付 | 2 | 3 | - | - | 2 | - | **REJECT** | 与 mattpocock 的垂直切片规则重叠，取其一即可；本身是另一个 skill 领域 |
| 13 | cloudflare/computer `.agents/skills/test-driven-development/SKILL.md`（330 行） | https://github.com/cloudflare/computer | 9,140 | 2026-09-10 | MIT | 与 #6 同构 | 1 | 3 | 3 | 3 | 2 | 12 | **REJECT（派生）** | 读过全文：逐字复制 addyosmani #6（删掉浏览器与子代理两节），零新增规则。合入等于重复计票；已在正文以 #6 为源 |
| 14 | vibeeval/vibecosystem `skills/tdd/SKILL.md`（389 行） | https://github.com/vibeeval/vibecosystem | 529 | 2026-08-08 | MIT | 与 #1 同构 | 0 | 2 | 2 | 2 | 2 | 8 | **REJECT（派生）** | 读过全文：obra #1 的复制 + `/tdd` 命令外壳与 `keywords` 非规范 frontmatter 字段；无独有内容 |
| 15 | glebis/claude-skills `tdd/SKILL.md`（744 行） | https://github.com/glebis/claude-skills | 374 | 2026-09-02 | MIT | 多代理编排 TDD | 0 | 3 | 2 | 2 | 2 | 9 | **REJECT（量表覆盖）** | 分数过线但仍拒：整套流程强绑定 Claude Code 的 Task 子代理编排与人工检查点，违反 `docs/skill-standard.md` 1.3 的 harness 绑定禁令；其唯一亮点（写测试的子代理看不到实现）已由 #6 的子代理节覆盖 |
| 16 | arjunprabhulal/agent-skills `skills/qa/test-driven-development/SKILL.md`（100 行） | https://github.com/arjunprabhulal/agent-skills | 2 | 2026-08-04 | MIT | 小循环 TDD | 0 | 2 | 2 | 2 | 2 | 8 | **MAYBE → 不合入** | 写作质量尚可，用作第三方校验（其「reproduction 就是第一个测试」与 #6 的 Prove-It 一致）；但规则与 #1/#3/#6 完全重叠，2★ 无采纳信号，合入无增量 |
| 17 | rbaumier/skills `matt-tdd/SKILL.md` | https://github.com/rbaumier/skills | 5 | 2026-09-08 | 无 | mattpocock 镜像 | 0 | 3 | - | - | 0 | - | **REJECT** | 个人镜像仓库，内容同步自 #3，无许可声明；直接跟 #3 上游 |
| 18 | mfranzon/tdd | https://github.com/mfranzon/tdd | 141 | 2026-02-24 | 无 | `/tdd` 命令吃计划文件 | 0 | 0 | - | - | 0 | 0 | **REJECT** | 6 个月无推送（新鲜度 0，量表规定直接 REJECT），单一用途小仓库，无许可 |
| 19 | JSerek/claude-sdd-skills `tdd/SKILL.md` | https://github.com/JSerek/claude-sdd-skills | 0 | 2026-07-26 | MIT | SDD 风味 TDD | 0 | 2 | 1 | - | 2 | 5 | **REJECT** | 0★，无任何采纳或评审信号 |
| 20 | davila7/claude-code-templates（TDD 模板） | https://github.com/davila7/claude-code-templates | 30,583 | 2026-09-10 | MIT | 模板农场 | 0 | 3 | 1 | - | 2 | 6 | **REJECT** | 种子记录的路径今日取 404，无法核实具体文件；仓库定位是 CLI 模板分发，skill 内容为他人作品的派生副本 |
| 21 | SkillMedev/legacy-modernization `skills/tdd-expert/` | https://github.com/SkillMedev/legacy-modernization | 2 | 2026-07-05 | MIT | 遗留系统 TDD | 0 | 2 | - | - | 2 | - | **REJECT** | 2★ 无信号；主题偏遗留系统改造，与本 skill 范围不同 |
| 22 | BjornMelin/dev-skills | https://github.com/BjornMelin/dev-skills | 7 | 2026-09-08 | 无 | 开发技能杂货铺 | 0 | 3 | - | - | 0 | - | **REJECT** | 7★、无许可、无评审信号 |
| 23 | antfu/skills `skills/vitest/SKILL.md` | https://github.com/antfu/skills | 5,871 | 2026-06-23 | MIT | Vitest 配置/API/mock/覆盖率 | 2 | 1 | 3 | - | 2 | - | **REJECT（本批）** | 生态 skill 而非任务型：合入会把框架 API 细节塞进本 skill，与 description 的否定边界冲突。正文以「用你测试运行器自己的生态 skill」路由；后续生态批次候选（注意其面向 Vitest 5.x beta，需版本固定） |
| 24 | full-stack-skills/testing-skills `skills/{vitest,jest,pytest}` | https://github.com/full-stack-skills/testing-skills | 1 | 2026-07-29 | NOASSERTION | 框架专用测试 | 0 | 2 | - | - | 1 | - | **REJECT（本批）** | 生态 skill；且 1★ + NOASSERTION，采纳前需另行审查 |
| 25 | microsoft/debugpy `.claude/skills/pytest/SKILL.md` | https://github.com/microsoft/debugpy | 2,469 | 2026-09-03 | NOASSERTION | pytest fixture/parametrize/marker | 3 | 3 | - | - | 1 | - | **REJECT（本批）** | 微软项目的仓库内 skill，生态批次候选；含项目自身约定 |
| 26 | prowler-cloud/prowler `skills/pytest/SKILL.md` | https://github.com/prowler-cloud/prowler | 14,785 | 2026-09-10 | Apache-2.0 | Python 测试模式 | 1 | 3 | - | - | 2 | - | **REJECT（本批）** | 混入项目专属约定；生态批次候选 |
| 27 | LambdaTest/agent-skills `{jest,pytest,vitest}-skill` | https://github.com/LambdaTest/agent-skills | 366 | 2026-07-24 | MIT | 厂商测试平台 | 1 | 2 | - | - | 2 | - | **REJECT** | 面向厂商平台集成，商业绑定 |
| 28 | jezweb/claude-skills `plugins/dev-tools/skills/vitest/` | https://github.com/jezweb/claude-skills | 1,000 | 2026-07-02 | MIT | Vitest | 0 | 2 | - | - | 2 | - | **REJECT** | 无评审信号；生态 skill，非本批范围。另：`woojubb/robota` 的 `tdd-red-green-refactor` 同类，本次 API 匿名限流未取到元数据，一并按「生态/派生小仓库」搁置 |

INCLUDE 8 项（#1–#8），其中 #1+#2、#3+#4+#5 各属同一上游目录，落成 5 条 `SOURCES.yaml` 记录。

## 深度审查

**obra `test-driven-development`（#1）** — frontmatter 极简，只有 `name` + `description`
（`Use when implementing any feature or bugfix, before writing implementation code`）。320 行，
结构：Overview → When to Use → The Iron Law → Red-Green-Refactor（带一个 Graphviz `dot`
循环图）→ 每阶段一节，各带 `<Good>`/`<Bad>` TypeScript 对照 → Good Tests 表 →
Common Rationalizations（11 行）→ Red Flags（13 条）→ bug 修复完整示例 →
Verification Checklist → When Stuck 表 → Debugging Integration → Final Rule。
质量：行为密度极高，几乎每行都是一条指令或对一种具体规避话术的反驳。
agent 绑定：高——它是写给「会给自己找理由的 agent」的，`your human partner` 这类措辞需要泛化。
仓库耦合：`npm test` 硬编码（4 处）、Graphviz 块（渲染为空白）、`superpowers:` 命名空间
交叉引用（`writing-good-tests.md` 里一处指向 `superpowers:writing-skills`）。
与其他候选重叠：与 #6 在「循环三步 + 合理化借口」上重叠约 40%，但 #1 的强制验证 RED 与
「先写的代码删掉」是独有的。

**obra `writing-good-tests.md`（#2）** — 不是 skill（无 frontmatter），是带显式触发行的
按需引用（"Load this reference when: writing or changing tests, adding mocks…"）。两条原则
（Name the Break / Exercise the Real Thing），每条以伪代码 **Gate Function** 收尾，然后
Mutation Check、Quick Reference 表、Warning Signs。这是全生态最强的反假测试材料：
镜像断言、变更探测器、"behavior not text"（不要 grep 源码）、"your code not the framework"、
完整结构 mock、生产类只带生产方法。与 #3/#4 无冲突——它们观点一致、示例不同，合并干净。

**mattpocock `tdd`（#3）** — frontmatter `name` + 触发短语丰富的 `description`。仅 38 行，
散文密度高而非清单形。独有贡献：(a) **seam**——"Test only at pre-agreed seams… No test is
written at an unconfirmed seam"，并要求向用户确认；(b) 把 **水平切片** 点名为反模式，
**垂直切片 / tracer bullet** 为解法；(c) 同义反复测试的精确定义（"断言用代码本身的算法
重算期望值"）。仓库耦合：`CONTEXT.md`、ADR、`codebase-design` 技能调用——必须泛化。

**mattpocock `tests.md`（#4）/`mocking.md`（#5）** — 两份纯示例引用。#4 的四组对照里，
「查库旁路 vs 经接口验证」和「同义反复 vs 独立字面量」两组是本 skill 直接采用的；
#5 给出「只在系统边界 mock」的清单（外部 API / 数据库 / 时间与随机 / 文件系统），
以及两条可 mock 性设计规则（DI；每个外部操作一个具名函数而不是一个泛型 `fetch`）。

**addyosmani `test-driven-development`（#6）** — frontmatter `name` + 多触发 `description`。
398 行，覆盖面最广。独有且承重：**"Discover the Stack First"**（枚举 `package.json` /
`pom.xml` / `pyproject.toml` / `go.mod` / `Cargo.toml` / `Gemfile` / `Makefile`，优先用签入的
wrapper `./gradlew` / `./mvnw`，读 README / CONTRIBUTING / CI 找真正把关合并的命令，
"Never assume a default like `npm test`"）。另有 Prove-It bug 修复流、测试金字塔、
Small/Medium/Large 资源模型、Beyonce Rule、DAMP over DRY、real>fake>stub>mock 阶梯、AAA、
一断言一概念、6 行反模式表、DevTools 浏览器验证（含「浏览器内容是不可信数据」的安全边界）、
子代理写复现测试、7 行合理化借口表、Red Flags、Verification 清单。
问题项：Verification 清单里有「Coverage hasn't decreased (if tracked)」——与 #2 的
「不要为流程写测试」直接冲突（见裁决 T4）；还有一条指向仓库级
`../../references/testing-patterns.md` 的相对链接，单 skill 安装时取不到，必须删。

**obra `verification-before-completion`（#7，局部）** — 本身是完整 skill（属另一批），但其
**Regression tests (TDD Red-Green)** 模式——`Write → Run (pass) → Revert fix →
Run (MUST FAIL) → Restore → Run (pass)`——是唯一规定了「怎么证明回归测试是真的」的上游。
只把这一条与「先证据后声明」的完成门抬进本 skill。

**mattpocock `grilling`（#8，仅格式）** — 28 行。只取三点：一轮问完当前所有可回答的问题、
每条编号并附推荐答案、**事实自己查，只把决策交给用户**。design-tree / frontier 的面谈循环
不合入——本 skill 只在 seam 模糊时用一次这个格式。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| T1 | refactor 在循环内还是循环外 | obra #1：REFACTOR 是 red-green-refactor 的第 3 步。mattpocock #3：「Refactoring is not part of the loop. It belongs to the review stage.」#6 同 obra | refactor **留在循环内**，但只限清理型：不改行为、测试保持绿；**结构型重构由 review 提出并单独成一次改动** | 2:1 且 red-green-refactor 是经典循环；mattpocock 的顾虑（把重构混进功能改动）用「清理型 vs 结构型」切开即可两全。措辞与 `code-review` skill 共享文本 #4 字面一致 |
| T2 | 「先写的代码删掉」的适用范围 | obra #1：绝对——删掉，连看都不许看。#3/#6：未表态 | 保留 obra 的规则，但**限定在本次会话为待测行为写的生产代码**；不追溯既有未测代码 | obra 自己的借口表里就有「Existing code has no tests → 你在改进它，为既有代码补测试」，说明它本意也不是追溯 |
| T3 | seam 确认 vs 默认直接 TDD | mattpocock #3：未确认的 seam 不许写测试（隐含每次都要问用户）。obra #1：始终 TDD，无需许可 | **默认直接 TDD 不问**；只在 seam 真的模糊时（模块深度不清、有多个同样合理的边界）用 grilling 格式问一轮 | 无条件确认会把每个琐碎改动变成一次用户往返，成本超过收益；但 seam 选错会让整批测试白写，所以模糊时必须问 |
| T4 | 测试数量 / 覆盖率的框架 | #6：金字塔比例（~80/15/5）+ 检查项「Coverage hasn't decreased」。#1/#2：「为流程写的测试要付一辈子维护费」，只交付行为需要的测试 | 规则采用 obra 的表述；金字塔比例**只在 `references/test-strategy.md` 作形状指引**；**删除覆盖率不下降的检查项** | 覆盖率棘轮奖励填充测试，而填充测试正是 #2 明令禁止的（"The test exists for coverage, checking no side effect or outcome" 是它的 warning sign 之一） |
| T5 | 语言偏置 | #1/#3 只有 TypeScript；#6 用 TS 举例但明确声明与栈无关 | 全局采用 #6 的立场：示例保持 TS，**所有命令一律写「仓库自己的命令」**；清除从 obra 抬来的 `npm test` 硬编码 | 本 skill 的 description 承诺 any language or framework；硬编码 `npm test` 会在 Gradle / Cargo / pytest 仓库里直接把 agent 带偏（#6 的 red flag 里也点了这条） |
| T6 | 仓库专属约定 | #3 引用 `CONTEXT.md`、ADR、`codebase-design` 技能、`/setup-…` 命令；#1/#2 引用 `superpowers:` 命名空间 | 全部泛化为「project context docs if present（CONTEXT.md、ADR、CONTRIBUTING 之类）」；命名空间交叉引用改为不带前缀的技能名提及 | `docs/skill-standard.md` 1.3 明确禁止 harness 绑定与上游交叉引用残留；`superpowers:` 也是校验器的禁词 |
| T7 | 三个工程实践 skill 的共享概念 | obra 的完成门、mattpocock 的 grilling 格式、seam 定义各自散落在三个 skill 里 | 完成门、grilling 格式、seam 定义、重构归属四段**在 `test-driven-development` / `debugging` / `code-review` 三处字面一致**，互不链接，只用技能名提及 | skill 之间只允许 SKILL.md → 自己的 reference 一层引用；三份措辞打架会让 agent 在同一次任务里收到互相矛盾的指令 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| obra-tdd | obra/superpowers `skills/test-driven-development/`（SKILL.md + writing-good-tests.md）@ b36e082 | merged | Iron Law、强制验证 RED、合理化借口表、红旗清单、When stuck 表、「先写的代码删掉」；两条 Gate Function、独立期望值、变更探测器与 mock 断言禁令、mutation check |
| obra-verification | obra/superpowers `skills/verification-before-completion/` @ b36e082 | merged | 先证据后声明的完成门；回归测试红绿证明（写 → 过 → 撤销修复 → 必须失败 → 恢复 → 过） |
| mattpocock-tdd | mattpocock/skills `skills/engineering/tdd/`（SKILL.md + tests.md + mocking.md）@ 3cca18b | merged | seam 词汇与先确认 seam、垂直切片 / tracer bullet、水平切片反模式、同义反复定义、经接口验证不走旁路、只在系统边界 mock、DI、SDK 形接口 |
| mattpocock-grilling | mattpocock/skills `skills/productivity/grilling/` @ 3cca18b | merged | seam 模糊时的一轮提问格式（编号 + 推荐答案 + 事实自己查） |
| addy-tdd | addyosmani/agent-skills `skills/test-driven-development/` @ 6ca0cd7 | merged | Discover-the-stack-first、Prove-It bug 修复、金字塔与 Small/Medium/Large、DAMP over DRY、real>fake>stub>mock 阶梯、AAA、反模式表 |

未作为 `SOURCES.yaml` 条目、只在正文以技能名路由的目标：测试运行器的生态 skill
（vitest / pytest / jest 之类）、浏览器端验证（`webapp-testing` 型 / DevTools 型）、
`debugging`（复现不了或修了三次还错时）、`code-review`（结构型重构与测试评审的落地）。
理由：这些没有任何内容被复制，`relation: reference` 会虚报「读过并对齐」。

## 基线缺口

无 skill（`uv run tools/run_evals.py test-driven-development --baseline`，默认模型，
四个场景全部 `status: ok` / `skill_read: false`）。逐条读 `answer.md` 与 `events.jsonl`
判定，未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明（判定依据） |
|---|---|---|
| 1 implement splitEvenly | #7 一次只做一个行为 | 一次 `edit` 把 9 个测试全部写进 `money.test.js`（整除、余数、负数、单人、零额、求和、`people < 1`、两类非整数），然后一次性实现。这正是 mattpocock 点名的水平切片：测试结构在了解代码之前就被锁死 |
| 1 implement splitEvenly | 其余 6 条均达成 | 自己读了 CONTRIBUTING.md / Makefile 找到 `make test` / `make test-one`，并明确说明「`npm test` 是故意缺失的」；先测后实现；报告里给出 9 fail → 13 pass 的真实计数；期望值是手算字面量 |
| 2 fix-bug slug | #1 先写会失败的复现测试 | `events.jsonl` 的工具顺序是决定性证据：`read` → `bash node -e`（手动复现）→ **`edit slug.js`（修复）** → `edit slug.test.js`（补测试）→ `make test`。测试从未在未修复的代码上跑过，一次红都没见过 |
| 2 fix-bug slug | #4 回归测试红绿证明 | 完全没做——没有撤销修复再跑一次的动作。它交付的是一个「只见过绿」的测试 |
| 2 fix-bug slug | 其余 4 条达成 | 用了仓库自己的命令；改的是根因（`[^a-z0-9]+` 加量词 + 去首尾连字符）而非特例；跑了全量并给出计数 |
| 3 review-tests | #2 镜像/同义反复断言判为必改 | 找到了 `:15` 的 reduce 重算，但判为「风格缺陷而非正确性缺陷」并保留该测试。Name-the-break 门的结论应当是「它无法失败」，降级为风格问题等于没应用这道门 |
| 3 review-tests | #4 只断言 mock 的测试 | 反向判错：把 `charges the payment gateway`（`vi.mock('./payment-gateway')` + 只断言 `charge` 的次数与参数）评为「保留，全套最强」 |
| 3 review-tests | #7 `sidebar-mock` 断言 mock 的存在 | 先判对，随后**主动撤回**，理由是 `getByTestId` 缺失即抛错所以「是真实断言」。它把「断言能否失败」与「断言的是不是脚手架」混为一谈 |
| 3 review-tests | #10 每条发现都命名 break | 为了拿证据，它在 `/tmp` **凭空重建了一份 `./checkout` 实现**并对其跑变异测试，随后自己发现这只能证明自己写的 stub，作废整张变异表。最终三条判决停在「需读实现才能定」 |
| 3 review-tests | 达成 5 条 | #1 file:line、#3 自比较、#5 `MAX_RETRIES` 变更探测器、#6 查库旁路、#8 `not.toThrow` 恒真、#9 sleep 计时 + 模块级共享状态 |
| 4 负例 CI 缓存 | 无缺口（全部达成） | `skill_read: false`；答案是 `setup-node` 的 `cache: pnpm` + 顺序前提核对，没有任何 red-green / 先写测试的框架；并且诚实拒绝编造加速百分比 |

缺口收敛为四类，正是 SKILL.md 要压的四件事：**垂直切片**（S1#7）、
**bug 修复必须先见红**（S2#1）、**回归测试的红绿证明**（S2#4）、
**Name-the-break 门要敢下删除判决而不是降级/撤回**（S3#2/#4/#7/#10）。

## 评测结果

三组运行：`--baseline`（默认模型，无 skill）、默认模型有 skill、`--model @smol` 有 skill。
每组 4 个场景全部 `status: ok`，`result.json` 落在
`/tmp/hs-evals/test-driven-development/{default,smol}/{baseline,skill}/<n>/`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 implement splitEvenly | default | 无 | false | 6 / 7（缺 #7） | 一次写完 9 个测试再实现——水平切片 |
| 1 implement splitEvenly | default | 有 | true | **7 / 7** | 六个切片，每片单独 RED；第 3、6 片首跑即绿，于是按规则改用变异证明（floor→trunc、`people < 2`）来确认测试能失败 |
| 1 implement splitEvenly | @smol | 有 | true | **7 / 7** | 五个切片；切片 4 自己发现「先写了没有测试的守卫」，按规则删掉重走，而不是就地将就 |
| 2 fix-bug slug | default | 无 | false | 4 / 6（缺 #1、#4） | 先改 `slug.js` 再补测试；测试从未见过红；无回归证明 |
| 2 fix-bug slug | default | 有 | true | **6 / 6** | 先 RED（`actual 'deploy----v2-' / expected 'deploy-v2'`，与报告签名一致），再修，再回退修复复现红，恢复复绿——三段输出全部引用 |
| 2 fix-bug slug | @smol | 有 | true | **6 / 6** | 同上，输出严格按 `## Output format` 的 RED / GREEN / Full suite / Reverted fix 四段 |
| 3 review-tests | default | 无 | false | 6 / 10（缺 #2、#4、#7、#10） | 把镜像断言降级为「风格缺陷」；把只断言 mock 的用例评为「全套最强」；撤回 `sidebar-mock` 判决；为拿证据在 `/tmp` 凭空重建实现跑变异，事后自行作废 |
| 3 review-tests | default | 有 | true | **10 / 10** | 开头即声明实现不可读、逐条标注，不再编造实现；每条判决带 Break 行；`charges the payment gateway` 判 keep 但点出「首要断言缺失——没有断言 `checkout` 返回给调用方什么」，与 `references/writing-good-tests.md` 的「调用次数是第二条断言，不是唯一一条」一致 |
| 3 review-tests | @smol | 有 | true | **10 / 10** | 同上；额外指出 `vi.mock('./db')` 是在 mock 自有模块（`references/mocking.md` 的边界规则） |
| 4 负例 CI 缓存 | default | 无 | false | 3 / 3 | — |
| 4 负例 CI 缓存 | default | 有 | **false**（修正后） | 3 / 3 | 首轮 `skill_read: true`——事件流显示它执行了 `read skill://test-driven-development`，intent 为 "Checking TDD skill applicability"（夹具里有 `pnpm vitest run` 步骤，触发了适用性探查）。据此在 `description` 的否定边界与 `## Scope` 的不覆盖列表中显式排除 CI / 构建 / 依赖缓存配置，`--only 4` 重跑后 `skill_read: false`，答案仍是正确的 `setup-node` `cache: pnpm` 方案 |
| 4 负例 CI 缓存 | @smol | 有 | false | 3 / 3 | 未读 skill；并主动说明「纯 CI 配置变更没有可测接缝，写 YAML 断言只会变成钉死实现的死测试」 |

结论：**通过**。基线未达成的 7 条行为（S1#7、S2#1、S2#4、S3#2、S3#4、S3#7、S3#10）
在**两种模型**有 skill 时**全部达成**，三个正例场景 `skill_read` 均为 true，负例为 false。
两种模型的差异只在切片数量与措辞密度（default 六片、smol 五片），关键行为无差别——
这说明起作用的是 skill 的规则与门，不是模型的自发倾向。

值得单独记一笔的两处「skill 在起作用」的直接证据：

1. 默认模型在场景 1 遇到「新测试首跑即绿」时，没有含糊放过，而是按 rule 5 与
   `writing-good-tests.md` 的变异检查主动破坏生产代码确认测试会红——这是基线从未出现的动作。
2. `@smol` 在场景 1 承认自己写了没有测试的守卫，并按 rule 6 / rule 「先写的代码删掉」
   删掉重走一遍红绿。T2 的裁决（只限本次会话为待测行为写的代码）在这里正好落地。

## 备注

- **评测夹具的一处刻意偏离**：计划建议场景 1 的夹具用 `pnpm vitest run` 作为「真实命令」。
  改为 `make test` / `make test-one FILE=…`（Node 内建 test runner），原因是评测要求
  「**实际跑一次看到它失败**」，而 vitest 在离线夹具里没有 `node_modules` 根本跑不起来，
  该条 `expected_behavior` 就会永远不可达。现在的夹具零依赖、可离线运行，并且
  `package.json` 故意不含 `test` 脚本——`npm test` 会以 missing-script 失败，
  「不能直接 `npm test`」这条依然是硬约束，且比原方案更硬（原方案里 `npm test` 恰好能工作）。
- **`mattpocock-grilling` 是加进来的第 5 个上游**（种子清单只有 4 个）。SKILL.md 里
  「seam 模糊时的一轮提问格式」字面来自该 skill，不记进 `SOURCES.yaml` 等于漏报来源。
- **未合入但要盯的上游**：`antfu/skills` 的 `vitest`（生态批次，注意其面向 Vitest 5.x beta）；
  `anthropics/skills` 若哪天新增 TDD 类 skill，需要重新评估——目前官方仓库确认没有。
- **同步时要重读的位置**：obra `writing-good-tests.md`（两条 Gate Function 的措辞是本 skill
  reference 的骨架）、addyosmani SKILL.md 的 Discover-the-Stack 清单（文件类型列表会随生态增补）。
  obra 仓库更新极快（几乎每日推送），`check_upstream.py` 会经常报 behind；只有触及上述两处
  才需要动本 skill。
- **共享文本**：完成门（rule 15）、grilling 格式（Workflows 末节）、seam 定义（rule 3）、
  重构归属（rule 7）四段与 `debugging`、`code-review` 字面一致，三个 skill 之间不互相链接，
  只用技能名提及（`debugging` 出现在 Scope 与 fix-bug / When stuck；`code-review` 出现在
  Scope 与 rule 7）。
- **放弃的方向**：不写任何测试框架的 API 细节（vitest / pytest / jest），不写浏览器端验证流程；
  两者都在 `## Scope` 的不覆盖列表里点名并路由出去。glebis 的多代理编排 TDD 虽然量表过线，
  但整套依赖 Claude Code 的 Task 工具，属规范禁止的 harness 绑定，不采纳。
