# fastapi 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"fastapi skill SKILL.md github"`、`site:skills.sh fastapi`
  - GitHub 代码搜索：`gh api -X GET search/code -f q='fastapi filename:SKILL.md'`（78848 命中，取前 60 条人工筛）
  - 领域官方组织仓库：`fastapi/`、`pydantic/`、`encode/`、`astral-sh/`、`microsoft/`、`github/awesome-copilot`
  - 社区权威：`zhanymkanov/fastapi-best-practices`、`Kludex/fastapi-tips`（Starlette / uvicorn 维护者）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`

### 版本核实（写正文前的前置条件）

`gh api repos/<repo>/releases` 加本机安装实测（`uv run --no-project --with 'fastapi[standard]'`）：

| 组件 | 最新发布 | 发布时间 | 本机实测版本 |
|---|---|---|---|
| fastapi | `0.141.1` | 2026-07-29 | 0.141.1 |
| pydantic | `v2.13.5` | 2026-08-28 | 2.13.5 |
| starlette | `1.6.0` | 2026-08-08 | 1.6.0 |

正文按 **FastAPI 0.141 + Pydantic 2.13 + Starlette 1.6** 写。实测确认的 API（都是模型不太可能凭训练数据说对的）：

- `app.frontend()` / `router.frontend()` 存在（`hasattr(FastAPI(), "frontend") == True`）。
- `from fastapi.sse import EventSourceResponse, ServerSentEvent` 可导入。
- `Depends()` 签名为 `(dependency=None, *, use_cache, scope)`，`scope` 默认 `None`（`yield` 依赖缺省按 `"request"`）。
- `[tool.fastapi] entrypoint = "my_app.main:app"` 被 `fastapi run` 读取（实跑 `curl localhost:8199/` → `{"ok":true}`，日志打印
  `🐍 Using import string: my_app.main:app`）。
- Starlette 1.6 的 `starlette.testclient` 优先 `import httpx2 as httpx`，退回 `httpx` 时抛
  `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
  装上 `httpx2`（2.12.0）后该警告消失。**`fastapi[standard]` 只带 httpx v1**，所以默认装法就会踩到这条。
- 默认线程池上限为 40（`anyio.to_thread.current_default_thread_limiter().total_tokens == 40`）。
- 响应二次校验实测：`response_model=P` 与 `-> P` 两种写法下，`model_validator(mode="after")` 每请求各触发 **2 次**。
- `httpx.AsyncClient.__init__` 已无 `app` 参数（`'app' in signature(...).parameters == False`）。
- 模块属性替换对已声明依赖无效、`app.dependency_overrides` 有效（同一 app 实测：换模块属性仍返回 `real`，
  设 override 后返回 `override`）。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | fastapi/fastapi `fastapi/.agents/skills/fastapi`（SKILL.md + 6 个 references） | https://github.com/fastapi/fastapi | 102234 | 2026-09-01 | MIT | FastAPI 官方 skill：`Annotated`、路由组织、response_model、async/def、SSE、工具链 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 主干。作者本人维护，规则即口径（禁 Ellipsis、禁 RootModel、禁 ORJSONResponse、`scope="function"`）。缺测试/错误处理/lifespan/后台任务/鉴权 |
