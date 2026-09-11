# mongodb 调研记录

单一权威上游改写（官方厂商特例：mongodb/agent-skills + mongodb.com/docs + 跨厂商/社区上游）。

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"MongoDB agent skill SKILL.md github claude skills mongodb aggregation indexing"`
  - `gh api search/repositories -f q='mongodb skill agent SKILL.md in:name,description,readme'`（40 条）
  - <https://www.skills.sh>（经 web_search 结果页命中 `mongodb/agent-skills` 各 skill）
  - VoltAgent/awesome-agent-skills、libukai/awesome-agent-skills（搜索结果命中，未收录独立 mongodb skill）
  - 领域官方组织仓库：`mongodb/`、`mongodb-developer/`、`mongodb-js/`、`Azure/`、`github/awesome-copilot`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- 上游全树列举：`gh api repos/mongodb/agent-skills/git/trees/main?recursive=1`
  （注意：`plugins/mongodb/.agy-plugin/skills/*` 与 `plugins/mongodb-atlas/.agy-plugin/skills/*`
  是 `plugins/*/skills/*` 的镜像副本，同一份内容出现三处；`skills/` 顶层只有 `OWNERS.yaml`，
  真实内容在 `plugins/mongodb/skills/*`，`paths` 按此填写。）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | mongodb/agent-skills `plugins/mongodb/skills/mongodb-schema-design` | https://github.com/mongodb/agent-skills | 182 | 2026-09-10 | Apache-2.0 | 建模：嵌入 vs 引用、16 MB、schema 验证、11 个模式、3 个反模式 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方；22 个 reference 全是「错误示例 → 正确示例 → 何时不用 → 量化影响 → 验证命令」的定型结构，正是本 skill 建模章的骨架 |
| 2 | mongodb/agent-skills `plugins/mongodb/skills/mongodb-query-optimizer` | https://github.com/mongodb/agent-skills | 182 | 2026-09-10 | Apache-2.0 | 索引原则、ESR、聚合优化、更新反模式、explain 流程 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方；`core-indexing-principles.md` 与 `aggregation-optimization.md` 是索引/管道两章的事实来源。正文骨架被 MongoDB MCP 工具名绑死，须整体剥离后重写 |
| 3 | mongodb/agent-skills `plugins/mongodb/skills/mongodb-search-and-ai` | https://github.com/mongodb/agent-skills | 182 | 2026-09-10 | Apache-2.0 | Atlas Search、$vectorSearch、自动 embedding、$rankFusion/$scoreFusion 混合检索 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方；版本门槛（`$rankFusion` 8.1+、`$scoreFusion` 8.2+）与「不要用 `$regex`/`$text` 做检索」这条裁决直接采纳 |
| 4 | mongodb/agent-skills `plugins/mongodb/skills/mongodb-connection` | https://github.com/mongodb/agent-skills | 182 | 2026-09-10 | Apache-2.0 | 连接池大小、超时、serverless、监控连接数公式 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方；`(minPoolSize + 2) × 成员数 × 实例数` 这个易被忽略的监控连接开销来自这里 |
| 5 | mongodb/agent-skills `plugins/mongodb/skills/mongodb-natural-language-querying` | https://github.com/mongodb/agent-skills | 182 | 2026-09-10 | Apache-2.0 | 自然语言 → 只读查询/管道的生成流程 | 3 | 3 | 2 | 3 | 2 | 13 | MAYBE | 内容优秀但形态是「MCP 只读查询代理」的操作规程，与本 skill「写代码/评审」的定位不同；只取其中「先 `collection-schema` 再写查询」「默认加 `limit`」两条语义 |
| 6 | mongodb/agent-skills `plugins/mongodb/skills/mongodb-mcp-setup` | https://github.com/mongodb/agent-skills | 182 | 2026-09-10 | Apache-2.0 | 安装配置 MongoDB MCP Server | 3 | 3 | 3 | 3 | 2 | 14 | REJECT | 产品安装说明书，边界外（属 `mcp-server` 主题），不合入 |
| 7 | mongodb/agent-skills `plugins/mongodb/skills/mongodb-atlas-stream-processing` | https://github.com/mongodb/agent-skills | 182 | 2026-09-10 | Apache-2.0 | Atlas Stream Processing 管道 | 3 | 3 | 3 | 3 | 2 | 14 | REJECT | Atlas 托管产品面（本 skill 明确不覆盖云托管控制面） |
| 8 | Azure/documentdb-agent-kit `skills/{indexing,data-modeling,sharding,query-optimization,driver,connection}` | https://github.com/Azure/documentdb-agent-kit | 5 | 2026-08-31 | MIT | ESR、多键/通配/TTL/2dsphere、分片键选型、16 MB、explain | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE | 跨厂商交叉校验：DocumentDB 是 MongoDB 线协议兼容引擎，索引/分片/建模规则与 MongoDB 一致，能验证官方仓的说法；**引擎差异条目（RUM/GiST 索引、`textSearch` 代替 `$text`、64 索引上限）一律不采纳** |
| 9 | mongodb-developer/edd-skill | https://github.com/mongodb-developer/edd-skill | 2 | 2026-05-11 | NONE（无 LICENSE 文件） | EDD 实体文档图记法：用一种紧凑文本表示建模决策 | 2 | 1 | 3 | 3 | 0 | 9 | MAYBE | MongoDB Developer Relations 组织，但非产品团队；记法本身是发明的新符号，不进正文；只取「先把访问模式画成图再定嵌入/引用」这条流程语义 |
| 10 | github/awesome-copilot `instructions/mongo-dba.instructions.md` | https://github.com/github/awesome-copilot | 38872 | 2026-09-10 | MIT | DBA 场景的 Copilot 行为指令 | 1 | 3 | 1 | 2 | 2 | 9 | MAYBE | 25 行，全是「推荐装 VS Code 扩展」「参考官方文档」这类元指令，无可执行规则；只作覆盖面清单参照，不取文字 |
| 11 | github/awesome-copilot `agents/mongodb-performance-advisor.agent.md` | https://github.com/github/awesome-copilot | 38872 | 2026-09-10 | MIT | 性能诊断 agent 定义 | 1 | 3 | 2 | 2 | 2 | 10 | MAYBE | 77 行 agent 定义（含 `tools:` 绑定），主题清单可用（profiler、`$indexStats`、working set），文字与结构不取 |
| 12 | claude-dev-suite/claude-dev-suite `skills/databases/mongodb` | https://github.com/claude-dev-suite/claude-dev-suite | 33 | 2026-09-08 | MIT | CRUD、聚合、索引速查 | 1 | 3 | 2 | 2 | 2 | 10 | MAYBE | 322 行通用教程 + `quick-ref/`，多数是模型已知的 API 罗列；仅用作「常见任务清单」的覆盖面对照 |
| 13 | Mindrally/skills `mongodb-development` | https://github.com/Mindrally/skills | 260 | 2026-09-03 | Apache-2.0 | Payload CMS + Mongoose + TypeScript | 1 | 3 | 1 | 2 | 2 | 9 | REJECT | 实质是 Payload CMS/Mongoose 说明，MongoDB 规则只有 7 条泛泛之谈（「设计索引」「用聚合管道」），无边缘情况 |
| 14 | BagelHole/DevOps-Security-Agent-Skills `infrastructure/databases/mongodb` | https://github.com/BagelHole/DevOps-Security-Agent-Skills | 1081 | 2026-05-22 | MIT | 副本集、分片、备份的运维操作 | 1 | 1 | 2 | 2 | 2 | 8 | MAYBE | 420 行运维手册，>3 月未推送；只用于核对副本集/写关注度一节的覆盖面，不取文字 |
| 15 | HoangNguyen0403/agent-skills-standard `skills/database/database-mongodb` | https://github.com/HoangNguyen0403/agent-skills-standard | 565 | 2026-09-09 | MIT | 48 行规则卡：访问模式建模、ESR、深 skip 分页、无界数组 | 1 | 3 | 2 | 3 | 2 | 11 | MAYBE | 规则密度高且全部正确，但每条都被 1–4 号官方上游以更细的形式覆盖；用作「本 skill 是否漏了常见坑」的核对清单 |
| 16 | mongodb.com/docs（源仓 mongodb/docs） | https://www.mongodb.com/docs/manual/ | 777 | 2026-09-10 | NONE（无 LICENSE 文件） | 服务端手册：版本门槛、算子语义、explain 字段 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE | 所有版本敏感事实的取证源。许可实查见「备注」 |
| 17 | mongodb/mongo（服务端本体） | https://github.com/mongodb/mongo | 28549 | 2026-09-10 | SSPL-1.0（API 报 NOASSERTION） | 服务端实现与 jstests | 3 | 3 | 3 | 3 | 0 | — | reference | **SSPL → 只 reference**：仅用于确认当前发布分支（8.3.x rapid / 8.0 LTS，9.0 尚在 alpha），不复制任何代码或文本 |
| 18 | mongodb-js/mongodb-mcp-server | https://github.com/mongodb-js/mongodb-mcp-server | 1125 | 2026-09-10 | Apache-2.0 | MongoDB MCP Server 实现 | 3 | 3 | 3 | 3 | 2 | — | REJECT | 是官方上游 skill 依赖的工具本身，不是 MongoDB 使用知识；边界外 |

## 深度审查

### 1–4 mongodb/agent-skills（官方，Apache-2.0）

- **结构**：仓库把内容放在 `plugins/{mongodb,mongodb-atlas}/skills/<name>/`，并在
  `plugins/*/.agy-plugin/skills/` 下各复制一份（三处同名文件内容一致）。顶层 `skills/`
  只有 `OWNERS.yaml`。`SOURCES.yaml` 的 `paths` 取 `plugins/mongodb/skills/...` 这一份。
- **frontmatter**：`name` / `description` / `license: Apache-2.0` / `metadata.version: "1.0.0"`；
  `mongodb-query-optimizer` 还有顶层 `compatibility:`（规范允许）。没有 `allowed-tools`、
  `paths` 之类的 agent 专属字段，剥离成本低。`metadata.version` 是语义版本，本仓库要求日期版本，需改写。
- **质量**：`mongodb-schema-design` 的 22 个 reference 是全仓最有价值的部分——每篇都给
  「反例 → 正例 → 何时不适用 → 量化影响 → 验证命令」。`mongodb-query-optimizer` 的
  `core-indexing-principles.md`、`aggregation-optimization.md` 同样具体。
- **agent 绑定（本 skill 必须解掉的部分）**：四个 skill 的正文主线都是「调用 MongoDB MCP
  server 的 `collection-indexes` / `explain` / `find` / `atlas-get-performance-advisor` 工具」，
  甚至写了 MCP 参数对象的 JSON schema。`docs/skill-standard.md` §1.3 禁止绑定特定 agent 的工具名，
  且本 skill 的读者多数在写应用代码而非连着 MCP。**裁决**：把工具调用改写成
  `mongosh` / 驱动侧的等价命令（`db.coll.getIndexes()`、`explain("executionStats")`、
  `db.currentOp()`、`$indexStats`），MCP 只在 `## Environment` 里以一句「若已连接 MongoDB MCP
  server，同样的检查可由它执行」带过。
