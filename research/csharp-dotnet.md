# csharp-dotnet 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `gh api search/repositories`：`dotnet skills SKILL.md in:name,description,readme`、`csharp agent skills`、
    `aspnetcore claude skill`、`blazor agent skill`、`dotnet agent-skills`
  - `github/awesome-copilot` 全树过滤 `skills/` 与 `instructions/` 中 `csharp|dotnet|aspnet|blazor|maui|nuget|msbuild|xunit|nunit|mstest|ef-core`
  - 领域官方组织仓库：`dotnet/`（skills、docs、AspNetCore.Docs、maui、aspnetcore、efcore、runtime、core）、
    `microsoft/`、`JetBrains/`
  - 官方文档：learn.microsoft.com（`/dotnet`、`/aspnet/core`）支持内容协商返回 markdown，逐条核对事实
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- `gh auth status`：已登录（账号 Lynricsy），全程未触发限流，无匿名回退。

### 当前版本基线（写正文前先核实）

`gh api repos/dotnet/core/contents/release-notes/releases-index.json` 解码后：

| 通道 | 最新版本 | 类型 | 支持阶段 | EOL |
|---|---|---|---|---|
| 11.0 | 11.0.0-rc.1 | sts | go-live | — |
| 10.0 | 10.0.12 | **lts** | **active** | 2028-11-14 |
| 9.0 | 9.0.20 | sts | maintenance | 2026-11-10 |
| 8.0 | 8.0.31 | lts | maintenance | 2026-11-10 |

结论：正文以 **.NET 10（LTS，C# 14）为默认目标**，`net11.0`/C# 15 作为「即将 GA 的 STS」提一句；
`net8.0` 只在「还没升上来的仓库」语境出现。语言版本随 TFM 绑定这一点由
learn.microsoft.com/dotnet/csharp/language-reference/configure-language-version 核实
（表中同时列出 `15.0` 与 `14.0`，并明确「不支持使用比 TFM 对应版本更新的 C# 语言版本」、
「不要把 `LangVersion` 设成 `latest`」）。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | dotnet/skills（`plugins/dotnet-{msbuild,nuget,aspnetcore,blazor,maui,test,test-migration,upgrade,diag,data,advanced}/skills/*`） | https://github.com/dotnet/skills | 5398 | 2026-09-10 | MIT | MSBuild/CPM/Web API/Blazor/MAUI/测试/升级/诊断/EF Core/SIMD，逾 100 个 skill | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | .NET 团队自营，规则级具体（`.props` 里 `$(TargetFramework)` 静默为空、NU1008、AP-01..AP-23 反模式目录）。**只取与本 skill 边界对应的 28 个目录**，见备注 |
| 2 | github/awesome-copilot（`skills/{csharp-async,csharp-xunit,csharp-nunit,csharp-mstest,csharp-tunit,dotnet-best-practices,dotnet-design-pattern-review,dotnet-upgrade,aspnet-minimal-api-openapi,nuget-manager,ef-core}`、`instructions/{csharp,blazor,dotnet-maui,dotnet-architecture-good-practices,aspnet-rest-apis,dotnet-upgrade}`） | https://github.com/github/awesome-copilot | 38860 | 2026-09-10 | MIT | C# 风格、测试框架四选、minimal API + OpenAPI、DDD 分层 | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE | GitHub 官方，覆盖面广但多为「条目式建议」，具体性低（`csharp-async` 通篇是命名/返回类型清单，没有一条讲 `ValueTask` 只能消费一次）。作交叉校验与版本口径（C# 14 当前）而非主干 |
| 3 | Aaronontheweb/dotnet-skills（`skills/{csharp-nullable-reference-types,csharp-concurrency-patterns,csharp-type-design-performance,csharp-api-design,csharp-coding-standards,package-management,project-structure,microsoft-extensions-dependency-injection,microsoft-extensions-configuration,serialization,aot-trimming,snapshot-testing,testcontainers}`） | https://github.com/Aaronontheweb/dotnet-skills | 1148 | 2026-09-10 | MIT | C# 语言层、并发选型、DI 组织、包管理、AOT | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | Akka.NET 维护者（公认专家）。NRT 属性目录（`NotNullWhen`/`MemberNotNull`/`DoesNotReturnIf`）与并发升级阶梯是全场最细的。Akka/Aspire 专属目录不取 |
| 4 | learn.microsoft.com/dotnet（源 `dotnet/docs`） | https://learn.microsoft.com/dotnet | 4764 | 2026-09-10 | CC-BY-4.0 | DI 指南与反模式、MTP、语言版本、ConfigureAwait、诊断工具 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 仓库根 `LICENSE` 实读为 CC BY 4.0（不是 API 报的空值/NOASSERTION），可 merged，`notes` 写署名。所有裁决的最终依据 |
| 5 | learn.microsoft.com/aspnet/core（源 `dotnet/AspNetCore.Docs`） | https://learn.microsoft.com/aspnet/core | 13136 | 2026-09-10 | CC-BY-4.0 | ASP.NET Core DI 生命周期、中间件、Blazor 渲染模式与预渲染 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 同上，`LICENSE` 实读为 CC BY 4.0。Blazor 四种渲染模式表、`RendererInfo`、中间件构造注入 scoped 抛异常均由此核实 |
| 6 | wieslawsoltes/Performance-Skill | https://github.com/wieslawsoltes/Performance-Skill | 35 | 2026-07-28 | MIT | 证据优先的性能/诊断流程、跨平台工具选择 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE | Avalonia 作者。「不许只凭一次平均值宣布修好」「不许从 RSS 推断托管保留量」这类度量纪律，dotnet/skills 的 diag 目录没有 |
| 7 | kevintsengtw/dotnet-testing-agent-skills（`skills/dotnet-testing-*`） | https://github.com/kevintsengtw/dotnet-testing-agent-skills | 28 | 2026-08-16 | MIT | xUnit v3/TUnit、`TimeProvider`、`IFileSystem`、测试替身、集成测试 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 正文为繁体中文，只取语义并全部改写为英文。可测性抽象（`TimeProvider`、`System.IO.Abstractions`）与 `WebApplicationFactory` 边界规则有效；库选型清单（AutoFixture/Bogus/NSubstitute/AwesomeAssertions）按标准第 3 节收敛为「一个默认 + 一个逃生口」 |
| 8 | dennisdoomen/CSharpGuidelines（`Skills/csharp-guidelines` + `_rules/`） | https://github.com/dennisdoomen/CSharpGuidelines | 776 | 2026-07-21 | CC-BY-SA-4.0（API 报 NOASSERTION，实读 `LICENSE.md` 为 CC BY-SA 4.0） | AV0100–AV2400 分类的 C# 编码/设计规则 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE（受限） | 只取**分类结构与清单语义**（成员设计、异常、命名、布局的检查点覆盖面），一句话不复制，全部用自己的话重写 |
| 9 | JetBrains/rider-skills | https://github.com/JetBrains/rider-skills | 22 | 2026-09-01 | Apache-2.0 | Rider 内的调试/重构/找测试 | 2 | 3 | 2 | 3 | 2 | 12 | MAYBE → reference | 官方厂商但全部经 `execute_tool` 绑定 Rider MCP，且 frontmatter 带 `allowed-tools`（本仓库禁用的 agent 绑定）。「先用调试器拿运行时证据、compile error 不进调试器」的判据已由 `debugging` skill 覆盖；仅用于覆盖面自检 |
| 10 | microsoft/skills（`.github/plugins/azure-sdk-dotnet/skills/*`） | https://github.com/microsoft/skills | 3006 | 2026-09-10 | MIT | Azure SDK for .NET 各服务客户端 | 3 | 3 | 2 | 3 | 2 | — | REJECT（越界） | 其 .NET 内容全部是 Azure 服务客户端用法，落在本 skill 明确排除的「Azure 资源编排/云 SDK」一侧。没有语言/SDK/框架层内容 |
| 11 | dotnet/efcore（`.agents/skills/{model-building,change-tracking,query-pipeline,migrations,...}`） | https://github.com/dotnet/efcore | 14790 | 2026-09-10 | MIT | EF Core **实现内幕** | 3 | 3 | 3 | 3 | 2 | — | REJECT（受众不符） | 实读 `model-building/SKILL.md`：讲 `ConventionSet`/`RuntimeModelConvention` 源码路径，`user-invocable: false`，面向 EF Core 贡献者而非应用开发者。应用侧 EF Core 用 dotnet/skills 的 `optimizing-ef-core-queries` |
| 12 | dotnet/maui（`.github/skills/*`）、dotnet/aspnetcore（`.github/skills/*`）、dotnet/runtime（`.github/skills/*`） | https://github.com/dotnet/maui | 23323 / 38433 / 18262 | 2026-09-10 | MIT | 仓库自身的 CI 修复、PR 评审、Helix 测试、JIT 回归 | 3 | 3 | 3 | 3 | 2 | — | REJECT（受众不符） | 全是维护 .NET 本体的流程 skill（`run-helix-tests`、`fuzzlyn-triage`、`api-proposal`）。MAUI/ASP.NET Core 的应用侧指引在 dotnet/skills 的对应 plugin 里 |
| 13 | Postpartum-genushyacinthus29/dotnet-skills | https://github.com/Postpartum-genushyacinthus29/dotnet-skills | 10 | 2026-09-10 | MIT | 与 dotnet/skills 同构（`agents/dotnet-ai`、`agents/dotnet-build`…） | 0 | 3 | 3 | — | 2 | — | REJECT（重复） | `fork: false` 但描述与目录结构是 dotnet/skills 的再发布，无独立贡献；引它等于把同一份内容 pin 两次 |
| 14 | CrestApps/CrestApps.AgentSkills | https://github.com/CrestApps/CrestApps.AgentSkills | 13 | 2026-08-28 | MIT | Orchard Core / CrestApps 模块用法（约 200 个 `orchardcore-*`） | 1 | 3 | 2 | — | 2 | 4 | REJECT | 单一 CMS 产品说明书，属产品包装类；与「C#/.NET 通用工程」无交集 |
| 15 | burakdmir/abp-skills | https://github.com/burakdmir/abp-skills | 17 | 2026-08-14 | MIT | ABP Framework | 1 | 3 | 2 | — | 2 | 4 | REJECT | 同上，第三方应用框架说明书 |
| 16 | tunahanaliozturk/secure-dotnet-skills | https://github.com/tunahanaliozturk/secure-dotnet-skills | 1 | 2026-06-21 | MIT | 12 个「判断式」安全/性能/并发 skill，语境绑 Azure | 0 | 2 | 2 | — | 2 | 6 | REJECT | 零采纳（1★），且自述面向「.NET on Azure」，安全审计部分也不属本 skill 边界 |
| 17 | Azure-Samples/agent-skills-dotnet-demo | https://github.com/Azure-Samples/agent-skills-dotnet-demo | 45 | 2026-04-10 | MIT | 演示如何在 Microsoft Agent Framework 里用 skill 的 .NET 控制台样例 | 2 | 0 | 1 | — | 2 | 5 | REJECT | 是「用 .NET 写 agent」的示例应用，不是 .NET 工程指引；且 >5 月未推送 |
| 18 | syncfusion/maui-toolkit-ui-components-skills | https://github.com/syncfusion/maui-toolkit-ui-components-skills | 39 | 2026-09-09 | 无（API `license: null`） | Syncfusion MAUI 控件用法 | 1 | 3 | 2 | — | 0 | 6 | REJECT | 商业控件库包装；MAUI 一节只需框架自带控件（`CollectionView`、Shell），不引入厂商控件 |
| 19 | dotnet/roslynator | https://github.com/dotnet/roslynator | 3478 | 2026-09-02 | NOASSERTION | Roslyn 分析器/重构产品 | 2 | 3 | — | — | 1 | — | REJECT（形态不符） | 是分析器产品仓库，没有 `SKILL.md`；分析器配置在正文中改由官方 `AnalysisLevel`/`EnforceCodeStyleInBuild` 文档取证 |
| 20 | VoltAgent/awesome-agent-skills | https://github.com/VoltAgent/awesome-agent-skills | 34030 | 2026-09-07 | MIT | 目录索引 | 1 | 3 | 0 | — | 2 | — | REJECT（索引） | 只用于发现候选，自身无 .NET 内容 |
| 21 | dotnet/core `release-notes/releases-index.json` | https://github.com/dotnet/core | 22033 | 2026-09-09 | MIT | 机器可读的通道/支持状态索引 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: docs`） | 不是 skill，但正文「默认目标是哪个版本」必须由它决定而不是凭印象。每次同步重读 |

