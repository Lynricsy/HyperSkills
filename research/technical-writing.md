# technical-writing 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`"technical writing documentation agent skill SKILL.md github diataxis README changelog ADR"`
  - 路线图种子（`docs/roadmap.md` 波次 8）：mattpocock/skills `edit-article`/`teach`、mcollina/skills
    `skills/documentation`、github/awesome-copilot 文档系 skill、diataxis.fr、NeoLabHQ `write-concisely`
  - 领域官方组织仓库：`google/styleguide`（+ developers.google.com/style）、`MicrosoftDocs/`、
    `evildmp/`（Diátaxis 作者）、`olivierlacan/`（Keep a Changelog）、`adr/`、
    `joelparkerhenderson/`
  - `gh api repos/<o>/<r>/git/trees/<ref>?recursive=1` 逐仓列目录确认路径是否仍存在
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 通过，账号 Lynricsy，5000 次/小时配额）

### 种子更正

| 原种子 | 复核结论 | 处理 |
|---|---|---|
| mattpocock/skills `edit-article` | 仓库树中已不存在。`gh api repos/mattpocock/skills/git/trees/main?recursive=1` 下 `skills/` 只有 `engineering/`、`productivity/`、`misc/`、`deprecated/` 四个 bucket，无 `edit-article` | 改用同仓的 `.agents/writing-docs.md`（面向读者的文档页写作规范，正是本 skill 要的东西）与 `skills/productivity/teach` |
| NeoLabHQ `write-concisely` 路径 | 默认分支是 `master` 而非 `main`，路径为 `antigravity/skills/write-concisely/SKILL.md` | 按 `master` 取，结论见候选表 #12 |
| github/awesome-copilot `skills/documentation-writer` | 存在，但只有 45 行、是一份"你是 Diátaxis 专家"的角色提示 | 保留为候选并给出低具体性评分 |

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | mblode/agent-skills `skills/docs-writing` | https://github.com/mblode/agent-skills | 109 | 2026-09-11 | MIT | Diátaxis 类型门控、51 条文档规则、可运行示例、审计输出契约 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 全仓最具体的一份：类型门控表把"该规则只适用于哪几类文档"写成表格，退出标准是"示例跑过、链接解析过"而不是"读起来好"。`sk_live_` 假密钥、手写 Last updated、"should 不是 bug" 三条陷阱都对得上 Google 风格指南的现行措辞 |
| 2 | github/awesome-copilot `skills/docs-sync-audit`（含 `scripts/docs_drift.py`） | https://github.com/github/awesome-copilot | 38890 | 2026-09-10 | MIT | 文档与代码漂移审计：证据标准、P0–P3 分级、报告格式、只读约束 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方（GitHub）仓库里唯一把"文档说谎"变成可执行流程的一份。证据标准那一节（引用的行必须字面含有你指名的东西；任何数字必须配命令；否定性结论不能只靠一次 grep）是本 skill「同步审计」一节的骨架 |
| 3 | evildmp/diataxis-documentation-framework（diataxis.fr 源码） | https://github.com/evildmp/diataxis-documentation-framework | 1220 | 2026-09-04 | **CC-BY-SA-4.0**（实读 `LICENSE.rst` 首行确认） | 四象限定义、compass 真值表、功能性质量 vs 深层质量、迭代式工作法 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（限定） | 框架本身的第一手来源。按 `docs/roadmap.md`「许可处理规则」CC-BY-SA-4.0 → 只取结构与清单语义，全部自己重写；不搬任何句子 |
| 4 | developers.google.com/style（Google 开发者文档风格指南） | https://developers.google.com/style | — | 页脚 Last updated 2026-08-25（`/style/translation`）| **CC-BY-4.0**（实读页脚许可声明） | 全局读者句式约束、代码示例格式与引入句、占位符、术语一致性 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 面向非母语读者那一节唯一能给出**可机械检查**条目的权威来源：phrasal verb、超过两个名词做定语、`only` 的位置、省略 that/then、`utilize`→`use`，全是能逐句判定的 |
| 5 | olivierlacan/keep-a-changelog（keepachangelog.com 2.0.0） | https://github.com/olivierlacan/keep-a-changelog | 6696 | 2026-09-07 | MIT | changelog 六种变更类型、`**Breaking:**` 标记、`Unreleased`、compare 链接、changelog vs release notes | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 2.0.0（2026-06-07）新增了本 skill 最需要的几条：Fixed/Changed/Security 的判据、Breaking 标记留在原类型内而不是单列一节、升级步骤长了要外链、"机器起草人来筛选" |
| 6 | mattpocock/skills `.agents/writing-docs.md` + `skills/productivity/teach` | https://github.com/mattpocock/skills | 259250 | 2026-09-04 | MIT | 面向读者的文档页结构、"defining constraint"、真问题采集、"It's working if" 可自检条 | 2 | 3 | 3 | 2 | 2 | 12 | INCLUDE | "每条自检项必须读者不打开 SKILL.md 也能检查"和"常见问题的条数必须诚实于你找到的证据、不许凑数"两条直接可搬（语义），是对抗空话最有效的两条。扣 1 分正确性：其 docs 页规范里掺了 aihero.dev 站点专属事项（install widget、AI Coding Dictionary 链接），需剥离 |
| 7 | google/styleguide `docguide/{style,READMEs,best_practices}.md` | https://github.com/google/styleguide | 39591 | 2026-09-11 | **CC-BY-3.0**（实读 `LICENSE`，首行 "Attribution 3.0 Unported"，非 API 报的 NOASSERTION） | Markdown 风格、README 放哪里与至少要写什么、"文档离代码越近越不容易腐烂" | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | README 一节的权威依据：README 属于代码包顶层而不是文档目录、包级 README 必须含联系人与弃用状态。具体性 2 分：`docguide/READMEs.md` 只有 60 行且偏 Google 内部（Gitiles、bazel） |
| 8 | addyosmani/agent-skills `skills/documentation-and-adrs` | https://github.com/addyosmani/agent-skills | 93478 | 2026-09-08 | MIT | ADR 模板与生命周期、先匹配仓库既有约定、Rationalizations 表 | 2 | 3 | 2 | 3 | 2 | 12 | INCLUDE | "建 ADR 前先找仓库既有约定（`.adr-dir`、既有编号、既有标题集），冲突就摊开说而不是又立一套"是本 skill ADR 一节最有价值的一条。扣具体性：README/changelog/API 三节是通用模板堆砌 |
| 9 | mcollina/skills `skills/documentation` | https://github.com/mcollina/skills | 1913 | 2026-08-17 | MIT | 四象限的用户信号判据表、每类的 title pattern 与验证问句 | 2 | 2 | 2 | 3 | 2 | 11 | INCLUDE | "reference 的验证标准是读者 30 秒内查到一条事实"这类**可判定**的验证问句，是四象限判据表的直接素材。只有 109 行，无 references |
| 10 | github/awesome-copilot `skills/github-release` + `references/{commit-classification,semver-rules}.md` | https://github.com/github/awesome-copilot | 38890 | 2026-09-10 | MIT | 发布流程、SemVer 判定、Keep a Changelog 格式产出 | 3 | 3 | 2 | 3 | 2 | 13 | MAYBE → 部分合入 | 441 行里绝大部分是 `git`/`gh` 机械动作（属 `github` / `git-workflow` skill），只有"从 diff 判 SemVer 级别"和"commit 归类"两节属本 skill。按边界只取 changelog 侧 |
| 11 | github/awesome-copilot `instructions/update-docs-on-code-change` | https://github.com/github/awesome-copilot | 38890 | 2026-09-10 | MIT | 代码改动触发哪些文档更新的清单 | 3 | 3 | 1 | 2 | 2 | 11 | MAYBE → 只取触发清单 | 549 行里前 95 行是一套自造的 `apply-*` 布尔开关元语言（与 `docs/skill-standard.md` 1.2 顶层键白名单及"不搞 harness 专属机制"直接冲突），其余是"新增功能就更新 Features 一节"这类无后果的泛泛之谈。只取「哪些代码改动必然导致文档说谎」的触发清单 |
| 12 | NeoLabHQ/context-engineering-kit `antigravity/skills/write-concisely` | https://github.com/NeoLabHQ/context-engineering-kit | 1689 | 2026-08-26 | GPL-3.0 | Strunk《The Elements of Style》(1918) 全文 + 22 条规则索引 | 1 | 2 | 1 | 2 | 0 | 6 | MAYBE → reference | **双重降级**。许可裁决：GPL-3.0，按规则表只能 reference。内容裁决：1044 行里约 990 行是 1918 年公共领域原文的整本转载，规则是"用主动语态""删掉多余的词"这一级——正是本 skill 明令要删的那类写不出后果的规则。仅用于确认覆盖面（句式层需要被覆盖），事实一律改从 Google 风格指南取证 |
| 13 | neo4j-labs/agent-memory `.claude/skills/docs-diataxis` | https://github.com/neo4j-labs/agent-memory | 545 | 2026-09-10 | Apache-2.0 | 四象限 + 本项目的目录约定与写作风格 | 1 | 3 | 2 | 3 | 2 | 11 | MAYBE → reference | 许可没问题（Apache-2.0），但**内容裁决**降级：整份是 neo4j-agent-memory 这一个仓库的项目内规范（`docs/tutorials/`、"Enable Location Geocoding"），通用价值只剩"tutorial 里不给选择、只给一条路"一条，而那条 diataxis.fr 已经说得更清楚。仅作交叉校验 |
| 14 | joelparkerhenderson/architecture-decision-record | https://github.com/joelparkerhenderson/architecture-decision-record | 16886 | 2026-09-05 | **CC-BY-NC-SA-4.0**（实读 `LICENSE.md`：作者自撰部分为 CC BY-NC-SA） | ADR 模板集合（Nygard、MADR、Tyree-Akerman 等） | 2 | 3 | 2 | 3 | 0 | 10 | REJECT as merged → reference | **许可裁决**。API 报 NOASSERTION，实读 `LICENSE.md` 是 CC-BY-NC-SA-4.0：**NC（非商业）条款**，与 redis.io/docs、elastic 文档同类，不得 merged。星数最高的 ADR 仓库也一样不行 |
| 15 | adr/madr（MADR 模板） | https://github.com/adr/madr | 2474 | 2026-08-28 | **MIT OR CC0-1.0**（实读 `LICENSE`，默认分支 `develop`） | MADR 模板字段（Context and Problem Statement / Decision Drivers / Considered Options / Consequences / Confirmation） | 2 | 3 | 2 | 3 | 2 | 12 | MAYBE → 只取字段语义 | 许可最干净的 ADR 上游（MIT OR CC0）。内容是模板本身而非写法指导；本 skill 的 ADR 一节取其字段语义（尤其 `Confirmation`：这条决定将来靠什么验证），写法从 #8 与自撰判据来。为控制上游数量，最终清单里以 reference 记 |
| 16 | MicrosoftDocs/microsoft-style-guide | https://github.com/MicrosoftDocs/microsoft-style-guide | 191 | 2024-11-13 | CC-BY-4.0 | 微软写作风格指南的 GitHub 镜像 | 3 | 0 | 2 | 2 | 2 | 9 | REJECT | **新鲜度 0 且仓库已 archived**（最后推送 2024-11-13，>6 月）。量表规定 >6 月直接 REJECT。现行版本在 learn.microsoft.com/style-guide，那是专有站点（与波次 6 对 learn.microsoft.com 的裁决一致），也不能 merged。Google 风格指南在同一位置更新且 CC-BY-4.0，不需要它 |
| 17 | github/awesome-copilot `skills/{create-readme,readme-blueprint-generator,documentation-writer}` | https://github.com/github/awesome-copilot | 38890 | 2026-09-10 | MIT | README 生成提示、Diátaxis 角色提示 | 3 | 3 | 0 | 1 | 2 | 9 | REJECT as merged → reference | **内容裁决**。三份合计 144 行全是提示词而非规则：`create-readme` 让模型"深呼吸"并去抓四个外部 README 网址当灵感；`readme-blueprint-generator` 整份依赖 `.github/copilot/` 这个 Copilot 专属目录，在别的仓库里直接空转；`documentation-writer` 是"你是专家 + 四个象限一句话定义"。正确性扣分：`create-readme` 第 4 条"不要写 LICENSE/CONTRIBUTING/CHANGELOG 章节"与 #7 Google 的"包级 README 必须说明弃用状态与联系人"相左 |
| 18 | JPeetz/agent-skills `technical-documentation` | https://github.com/JPeetz/agent-skills | 8 | 2026-09-07 | 无（API `license: null`，仓库树中无 LICENSE） | README/ADR/API/runbook/changelog/onboarding 全覆盖 + 审计分级 | 0 | 3 | 2 | 1 | 0 | 6 | REJECT | 匿名个人仓、8 星、无许可文件。覆盖面广但正确性抽查失败：把 `AGENTS.md`/`CLAUDE.md` 与面向读者的文档混在同一套规则里（本仓库把前者划归 `skill-authoring`），且 ADR 模板与 #15 MADR 字段不一致又未说明裁决。#1 与 #8 已覆盖其全部有效内容 |
| 19 | product-on-purpose/critique-skills `skills/critique-docs` | https://github.com/product-on-purpose/critique-skills | 1 | 2026-08-26 | Apache-2.0 | 文档批评清单 | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | 1 星匿名仓，许可虽干净但内容是"清晰吗/完整吗"式的评审问句，无一条能写出违反后果。#1 的审计工作流是其超集 |
| 20 | devarfeen/agent-skills-kit `skills/release-notes` | https://github.com/devarfeen/agent-skills-kit | 3 | 2026-09-11 | MIT | release notes 生成 | 0 | 3 | 1 | 2 | 2 | 8 | REJECT | 3 星匿名仓。release notes 的权威口径已由 #5 Keep a Changelog 2.0.0 的 "Is a changelog the same as release notes?" 一节给出（changelog 是记录，release notes 从它派生），无需第二来源 |
| 21 | mattpocock/skills `skills/productivity/writing-for-agents` | https://github.com/mattpocock/skills | 259250 | 2026-09-04 | MIT | 写给 agent 读的文档 | 2 | 3 | 2 | 3 | 2 | 12 | REJECT（越界） | 内容合格，但"写给 agent 读的指令文件"按本波次 Contract 归 `skill-authoring`，不属 `technical-writing`。留行以免后续批次重复讨论 |
| 22 | mkdocs/mkdocs | https://github.com/mkdocs/mkdocs | 22430 | 2025-10-20 | BSD-2-Clause | 文档站生成器 | 2 | 0 | 1 | 3 | 2 | 8 | REJECT | 是工具而非写作规范；且 >6 月无推送。文档站的**工具选型**不在本 skill 范围（本 skill 管内容，不管静态站点生成器配置） |