- **另一处必须删的东西**：`mongodb-schema-design` 结尾有大段第一人称的「Action Policy」
  （"I will NEVER execute write operations without your explicit approval"、"We're a team"）。
  标准要求第三人称、祈使语气，且这属于 harness 层的审批策略而非 MongoDB 知识 → 整段不合入，
  只把「对生产库执行写/DDL 前先展示命令并取得确认」压缩成 workflow 里的一步。
- **重叠**：四个 skill 之间边界清晰（建模 / 索引与查询 / 检索 / 连接），正好映射成本 skill 的
  四组 reference，无内部冲突。

### 8 Azure/documentdb-agent-kit（MIT）

结构比官方仓更「规则卡化」：每个 `skills/<topic>/SKILL.md` 只列条目，正文在同目录的
`<topic>-<rule>.md`。索引一章（11 条）与分片一章（7 条）覆盖度超过官方 skill——官方
`core-indexing-principles.md` 没有单独讲多键索引的「一个复合索引里只能有一个数组字段」限制，
也没有 `hideIndex` → `dropIndex` 的安全下线流程。这两条经 mongodb.com/docs 核实后采纳。
**引擎差异必须过滤**：DocumentDB 建在 PostgreSQL 上，其「RUM/GiST 索引类型」「64 个单字段索引
上限」「用 `textSearch` 索引代替 `$text`」都是 DocumentDB 独有，不适用于 MongoDB，全部丢弃。