## 深度审查

### 1. dotnet/skills（主干）

- **结构**：`plugins/<plugin>/skills/<skill>/{SKILL.md,references/*}`，逾 100 个 skill。frontmatter 是
  `name`/`description`/`license: MIT`，少数带 `metadata.{portability,binding,binding-revision}`（`run-tests`）——
  这些专属字段在合入时全部剥离。
- **质量**：`msbuild-antipatterns`（409 行，AP-01..AP-23，每条 Smell/Why/Fix + BAD→GOOD）与
  `directory-build-organization`（`.props`/`.targets` 求值顺序表 + 故障表）是本次调研里信息密度最高的两份。
  `property-patterns` 明确写出「`.props` 中 `$(TargetFramework)` 对单目标项目为空」这个静默失败，
  和 `directory-build-organization` 的 ⚠️ 段相互印证。
- **agent 绑定**：`run-tests` 要求读取仓库根 `.agents/skill-overlays/dotnet-test/run-tests.md` 覆盖文件，
  `analyzing-dotnet-performance` 要求「从 SKILL.md 所在目录解析 bundled 路径」。两者都是上游自家的
  分发约定，本 skill 不复制这套机制，只取其技术判据。
- **过度分叉**：测试相关有 20 个 skill（`assertion-quality`/`crap-score`/`test-smell-detection`/
  `test-gap-analysis`/`test-tagging`…），彼此靠 description 里的长串「DO NOT USE FOR」互斥。这套切法服务于
  「一个 skill 一个动作」的分发模型，与本仓库「一个生态一个 skill」冲突：合入时压缩为
  `references/testing.md` 的一节，不保留 20 个入口。
- **重叠**：`convert-to-cpm`（NuGet plugin）与 `directory-build-organization`（MSBuild plugin）都讲 CPM，
  前者是「转换流程 + 证据产物」，后者是「文件放哪」。取前者的流程骨架 + 后者的求值顺序。

### 2. Aaronontheweb/dotnet-skills

- **结构**：`skills/<name>/{SKILL.md, *.md}`，frontmatter 带 `invocable: false` / `version` / `tags`（剥离）。
- **质量**：`csharp-nullable-reference-types` 把 `System.Diagnostics.CodeAnalysis` 全属性目录讲清楚，
  并给了「先用控制流收窄、把可空处理留在边界，再考虑 `!`」这条排序——比「别用 `!`」有用得多。
  `csharp-concurrency-patterns` 的升级阶梯（redesign → `System.Collections.Concurrent` → `Channel<T>` → `lock`）
  可直接作为 Core rule。
- **偏差**：约三分之一目录是 Akka.NET/Aspire/MJML 自家栈说明书（`akka-*`、`aspire-*`、`mjml-email-templates`、
  `r3-reactive-extensions`、`verify-email-snapshots`）。`csharp-concurrency-patterns` 的决策树末端有四个分支
  指向 Akka.NET，这部分不取——正文只保留 `async/await` → `Parallel.ForEachAsync` → `Channel<T>` 三级。
- **`package-management` 的硬规则「永远不要直接编辑 XML，一律用 `dotnet add package`」**：与 dotnet/skills
  `convert-to-cpm` 直接改 `Directory.Packages.props` 的流程冲突，见裁决 1。

### 3. github/awesome-copilot

