# cloudflare 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`"Cloudflare Workers agent skill SKILL.md github wrangler durable objects"`
  - `gh api search/repositories?q=cloudflare+workers+claude+skill&sort=stars`
  - 官方组织仓库：`cloudflare/skills`、`cloudflare/cloudflare-docs`、`cloudflare/workers-sdk`、`cloudflare/computer`
  - 第三方 skill 集合：`jezweb/claude-skills`、`secondsky/claude-skills`、`openai/plugins`、
    `xiaoyuboi/cloudflare-tunnel-skill`、`null-shot/cloudflare-skills`、`straticus1/claude-cloudflare-skill`
  - `github/awesome-copilot`：`gh api .../git/trees/main?recursive=1` 过滤 `cloudflare|wrangler|workers` → **零命中**，本轮无候选
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- 许可复核方式：`gh api repos/<o>/<r>/contents/LICENSE --jq .content | base64 -d`，**实读正文**，不采信 `license.spdx_id`

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cloudflare/skills · `skills/workers-best-practices` | https://github.com/cloudflare/skills | 2813 | 2026-09-08 | Apache-2.0（实读 LICENSE 正文确认） | Workers 运行时反模式、配置、可观测 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方厂商；13 条反模式表全部可证伪（`ctx` 解构丢失 receiver、模块级可变状态、floating promise、`passThroughOnException` 失败开放、手写 `Env`）；抽查 3 条对官方文档全对 |
| 2 | cloudflare/skills · `skills/durable-objects` | 同上 | 2813 | 2026-09-08 | Apache-2.0 | DO 建模、storage、alarms、RPC、迁移 | 3 | 3 | 3 | 2 | 2 | 13 | INCLUDE | 唯一把「一个协调原子一个 DO」「先落盘再改内存」「一个 DO 一个 alarm」写成规则的上游；扣 1 分：wrangler 配置仍只教 legacy `migrations`，未提 `exports`（裁决 1） |
| 3 | cloudflare/skills · `skills/wrangler` | 同上 | 2813 | 2026-09-08 | Apache-2.0 | wrangler 配置/环境/密钥/部署与回滚 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 52 行全是判断而非命令清单：环境继承、dashboard 漂移会被 wrangler 覆盖、`secret put` 即部署、回滚不回滚数据、`CLOUDFLARE_ENV` 在 Vite 插件下的选择时机 |
| 4 | cloudflare/skills · `skills/cloudflare` | 同上 | 2813 | 2026-09-08 | Apache-2.0 | 50+ 产品的 `README/api/configuration/gotchas/patterns` 四件套 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（作覆盖面与 gotcha 取材） | 是一棵 250+ 文件的产品参考树，单文件偏 API 说明书（具体性 2）；本 skill 只取 KV/R2/D1/Queues/DO-storage/static-assets/tunnel/tail-workers/miniflare/bindings 几支的 gotcha |
| 5 | cloudflare/skills · `skills/cloudflare-one` | 同上 | 2813 | 2026-09-08 | Apache-2.0 | Access/Gateway/WARP/Tunnel/DLP/CASB | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | Zero Trust 侧最强上游：Access 默认拒绝、enrollment rule 其实是 `warp` 型 Access 应用、split tunnel include/exclude 选择表、`dns.domains` vs `dns.fqdn`、Do Not Inspect 先于 Block |
| 6 | cloudflare/skills · `skills/nextjs-on-cloudflare` | 同上 | 2813 | 2026-09-08 | Apache-2.0 | Next.js on Workers 适配器 | 3 | 3 | 1 | 3 | 2 | 12 | MAYBE → 仅 reference | 33 行路由文件，且内容主体是 Next.js 本身（按 Contract 归 `react`）；只取「用 OpenNext 适配器 + Workers static assets，不要 Pages」这一句边界 |
| 7 | cloudflare/skills · `skills/agents-sdk` | 同上 | 2813 | 2026-09-08 | Apache-2.0 | Agents SDK、MCP、codemode、voice | 3 | 3 | 3 | 3 | 2 | 14 | REJECT（越界） | 质量很高，但主题是 AI agent 框架；`ai-engineering` / `mcp-server` 两个 skill 本库尚不存在，不能转交也不该并入本 skill。只借用其 DO-as-agent 的状态/调度心智做交叉校验 |
| 8 | cloudflare/cloudflare-docs（developers.cloudflare.com） | https://github.com/cloudflare/cloudflare-docs | 5208 | 2026-09-11 | **CC-BY-4.0（实读 LICENSE：Attribution 4.0 International）** | 全平台官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | 本 skill 所有限额、版本门、默认值的最终事实来源。许可实读结论见「备注」——与波次 5 的 redis.io/elastic/hashicorp 不同，Cloudflare 文档仓是真正的 CC-BY-4.0，可 merged |
| 9 | cloudflare/workers-sdk · `packages/wrangler` | https://github.com/cloudflare/workers-sdk | 4524 | 2026-09-10 | Apache-2.0 | wrangler 源码、`config-schema.json`、CHANGELOG | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 版本门的唯一可靠来源：`exports` 声明式 DO 生命周期落在 **wrangler 4.107.0**（CHANGELOG #14382）；`config-schema.json` 给出 `exports`/`migrations` 互斥的 schema 级说明 |
| 10 | jezweb/claude-skills · `plugins/cloudflare` | https://github.com/jezweb/claude-skills | 1000 | 2026-07-02 | MIT（实读） | Worker 脚手架、Hono、D1+Drizzle、Vite 插件 | 1 | 1 | 2 | 2 | 2 | 8 | INCLUDE（薄） | 社区，2 月未推送。可用的是脚手架期的具体坑：Wrangler 4.45+ 未填 id 会自动 provision、Vite 插件下 API 路由与 static assets 冲突、`.dev.vars` 模板。Hono/Drizzle/React/Tailwind 部分按 Contract 剥离 |
| 11 | secondsky/claude-skills · `plugins/cloudflare-*`（33 个 skill） | https://github.com/secondsky/claude-skills | 217 | 2026-09-09 | MIT（实读） | KV/R2/D1/Queues/DO/Workflows/Zero Trust/Workers 十支 | 1 | 3 | 2 | 1 | 2 | 9 | MAYBE → 主要作覆盖面清单 | 覆盖面最全，但**正确性只有 1**：`cloudflare-kv` 写着「Writes: 1000/sec per key」，官方是**同一 key 1 次/秒**（裁决 2）；frontmatter 塞满 `production_tested`/`token_savings` 之类非规范字段。事实一律改从官方文档取证 |
| 12 | xiaoyuboi/cloudflare-tunnel-skill | https://github.com/xiaoyuboi/cloudflare-tunnel-skill | 215 | 2026-06-11 | MIT（实读） | cloudflared quick/named tunnel | 1 | 1 | 3 | 3 | 2 | 10 | INCLUDE（窄） | 单主题但全是可执行判断：quick 与 named 的选择条件、「拿到 URL 不等于隧道可用，要同时看到 `Registered tunnel connection`」、把 200/301/302/304/401/403 都算作本地服务可达、DoH 兜底解析新 trycloudflare 主机名 |
| 13 | openai/plugins · `plugins/cloudflare` | https://github.com/openai/plugins | 6392 | 2026-09-08 | **无 LICENSE（API `license: null`）**；`skills/agents-sdk/LICENSE.txt` 为 Cloudflare 自己的 Apache-2.0 | Agents SDK / MCP server on Cloudflare | 2 | 3 | 3 | 3 | 0 | 11 | REJECT（越界 + 许可） | 内容是 cloudflare/skills `agents-sdk` 的再分发，主题同第 7 行越界；仓库级无许可，只有子目录自带 Apache-2.0。无独立贡献，不入 SOURCES |
| 14 | cloudflare/computer · `.agents/skills/cloudflare` | https://github.com/cloudflare/computer | 9144 | 2026-09-10 | MIT（实读） | 指向 cloudflare/skills 的索引 | 3 | 3 | 1 | 3 | 2 | 12 | MAYBE → 仅 reference | 74 行纯路由表，本身不含平台事实。价值在于**官方自己在真实产品仓里的取舍**：把 `durable-objects`/`workers-best-practices`/`agents-sdk` 列为三大主 skill，并明确「平台指南不 vendor 进仓库，保持跟随上游」——用于校验本 skill 的 topic router 权重 |
| 15 | null-shot/cloudflare-skills | https://github.com/null-shot/cloudflare-skills | 0 | 2026-01-18 | Apache-2.0 | Workers/DO skill 集 | 0 | 1 | 1 | – | 2 | ≤4 | REJECT | 0 star、8 个月未推送、匿名维护者；与 cloudflare/skills 主题完全重叠且更旧，无任何独有事实 |
| 16 | straticus1/claude-cloudflare-skill | https://github.com/straticus1/claude-cloudflare-skill | 1 | 2025-12-23 | MIT | Cloudflare API 包装 | 0 | 0 | 1 | – | 2 | ≤4 | REJECT | 1 star、近 9 个月未推送（>6 月按量表直接 REJECT），内容是 REST API 调用示例；本 skill 的立场恰好相反——Worker 内有 binding 就不要走 REST API |
| 17 | github/awesome-copilot | https://github.com/github/awesome-copilot | – | – | MIT | – | – | – | – | – | – | – | REJECT（无命中） | 递归列出 `skills/` 与 `instructions/` 全表后按 `cloudflare|wrangler|workers` 过滤为零命中；该仓本轮对 Cloudflare 无覆盖，留行以免后续批次重查 |