### 9 mongodb-developer/edd-skill（无许可）

398 行，定义了一套「实体文档图」文本记法（`@collection`、`~>` 表示引用等）。发明记法这件事
本身与本仓库「不重复模型已知常识、只写陷阱」的写作规则冲突——让模型学一套新符号是纯 token 成本。
只保留其流程语义：建模讨论从「列出访问模式」开始，而不是从「画实体关系」开始。

### 10–15 社区候选

`mongo-dba.instructions.md`（25 行）与 `mongodb-performance-advisor.agent.md`（77 行）都是
Copilot 的行为配置而非知识；`claude-dev-suite` 与 `Mindrally` 是教程/框架说明；
`BagelHole` 是运维手册且 >3 月未推送；`HoangNguyen0403` 的 48 行规则卡质量最高但完全被官方覆盖。
六者合计的唯一价值是覆盖面核对：它们提到而官方 skill 未展开的主题只有两个——
**深 `skip()` 分页**（HoangNguyen0403）与 **profiler / `db.currentOp()` 定位在跑的慢查询**
（awesome-copilot agent）。两者都补进正文，事实从 mongodb.com/docs 取证。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 全文检索用什么 | mongodb-search-and-ai：**绝不**推荐 `$regex` / `$text`，一律 Atlas Search；社区候选（claude-dev-suite、BagelHole）仍教 `$text` 索引 | 分情况：Atlas 上用 `$search`；自管副本集上没有 Atlas Search，`$text` 是唯一内置选项，写明其限制（每集合仅一个 text 索引、无相关性调优、无模糊匹配）并指向 `elasticsearch` skill | 官方 > 社区；但官方 skill 默认读者在 Atlas，自管场景不能留空。本机实测：自管 8.3.9 上 `$text` 可用，`$search` / `$vectorSearch` 报 `Using $search and $vectorSearch aggregation stages requires additional configuration. Please connect to Atlas or an AtlasCLI local deployment to enable.` |
| 2 | 一个集合应该有多少索引 | mongodb-query-optimizer：「一般不超过 20 个」；Azure documentdb-agent-kit：「保持 5–15 个，上限 64」 | 正文写「超过约 20 个就要逐个论证」，不写硬上限 | 官方厂商 > 跨厂商；64 是 DocumentDB 的引擎限制，MongoDB 的硬限制是每集合 64 个索引——数字巧合但来源不同，正文只保留「每集合 64 个索引的硬上限」这一条 MongoDB 事实并从 docs 取证 |
| 3 | 嵌入 vs 引用的判定阈值 | mongodb-schema-design 给表：1:N，N<100 嵌入，N>100 引用；同一文件下方又说这是 "rough guideline" | 正文不写 100 这个数，改写成三个可判定的条件：数组是否有确定上界、子文档是否被独立查询/更新、增长是否与父文档寿命同步 | 阈值不可判定（100 个 1 KB 子文档和 100 个 1 MB 子文档不是一回事）；官方自己标注为粗略指引 |
| 4 | `$lookup` 是不是反模式 | mongodb-schema-design `antipattern-excessive-lookups`：过度规范化导致的 `$lookup` 是反模式；Azure documentdb 与社区：`$lookup` 是正常的联表手段 | 正文按代价写而不是按禁令写：`$lookup` 的内层每个外层文档执行一次，只有 `localField`/`foreignField` 形式能用被连接集合的索引；`let` + `pipeline` 形式里的 `$match` 只有写成 `$expr` 且命中索引才不退化 | 官方 > 社区；且这是可实测的（见「本机实验」第 4 组） |
| 5 | 版本门槛 | 官方 skill 的 `metadata.version: 1.0.0` 不体现服务端版本；`mongo-dba` 只说 "MongoDB 7.x+"；hybrid-search.md 自称 `$rankFusion` 8.0+ / `$scoreFusion` 8.3+ | 正文以 **MongoDB 8.0 LTS** 为基线，rapid release 才有的能力逐条加门（`$rankFusion` 8.0+、`$scoreFusion` 8.3+），当前 rapid 为 8.3.x | `gh api repos/mongodb/mongo/tags` 显示最新 tag `r8.3.9`，`r9.0.0-alpha*` 仍是 alpha；本机 `mongo:8.3` 镜像 `db.version()` = 8.3.9；两个门槛以 mongodb.com/docs 的 `$rankFusion`（"MongoDB 8.0 and later"）与 `$scoreFusion`（"MongoDB 8.3+"）页面复核，未采信记忆 |
| 6 | 连接池大小 | mongodb-connection：默认 100 够用，serverless 用 3–5；社区候选普遍不提监控连接 | 采纳官方，并把 `(maxPoolSize + 2) × 副本集成员数 × 应用实例数` 这个总量公式提到 Core rules | 官方；这是最常被漏算的一项 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `mongodb-agent-skills` | mongodb/agent-skills（Apache-2.0，官方） | merged | 建模模式与反模式、索引原则与 ESR、聚合优化、检索与向量、连接池的全部骨架 |
| `mongodb-docs` | mongodb.com/docs（源仓 mongodb/docs，无 LICENSE） | merged | 全部版本门槛与算子语义的取证源；`license: NONE` + notes |
| `azure-documentdb-kit` | Azure/documentdb-agent-kit（MIT） | merged | 多键索引的并行数组限制、`hideIndex` 下线流程、分片键选型清单（已剥离 DocumentDB 引擎差异） |
| `awesome-copilot` | github/awesome-copilot（MIT） | reference | 覆盖面核对（profiler / `$indexStats` / working set），未取文字 |
| `mongodb-server` | mongodb/mongo（SSPL-1.0） | reference | 仅确认发布分支与版本门槛，不复制任何内容 |
| `edd-skill` | mongodb-developer/edd-skill（无 LICENSE） | reference | 「从访问模式清单起步」的建模流程语义 |

