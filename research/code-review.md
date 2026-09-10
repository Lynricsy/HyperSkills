# code-review 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-10
- 复核日期：2026-09-10（本次全部数据当日重新核对）
- 检索途径：
  - 会话内已归档的种子调研（TDD / debugging / code-review 三领域，约 180 个候选）中的 code-review 部分，
    本次逐条重核并补搜。
  - `web_search`：`code review agent skill SKILL.md github "code-review" claude skill 2026`
  - GitHub 搜索 API：`user:<owner> skills`（定位种子清单里只有姓氏的候选）
  - 领域来源仓库直查：`obra/superpowers`、`mattpocock/skills`、`addyosmani/agent-skills`、
    `trailofbits/skills`、`anthropics/claude-code`、`n8n-io/skills`
- GitHub API 核对方式：`curl -s https://api.github.com/repos/<owner>/<repo>`
  （`stargazers_count` / `pushed_at` / `license.spdx_id`）。
  **今日 API 在核完前 6 个仓库后触发未认证限流（60/h，本机无 `GITHUB_TOKEN`）**，其余候选改用
  两条无需 API 的途径复核并在表中标注：仓库 HTML 的 star 计数、
  `https://github.com/<repo>/commits/<branch>.atom` 的最新 `<updated>` 作为最近推送时间。
  许可证一律直读 `LICENSE*` 原文或 skill frontmatter，未凭 API 推断。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | obra/superpowers — `skills/requesting-code-review/SKILL.md` | https://github.com/obra/superpowers | 284,401（API） | 2026-09-10（API） | MIT | 何时请求审阅、SHA 固定、派发理由、按严重度处置 | 2 | 3 | 2 | 3 | 2 | **12** | **INCLUDE** | 唯一把「派发审阅者而非内联读 diff」的上下文经济学写清楚的上游；SHA 固定与「reviewer 错了就有据反驳」是本 skill 的骨架 |
