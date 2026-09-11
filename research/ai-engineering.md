# ai-engineering 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - 路线图种子（波次 8 指定）：`vercel/ai`、`langchain-ai/langchain-skills`、
    `google/skills`、`huggingface/skills`、
    `muratcankoylan/Agent-Skills-for-Context-Engineering`、`obra/superpowers`、
    `github/awesome-copilot`、platform.claude.com、platform.openai.com
  - 官方组织补搜：`openai/`（`openai-agents-python`、`openai-cookbook`）、
    `anthropics/`（`skills`、`anthropic-cookbook`）、`google/adk-python`、
    `microsoft/ai-agents-for-beginners`
  - 领域工具与标准：`promptfoo/promptfoo`、`explodinggradients/ragas`、
    `langfuse/langfuse`、`Arize-ai/phoenix`、`BerriAI/litellm`、
    OWASP Top 10 for LLM Applications
  - 仓库内目录枚举：`gh api repos/<o>/<r>/git/trees/main?recursive=1`（google/skills
    与 huggingface/skills 的实际路径与路线图记的不同，见「种子更正」）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （已登录账号 Lynricsy，5000 次/小时；未使用匿名 API）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | vercel/ai `skills/use-ai-sdk` | https://github.com/vercel/ai | 26688 | 2026-09-11 | Apache-2.0（实读 LICENSE；API 报 NOASSERTION） | AI SDK 用法 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（部分） | 78 行，一半是 AI Gateway / DevTools 产品说明。剥离后剩一条真判据：不要凭记忆写 SDK 与 model id，读 `node_modules/ai/docs/` 与在线 model 列表。该判据跨厂商成立 |