## 本机实验

环境：`docker run -d --name mdbcheck --rm mongo:8.3 --replSet rs0 --bind_ip_all` + `rs.initiate(...)`，
单节点副本集，`db.version()` = **8.3.9**。脚本在 `/tmp/mdb-exp/exp{1..7}.js`，用
`docker cp … && docker exec mdbcheck mongosh --quiet /tmp/expN.js` 执行。
数据集：`lab.orders` 20 万文档（`status` 4 值、`region` 4 值、二者取值互相独立、`date` 递增、
`customerId` 0–4999），`lab.cust` 20 万文档。

### 1. ESR 复合索引列序（`find({status,region}).sort({date:-1}).limit(20)`）

| 索引 | nReturned | totalKeysExamined | totalDocsExamined | ms |
|---|---|---|---|---|
| 无索引 | 20 | 0 | 200000 | 74 |
| `{status:1}` | 20 | 50000 | 50000 | 57 |
| `{date:-1,status:1,region:1}`（S 在前） | 20 | 319 | 319 | 3 |
| `{status:1,region:1,date:-1}`（ESR） | 20 | 20 | 20 | 2 |

关键补充：把过滤值换成只匹配 1 个文档的稀有值后，**S 在前的索引退化为全索引扫描**
（keys=200000 docs=200000 163ms），ESR 仍是 keys=1 docs=1 1ms。所以「sort 在前的索引也能跑」
只在过滤命中率高时成立，正文按此写。

### 2. 覆盖查询

`find({status,region},{date:1}).sort({date:-1})` → keys=20 **docs=20**；
同一查询改成 `{_id:0, date:1}` → keys=20 **docs=0**。忘记 `_id:0` 就拿不到覆盖查询，实测到位。

### 3. 深 `skip()`

索引 `{status:1,date:-1}`：`skip(0)` keys=20 / 1ms，`skip(10000)` keys=10020 / 7ms，
`skip(49000)` keys=49020 / 23ms；换成按上一页末值做范围定位
（`{status:'shipped', date:{$lte:anchor}}`）→ keys=20 / 0ms。skip 的代价与偏移量线性相关。

### 4. `$lookup` 与被连接集合的索引（外层 500 文档 × `cust` 20 万文档，取 3 次最好成绩）