| 2 | fastapi/fastapi `docs/en/docs/**`（fastapi.tiangolo.com，465 篇） | https://fastapi.tiangolo.com | 102234 | 2026-09-01 | MIT | 官方文档：`dependencies-with-yield`、`testing-dependencies`、`async-tests`、`events`、`background-tasks`、`handling-errors`、`separate-openapi-schemas`、`authentication-error-status-code` | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `kind: docs`，许可实查：文档与代码同仓，仓库 LICENSE 为 MIT，故 `merged`。补齐官方 skill 的全部空白 |
| 3 | pydantic/pydantic `.agents/skills/pydantic` | https://github.com/pydantic/pydantic | 28754 | 2026-09-10 | MIT | Pydantic 官方 skill：`Field()` 两种写法、约束优先于校验器、after > before、类型强制与 union、前向引用、子类序列化与判别联合 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | Pydantic 侧主干。"序列化按声明类型而非运行时子类" 这条是 response_model 最常见的静默数据丢失来源 |
| 4 | pydantic/pydantic 文档（docs.pydantic.dev） | https://docs.pydantic.dev | 28754 | 2026-09-10 | MIT | `model_config`/`ConfigDict`、`field_validator`、别名与 `populate_by_name`、`from_attributes`、v1→v2 迁移 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | `kind: docs`，许可实查 `gh api repos/pydantic/pydantic/license` → MIT，故 `merged` |
| 5 | zhanymkanov/fastapi-best-practices | https://github.com/zhanymkanov/fastapi-best-practices | 18058 | 2026-08-27 | 无（API `license: null`） | 依赖缓存与链式依赖、响应二次序列化、`run_in_threadpool`、BackgroundTasks vs 任务队列、schema 里的 `ValueError` | 2 | 3 | 3 | 2 | 0 | 10 | INCLUDE | 社区最高权威的 FastAPI 工程实践清单。许可 NONE：全部改写，不抄任何段落。正确性扣 1：仍用非 `Annotated` 的 `Depends()` 默认值写法，且「一律优先 async 依赖」与官方冲突（见裁决 1） |
| 6 | Kludex/fastapi-tips（101 FastAPI Tips） | https://github.com/Kludex/fastapi-tips | 3622 | 2026-08-17 | 无（API `license: null`） | 40 线程上限与调大方式、lifespan state vs `app.state`、纯 ASGI 中间件 vs `BaseHTTPMiddleware`、依赖跑在线程上、`pytest.mark.anyio` | 2 | 3 | 3 | 2 | 0 | 10 | INCLUDE | 作者 Marcelo Trylesinski 是 Starlette/uvicorn 维护者，属公认专家。许可 NONE：全部改写。正确性扣 1：示例里的 `AsyncClient(app=app)` 已被 httpx 移除（实测确认），且 tip 2「always prefer async」与官方冲突 |
| 7 | encode/starlette 文档（starlette.dev） | https://starlette.dev | 12613 | 2026-09-07 | BSD-3-Clause | `TestClient`（lifespan 需 `with`）、`run_in_threadpool`、`BackgroundTask` vs `BackgroundTasks`、`StreamingResponse`、纯 ASGI 中间件 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `kind: docs`。FastAPI 的请求/响应/测试底座都在这里，`httpx2` 迁移这条只有 Starlette 侧有说明 |
| 8 | astral-sh/ruff 的 `FAST` 规则组文档 | https://docs.astral.sh/ruff/rules/#fastapi-fast | 49577 | 2026-09-10 | MIT | `FAST001` 冗余 response_model、`FAST002` 非 Annotated 依赖（可自动改写）、`FAST003` 未使用的路径参数 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `kind: docs`，窄贡献：FastAPI 项目里 ruff 该额外开哪一组。实测 `uvx ruff rule --all` 确认三条规则与其可修复性 |
| 9 | microsoft/skills `.github/plugins/azure-sdk-python/skills/fastapi-router-py` | https://github.com/microsoft/skills | 3006 | 2026-09-10 | MIT | router CRUD 骨架、每操作的状态码约定（201/204）、"长生命周期资源放 lifespan、按请求资源用 `Depends`" | 2 | 3 | 2 | 2 | 2 | 11 | INCLUDE | 剥离 Azure/前端语境后，状态码与资源生命周期两节可用。正确性扣 1：鉴权示例用非 `Annotated` 的 `Depends()`，且失败返回 403（FastAPI 0.122 起官方改为 401） |
| 10 | microsoft/skills `.github/plugins/azure-sdk-python/skills/pydantic-models-py` | https://github.com/microsoft/skills | 3006 | 2026-09-10 | MIT | Base/Create/Update/Response/InDB 多模型分层命名、camelCase 别名 + `populate_by_name` | 2 | 3 | 2 | 2 | 2 | 11 | INCLUDE | 只取多模型分层这一条结构语义。正确性扣 1：`Field(..., alias=...)` 的 Ellipsis 与 FastAPI 官方口径冲突（裁决 2） |
| 11 | wshobson/agents `plugins/api-scaffolding/skills/fastapi-templates` | https://github.com/wshobson/agents | 39555 | 2026-09-07 | MIT | 分层项目布局（api/core/models/schemas/services/repositories）、conftest 夹具主题清单 | 1 | 3 | 2 | 1 | 2 | 9 | INCLUDE（reference） | 只用来核对「一个 FastAPI skill 该覆盖哪些主题」。内容不可用：`AsyncClient(app=app)`（已失效）、`event_loop` 夹具（pytest-asyncio 0.23+ 已移除）、全篇非 `Annotated` |
| 12 | fastapi/full-stack-fastapi-template | https://github.com/fastapi/full-stack-fastapi-template | 45495 | 2026-09-03 | MIT | 官方项目模板：`app/api/routes` + `app/core` 布局、`SQLModel`、`deps.py` | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE（reference） | 官方，但形态是可运行模板而非规则集，具体性 1。用于核对官方推荐的目录布局，不抄文件 |
| 13 | fastapi/sqlmodel 文档 | https://sqlmodel.tiangolo.com | 18318 | 2026-09-01 | MIT | SQLModel 与 Pydantic 模型共用 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（reference） | 官方 skill 推荐 SQLModel 优先于 SQLAlchemy，需要核对这条；但 ORM/数据库调优不在本 skill 范围，只作逃生口一句 |
| 14 | github/awesome-copilot | https://github.com/github/awesome-copilot | 38862 | 2026-09-10 | MIT | 无 FastAPI skill、无 `instructions/fastapi*`；仅 `skills/eval-driven-dev/references/runnable-examples/fastapi-web-server.md` 一个示例 | 3 | 3 | 0 | — | 2 | ≤4 | REJECT | 用 `git trees` 全量列举确认（`grep -E '^(skills\|instructions)/' \| grep -i fastapi` 无命中）。GitHub 官方目录本轮对 FastAPI 无覆盖，留行以免下批重查 |
| 15 | jezweb/claude-skills `skills/fastapi` | https://github.com/jezweb/claude-skills | 1000 | 2026-07-02 | MIT | web_search 命中，但 HEAD 上已无该路径 | 1 | 1 | 0 | — | 2 | ≤4 | REJECT | `gh api repos/jezweb/claude-skills/git/trees/main?recursive=1 \| grep -i fastapi` 无命中，`contents/skills/fastapi/SKILL.md` 返回 404。仓库已重构为 `plugins/`。搜索引擎缓存过期 |
| 16 | eggboy/skills `fastapi` | https://github.com/eggboy/skills | 0 | 2026-04-03 | 无 | 与候选 1 同构（章节标题逐条对应），另加 lifespan / 错误处理两节 | 0 | 1 | 2 | 2 | 0 | 5 | REJECT | 官方 skill 的派生复制品，无独立价值；上游本身无许可。其新增的两节主题已由候选 2 的官方文档覆盖 |
| 17 | samuelpkg/skills `fastapi` | https://github.com/samuelpkg/skills | 0 | 2026-05-27 | MIT | 教程式全景（项目结构、配置、schema、路由、异步、错误处理） | 0 | 2 | 2 | 1 | 2 | 7 | MAYBE（未采用） | 全篇非 `Annotated` 的 `Depends()` 默认值写法；`get_db()` 的返回标注写成 `-> AsyncSession` 而实际是生成器；`UserResponse.model_validate(u)` 之后又挂 `response_model`，正是候选 5 指出的二次校验。仅作主题清单交叉核对 |
| 18 | mfmezger/skills `fastapi` | https://github.com/mfmezger/skills | 0 | 2026-08-20 | 无 | 个人整理，内容与官方 skill 高度重叠 | 0 | 3 | 1 | 1 | 0 | 5 | REJECT | 无许可 + 无独立规则，收益为零 |
| 19 | conjure-3301/skills `fastapi` | https://github.com/conjure-3301/skills | 0 | 2026-08-18 | 无 | 个人整理 | 0 | 3 | 1 | 1 | 0 | 5 | REJECT | 同上 |
| 20 | cesasol/skills `fastapi-api` | https://github.com/cesasol/skills | 0 | 2026-08-27 | 无 | 个人整理，偏项目脚手架 | 0 | 3 | 1 | 1 | 0 | 5 | REJECT | 同上 |

