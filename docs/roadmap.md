# 主题路线图

粒度：**一个生态 / 一类事情 = 一个 skill**。下列种子上游来自建设期的领域调研，
**执行每个批次前必须按 `docs/workflow.md` Phase A 重新复核** stars、`pushed_at`、许可——
这些数据会随时间变化，路线图只负责记住「往哪儿找」，不负责记住「当时是什么样」。

星标数与推送时间标注的是调研当时的观测值，仅用于判断量级，不作为合入依据。

## Batch 1（已完成）

`apple`、`flutter`、`office`、`frontend-design`、`react`、`skill-authoring`、
`test-driven-development`、`debugging`、`code-review`。

## 全面扩展：波次 1–9（44 个 skill，终态共 53 个）

每波 ≤5 个 skill（AGENTS.md：不得同时让 5 个以上 subagent 工作）。顺序为
平台/语言 → Web/后端 → 数据/云 → 任务/AI → 游戏/Web3/中文生态。

「边界」列是该 skill 的 `## Scope` 否定范围与 `description` 末尾 `Do not use for …` 的内容来源；
括号内 `→ x` 表示转交给哪个 skill。许可标注中 `(无许可)` = GitHub API `license: null`，
`(NOASSERTION)` = 需实读仓库 LICENSE 文件再定；处理方式见「许可处理规则」。

### 波次 1 — 平台与语言 I

| skill | category | 种子上游（Phase A 起点） | 边界 | 状态 |
|---|---|---|---|---|
| `android` | platform | android/skills `jetpack-compose/*`、`navigation/*`、`build-system/agp/*`、`testing/*`、`performance/*`(Apache-2.0, 7.3k★) 主干；Kotlin/kotlin-agent-skills `skills/kotlin-tooling-*`(Apache-2.0)；new-silvermoon/awesome-android-agent-skills(Apache-2.0)；Drjacky/claude-android-ninja(Apache-2.0)；KMP：felipechaux/kmp-compose-multiplatform-skill(MIT)、mmiani/kotlin-kmp-claude-agent-skills(NOASSERTION)、Kotlin `kotlin-tooling-cocoapods-spm-migration`；maxrave-dev/kotlin-footguns(GPL-3.0 → reference)；developer.android.com(docs) | 覆盖 Kotlin + Compose + View 体系 + Gradle/AGP + 测试 + 性能 + KMP/Compose Multiplatform 一节（不单独立 skill）。不覆盖 Flutter(→`flutter`)、React Native(→`react-native`)、iOS 原生(→`apple`)、Kotlin 服务端 Spring(→`java-spring`) | 已完成 |
| `react-native` | platform | expo/skills(MIT, 2.5k★)；callstackincubator/agent-skills `skills/react-native-best-practices`、`upgrading-react-native`、`react-navigation`、`react-native-brownfield-migration`、`create-react-native-library`(MIT) 主干；react-native-community/skills(MIT，交叉校验)；reactnative.dev + docs.expo.dev(docs)；maikotrindade/awesome-react-native-skills(GPL-3.0 → reference) | 覆盖 RN/Expo 运行时（Hermes、New Architecture/Turbo Modules、FlashList、EAS、升级、react-navigation、brownfield）。不覆盖 React 组件/hook/渲染规则(→`react`)、原生模块内部 Swift/Kotlin(→`apple`/`android`)、Flutter(→`flutter`) | 已完成 |
| `typescript` | framework | mattpocock/skills `skills/engineering/{domain-modeling,codebase-design,improve-codebase-architecture}`(MIT) 主干；mcollina/skills `skills/typescript-magician`(MIT)；github/awesome-copilot `skills/javascript-typescript-jest`、`instructions/nodejs-javascript-vitest`(MIT)；giuseppe-trisciuoglio/developer-kit TS 部分(MIT)；fallow-rs/fallow-skills(MIT → reference)；typescriptlang.org handbook(docs) | 覆盖类型层建模、模块/深模块设计、tsconfig 与构建、类型收窄、测试（vitest/jest）。不覆盖 React(→`react`)、服务端框架(→`nodejs-backend`)、Vue/Svelte/Astro | 已完成 |
| `go` | framework | samber/cc-skills-golang `skills/golang-*`(MIT, 3.2k★) 主干（自家库说明书剔除）；spf13/go-skills(无许可 → NONE)；ashwingopalsamy/golangskills.com(Apache-2.0)；github/awesome-copilot `instructions/go`(MIT)；go.dev/doc/effective_go + Go Wiki CodeReviewComments(docs)；douglassantosreis/golang-profiling-analyzer(reference) | 覆盖语言、并发、错误处理、项目布局、testing、pprof、lint、模块管理。不覆盖云 SDK(→`aws`/`gcp`/`azure`)、K8s operator(→`containers`)、MCP server(→`mcp-server`) | 已完成 |
| `python` | framework | trailofbits/skills `plugins/modern-python/skills/modern-python`(CC-BY-SA-4.0 → 只取结构与清单语义) 主干；github/awesome-copilot `skills/python-pypi-package-builder`、`instructions/python-mcp-server` 语言层部分(MIT)；getsentry/skills `skills/typing-exclusion-worker`、`skills/find-bugs`(Apache-2.0)；existential-birds/beagle Python 评审部分(Apache-2.0)；giuseppe-trisciuoglio/developer-kit Python(MIT)；docs.astral.sh/uv、docs.astral.sh/ruff、docs.pytest.org、typing.python.org(docs) | 覆盖 uv/ruff/pyproject/pytest/typing/packaging/asyncio/PEP 723。不覆盖 Django（暂缓）、FastAPI(→`fastapi`)、数据分析、模型训练(→`ml-training`) | 已完成 |