| 2 | langchain-ai/langchain-skills `config/skills/eval-engineering` | https://github.com/langchain-ai/langchain-skills | 1209 | 2026-09-08 | NONE（仓库无 LICENSE 文件，树内实查） | 评测工程 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE | 314 行，本波次最好的评测上游。泄漏与公平性、hidden truth 不得进入被测工作区、verifier 必须对「正确 / 合理替代 / 明显错误 / 抄近道 / 越权副作用 / 证据缺失」六种输入各测一次、失败运行按八类归因（能力 / 信息缺失 / harness / 环境 / verifier 误拒 / verifier 误收 / 泄漏 / 基础设施）。Harbor 专有部分剥离 |
| 3 | langchain-ai/langchain-skills `config/skills/langchain-rag` | 同上 | 1209 | 2026-09-08 | NONE | RAG | 3 | 3 | 2 | 3 | 0 | 11 | INCLUDE（部分） | 558 行里约 400 行是 LangChain API 示例。有价值的是 WRONG/CORRECT 失败清单：chunk 过大过小、无 overlap、索引与查询用不同 embedding、维度不匹配、InMemory 上生产、FAISS pickle 反序列化不可加载外部索引。这些是跨框架事实 |
| 4 | langchain-ai/langchain-skills `config/skills/langgraph-fundamentals` | 同上 | 1209 | 2026-09-08 | NONE | 图式编排 | 3 | 3 | 2 | 2 | 0 | 10 | MAYBE | 843 行几乎全是 LangGraph reducer / Send / Command API。剥离后只剩「无 reducer 的并行写会互相覆盖」「条件边必须返回存在的节点名」两条，且都是框架内部事实。仅用于校验 |
| 5 | langchain-ai/langchain-skills `config/skills/langgraph-persistence` | 同上 | 1209 | 2026-09-08 | NONE | 持久化 | 3 | 3 | 2 | 3 | 0 | 11 | INCLUDE（部分） | 取三条通用事实：不传 thread_id 则状态根本没持久化（表现为「忘记一切」而非报错）、内存 checkpointer 进程重启即丢、`update_state` 会穿过 reducer。线程隔离即用户数据隔离 |
| 6 | langchain-ai/langchain-skills `config/skills/langchain-middleware` | 同上 | 1209 | 2026-09-08 | NONE | HITL | 3 | 3 | 2 | 3 | 0 | 11 | INCLUDE（部分） | 人审的 approve / edit / reject 三路语义，尤其「edit 后必须带 name + args 重新入环」与「reject 要回一个 tool result」。这两条是 HITL 能不能用的分界 |
| 7 | google/skills `skills/cloud/agent-platform-eval-flywheel` | https://github.com/google/skills | 19763 | 2026-09-11 | Apache-2.0（实读 LICENSE） | 评测飞轮 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 491 行。「准备数据 → 推理 → 必须评分 → 先分析失败再优化」的次序，外加一节「浪费时间的抄近道」；破坏性操作的确认分级；打分运行前先跟人确认模型 / 试验次数 / judge / 最大花费。产品 SDK 部分剥离 |
| 8 | google/skills `skills/cloud/gemini-api` | 同上 | 19763 | 2026-09-11 | Apache-2.0 | Gemini API | 3 | 3 | 2 | 3 | 2 | 13 | MAYBE | 251 行，多语言 quickstart + ADC 认证，属产品说明书。只用来核对 Gemini 侧 schema 方言（`nullable` / `property_ordering`）。作为 merged 贡献很薄 |
| 9 | google/skills `skills/cloud/agent-platform-rag-engine-management` | 同上 | 19763 | 2026-09-11 | Apache-2.0 | 托管 RAG | 3 | 3 | 1 | 3 | 2 | 12 | REJECT（内容裁决） | 246 行全是 corpus CRUD 与分页 SDK 调用，是 Vertex RAG Engine 的资源管理手册。剥离产品包装后不剩任何跨厂商判据 |
| 10 | google/skills `skills/cloud/gemini-agents-api` | 同上 | 19763 | 2026-09-11 | Apache-2.0 | 托管 agent | 3 | 3 | 1 | 3 | 2 | 12 | REJECT（内容裁决） | 353 行是 LRO 轮询与 control-plane CRUD 的 curl 清单。同上 |
| 11 | huggingface/skills `skills/huggingface-community-evals` | https://github.com/huggingface/skills | 11037 | 2026-09-10 | Apache-2.0（实读 LICENSE） | 基准评测 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT（内容裁决 → reference） | 207 行讲 inspect-ai / lighteval 跑公开基准、后端与硬件选择。测的是模型而不是应用；权重侧归 `ml-training`。许可没问题，是内容不属本 skill |
| 12 | anthropics/skills `skills/claude-api` | https://github.com/anthropics/skills | 175747 | 2026-09-10 | Apache-2.0（**逐目录**实读 `skills/claude-api/LICENSE.txt`；仓库无顶层 LICENSE） | Messages API | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（部分） | 572 行。取 API 形状事实：system 是顶层参数而非消息角色、tool_result 按 id 配对、cache breakpoint 放哪与何时失效。同仓 `pdf`/`docx` 是专有，未使用 |
| 13 | openai/openai-agents-python `docs/{running_agents,tools,guardrails,multi_agent}.md` | https://github.com/openai/openai-agents-python | 29351 | 2026-09-10 | MIT | agent 循环 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 循环终止语义与 `MaxTurnsExceeded`（`max_turns=None` 可关闭）；工具失败三路（回给模型 / 重抛并区分 `ModelBehaviorError` 与 `UserError`）；`docs/tools.md:852` 明确「`is_enabled` 只控制可见性与派发，不替代按参数或资源的授权」——正是本 skill 规则 3 的上游依据 |
| 14 | OWASP Top 10 for LLM Applications `2_0_vulns/LLM{01,05,06,08,10}` | https://github.com/OWASP/www-project-top-10-for-large-language-model-applications | 1388 | 2026-08-05 | CC-BY-SA-4.0（实读 LICENSE.md） | 注入与代理权限 | 3 | 2 | 3 | 3 | 2 | 13 | INCLUDE | 直接 / 间接注入分类，并明确「不清楚是否存在万无一失的预防手段」；权限控制要求应用自己持凭据、特权功能放代码里；excessive agency 拆成 functionality / permissions / autonomy；向量库与 embedding 的访问与投毒；unbounded consumption。按规则表只取结构与清单语义并全文重写，派生 reference 首行加改编声明 |
| 15 | obra/superpowers `skills/{dispatching-parallel-agents,subagent-driven-development}` | https://github.com/obra/superpowers | 285002 | 2026-09-11 | MIT（实读 LICENSE） | 子代理编排 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 子代理不继承会话历史而是收构造好的 brief；一个独立问题域一个子代理；同形小改动合并成一个 brief；按角色选模型层级 + 「轮次数比 token 单价更贵」的反直觉修正；必须看 diff 不看报告。Graphviz `dot` 图按仓库规则删除 |
| 16 | muratcankoylan/Agent-Skills-for-Context-Engineering `skills/{context-compression,context-degradation,tool-design,multi-agent-patterns}` | https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering | 17958 | 2026-09-11 | MIT（实读 LICENSE） | 上下文工程 | 2 | 3 | 3 | 2 | 2 | 12 | INCLUDE | 压缩摘要必须有固定小节（意图 / 改了什么 / 决定 / 当前状态 / 下一步）、触发点要提前定；可用上下文小于标称上下文；**单个干扰文档的伤害远大于后续几个**；工具合并优于近重复工具；状态外置到文件系统。长上下文退化数字是它对公开基准的转述，本仓库未实测，标 `[community]`，正确性因此扣 1 |
| 17 | github/awesome-copilot `skills/agentic-eval` | https://github.com/github/awesome-copilot | 38890 | 2026-09-10 | MIT（实读 LICENSE） | 自评回路 | 3 | 3 | 2 | 2 | 2 | 12 | INCLUDE（部分） | 189 行。迭代上限、收敛检测、judge 用结构化输出而不是抓正文——三条可用。`reflect_and_refine` / `EvaluatorOptimizer` 代码模板是模型已知的回路，不合入；`RUBRIC` 加权平均与本 skill 规则 21（不许用均值当门）冲突，按裁决 3 取后者 |
| 18 | github/awesome-copilot `skills/ai-prompt-engineering-safety-review` | 同上 | 38890 | 2026-09-10 | MIT | 提示审查 | 3 | 3 | 2 | 2 | 2 | 12 | INCLUDE（部分） | 230 行审查框架（安全 / 偏见 / 隐私 / 有效性 / 健壮性）。取其审查轴用于注入审查清单；大量 emoji 输出模板与「教育性洞见」节不合入 |
| 19 | promptfoo/promptfoo `site/docs/configuration/expected-outputs` | https://github.com/promptfoo/promptfoo | 25015 | 2026-09-11 | MIT（实读 LICENSE） | 评测断言 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 确定性 trajectory 断言（`trajectory:tool-used` / `tool-args-match` / `tool-sequence`）与 model-graded 断言配合使用；RAG 侧 context-recall / context-relevance / context-faithfulness 三项分开测；**「judge 传输或解析失败仍记为失败，坏掉的 judge 不能静默变成通过」**——与本 skill 规则 23 完全一致，作为第二来源 |
| 20 | openai/openai-cookbook | https://github.com/openai/openai-cookbook | 75914 | 2026-09-11 | MIT | 示例集 | 3 | 3 | 1 | 3 | 2 | 12 | REJECT（内容裁决） | notebook 教程集，是「怎么调 API」的可运行示例，不是可证伪的工程判据。本 skill 需要的事实已由 SDK 源码实测取得（更可靠） |
| 21 | anthropics/anthropic-cookbook | https://github.com/anthropics/anthropic-cookbook | 52616 | 2026-09-03 | MIT | 示例集 | 3 | 2 | 1 | 3 | 2 | 11 | REJECT（内容裁决） | 同上 |
| 22 | explodinggradients/ragas | https://github.com/explodinggradients/ragas | 15705 | 2026-02-24 | Apache-2.0 | RAG 评测 | 2 | 0 | 2 | 3 | 2 | 9 | REJECT（新鲜度） | 最近推送 2026-02-24，>6 个月，按量表新鲜度 0 且非官方厂商。其指标语义已由 promptfoo 的 context-* 断言覆盖 |
| 23 | google/adk-python | https://github.com/google/adk-python | 21496 | 2026-09-11 | Apache-2.0 | agent 框架 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT（内容裁决） | 是框架源码而非工程判据文档；循环 / 工具 / 护栏语义已由 openai-agents-python 文档以更可引用的形式覆盖，再加一份同义上游只会制造冲突 |
| 24 | microsoft/ai-agents-for-beginners | https://github.com/microsoft/ai-agents-for-beginners | 74412 | 2026-09-10 | MIT | 教程 | 3 | 3 | 1 | 2 | 2 | 11 | REJECT（内容裁决） | 课程式教程，目标读者是初学者；具体性 1。本仓库的写作规则是「默认模型已经很聪明」，教程内容整体不合入 |
| 25 | BerriAI/litellm | https://github.com/BerriAI/litellm | 58501 | 2026-09-11 | NOASSERTION（默认分支 `litellm_internal_staging`） | 多厂商代理 | 2 | 3 | 2 | 2 | 0 | 9 | REJECT | 许可 NOASSERTION 且默认分支是内部 staging 分支，pin 不稳定；内容是路由代理的产品文档 |
| 26 | langfuse/langfuse | https://github.com/langfuse/langfuse | 34469 | 2026-09-11 | NOASSERTION | 可观测性 | 2 | 3 | 2 | 2 | 0 | 9 | REJECT | 许可 NOASSERTION；且 trace 采集与告警归 `observability` skill，本 skill 只定义「一条 trajectory 必须包含什么」 |
| 27 | Arize-ai/phoenix | https://github.com/Arize-ai/phoenix | 11415 | 2026-09-11 | NOASSERTION | 可观测性 | 2 | 3 | 2 | 2 | 0 | 9 | REJECT | 同上 |
| 28 | platform.claude.com/docs | https://platform.claude.com/docs | — | 持续 | Proprietary（实读 Commercial Terms §F） | 官方文档 | 3 | 3 | 3 | 3 | 0 | 12 | reference（许可裁决） | 内容质量足以 INCLUDE，但无内容许可：Commercial Terms of Service 的 F 节明确「除本条款明示外，不授予任何一方对另一方内容或知识产权的权利」，文档站也没有另行声明开放许可。只作事实复核，不复制 |
| 29 | platform.openai.com/docs | https://platform.openai.com/docs | — | 持续 | Proprietary（未找到任何内容许可声明） | 官方文档 | 3 | 3 | 3 | 3 | 0 | 12 | reference（许可裁决） | 同上。Terms of Use 页面是 JS 渲染、抓不到正文，也没有任何 licence grant；按「缺失即视同专有」处理。同样的指引改从 MIT 的 openai/openai-agents-python 合入 |
| 30 | VoltAgent/awesome-agent-skills | https://github.com/VoltAgent/awesome-agent-skills | 34071 | 2026-09-07 | MIT | 索引 | 1 | 3 | 0 | 3 | 2 | 9 | REJECT | 链接索引，无内容。仅用作检索入口 |