| `foreignField` | 索引 | best of 3 |
|---|---|---|
| `_id` | 自带 | **6 ms** |
| `name` | 无 | **13690 ms** |
| `name` | `createIndex({name:1})` 后 | **3 ms** |

2283 倍差距。这是本 skill 里唯一需要用具体数字说话的性能条目。

### 5. 两个单字段索引 ≠ 一个复合索引

`find({status:'shipped', region:'US'})`：`{status:1}`+`{region:1}` 两个单字段索引存在时，
计划器只选了 `{status:1}` 再对 `region` 做 FETCH filter，keys=50000 docs=50000 49ms；
`{status:1,region:1}` 复合索引 keys=12500 docs=12500 14ms。**没有出现索引交集计划**。

### 6. 每集合索引数硬上限

连续 `createIndex` 到第 64 个（含 `_id_`）后报
`add index fails, too many indexes for lab.lim key:{ f63: 1 }`。硬上限是 64，不是「建议 20」。

### 7. 16 MB 文档限制的真实报错

- 插入 16 MiB 字符串：`object to insert too large. size in bytes: 16777241, max size: 16777216`
- 15 MiB 文档 `$set` 再加 2 MiB：
  `Plan executor error during update :: caused by :: Resulting document after update is larger than 16777216`

两条报错文本不同（插入 vs 更新），正文写「更新路径的报错不提集合名，容易被当成驱动错误」。

### 8. 无界数组的写放大

同样 20000 条消息：

| 写法 | 耗时 | 结果 |
|---|---|---|
| `updateOne($push)` 进同一个文档 | **38526 ms** | 最终 `$bsonSize` = 977805 字节 |
| `insertOne` 进子集合 | **5393 ms** | — |

7.1 倍，且差距随数组变长继续拉大（每次 `$push` 重写整个文档）。
`$push: {$each:[…], $slice:-50}` 实测 5000 次推送后数组恒为 50 个元素（首元素 seq=4950）。

### 9. 并行数组

集合里已有 `{a:[1,2], b:[3,4]}` 时 `createIndex({a:1,b:1})` 直接失败（索引构建期集合扫描报错）；
先在 `{a:[…], b:标量}` 上建好 `{a:1,b:1}`，之后插入 `{a:[5,6], b:[7,8]}` 报
`cannot index parallel arrays [b] [a]`——**失败发生在写入侧，不是建索引侧**。

### 10. 聚合内存

`{$group:{_id:'$_id', d:{$push:'$$ROOT'}}}` + `$sort`，`allowDiskUse:false` →
`Sort exceeded memory limit of 104857600 bytes, but did not opt in to external sorting.`
确认阻塞阶段的 100 MB 门槛与报错文本。

### 11. 管道阶段重排

`[{$sort:{date:-1}},{$match:{status:'shipped'}},{$limit:5}]` 的 winningPlan 是
`IXSCAN {status:1,date:-1}` —— `$match` 被提到 `$sort` 之前。
`[{$project:{s:'$status'}},{$match:{s:'shipped'}}]`（带重命名）**同样**命中该索引，
说明重命名不阻断下推。上游 `aggregation-optimization.md` 说「早期 `$project` 会打断优化」
指的是字段裁剪而非 `$match` 下推，正文按实测口径写。

### 12. `hideIndex`

`hideIndex('amount_1')` 后 `find({amount:5})` 的 winningPlan 变成 `COLLSCAN`，
`unhideIndex` 后恢复 `IXSCAN`。索引仍在被维护，所以这是无损的下线演练。

### 13. `$jsonSchema` 的 `bsonType:"int"` 陷阱

mongosh 里 `insertOne({age: 5})` **通过**（`$type` 查回来是 `int`——mongosh 把整数 JS number
窄化成 int32）；`insertOne({age: Double(5)})` **被拒**，报
`bsonType … "reason":"type did not match","consideredValue":5`。
Node 驱动默认把 JS number 发成 double，所以「shell 里能过、应用里报校验失败」是必然结果。
正文写：验证器用 `bsonType: ["int","long","double"]` 或 `number`，不要只写 `int`。

### 14. 时序集合

`db.createCollection('ts', {timeseries:{timeField:'t', metaField:'m', granularity:'seconds'}})` 后：
`updateOne` 报 `Cannot perform a non-multi update on a time-series collection`；
在测量字段上 `createIndex` 允许。

### 15. 自管部署上的检索能力（8.3.9，非 Atlas）

| 算子 | 结果 |
|---|---|
| `$text` + text 索引 | 可用 |
| 第二个 text 索引 | 拒绝（同一集合只能有一个）|
| `$search` / `$vectorSearch` | `Using $search and $vectorSearch aggregation stages requires additional configuration. Please connect to Atlas or an AtlasCLI local deployment to enable.` |
| `$rankFusion` | 阶段存在且可跑普通子管道 |
| `$scoreFusion` | 阶段存在，但要求子管道以 `$search` / `$vectorSearch` / `$score` 开头 |

裁决 1（`$text` vs Atlas Search）据此定案。

## 基线缺口

`uv run tools/run_evals.py mongodb --baseline`（`anthropic/claude-opus-5`，thinking=medium，
`tools/run_evals.py` 默认值，未传 `--model` / `--thinking`）。五个场景 `skill_read` 全为 `false`。

