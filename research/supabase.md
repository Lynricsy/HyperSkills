# supabase 调研记录

单一权威上游改写

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。
> 本 skill 按「官方厂商特例」立项：Supabase 官方组织维护活跃 skill 仓库
> （`supabase/agent-skills`，MIT，2592★），配官方文档（`supabase/supabase` 的 `apps/docs`，
> Apache-2.0）与 5 个社区上游（其中 3 个 merged）。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"supabase agent skill SKILL.md github claude"`
  - `gh api search/repositories`：`supabase skill` / `supabase-skills` / `supabase edge functions skill` /
    `supabase rls skill` / `supabase auth skill`（各取 updated 排序前 15）
  - `gh api search/code`：`q=supabase filename:SKILL.md`（30 条，逐个查元数据）
  - 领域官方组织仓库：`supabase/agent-skills`、`supabase/supabase`、`supabase/cli`、`supabase/server`
  - 多技能仓库整树 grep（零命中的也留行）：`github/awesome-copilot`、`jezweb/claude-skills`、
    `secondsky/claude-skills`、`wshobson/agents`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- `gh auth status`：已登录（账号 Lynricsy，scopes `gist, read:org, repo, workflow`），全程使用登录态配额。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | supabase/agent-skills `skills/supabase` | <https://github.com/supabase/agent-skills> | 2592 | 2026-08-12 | MIT | Supabase 全平台（Auth/RLS/CLI/MCP/迁移/排错） | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE (merged) | 官方唯一权威 skill。安全清单密度极高（`user_metadata` 不可用于授权、view 默认绕过 RLS、UPDATE 需 SELECT 策略、`SECURITY DEFINER` 默认 `EXECUTE` 给 PUBLIC、Storage upsert 需三种权限）。扣「具体」是因为约四成篇幅是「去 fetch 文档」的路由而非可执行规则 |
| 2 | supabase.com/docs（源在 supabase/supabase `apps/docs`） | <https://supabase.com/docs> | 109029 | 2026-09-10 | Apache-2.0（实读仓库根 LICENSE 确认；`apps/docs` 下无独立 LICENSE，受仓库许可覆盖） | 官方文档全集 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | 所有版本敏感事实的裁决源。`.md` 后缀可直接取纯文本，便于逐条核实 |
| 3 | supabase/agent-skills `skills/supabase-postgres-best-practices` | 同上 | 2592 | 2026-08-12 | MIT | 纯 Postgres 性能（索引/EXPLAIN/锁/连接池/RLS 性能） | 3 | 3 | 3 | 3 | 2 | 14 | reference（本 skill 不取） | 内容全部落在同波 `postgres` skill 的边界内（见「备注 — 与 postgres skill 的去重」）。本 skill 只读它确认自己不该写什么 |
| 4 | magnus919/agent-skills `supabase` | <https://github.com/magnus919/agent-skills> | 76 | 2026-09-09 | MIT | 托管/本地/自托管三环境 + 验证矩阵 | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE (merged) | 唯一把「先判定目标环境再选命令」写成硬约束的上游；「验证矩阵」（容器健康 ≠ API 健康、service-role 绕过不能当授权证明）可直接转成验证门。扣「正确」是因为自托管章节的镜像/端口事实无法在本仓库复核 |
| 5 | tushaarmehtaa/tushar-skills `supabase` | <https://github.com/tushaarmehtaa/tushar-skills> | 11 | 2026-09-09 | MIT | schema + grants/RLS + SSR + 类型生成 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE (merged) | 31 行零废话。抽查三条全部与官方文档一致：`getAll`/`setAll` 适配器、每请求新建 client、grants 与 RLS 两层都要写。且明确反对「给每张表机械加 user_id + 四条策略」 |
| 6 | CarolMonroe22/lovable-cloud-to-supabase-migration | <https://github.com/CarolMonroe22/lovable-cloud-to-supabase-migration> | 31 | 2026-08-31 | MIT | Lovable Cloud → 自有 Supabase 迁移 | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE (merged，仅迁移清单语义) | 作者是 Supabase SupaSquad 成员，且声明在真实项目上端到端验证过（12 表 / 237 行 / 23 用户 / 40 storage 文件 / 5 edge functions / 2 cron jobs）。可迁移的通用事实只有两条：一个 Supabase 项目的完整搬迁面 = db + auth.users + storage 对象 + edge functions + secrets + cron；密码哈希不可假定可携，默认走重置流程。Lovable 专属流程一律不取 |
| 7 | anymikey/supabase-security-audit | <https://github.com/anymikey/supabase-security-audit> | 0 | 2026-09-10 | MIT | RLS 审计（advisors 之外的业务逻辑漏洞） | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE (merged) | 明确「先跑 advisors，只报它结构上看不见的东西」——付费内容无订阅校验、多租户表漏 tenant 过滤、只限读不限写。这个分工正是本 skill 需要的审计口径 |
| 8 | braindesmond5-boop/supabase-rls-audit `skills/rls-audit` | <https://github.com/braindesmond5-boop/supabase-rls-audit> | 1 | 2026-07-28 | MIT | 用 anon key 实际发请求验证 RLS | 1 | 2 | 3 | 2 | 2 | 10 | INCLUDE (merged) | 提供了本 skill 最缺的「验证门」：读策略文件不算验证，要用 publishable key 实际请求。三条判读语义极有价值——`200` 带行 = 暴露、`200 []` = **不确定**（空表与锁住的表从外面看一样）、`401/403/42501` = 受保护；并指出 PostgREST 的 OpenAPI 根现在只允许 `service_role`，不能用来枚举表 |
| 9 | supabase/server（`@supabase/server` SDK） | <https://github.com/supabase/server> | 89 | 2026-09-10 | MIT | Edge Function 的 `withSupabase` / `createSupabaseContext` | 3 | 3 | 2 | 3 | 2 | 13 | reference | 官方仓库但不是 skill，无可合入的 skill 文本；只用来核实 `auth` 模式取值、`ctx` 字段与注入的环境变量名。事实本身从官方文档取证 |
| 10 | 0xquinto/supabase-realtime-skill | <https://github.com/0xquinto/supabase-realtime-skill> | 0 | 2026-05-06 | Apache-2.0 | Realtime 有界订阅（Edge Function 内） | 0 | 1 | 3 | 1 | 2 | 7 | MAYBE → reference | 「broadcast 是即发即弃、不持久，接收方可能离线就该走 pgmq」这条正确且有用，但它把 150s 当成通用 wall-clock 上限（官方：Free 150s / 付费 400s，另有 CPU time 2s 与 idle timeout 150s），版本敏感事实错一条即扣「正确」。只作主题清单与交叉校验，正文事实全部改从官方文档取 |
| 11 | mathruffian-dot/supabase-connect-skill `skills/supabase-setup` | <https://github.com/mathruffian-dot/supabase-connect-skill> | 1 | 2026-08-09 | MIT | 零基础用户接 MCP + 建表开 RLS | 1 | 2 | 2 | 2 | 2 | 9 | MAYBE → reference | 「建完表一定要开 RLS 并验证」的红线与本 skill 一致，但通篇是面向从没用过数据库的终端用户的中文引导流程（替用户点授权、教他别选付费方案），与本仓库读者（写代码的 agent）不匹配。只读它确认覆盖面，不合入文本 |
| 12 | supabase-community/supabase-plugin `skills/supabase` | <https://github.com/supabase-community/supabase-plugin> | 18 | 2026-09-07 | 无（API `license: null`） | 官方 skill 的打包分发 | — | — | — | — | — | — | REJECT | `diff` 与官方 `skills/supabase/SKILL.md` 逐字节相同（空 diff）。纯分发副本，合入它等于把同一份内容记两次上游 |
| 13 | Sheshiyer/skill-clusters `skills/supabase` | <https://github.com/Sheshiyer/skill-clusters> | 0 | 2026-09-03 | MIT | 官方 skill 的 fork | — | — | — | — | — | — | REJECT | 官方 v0.1.0 的旧 fork（官方现为 v0.1.2），删掉了 changelog 核对那一条并加了非规范的 `cluster:` 顶层键。旧且更差 |
| 14 | bpthevenot-hub/agent-skills `skills/supabase` | <https://github.com/bpthevenot-hub/agent-skills> | 0 | 2026-07-01 | MIT | 官方 skill 的 fork | — | — | — | — | — | — | REJECT | 文件里留着未解决的 `<<<<<<< HEAD` 冲突标记，内容是官方 v0.1.2 的一半。质量不可用 |
| 15 | prodbartist/supabase-agent-skills | <https://github.com/prodbartist/supabase-agent-skills> | 0 | 2026-03-03 | MIT | 官方 postgres-best-practices 的 fork | — | 0 | — | — | 2 | — | REJECT | 最近推送距今 >6 个月，量表规定直接 REJECT；且只有官方内容的旧副本 |
| 16 | officeos-co/skill-supabase | <https://github.com/officeos-co/skill-supabase> | 0 | 2026-04-19 | MIT | 用 CLI 风格语法调 Supabase REST | — | 1 | 2 | — | 2 | — | REJECT | 全篇命令都要经专有运行器 `skill_exec`（`supabase query --sql ...`）。agent 绑定且平台不可得，标准第 1.3 节禁止这类正文 |
| 17 | OpenSIN-Code/supabase-skill | <https://github.com/OpenSIN-Code/supabase-skill> | 0 | 2026-06-28 | 无（API `license: null`） | 单台自托管实例运行手册 | — | 1 | 3 | — | 0 | — | REJECT | 内容是某台 OCI 虚机（含公网 IP、13 个容器的内网 IP、`.env` 路径、SSH 别名）的私有运行手册。无普适性，且把基础设施细节写进 skill |
| 18 | github/awesome-copilot | <https://github.com/github/awesome-copilot> | 38866 | 2026-09-10 | MIT | GitHub 官方 skills/instructions 集 | — | 3 | — | — | 2 | — | REJECT | 整树 `git/trees/main?recursive=1` grep `supabase` 零命中。本主题无素材可取（记录在案，避免下批重复检索） |
| 19 | jezweb/claude-skills | <https://github.com/jezweb/claude-skills> | 1000 | 2026-07-02 | MIT | 多技能集 | — | 2 | — | — | 2 | — | REJECT | 整树 grep `supabase` 零命中 |
| 20 | secondsky/claude-skills | <https://github.com/secondsky/claude-skills> | 217 | 2026-09-09 | MIT | 多技能集 | — | 3 | — | — | 2 | — | REJECT | 整树 grep `supabase` 零命中（roadmap 里它是 Cloudflare/GraphQL 的种子，不是 Supabase 的） |
| 21 | wshobson/agents | <https://github.com/wshobson/agents> | 39556 | 2026-09-07 | MIT | 多技能集 | — | 3 | — | — | 2 | — | REJECT | 整树 grep `supabase` 零命中 |

## 深度审查

### 1. supabase/agent-skills `skills/supabase`（官方，主干）

149 行，结构是「Core Principles → CLI → MCP → 文档 → schema 变更 → 调试 → Reference Guides」。
frontmatter 只有 `name` / `description` / `metadata.{author,version}`，没有 agent 专属字段，剥离成本低
（把 `metadata.author: supabase` 换成 HyperSkills 即可）。

真正的价值集中在两处：

- **安全清单**（第 33–75 行）。九条里有七条是「静默失败」类陷阱，正是标准第 3 节要的东西：
  `raw_user_meta_data` 用户可改却会出现在 `auth.jwt()`；删用户不会失效已签发的 access token；
  view 在 PG15+ 需要 `security_invoker = true` 否则绕过 RLS；UPDATE 需要先能 SELECT，缺 SELECT 策略时
  update 返回 0 行且不报错；`auth.role()` 已弃用（且开了匿名登录后 `auth.role() = 'authenticated'`
  会静默放行匿名用户）；UPDATE 策略缺 `WITH CHECK` 时用户可把行的 `user_id` 改成别人；
  `public` 下的 `SECURITY DEFINER` 函数因 Postgres 默认把 `EXECUTE` 授予 `PUBLIC` 而成为公开端点；
  Storage upsert 需要 INSERT + SELECT + UPDATE 三种权限。
- **Data API 暴露与 RLS 是两回事**（第 24–31 行）。新建表是否经 Data API 可达取决于 Data API 设置与
  `anon`/`authenticated` 的 `GRANT`；RLS 只管「可达之后能看到哪些行」。这条是「SQL 里建了表却 404」
  这类报障的正确入口。

弱点：约四成篇幅是「先 fetch `https://supabase.com/changelog.md`」「用 MCP `search_docs`」这类文档路由，
以及 MCP 连接排障（`curl` 打 `mcp.supabase.com` 看是不是 401）。这些在本仓库里价值低——
标准要求正文写规则而不是写「去查文档」，且 MCP 服务器排障属于工具配置而非 Supabase 工程。
另有两条 CLI 版本门槛（`db query` 需 v2.79.0+、`db advisors` 需 v2.81.3+）在当前 CLI（v2.117.0）下
已是历史噪声，按标准第 3 节「不写时间敏感表述」处理：正文只写命令，不写版本下限。

