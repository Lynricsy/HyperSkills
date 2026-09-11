# mcp-server 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`"MCP server agent skill SKILL.md github"`、`"model context protocol" building skill 2026`
  - `gh api search/repositories`：`mcp skills agent-skills stars:>50 pushed:>2026-03-01`
  - `gh api repos/<o>/<r>/git/trees/main?recursive=1 | grep -i mcp`（anthropics/skills、
    anthropics/claude-plugins-official、microsoft/skills、github/awesome-copilot、cloudflare/skills）
  - 官方组织仓库：`modelcontextprotocol/*`（规范、TS/Python/Go/C# SDK、inspector、servers）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- 许可实读：每个 `relation: merged` 的上游都实读了 LICENSE 正文（见「许可实读结论」节），
  不依赖 API 的 `spdx_id`。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | anthropics/claude-plugins-official `plugins/mcp-server-dev/skills/build-mcp-server` | https://github.com/anthropics/claude-plugins-official | 36125 | 2026-09-10 | Apache-2.0（目录内 LICENSE 实读） | 部署形态决策、工具设计模式、auth 三层、MCPB 本地安全 | 3 | 3 | 3 | 2 | 2 | 13 | INCLUDE | 目前最强上游。`references/tool-design.md` 的描述写法、schema 收紧表、`resource_link` vs embedded 取舍是全集最实用的；`references/versions.md` 自陈「MCP spec 2025-11-25 CIMD/DCR status，last verified 2026-03」，即官方 skill 本身落后于 2026-07-28 规范 —— 扣正确 1 分 |