- **结构**：`skills/<name>/SKILL.md`（418 个）与 `instructions/<name>.instructions.md`（193 个，带 `applyTo` glob）。
- **质量分层明显**：`instructions/csharp.instructions.md` 有价值的只有两三句（「C# 14 是当前版本」、
  「相信可空标注，别在类型系统已保证非空处加 null 检查」、「用 `is null` 而非 `== null`」），其余是
  编辑器格式偏好（`.editorconfig`、大括号换行），落在本仓库「不重复模型已知常识」的红线里。
  `skills/dotnet-best-practices` 更差：把 Semantic Kernel、ResourceManager 本地化、Moq+MSTest+FluentAssertions
  三选一都写成「best practice」，属于某一个团队的内部约定。
- **有效贡献**：`skills/aspnet-minimal-api-openapi` 的 `TypedResults` + `Results<T1,T2>` + `MapGroup` +
  document/schema transformer 组合；四个测试框架 skill 提供的框架矩阵（xUnit v3 / NUnit / MSTest / TUnit）；
  `instructions/dotnet-architecture-good-practices` 的分层与 DDD 检查点。
- **重叠**：与 dotnet/skills 在 CPM、升级、Blazor 上全面重叠且更浅。凡冲突一律以 dotnet/skills + learn 为准。
- 该仓库同时是本仓库 `typescript`、`go`、`python` 等 skill 的上游；`paths` 只列本 skill 实际用到的路径。

### 4. learn.microsoft.com（两个文档源）

- `dotnet/docs` 与 `dotnet/AspNetCore.Docs` 的仓库根 `LICENSE` 均为 **CC BY 4.0 全文**（实读，非 API 推断），
  因此按许可规则表可 `merged`，`notes` 写署名。
- 提供了社区上游没有的、且本 skill 必须写对的事实：
  - DI 指南的「反模式」节：容器持有 transient `IDisposable` 造成泄漏；async DI 工厂里取 `Task.Result` 死锁；
    「启用作用域校验以确保没有 singleton 捕获 scoped」。
  - ASP.NET Core DI：**常规中间件构造注入 scoped 服务会在运行时抛异常**，必须走 `InvokeAsync` 参数或
    factory-based middleware；keyed services 三个注册方法。
  - Blazor 渲染模式四行表 + 「交互式渲染模式默认开启预渲染」+ `RendererInfo`/`AssignedRenderMode`（.NET 9+）。
  - MTP：嵌入测试项目、支持 MSTest/NUnit/xUnit v3/TUnit、目标框架 .NET 8+/.NET Framework 4.6.2+，
    `Microsoft.Testing.Platform.MSBuild` 提供 `dotnet test` 支持与入口点生成。
  - `ConfigureAwait(ConfigureAwaitOptions)` 重载存在于 net8.0+。

### 5. wieslawsoltes/Performance-Skill

- **结构**：单 skill + `references/{core,memory,latency,startup,benchmarking,production,gpu,platforms}/` 树。
- **质量**：「不可协商规则」那一段是纯度量纪律（Release 构建、记录 commit/SDK/OS/硬件/命令、先建立确定性复现、
  区分冷启动与稳态、不从 RSS 推断托管保留、不凭单次平均值宣布修好）。这些正是 agent 最容易跳过的步骤。
- **偏差**：GPU/WebGPU/Metal/着色器占了很大篇幅，与本 skill 无关，不取。

### 6. kevintsengtw/dotnet-testing-agent-skills

- **结构**：一个导航 skill + 29 个子 skill，正文繁体中文，frontmatter 里有 `/skill <name>` 形式的加载指令
  （agent 绑定，剥离）。
- **有效贡献**：`TimeProvider` 替代 `DateTime.Now`、`System.IO.Abstractions` 替代 `File`/`Directory`、
  xUnit v3 与 MTP 的关系、`WebApplicationFactory` 下替换真实依赖的边界。
- **偏差**：库选型面铺得过宽（AutoFixture + Bogus + NSubstitute + AwesomeAssertions + 各种 integration）。
  按标准第 3 节收敛：默认 xUnit v3 + 手写 fake，逃生口写明「没有可实现的接口时才引入 mock 库」。

### 7. dennisdoomen/CSharpGuidelines

- 许可是 CC BY-SA 4.0，按规则只能取「结构与清单语义」。实际用途：用它的 AV 分类（类设计 / 成员设计 /
  杂项设计 / 可维护性 / 可测性 / 命名 / 性能 / 框架用法 / 文档 / 布局）对照本 skill 的 Core rules 与
  references 做覆盖面自检，发现两处缺口（异常设计、`IDisposable`/终结器契约），补进 `references/csharp-language.md`。
  一句话未复制。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 改包版本该用 CLI 还是直接编辑 XML | Aaron `package-management`：「Golden Rule：永远不要直接编辑 `.csproj`/`Directory.Packages.props`，一律 `dotnet add package`」。dotnet/skills `convert-to-cpm`：整个转换流程就是读写 `Directory.Packages.props` 并从 `PackageReference` 上摘掉 `Version` | **加/删单个包用 `dotnet add|remove package`（它在 CPM 下会同时写 `PackageVersion` 与无版本的 `PackageReference`）；批量对齐、启用 CPM、加条件版本或 `VersionOverride` 直接编辑 XML，然后用 restore + 构建证据验证。** 正文写成「按操作形态分流」而不是二选一 | 官方厂商 > 公认专家；且 `dotnet add package` 无法表达 `Condition`/`VersionOverride`/`GlobalPackageReference`，把它当唯一入口会直接堵死 CPM 的正常用法 |