## 深度审查

### cloudflare/skills `workers-best-practices`（60 行 SKILL.md + 3 个 reference，共 529 行）

结构是「路由表 + 反模式表 + Validation」，frontmatter 只有 `name`/`description`，无需剥离 agent 专属字段。最值得合入的是它的**反模式→后果**成对写法，而不是 API 列表：`const { waitUntil } = ctx` 丢 receiver 抛 `Illegal invocation`、模块级可变状态同时导致跨请求泄漏与 `Cannot perform I/O on behalf of a different request`、`implements` 代替 `extends` 会丢 `this.ctx`/`this.env`、序列化边界（Queues `contentType` / DO SQL 绑定参数 / WebSocket `send()`）不能用一条规则一概而论。

它有一条明确过时的事实：`runtime-patterns.md` 写「10ms CPU（Bundled）或 30s（Standard/Unbound）」。Bundled/Unbound 计费模型早已退役，现行是 Free 固定 10 ms、Paid 默认 30 s 且可用 `limits.cpu_ms` 提到 300000 ms（裁决 3）。

它的通篇基调是「**优先检索而非依赖预训练**」，并把 `wrangler --help` 与 `node_modules/wrangler/config-schema.json` 当作版本真相。这一条被本 skill 完整继承并写成 Core rule。