| 2 | modelcontextprotocol/modelcontextprotocol `schema/2026-07-28`、`docs/specification/2026-07-28` | https://github.com/modelcontextprotocol/modelcontextprotocol | 9181 | 2026-09-10 | Apache-2.0（规范与代码）/ CC-BY-4.0（非规范文档），LICENSE 实读 | 规范正文：版本模型、传输、tools/resources/prompts、鉴权、缓存、分页、弃用登记表 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 唯一的规范性事实来源。所有版本门都对 `schema/2026-07-28/schema.ts` 的 `LATEST_PROTOCOL_VERSION` 与 `docs/specification/2026-07-28/deprecated.mdx` 复核 |
| 3 | modelcontextprotocol/python-sdk | https://github.com/modelcontextprotocol/python-sdk | 24266 | 2026-09-10 | MIT（LICENSE 实读，含 MIT→Apache-2.0 过渡声明） | Python 侧真实行为：`MCPServer`（原 `FastMCP`）、stdio fd 挪用、`_meta` 校验、modern/legacy 双时代 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 本机实测对象。`mcp` 2.2.0 是唯一 `LATEST_PROTOCOL_VERSION == 2026-07-28` 的官方 SDK |
| 4 | modelcontextprotocol/typescript-sdk | https://github.com/modelcontextprotocol/typescript-sdk | 13368 | 2026-09-11 | Apache-2.0 / MIT 过渡（LICENSE 实读） | TS 侧真实行为：v1 单包 1.30.0 与 v2 拆包 2.0.0 的 API 与协议上限差异 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 本机实测对象。v1/v2 都把 `LATEST_PROTOCOL_VERSION` 停在 `2025-11-25`，这是 skill 的核心版本分界事实 |
| 5 | github/awesome-copilot `skills/typescript-mcp-server-generator` | https://github.com/github/awesome-copilot | 38883 | 2026-09-10 | MIT | TS SDK v2 拆包清单、codemod、`ctx` 形参、v2 移除 SSE/WebSocket | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 全集唯一跟上 TS SDK v2 的候选；每条包名与 API 变更都在本机 `npm view` + 实跑复核过 |
| 6 | github/awesome-copilot `skills/dotnet-mcp-builder` | 同上 | 38883 | 2026-09-10 | MIT | .NET `ModelContextProtocol` 2.x：`Stateless=true` 默认、`MCP9005` 弃用警告、stdio 日志阈值 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 唯一对齐 2026-07-28 的语言侧候选；「`Stateless=false` 会把客户端逼回 legacy initialize 回退」是别处没有的判断 |
| 7 | github/awesome-copilot `skills/mcp-implementation-security-review` | 同上 | 38883 | 2026-09-10 | MIT | MCP-01..05 基线控制、七类 RCE 向量、绑定地址真值表、误报过滤 | 3 | 3 | 3 | 1 | 2 | 12 | INCLUDE | 全集最强安全内容。仅版本框架陈旧（自称「current: 2025-11-25」、围绕 `Mcp-Session-Id` 组织会话）；控制项本身可移植 |
| 8 | anthropics/skills `skills/mcp-builder` | https://github.com/anthropics/skills | 175703 | 2026-09-10 | Apache-2.0（**目录内 LICENSE.txt 实读**，Copyright 2026 Anthropic, PBC） | 四阶段流程、工具命名、响应格式、`CHARACTER_LIMIT` 截断、评测方法 | 3 | 3 | 2 | 1 | 2 | 11 | INCLUDE | 被 #1 取代但 `reference/node_mcp_server.md` 的内容预算规则、`reference/evaluation.md` 的评测设计仍是最好的。陈旧处：Python 侧仍称 `FastMCP`、分页用 `offset`/`has_more`、正文出现 `WebFetch` 工具名（本仓库禁用） |
| 9 | github/awesome-copilot `skills/mcp-release-qa` | 同上 | 38883 | 2026-09-10 | MIT | 发布前运行时 QA：单一活会话、四路清单一致性、失败路径探针、装到临时目录再验 | 3 | 3 | 3 | 1 | 2 | 12 | INCLUDE | 「只读过的安装串等于未验证」「不要把 init 后的请求拆到多个一次性进程里」是真正的工程纪律。握手步骤需按 2026-07-28 重写 |
| 10 | github/awesome-copilot `skills/mcp-security-audit` | 同上 | 38883 | 2026-09-10 | MIT | `.mcp.json` 客户端配置审计：硬编码凭据正则、危险 args 模式、`@latest` 未固定 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 严格说是客户端配置卫生而非造 server，但「我们让用户粘贴的配置块」确属交付物，作为一节合入 |
| 11 | modelcontextprotocol/inspector | https://github.com/modelcontextprotocol/inspector | 10859 | 2026-09-11 | MIT（**仓库无 LICENSE 文件**，仅 `package.json` 声明） | `--cli` 无头模式：`--method tools/list`、`--tool-name`；2.6.0 | 3 | 3 | 2 | 3 | 1 | 12 | INCLUDE（reference） | 无 LICENSE 文件 → 许可分 1、`relation: reference`，只用其 CLI 行为，不复制任何文字 |
| 12 | modelcontextprotocol/servers | https://github.com/modelcontextprotocol/servers | 90224 | 2026-09-03 | Apache-2.0 / MIT 过渡（LICENSE 实读） | 官方参考 server 实现集 | 3 | 2 | 2 | 2 | 2 | 11 | MAYBE | 是实现样例仓而非指导文本，没有可合入的规则性内容；留作日后校对实现风格的参照，不进 SOURCES |
| 13 | microsoft/skills `.github/skills/mcp-builder` + `reference/mcp_best_practices.md` | https://github.com/microsoft/skills | 3007 | 2026-09-10 | MIT | Anthropic mcp-builder 的 Microsoft 分叉 + 注解默认值表、描述质量门槛 | 3 | 3 | 2 | 0 | 2 | 10 | MAYBE | 正确性 0：C#/.NET 包名写成 `Microsoft.Mcp.Core`（实际是 `ModelContextProtocol`），TS 仍给 v1 单包，并要求运行时去 WebFetch `specification/draft.md`。只取 `mcp_best_practices.md` 的注解默认值表与「描述必须在相似工具里排进前三且不被无关查询选中」这条可证伪门槛 |
| 14 | microsoft/skills `.github/skills/mcp-builder/reference/microsoft_mcp_patterns.md` | 同上 | 3007 | 2026-09-10 | MIT | Azure MCP Server 内部规范：`IAreaSetup`、AOT、Bicep live tests、Foundry 审批 | 3 | 3 | 2 | 2 | 2 | 11 | REJECT | 内容是 Azure MCP Server 这一个产品的内部工程标准，迁移性极低；且自相矛盾地推荐 `npx @azure/mcp@latest`。仅「delete 是破坏性但幂等 / purge 两者都不是」的注解矩阵有价值，已从别处取得同等信息 |
| 15 | github/awesome-copilot `instructions/typescript-mcp-server.instructions.md` | 同上 | 38883 | 2026-09-10 | MIT | TS SDK v1 指令集 + 片段 | 3 | 3 | 2 | 0 | 2 | 10 | REJECT | 与同仓库的 `skills/typescript-mcp-server-generator` 直接冲突且全面落后：`zod@3`、`sessionIdGenerator`、CORS 暴露 `Mcp-Session-Id`、把 sampling 当现行做法。按「更新 > 更旧」全部采信 v2 那份 |
| 16 | github/awesome-copilot `instructions/python-mcp-server.instructions.md` | 同上 | 38883 | 2026-09-10 | MIT | Python FastMCP 指令集 | 3 | 3 | 2 | 0 | 2 | 10 | REJECT | 正确性 0：推荐 `ctx.session.create_message()` 做 sampling（2026-07-28 已弃用）、教客户端通过 CORS 暴露已被移除的 `Mcp-Session-Id`。唯一独有的 `lifespan_context` 用法已由官方 SDK 文档覆盖 |
| 17 | github/awesome-copilot `skills/python-mcp-server-generator` | 同上 | 38883 | 2026-09-10 | MIT | FastMCP 项目生成清单 | 3 | 3 | 1 | 1 | 2 | 10 | REJECT | 教程式清单，无陷阱无判断；内容是 #15/#16 的更薄版本 |
| 18 | github/awesome-copilot `skills/go-mcp-server-generator` | 同上 | 38883 | 2026-09-10 | MIT | Go SDK 项目脚手架 | 3 | 3 | 2 | 1 | 2 | 11 | MAYBE | 主体是 go.mod/main.go 模板。`&mcp.Options{Capabilities: ...}` 与实际 `*mcp.ServerOptions` 不符。只取「泛型 `AddTool` 处理器签名」与 `jsonschema` struct tag 两条事实，不合入正文 |
| 19 | cloudflare/skills `skills/agents-sdk/references/mcp.md` | https://github.com/cloudflare/skills | 2814 | 2026-09-08 | Apache-2.0 | 13 行链接表：`createMcpHandler` 取代已弃用的 `McpAgent` | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE（reference） | 实质内容只有一句，且其余全在链接后面。按「许可通过 ≠ 值得合入」降为 reference，只在正文写一句平台注记并指向 `cloudflare` skill |
| 20 | anthropics/claude-plugins-official `plugins/mcp-server-dev/skills/build-mcpb`（含 `references/local-security.md`） | https://github.com/anthropics/claude-plugins-official | 36125 | 2026-09-10 | Apache-2.0 | 本地 server 无沙箱、路径逃逸 `resolve`+`relative` 判定、命令注入 | 3 | 3 | 3 | 2 | 2 | 13 | INCLUDE | 「MCPB 不提供沙箱，工具入参即不可信输入」是本地 server 最重要的一句。其 roots 一节已被 2026-07-28 弃用，不采 |
| 21 | anthropics/skills `skills/mcp-builder/reference/evaluation.md` | https://github.com/anthropics/skills | 175703 | 2026-09-10 | Apache-2.0（同 #8 目录内 LICENSE.txt） | 评测题设计：可字符串比对、不可被关键词搜索命中、答案须稳定 | 3 | 3 | 3 | 1 | 2 | 12 | INCLUDE | 「server 质量 = LLM 能否用这些工具真的解决任务」这一立场表述得最清楚。陈旧处：runner 仍列 sse 传输、默认模型 `claude-3-7-sonnet-20250219` |
| 22 | modelcontextprotocol/experimental-ext-skills | https://github.com/modelcontextprotocol/experimental-ext-skills | 216 | 2026-09-10 | Apache-2.0 | Skills over MCP 扩展草案（用 MCP 分发 skill） | 3 | 3 | 2 | 3 | 2 | 13 | REJECT | 主题不符：讲的是「通过 MCP 分发 skill」，不是「设计与实现 MCP server」。写 skill 归 `skill-authoring` |
| 23 | ComposioHQ/awesome-claude-skills `mcp-builder/SKILL.md` | https://github.com/ComposioHQ/awesome-claude-skills | 74838 | 2026-08-10 | 无（API `license: null`，仓库无 LICENSE） | Anthropic mcp-builder 的再分发副本 | 0 | 2 | 2 | 1 | 0 | 5 | REJECT | 内容是 #8 的复制，星数来自聚合仓而非该文件的权威性；无许可，且上游本身就有 Apache-2.0 原件可直接用 |
| 24 | modelcontextprotocol/go-sdk、modelcontextprotocol/csharp-sdk | https://github.com/modelcontextprotocol/go-sdk | 5088 / 4521 | 2026-09-07 / 2026-09-11 | Apache-2.0 / MIT 过渡（LICENSE 实读） | Go/C# SDK 真实 API | 3 | 3 | 3 | 3 | 2 | 14 | MAYBE | 本机未安装 Go/.NET 工具链，无法实测，因此不把它们的 API 细节写进正文（只写「语言本身 → 对应生态 skill」）。不进 SOURCES |