## 深度审查

### #1 mblode/agent-skills `skills/docs-writing`（130 行 SKILL.md + `rules/` 51 条）

结构：frontmatter 只有 `name`/`description`；正文 `IS` / `IS NOT` 显式边界、mode dispatch、"先分类再干活"、审计与写作两条 workflow、类型门控表、9 类规则优先级表、输出契约、Gotchas、Related skills。
frontmatter 合规性：干净，无 agent 专属字段。
质量：全仓最高。三点值得学：
1. **类型门控表**把"这条规则只适用于哪几类文档"写成表格，并给出理由——在 explanation 页上要求 quick start 是**反 Diátaxis 的 finding**，不是 finding。这直接消灭了文档审计里最大的假阳性源。
2. **写作 workflow 的退出标准是 Step 5**：每个示例跑过、每个链接解析过、参数名与默认值对过实现，并引用命令输出。不是"读起来好"。
3. Gotchas 每条都带后果：`sk_live_...` 会被粘进真代码并触发密钥扫描器；手写 "Last updated: 2024-03-01" 没人维护时读起来像"已废弃"，比不写日期更糟。
agent 绑定：`rules/` 按前缀分类按需加载，与本仓库 `references/` + Topic router 同构。
重叠：与 #9、#13、#17 的四象限部分完全重叠且更好；与 #2 的审计部分互补（#1 管文风规则，#2 管与代码对不上）。