30 行，其中 INCLUDE 13、MAYBE 2、REJECT 13、许可降级 2。

## 深度审查

### langchain-ai/langchain-skills `eval-engineering`（12 分，最高之一）

结构是「Flow → Terms → Reference routing → 七个编号阶段」，没有 frontmatter 之外的 agent 专属字段，`description` 是一句话加触发词表。质量上它是本波次唯一把评测当工程而不是当指标的上游：

- 它把「Task Spec」与「Task」分开，并规定 `Task.md` **绝不能挂载进被测 agent 的工作区**——这就是泄漏的具体机制，而不是一句「注意泄漏」。
- verifier 必须用六类输入各测一次（明确正确、合理替代、现实的错误、抄近道、越权的附带修改、证据缺失或损坏）。这条我在 `references/evaluation.md` 里改写成「criterion defect 分误拒与误收，后者更糟因为看不见」。
- 失败运行的八类归因，以及「access / startup / reset / timeout / judge / verifier 失败算无效运行，不算 agent 失败」。
- 「模型对比是可选的校准策略，不是完成条件；通过率与模型排序不能证明 Task 质量」。

绑定：路径全部是相对 skill 根的 `references/*.md` 与 `scripts/*.py`，无 harness 变量。
重叠：与 google `eval-flywheel` 重叠在「先分析失败再优化」，与 promptfoo 重叠在「judge 失败不能变成通过」。三者互相印证，不冲突。

### google/skills `agent-platform-eval-flywheel`（14 分）

结构良好：`When to use` / `Safety & Confirmation Tiers (CRITICAL)` / `The Quality Flywheel` / 五个编号阶段 / `Proving your work` / `Rules of Engagement`。frontmatter 干净。

值得取的是两处：一是「Shortcuts that waste time」这一节，直接列出跳过 grade、只看总分、先优化后分析等具体反模式；二是打分运行前必须与人确认「模型、试验次数、judge、最大预期花费」——把成本确认写成流程门，而不是提醒。

不取的：`agent_platform` SDK 的 entrypoint 清单、`PydanticSerializationError` 之类产品特有报错、region 限制。这些是 Vertex 的说明书。