REJECT/MAYBE 的行全部保留，避免后续批次重复讨论。

## 许可实读结论

| 上游 | API `spdx_id` | 实读 LICENSE 的结论 | 处置 |
|---|---|---|---|
| anthropics/skills（仓库根） | `null` | 仓库根无 LICENSE；**`skills/mcp-builder/LICENSE.txt` 是完整 Apache-2.0 正文，附录写 `Copyright 2026 Anthropic, PBC.`** | 该目录 **`relation: merged`**。这与波次 5/6 遇到的 anthropics/skills 专有目录不同 —— 许可是**逐目录**的，必须逐目录实读 |
| anthropics/claude-plugins-official | `Apache-2.0` | `plugins/mcp-server-dev/LICENSE` 另有一份完整 Apache-2.0 正文（插件目录自带） | `merged` |
| modelcontextprotocol/modelcontextprotocol | `NOASSERTION` | LICENSE 首段声明项目正在从 MIT 迁移到 Apache-2.0：新代码与**规范**贡献为 Apache-2.0，**非规范文档**为 CC-BY-4.0，未同意重新许可的旧贡献仍为 MIT。三者都是宽松许可 | `merged`，`license: Apache-2.0`，`notes` 写明混合状态与 CC-BY-4.0 署名 |
| modelcontextprotocol/typescript-sdk / go-sdk / csharp-sdk / servers | `NOASSERTION` | 同上同一份过渡声明 + Apache-2.0 正文 | `merged`（typescript-sdk） |
| modelcontextprotocol/python-sdk | `MIT` | LICENSE 含同一段过渡声明；API 归类为 MIT | `merged` |
| modelcontextprotocol/inspector | `null` | **仓库树中没有任何 LICENSE 文件**；只有 `package.json` 的 `"license": "MIT"` | 许可分 1，`relation: reference`，不复制任何文字，只写实测到的 CLI 行为 |
| github/awesome-copilot、microsoft/skills | `MIT` | 仓库根 MIT 正文 | `merged` |
| cloudflare/skills | `Apache-2.0` | 仓库根 Apache-2.0 正文 | 许可通过，但内容是生成式链接表 → 降为 `reference` |

**教训复述**：一个仓库的许可是它自己的，不是它所记录的那个产品的；而 `anthropics/skills` 这种
多 skill 仓库的许可甚至是逐目录的 —— 本次实读发现 `skills/mcp-builder` 是 Apache-2.0，
可以 merged，不能沿用「anthropics/skills 多数目录专有」的成见。

## 深度审查

**#1 anthropics/claude-plugins-official `build-mcp-server`（221 行 + 8 个 references）**
结构：frontmatter 只有 `name`/`description`/`version`（非规范字段 `version` 需剥离）；正文按
Phase 1 追问用例 → Phase 2 推荐部署形态 → Phase 3 工具设计模式 → Phase 4 框架 → Phase 5 脚手架 →
Phase 6 测试发布。质量最高的是 `references/tool-design.md`：描述必须说清「做什么 / 返回什么 /
**不做什么**」、兄弟工具互相指路、schema 收紧对照表（`z.string()` → `z.string().regex(...)`）、
工具数量与上下文经济学（30 个富 schema 工具在对话开始前就吃掉 3–5k token）。
agent 绑定：重度 Claude 绑定 —— `https://claude.com/docs/llms-full.txt`、Anthropic Directory
审核标准、`clientInfo.name: "claude-ai"`、`claude.ai/api/mcp/auth_callback`。这些必须去绑定或
改写成「宿主特定要求」。与 #8 的重叠：#1 是 #8 的实质继任者（同一厂商、更新、更具体）。

**#2 modelcontextprotocol/modelcontextprotocol（规范）**
`docs/specification/` 下并列 `2024-11-05`、`2025-03-26`、`2025-06-18`、`2025-11-25`、
`2026-07-28`、`draft` 六个版本目录；`schema/2026-07-28/schema.ts` 的 `LATEST_PROTOCOL_VERSION`
= `"2026-07-28"`，`schema/draft` 不算已发布版本。`2026-07-28/deprecated.mdx` 是**弃用登记表**
（feature lifecycle，SEP-2596），这是本 skill 版本门的唯一权威出处。2026-07-28 的结构性变化把
`basic/lifecycle.mdx` 换成了 `basic/versioning.mdx`，`basic/transports.mdx` 拆成
`transports/{index,stdio,streamable-http}.mdx`，并新增 `server/discover.mdx`、
`basic/patterns/mrtr.mdx`、`server/utilities/caching.mdx`、`deprecated.mdx`。

**#5 awesome-copilot `typescript-mcp-server-generator`（113 行）**
唯一说清 TS SDK v1→v2 的候选：v1 单包 `@modelcontextprotocol/sdk` 退休，拆成
`@modelcontextprotocol/{core,server,client,node}` + `express|hono|fastify` 适配器；v2 移除
SSE 与 WebSocket 传输；处理器第二参数从 v1 的 `extra` 变成结构化 `ctx`；`npx
@modelcontextprotocol/codemod v1-to-v2` 后 grep `@mcp-codemod-error`。本机 `npm view` 全部
复核通过（见「本机实验」E1）。

**#7 awesome-copilot `mcp-implementation-security-review`（316 行）**
MCP-01..05 基线 + 七类 RCE 向量 + OWASP MCP Top 10 + 报告格式。独有价值：Express 不显式给
host 时实际绑 `0.0.0.0`；Docker 端口发布会穿透进程内的 `127.0.0.1` 绑定；误报过滤清单
（vendored SDK 副本、`.vscode/mcp.json` 是客户端配置不是 server、只出网的
`DefaultAzureCredential`）；「session id 只是关联令牌，永远不是授权凭据」。

**#8 anthropics/skills `mcp-builder`（236 行 + 4 个 reference + 3 个 script）**
`reference/node_mcp_server.md`（969 行）里最值钱的两条：`CHARACTER_LIMIT`（约 25000 字符）
超限就截断、减半数据、置 `truncated: true` 并在文本里说明；**JSDoc 不会被抽取成 description**，
描述必须显式写出并内嵌完整返回 schema。`reference/python_mcp_server.md` 有一个平坦 bug：
`mcp.run(transport="streamable_http")`（实际字面量是 `streamable-http`），以及把所有参数塞进
一个 wrapper Pydantic 模型导致生成的 `inputSchema` 全部嵌在 `params` 下 —— 这是要纠正而非抄袭的
schema 陷阱。scripts/ 三个脚本按约束不复制。