### 2. supabase.com/docs（官方文档，裁决源）

逐页取纯文本核实（`https://supabase.com/docs/<path>.md`），本次实读 26 页。它相对官方 skill 多出来的、
且本 skill 必须写的当前形态：

- **API key 体系换代**：`sb_publishable_...` / `sb_secret_...` 取代 JWT 形态的 `anon` / `service_role`，
  后者官方计划 2026 年底弃用；两套并存，创建新 key 不会吊销旧 key。判读技巧很实用——
  「让你复制以 `eyJ` 开头的长字符串的教程都是给 legacy key 写的」。secret key 还带两个防误用检查：
  带浏览器 `User-Agent` 会被判 401；项目不需要就可以完全不建 secret key。
- **grants 先于 RLS，两种失败长得不一样**：缺 `GRANT` 返回 `42501` 权限错（`service_role` 也一样），
  策略不匹配返回空结果。「先看 grant 再 debug 策略」。且 `public` 下自动授予 `anon`/`authenticated`
  的平台默认正在改为「默认不授予」（supabase/discussions#45329）。
- **三个身份读取函数的分工**：`getClaims()` 验证身份（新项目默认非对称签名，走 WebCrypto + 缓存的
  JWKS 本地验签）、`getUser()` 要最新用户记录时用（一次网络往返）、`getSession()` 只在需要 raw token
  时用且其 user 对象不可用于授权。SSR 下 `setAll` 现在收两个参数（cookies 与必须回写到响应的
  `Cache-Control`/`Expires`/`Pragma`），不回写会让 CDN 缓存住带会话的响应并泄漏给其他用户。
  cookie 默认名 `sb-<project_ref>-auth-token`。