| 2 | CPM 里同版本包该用共享属性还是字面量 | Aaron `package-management`：用 `<AkkaVersion>`/`<XunitVersion>` 这类共享属性组。dotnet/skills `convert-to-cpm`：把 MSBuild 版本属性**内联**成字面 `PackageVersion` 并删掉属性定义 | **同一产品族（同步发版的多个包）保留一个共享属性；转换 CPM 时不要把散落在 `Directory.Build.props` 的一次性版本属性搬进来，内联成字面量。** 判据是「这个属性是否表达了一个真实的版本族约束」 | 两者不是同一场景：上游 A 讲稳态组织，上游 B 讲迁移时的清理。合并后正文给出判据而非并列两种做法 |
| 3 | `ConfigureAwait(false)` 是不是通用建议 | awesome-copilot `csharp-async`：「在适当时候用 `ConfigureAwait(false)` 防止死锁」。Aaron `csharp-concurrency-patterns`：「库代码里用 `ConfigureAwait(false)`」 | **ASP.NET Core 没有 `SynchronizationContext`，在其中加 `ConfigureAwait(false)` 不解决任何问题；它只对可能运行在 UI（WinForms/WPF/MAUI）或旧 ASP.NET 同步上下文下的库代码有意义。真正会死锁的是 `.Result`/`.Wait()`/`GetAwaiter().GetResult()`。** | learn.microsoft.com `Task.ConfigureAwait` 的 Remarks 把它定位为「回到原上下文有性能代价、可能在 UI 线程死锁」；DI 指南的反模式节把死锁归因于工厂里的 `Task.Result`。Aaron 的说法更准（限定库代码），awesome-copilot 的「适当时候」无判据 |
| 4 | scoped 服务能不能构造注入进中间件 | Aaron DI skill 只讲 `Add*` 扩展方法组织，未涉及；awesome-copilot `dotnet-best-practices` 泛泛讲「按合适生命周期注册」 | **常规中间件是单例，构造注入 scoped 服务在运行时抛异常；scoped 依赖必须作为 `InvokeAsync` 的参数，或改用 factory-based middleware / `IMiddleware`。** | learn.microsoft.com/aspnet/core DI 文档「Service lifetimes」节原文：使用构造注入会抛运行时异常，因为它强迫 scoped 服务表现为 singleton |
| 5 | 作用域校验是否「默认开着」 | 社区上游普遍暗示「跑一次就会发现 captive dependency」 | **作用域校验只在 Development 环境默认开启**；要在其他环境或单元测试里挡住 captive dependency，必须显式设 `ValidateScopes`/`ValidateOnBuild`。正文按此写 | learn.microsoft.com DI 指南 → `overview#scope-validation`。这条决定了评测场景 2 的正确答案不是「跑一下就知道了」 |
| 6 | 测试框架/断言库选型 | awesome-copilot `dotnet-best-practices`：MSTest + FluentAssertions + Moq。kevintsengtw：xUnit + AwesomeAssertions + NSubstitute + AutoFixture + Bogus。dotnet/skills：`writing-mstest-tests` 与 6 个「迁移到 MSTest/xUnit v3/MTP」skill 并存 | **沿用仓库现有框架，不迁移；新项目默认 xUnit v3 跑在 Microsoft.Testing.Platform 上。断言默认用框架自带断言，只有在对象图比较确实笨重时才引入流式断言库。mock 库只在没有可实现接口时引入。** | 标准第 3 节「只给一个默认方案 + 一个逃生口，不罗列多个可选库」；MTP 支持 xUnit v3/NUnit/MSTest/TUnit 由 learn.microsoft.com MTP 概览核实。上游的框架偏好互斥且都无普适依据，改以「项目既有约定」为第一判据 |
| 7 | `.props` 里能不能按 `$(TargetFramework)` 加条件 | dotnet/skills 两处（`property-patterns` 警告段、`directory-build-organization` ⚠️ 段）说单目标项目下该属性为空，条件静默不成立；awesome-copilot 无相关内容 | **采纳 dotnet/skills：TFM 条件的 `PropertyGroup` 放 `Directory.Build.targets`（或项目文件）；`ItemGroup`/`Target` 条件不受影响。** 作为 Core rule 与评测场景 1 的必答点 | 官方厂商，且两个独立目录互相印证；MSBuild 求值顺序（`Directory.Build.props` → SDK `.props` → 项目 → SDK `.targets` → `Directory.Build.targets`）本身即可推出 |
| 8 | 是否为 Blazor 预渲染重复取数 | dotnet/skills `support-prerendering`：用 `[PersistentState]` 特性 + `??=`；旧社区做法是 `PersistentComponentState` 手写 `RegisterOnPersisting` | **默认 `[PersistentState]` + `??=`；只有动态 key 或自定义序列化才降到 `PersistentComponentState` 命令式 API。** | 官方 skill 与 learn.microsoft.com 渲染模式/预渲染文档一致；「更新 > 更旧」 |
| 9 | 性能结论的举证门槛 | dotnet/skills `analyzing-dotnet-performance` 是「扫代码找 ~50 个反模式」；wieslawsoltes 是「证据优先，不许无 before/after 就宣布改进」 | **两者组合但顺序固定：先建立可复现的 Release 度量与基线，再用反模式目录定位候选，最后用等价工作负载的 before/after 收口。** 反模式扫描不能替代度量 | wieslawsoltes 的度量纪律更严格且与本仓库 `debugging` skill 的「先复现」一致；dotnet/skills 自己也把 hot-path 上下文列为「recommended input」 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `dotnet-official` | dotnet/skills（31 个目录，见备注） | merged | MSBuild 求值顺序与反模式目录、CPM 转换流程与 NU1008、增量构建与 binlog 归因、Web API/minimal API 结构、Blazor 组件与预渲染/JS interop/渲染模式选择、MAUI 生命周期/绑定/Shell/CollectionView、测试反模式与 `dotnet test` 命令形态、.NET 9→10→11 升级步骤与破坏性变更、NRT 迁移、AOT/trim 警告、诊断工具选择与 dump/trace 采集、EF Core 查询优化、SIMD |
| `awesome-copilot` | github/awesome-copilot | merged | `TypedResults` + `Results<T1,T2>` + `MapGroup` + OpenAPI transformer 组合；测试框架矩阵（xUnit v3/NUnit/MSTest/TUnit）；分层与 DDD 检查点；当前语言版本口径 |
| `aaronontheweb` | Aaronontheweb/dotnet-skills | merged | NRT 属性目录与「先收窄控制流、再考虑 `!`」的排序；并发升级阶梯；DI 注册用 `Add*` 扩展方法组织并在测试中复用；CPM 共享版本属性；项目结构与 AOT/trim 约束 |
| `dotnet-docs` | learn.microsoft.com/dotnet | merged | DI 反模式（transient `IDisposable` 泄漏、async 工厂死锁）、作用域校验的默认范围、`IDisposable` 处置规则、MTP 模型与支持矩阵、C# 语言版本随 TFM 绑定、`ConfigureAwait` 语义、诊断工具口径 |
| `aspnetcore-docs` | learn.microsoft.com/aspnet/core | merged | 服务生命周期与中间件里 scoped 的正确取法、keyed services、Blazor 四种渲染模式与预渲染默认开启、`RendererInfo`/`AssignedRenderMode`、`Add{GROUP}` 注册约定 |
| `soltes-perf` | wieslawsoltes/Performance-Skill | merged | 性能与诊断的举证纪律：Release + 真实部署形态、记录环境与命令、先建立确定性复现、区分冷启动与稳态、不从 RSS 推断托管保留、等价 before/after 才算修好 |
| `kevintsengtw-testing` | kevintsengtw/dotnet-testing-agent-skills | merged | 可测性抽象（`TimeProvider`、`System.IO.Abstractions`）、`WebApplicationFactory` 集成测试的替换边界、测试命名与 3A 结构 |
| `csharpguidelines` | dennisdoomen/CSharpGuidelines | merged | 仅结构与清单语义：C# 编码/设计规则的分类覆盖面自检，补齐异常设计与 `IDisposable` 契约两处缺口（CC BY-SA 4.0，未复制任何句子） |
| `rider-skills` | JetBrains/rider-skills | reference | 覆盖面自检：确认「用调试器取运行时证据」的判据属于 `debugging` skill 而非本 skill；未取内容（IDE/MCP 工具绑定） |
| `dotnet-releases` | dotnet/core `release-notes/releases-index.json` | merged | 支持状态表：当前 LTS / 下一个 STS / 维护期通道。写任何版本相关规则前先读它，正文的默认目标（.NET 10）由它决定；每次同步必须重读，支持阶段会变 |

## 基线缺口

无 skill（`uv run tools/run_evals.py csharp-dotnet --baseline`，Claude Opus 5 · medium）时，各场景未达成的 `expected_behavior`：

基线整体很强（Opus 5 medium 会自建临时工程实跑验证），因此缺口是窄而具体的几条，
而不是「什么都不知道」。逐条判定见下表；序号对应 `evals.json` 里 `expected_behavior` 的顺序。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 MSBuild/CPM | #5 `OutputPath` 的可覆盖默认值 | 它把 `OutputPath` 判成「硬编码导致多项目输出互相覆盖」，换成了另一个硬编码的 `BaseOutputPath`。**没有识别出 props 无条件赋值被 csproj 静默覆盖**这个真正的失败模式，也没有给出 `Condition="'$(OutputPath)' == ''"` |
| 1 MSBuild/CPM | #8 后半：反斜杠字面量 | `<Import>` 加了 `Condition="Exists(...)"`（前半达成），但保留 `..\eng\signing.props` 的反斜杠，未换正斜杠或路径函数 |
| 1 MSBuild/CPM | #9 具名诊断命令 | 全程靠「复制文件到临时工程真跑一遍 restore/build」取证。这在夹具目录里可行，在真实仓库里成本极高；`dotnet msbuild -pp` 与 `-bl` 一次都没提 |
| 2 ASP.NET Core DI | #7 `TypedResults` / `Results<Ok<T>, NotFound>` / `ProblemDetails` | 五个 DI 与阻塞缺陷全部命中，但端点返回类型只字未提，生成的 OpenAPI 仍然没有响应 schema |
| 3 async | #8 `ConfigureAwait` 的适用边界 | 它承认 `ConfigureAwait(false)` 不是构造函数死锁的解，但随后**给所有方法无差别加上了 `ConfigureAwait(false)`**，并写「库代码统一 `ConfigureAwait(false)`」。没有说明 ASP.NET Core 没有同步上下文、加了等于没加 |
| 4 Go（负例） | 无 | 四条全达成：`skill_read=false`，正确指出 `results` 无缓冲导致超时后 worker 永久阻塞、`watch` 的 ticker goroutine 泄漏，给的是 pprof / goleak / 缓冲 channel / `defer ticker.Stop()` 这些 Go 手段，没有掺入 .NET 工具 |