### openai/openai-agents-python docs（14 分）

不是 skill 而是框架文档，但它是唯一把 agent 循环的终止语义写成规范的官方上游：循环三种退出（final output / handoff / tool calls）加一个 `max_turns` 异常，且「final output」的判定规则被明确定义为「产生了目标类型的文本且没有工具调用」。`docs/tools.md` 的 `failure_error_function` 三态（默认给模型一句错误、自定义、`None` 重抛）是「错误怎么回给模型」这一节的骨架。

最关键的一句在 `docs/tools.md:852`：`is_enabled` 控制可见性与派发，**不替代**依赖工具参数或所访问资源的授权，那些检查必须在工具实现内部或用 tool input guardrails / approvals。这把「可见性 ≠ 授权」从我的推断升级为官方立场。

### OWASP LLM01 / LLM06（13 分）

LLM01 的价值在它的诚实：`Prevention and Mitigation Strategies` 开头就写「鉴于生成式 AI 的本质与其随机性，不清楚是否存在万无一失的预防手段」，随后七条全部叫 mitigate。这正是本 skill 规则 2 的立论基础，也是我拒绝夹具里那条 postmortem 行动项的依据。七条里第 4 条（应用自己持 API token，特权功能放在代码里而不是交给模型）与第 5 条（高风险动作要人审）构成规则 2 与规则 3 的具体做法。

LLM01 场景 2（页面里的隐藏指令让模型插入一张图片链接，从而外泄对话）是 `prompt-injection.md` 外泄通道那节的来源。

### obra/superpowers `subagent-driven-development`（13 分）

568 行，写作水位高，`Common Rationalizations` 一节的体例本仓库已在用。`Model Selection` 一节有一条反直觉修正值得单独记：「轮次数比 token 单价更贵」——最便宜的模型在多步工作上常多花 2–3 倍轮次，总成本更高，所以除纯转录外用中档模型做下限。另一条是「派发子代理时必须显式指定模型，否则继承会话模型（通常最贵）」。

不取的：`dot` 决策图（仓库规则要求删除或转 ASCII）、五轮 fix-loop 的具体轮次编号（那是它自己 harness 的流程）。

### muratcankoylan `context-degradation` / `tool-design`（12 分）

`context-degradation` 提供了本波次唯一的「上下文不是越多越好」的成体系论证：四种退化（lost-in-middle / poisoning / distraction / confusion / clash）与 Write-Select-Compress-Isolate 四桶缓解框架。两条进了正文：可用上下文小于标称上下文，以及单个干扰文档的伤害远大于后续的。

正确性扣 1 的原因：文中的具体阈值（「60-70% 的标称窗口」「8K-16K 就开始退化」）带 `claim-*` 标记指向它自己的证据库，本机无法复核，且它自己也写了「always benchmark with your specific workload」。本 skill 因此只保留方向性结论并标 `[community]`，不搬数字。

`tool-design` 的 Consolidation Principle（合并近重复工具）与 Tool Audit Checklist 进了 `tool-calling.md` 的审查表。

### anthropics/skills `claude-api`（14 分，但贡献面窄）