- **Edge Functions 的新模板**：`export default { fetch: withSupabase({ auth: [...] }, handler) }`，
  `withSupabase` 来自 `npm:@supabase/server`，顺带处理 CORS 预检；`ctx` 上给
  `supabase`（按调用者 RLS 作用域）/ `supabaseAdmin`（绕过 RLS）/ `userClaims` / `jwtClaims` / `authMode`。
  运行时注入 `SUPABASE_SECRET_KEYS`（按名字索引的 JSON 字典），旧的 `SUPABASE_SERVICE_ROLE_KEY` 仍在但是 legacy 路径。
  限额：内存 256MB、wall clock Free 150s / 付费 400s、**CPU time 2s**、idle timeout 150s（超时回 504）。
- **Realtime 的三条通道语义与选型阈值**：授权发生在「加入频道时」，靠 `realtime.messages` 上的 RLS
  策略（`realtime.topic()` 取频道名、`request.jwt.claims` 取 claims），且客户端必须同时传
  `config: { private: true }`；`realtime` schema 被锁定，在里面建表/建函数会 `permission denied`，
  但管理 `realtime.messages` 的策略是允许的。Postgres Changes 对**每个订阅者**各做一次授权检查
  （100 个订阅者 = 100 次），且为保序单线程处理，加大 compute 基本无效；预计并发订阅者
  超过约 3000 就该换成「从数据库 broadcast」。另有一条容易踩的坑：**DELETE 事件不经 RLS**。
- **声明式 schema 的核心陷阱**：`supabase db diff` 比的是 `supabase/schemas/*.sql` 与已有迁移，
  **不读活库**——在 Studio/SQL editor 里改的东西 diff 看不见，会报「No schema changes found」
  然后被静默丢弃。新列要追加到表末尾（view 与 enum 依赖列序）。diff 引擎（`pg-delta`）不捕获 DML、
  view 的 owner/grants 与 `security_invoker`、物化视图、`alter policy`、列级权限、comment、分区、
  `create domain`，且会从默认权限里重复产出 grant 语句。
- **Storage 私有桶的正确取法**：`getPublicUrl` 只对公开桶有意义，私有桶要 `createSignedUrl`；
  签名 URL 用的是独立的内部签名密钥，**不随 Auth 密钥轮换或 HS256→ES256 切换而失效**，
  想吊销只能找官方支持。

### 3. magnus919/agent-skills `supabase`

122 行 SKILL.md + 9 个 reference，MIT，76★，昨天推送。三点被采纳：

- 「先判定目标环境」——托管项目 / CLI 本地栈 / 自托管 Compose 是三套不同的操作环境，命令不通用。
  本 skill 收窄为「托管 + CLI 本地栈」两套（自托管属于运维控制面，不在边界内），但这条判定纪律照搬。