**#9 awesome-copilot `mcp-release-qa`（198 行）**
四路清单一致性矩阵（源码注册 / 运行时发现 / 生成的 catalog / 文档）按稳定标识符比对；用仓库自己的
build 命令重生成派生 catalog 并对未解释的工作树 diff 失败；安装串必须装到 checkout 之外的临时
目录再重跑发现。握手相关步骤（`initialize` 与 `notifications/initialized` 必须在同一会话、
「初始化完成前发请求」「重复初始化」作为负路径）在 2026-07-28 下已不存在，须改写成
「per-request `_meta` 缺 `clientCapabilities` → `-32021`」「`Mcp-Method` 与 body 不符 → `-32020`」
这类现行负路径 —— 本机已实测出这两条的真实报文（见「本机实验」E5/E7）。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 当前规范版本是哪个 | #7 自称「current: 2025-11-25」；#1 的 `versions.md` 以 2025-11-25 为准；#6 按 2026-07-28 写 | **2026-07-28**。正文一律标 `(2026-07-28)`；讲到 SDK 现状时另标 SDK 版本 | `schema/2026-07-28/schema.ts` 的 `LATEST_PROTOCOL_VERSION = "2026-07-28"`；`draft` 不是已发布版本 |
| 2 | `initialize` 握手还算不算现行做法 | #8/#9/#15/#16 全部围绕 `initialize` 组织；#6 说 2.x 默认无状态 | **规范层面已移除**，但**实现层面仍普遍存在**。正文按「规范 2026-07-28 无握手；TS SDK v1 1.30.0 与 v2 2.0.0 的 `LATEST_PROTOCOL_VERSION` 都是 2025-11-25，因此现实里必须双时代兼容」写 | 规范 `2026-07-28/changelog.mdx` 主要变更 2；本机实测 E2/E3/E6 |
| 3 | 会话状态放哪 | #15/#16 教 `sessionIdGenerator` + CORS 暴露 `Mcp-Session-Id`；#7 把会话当审计单位 | **服务端自铸 handle 作为普通工具参数**，协议层无会话 | `2026-07-28/server/tools.mdx` 的 Stateful Tools 一节；`changelog.mdx` 主要变更 1 |
| 4 | 分页形态 | #8/#13 用 `offset`/`has_more`/`total_count` 信封；规范用不透明 `nextCursor` | **不透明 `nextCursor`**（协议层）；业务分页信封可另外放进 `structuredContent`，但不得替代 `nextCursor` | `2026-07-28/server/utilities/pagination.mdx`：cursor 是不透明串，客户端 MUST NOT 解析，空串也是有效 cursor |
| 5 | roots / sampling / logging 要不要用 | #20 教「先问宿主 `roots/list`」；#16 给完整 sampling 示例 | **都不要用于新实现**：2026-07-28 已弃用三者。roots → 工具参数/资源 URI/服务端配置；sampling → 直连 LLM 供应商 API；logging → stdio 写 stderr 或 OpenTelemetry | `2026-07-28/deprecated.mdx` + `changelog.mdx` Deprecated 1（SEP-2577），弃用窗口至少 12 个月 |
| 6 | HTTP+SSE 传输 | #10/#15/#16/#21 仍把 `sse` 当可选传输；#5 说 v2 直接移除 | **自 2025-03-26 起弃用**，2026-07-28 由 SEP-2596 正式归入 Deprecated 状态，迁移到 Streamable HTTP | `2026-07-28/deprecated.mdx` 的 HTTP+SSE 行：`Deprecated in 2025-03-26`，migration path = Streamable HTTP |
| 7 | 抛异常够不够 | #8 的错误示例 `catch (error) { isError: true, text: error.message }`；#1 说「返回 MCP 工具错误，别让异常崩传输」 | **两条都要**：可恢复失败必须落在 `isError: true` 的结果里且文本要可执行；同时**不能把原始异常消息直接转给模型**。两个官方 SDK 在这点上行为相反且都有问题（Python 吞掉消息只给 `Error executing tool <name>`，TS 原样转发含凭据的 `Error.message`），所以必须自己构造错误文本 | 本机实验 E4/E6 的原始报文 |
| 8 | Python 侧入口叫什么 | #8/#16/#17 一律 `from mcp.server.fastmcp import FastMCP` | **`mcp` 2.x 是 `from mcp.server.mcpserver import MCPServer`**；旧路径直接 `ModuleNotFoundError`。另有独立的第三方 PyPI 包 `fastmcp`（4.0.3），与官方 `mcp` 不是同一个东西 | 本机实验 E0 的原始报错 |
| 9 | 工具数量上限 | #1 给 15/30 两档；#13 要求描述在相似工具里排进前三 | 采 #1 的分档（<15 一工具一动作；30+ 转 search+execute），并采 #13 的可证伪门槛作为描述验收方式 | 「官方厂商 > 社区」且两条不矛盾，是同一问题的规则与验收 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| mcp-spec | modelcontextprotocol/modelcontextprotocol | merged | 2026-07-28 规范事实：版本模型、`_meta` 信封、传输、tools/resources/prompts、鉴权、缓存、分页、弃用登记表 |
| mcp-python-sdk | modelcontextprotocol/python-sdk | merged | Python 侧实测行为：`MCPServer` 重命名、stdio fd 挪用、`_meta` 必填键校验、双时代拒绝 |
| mcp-typescript-sdk | modelcontextprotocol/typescript-sdk | merged | TS 侧实测行为：v1 1.30.0 与 v2 2.0.0 的协议上限、`serveStdio` 工厂形参、validator 必填 |
| anthropic-mcp-server-dev | anthropics/claude-plugins-official | merged | 部署形态决策、工具描述与 schema 收紧规则、auth 三层、本地 server 无沙箱与路径逃逸判定 |
| anthropic-mcp-builder | anthropics/skills | merged | 内容预算（截断 + `truncated` 标记）、描述须内嵌返回 schema、评测题设计原则 |
| awesome-copilot-mcp | github/awesome-copilot | merged | TS SDK v2 拆包与 codemod、.NET 2.x 无状态默认、安全审查基线与误报过滤、发布前运行时 QA 纪律、客户端配置审计 |
| microsoft-mcp-builder | microsoft/skills | merged | 注解默认值表与「描述质量可证伪门槛」 |
| mcp-inspector | modelcontextprotocol/inspector | reference | `--cli` 无头验证路径（仅实测行为，未复制任何文字） |
| cloudflare-agents-mcp | cloudflare/skills | reference | 平台注记：Workers 上用 `createMcpHandler` 而非已弃用的 `McpAgent` |

