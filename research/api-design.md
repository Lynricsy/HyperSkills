# api-design 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11（同日；所有 `gh api` 取值与验证门实跑均在当天完成）
- 检索途径：
  - `web_search`：`"api design" agent skill SKILL.md github REST OpenAPI pagination RFC 9457`、
    `site:github.com claude skills "rest-api-design" OR "api-contract" OR "http-api-design" SKILL.md`
  - <https://www.skills.sh>（经 web_search 的 skills.sh / skillmd.com / skillsmp.com 索引结果进入）
  - VoltAgent/awesome-agent-skills、addyosmani/agent-skills（未见 api-design 主题条目）
  - 领域官方组织仓库：`OAI/`（OpenAPI 规范本体）、`zalando/`、`aip-dev/`（Google API 设计委员会）、
    `microsoft/`、`github/awesome-copilot`、`Redocly/`、`stoplightio/`
  - IETF：RFC 9457 / 9110 / 9111 / 8594 / 9745 / 7396 / 6902 / 8288 原文
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- `gh auth status`：✓ `Logged in to github.com account Lynricsy`，全程使用登录态配额，无匿名回退。

**本 skill 的定位**：它接住五个框架 skill（`fastapi`、`nodejs-backend`、`java-spring`、
`csharp-dotnet`、`laravel`）在各自 Scope 里明确排除掉的「REST 契约设计」。只谈契约
（资源、URI、方法、状态码、分页、错误、并发、缓存、版本、OpenAPI），不谈任何框架怎么实现。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