- 「验证矩阵」的判据写法：容器健康不是 API 健康；一个 API 返回 200 不是授权证明；备份不是恢复证据。
  转成本 skill 的验证门措辞——授权层的最小证据是「以 anon / authenticated 各跑一次正例与反例，
  且不得用 service-role 通过来当证明」。
- CLI 本地栈是开发用的：默认凭据、无 TLS、无生产限流，不能对外暴露。

不采纳：自托管 Compose 生命周期（`run.sh`、Kong 8000/8443、Supavisor 5432/6543、pgsodium root key 卷）
——超出边界，且这些事实本仓库无法复核。

### 4. tushaarmehtaa/tushar-skills `supabase`

31 行，密度最高的社区上游。抽查三条对照官方文档全部命中，采纳其：

- 「不要机械化」原则：不给每张表都加 `user_id` 和四条 CRUD 策略；从领域模型推断所属与租户关系。
- 第三方 auth（Clerk 等）：要走原生集成并把 provider token 传给客户端，用真实 JWT `sub`/claims；
  **写一个 RLS 表达式并不等于配好了 token 验证**。
- 部署前的三步：`supabase migration list` → `supabase db push --dry-run` → `db push`；
  `migration up` 不是远端部署的替代品。以及 `db reset --linked`、`db push --include-seed` 不能对生产用。

### 5. anymikey/supabase-security-audit 与 braindesmond5-boop/supabase-rls-audit

两个都是审计型 skill，互补且都不与官方重复：

- anymikey 定的是**分工**：先跑 `supabase db advisors`（或 MCP `get_advisors`），凡它已报的
  （表级 RLS 关闭、缺 FK 索引、`SECURITY DEFINER` 无 `search_path`、物化视图经 API 暴露）
  只留一行指针，本 skill 只报 advisors 结构上看不见的业务逻辑漏洞。
- braindesmond5 定的是**验证方式**：用 publishable key 实际发 REST 请求，而不是读策略文件猜。
  三条判读语义（`200`+行 = 暴露 / `200 []` = 不确定 / `401`·`403`·`42501` = 受保护）被直接写进本 skill 的
  审计工作流；并采纳「PostgREST 的 OpenAPI 根现在只允许 `service_role`，不能用它枚举表，
  要从代码里 grep `.from('…')` 再并上迁移文件里的 `create table`」。