## 本机实验

环境：Linux 7.2.0-1-cachyos · Node v26.7.0 · Python 3.12（uv venv）· uv 0.11.21。
工作目录 `/tmp/mcp-lab`（`/tmp` 可能被清理，故原始输出抄录在此）。

### E0 — Python 官方 SDK 的入口改名

```
$ uv pip install mcp && python -c "import importlib.metadata as m; print(m.version('mcp'))"
2.2.0
$ python py_server.py            # 文件里写的是 from mcp.server.fastmcp import FastMCP
ModuleNotFoundError: No module named 'mcp.server.fastmcp'. This is mcp 2.x, where FastMCP was
renamed to MCPServer (from mcp.server.mcpserver import MCPServer) and other APIs changed; see the
migration guide at https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver
or pin 'mcp<2' to keep running v1 code.
```

`python3 -c` 查 PyPI：`mcp 2.2.0`、`fastmcp 4.0.3`（两个不同的包）。

### E1 — 各 SDK 的协议版本上限（这是 skill 的核心版本分界）

```
$ grep LATEST_PROTOCOL_VERSION node_modules/@modelcontextprotocol/sdk/dist/esm/types.js
export const LATEST_PROTOCOL_VERSION = '2025-11-25';
export const DEFAULT_NEGOTIATED_PROTOCOL_VERSION = '2025-03-26';
export const SUPPORTED_PROTOCOL_VERSIONS = [LATEST_PROTOCOL_VERSION, '2025-06-18', '2025-03-26', '2024-11-05', '2024-10-07'];

$ python -c "import mcp.types as t; print(t.LATEST_PROTOCOL_VERSION, t.DEFAULT_NEGOTIATED_VERSION)"
2026-07-28 2025-03-26

$ npm view @modelcontextprotocol/sdk version        -> 1.30.0
$ npm view @modelcontextprotocol/server version     -> 2.0.0
$ npm view @modelcontextprotocol/core version       -> 2.0.0
$ npm view @modelcontextprotocol/node version       -> 2.0.0
$ npm view @modelcontextprotocol/express version    -> 2.0.0
$ npm view @modelcontextprotocol/fastify version    -> 2.0.0
$ npm view @modelcontextprotocol/hono version       -> 2.0.0
$ npm view @modelcontextprotocol/codemod version    -> 2.0.0
$ npm view @modelcontextprotocol/inspector version  -> 2.6.0
$ npm view @modelcontextprotocol/ext-apps version   -> 2.0.0

# TS SDK v2 的常量仍停在 2025-11-25：
node_modules/@modelcontextprotocol/core/dist/internal.d.mts:
declare const LATEST_PROTOCOL_VERSION = "2025-11-25";
declare const DEFAULT_NEGOTIATED_PROTOCOL_VERSION = "2025-03-26";
```

判定：**规范是 2026-07-28，两条 TS SDK 线（v1 1.30.0 / v2 2.0.0）的 `LATEST_PROTOCOL_VERSION`
都还是 2025-11-25，只有 Python `mcp` 2.2.0 到了 2026-07-28。** 但 TS v2 的
`server/discover` 回的是 `supportedVersions: ["2026-07-28"]`（E6）—— 也就是说 v2 里
`LATEST_PROTOCOL_VERSION` 这个导出常量描述的是 legacy 时代，不能当成实现上限来读。

### E2 — 2026-07-28 的 `_meta` 必填键（Python `mcp` 2.2.0，stdio 原始报文）

发 `server/discover` 只带 `io.modelcontextprotocol/protocolVersion`：

```
[STDOUT] {"jsonrpc":"2.0","id":1,"error":{"code":-32602,"message":"params._meta is missing the required envelope key(s): io.modelcontextprotocol/clientCapabilities"}}
```

补上 `clientCapabilities` 后：

```
[STDOUT] {"jsonrpc":"2.0","id":1,"result":{"cacheScope":"private","capabilities":{"prompts":{"listChanged":true},"resources":{"listChanged":true,"subscribe":true},"tools":{"listChanged":true}},"resultType":"complete","supportedVersions":["2026-07-28"],"ttlMs":0,"_meta":{"io.modelcontextprotocol/serverInfo":{"name":"lab","version":"0.1.0"}}}}
```

判定：2026-07-28 下每个请求都要带 `protocolVersion` + `clientCapabilities`，缺了是 `-32602`；
结果里 `resultType`、`ttlMs`、`cacheScope`、`_meta.serverInfo` 是 SDK 自动补的。

### E3 — 同一个 server 上两个时代是互斥的（Python `mcp` 2.2.0）

先发 legacy `initialize`，再在同一连接上发带 modern 信封的 `tools/list`：

```
[STDOUT] {"jsonrpc":"2.0","id":1,"result":{"capabilities":{...},"protocolVersion":"2025-11-25","serverInfo":{"name":"lab","version":"0.1.0"}}}
[STDOUT] {"jsonrpc":"2.0","id":2,"error":{"code":-32600,"message":"this connection serves the handshake protocol era; requests carrying the 2026-07-28 envelope are not accepted on it"}}
```

判定：时代由连接的开场消息钉死。注意 `server/discover` 只报
`supportedVersions: ["2026-07-28"]`，但同一 server 的 `initialize` 会协商出 `2025-11-25` ——
`discover` 的 `supportedVersions` 只描述 modern 时代。

### E4 — 未捕获异常在两个 SDK 上的结果完全不同

Python `mcp` 2.2.0，工具里 `raise ValueError("db credentials rejected: user=svc host=10.0.0.5")`：

```
[STDERR] mcp.server.mcpserver.exceptions.UnexpectedToolError: Error executing tool boom
[STDOUT] {"jsonrpc":"2.0","id":3,"result":{"content":[{"text":"Error executing tool boom","type":"text"}],"isError":true,...}}
```

TS SDK 1.30.0 与 2.0.0，同样一个 `throw new Error(...)`：

```
[STDOUT] {"result":{"content":[{"type":"text","text":"db credentials rejected: user=svc host=10.0.0.5"}],"isError":true},"jsonrpc":"2.0","id":3}
```

