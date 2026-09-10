# graphql 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`"GraphQL agent skill SKILL.md github claude skills graphql schema design"`
  - <https://www.skills.sh>（apollographql/skills 条目）、claudeskills.info、agent-skills.md 目录页
  - VoltAgent/awesome-claude-code-subagents、rohitg00/awesome-claude-code-toolkit、sickn33/agentic-awesome-skills
  - `github/awesome-copilot`：**整仓 `git/trees?recursive=1` 里 grep `graphql` 零命中**，无 GraphQL 主题的
    `skills/*` 或 `instructions/*`，故本 skill 没有 awesome-copilot 上游（见候选表 #16）
  - 领域官方组织仓库：`apollographql/`、`graphql/`（graphql-js、graphql-spec、graphql.github.io、dataloader）、
    `dotansimha/`（Yoga、codegen）、`hayes/`（Pothos）、`graphql-hive/`（inspector、eslint）、`facebook/relay`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | apollographql/skills · `skills/graphql-schema`（+5 个 references） | <https://github.com/apollographql/skills/tree/main/skills/graphql-schema> | 111 | 2026-07-29 | MIT | 类型/命名/nullability/分页/错误/安全 | 3 | 1 | 2 | 2 | 2 | 10 | INCLUDE | `compatibility: Any GraphQL implementation`，是候选里唯一成体系的 schema 设计上游。扣分点：nullability 一节与 graphql.org 官方立场相反（见冲突 #1），错误传播完全未提 |