### cloudflare/skills `durable-objects`（175 行 + 388 行 reference）

唯一把 DO 建模写成规则的上游：一个协调原子（房间/对局/用户）一个 DO 而不是一个全局 DO；`getByName()` 做确定性路由；`blockConcurrencyWhile()` 只用于构造期建表，不能每请求用、不能跨 `fetch()` 持有；先写 storage 再更新内存缓存；一个 DO 一个 alarm，`setAlarm()` 覆盖既有。

缺陷是 wrangler 配置部分：`migrations` + `new_sqlite_classes` 是 legacy 流程，而现行是声明式 `exports`（裁决 1）。`references/workers.md` 里还混了大量与 DO 无关的通用 Worker 代码（CORS、Zod 校验、超时包装），属于本 skill 不该复制的模型已知常识。

### cloudflare/skills `wrangler`（52 行）

密度最高的一份。它不列命令，而列**会出事的判断**：非继承键必须每个环境重写（「默认配置能跑不代表 staging 配好了」）；dashboard 上的改动会被 wrangler 覆盖，部署前要先对账；省略资源 id 会触发自动 provision；`wrangler secret put` 会创建版本并**立即部署**，需要分阶段时用 `wrangler versions secret`；回滚只回代码，连接的资源与数据不回滚；Vite 插件下环境在 dev/build 时用 `CLOUDFLARE_ENV` 选，部署时再指定环境不会重新定向已 flatten 的配置。这些全部合入。

### cloudflare/skills `cloudflare-one`（178 行）

Zero Trust 侧的取材源。核心判断：Access 管应用授权、Gateway 管流量检查，两者职责不同；Access 策略默认拒绝，「有路由没 Allow 策略」仍然不通；enrollment rule 实际上是 `warp` 类型的 Access 应用，排障要去 Access 而不是 Devices 找；无人值守设备用 service token 入网，身份是 `non_identity@<team>.cloudflareaccess.com`，因此针对 IdP 组的 device profile 永远匹配不上；split tunnel 的 include/exclude 是 per-profile 而非 per-entry，且必须与 tunnel route 双向对齐，否则一侧黑洞；MDM 文件覆盖 dashboard 配置；`dns.domains` 匹配域及子域、`dns.fqdn` 精确匹配；HTTP Do Not Inspect 先于 Allow/Block/Isolate 生效；生成的 IPsec PSK 只返回一次。

### cloudflare/skills `cloudflare`（250+ 文件参考树）

单个 `gotchas.md` 的信噪比高于 `api.md`。取用的是 KV/R2/D1/Queues/do-storage/static-assets/tunnel/tail-workers/miniflare/bindings 这几支的 gotcha 与 configuration；其余（Stream、Zaraz、RealtimeKit、Spectrum、Turnstile、WAF、Bot Management、AI Gateway…）属于产品面，与本 skill 的「构建与运维 Workers 应用」范围不符，且多数会随产品变动腐化。

### secondsky/claude-skills（33 个 Cloudflare skill）

覆盖面是所有候选里最广的，把 KV/R2/D1/Queues/DO/Workflows/Hyperdrive/Vectorize/Browser Rendering/Cron/Zero Trust 各写成独立 skill。但它的定位是「产品 API 速查 + Always Do / Never Do 十条」，`last_verified: 2025-12-27`，且抽查即发现硬错（KV 同 key 写入速率、Queues 保留期）。frontmatter 含 `production_tested`、`token_savings`、`errors_prevented`、`keywords` 等非规范字段，按标准第 1.2 节必须剥离。**结论：只用它的主题清单确认本 skill 的覆盖面没有漏项，每条事实重新从官方文档取证。**

### 与其他候选的重叠