| 2 | obra/superpowers — `skills/requesting-code-review/code-reviewer.md` | 同上 | 同上 | 同上 | MIT | 可派发的审阅者提示模板 | 2 | 3 | 3 | 3 | 2 | **13** | **INCLUDE** | 只读守卫（不动 worktree/index/HEAD，要别的 revision 就 `git worktree add`）、「你不派发子代理」及其理由、Strengths/Critical/Important/Minor/Recommendations/Assessment 输出格式与完整示例——三样都是别处没有的 |
| 3 | obra/superpowers — `skills/receiving-code-review/SKILL.md` | 同上 | 同上 | 同上 | MIT | 接收反馈的完整流程 | 2 | 3 | 3 | 3 | 2 | **13** | **INCLUDE** | 全生态唯一认真处理「回应方向」的上游：六步、禁止表演式回应（连道谢都禁）、任一条不清则全部澄清后再动手、来源分级、YAGNI grep、实现顺序、有据反驳与自我纠正、GitHub 行内线程回复 |
| 4 | obra/superpowers — `skills/verification-before-completion/SKILL.md` | 同上 | 同上 | 同上 | MIT | 完成前的证据门 | 2 | 3 | 3 | 3 | 2 | **13** | **INCLUDE（部分）** | 整体属于另一个 skill；本 skill 只取「先证据后声明」门函数与「验证作者的验证」语义（三个工程实践 skill 的共享文本 #1） |
| 5 | mattpocock/skills — `skills/engineering/code-review/SKILL.md` | https://github.com/mattpocock/skills | 258,396（API） | 2026-09-04（API） | MIT | 双轴审阅（Standards / Spec） | 2 | 2 | 3 | 3 | 2 | **12** | **INCLUDE** | 固定基点 + `git rev-parse` 快失败 + 三点 diff；spec 来源优先级；**双轴分开采集、禁止跨轴重排**并给出理由（一轴会掩盖另一轴）；12 条 Fowler 味道基线含「仓库标准覆盖基线」「味道皆为判断题」「跳过工具已强制项」三条元规则 |
| 6 | addyosmani/agent-skills — `skills/code-review-and-quality/SKILL.md` | https://github.com/addyosmani/agent-skills | 93,324（API） | 2026-09-08（API） | MIT | 五轴质量审阅 | 2 | 3 | 3 | 2 | 2 | **12** | **INCLUDE** | 最宽的一份（396 行）：批准标准、五个质量轴的具体问题清单、**严重度前缀分级**、领头规则、8 种结构性补救、改动规模与四种拆分策略、先看测试、验证作者的验证、诚实/反谄媚、分歧层级、死代码卫生、依赖升级五条。正确性扣 1 分：SLA 类人类流程与「覆盖率」式条目对 agent 无意义（见 R8） |
| 7 | trailofbits/skills — `plugins/differential-review/skills/differential-review/`（含 `methodology.md` / `adversarial.md` / `reporting.md` / `patterns.md`） | https://github.com/trailofbits/skills | 7,030（API） | 2026-09-09（API） | **CC-BY-SA-4.0** | 安全向差分审阅 | 3 | 3 | 3 | 3 | 1 | **13** | **INCLUDE（只取结构与清单语义，全文重写）** | 权威安全团队；风险分级触发器、按代码库规模调深度、对删除的守卫做 `git blame`、按调用方计数算爆炸半径、改动代码的测试覆盖升档规则、升级触发器、报告必须落文件。许可分只给 1：share-alike 与本仓库 MIT 冲突，**不得复制原文**（见 R9） |
| 8 | mattpocock/skills — `skills/productivity/grilling/SKILL.md` | https://github.com/mattpocock/skills | 258,396（API） | 2026-09-04（API） | MIT | 一轮问完前沿的提问格式 | 2 | 2 | 2 | 3 | 2 | **11** | **INCLUDE（仅提问格式）** | 只取「一轮问完当前所有未决问题、每条编号并附推荐答案、事实自己查决策交用户」的格式；design-tree 那套完整方法属于另一个 skill |
| 9 | anthropics/claude-code — `plugins/code-review/commands/code-review.md`、`plugins/feature-dev/agents/code-reviewer.md` | https://github.com/anthropics/claude-code | 未核（API 限流） | 2026-09-09（atom） | **Proprietary**（`LICENSE.md`：© Anthropic PBC, All rights reserved） | 官方 PR 审阅命令与审阅者 agent | 3 | 3 | 2 | 3 | 0 | **11** | **REJECT 为 merged → relation: reference** | 专有许可，一字不抄。但它证实了一条别处缺失的纪律：**每条发现在上报前单独复核，未复核的丢弃**（官方用 confidence≥80 与专门的验证子代理实现），以及「linter 会抓的、既有的、迂腐的」三类假阳性清单。本 skill 用自己的话写了等价的自检步骤 |
| 10 | trailofbits/skills — `second-opinion` | https://github.com/trailofbits/skills | 7,030（API） | 2026-09-09（API） | CC-BY-SA-4.0 | 对已有结论求第二意见 | 3 | 3 | 2 | — | 1 | — | **REJECT** | 另一个任务域（质疑既有分析结论），与 diff 审阅无关；且 CC-BY-SA 成本不值得为一个非核心能力付 |
| 11 | addyosmani/agent-skills — `skills/security-and-hardening` | https://github.com/addyosmani/agent-skills | 93,324（API） | 2026-09-08（API） | MIT | 通用安全加固 | 2 | 3 | 2 | — | 2 | — | **REJECT（路由不合并）** | 是「整仓安全审计」而非「改动集安全审阅」；本 skill 的否定边界明确把整仓审计排除，正文以技能名提及即可 |
| 12 | addyosmani/agent-skills — `skills/code-simplification` | 同上 | 93,324（API） | 2026-09-08（API） | MIT | 简化既有代码 | 2 | 3 | 2 | — | 2 | — | **REJECT（路由不合并）** | 属于重构执行域；审阅只负责「指出结构问题并命名该做的动作」，执行不在本 skill（见 R1） |
| 13 | mattpocock/skills — `skills/engineering/improve-codebase-architecture`、`skills/engineering/codebase-design` | https://github.com/mattpocock/skills | 258,396（API） | 2026-09-04（API） | MIT | 架构改造与设计词汇 | 2 | 2 | 2 | — | 2 | — | **REJECT（仅作交叉引用）** | 架构重设计是另一领域（本 skill 否定边界已排除）。只借其 **seam 词汇**，且该词汇在三个工程实践 skill 中统一措辞（共享文本 #3） |
| 14 | n8n — `human-like-code-review` | https://github.com/n8n-io/n8n | 203,916（API，n8n 主仓） | 2026-09-10（API） | NOASSERTION（Sustainable Use） | 产品仓库内部审阅约定 | 1 | 3 | 1 | — | 0 | — | **REJECT** | 今日在 `n8n-io/n8n` 的三条可能路径（`.claude/skills/...`、`skills/...`）与 `n8n-io/skills`（488★, 2026-09-10, Apache-2.0，只有 n8n 产品向 skill）均未找到该 skill，已不可定位；即便存在也是单一产品仓库的内部评审约定 + 非开源许可，不可作上游 |
| 15 | HermeticOrmus/code-review-skills — `skills/code-review` | https://github.com/HermeticOrmus/code-review-skills | 0（HTML） | 2026-05-25（atom） | MIT（frontmatter） | 按领域分类的 diff 审阅 | 0 | 1 | 2 | — | 1 | **4** | **REJECT** | 匿名作者、0 star、3.5 个月无推送；内容是「先给 diff 分类再按类过清单」，此思路已被 addyosmani 五轴 + trailofbits 风险分级覆盖；正文还引流到同作者的另两个仓库 |
| 16 | googs1025/code-review-skill | https://github.com/googs1025/code-review-skill | 未核（HTML 抓取失败） | 2026-03-18（atom） | MIT | PR / diff / issue 审阅 | 0 | 1 | 2 | — | 2 | **5** | **REJECT** | 近 6 个月无推送；正文为中文（本仓库 skill 正文必须英文，等于全部重写）；核心价值是抓取 PR 的脚本，与本仓库「不引 harness 绑定脚本」相冲 |
| 17 | enkr1/claude-code-skills — `skills/comprehensive-review` | https://github.com/enkr1/claude-code-skills | 0（HTML） | 2026-09-10（atom） | 未声明 | staff 级 ship gate | 0 | 3 | 1 | — | 0 | **4** | **REJECT** | 0 star、无许可；且自述「diff 审阅委托给内置 `/code-review`，本 skill 不重复」——去掉委托部分后只剩一个 REJECT/NEEDS WORK/APPROVE 判定，本 skill 的 merge verdict 已覆盖 |
| 18 | nledford/engineering-review-board | https://github.com/nledford/engineering-review-board | 0（API 搜索） | 2026-08-29（API 搜索） | MIT | 多角色评审委员会 | 0 | 3 | 1 | — | 2 | **6** | **REJECT** | 0 star 的个人实验：让多个角色 persona 对同一改动发言。角色扮演不产出可检查的规则，且与 R4 的「编排者派发、审阅者不再派发」分层冲突 |
| 19 | JUNERDD/skills | https://github.com/JUNERDD/skills | 3（API 搜索） | 2026-09-08（API 搜索） | MIT | 个人 skill 合集 | 0 | 3 | 1 | — | 2 | **6** | **REJECT** | 3 star 的未审个人合集，无可辨识的审阅方法论 |
| 20 | davila7/claude-code-templates — `.../skills/code-review*` | https://github.com/davila7/claude-code-templates | 30,583（API 搜索） | 2026-09-10（API 搜索） | MIT | 模板农场 | 1 | 3 | 1 | — | 2 | **7** | **REJECT** | star 高但内容是批量生成的模板集合，审阅 skill 是他人作品的派生且无溯源；作为上游会把不可追责的内容引进来 |
| 21 | github/awesome-copilot | https://github.com/github/awesome-copilot | 38,847（API 搜索） | 2026-09-10（API 搜索） | MIT | Copilot 指令 / chatmode 集合 | 3 | 3 | 1 | — | 2 | **9** | **REJECT（本 skill 用不上）** | 官方且活跃，但其 code-review 相关产物是 `*.instructions.md` / chatmode 提示页，内容为通用清单式空话，具体性 1；本 skill 已有三份更具体的上游 |
| 22 | JPeetz、pnewsam（种子清单只给了姓氏） | — | — | — | — | — | — | — | — | — | — | — | **REJECT（无法定位）** | 用 GitHub 搜索 API 按 owner 检索，`JPeetz` 名下只有无关仓库（Hermes-Studio），`pnewsam` 名下无 skill 仓库。无法定位 = 无法核实 = 不作上游 |