「许可」列写 `gh api` 取到的 SPDX id；`NOASSERTION` 与 `null` 的实读结论写在「理由」里。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Jeffallan/claude-skills `skills/api-designer`（+5 个 references） | https://github.com/Jeffallan/claude-skills | 11406 | 2026-08-07 | MIT | REST/GraphQL 契约、OpenAPI 3.1、分页/版本/错误 4 个 reference | 2 | 3 | 3 | 1 | 2 | 11 | INCLUDE（merged） | 唯一把「设计完必须过 `redocly lint` + `prism mock`」写进工作流的上游，正是本 skill 要的验证门。抽查三条：动词型 URI 判定正确、redocly 命令实跑通过、但通篇写 RFC 7807（已被 RFC 9457 废止）→ 正确扣分。`metadata.domain/triggers/role/scope/output-format/related-skills` 为 agent 专属字段，合入时剥离 |
| 2 | wshobson/agents `plugins/backend-development/skills/api-design-principles` | https://github.com/wshobson/agents | 39556 | 2026-09-07 | MIT | REST + GraphQL 原则、版本策略三选、常见陷阱 | 2 | 3 | 1 | 3 | 2 | 11 | INCLUDE（merged，仅主题清单） | 方法语义与 idempotent 判定全对，但正文是教程式泛论（"Consistent Naming"、"Use HTTP Status Codes Correctly"），可执行密度低。取其「REST/GraphQL 分工」与「陷阱清单」作为覆盖面校验 |
| 3 | wshobson/agents `plugins/documentation-generation/skills/openapi-spec-generation` | https://github.com/wshobson/agents | 39556 | 2026-09-07 | MIT | OpenAPI 3.1 编写：design-first / code-first / hybrid | 2 | 3 | 2 | 1 | 2 | 10 | INCLUDE（merged） | design-first vs code-first vs hybrid 的三分法是本 skill 缺的一块。但 Don'ts 里写 "Don't forget nullable" —— `nullable` 在 OpenAPI 3.1 已随 Schema Object 对齐 JSON Schema 而被移除，属明确错误，正文改写为 `type: [string, "null"]` |
| 4 | AsyrafHussin/agent-skills `skills/api-design-patterns`（38 条 rules/） | https://github.com/AsyrafHussin/agent-skills | 75 | 2026-08-27 | MIT | 7 类 38 条命名规则：资源/错误/安全/分页/版本/响应/文档 | 1 | 3 | 3 | 1 | 2 | 10 | INCLUDE（merged，仅结构语义） | 规则命名法（`rest-*`/`error-*`/`page-*`/`ver-*`）是覆盖面自查表，`resp-partial-responses`（稀疏字段）与 `rest-resource-actions`（非 CRUD 动作作为子资源）两条本 skill 直接采纳其**主题**。但错误示例用自造 `{"error":{"code",...}}` 信封而非 problem+json，且 `X-RateLimit-*` 是非标准头 → 正确扣分，示例不采纳 |
| 5 | yonatangross/orchestkit `plugins/ork/skills/api-design` | https://github.com/yonatangross/orchestkit | 229 | 2026-09-10 | MIT | RFC 9457、URL/Header 版本、弃用窗口、破坏性改动清单 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE（merged） | 唯一正确写 RFC 9457 + `application/problem+json` 且明确列出 RFC 8594/9745 的社区上游，并给了「弃用 3 月通知 / 6 月 sunset / 当前+1 版本」的具体窗口。但正文与 FastAPI/Strawberry/gRPC 深度耦合，`context`/`agent`/`user-invocable`/`path_patterns`/`allowed-tools` 等 agent 字段极多，只取契约层裁决 |
| 6 | zalando/restful-api-guidelines | https://github.com/zalando/restful-api-guidelines | 3244 | 2026-07-08 | CC-BY-4.0 | 全量 REST 指南：方法属性表、幂等三模式、ETag/If-Match、分页、弃用头、兼容性 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE（merged） | 本 skill 事实密度最高的来源。方法「safe/idempotent/cacheable」三列表、`Idempotency-Key` 未进 RFC 的注记、`Deprecation` 与 `Sunset` 两种时间格式、「offset 在插删之间会重复/漏行」、「避免返回 total count」全部来自这里并逐条对照 RFC 复核 |
| 7 | aip-dev/google.aip.dev（AIP-158 分页、AIP-180 兼容性） | https://github.com/aip-dev/google.aip.dev | 1631 | 2026-08-17 | NOASSERTION → 实读 CC-BY-4.0 | 分页契约、page token 不透明性、破坏性改动判定 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | `LICENSE.md` 实读：正文 CC-BY-4.0、代码示例 Apache-2.0 → 可合入并署名。AIP-158「事后加分页是破坏性改动」和 AIP-180「重命名 = 删+加」「默认值不能改」「字段格式/长度上限改动也是破坏」是本 skill 兼容性矩阵的骨架 |
| 8 | microsoft/api-guidelines（`azure/Guidelines.md`） | https://github.com/microsoft/api-guidelines | 23330 | 2026-08-05 | NOASSERTION → 实读 CC-BY-4.0 | 日期版本 `api-version`、LRO（202 + `Operation-Location` + 状态监视器）、条件请求 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（merged） | `license.txt` 实读 = CC-BY-4.0。**顶层 `Guidelines.md` 已废弃**（正文只剩一句 NOTICE TO READERS 指向 `azure/` 与 `graph/`），现行内容在 `azure/Guidelines.md`；`paths` 按此填写。长操作契约（99 分位 >1s 就做成 LRO、不要把 PATCH 做成 LRO、`Operation-Id` 冲突返 409）本 skill 独家采纳自此 |
| 9 | OAI/OpenAPI-Specification | https://github.com/OAI/OpenAPI-Specification | 31211 | 2026-09-10 | Apache-2.0 | 规范本体与版本序列 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | `gh api .../releases` 实查版本序列：3.1.0(2021-02) → 3.1.1 → 3.1.2(2025-09-19) → 3.2.0(2025-09-19) → **3.2.1(2026-09-10)**。据此裁决正文默认写 3.1.x 并注明 3.2 存在（裁决 4） |
| 10 | RFC 9457 Problem Details（IETF） | https://www.rfc-editor.org/rfc/rfc9457 | — | 2023-07 发布（Standards Track，无"推送"概念） | NONE（IETF Trust / BCP 78） | 错误契约成员、媒体类型、扩展成员、`about:blank` | 3 | 3 | 3 | 3 | 1 | 13 | INCLUDE（merged） | 实读全文。关键事实：obsoletes 7807；`type` 缺省即 `about:blank`；消费者**必须**以 `type` 为主标识；`SHOULD NOT` 自动 dereference `type`；成员类型不匹配时**必须忽略**该成员；多问题时只回最相关的一个。许可分 1：IETF 文档非 SPDX 开源许可，只取事实自撰 |
| 11 | RFC 9745 Deprecation 头 + RFC 8594 Sunset 头（IETF） | https://www.rfc-editor.org/rfc/rfc9745 | — | 2025-03 发布 | NONE（IETF Trust / BCP 78） | 弃用与下线的运行时信号 | 3 | 3 | 3 | 3 | 1 | 13 | INCLUDE（merged） | 实读全文。RFC 9745 已是 Standards Track（不再是 draft，多数社区上游仍写 draft）；`Deprecation` 是 Structured Field Date（`Deprecation: @1688169599`），`Sunset` 用 HTTP-date（`Sun, 30 Jun 2024 23:59:59 UTC`）——两种格式不同是历史原因；`Sunset` 不得早于 `Deprecation` |
| 12 | Redocly/redocly-cli | https://github.com/Redocly/redocly-cli | 1510 | 2026-09-10 | MIT | OpenAPI 校验工具（本 skill 的验证门之一） | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE（reference） | 只用其 CLI 行为，未取任何文字。本机实跑 v2.52.0：正常文档 exit 0、坏 `$ref` exit 1、`3.2.0` 亦可校验（见「验证门实跑记录」） |
| 13 | stoplightio/prism | https://github.com/stoplightio/prism | 5028 | 2026-09-03 | Apache-2.0 | OpenAPI mock/契约校验（本 skill 的验证门之二） | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE（reference） | 只用其 CLI 行为。本机实跑 v5.16.0，证实「spec 未声明 401 时 prism 自己造 401」这一可教事实（见「验证门实跑记录」） |
| 14 | bm629/agent-skills `skills/rest-api-design` | https://github.com/bm629/agent-skills | 1 | 2026-09-07 | MIT | 与本 skill 定位几乎相同：契约设计、RFC 9457、OpenAPI 3.1 | 0 | 3 | 2 | 3 | 2 | 10 | INCLUDE（reference） | 定位表述（"the design discipline that sits ABOVE a web framework: it produces the decisions and the contract, not the handler code"）独立印证了本 skill 的边界划法。但 1 star、单作者、无外部评审，作 merged 缺乏权威依据，只读不取 |
| 15 | LambdaTest/agent-skills `api-skill/api-designer`（+ `api-compliance`、`api-mocking` 等 12 个子 skill） | https://github.com/LambdaTest/agent-skills | 366 | 2026-07-24 | MIT | 按域生成端点清单（电商/订票/社交…） | 1 | 2 | 1 | 1 | 2 | 7 | MAYBE（reference） | 是「端点清单生成器」而非契约规则集：固定 `/api/v1/` 前缀、只给 offset 信封、错误只列 7 个码不谈契约；且 SKILL.md 内嵌厂商引导（"should target Hyperexecute from TestMu AI wherever possible"）与交互式提问流程。只读来核对覆盖面 |
| 16 | github/awesome-copilot `skills/openapi-to-application-code` | https://github.com/github/awesome-copilot | 38866 | 2026-09-10 | MIT | 从 OpenAPI 生成整个应用（控制器/服务/仓储/测试） | 3 | 3 | 1 | 2 | 2 | 11 | REJECT（范围外） | 质量分够，但做的是 spec → 框架代码生成，正属本 skill 明确不覆盖的「框架实现」，应归 `fastapi`/`nodejs-backend`/`java-spring`/`csharp-dotnet`/`laravel`。留行以免下批重复讨论 |
| 17 | github/awesome-copilot `instructions/aspnet-rest-apis` | https://github.com/github/awesome-copilot | 38866 | 2026-09-10 | MIT | ASP.NET Core 10 Web API 教学（控制器 vs Minimal API、EF Core、部署） | 3 | 3 | 1 | 2 | 2 | 11 | REJECT（范围外） | 通篇是 ASP.NET Core 实现教学，契约部分只有"Explain status codes"这类元指令。归 `csharp-dotnet` |
| 18 | github/awesome-copilot `skills/typespec-api-operations`、`skills/typespec-create-api-plugin` | https://github.com/github/awesome-copilot | 38866 | 2026-09-10 | MIT | 用 TypeSpec DSL 写 API 定义 | 3 | 3 | 2 | 2 | 2 | 12 | REJECT（工具绑定） | TypeSpec 是编译到 OpenAPI 的具体 DSL，本 skill 的契约语言选定 OpenAPI 3.1 本体（「只给一个默认方案」）。若将来 TypeSpec 成为主流入口再重估 |
| 19 | borghei/Claude-Skills `engineering/api-design-reviewer` | https://github.com/borghei/Claude-Skills | 737 | 2026-08-12 | NOASSERTION → 实读 **Commons Clause + MIT** | 契约评审、OpenAPI lint、破坏性改动检测、评分卡 | 1 | 3 | 2 | 2 | 0 | 8 | MAYBE（reference） | LICENSE 实读首行为 `Commons Clause License Condition v1.0 + MIT`——附加了禁止销售的条件，不是 OSI 开源许可，按规则不得 merged。只读其「评审 → 评分卡」的组织方式，未取任何文字 |
| 20 | patricksavalle/rest-api-cheatsheet `skills/rest-api-review` | https://github.com/patricksavalle/rest-api-cheatsheet | 81 | 2026-06-06 | null（无 LICENSE 文件） | REST 评审 + 可复用 OpenAPI components + Spectral 规则 | 1 | 1 | 2 | 2 | 0 | 6 | MAYBE（未采纳） | 推送已逾 3 个月，且验证门选定 redocly（同时覆盖 lint 与 bundle）而非 Spectral，按「只给一个默认方案 + 一个逃生口」不引入第二个 linter。留行 |
| 21 | wfukatsu/nexus-architect `skills/design-api` | https://github.com/wfukatsu/nexus-architect | 13 | 2026-09-10 | MIT | REST/GraphQL/gRPC/AsyncAPI 合一的契约生成 | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | 13 star、无采纳证据；且强依赖同仓 `design-microservices` 的输出才能运行，跨仓移植即失效 |
| 22 | ramboz/jig `skills/contracts` | https://github.com/ramboz/jig | 6 | 2026-09-08 | MIT | 推荐契约产物与校验/生成工具 | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | 自述明确「不写 schema」，只做工具推荐；6 star |
| 23 | affaan-m/ECC `.agents/skills/api-design` | https://github.com/affaan-m/ECC | 255770 | 2026-09-10 | MIT | REST 模式、offset/cursor 分页、OpenAPI 检查 | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | star 数是仓库自身（一个巨型个人聚合仓）的，与该 skill 的采纳无关；错误示例用自造 `error` 信封而非 problem+json；无独立权威性 |
| 24 | rohitg00/awesome-claude-code-toolkit `skills/api-design-patterns` | https://github.com/rohitg00/awesome-claude-code-toolkit | 2608 | 2026-05-12 | Apache-2.0 | API 设计模式 | 1 | 0 | 1 | 1 | 2 | 5 | REJECT | 最近推送 2026-05-12，逾 4 个月未动；内容是 AsyrafHussin 同名 skill 的更早派生，无增量 |