### 波次 2 — 平台与语言 II

| skill | category | 种子上游 | 边界 | 状态 |
|---|---|---|---|---|
| `java-spring` | framework | rrezartprebreza/spring-boot-skills `skills/spring-boot-3/*`、`skills/spring-boot-4/*`(MIT) 主干；github/awesome-copilot `skills/{java-springboot,spring-boot-testing,java-junit,create-spring-boot-java-project,create-spring-boot-kotlin-project,java-add-graalvm-native-image-support}`、`instructions/{springboot,springboot-4-migration,java-17-to-java-21-upgrade,java-21-to-java-25-upgrade}`(MIT)；a-pavithraa/springboot-skills-marketplace(MIT)；spring-ai-community/spring-testing-skills(NOASSERTION → 实读)；Amplicode/spring-skills(无许可 → NONE)；docs.spring.io(docs) | 覆盖 Spring Boot 3/4（Web、Data JPA、Security、Test、Modulith、可观测、3→4 迁移）+ Java 17→25 语言升级。不覆盖 Android Kotlin(→`android`)、云托管细节(→`aws`/`azure`/`gcp`)、REST 契约设计(→`api-design`) | 已完成 |
| `csharp-dotnet` | framework | dotnet/skills `plugins/dotnet-{msbuild,test,aspnetcore,blazor,maui,upgrade,diag}/skills/*`(MIT, 5.4k★) 主干；github/awesome-copilot `skills/{csharp-*,dotnet-*,aspnet-minimal-api-openapi,containerize-aspnetcore}`、`instructions/{csharp,blazor,dotnet-maui,dotnet-architecture-good-practices}`(MIT)；Aaronontheweb/dotnet-skills(MIT)；kevintsengtw/dotnet-testing-agent-skills(MIT)；learn.microsoft.com/dotnet(docs) | 覆盖 C#、SDK/MSBuild/NuGet/CPM、ASP.NET Core、Blazor、MAUI、测试框架、诊断、升级。不覆盖 Unity C#(→`unity`)、Azure 资源编排(→`azure`) | 已完成 |
| `tauri` | platform | full-stack-skills/tauri-skills `skills/*`(NOASSERTION，README 自述 Apache-2.0 → 实读 LICENSE)；nodnarbnitram/claude-code-extensions `tauri-v2`(MIT)；Mindrally/skills `tauri-development`(Apache-2.0，交叉)；v2.tauri.app(docs) | 覆盖 Tauri v2 配置、capabilities/permissions、IPC commands/events、插件、updater、sidecar、打包签名。不覆盖前端框架本身(→`react`/`vue`/`svelte`)、通用 Rust（暂缓）、Electron（暂缓） | 已完成 |
| `chrome-extension` | platform | GoogleChrome/modern-web-guidance `skills/chrome-extensions`(Apache-2.0) 主干；samber/cc-skills `chrome-extension`(MIT)；pproenca/dot-skills `chrome-extension`、`chrome-extension-ui`(MIT)；tenequm/skills `chrome-extension-wxt`(MIT)；quangpl/browser-extension-skills `extension-test`(MIT)；developer.chrome.com/docs/extensions(docs) | 覆盖 MV3 manifest/permissions、service worker、content scripts、消息通道、storage、WXT、测试、上架。不覆盖用浏览器测网页(→`web-testing`)、页面视觉(→`frontend-design`) | 已完成 |
| `github` | platform | github/awesome-copilot `skills/{github-actions-efficiency,github-actions-hardening,github-actions-runtime-upgrade-conventions,copilot-pr-autopilot,pr-dashboard,create-github-issue-feature-from-specification,gen-specs-as-issues,git-flow-branch-creator}`、`instructions/github-actions-ci-cd-best-practices`(MIT, 38.9k★) 主干；getsentry/skills `skills/{gha-security-review,gh-review-requests,iterate-pr,pr-link-issue,pr-writer,create-branch,triage-frontend-issues}`(Apache-2.0)；alpha-omega-security/scrutineer `skills/zizmor`(MIT)；SethGammon/Citadel `skills/{triage,pr-watch}`(MIT)；coderabbitai/skills `skills/autofix`(MIT)；mcollina/skills `skills/octocat`(MIT)；docs.github.com(docs) | 覆盖 Actions 编写/效率/加固（脚本注入、pull_request_target、SHA pinning、permissions、zizmor）、PR 生命周期、Issue 分诊与创建、仓库治理（branch protection、CODEOWNERS、Dependabot、secret scanning）、Releases。不覆盖本地 git 操作(→`git-workflow`)、应用代码安全审计(→`security-review`)、其他 CI 平台、部署目标(→各云 skill) | 已完成 |

### 波次 3 — Web 与后端框架 I