| 2 | apollographql/skills · `skills/graphql-operations`（5 个 references） | <https://github.com/apollographql/skills/tree/main/skills/graphql-operations> | 111 | 2026-07-29 | MIT | 操作命名/变量/片段/指令/codegen | 3 | 1 | 2 | 3 | 2 | 11 | INCLUDE | 客户端无关（`compatibility: Any GraphQL client`）。规则抽查 3 条（命名操作、变量优于内联、片段与组件共置）全部与 graphql.org / graphql-eslint 一致 |
| 3 | apollographql/skills · `skills/apollo-federation`（directives/schema-patterns/composition） | <https://github.com/apollographql/skills/tree/main/skills/apollo-federation> | 111 | 2026-07-29 | MIT | Fed 2 指令、实体、组合错误 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 本波唯一权威联邦素材。其 `@link` 版本"floor vs composition"区分和"版本号仅为示例、勿照抄"的提醒质量很高 |
| 4 | apollographql/skills · `skills/apollo-server`（context-and-auth/errors/resolvers…） | <https://github.com/apollographql/skills/tree/main/skills/apollo-server> | 111 | 2026-07-29 | MIT | Apollo Server 4/5 装配 | 3 | 1 | 2 | 3 | 2 | 11 | INCLUDE（限定） | 只取"Apollo 特有默认值"这一层，正文明确标注为 Apollo 而非 GraphQL 通用；其余装配细节属实现说明书，不合入 |
| 5 | apollographql/skills · `skills/apollo-router` | <https://github.com/apollographql/skills/tree/main/skills/apollo-router> | 111 | 2026-07-29 | MIT | Router v1/v2 YAML 配置模板 | 3 | 1 | 3 | 3 | 2 | 12 | REJECT（范围外） | 是单一商业产品的配置手册（`templates/v1|v2/*.yaml`、遥测/流量整形）。网关配置不属于"编写 GraphQL"，写进来必然把本 skill 变成 Apollo 说明书 |
| 6 | apollographql/skills · `skills/apollo-client` | <https://github.com/apollographql/skills/tree/main/skills/apollo-client> | 111 | 2026-07-29 | MIT | React hooks、规范化缓存 | 3 | 1 | 3 | 3 | 2 | 12 | REJECT（范围外） | 按 Contract，React 侧 Apollo Client hooks 与缓存归 `react` skill；此处只在 Scope 里转交 |
| 7 | graphql/graphql.github.io（graphql.org/learn 全部 best-practices 页） | <https://graphql.org/learn/> | 888 | 2026-09-10 | MIT | 规范之外的官方公认实践 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: docs`） | **本 skill 的裁决基准**。已实查：站点源码仓 `graphql/graphql.github.io` 的 API `license.spdx_id == MIT`，因此官方文档可 merged 而非仅 reference |
| 8 | graphql/graphql-spec（`spec/Section 6 -- Execution.md` 等） | <https://github.com/graphql/graphql-spec> | 14590 | 2026-09-10 | NOASSERTION → 实读 `LICENSE.md` | 执行语义、错误传播、`@oneOf` | 3 | 3 | 3 | 3 | 1 | 13 | INCLUDE（`kind: docs`，relation reference） | 实读 `LICENSE.md`：Joint Development Foundation / GraphQL Series 的 technical-charter IP 政策，**不是 SPDX 开源许可**（无 SPDX id，只有版权声明与免责声明）。按规则视同"专有/不明确"→ `license: Proprietary`、`relation: reference`，正文一字不抄，只据其语义自行表述 |
| 9 | SkillMedev/skills · `skills/graphql-schema` | <https://github.com/SkillMedev/skills/blob/main/skills/graphql-schema/SKILL.md> | 12 | 2026-07-05 | MIT | 域建模/Relay/DataLoader/成本限制 | 1 | 1 | 3 | 2 | 2 | 9 | INCLUDE | 星数低但密度最高的社区候选：DataLoader 逐请求实例化、`first` 硬上限 100、成本模型按页大小乘子、按点数而非请求数限流——这些都不在 Apollo 素材里。扣分：`Prefer non-null (!) by default` 与官方相反（冲突 #1），"errors mid-list: return partial results"与 spec 的列表传播规则相反（冲突 #2） |
| 10 | wshobson/agents · `plugins/backend-development/skills/api-design-principles/references/graphql-schema-design.md` | <https://github.com/wshobson/agents> | 39556 | 2026-09-07 | MIT | 583 行 schema 模式合集 | 2 | 3 | 2 | 2 | 2 | 11 | INCLUDE（补充） | 模块化 SDL（`extend type Query`）、订阅、`@defer` 之外的实用片段。属"半通用+代码样例"，作交叉校验与主题清单，不作事实来源 |
| 11 | secondsky/claude-skills · `plugins/graphql-implementation` | <https://github.com/secondsky/claude-skills/tree/main/plugins/graphql-implementation> | 217 | 2026-09-09 | MIT | Apollo Server + Graphene 装配 | 1 | 3 | 1 | 2 | 2 | 9 | MAYBE → 仅作 Python 侧覆盖面参考 | 124 行 SKILL + `references/python-graphene.md`。内容是"抄一段 Apollo Server 启动代码"级别，`users(limit, offset)` 无上限，与本 skill 的分页规则冲突；唯一价值是提醒非 JS 生态（Graphene/Strawberry）存在 |
| 12 | LambdaTest/agent-skills · `api-skill/*`（10 个子 skill） | <https://github.com/LambdaTest/agent-skills/tree/main/api-skill> | 366 | 2026-07-24 | MIT | API 设计/测试/mock/监控 | 1 | 1 | 2 | 2 | 2 | 8 | REJECT（无 GraphQL 内容） | 计划把它列为"GraphQL 测试那一节"的来源，实读后**该节不存在**：`api-designer/SKILL.md` 全文 grep `graphql` 零命中，整个 `api-skill/` 是 REST + LambdaTest 平台导向。GraphQL 测试改从 Yoga/Apollo Server 官方文档取证 |
| 13 | rohitg00/awesome-claude-code-toolkit · `skills/graphql-design` | <https://github.com/rohitg00/awesome-claude-code-toolkit/blob/main/skills/graphql-design/SKILL.md> | 2608 | 2026-05-12 | Apache-2.0 | SDL 样例 + DataLoader + 订阅 | 1 | 1 | 1 | 2 | 2 | 7 | MAYBE → 未采用 | 193 行几乎全是 SDL/JS 代码块，无"为什么"。覆盖面与 #9 重叠且更浅，无独有事实 |
| 14 | sickn33/agentic-awesome-skills · `skills/graphql` | <https://github.com/sickn33/agentic-awesome-skills/blob/main/plugins/agentic-awesome-skills-claude/skills/graphql/SKILL.md> | 46246 | 2026-09-09 | MIT | 概览 + `references/detailed-guide.md` | 1 | 3 | 1 | 1 | 1 | 7 | REJECT | 星数来自聚合仓而非内容。frontmatter 有非规范字段 `risk`/`source`/`date_added`，且自述转载自 `vibeship-spawner-skills (Apache 2.0)`（二手来源）；正文含"2025 lesson"式时间敏感表述，正是标准第 3 节禁止的写法 |
| 15 | Mindrally/skills · `graphql-development`（另有 `apollo-graphql`、`graphql`） | <https://github.com/Mindrally/skills/blob/main/graphql-development/SKILL.md> | 260 | 2026-09-03 | Apache-2.0 | 泛化清单 | 1 | 3 | 0 | 1 | 2 | 7 | REJECT | 89 行全是"Use nullable types appropriately""Implement proper error handling"式空话，且以 `You are an expert in…` 人格设定开头。零可执行规则 |
| 16 | github/awesome-copilot | <https://github.com/github/awesome-copilot> | 38866 | 2026-09-10 | MIT | — | 3 | 3 | — | — | 2 | — | REJECT（无相关内容） | 按 workflow Phase A 要求检索了 `skills/` 与 `instructions/` 两处，`git/trees?recursive=1` 中 `grep -i graphql` 零命中。留行以免后续批次重复检索 |
| 17 | TheBushidoCollective/han · `.claude/rules/graphql/*` | <https://github.com/TheBushidoCollective/han> | 195 | 2026-09-08 | NOASSERTION | 单一 Rust/Relay 项目的内部约定 | 1 | 3 | 2 | 1 | 0 | 7 | REJECT | 不是通用 skill，是某个产品仓的 `.claude/rules`（`greenfairy-filter-pattern`、`one-type-per-file`）。许可未声明且内容与自家宏绑定 |
| 18 | graphql/graphql-js（源码 + graphql-js.org 文档） | <https://github.com/graphql/graphql-js> | 20340 | 2026-09-09 | MIT | 参考实现语义 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: repo`） | 直接读 `v17.0.2` 源码取证：`src/execution/execute.ts:848` 的 `errorPropagation` 开关、`src/type/directives.ts:456` 的 `GraphQLOneOfDirective`（已进 `specifiedDirectives`）、`:471` 的 `experimental_disableErrorPropagation`。npm `graphql@latest == 17.0.2` |
| 19 | dotansimha/graphql-yoga（the-guild.dev/graphql/yoga-server 文档） | <https://github.com/dotansimha/graphql-yoga> | 8529 | 2026-09-09 | MIT | 非 Apollo 服务端的默认值 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: repo`） | 交叉验证 Apollo 之外的实现：默认开启错误屏蔽（未知错误一律 `Unexpected error.`）、`NODE_ENV=development` 才把 `originalError` 放进 extensions、只有 `GraphQLError` 的 message 会透出。npm `graphql-yoga@latest == 5.22.0` |
| 20 | hayes/pothos（pothos-graphql.dev 文档） | <https://github.com/hayes/pothos> | 2615 | 2026-09-10 | ISC | code-first 构建器 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE（`kind: repo`） | 代表 code-first 一派（与 SDL-first 的取舍差异）；relay 插件生成 Connection。npm `@pothos/core@latest == 4.13.1` |
| 21 | apollographql/apollo-server（apollographql.com/docs/apollo-server） | <https://github.com/apollographql/apollo-server> | — | — | MIT（`@apollo/server@5.5.1`） | Apollo 特有默认值 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: docs`） | 逐条实查 API 参考页取得的默认值：`introspection` 默认 true（除 `NODE_ENV=production`）、`includeStacktraceInErrorResponses` 默认 true（除 production/test）、`hideSchemaDetailsFromClientErrors` 默认 **false**、`allowBatchedHttpRequests` 默认 false、`csrfPrevention` 默认开、`maxRecursiveSelections` 默认 false。这些是"Apollo 特有"的关键证据 |
| 22 | graphql/dataloader | <https://github.com/graphql/dataloader> | 13390 | 2026-09-07 | MIT | 批处理契约 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: repo`） | batch 函数必须返回与 `keys` 等长同序的数组这一硬契约，只有官方 README 说得准；#9 与 #10 的样例都违反了它 |
| 23 | facebook/relay · `relay.dev/graphql/connections.htm` | <https://relay.dev/graphql/connections.htm> | 18961 | 2026-09-09 | MIT | Cursor Connections 规范 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: docs`） | Connection 形状的**规范原文**所在处；graphql.org/learn/pagination 明确把它作为正式规范引用。用于把"Connection 不是 GraphQL 规范的一部分"这条讲清楚 |
| 24 | graphql-hive/graphql-inspector + graphql-hive/graphql-eslint | <https://github.com/graphql-hive/graphql-inspector> | 1767 / 831 | 2026-09-09 / 2026-09-09 | MIT / MIT | 验证门 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE（`kind: repo`，reference） | 提供两个 workflow 的具名验证门：`@graphql-inspector/cli@7.0.0`（`diff` 破坏性变更检查）、`@graphql-eslint/eslint-plugin@4.4.1`（schema 与操作 lint）。只用其 CLI 契约，不抄文档 |