第 1–7 行是同一仓库的 7 个 skill，互不重叠（Cloudflare 自己做了切分）。第 13、14 行都是 cloudflare/skills 的再分发或索引，无独立事实。第 11 行与第 4 行在产品面上高度重叠，第 4 行权威且更新，冲突一律取第 4 行并回官方文档复核。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | Durable Object 类生命周期怎么声明 | cloudflare/skills `durable-objects` 与 secondsky：`migrations` 数组 + `new_sqlite_classes` / `new_classes`。官方文档 `durable-objects/reference/durable-objects-migrations/` 标题已改为「Durable Object class exports」，称 `migrations` 为 legacy | 正文只写声明式 `exports`（`state: created/deleted/renamed/transferred/expecting-transfer`），并标 `(Wrangler 4.107+)`；legacy `migrations` 只在 `## Old patterns` 折叠块里出现一句 | 官方文档 > 官方 skill（同厂商取更新）。版本门取自 `cloudflare/workers-sdk` `packages/wrangler/CHANGELOG.md` 4.107.0 条目（PR #14382）。本机 wrangler 4.131.0 实测两者同时出现即报 `` `migrations` and `exports` are mutually exclusive `` |
| 2 | Workers KV 同一 key 的写入速率 | secondsky `cloudflare-kv`：「Writes: 1000/sec per key」，并在 Never Do 里写「Never exceed rate limits (1000 writes/second)」 | 官方限额表：**Writes to same key = 1 per second**（Free 与 Paid 相同）。正文按 1 次/秒写，并据此断言「KV 做热点计数器不可行」 | 官方文档 > 社区。`kv/platform/limits/`（Last updated 2026-04-21）。差 3 个数量级，直接决定「KV 能不能做配额计数」这个架构结论 |
| 3 | Workers CPU 时间上限 | cloudflare/skills `runtime-patterns.md`：「10ms CPU limit (Bundled) or 30s (Standard/Unbound)」 | 正文写：Free 固定 10 ms；Paid 默认 30 s（30000 ms），可用 `limits.cpu_ms` 提到 5 min（300000 ms）；Cron < 1 小时间隔 30 s、≥ 1 小时 15 min。不使用 Bundled/Unbound 这两个已退役的计费模型名 | 官方文档 > 官方 skill（更新 > 更旧）。`workers/platform/limits/`（Last updated 2026-09-05） |
| 4 | Queues 消息保留期与消费者默认值 | 社区材料（含 secondsky `cloudflare-queues`）把 4 天写成「保留期」，不区分默认与上限，也不提 Free 的差异 | 正文写：默认 345600 s（4 天），可配置 60 s–**14 天**（`wrangler queues update --message-retention-period-secs`），Workers Free 固定 24 小时不可配；消费者默认 `max_batch_size = 10`、`max_batch_timeout = 5` s、`max_retries = 3`，未配 `dead_letter_queue` 时超过重试次数的消息**被丢弃** | `queues/platform/limits/` 与 `queues/configuration/configure-queues/`（均 2026-04-21）。把默认值当上限会让人以为保留期不可调，把重试次数用尽的行为当成「进死信队列」则会直接丢消息 |
| 5 | Workers 单元测试用哪个包 | 全部上游 skill（cloudflare/skills、secondsky、jezweb）：`@cloudflare/vitest-pool-workers` | 正文写 `@cloudflare/vitest-plugin`（v1，替代 `@cloudflare/vitest-pool-workers`，API 与 Vitest 配置不变），并给出官方 codemod `npx @cloudflare/codemods vitest:pool-workers-to-vitest-plugin`；集成测试指向 `createTestHarness()` | 官方文档 `workers/testing/vitest-integration/migration-guides/migrate-to-vitest-plugin/`（2026-08-20）与 `workers/testing/`（2026-07-27）。三家上游一致但一致地过时 |
| 6 | Pages 与 Workers 的路由默认值 | jezweb 与社区材料按 Pages 心智写（Functions 先于静态资源） | 正文写：Pages 默认 Functions 先跑；**Workers 默认静态资源先于 Worker 脚本**，要先跑脚本必须显式 `assets.run_worker_first`；`not_found_handling` 也必须显式，Workers 不像 Pages 从 `index.html`/`404.html` 推断 | `workers/static-assets/migration-guides/migrate-from-pages/`（2026-08-14）。方向搞反会让认证中间件静默失效 |
| 7 | `_headers` / `_redirects` 迁移后是否继续生效 | 所有上游都把它当成「Pages 与 Workers 都支持」而不加限定 | 正文写：两者在 Workers static assets 上受支持，但**不作用于 Worker 代码生成的响应**；SSR 或 `run_worker_first` 场景下安全头与跳转必须在 Worker 内自己加 | `workers/static-assets/headers/` 与 `.../redirects/`（均 2026-08-25）的 Caution 段 |
| 8 | 新建 DO 用哪个 storage backend | cloudflare/skills 的 `references/workers.md` 示例里既有 `new_sqlite_classes` 也有 `new_classes` | 正文只写 SQLite（`storage: "sqlite"`）：没有既存 KV-backed namespace 的账户已无法新建 KV backend，Free 计划只有 SQLite | `durable-objects/reference/durable-objects-migrations/` 与 `durable-objects/platform/limits/`（2026-06-01） |
| 9 | Tail Worker 还是 OTel 导出 | 社区材料一律推 Tail Worker 转发日志到第三方 | 正文写：要把日志/追踪送到 Sentry/Grafana/Honeycomb，用 Workers 的 OTel 导出（批量发送）；Tail Worker 是需要自定义处理时的高级选项。OTel 埋点与流水线本身按 Contract 归 `observability` | `workers/observability/logs/tail-workers/`（2026-06-25）自己给出的指引 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| cloudflare-skills | cloudflare/skills（`workers-best-practices`、`durable-objects`、`wrangler`、`cloudflare`、`cloudflare-one`、`nextjs-on-cloudflare`） | merged | 骨干：Workers 反模式与后果配对、DO 建模与并发规则、wrangler 的判断型规则、Zero Trust 的策略语义与 split tunnel 对齐规则、「优先检索而非依赖预训练」的基调 |
| cloudflare-docs | developers.cloudflare.com（cloudflare/cloudflare-docs, CC-BY-4.0） | merged | 全部限额、默认值、版本门与行为事实的最终来源；`exports` 生命周期语义、静态资源路由与 `_headers`/`_redirects` 边界、KV 一致性模型、Queues/D1/R2/DO 限额、版本与回滚语义 |
| workers-sdk | cloudflare/workers-sdk（`packages/wrangler`） | merged | `exports` 落地版本（wrangler 4.107.0）、`config-schema.json` 的 `exports`/`migrations` 互斥说明与 `DurableObjectExport` 各 `state` 的必填字段 |
| xiaoyuboi-tunnel | xiaoyuboi/cloudflare-tunnel-skill | merged | quick vs named tunnel 的选择条件与验证门：拿到 `trycloudflare.com` URL 不等于隧道可用，必须同时看到 `Registered tunnel connection`；本地服务可达性判定把 401/403 也算通 |
| jezweb-cloudflare | jezweb/claude-skills（`plugins/cloudflare`） | merged | 脚手架期的两个具体坑：省略资源 id 会触发 Wrangler 自动 provision（必须显式命名）、Vite 插件下 API 路由与 static assets 的 fallback 冲突 |
| secondsky-cloudflare | secondsky/claude-skills（`plugins/cloudflare-*`） | reference | 只用作覆盖面清单，确认 KV/R2/D1/Queues/DO/Workflows/Hyperdrive/Zero Trust 无漏项；其事实因裁决 2、4 不可信，未复制任何内容 |
| cloudflare-computer | cloudflare/computer（`.agents/skills/cloudflare`） | reference | 只读，用于校验 topic router 权重：官方在真实产品仓里把 DO、Workers 最佳实践列为首要，且平台指南不 vendor 而跟随上游 |
| cf-nextjs | cloudflare/skills（`nextjs-on-cloudflare`） | reference | 只读一句边界：Next.js on Cloudflare 走 Workers static assets + 适配器，不走 Pages。Next.js 本身归 `react` |