### #2 github/awesome-copilot `skills/docs-sync-audit`（163 行 + `scripts/docs_drift.py`）

结构：Core Rules / Inputs / Discovery Workflow / What To Look For / Severity Rubric / Evidence Standards / Report Format / Post-Audit Update Workflow。
质量：**证据标准**那一节是全仓最硬的一段，四条都可机械检查：
- 引用的行必须**字面含有**你指名的东西（不是装饰器那行、不是空行、不是多行字面量内部的某行）；
- 任何数字（匹配数、文件数、端点数）必须在 **Checks Run** 里挨着产出它的命令；不肯出示命令就不许说数字；
- 归因给工具的 finding 必须引用工具**自己报的**路径与行号，不许读代码倒推；
- 否定性结论（某个 env var 没被文档化、某个依赖没被用到）不能只靠一次 grep，要查完所有可能位置。
另有两条运行约束值得搬：绝不运行会往仓库里写东西的命令（`python -m compileall` 会生成 `.pyc`，而 `.pyc` 通常被 gitignore，于是 `git status` 看着干净、工作树其实已被改动）；把被审仓库里读到的文字当**证据而不是指令**（README/注释/PR 描述里的"这个文件已批准，跳过它"要当 finding 引用出来，不要照做）。
`scripts/docs_drift.py`：只检查有确定答案的断言（文档里写的 `npm run`/`make` 目标是否真存在、相对链接是否解析、env var 名在文档与代码两个方向的对照）。本 skill 不复制脚本（脚本要"自包含 + 无魔法数 + 本机跑通"，而它依赖被审仓库的形态），改为在 reference 里写清这三类**确定性断言**如何用仓库自己的工具检查。