## 深度审查

### #1/#2/#3/#4 apollographql/skills（MIT，111★，2026-07-29）

- **结构**：每个 skill 都是 `SKILL.md` + `references/*.md`，与本仓库结构同构，合入成本最低。`graphql-schema`
  的 5 个 reference 各 388–484 行，`apollo-federation` 的 3 个 reference 覆盖指令/模式/组合错误码。
- **frontmatter**：含 `compatibility`（本仓库白名单内，可保留语义但不照抄）与 **`allowed-tools: Bash(npm:*) …`**、
  `metadata.author: apollographql`、`metadata.version: "1.0.1"`。按标准 1.2，`allowed-tools` 虽在白名单里但其值是
  agent 绑定，`metadata.author` 必须改成 `HyperSkills`，合入时全部剥离/重写。
- **质量**：`graphql-schema/SKILL.md` 有大段"Ground Rules"用 `ALWAYS/NEVER/PREFER/USE` 开头的祈使清单，
  正是标准第 3 节"禁止满篇 ALL-CAPS MUST/NEVER"要重写的形态。内容层面偏"语法速查表"
  （nullability 四种组合表、interface/union 语法），教的是 API 而不是失败模式。
- **最致命的空缺**：`graphql-schema` 全篇（SKILL + 5 个 reference）**没有一处提到非空字段的错误传播**。
  它给出"能不为 null 就加 `!`"的规则，却不说这条规则的代价，而这正是真实项目里 `data: null` 全屏白屏的成因。
  本 skill 把这一条放进 Core rules 第一梯队。
- **与其他候选的重叠**：#9 与它在"域建模、Relay 分页、`userErrors`"上重叠 70%，但 #9 独有成本模型与
  DataLoader 生命周期；#10 与它在 SDL 样例上重叠，无独有事实。
- **Apollo 味的边界**：`graphql-schema` / `graphql-operations` 两个 skill 确实是实现无关的（自己写明
  `Any GraphQL implementation` / `Any GraphQL client`），可以放心作主干；`apollo-server` / `apollo-router` /
  `apollo-client` 三个是产品说明书，前者只取默认值层，后两者直接排除（见候选表 #5/#6）。

### #7 graphql.org/learn（MIT，官方，2026-09-10）

- 覆盖 `thinking-in-graphs`、`serving-over-http`、`authorization`、`pagination`、`schema-design`、
  `global-object-identification`、`caching`、`performance`、`security`、`robust-applications`、`federation`。
- 质量远超所有社区候选，且**每一页都直接回答社区候选含糊掉的问题**：
  - `schema-design#nullability`：解释了"每个字段默认可空"是**有意设计**，因为网络服务里数据库会挂、
    异步动作会失败、授权可以细到字段级；加了 `!` 就等于承诺"出错时改让父字段为 null"。
  - `security#demand-control`：trusted documents（= persisted documents，正在 graphql-over-http 规范化）、
    分页、深度限制、**列表嵌套要单独设更小的限制**、breadth/alias/batch 限制、按业务层限流、复杂度分析。
  - `security#introspection`：关闭 introspection 是"security through obscurity"，单靠它不够；
    还必须屏蔽 "did you mean" 提示，否则攻击者能靠错误信息反推整个 schema。
  - `authorization`：授权逻辑要下放到业务层单一真源，而不是写在 resolver 里；`@auth` 指令只是入口。
  - `performance#n1`：N+1 的定义与 DataLoader 批处理；`GET` + 持久化文档换 HTTP 缓存。
  - `robust-applications`：枚举新增值、union/interface 新增成员、不要 force-unwrap 可空字段——
    这一页是"schema 演进"话题在客户端侧的官方对应物，社区候选里没有任何一家提到。
- **许可实查**：文档源码仓 `graphql/graphql.github.io` 的 `license.spdx_id == MIT`，可 merged。

### #8 graphql/graphql-spec（NOASSERTION → 实读为非 SPDX 的 JDF IP 政策）