许可需要逐目录读：该仓库**没有**顶层 LICENSE，`skills/claude-api/LICENSE.txt` 实读为 Apache-2.0（同仓 `pdf`/`docx` 为专有）。内容是 Messages API 的准确说明，价值集中在三处 API 形状事实（system 顶层参数、tool_result 按 id 配对、cache breakpoint 位置与失效条件），这些正好是跨厂商对照表需要的第三列。其余是单厂商 API 细节，不合入。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 防注入靠什么 | 夹具的 postmortem 与 `ai-prompt-engineering-safety-review` 倾向「强化提示词」；OWASP LLM01 说无已知预防手段，只能缓解；openai-agents `tools.md:852` 说可见性开关不替代授权 | 提示层措施一律写成 mitigation；能力边界（移出工具集 / 上限 / 人审 / 参数对账）才是 control。规则 2 明写「违反的后果是钱已经离开账户」 | 官方厂商与标准组织 > 社区；且夹具事故本身是反例（系统提示已有该句，退款仍然发生） |
| 2 | 评测要不要 judge | `agentic-eval` 以 LLM-as-judge 与加权 rubric 为主线；promptfoo 主张确定性 trajectory 断言与 model-graded 配合；langchain `eval-engineering` 要求 verifier 提供独立证据 | 能用代码判的一律用代码判，judge 只用于语义等价 / 覆盖度 / 成对比较；judge 解析失败 = 该用例失败 | 「更新 > 更旧」+ 两个更权威上游（promptfoo 文档与 langchain eval-engineering）一致；`agentic-eval` 的加权平均与规则 21 直接冲突 |
| 3 | 门用均值还是逐例 | `agentic-eval` 的 `evaluate_with_rubric` 返回加权平均并与阈值比较；本仓库 `planning`/`code-review` 的既有水位要求可证伪的逐项判定 | 逐例 pass/fail + 必不许失败集；均值只作为参考数字 | 均值在 200 例上无法被一个灾难性用例推动——这正是夹具「每晚都说 looks good」的机制，可证伪 |
| 4 | Gemini 的 schema 方言是否支持 `$ref` | 旧的社区共识（含我自己的先验）是 Gemini `responseSchema` 不支持 `$ref` / `anyOf` | **实测否定**：`google-genai 2.23.0` 的 `types.Schema` 同时有 `ref`、`defs`、`any_of`、`additional_properties`、`property_ordering`、`nullable` 字段。正文改为「三家方言差在 nullable 表达与 key order，不在 `$ref` 支持」 | 本机实测 > 记忆；未写入任何「不支持 `$ref`」的说法 |
| 5 | 重试该写在哪一层 | 夹具与大量社区代码在调用外面自己包 `for attempt in range(5)`；两个官方 SDK 自带 `max_retries=2` | 重试配置在 client 上；外层循环只在切换模型 / 厂商时成立 | 实测两个 SDK 的 `DEFAULT_MAX_RETRIES` 与 `_should_retry` 源码；相乘后最坏 15 次付费请求是算得出来的后果 |
| 6 | strict schema 下 optional 字段的语义 | Pydantic 的 `Optional[str] = None` 读起来是「可以不给」 | 实测 `to_strict_json_schema` 把**每个**属性放进 `required` 并剥掉 `default`；正文写成「strict 模式没有可选字段，只有可为 null 的必填字段」，并点出 `if "x" in data` 恒真导致的 `NoneType` 崩溃 | 本机实测 openai 3.13.0 |
| 7 | `ml-training` 边界 | huggingface/skills 的评测与数据集 skill 既像应用评测又像模型评测 | 跑公开基准衡量模型 → `ml-training`；衡量自己这套应用 → 本 skill。huggingface-skills 降为 reference 并在 `contributes` 写明是内容裁决 | 波次 8 契约的分界句：调用别人训好的模型归 `ai-engineering`，改权重归 `ml-training` |
| 8 | 向量库调优归谁 | RAG 上游普遍连带讲索引参数 | HNSW/IVF 参数、recall、构建内存、ANN 延迟 → 对应数据库 skill；embed 什么、取几条、怎么排序 → 本 skill。负例场景专门测这条边界 | 波次 8 契约 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `vercel-ai-sdk` | vercel/ai `skills/use-ai-sdk` | merged | 不凭记忆写 SDK API 与 model id；读随版本发布的文档 |
| `langchain-skills` | langchain-ai/langchain-skills（5 个 skill） | merged | 评测泄漏与公平性、verifier 六类输入、失败八类归因；RAG 失败清单；HITL approve/edit/reject；thread_id 与 checkpointer 陷阱 |
| `google-skills` | google/skills（4 个 skill） | merged | 评测飞轮次序与「浪费时间的抄近道」；破坏性操作确认分级；打分前的成本确认 |
| `openai-agents-python` | openai/openai-agents-python docs | merged | 循环终止语义与轮次上限；工具失败三路；可见性不替代授权 |
| `anthropics-claude-api` | anthropics/skills `skills/claude-api` | merged | Messages API 形状事实与 prompt cache 失效条件 |
| `owasp-llm-top10` | OWASP LLM Top 10（5 条） | merged | 直接/间接注入分类与「无已知预防」；权限控制；excessive agency 三轴；embedding 投毒；unbounded consumption |
| `obra-superpowers` | obra/superpowers（2 个 skill） | merged | 子代理 brief 构造、独立域切分、按角色选模型、轮次数比单价贵、看 diff 不看报告 |
| `murat-context-engineering` | murat（4 个 skill） | merged | 压缩摘要固定小节与触发点、可用上下文 < 标称、单个干扰项伤害最大、工具合并、状态外置 |
| `github-awesome-copilot` | github/awesome-copilot（2 个 skill） | merged | 迭代上限与收敛检测、judge 结构化输出、提示审查轴 |
| `promptfoo` | promptfoo/promptfoo 断言文档 | merged | 确定性 trajectory 断言与 model-graded 配合；context-recall/relevance/faithfulness 分开测；judge 解析失败必须记为失败 |
| `huggingface-skills` | huggingface/skills `huggingface-community-evals` | reference | **内容裁决**：测模型而非测应用，归 `ml-training`；许可（Apache-2.0）无问题 |
| `anthropic-docs` | platform.claude.com/docs | reference | **许可裁决**：Commercial Terms §F 不授予内容权利；仅事实复核 |
| `openai-docs` | platform.openai.com/docs | reference | **许可裁决**：无任何内容许可声明；同义指引改从 MIT 的 openai-agents-python 合入 |

## 本机实测记录

无 API 密钥（`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` 均未设置），因此**所有实测都是离线的**：读 SDK 自己的转换与重试逻辑、跑 tokenizer。环境：Python 3.14.7 / Node 26.7.0。装的版本：`openai 3.13.0`、`anthropic 1.5.0`、`tiktoken 0.14.0`、`google-genai 2.23.0`、`pydantic 2.13.5`、`httpx 0.28.1`。