INCLUDE（merged）：1、2、3、4、5、6、7、8、9、10。INCLUDE（reference）：11、12、13。REJECT：14–20。

## 深度审查

**1. fastapi/fastapi `.agents/skills/fastapi`（321 行 SKILL.md + 6 个 reference）**
frontmatter 只有 `name` + `description`，无 agent 专属字段，合入时无需剥离。结构是「Quick Reference 索引 +
主题小节 + references 深链」。质量特点是**只写口径不写教程**：`Annotated` 强制、禁 `...`、禁 `RootModel`、
禁 `ORJSONResponse`/`UJSONResponse`（已弃用）、router 级参数写在 `APIRouter()` 而非 `include_router()`、
一个函数一个 HTTP 方法、`response_class=EventSourceResponse` + `yield`。`references/dependencies.md` 里的
`Depends(..., scope="function")` 是本机实测确认存在的新能力，训练数据里几乎不会有。
**空白**：完全没有测试、错误处理、lifespan、后台任务、鉴权、OpenAPI schema 分裂这六块——这正是候选 2 的作用。
与候选 3 的重叠只在 Pydantic 的两条禁令上，其余互补。

**2. fastapi/fastapi 官方文档**
`docs/en/docs/` 里 465 篇。真正有 token 价值、且模型容易答错的几篇：
`tutorial/dependencies/dependencies-with-yield.md`（`except` 不重新 raise 会让服务端日志空白、
`scope` 对子依赖的约束方向）、`advanced/testing-dependencies.md`（`app.dependency_overrides` 及清空）、
`advanced/async-tests.md`（`docs_src` 里已经是 `AsyncClient(transport=ASGITransport(app=app))`）、
`advanced/testing-events.md`（lifespan 必须 `with TestClient(app)`）、
`how-to/separate-openapi-schemas.md`（`Item-Input`/`Item-Output` 双 schema，`separate_input_output_schemas=False` 可关）、
`how-to/authentication-error-status-code.md`（0.122.0 起安全工具从 403 改 401 并带 `WWW-Authenticate`）、
`tutorial/handling-errors.md`（异常处理器要注册在 **Starlette 的** `HTTPException` 上才能接住框架内部抛出的那些）。
文档用 `{* ../../docs_src/... *}` 引用真实可跑代码，所以事实密度高于任何社区二手材料。