- `LICENSE.md` 是 "Appendix: Copyright and Licensing"，指向 <https://technical-charter.graphql.org>
  的工作组 IP 政策，只给版权声明 + 免责声明，**没有授予再分发/改写文本的 SPDX 许可**。
- 结论：`license: Proprietary`、`relation: reference`。用途仅限"确认语义、给出条款编号"，正文全部自行表述。
- 取证内容（`spec/Section 6 -- Execution.md`，v `main`@2026-09-10）：
  - `Errors and Non-Null Types`（第 596–606 行）：非空位置抛执行错误必须向父响应位置传播，
    要么在允许时解析为 null，要么继续往上传播；同时"尚未执行的兄弟位置可以被取消"。
  - `Handling Execution Errors`（第 898–941 行）：每个响应位置最多一条错误；
    `List` 包 `Non-Null` 时**一个元素为 null 会让整个列表位置为 null**；
    若从根到出错点每一层都是非空，则 `data` 为 null。
  - `@oneOf` 已通过 "RFC: OneOf Input Objects"（merged 2025-09-01）进入规范。

### #9 SkillMedev/skills（MIT，12★，2026-07-05）

- 133 行单文件，无 references。`description` 已经在做本仓库要求的否定边界
  （`Do NOT use for REST or RPC endpoint design - use api-design instead`），写法值得参考。
- 独有且经核实为真的规则：DataLoader **逐请求**实例化（共享会跨用户泄漏缓存）、
  `first` 硬上限 100 / 默认 20–25、复杂度成本模型（scalar 1 / object 2 / list = 子成本 × 页大小）、
  在**校验阶段**而非执行阶段拒绝、公开 API 按成本点数限流而不是按请求数。
- 两处错误：`Prefer non-null (!) by default`（冲突 #1）、
  `Errors mid-list: return partial results with the errors array rather than failing the whole response`
  （冲突 #2，与 spec 的列表传播规则直接矛盾）。正确性因此判 2 分。
- 另有对不存在的 skill 的交叉引用（`n-plus-one-hunter`、`database-schema`、`api-versioning-strategist`），
  合入时必须删除——本仓库只允许指向已存在或本波新建的 skill。

### #18/#19/#20/#21 四个服务端实现（用于把"通用 vs Apollo 特有"分开）

四家的默认值差异是本 skill 最有价值的一张表，且**没有任何候选 skill 写过**：

| 行为 | graphql-js 17.0.2（参考实现） | Yoga 5.22.0 | Apollo Server 5.5.1 | Pothos 4.13.1 |
|---|---|---|---|---|
| resolver 抛普通 `Error` 后客户端看到什么 | 原样 message（库不做屏蔽） | 一律 `Unexpected error.` | 原样 message + `extensions.code: INTERNAL_SERVER_ERROR` | 取决于底层 server |
| 堆栈是否进响应 | 否 | 仅 `NODE_ENV=development` 时进 `extensions.originalError` | `includeStacktraceInErrorResponses` 默认 **true**（除 `NODE_ENV` 为 production/test） | 同上 |
| introspection | 库不管 | 需自行加插件关闭 | 默认 true，`NODE_ENV=production` 时默认 false | 同上 |
| "did you mean" 提示 | `hideSuggestions` 执行选项 | 透传 | `hideSchemaDetailsFromClientErrors` 默认 **false**（官方文档自己建议生产打开） | 同上 |
| HTTP 批量请求 | 不涉及 | 需插件 | `allowBatchedHttpRequests` 默认 false | 同上 |
| schema 定义方式 | 手写 `GraphQLObjectType` 或 `buildSchema` | SDL（`createSchema`）或任意 executable schema | SDL 或 `schema` | code-first 构建器，类型从 TS 推导 |
| Connection 生成 | 无 | 无 | 无 | `@pothos/plugin-relay` |

- graphql-js 17 独有事实（源码取证）：操作级指令 `@experimental_disableErrorPropagation` 可以关掉
  null 冒泡（`execute.ts:848` 据此设 `errorPropagation`）。这是**非规范**能力，正文写成"知道它存在，
  但不要用它替代把字段改成可空"。
- Apollo Server 的 `csrfPrevention` 默认开启，会挡掉不带指定头的 `GET`——与 graphql.org
  "用 `GET` 换 HTTP 缓存"的建议有交互，正文必须提。

### #22/#23 DataLoader 与 Relay Connections 规范

- DataLoader 的硬契约：batch 函数收到 `keys: readonly K[]`，必须返回**与 keys 等长且同序**的
  `V | Error` 数组。#9 的示例用 `ids.map(id => rows.find(...))` 满足契约；#10、#11 与本 skill 夹具里
  `return rows` 的写法都不满足——这是真实项目里"DataLoader 装上了但返回错人数据"的成因。
- Relay Cursor Connections Specification 是 `edges`/`node`/`cursor`/`pageInfo` 形状的规范原文；
  graphql.org/learn/pagination 明确把它作为正式规范引用，并额外指出：可以在 connection 上直接暴露
  `nodes` 便利字段以省掉 edges 一层；`totalCount` 是可选的额外信息而非必备字段。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 输出字段是否默认加 `!` | apollographql/skills：`ALWAYS use non-null (!) for fields that cannot be null`、`Best Practice: Use [Type!]! for lists`；SkillMedev：`Prefer non-null (!) by default`；graphql.org：**每个字段默认可空是有意设计**，"important to keep in mind all the problems that could go wrong and if null is an appropriate value for a failed field. Typically it is" | 采官方立场：**默认可空，非空是需要论证的例外**。判据是"这个位置能不能独立失败"——能独立失败（跨服务、跨网络、字段级授权、可能被计算失败）就必须可空；不能独立失败且与父对象同生命周期（如 `id`）才加 `!` | 官方厂商（graphql.org/learn/schema-design#nullability）> 社区；且 spec §6 的传播规则给出机制层证据：加 `!` 的代价是把字段失败抬升成父对象为 null，全链非空则 `data: null` |