已达成（不构成缺口，正文仍然覆盖，避免有 skill 时反而变差）：NU1008、`.props` 里 TFM 条件静默失效、
条件加引号、`DefineConstants` 追加、`PrivateAssets="all"`、SDK 默认值与 `Compile` 冗余、
捕获依赖与 `ValidateScopes` 的 Development 默认、中间件构造注入 scoped、`BuildServiceProvider`、
`new HttpClient()` + `.Result`、构造函数 sync-over-async、`async void`、`ValueTask` 双消费、
串行 await、`Task.Run` 包装 I/O、fire-and-forget。

## 评测结果

两组均为 `anthropic/claude-opus-5` + `medium`（`tools/run_evals.py` 默认，未传 `--model` / `--thinking`）。
`达成` 列的编号对应 `evals.json` 中 `expected_behavior` 的顺序。原始产物在
`/tmp/hs-evals/csharp-dotnet/anthropic-claude-opus-5-medium/{baseline,skill}/<n>/answer.md`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 MSBuild/CPM | claude-opus-5:medium | 无（基线） | false | 1,2,3,4,6,7；#8 仅前半 | 未达成 #5、#9，#8 后半。把 `OutputPath` 判成「多项目输出冲突」而非「props 被 csproj 静默覆盖」，靠复制到临时工程实跑取证而非用具名求值命令 |
| 1 MSBuild/CPM | claude-opus-5:medium | 有 | true | 1,2,3,4,**5**,6,7,**9**；#8 仅前半 | **#5 填补**：明确写出「实测被 csproj 的 `bin\api\` 静默覆盖（last-write-wins）。共享默认值必须带 `Condition="'$(OutputPath)' == ''"`」。**#9 填补**：用 `-getProperty:AnalysisLevel` 直接查最终求值结果来证明条件没生效（而非只看症状）。**#8 后半仍未达成**：`Condition="Exists('..\eng\signing.props')"` 保留了反斜杠 |
| 2 ASP.NET Core DI | claude-opus-5:medium | 无（基线） | false | 1,2,3,4,5,6 | 未达成 #7：端点返回类型完全没提，`Results.Ok(...)` 原样保留 |
| 2 ASP.NET Core DI | claude-opus-5:medium | 有 | true | 1,2,3,4,5,6,**7** | **#7 填补**：`Results<Ok<OrderResponse>, NotFound>` + `TypedResults` + DTO，并指出无类型结果会让生成的 OpenAPI 没有响应 schema。另外多出两条：全链路 `CancellationToken`、删掉无人消费的 `TenantResolver` 注册 |
| 3 async | claude-opus-5:medium | 无（基线） | false | 1,2,3,4,5,6,7 | 未达成 #8：一边说 `ConfigureAwait(false)` 不是构造函数死锁的解，一边给所有方法无差别加上并写「库代码统一 `ConfigureAwait(false)`」，没有 ASP.NET Core 无同步上下文这一层 |
| 3 async | claude-opus-5:medium | 有 | true | 1,2,3,4,5,6,7,**8** | **#8 填补**：区分「有同步上下文时死锁 / ASP.NET Core 下饿死线程池」两种失败模式，并在场景 2 的同一批判定里写明「ASP.NET Core 没有同步上下文，所以不是死锁而是线程池饥饿（`ConfigureAwait(false)` 无用）」；本文件是库代码，加 `ConfigureAwait(false)` 被定位为一致性而非疗法。另外用 10ms CTS 证明 token 真的下传 |
| 4 Go（负例） | claude-opus-5:medium | 无（基线） | false | 1,2,3,4 | 全达成 |
| 4 Go（负例） | claude-opus-5:medium | 有（本 skill 在会话中可用） | **false** | 1,2,3,4 | 负例通过：首句即声明「这个目录挂的是 `csharp-dotnet` skill，但 `worker.go` 是 Go 代码，所以那份 skill 完全没用上」。修法全为 Go 手段（`context.WithTimeout`、缓冲 channel、`WaitGroup` + `close`、`defer ticker.Stop()`、`go vet` / `-race` / goleak），未出现任何 .NET 工具 |

结论：**通过**。四条基线未达成的行为在有 skill 时达成——场景 1 的 `OutputPath` 可覆盖默认值（#5）与具名求值诊断命令（#9）、场景 2 的 `TypedResults` / `Results<T1,T2>` 联合（#7）、场景 3 的 `ConfigureAwait` 适用边界（#8）；负例 `skill_read == false` 且答复完全留在 Go 生态内。
唯一仍未达成的是场景 1 的 #8 后半（`<Import>` 路径里的反斜杠改正斜杠）：两组都只加了 `Exists()` 守卫而保留反斜杠。该规则写在 `references/build-msbuild-nuget.md` 的「Property patterns」一节，并明确说明反斜杠只有在字符串离开 MSBuild 求值器时才是真 bug、在 `Import` 里只是风格问题——模型判成风格问题因而不改，与 reference 的定性一致，故不回 Phase C。

## 备注

### dotnet/skills 为什么不整仓引用

该仓库有 106 个 `SKILL.md`，其中 `.agents/skills/*`（create-skill、improve-skill-quality…）、
`.github/skills/agentic-workflows`、`eng/skill-validator/tests/fixtures/*`、
`plugins/dotnet-template-engine/*`（6 个 `dotnet new` 模板作者向 skill）、
`plugins/dotnet-ai/*`、`plugins/dotnet-experimental/*` 与本 skill 边界无关。
`SOURCES.yaml` 只列实际取用的 31 个目录：

```
plugins/dotnet-msbuild/skills/{directory-build-organization,property-patterns,msbuild-antipatterns,
                               incremental-build,binlog-failure-analysis}
plugins/dotnet-nuget/skills/convert-to-cpm
plugins/dotnet-aspnetcore/skills/{dotnet-webapi,configuring-opentelemetry-dotnet}
plugins/dotnet-blazor/skills/{create-blazor-project,author-component,support-prerendering,use-js-interop}
plugins/dotnet-maui/skills/{maui-app-lifecycle,maui-data-binding,maui-shell-navigation,
                            maui-collectionview,maui-dependency-injection}
plugins/dotnet-test/skills/{run-tests,test-anti-patterns,detect-static-dependencies,platform-detection}
plugins/dotnet-upgrade/skills/{migrate-dotnet9-to-dotnet10,migrate-dotnet10-to-dotnet11,
                               migrate-nullable-references,dotnet-aot-compat}
plugins/dotnet-diag/skills/{analyzing-dotnet-performance,dotnet-trace-collect,dump-collect,microbenchmarking}
plugins/dotnet-data/skills/optimizing-ef-core-queries
plugins/dotnet-advanced/skills/vectorization
```

理由：`check_upstream.py` 用 `paths` 过滤 compare 区间的变更文件。整仓引用会让
template-engine、AI plugin、skill-authoring 目录的任何提交都把本 skill 报成 `behind`，
同步噪声淹没真实变更。

### 许可注意

- `dotnet/docs`、`dotnet/AspNetCore.Docs` 两个文档源的仓库根 `LICENSE` **实读**为 CC BY 4.0 全文，
  因此挂 `merged` 而非 `reference`——本 skill 的事实确实来自官方文档，挂 reference 会与写法自相矛盾。
  `notes` 写署名要求。
- `dennisdoomen/CSharpGuidelines`：GitHub API 报 `NOASSERTION`，实读 `LICENSE.md` 为
  **CC BY-SA 4.0**。按规则只取结构与清单语义，全部改写，`notes` 记明。