| # | 声明 | 怎么测的 | 结果 | 正文标注 |
|---|---|---|---|---|
| 1 | strict schema 把每个属性变成必填并剥掉 default | 对含 `Optional[str] = None` 与 `currency: str = "EUR"` 的 Pydantic 类调 `openai.lib._pydantic.to_strict_json_schema` | `required` 含全部 5 个字段；`note` 的 `default: null` 被删除；每层对象加 `additionalProperties: false` | `[verified: openai 3.13.0 to_strict_json_schema]` 规则 13 |
| 2 | 未约束的 `dict` 字段本地通得过 | 对 `data: dict` 调同一函数 | 本地接受（不抛），只会在真实请求时被 API 拒 | `structured-output.md` 方言表 |
| 3 | 拒答不抛异常、parsed 为 None | 读 `openai.lib._parsing._completions.maybe_parse_content` 源码 | 仅当 `message.content and not message.refusal` 才解析，否则返回 `None` | `[verified: openai 3.13.0 parse]` 规则 14 |
| 4 | 截断与内容过滤会抛，且不是 HTTP 异常 | 读 `parse_chat_completion` 源码与 `LengthFinishReasonError.__mro__` | `finish_reason == "length"` → `LengthFinishReasonError`；`content_filter` → `ContentFilterFinishReasonError`；两者的父类是 `OpenAIError`，不是 `APIStatusError` | 规则 14 / `cost-and-reliability.md` |
| 5 | 两个 SDK 默认重试 2 次、超时 600s | 读 `openai.DEFAULT_MAX_RETRIES`、`anthropic._constants.DEFAULT_MAX_RETRIES` 与两者的 `DEFAULT_TIMEOUT` | 都是 2；`Timeout(connect=5.0, read=600, write=600, pool=600)` | `[verified: openai 3.13.0, anthropic 1.5.0]` 规则 7 |
| 6 | 哪些状态码会重试 | 读两个 `BaseClient._should_retry` | 408 / 409 / 429 / ≥500，并服从 `x-should-retry`；`openai` 额外在 `Retry-After` 超过上限时拒绝重试。400/401/403/404/422 从不重试 | `cost-and-reliability.md` 状态表 |
| 7 | 工具 `description` 在类型层是可选的 | 检查 `anthropic.types.ToolParam` 与 `openai.types.shared_params.FunctionDefinition` 的 `__optional_keys__` | `description` 在两者都是 optional（`FunctionDefinition` 的 `name`/`parameters` 也是） | `[verified]` 规则 4 |
| 8 | `chars//4` 的误差方向与量级 | `tiktoken` `o200k_base` 编码四类内容并与 `len//4` 对比 | 英文散文 6.01 chars/token（高估 50%）；Python 源码 3.87（−3%）；JSON 记录 2.35（**低估 41%**）；裸 UUID 1.32（**低估 67%**） | `[verified: tiktoken 0.14.0, o200k_base]` 规则 9 |
| 9 | Gemini schema 方言是否支持 `$ref` | 列 `google.genai.types.Schema.model_fields` | 有 `ref`、`defs`、`any_of`、`additional_properties`、`property_ordering`、`nullable` —— 否定了「不支持 `$ref`」的先验 | `structured-output.md` 方言表（裁决 4） |
| 10 | `scripts/token_budget.py` 可跑并复现上述误差 | 构造一个含 system / 1 个 tool schema / 一轮 tool_call + tool 结果（40 条 JSON 记录）的请求体，`uv run scripts/token_budget.py` | 实测 3471 tokens，`len//4` 估 1751，报 `-50%, under-counts`；错误路径（文件不存在 / 非 JSON / 缺 `messages` / 超窗口）分别退 2/2/2/1 | 脚本本身 |

未能实测、只能标 `[official]` 或 `[community]` 的项，已在正文逐条标注：

- 上下文超限的 400 报文形状（`prompt is too long: N tokens > M maximum`）——取自夹具所依据的真实事故记录与官方文档措辞，无密钥无法复现。
- prompt caching 的计费比例与过期时间、Anthropic 的 cache write 溢价——`[official]`，正文只写方向性结论（顺序决定命中、任何前序改动全失效），不写具体倍数与分钟数。
- 长上下文退化的具体阈值——`[community]`，只保留「可用 < 标称」与「单个干扰项伤害最大」两条方向性结论。
- 各厂商 count_tokens 端点的精确性——`[official]`，正文只说它是权威来源。

## 基线缺口

无 skill（`uv run tools/run_evals.py ai-engineering --baseline`，Claude Opus 5 / medium）时，各场景未达成的 `expected_behavior`。