**3. pydantic/pydantic `.agents/skills/pydantic`（312 行）**
唯一一份官方 Pydantic skill。最值钱的三条：①「序列化按声明类型走」——声明 `Base` 却传 `Sub1`，
`model_dump()` 静默丢掉子类字段，改用判别联合或泛型；②约束优先于自定义校验器，自定义时优先 `after` +
annotated 形式（`Annotated[int, AfterValidator(...)]`），因为 `before` 的入参可以是任何东西；
③别名/默认值这类对静态类型检查器有意义的元数据必须写赋值形式 `= Field(alias=...)`，其余写 `Annotated`。
另有「不要用 Pydantic 定义只在内部实例化的类」这条取舍判断，正好对上 FastAPI 项目里 schema 与领域模型混用的常见错误。
与候选 10 的多模型分层不冲突（一个讲怎么写字段，一个讲分几个模型）。

**5. zhanymkanov/fastapi-best-practices（871 行 README）**
社区第一权威（18k★）。不可替代的四条：①**同一请求内依赖结果被缓存**，因此可以把依赖切小复用，
`parse_jwt_data` 被三个依赖引用也只执行一次；②**响应二次序列化**——FastAPI 先 `jsonable_encoder`
再按 `response_model` 校验，所以你手工构造的模型对象会被创建两次（本机实测确认为 2 次）；
③必须用同步 SDK 时用 `run_in_threadpool`；④`BackgroundTasks` 与真任务队列的选择表（同进程、
无重试、worker 死了任务就没了）。缺点是全篇非 `Annotated` 写法，且项目结构建议（按领域分包）与
候选 11/12 的分层布局互相矛盾——本 skill 不写目录规范，只写「按领域还是按层由既有仓库决定」。

**6. Kludex/fastapi-tips**
Starlette / uvicorn 维护者。不可替代的三条：①`def` 路由和 `def` 依赖都跑在同一个
**40 线程**的池子里，池子打满则整个应用阻塞，调大方式是在 lifespan 里改
`anyio.to_thread.current_default_thread_limiter().total_tokens`；②lifespan 里 `yield {...}`
产出的 state 经 `request.state` 读取，优于 `app.state`（本机实测通过）；
③`BaseHTTPMiddleware`（含 `@app.middleware("http")`）有性能代价，热路径用纯 ASGI 中间件。
其 tip 5「用 AsyncClient 取代 TestClient」示例已过期（`AsyncClient(app=app)`），按候选 2 的
`ASGITransport` 写法纠正。

**7. encode/starlette 文档**
FastAPI 的 `TestClient`、`run_in_threadpool`、`StreamingResponse`、`BackgroundTask` 全部来自这里。
唯一记录 `httpx2` 迁移的地方，而这条影响每个装了 `fastapi[standard]` 的项目（实测会打
`StarletteDeprecationWarning`）。BSD-3-Clause，可合入。