- `JetBrains/rider-skills`：Apache-2.0，本可 merged，但其内容全部经 Rider MCP 工具绑定
  （frontmatter `allowed-tools: execute_tool`），本仓库禁用 agent 绑定字段，因此按「仅阅读对齐」
  记为 `reference`。
- 无 `NONE`、无 GPL 家族、无 Proprietary 上游。

### 未来同步时要盯的

- `plugins/dotnet-upgrade/skills/migrate-dotnet10-to-dotnet11`：上游自述「.NET 11 仍在预览，
  覆盖到 Preview 3」。.NET 11 GA（2026-11 前后）后这份内容会大改，`references/upgrade.md` 的
  net11 一节须重新取证。
- `plugins/dotnet11/skills/system-text-json-net11` 本次未取（单点 API、且限 net11.0+）。
  .NET 11 GA 后重估是否并入 `references/csharp-language.md`。
- .NET 9 与 .NET 8 均在 2026-11-10 EOL；届时正文里「还没升上来的仓库」的举例版本需要下移。

### 放弃的方向

- 不写 EF Core 建模教程：只在 `references/aspnetcore.md` 保留「查询与 `DbContext` 生命周期」一节
  （N+1、跟踪、split query、`DbContextFactory`），因为它是 ASP.NET Core 请求路径上的真实故障源；
  schema/索引/迁移策略不在本 skill 边界内。
- 不写 Aspire：dotnet/skills 与 Aaron 都有大量 Aspire 内容，但 Aspire 是编排/托管面，
  与「Azure 资源编排不覆盖」的边界同源，且尚无对应 skill 可转交，正文只在 `## Scope` 直述不覆盖。
- 不写 WinForms/WPF：仅在升级破坏性变更清单里作为「桌面项目也要检查」的一行提示出现。

## 2026-09-30 上游同步

依据：`/tmp/upstream-report-0930.txt`（2026-09-30 `check_upstream.py`）中本 skill 有 3 条 `behind`，其中
awesome-copilot 为 `diff too large`。全部按完整区间归因：blobless 克隆到 `/tmp/hs-up/<owner>__<repo>`，对
`<旧 pin>..<HEAD>` 跑 `git log --oneline -- <paths>`、`git diff --stat` 与 `git diff`，并用
`git cat-file -e <HEAD>:<path>` 核对每个 tracked path 在 HEAD 上是否仍存在。`--pin` 后逐条核对：写入的 commit
与审阅 HEAD 一致（ff66f96、15ed97c、26b2404）；aaronontheweb 为 repo moved / tracked paths unchanged，顺带前移到
e426ed9。三条 docs 为 manual check；其中 dotnet-releases 按其 notes「每次同步重读」用 `gh api` 读了
`releases-index.json`：11.0 go-live STS（11.0.0-rc.1）、10.0 active LTS、9.0 与 8.0 maintenance，与正文「.NET 10 为
当前 LTS、.NET 11 为下一个 STS」一致，无需改动。

### 归因表

| 上游 | 区间 | 命中提交/文件 | 判定 | 理由 |
|---|---|---|---|---|
| dotnet-official | 9beca0b → ff66f96（203 提交） | 8599a06（#1210）：删除 `plugins/dotnet-aspnetcore/skills/configuring-opentelemetry-dotnet`（连同 eval） | 上游移除，删 path | 本 skill 从未取其内容（正文与 references 无任何 OpenTelemetry 段落，上一轮合入清单也未列它），删后无继任内容；从 `paths` 去掉，`notes` 记删除提交 |
| dotnet-official | 同上 | a824bbb（#1206，面向 GPT-5 的提示优化）：`test-anti-patterns` 改为先清点再读、ledger 增加「并发安全」「前置条件/断言顺序」两列，并点名「无同步的静态集合既顺序耦合又并行不安全」「断言非空之前先解引用」；`platform-detection` 只改 description 的路由措辞 | 已覆盖 / 噪声 | `references/testing.md` 已有「无顺序依赖、无共享可变静态状态」的确定性规则；断言顺序属通用常识；其余是该仓库 agent 工作流与路由措辞 |
| awesome-copilot | 7568a48 → 15ed97c（64 提交） | 17 个 tracked 路径 0 提交 | 噪声 | 区间改动全在其他 skill/instructions；too-large 只是 compare 上限 |
| rider-skills | 638e23b → 26b2404（13 提交） | `debugging-code`：断点工具批量化（`xdebug_set_breakpoints`/`xdebug_remove_breakpoints`）、新增静音/附加进程/进程输出/忽略异常工具参考；三个 skill 加 `metadata.json`；`refactoring-code` 工具参考措辞刷新 | 噪声 | relation 为 reference，只作覆盖自检；变更全是 Rider MCP 工具契约，本仓库禁止的 agent 绑定面 |

### 未合入原因与评测

三条 behind 均为噪声、已覆盖或上游删除，正文与 references 未改，未新增评测场景、未跑评测，也不需要安装冒烟。
本次提交只含 re-pin、版本号、dotnet-official 的 `paths`/`notes` 与本节。

## 2026-10-15 上游同步

依据：主代理 2026-10-15 `check_upstream.py --json` 报告与归因结果 `/tmp/hs-attr/attribution.md`。本 skill 4 条上游在 tracked
paths 下确有提交。归因方法：dotnet-official 为 too-large 条目，用主代理的 blobless 裸仓库缓存 `/tmp/hs-attr/dotnet__skills`
按 30 个 tracked 目录跑 `git diff ff66f96..9de888b`（9 个文件、+252/−59），并读 HEAD 上的 `optimizing-ef-core-queries/SKILL.md`
全文；aaronontheweb、kevintsengtw-testing、rider-skills 用 `gh api repos/<o>/<r>/compare/<pinned>...<head>` 取 patch 后按 paths
过滤。awesome-copilot 为 too-large 但主代理归因为空（噪声），随 `--pin` 前移。`dotnet-releases` 按 notes 要求重读
releases-index：11.0 go-live STS（11.0.0-rc.2）、10.0 active LTS、9.0/8.0 maintenance，与正文一致。`--pin` 后
`pin_check.py` 报 `PIN CHECK CLEAN`。

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| dotnet-official | ff66f96 → 9de888b（14 提交命中） | 7ce04b1（#1285）重写 `optimizing-ef-core-queries`：源码审查流程、证据门、物化/`IEnumerable` 边界、`EF.Parameter`/`EF.Constant` 与计划缓存、动态表达式里的 `Expression.Constant`、按结果图决定跟踪（标量投影无跟踪、DTO 里的实体仍被跟踪）、过滤 Include 的 fixup、split query 的代价与一致性、降序复合 keyset 谓词、隐藏在仓储里的 `SaveChanges`、长导入的变更检测超线性、`ExecuteUpdate` 不更新已跟踪实体且不查并发令牌/不与后续 `SaveChanges` 原子、同一 `DbContext` 不得重叠操作；并把「不可翻译谓词会退化为客户端求值拉全表」更正为「当前 EF Core 直接抛错」。msbuild 组（c75e165、2a896b2、e961b65、f3cad1e、d2cd7c6、2b5f5a4、83662c4、ac46442、970e0dc）：`directory-build-organization` 把求值顺序从「D.B.props → SDK .props → 项目 → SDK .targets → D.B.targets」改为「`Microsoft.Common.props` 早导入 D.B.props … `Microsoft.Common.targets` 晚导入 D.B.targets」，`incremental-build` 删去不存在的 Target `Incremental` 属性、加「生成器内容不变时保留时间戳（`WriteOnlyWhenDifferent`）」与诊断输出契约，`binlog-failure-analysis` 给 `-flp` 参数加引号，其余为 description 路由措辞；e191d40、a51399b：test 组改为读 reference-only helper；c6ec97b：description 去 XML 标签 | 求值顺序与 EF 客户端求值：**事实更正** ×2；EF 的新增内容：**评测后部分合入**；其余：噪声（路由/agent 行为契约，或本 skill 未写的细节） |
| aaronontheweb | e426ed9 → ac0deb2（2 提交命中） | a43e250：各 SKILL.md frontmatter `invocable` → `user-invocable`；acee683：coding-standards 把「用 `Result<T, TError>`」改为「用领域专用结果类型，而非泛型 `Result<T>`」 | 噪声：frontmatter 本就剥离；本 skill 未写结果类型 |
| kevintsengtw-testing | 4e34a97 → 3961475（3 提交命中） | description 去掉「Make sure to use…」句、加「範例檔案」节；WebAPI 集成测试模板把 Respawner/数据库初始化移到 Collection fixture 只建一次、`FakeTimeProvider` 在 Collection 内共用不再回设；TimeProvider 篇补「`SetUtcNow` 只能向前，回设抛 `ArgumentOutOfRangeException`」与包名/命名空间不同 | 无影响：本 skill 只在 `testing.md` 表格里给出 `TimeProvider`/`FakeTimeProvider` 这一替换，不涉及共用实例或回设；属上游细节，未合入 |
| rider-skills（reference） | 26b2404 → eddf751（5 提交命中） | `debugging-code` 新增 Rider 调试器 MCP 工具（异步任务栈、断点命中时抓线程 dump、plain resume） | 噪声：绑定 Rider MCP，按 notes 仅作覆盖自查，归 `debugging` skill |

