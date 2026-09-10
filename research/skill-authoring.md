# skill-authoring 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-10（种子报告 `local/research-spec.md` 同日产出）
- 复核日期：2026-09-10（本文所有 stars / `pushed_at` / license 均为当日 `api.github.com` 实测；
  规范与厂商文档为当日实读）
- 检索途径：
  - `web_search`：`"skill-creator" OR "writing-skills" OR "skill authoring" agent skill SKILL.md github 2026`、
    `site:skills.sh skill creator authoring meta skill`
  - <https://www.skills.sh>（命中 grafana/skills、getsentry/skills、mgechev/skills-best-practices、
    kensaurus/cursor-kenji 等）
  - 领域官方组织仓库：`anthropics/`、`openai/`、`vercel-labs/`、`agentskills/`、`grafana/`、`getsentry/`
  - 官方规范与厂商文档：agentskills.io、platform.claude.com、code.claude.com、cursor.com、learn.chatgpt.com
- GitHub API 核对方式：`https://api.github.com/repos/<owner>/<repo>` 取
  `stargazers_count` / `pushed_at` / `license.spdx_id`。**复核期间匿名配额被打满（HTTP 403）**，
  其后的仓库改用 `git ls-remote --symref` 定位默认分支 + blobless 浅克隆读取实际文件，
  已在下表「许可」列标注取证方式。skill 目录级许可以 `LICENSE.txt` 原文为准，不采信仓库根的
  `license: null`。

### 当日核实的关键事实（与种子报告的差异）

1. `anthropics/skills/skills/skill-creator/LICENSE.txt` 当日实读为 **Apache-2.0**
   （`Copyright 2026 Anthropic, PBC.`），与四件套文档 skill 的专有许可不同 → 可 `merged`。
2. `openai/skills` 当日仍有推送（2026-09-08），但 README 自述 deprecated；其
   `.system/skill-creator` 深度绑定 Codex 运行时（`init_skill.py`、`agents/openai.yaml`、
   `quick_validate.py`）→ 不作为 merged 上游。
3. grafana 的授权 skill 实际路径是 `skills/grafana-core/skill-authoring/`（skills.sh 展示的
   `grafana/skills/skill-authoring` 省略了 plugin 层），种子报告未收录该候选。
4. `npx skills` 的 Cursor 项目路径当日已是 `.agents/skills/`（全局 `~/.cursor/skills/`）；
   支持 agent 数当日为 79（README 自述 “4 + 75 more”）。
5. Codex 初始 skill 列表预算当日仍为「上下文窗口 2%，未知时 8000 字符，先压缩 description」。
6. `curiositech/some_claude_skills` 的 `skill-architect` 在当日的默认分支上找不到
   （raw 404），按「无法定位」处理。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | anthropics/skills `skills/skill-creator/`（+ `references/schemas.md`、`agents/`、`scripts/`、`template/SKILL.md`） | https://github.com/anthropics/skills | 175553 | 2026-09-03 | Apache-2.0（skill 内 `LICENSE.txt` 当日实读） | 建 skill、跑评测、优化 description | 3 | 2 | 3 | 3 | 2 | 13 | INCLUDE | 唯一由格式提出方维护的授权 skill；description「略推销」策略、20 条触发查询 + 60/40 划分、评测 schema 字段名都只有这里有 |