判定：**Python 吞掉异常消息，模型只看到 `Error executing tool <name>`（无法自纠）；
TypeScript 原样把异常消息转给模型（凭据/内网地址泄进上下文）。** 两边都不能依赖，必须在
handler 里自己构造 `isError: true` 的错误文本。另外 Python 侧的**参数校验**错误是原样转发的：

```
[STDOUT] {... "text":"Error executing tool documented: 1 validation error for documentedArguments\ncity\n  Field required [type=missing, input_value={}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing" ...}
```

### E5 — 无描述的工具，客户端到底看到什么

Python `mcp` 2.2.0 的 `tools/list`（`def undocumented(x: str, y: int)`，无 docstring）：

```
{"description":"","inputSchema":{"type":"object","properties":{"x":{"title":"X","type":"string"},"y":{"title":"Y","type":"integer"}},"required":["x","y"],"title":"undocumentedArguments"},"name":"undocumented",...}
```

TS SDK 1.30.0 同样的工具：`description` 键**直接不存在**，参数只有 `type`。
有 `.describe()` 的参数则原样带上 `"description":"City name, e.g. 'Berlin'"`。
另：TS v1 生成 `"$schema":"http://json-schema.org/draft-07/schema#"`，TS v2 生成
`"$schema":"https://json-schema.org/draft/2020-12/schema"`（规范默认方言即 2020-12）。
TS v1 还给每个工具加了 `"execution":{"taskSupport":"forbidden"}`。

### E6 — TS SDK 的双时代行为

v1 1.30.0，客户端请求 `2026-07-28`：

```
[STDOUT] {"result":{"protocolVersion":"2025-11-25",...},"jsonrpc":"2.0","id":1}   # 静默降级
[STDOUT] {"jsonrpc":"2.0","id":6,"error":{"code":-32601,"message":"Method not found"}}   # server/discover
```

v2 2.0.0（`serveStdio(factory)`，默认 `legacy: 'serve'`）：

```
[STDOUT] {"result":{"supportedVersions":["2026-07-28"],"capabilities":{"tools":{"listChanged":true}},"resultType":"complete","ttlMs":0,"cacheScope":"private","_meta":{"io.modelcontextprotocol/serverInfo":{"name":"lab-v2","version":"0.1.0"}}},"jsonrpc":"2.0","id":1}
[STDOUT] {"result":{"protocolVersion":"2025-11-25",...},"jsonrpc":"2.0","id":2}
```

判定：规范 `basic/transports/stdio.mdx#backward-compatibility` 说双时代客户端先探
`server/discover`，**收到任何非 modern 错误就回退 `initialize`，不得只认某一个错误码** ——
v1 回的正是 `-32601`，实测与规范的描述一致。v2 可用 `legacy: 'reject'` 拒绝握手时代客户端。

v2 还踩到两个纯 API 陷阱（都会表现为不透明的 `-32603 Internal server error`）：
`serveStdio` 收的是**工厂函数**而不是 server 实例；且必须显式传
`jsonSchemaValidator`（`@modelcontextprotocol/server/validators/ajv` 的 `AjvJsonSchemaValidator`），
否则每个请求都失败。

### E7 — Streamable HTTP：modern 时代的必需头与被移除的端点

`mcp.run("streamable-http", port=8931)`（Python `mcp` 2.2.0）。不带
`MCP-Protocol-Version` 头时走的是 **legacy** 会话式实现：

```
$ curl -i -X POST .../mcp -d '{... tools/list ... _meta{protocolVersion:2026-07-28, clientCapabilities:{}}}'
HTTP/1.1 400 Bad Request
mcp-session-id: 47e44e44aaaf45ed932afa6082a46e26
{"jsonrpc":"2.0","id":null,"error":{"code":-32600,"message":"Bad Request: Missing session ID"}}

$ curl -i -X POST .../mcp -d '{... "method":"initialize","params":{"protocolVersion":"2026-07-28"...}}'
HTTP/1.1 200 OK ... mcp-session-id: 6dccf00d0e0d496fa7d4720243250c4e
data: {"jsonrpc":"2.0","id":1,"result":{...,"protocolVersion":"2025-11-25",...}}
```

带上 `MCP-Protocol-Version: 2026-07-28` 后切到 modern 实现，响应里**没有** `mcp-session-id`：

```
$ curl -H 'MCP-Protocol-Version: 2026-07-28' ...                       # 缺 Mcp-Method
{"jsonrpc":"2.0","id":1,"error":{"code":-32020,"message":"mcp-method header does not match the request body's method"}}
$ ... -H 'Mcp-Method: tools/call'                                       # tools/call 缺 Mcp-Name
{"jsonrpc":"2.0","id":2,"error":{"code":-32020,"message":"mcp-name header does not match the request body's 'name' parameter"}}
$ ... -H 'Mcp-Method: tools/call' -H 'Mcp-Name: echo'                   # 通过
{"jsonrpc":"2.0","id":2,"result":{"content":[{"text":"hi","type":"text"}],"isError":false,"resultType":"complete","structuredContent":{"result":"hi"},...}}
$ ... -H 'Origin: https://evil.example'      -> 403
$ curl -X GET .../mcp -H 'Accept: text/event-stream'  -> 405
```

判定：`Mcp-Method`（所有请求）与 `Mcp-Name`（`tools/call`/`resources/read`/`prompts/get`）是
2026-07-28 的必需头，不符即 `-32020 HeaderMismatch`；Origin 校验默认开启（403）；
GET SSE 端点在 modern 时代不存在（405）。

### E8 — stdio 上往 stdout 写日志的真实后果

三种情况实测：

1. **Python `mcp` 2.2.0**：工具里 `print("DEBUG: ...")` 出现在 **STDERR** 上，协议帧完好。
   原因在 `mcp/server/stdio.py`：`_claim_fd(1, ...)` 用 `os.dup(2)` 把 fd 1 挪到 stderr，
   把真正的 wire 留在一个私有副本上。源码自述是 best-effort —— 无法复制描述符时
   「serves the sys stream's buffer in place, exactly as v1 did」，即仍可能损坏。
2. **TS SDK 1.30.0 / 2.0.0**：`console.log("DEBUG: ...")` 直接作为一行裸文本出现在 stdout
   的协议流里（`[STDOUT] DEBUG: about to do work`）。宽容的客户端会跳过该行 ——
   Inspector 2.6.0 CLI 仍返回了正确结果。
3. **不带换行的写入才是致命的**。`process.stdout.write("working... ")` 后再返回结果：