### 事实更正（读源码 + 本地实跑）

1. **MSBuild 求值顺序。** 读 dotnet/msbuild `src/Tasks/Microsoft.Common.props`（导入 `$(DirectoryBuildPropsPath)`）、
   `Microsoft.Common.targets`（`CommonTargetsPath` 与 NuGet 包 `.targets` 之后导入 `$(DirectoryBuildTargetsPath)`），dotnet/sdk
   `Sdk.props`（BeforeCommon.props → Microsoft.Common.props → Microsoft.NET.Sdk.props）与 `Sdk.targets`（BeforeCommon.targets →
   `$(LanguageTargets)` → Microsoft.NET.Sdk.targets）；再在本机 SDK 9.0.121 建空 console 项目放两个标记属性跑
   `dotnet msbuild -pp`，顺序为 Common.props（57 行）→ D.B.props 标记（98）→ Microsoft.NET.Sdk.props（342）→ 项目体（1217）→
   BeforeCommon.targets（1252）→ Microsoft.Common.targets（3505）→ D.B.targets 标记（9667）→ Microsoft.NET.Sdk.targets（9822）。
   据此改 `references/build-msbuild-nuget.md` 的顺序图并说明「D.B.targets 早于其余 .NET SDK targets」，`SKILL.md` 规则 3 同步改写。
2. **EF Core 客户端求值。** 原文「不能翻译的构造要么抛错要么静默拉全表」不准确：EF Core 3.0 起只允许最终投影在客户端求值，
   其余不可翻译谓词抛 `InvalidOperationException`；静默拉全表来自代码自身的 `AsEnumerable()`/`ToList()` 或仓储返回列表/`IEnumerable<T>`。
   本地 EF Core 9 + SQLite 实测：`Where(p => Helper(p.Name))` 抛 `InvalidOperationException`，同一函数放在 `Select` 里正常返回。
   同一节顺带收紧两处：`AsNoTracking()` 只对物化实体有意义（实测标量投影 0 条跟踪、`new { p.Id, Entity = p }` 5 条），
   `AsSplitQuery` 针对兄弟集合 Include 的行相乘，并注明多语句非一致快照（EF 官方 single-vs-split 文档同述）。

### 新增内容（评测先行）

新增场景 5（夹具 `evals/files/StockImportService.cs`）：夜间按供应商导入库存，逐行 `ChangeTracker.Entries<Product>()` 计数、
先加载并跟踪商品再 `ExecuteUpdateAsync` 释放过期预留、`Expression.Constant(supplierCode)` 拼过滤器。三条期望先在本地
EF Core 9 + SQLite 实测成立（批量保存后 1000 条全为 `Unchanged` 仍被跟踪、`Entries<T>()` 触发 `DetectedAllChanges`、
`ExecuteUpdate` 后已跟踪实体仍是旧值且 `SaveChanges` 写回 15 而非 12、`ToQueryString()` 常量为字面量而捕获变量为参数）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 5 | gpt-6.1-sol medium | 无 | false | EB1 ◐ EB2 ◐ EB3 ✔ | 原因三条都讲对；但 EB1 的修复是关掉 `AutoDetectChangesEnabled`，跟踪集仍无界增长；EB2 的修复是先释放后加载，未提批量语句与后续保存不原子。输出 `/tmp/hs-evals-sync/SyncG6/csharp-b5` |
| 5 | gpt-6.1-sol medium | 有 | true | EB1 ✔ EB2 ◐ EB3 ✔ | 去掉逐行跟踪查询，查找字典 `AsNoTracking()`，每 500 行只附加本批实体、保存后 `ChangeTracker.Clear()`（注明上下文归本批所有）；EB2 同基线。输出 `csharp-s5` |

EB1 缺口在有 skill 时补上，按 D2 通过，合入 `references/aspnetcore.md`「EF Core on the request path」三条：长生命周期上下文的跟踪集增长与
`ChangeTracker.Clear()`/工厂新上下文、`ExecuteUpdate`/`ExecuteDelete` 不触碰已跟踪实体及其原子性与并发令牌、动态表达式用捕获变量而非
`Expression.Constant`。EB2 的原子性提示两侧都未达成，正文已写，不再加码。上游其余新增（`EF.Parameter`/`EF.Constant` 取舍、过滤 Include
fixup、降序复合 keyset 谓词、隐藏 `SaveChanges`、证据门）未写评测：属 EF 专项调优，超出本 skill「请求路径上的 EF Core 缺陷」范围，
本轮不合入，记录待后续 EF 专题时评估。

结论：两处事实更正（MSBuild 求值顺序、EF 客户端求值，另收紧跟踪与 split query 两句）；EF 长导入/批量更新/动态表达式三条基线 ◐ → 有 skill ✔
（EB1）后合入；其余上游为噪声或未合入细节。

`ExecuteUpdate` 三点另以官方文档核对：dotnet/EntityFramework.Docs `core/saving/execute-insert-update-delete.md` 的「Change tracking」
（已跟踪实例不更新、`SaveChanges` 覆盖批量修改）、「Transactions」（每次调用各自提交、需显式事务）、「Concurrency control and rows affected」
（不自动做并发控制，需自己在 `Where` 中带令牌并检查受影响行数）；split query 一致性以 `core/querying/single-split-queries.md` 核对。

## 2026-10-15 上游新增内容评估

依据：主代理的上游新增文件评估（NewS4 C：Aaronontheweb `skills/sdk-container-publishing` MERGE；D：dotnet/skills `plugins/dotnet-test/skills/code-testing` MAYBE）。E（dotnet `process-api-net11`）按同类 `system-text-json-net11` 的既有裁决等 .NET 11 GA，不在本次范围。原文：Aaronontheweb/dotnet-skills @ `ac0deb2`（`gh api` 读取，MIT）、dotnet/skills @ `9de888b`（MIT）。

### 候选与裁决