## 深度审查

**obra `requesting-code-review` + `code-reviewer.md`（95 + 181 行）** — frontmatter 只有 `name` +
`description`，无 agent 专属字段。`code-reviewer.md` 不是 skill，而是一份带占位符
（`[DESCRIPTION]` / `[PLAN_OR_REQUIREMENTS]` / `[BASE_SHA]` / `[HEAD_SHA]`）的子代理提示模板。
三处独有内容：①**只读守卫**——不得改动 worktree、index、HEAD、分支；要看别的 revision 就
`git worktree add /tmp/review-<sha>`；②**「你不派发子代理」**并给出理由（本流程已经给足审阅席位，
你派生的审阅者只是全价复制其中一席，其结论不作数）；③输出格式
Strengths → Issues(Critical/Important/Minor) → Recommendations → Assessment(Ready to merge:
Yes|No|With fixes) + 每条发现四要素（file:line / 问题 / 为什么要紧 / 怎么修）+ 一份完整示例输出。
`requesting-code-review` 的合理化借口表里藏着关键论证：编排者内联读 diff 会烧掉自己继续驱动工作
所需的上下文窗口，派发后 diff 与评估留在审阅者上下文里、只有结论回流。缺点：`superpowers:`
命名空间与「your human partner」措辞需清除；红旗节里「Proceed with unfixed Important issues」
是针对 agent 审自己工作的严格门，直接套到审他人 PR 上会变成阻塞（见 R5）。

**obra `receiving-code-review`（205 行）** — 回应方向的唯一来源，也是三份 obra 文档里最完整的一份。
六步 READ → UNDERSTAND → VERIFY → EVALUATE → RESPOND → IMPLEMENT；禁止回应被逐字点名
（"You're absolutely right!"、"Great point!"、任何道谢）并给出理由（行动胜于言辞，代码本身说明你听懂了）；
「任一条不清 → 停下，先把所有不清的问完再实现任何一条」并给出理由（条目之间可能相关，
半懂 = 实现错）；来源分级（伙伴反馈可信但仍要问清范围；外部反馈五问核对）；YAGNI grep
（reviewer 要求「实现得更专业」时先 grep 有没有调用方）；实现顺序（阻塞 → 简单 → 复杂，逐条测试）；
反驳时机与「反驳错了怎么优雅纠正」；末尾一句 GitHub 行内线程回复命令。需要注意：它把「道谢」
一律禁掉，但自己的 ✅ 清单里又有 "Good catch — [specific issue]. Fixed in [location]."——
说明真正禁的是空洞赞同（见 R7）。