| skill | category | 种子上游 | 边界 | 状态 |
|---|---|---|---|---|
| `vue` | framework | vuejs-ai/skills(MIT, 2.8k★) 主干；onmax/nuxt-skills `skills/{vue,nuxt}`(无许可 → NONE)；antfu/skills `skills/{vue,nuxt}`(MIT，自述 PoC → 交叉校验)；github/awesome-copilot `instructions/vue`、`skills/unit-test-vue-pinia`(MIT)；awesome-skills/code-review-skill Vue 规则(MIT)；vuejs.org + nuxt.com(docs) | 覆盖 Vue 3 Composition API、Pinia、Vue Router、Nuxt 4、测试。不覆盖视觉设计(→`frontend-design`)、React(→`react`)、uni-app 小程序(→`wechat-miniprogram`) | 已完成 |
| `svelte` | framework | sveltejs/ai-tools `svelte-code-writer`(MIT，官方) 定口径；spences10/skills `skills/{svelte-runes,sveltekit-data-flow,sveltekit-structure,sveltekit-remote-functions}`(无许可 → NONE)；ejirocodes/agent-skills `svelte5-best-practices`；github/awesome-copilot `instructions/svelte`(MIT)；svelte.dev(docs)；full-stack-skills/svelte-skills(NOASSERTION → reference) | 覆盖 Svelte 5 runes、SvelteKit 路由/load/form actions/remote functions、测试。不覆盖 Tailwind/视觉(→`frontend-design`) | 已完成 |
| `astro` | framework | withastro/astro `.agents/skills/{astro-developer,astro-code-review}`(仓库 LICENSE MIT，实读)；delineas/astro-framework-agents(MIT)；incluud/astro-agent-skills(MIT)；github/awesome-copilot `instructions/astro`(MIT)；docs.astro.build(docs) | 覆盖 islands/hydration 指令、content collections、SSR adapters、actions、view transitions、集成。不覆盖框架组件内部(→`react`/`vue`/`svelte`)、视觉(→`frontend-design`) | 已完成 |
| `nodejs-backend` | framework | mcollina/skills `skills/{fastify,node,nodejs-core,oauth}`(MIT) 主干；Kadajett/agent-nestjs-skills(无许可 → NONE)；secondsky/claude-skills `plugins/hono-routing`(MIT)；github/awesome-copilot `instructions/nestjs`(MIT)；amirtaherkhani/nestjs-agent-skills(MIT)；nodejs.org/docs + fastify.dev + docs.nestjs.com + hono.dev(docs) | 通用层（生命周期、校验、错误、日志、配置、测试注入、streams/AsyncLocalStorage）+ 框架分支 reference（`fastify.md`、`nestjs.md`、`hono.md`，Express 只在迁移小节）。不覆盖 Next.js server actions/RSC(→`react`)、REST 契约(→`api-design`)、GraphQL(→`graphql`)、类型建模(→`typescript`) | 已完成 |
| `fastapi` | framework | fastapi/fastapi `fastapi/.agents/skills/fastapi`(MIT，官方) 主干；microsoft/skills `skills/{fastapi-router-py,pydantic-models-py}`(MIT，剥离 Azure 语境)；wshobson/agents `fastapi-templates`(MIT)；fastapi.tiangolo.com + docs.pydantic.dev(docs) | 覆盖路由、`Annotated` 依赖注入、Pydantic v2、响应模型、流式（SSE）、后台任务、测试、uv/ruff 工具链。不覆盖 Python 语言层(→`python`)、REST 契约(→`api-design`) | 已完成 |

### 波次 4 — Web 与后端框架 II / 数据 I

| skill | category | 种子上游 | 边界 | 状态 |
|---|---|---|---|---|
| `laravel` | framework | laravel/boost `.ai/laravel/skill/laravel-best-practices`、`.ai/pennant/skill/pennant-development`(MIT，官方) 主干；laravel/agent-skills `laravel/skills/starter-kit-upgrade`(无许可 → NONE；产品包装目录排除)；laravel.com/docs(docs)；github/awesome-copilot `instructions/php-symfony` PHP 层交叉校验(MIT) | **官方特例**。覆盖 Laravel 12+（Eloquent、队列、事件、Pest 测试、Blade/Livewire、Pennant、Artisan）+ 现代 PHP。不覆盖 Laravel Cloud/Forge 托管、WordPress | 已完成 |
| `graphql` | framework | apollographql/skills `skills/{graphql-schema,graphql-operations,apollo-server,apollo-federation,apollo-router}`(MIT) 主干；wshobson/agents `graphql-architect`(MIT)；secondsky/claude-skills `graphql-implementation`(MIT)；LambdaTest/agent-skills `api-skill` GraphQL 测试节(MIT)；graphql.org/learn + spec(docs) | 覆盖 schema 设计（nullability、分页、错误、演进）、操作编写、服务端、联邦；Yoga/graphql-js/Pothos 以官方 docs 校正。不覆盖 REST(→`api-design`)、Apollo Client React 绑定(→`react`) | 已完成 |
| `api-design` | task | Jeffallan/claude-skills `skills/api-designer`(MIT) 主干；wshobson/agents `openapi-spec-generation`(MIT)；AsyrafHussin/agent-skills `api-design-patterns`(MIT)；LambdaTest/agent-skills `api-skill`(MIT)；github/awesome-copilot `skills/openapi-to-application-code`、`instructions/aspnet-rest-apis`(MIT)；OpenAPI 3.1 spec + RFC 9457(docs) | 覆盖资源建模、URI/方法/状态码、分页（cursor/offset/keyset）、错误契约 RFC 9457、版本与弃用、OpenAPI 3.1，验证门 `redocly lint` + `prism mock`。不覆盖框架实现(→`nodejs-backend`/`fastapi`/`java-spring`/`csharp-dotnet`)、GraphQL(→`graphql`) | 已完成 |
| `postgres` | framework | supabase/agent-skills `skills/supabase-postgres-best-practices`(MIT) 主干；neondatabase/agent-skills `skills/neon-postgres`(Apache-2.0，剥离分支/计费)；prisma/skills `prisma-postgres`、`prisma-postgres-setup`(MIT，只作 ORM 接入一节)；github/awesome-copilot `skills/{postgresql-code-review,postgresql-optimization,sql-code-review,sql-optimization}`(MIT)；google/skills `skills/cloud/cloud-sql-basics`(Apache-2.0)；postgresql.org/docs(docs) | 覆盖 schema、索引、EXPLAIN、RLS、迁移、连接池、pgvector 基础、ORM 接入（Prisma/Drizzle 只写 Postgres 侧陷阱）。不覆盖 Supabase 平台面(→`supabase`)、托管控制面(→`aws`/`gcp`/`azure`) | 已完成 |
| `supabase` | framework | supabase/agent-skills `skills/supabase`(MIT，官方) 主干；supabase.com/docs(docs)；CarolMonroe22/lovable-cloud-to-supabase-migration(MIT，迁移一节交叉) | **官方特例**。覆盖 Auth、Storage、Realtime、Edge Functions、CLI 与迁移工作流、RLS 策略编写。不覆盖通用 Postgres 调优(→`postgres`)、Firebase（暂缓） | 已完成 |