## 基线缺口

无 skill（`uv run tools/run_evals.py cloudflare --baseline`，claude-opus-5 · medium）时，各场景未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 worker-review | **#3 CPU 时间数字**：答案指出 `cpu_ms = 50` 会触发 1102，但从未给出正确数字（Free 固定 10 ms / Paid 默认 30000 ms / 上限 300000 ms），因此无法判断 50 是不是一个荒谬的值 | 其余 7 条达成，且本机真跑了 wrangler 4.131.0 复现 `Illegal invocation` 与全局缓存串号。基线在这个场景上很强 |
| 1 worker-review | **#5 部分**：提到用 `crypto.subtle.timingSafeEqual`，但没说必须先哈希成等长再比（该 API 对不等长输入会抛错，直接传两个 token 是行不通的） | 只差「先摘要再比」这一步 |
| 1 worker-review | **#8 部分**：把 `DB: any` 归入「卫生问题」，未给出 `wrangler types` 生成 `worker-configuration.d.ts` 这个修法 | `passThroughOnException` 与 fail-open 后果达成 |
| 2 kv-counter | **#2 KV 同 key 写入速率**：全文没有出现「同一 key 1 次/秒」这个限额，只说「无原子 read-modify-write」。少了这条就无法解释为什么连「加锁重试」都救不了 | 这是裁决 2 对应的缺口 |
| 2 kv-counter | **#5 DO 容量事实**：没有提到单个 DO 约 1000 请求/秒的软上限与 `overloaded` 错误，因此「为什么分片键必须是 team」只是直觉而非事实 | |
| 2 kv-counter | **#6 本地为什么复现不出来**：答案归因为「本地 dev 单进程近乎无并发」。真实机制是本地 KV（`.wrangler/state` 下的 SQLite）**读己之写一致**，所以最终一致缺陷在本地根本不存在——归因错了，导致「加并发压测就能在本地复现」的错误推论 | 本机实测第 5 条正是这一点 |
| 2 kv-counter | **#8 部分**：正确地把 `plan:` 读留在 KV，但没提 `cacheTtl` 默认 60 秒、可上调 | |
| 3 do-lifecycle | **#3 `exports` 机制与版本门**：答案主动选择留在 legacy `migrations` + `renamed_classes`，全文没有 `state: "renamed"` / `renamed_to`，也没有任何 Wrangler 版本门。它对「切过去不可逆」「`versions upload` 不应用生命周期变更」「回滚不能跨生命周期变更」的判断是准确的，但缺了现行机制本身 | 其余 7 条达成（包括三次部署改名与 alarm 幂等），基线在这个场景上也很强 |
| 4 pages-migration | **#5**：手写重写了 middleware，但没提 `wrangler pages functions build --outdir=`，也没说 `_routes.json` 在 Workers 上没有对应物、由 `run_worker_first` 取代 | |
| 4 pages-migration | **#6**：`.assetsignore` 一次都没出现（`_worker.js`、`node_modules`、`.git` 的排除方式） | |
| 4 pages-migration | **#7**：静态资源限额（Free 20,000 / Paid 100,000 文件每版本、单文件 25 MiB）完全缺失 | 这是会让部署直接失败的门 |
| 4 pages-migration | **#8**：迁移里没有开 observability，也没有「`observability.enabled` 不会连带打开 traces，必须另设 `observability.traces.enabled`」这条 | |
| 5 负例 | 无缺口 | 4 条全部达成：`skill_read=False`，答案是纯前端加载性能（`next/image`、`priority`/`fetchPriority`、显式尺寸防 CLS、`Promise.all` 打散串行 waterfall、建议上提到 Server Component），未引入任何 Cloudflare 产品 |