| 2 | Anthropic《Skill authoring best practices》 | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices | — | 活文档（当日实读全文 1192 行） | NONE（厂商文档） | 核心原则、结构、评测先行、脚本规则、发布前清单 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE (docs) | 「自由度与脆弱性匹配」、进阶披露三模式、Claude A/Claude B 迭代法、导航观察四信号、solve-don't-defer、voodoo constants、发布前三组清单的唯一权威出处 |
| 3 | obra/superpowers `skills/writing-skills/` | https://github.com/obra/superpowers | 284401 | 2026-09-10 | MIT | 用 TDD 纪律写 skill | 2 | 3 | 3 | 2 | 2 | 12 | INCLUDE | RED/GREEN/REFACTOR、「没看它失败就不知道教对了没」、token 预算、动词优先命名、禁 `@path`、Match-the-Form-to-the-Failure 表、微测试方法论。正确性扣分见「深度审查」 |
| 4 | agentskills.io 规范 + agentskills/agentskills `skills-ref/` | https://agentskills.io/specification | 25194 | 2026-08-09 | Apache-2.0 | 规范字段表、目录、进阶披露、校验 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE (docs) | 唯一规范来源：`name` 六条约束、`description` 1024、`compatibility` 500、`metadata` 为 string→string、`allowed-tools` 实验性、`skills-ref validate` |
| 5 | vercel-labs/skills（`npx skills` CLI README） | https://github.com/vercel-labs/skills | 30900 | 2026-09-08 | MIT | 安装器、仓库扫描规则、各 agent 路径表 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 容器目录清单 + 三层深度遍历 + 浅层遮蔽深层、`metadata.internal`、marketplace 清单发现、下载/解压上限、能力矩阵 |
| 6 | Claude Code skills 文档 | https://code.claude.com/docs/en/skills | — | 活文档（当日实读） | NONE（厂商文档） | Claude Code 扩展字段与发现路径 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE (docs) | 21 个非规范字段的完整表、1536 字符列表截断、`synced` 保留名、企业 > 个人 > 项目的反向优先级、「Claude Code 之外只能用规范字段」的官方警告 |
| 7 | Cursor skills 文档 | https://cursor.com/docs/skills | — | 活文档（当日实读） | NONE（厂商文档） | Cursor 扩展字段与发现路径 | 3 | 3 | 2 | 3 | 0 | 11 | INCLUDE (docs) | `paths`（旧名 `globs`）、`disable-model-invocation`、`icon`/`color`；递归扫描且嵌套目录自动路径限定 |
| 8 | Codex / ChatGPT build-skills 文档 | https://learn.chatgpt.com/docs/build-skills | — | 活文档（当日实读） | NONE（厂商文档） | Codex 发现路径、截断预算、`agents/openai.yaml` | 3 | 3 | 2 | 3 | 0 | 11 | INCLUDE (docs) | 2% / 8000 字符预算与「先压缩 description」是「关键用途前置」这条规则的唯一依据；`allow_implicit_invocation` |
| 9 | grafana/skills `skills/grafana-core/skill-authoring/`（+ 4 个 references） | https://github.com/grafana/skills | 250 | 2026-09-09 | Apache-2.0 | 按四维量表写与审 skill | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 四维评分量表（conciseness / actionability / workflow clarity / progressive disclosure）、「LLM 评委分数跑动 7–10 分，连过三次再交」、「路由型文档不要被优化器内联回去」 |
| 10 | getsentry/skills `skills/skill-writer/` | https://github.com/getsentry/skills | 989 | 2026-09-07 | Apache-2.0 | 纯路由型授权 skill | 2 | 3 | 2 | 3 | 2 | 12 | INCLUDE | 纯路由 SKILL.md 形态：全部 reference 扁平 + 每行一个 “open when...” 理由；「加新指导前先说清要收窄/删掉哪一条」；产出契约四段式 |
| 11 | mgechev/skills-best-practices `skill/` | https://github.com/mgechev/skills-best-practices | 2252 | 2026-07-27 | NONE（仓库无 LICENSE；blobless 克隆当日核实） | 六步授权流程 + 元数据校验脚本 | 2 | 2 | 3 | 3 | 0 | 10 | INCLUDE | 「hallucination gaps」= 正文里逼模型猜的位置；「不要造 README/CHANGELOG 这类给人看的文件」；校验脚本 stderr 自纠环 |
| 12 | 本仓库 `docs/skill-standard.md`、`docs/workflow.md`、`tools/` | https://github.com/Lynricsy/HyperSkills | — | 当日 | MIT | 可机械执行的规范 + 溯源 + 评测运行器 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE (docs) | `SOURCES.yaml` 溯源模式、NOTICE 生成、15 项校验清单、`evals.json` + 基线对照的运行器形态——`publishing.md` 与 `evaluation.md` 的骨架就是它的英文版 |
| 13 | Ronifue/skill-authoring | https://github.com/Ronifue/skill-authoring | 54 | 2026-07-07 | MIT | 触发可靠性、路由、清单、反漂移 | 1 | 2 | 3 | 2 | 2 | 10 | MAYBE → reference | 内容扎实（任务路由表、Anti-Drift、安装前审计），但个人仓库、无第三方验证；且它把 description 写成 `Load when...` 引号短语堆叠，与规范推荐的第三人称「什么 + 何时」不同——只作交叉校验，不合入措辞 |
| 14 | openai/skills `skills/.system/skill-creator/` | https://github.com/openai/skills | 26824 | 2026-09-08 | 见 skill 内 `LICENSE.txt` | Codex 向的授权指南 | 3 | 3 | 2 | 3 | 1 | 12 | REJECT as upstream | 仓库 README 自述 deprecated，且正文绑定 Codex 专属机制（`init_skill.py`、`agents/openai.yaml`、`quick_validate.py`）。其「context window is a public good」「不要造额外文档文件」两条与 Anthropic 文档同源，从后者取 |
| 15 | openai/skills `skills/.curated/aspnet-core/references/_sections.md` | https://github.com/openai/skills | 26824 | 2026-09-08 | 见 skill 内 `LICENSE.txt`（当日 HTTP 200） | 大型 skill 的 references 索引 | 3 | 3 | 3 | 3 | 1 | 13 | INCLUDE as reference | 只借结构惯例：`_sections.md` 用「Start Here 路径链 + Primary / Cross-Cutting 两张 open-when 表 + Reading Strategy」。不抄一字（同一 deprecated 仓库，按上一行的理由不做 merged） |
| 16 | openai/plugins | https://github.com/openai/plugins | 6347 | 2026-09-08 | NONE（API `license: null`） | 插件目录 | — | — | — | — | — | — | REJECT | 形态是 plugin 而非 skill；且全仓库无任何许可声明。打包分发的事实以 Codex 官方文档为准 |
| 17 | jkeskikangas/skills | https://github.com/jkeskikangas/skills | 10 | 2026-07-31 | Apache-2.0 | rubric 评分的授权 + 审查工作流 | 0 | 2 | — | — | 2 | ≤4 | REJECT | 10 star、无外部采用信号；其 rubric 思路已由 grafana（250★、厂商维护、CI 实跑）以更强证据覆盖 |
| 18 | bdfinst/agentic-dev-team `plugins/marketplace-dev/skills/agent-skill-authoring/` | https://github.com/bdfinst/agentic-dev-team | 281 | 2026-09-09 | MIT | 区分 agent 编排与 skill 知识 | 1 | 3 | 1 | — | 2 | ≤7 | REJECT | 内容是该仓库自身的 plugin/marketplace 约定，不可移植；「编排归 agent、知识归 skill」这条边界我们已通过 Scope 的否定范围表达 |
| 19 | itechmeat/llm-code `skills/skill-master/` | https://github.com/itechmeat/llm-code | 22 | 2026-09-04 | MIT | 授权 + 校验 + 触发评测 + 盲测 A/B | 0 | 3 | — | — | 2 | ≤5 | REJECT | 22 star 个人工作仓；盲测 A/B 与触发评测已由 skill-creator 原始出处覆盖 |
| 20 | DeerHide/agent_skills `skills/writing-skills/` | https://github.com/DeerHide/agent_skills | 0 | 2026-08-01 | MIT | 格式与授权指南 | 0 | 2 | — | — | 2 | ≤4 | REJECT | 0 star；内容是 Anthropic 文档 + obra 的二手汇总，且引入 MUST/SHOULD/MAY 强度分级——与「解释 why 而非堆 MUST」冲突 |
| 21 | oryanmoshe/agent-skills `skills/writing-skills/` | https://github.com/oryanmoshe/agent-skills | 2 | 2026-02-19 | NONE | 仓库自用授权约定 | 0 | 0 | — | — | 0 | ≤2 | REJECT | 超 6 个月无推送（新鲜度 0）+ 2 star + 无许可，三项独立否决 |
| 22 | kensaurus/cursor-kenji `meta-skill-creator` | https://github.com/kensaurus/cursor-kenji | 9 | 2026-09-10 | MIT | 元 skill 创建清单 | 0 | 3 | — | — | 2 | ≤5 | REJECT | 9 star 个人配置仓；「house limits」是其自家约定 |
| 23 | netlify/context-and-tools `skill-creator` | https://github.com/netlify/context-and-tools | 36 | 2026-09-04 | MIT | Netlify 产品向 skill 创建 | 1 | 3 | 1 | — | 2 | ≤7 | REJECT | 36 star，内容围绕 Netlify 部署上下文，与通用授权无关 |
| 24 | curiositech/some_claude_skills `skill-architect` | https://github.com/curiositech/some_claude_skills | 219 | 2026-09-06 | MIT | 「skill 架构师」 | — | — | — | — | 2 | — | REJECT | skills.sh 索引指向的路径在当日默认分支上 raw 404，无法定位实际文件；无法核实即不合入 |