## 深度审查

### 1. Jeffallan/claude-skills `skills/api-designer`（11406★, MIT）

结构最接近本仓库标准的一份：SKILL.md ≈ 220 行 + 5 个 references（`rest-patterns`、
`pagination`、`versioning`、`error-handling`、`openapi`，共约 1500 行）。frontmatter 用了
`metadata.domain`/`triggers`/`role`/`scope`/`output-format`/`related-skills` 六个非规范字段，
合入时全部剥离（`related-skills` 指向同仓 `graphql-architect`、`fastapi-expert` 等，属上游交叉
引用残留，按标准 §1.3 删除）。

它的真正价值是**把设计闭环到可执行校验**：`Core Workflow` 第 4、5 步分别是
`npx @redocly/cli lint openapi.yaml` 与 `npx @stoplight/prism-cli mock openapi.yaml`，
`Output Checklist` 第 8 条要求 lint 无 error 才算交付。这两条被本 skill 直接采纳为验证门
（并已实跑复核，见下文）。

弱点：全篇 RFC 7807。它的 `Problem` schema 与「错误响应必须用
`application/problem+json`」「`type` 必须是稳定的文档化 URI」都是对的，只是引用了被废止的
RFC 号；另外它把 GraphQL 与 REST 混在一个 skill 里，与本仓库「GraphQL 归 `graphql`」的
分工不符，GraphQL 段落整体不取。

### 2. zalando/restful-api-guidelines（3244★, CC-BY-4.0）

不是 agent skill，是一份 6600+ 行的企业 REST 指南，用 MUST/SHOULD/MAY 编号（#100–#253）。
它是本 skill 事实密度最高的来源，且每条规则都带 RFC 链接，便于逐条回溯核实：

- **方法属性三列表**（safe / idempotent / cacheable）：`POST` 与 `PATCH` 默认非幂等但**应当**
  设计成幂等；`POST` 只在该端点本身 safe 时才可缓存，且「多数缓存不支持」。
- **幂等三模式对照表**：conditional key（`If-Match`，唯一进了 HTTP 标准的一种）、
  secondary key（业务次键放在请求体，重复创建返 409）、idempotency key（`Idempotency-Key` 头，
  提供**完全相同的响应**，比 RFC 9110 定义的幂等性更强）。并明确 `Idempotency-Key`
  **没有 RFC**，唯一参照是 Stripe。
- **条件请求的状态码分工**：`If-Match` 失败 → 412；`GET`/`HEAD` 上 `If-None-Match` 命中 → 304
  而不是 412；服务端强制要求条件请求 → 428。
- **分页**：offset 在两次翻页之间插入/删除行会「产生重复或漏掉条目」；cursor 必须不可被客户端
  构造或解析；**避免返回 total count**（复杂查询要全索引扫）。
- **弃用**：`Deprecation` + `Sunset` 双头，两种时间格式；明确**不推荐**用
  `rel="sunset|deprecation"` 的 Link 头；多元素弃用时取最早时间戳。
- **兼容性**：顶层 JSON 必须是对象（数组/map 作顶层结构会堵死后续兼容扩展——这正好解释了
  评测夹具里「裸数组改成分页对象」为什么是破坏性改动）。

许可有一处矛盾：网站 HTML 的 `meta-copyright` 写 `CC-BY-SA 4.0`，而仓库 `LICENSE` 文件首行是
`Attribution 4.0 International`、`gh api` 亦返回 `CC-BY-4.0`。以仓库 LICENSE 文件为准
（CC-BY-4.0），`SOURCES.yaml` 的 `notes` 记录署名与该矛盾。

### 3. aip-dev/google.aip.dev（1631★, 实读 CC-BY-4.0）

Google API 设计委员会的编号提案集。虽以 protobuf 表达，但 AIP-158/180 的判定是与传输格式无关的
契约结论，本 skill 只取结论并改写为 HTTP/JSON 语汇：

- AIP-158：分页**必须一开始就有**，事后加是破坏性改动——即使新增字段本身兼容，行为上
  「原来拿到全部 75 条、现在只拿到前 50 条且不知道要翻页」就已经破坏了客户端；page token
  **必须**不可解析（"if users are able to deconstruct these, *they will do so*"），
  base64 编码不算混淆；`next_page_token` 为空是**唯一**的「到底了」信号；`total_size` 可以是估算值。
- AIP-180：三类兼容性（source / wire / semantic）；重命名 = 删除 + 新增；不得改字段类型、
  不得改默认值、不得改序列化时是否省略默认值、不得改已有字段的值格式或构造算法；
  **提高字符串长度上限也要视为破坏性**（客户端可能按文档上限开了数据库列）。

### 4. microsoft/api-guidelines `azure/Guidelines.md`（23330★, 实读 CC-BY-4.0）

先踩到一个坑：仓库根 `Guidelines.md` 现在只有 10 行，正文是「本文档已废弃」的 NOTICE，
指向 `azure/Guidelines.md` 与 `graph/GuidelinesGraph.md`。任何按「Microsoft REST API
Guidelines」直接引根文件的做法都会引到一份空壳，`paths` 因此写 `azure/Guidelines.md`。