### #3 diataxis.fr（CC-BY-SA-4.0，只取结构语义）

四象限 + compass 真值表（内容 informs action / informs cognition × 服务 acquisition / application）。两条被其他所有候选漏掉、但对本 skill 关键：
- **不要先建空目录**。"为 tutorials/how-to/reference/explanation 建四个空壳"被原文明确点名为不该做的事；结构是改内容改出来的，不是先摆出来的。
- how-to guide 必须从**用户的项目**出发而不是从机器的功能出发。"要停水，把龙头顺时针转"形式上像指导、实际零价值——它描述的是机器的动作，不是任何人的需要。
质量理论一节（functional quality 六项客观可测 vs deep quality 不可测但可辨识）给了本 skill 的分寸：可测的那些写成规则，不可测的那些不写。

### #5 Keep a Changelog 2.0.0（MIT）

2.0.0（2026-06-07）相对 1.1.x 是**指南的破坏性修订而非格式的**：六种类型、`YYYY-MM-DD`、`Unreleased`、`[YANKED]` 全部不变，变的是页面结构与建议。新增且本 skill 要用的：
- Fixed / Changed / Security 的判据："旧行为是 bug 吗？是 → Fixed；是有意的而你在改它 → Changed"。
- `**Breaking:**` 标记**留在它所属的类型里**（通常 Changed 或 Removed），不单列一节——这样扫 Changed 的人在原地就看到破坏项。
- 必须说清"破坏的是什么接口"：命令行、库 API、网络协议、文件格式还是配置 schema。
- 升级步骤短则写进条目（"把 `color` 选项改名为 `theme`"），长则外链迁移指南——长流程会埋掉"改了什么"，把可扫读的记录变成 how-to。
- Dependencies 不是一种变更类型；Known issues 是被发现的而不是被改的。
- changelog ≠ release notes：changelog 是仓库里的完整记录，release notes 是单次发布的公告，从前者派生。
- "机器可以起草，人来筛选"：模型判不了什么对你的读者算 notable。

### #4 Google 开发者文档风格指南（CC-BY-4.0）

`/style/translation` 是本 skill「面向非母语读者」一节的唯一可机械检查来源。抽查三条对照原文核实通过：
- `only` 必须紧贴它修饰的词（`Request only one token.` 而非 `Only request one token.`）；
- 不要超过两个名词连用作定语（`A cloud-native DevSecOps pipeline in a hybrid environment` 而非 `A hybrid cloud-native DevSecOps pipeline`）；
- 不要省略 `that` / `then` / `of`（`If the attribute key is not found, then the default value is returned.`）。
`/style/code-samples` 给出代码示例的引入句规则（紧接示例用冒号，中间还有别的材料用句号）与"省略的代码用该语言的注释表示，不用 `…`；含省略的代码块不要标成可一键复制"——后者正是"代码块必须能粘贴运行"这条规则的官方依据。

### #7 google/styleguide `docguide/`（CC-BY-3.0）

`READMEs.md` 60 行，但有两条别处没有的硬条目：`README.md` **不放在文档目录里**，放在代码包顶层；包级 README 必须包含或指向"这是什么/联系人/是否弃用或不对外/怎么用（可复制的命令）/相关文档链接"。`best_practices.md` 的"文档离它描述的代码越近越好"是同步审计一节的立论依据。

### #8 addyosmani/agent-skills `skills/documentation-and-adrs`