## 深度审查

### 1. anthropics/skills `skill-creator`（491 行，全文读毕）

- **frontmatter**：只有 `name` + `description`，description 刻意「推销」并罗列触发场景。
- **结构**：SKILL.md 是工作流主干；`agents/{grader,comparator,analyzer}.md` 是子代理简报；
  `references/schemas.md` 放 JSON schema；`scripts/` 放评测机械（`run_loop.py`、`run_eval.py`、
  `aggregate_benchmark.py`、`improve_description.py`、`package_skill.py`、`quick_validate.py`）；
  `eval-viewer/generate_review.py` 渲染结果。
- **可迁移的规则**：description 是唯一触发机制、模型倾向「欠触发」所以要略推销、进阶披露三级
  （metadata ~100 词 / 正文 <500 行 / 资源无限）、>300 行 reference 加目录、按 variant 组织
  reference、祈使语气 + 解释 why、ALL-CAPS ALWAYS/NEVER 是黄旗、「三次运行都自己写了同一个
  helper 脚本」= 该把脚本打包进去、评测的 with-skill 与 baseline 必须同一轮同时发起、
  grading.json 必须用 `text`/`passed`/`evidence` 三个字段名、20 条触发查询 8–10 正 8–10 近似负、
  「明显不相关的负例什么都测不出」、60/40 训练/留出并按留出分选 `best_description`、
  「Principle of Lack of Surprise」安全条款。
- **agent 绑定**：重度绑定 Claude 生态（子代理、`claude -p`、`present_files`、Cowork/claude.ai 分节、
  HTML viewer 服务器）。这些机械**不移植**；只保留与 harness 无关的判据（同轮对照、
  留出集选优、非区分性断言的识别）。
- **与其他候选重叠**：与 obra 在 description、进阶披露、测试三处重叠，其中 description 一处直接冲突（见裁决 A1）。

### 2. obra/superpowers `writing-skills`（683 行，全文读毕）

- **主张**：写 skill 就是对「流程文档」做 TDD。RED = 无 skill 时看子代理违规并逐字记录它的
  合理化说辞；GREEN = 写最小 skill 关掉那些说辞；REFACTOR = 补新漏洞。
- **可迁移的规则**：description 只写触发条件、绝不摘要工作流（有实测证据：description 里写了
  "code review between tasks" 导致代理只做一次评审，而正文流程图要求两次；改成纯触发条件后
  才按正文走两阶段）；动词优先/动名词命名；token 预算按加载频率分级并用 `wc -w` 验证；
  跨 skill 引用只用**名字**、禁 `@path`（会立刻强制加载烧上下文）；
  **Match the Form to the Failure** 四行表（违纪→禁令+说辞表+红旗；输出形状错→正面配方/契约；
  漏要素→模板里的必填槽位；条件相关→挂在可观测谓词上的条件句）——并附实测：在自包含提示这个
  竞争激励下，禁令组产出的坏内容比配方组明显更多，甚至不如不给指导的对照组；
  「不要加 nuance 条款」「豁免条款不会限定作用域」；微测试方法论（每次调用一个全新上下文样本、
  必须有无指导对照组、每变体 ≥5 次、每个命中人工读一遍、方差本身是指标）。