## 评测结果

两组均为 `anthropic/claude-opus-5` · thinking=medium（`tools/run_evals.py` 默认，未传 `--model` / `--thinking`），10 次运行全部 `status: ok`，无超时。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 worker-review | claude-opus-5 · medium | 无（基线） | False | 8 条中 5 条达成 + 2 条部分 | 缺 CPU 数字；`timingSafeEqual` 未说先哈希等长；未提 `wrangler types`。155.3 s |
| 1 worker-review | claude-opus-5 · medium | 有 | **True** | **8/8** | 「Paid 默认 30000 ms、上限 300000 ms（5 分钟）」、「`timingSafeEqual` 比等长摘要」、「用 `wrangler types` 生成 `worker-configuration.d.ts`，绑定改名就变成类型错误」三条缺口全部填补；额外指出本地 dev 不强制 `limits.cpu_ms`。196.4 s |
| 2 kv-counter | claude-opus-5 · medium | 无（基线） | False | 8 条中 4 条达成 + 2 条部分 | 缺 KV 同 key 1 写/秒、缺 DO ~1000 req/s 与 `overloaded`、缺 `cacheTtl`；且把本地不复现误归因为「单进程无并发」。277.7 s |
| 2 kv-counter | claude-opus-5 · medium | 有 | **True** | **8/8** | 「同一 key 1 写/秒」「一个全局 DO 约 1000 req/s 就 `overloaded`」「本地 KV 读写强一致、无全球传播，最终一致 bug 物理上不可能出现」「KV 只留 `plan:` 配置，`cacheTtl: 300`，staleness budget 300 秒」四条缺口全部填补。281.0 s |
| 3 do-lifecycle | claude-opus-5 · medium | 无（基线） | False | 8 条中 7 条达成 | 缺 `exports` 机制本身：主动选择留在 legacy `migrations` + `renamed_classes`，无 `state: "renamed"` / `renamed_to`，无版本门。412.5 s |
| 3 do-lifecycle | claude-opus-5 · medium | 有 | **True** | **8/8** | 缺口填补：给出 `state: "renamed"` + `renamed_to` 的 `exports` 写法与五步部署序列，并正确推断 `Room` 由 `new_classes` 创建故后端是 `legacy-kv`、写 `sqlite` 会被 `storage_type_mismatch` 拒、后端 provision 后不可变。131.1 s |
| 4 pages-migration | claude-opus-5 · medium | 无（基线） | False | 8 条中 4 条达成 + 1 条部分 | 缺 `wrangler pages functions build` 与 `_routes.json` 无对应物、缺 `.assetsignore`、缺静态资源限额、缺 observability traces。320.0 s |
| 4 pages-migration | claude-opus-5 · medium | 有 | **True** | 8 条中 5 条达成 | `.assetsignore` 缺口填补（`node_modules`/`.git`/`.DS_Store` + `_worker.js`）。**仍未达成 3 条**：#5 未提 `wrangler pages functions build --outdir=` 与 `_routes.json` 由 `run_worker_first` 取代；#7 未给 20,000/100,000 文件与 25 MiB 的限额；#8 未在迁移里开 observability。184.6 s |
| 5 负例 | claude-opus-5 · medium | 无（基线） | False | **4/4** | 纯前端加载性能答案，未引入 Cloudflare。114.5 s |
| 5 负例 | claude-opus-5 · medium | 有 | **False** | **4/4** | 负例达标：skill 在场但未被读取；答案是串行 waterfall + `next/image` + `priority`/`fetchPriority` + `fill`/`aspectRatio` 防 CLS，全程无 Workers/Images/Cache/wrangler。318.0 s |