| 2 | 列表中间某个元素出错时的行为 | SkillMedev：`Errors mid-list: return partial results with the errors array rather than failing the whole response`；apollographql/skills：未提；spec：`If a List type wraps a Non-Null type, and one of the response position elements of that list resolves to null, then the entire list response position must resolve to null` | 采规范：`[T!]` 里**任一元素出错会让整个列表变 null**，想要"部分结果"必须把元素声明为可空（`[T]`）。SkillMedev 的说法只在 `[T]` 下成立，作为无条件规则是错的 | GraphQL spec `Section 6 -- Execution.md` §Handling Execution Errors（第 934–937 行） |
| 3 | 变更操作的错误怎么建模 | apollographql/skills `errors.md`：结果 **union**（`union CreateUserResult = CreateUserSuccess \| ValidationError \| …`）为主推；graphql.org/learn/error-handling：**payload + `userErrors: [UserError!]!`**；SkillMedev：payload + `userErrors` | 正文只给一种默认方案：**payload 类型带可空实体 + 非空 `userErrors` 列表**，逃生口是"当各分支返回的数据形状根本不同时改用结果 union"。理由是 payload 形状可加字段而不破坏客户端，union 加成员则要求客户端已写 `__typename` 兜底 | 官方文档（graphql.org/learn/error-handling 的表格把 business rule violation / validation failure 归 errors-as-data）> Apollo 的 skill；标准第 3 节"只给一个默认方案 + 一个逃生口" |
| 4 | 联邦是不是 GraphQL 的一部分 | apollographql/skills：以 Apollo Federation 2.x 的 `@link`/`@key`/`@shareable` 为事实标准叙述，不提规范状态；graphql.org/learn/federation：联邦是**架构模式**，Apollo 2019 年的实现"成为社区参照点"，GraphQL Foundation 的 Composite Schema Working Group 正在制定官方规范 | 联邦一节以 Apollo Federation 2 为具体写法（它是目前唯一有完整指令集与组合规则的实现），但**首句明确它是一种实现而非规范**，并指明标准化在 Composite Schemas WG 进行中。指令语义（`@key`/`@external`/`@requires`/`@provides`/`@override`/`@inaccessible`）按 Apollo 文档写，且注明 `@link` 的版本号是示例、必须查当前支持版本 | 官方基金会文档（graphql.org/learn/federation）定性质，官方厂商文档（apollographql/skills `apollo-federation`）定细节；「官方厂商 > 社区」不适用于"这是不是规范"这个定性问题 |
| 5 | 关闭 introspection 算不算安全措施 | apollographql/skills `security.md` 与多个社区候选：作为生产环境安全清单的一条；graphql.org/learn/security#introspection：是 "security through obscurity"，**单靠它不足以隐藏 schema**，攻击者可用错误提示反推 | 正文写：关闭 introspection 只是降低可发现性，真正的措施是 trusted documents + 授权；同时**必须**一并关闭 "did you mean" 建议（Apollo 的 `hideSchemaDetailsFromClientErrors` 默认为 false，需显式打开），否则关 introspection 等于没关 | graphql.org/learn/security；Apollo Server API 参考的默认值实查 |
| 6 | 分页默认方案 | apollographql/skills：cursor Connection「推荐用于大多数情况」，offset 列为可选；secondsky：`users(limit, offset)` 无上限；graphql.org/learn/pagination：cursor-based「is the most powerful of those designed」，且 offset/ID 都能用 cursor 表达 | 默认 Relay Connection + 不透明游标；逃生口是"UI 真的需要跳页时才用 offset，并注明它在并发写入下会漏/重"。同时把 `totalCount` 定为可空的额外字段 | 官方文档 > 社区；且 #9 的"`first` 硬上限"补上了 Apollo 素材里只在 resolver 注释里出现的上限规则 |
| 7 | 错误信息屏蔽是"通用事实"还是"实现差异" | 多个候选写成通用规则"never expose raw database errors"；实查发现 Yoga **默认**屏蔽，Apollo Server **默认不屏蔽**且默认把堆栈放进响应（除 production/test） | 正文把"未知错误必须屏蔽"作为通用规则，但**紧跟一句实现差异**：Yoga 默认已屏蔽、Apollo Server 需要 `formatError` 并注意 `includeStacktraceInErrorResponses` 的默认值。不写成"所有服务器都一样" | Yoga 官方文档 error-masking 页；Apollo Server API 参考页 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `apollo-skills-graphql` | apollographql/skills `skills/graphql-schema`、`skills/graphql-operations`、`skills/apollo-federation`、`skills/apollo-server` | merged | Schema 设计与操作编写的主题骨架（命名、类型选择、输入类型、片段、变量、codegen）；联邦指令、实体与组合错误的全部细节；Apollo Server 特有默认值那一层 |
| `graphql-org-learn` | graphql.org/learn（源码仓 graphql/graphql.github.io，MIT） | merged | 本 skill 的裁决基准：nullability 的设计意图、错误建模（top-level vs errors-as-data）、分页、授权下放业务层、demand control 全清单、introspection 的真实价值、客户端演进健壮性 |
| `graphql-js` | graphql/graphql-js | merged | 参考实现语义：`errorPropagation` 开关与 `@experimental_disableErrorPropagation`、`@oneOf` 已是 specified directive、`hideSuggestions` 执行选项、当前 GA 版本 17.0.2 |
| `graphql-yoga` | dotansimha/graphql-yoga | merged | 非 Apollo 服务端的默认行为（默认错误屏蔽、`GraphQLError` 才透出 message、dev 模式才带 `originalError`），用于把"Apollo 特有"和"通用"分开 |
| `pothos` | hayes/pothos | merged | code-first 一派的取舍与 relay 插件生成 Connection 的事实 |
| `apollo-server-docs` | apollographql.com/docs/apollo-server | merged | Apollo Server 5 的安全相关默认值（introspection / stacktrace / schema 提示 / 批量请求 / CSRF）逐条实查值 |
| `dataloader` | graphql/dataloader | merged | batch 函数"等长同序"硬契约与逐请求实例化 |
| `relay-connections` | relay.dev/graphql/connections.htm（facebook/relay，MIT） | merged | Cursor Connections 规范的字段形状与语义，以及"它不是 GraphQL 规范"这一定性 |
| `skillmedev-graphql-schema` | SkillMedev/skills `skills/graphql-schema` | merged | 分页硬上限、复杂度成本模型、校验阶段拒绝、按成本点数限流、DataLoader 逐请求 |
| `wshobson-graphql` | wshobson/agents `plugins/backend-development/skills/api-design-principles/references/graphql-schema-design.md` | merged | 模块化 SDL 组织（`extend type Query`）与订阅、主题覆盖面交叉校验 |
| `graphql-spec` | graphql/graphql-spec | reference | 执行错误与非空传播的规范语义、`@oneOf` 的规范状态。许可为 JDF IP 政策（非 SPDX），一字未抄 |
| `graphql-hive-tooling` | graphql-hive/graphql-inspector、graphql-hive/graphql-eslint | reference | 两个 workflow 的具名验证门命令（`graphql-inspector diff`、`graphql-eslint`），只用 CLI 契约 |