**mattpocock `code-review`（87 行）** — frontmatter 的 `description` 本身就是路由契约。流程：
固定基点（未给就问）→ `git rev-parse` 确认能解析且 diff 非空（**快失败在编排者这一层，
而不是在两个并行子代理里面才炸**）→ `git diff <fp>...HEAD` 三点 diff（对 merge-base 比较）+
`git log <fp>..HEAD --oneline` → 按优先级找 spec 来源（提交信息里的 issue 引用 → 用户给的路径 →
`docs/`|`specs/`|`.scratch/` 下与分支同名的文件 → 问用户；确实没有则 Spec 轴报「no spec available」）→
找 standards 来源（`CODING_STANDARDS.md`、`CONTRIBUTING.md` 等）+ 常驻的 12 条 Fowler 味道基线 →
并行派发 Standards / Spec 两个子代理（每个 400 词上限，味道基线要整段贴进子代理提示，因为它没有别的
获取途径）→ 聚合成两节、**不合并不重排**。仓库专属耦合需清除：`docs/agents/issue-tracker.md`、
`/setup-matt-pocock-skills`。

**addyosmani `code-review-and-quality`（396 行）** — 最宽。批准标准写得好：「确实改善整体代码健康
就批准，即使不完美；不要因为不是你会写的样子而阻塞」。五轴（正确性 / 可读性与简洁 / 架构 / 安全 /
性能）每轴都是具体问题清单，可读性与架构两轴里有几条真正针对 agent 的锐利条目：
「新条件语句是不是被硬焊到一条无关流程上」「重构是减少了复杂度还是只是搬家——数一下读者要同时
持有的概念数」「特性逻辑是否漏进了共享模块」「类型边界是否显式，还是用 `any`/可选/强转/静默兜底
糊住了不清楚的不变量」。严重度前缀表（无前缀=必改 / Critical / Nit / Optional-Consider / FYI）
是唯一区分「必须」与「可选」的分级方案，而这正是真实失效模式（作者把所有意见都当强制）。
另有 8 种结构性补救、改动规模阈值与四种拆分策略、先看测试、验证作者的验证、诚实条款、
分歧层级、死代码卫生（列出来、删之前先问）、依赖升级五条。需要砍掉的：审阅速度 SLA
与多轮节奏（人类团队流程，对 agent 无意义，见 R8）；`../../references/*.md` 的越级相对链接；
指向同仓库其他 skill 的 `security-and-hardening` / `performance-optimization` 引用改为技能名提及。

**trailofbits `differential-review`（SKILL 225 行 + 四份参考 1106 行）** — 唯一使用
`allowed-tools` 的候选（本仓库剥离）。风险优先：HIGH = 认证、加密、外部调用、价值转移、
校验移除；MEDIUM = 业务逻辑、状态变更、新公开 API；LOW = 注释、测试、UI、日志。
代码库规模策略：SMALL <20 文件 → DEEP（读全部依赖、完整 blame），MEDIUM 20–200 → FOCUSED
（一跳依赖、优先文件），LARGE 200+ → SURGICAL（只走关键路径）。方法论里可复用的语义：
对删除的代码做 `git log -S` / `git blame`，来自 "fix"/"security"/"CVE" 提交的删除直接 CRITICAL；
「加过 → 因安全被删 → 现在又加回来」= 回归；测试覆盖升档规则（新函数无测试 MEDIUM→HIGH，
改了校验但测试没动 = HIGH）；按调用方计数分档爆炸半径（1–5 / 6–20 / 21–50 / 50+）并与风险
交叉成优先级矩阵；升级触发器清单；报告必须落文件而不是只发到聊天里。它的合理化借口表里那句
「小 PR 快速过一下」→「Heartbleed 只有两行」是最有说服力的反例。**许可约束**：CC-BY-SA-4.0，
share-alike。本 skill 只取上述结构与清单语义，全部用自己的话重写，不复制任何句子、表格或模板
（见 R9）。它的 Solidity 偏向（`onlyOwner`、reentrancy、`*.sol` grep）改写为语言中立表述。