ADR 一节的"先匹配既有约定"三条（位置与格式、编号与命名、章节标题集）比任何模板都重要：在已有 `Documentation/Decisions/*.rst` 的仓库里新建 `docs/adr/0001-foo.md` 会产生第二套编号体系，之后没人知道哪套是权威。其 Rationalizations 表（"代码会自解释"→ 代码解释 what，不解释 why 与被否掉的方案）语义可搬。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | README 是否该有 LICENSE / CONTRIBUTING / CHANGELOG 章节 | awesome-copilot `create-readme`：不要写，那些有专门文件（#17）／google `docguide/READMEs.md`：包级 README 必须包含或**指向**弃用状态、联系人、相关文档（#7） | 采 #7 并明确区分「复制内容」与「指路」：README 不复制许可正文或贡献流程，但必须有一行指向它们；**弃用状态与联系人必须在 README 里**，因为那是读者在别处找不到的 | 官方厂商（Google）> 社区提示词；且 #17 那条会导致"这个包已废弃"无处可说 |
| 2 | changelog 的破坏性变更是否单列一节 | 常见实践与部分工具：单列 "Breaking changes" 节／Keep a Changelog 2.0.0：`**Breaking:**` 标记留在它所属的类型（Changed/Removed）内（#5） | 采 #5 | 更新（2026-06-07）> 更旧；且原文给出后果：单列会让扫 `Changed` 的人在原地看不到破坏项 |
| 3 | 文档结构是先搭四象限骨架还是从内容长出来 | 多数四象限 skill（#9、#13、#17）：按四类建目录再填／diataxis.fr：**明确点名**"建四个空壳"是不该做的事，结构从内容改出来（#3） | 采 #3；本 skill 只在已有内容需要归位时才谈目录 | 框架第一手来源 > 二手改写 |
| 4 | tutorial 用不用 "we" | mcollina（#9）/neo4j（#13）：tutorial 用 "we will…" 包容性表达／Google `/style/person`：一律用 "you" 直接称呼读者（#4） | 分场景：文档站 tutorial 允许 "we"（#1 的 voice-defaults 亦给 tutorial 开了这个口子），其余四类一律 "you"。正文只写这一种做法 | 两边都是权威，按适用范围切分而不是二选一；#1 已有先例 |
| 5 | 代码示例里的省略怎么写 | 广泛实践：`...` 或 `…`／Google `/style/code-samples`：用该语言的注释写省略，且含省略的块不要标成可一键复制（#4） | 采 #4 | 官方厂商；且后果明确：`...` 在 Python 里是合法字面量、在 YAML 里是文档分隔符，粘贴后报的错与省略无关 |
| 6 | "写给 agent 的文档"归谁 | #21 mattpocock `writing-for-agents` 把 AGENTS.md 与文档同套规则／#18 JPeetz 同样混在一起／本波次 Contract：SKILL.md 归 `skill-authoring` | 归 `skill-authoring`。本 skill 的 `## Scope` 显式排除 | 本波次跨 skill 边界契约 |
| 7 | 文档审计要不要顺手把文档改好 | #2：默认只读，除非用户明确要求更新／#1：用户说 "improve"/"fix" 才改，说 "review" 就只报 | 两者一致，采「说 review 只报、说 fix 才改」并写明后果：被要求评审时直接重写，作者学不到东西，也看不出原稿错得多厉害 | 两家主张相容，取更具体的措辞 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `mblode-docs-writing` | mblode/agent-skills `skills/docs-writing` | merged | 类型门控（哪条规则只适用于哪类文档）、"示例跑过 + 链接解析过"作为退出标准、审计输出契约、假密钥与手写日期两条陷阱 |
| `copilot-docs` | github/awesome-copilot `skills/docs-sync-audit`、`skills/github-release/references`、`instructions/update-docs-on-code-change` | merged | 文档漂移审计的证据标准与 P0–P3 分级、只读约束、三类确定性断言、代码改动→文档说谎的触发清单、从 diff 判 SemVer 级别 |
| `diataxis` | diataxis.fr（Diátaxis 框架文档） | merged | 四象限与 compass 真值表的**语义**、"不要先建空目录"、how-to 从用户项目出发、功能性质量与深层质量的分界。CC-BY-SA-4.0：只取结构与清单语义，全文自撰 |
| `google-devdocs-style` | developers.google.com/style | merged | 面向全球读者的可机械检查句式条目、代码示例引入句与省略写法、术语一致性 |
| `keep-a-changelog` | olivierlacan/keep-a-changelog | merged | 六种变更类型与 Fixed/Changed/Security 判据、`**Breaking:**` 留在原类型内、破坏的是哪个接口、`Unreleased` 与 compare 链接、changelog vs release notes |
| `mattpocock-skills` | mattpocock/skills `.agents/writing-docs.md`、`skills/productivity/teach` | merged | "defining constraint"（一句话说清这东西与默认做法的差别）、真问题采集而非凭空编问题、可自检条目的判定标准 |
| `google-styleguide` | google/styleguide `docguide/` | merged | README 的位置与最低内容集、"文档离代码越近越不容易腐烂" |
| `addyosmani-skills` | addyosmani/agent-skills `skills/documentation-and-adrs` | merged | ADR 先匹配仓库既有约定、ADR 生命周期与 supersede、Rationalizations 表语义 |
| `mcollina-skills` | mcollina/skills `skills/documentation` | merged | 四象限的用户信号判据表、每类的可判定验证问句（如 reference 的 30 秒查得到） |
| `madr` | adr/madr | reference | ADR 字段语义（尤其 `Confirmation`：这条决定将来靠什么验证）；模板本身不复制 |
| `jph-adr` | joelparkerhenderson/architecture-decision-record | reference | **许可裁决**：实读 `LICENSE.md` 为 CC-BY-NC-SA-4.0，NC 条款 → 不得 merged。仅用于确认 ADR 模板家族的覆盖面 |
| `neolab-write-concisely` | NeoLabHQ/context-engineering-kit `antigravity/skills/write-concisely` | reference | **许可裁决 + 内容裁决**：GPL-3.0 → reference；且内容为 1918 年 Strunk 原文转载，规则写不出违反后果。仅确认"句式层需要被覆盖"这一点 |

## 基线缺口

无 skill（`uv run tools/run_evals.py technical-writing --baseline`，claude-opus-5 · medium）时，
各场景未达成的 `expected_behavior`。评判依据是交付给用户的答复本身（`answer.md`）与它写进
工作区的产物，不是它在别处留下的中间记录。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 README 重构 | 无（9/9 全达成） | **零区分度**。基线自己认出四种文档被揉在一起、把教程与参考指回已存在的 `docs/getting-started.md` / `docs/reference.md`、合并了两处 installation、逐条列出 13 项与源码不符的断言（含 `make docs-serve`/`npm run docs` 不存在、`docs/concepts.md` 不存在、CLI 是 `corral` 不是 `corral-cli`）、并且明确写下"README 里除小速查表外不再复制默认值，参考数据只住在 `docs/reference.md`"。处理见下文说明 |
| 2 教程修复 | #8「保持单一路径」部分未达成 | 定位完全正确（指出真正的断点是 Step 2 的 token，早于读者报告的 Step 3；逐块实测出 5 个错误）。但重写后的产物把 4 步扩成 9 步，末尾追加了一张 2.x→3.x 迁移表（首次运行的读者不需要的参考材料），并在 Step 2 给出"传 `token=` 或写进环境"两种做法、Step 3 给出"已有 Redis 则跳过"分支——首次运行页面上出现了选择 |
| 3 参考文档漂移审计 | 9 条中 8 条未达成（只达成 #1 只读） | **最大缺口，且与写作能力无关**：基线把完整审计写进了 `.agent-logs/0001-*.md`，交给用户的答复只有三行「Audit logged to `.agent-logs/...`. Nothing in the repo was modified.」。用户的要求是"告诉我具体哪几行在撒谎"，而交付物里没有任何一条 finding、任何一个 `path:line`、任何一个分级。日志里的内容质量很高（11/14 条构造器断言判错、分层给出阻塞级/取值错误/打包失实/勿动/遗漏），但那不是交付 |
| 4 changelog 重写 | 9 条中 5 条未达成 | 噪音清理、六类分组、旧新名并存与 `max_attempts` 语义说明、`YYYY-MM-DD` 日期都做到了。未达成：(a) **没有任何逐条 `**Breaking:**` 标记**，只在版本级写了一句"Breaking release"；(b) 没有逐条说明破坏的是哪个接口（API / 环境变量 / 安装）；(c) 缺 `Unreleased` 节，版本链接指向 `releases/tag/`（发布页）而不是 `compare/` 差异，preamble 还把 Keep a Changelog 钉在已被 2.0.0 取代的 **1.1.0**；(d) 完全没提"3.0 的这些移除在 2.4.x 里从未标过 Deprecated"；(e) **把 changelog 变成了升级手册**——在 `CHANGELOG.md` 内部塞进六节带 `diff` 的迁移步骤，正是本 skill 明令外链的那种长流程 |
| 5 负例（打包 runbook 为 skill） | 无（3/3 全达成） | `skill_read=false`。答复全是 skill 编写机制（frontmatter 字段、description 的触发词面、目录布局），没有滑向 Diátaxis / README / changelog 话题 |