被明确拒绝且不再重复评估的：apollographql/skills 的 `apollo-router` / `apollo-client`（范围外，见 Contract）、
LambdaTest `api-skill`（无 GraphQL 内容）、sickn33、Mindrally、TheBushidoCollective、rohitg00、
github/awesome-copilot（无相关内容）。

## 基线缺口

无 skill（`uv run tools/run_evals.py graphql --baseline`）时，各场景未达成的 `expected_behavior`：

基线用 Claude Opus 5 · medium 跑（`/tmp/hs-evals/graphql/anthropic-claude-opus-5-medium/baseline/`）。
这个模型对 GraphQL 的底子很好：场景 1（nullability 与错误传播）**6 条全部达成**，
场景 2、3、4 也各自达成大部分。区分度落在下面这 5 条上。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 nullability 与错误传播 | 无 | 基线自行推出了 null 冒泡全链路、`[Post!]!` 的列表语义、根字段要可空、以及「`!` 不是类型整洁度而是故障传播半径」这层反驳。此场景无缺口 |
| 2 分页 | `totalCount` 仍写成 `totalCount: Int!` 挂在每一页上 | 基线确实把它描述成「独立的索引计数查询、允许缓存」，但仍在两个 connection 上声明为非空必备字段，正是 expected_behavior 明确排除的写法 |
| 2 分页 | 没有说明 Connection 形状来自 Relay Cursor Connections 规范而非 GraphQL 规范 | 全文未出现 Relay。结果是把一个「字段名必须逐字匹配否则客户端工具失效」的约定讲成了自由设计，还自造了 `CollectionProductConnection`/`curationRevision` 等偏离规范的字段 |
| 3 N+1 | 没有 demand control：深度、嵌套列表深度、breadth/alias、复杂度预算，以及 `Post.author.posts` 的环状选择集 | 基线把分页列为「遗留」，但完全没提批处理无法给环状查询设界这件事，也没提任何在校验阶段拒绝的限制 |
| 4 演进 | 没有指出「新增枚举值在输入位置是破坏性变更」，也没有给客户端侧的健壮性要求（枚举 default 分支、抽象类型上的 `__typename` 兜底） | 基线在输入侧直接「两个名字都接受」，未说明这对上游同侪是契约变更；也完全没提客户端要怎么写才能承受加性演进 |
| 4 演进 | 整个下线路径锚定在「v2 schema」上，并把按 URL/header 路由到冻结 v1 作为兜底方案 | expected_behavior 要求不把端点版本化当主策略。基线的 P4「删除弃用字段只发生在 v2 schema」实际上把版本化当成了删除的前提 |

## 评测结果