**9/10. microsoft/skills 两个 py skill**
`.github/plugins/azure-sdk-python/` 下，形态是「模板 + 占位符替换」，`{{ResourceName}}` 这类东西不能带进来。
可用的只有两小块：每 HTTP 操作的状态码约定（POST→201、DELETE→204）与多模型分层命名。
两者的 frontmatter 带 `metadata.author: Microsoft`、`metadata.version`，合入时按标准剥离。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 路由与依赖默认写 `async def` 还是 `def` | Kludex tip 2：「非 async 函数有性能代价，一律优先 async」；zhanymkanov：「优先 async 依赖，小的非 I/O 操作走线程没必要」；fastapi 官方 skill：「拿不准就用 `def`，它会在线程池里跑；确保阻塞代码不在 `async` 函数里」 | 采用官方：**函数体内的调用决定关键字**。全程可 await → `async def`；有任何阻塞调用 → `def`（或留在 `async def` 里用 `run_in_threadpool`/`asyncify` 推出去）。把「优先 async」写成默认会诱导把阻塞调用塞进 `async def`，那是最坏结果。社区那条的真实含义（线程有开销、池子只有 40 格）作为**容量约束**单独写，不作为写法默认 | 官方厂商 > 公认专家；且实测线程池上限 40，两条并不真矛盾，只是社区表述把结论写反了 |
| 2 | 必填字段要不要写 `Field(...)` 的 Ellipsis | microsoft `pydantic-models-py`：`workspace_id: str = Field(..., alias="workspaceId")`；候选 17 同样；fastapi 官方 skill 与 reference：**明确禁止** `...` | 采用官方：不写 `...`。无默认值即必填 | 官方厂商 > 厂商第三方 skill；官方 skill 与官方文档一致 |
| 3 | 异步测试客户端怎么构造 | Kludex tip 5 与 wshobson：`AsyncClient(app=app, base_url=...)`；官方 `docs_src/async_tests`：`AsyncClient(transport=ASGITransport(app=app), base_url=...)` | 采用官方 `ASGITransport`。实测 `httpx.AsyncClient.__init__` 已无 `app` 参数，社区写法直接 `TypeError` | 更新 > 更旧，且本机实测可证 |
| 4 | 安全依赖鉴权失败返回什么状态码 | microsoft `fastapi-router-py`：403；FastAPI 0.122.0 起官方安全工具：401 + `WWW-Authenticate` | 采用 401。要 403 需自己覆盖 `make_not_authenticated_error`，属于兼容老客户端的逃生口 | 官方文档 `how-to/authentication-error-status-code.md` 明确写了这次变更与理由（RFC 7235 / 9110） |
| 5 | `TestClient` 还是 `httpx.AsyncClient` 作首选 | Kludex：AsyncClient 优先；官方文档：`TestClient` 是默认，只有测试函数本身要 `await` 应用代码时才换 `AsyncClient` | 采用官方：`TestClient` 默认，测试体自身需要 await 时才换。理由是 `TestClient` 内部替你驱动事件循环，而在 `async def` 测试里这套魔法失效 | 官方文档 `advanced/async-tests.md` 直接解释了失效原因 |
| 6 | `TestClient` 依赖哪个 HTTP 库 | 各社区上游一律 `httpx`；Starlette 1.6 的 testclient 先 `import httpx2 as httpx`，退回 httpx 时打弃用警告 | 写 `httpx2`。`fastapi[standard]` 只带 httpx v1，所以要显式加 `httpx2` 才没警告 | 实测：装 httpx2（2.12.0）后警告消失；读 `starlette/testclient.py` 源码确认导入顺序 |
| 7 | 项目目录规范 | wshobson / microsoft / 候选 17：按层分（`api/`、`services/`、`repositories/`、`schemas/`）；zhanymkanov：按领域分（`src/auth/`、`src/posts/` 各自带 router/schemas/service）；官方模板：`app/api/routes` + `app/core` | 本 skill **不规定目录树**。只写一条：沿用仓库既有约定，新仓库按领域切分并保持 router/schema/service 同层。理由是三家权威互相矛盾且都能工作，属于高自由度决策，写死等于制造无谓的重构 | `docs/skill-standard.md` 第 3 节「自由度与脆弱性匹配」 |
| 8 | 耗时任务放哪里 | 官方 `tutorial/background-tasks.md`：小任务用 `BackgroundTasks`，重计算考虑 Celery；zhanymkanov：给出明确的分界表 | 采用 zhanymkanov 的分界并用官方措辞收口：任务丢了要有人被叫起来 → 外部队列；否则 `BackgroundTasks` | 两方不冲突，社区那份更可判定，官方给了同向依据 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `fastapi-official-skill` | fastapi/fastapi `fastapi/.agents/skills/fastapi` | merged | 全部核心口径：`Annotated` 参数与依赖、类型别名依赖、router 级 prefix/tags/dependencies、返回类型优先于 `response_model`、禁 Ellipsis / 禁 `RootModel` / 禁 `ORJSONResponse`、`async def` vs `def`、`yield` 依赖的 `scope`、SSE 与流式、`fastapi` CLI 与 `[tool.fastapi] entrypoint` |
| `fastapi-docs` | fastapi.tiangolo.com（源在 fastapi/fastapi `docs/en/docs`） | merged | `yield` 依赖的异常传播与「必须重新 raise」、`dependency_overrides` 与清空、`ASGITransport` 异步测试、lifespan 必须 `with TestClient`、异常处理器要注册到 Starlette 的 `HTTPException`、`RequestValidationError`、输入/输出双 OpenAPI schema、安全工具 401 变更、`BackgroundTasks` 与依赖注入的合并语义 |
| `pydantic-official-skill` | pydantic/pydantic `.agents/skills/pydantic` | merged | 按声明类型序列化导致子类字段丢失 → 判别联合；约束优先于校验器；`after` 优于 `before` 且优先 annotated 形式；赋值形式 vs `Annotated` 形式的分工；避免 union 与抽象集合；前向引用与递归类型别名 |
| `pydantic-docs` | docs.pydantic.dev（源在 pydantic/pydantic） | merged | `model_config = ConfigDict(...)`、`from_attributes`、`populate_by_name` 与 `serialization_alias`、`field_validator` 的 `@classmethod` 要求、v1→v2 迁移映射 |
| `zhanymkanov-best-practices` | zhanymkanov/fastapi-best-practices | merged | 请求内依赖缓存与依赖切分复用、响应二次校验的代价、`run_in_threadpool` 包同步 SDK、`BackgroundTasks` vs 外部任务队列的分界、schema 里 `ValueError` 变成 422 |
| `kludex-fastapi-tips` | Kludex/fastapi-tips | merged | 40 线程上限与在 lifespan 里调大、lifespan state 优于 `app.state`、纯 ASGI 中间件优于 `BaseHTTPMiddleware`、`def` 依赖也占线程、`pytest.mark.anyio` |
| `starlette-docs` | starlette.dev | merged | `TestClient` 的 lifespan 语义与 `httpx2` 迁移、`run_in_threadpool`、`BackgroundTask` vs `BackgroundTasks`、`StreamingResponse`、纯 ASGI 中间件形态 |
| `ruff-fast-rules` | docs.astral.sh/ruff（FAST 规则组） | merged | FastAPI 项目里 ruff 要额外开 `FAST`：`FAST001` 冗余 response_model、`FAST002` 非 Annotated 依赖（可自动改写）、`FAST003` 未使用路径参数 |
| `microsoft-skills-py` | microsoft/skills（两个 py skill） | merged | 每 HTTP 操作的状态码约定（201/204 + `response_model=None`）、长生命周期资源放 lifespan 而按请求资源走 `Depends`、Base/Create/Update/Response 多模型分层命名 |
| `wshobson-fastapi-templates` | wshobson/agents `plugins/api-scaffolding/skills/fastapi-templates` | reference | 只用于核对主题覆盖面（分层布局、conftest 夹具、中间件、限流）。其代码事实已过期，未采用任何内容 |
| `fastapi-full-stack-template` | fastapi/full-stack-fastapi-template | reference | 核对官方推荐的目录布局与 `deps.py` 惯例，未复制文件 |
| `sqlmodel-docs` | sqlmodel.tiangolo.com | reference | 核对官方「SQLModel 优先于 SQLAlchemy」这条推荐的适用条件；ORM 与数据库调优不在本 skill 范围 |