- **正确性扣分（得 2）**：正文的 frontmatter 示例写 `name: Skill-Name-With-Hyphens`，与规范的
  「仅小写字母数字连字符」直接矛盾（其自身文件名是小写的，属文档笔误）；正文含
  `superpowers:<skill>` 命名空间与 `../using-superpowers/references/*.md` 跨 skill 相对链接，
  单独摘出即失效。两处都在合入时剔除。
- **agent 绑定**：中度（子代理压力场景、`render-graphs.js`、graphviz 约定文件）。graphviz 全删。

### 3. Anthropic《Skill authoring best practices》（1192 行，全文读毕）

- 独有内容：自由度三档与「窄桥 vs 开阔地」类比；进阶披露三模式（高层指南+引用 / 按域组织 /
  条件式细节）；「避免深层嵌套引用——模型遇到嵌套链可能用 `head -100` 预览而读不全」；
  >100 行 reference 加 `## Contents`；工作流清单 + 校验环两个模式（无代码版与有代码版各一例）；
  时间敏感表述改 `<details>` old-patterns；术语一致；模板模式的严格/灵活两种措辞；示例模式；
  条件工作流模式；**评测先行五步**（跑无 skill 找缺口 → 建三个场景 → 量基线 → 写最小指令 → 迭代）
  与 `{skills, query, files, expected_behavior}` 结构（本仓库 `evals.json` 即此结构）；
  Claude A / Claude B 迭代法；**导航观察四信号**（意外读取顺序 / 漏跟引用 / 反复读同一文件 /
  从未读的文件）；solve-don't-defer 与 voodoo constants；plan-validate-execute；
  MCP 全限定工具名 `Server:tool`；正斜杠；「不要罗列多个库，给一个默认 + 一个逃生口」；
  发布前三组清单（核心质量 10 项 / 代码与脚本 8 项 / 测试 4 项）。
- 与 skill-creator 的关系：同一团队，方向一致，文档版更系统、更少 harness 绑定 → 冲突时以文档为准。

### 4. agentskills.io 规范（当日实读）

- 六个 frontmatter 字段的精确约束；`name` 五条构造规则 + 必须等于父目录名；
  `description` 1–1024；`compatibility` ≤500 且「多数 skill 不需要」；
  `metadata` 是 string→string 且建议 key 名足够独特；`allowed-tools` 实验性、支持度不一。
- 进阶披露预算：metadata ~100 tokens、正文 <5000 tokens 推荐、资源按需；正文 <500 行。
- 引用规则：相对 skill 根的路径、保持一层深、避免深层引用链。
- 校验：`skills-ref validate ./my-skill`。

### 5. vercel-labs/skills（README 全文读毕）

- 容器目录清单（仓库根、`skills/`、`skills/.curated|.experimental|.system/`、`.agents/skills/`、
  `.claude/skills/` 及约 55 个客户端目录），**每个容器向下遍历三层**，浅层 `SKILL.md` 遮蔽其下嵌套；
  `--full-depth` 才扫容器之外。仓库唯一可声明的元数据是 `metadata.internal: true`。
  `.claude-plugin/marketplace.json` / `plugin.json` 里声明的 skill 也会被发现，且不受三层限制。
- 项目 `./<agent>/skills/`、全局 `~/<agent>/skills/`；默认符号链接，`--copy` 复制。
- 79 个 agent 的项目/全局路径表；能力矩阵记录 `allowed-tools`（Kiro CLI 与 Zencoder 为 No）、
  `context: fork`（仅 Claude Code）、hooks（Claude Code / Cline / Kiro CLI）。
- 下载 10 MiB、解压 25 MiB、1000 文件上限，可用三个环境变量放宽。

### 6. grafana/skills `skill-authoring`（99 行 + 4 个 reference，全文读毕）

- 四维量表（conciseness / actionability / workflow clarity / progressive disclosure，各 0–3）
  接 CI 分数门；每维给了「1–2 分怎么修」的对应动作。
- 两条别处没有的经验：**LLM 评委的分数跑动 7–10 分**，本地 94 常在 CI 落到 85，所以「连续三次
  满分再交」；**故意做成路由文档的 skill 不要让优化器把 bundle 内联回 SKILL.md**，而是在
  SKILL.md 里手写一段最小可复制的校验环，让它自身仍然可执行。
- 其 `references/anti-patterns.md` 基本是 Anthropic 文档的重述（自己也这么标注），不重复合入。
- 仓库绑定重（Tessl CLI、三份 marketplace.json、plugin 目录、CI 分数门）→ 只取量表语义与两条经验。

### 7. getsentry/skills `skill-writer`（全文读毕）

- 形态本身是最好的教材：SKILL.md 几乎只有六个步骤 + 五张「Open when you need to... / Read」表，
  40 余个 reference 全部扁平在 `references/` 下，每个都有一行触发理由。
- 两条可迁移规则：**「加新指导之前，先指出哪一条现有规则/章节应当被收窄、替换或删除」**
  （对抗 skill 单调膨胀）；**输出契约四段式**（Summary / Changes Made / Validation Results / Open Gaps）。