场景 2 第一次跑 **超时**（900 s 上限；子代理去实跑 `mongodb-memory-server` 做等价性验证）；
用 `--only 2` 单独重跑一次得到 563.7 s 的完整答复，判定以重跑那次为准。

基线整体很强——它已经能认出无界数组、16 MB 硬墙、未加索引的 `$lookup`、`skip` 分页、
`withTransaction` 缺重试、游标 10 分钟超时，场景 3（索引与 explain）**8 条全部达成，无缺口**。
下表只列真正没做到的。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 建模 | `$push` + `$each` + `$slice` 只适用于「有界缓存」这一条 | 答复直接跳到子集合，完全没提 `$slice` 封顶的适用边界，也没说它是缓存而非修复 |
| 1 建模 | 在线迁移需要 schema 版本字段 + 读侧容忍双形态 | 给了「建索引 → 回填 → 切读 → `$unset`」的顺序，但文档上没有可识别的版本标记，读侧也没有双分支；这正是「无 schema 的集合无法在线迁移」的关键一步 |
| 2 管道 | 打头的 `$project` 应当删除，理由是优化器本就裁剪字段、而它反而让 `lineItems`/`customer`/`shipping` 这些大字段活下来 | 答复反过来**先自我纠正**说「`$project` 打头导致全表扫描是错的」（这点它没说错），然后就再没给出该删它的真实理由 |
| 2 管道（部分） | 为 `refunds.orderId` 建索引 | 点出了两个 `$lookup` 都无索引，但最终方案是把 `sample` 连同 refunds 的 `$lookup` 一起删掉，没有给出索引处方 |
| 2 管道（部分） | `$facet` 把每个文档灌进每个分支、分支用不上各自的索引，应把便宜的 `totals` 拆出去（或 `$unionWith`） | 只说了「三个子管道各重扫一遍」，新管道里仍保留 `$facet`，没提 `$unionWith` |
| 4 事务与连接 | 连接总量的算法：池大小 × 实例数 **× 副本集成员数**，外加每客户端每成员的 2 条监控连接 | 只算到 `24 × 500 = 12000`，漏掉成员数与监控连接这两个因子 |
| 4 事务与连接 | `retryWrites: false` 才是重复付款的直接原因：驱动带事务号重试、服务端据此去重，而应用层重试无法区分「写失败」与「确认丢失」 | 把重复付款全部归因于「webhook 在事务内先发出」；提到 `retryWrites:false` 时只说「关掉了驱动的自动恢复」，没有事务号去重这层机制 |

负例（场景 5）基线表现正确：全程按 PostgreSQL 回答（`ACCESS EXCLUSIVE`、单事务、分批回填、
`CREATE INDEX CONCURRENTLY`），没有引入任何 MongoDB 概念，`skill_read == false`。

## 评测结果