两次运行都用 `tools/run_evals.py` 的默认模型与思考档（`anthropic/claude-opus-5`、`medium`），
未传 `--model` / `--thinking`。产物：`/tmp/hs-evals/graphql/anthropic-claude-opus-5-medium/{baseline,skill}/<i>/`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 nullability 与错误传播 | claude-opus-5:medium | 无（baseline） | false | 6 / 6 | 基线已能独立推出传播链、`[Post!]!` 的列表语义、根字段可空、以及对「非空让生成类型更干净」的反驳。此场景无区分度 |
| 1 nullability 与错误传播 | claude-opus-5:medium | 有 | true | 6 / 6 | 维持全达成，并按 skill 的 Output format 输出了 `path:line - finding` 分组与 Verdict/Gate。额外把 `Image` 内部字段、`recommendations`、`billingSummary` 一并纳入审计，并给出「若 url 由本地拼装可保留非空」的条件判断 |
| 2 分页 | claude-opus-5:medium | 无（baseline） | false | 5 / 7 | 未达成：`totalCount: Int!` 仍非空挂在每一页；全文未提 Relay 规范。另自造了 `CollectionProductConnection`、`curationRevision`、`CURSOR_ARGUMENT_MISMATCH` 等偏离 Connection 约定的形状 |
| 2 分页 | claude-opus-5:medium | 有 | true | 7 / 7 | **两条缺口都被填补**：`totalCount: Int` 改为可空且默认不计算并写明「无法从当前页推导、是每页一次的额外查询」；`hasPreviousPage` 的近似处理明确援引 Relay 作为裁决依据（「Relay 允许此近似」），并按 skill 规则不声明未实现的 `last`/`before`。额外补上 `nodes` 便利字段、连接相乘的需求控制、以及按请求构造的 DataLoader |
| 3 N+1 与 DataLoader | claude-opus-5:medium | 无（baseline） | false | 6 / 7 | 未达成：没有 demand control。只把分页列为「遗留建议」，未提批处理无法给环状选择集设界，也未提任何在校验阶段拒绝的深度/广度/复杂度限制 |
| 3 N+1 与 DataLoader | claude-opus-5:medium | 有 | true | 7 / 7 | **缺口被填补**：结尾明确「批处理只降低了每层成本，环状查询仍需要 validation 阶段的预算拦截」，并同时给 `Viewer.feed`、`Author.posts` 上了分页与每作者上限。另主动把 schema 侧的非空链问题一并指出（本场景夹具含 schema），沙盒实测 143→6 条 SQL、50→1 次 HTTP，并验证了「ranking 挂掉时降级到字段、data 未变 null」 |
| 4 schema 演进 | claude-opus-5:medium | 无（baseline） | false | 6 / 8 | 未达成：未指出新增枚举值在输入位置是破坏性变更，也没给客户端健壮性要求；整个下线路径锚定在「v2 schema」并把 URL/header 版本钉住列为兜底 |
| 4 schema 演进 | claude-opus-5:medium | 有 | true | 8 / 8 | **两条缺口都被填补**，且以最强形式：把「变更 3 的 `status` 过滤把 `OrderStatus` 放进输入位置」和「输入位置新增枚举值是破坏性变更」连起来，推出「变更 4 的加值步骤必须与变更 3 同版或更早发布」这个纯排序性结论——基线完全没看到。R2 明确要求客户端枚举 switch 加 default 分支。全程零端点版本化，删除条件设在实测 per-field 用量归零。`__typename` 兜底未提（本夹具无 union/interface，不构成扣分） |
| 5 REST/OpenAPI（负例） | claude-opus-5:medium | 无（baseline） | false | 3 / 3 | 基线本就没有 skill 可读 |
| 5 REST/OpenAPI（负例） | claude-opus-5:medium | 有 | **false** | 3 / 3 | **负例通过**：未加载 `graphql` skill。答复是纯 HTTP 契约——RFC 9457 `application/problem+json`、201 + `Location`、422 对应坏优惠券、409 对应状态禁止转移、游标分页信封 `{data, page}` + RFC 8288 `Link`，写成 OpenAPI 3.1。全文没有出现 GraphQL schema、Connection/edges/pageInfo 或 `userErrors` |

结论：**通过**。基线共有 5 条 `expected_behavior` 未达成（场景 2 两条、场景 3 一条、场景 4 两条），
有 skill 时**全部 5 条均达成**，且场景 4 的枚举输入位置那条从「未提及」变成了推动整个发布排序的核心论证。
负例 `skill_read == false`，答复内容也未被 GraphQL 术语污染。
场景 1 无区分度（基线满分），保留它是因为它是本 skill 最核心的规则，需要确认有 skill 时不退化——确认未退化。

## 备注

### 「哪些是 GraphQL 通用事实、哪些是 Apollo 特有」——本 skill 的防说明书化措施

主干上游是 Apollo 官方，最大的风险是把本 skill 写成 Apollo 说明书。采取的措施与交叉验证如下。

**判定为 GraphQL 通用事实（写成无条件规则，来源为规范或 graphql.org）：**

- 字段默认可空及其设计意图、非空的错误传播语义、`[T!]` 一元素失败毁整表
  （spec `Section 6 -- Execution.md` §Errors and Non-Null Types / §Handling Execution Errors；
  graphql.org/learn/schema-design#nullability）。
- 请求错误与执行错误的区别、顶层 `errors` 与 errors-as-data 的分工
  （graphql.org/learn/error-handling 的分类表）。
- 授权下放业务逻辑层（graphql.org/learn/authorization）。
- demand control 全清单：trusted documents、分页、深度限制 + **列表嵌套单独设更小的限制**、
  breadth/alias/batch 限制、按业务层限流、复杂度分析（graphql.org/learn/security#demand-control）。
- 关闭 introspection 只是 obscurity、必须同时屏蔽 "did you mean" 提示（graphql.org/learn/security#introspection）。
- N+1 与批处理、`GET` + 持久化文档换 CDN 缓存、gzip（graphql.org/learn/performance）。
- 客户端演进健壮性三条：枚举 default 分支、`__typename` 兜底、不要 force-unwrap
  （graphql.org/learn/robust-applications）。
- 变更的破坏性分类（spec 的校验规则 + graphql.org/learn/schema-design#versioning）。

**判定为约定而非规范（正文明确标注出处）：**

- **Connection 形状来自 Relay Cursor Connections Specification，不是 GraphQL 规范**。
  `references/pagination.md` 开篇一节就是这句，并解释了「因此字段名必须逐字匹配」这个后果。
  依据：graphql.org/learn/pagination 末尾把 relay.dev/graphql/connections.htm 作为正式规范引用。
- **联邦是架构模式，Apollo Federation 是其一种实现**，标准化在 GraphQL Foundation 的
  Composite Schemas 工作组进行。`references/federation.md` 第一节就是这句，并要求
  「先确认网关组合的是哪个实现的哪个版本，再照着那个版本的指令表写，包括不要照抄本文的 `@link` 版本」。
  依据：graphql.org/learn/federation。
- 持久化文档（persisted documents）的线上格式仍在 graphql-over-http 规范化中，因此实现相关。

**判定为实现特有（正文一律在同一句里点名产品）：**

- 错误屏蔽：Yoga 默认屏蔽为 `Unexpected error.`、只有 `NODE_ENV=development` 才把 `originalError`
  放进 extensions、要透出消息必须抛 `GraphQLError`；Apollo Server 默认不屏蔽且
  `includeStacktraceInErrorResponses` 默认 true（除 production/test）。