- 与本仓库标准的差异：它另立 `SPEC.md` 维护契约文件。本仓库用 `SOURCES.yaml` + `research/` 承担
  同一职能，不引入第三种约定。

### 8. mgechev/skills-best-practices（55 行 + checklist，全文读毕）

- 两条独有措辞值得吸收：**hallucination gaps** —— 正文里「逼模型猜」的位置，成稿前专门扫一遍；
  **不要在 skill 里造给人看的文件**（README / CHANGELOG / INSTALLATION）。
- 校验脚本设计成 stderr 自纠环（失败 → 读错误 → 改 → 重跑），与 Anthropic 的校验环模式同构。
- 无许可 → 按仓库宽松策略 `merged` 并在 `notes` 记明。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| A1 | description 里能不能出现工作流摘要 | obra：**绝不**，只写触发条件，并给出实测——摘要会变成代理走的捷径，正文被跳过；Anthropic（文档 + skill-creator）：写「什么 + 何时 + 关键词」，还要略推销，因为模型倾向欠触发 | **按 skill 类型分流**：多步工作流型 skill 的 description 只写触发条件（obra）；能力/参考型 skill 写「什么 + 何时 + 关键词」（Anthropic）。**两类都必须含否定边界。** | 两方各有实测，且各自的实测对象不同类（obra 的反例是带流程图的工作流 skill，Anthropic 的正例是 pdf/xlsx 这类能力 skill）。按「更新 > 更旧」无法裁决，按证据适用范围分流 |
| A2 | 命名风格 | obra：动词优先/动名词（`creating-skills`）；Anthropic 文档：推荐动名词，但明确接受名词短语（`pdf-processing`）与动作式（`process-pdfs`）；本仓库现有 skill 是领域名词（`apple`、`react`） | 正文只给一条判据：**名字要说清「做什么」**；生态/领域型 skill 用领域名，任务型 skill 用动名词。不把动名词写成硬规则 | 官方厂商 > 公认专家；且硬规则会与本仓库自己的既有命名冲突，属于自相矛盾 |
| A3 | 「MUST/NEVER」还是「解释 why」 | Anthropic + skill-creator：ALL-CAPS ALWAYS/NEVER 是黄旗，解释 why 更有效；DeerHide 等社区仓：引入 MUST/SHOULD/MAY 强度分级 | 采用「解释 why」；只有真正的硬约束才用强制语气。DeerHide 已 REJECT | 官方厂商 > 社区 |
| A4 | 禁令还是配方 | obra 的实测：面对竞争激励，禁令式措辞（"don't X"）比正面配方更差，甚至不如无指导对照；Anthropic 文档没有涉及这一层 | 采用 obra 的 Match-the-Form-to-the-Failure：先给基线失败分类，再选形式；**只有「明知规则仍违反」这一类才用禁令 + 说辞表** | 唯一有头对头实测的一方；不与官方文档冲突（官方未表态），属补充 |
| A5 | 一个 skill 该多大 / 是否拆成纯路由 | getsentry：极端路由化（SKILL.md 只有表格，40+ reference）；grafana：SKILL.md 本身也必须独立可执行，别让优化器把 bundle 内联；Anthropic：正文 <500 行 + 一层引用 | 采用 grafana 的折中：SKILL.md 必须自身可执行到「不读任何 reference 也能完成常规任务」，reference 承载深度；路由表是导航层不是全部内容 | grafana 的说法是对 getsentry 形态失效方式的直接修正（评委/优化器会把纯路由判为低分并试图内联），且与官方「正文是概览 + 指针」一致 |
| A6 | 评测的机械形态 | skill-creator：workspace 目录树 + iteration-N + grading.json/benchmark.json + HTML viewer + 子代理 grader；本仓库：`evals/evals.json` + `run_evals.py` + `--baseline` | 正文写与 harness 无关的**步骤与判据**（同轮对照、逐条判定、留出集、多模型、识别非区分性断言），把具体文件树留给各自的工具；`references/evaluation.md` 同时记录 skill-creator 的字段名，因为读到那套产物的人需要知道 | 官方机械绑定 Claude 子代理与浏览器，不可移植；但字段名是事实性信息，值得保留 |
| A7 | 各 agent 的扩展字段能不能写进 skill | Claude Code 文档自己警告「Claude Code 之外只能用规范字段」；Cursor / Codex 各有自己的扩展 | 正文规则：**只写规范字段**；扩展字段全部集中在 `references/client-extensions-and-paths.md` 并逐个标注「非规范，仅 <agent> 生效」 | 厂商自身的警告即最强依据；也与本仓库 `docs/skill-standard.md` 第 1.2 节一致 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| anthropic-skill-creator | anthropics/skills `skills/skill-creator/` | merged | description 推销策略与 20 条触发查询 / 60-40 留出划分、评测循环与 `evals.json`·`grading.json`·`benchmark.json` 字段名、按 variant 组织 reference、脚本打包的触发信号、Lack-of-Surprise 安全条款 |
| anthropic-best-practices | Anthropic《Skill authoring best practices》 | merged (docs) | 核心原则、自由度三档、进阶披露三模式与一层引用的理由、工作流清单与校验环、模板/示例/条件工作流模式、评测先行五步、Claude A/B 迭代法与导航四信号、脚本规则、反模式、发布前三组清单 |
| obra-writing-skills | obra/superpowers `skills/writing-skills/` | merged | RED/GREEN/REFACTOR、description 只写触发条件（工作流型）、token 预算、命名、禁 `@path` 强制加载、Match-the-Form-to-the-Failure、说辞表与红旗、微测试与「方差是指标」 |
| agentskills-spec | agentskills.io 规范 + `agentskills/agentskills` | merged (docs) | 字段表与精确约束、目录约定、进阶披露预算、文件引用规则、`skills-ref validate` |
| vercel-skills-cli | vercel-labs/skills | merged | `npx skills` 命令与限制、容器目录 + 三层遍历 + 浅层遮蔽、marketplace 清单发现、`metadata.internal`、能力矩阵 |
| claude-code-skills-docs | code.claude.com/docs/en/skills | merged (docs) | Claude Code 扩展字段全表（标注非规范）、1536 字符列表截断、`synced` 保留名、企业>个人>项目 |
| cursor-skills-docs | cursor.com/docs/skills | merged (docs) | `paths`/`globs`、`disable-model-invocation`、`icon`/`color`、递归发现与嵌套自动限定 |
| codex-skills-docs | learn.chatgpt.com/docs/build-skills | merged (docs) | 2% / 8000 字符预算与「先压缩 description」、`agents/openai.yaml`、`allow_implicit_invocation` |
| grafana-skill-authoring | grafana/skills `skills/grafana-core/skill-authoring/` | merged | 四维评审量表语义、LLM 评委分数方差与「连过三次再交」、路由型文档不可被内联回去 |
| getsentry-skill-writer | getsentry/skills `skills/skill-writer/` | merged | 「open when」路由表的一行一理由写法、加指导前先说明删什么、输出契约四段式 |
| mgechev-skill-creator | mgechev/skills-best-practices `skill/` | merged | hallucination gaps 扫查、不在 skill 里造给人看的文件、校验脚本 stderr 自纠环 |
| hyperskills-self | 本仓库 `docs/skill-standard.md`、`docs/workflow.md`、`tools/` | merged (docs) | `SOURCES.yaml` 溯源模式与 NOTICE 生成、可机械执行的校验清单、`evals.json` + 基线对照的运行器形态 |
| openai-aspnet-core | openai/skills `skills/.curated/aspnet-core/references/_sections.md` | reference | 大型 skill 的 references 索引惯例（Start Here 路径链 + open-when 表 + Reading Strategy），仅阅读对齐，未复制内容 |
| ronifue-skill-authoring | Ronifue/skill-authoring | reference | 任务路由表与「反漂移」「安装前审计」两个角度的交叉校验，未复制内容 |