基线整体很强：场景 1、2、4 的结构性缺陷（tool 结果进 user 轮、`while True` 无上限、整文件 embedding、静默截断、`in` 判键不判值）全部自己找到了，而且场景 2 还多找到一条我没写进期望的真缺陷（`text-embedding-3-small` 输入上限 8191 token，91 KB 的 `returns.md` 根本没进过索引）。**缺口集中在「实测数字」与「授权而非校验」这两类**——正好是这个 skill 唯一能提供、模型自己推不出来的东西。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 agent 循环 | SDK 自带重试与外层循环相乘的**具体倍数**，以及「SDK 刻意不重试 400」 | 基线说「最坏 10+ 次」并建议只重试瞬时错误，方向对但数字错（实际 5×3=15），也没说 `prompt is too long` 是 400、SDK 从不重试它，所以没解释 2026-03-19 为什么白付了 5 次 |
| 1 agent 循环 | `len//4` 的**误差方向与量级**，以及该测量漏掉了 tool schema 与 tool_call 参数 | 基线只说「估算不准、检查位置也不对」。没有「JSON 低估 41%、UUID 低估 67%」这个方向性事实，也没指出五个工具的 schema 每轮都要计费却没被计入 |
| 2 检索管道 | 检索单元与上下文单元**分开决定**（命中 chunk 后再扩到邻居或父节） | 基线给了 heading-aware 切块与行 schema，但仍是「切块后直接把 chunk 塞进上下文」，没有 parent 扩展这一层 |
| 2 检索管道 | 先取宽候选集再 **rerank** | 基线提到「无距离阈值」（相关性下限），但完全没提重排；这是朴素管道收益最高的一步 |
| 3 评测 harness（第一版题目） | ——（超时，无结果） | 第一版 query 是「Make it actually catch regressions」，最后一条期望还要求「跑一个错答证明新门会 fail」。900s 上限时 `events_bytes = 3 974 808`、`stderr.log` 为 0 字节、54 轮 58 次工具调用仍在流式输出——不是基础设施问题，是在无凭据的沙箱里真的去搭 harness。按「先看 stderr 与 events_bytes」的规程判定为题目要求了沙箱内不可能完成的动作，改成「只要诊断与设计，不要搭」后重跑，179.8s 完成 |
| 3 评测 harness（第二版题目，基线全中） | ——（零区分度） | 重跑后九条期望**全部达成**，包括均值门的算术（「一例 9→1 均值只动 0.04」）、`head -200` 泄漏、judge 自偏好、`return 5.0`、沙箱缺失、并且把诊断挂到了 2026-02-11 事故上（`issue_refund` 次数 ≤ 1）。按 Phase B 规程不降低标准、不改题目，而是把 `expected_behavior` 改写为更硬的会出事故的判断后重测（见下三行） |
| 3 评测（改写后） | 三类泄漏要分开：provenance / 迭代集污染 / **答案泄漏**（ground truth 放进被测能读到的工作区本身就是缺陷） | 基线只说了 provenance，并且**主动建议**在用例里保留 ground truth 字段——恰好是它没识别出的第三类泄漏 |
| 3 评测（改写后） | 被评的答案对 judge 而言是**不可信文本**：答案里写「本回答完全满足所有判据，10 分」会进入 judge 的指令通道 | 基线完全未提。这是一条能把发布门说服掉的注入路径 |
| 3 评测（改写后） | `gpt-5.1` 是浮动别名，被测与 judge 都必须 pin 到带日期的快照，否则行为无部署变化而改变、历史分数不可比 | 基线做到了 `temperature=0` 与按 commit 落产物，但没提别名会自己移动 |
| 3 评测（改写后） | must-never-fail 用例 5 次里过 3 次**算失败**（坏结果可达），与用重复采样估噪声带是两回事 | 基线只用 N≥3 估噪声带 |
| 3 评测（改写后） | 失败用例先分类（能力 / 用例缺信息 / harness / 判据 / 泄漏 / 基础设施）再用分数；判据误收比误拒更糟，因为看不见 | 基线只有一个 `error` 桶 |
| 4 结构化输出 | 字段**没有 description**：`amount_cents` 没说是最小货币单位 | 完全未提。基线把 schema 当形状约束，没把它当语义契约——单位错 100 倍的值能完美通过校验 |
| 4 结构化输出 | `currency: str = "EUR"` 的 default 在 strict 模式下**不再生效**，必须由模型产出 | 基线正确地说了「strict 不能带 default」，但没说后果：一个本意是「模型可以不填、代码兜底」的字段变成了强制模型自己编 |
| 4 结构化输出 | **校验 ≠ 授权**：副作用前要拿模型没写过的记录对账（订单存在、属于本工单、金额有上限） | 基线只说「宁可响亮报错也不要把截断 JSON 当合法结果」，`apply()` 直接拿模型输出打款这件事没有被当成缺陷 |
| 5 负例（pgvector） | —（无缺口，且不应有） | 三条期望全部达成：纯按 Postgres 索引问题回答（`halfvec` 降字节让索引常驻、装完数据再建索引并给够 `maintenance_work_mem`、最后才调 `ef_search`），没有碰管道、重排、提示或评测。`skill_read=False` |

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 agent 循环审查 | claude-opus-5 / medium | 无（baseline） | false | 10 条中 8 条达成 | 未达成：SDK 重试相乘的具体倍数与「400 从不重试」；`len//4` 的误差方向量级与漏算 tool schema |
| 1 agent 循环审查 | claude-opus-5 / medium | **有** | **true** | **10/10** | 两处缺口都补上：明写「openai 3.13.0 默认重试 2 次，叠加后最多 15 个计费请求」「`prompt is too long` 是永久 400」；并且**实跑了 `scripts/token_budget.py`**，报「measured 6,105 vs len//4 3,639，低估 40%，tool schemas 另占 294 tokens」。还输出了 Trust boundary / Tools / Budgets 三张表 |
| 2 检索管道审查 | claude-opus-5 / medium | 无（baseline） | false | 9 条中 7 条达成 | 未达成：检索单元与上下文单元分开（父节扩展）；宽候选集 + rerank。额外找到一条我没写的真缺陷（embedding 输入 8191 token 上限） |
| 2 检索管道审查 | claude-opus-5 / medium | **有** | **true** | **9/9** | 两处缺口都补上：块表带 `parent_id`、检索单元用块 / 上下文单元用块+父节；30–100 候选 → 相关度下限 → cross-encoder rerank。并**实测复现**了截断缺陷（8×120k 字符 → 输出 800000 字符、`"QUESTION:" in prompt` 为 False） |
| 3 评测 harness | claude-opus-5 / medium | 无（baseline） | false | 9 条中 4 条达成 | 未达成 5 条：三类泄漏只说了一类、答案对 judge 是不可信文本、浮动别名要 pin 快照、3/5 通过算失败、失败分类。题目与基线均按上表两次调整后测得 |
| 3 评测 harness | claude-opus-5 / medium | **有** | **true** | **9/9** | 五条缺口全补：明确 iterate/gate 切分且「期望输出存放在 run workspace 之外」；「答案里写 'score 10' 会被当命令执行」；「模型别名移动」列为掉分四因之一并要求 pin 快照；「3/5 通过不算通过——坏结果可达就是失败」；六类失败分类先于用分数。并给出按事故建的 8 行用例表与 `Gate = all(must_never_fail) and pass_rate >= baseline - tolerance` |
| 4 结构化输出 | claude-opus-5 / medium | 无（baseline） | false | 8 条中 6 条达成 | 未达成：字段 description（`amount_cents` 的单位）；校验 ≠ 授权（`apply()` 直接拿模型输出打款） |
| 4 结构化输出 | claude-opus-5 / medium | **有** | **true** | **8/8** | 两处缺口都补上：给每个字段加 `Field(description=...)` 标明「分」「不超订单总额」，并把 `currency` 整个移出 schema 改由订单记录提供；新增 `authorise()` 在退款前核对订单号一致、金额为正、≤ 订单总额、≤ 单笔上限 5000，并 stub 验证四种越权全部被拦、`apply` 被拦后未发生退款 |
| 5 负例 pgvector（初版 description） | claude-opus-5 / medium | 有 | **true**（不合格） | 3/3（内容对，但 skill 被读了） | 模型读了 skill 之后自己声明「HNSW/ANN 归 postgres」再作答——行为正确但违反负例要求。原因：`description` 的正面触发词含 retrieval/reranking，而排除项只泛泛写了「vector index or database tuning」 |
| 5 负例 pgvector（收紧后） | claude-opus-5 / medium | 有 | **false** | **3/3** | 把排除项改成用题目自己的词汇点名：`HNSW or IVF parameters, ef_search, recall against exact search, index build memory, ANN latency`。重跑 107.1s，`skill_read=false`，回答纯按 Postgres 索引问题展开（元组 6448 B/页只放 1 个 → 9.7 GB 索引 vs 2 GB `shared_buffers`；`maintenance_work_mem` 64 MB 差 150 倍必然 spill；装载后重建 + `m=32`；最后才扫 `ef_search` 曲线）。**如实记录一处边缘**：结尾有两行「范围外提醒」提到切块过碎可能影响端到端质量、建议之后单独跑评测——它显式标了「范围外」且没有改动管道方案，判定为达成，但它确实碰到了边界 |