两者的 frontmatter 都缺 `license` 字段（仓库有 LICENSE 文件，MIT），按仓库许可处理。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 服务端该用哪个函数验证身份 | 社区上游与大量教程：`getUser()`；官方 skill 的 description 同时列 `getSession`/`getUser`/`getClaims`；官方文档：`getClaims()` | 正文只写 `getClaims()` 验证身份；需要「最新的用户记录」时才 `getUser()`；`getSession()` 仅用于取 raw token 且其 user 对象不可用于授权 | 官方文档 `guides/auth/server-side/creating-a-client`：新项目默认非对称签名，`getClaims()` 本地用 WebCrypto + 缓存 JWKS 验签，每次都校验签名；`getUser()` 每次一个网络往返。官方 > 社区，更新 > 更旧 |
| 2 | SSR cookie 适配器的形状 | 旧教程与 `@supabase/auth-helpers` 时代：`get`/`set`/`remove` 三个单 cookie 方法；tushaarmehtaa 与官方文档：`getAll`/`setAll` | 只写 `getAll`/`setAll`，并写明 `setAll` 的第二个参数是必须回写到响应的缓存头 | 官方文档同页：`@supabase/ssr` 的 cookie 方法不硬编码，`setAll(cookies, headers)`，不回写 `Cache-Control`/`Expires`/`Pragma` 会让 CDN 缓存住带会话的响应。`auth-helpers` 已被 `@supabase/ssr` 取代 |
| 3 | 客户端该带哪个 key | 社区上游普遍写 `NEXT_PUBLIC_SUPABASE_ANON_KEY` / `service_role`；官方文档：publishable / secret | 正文以 publishable / secret 为默认命名与推荐，`anon`/`service_role` 只作为 legacy 名出现在识别与迁移语境（「以 `eyJ` 开头 = legacy」） | 官方文档 `guides/api/api-keys`：`anon`/`service_role` 计划 2026 年底弃用；secret key 另带浏览器 UA 401 检查。标准第 3 节要求主线只写当前做法 |
| 4 | Edge Function 的入口形状 | 社区上游全部是 `Deno.serve(handler)` + 手写 CORS + `Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')`；官方文档与 `supabase functions new` 模板：`export default { fetch: withSupabase({ auth }, handler) }` | 正文默认写 `withSupabase`（它同时处理凭据校验与 CORS 预检，并在 `ctx` 上给作用域化的 client）；`Deno.serve` + `corsHeaders` 作为「不用该 SDK 时」的逃生口 | 官方文档 `guides/functions/quickstart`（`functions new` 生成的模板）、`guides/functions/auth`、`guides/functions/cors`。官方厂商 > 社区 |
| 5 | Edge Function 的时间上限 | 0xquinto：150s wall clock（据此把订阅超时封在 120s）；官方文档：Free 150s / 付费 400s，另有 CPU time 2s 与 idle timeout 150s | 正文写三个独立限额（内存 256MB、CPU time 2s、wall clock 因计划而异、idle 150s 超时回 504），并指出「先撞上的通常是 CPU time 2s 而不是 wall clock」 | 官方文档 `guides/functions/limits`。社区上游把单一档位当通用值，属事实错误 |
| 6 | Postgres Changes 还是 Broadcast | 社区上游与旧教程默认 Postgres Changes；官方文档给出阈值与机制差异 | 正文给一条可判定的规则：需要「每个订阅者按 RLS 各自过滤」且订阅者不多 → Postgres Changes；否则（尤其预计 >~3000 并发订阅者、或只是要把一次变更扇出给所有人）→ 数据库里 `realtime.broadcast_changes()` 触发器 + 私有频道 | 官方文档 `guides/realtime/postgres-changes`（每订阅者一次授权检查、单线程保序、加大 compute 无效、~3000 阈值、DELETE 不经 RLS）与 `guides/realtime/broadcast` |
| 7 | 「表建好了但 API 取不到」的第一入口 | 社区上游几乎一律先怀疑 RLS 策略；官方 skill 与文档：先看 Data API 暴露与 `GRANT` | 正文的排查顺序固定为：Data API/schema 暴露 → `GRANT`（`42501` 权限错） → RLS 策略（空结果） → 会话是否到达（`auth.uid()` 为 null） | 官方文档 `guides/api/securing-your-api`：grants 先于 RLS 被评估，两种失败的可观察表现不同（权限错 vs 空结果） |
| 8 | `auth.role()` 能不能用来判「已登录」 | 旧社区示例大量使用 `auth.role() = 'authenticated'`；官方 skill：已弃用 | 正文只写 `TO authenticated`，并写明为什么：开了匿名登录后匿名用户也持有 `authenticated` 这个 Postgres 角色，`auth.role()` 检查会静默放行 | 官方 skill 安全清单 + 官方文档匿名登录说明。同时写明 `TO authenticated` 单独用只是「认证」不是「授权」（BOLA/IDOR），必须配所属谓词 |
| 9 | RLS 策略里 `auth.uid()` 要不要包一层 `(select …)` | 社区写法两种都有；同波 `postgres` skill 在 PostgreSQL 18.6 上实测：谓词落在 Filter 节点时 200k 行 1223ms → 11ms，落在 Index Cond 时无差别 | 本 skill 正文统一写 `(select auth.uid())` 形式（无副作用且在最坏情况下差两个数量级），**但性能机理不在本 skill 展开**，指向 `postgres` skill | 分界句：RLS 策略语法与性能归 `postgres`。实测数据来自同波 `PostgresSkill` 的现场验证，本 skill 只照结论用不复述 |
| 10 | 私有桶的 URL 怎么给 | 上游示例里 `getPublicUrl` 被用在私有桶上（本 skill 的场景 3 夹具就是这个真实错法）；官方文档：私有桶用 `createSignedUrl` | 正文写 `createSignedUrl` + 到期时间，并补一条官方文档才有的事实：签名 URL 用独立内部密钥，不随 Auth 密钥轮换失效，想吊销只能联系官方支持 | 官方文档 `guides/storage/serving/downloads` |
| 11 | 省略 `WITH CHECK` 的 `UPDATE` 策略是不是漏洞 | 官方 skill 安全清单：「UPDATE 策略必须同时有 `USING` 与 `WITH CHECK`，缺 `WITH CHECK` 用户可把行的 `user_id` 改成别人」；PostgreSQL 官方文档：`ALL` 与 `UPDATE` 策略在未定义 `WITH CHECK` 时，`USING` 表达式**同时**用于判定可见行与允许写入的新行 | **官方 skill 这条事实错了**。正文改写为：省略 `WITH CHECK` 不构成开放写入（复用的 `USING` 会挡住改成别人 `user_id` 的新行），但它使两个表达式永远无法不同（「可编辑本工作区任意行，但不得把行移出工作区」需要两个不同表达式），所以仍然要显式写两个——理由是意图表达而不是安全漏洞。reference 里明确指出该上游说法有误 | <https://www.postgresql.org/docs/current/sql-createpolicy.html>：「For policies that can have both USING and WITH CHECK expressions (ALL and UPDATE), if no WITH CHECK expression is defined, then the USING expression will be used both to determine which rows are visible (normal USING case) and which new rows will be allowed to be added (WITH CHECK case).」RLS 语义的权威是 Postgres 本身，官方厂商 skill 在此不具更高权威 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `supabase-official-skill` | supabase/agent-skills `skills/supabase` | merged | 安全清单（`user_metadata` 不可用于授权、view 默认绕过 RLS、UPDATE 需 SELECT 策略且需 `WITH CHECK`、`SECURITY DEFINER` 的两个陷阱、Storage upsert 需三权限、删用户不失效 token）、Data API 暴露与 RLS 的分层、声明式 vs 命令式两条 schema 路线的判定、`db advisors` 作为提交前门 |
| `supabase-docs` | supabase.com/docs | merged | 全部版本敏感事实：publishable/secret key 体系与 legacy 识别、grants 先于 RLS 与 `42501`、`getClaims`/`getUser`/`getSession` 分工、`getAll`/`setAll` 与缓存头、`withSupabase` 与 `ctx`、Edge Function 四个限额、Realtime 三通道与授权表、`realtime.broadcast_changes()`、声明式 diff 的盲区清单、私有桶签名 URL 与其独立密钥、自定义 claim 的 access-token hook 与授权函数、`gen types` |
| `magnus-agent-skills` | magnus919/agent-skills `supabase` | merged | 「先判定目标环境（托管 / CLI 本地栈）再选命令」的纪律；验证门判据（API 200 不是授权证明、service-role 通过不算证明）；CLI 本地栈是开发用途、不可对外暴露 |
| `tushar-skills` | tushaarmehtaa/tushar-skills `supabase` | merged | 反对机械化建策略；第三方 auth 集成的边界（RLS 表达式 ≠ 配好 token 验证）；部署三步 `migration list` → `db push --dry-run` → `db push`，以及不得对生产用 `db reset --linked` / `db push --include-seed` |
| `rls-audit` | braindesmond5-boop/supabase-rls-audit | merged | 审计验证门：用 publishable key 实际发请求；三条判读语义（`200`+行 / `200 []` 不确定 / `401`·`403`·`42501`）；表清单要从代码 grep `.from()` 并上迁移里的 `create table`，因为 PostgREST OpenAPI 根只允许 `service_role` |
| `supabase-security-audit` | anymikey/supabase-security-audit | merged | 与 `db advisors` 的分工：advisors 已报的只留指针，本 skill 只找它结构上看不见的业务逻辑漏洞（付费内容无订阅校验、多租户漏 tenant 过滤、限读不限写） |
| `lovable-migration` | CarolMonroe22/lovable-cloud-to-supabase-migration | merged | 项目搬迁的完整面清单（db + `auth.users` + storage 对象 + edge functions + secrets + cron）与「密码哈希不可假定可携，默认走重置流程」 |
| `postgres-docs` | postgresql.org `sql-createpolicy` | merged | 裁决官方 skill 那条错误主张所依据的权威语义：`ALL` / `UPDATE` 策略未定义 `WITH CHECK` 时，`USING` 表达式同时用于判定可见行与允许写入的新行（见「冲突与裁决」第 11 条） |
| `supabase-postgres-best-practices` | supabase/agent-skills `skills/supabase-postgres-best-practices` | reference | 只读来划边界：其覆盖的索引 / EXPLAIN / 锁 / 连接池 / RLS 性能全部让给同波 `postgres` skill，本 skill 一条不写 |
| `supabase-server-sdk` | supabase/server | reference | 只读来核实 `withSupabase` 的 `auth` 模式取值、`ctx` 字段与注入的环境变量名；事实本身取自官方文档 |
| `quinto-realtime` | 0xquinto/supabase-realtime-skill | reference | 只读来交叉校验 Realtime 主题覆盖面；其 wall-clock 事实有误，正文全部改从官方文档取证 |
| `supabase-setup-mcp` | mathruffian-dot/supabase-connect-skill | reference | 只读来交叉校验「建表即开 RLS 并验证」这条红线的覆盖面；其面向零基础终端用户的引导流程不合入 |