## 基线缺口

无 skill（`uv run tools/run_evals.py skill-authoring --baseline`，默认模型 anthropic/claude-opus-5，
`--no-skills`）时逐条判定的结果。**基线很强**——四个场景里多数 `expected_behavior` 都自行达成了，
这正是要记录的：只有真正未达成的那几条才有资格在正文里占位置。

> 场景 2、3 的 query 在首轮基线后改写过一次。首轮场景 3 在 900 秒超时（代理去搭真实评测装置了），
> 场景 2 跑了 542 秒并直接把整个 skill 建了出来。两条 query 补上「在对话里回答，不要建文件」后，
> 基线分别落到 115 秒与 86 秒，且判定的是方法而非产物。改写后重跑了这两条基线，本表用重跑结果。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 review-bad-skill | #1 的否定边界部分 | 重写出的 description 是第三人称、塞满了触发词，但**完全没有 `Do not use for ...`**——邻居 skill 的竞争没有被解决 |
| 1 review-bad-skill | #5 两层引用链 | 不只是漏掉，而是**判反了**：原话「`advanced.md` L23 指向 `internals.md` 是对的，两者同目录」。一层引用规则与「深层文件只会被预览」的机制都没有出现 |
| 1 review-bad-skill | （已达成：#2 name 非法、#3 两个宿主专属构造、#4 842 行超预算 + 目录外移、#6 删通识、#7 三项全中） | 基线在这五条上表现很好，其中 #3 是从「路径不存在、宏不会展开」的角度切入，而不是可移植性 |
| 2 author-from-scratch | #1 先跑无 skill 基线 | 基线的第 1 步是「翻历史会话考古」，而对照评测被放在第 6 步、**写完之后**。顺序颠倒 = 缺口未被测量就先写文 |
| 2 author-from-scratch | #2 动笔前写 ≥3 个评测场景（含近似负例） | 完全没有出现。既没有场景数量，也没有负例概念 |
| 2 author-from-scratch | #4 具体的 description（什么+何时+关键词+否定边界） | 只列了「触发语境要覆盖哪些」，没给出可用文本，也没有否定边界 |
| 2 author-from-scratch | #5 reference 一层深 + 每个带 read-when 条件 | 列出了三个 reference 文件名，但没有任何加载条件，也没有一层深的规则 |
| 2 author-from-scratch | #6 脚本以「多次重写同一段代码」为证据 | 第 5 步直接推荐 bundle 脚本，理由是「可机器判定」。推理合理，但不是证据条件式——这正是会长出无人用的脚本的那条路 |
| 2 author-from-scratch | （已达成：#3 只写模型不会的内容） | 基线在这条上极强，还自带「进/不进」两栏判据 |
| 3 fix-triggering | #2 关键用途前置 / 列表截断 | 从未提及宿主会压缩或截断 skill 列表，因此也没有「把最强关键词放最前」的动作 |
| 3 fix-triggering | #5 留出集 | 提出了固定回归查询集 + 配对符号检验，但**没有训练/留出划分**。措辞仍然是对着用来改它的那一组查询拟合出来的，无法区分「更好」与「更贴合这组查询」 |
| 3 fix-triggering | （已达成：#1 第三人称三段式、#3 30/20/10 查询集、#4 边界负例并明确「少了它只能证明更贪婪」、#6 k=5 重复） | 基线在触发机制上的理解很到位 |
| 4 负例 mcp-server | — | 基线用 `--no-skills`，`skill_read` 恒为 False，此场景的判定意义在「有 skill」那两组。基线答复是纯 MCP server 实现，无任何 skill 授权内容，说明这条 query 本身不会把话题带偏 |