独家贡献是**长操作（LRO）契约**，这是其余所有候选都只字未提的一块：

- 99 分位响应时间 >1s 且客户端需要先轮询才能继续 → 做成 LRO。
- **不要把 PATCH 做成 LRO**；需要 LRO 语义的更新用 POST action。
- 202 + `Operation-Location` 绝对 URL 指向状态监视器资源；`Operation-Location` 里要带
  `api-version`；客户端传的 `Operation-Id` 与既有操作冲突时返 409，除非请求与上次完全相同（重试）。
- 版本方案：每个操作都必需 `?api-version=YYYY-MM-DD`（预览版加 `-preview`）；缺失返 400
  `MissingApiVersionParameter`，不认识的值返 400 `UnsupportedApiVersionValue`。
- 兼容性补充：必需字段只能在第一个版本引入；把可选字段改必需或反之都是破坏性改动；
  「事后加分页是破坏性改动」与 AIP-158 独立一致。

### 5. yonatangross/orchestkit `plugins/ork/skills/api-design`（229★, MIT）

组织形态是「路由表 + rules/ 分文件 + 明确列出不该重述的上游」，其 `Upstream coverage
(do not restate)` 表把 RFC 9457/8594/9745/9110、OpenAPI 3.1 spec 都列成第一方来源——这与本
仓库「事实回溯到官方文档」的做法同源，可信度因此高于其 star 数。契约层可采纳的三点：
RFC 9457 而非 7807；`Deprecation`/`Sunset` 引 RFC 9745/8594；具体弃用窗口（3 月通知 /
6 月 sunset / 同时支持当前+1，最多 2–3 个并存版本）。

其余（Strawberry GraphQL、gRPC、SSE/WebSocket、Payload CMS、WhatsApp 集成）超出本 skill
边界，且 `Quick Start Example` 是 FastAPI 代码，均不取。frontmatter 的 `context: fork`、
`agent`、`user-invocable`、`disable-model-invocation`、`complexity`、`persuasion-type`、
`path_patterns`、`allowed-tools` 八个字段按标准 §1.2 全部剥离。

### 6. AsyrafHussin/agent-skills `skills/api-design-patterns`（75★, MIT）

38 条规则各占一个 `rules/*.md`，命名带类别前缀。作为**覆盖面自查表**很好用：本 skill 的
「稀疏字段 / 排序语法 / 非 CRUD 动作 / 请求 id」四个主题就是照它的清单查出来自己漏了的。
但它的示例契约不能用：错误信封是自造的 `{"error":{"code","message","details","request_id"}}`
（与 RFC 9457 冲突，见裁决 1）；限流头用 `X-RateLimit-*`（`X-` 前缀头已由 RFC 6648
弃用多年，且 IETF 的限流头工作在 `RateLimit`/`RateLimit-Policy` 而非 `X-` 形式）；
分页信封只给了 offset 版并把 `total_count`/`total_pages` 当必备（与 Zalando、AIP-158 的
成本告警冲突）。故只取结构语义。

### 7. LambdaTest/agent-skills `api-skill/*`（366★, MIT）