### 波次 5 — 数据 II / 云与基础设施 I

| skill | category | 种子上游 | 边界 | 状态 |
|---|---|---|---|---|
| `redis` | framework | redis/agent-skills `skills/redis-*`(MIT，官方) 主干；redis.io/docs(docs)；github/awesome-copilot `skills/upstash-redis`(MIT，交叉校验) | **官方特例**。覆盖数据结构选型、键空间、过期/淘汰、集群与连接、RediSearch/向量、语义缓存、安全、可观测。不覆盖应用侧缓存架构(→各框架 skill)、Memcached | 已完成 |
| `mongodb` | framework | mongodb/agent-skills `skills/mongodb-*`(Apache-2.0，官方) 主干；Azure/documentdb-agent-kit(MIT)；mongodb-developer/edd-skill(无许可 → NONE)；github/awesome-copilot `instructions/mongo-dba`(MIT)；mongodb.com/docs(docs) | **官方特例**。覆盖文档建模（嵌入 vs 引用）、聚合管道、索引与 explain、Atlas Search/向量、连接与驱动。不覆盖关系型(→`postgres`)、Firestore | 已完成 |
| `elasticsearch` | framework | elastic/agent-skills(Apache-2.0，官方) 主干；elastic.co/docs(docs)；若 Phase A 找不到评分 ≥5 的第三方上游，则以「官方 + docs」立项并在 research 备注说明 | **官方特例**。覆盖索引与 mapping 设计、查询 DSL / ES\|QL、相关性、向量检索、集群运维。不覆盖日志可观测流水线(→`observability`)、Kibana 看板 | 已完成 |
| `terraform` | framework | hashicorp/agent-skills `plugins/terraform/skills/*`(MPL-2.0) 主干；antonbabenko/terraform-skill(NOASSERTION → 实读)；LukasNiessen/terrashark(MIT)；github/awesome-copilot `instructions/terraform`(MIT)；nitinjain999/platform-skills Terraform 节(Apache-2.0)；developer.hashicorp.com/terraform(docs) | 覆盖 HCL 风格、模块、state、`terraform test`、policy、refactor、OpenTofu 差异、provider 开发。不覆盖具体云资源字段(→`aws`/`azure`/`gcp`)、Bicep(→`azure`) | 已完成 |
| `containers` | platform | LukasNiessen/kubernetes-skill(MIT) 主干；google/skills `skills/cloud/gke-*`(Apache-2.0，剥离 GKE 专属)；github/awesome-copilot `skills/multi-stage-dockerfile`、`instructions/{containerization-docker-best-practices,kubernetes-deployment-best-practices,kubernetes-manifests,devcontainers}`(MIT)；Impertio-Studio/Docker-Claude-Skill-Package(MIT)；Azure/AKS-Skills(MIT，Day-2 补充)；netresearch/docker-development-skill(NOASSERTION → reference)；docs.docker.com + kubernetes.io/docs(docs) | 覆盖 Dockerfile/多阶段/Compose、K8s 清单、Helm/Kustomize、探针与资源限制、Pod 安全、滚动更新、devcontainer。不覆盖托管集群控制面(→`aws`/`azure`/`gcp`)、服务网格产品 | 已完成 |

### 波次 6 — 云与基础设施 II