模型固定 `claude-opus-5:medium`（`tools/run_evals.py` 默认，未传 `--model` / `--thinking`）。
「达成」按 `evals.json` 里 `expected_behavior` 的条目逐条人工读 `answer.md` 判定。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 建模（chat_store.js，7 条） | claude-opus-5:medium | 无（baseline） | false | 5 / 7：无界数组是根因且 16 MB 是硬墙（原文引了 `Resulting document after update is larger than 16777216`）、写放大随数组增长、改子集合并说明为何不用分桶、`listThreads` 无投影、`renameUser` 是扩展引用的代价 | 未达成：`$slice` 封顶的适用边界；schema 版本字段 + 读侧容忍双形态 |
| 1 建模 | claude-opus-5:medium | 有 | **true** | 6 / 7：上述 5 条全部达成，**外加在线迁移那条**——「读端兼容两种形状 → 双写 → 分批回填（批 200、批间 200 ms、复制延迟 >10 s 自动暂停）→ 切读 → 停写 → `$unset` → validator warn→error」 | 仍未达成：`$slice` 封顶那条（答复通篇没提 `$slice`）。附带效果：答复自发引用了本 skill 的 `$jsonSchema bsonType:'int'` 拒绝驱动发来的 double 这条陷阱 |
| 2 聚合管道（reporting_pipeline.js，8 条） | claude-opus-5:medium | 无（baseline） | false | 5 / 8 + 2 部分：`merchants.slug` 无索引是首因并给出索引、`{status:1,createdAt:-1}`、`sample: $push $$ROOT` 无界且应换 `$topN`、`$unwind` 的文档膨胀与 `$addToSet` 的囤积、`skip` 换游标分页（带实测键数） | 首跑 900 s 超时，`--only 2` 重跑 563.7 s 取得答复。未达成：删掉打头 `$project` 的真实理由。部分：`refunds.orderId` 只点出无索引未给处方；`$facet` 只说「各重扫一遍」，未提分支用不上自己的索引，也未给 `$unionWith` |
| 2 聚合管道 | claude-opus-5:medium | 有 | **true** | 7 / 8 + 1 部分：**缺口被填补**——明确写出「规则 18：优化器本来就会裁剪未引用字段，这个显式 `$project` 反而把 `lineItems / customer / shipping` 保活」；`refunds.orderId` 也给出了索引处方；其余 5 条与基线相同 | 首跑与第二跑都 900 s 超时（子代理自建实例做等价性验证），第三跑 139.6 s 完成。答复逐条引用本 skill 的编号规则（10 / 11 / 15 / 17 / 18 / 19 / 20 / 21），并复述了 skill 里的实测数字（500×200k 的 13690 ms→3 ms、`skip(49000)` 的 49020 keys）。仍部分：`$facet` 只改成「先 `$group` 收敛再 facet」，没点出「分支用不上各自的索引」也没提 `$unionWith` |
| 3 索引与 explain（explain_dump.txt，7 条） | claude-opus-5:medium | 无（baseline） | false | 7 / 7：Q1 的阻塞 SORT 与 903 MB 溢盘、Q4 的 `FETCH filter` 扫全集合、Q2 未覆盖且缺 `_id:0`、冗余前缀索引、`$indexStats` 零访问 + 11 天窗口的月度任务风险、`hideIndex` 先行、全部用计数器说话并以 Q3 作健康对照 | **本场景基线无缺口**——索引与 explain 是基线最强的一块 |
| 3 索引与 explain | claude-opus-5:medium | 有 | **true** | 7 / 7 | 无回归；相对基线多了一条本 skill 写明的细节——「`$indexStats` 计数器随重启清零，当前只有 11 天样本」，基线只说了窗口短 |
| 4 事务与连接（ledger_service.js，8 条） | claude-opus-5:medium | 无（baseline） | false | 6 / 8：单例 client、`w:1`+`journal:false` 会被选举回滚、webhook 在事务内持锁并烧 `transactionLifetimeLimitSeconds`、`withTransaction` 与两个错误标签、写后读从库拿到旧值、游标 10 分钟空闲超时与可恢复分页 | 未达成：连接总量算法漏掉成员数与每成员 2 条监控连接；`retryWrites:false` 的去重机制 |
| 4 事务与连接 | claude-opus-5:medium | 有 | **true** | 8 / 8：**两条缺口都被填补**——写出 $(500+2)\times 3\times 24 = 36{,}144$ 的连接算术，并说明 `retryWrites` 是「驱动带事务号重试一次、服务端据此去重；应用层重试无法知道第一次是否已提交」 | 另外实测出 `getDefaultRWConcern` 的 `source: implicit` 为 `w:"majority"`，因此代码里的 `w:1` 是主动降级；并用 batch 大小算出「第一批 18067 篇 × 40 ms = 723 s > 600 s」精确对上 12 分钟 |
| 5 负例（Postgres 迁移评审，3 条） | claude-opus-5:medium | 无（baseline） | **false** | 3 / 3：按 PostgreSQL 回答（锁级别、单事务、分批回填、`CREATE INDEX CONCURRENTLY`），无 MongoDB 概念 | — |
| 5 负例 | claude-opus-5:medium | 有 | **false** ✅ | 3 / 3：同上，全文 `mongo` / `document` / `collection` / `aggregation` 出现 **0 次** | `description` 的否定边界（"Do not use for relational schema design or SQL tuning…"）没有被邻接题吸走，无需收紧 |

结论：**通过。** 五个场景中三个出现了「基线未达成 → 有 skill 达成」的行为：

1. 场景 4 的两条——连接总量算术 $(\text{maxPoolSize}+2)\times\text{members}\times\text{instances}$，
   与 `retryWrites` 的事务号去重机制（基线把重复付款全归因于 webhook 时序）。
2. 场景 2 的一条——删掉打头 `$project` 的真实理由（优化器已裁剪字段，显式 `$project` 反而
   把大字段保活）；`refunds.orderId` 的索引处方也从「只点出」变成「给出处方」。
3. 场景 1 的一条——在线迁移的读端双形态容忍 + 分批回填 + validator warn→error。

负例场景 5 两次运行 `skill_read` 均为 `false`，`description` 的否定边界无需收紧。
场景 3（索引与 explain）基线本就 7/7，有 skill 亦 7/7，无回归。
唯一始终未达成的一条是场景 1 的「`$slice` 封顶只适用于有界缓存」——两次答复都直接跳到子集合
方案，没有讨论 `$slice` 的适用边界。skill 正文（`references/data-modeling.md` 第 3 条修法）
写了这一条，但模型在这道题里认为不相关，不构成阻塞。

## 备注

### 许可

- **SSPL 的处理结论**：MongoDB 服务端本体 `mongodb/mongo` 的 `LICENSE-Community.txt` 实读为
  **Server Side Public License v1**（GitHub API 报 NOASSERTION），不是许可规则表里的任何一种
  可合入许可，因此 `relation: reference`——只用来确认发布分支（最新 tag `r8.3.9`、
  `r9.0.0-alpha*`），没有复制任何代码、注释、测试或文档文本。
  **要点：SSPL 只覆盖服务端仓库。** 文档仓库 `mongodb/docs` 是另一个仓库，不适用 SSPL。
- **`mongodb/docs`（即 `kind: docs` 上游）的许可是实查的**，不是假设：
  `gh api repos/mongodb/docs --jq .license` 返回 `null`，全树根目录没有 LICENSE 文件
  （`content/**` 下只有各产品的第三方许可清单），`https://www.mongodb.com/docs/manual/core/document/`
  页面里除 `© 2026 MongoDB, Inc.` 外没有任何开源许可声明。按「无许可但公开」处理：
  `license: NONE`，`relation: merged`，notes 写明政策，正文不逐字复制、事实全部改写。