- Apollo Server 的 `introspection`（production 默认关）、`hideSchemaDetailsFromClientErrors`（默认 **false**）、
  `allowBatchedHttpRequests`（默认 false）、`csrfPrevention`（默认开，与 `GET` 缓存有交互）、
  `maxRecursiveSelections`（默认 false）、`maxCoercionErrors`（50）、`documentStore`（约 30 MiB LRU）。
- graphql-js 17 的 `@experimental_disableErrorPropagation`（正文明确写成「知道它存在，但不要用它
  替代把字段改成可空」）、`hideSuggestions` 执行选项、`@defer`/`@stream` 早于规范存在。
- Pothos 的字段默认非空（与 SDL 相反）、`@pothos/plugin-relay` 生成 Connection、
  code-first 需要把生成的 SDL 提交才能让 diff 门生效。
- `references/servers.md` 的「Defaults that differ」表把这四家逐行并列，并在开头写明
  「所有 JS 服务器都跑 graphql-js，所以类型系统、校验、执行顺序、强制转换与错误传播四家一致；
  不同的是外面那一层」——这是把两类事实分开的总原则。

**交叉验证做了哪几轮（Apollo 之外的官方来源）：**

1. graphql.org/learn 的 `schema-design`、`error-handling`、`pagination`、`security`、`performance`、
   `authorization`、`federation`、`robust-applications` 八页逐页实读，作为裁决基准（冲突 #1、#3、#4、#5、#6）。
2. GraphQL spec `Section 6 -- Execution.md` 实读，取错误传播与列表传播的条款（冲突 #2）。
3. graphql-js `v17.0.2` **源码**实读：`src/execution/execute.ts:848` 的 `errorPropagation`、
   `src/type/directives.ts:456`（`@oneOf` 已在 `specifiedDirectives`）与 `:471`
   （`experimental_disableErrorPropagation`）。npm `graphql@latest == 17.0.2`。
4. Yoga 官方文档 error-masking 页实读，确认「错误屏蔽是实现默认值而非 GraphQL 规则」（冲突 #7）。
5. Apollo Server 5 API 参考页逐项实读，取上面那批默认值——这批值同时也是「Apollo 特有」的证据。
6. Pothos 与 DataLoader 官方仓库确认 code-first 取舍与 batch 契约。
7. 版本事实全部用 `gh api releases` 或 npm dist-tags 核实：`graphql@17.0.2`、`graphql-yoga@5.22.0`、
   `@apollo/server@5.5.1`、`@pothos/core@4.13.1`、`dataloader@2.2.3`、`@graphql-inspector/cli@7.0.0`、
   `@graphql-eslint/eslint-plugin@4.4.1`，未凭记忆。

**结果自查**：`skills/graphql/SKILL.md` 的 25 条 Core rules 里，只有第 13 条（错误屏蔽）和第 24 条
（联邦）点名了具体产品，且两条都是在说「这件事按实现而定」。Apollo Server 与 Yoga 的细节全部下沉到
`references/servers.md` 与 `references/errors.md` 的对照表里，`references/federation.md` 之外没有一处
把 Apollo 的做法当成 GraphQL 的做法。

### 许可注意

- `graphql/graphql-spec` 的 GitHub 许可是 NOASSERTION，实读 `LICENSE.md` 后确认是 Joint Development
  Foundation / GraphQL Series 的工作组 IP 政策（版权声明 + 免责声明），**不是 SPDX 开源许可**。
  按规则表「NOASSERTION → 实读后若非开源则 reference」处理：`license: Proprietary`、
  `relation: reference`，正文一字未抄，全部用自己的话重述语义。
- `kind: docs` 的两个上游都实查了真实许可，因此都是 merged：graphql.org 的站点源码仓
  `graphql/graphql.github.io`（默认分支 `source`）API 许可为 MIT；relay.dev 的 Connections 规范由
  `facebook/relay`（MIT）发布。
- `hayes/pothos` 是 **ISC**（不是 MIT），已如实填写。
- Apollo Server 的默认值是从 apollographql.com 的 API 参考页读的，但该包本身是 MIT，
  SOURCES 以 `kind: repo` 指向 `apollographql/apollo-server`，`notes` 写明了取值页面与「只取事实值、
  未复制文档文字」。

### 种子更正记录（供后续批次不要重复踩）

- **LambdaTest/agent-skills `api-skill` 里没有 GraphQL 测试那一节**。计划表把它列为 GraphQL 测试来源，
  实读后 `api-designer/SKILL.md` 全文 grep `graphql` 零命中，整个 `api-skill/` 是 REST + LambdaTest
  平台导向。已在候选表 #12 标 REJECT。GraphQL 测试内容改从 Yoga / Apollo Server 官方文档取证。
- **`github/awesome-copilot` 没有任何 GraphQL 主题内容**（`skills/` 与 `instructions/` 都查过），
  候选表 #16 留行说明。
- `apollographql/skills` 的 `apollo-router` 与 `apollo-client` 质量很高但属范围外
  （前者是产品配置手册，后者按 Contract 归 `react`），候选表 #5/#6 留行。

### 未来同步时要盯的上游

- `graphql/graphql-spec`：Composite Schemas 规范一旦发布，`references/federation.md` 的定性段落要改写。
- `graphql/graphql-over-http`：persisted documents 标准化后，`references/operations.md` 的
  「线上格式仍实现相关」一句要更新。
- `graphql-js`：`@experimental_disableErrorPropagation` 若毕业或移除、增量投递（`@defer`/`@stream`）
  若进规范，`references/schema-design.md` 与 `references/operations.md` 各有一段要改。
- `apollographql/apollo-server`：`references/servers.md` 的默认值表逐行依赖它，任何默认值变更都要同步。