## 基线缺口

无 skill（`uv run tools/run_evals.py supabase --baseline`，claude-opus-5 / medium，
`/tmp/hs-evals/supabase/anthropic-claude-opus-5-medium/baseline/`）时，各场景未达成的
`expected_behavior`。**基线答复整体很强**——它自己起了 Postgres 容器复现 RLS、起了 stub 服务验证
Storage 调用序列，所以缺口都不是「答不出来」而是「Supabase 侧的当前形态与静默失败没覆盖到」：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 RLS/`auth.uid()` 排查（4/7） | ③ publishable/anon 与 secret/service_role 的区别、secret 绕过 RLS 且绝不下发到客户端 | 全篇没提 secret / `service_role`，只说了「以 anon 身份查库」。key 模型这一层完全缺席 |
| 1 | ⑤ 中「per-cookie 的 `get`/`set`/`remove` 适配器已被 `getAll`/`setAll` 取代」这一半 | 它抓到了缺 proxy/middleware 与 `cookies()` 未 await（都对），但把 `set`/`remove` 只当成「RSC 里 cookie store 只读会抛异常」，没有指出这个适配器形状本身已经过时 |
| 1 | ⑦ 缺 `GRANT` 是 `42501` 权限错、策略不匹配是空结果 | 两种失败的可观察差异没写，所以「空结果」这个入口没有被排除 grant 的分支 |
| 2 Edge Function（5/7） | ③ `SUPABASE_SECRET_KEYS` 是当前注入形式、`SUPABASE_SERVICE_ROLE_KEY` 是 legacy 路径 | 它正确指出了用 service_role 建 client 会绕过 RLS 造成越权，但改写后的代码用 `SUPABASE_ANON_KEY`，把 legacy key 当成当前做法；也没提 `withSupabase` / `ctx` |
| 2 | ⑦ 运行时限额（内存 256MB、CPU time ~2s、wall clock 按计划分档、idle 150s） | 一条限额都没提，长第三方调用的风险也没标 |
| 3 Storage（6/7） | ⑥ 签名 URL 用项目独立的内部密钥，轮换/停用 Auth 密钥或切换签名算法都不会使其失效，提前吊销只能找官方支持 | **基线在这里给了相反的错答**：它声称 token 是用「项目 JWT secret」签的，并把「轮换项目 JWT secret 会同时废掉全部签名 URL 和全部用户会话」列为可选处置。官方文档明确说签名 URL 用独立密钥、不受 Auth 密钥变更影响。这是本 skill 唯一一处「基线不只是漏答而是答错」的缺口 |
| 4 CLI/声明式迁移（4/6） | ⑤ 已部署的变更要回滚：改 schema 文件再生成前向迁移，不重写历史；且要逐句 review 破坏性语句 | 它只讲了本地 `db reset` 路线，完全没有区分「本地还在迭代」与「已经推到生产」。它对 `migration up` 会 `column already exists` 的判断是对的且很好 |
| 4 | ⑥ 变更后重新生成 TypeScript 类型 | 没提 `supabase gen types` |
| 5 负例（纯 SQL 调优，3/3） | —（本场景只用于确认不误触发） | 基线按 Postgres 调优正常作答：读出 parallel seq scan 与 1,188,402 次块读，给 `(event_type, occurred_at) INCLUDE (tenant_id)` 并解释列序与 index-only scan 的前置条件。`--no-skills` 下 `skill_read` 恒为 false |

合计 8 条未达成行为分布在 4 个正例场景上，其中场景 3 的第 6 条是基线**答错**而非漏答。

## 评测结果