| skill | category | 种子上游 | 边界 | 状态 |
|---|---|---|---|---|
| `aws` | platform | awslabs/agent-plugins `plugins/{aws-serverless,deploy-on-aws,databases-on-aws}/skills/*`(Apache-2.0，官方) 主干；aws/agent-toolkit-for-aws(Apache-2.0)；aws-samples/sample-well-architected-skills-and-steering(MIT-0)；itsmostafa/aws-agent-skills(MIT)；zxkane/aws-skills(MIT)；github/awesome-copilot `skills/aws-*`(MIT)；docs.aws.amazon.com(docs) | 覆盖控制面与架构（IAM、Lambda/Step Functions/API Gateway、部署、Well-Architected、成本、CDK 选型）。不覆盖 Terraform 语法(→`terraform`)、K8s 通用(→`containers`)、Bedrock 应用开发(→`ai-engineering`) | 已完成 |
| `azure` | platform | microsoft/azure-skills `skills/*`(MIT，官方) 主干；github/awesome-copilot `skills/azure-*`、`instructions/{azure-verified-modules-bicep,bicep-code-best-practices,azure-naming}`(MIT)；Azure/azure-functions-skills(MIT)；ricmmartins/azure-sre-agent-skills(MIT)；MicrosoftDocs/Agent-Skills(CC-BY-4.0，署名)；learn.microsoft.com/azure(docs) | 覆盖资源编排（Bicep、azd）、诊断、成本/配额、Entra、Functions、AKS 控制面、Well-Architected。不覆盖 K8s 通用(→`containers`)、.NET 代码(→`csharp-dotnet`)、Foundry LLM 应用(→`ai-engineering`) | 已完成 |
| `gcp` | platform | google/skills `skills/cloud/*`(Apache-2.0，官方) 主干；gemini-cli-extensions/google-cloud-storage(Apache-2.0)；google/agents-cli 部署部分(Apache-2.0 → reference)；cloud.google.com/docs(docs) | 覆盖 gcloud、IAM、Cloud Run、Cloud SQL、GCS、Logging/Monitoring、Well-Architected、GKE 控制面。不覆盖 K8s 通用(→`containers`)、Firebase（暂缓）、Gemini API(→`ai-engineering`) | 已完成 |
| `cloudflare` | platform | cloudflare/skills `skills/{workers-best-practices,wrangler,durable-objects,cloudflare,cloudflare-one,nextjs-on-cloudflare,agents-sdk}`(Apache-2.0，官方) 主干；jezweb/claude-skills(MIT，剥离 React/Tailwind)；secondsky/claude-skills Cloudflare 部分(MIT)；xiaoyuboi/cloudflare-tunnel-skill(MIT)；developers.cloudflare.com(docs) | 覆盖 Workers/Pages、Durable Objects、KV/R2/D1/Queues、wrangler、Cloudflare One、Tunnel。不覆盖通用 Web 性能(→`frontend-design`)、Next.js 本身(→`react`) | 已完成 |
| `observability` | task | ollygarden/opentelemetry-agent-skills `skills/otel-*`(Apache-2.0) 主干；getsentry/skills `skills/{sentry-sdk-setup,sentry-workflow}` + getsentry/sdk-skills(Apache-2.0)；grafana/skills(Apache-2.0)；dash0hq/agent-skills(Apache-2.0)；github/awesome-copilot `skills/appinsights-instrumentation`(MIT)；opentelemetry.io/docs(docs) | 覆盖 OTel 埋点/Collector/语义约定、结构化日志、RED/USE 指标、追踪、告警与 SLO、从告警反查代码。不覆盖本地调试(→`debugging`)、各云监控产品面(→`aws`/`azure`/`gcp`)、ES 索引设计(→`elasticsearch`) | 已完成 |

### 波次 7 — 任务类 I