| 候选 | 结论 | 理由 |
|---|---|---|
| sdk-container-publishing：`/t:PublishContainer` 不需要 Dockerfile 与 daemon、`ContainerArchiveOutputPath` 出 tarball、.NET 8 起不设 tag 即 `latest`、`ContainerImageTag(s)` 同设报 CONTAINER2008、项目正文里 `$(VersionPrefix)` 尚为空、`ContainerRuntimeIdentifiers` 出多架构、Windows 需显式 `ContainerBaseImage` | 不合入 | 场景 6、8 基线均 4/4：场景 6 自行解释 `;latest` 与 CONTAINER2008、改用 `-p:VersionPrefix="${GITHUB_REF_NAME#v}"` 并用 `ComputeContainerConfig` 验证；场景 8 在无 daemon 的 Kubernetes runner 上用 SDK 出单个多架构 OCI archive、trivy 扫描后用 skopeo `--all` 推送原 archive。场景保留作哨兵 |
| containers `references/dockerfile.md` 指向 csharp-dotnet 的 SDK 出镜像一行 | 不做 | 依附于上一条；本 skill 未新增该内容，指向会落空 |
| code-testing：非 SDK 老项目显式 `<Compile Include>`、保留 packages.config 与锁定版本、用仓库的 msbuild/vstest 命令；MSTest 3.5 用 `Assert.ThrowsException<T>`（`ThrowsExactly`/`Throws` 自 3.8 起） | 不合入 | 场景 7 基线 4/4：加了 `<Compile Include="DiscountPolicyTests.cs" />`、用 `Assert.ThrowsException`、未改 packages.config 与项目格式、说明 Linux 下无法跑 build.cmd |
| process-api-net11 | 不做 | .NET 11 GA 前不评估（见 2026-10-15 上游同步一节对 `system-text-json-net11` 的裁决） |

### 核实

- 默认 tag `latest`（.NET 8 起）、`ContainerRepository` 默认 `AssemblyName`、Windows 基础镜像需显式指定、多 RID 版本门（8.0.405 / 9.0.102 / 9.0.2xx）、`ContainerPublishInParallel`（8.0.408 / 9.0.300 / 10.0）、`RUN` 不可模拟：learn.microsoft.com `core/containers/publish-configuration`（ms.date 2026-08-04）。
- CONTAINER2008 文案：`gh api repos/dotnet/sdk/contents/src/Containers/Microsoft.NET.Build.Containers/Resources/Strings.resx`；`VersionPrefix` 默认值在 `Microsoft.NET.DefaultAssemblyInfo.targets`（SDK targets，晚于项目正文）。
- 本机 .NET SDK 9.0.121 实测：项目正文写 `$(VersionPrefix);latest` 时 `dotnet msbuild -getProperty:ContainerImageTags` 得 `;latest`（`VersionPrefix` 同时为 `1.0.0`），`-p:VersionPrefix=2.4.0` 得 `2.4.0;latest`；`dotnet publish /t:PublishContainer -p:ContainerArchiveOutputPath=… -p:ContainerImageTag=2.4.0` 报 CONTAINER2008；去掉后输出 "Building image 'orders-api' with tags 'latest'"。
- MSTest：dotnet/docs `mstest0039.md` —— 新 `Assert.Throws*` 与 MSTEST0039 自 3.8.0 引入，3.10 起警告，MSTest 4 移除旧 API。

### 评测结果

模型 `openai/gpt-6.1-sol` medium（run_evals 默认，VM 内 omp），产物在 `/tmp/hs-evals/csharp-dotnet/omp-openai-gpt-6.1-sol-medium/`；逐条读 `answer.md` 与 `workspace/` 人工判定。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 6 | gpt-6.1-sol medium | 无 | False | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ | 61 s。根因两条都对（观测到 `;latest`）；`-p:VersionPrefix="${GITHUB_REF_NAME#v}"`；跑 `ComputeContainerConfig` 验证两个 tag |
| 7 | gpt-6.1-sol medium | 无 | False | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ | 84 s。显式 Compile 项、`Assert.ThrowsException`、未动 packages.config；说明缺 Windows/.NET Framework 工具链无法跑 build.cmd |
| 8 | gpt-6.1-sol medium | 无 | False | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ | 83 s。SDK + `ContainerRuntimeIdentifiers` 出单个 OCI archive，逐架构 trivy 扫描后 skopeo 推送扫描过的 archive；从命令行覆盖 `ContainerImageTags` |

结论：本次候选均为基线已具备的行为，不合入正文；场景 6–8 留作哨兵。

## 2026-10-15 文档上游复核

按 manual check 要求逐条对照，接在今天的上游同步与新增内容评估之后。Learn 文档读源仓库 `dotnet/docs` 与
`dotnet/AspNetCore.Docs`（`gh api`）；发布索引读 `dotnet/core` 的 `releases-index.json`。

| 上游 id | 核对的事实 | 当前官方页面 | 结论 |
|---|---|---|---|
| dotnet-docs | DI 反模式：容器捕获的 transient disposable、async DI factory 死锁、启用 scope validation | `docs/core/extensions/dependency-injection/guidelines.md`（目录已从 `extensions/dependency-injection-guidelines.md` 移到 `extensions/dependency-injection/` 下） | 一致 |
| dotnet-docs | C# 版本绑定 TFM：C# 14 仅 .NET 10+，C# 15 仅 .NET 11+ | `docs/csharp/language-reference/language-versioning.md` | 一致 |
| dotnet-docs | MTP：嵌入测试项目、支持 .NET 8+ 与 .NET Framework 4.6.2+、`Microsoft.Testing.Platform.MSBuild` 为 MSTest/NUnit/xUnit runner 默认并自动注册扩展、关闭 `GenerateTestingPlatformEntryPoint` 须手工注册 | `docs/core/testing/microsoft-testing-platform-intro.md` | 一致 |
| dotnet-docs | `dotnet test` 如何运行 MTP 项目 | `docs/core/testing/unit-testing-with-dotnet-test.md`、`microsoft-testing-platform-migration-from-v1-to-v2.md` | **更正**，见下 |
| aspnetcore-docs | 常规中间件构造函数注入 scoped 服务会抛运行时异常，改用 `InvokeAsync` 参数或 factory-based 中间件；`Add{GROUP NAME}` 约定；keyed services | `aspnetcore/fundamentals/dependency-injection.md`、`fundamentals/middleware/write.md` | 一致 |
| aspnetcore-docs | 交互式组件默认预渲染；`RendererInfo`、`AssignedRenderMode` | `aspnetcore/blazor/components/render-modes.md` | 一致 |
| dotnet-releases | 11.0 go-live STS（11.0.0-rc.2，2026-10-13）、10.0 active LTS（EOL 2028-11-14）、9.0 与 8.0 maintenance（均 2026-11-10 EOL） | `release-notes/releases-index.json` | 一致（今日上游同步已读过，`synced_at` 已是当天；`references/upgrade.md` 的支持状态表与之相符） |

更正：**.NET 10 SDK 上 `dotnet test` 运行 MTP v2 项目须在 `global.json` 打开 MTP 模式。** 原 `references/testing.md` 写「`dotnet test`
works against MTP projects through the same MSBuild integration」，并给 `dotnet test -- --filter-query …` 作为通用 MTP 写法。当前
`unit-testing-with-dotnet-test.md`：`dotnet test` 有 VSTest 模式（默认）与 .NET 10 SDK 引入的 MTP 模式（`global.json` 写
`"test": { "runner": "Microsoft.Testing.Platform" }`，.NET 11 Preview 6 起也可用 `DOTNET_TEST_RUNNER`）；在 VSTest 模式下跑 MTP 项目
需 `TestingPlatformDotnetTestSupport=true`，且「will be removed in MTP version 2 if run with .NET 10 SDK」。
`microsoft-testing-platform-migration-from-v1-to-v2.md`：「Running MTP test projects with .NET 10 SDK now requires opting-in to the
MTP-based `dotnet test`」，否则报「Testing with VSTest target is no longer supported by MTP on .NET 10 SDK and later」。本 skill
默认目标是 .NET 10、默认新测试项目是 xUnit v3 on MTP，原写法会直接撞上这条错误。改为写明两种模式与 `global.json` 开关、过滤参数
按框架区分（xUnit v3 `--filter-query`/`--filter-trait`，MSTest `--filter`，互不接受）。本机只有 .NET 9 SDK，无法实跑 .NET 10
行为，证据以上述两页为准。

SOURCES：dotnet-docs、aspnetcore-docs 的 `synced_at` 改为 2026-10-15，dotnet-docs 的 `contributes` 补上 `dotnet test` 两种模式。