**anthropics/claude-code `plugins/code-review`（109 行命令）+ `feature-dev/agents/code-reviewer.md`
（46 行）** — 官方实现，专有许可，只读不抄。它的两条纪律值得本 skill 用自己的话写下来：
①**发现要先复核再上报**——官方做法是给每条候选发现单独派一个验证子代理，并要求 confidence ≥ 80
才上报，理由写得直白：假阳性侵蚀信任、浪费审阅者时间；②**假阳性排除清单**——既有问题、
linter 会抓的问题（且不要为了验证去跑 linter）、迂腐到资深工程师不会提的点、CLAUDE.md 里提过
但代码里已显式静默的项。另有一条实用细节：在 PR 行内评论里引用代码必须用带完整 SHA 的
permalink（`blob/<full-sha>/<path>#L4-L7`），命令替换写法在 Markdown 渲染里不生效。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| R1 | 重构归属哪一环 | mattpocock（tdd）：重构不属于 TDD 循环，属于审阅阶段。addyosmani（review）：既重构又加行为的改动是两个改动，分开提 | 清理型重构（不改行为、测试保持绿）留在 TDD 循环内；结构型重构由审阅提出并作为独立改动落地。两个 skill **同一段文字**，字面一致 | 两方各说对了一半；分层后不再冲突。跨 skill 措辞统一避免用户在两处读到互相矛盾的规则 |
| R2 | 严重度词汇 | obra：Critical / Important / Minor。addyosmani：无前缀=必改 / Critical / Nit / Optional-Consider / FYI。mattpocock：硬违规 vs 判断题 | 评论级用 addyosmani 五级；报告节标题用 obra 三级；给出显式映射：Critical→Critical、无前缀→Important、Nit 与 Optional→Minor、FYI→Recommendations。同时保留 mattpocock 的「硬违规 / 判断题」作为**正交**标签 | 五级是唯一区分必须与可选的方案（真实失效模式是作者把所有意见当强制）；三级适合报告结构。两套并存必须给映射，否则等于发两套标准 |
| R3 | 双轴合并还是分开 | mattpocock：绝不合并或跨轴重排，分开就是全部意义。obra / addyosmani：一份按严重度排序的整合报告 | **采集分开**（两轴回答不同问题，一轴会掩盖另一轴），**输出一份报告两节**，每节内部按严重度排序，禁止跨轴重排；结尾也不选「总冠军」，只给每轴最严重项 | mattpocock 的理由可检验：符合全部规范但实现错了东西 = Standards 过 Spec 挂；反之亦然。合并后必然被一轴掩盖 |
| R4 | 审阅者是否再派发子代理 | obra `code-reviewer.md`：审阅者**不得**派发。mattpocock：编排者派发两个并行子代理 | 分层：**编排者**可以并行派发 Standards / Spec / Security 三个审阅者；**每个审阅者自己一遍过，永不再委派**。正文明写这个分层 | 不是真冲突，是层级不同。写明分层可防止递归扇出——obra 已给出理由：派生的审阅者只是全价复制一席，结论不作数 |
| R5 | 批准门槛 | addyosmani：确实改善整体健康即可批准，即使不完美。obra：带着未修的 Important 继续是红旗，Critical 与 Important 都要修完 | 按语境分开：**审他人（或另一 agent）的 PR** → 改善整体健康即可批准，因非 Critical 问题阻塞是妨碍；**agent 审自己的工作、准备宣称完成** → 严格门，Critical 与 Important 全部修完 | 两者是不同的工作。写清语境比强行统一诚实 |
| R6 | 安全覆盖到什么程度 | mattpocock：无安全轴。addyosmani：安全是五轴之一，细节路由到别的 skill。trailofbits：安全优先、风险分级、对抗建模 | 分层：安全是**常驻轴**（addyosmani 清单，每次审阅都过）+ **升级模式**（trailofbits 流程），由 HIGH 风险触发器触发。完整对抗建模绝不作默认 | 对 LOW 风险 diff 做完整对抗建模是纯浪费；但认证/加密/校验移除类改动不升级则会漏真问题 |
| R7 | 反谄媚措辞 | obra：接收方禁止道谢与「你完全正确」。addyosmani：给出方禁止盖章式 LGTM 与软化真问题 | 两条都留，各归其位。但把 obra 的绝对化收紧为：禁止的是**空洞赞同**；`Good catch — <具体问题>. Fixed in <位置>.` 允许（obra 自己的 ✅ 清单里就有这句） | 照字面执行会产出一个生硬机械的审阅者。禁的是无信息量的表演，不是一切确认 |
| R8 | 人类团队流程 | addyosmani 带审阅速度 SLA（一个工作日内回应）、多轮节奏 | **全部删除**。 | 对 agent skill 无意义，纯 token 成本。底层原则（快的部分反馈优于慢的完整反馈）也没到值一行的程度 |
| R9 | 许可 | trailofbits 是 CC-BY-SA-4.0，其余 INCLUDE 都是 MIT | 不复制 trailofbits 任何原文。只取清单语义与流程结构，全部用自己的话重写；`SOURCES.yaml` 的 `license` 记 `CC-BY-SA-4.0`、`notes` 记录该约束；`security-review.md` 的措辞、表格划分、阈值表述均为原创，Solidity 专属内容改写为语言中立 | 仓库自有内容 MIT，混入 share-alike 原文会污染许可。`AGENTS.md` 许可策略第 5 条即此规定 |
| R10 | 发现要不要逐条复核（本次新增） | anthropics/claude-code：每条候选发现单独验证，未过验证的丢弃（confidence ≥ 80）。obra：「不要对你没真读过的代码提意见」。addyosmani：不要盖章、不要软化 | 采纳「上报前逐条复核」为 Core rule，并给出假阳性排除清单（既有问题、linter 已强制项、迂腐点、代码里已显式静默项）。**用自己的话写**，不抄官方文本（专有许可） | 官方厂商 > 公认专家；且这条填补了 obra/addyosmani 只给态度不给动作的缺口。假阳性侵蚀信任是可观察的失效模式 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| obra-requesting-review | obra/superpowers `skills/requesting-code-review`（含 `code-reviewer.md`） | merged | 基点 SHA 固定与「派发而非内联」的上下文理由；审阅者提示模板的只读守卫、不嵌套派发规则、Strengths/Critical/Important/Minor/Recommendations/Assessment 输出格式与示例、校准规则；按严重度处置反馈 |
| obra-receiving-review | obra/superpowers `skills/receiving-code-review` | merged | 回应方向全流程：六步、禁止空洞赞同、任一条不清则全部澄清后再实现、来源分级五问、YAGNI grep、阻塞→简单→复杂的实现顺序、有据反驳与优雅自我纠正、GitHub 行内线程回复 |
| obra-verification | obra/superpowers `skills/verification-before-completion` | merged | 「先证据后声明」完成门（共享文本 #1）与「验证作者的验证」——作者跑了什么命令、输出是什么 |
| mattpocock-review | mattpocock/skills `skills/engineering/code-review` | merged | 固定基点 + `git rev-parse` 快失败 + 三点 diff；spec 来源优先级；Standards / Spec 双轴分开采集与禁止跨轴重排；12 条 Fowler 味道基线及其三条元规则 |
| mattpocock-grilling | mattpocock/skills `skills/productivity/grilling` | merged | 一轮问完当前所有未决问题、每条编号并附推荐答案的提问格式（共享文本 #2） |
| addyosmani-review | addyosmani/agent-skills `skills/code-review-and-quality` | merged | 五个质量轴与其问题清单；严重度前缀分级；领头规则；8 种结构性补救；改动规模与四种拆分策略；先看测试；验证作者的验证；诚实与反谄媚；分歧层级；死代码卫生；依赖与升级审阅 |
| trailofbits-diffreview | trailofbits/skills `plugins/differential-review/skills/differential-review` | merged（结构与清单语义，全文重写） | 安全模式：风险分级触发器、按代码库规模调深度、对删除的守卫做 blame、按调用方计数的爆炸半径与优先级矩阵、测试覆盖升档规则、升级触发器、报告落文件与诚实声明覆盖范围 |
| anthropic-claude-code | anthropics/claude-code `plugins/code-review`、`plugins/feature-dev/agents/code-reviewer.md` | reference | 证实「每条发现上报前先复核、未过复核的丢弃」这条纪律与假阳性排除清单的构成；PR 行内评论必须用带完整 SHA 的 permalink。专有许可，未复制任何文字 |
| mattpocock-codebase-design | mattpocock/skills `skills/engineering/codebase-design` | reference | seam 词汇（共享文本 #3）的来源；结构型重构归属的另一半论据（R1） |