| skill | category | 种子上游 | 边界 | 状态 |
|---|---|---|---|---|
| `security-review` | task | getsentry/skills `skills/security-review`(Apache-2.0) 主干；cloudflare/security-audit-skill(MIT, 3.3k★)；github/awesome-copilot `skills/{security-review,agent-owasp-compliance}`、`instructions/security-and-owasp`(MIT)；openai/skills `skills/{security-best-practices,security-threat-model,security-ownership-map}`(无许可 → NONE)；trailofbits/skills `plugins/differential-review`、`semgrep-rule-creator`、`insecure-defaults`(CC-BY-SA-4.0 → 结构)；OWASP ASVS/Top 10(docs) | 覆盖整仓/功能级安全审计：威胁建模、OWASP 类漏洞、密钥泄露、依赖与供应链、semgrep 规则、报告格式。不覆盖 diff 的通用正确性评审(→`code-review`)、GHA 加固(→`github`)、合约审计(→`solidity-web3`)、渗透测试 | 已完成 |
| `web-testing` | task | microsoft/playwright-cli `skills/playwright-cli`(Apache-2.0) 主干；anthropics/skills `skills/webapp-testing`(实读该目录 LICENSE.txt)；vercel-labs/agent-browser(Apache-2.0)；currents-dev/playwright-best-practices-skill(MIT)；github/awesome-copilot `skills/{playwright-generate-test,playwright-explore-website,webapp-testing,chrome-devtools}`、`instructions/playwright-typescript`(MIT)；addyosmani/agent-skills `browser-testing-with-devtools`(MIT)；playwright.dev(docs) | 覆盖真实浏览器 E2E：locator 策略、断言、flaky 治理、截图/控制台/网络、鉴权状态、CI。不覆盖单元测试方法论(→`test-driven-development`)、Lighthouse 性能/a11y 审计(→`frontend-design`)、造扩展(→`chrome-extension`) | 已完成 |
| `planning` | task | obra/superpowers `skills/{brainstorming,writing-plans,executing-plans}`(MIT) 主干；mattpocock/skills PRD / issue-triage 类(MIT，目录在 Phase A 用 `gh api …/git/trees` 确认)；github/awesome-copilot `skills/{create-specification,create-implementation-plan,breakdown-plan,breakdown-feature-prd,prd,update-implementation-plan}`(MIT)；NeoLabHQ/context-engineering-kit `plugins/sdd`(GPL-3.0 → reference) | 覆盖需求澄清→设计定稿→计划文档→执行跟踪。不覆盖写 SKILL.md(→`skill-authoring`)、TDD 循环(→`test-driven-development`)、在 GitHub 上建 issue 的机械动作(→`github`) | 已完成 |
| `git-workflow` | task | obra/superpowers `skills/{using-git-worktrees,finishing-a-development-branch}`(MIT)；mattpocock/skills `git-guardrails`、`resolving-merge-conflicts`(MIT)；github/awesome-copilot `skills/{git-commit,conventional-commit}`(MIT)；getsentry/skills `skills/{commit,create-branch}`(Apache-2.0)；fvadicamo/dev-agent-skills(MIT)；git-scm.com/docs(docs) | 覆盖本地 git：分支策略、worktree、rebase/merge 与冲突、提交粒度与信息、历史重写护栏、分支收尾。不覆盖 PR/Issue/Actions/`gh`(→`github`)、评审内容(→`code-review`) | 已完成 |
| `mcp-server` | task | anthropics/skills `skills/mcp-builder`(实读目录 LICENSE.txt) 主干；microsoft/skills `skills/mcp-builder`(MIT)；github/awesome-copilot `skills/{typescript,python,go,java,rust}-mcp-server-generator`、`skills/dotnet-mcp-builder`、`skills/{mcp-security-audit,mcp-implementation-security-review}`、`instructions/*-mcp-server`(MIT)；cloudflare/skills `agents-sdk` MCP 部分(Apache-2.0)；modelcontextprotocol.io spec(docs) | 覆盖设计与实现 MCP server：工具命名与 schema、错误信息、传输（stdio/HTTP）、鉴权、测试、安全审计。不覆盖写 skill(→`skill-authoring`)、使用某个 MCP 产品 | 已完成 |

### 波次 8 — 任务类 II / AI / Web3 / 中文生态 I

| skill | category | 种子上游 | 边界 | 状态 |
|---|---|---|---|---|
| `technical-writing` | task | mattpocock/skills `edit-article`、`teach`(MIT) 主干；mcollina/skills `skills/documentation`(MIT，Diátaxis)；github/awesome-copilot `skills/{create-readme,documentation-writer,readme-blueprint-generator,docs-sync-audit}`、`instructions/update-docs-on-code-change`(MIT)；diataxis.fr(docs, CC-BY-SA)；NeoLabHQ `write-concisely`(GPL-3.0 → reference) | 覆盖 README、文档站（Diátaxis 四象限）、教程、技术文章、ADR、changelog。不覆盖 SKILL.md(→`skill-authoring`)、OpenAPI 参考生成(→`api-design`)、营销文案 | 已完成 |
| `ai-engineering` | task | vercel/ai `skills/use-ai-sdk`(NOASSERTION → 实读)；langchain-ai/langchain-skills `config/skills/{langchain-rag,eval-engineering,langgraph-fundamentals,langgraph-persistence}`(无许可 → NONE)；google/skills `skills/{gemini-api-dev,vertex-ai-api-dev}`(Apache-2.0)；huggingface/skills `skills/{hugging-face-evaluation,datasets}`(Apache-2.0)；muratcankoylan/Agent-Skills-for-Context-Engineering(MIT)；obra/superpowers `skills/{dispatching-parallel-agents,subagent-driven-development}`(MIT)；github/awesome-copilot `skills/{agentic-eval,ai-prompt-engineering-safety-review}`(MIT)；platform.claude.com + platform.openai.com(docs) | 两大节：应用层（提示、结构化输出、tool calling、RAG、评测）与 agent 层（循环、记忆、子代理编排、上下文压缩）。不覆盖训练/微调(→`ml-training`)、向量库运维(→`redis`/`mongodb`/`postgres`/`elasticsearch`)、MCP server 实现(→`mcp-server`)、写 skill(→`skill-authoring`) | 已完成 |
| `ml-training` | task | NVIDIA/skills `skills/Megatron-Bridge/*`、`Model-Optimizer/*` 精选(Apache-2.0)；huggingface/skills `skills/hugging-face-model-trainer`、`hugging-face-evaluation`(Apache-2.0) 主干；Orchestra-Research/AI-Research-SKILLs 训练/推理部分(MIT)；pytorch.org/docs + huggingface.co/docs/trl(docs) | 覆盖训练/微调（SFT/DPO/GRPO）、量化、分布式并行、OOM 排查、评测、推理部署（vLLM）。不覆盖调用第三方 LLM API(→`ai-engineering`)、科研生信 | 已完成 |
| `solidity-web3` | framework | pashov/skills `solidity-auditor`(MIT)；wshobson/agents `solidity-security`(MIT)；0xlayerghost/solidity-agent-kit(MIT)；trailofbits/skills `building-secure-contracts`(CC-BY-SA-4.0 → 结构)；OpenZeppelin/openzeppelin-skills、Cyfrin/solskill(AGPL-3.0 → reference)；docs.soliditylang.org(docs) | 覆盖合约编写、升级模式（代理）、Foundry 测试/fuzz、审计清单、Slither。不覆盖通用应用安全审计(→`security-review`)、钱包/交易 API 产品、dApp 前端(→`react`) | 已完成 |
| `harmonyos` | platform | linhay/harmony-next.skills `skills/harmony-next`(无许可 → NONE)；CoreyLyn/harmonyos-skills `harmonyos-dev`、`harmonyos-review`(MIT)；openharmonyinsight/openharmony-skills(无许可 → NONE)；web-infra-dev/midscene-skills `harmonyos-device-automation`(MIT)；KwaiAppTeam/ks-arkts-skills(无许可 → NONE)；developer.huawei.com/consumer/cn/doc(docs) | 覆盖 ArkTS、ArkUI 状态管理、Stage 模型、DevEco 构建/签名/上架、Android→鸿蒙迁移、设备自动化验证。不覆盖 Android/iOS 本身(→`android`/`apple`)、Flutter OHOS | 已完成 |