```
$ printf '...' | node server_partial.mjs        # 原始 wire
{"result":{"protocolVersion":"2025-11-25",...},"jsonrpc":"2.0","id":1}
working... {"result":{"content":[{"type":"text","text":"done"}]},"jsonrpc":"2.0","id":2}

$ npx @modelcontextprotocol/inspector --cli node server_partial.mjs --method tools/call --tool-name partial_write
{"error":{"code":"error","message":"Request timed out"}}
```

判定：日志文本被拼到了响应帧前面，该行不再是合法 JSON，客户端**丢掉这次响应并超时** ——
这就是「进程随机卡住」的机制。规范 `basic/transports/stdio.mdx` 原文：服务端
**MUST NOT** 往 stdout 写任何非 MCP 消息，**MAY** 往 stderr 写任意 UTF-8 日志。

### E9 — MCP Inspector 可无头使用

```
$ npx @modelcontextprotocol/inspector --cli <cmd> --method tools/list
{ "tools": [ ... ] }        # 正常返回 JSON
$ npx @modelcontextprotocol/inspector --version
（不支持 --version；会启动 UI 并尝试 "Opening browser..."，在无头环境挂住）
```

判定：验证要用 `--cli`（配 `--method` / `--tool-name` / `--tool-arg`）；裸 `npx
@modelcontextprotocol/inspector` 是要开浏览器的 UI，不能进 CI。版本用 `npm view` 查：2.6.0。

### 未在本机验证的部分（正文标 `[official]`）

- OAuth 2.1 / RFC 8707 / RFC 9728 / CIMD 的完整流程 —— 需要真实授权服务器，本机未搭建；
  规则出处是 `2026-07-28/basic/authorization/{index,security-considerations,client-registration}.mdx`。
- `subscriptions/listen`、MRTR（`InputRequiredResult`）、tasks 扩展、`x-mcp-header` 镜像 ——
  Python `mcp` 2.2.0 声明了 `resources.subscribe` 能力，但未实测这些流程的完整往返。
- Go / C# SDK 的 API 细节 —— 本机无 Go、无 .NET 工具链，未安装未实测；正文不写其 API。
- `caching.mdx` 的 `ttlMs`/`cacheScope` 客户端侧语义 —— 只实测到服务端会发出这两个字段
  （`ttlMs: 0`、`cacheScope: "private"`），未实测客户端缓存行为。

## 基线缺口

无 skill（`uv run tools/run_evals.py mcp-server --baseline`，Claude Opus 5 · medium，五场
`skill_read=False`）时，各场景未达成或只部分达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 | #3 每个参数都要有 `description`（`mode`/`op` 应为 enum） | 基线删掉了没用到的 `mode`、给 `id` 加了正则白名单，但从未提出「参数级 description 是模型唯一能读到的语义」这条规则 |
| 1 | #1 的机制部分（部分达成） | 正确指出 `console.log` 写 stdout 是协议帧 bug，但把「随机挂起」归因于 `uncaughtException` 处理器不退出导致请求无响应；未识别「不带换行的写入会拼到下一帧前面、客户端丢响应并超时」这条实测机制 |
| 1 | #6 的不透明游标部分（部分达成） | 加了 `cursor`/`limit`，但游标是数字偏移（实跑输出 `nextCursor:3`），不是不透明串；也没提「空串是合法游标」 |
| 1 | #7 的泄漏部分（部分达成） | 用 `guard()` 把异常转成 `{isError:true}`，但没有指出 TS SDK 会把 `Error.message` 原样交给模型这件事本身是泄漏面 |
| 2 | #4 规范版本 ≠ SDK 实现上限，必须实测 | 基线读了 v1 的 `LATEST_PROTOCOL_VERSION = '2025-11-25'`（正确），但随后**从版本号推断** v2 支持 2026-07-28，没有去读 v2 的同名常量（也是 2025-11-25）也没有对运行中的 server 打 `server/discover`。后果直接可见：它接着编造了 `createMcpHandler`、`createRequestStateCodec({key,ttlSeconds})`、`legacy: 'stateless'`、`isLegacyRequest()`、`ServerOptions.cacheHints`、`ctx.mcpReq.elicitInput()` —— 这些在 `@modelcontextprotocol/server` 2.0.0 里都不存在 |
| 2 | #3 的回退规则部分（部分达成） | 说了 `server/discover` 是 MUST，但没说双时代回退「不得只认某一个错误码」，而是给了一个虚构的 `isLegacyRequest()` 分流 |
| 3 | #3 的 CIMD 部分 | 完全没提 DCR 在 2026-07-28 已被弃用、应改 Client ID Metadata Documents；改写后的配置仍保留 `client_registration: dcr` + `registration_endpoint` |
| 3 | #5 的会话移除部分 | 说了「session 不是凭据」，但把 `session:` 块**保留并加固**（`store: redis`、`id_source: csprng`、`bind_to_user`），从未指出 2026-07-28 已经没有协议级会话、`Mcp-Session-Id` 头已被移除 |
| 3 | #4 的 scope 挑战部分（部分达成） | 收敛了 scope，但没有 `403` + `WWW-Authenticate` 指明所需 scope 的挑战机制，也没有 step-up 授权 |
| 4 | #6 用实跑验证发布配置 | 给出了正确的最小配置块，但完全没有「装起来跑一遍 `tools/list` 再发布」这一步；它自己也说「未改写 mcp.json」，整份审查停在阅读 |
| 5（负例） | 无 | 三条全达成，`skill_read=False`，没有任何协议内幕 |

另外两个观察，不计入缺口但值得记录：

1. 基线在场景 2/3 里引用的是 **2025-06-18 / 2025-11-25** 的规范页面，而不是 2026-07-28；它拿到的
   「当前版本」取决于当次检索命中哪一页。
2. 基线的失败模式不是「不知道」而是**用对的框架编错的 API**：spec 层面几乎全中，SDK 层面凭
   合理性生成函数名。这正是「本机实测 + 版本矩阵」这类内容的价值所在。

## 评测结果