**关于场景 1 的零区分度**：`expected_behavior` 已经是可机械验证的产物属性（install 出现几次、哪些命令不存在、哪个符号不在源码里、参考表是否被复制），基线仍然全中。这不是题目太软，而是「对着源码核对一份 README 并重排」确实是强模型的强项。按标准要求**如实记录、不改判、不为了制造缺口而降低标准**：本 skill 在这一类任务上的价值不是能力补齐，而是把这次做对的事情固定成规则（rule 2/11/12、`restructure` 工作流的验证门），下次不依赖模型当场想起来。区分度由场景 3 与 4 提供。

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 README 重构 | claude-opus-5 · medium | 无（基线） | false | 9 / 9 | 零区分度，见「基线缺口」。诊断与事实核对都对，但交付是散文式诊断 + 重写全文 |
| 1 README 重构 | claude-opus-5 · medium | 有 | true | **9 / 9** | 差别在形态而非结论：按 `Output format` 的 restructure plan 出表（section / 类型 / 去处 / 目标页是否存在），`docs/concepts.md` 从「不存在所以删掉那段 explanation」变成**本次新建并写出来**，Documentation 链接区显式写明「Reference is authoritative for defaults; this page shows only the ones a first run prints」（rule 11），并把「reference.md 未随附、无法确认那张表是否已正确」列为残留风险 |
| 2 教程修复 | claude-opus-5 · medium | 无（基线） | false | 8 / 9 | 未达成 #8：重写为 9 步并加了 2.x→3.x 迁移表与「传 `token=` 或写进环境」「已有 Redis 可跳过」两处分支，首次运行页上出现了选择 |
| 2 教程修复 | claude-opus-5 · medium | 有 | true | **9 / 9** | 单一路径成立：删掉 step 7（部署明确判给 how-to），不建新页，Next steps 只链 `reference.md`。每个可运行步骤以**实测捕获**的输出结尾；`request`/`acquire` 都是 `NotImplementedError` 这一项被作为阻塞项上报且**拒绝伪造输出**（rule 9），另如实列出 `redis-cli ping` 与 extra 安装未验证 |
| 3 参考文档漂移审计 | claude-opus-5 · medium | 无（基线） | false | 1 / 9 | 把完整审计写进 `.agent-logs/`，交付给用户的只有三行「Audit logged to …」。要求是「告诉我哪几行在撒谎」，交付物里零条 finding |
| 3 参考文档漂移审计 | claude-opus-5 · medium | 有 | true | **9 / 9** | 按 `Output format` 的 Docs audit 契约**当面交付** 14 条确认 + 3 条推断，P0 4 条；每条 `Drift / Impact / Evidence / Fix` 四段，docs 与 source 两侧都给 `path:line`；`CORRAL_TIMEOUT` 的否定性结论带 grep 命令；`Checks run` / `Not checked` / `Inferred, not confirmed` 三节齐全；全程只读。并且按 rule 13 主动补了「reference 不完整」一条（`Limiter` 协议、`retry_after`、`ValueError` 未文档化），这不在 `expected_behavior` 里 |
| 4 changelog 重写 | claude-opus-5 · medium | 无（基线） | false | 4 / 9 | 未达成：逐条 `**Breaking:**` 标记、逐条点名破坏的接口、`Unreleased` 与 `compare` 链接（写成了 `releases/tag/`，preamble 还钉在已被取代的 KaC 1.1.0）、缺失 deprecation 周期的说明、以及**把 changelog 变成了六节带 diff 的升级手册** |
| 4 changelog 重写 | claude-opus-5 · medium | 有 | true | **9 / 9** | 每条破坏项 `**Breaking** (Python API) / (environment) / (install)` 留在 `Changed`/`Removed` 内；`Unreleased` + 逐版本 `compare/` 链接（最旧版指向自己的 tag）；preamble 钉 `keepachangelog.com/en/2.0.0/`；显式写出「Nothing below was deprecated in a 2.x release first — 2.4.1 shipped no warnings」且**没有回填假的 Deprecated 条目**；升级动作压在条目内（`max_attempts=max_retries + 1`），没有另起迁移流程；两处无据的旧值（token 旧变量名、3.0 的合法 backoff 集合）如实标注不可考 |
| 5 负例（搭 mkdocs 文档站） | claude-opus-5 · medium | 有 | **false** | 4 / 4 | 未读 `skills/technical-writing/SKILL.md`。交付 `mkdocs.yml`（nav 显式列全 15 页）+ `validation:` 段 + `mkdocs build --strict` + Pages 部署 workflow，并在 `/tmp` 用同构目录**实跑**验证（正常构建零警告；把链接改成不存在的 `nope.md` → `Aborted with 1 warnings in strict mode!`, exit=1）。未审内容、未重排四象限，末尾只提了一句「内容审计要另开一轮」 |