## 基线缺口

无 skill（`uv run tools/run_evals.py fastapi --baseline`，Claude Opus 5 · medium，四个场景
`skill_read` 均为 `False`）时，各场景未达成的 `expected_behavior`。基线答复整体很强——阻塞根因、
`monkeypatch` 无效、结构性防泄露这些主线都答对了——所以缺口集中在**FastAPI 特有的机制细节**上，
这正是 skill 该补的部分：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 阻塞路由 | ② 两种修法与各自适用条件 | 只给了「全改异步」一条路（async engine + httpx），没有把「整体阻塞就声明 `def` 走线程池」和「混合体用 `run_in_threadpool` / `asyncify` 推出去」作为可选修法给出判据 |
| 1 阻塞路由 | ③ 线程池上限的处置 | 提到了 `total_tokens = 40` 与线程饥饿，但没给出在 lifespan 里调大的做法 |
| 1 阻塞路由 | ⑤ lifespan state 优于 `app.state` | 换掉了 `on_event` ✓，但仍在 lifespan 里往 `app.state` 上挂属性，没用 `yield {...}` + `request.state` |
| 1 阻塞路由 | ⑥ router 级参数写在 `APIRouter()` | 完全未提，改后代码仍是 `include_router(router, prefix=..., tags=...)` |
| 2 依赖覆盖与测试 | ② 覆盖后必须清理 | 写了 conftest 夹具，但通篇没提 `app.dependency_overrides.clear()` 或 teardown 恢复，覆盖会跨测试泄漏 |
| 2 依赖覆盖与测试 | ⑦ 两种客户端的选择依据 | 两个客户端都建了，但没说「同步测试用 `TestClient`，只有测试体本身要 await 应用代码才换 `AsyncClient`」 |
| 3 Pydantic 与 response_model | ④ 去掉 `Field(...)` 的 Ellipsis | 改后代码仍写 `Field(..., description=...)` 与 `Field(..., min_length=8)` |
| 3 Pydantic 与 response_model | ⑤ 用 `list[User]` 取代 `RootModel` | 未处理 `UserList(RootModel[...])`，仍保留包装模型 |
| 3 Pydantic 与 response_model | ⑥ 按声明类型序列化 → 子类字段静默丢失 | 造了 `AdminPublic` 但没指出「声明 `User` 却返回 `Admin` 会静默丢掉 `permissions`」，也没提判别联合 |
| 3 Pydantic 与 response_model | ⑦ 响应二次校验 + 输入/输出双 schema | 两条都未出现；答复里甚至检查了 `app.openapi()` 却没注意 `User-Input`/`User-Output` 分裂 |
| 4 负例 | —（全部达成） | 控制组：`skill_read=False`，答复是通用 uv/ruff/PEP 735 迁移，未引入 FastAPI |

## 评测结果