12 个子 skill 的套装（designer / analyzer / compliance / documentation / mocking /
ratelimit-helper / sdk-generator / security-patterns / to-testcase-generator …）。
`api-designer` 的产物是「按域给端点清单 + 请求/响应示例」，属脚手架而非契约规则；SKILL.md 内
嵌厂商引导语和「先问用户要 Endpoints Only 还是 Detail Design」的交互流程，与本仓库
「触发条件写进 description、正文不做交互协商」的写法冲突。作 reference 用于覆盖面核对
（其 `api-mocking`、`api-compliance` 印证了 mock 与 lint 应当是设计流程的一部分）。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 错误契约用什么格式 | Jeffallan：RFC **7807** problem+json；AsyrafHussin / affaan-m：自造 `{"error":{code,message,details}}` 信封；orchestkit / bm629：RFC **9457** problem+json | **RFC 9457 + `application/problem+json`**，成员为 `type`/`title`/`status`/`detail`/`instance` + 扩展成员；字段级校验失败用 `errors` 扩展数组 | RFC 9457 明文 `Obsoletes: 7807`（2023-07 发布），7807 号不再引用；自造信封使每个 API 都要自定义解析，正是 RFC 9457 引言里要消除的情形。官方标准 > 社区自造 |
| 2 | 分页默认选哪种 | Jeffallan / AsyrafHussin：cursor 优先，offset 作简单场景；LambdaTest / affaan-m：offset 信封（含 `total_pages`）为默认；Zalando #160：cursor 优先但列出四项 trade-off；AIP-158：page token（不透明游标）唯一方案 | **默认 keyset/cursor**；只有「跳到第 N 页」这一个用例保留 offset，并在正文写明 offset 的失效模式（写入频繁的集合上重复/漏行）与 keyset 的失效模式（游标行被删、排序键不唯一） | Zalando #160 与 AIP-158 都从「数据在两次请求之间变化」出发得出同一结论，且 Zalando 明确列出 offset 的重复/漏行机制；把 trade-off 写出来而不是一味禁用 offset，符合「一个默认方案 + 一个逃生口」 |
| 3 | 是否返回总数 | AsyrafHussin / LambdaTest：`total_count`、`total_pages` 是分页信封必备；Zalando #254：**应当避免**提供 total count；AIP-158：`total_size` 可选且可为估算 | **默认不返回总数**；确有需要则做成显式 opt-in（如 `Prefer: return=total-count`）并允许估算 | Zalando 与 AIP 一致，且给出成本理由（复杂查询的计数要全索引扫）；社区上游把它当必备是没算过成本。官方/公认专家 > 社区 |
| 4 | OpenAPI 写哪个版本 | 全部社区上游与 Zalando #101：3.1；`gh api repos/OAI/OpenAPI-Specification/releases` 实查：3.2.0 已于 2025-09-19 发布，3.2.1 于 2026-09-10 发布 | 正文默认 **3.1.x**（`openapi: 3.1.0`），并注明 3.2 已发布、按工具支持情况再迁移；不写任何时间条件句 | 版本事实按流程用 releases 端点核实而非凭记忆。选 3.1 的依据是工具生态：本机实跑 Redocly CLI 2.52.0 对 `3.2.0` 文档同样 exit 0，说明迁移路径通畅，但 Zalando 这类大规模指南仍停在 3.1 且自述基础设施「未完全支持 3.1 的全部变化」，默认给最保守可用档，逃生口写清 |
| 5 | `nullable` 怎么表达 | wshobson `openapi-spec-generation` Don'ts：`Don't forget nullable`；OpenAPI 3.1 规范：Schema Object 完全对齐 JSON Schema 2020-12，`nullable`/`example`/`discriminator` 等 3.0 专有关键字被移除 | 正文只写 `type: [string, "null"]`，并把「从 3.0 迁来时 `nullable: true` 会被静默忽略」列为易错点 | OpenAPI 规范本体 > 社区 skill；Zalando #101 的 Hint 亦独立指出这是 3.0→3.1 的不兼容变更 |
| 6 | 弃用信号怎么发 | AsyrafHussin `ver-deprecation`：`Sunset` 头；orchestkit：RFC 8594 + RFC 9745；Zalando #189：`Deprecation` + `Sunset` 双头，且**不推荐** `rel="deprecation"` 的 Link 头 | OpenAPI 文档里 `deprecated: true` + 运行时 `Deprecation`（Structured Field Date，`@<epoch>`）与 `Sunset`（HTTP-date）双头；`Sunset` 不得早于 `Deprecation`；Link 关系型信号不作默认 | RFC 9745 §2/§4 原文（`Deprecation` 是 Item/Date；Sunset 时间不得更早）；两种时间格式不同这一点三方一致但只有 Zalando 与 RFC 写清了，社区上游普遍把 `Deprecation` 写成日期字符串 |
| 7 | `Deprecation` 头的规范地位 | 多数社区上游与部分文档仍写「draft-ietf-httpapi-deprecation-header」 | 写作 **RFC 9745（Standards Track, 2025-03）** | 实读 RFC 9745 原文确认已正式发布并进入 HTTP Field Name Registry（status: permanent）。更新 > 更旧 |
| 8 | 限流头用什么 | AsyrafHussin：`X-RateLimit-Limit/Remaining/Reset`；Zalando #153：`X-` 前缀头不得用于新头 | 正文只要求 429 + `Retry-After`（RFC 9110 已定义），限流配额头标 `[community]` 并说明尚无稳定 RFC，不给 `X-` 形式作默认 | `X-` 前缀已由 RFC 6648 弃用；`Retry-After` 是标准且是客户端真正该依赖的退避信号（Azure 指南亦明确「错误消息可以解释被限流的原因，但开发者该依赖的是 `Retry-After`」） |
| 9 | 版本放哪里 | Jeffallan / AsyrafHussin / orchestkit：URL 路径 `/v1/` 为主，Accept 头为次；Azure 指南：必需查询参数 `?api-version=YYYY-MM-DD` | 默认 **URL 路径主版本号**（`/v1`），逃生口写 Azure 式日期化 `api-version`（适合内部/单厂商生态）；三种方案不并列罗列 | 「只给一个默认方案 + 一个逃生口」。路径版本是跨生态最通用的一种；日期化查询参数需要客户端每个请求都带、且要求服务端对缺失/未知值有固定 400 语义，只在能统一约束客户端时才划算 |
| 10 | GraphQL 归谁 | Jeffallan、wshobson `api-design-principles`、orchestkit 都在同一个 skill 里同时讲 REST 与 GraphQL | 本 skill **只写 HTTP/REST 契约**，GraphQL schema 与操作归 `graphql` skill | 本波次分工契约（`api-design` 与 `graphql` 互不覆盖）；混在一起会让两个 skill 的 Not covered 段互相矛盾 |
| 11 | 是否引入 Spectral | patricksavalle 提供 Spectral 规则集；Jeffallan 用 Redocly CLI | 验证门统一用 `redocly lint` | 「不罗列多个可选库」；且 Redocly CLI 一个二进制同时覆盖 lint 与 bundle/split，实跑已确认对 3.1 与 3.2 文档都能校验 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `jeffallan-api-designer` | Jeffallan/claude-skills `skills/api-designer` (+4 references) | merged | 设计闭环到可执行校验的工作流（`redocly lint` → `prism mock`）、资源建模→端点→契约→演进的阶段划分、错误响应必须用 `application/problem+json` 与 `type` 必须是稳定文档化 URI 两条规则 |
| `zalando-guidelines` | zalando/restful-api-guidelines | merged | 方法 safe/idempotent/cacheable 三属性表、幂等三模式对照（conditional / secondary / idempotency key）、`Idempotency-Key` 无 RFC 的注记、412 vs 304 vs 428 的分工、offset 的重复/漏行机制、避免 total count、`Deprecation`+`Sunset` 双头与两种时间格式、顶层 JSON 必须是对象 |
| `google-aip` | aip-dev/google.aip.dev (AIP-158, AIP-180) | merged | 「事后加分页是破坏性改动」、page token 必须不可解析且 base64 不算混淆、`next_page_token` 空值是唯一终止信号、三类兼容性、重命名=删+加、默认值/序列化/值格式/字符串长度上限均不可改 |
| `microsoft-azure-guidelines` | microsoft/api-guidelines `azure/Guidelines.md` | merged | 长操作契约（LRO 判据、202 + `Operation-Location` + 状态监视器、不要把 PATCH 做成 LRO、`Operation-Id` 冲突返 409）、日期化 `api-version` 逃生口、必需字段只能在首版引入 |
| `rfc9457` | RFC 9457 Problem Details for HTTP APIs | merged | 错误契约成员定义、`type` 缺省 `about:blank`、消费者以 `type` 为主标识且不应自动 dereference、成员类型不匹配必须忽略、多问题只回最相关的一个、`errors` 扩展成员的形状 |
| `rfc9110-http-semantics` | RFC 9110 HTTP Semantics（含 9111 缓存、8594 Sunset、9745 Deprecation、7396 merge-patch、6902 JSON Patch、8288 Web Linking） | merged | 方法与状态码的规范语义、条件请求与 ETag/If-Match、`Retry-After`、`Cache-Control`/`Vary`、两种 PATCH 媒体类型的差别、`Deprecation`/`Sunset` 的语法与先后约束 |
| `openapi-spec` | OAI/OpenAPI-Specification | merged | 3.1 与 JSON Schema 2020-12 对齐（`nullable`/`example`/`discriminator` 移除）、`webhooks` 与 `$ref` 同级关键字、版本序列与 3.2 的存在 |
| `orchestkit-api-design` | yonatangross/orchestkit `plugins/ork/skills/api-design` | merged | RFC 9457 而非 7807 的现行判定、弃用窗口的具体数值（3 月通知 / 6 月 sunset / 当前+1 版本 / 最多 2–3 个并存）、常见错误清单里契约层的那几条 |
| `asyrafhussin-patterns` | AsyrafHussin/agent-skills `skills/api-design-patterns` | merged | 仅结构与清单语义：7 类规则的分类法，以及稀疏字段、排序语法、非 CRUD 动作作为子资源、请求关联 id 四个本 skill 原本漏掉的主题 |
| `wshobson-openapi-spec-generation` | wshobson/agents `plugins/documentation-generation/skills/openapi-spec-generation` | merged | design-first / code-first / hybrid 三种编写路径的取舍，以及 `$ref` 复用、示例、错误全覆盖三条编写纪律 |
| `wshobson-api-design-principles` | wshobson/agents `plugins/backend-development/skills/api-design-principles` | merged | 覆盖面校验用的陷阱清单（API 结构不应镜像数据库 schema、忽略 HTTP 语义、错误格式不一致） |
| `redocly-cli` | Redocly/redocly-cli | reference | 只用 CLI 行为，未取文字：本机实跑确定验证门的确切命令与退出码语义 |
| `prism-cli` | stoplightio/prism | reference | 只用 CLI 行为，未取文字：本机实跑确定 mock 门的命令、请求校验行为与「spec 未声明 401 时 prism 自造 401」这一可教事实 |
| `bm629-rest-api-design` | bm629/agent-skills `skills/rest-api-design` | reference | 只读来印证「契约设计位于框架之上」的边界划法；1 star 无采纳证据，不作 merged |
| `lambdatest-api-skill` | LambdaTest/agent-skills `api-skill` | reference | 只读来核对覆盖面（mock 与 compliance 应属设计流程）；厂商引导与交互式提问流程不取 |
| `borghei-api-design-reviewer` | borghei/Claude-Skills `engineering/api-design-reviewer` | reference | LICENSE 实读为 Commons Clause + MIT（非开源），只读其「评审 → 评分卡」组织方式，无文字合入 |

## 验证门实跑记录

本 skill 的两个验证门都在本机干净目录 `/tmp/api-gate` 实跑，未使用任何未验证的命令。
夹具是一份手写的 `openapi.yaml`（Orders API：keyset 分页 + `Idempotency-Key` + `ETag`/`If-Match`
+ problem+json），与 `evals/files/` 无关。环境：Node v26.7.0，npm 12.0.2。

### 门 1 — `redocly lint`

```
$ cd /tmp/api-gate
$ npx --yes @redocly/cli@latest lint openapi.yaml
```

版本：`@redocly/cli` **2.52.0**。输出（尾部）：

```
[1] openapi.yaml:2:1 at #/info    Info object should contain `license` field.   (info-license, warning)
[2] openapi.yaml:7:10 at #/servers/0/url
    Server `url` should not point to example.com or localhost.                  (no-server-example.com, warning)