### 波次 9 — 中文生态 II / 游戏引擎

| skill | category | 种子上游 | 边界 | 状态 |
|---|---|---|---|---|
| `wechat-miniprogram` | platform | TencentCloudBase/awesome-miniprogram-skills(MIT) 主干；whinc/super-skills `miniprogram-automation`、`miniprogram-ci`(无许可 → NONE)；sonofmagic/skills `wevu-best-practices`、`weapp-tailwindcss-setup`(MIT)；uni-helper/skills `uni-app`(MIT，推送时间临界 → Phase A 复核)；developers.weixin.qq.com/miniprogram/dev(docs) | 覆盖小程序运行时（双线程、setData、生命周期、原生组件层级）、uni-app/Taro 工程、miniprogram-ci 上传、审核规范；排除云开发 CloudBase API。不覆盖 Vue 本身(→`vue`)、H5 | 已完成 |
| `unity` | platform | gamedev-skills/awesome-gamedev-agent-skills `skills/unity-*`(Apache-2.0) 主干；Unity-Technologies/skills `skills/{unity-cli,new-unity-project,ui-uitk,urp-postprocessing,optimize-*}`(NOASSERTION → 实读 LICENSE；专有则 reference)；wshobson/agents `unity-ecs-patterns`(MIT)；docs.unity3d.com(docs) | 覆盖 Unity 6 编辑器/CLI、C# 脚本约定、URP、UI Toolkit、DOTS、构建。不覆盖 C# 语言与 .NET 工程(→`csharp-dotnet`)、Godot/Unreal | 已完成 |
| `godot` | platform | gamedev-skills/awesome-gamedev-agent-skills `skills/godot-*`(Apache-2.0) 主干；wshobson/agents `godot-gdscript-patterns`(MIT)；thedivergentai/GD-Agentic-Skills(LGPL-3.0 → reference)；docs.godotengine.org(docs, CC-BY-3.0) | 覆盖 Godot 4 节点/场景树、GDScript、signals、物理、导出、多人。不覆盖 C# 语言(→`csharp-dotnet`) | 已完成 |
| `unreal` | platform | gamedev-skills/awesome-gamedev-agent-skills `skills/unreal-*`(Apache-2.0) 主干；EpicGames/unreal-engine-skills-for-claude-code-plugin(MIT，官方)；maystudios/claude-skills `unreal-*`(MIT)；kevinpbuckley/unreal-engine-skills(无许可 → NONE)；quodsoler/unreal-engine-skills(MIT，推送时间临界 → 复核)；dev.epicgames.com/documentation(docs) | 覆盖 UE5 C++ Gameplay Framework、Blueprint、GAS、Enhanced Input、Niagara、复制、打包。不覆盖通用 C++ | 已完成 |

三个游戏引擎同波：SKILL.md 章节与 `references/` 命名保持同构（`scripting`、`rendering`、`ui`、
`physics`、`build`）。

## 官方厂商特例主题

按「新增主题的判据」第 4 条立项，`research/<skill>.md` 标题下第一行写「单一权威上游改写」。

| skill | 官方上游 | 许可 |
|---|---|---|
| `supabase` | supabase/agent-skills `skills/supabase` | MIT |
| `redis` | redis/agent-skills | MIT |
| `mongodb` | mongodb/agent-skills | Apache-2.0 |
| `elasticsearch` | elastic/agent-skills | Apache-2.0 |
| `laravel` | laravel/boost `.ai/laravel/skill/*` | MIT |

## 跨 skill 分界句（两边 SKILL.md 原文照抄，字面一致）

| 一对 | 分界句 |
|---|---|
| `git-workflow` / `github` | 能离线只靠 git 完成的归 `git-workflow`；需要 GitHub（Actions、PR、Issue、`gh`、仓库设置）的归 `github` |
| `postgres` / `supabase` | RLS 策略语法与性能归 `postgres`；Supabase Auth 上下文（`auth.uid()`、JWT claims）与 dashboard/CLI 流程归 `supabase` |
| `code-review` / `security-review` | 评审一个 diff 时的安全视角归 `code-review`；对整个仓库、功能或威胁面做审计归 `security-review` |
| `debugging` / `observability` | 有可复现的本地失败归 `debugging`；只有生产信号（日志/指标/追踪/告警）归 `observability` |

## 许可处理规则