## 基线缺口

无 skill（`uv run tools/run_evals.py code-review --baseline`，默认模型，四个场景 `skill_read == False`）时，
各场景未达成的 `expected_behavior`。基线模型能力很强，八条里通常能命中五到六条——
缺的恰好都是**方法层面**的（历史证据、双轴分离、分级词汇、澄清纪律），这正是本 skill 要填的空。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 审阅 diff | #4 对删除的守卫做 `git blame` / `git log -S` | 基线确实指出「validate.js 被整文件删除、越界」，但取证方式全是 `rg` 搜引用与 `git stash` 跑测试，**从未去查这段校验当初为什么被加进来**。无历史 = 无法判断这是清理还是回归 |
| 1 审阅 diff | #5 Spec 与 Standards 分开采集、分节输出、禁止跨轴重排 | 基线输出的分节是「阻断项 / 功能性缺陷 / 待验证疑点」——按类型与严重度混排。工单越界（Spec）与 SQL 拼接（Standards）被塞进同一个「阻断项」列表，一轴掩盖另一轴 |
| 1 审阅 diff | #6 每条发现带严重度标签 | 用的是自造的「阻断 / 缺陷 / 疑点」三分，既不是 Critical/Important/Minor 也不是 Critical/无前缀/Nit/Optional/FYI；作者无法据此区分「必须改」与「可以不改」 |
| 2 安全审阅 | #2 对删除的签名校验做 `git blame` / `git log -S` | 同上：跑了 `rg 'verify_signature'` 找是否还有别处调用，也跑了 `git log --oneline main..HEAD` 看意图，但没有对**被删掉的那几行**追溯来源提交，无法判定是否来自安全修复 |
| 2 安全审阅 | #3 按调用方计数算爆炸半径 | 部分达成：正确点出 `replay_webhook` 是第二个入口，但没有给出计数命令、没有把「风险 × 调用方数量」交叉成优先级 |
| 3 回应审阅 | #1 有不清的条目就先全部澄清、一条都不实现 | **反向失败**：直接改了 `rates.ts`（采纳 #1、#3），把 #4 #5 归为「范围外 / 信息不足」写在报告里。第 5 条明确不清（哪个「另一个服务」）却仍先动了手 |
| 3 回应审阅 | #2 编号提问 + 每条附推荐答案 | 没有任何提问格式；只在末尾问了一句「要不要我整理成能贴回 PR 的回复」。#5 的追问被写成叙述而非可回答的问题 |
| 3 回应审阅 | #5 对「实现得更专业」先 grep 调用方（YAGNI） | 把 #4 判为「依赖上游 API 能力、应开独立 issue」——理由合理但方向不同：**没有查有没有调用方**，因而错过了「这个端点根本没人调，删掉即可」这条更省事的结论 |
| 3 回应审阅 | #8 行内评论回到原线程 | 完全未提；默认想法是产出一段贴回 PR 的整体回复 |
| 4 负例 | —（基线全达成） | 无 skill 时本就不会读本 skill；写出了中间件、没有产出审阅报告。此场景用于验证**有 skill 时也不会误触发** |