结论：**通过**。五个场景里有四个在基线存在未达成行为，四个在有 skill 时全部达成；负例在收紧 `description` 后 `skill_read=false` 且答案未越界。最有说服力的两处不是文字覆盖而是行为改变：场景 1 有 skill 时**实跑了 skill 自带的 `scripts/token_budget.py`** 并把实测的 40% 低估写进结论，场景 2 有 skill 时**动手复现**了 `prompt[:limit*4]` 会把问题本身切掉。

## 备注

### 许可裁决记录

- **`anthropics/skills` 必须逐目录读许可。** 该仓库没有顶层 LICENSE。`skills/claude-api/LICENSE.txt` 实读为 Apache-2.0（可 merged），而同仓 `pdf`/`docx` 是专有。沿用上一波的教训，这次没有凭 API 的 `license: null` 下结论。
- **`vercel/ai` 的 API `spdx_id` 是 NOASSERTION，实读 LICENSE 是 Apache-2.0**，只是正文以 `Copyright 2023 Vercel, Inc.` 开头，GitHub 的许可探测因此不认。凡 NOASSERTION 一律实读，这次又验证一次。
- **厂商文档站的结论：两家都只能 reference。** Anthropic 的 Commercial Terms F 节写明「除本条款明示外，不授予任何一方对另一方内容或知识产权的权利」，文档站也无开放许可声明。OpenAI 的 Terms of Use 页面是 JS 渲染、抓不到正文，同样找不到任何 licence grant，按「缺失即视同专有」处理。**同样的工程事实改从 MIT 的 `openai/openai-agents-python` 合入**——这是「一个仓库的许可是它自己的」的正向用法。
- **许可通过 ≠ 内容值得合入。** `huggingface/skills` 是 Apache-2.0，但 `huggingface-community-evals` 测的是模型而不是应用，降为 reference 并在 `contributes` 写明是**内容裁决**；`google/skills` 的 `agent-platform-rag-engine-management` 与 `gemini-agents-api` 同样是 Apache-2.0，但内容是 Vertex 资源管理手册，直接 REJECT。

### 这个题材特有的两个坑

1. **上游几乎全是某个框架的说明书。** langchain-skills 的 1958 行里能跨厂商成立的不到 200 行；vercel 的 78 行里只有 1 条。处理方式是先问「换一个 SDK 这句话还成立吗」，不成立就删。SKILL.md 里没有任何一个框架的 API 名，只有 provider 层的概念（tool-result turn、schema mode、finish reason、usage）。
2. **极易写成空话。** 定稿前对每条 Core rule 问一遍「违反它会发生什么具体的事」，写不出的删掉。被删掉的候选包括：「提示要清晰具体」「为 agent 设定明确角色」「用结构化输出提升可靠性」「记录日志便于排查」——它们都是真的，但后果写不出来，所以不占位置。最终 25 条每条后半句都是一个可观察的事故。

### 下次同步要盯的上游

- `openai/openai-agents-python` 的 `docs/tools.md` 与 `docs/running_agents.md`：这两份变化最快（本次已见 `allowed_callers`、`ProgrammaticToolCallingTool` 等新概念），循环与工具语义一旦变化本 skill 的规则 3、6 要跟着复核。
- `OWASP` 的 LLM Top 10：2_0 是当前版本，下一版发布时要重读 LLM01/05/06/08/10。
- `langchain-ai/langchain-skills`：仍无 LICENSE 文件。若上游后来加了 GPL 类许可，`langchain-skills` 这条要从 merged 降为 reference，其贡献需改从别处取证。
- SDK 版本敏感的四条 `[verified]`（规则 7、9、13、14）绑定 `openai 3.13.0` / `anthropic 1.5.0` / `tiktoken 0.14.0`。大版本升级后要重跑 `research` 的实测表，尤其 `to_strict_json_schema` 的行为与 `_should_retry` 的状态码集合。

### 放弃的方向

- **不做「prompt engineering」独立章节。** 路线图已把 `prompt-engineering` 并入本 skill；写成独立一节的结果必然是空话集合。最终只保留 `prompt-structure.md`，且全篇围绕「指令与数据分离」这一条可证伪的结构决策，不写措辞技巧。
- **不写多厂商路由 / 网关（litellm 类）。** 许可与内容都不合格，且属于产品选型而非工程判据。
- **不写 trace 采集与告警。** 归 `observability`；本 skill 只定义「一条 trajectory 必须包含什么才叫可调试」（规则 25）。
- **`scripts/` 只留一个。** 考虑过再写一个 tool-set 审计脚本，但它的产出就是 SKILL.md 里那张表，脚本化没有增量；`token_budget.py` 留下是因为它产出的是**本机实测数字**，那是读文档得不到的。