模型固定 `anthropic/claude-opus-5` + `medium`（`tools/run_evals.py` 默认，两次运行未传
`--model` / `--thinking`）。产物：`/tmp/hs-evals/supabase/anthropic-claude-opus-5-medium/{baseline,skill}/<n>/answer.md`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 RLS/`auth.uid()` 排查 | claude-opus-5:medium | 无（baseline） | false | 4 / 7（①②④⑥） | 会话链路诊断很到位（`getSession()` 解构错误、缺 middleware、`cookies()` 未 await），但缺 key 模型、缺 `getAll`/`setAll`、缺 grant 与策略两种失败的差异 |
| 1 | claude-opus-5:medium | 有 | true | **7 / 7** | 开篇即「SQL 编辑器不是对照组，它以 `postgres` 角色运行带 `BYPASSRLS`」，并单列一条「不是 GRANT 问题：缺 GRANT 是 `42501`，策略不匹配才是 `200` + `[]`」；明确指出 `get/set/remove` 已被 `getAll`/`setAll` 取代且旧形态会写坏分块 cookie；给 A/B 两条 `curl` 判定分叉；末尾点明 `NEXT_PUBLIC_..._ANON_KEY` 是退役中的 legacy 对，且不得用 secret key 或 `SECURITY DEFINER` 让症状消失 |
| 2 Edge Function | claude-opus-5:medium | 无（baseline） | false | 5 / 7（①②④⑤⑥） | 把 `SUPABASE_ANON_KEY` 当当前做法；一条运行时限额都没提 |
| 2 | claude-opus-5:medium | 有 | true | 6 / 7（补上③） | 改用 `withSupabase` + `ctx.supabase` / `ctx.supabaseAdmin`，代码里不再出现任何 key（③ 的「或」分支达成）；`verify_jwt` 拆成两个函数并给出 `config.toml`；仍未提运行时限额（⑦ **未达成**，SKILL.md 规则 22 有写但模型没展开） |
| 3 Storage | claude-opus-5:medium | 无（baseline） | false | 6 / 7（①②③④⑤⑦） | ⑥ **答错**：声称签名 URL 由「项目 JWT secret」签发、轮换该 secret 会同时废掉全部签名 URL 与全部用户会话 |
| 3 | claude-opus-5:medium | 有 | true | **7 / 7** | ⑥ 被纠正为官方口径：「签名 URL 用项目专属的内部签名密钥，和 Auth 的 JWT 签名密钥是两套东西；轮换 Auth 密钥、禁用 legacy key、切换 HS256 → 非对称签名都不会让它失效，提前作废需要联系 Supabase support」；并据此推出 60s TTL + 每次访问重新签发，而不是签长 TTL |
| 4 CLI/声明式迁移 | claude-opus-5:medium | 无（baseline） | false | 4 / 6（①②③④） | 只讲本地 `db reset` 路线，未区分「本地迭代」与「已部署」；未提重新生成类型 |
| 4 | claude-opus-5:medium | 有 | true | 5 / 6（补上⑥） | 补上 `supabase gen types typescript --local`，并额外追问「你点的是哪个 Studio」（本地栈 vs 生产漂移），顺带发现夹具的视图缺 `security_invoker`、两张表既无 RLS 也无 grants。⑤ 仍**未达成**：给了 `db pull` 对齐漂移与「生成的 `drop column` 会带走数据」，但没写出「已部署只向前滚：改 schema 文件再生成前向迁移」这条 |
| 5 负例（纯 SQL 调优） | claude-opus-5:medium | 无（baseline） | false | 3 / 3 | — |
| 5 负例 | claude-opus-5:medium | 有（`--skills supabase` 可用但不应加载） | **false** | 3 / 3 | 未加载本 skill。全程只有 EXPLAIN 判读、`(event_type, occurred_at, tenant_id)` 复合索引与 Index Only Scan 的前置条件、可选偏索引；没有任何 RLS / key / Edge Function / CLI 内容渗入 |

结论：**通过**。8 条基线未达成的行为中有 6 条在有 skill 时达成（场景 1 的 ③⑤⑦、场景 2 的 ③、
场景 3 的 ⑥、场景 4 的 ⑥），其中场景 3 的 ⑥ 是把基线的**错误事实**纠正为官方口径。
负例场景 `skill_read == false` 且答复未被本 skill 污染。

仍未被填补的 2 条，如实记录不当作达成：

- 场景 2 ⑦（Edge Function 运行时限额）：SKILL.md 核心规则 22 与
  `references/edge-functions.md` 都写了，但该场景的问题重心在 CORS 与 webhook 上，模型没有
  主动展开限额。属于「skill 里有、该次答复没用上」，不改评测也不改正文。
- 场景 4 ⑤（已部署变更的回滚方向）：`references/cli-and-migrations.md` 的
  「Deploying and rolling back」一节写得明确，但模型这次把注意力放在「Studio 改的是本地还是
  生产」的分叉上。同上，属未展开而非缺失。

另有一处在「有 skill」评测**之后**做的正文修改，如实记录：场景 1 的答复在末尾复述了官方 skill
那条错误主张（「UPDATE 只有 `USING` 没有 `WITH CHECK` ⇒ 拥有者可以把 `owner_id` 改成别人」）。
该次答复只加载了 SKILL.md，没有展开 `references/rls-and-data-api.md`（纠正写在那里），而当时
SKILL.md 的 workflow 只写「give `UPDATE` policies both `USING` and `WITH CHECK`」，没有带上机理。
因此把那一条改成带机理的版本（Postgres 在 `WITH CHECK` 缺失时复用 `USING`，所以省略是「收窄了
意图表达」而不是「开了写入口子」）。这处修改不涉及任何被判定的 `expected_behavior`
（五个场景都没有一条与 `WITH CHECK` 相关），因此上表结论不受影响；但下次同步时值得复跑场景 1
确认这条错误主张不再出现。


## 备注

### 与 `postgres` skill 的去重

同波 `postgres` skill 取用 `supabase/agent-skills` 的 `skills/supabase-postgres-best-practices`
（索引类型、覆盖索引、部分索引、`EXPLAIN ANALYZE`、`pg_stat_statements`、vacuum、锁与 `skip locked`、
连接池与 prepared statements、批量插入、N+1、分页、JSONB 索引、全文检索、RLS 性能）。
本 skill **一条都不写**，并在 `## Scope` 用双方原文一致的分界句交接：