基线全达成的行为（说明这些不是本 skill 的价值点，但仍写进评测以防回退）：场景 1 的 #1 基点与三点 diff、
#2 测试被阉割、#3 SQL 注入、#7 明确的 merge 判定、#8 不纠结格式；场景 2 的 #1 风险定级、#4 覆盖缺口、
#5 具体攻击场景、#6 通配符与金额校验、#7 原始报文进日志、#8 报告落文件并声明未核项。

## 评测结果

运行：`uv run tools/run_evals.py code-review --baseline` / `... code-review` / `... code-review --model @smol`。
`skill_read` 取自 `result.json`。expected_behavior 编号见 `skills/code-review/evals/evals.json`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 审阅 diff | default | 无 | false | #1 #2 #3 #7 #8（5/8） | 未达成 #4 #5 #6：无历史取证、Spec/Standards 混排、自造严重度词 |
| 1 审阅 diff | default | 有 | true | #1–#8（8/8） | 分「Standards 轴 / Spec 轴」两节，各自 Critical/Important；命令清单含 `git log -S 'assertPositiveQuantity'` 与 `git blame <base> -- src/orders/validate.js`；另主动落盘安全增量报告 `security-review-482.md`。本行是**在最终版 SKILL.md 上复跑**的结果，与收紧措辞前的那一轮同为 8/8 |
| 1 审阅 diff | @smol | 有 | true | #1–#8（8/8） | 同样双轴分节 + Critical/Important/Minor(Nit)；给出还原断言后应变红的验证步骤作为「测试被阉割」的证据 |
| 2 安全审阅 | default | 无 | false | #1 #4 #5 #6 #7 #8（6/8） | 未达成 #2（对删除的签名校验无 blame/`log -S`）；#3 仅点出第二入口，未给计数命令与风险交叉 |
| 2 安全审阅 | default | 有 | true | #1–#8（8/8） | 报告落 `security-review-payments-relax.md`（143 行），含 Depth、What changed 表（Risk / Blast radius / Tests cover）、每条 HIGH 的 Goal/Preconditions/Steps、用 `grep -rn 'handle_webhook('` 管道接 `wc -l` 数调用方、`git ls-files` 接 `wc -l` 定深度、强制的 Not examined 节 |
| 2 安全审阅 | @smol | 有 | true | #1–#8（8/8） | 同上（176 行报告）；额外把「既有问题」与「本次引入」分开计数，并对每条 Critical 写出「什么情况下降级」 |
| 3 回应审阅 | default | 无 | false | #3 #4 #6（+#7 部分，3.5/8） | 未达成 #1 #2 #5 #8：先改了代码再报告，无编号提问格式，未 grep 调用方，未提行内线程回复 |
| 3 回应审阅 | default | 有 | true | #1–#7（7/8） | 首句即「还没有动任何代码」，三条 `❓ Qn` + `➡️ 建议`；`getRateHistory` 零调用方 → 建议删；对意见 2 用 `Number.parseInt` 实测输出反驳。未达成 #8（无 PR/仓库上下文，未提线程回复） |
| 3 回应审阅 | @smol | 有 | true | #1–#8（8/8） | 最终版复跑：「有任何一条不明确就本轮不动任何文件……尚未修改 rates.ts」+ 三条 `❓ Qn` / `➡️ 建议`；反驳附 `node -e` 输出；`getRateHistory` 零调用方；并主动说明当前目录非 git 仓库、无法用 `gh` 回帖到 PR 线程（#8 达成）。收紧措辞后的第一轮为 7/8（未提线程回复） |
| 4 负例 | default | 无 | false | 全部 3 条 | 写出中间件，无审阅报告 |
| 4 负例 | default | 有 | **false** | 全部 3 条 | 收窄 description 触发词后不再读本 skill（见下） |
| 4 负例 | @smol | 有 | **false** | 全部 3 条 | 同上 |

