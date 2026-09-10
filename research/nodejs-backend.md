# nodejs-backend 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"Fastify agent skill SKILL.md github claude skills"`、`"NestJS claude agent skills SKILL.md github repository"`
  - <https://www.skills.sh>（经搜索结果聚合站 skillmd.com / truefoundry skills-registry 间接命中）
  - VoltAgent/awesome-agent-skills、addyosmani/agent-skills
  - 领域官方组织仓库：`nodejs/`、`fastify/`、`nestjs/`、`honojs/`、`expressjs/`、`platformatic/`
    （逐个查 `git/trees` 确认：`fastify/fastify`、`nestjs/nest`、`honojs/hono` 三个框架主仓
    **都没有** `.agents/skills` 或 `skills/` 目录，所以本 skill 没有「框架官方 skill」，
    官方权威只能来自文档仓库）
  - `github/awesome-copilot`（`instructions/nestjs`、`instructions/nodejs-javascript-vitest`）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`

### 运行时与框架版本核对（写正文前先定基线）

用 `gh api repos/nodejs/Release/contents/schedule.json` 与 `gh api repos/nodejs/node/releases` 取值：

| 线 | 状态（2026-09-11） | 依据 |
|---|---|---|
| Node 26.x | Current（26.8.2，2026-09-09） | `releases` 里标 `(Current)`；`schedule.json` 的 `v26.lts` = 2026-10-28，尚未到 |
| Node 24.x 'Krypton' | **Active LTS**（24.21.0，2026-09-08） | `v24.lts` = 2025-10-28，`v24.maintenance` = 2026-10-20 |
| Node 22.x 'Jod' | Maintenance LTS | `v22.maintenance` = 2025-10-21 |
| Node 20.x 'Iron' | 已 EOL | `v20.end` = 2026-04-30 |

所以正文的版本底线写 **Node 24 LTS**，并在需要时标 `(Node 22+)` 之类的可用性底线。

框架当前版本（`npm view <pkg> version` + `gh api .../releases/latest` 双取）：
Fastify `5.12.3`（`fastify/fastify` 的 `v6.0.0-alpha.3` 是预发布，不作基线）、
NestJS `@nestjs/core 12.0.1`、Hono `4.13.7`、Express `5.2.1`（`latest-4` 仍为 `4.22.2`）、
pino `10.3.1`。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | mcollina/skills `skills/node` | https://github.com/mcollina/skills | 1913 | 2026-08-17 | MIT | 通用 Node 层：错误、streams、优雅关机、配置、profiling、type stripping | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | Matteo Collina 是 Node.js TSC 成员与 Fastify 作者；`rules/` 15 个文件全是可执行规则与陷阱（`--env-file`、`loadEnvFile`、NODE_ENV 反模式、`pipeline` + async generator、drain 背压）。抽查 `--env-file`/`loadEnvFile`/`pipeline` 三条全部对得上 nodejs/node 的 `doc/api` |
| 2 | mcollina/skills `skills/fastify` | https://github.com/mcollina/skills | 1913 | 2026-08-17 | MIT | Fastify 分支：封装、hooks、schema、decorators、inject 测试 | 3 | 3 | 3 | 2 | 2 | 13 | INCLUDE | 框架作者本人写的，权威等同官方。扣 1 分正确性：`rules/hooks.md` 把数据库事务的 `commit` 放在 `onResponse`（响应已发出，commit 失败无法回报），与 Fastify `docs/Reference/Hooks.md` 对 `onResponse` 的定义冲突，见裁决 3 |
| 3 | mcollina/skills `skills/nodejs-core` | https://github.com/mcollina/skills | 1913 | 2026-08-17 | MIT | 给 `nodejs/node` 本身提 PR：V8/libuv/N-API/node-gyp/DCO | 3 | 3 | 3 | 3 | 2 | 14 | REJECT（范围） | 分数最高但主题是「贡献 Node 核心」，不是「用 Node 写后端服务」。整份内容（`make lint`、`core-validate-commit`、HandleScope）对本 skill 的读者零价值。留行以免后续批次重复讨论 |
| 4 | mcollina/skills `skills/oauth` | https://github.com/mcollina/skills | 1913 | 2026-08-17 | MIT | Fastify 上的 OAuth 2.0/2.1 流程（PKCE、refresh rotation、introspection） | 2 | 3 | 3 | 2 | 2 | 12 | REJECT（范围） | 内容质量高，但 OAuth 流程属于认证协议实现，不是「通用后端层 + 框架分支」。塞进来会把 SKILL.md 挤爆，且本库尚无对应 skill；正文只保留「auth 挂在哪个 hook / guard」这一层，不写协议 |
| 5 | Kadajett/agent-nestjs-skills `skills/nestjs-best-practices` | https://github.com/Kadajett/agent-nestjs-skills | 273 | 2026-07-23 | NONE（API `license: null`，仓库无 LICENSE 文件） | NestJS 分支：40 条规则 / 10 类 | 1 | 2 | 3 | 3 | 0 | 9 | INCLUDE（merged, `license: NONE`） | 每条规则都是 incorrect/correct 对照。抽查三条对照 docs.nestjs.com 全对：`Scope.REQUEST` 沿注入链向上冒泡、`app.enableShutdownHooks()` 是 `onModuleDestroy` 生效的前提、exception filter 集中处理。`rules/di-scope-awareness.md` 自己给出「Best: ClsService（AsyncLocalStorage），provider 保持 singleton」的阶梯，正是本 skill 想要的裁决方向 |
| 6 | secondsky/claude-skills `plugins/hono-routing` | https://github.com/secondsky/claude-skills | 217 | 2026-09-09 | MIT | Hono 分支：路由、middleware、验证器、RPC、12 个高频错误 | 1 | 3 | 3 | 1 | 2 | 10 | INCLUDE（需裁决） | 唯一成体系的 Hono 上游，错误清单（middleware 忘记 `await next()`、`c.req.valid` vs `c.req.json`、`Variables` 类型）确实是真实坑。正确性只给 1：①「validation hooks deprecated，只能用 middleware」是错的，`zValidator(target, schema, hook)` 是 honojs/middleware 当前文档化的 API；②它标为「✅ 正确」的 middleware 例子缺 `async` 却写着 `await next()`，照抄即语法错误。见裁决 1、2 |
| 7 | github/awesome-copilot `instructions/nestjs.instructions.md` | https://github.com/github/awesome-copilot | 38862 | 2026-09-10 | MIT | NestJS 目录结构、命名约定、DTO/守卫/过滤器骨架 | 3 | 3 | 1 | 2 | 2 | 11 | INCLUDE（只取结构） | GitHub 官方仓库，但这份是教程体（"Your Mission"、`@Controller` 怎么写），模型本来就会。只取两样：`*.controller.ts`/`*.service.ts`/`*.module.ts` 命名约定与 `common/ modules/ shared/` 目录形态。扣正确性 1 分：`@UsePipes(ValidationPipe)` 不带 `whitelist`，且把 TypeORM 当作唯一 ORM |
| 8 | github/awesome-copilot `instructions/nodejs-javascript-vitest.instructions.md` | https://github.com/github/awesome-copilot | 38862 | 2026-09-10 | MIT | 30 行 JS 风格偏好 + 「用 Vitest」 | 3 | 3 | 1 | 1 | 2 | 10 | REJECT（内容） | 分数够但实质是个人风格清单（"Never use `null`, always use `undefined`"、"Prefer functions over classes"），与 mcollina 的 `rules/testing.md`（默认 `node:test`）直接冲突且没有依据。取它会让 skill 出现第二套约定 |
| 9 | myatminlu/vector-skills `skills/nestjs-dev-guidelines` | https://github.com/myatminlu/vector-skills | 18 | 2026-08-22 | MIT | NestJS 42 个 reference：错误分类、验证、日志、分页、安全 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 星数低但信息密度最高的 NestJS 上游。`10-error-handling.md` 里两条非显然事实——全局 exception filter 必须按 `host.getType()` 分支（它在 BullMQ worker / gateway / microservice 上下文也会被调用），以及必须在 `response.headersSent` 时跳过写入（流式响应）——在其他任何候选里都没有 |
| 10 | TheCodePace/fastify-skills `skills/fastify-best-practise` | https://github.com/TheCodePace/fastify-skills | 12 | 2026-09-01 | NONE（无 LICENSE 文件） | Fastify：Zod type provider、multipart、autoload、http-proxy | 1 | 3 | 3 | 2 | 0 | 9 | INCLUDE（merged, `license: NONE`） | 与 mcollina 的 Fastify skill 高度重叠，唯一增量是 `fastify-type-provider-zod` 这条「用 Zod 而不是手写 JSON Schema 时的正确接法」，以及响应序列化的兼容性注意。其余照 mcollina |
| 11 | platformatic/skills | https://github.com/platformatic/skills | 3 | 2026-06-26 | Apache-2.0 | Platformatic Watt / Kafka 产品用法 | 2 | 1 | 2 | 2 | 2 | 9 | REJECT（产品包装） | `skills/watt`、`skills/kafka` 教的是 Platformatic 自家运行时（含 `references/deployment/cloud.md`），属产品说明书。与本仓库「排除 SaaS/产品包装类」一致 |
| 12 | amirtaherkhani/nestjs-agent-skills | https://github.com/amirtaherkhani/nestjs-agent-skills | 4 | 2026-08-02 | MIT | NestJS 架构：模块边界、依赖方向、架构阶梯、DI | 1 | 2 | 2 | 3 | 2 | 10 | INCLUDE（部分） | 写得克制且有 evals，「先读 `package.json`/`nest-cli.json`/bootstrap 再判断架构，不要凭目录名给项目贴 Clean Architecture 标签」这条被采纳成 Core rule 1 的 NestJS 分支说法。扣具体性 1 分：每个 SKILL.md 开头是长篇「pre-execution conflict guard」，绑定它自家 skill 家族，必须整段剥离 |
| 13 | giuseppe-trisciuoglio/developer-kit-claude-code `plugins/developer-kit-typescript` NestJS 部分 | https://github.com/giuseppe-trisciuoglio/developer-kit-claude-code | 343 | 2026-09-10 | MIT | NestJS 架构/安全/测试 rules + agents | 1 | 3 | 2 | 2 | 2 | 10 | MAYBE → reference | 内容以 `agents/*.md`（子代理人格）和 `rules/*.md` 为主，属 agent 编排而非规则清单；NestJS 规则与候选 5/9 重复。只用来交叉校验 clean-architecture 一节，不合入文字 |
| 14 | benedya/nestjs-skills | https://github.com/benedya/nestjs-skills | 0 | 2026-07-18 | NONE | NestJS + TypeORM 分层约定 | 0 | 2 | 2 | — | 0 | 4 | REJECT | 零采纳、无许可、且把 TypeORM 写成前提；正确性未抽查（总分已 ≤4） |
| 15 | Kianibound/nestjs-playbook-skill | https://github.com/Kianibound/nestjs-playbook-skill | 0 | 2026-08-05 | MIT | NestJS 端到端 playbook（模块→认证→部署） | 0 | 2 | 1 | — | 2 | 5 | REJECT | 教程式一条龙，规则密度低，零采纳。与候选 5 完全被覆盖 |
| 16 | 2muchcoffeecom/nestjs-manifesto | https://github.com/2muchcoffeecom/nestjs-manifesto | 0 | 2026-05-12 | MIT | NestJS 团队规范 | 0 | 1 | 1 | — | 2 | 4 | REJECT | 4 个月未推送、零采纳、是某公司内部 manifesto |
| 17 | nodejs.org/docs（源仓 `nodejs/node` `doc/api`） | https://nodejs.org/docs/latest-v24.x/api/ | 121165 | 2026-09-10 | MIT（API 报 `NOASSERTION`；实读 `LICENSE` 首段为完整 MIT 文本，其后是 bundled deps 的许可） | 运行时权威：`async_context`、`stream`、`cli`、`process`、`test` | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | 每条版本敏感断言的最终依据。已实读并据此改写：`--unhandled-rejections` 默认自 v15.0.0 起为 `throw`（未处理即 uncaught exception）；`enterWith()` 会污染同一同步执行里后续的事件处理器，所以默认用 `run()`；`withScope()`（v24.20.0 / v25.9.0，Experimental）配 `using`；`AsyncLocalStorage` 上下文丢失的定位手法 |
| 18 | fastify.dev docs（源仓 `fastify/fastify` `docs/Reference`） | https://fastify.dev/docs/latest/ | 37101 | 2026-09-10 | MIT | Fastify 分支权威 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | 提供了社区上游全部没写、却是本 skill 最有价值的一条事实：默认 error handler 把 `error.message` 与 `error.code` **原样**发给客户端（含 500），Fastify 不区分 dev/prod；同时给出 `FST_ERR_DEC_REFERENCE_TYPE`（`decorateRequest` 传引用类型直接启动失败）、`forceCloseConnections` 默认 `"idle"`、`handlerTimeout` 与 `request.signal` 的协作取消语义 |
| 19 | docs.nestjs.com（源仓 `nestjs/docs.nestjs.com`） | https://docs.nestjs.com | 1369 | 2026-09-10 | MIT | NestJS 分支权威 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | `content/fundamentals/provider-scopes.md`：REQUEST 沿注入链冒泡、性能影响、durable providers、WebSocket gateway / Passport strategy / cron controller 不能用 request scope。`content/fundamentals/lifecycle-events.md`：关机钩子默认关闭，必须 `enableShutdownHooks()`；`app.close()` 不会结束进程 |
| 20 | hono.dev（源仓 `honojs/website`，验证器 API 另读 `honojs/middleware`） | https://hono.dev/docs/ | 178 | 2026-09-03 | MIT | Hono 分支权威 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | 裁掉候选 6 的两个错误所依据的原文：`validator()` 手写回调、`zValidator(target, schema, hook)`、`json`/`form` 校验要求请求带匹配的 `content-type`（否则回调收到 `{}`，测试里最容易踩）、`header` 目标的键必须小写、`contextStorage()` 基于 `AsyncLocalStorage` 且 Cloudflare Workers 需要 `nodejs_als` 标志 |

## 深度审查

**mcollina/skills（候选 1、2 = 主干）** — 结构是 `SKILL.md` + `rules/*.md`，SKILL.md 只当索引用（"How to use: read individual rule files"），实质全在 rules 里，共 10382 行。frontmatter 只有 `name`/`description`/`metadata.tags`，没有 `license`，`tags` 是专属字段需剥离；另有 `tile.json` 是其自家展示元数据，不进 `paths`。质量分层明显：`node/rules/{streams,environment,graceful-shutdown,error-handling}.md` 是本 skill 通用层的骨架，`node/rules/typescript.md`（type stripping）与 `fastify/rules/{plugins,hooks,decorators,schemas,testing}.md` 是分支骨架；`node/rules/node-modules-exploration.md` 与 `fastify/rules/{websockets,http-proxy}.md` 超出边界，不取。与其他候选的重叠：`skills/typescript-magician` 已是本仓库 `typescript` skill 的上游，本 skill 的 `paths` 只列 `skills/node` 与 `skills/fastify` 两棵子树，不重叠。写作上有一个必须改的倾向：它把三个具名库（`close-with-grace`、`@fastify/create-error`、`async-cache-dedupe`）写成硬性前提。本 skill 按标准第 3 节「只给一个默认方案 + 一个逃生口」处理——不变量写成「关机必须排空、错误必须带稳定 code」，库只作为默认实现出现一次。

**Kadajett/agent-nestjs-skills（候选 5）** — 40 个 `rules/<prefix>-<name>.md`，每篇 frontmatter 带 `title`/`impact`/`impactDescription`/`tags`（全是专属字段，剥离），正文严格 incorrect→correct→Reference 三段，每篇末行链回 docs.nestjs.com，便于逐条核对。仓库根还有一个 163 KB 的 `AGENTS.md` 全量编译产物，不进 `paths`。无 LICENSE 文件 → 按许可规则 `license: NONE` + notes 合入，且不复制任何段落。它的 `perf-async-hooks.md` 同时点出两件事：`onModuleInit()` 里 fire-and-forget 的 `this.connect()` 会让模块在池可用之前就报 ready；重活不要放构造函数。这两条直接进了 NestJS 分支。

**myatminlu/vector-skills（候选 9）** — 唯一带 `evals/`（含 `grade.py`）的 NestJS 上游，reference 用 `NN-topic.md` 编号命名，每篇有 TL;DR + Why it matters。它的错误分类（HTTP status + 命名空间化 `code` + `traceId`，客户端只 switch `code` 从不 switch `message`）比其他候选完整一档。注意它绑定了 `nestjs-pino`，并明确指出 `@nestjs/common` 的 `Logger` 不接受结构化元数据签名会把对象 stringify——这条是真陷阱，进 NestJS 分支。它的分页/过滤/排序与「标准响应包裹」属 REST 契约设计，本 skill 不覆盖，不取。

**secondsky/claude-skills `plugins/hono-routing`（候选 6）** — 508 行单文件 SKILL.md + 6 个 reference + 9 个 template + `scripts/check-versions.sh`。frontmatter 里 `package_version`/`last_verified`/`errors_prevented`/`templates_included`/`keywords` 全是专属字段。正文大量 ✅/❌ emoji 清单与 "Status: Production Ready ✅" 徽章，按标准要全部重写。它把版本钉死在 `hono@4.12.12`（正文写 `bun add hono@4.12.12`），当前是 4.13.7——本 skill 不写钉版命令。两处实质错误见裁决 1、2。可取的是错误清单的**问题面**：middleware 断链、`c.req.valid` 的取数时机、`Hono<{ Variables }>` 的类型声明位置、RPC 需要 `export type AppType = typeof routes`。

**github/awesome-copilot `instructions/nestjs`（候选 7）** — Copilot instruction 文件，`applyTo` 是 glob 专属字段。406 行里可用的不到 30 行。它的价值是「GitHub 官方仓库背书的目录/命名约定」，这类约定不需要权威也不会错，正好补齐 Kadajett 与 amirtaherkhani 都跳过的项目形态。

**官方文档三家（候选 18、19、20）** — 都能直接读到源仓库并确认 MIT：`fastify/fastify`（docs 就在主仓 `docs/`）、`nestjs/docs.nestjs.com`（`content/`）、`honojs/website`（`docs/`）。因此 `relation` 全部为 `merged`，不是 `reference`——本 skill 大部分版本敏感事实的确来自它们。`nodejs/node` 的 API 返回 `NOASSERTION`，实读 `LICENSE` 确认首段是完整 MIT 授权文本（其后追加 joyent 与 bundled deps 的许可），按规则填真实 SPDX id `MIT`。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | Hono 验证失败时怎么定制响应 | secondsky（候选 6）：「validation hooks 已弃用，只能用 middleware 验证器」；官方：`validator(target, cb)` 手写回调与 `zValidator(target, schema, hook)` 都是当前 API | **hook 就是官方定制入口**。正文写：用验证器 middleware 取数（`c.req.valid()`），需要统一错误体时给验证器传第三个 hook 参数并在其中 `throw new HTTPException(...)`；不存在「hooks 弃用」 | hono.dev `docs/guides/validation.md` 全篇是 `validator()` 回调；`honojs/middleware` 的 `packages/zod-validator/README.md` 明确列出 "Hook:" 与 "Throw Error:" 两段用法。官方 > 社区 |
| 2 | secondsky 标为「✅ 正确」的 middleware 写法 | 候选 6：`app.use('*', (c, next) => { ... await next() })` | 该写法语法错误（非 async 函数里 `await`）。正文只给 `async (c, next) => { …; await next() }` 一种形态，并把「忘记 `await next()`」单独立为一条规则，因为它的症状是路由静默不执行而不是报错 | hono.dev `docs/guides/middleware`；候选 6 自身的正例即为反证 |
| 3 | 数据库事务在哪里提交（Fastify） | mcollina `fastify/rules/hooks.md`：`preHandler` 开事务、`onResponse` 提交、`onError` 回滚 | **提交必须发生在响应之前**，即 handler/service 边界内；`onResponse` 只做日志与指标。理由：`onResponse` 在响应已发出后运行，此时 commit 失败无法改变已返回的 2xx，客户端拿到成功却没有落库 | `fastify/fastify` `docs/Reference/Hooks.md` 定义 `onResponse` 在响应发送完毕后执行且不能修改响应；官方文档 > 上游示例（同一作者，取更新更权威的那份） |
| 4 | 未处理的 promise rejection 要不要自己挂 handler | mcollina `node/rules/error-handling.md`：「不要手动处理 `unhandledRejection`/`uncaughtException`，交给 `close-with-grace`」；Node 文档：默认模式 `throw`，没有 handler 就升级为 uncaught exception | 两者不冲突，但必须把默认行为写出来才可操作。正文：默认模式下未处理的 rejection 会终止进程（自 Node 15），所以不要为了「不崩」而挂一个吞掉错误的 handler；关机协调器（`close-with-grace` 或框架自带的 `enableShutdownHooks`）只负责收到信号/致命错误后**排空再退出** | `nodejs/node` `doc/api/cli.md` `--unhandled-rejections=mode`（changes: v15.0.0 默认改为 `throw`）。官方 > 专家 |
| 5 | `NODE_ENV` 该不该用 | mcollina `node/rules/environment.md`：`NODE_ENV` 是反模式，一个变量混了日志/安全/基础设施四种关切；Express 与 NestJS 生态大量以 `NODE_ENV` 分叉行为 | 采纳 mcollina 的默认（每个关切一个显式变量，配 schema 校验），同时写清 `NODE_ENV` 仍然真实影响的一处：包管理器的生产安装与部分框架/库自身的默认值，所以别删它，只是不要把业务行为挂上去 | 公认专家的设计主张 + 生态既有事实；两边都保留才不会给出「删掉 NODE_ENV」这种会坏事的建议 |
| 6 | NestJS 里怎么拿请求作用域上下文 | Kadajett `di-scope-awareness.md` 给出阶梯：可变 singleton（错）→ `Scope.REQUEST` + `@Inject(REQUEST)` → `nestjs-cls`（最佳）；官方文档强调 REQUEST 会沿注入链冒泡并有性能代价，另给 durable providers | **默认 `AsyncLocalStorage`**（直接用或经 `nestjs-cls`），provider 保持 singleton；`Scope.REQUEST` 是逃生口，且必须同时说出「冒泡到控制器」这个代价。durable providers 只在多租户按 tenant 聚合的场景提一句 | docs.nestjs.com `fundamentals/provider-scopes.md`「The `REQUEST` scope bubbles up the injection chain」+ Performance / Durable providers 两节；与候选 5 自己的结论一致 |
| 7 | 用哪个校验库 | mcollina：JSON Schema / TypeBox + `env-schema`；secondsky 与 TheCodePace：Zod；awesome-copilot：class-validator | 不变量是「每个入口都有 schema，并且响应也过 schema」，默认用**框架原生的那一套**（Fastify = JSON Schema、NestJS = class-validator + `ValidationPipe({whitelist:true})`、Hono = Standard Schema 验证器）；逃生口是 Zod，经框架的 type provider 接入（Fastify 用 `fastify-type-provider-zod`）。不罗列多个可选库 | `docs/skill-standard.md` 第 3 节「只给一个默认方案 + 一个逃生口」；三家官方文档各自的默认 |
| 8 | 错误响应体长什么样 | myatminlu：HTTP status + 命名空间 `code` + `traceId`，客户端只 switch `code`；Fastify 默认：`{statusCode, error, message, code?}` | 只写不变量：一个 API 一种错误体；机器读 `code`（稳定），人读 `message`（可变），运维读 correlation id。**具体字段名与 HTTP 语义属 REST 契约设计，本 skill 不覆盖**，直述 Not covered | 边界表；标准第 3 节「触发条件写 description，正文不越界」 |
| 9 | Express 放在哪 | 备选：把 Express 也做成一个分支 reference | Express 只出现在 `references/express-migration.md`。三条理由：①Express 5.2.1 自身不提供校验、序列化、结构化日志、关机排空，本 skill 每条通用规则落到 Express 上都变成「再装一个库」，规则密度归零；②NestJS 的默认平台就是 Express，Express 的实际用法已被 NestJS 分支覆盖一遍；③新服务在本生态里选 Fastify / NestJS / Hono，Express 的真实需求是「已有服务怎么搬」 | `expressjs/express` 的 `npm dist-tags`（latest 5.2.1，latest-4 4.22.2）+ docs.nestjs.com 的 platform-agnosticism 一节；边界表要求 Express 只在迁移小节出现 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `mcollina-skills` | mcollina/skills（`skills/node`、`skills/fastify`） | merged | 通用层主干：错误分类与 `cause` 链、`pipeline` + async generator + `drain` 背压、优雅关机的顺序（停收→排空→逆序关资源）、`--env-file`/`loadEnvFile`/schema 校验/每关切一个变量的配置法、profiling 入口（`--cpu-prof`、堆快照）、卡死进程与 flaky 测试的诊断路径、type stripping 的兼容约束；Fastify 分支主干：插件封装与 `fastify-plugin` 的边界、hook 顺序与作用域、decorator 三种类型与请求上下文的初始化时机、`inject()` 测试、`@fastify/autoload` |
| `kadajett-nestjs` | Kadajett/agent-nestjs-skills | merged | NestJS 分支主干：provider scope 三态与可变 singleton 的跨请求泄漏、`onModuleInit` 不 await 导致模块提前 ready、`enableShutdownHooks()` 是关机钩子的前提、exception filter 的分层（领域异常 → 专用 filter → `@Catch()` 兜底）、DTO 序列化与 pipe 的职责切分、`Test.createTestingModule` 的替身注入 |
| `myatminlu-nestjs` | myatminlu/vector-skills（`skills/nestjs-dev-guidelines`） | merged | 全局 exception filter 的两个必要分支（`host.getType()`、`response.headersSent`）、错误 `code`/`traceId`/`message` 三分职责、`@nestjs/common` 的 `Logger` 不支持结构化元数据这一陷阱 |
| `amirtaherkhani-nestjs` | amirtaherkhani/nestjs-agent-skills | merged | 「先读 `package.json`/`nest-cli.json`/bootstrap 文件与模块图再判断，不要凭目录名给项目贴架构标签」；模块按业务能力而非技术分层切分、公共模块 API 与依赖方向 |
| `thecodepace-fastify` | TheCodePace/fastify-skills | merged | Fastify 用 Zod 时的正确接法（`fastify-type-provider-zod` 作为 type provider，而不是在 handler 里手动 parse）与响应序列化的注意点 |
| `secondsky-hono` | secondsky/claude-skills（`plugins/hono-routing`） | merged | Hono 分支的问题面：middleware 断链、`c.req.valid` 取数时机、`Hono<{ Variables }>` 类型声明位置、RPC 需要导出 `typeof routes`、sub-app 组织（全部经官方文档重写，两处错误已裁掉） |
| `awesome-copilot` | github/awesome-copilot（`instructions/nestjs.instructions.md`） | merged | NestJS 文件命名约定与 `common/ modules/ shared/` 目录形态 |
| `nodejs-docs` | nodejs.org/docs（源仓 `nodejs/node`） | merged | 运行时权威：LTS 基线、`--unhandled-rejections` 默认 `throw`、`AsyncLocalStorage` 的 `run` vs `enterWith` vs `withScope` 与上下文丢失定位、stream/`pipeline` 语义、`node:test`、`--env-file` |
| `fastify-docs` | fastify.dev（源仓 `fastify/fastify` `docs/Reference`） | merged | Fastify 权威：默认 error handler 原样外发 `message`/`code`、`FST_ERR_DEC_REFERENCE_TYPE`、`close()` 与 `forceCloseConnections`/`return503OnClosing`、`handlerTimeout` + `request.signal` 协作取消、schema 序列化的裁剪语义 |
| `nestjs-docs` | docs.nestjs.com（源仓 `nestjs/docs.nestjs.com`） | merged | NestJS 权威：provider scope 冒泡与性能、durable providers、生命周期事件顺序与 `enableShutdownHooks()`、`app.close()` 不终止进程、request scope 的禁用场景 |
| `hono-docs` | hono.dev（源仓 `honojs/website`；验证器 API 另据 `honojs/middleware`） | merged | Hono 权威：`validator()`/`zValidator` 与 hook、`json`/`form` 校验对 `content-type` 的硬要求、`header` 目标键必须小写、`contextStorage()` 与 `AsyncLocalStorage`、Node 适配器 `@hono/node-server` |
| `giuseppe-developer-kit` | giuseppe-trisciuoglio/developer-kit-claude-code | reference | 仅用于交叉校验 NestJS clean-architecture / 分层建议是否与候选 5、12 一致；未取文字 |

被明确拒绝且不再复议：`mcollina/skills` 的 `skills/nodejs-core`（贡献 Node 核心）与 `skills/oauth`（OAuth 协议实现）——范围外；
`github/awesome-copilot` 的 `instructions/nodejs-javascript-vitest`——个人风格清单；`platformatic/skills`——产品包装；
`benedya/nestjs-skills`、`Kianibound/nestjs-playbook-skill`、`2muchcoffeecom/nestjs-manifesto`——零采纳且被覆盖。

## 基线缺口

无 skill（`uv run tools/run_evals.py nodejs-backend --baseline`，anthropic/claude-opus-5 · medium，
四个场景 `skill_read` 均为 `false`）时未达成的 `expected_behavior`。判定依据是逐个读
`/tmp/hs-evals/nodejs-backend/anthropic-claude-opus-5-medium/baseline/<N>/answer.md`
以及基线自己写出的文件（场景 1 的 `server.ts`、场景 3 的 `export.route.ts`）。

基线整体很强：三个正例都自己复现了故障，`decorateRequest` 引用类型、错误体外泄 stack、
`readFileSync` 阻塞、`process.exit(0)` 掐断在途请求、单例可变字段串号、
`enableShutdownHooks()` 缺失、`setInterval` 重入与未处理 rejection、middleware 断链、
两处全量缓冲、路径穿越，全部命中。缺口集中在**「有 schema / 有校验器」这条线**上——
基线一律改成手写 `typeof` 判断，从不引入框架的校验与序列化机制。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 Fastify 生产前评审 | EB6：路由没有 JSON Schema（`:id` 未校验、响应未过 schema，`select *` 直接外发） | 它把 `select *` 列进「还需要主人决定的两件事」，理由是不知道表结构；实际写出的 `server.ts` 里 `grep schema` 零命中。正确做法与表结构无关：加响应 schema，序列化器就只放行列出的字段 |
| 2 NestJS 审计串号 + 关机丢事件 | EB7：`new ValidationPipe()` 缺 `whitelist` / `forbidNonWhitelisted` | 修复版把 `app.useGlobalPipes(new ValidationPipe())` 原样抄回；整份 events.jsonl 里 `whitelist` 出现 0 次。未知属性照旧进 handler |
| 3 Hono 导出 OOM + requestId 不出现 | EB5：没有校验器 middleware，`body.table` 仍是任意字符串；无表名白名单 | 它在 handler 里写 `typeof body.table === 'string'` 就放行，随后 `db.stream(body.table)`。既没用 `zValidator` / `c.req.valid('json')`，也没有白名单——OOM 修好了，任意表读取这个洞原样留着 |
| 3 Hono 导出 OOM + requestId 不出现 | EB7：`onError` 仍返回 `String(err)` | 输出文件第 147–150 行原样保留 `return c.json({ error: String(err) }, 500)`，内部错误文本继续外泄；也未提 `HTTPException` |
| 4 Next.js server action（负例） | — | 负例只需 `skill_read == false`，基线本就不加载任何 skill，此行在 Phase D 判定 |

## 评测结果

模型全部为 `claude-opus-5:medium`（`tools/run_evals.py` 默认，未传 `--model` / `--thinking`）。
判定方式：逐条读 `answer.md`，并对场景 1 / 3 额外读代理实际写出的代码文件核对，不只看叙述。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Fastify 生产前评审 | claude-opus-5:medium | 无（baseline） | false | 6/7：EB1 `decorateRequest` 引用类型（实测复现 `FST_ERR_DEC_REFERENCE_TYPE`）、EB2 错误体外泄 message/code/stack、EB3 `readFileSync` 阻塞并改流式、EB4 `process.exit(0)` 改 `app.close()`+15s 兜底、EB5 pool 未关闭、EB7 只记 `error.message` 丢 stack | **EB6 未达成**：写出的 `server.ts` 里 `schema` 零命中，`select *` 原样保留并被列入「还需要主人决定」 |
| 1 Fastify 生产前评审 | claude-opus-5:medium | 有 skill | true | **7/7**。EB6 补上：`L24 important - 没有 params/response schema：id 未校验就进数据库，select * 会把明天新加的列直接发给客户端`，修法是 `schema.params` 校验 uuid + `schema.response.200` 只声明对外字段 | 额外命中 schema 之外的项：`requestTimeout` 默认 0 与缺 `handlerTimeout`/`request.signal`、readiness/liveness 分离、配置未启动期校验。并自行发现一个真实排空坑（Fastify 只在 `close()` 那一刻调一次 `closeIdleConnections()`，慢请求结束后才变空闲的 keep-alive 连接会挂住 `server.close()`），用 250 ms 周期扫描解决，实测 SIGTERM 后在途请求完整返回 200 且进程自行 exit 0 |
| 2 NestJS 审计串号 + 关机丢事件 | claude-opus-5:medium | 无（baseline） | false | 6/7：EB1 单例可变字段跨请求覆盖、EB2 改 `AsyncLocalStorage`、EB3 说出 REQUEST scope 沿注入链冒泡的代价、EB4 缺 `enableShutdownHooks()`、EB5 `pool.connect()` 未 await、EB6 `setInterval` 未处理 rejection 且会重入 | **EB7 未达成**：修复版原样抄回 `new ValidationPipe()`，整份 events.jsonl 里 `whitelist` 出现 0 次 |
| 2 NestJS 审计串号 + 关机丢事件 | claude-opus-5:medium | 有 skill | true | **7/7**。EB7 补上：`L7 important - ValidationPipe 默认放行未声明的属性，客户端可塞 isAdmin: true 进 DTO`，修法 `new ValidationPipe({ whitelist: true, forbidNonWhitelisted: true, transform: true })` | 两次运行都独立发现了拦截器里 `als.run(() => next.handle())` 无效这个陷阱（Nest 在 `intercept()` 返回后才订阅），有 skill 的那次把它写成 `blocking` 并给出在订阅处进入 store 的写法。有 skill 还多命中：`fetch` 无超时/无 abort signal、publish 失败仍标记 `sent_at`、readiness/liveness 分离；并主动丢弃一条真实但超出问题范围的发现（换 `nestjs-pino`）并说明理由 |
| 3 Hono 导出 OOM + requestId 不出现 | claude-opus-5:medium | 无（baseline） | false | 5/7：EB1 middleware 断链、EB2 改 `async` + `await next()`、EB3 `/exports` 全量缓冲改流式、EB4 `readFile` 改流式、EB6 路径穿越 | **EB5 未达成**：只在 handler 里写 `typeof body.table === 'string'`，没有校验器 middleware、没有 `c.req.valid`、没有表名白名单。**EB7 未达成**：`onError` 原样保留 `return c.json({ error: String(err) }, 500)` |
| 3 Hono 导出 OOM + requestId 不出现 | claude-opus-5:medium | 有 skill | true | **6.5/7**。EB7 补上：`onError` 改为 `{ code: 'INTERNAL', requestId }`，并写明「不再回 `String(err)`（泄漏驱动/路径文本）」。EB5 机制补上：改用 `validator('json', …)` middleware + `c.req.valid('json')` + `HTTPException`；白名单只写出结论未落地 | EB5 算部分达成：它明确说「真正安全的是白名单（`z.enum` 那种），但仓库里没有可依据的表名，不敢编」——把洞点出来并拒绝编造，比基线的静默放行好一档，但没有实现。另外正确用上了 stream 的第三个参数作流内错误处理器，并说明理由「响应头已发，`onError` 管不到」；`onAbort` 关游标经实测（`curl -m 1` 后 `cursor.closed emitted=224642`） |
| 4 Next.js server action（负例） | claude-opus-5:medium | 有 skill（`skills: []`） | **false** | 3/3：未加载本 skill；按 App Router 语义作答——server action 不隐式失效缓存，修法 `revalidatePath('/products')`，并说明为何此处选 `revalidatePath` 而非 `revalidateTag`；全篇无 Fastify / NestJS / Hono / 插件封装 / 优雅关机内容 | 负例判定通过。它还如实上报「仓库只有两个孤立片段，无法启动 Next 做提交冒烟」，没有编造验证 |

结论：**通过**。基线未达成的 4 条行为里，3 条（场景 1 EB6、场景 2 EB7、场景 3 EB7）在有 skill 时完全达成，
第 4 条（场景 3 EB5）机制达成、白名单部分达成。缺口方向高度一致——基线一律用手写 `typeof` 判断代替框架的
校验与序列化机制，也一律把内部错误文本继续外发；这两点正是 skill 的 Core rule 3 与 Core rule 4。
负例 `skill_read == false`，且答案完全落在 `react` skill 的领域内，边界有效。

## 备注

- **许可**：`Kadajett/agent-nestjs-skills` 与 `TheCodePace/fastify-skills` 都没有 LICENSE 文件，
  API 返回 `license: null`，按仓库规则填 `license: NONE` 并在 `notes` 写明未逐字复制。
  `nodejs/node` 的 API 返回 `NOASSERTION`，实读 `LICENSE` 后填 `MIT`。
  其余上游（含四个 `kind: docs`）均已定位到源仓库并确认 MIT，因此 `relation` 都是 `merged`——
  本 skill 的版本敏感事实确实来自这些官方文档，挂 `reference` 会与实际写法自相矛盾。
- **为什么 Express 只放迁移小节**：见裁决 9。三条理由分别是「Express 自身不提供本 skill 的任何一层能力，
  规则会退化成装库清单」「NestJS 默认平台即 Express，其用法已被 NestJS 分支覆盖」
  「新服务不选 Express，真实需求是搬迁」。因此 `references/express-migration.md` 是唯一提到 Express 的文件，
  Topic router 里它的 "Read when" 明确写成「`package.json` 里有 `express` 且要迁走」。
- **与 `typescript` skill 的上游重叠**：`mcollina/skills` 同时是 `typescript` skill 的上游
  （那边用 `skills/typescript-magician`）。本 skill 的 `paths` 只列 `skills/node` 与 `skills/fastify`，
  按计划「同波两个 skill 对同一上游 `paths` 重叠时各自只列实际使用的路径」处理。
- **正文断言的本机实证**（Phase C 期间跑的一次性脚本，已删除，命令与输出如下）：
  - Fastify 5.12 + `fastify-plugin`：`decorateRequest('ctx', { traceId: '' })` 抛
    `FST_ERR_DEC_REFERENCE_TYPE`；`decorateRequest('ctx')` + `onRequest` 赋值与
    getter-over-holder 两种写法都拿到每请求独立对象；默认 error handler 对
    `throw new Error("Unknown column 'username'")` 返回
    `{"statusCode":500,"code":"ER_BAD_FIELD","error":"Internal Server Error","message":"Unknown column 'username'"}`
    （证实 message/code 原样外发）；响应 schema 只声明 `id` 时，handler 返回的
    `secretInternalColumn` 被丢弃，客户端只收到 `{"id":"o1"}`。
  - Fastify 排空：**新发现，已写入 `references/fastify.md`**。默认
    `forceCloseConnections: "idle"` 下，drain 只在关闭流程第 3 步执行一次；一条
    keep-alive 连接若在那一刻正服务请求、之后才变空闲，就不再被回收，
    `server.close()` 会一直等到 `keepAliveTimeout`。实测：慢请求 1.5 s，
    `close()` 到 8.3 s 仍未 resolve；加上 `setInterval(() => app.server.closeIdleConnections?.(), 250)`
    后 `close()` 在慢请求结束后 50 ms resolve（1.557 s）。这条也是评测里有 skill 的
    场景 1 独立踩到的同一个坑。
  - Hono 4.13 + `@hono/zod-validator` + Zod 4：`zValidator(target, schema, hook)`
    的 hook 生效（证伪候选 6 的「hooks 已弃用」）；带
    `Content-Type: application/json` 返回 200，不带则 400（证实官方文档所说
    「无匹配 content-type 时 body 不解析」）；`z.enum` 白名单拒掉未列表名；
    middleware 不调 `next()` 时报
    `Context is not finalized. Did you forget to return a Response object or 'await next()'?`。
  - NestJS 拦截器 + `AsyncLocalStorage`（用 rxjs 单独复现，不需装 Nest）：
    `als.run(store, () => handle())` 订阅时读到 `NO STORE`，
    `new Observable((sub) => als.run(store, () => handle().subscribe(sub)))` 读到
    `{"id":"A"}`——证实「必须在订阅处进入 store」。
  - `references/config-and-secrets.md` 的 Zod 配置片段按原文逐字跑通（Zod 4.6.1）：
    `z.url()`、`z.stringbool()`（`'false'` → `false`）、`z.treeifyError()` 均为当前 API，
    输出 `{"port":8080,"logging":{...},"database":{...},"drainTimeoutMs":25000}`。
  - `references/streams-and-event-loop.md` 的 `monitorEventLoopDelay` 片段跑通
    （阻塞 150 ms 后 p99 报 163.8 ms）；`Readable.fromWeb`/`toWeb` 存在；
    `references/testing-and-injection.md` 的 `mock.timers` 片段在 `node --test` 下通过。
  - CLI 断言核对自 `nodejs/node` 的 `doc/api/cli.md` 与 `doc/api/process.md`：
    `--env-file` v20.6.0、`--env-file-if-exists` v22.9.0、`process.loadEnvFile` v20.12.0、
    `node --run` v22.0.0、`--unhandled-rejections` 默认自 v15.0.0 起为 `throw`。
  - 所有被点名的包都确认存在于 npm：`@fastify/express` 4.0.7、`@fastify/middie` 9.3.4、
    `@hono/node-server` 2.1.1、`fastify-type-provider-zod` 7.0.0、`nestjs-cls` 6.3.0、
    `@hono/standard-validator` 0.4.0、`close-with-grace` 2.5.0、`why-is-node-running` 3.2.2。
- **一处按官方文档纠正后写进正文的说法**：`references/express-migration.md` 原稿说可以用
  Hono 的 `app.mount()` 挂载 Express 应用做渐进迁移；查 hono.dev 的 `docs/api/hono.md` 后
  确认 `mount()` 只接受 fetch 式 `(Request) => Response` handler，Express 应用不是，
  已改成「Hono 迁移只能走反向代理分流」。
- **下次同步要盯的**：①`fastify/fastify` 的 v6 主线（当前 `v6.0.0-alpha.3`）——GA 后
  `references/fastify.md` 需重核 `forceCloseConnections` 与 schema 相关默认值；
  ②Node 26 在 2026-10-28 转 LTS，届时正文的 LTS 基线要从 24 抬到 26；
  ③`AsyncLocalStorage.withScope()` 仍是 Experimental（Stability 1），转稳定后可从「逃生口」升为默认写法。
- **放弃的方向**：OAuth/OIDC 流程（候选 4 质量足够但属协议实现）、WebSocket 与 SSE 之外的实时协议、
  `@fastify/http-proxy` 之类的网关模式、消息队列与 outbox 的完整实现（正文只写「后台循环必须处理 rejection
  且不可重入」这一层）。