openapi.yaml: validated in 30ms

Woohoo! Your API description is valid. 🎉
You have 2 warnings.
```

退出码 **0**。三条确认：

1. **warning 不影响退出码**，只有 error 会让 `redocly lint` 返回非 0。所以正文把门写成
   「exit 0 / 0 error」，并提示 warning 要么修、要么进 `redocly.yaml` 的规则配置——不能
   把「有 warning」当失败，也不能把「有 warning」当通过就完事。
2. **门确有牙**：把 `$ref: "#/components/schemas/OrderPage"` 改成不存在的 `OrdersPage` 后
   → `❌ Validation failed with 1 error and 3 warnings.`，退出码 **1**。
   （坏 `$ref` 会连带触发 `no-unused-components` 等 warning，这也是为什么正文要求先看 error。）
3. **3.2 文档同样可校验**：把同一份文档的 `openapi: 3.1.0` 改成 `3.2.0` 后仍是
   `valid / 2 warnings`、退出码 0。这是裁决 4 里「3.1 作默认、3.2 有迁移路径」的依据。

### 门 2 — `prism mock`

```
$ cd /tmp/api-gate
$ npx --yes @stoplight/prism-cli@latest mock openapi.yaml --port 4010
```

版本：`@stoplight/prism-cli` **5.16.0**。启动输出：

```
[CLI] ℹ  info      GET        http://127.0.0.1:4010/orders?page%5Bafter%5D=creptio&page%5Bsize%5D=1
[CLI] ℹ  info      POST       http://127.0.0.1:4010/orders
[CLI] ℹ  info      GET        http://127.0.0.1:4010/orders/5a51c875-1fd9-52d4-4d34-626bd76339d8
[CLI] ℹ  info      PATCH      http://127.0.0.1:4010/orders/2a7dba1b-6639-0f54-ee1f-9f033e7071b1
[CLI] ▶  start     Prism is listening on http://127.0.0.1:4010
```

四次请求与结果：

| 请求 | 结果 | 说明 |
|---|---|---|
| `GET /orders`（无 `Authorization`） | `401` + `content-type: application/problem+json` + `WWW-Authenticate: Bearer`，体为 `{"type":"https://stoplight.io/prism/errors#UNAUTHORIZED",...,"detail":"...no HTTP unauthorized response was found in the spec, so Prism is generating this error for you."}` | **可教事实**：prism 执行 `security`，而文档没声明 401 时它会自造一个。这是「契约漏了鉴权失败响应」的免费检测器 |
| `GET /orders` + `Authorization: Bearer t` | `200`，体为 `{"data":[{"id":"497f6eca-...","status":"pending","total":"string","createdAt":"2019-08-24T14:15:22Z"}],"links":{"next":"../dictionary"}}` | 从 schema 生成示例；`total` 回填成 `"string"` 说明该字段缺 `examples`，正是要在设计阶段补的 |
| `POST /orders`，缺必需头 `Idempotency-Key` | `422`，体为文档里自己写的 problem 示例 `{"type":"https://api.example.com/problems/validation-error","title":"Request body failed validation","status":422}` | prism 校验请求后**挑文档中匹配的错误响应**返回；契约里若没有对应错误响应，客户端就只能收到 prism 自造的体 |
| `POST /orders`，`items[0].quantity = 0` | `422`；日志 `[VALIDATOR] ✖ error Request body property items.0.quantity must be >= 1` → `[NEGOTIATOR] ✔ Found response 422. I'll try with it.` | 约束（`minimum: 1`）真的被执行，而不是只写在文档里 |
| `POST /orders`，合法体 + `Idempotency-Key` | `201` + `Location: ../dictionary` + `Content-type: application/json`；日志 `The request passed the validation rules` | 成功路径与 `Location` 头都被覆盖 |

结论：两个门都可执行、都有区分度，正文按实跑的命令原样写入
（`npx @redocly/cli@latest lint <spec>` / `npx @stoplight/prism-cli@latest mock <spec>`），
并把「warning 不影响退出码」「prism 会为缺失的鉴权失败响应自造 401」两条实跑发现写进正文。

## 基线缺口

无 skill（`uv run tools/run_evals.py api-design --baseline`，Claude Opus 5 / medium）时，
各场景未达成的 `expected_behavior`：