两次运行模型与思考档相同（`anthropic/claude-opus-5` · medium，`tools/run_evals.py` 默认值），
基线在 Phase B 跑、有 skill 在 Phase D 跑。逐条人工读 `answer.md` 判定，编号对应
`evals/evals.json` 里 `expected_behavior` 的顺序。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 阻塞路由与丢任务 | claude-opus-5:medium | 无（baseline） | false | ①④⑦（3/7） | 阻塞根因、`BackgroundTasks` 丢任务、GET 改状态都答对；②③⑤⑥ 未达成（只给全异步一条修法、未给调线程池上限的做法、仍用 `app.state`、`prefix`/`tags` 仍在 `include_router()`） |
| 1 阻塞路由与丢任务 | claude-opus-5:medium | 有 | true | ①②③④⑤⑥⑦（7/7） | ② 明确用 `run_in_threadpool` 保住 `async def` 并指出 `def` 处理器走 40 槽线程池；③ 点名 `total_tokens` 并给出「只调线程池不调连接池只是把排队搬家」的配套规则；⑤ 改为 `lifespan` 里 `yield {...}` + `request.state` 读取；⑥ `APIRouter(prefix=..., tags=...)` + 裸 `include_router(router)` |
| 2 依赖覆盖与测试 | claude-opus-5:medium | 无（baseline） | false | ①③④⑤⑥（5/7） | 「`monkeypatch` 对已声明依赖无效」这条基线自己就答对了；② 未提清理覆盖（会跨测试泄漏）、⑦ 未给两种客户端的选择判据 |
| 2 依赖覆盖与测试 | claude-opus-5:medium | 有 | true | ①②③④⑤⑥（6/7），⑦ 部分 | ② teardown 显式清空覆盖，且覆盖设置早于 client 构建；另外自发用 `unshare -n` 在无网络命名空间下验证离线，并确认 `ASGITransport` 不跑 lifespan。⑦ 行为正确（同步用 `TestClient`，只有一个 async 用例用 `AsyncClient`）但未把判据写成一句话 |
| 3 Pydantic v2 与 response_model | claude-opus-5:medium | 无（baseline） | false | ①②③（3/7） | 结构性拆出公开模型、v1→v2 迁移、`assert` 在 `-O` 下失效都答对；④⑤⑥⑦ 未达成（保留 `Field(...)`、保留 `RootModel`、未提按声明类型序列化的静默截断、未提二次校验与双 schema） |
| 3 Pydantic v2 与 response_model | claude-opus-5:medium | 有 | true | ①②④⑤⑥（5/7），③ 部分，⑦ 未达成 | ④ 明确「删噪声」去掉 Ellipsis；⑤ `RootModel` 删掉改 `-> list[AnyUserRead]`；⑥ 指出 `Admin` 声明成 `User` 会静默丢 `permissions`，改判别联合并实测「`permissions` 未被截断」。③ 说对了 `-O` 剥断言的原因，但改法用了声明式 `EmailStr` 而非 `raise ValueError`（符合本 skill「约束优先于校验器」的规则，判为部分达成）。⑦ 仍未提响应二次校验；双 schema 因模型已彻底拆分而不再出现，属于该条本身失去对象 |
| 4 负例：纯 Python 库迁 uv/ruff | claude-opus-5:medium | 无（baseline） | false | ①②③（3/3） | 控制组 |
| 4 负例：纯 Python 库迁 uv/ruff | claude-opus-5:medium | 有 | **false** | ①②③（3/3） | 未加载 fastapi skill；全文 grep `fastapi\|uvicorn\|APIRouter\|pydantic` 零命中，答复是 hatchling + PEP 735 + ruff 的通用迁移 |

结论：**通过**。三个正例在基线合计有 **10** 条 `expected_behavior` 未达成（场景 1 的 ②③⑤⑥、
场景 2 的 ②⑦、场景 3 的 ④⑤⑥⑦）。有 skill 时其中 **8 条达成**（场景 1 全部四条、场景 2 的 ②、
场景 3 的 ④⑤⑥），1 条部分达成（场景 2 的 ⑦：行为正确但判据未明述），1 条仍未达成
（场景 3 的 ⑦ 响应二次校验）。另外场景 3 的 ③ 在有 skill 时改用声明式 `EmailStr` 而非
`raise ValueError`——原因说对、改法更好但与该条字面不完全吻合，记为部分达成，不计入缺口填补。
负例两次 `skill_read == false`，无越界。

## 备注

### 与 `python` skill 的去重

`python` skill 已经覆盖：uv 项目与 `[dependency-groups]`、PEP 723 脚本、ruff 规则选取与
`# noqa` 纪律、`pyproject.toml` 里 pytest 配置表名的版本差异、fixture 作用域与顺序依赖、
`unittest.mock.patch` 的目标解析、`asyncio.TaskGroup` 与取消语义、「`async def` 里不能有阻塞调用」这条通则。
本 skill 只写这些东西**在 FastAPI 项目里的特有形态**：

- 阻塞边界：不是「不要阻塞」，而是「`def` 路由走 40 格线程池、`async def` 路由直接占事件循环」这条 FastAPI 特有的二分。
- 测试：不写 pytest 通则，只写 `TestClient` vs `httpx.AsyncClient` 的选择依据、`dependency_overrides`
  为什么必须取代 `monkeypatch`、lifespan 要 `with`、`httpx2`。
- 工具链：不重复 uv/ruff 的通用配置，只写 `FAST` 规则组与 `[tool.fastapi] entrypoint`。
- 类型：Pydantic 模型作为 HTTP 边界契约（响应过滤、双 schema、别名）——`python` skill 的 typing 一节讲的是
  `Protocol`/`TypedDict` 那一层，不重叠。