结论：**通过**。基线未达成的 14 条行为（2#8、3 的 8 条、4 的 5 条）在有 skill 时全部达成，场景 3 从 1/9 到 9/9、场景 4 从 4/9 到 9/9。负例 `skill_read=false`。

### 负例的两次未通过与真实原因

负例前两版都是 `skill_read=true`，按要求逐次收紧 `description` 后重跑，第三版才 false。原因不是边界写得含糊，而是**这个 skill 的 `description` 自己伸手把题目接了过来**：

1. **第一版负例**「把部署 runbook 打包成 agent skill」。转录里模型的思考是：「用户要 SKILL.md frontmatter，而指引说 technical-writing 管人读的文档、SKILL.md 归 skill-authoring —— 但可用 skill 列表里只有 technical-writing，我得先确认 skill-authoring 是否存在」，于是先 `read skill://skill-authoring`（失败，不计入），再 `read skill://technical-writing`，intent 写的是 "Checking technical-writing scope"。`run_evals.py` 对非基线一律传 `--skills <skill>`，场景里的 `skills: []` 不会改变可用集合，所以**被排除的邻居 skill 在评测里永远不可加载**；一旦否定边界点名一个加载不到的 skill，模型就会回头翻唯一在场的那一份来定夺。这是评测装置与 `description` 交互产生的，不是内容缺陷——同一次运行里它给出的答案完全正确（skill 编写机制，无任何 Diátaxis/README 串味）。
2. **第二版负例**换成「用 mkdocs-material 把 `docs/` 搭成站点」，中心落在工具链。仍然 true，思考是：「这是文档基础设施，technical-writing 可能相关，我先看仓库状态再决定怎么用它」。根因找到了：当时的 `description` 第一句把 **`docs sites`** 列为本 skill 的覆盖物，题目里的「搭文档站」正好咬住这个词。
3. **第三版**做两处修改：覆盖物清单里 `docs sites` → `documentation pages`（管页面，不管站点），并加一句正面声明 `It governs what pages say, never the tooling that builds them.` 与一条排除项 `for configuring a docs-site generator`。重跑即 `skill_read=false`，而且模型在答复末尾自己写出「`technical-writing` 技能明确把「配置文档站生成器」排除在外，所以这次只做工具链、没动内容」——说明它是**只读 `description` 就完成了路由**，正是 `description` 应该承担的全部工作。

第一版负例的题目（打包 runbook 为 skill）予以保留记录但不作为评测场景：在 `run_evals.py` 当前的 `--skills` 语义下它测不出东西。`SKILL.md` 与 `AGENTS.md` 的边界仍在 `description` 的 `Do not use for` 与 `## Scope` 里写明。

### 运行记录

- 基线：五场景一次跑完（130.8s / 211.5s / 110.0s / 133.9s / 152.7s），`events_bytes` 均在 0.34–0.95 MB，无超时。
- 有 skill：因 `description` 前后调整过，场景 1–4 在最终文件上**重跑过一遍**（204.0s / 184.4s / 136.1s / 87.4s），表中记的是重跑结果；负例记第三版（133.7s）。

## 备注

### 这个 skill 相比不加载它，产生了什么可观察的差别

四类，按可观察性从强到弱：

1. **审计结果会不会真的交到人手上。** 场景 3 的基线把一份质量很高的审计写进 `.agent-logs/`，答复只剩三行；有 skill 时同一份内容按 `Output format` 的 Docs audit 契约当面交付，14 条确认 + 3 条推断、两侧 `path:line`、`Checks run` / `Not checked` / `Inferred, not confirmed` 三节齐全。1/9 → 9/9。**这是本 skill 最大的一处差别，而它不是写作能力**——是「交付物是什么形状」被写死在了 skill 里。
2. **changelog 的破坏性变更能不能被扫读到。** 基线写了「Breaking release」当版本级抬头，然后另起六节带 `diff` 的升级手册；有 skill 时每条破坏项带 `**Breaking** (Python API / environment / install)` 并留在 `Changed`/`Removed` 原位，升级动作压回条目（`max_attempts=max_retries + 1`），`Unreleased` 与 `compare/` 链接补齐，preamble 从过期的 KaC 1.1.0 钉到 2.0.0，并显式说出「这些移除在 2.4.x 从未标过 Deprecated」。对一个在 `Changed` 里扫一眼就走的读者，前者等于没标。
3. **教程会不会为了「完整」把首次运行的路径重新变宽。** 基线修好了所有断点，却顺手加了迁移表和两处分支；有 skill 时删掉部署那一步（判给 how-to）、不建新页、Next steps 只留一条链接。教程的单一路径是最容易在「顺手补全」中丢掉的属性，而它一丢，读者又回到有选择就停下的状态。
4. **拒绝伪造。** 两组都发现了 `request()`/`acquire()` 是 `NotImplementedError`，但有 skill 的三个场景都把「输出无法捕获」当成需要上报的阻塞项，并明确写出哪几块没跑过（rule 9 + 各 workflow 的验证门）。基线也提了，但是作为末尾的一句提醒。

反过来说清楚**没有**产生差别的地方：场景 1（README 对着源码核对并重排）基线就是 9/9。差别只在交付形态（restructure plan 表、新建 `docs/concepts.md` 而不是删掉那段 explanation、显式声明 reference 权威）。这一类任务上本 skill 买到的是可重复性，不是能力。

### 许可注意事项