**结论：可写的缺口共 9 条**——否定边界（两处）、一层引用与其机制、评测先行的顺序与场景数、
read-when 条件、脚本的证据条件、关键用途前置与截断预算、留出集。正文与 references 只针对这些
以及支撑它们的事实来写；基线已达成的部分（删通识、超预算、name 规则、近似负例、重复采样）
在正文里保留为清单项，但不作为本 skill 的价值主张。

> 运行器注记：首轮场景 2 的基线 `result.json` 报 `skill_read: true`，但该轮是 `--no-skills`，
> skill 不可能被加载——`detect_skill_read` 在事件流里匹配到了 overlay 配置携带的仓库 skills 路径。
> 这是检测器的假阳性，负例判定以「有 skill」两组为准。

## 评测结果

三组：`--baseline`（默认模型，`--no-skills`）、有 skill 默认模型（anthropic/claude-opus-5）、
有 skill `@smol`。场景 1 的夹具在首轮之后从 `evals/files/SKILL.md` 改名为
`evals/files/widget-builder-SKILL.md`（理由见「备注」），改名后**三组都重跑了场景 1**，本表用重跑结果。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 review-bad-skill | default | 无 | False | #2 #3 #4 #5 #6 #7；#1 仅达成第三人称与触发词部分 | **#1 的否定边界未达成**——重写的 description 里没有 `Do not use for`。#5 本轮达成（指出 SKILL.md 应一级直达），但理由是「别让模型做图遍历」，未提「深层文件只被预览」的机制；首轮基线则把这条**判反了** |
| 1 review-bad-skill | default | 有 | True | #1–#7 全部 | 否定边界写进了替换文本；二级引用链按「只会被 preview 然后按残缺信息行动」解释；额外补了 `## Read first` 与带可观测条件的 router |
| 1 review-bad-skill | @smol | 有 | True | #1–#7 全部 | 同上；另外主动指出 `evals/` 不存在、无 baseline 就无法判断哪些文本在承重，并给了三个场景 + 一个近似负例的建议 |
| 2 author-from-scratch | default | 无 | False | #3 | #1 #2 #4 #5 #6 全未达成：评测被排到「写完之后」，无场景数与负例概念，无具体 description 与否定边界，reference 无 read-when，脚本被前置推荐 |
| 2 author-from-scratch | default | 有 | True | #1–#6 全部 | 第 2 步即「跑无 skill 基线、逐字记录失败」并注明 with/without **同批发起**；第 4 步 ≥3 场景 + 共享词汇的近似负例；第 6 步判为 capability 型并写明关键词前置 + 末尾负边界；第 8 步「按主题拆、每个一个可观察 read-when、一层深、不互链」；脚本一条原文：「首版不带。只有当 eval transcript 显示每次运行都在重写同一段代码时才 bundle」 |
| 2 author-from-scratch | @smol | 有 | True | #1 #2 #3 #4 #5；#6 部分 | 第 2 步基线并称其为「全部后续文本的唯一依据」；第 4 步 ≥3 场景 + 负例；第 5 步 capability 公式含 `Do not use for`；第 7 步 read-when。#6 判**部分**：它没有前置推荐脚本（基线会），但也没有把「多次重写同一段代码」这个证据条件说出来 |
| 3 fix-triggering | default | 无 | False | #1 #3 #4 #6 | #2 #5 未达成：从未提宿主会截断列表，因此没有关键词前置；只有固定回归集 + 配对符号检验，没有训练/留出划分 |
| 3 fix-triggering | default | 有 | True | #1–#6 全部 | 明确写出两种截断预算（整表 2% 上下文 / 每条 1536 字符）并据此前置关键词；「60/40 切分，40% 完全不看，只在 held-out 上打分」；验收看 held-out 上的命中率与误触率两个数 |
| 3 fix-triggering | @smol | 有 | True | #1–#6 全部 | 同样给出「宿主列表会截断且从尾部切」与 60/40 train/held-out、按 held-out 挑赢家；并补了「若技能已加载但产出仍不对，改 description 无效」这条分流 |
| 4 负例 mcp-server | default | 无 | False | #2 | `--no-skills`，`skill_read` 恒 False；答复是纯 MCP server 实现 |
| 4 负例 mcp-server | default | 有 | **False** | #1 #2 | 负例成立：skill 在场但未被读取；答复全程 MCP server（SDK 版本核实、stdio 接线、工具 schema），`skill-authoring` / `frontmatter` / `progressive disclosure` 字样命中数 0 |
| 4 负例 mcp-server | @smol | 有 | **False** | #1 #2 | 同上，命中数 0 |