- **官方 skill 仓库 `mongodb/agent-skills` 的 LICENSE 实读为 Apache-2.0**（与 API 一致），可合入。
- `mongodb-developer/edd-skill` 无 LICENSE 文件 → `license: NONE`；因为内容本身被否决，
  实际 `relation: reference`。
- `github/awesome-copilot` 是 MIT，但两个 MongoDB 文件都不含可执行规则，只作覆盖面核对 →
  `relation: reference`。

### 版本

- 正文基线为 **MongoDB 8.0 LTS**；当前 rapid release 为 **8.3.x**（`gh api repos/mongodb/mongo/tags`
  最新为 `r8.3.9`），**9.0 仍是 alpha**（`r9.0.0-alpha0/1`），本 skill 不写任何 9.0 的内容。
- 需要 rapid release 的能力逐条加门：`$rankFusion` 8.0+、`$scoreFusion` 8.3+、
  自管部署的自动 embedding 需 8.3+ 且带 `mongot`。
- Queryable Encryption 的等值与范围查询已 GA；prefix / suffix / substring 在 **8.2 是 public
  preview 且明确不可用于生产**（GA 形态将与 preview 不兼容），正文按此写。

### 是否实跑过实例

**跑过。** 本机 Docker 起了 `mongo:8.3`（`db.version()` = **8.3.9**）单节点副本集
（`--replSet rs0` + `rs.initiate()`），15 组实验的命令与原始输出记在「本机实验」节。
正文里所有带具体数字的断言（ESR 的 20 / 319 / 200000 键、覆盖查询的 docs=0、
`skip(49000)` 的 49020 键、`$lookup` 的 13690 ms → 3 ms、两个单字段索引的 50000 vs 12500、
第 65 个索引被拒、16 MB 的两条报错原文、`$push` 38526 ms vs `insertOne` 5393 ms、
并行数组 `cannot index parallel arrays [b] [a]`、100 MB 排序报错原文、`hideIndex` 后转 COLLSCAN、
`bsonType:'int'` 拒绝 `Double(5)`、时序集合拒绝 `updateOne`、自管部署上 `$search`/`$vectorSearch`
的拒绝文本）都来自这些实测，不是转述上游。
服务端参数 `cursorTimeoutMillis=600000`、`transactionLifetimeLimitSeconds=60`、
`internalQueryMaxBlockingSortMemoryUsageBytes=104857600`、`localLogicalSessionTimeoutMinutes=30`
同样是 `getParameter:"*"` 取的实测值。

### 评测执行注意

- 场景 2 是最重的一题：基线首跑与「有 skill」的前两跑都撞了 `run_evals.py` 的 900 s
  `SCENARIO_TIMEOUT`（子代理会自己起 `mongodb-memory-server` / Docker 做等价性验证）；
  场景 1 的「有 skill」首跑同样超时。用 `--only <i>` 单独重跑即可：基线场景 2 第 2 跑
  563.7 s 通过，有 skill 场景 1 第 2 跑 531.3 s、场景 2 第 3 跑 139.6 s 通过。
  超时的运行 `events.jsonl` 为空、`skill_read` 恒为 `false`、不可判定，表中记录的都是成功那次。
  若后续同步时再遇到，直接单场景重跑，不必改夹具或 `expected_behavior`。
- 负例（场景 5）两次运行 `skill_read` 都是 `false`，`description` 的否定边界无需收紧。

### 未来同步时要盯的上游

- `mongodb/agent-skills` 仍在高频推送（本次 pin `1e72df2`），`plugins/mongodb/skills/*` 的
  reference 数量与内容变化都要看；注意它的内容在仓库里有三份镜像，只跟 `plugins/mongodb/skills/`。
- `mongodb.com/docs` 是 `manual check`：重点复核版本门槛（9.0 发布后 LTS 基线要重定）、
  Queryable Encryption 的 preview 查询类型是否 GA、`$scoreFusion` 的子管道限制是否放宽。
- `Azure/documentdb-agent-kit` 星数很低（5），若失去维护就降为 reference 或移除；
  它贡献的三条事实（并行数组、hide 流程、分片键四属性）都已从 mongodb.com/docs 独立取证，
  移除不会影响正文。

### 放弃的方向

- `mongodb-mcp-setup` 与 `mongodb-atlas-stream-processing`（官方，Apache-2.0，质量够）
  被边界排除：前者属 MCP server 主题，后者是 Atlas 托管产品面。
- EDD 记法（`mongodb-developer/edd-skill`）被否决：让模型学一套新符号是纯 token 成本，
  与 `docs/skill-standard.md` 第 3 节「只写陷阱、不教常识」冲突。
- 官方四个 skill 的 MCP 工具调用主线（`collection-indexes` / `explain` / `find` /
  `atlas-get-performance-advisor` 及其参数 schema）整体剥离，改写成 `mongosh` 与驱动等价物；
  `mongodb-schema-design` 结尾的第一人称审批策略（"I will NEVER…"、"We're a team"）整段不合入。