基线极强（Claude Opus 5 medium 本身就是很好的 API 设计者），场景 1 与场景 4 的 6–7 条行为
几乎全部达成。有区分度的缺口集中在三条**需要精确规范知识而非通用判断**的行为上：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 2（分页选型） | 「游标必须不可解析（不是客户端能构造的时间戳），并说明透明游标的后果」 | 答复口头声称游标「不透明、带版本、服务端校验」，但给出的示例游标 `eyJ2IjoxLCJ0IjoiMjAyNi0wMi0xMVQwOTowMzoxMloiLCJpZCI6OTE4MjN9` 是 **JSON 的裸 base64**，`base64 -d` 即得 `{"v":1,"t":"2026-02-11T09:03:12Z","id":91823}`。AIP-158 明确「base64 编码不构成充分的混淆」；答复自身示例与自身主张矛盾，且未说明「客户端一旦能解构就会自己构造，分页实现随即变成公开契约」这个后果 |
| 3（错误契约） | 「要求 `type` 是稳定的文档化 URI，并指出客户端以 `type` 而非 `title`/`detail` 判别」 | 答复用了 RFC 9457 的外壳，却新增扩展成员 `code` 并写下「**只有 `code` 可被分支**」。RFC 9457 §3.1.1 的规范要求是消费者**必须**以 `type` URI 作为问题类型的主标识；把分支键从 `type` 挪到自造的 `code` 上，等于在标准格式里重建了一个私有标识体系。另外答复把 `balance_cents` 从错误体移出（「错误体不载业务数据」），而 RFC 9457 的规范示例正是用 `balance` 扩展成员承载余额——扩展成员就是为让客户端能恢复而存在的 |
| 4（兼容性审查） | 「以对修订后文档的校验步骤收尾（如 `redocly lint`，或用 `prism mock` 跑一遍新契约）」 | 答复给了三阶段发布计划与 YAML 片段，**完全没有任何校验动作**，结尾是「要我把 1.5.0 那批加法直接落到 yaml 里吗？」。改完 OpenAPI 文档不 lint、不 mock，正是本 skill 的验证门要治的 |

另外两条虽不在 `expected_behavior` 里、但值得记录的基线偏差（有 skill 时是否修正一并观察）：

- 场景 1 与场景 4 都写出了 `Deprecation: true`。RFC 9745 §2.1 规定该头的值 **MUST 是
  Structured Field Date**（`Deprecation: @1688169599`）；`true` 是早期草案与二手资料里的
  写法，不符合已发布的 RFC。
- 场景 3 的 `"code": "rate_limited"` 与 `type` URI 尾段完全重复，属冗余标识。

## 评测结果

两组均为 `anthropic/claude-opus-5` + `thinking=medium`（`tools/run_evals.py` 默认，未传
`--model` / `--thinking`）。基线：`--baseline`，答复在
`/tmp/hs-evals/api-design/anthropic-claude-opus-5-medium/baseline/<n>/answer.md`；
有 skill：无参数运行，答复在同路径 `skill/<n>/answer.md`。逐条人工读答复判定。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 资源重建模 | claude-opus-5:medium | 无（baseline） | false | **6/6**：名词化集合、逐条状态码（404/201+Location/404/409）、upsert 归到 `PATCH`、导出改 202 + 轮询、reserve/release 作非 CRUD 动作并提 `Idempotency-Key`、版本分裂给出 `Deprecation`/`Sunset` 路径 | 基线本身就很强。唯一规范偏差：写出 `Deprecation: true`（RFC 9745 要求 Structured Field Date） |
| 1 资源重建模 | claude-opus-5:medium | 有 | true | **6/6** | 产出了 1300+ 行 `openapi.yaml`：`/inventory-exports` 为 202 + `Operation-Location` + `Retry-After` + `/content` 取件，reservation/adjustment 必需 `Idempotency-Key`，遗留路径带 `Deprecation`/`Sunset`。且主动收回上一轮对 `/reserveStock` 的 500 归因（原表无证据），把 12 条「响应全错」拆成「可证的错误响应 / 方法语义错 / 新契约选择」三桶——比基线更克制。`Deprecation` 不再写成 `true` |
| 2 分页选型 | claude-opus-5:medium | 无（baseline） | false | **5/6**。达成：offset 位移机制与 staging 复现不了的因果、改 keyset/cursor、`(created_at, id)` tiebreaker、管理台保留编号页的取舍、去掉 `total_count`。**未达成**：游标不可解析 | 示例游标 `eyJ2IjoxLCJ0IjoiMjAyNi0wMi0xMVQwOTowMzoxMloiLCJpZCI6OTE4MjN9` 是 JSON 的裸 base64，`base64 -d` 即可读并可自行构造；答复声称「不透明」却与自身示例矛盾，也未说明透明游标会把分页实现变成公开契约 |
| 2 分页选型 | claude-opus-5:medium | 有 | true | **6/6**（补上了游标不可解析这条） | 游标改为**服务端签名**，文档写明 `Server-issued and signed; clients echo it back unmodified and MUST NOT parse or construct one`，签名校验失败有独立 problem type `cursor-invalid`；另外补了「过期游标返 422 而不是空页，空页会被误判成遍历结束」。`redocly lint` exit 0 / 0 error 0 warning，prism mock 7 个请求全部命中文档声明的示例、无 prism 合成响应。中途自曝并改掉两处自造错误（未加引号的 YAML 值、把 `Prefer` 头写成 enum 被 prism 判 422） |
| 3 错误契约 | claude-opus-5:medium | 无（baseline） | false | **5/6**。达成：RFC 9457 + `application/problem+json` 五成员、修掉 2xx 失败且状态一致、`errors[]` 带 pointer、剥离堆栈并加 `request_id`、`retryable` + `Retry-After`。**未达成**：`type` 为主标识 | 新增扩展成员 `code` 并明写「**只有 `code` 可被分支**」，把分支键从 `type` 挪到自造标识上，与 RFC 9457 §3.1.1「消费者 MUST 以 `type` URI 为问题类型的主标识」相悖；且 `"code":"rate_limited"` 与 `type` 尾段重复。另把 `balance_cents` 移出错误体，而 RFC 9457 的规范示例恰是用 `balance` 扩展成员承载余额 |
| 3 错误契约 | claude-opus-5:medium | 有 | true | **6/6**（补上了 `type` 为主标识这条） | 明写「`title`/`detail` 在文档里被显式声明为非契约面，唯一分支依据是 `type` URI」，删掉与状态行重复的 `code`，也**不加** `retryable` 布尔（与状态码重复）；`balance_cents` 保留在错误体内并改为 `outstanding_balance {amount_minor, currency}`。补齐 `about:blank` 用法与 `Idempotency-Key` 回放（识破 `idx_charges_idem` 说明有幂等索引但没有回放）。`redocly lint` exit 0 / 0 error 0 warning，11 条 mock 请求全部命中文档示例 |
| 4 兼容性审查 | claude-opus-5:medium | 无（baseline） | false | **6/7**。达成：逐条判定且裸数组→对象与「事后加分页本身破坏」都判对、required 字段/重命名/类型变更、量纲重释义判为最危险、枚举按方向区分、放宽 `maxLength` 判为事实破坏、否掉 200→201 与「只写 changelog」并给出 `Deprecation`/`Sunset`。**未达成**：以对文档的校验步骤收尾 | 三阶段发布计划与 YAML 片段齐全，但**完全没有任何 lint / mock 动作**，结尾是「要我把 1.5.0 那批加法直接落到 yaml 里吗？」。另 `Deprecation: true` 格式错误 |
| 4 兼容性审查 | claude-opus-5:medium | 有 | true | **7/7**（补上了校验收尾这条） | 实跑 `npx @redocly/cli@latest lint shipments-openapi.yaml` → **6 errors / 4 warnings**，并指出这些是 1.4.0 的**现存**缺陷（三个操作缺 `summary`、三个操作无 `security`、三个操作没有任何 4xx 响应）而非本次提案引入，据此论证错误契约只能在 `/v2` 统一定义；同时**如实说明**没跑 prism，因为按要求未产出修订后文档。`Deprecation` 明写为 RFC 9745 结构化字段日期 `@<unix>` 且 `Sunset` 不得更早。另主动回滚了自己越界改写的 1.5.0 文件并给出原文件 md5 |
| 5 负例（FastAPI `Depends` 测试覆盖） | claude-opus-5:medium | 无（baseline） | false | **3/3** | `app.dependency_overrides` + `TestClient`，未读本 skill（baseline 模式），未变成契约评审 |
| 5 负例（FastAPI `Depends` 测试覆盖） | claude-opus-5:medium | 有 | **false** ✅ | **3/3** | 负例判据满足：`skill_read == false`，本 skill 未被加载。答复主体是 `dependency_overrides` 键同一性、per-app 作用域、生成器 override、用真会话而非 Mock 才能让 404 测试不假通过；结尾两行顺带提到 `create_order` 缺 `Location`，属附注而非把答复变成契约评审 |