> RLS policy syntax and its performance are the `postgres` skill's subject; the Supabase auth
> context (`auth.uid()`, JWT claims) and the dashboard/CLI workflow around it are the
> `supabase` skill's.

已与 `PostgresSkill` 子代理通过 `hub` 对齐：两边同一句、同样的两行折行，逐字节一致；
对方确认 SQL 调优 / 索引选择 / EXPLAIN / 连接池 / pgvector / RLS 策略语法与性能归它。
`references/rls-in-supabase.md` 只写 Supabase 语境（`auth.uid()` / `auth.jwt()` / 自定义 claim /
`TO` 子句 / grants 与 Data API 暴露 / view 与 `SECURITY DEFINER` 的绕过 / 用 publishable key 实证），
`(select auth.uid())` 的性能机理只给一句结论并指向 `postgres`。

### CLI 当前形态的核实结果

- `gh api repos/supabase/cli/releases`：最新非预发布的 `v*` 标签是 **v2.117.0**（2026-09-07）。
  同日还有 `v2.118.0-beta.21` 等预发布，以及独立的 `config-v0.6.0` 系列标签（`config` 包自己的版本线，
  不是 CLI 版本）。
- `supabase/cli` 仓库根**没有 LICENSE 文件**（`gh api repos/supabase/cli/license` → 404，
  根目录列表里也没有），仓库已重构为 bun/pnpm 的 TS monorepo（`apps/`、`packages/`、`mise.toml`）。
  本 skill 不合入该仓库任何文本，因此不作为上游列入 `SOURCES.yaml`；CLI 事实全部从
  `supabase.com/docs` 取证。**下次同步要注意**：官方 skill 里的 CLI 版本门槛
  （`db query` 需 v2.79.0+、`db advisors` 需 v2.81.3+）在 v2.117 下已无意义，正文按标准
  第 3 节不写这类时间敏感表述。
- `supabase functions new` 生成的模板已经是 `export default { fetch: withSupabase(...) }`
  （官方 quickstart 正文），不是 `Deno.serve`；`supabase functions deploy` 在没有 Docker 时
  自动回退到 API 部署，也可显式 `--use-api`。

### Auth 当前形态的核实结果

- `@supabase/auth-helpers` 已被 `@supabase/ssr` 取代；官方 SSR 文档只给 `@supabase/ssr`，
  且 cookie 适配器只有 `getAll`/`setAll`。单 cookie 的 `get`/`set`/`remove` 形式已不在官方文档里出现，
  本 skill 把它写进 `## Old patterns` 折叠块。
- 身份验证函数的当前推荐是 `getClaims()`（新项目默认非对称签名密钥，本地 WebCrypto 验签 + 缓存 JWKS），
  不是 `getUser()`；`getSession()` 的 user 对象明确不可用于授权。
- Next.js 侧官方文档现在称之为 **Proxy**（`proxy.ts`）而不是 middleware；本 skill 用
  「proxy (formerly middleware)」的写法，避免读者在旧项目里找不到文件。
- API key：`sb_publishable_...` / `sb_secret_...` 为当前形态，legacy `anon`/`service_role`（JWT，`eyJ` 开头）
  计划 2026 年底弃用，两套并存且创建新 key 不吊销旧 key。secret key 带浏览器 UA 会被判 401。

### 许可注意

- `supabase.com/docs` 的内容源在 `supabase/supabase` 的 `apps/docs`；实读仓库根 LICENSE 为
  Apache-2.0，`apps/docs` 下没有另一份 LICENSE，因此按 Apache-2.0 处理为 `merged`（不逐字复制）。
- `braindesmond5-boop/supabase-rls-audit` 与 `anymikey/supabase-security-audit` 的 SKILL.md frontmatter
  没有 `license` 字段，但仓库根有 MIT LICENSE 文件（API `license: MIT`），按仓库许可算 MIT。
- `supabase-community/supabase-plugin`（API `license: null`）本可按「无许可但公开」合入，
  但它与官方 skill 逐字节相同，作为独立上游没有意义，REJECT 而非 `license: NONE`。
- 本次没有 GPL/LGPL/AGPL/CC-BY-SA/MPL/专有上游，无需相应的 `notes` 或首行注释。

### 放弃的方向

- **自托管 Supabase**（Docker Compose、Kong、Supavisor、pgsodium 密钥卷）：magnus919 覆盖得不错，
  但属于托管控制面/运维，本 skill 边界外，且事实无法在本仓库复核。
- **MCP 服务器排障**（官方 skill 里有一节）：属于 agent 工具配置而不是 Supabase 工程，
  且写进正文会让 skill 依赖某个 MCP 服务器可用。正文只在 CLI 命令旁提一句「若项目已接 MCP，
  `execute_sql` / `get_advisors` 是等价入口」。
- **pgvector / 队列 / cron 的深度用法**：向量与纯 SQL 侧归 `postgres`；本 skill 只在
  「Data API 暴露与扩展」处提一句。
- **Firebase 对照迁移**：`firebase` 主题已被用户暂缓，没有对应 skill，`## Scope` 里只直述不覆盖。

### 评测构造过程中的一次修改（如实记录）

第一轮 baseline 跑完后，场景 3（Storage）5 条 `expected_behavior` **全部达成**，没有区分度。
按 `docs/workflow.md` Phase B「若基线全部达成，改写评测直到出现缺口」处理：在 query 末尾追加
「这个 URL 该用多长有效期？泄露了能吊销吗？」，并加了两条 `expected_behavior`（签名 URL 的独立
签名密钥与吊销、由此推导有效期），然后**只重跑了场景 3 的 baseline**。第一次重跑的 `answer.md`
在 `## Fix` 处被截断（`status: ok` 但正文不完整），不可用于判定，因此又重跑一次拿到完整答复才判分。
其余四个场景的 baseline 未改动、未重跑。