结论：**通过**。「基线缺口」表共记录 12 条未达成/部分达成的行为，有 skill 后填补 **9 条**——场景 1 的三条（CPU 数字、等长摘要、`wrangler types`）、场景 2 的四条（同 key 1 写/秒、DO ~1000 req/s 与 `overloaded`、本地读己之写一致的正确归因、`cacheTtl`）、场景 3 的一条（`exports` 的 `renamed` 机制）、场景 4 的一条（`.assetsignore`）。负例两组 `skill_read` 均为 `False`。

未达成项（如实记录，不改判）：场景 4 的 #5、#7、#8 三条在有 skill 时仍未达成。三条事实都写在 `references/static-assets.md` 里（`wrangler pages functions build --outdir=`、`_routes.json` 无对应物、20,000/100,000 文件与 25 MiB），traces 字段也在 SKILL.md Core rule 27 里，但该场景的答案把预算花在了真跑 `wrangler dev` 逐条验收 9 个响应上，没有回到覆盖清单。诊断是：`migrate-pages-to-workers-static-assets` 这个 workflow 的验证门足够强，而「部署前先数文件数」和「迁移时顺手开 observability」原本排在清单第 6 步与完全缺席的位置，太靠后。

**测量之后做的一处修改（表格数字不含此修改的效果）**：把资源限额检查提到该 workflow 的第 1 步（理由写进正文：限额是会让部署直接失败的硬门，不是节流），把 `observability.enabled` + `observability.traces.enabled` 并入第 2 步的同一次配置编辑，并补了「每个环境重新声明绑定与 `vars`」这一步（基线与有 skill 两次都自发发现了 preview 丢 `SESSIONS` 的问题，说明它值得进清单）。下次同步时重跑场景 4 即可验证这次重排是否把 #7、#8 也带过线；#5 属于覆盖面而非顺序问题。

## 本机实测（[verified] 的来源）

环境：wrangler 4.131.0 + workerd 1.20260910.1，Node v26.7.0，无 Cloudflare 账号、未登录。工程在 `/tmp/cfw`。

| # | 实测 | 观察结果 |
|---|---|---|
| 1 | `npx wrangler --version` | `4.131.0` |
| 2 | `wrangler types` | 生成 `worker-configuration.d.ts`：`interface __BaseEnv_Env { CACHE: KVNamespace; DB: D1Database; COUNTER: DurableObjectNamespace<import("./src/index").Counter> }` + 完整运行时类型，头部注明 `Runtime types generated with workerd@1.20260910.1 <compat date> nodejs_compat`；`Cloudflare.GlobalProps.durableNamespaces` 由 `exports` 推导 |
| 3 | `migrations` 与 `exports` 同时出现 + `wrangler deploy --dry-run` | 报错 `` `migrations` and `exports` are mutually exclusive. Choose one or the other to declare your Durable Object lifecycle, but not both. `` |
| 4 | `wrangler deploy --dry-run --outdir=...` | 输出 `Total Upload: 1.48 KiB / gzip: 0.71 KiB` 与绑定清单表；`--dry-run` 不联网、不需要账号 |
| 5 | `wrangler dev`（默认本地）+ curl `/kv` | 写后立即读回 `{"immediate":"v1"}` —— **本地 KV 是读己之写一致的**，生产的最终一致缺陷在本地无法复现 |
| 6 | curl `/do` 两次 | `{"n":1}` → `{"n":2}`；SQLite storage 的 `INSERT ... ON CONFLICT` 计数正确 |
| 7 | curl `/d1` | `{"one":1}`；本地 D1 无需真实 `database_id` |
| 8 | `hub restart` wrangler dev 后再 curl | `/do` 返回 `{"n":3}`，`/kv` 仍有值；本地状态持久在 `.wrangler/state/v3/{kv,d1,do,r2,cache}` 下的 SQLite 文件里 |
| 9 | 模块作用域缓存 `ReadableStream` 跨请求复用 | 第二个请求抛 `Cannot perform I/O on behalf of a different request. I/O objects (such as streams, request/response bodies, and others) created in the context of one request handler cannot be accessed from a different request's handler. ... (I/O type: ReadableStreamSource)` |
| 10 | `wrangler kv key list --binding CACHE --local` / 不带 `--local` | 都返回本地的 `[{"name":"k"}]`；`--help` 显示 `wrangler dev` 的 `--remote` 默认 `false`，`kv`/`d1` 的 `--local`/`--remote` 无默认值，未登录时落在本地 |