### Phase D → Phase C 的两次回修（有据）

1. **负例误触发 → 收窄 description。** 第一轮有 skill 运行时，**两种模型的负例都读了本 skill**
   （`events.jsonl` 里有真实的 `read skill://code-review` 调用，不是提示词里的字面量）。
   原因是触发语中的「or before declaring work done」可被读成「任何任务收尾时」。
   改为「to review an already-finished change of your own before calling it done」，
   并把否定边界补成「Do not use for writing a feature or a fix, …」。重跑后两种模型
   `skill_read == false`，且都正常交付了中间件。
2. **「有不清就一条都不实现」不生效 → 把闸门写成动作。** 第一轮有 skill 运行时两种模型都先改了
   清楚的两条、再问不清的两条。原文是「clarify every unclear item before implementing any of
   them」，被理解成「只是不实现不清楚的那几条」。改为 Core rule 19「wait for the answers before
   touching any item, the clear ones included」+ `respond-to-review` 第二步「Count the unclear
   items. One or more unclear: no file is edited this turn.」重跑后 default 与 @smol 都明确声明
   本轮不改任何文件。

Phase D1 静态与安装冒烟：`uv run tools/validate_skills.py skills/code-review` 只剩允许存在的
`NOTICE.md is missing`（0 warning）；`npx skills@latest add <repo> --skill code-review --agent
universal --copy --yes` 安装到 `/tmp/hs-smoke-cr/.agents/skills/code-review/`，`SKILL.md`、
四份 `references/`、`SOURCES.yaml`、`evals/` 与夹具齐全。

结论：**通过**。基线未达成而有 skill 时达成的行为，两种模型都出现且互相独立：

- 场景 1：#4（对删除的守卫做 `git log -S` / `git blame`）、#5（双轴分节不重排）、#6（严重度分级）
  ——default 与 @smol 均从「未达成」变为「达成」。
- 场景 2：#2（对删除的签名校验取证）与 #3（按调用方计数的爆炸半径 + 风险交叉）——两种模型均达成。
- 场景 3：#1（有不清则本轮不动手）、#2（编号提问 + 推荐答案）、#5（YAGNI grep）——两种模型均达成。
  #8（行内线程回复）：@smol 在最终版复跑中达成（明说无 git 仓库、无法用 `gh` 回帖），default 那一轮
  未提；夹具里没有真实 PR 上下文，这条的达成本身带随机性。
- 负例：两种模型 `skill_read == false`，说明收窄后的触发词没有过度捕获。

@smol 与 default 的差别只体现在篇幅与个别细节的深度（如 @smol 在场景 2 的报告更长但对
`credit_balance` 的降级条件写得更细），行为清单的达成情况一致。

## 备注

- **trailofbits 的 CC-BY-SA-4.0 处理方式（红线，勿改）**：`references/security-review.md` 与
  SKILL.md 的 `security-review-delta` workflow 只继承 trailofbits 的**结构与清单语义**
  （风险分级三档、规模三档、blame 删除的守卫、调用方计数爆炸半径、覆盖升档、升级触发器、
  报告落文件），**全部句子、表格划分与阈值表述均为本仓库原创**，未复制任何原文；其
  Solidity 专属内容（`onlyOwner`、reentrancy、`*.sol`）已改写为语言中立表述。
  `SOURCES.yaml` 中该条 `license: CC-BY-SA-4.0` 且 `notes` 记录此约束。后续同步时若要引入
  新内容，仍须重写而不得粘贴。
- **anthropics/claude-code 是专有许可**（`LICENSE.md`：© Anthropic PBC, All rights reserved，
  受 Anthropic Commercial Terms 约束），永久保持 `relation: reference`，一字不抄。
- 今日 GitHub API 未认证限流（60/h）在第 6 个仓库后触发。后续同步前建议 `export GITHUB_TOKEN=…`；
  `check_upstream.py` 已内置 `git ls-remote` 回退，取 HEAD 不受限流影响。
- 三个工程实践 skill（`test-driven-development`、`debugging`、`code-review`）共享四段文字：
  完成门、grilling 提问格式、seam 定义、重构归属。本 skill 按主代理下发的字面文本落地，
  三处不互相链接，只用技能名提及。上游同步时若改动这四段，必须三处同时改。
- 未来盯的上游：obra/superpowers 与 addyosmani/agent-skills 推送频繁（当日均有提交），
  同步时优先看 `receiving-code-review` 与 `code-review-and-quality` 的 diff；trailofbits
  `differential-review` 的 `patterns.md` 若新增语言中立的漏洞模式，值得重写补入。