结论：**通过**。

- **默认模型**：基线未达成而有 skill 达成的行为共 8 条——场景 1 的否定边界；场景 2 的
  基线先行、≥3 场景含近似负例、具体 description 含否定边界、reference 的一层深与 read-when、
  脚本的证据条件（5 条）；场景 3 的关键用途前置与截断预算、60/40 留出集（2 条）。
- **`@smol`**：同样的 8 条中有 7 条完全达成，第 8 条（脚本证据条件）部分达成——它不再前置推荐
  脚本，但没有把判据说出口。两种模型都闭合了「否定边界」「评测先行」「read-when」
  「关键用途前置」「留出集」这五类缺口。
- **负例**：两种模型在有 skill 时 `skill_read` 均为 `False`，且答复中零 skill 授权词汇，
  说明 description 的否定边界（`Do not use for MCP servers, slash commands, ...`）真的在起作用。
- **非区分项**：场景 1 的 #2 #3 #4 #6 #7 与场景 2 的 #3、场景 3 的 #1 #3 #4 #6 在两种配置下都达成，
  属非区分项——它们在正文里作为清单项保留（回归价值），但不能用来给本 skill 的文字辩护。
- **方差**：场景 1 的 #5（二级引用链）在两次基线中一次判反、一次判对，是本轮观察到的唯一
  跑动项。这与 `references/evaluation.md` 里「单次运行不能把效应和噪声分开」自洽，故本表按
  「基线可自行达成、但机制解释缺失」记录，不把它算进那 8 条。

## 备注

- 许可注意：`anthropics/skills` 仓库根无 LICENSE，许可按 skill 目录下的 `LICENSE.txt` 判定。
  `skill-creator` 当日为 Apache-2.0，与四件套文档 skill 的专有许可**不同**，可以 `merged`；
  同步上游时必须重新核对该文件，一旦改为专有须立刻降级为 `reference` 并重写受影响段落。
- `mgechev/skills-best-practices` 无任何许可声明，按本仓库宽松策略以署名方式合入，
  `SOURCES.yaml` 的 `notes` 已记明。
- 未来同步时要盯的上游：agentskills.io 规范（字段表是硬事实，一旦变动
  `references/spec-reference.md` 与本仓库校验器同时要改）；`vercel-labs/skills` 的容器目录清单与
  agent 路径表（变动最频繁，`references/client-extensions-and-paths.md` 是唯一落点）；
  Claude Code / Cursor / Codex 三份厂商文档的扩展字段。
- 放弃的方向：不移植任何评测机械代码（skill-creator 的 `scripts/`、`eval-viewer/` 绑定 Claude
  子代理与浏览器；grafana 的 Tessl CLI 是商业工具），因此本 skill **无 `scripts/`**——
  评测流程写成与 harness 无关的步骤。
- 不采用 getsentry 的 `SPEC.md` 契约文件：本仓库已有 `SOURCES.yaml` + `research/<skill>.md`
  承担同一职能，第三种约定会造成分裂。
- **评测夹具改名（偏离计划的决定）**：场景 1 的夹具原本就叫 `evals/files/SKILL.md`，读起来最自然。
  安装冒烟后发现问题：它会被安装成
  `.agents/skills/skill-authoring/evals/files/SKILL.md`。`npx skills` 的「浅层遮蔽深层」规则会挡住它，
  但 Cursor 是**递归**扫描 skills 根目录、并以「含 SKILL.md 的那层目录」为 skill 身份，
  于是会多注册一个名为 `files`、frontmatter 写着 `name: Widget_Builder` 的坏 skill。
  这正是本 skill 自己反对的那类事故，故改名为 `widget-builder-SKILL.md` 并改写 query，
  三组评测的场景 1 全部重跑。**给后续 skill 的通用结论：`evals/files/` 里永远不要放名为
  `SKILL.md` 的夹具。**
- 安装冒烟（Phase D1）：
  `npx skills@latest add /root/Projects/Ling/HyperSkills --skill skill-authoring --agent universal --copy --yes`
  在 `/tmp/hs-smoke-sa` 成功，`.agents/skills/skill-authoring/` 下 `SKILL.md`、`SOURCES.yaml`、
  7 个 `references/*.md`、`evals/` 齐全。用 `--copy` 而非符号链接是刻意的——复制会暴露任何
  越出 skill 目录的相对路径。
- 自身一致性的一处修正：初稿的规则 5 写成「多步工作流型 skill 的 description 只写触发条件」，
  而本 skill 自己既有 6 个 workflow 又有 reference 面，按字面会自我违反。改为可判定的判据——
  「如果仅凭 description 就能造出正文流程的一个像样的仿制品，那个仿制品就会被执行」，
  并明确「覆盖主题清单是安全的，有序摘要不是」。`references/description-optimization.md`
  的同一节同步改写。这是唯一一处因「本 skill 必须自己合规」而回改的规则。
- GitHub API 匿名配额在复核中段被打满（HTTP 403）。其后的候选改用
  `git ls-remote --symref` + `--filter=blob:none --depth 1` 浅克隆读取实际文件，
  数据仍是当日实测，取证方式已在候选表「许可」列标注。`SOURCES.yaml` 的 commit 由
  `tools/check_upstream.py --pin` 写入（该脚本自带 `git ls-remote` 回退），9 个 repo 类上游全部钉住。