模型固定 `anthropic/claude-opus-5` · thinking=medium（`tools/run_evals.py` 默认）。
场景 2、3 的 `expected_behavior` 在首轮基线之后按 Phase B 收紧过（#2.4 改为要求「实测 SDK 常量
+ 打 `server/discover`」，#3.3 补上 CIMD），**基线已按收紧后的版本重跑**，两组因此可比。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 审查糟糕的 server 源码 | claude-opus-5 / medium | 无（基线） | false | 4/7 全达成 + 3 条部分达成（#1、#6、#7） | 未达成 #3；把挂起归因于 uncaughtException 而非帧拼接 |
| 1 | claude-opus-5 / medium | 有 | **true** | **7/7** | 明确写出「一条非 JSON 行或无换行写入会吞掉下一帧 → 客户端超时，这就是随机挂起的机制」；给出三段式描述模板与每参数 `.describe()`；游标用 base64url 不透明串且「空串是合法游标，不能当结束」；点名 `TS SDK 1.30.0 把 Error.message 原样交给模型`。自建脚手架实跑 7 帧全合法 JSON |
| 2 迁移到 2026-07-28 | claude-opus-5 / medium | 无（基线） | false | 4/6 全达成 + 1 条部分（#3） | 未达成 #4；并编造了六个不存在的 SDK API |
| 2 | claude-opus-5 / medium | 有 | **true** | **6/6** | 「v2 的 `LATEST_PROTOCOL_VERSION` 仍然读 2025-11-25，同一个 build 却用 `server/discover` 回答 2026-07-28。别拿这个常量当实现上限判据」；`serveStdio` 的 `legacy: 'serve' \| 'reject'` 是真实 API；另外自发带出 v2 必须显式传 `jsonSchemaValidator`、v1 静默降级、era 混用回 `-32600` |
| 3 审查鉴权配置 | claude-opus-5 / medium | 无（基线） | false | 4/7 全达成 + 3 条部分（#3、#4、#5） | 保留并加固了 `Mcp-Session-Id` 会话；`client_registration` 仍是 `dcr` |
| 3 | claude-opus-5 / medium | 有 | **true** | **7/7** | 「DCR 在 2026-07-28 弃用 → 改 CIMD（`client_id_metadata_document_supported: true`），删 `registration_endpoint`」；「2026-07-28 已无协议会话」并直接删掉 session 块；补 `403` + `WWW-Authenticate` + step-up 与 scope 层级；输出用 `path:line - finding` + 阻塞/加固两段 |
| 4 审查要发布的客户端配置 | claude-opus-5 / medium | 无（基线） | false | 5/6 | 未达成 #6（无实跑验证步骤） |
| 4 | claude-opus-5 / medium | 有 | **true** | **6/6** | 逐行 `mcp.json:5/7/12/15/19/20` + 阻塞/加固分段，并把 `npx @modelcontextprotocol/inspector --cli <cmd> --method tools/list`（装到 checkout 之外的临时目录）作为发布门；还自己纠了三条先前结论（改 `type` 不等于迁移传输） |
| 5 负例：连不上别人的 GitHub MCP server | claude-opus-5 / medium | 无（基线） | false | 3/3 | — |
| 5 负例 | claude-opus-5 / medium | 有 | **false** | **3/3** | **未读取 `skills/mcp-server/` 下任何文件**；回答全是运维排障（配置键名 `servers` vs `mcpServers`、`${input:...}` 不被解析、docker 缺 `-i`、镜像拉取超时），全文 0 次提及 `2026-07-28` / `server/discover` / `_meta` / `resultType` / `inputSchema` |

结论：**通过**。基线未达成的 5 条独立行为（1#3、2#4、3#3、3#5、4#6）在有 skill 时全部达成，
另有 4 条从「部分达成」升到「全达成」。负例两组 `skill_read` 都是 `false`，无需收紧
`description` 的 `Do not use for …`。

## 备注

**许可**

- `anthropics/skills` 的许可是**逐目录**的：仓库根无 LICENSE，但 `skills/mcp-builder/LICENSE.txt`
  是完整 Apache-2.0（`Copyright 2026 Anthropic, PBC.`）。本次据此 `relation: merged`，其
  `scripts/` 目录未复制。**这个结论只覆盖 `skills/mcp-builder` 一个目录**，其他目录仍须逐个实读。
- `modelcontextprotocol/*` 全系仓库的 LICENSE 首段是同一份 MIT→Apache-2.0 过渡声明：新代码与
  规范为 Apache-2.0、非规范文档为 CC-BY-4.0、未同意重新许可的旧贡献仍为 MIT。三者都宽松，
  `merged` 可行；`SOURCES.yaml` 的 `notes` 已写明。
- `modelcontextprotocol/inspector` 仓库树里**没有 LICENSE 文件**，MIT 只在 `package.json` 里声明
  → 许可分 1、`relation: reference`，只记录实测到的 CLI 行为。
- `cloudflare/skills` 许可（Apache-2.0）没问题，但 `skills/agents-sdk/references/mcp.md` 是 13 行
  生成式链接表 → 按「许可通过 ≠ 值得合入」降为 `reference`。

**日后同步时要盯的上游**

- `modelcontextprotocol/modelcontextprotocol` 的 `schema/` 目录：出现新的日期目录就意味着新修订，
  `references/protocol-model.md` 的版本门与 `deprecated.mdx` 派生表都要重算。
- `@modelcontextprotocol/server` / `@modelcontextprotocol/core`：只要它们的
  `LATEST_PROTOCOL_VERSION` 从 `2025-11-25` 动了，`references/sdk-versions.md` 的矩阵与
  SKILL.md 的「Migrate across a revision」workflow 都要改。
- `mcp`（PyPI）：2.x 已经把 `FastMCP` 改名 `MCPServer`，下一次大版本很可能再动入口。
- `github/awesome-copilot` 的 `instructions/*-mcp-server.instructions.md`：本轮全部 REJECT。
  若它们哪天与同仓 `skills/*-mcp-server-generator` 对齐了，可重估。

**放弃的方向**

- Go / C# 的 SDK API 细节：本机无 Go、无 .NET 工具链，无法实测，写进正文只会是未验证内容。
  正文只保留 .NET 包名与 `Stateless` 默认值这两条 `[official]`，其余交给 `go` / `csharp-dotnet` skill。
- MCP Apps（`ui://` 资源 + iframe widget）与 MCPB 打包：都有 Apache-2.0 的官方上游
  （`build-mcp-app`、`build-mcpb`），但前者是宿主特定的 UI 扩展、后者是分发打包格式，
  与「设计与实现 server」的主线相比是分支主题；只从 `build-mcpb` 取了「本地 server 无沙箱」这一节。
- `modelcontextprotocol/experimental-ext-skills`（Skills over MCP）：主题是用 MCP 分发 skill，
  归 `skill-authoring`，已在 SKILL.md 的 `## Scope` 里明确排除。
- 没有写 `scripts/`：本 skill 的可执行内容都是一行命令（Inspector CLI、`npm view`、`gh api`、
  `curl` 探针），包成脚本只会多一层间接；这些命令直接内联在 SKILL.md 与
  `references/{sdk-versions,testing}.md` 里。