### 版本核实结论

当前线是 **FastAPI 0.141.1 / Pydantic 2.13.5 / Starlette 1.6.0**（发布时间与本机实测见「版本核实」
一节）。三条与子版本强相关、写正文时必须按 0.141 而非训练记忆落笔的点：

- `Depends(scope="function")` 存在（`Depends` 签名为 `(dependency, *, use_cache, scope)`），
  `yield` 依赖缺省 `scope="request"`；旧材料里根本没有 `scope` 概念。
- 安全工具鉴权失败自 **0.122.0** 起返回 401 + `WWW-Authenticate`（原为 403），要旧行为需覆盖
  `make_not_authenticated_error`。
- SSE 已进主库（`fastapi.sse` 的 `EventSourceResponse` / `ServerSentEvent`），不再需要
  `sse-starlette`；`app.frontend()` 同样是新增能力。

Pydantic 侧按 2.13 写：`ConfigDict`、`field_validator`、`serialization_alias` /
`validation_alias`、`model_fields_set` 都以本机 2.13.5 实测为准。

### 写作过程中被实测推翻的两条常见说法

这两条本来按社区共识写进了草稿，实测后改写，记在此以免下次同步时又被写回：

1. **「返回 ORM 行必须给模型加 `from_attributes`，否则响应报错」——错。** FastAPI 校验请求与
   响应字段时无条件传 `from_attributes=True`（`fastapi/_compat/v2.py:182`），实测无该配置的模型
   也能从任意对象（含只有 `@property` 的对象）取值并返回 200。`from_attributes` 只在**你自己**调
   `Model.model_validate(row)` 时才需要。
2. **「`FastAPI(dependencies=[...])` 会一并保护 `/docs` 与 `/openapi.json`」——错。** 实测全局
   依赖抛 401 时业务路由 401，而 `/docs` 与 `/openapi.json` 仍返回 200；它们是 FastAPI 自己加的
   Starlette 路由，不走 path-operation 的依赖链。要藏 schema 用 `openapi_url=None`（`/docs` 随之 404）
   或自行把文档挂在同一套鉴权后面。

另外一条同样实测确认、与直觉相反的：`status_code=204` 的处理器返回了 body 也**不会报错**，
Starlette 直接把 body 丢掉，所以症状只出现在客户端侧。

### 许可注意

- 候选 5、6 的仓库 API `license` 为 `null` → `SOURCES.yaml` 写 `license: NONE`，`notes` 按仓库政策写
  「No licence file; used under the repository's permissive-attribution policy, no text copied verbatim」，
  正文全部改写，不留任何原句。
- 两个 `kind: docs` 上游都实查了源仓库许可：`gh api repos/fastapi/fastapi/license` → MIT、
  `gh api repos/pydantic/pydantic/license` → MIT，因此按规则填 `merged`（挂 reference 与「本 skill 的事实
  来自官方文档」自相矛盾）。starlette.dev 源仓 BSD-3-Clause、ruff 文档源仓 MIT，同样 `merged`。
- 候选 11（wshobson，MIT）许可上允许 merged，但其代码事实已过期，实际未采用内容，故按 `reference` 记录——
  relation 反映的是「有没有内容被合入」，不是许可允不允许。

### 未来同步时要盯的

- `fastapi/fastapi` 的 `.agents/skills/fastapi`：`app.frontend()`、`fastapi.sse`、`Depends(scope=)`
  都是新特性，仍在演进。
- Starlette 的 `httpx` → `httpx2` 迁移：目前是弃用警告，下一个大版本可能变成硬要求。
- `zhanymkanov/fastapi-best-practices` 与 `Kludex/fastapi-tips` 都无许可文件，若上游后续补上许可需重看
  relation。

### 未被填补的那一条

场景 3 的 ⑦「响应会被二次校验」两次运行都没出现在答复里。事实本身在
`references/responses-and-errors.md` 的 "The response is validated twice" 一节，且有本机实测数据
（每请求触发 2 次 `model_validator`）。判断是**这条不构成缺陷**：该场景的任务是修泄漏与迁移 v1，
二次校验只影响「别把副作用放进响应模型的校验器」，模型被彻底拆分后本来就没有副作用可放。
下次同步时如果要让它出现在答复里，正确做法是给它单独一个场景（例如「响应模型里的
`model_validator` 每请求打两条日志」），而不是把它塞进 SKILL.md 的 Core rules 抢占位置。

### 评测可比性说明

基线跑完之后、有 skill 那次之前，场景 3 的第 3 条 `expected_behavior` 被改写过一次：原文写的是
「返回 ORM 行只有设了 `from_attributes` 才成立」，而这条被实测推翻（见「被实测推翻的两条常见说法」），
于是改成了 `assert` → `raise ValueError` 那条。**`query` 与 `files` 两次完全相同**，改动只涉及人工
判定的标准文本，不影响模型看到的输入，因此两次运行仍然可比；基线的该条按新标准重新判定为达成。