| 上游许可 | `relation` | 做法 |
|---|---|---|
| MIT / Apache-2.0 / BSD / MIT-0 / CC-BY-4.0 | merged | 重写合入；CC-BY-4.0 在 `notes` 写署名 |
| MPL-2.0（hashicorp） | merged | 派生 reference 首行加 `<!-- Adapted from hashicorp/agent-skills (MPL-2.0); see NOTICE.md -->` |
| CC-BY-SA-4.0（trailofbits、diataxis） | merged | 只取结构与清单语义，全部用自己的话重写 |
| 无许可但公开（API `license: null`） | merged | `license: NONE`，`notes: "No licence file; used under the repository's permissive-attribution policy, no text copied verbatim"` |
| NOASSERTION | 先实读 LICENSE/README | 明确开源 → 按其许可；专有 → reference；缺失 → 视同无许可 |
| GPL-2.0 / GPL-3.0 / LGPL-3.0 / AGPL-3.0 | **reference** | 只用其主题清单判断覆盖面；每条事实改从官方文档取证 |
| Proprietary | reference | 与 Batch 1 `office` 同 |

## 暂缓与排除

| 主题 | 处置 | 理由 |
|---|---|---|
| `angular`、`firebase`、`dbt` | 用户暂缓 | 官方单一上游合格，用户本轮不要 |
| `django` | 暂缓 | 无官方上游；社区仅 imankulov(1★)、saaspegasus（维护脚本） |
| `rust` | 暂缓 | 仅 apollographql `rust-best-practices` 一份通用权威；其余框架专用或零采纳 |
| `electron` | 暂缓 | electron/electron 的 skills 是维护 Electron 本身；应用开发上游仅两家个人 |
| auth（auth0 / clerk / better-auth） | 排除 | SaaS 产品官方仓库，属产品包装类 |
| `wordpress` | 暂缓 | 官方仓 NOASSERTION，第二上游 GPL-2.0 且面向核心贡献者 |
| `data-analysis` | 暂缓 | 活跃上游几乎全是数据库产品用法；duckdb/duckdb-skills(541★, MIT) 可下轮重估 |
| `google-workspace` | 暂缓 | 用户暂不需要（Batch 1 决定，保留） |
| `incident-response`、`refactoring`、`performance-profiling`、`prompt-engineering`、`database-migration`、`dependency-upgrade` | 不立项 | 既有/本轮 skill 的子集（分别 → `observability`+`debugging`、`code-review`+`test-driven-development`、`frontend-design`/`ml-training`、`ai-engineering`、各数据库 skill、各生态 skill） |
| `web-accessibility`、`web-performance`、`seo`、`tailwind`、`animation` | 不立项 | `frontend-design` 子集；下次同步 `frontend-design` 时评估追加 addyosmani/web-quality-skills |
| `kotlin-multiplatform`、`prisma`、`agent-building`、`github-actions` | 并入 | 分别 → `android`、`postgres`、`ai-engineering`、`github` |
| `sql-general`、`linux-ops`、`cpp`、`shell-scripting`、`ruby-rails`、`htmx`、`wasm`、`embedded`、`cli-tooling`、`web-scraping`、`ecommerce`、`vector-db` | 无合格上游 | 无权威活跃上游，或属产品包装 |

## 已排除主题（Batch 1 起沿用）

| 类别 | 例子 | 排除原因 |
|---|---|---|
| Anthropic 内部 / 营销类 | `brand-guidelines`、`internal-comms`、`academy-guide`、`discernment-nudge` | 与本仓库的工程定位无关，且多为专有许可 |
| SaaS 产品包装类 | Lark、HeyGen、RunComfy 等 | 本质是某个产品的 API 说明书，随产品变动腐化，且不构成通用工程能力 |
| joke skill | `caveman` | 无工程价值 |
| 营销文案类 | 各类 copywriting skill | 与仓库范围（软件工程）不符 |

## 种子更正记录

调研期路线图里记下、但本轮复核发现不成立的种子：

| 原种子 | 复核结论 | 处理 |
|---|---|---|
| `vercel-labs/vercel-react-native-skills` | 仓库不存在 | 从 `react-native` 种子中删除 |
| getsentry/skills `languages/python.md` | 已不在仓库树中 | 从 `python` 种子中删除，改用 trailofbits + awesome-copilot |
| getsentry/skills `infrastructure/` | 不存在 | 从 `containers` 种子中删除 |
| `java-spring`「尚未找到合格上游」 | 已有 rrezartprebreza/spring-boot-skills 等多个合格上游 | 更新为正式立项 |

## 新增主题的判据

一个主题值得单独立 skill，当且仅当：

1. 它对应一次真实任务的完整上下文——不需要同时加载另一个同级 skill 才能干活；
2. 至少存在 3 个活跃（6 个月内有推送）、评审量表总分 ≥8 的上游可供合成；
3. 它不是既有 skill 的子集。`swiftui` 属于 `apple`，`tailwind` 属于 `react` / `frontend-design`，
   都不单独立项。
4. **官方厂商特例**：该生态的官方组织（框架/引擎/数据库的维护方本身，不含 SaaS 产品）维护着活跃
   skill 仓库时，允许以「该官方仓库（merged）+ 官方文档（`kind: docs`，merged）+ ≥1 个社区或
   跨厂商上游（可为 reference）」立项；`research/<skill>.md` 标题下第一行写「单一权威上游改写」。