未在本机验证（一律标 `[official]`，来源为官方文档）：所有需要账号或计费的行为——`wrangler deploy` 实际上传、`wrangler dev --remote`、`wrangler tail`、Logpush、gradual deployments 与 `wrangler rollback`、Queues 消费者与 Workflows 的真实投递、R2/D1 的生产限额、Tail Worker 的 `tail()` 触发、Cloudflare One（Access/Gateway/WARP/DEX/Logpush）全部、`cloudflared` 隧道（本机无 `cloudflared` 二进制）。

## 备注

### Cloudflare 文档许可的实读结论

`gh api repos/cloudflare/cloudflare-docs/contents/LICENSE` 解码后正文首行是 `Attribution 4.0 International`，即 **CC-BY-4.0** 全文，与 API 的 `license.spdx_id: "CC-BY-4.0"` 一致。按 `docs/roadmap.md`「许可处理规则」，CC-BY-4.0 可 `merged`，并在 `SOURCES.yaml` 的 `notes` 写明署名。

这一点必须和波次 5 的三个反例分开记：redis.io/docs 是 CC-BY-NC-SA-4.0、Elastic 文档是 CC-BY-ND，hashicorp/terraform 是 BUSL-1.1，三者都不能 merged。**一个仓库的许可是它自己的**——所以这里没有沿用「官方文档一律 reference」的保守做法，而是实读后按其真实许可 merged。`cloudflare/skills` 与 `cloudflare/workers-sdk` 的 LICENSE 也已实读，都是 Apache-2.0 全文。

### 未来同步时要盯的上游

- `cloudflare/workers-sdk` `packages/wrangler/CHANGELOG.md`：本 skill 的每个 `(Wrangler x.y+)` 版本门都来自这里。DO `exports` 仍在演进（`transferred` / `expecting-transfer` 的多次部署流程）。
- `cloudflare/cloudflare-docs` 的 `src/content/docs/{workers,durable-objects,kv,r2,d1,queues}/**/limits*`：限额表会变，每次同步重读。
- `@cloudflare/vitest-plugin` 主版本：它刚从 `vitest-pool-workers` 改名（裁决 5），下一次同步要确认 codemod 是否还需要提。
- `cloudflare/skills` 的 `durable-objects/SKILL.md`：一旦它改写成 `exports`，裁决 1 可以撤销。

### 产物与一处结构取舍

`SKILL.md` 337 行（标准建议 150–400，本批次水位 235–350），`description` 992 字符并以 `Do not use for …` 收尾，10 个 reference 共 2549 行（单文件 165–384）。

一处取舍值得记下来：第一稿写成 11 个 reference，其中 `wrangler-config.md`（227 行）与 `wrangler-cli.md`（163 行）分立。上限是 10，所以把两者合并成 `references/wrangler.md`（384 行）。合并是对的而不是凑数——「改配置」和「跑命令」在 wrangler 上本来就不是两件事：`secret put` 既是配置又是部署，环境既是配置键又是 `--env` 参数，`limits.cpu_ms` 既是字段又是 `exceededCpu` 的成因。剩下 9 个文件按失败模式分而不按产品分（`limits-and-versions` 是数字、`workers-runtime` 是运行时报错、`do-lifecycle` 是不可逆操作、`storage-selection` 是选型、`static-assets` 是迁移、`observability` 是只有生产信号时、`testing` 是证不到什么、`cloudflare-one` 是 Zero Trust），这是 topic router 能一行说清「什么时候读」的前提。

`references/*.md` 之间不互相链接：初稿有 4 处「见 `references/x.md`」的纯文本交叉引用（`durable-objects` → `do-lifecycle`、`observability` → `cloudflare-one`、`storage-selection` → `durable-objects`/`do-lifecycle`、`testing` → `static-assets`），已全部改写成「见 topic router 里的某个条目」这类不指向兄弟文件的表述。

`scripts/` 目录没有建：本 skill 里所有可运行的东西都是 `wrangler` 自己的子命令（`types`、`dev`、`deploy --dry-run`、`kv`/`d1` 的 `--local`），再包一层 Python 或 Node 脚本只会在上游改动时腐化，没有可运行价值。

### 放弃的方向

- **Agents SDK / MCP server on Cloudflare**：cloudflare/skills 的 `agents-sdk`（18 个 reference）与 openai/plugins 的 `building-mcp-server-on-cloudflare` 质量都很高，但主题属于 `ai-engineering` / `mcp-server`，这两个 skill 本库尚不存在。按 Contract 不引用、不并入，正文只在 Scope 的否定列表里说明「本库尚无 skill 覆盖，应当直说而不是即兴发挥」。
- **Cloudflare 的 CDN / WAF / DDoS / Bot Management / Turnstile / Stream / Zaraz 产品面**：属于 Cloudflare 的网络与安全产品，不是「构建与运维 Workers 应用」。`cloudflare/skills` 的参考树里有完整材料，将来若立 `web-security` 类 skill 可以再评。
- **Terraform / Pulumi provider 字段**：按 Contract，HCL 语法与 state 归 `terraform`；本 skill 出现 IaC 时用 Cloudflare 自己的原生工具（wrangler、`exports`、Access/Gateway API），需要 Terraform 时指向 `terraform`。