- **diataxis.fr 实读结论**：仓库 `evildmp/diataxis-documentation-framework` 的 `LICENSE.rst` 首行是 `Creative Commons Attribution-ShareAlike 4.0 International`，即 **CC-BY-SA-4.0**；GitHub API 的 `license.spdx_id` 报的是 `NOASSERTION`，不能据此判断。注意仓库里还有一个 `LICENSE`（无扩展名）路径不存在，`base64 -d` 会报错——要读的是 `LICENSE.rst`。按 `docs/roadmap.md`「许可处理规则」CC-BY-SA-4.0 → `merged`，但**只取结构与清单语义，全部自己重写**：`references/document-types.md` 里的 compass 判据表、四类各自的义务、「不要先建空目录」、how-to 从用户项目而非机器功能出发，都是按语义重写的，没有搬任何一句原文、一张表或一张图。
- 同类陷阱各一处，均已实读 LICENSE 正文而非信 API：`google/styleguide` API 报 NOASSERTION，实际是 CC-BY-3.0（`LICENSE` 首行 `Attribution 3.0 Unported`），attribution-only，按 CC-BY-4.0 同等处理；`adr/madr` API 报 NOASSERTION，实际 `MIT OR CC0-1.0`，且默认分支是 `develop`；`joelparkerhenderson/architecture-decision-record` API 报 NOASSERTION，实际 `LICENSE.md` 写明作者自撰部分为 **CC-BY-NC-SA-4.0**——**NC 条款**，与 redis.io/docs、elastic 文档同类，16.9k★ 也不得 merged，已降为 `reference`。
- `developers.google.com/style` 的许可来自页脚自己的声明（CC-BY-4.0，代码样例 Apache-2.0），署名已进 `NOTICE.md`。它的「参考层级」推荐 Microsoft Writing Style Guide，本 skill **不跟随**：现行版本在 learn.microsoft.com 上是专有的（与波次 6 对 learn.microsoft.com 的裁决一致），GitHub 镜像 `MicrosoftDocs/microsoft-style-guide` 虽是 CC-BY-4.0 但已 archived、最后推送 2024-11-13，按量表新鲜度 0 直接 REJECT。
- 两处双重降级（许可 + 内容）：`NeoLabHQ` `write-concisely`（GPL-3.0；且 1044 行里约 990 行是 1918 年 Strunk 原文转载，规则写不出违反后果）、`github/awesome-copilot` 的 `create-readme` / `readme-blueprint-generator` / `documentation-writer`（许可 MIT 没问题，是**内容裁决**：三份 144 行全是提示词，且 `create-readme` 的「不要写 LICENSE/CONTRIBUTING/CHANGELOG 章节」与 Google 的「包级 README 必须说明弃用状态与联系人」相左）。

### 未验证项

- `references/plain-english.md`、`references/code-examples.md` 里标 `[official]` 的条目全部对 developers.google.com 的对应页面逐条复核过原文措辞（`/style/translation` 页脚 Last updated 2026-08-25，`/style/code-samples` 2025-10-10）。标 `[community]` 的三条（reference 的 30 秒查得只判定、类型门控表、审计证据标准）来自上游 skill 而非厂商文档，无法对官方文档取证，已按标准标注置信度。
- 本 skill 不含 `scripts/`。候选 #2 的 `scripts/docs_drift.py` 有真实价值，但它围绕被审仓库的形态设计（扫 `package.json` scripts、`make` 目标、相对链接、env var 双向比对），搬过来无法满足本仓库「自包含 + 无魔法数 + 本机跑通」三条；改为在 `references/docs-code-sync.md` 把那三类**有确定答案的断言**写成「用仓库自己的工具怎么查」。
- 夹具里的 `corral` 是虚构项目，`client.py` / `limiter.py` 的 `request()` 与 `acquire()` 故意留 `NotImplementedError`——这不是疏漏：它让「拒绝伪造输出」成为一个能被观察到的行为，两组评测都因此暴露了各自对待「跑不通」的态度。

### 未来同步时要盯的上游

| 上游 | 盯什么 |
|---|---|
| `olivierlacan/keep-a-changelog` | `source/en/` 下出现 2.1 或 3.0 目录即为指南改版。`references/changelog.md` 顶部的 `Verified against: Keep a Changelog 2.0.0` 与 preamble 里钉的 `/en/2.0.0/` 链接要同步 |
| `developers.google.com/style` | `/style/translation`、`/style/code-samples`、`/style/word-list` 的 Last updated；`kind: docs` 只能人工比对 |
| `mblode/agent-skills` | `skills/docs-writing/rules/` 的规则数（当前自述 51 条）与类型门控表；该仓库推送很频繁 |
| `github/awesome-copilot` | `skills/docs-sync-audit`（含其 `scripts/docs_drift.py` 的检查项是否扩充）与 `skills/github-release/references/` |
| diataxis.fr | `source/*.rst` 的实质修订。作者近年改动集中在 `how-to-use-diataxis.rst` 与 `quality.rst`，四类定义已稳定 |

### 放弃的方向

- **不做「文档站工具链」一节**（mkdocs / Docusaurus / Sphinx 配置）。它是站点构建而不是内容，且负例第二版已经证明：只要 `description` 把 `docs sites` 列进覆盖物，这个 skill 就会被无关的工具链请求吸住。`## Scope` 与 `description` 两处都写明排除。
- **不做 Markdown 语法层规范**（标题层级、表格对齐、行宽）。`google/styleguide` 的 `docguide/style.md` 有 845 行这类内容，但它是 Google 内部渲染器（Gitiles）的约束，且项目的 formatter/linter 比任何散文规则都可靠。
- **不做「写给 agent 读的文档」**（`AGENTS.md`、`CLAUDE.md`、规则文件）。按本波次 Contract 归 `skill-authoring`；候选 #18、#21 都把它和面向读者的文档混在一套规则里，是它们被拒的原因之一。