结论：**通过**。三条基线未达成的行为在有 skill 时全部达成——

1. 场景 2「游标必须不可解析」：base64 JSON → 服务端签名 + 文档明写 MUST NOT parse or construct。
2. 场景 3「`type` 为问题类型主标识」：自造 `code` 分支键 → 删除 `code`，`title`/`detail` 声明为非契约面。
3. 场景 4「以校验步骤收尾」：无任何校验 → 实跑 `redocly lint` 并区分现存缺陷与提案引入的缺陷，
   同时如实说明未跑 mock 的原因。

附带修正（不在 `expected_behavior` 内）：两个场景的 `Deprecation: true` 都改成了 RFC 9745 的
`@<unix>` 结构化字段日期；`retryable` 这类与状态码重复的扩展成员被主动拒绝。
负例场景 `skill_read == false`，边界成立。

## 备注

### 许可注意

- `aip-dev/google.aip.dev` 与 `microsoft/api-guidelines` 的 GitHub API 都返回 `NOASSERTION`，
  实读 `LICENSE.md` / `license.txt` 后确认均为 **CC-BY-4.0**（AIP 的代码示例另为 Apache-2.0），
  可 merged 并在 `notes` 署名。
- `zalando/restful-api-guidelines` 存在许可标注矛盾：发布站 HTML 的 `meta-copyright` 写
  `CC-BY-SA 4.0`，仓库 `LICENSE` 文件与 GitHub API 均为 `CC-BY-4.0`。以仓库 LICENSE 为准，
  已在 `SOURCES.yaml` 的 `notes` 记录该矛盾。
- `borghei/Claude-Skills` 的 LICENSE 实读为 `Commons Clause License Condition v1.0 + MIT`
  ——附加了禁止销售条件，**不是 OSI 开源许可**，按规则记为 `Proprietary` 且 `relation: reference`，
  未复制任何文字。
- `patricksavalle/rest-api-cheatsheet` 无 LICENSE 文件（API `license: null`）。该候选最终未采纳，
  故未进 `SOURCES.yaml`。
- 六条 RFC 与 OpenAPI 规范：RFC 属 IETF Trust / BCP 78 而非 SPDX 许可，记 `license: NONE` 并在
  `notes` 说明只取规范事实自撰；OpenAPI 规范本体所在仓库 `OAI/OpenAPI-Specification` 实查为
  **Apache-2.0**，故 `openapi-spec` 记 Apache-2.0 而非 NONE。

### 临界与陷阱上游的复核结论

- **`microsoft/api-guidelines` 仓库根 `Guidelines.md` 已废弃**（正文只剩一句 NOTICE，指向
  `azure/` 与 `graph/`）。任何按「Microsoft REST API Guidelines」引根文件的做法都会引到空壳；
  `paths` 已改为 `azure/Guidelines.md`。
- `rohitg00/awesome-claude-code-toolkit` 最近推送 2026-05-12，逾 4 个月，新鲜度 0，REJECT。
- `patricksavalle/rest-api-cheatsheet` 最近推送 2026-06-06，逾 3 个月；且其 Spectral 规则与已选定的
  Redocly 验证门重复，按「不罗列多个可选库」不引入。
- `stoplightio/prism` 的默认分支是 `main` 而非 `master`；初次填 `master` 时 `check_upstream.py`
  报 `MISSING`，改正后 pin 成功。

### 未来同步时要盯的

- **OpenAPI 3.2**：3.2.0 已于 2025-09-19 发布、3.2.1 于 2026-09-10 发布，Redocly CLI 2.52.0
  已能校验 3.2 文档。正文当前默认 3.1.x 并写明迁移条件（生成器 / mock / 文档渲染器都接受时再动）。
  下次同步时重估默认版本。
- **限流配额头**：IETF 的 `RateLimit` / `RateLimit-Policy` 工作若成为 RFC，`error-contract.md`
  里标 `[community]` 的那一段要改写为 `[official]` 并给出具体头名。
- **`Idempotency-Key`**：目前无 RFC，事实标准随 Stripe。若 `draft-ietf-httpapi-idempotency-key-header`
  发布为 RFC，`concurrency-and-async.md` 的第三种幂等模式要改标注并对齐规范语法。

### 放弃的方向

- **TypeSpec**（`github/awesome-copilot` 的两个 skill，质量分 12）：编译到 OpenAPI 的具体 DSL，
  与「契约语言选定 OpenAPI 3.1 本体」冲突，且再引入一门 DSL 违反「只给一个默认方案」。
  若 TypeSpec 将来成为主流入口再重估。
- **`skills/openapi-to-application-code` 与 `instructions/aspnet-rest-apis`**：质量分够（11），
  但做的是 spec → 框架代码，正属本 skill 明确排除的框架实现，应归各生态 skill。
- **GraphQL**：Jeffallan、wshobson、orchestkit 三个上游都把 REST 与 GraphQL 混在一个 skill 里，
  本 skill 一律不取，归 `graphql`。
