# observability 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`"observability" OR "opentelemetry" agent skill SKILL.md github claude skills`
  - <https://www.skills.sh>（经 web_search 聚合结果转引）
  - VoltAgent/awesome-claude-code-subagents、addyosmani/agent-skills
  - 领域官方组织仓库：`open-telemetry/`（`semantic-conventions`、`opentelemetry-collector-contrib`、
    `opentelemetry.io`、`opentelemetry-specification`）、`grafana/`、`getsentry/`、`prometheus/`、
    `github/awesome-copilot`、`microsoft/`
  - 观测厂商的 agent-skill 仓库：`ollygarden/`（OllyGarden）、`dash0hq/`（Dash0）、`o11y-dev/`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`；
  **每个候选的许可都实读了仓库 LICENSE 文件**（见「备注」的许可核实记录），不只信 API 的 `spdx_id`。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ollygarden/opentelemetry-agent-skills `skills/otel-collector`、`otel-semantic-conventions`、`otel-sdk-versions`、`otel-ottl`、`otel-upgrade`、`otel-telemetry-emissions`、`otel-span-events-to-logs-migration` | <https://github.com/ollygarden/opentelemetry-agent-skills> | 97 | 2026-09-10 | Apache-2.0 | OTel Collector 组件级配置、语义约定查询、SDK 版本索引、OTTL | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 18 个 otel-* skill 的多技能仓库，`components/<type>/{configuration,quirks,verification}.md` 的分层是全场最细的一手事实源：`memory_limiter` 量的是 Go heap 而非 RSS、v0.156.0 起 GC 退避、v0.142.0 起的 extension 形态不在 stock 发行版里、组件 v0.146–v0.154 批量改名为 snake_case。本机 0.160.0 实测逐条对上（见「实测记录」）。作主干。 |
| 2 | dash0hq/agent-skills `skills/otel-instrumentation`、`otel-collector`、`otel-semantic-conventions`、`otel-ottl` | <https://github.com/dash0hq/agent-skills> | 89 | 2026-09-01 | Apache-2.0 | 埋点质量（span 命名/kind/status/属性/基数）、Collector 流水线与采样、语义约定迁移 | 2 | 3 | 3 | 2 | 2 | 12 | INCLUDE | 埋点侧最强：按 span kind 分别定义 status 映射（SERVER 的 4xx 不是 error，CLIENT 的 4xx 是）、span 卫生规则对齐 Instrumentation Score（无 CLIENT 根 span、无孤儿 span、INTERNAL ≤10、<5ms span ≤20）、"SDK 用 AlwaysOn，采样全部下沉到 Collector"、语义约定重命名表。正确性扣一分：两条 Collector 断言在 0.160.0 被实测推翻（裁决 1、2）。 |
| 3 | grafana/skills `skills/grafana-cloud/prometheus-cardinality-troubleshooter`、`prometheus-label-strategy`、`loki-label-analyzer`、`skills/grafana-core/alerting-irm` | <https://github.com/grafana/skills> | 250 | 2026-09-09 | Apache-2.0 | 基数诊断与预防、标签策略、告警规则 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方厂商。基数这一块的权威来源，且给出了本 skill 最重要的一条不变量的完整机理：**不能在 scrape 时 labeldrop 任何构成序列唯一性的标签**——计数器重置互相混合、`rate()` 返回荒谬值、DPM 反而上升、且没有任何配置错误留痕。`status/tsdb` 四个端点字段、histogram 的 (buckets+3) 放大、info-metric 与 `info()` 函数版本门都直接可用。 |
| 4 | addyosmani/agent-skills `skills/observability-and-instrumentation` | <https://github.com/addyosmani/agent-skills> | 93420 | 2026-09-08 | MIT | 结构化日志、RED/USE、基数、告警与 runbook、埋点自验 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 公认专家。三信号分工（metrics = that、traces = where、logs = why）、"先写下 on-call 会问的 2–4 个问题再埋点"、症状 vs 原因告警对照、两级严重度、runbook 三行最小形态、"埋点本身也是代码，要触发一次看真实输出"。同时明确把"正在发生的故障"转交给 debugging 类 skill——与本仓库的分界一致。 |
| 5 | o11y-dev/opentelemetry-skill | <https://github.com/o11y-dev/opentelemetry-skill> | 45 | 2026-09-10 | Apache-2.0（API 报 NOASSERTION，实读 LICENSE 为 Apache-2.0，frontmatter `metadata.license` 亦然） | Collector 配置、部署形态、采样、OTTL、安全、AI agent 可观测性 | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE | 19 个 reference 的单 skill，覆盖面最宽：OTLP gRPC 4317 / HTTP 4318 的选择依据、load-balancing 路由键必须确定（tail sampling 用 traceID）、">100 unique values 不得作为 metric 维度"的量化门、"把 Collector review 当系统 review"的跨字段一致性清单。权威性只给 1（社区组织，无厂商背书）；`triggers` / `file_patterns` / `tessl_version` 等 agent 专属 frontmatter 必须剥离。AI-agent 可观测性与 Lambda/ECS 安装流程超出本 skill 范围，未取。 |
| 6 | open-telemetry/semantic-conventions | <https://github.com/open-telemetry/semantic-conventions> | 646 | 2026-09-09 | Apache-2.0 | 语义约定的稳定性、版本迁移机制 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方规范仓。本 skill 全部版本分界事实的取证源：最新 tag v1.44.0（2026-08-04）；`OTEL_SEMCONV_STABILITY_OPT_IN` 的 `<category>` / `<category>/dup` 语义与 `/dup` 优先；`gen_ai.*` 在 v1.42.0 移出到 semantic-conventions-genai；`deployment.environment` → `deployment.environment.name` 自 v1.27.0 弃用；声明式版本选择 `.instrumentation/development.general.<domain>.semconv` 仍是 Development。 |
| 7 | open-telemetry/opentelemetry-collector-contrib | <https://github.com/open-telemetry/opentelemetry-collector-contrib> | 4917 | 2026-09-10 | Apache-2.0 | Collector 组件真实配置面与稳定度 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方仓 + 官方镜像。`otel/opentelemetry-collector-contrib:latest`（0.160.0）是本 skill 12 条实测的被测体；组件名、校验报错文本、默认值全部现场取证而非抄文档。 |
| 8 | open-telemetry/opentelemetry.io（`docs/`，kind: docs） | <https://opentelemetry.io/docs/> | 968 | 2026-09-11 | CC-BY-4.0（实读仓库 LICENSE：Creative Commons Attribution 4.0 International） | 官方文档：数据模型、SDK、Collector、语义约定 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 官方文档站。CC-BY-4.0 属可合入档（`docs/roadmap.md` 许可表第一行），`SOURCES.yaml` 的 `notes` 写署名。具体性给 2：面向入门的篇幅多，可执行不变量密度低于上面几个 skill 仓。 |
| 9 | rampstackco/claude-skills `skills/monitoring-and-alerting` | <https://github.com/rampstackco/claude-skills> | 840 | 2026-09-07 | MIT | SLO / 错误预算、告警分级与路由、on-call、告警疲劳 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE | SLO 侧唯一成体系的候选：SLO 四要素（对象/成功判据/目标/窗口）、各 nine 对应的月度允许时长表（99.9% = 43 分钟、99.99% = 4 分 22 秒）、三级告警（page/notify/log）与"tier 1 每周 >1–2 次即为疲劳"的量化门、季度告警审计。多窗口多燃烧率不在其中，由 Google SRE Workbook 补（候选 17）。 |
| 10 | github/awesome-copilot `skills/appinsights-instrumentation` | <https://github.com/github/awesome-copilot> | 38879 | 2026-09-10 | MIT（skill 目录自带 LICENSE.txt，Microsoft，MIT） | Azure Application Insights / Azure Monitor OTel 发行版埋点 | 3 | 3 | 2 | 2 | 2 | 12 | MAYBE → reference | 内容本身合格，但主体是 Azure Monitor 的产品面（连接字符串、`appinsights.bicep`、`appinsights.ps1`、采样百分比的 Azure 侧语义），按本波次 Contract 归 `azure`，不归 `observability`。只作 reference：用来确认"厂商发行版包的是 OTel SDK + 一个 exporter"这条边界说法，未取内容。 |
| 11 | getsentry/skills | <https://github.com/getsentry/skills> | 990 | 2026-09-07 | Apache-2.0 | —— | 2 | 3 | — | — | 2 | — | REJECT | 路线图里的种子 `skills/sentry-sdk-setup` 与 `skills/sentry-workflow` **已不存在**：`gh api .../git/trees/main?recursive=1` 列出的 27 个 skill 全是 agents-md / code-review / security-review / skill-writer / gha-security-review 一类，无任何可观测性 skill。种子更正，不占合入清单。 |
| 12 | getsentry/sdk-skills `plugins/sentry-sdk-skills/skills/span-convention-review` | <https://github.com/getsentry/sdk-skills> | 3 | 2026-06-19 | Apache-2.0 | 审查 SDK 仓库里的 span 是否符合 Sentry Conventions | 3 | 0 | 2 | 2 | 2 | 9 | MAYBE → reference | 新鲜度 0（>3 个月未推送）。内容是"给 Sentry SDK 贡献者审查 span op/description 是否符合 **Sentry** Conventions"，主体是 Sentry 产品约定而非 OTel 语义约定，且带 `model: opus`、`allowed-tools: … WebFetch` 等必须剥离的 agent 字段。只作 reference：其 op 前缀 → 模块 → 约定 URL 的映射表用来交叉验证本 skill 的 semconv 领域清单没有漏项。 |
| 13 | codewithmukesh/dotnet-claude-kit `skills/opentelemetry` | <https://github.com/codewithmukesh/dotnet-claude-kit> | 707 | 2026-08-07 | MIT | .NET 10 的 `ActivitySource` / `IMeterFactory` / OTLP + Aspire Dashboard | 1 | 1 | 2 | 2 | 2 | 8 | MAYBE → reference | 单语言（.NET）绑定，且与既有 `csharp-dotnet` skill 的地盘重叠。只作 reference：用于确认"自动埋点 + 手动 span 的分工"在 .NET 侧的说法与本 skill 语言中立的写法不冲突。未取内容。 |
| 14 | microsoft/vscode `.github/skills/otel` | <https://github.com/microsoft/vscode/blob/main/.github/skills/otel/SKILL.md> | 191977 | 2026-09-11 | MIT | VS Code 自己的 Copilot Chat 埋点抽象 | 3 | 3 | 1 | — | 2 | ≤4 | REJECT | 仓库私有约定：讲的是 Copilot Chat 内部的 instrumentation 抽象层、agent 执行路径的 span/metric/event 名。对本仓库读者是实现样例而非可迁移规则。 |
| 15 | chrisreddington/flight-school `.github/skills/opentelemetry` | <https://github.com/chrisreddington/flight-school> | 30 | 2026-09-10 | MIT | 某个示例项目的 GenAI 埋点 | 0 | 3 | 1 | — | 2 | ≤4 | REJECT | 个人 demo 仓的仓库内 skill，内容绑定该项目的 Aspire OTLP receiver 与 GenAI 约定，无通用规则。 |
| 16 | prometheus/prometheus | <https://github.com/prometheus/prometheus> | 66032 | 2026-09-10 | Apache-2.0 | Prometheus 本体：TSDB 状态端点、原生直方图、exemplar、`info()` | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE → reference | 只读不合入内容：用来复核候选 3 引用的每条 Prometheus 侧版本门（原生直方图 2.40+、`_created` 2.39+、exemplar 2.26+、`info()` 为 Prometheus 3.x 实验特性需 `--enable-feature=promql-experimental-functions`）。事实经它确认后写进正文，不复制文本。 |
| 17 | Google SRE Workbook ch. 5 "Alerting on SLOs" | <https://sre.google/workbook/alerting-on-slos/> | — | — | Proprietary（Google 版权，网页免费阅读，非开源许可） | 多窗口多燃烧率告警 | 3 | 1 | 3 | 3 | 0 | 10 | INCLUDE → reference | 多窗口多燃烧率的规范出处（14.4× / 1h + 5m 短窗页出、6× / 6h、1× / 3d 走工单，以及短窗存在的理由是让告警及时解除）。专有许可 → 只能 reference：全部结论用自己的话重写，数字对照该章复核。 |
| 18 | grafana/loki | <https://github.com/grafana/loki> | 28866 | 2026-09-11 | AGPL-3.0 | 日志标签基数 | 3 | 3 | 3 | — | 0 | — | REJECT（作为 merged） | AGPL-3.0，按 `docs/roadmap.md` 许可表只能 reference，且其内容（Loki 标签与 stream 设计）已被候选 3 的 `loki-label-analyzer` 以 Apache-2.0 覆盖。不单独立行为上游。 |
| 19 | open-telemetry/opentelemetry-specification | <https://github.com/open-telemetry/opentelemetry-specification> | 4337 | 2026-09-11 | Apache-2.0 | Span Event API 弃用计划 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE → reference | 只读一件事并取证：`oteps/4430-span-event-api-deprecation-plan.md` 确实存在（5688 字节）。这是"用日志记录异常而不是 `recordException`"这条规则的唯一权威依据，dash0 引用它而未给路径，本仓库实读确认。 |

## 深度审查

### 1. ollygarden/opentelemetry-agent-skills（主干，Collector 侧）

18 个 `skills/otel-*` 的多技能仓库，`.claude-plugin/marketplace.json` 打包。结构上是本次见过最好的：
`skills/otel-collector/` 下 22 个组件各自一个目录，固定五文件（`README.md` 元数据 + 描述 +
"Use when / Avoid when" + Details 索引、`configuration.md` 全配置表、`verification.md`
telemetrygen 验证配方、`advanced.md`、`quirks.md`）。这个"README 常驻、细节按需加载"的分层正是
`docs/skill-standard.md` 第 2 节想要的效果。

frontmatter 干净：只有 `name` + `description`，无 agent 专属字段，直接合规。

质量上最值钱的是 `quirks.md`：`memory_limiter` 一篇就给出七条会造成事故的判断——限值比的是 Go heap
而不是 RSS（容器 limit 要比 `limit_mib` 高 10–15%，否则内核先 OOM-kill）、`check_interval` 默认 `0s`
即校验失败、`limit_mib` 与 `limit_percentage` 同时给时静默取前者、拒绝数据返回的是**非永久**错误因此
不会重试的 receiver 会丢数据、持续拒绝是容量不足信号而非调参问题。这些全部在本机 0.160.0 上复核过。

它不覆盖：告警、SLO、基数经济学、结构化日志字段约定、从生产信号反查代码的工作流。这些由候选 2/3/4/9 补。

### 2. dash0hq/agent-skills（主干，埋点侧）

四个 skill（`otel-instrumentation` / `otel-collector` / `otel-semantic-conventions` / `otel-ottl`），
`rules/*.md` 带 `title` / `impact` / `tags` frontmatter。`impact: CRITICAL|HIGH|MEDIUM` 这个排序信号
本身有用，但它是 Dash0 自己的约定，不在 Agent Skills 规范里，剥离。

`rules/spans.md` 是这个仓库的核心，也是本 skill `references/instrumentation.md` 的骨架来源：
每个 span 三个决定（name / kind / status），逐决定给反例表；span kind 常见错误（消息发布是
`PRODUCER` 不是 `CLIENT`，消息处理是 `CONSUMER` 不是 `SERVER`）；status 按 kind 分表——**SERVER
span 上的 4xx 不是错误，CLIENT span 上的同一个 4xx 是错误**，这是全场最容易写错也最容易被基线答错
的一条；重试最终成功不置 ERROR；异常改用日志记录（引 OTEP 4430）。

agent 绑定问题：`rules/` 之间大量相对链接（`../../otel-collector/rules/sampling.md`），跨 skill 互链。
本仓库标准第 4 节禁止 reference 之间互链，全部改为由 SKILL.md 单层路由。

与候选 1 的重叠：两家都写 Collector。ollygarden 是**组件级**（某个组件的键、默认值、校验、稳定度），
dash0 是**流水线级**（一个信号一条 pipeline、processor 顺序、agent/gateway 两层、采样架构）。互补，
按这个切分各取一半。两家在 `batch` 处理器上正面冲突，见裁决 1。

### 3. grafana/skills（基数与告警）

官方厂商，56 个 skill 的大仓，按 `grafana-cloud/` 与 `grafana-core/` 分组。绝大多数是 Grafana Cloud
产品面（Adaptive Metrics、Fleet Management、OnCall/IRM、Synthetic Monitoring、k6），属产品包装，
不取。取四个与厂商解耦的：

- `prometheus-cardinality-troubleshooter`：诊断态。`status/tsdb` 的四个字段
  （`seriesCountByMetricName` / `labelValueCountByLabelName` / `memoryInBytesByLabelName` /
  `seriesCountByLabelValuePair`）、症状→原因→首个动作表、churn 诊断
  （`prometheus_tsdb_head_series_created_total` 对 `_removed_total`）、常见元凶画廊。
- `prometheus-label-strategy`：预防态。逐标签基数评分表、静态目标标签 vs 动态样本标签、histogram
  (buckets+3) 放大、info-metric 与 `info()`、五级补救手段的优先序。
- 两个 skill 共享的「The One Rule」是本 skill `## Core rules` 里权重最高的一条。
- `grafana-core/alerting-irm`：告警规则的三种形态（Grafana-managed / Prometheus ruler / Loki LogQL）
  完整 YAML，`for:` + `labels.severity` + `annotations.runbook_url` 的形状。

厂商绑定要剥离的部分：Adaptive Metrics / DPM / Active Series 是 Grafana Cloud 的计费与产品概念。
本 skill 保留"post-ingest、计数器重置感知、可审计、可回滚的聚合"这个**机制**描述，不点名产品——
读者的后端可能是 Mimir、Thanos 或云厂商托管服务。

### 4. addyosmani/agent-skills `observability-and-instrumentation`

单文件 skill，无 references。价值在框架而非细节：先定义"working"再埋点（写下 on-call 的 2–4 个问题，
每个信号必须回答其中一个）、三信号的成本画像表、日志级别与 on-call 动作的对应、correlation ID 强制、
"多个入口写同一个 sink 时必须标注入口"这条少见但真实的坑、症状/原因告警两列对照、runbook 三行最小
形态、以及第 7 步"验证埋点本身"（在 staging 触发错误后只靠遥测定位，不读源码）。

它的 `## Common Rationalizations` 与 `## Red Flags` 两节是本 skill `## Output format` 里"按后果排序、
说清没问题的地方"的来源。它把"正在发生的故障"明确转交给 `debugging-and-error-recovery`，与本仓库
`debugging` / `observability` 的分界句方向一致，属独立佐证。

### 5. o11y-dev/opentelemetry-skill

19 个 reference 的单 skill，覆盖面宽但深度不均：`collector.md` / `sampling.md` / `ottl.md` 与前两家
重叠且不如它们细；真正独有的是三条——OTLP gRPC(4317) 默认、HTTP(4318) 作为被代理/浏览器/后端挡住时
的逃生口；load-balancing 的路由键必须确定且非字符串属性要先归一化；">100 unique values 不得作为
metric 维度"这个可直接执行的量化门。`## Pre-Flight Checklist` 的五问（信号量级 / 基数风险 /
是否容忍重启丢数据 / 是否跨公网 / 部署目标）被采纳为本 skill 一个 workflow 的开头。

不取：`ai-agents.md`（观测 AI coding agent 自身）、`setup-ecs.md` / `setup-vm.md` /
`setup-kubernetes.md`（部署机制，K8s 清单归 `containers`，云侧归三朵云）。

frontmatter 污染最重的候选：`triggers`（含 `file_patterns` / `config_keys` / `keywords`）、
`tessl_version`、`signals`、`deployments`、`deployment_patterns`、`supported_platforms`、
`vendor_agnostic` 全部是 agent/平台专属字段，按标准 1.2 剥离。

### 6. rampstackco/claude-skills `skills/monitoring-and-alerting`

四层模型（可用性 / 正确性 / 性能 / 错误与异常）有用但偏 Web 站点视角（Core Web Vitals、synthetic
检查）。真正采纳的是 SLO 与错误预算那一节：SLO 四要素、各 nine 的月度允许时长表、"不要追求 100%，
每多一个 nine 贵一个数量级"、错误预算的三档反馈（健康时激进发布 / 半耗时减速 / 耗尽时冻结高风险变更）、
三级告警与"tier 1 每周 >1–2 次即为疲劳"。它的 `## If required data is unavailable` 那条"说清缺口
就是完整回答"与本仓库的交付要求一致。

不取：`display_order` / `catalog_summary` / `category` 是该仓库目录系统的字段，剥离；vendor 建议
（"不要新上 Opsgenie，Atlassian 2025-06 停售、2027-04 停服"）是时间敏感表述，按标准第 3 节不写进正文。

它缺多窗口多燃烧率——只有单窗口阈值。这个缺口由候选 17 补，也正是评测场景 3 的核心区分点。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | `batch` 处理器该不该用 | dash0 `rules/processors.md`：**不要用** `batch` 处理器，崩溃时内存里的批次全丢，改用 exporter 的 `sending_queue` + `storage: file_storage`；并引自家博客《Why the OpenTelemetry batch processor is going away (eventually)》。ollygarden `SKILL.md`：`batch` 处理器**仍是 Beta 且受支持**，需要 pipeline 级批处理时用它，放在丢数据的处理器之后；exporter 侧 `sending_queue.batch` 是 opt-in。 | 采 ollygarden，但保留 dash0 的持久化理由。正文写法：默认在 exporter 的 `sending_queue` 上配 `batch` 并配 `file_storage` 以便重启不丢数据；确实需要 pipeline 级批处理时 `batch` 处理器可用且不会报废，放在丢数据的处理器之后。**不写"batch 已弃用"。** | 实测 E4/E5（0.160.0）：`batch` 处理器被 pipeline 引用时正常启动，**没有任何 deprecation 警告**；`sending_queue.batch` 子块 `validate` 通过。"going away" 是厂商博客的路线图判断，不是当前运行时事实。官方厂商（两家都不是 OTel 官方）平级时以**可验证的运行时行为**裁决。 |
| 2 | 声明但未被任何 pipeline 引用的组件是否导致启动失败 | dash0 `rules/pipelines.md`：「Every component declared in the configuration must appear in at least one pipeline — unused components cause a startup error」，并把它列为 anti-pattern「The Collector rejects configurations with declared … not referenced by any pipeline」。 | **推翻**。正文写：未被引用的组件不会导致启动失败，删掉它是卫生问题；真正会出事的是被引用了却不该在生产里的组件（例如挂在生产 logs pipeline 上的 `debug` exporter）。 | 实测 E3（0.160.0）：`c4.yaml` 声明了 `batch` 处理器但任何 pipeline 都不引用它，`validate` 静默通过，真实启动打出 `Everything is ready. Begin running and processing data.`，无 error 无 warning。 |
| 3 | `memory_limiter` 必须排在 processors 首位——这是校验还是约定 | dash0 与 ollygarden 都写「必须首位」，但都未说明违反时会发生什么。读者容易读成"配错了会报错"。 | 正文写成**约定 + 无声后果**：放首位是为了在其它处理器分配内存之前施加背压；Collector 不校验这一点，错序的配置完全正常启动，代价只在负载升高时以 OOM 的形式出现，所以这是 review 必须抓的项，不是 CI 能抓的项。 | 实测 E1（0.160.0）：`processors: [resource, memory_limiter]` 启动干净，日志里连 warning 都没有，`Memory limiter configured` 正常打印。 |
| 4 | SDK 侧要不要采样 | dash0：SDK 一律 `AlwaysOn`（默认），所有采样下沉 Collector，因为头部决策发生在请求结果已知之前。addyosmani：`Sample head-based at a low rate by default; keep 100% of errors if your backend supports tail sampling`。 | 采 dash0。正文：SDK 保持默认 `AlwaysOn`；采样放 Collector。逃生口只有一个——SDK 到 Collector 的这一跳本身成本不可接受时（出网带宽、Lambda 计费）才在 SDK 做概率采样，并写明代价是错误与长尾按同一概率被丢。 | 更具体者胜，且与可验证机理一致：头部采样的决策在请求结果已知之前作出，`TraceIdRatioBased(0.05)` 会按同一概率丢掉错误与长尾——addyosmani 那句"保留 100% 错误"在 SDK 侧根本做不到（SDK 采样时还不知道会不会出错）。评测场景 2 的第一条正是这个点。 |
| 5 | 降基数能不能在 scrape / relabel 层做 | grafana 两个 skill：**绝对不行**——`labeldrop` 掉构成唯一性的标签会混合计数器重置、使 `rate()` 返回荒谬值、DPM 反而上升，且无配置报错、无数据留痕。dash0 `rules/processors.md`：用 `filter` / `transform` 处理器"降低遥测量"。 | 采 grafana，并把它上升为 `## Core rules` 里的一条硬不变量。dash0 的 `filter` 用法限定在它真正安全的场景：**丢弃整条指标/整条记录**（按 `__name__` 或 instrumentation scope），不是合并序列。 | grafana 是 Prometheus/Mimir 侧官方厂商，且给出了完整的破坏机理；dash0 那节讲的是 OTel 管道里的丢弃，本身并不主张合并序列，两者并非真冲突，而是"丢整条"与"合并"的区分没说清。评测场景 4 的夹具把这条做成了一个已经发生的事故。 |
| 6 | 异常怎么记 | dash0：**不要**用 `span.recordException`，Span Event API 正在弃用，改为在 active span 上下文里发一条带 `exception.*` 与 `trace_id`/`span_id` 的日志记录。多数其它上游仍写 `recordException`。 | 采 dash0。正文写日志记录形态，并在 `## Old patterns` 折叠块里保留 `recordException` 的说明。 | 实读取证：`open-telemetry/opentelemetry-specification` 的 `oteps/4430-span-event-api-deprecation-plan.md` 确实存在（5688 字节），dash0 引用它但未给路径，本仓库核对通过。官方规范 > 厂商 skill > 社区。 |
| 7 | `gen_ai.*` 语义约定去哪查 | ollygarden `otel-semantic-conventions`：`gen_ai.*` / OpenAI / MCP 用专门的 GenAI 仓库，核心仓在 v1.42.0 之后只留弃用存根。 | 采纳，并把版本号写进正文的版本门。 | `open-telemetry/semantic-conventions` 的 `CHANGELOG.md` v1.42.0 条目确认：`docs/gen-ai/` 已弃用并移至 `semantic-conventions-genai`。最新 tag v1.44.0。 |
| 8 | 语义约定迁移的控制面 | 各上游都给"旧名→新名"的重命名表，但只有官方仓说明了**切换机制**。 | 正文以机制为主、重命名表为辅：`OTEL_SEMCONV_STABILITY_OPT_IN` 取 `<category>` 切到稳定集、`<category>/dup` 双发以便分阶段迁移，两者同时出现时 `/dup` 优先；声明式配置形态（`.instrumentation/development.general.<domain>.semconv` 的 `version` / `experimental` / `dual_emit`）仍是 Development 状态，不能当稳定接口用。 | `open-telemetry/semantic-conventions` `docs/http/README.md`、`docs/db/README.md`、`docs/configuration/version-selection.md` 实读。这是基线最可能答不出的一类事实——重命名表模型背得出，切换机制与优先级背不出。 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `ollygarden-otel-skills` | ollygarden/opentelemetry-agent-skills | merged | Collector 组件级事实：`memory_limiter` 的 heap 语义、必填键、校验规则、拒绝语义与"持续拒绝 = 容量不足"；组件 snake_case 改名窗口与别名；per-signal 稳定度；`otlp` receiver 默认 localhost；exporter 侧 `sending_queue.batch` opt-in；telemetrygen + `debug` 的验证配方形态 |
| `dash0-agent-skills` | dash0hq/agent-skills | merged | 埋点侧骨架：span 三决定（name/kind/status）、按 span kind 分表的 HTTP status 映射、span 卫生量化门（无 CLIENT 根 span、无孤儿、INTERNAL ≤10、<5ms ≤20）、headless 操作的手动根 span、异常改日志记录、SDK 一律 AlwaysOn、Collector 流水线与 agent/gateway 两层采样架构、`k8sattributes` 的 pod_association 与 RBAC 静默失败、采样前物化 RED 指标 |
| `grafana-skills` | grafana/skills | merged | 基数与告警：「不得在 scrape 时丢弃构成唯一性的标签」及其完整破坏机理、`status/tsdb` 四字段诊断路径、churn 诊断、histogram (buckets+3) 放大、逐标签基数评分表、静态目标标签 vs 动态样本标签、info-metric 模式、告警规则 YAML 形状（`for:` + severity + runbook_url） |
| `addyosmani-agent-skills` | addyosmani/agent-skills | merged | 工作流骨架：先写下 on-call 的问题再埋点、三信号分工（that/where/why）、结构化日志的事件名 + correlation ID + 入口标注、RED/USE、症状 vs 原因告警、runbook 三行最小形态、"验证埋点本身"这一步 |
| `o11y-dev-otel` | o11y-dev/opentelemetry-skill | merged | OTLP gRPC 4317 默认 / HTTP 4318 逃生口；load-balancing 路由键必须确定；">100 unique values 不得作 metric 维度"的量化门；埋点/流水线动手前的五问前置清单；"Collector review 是系统 review"的跨字段一致性 |
| `otel-semconv` | open-telemetry/semantic-conventions | merged | 全部语义约定版本分界事实：v1.44.0、`OTEL_SEMCONV_STABILITY_OPT_IN` 的 `<category>` / `/dup` 与优先级、`gen_ai.*` 在 v1.42.0 移出、`deployment.environment` 自 v1.27.0 弃用、声明式版本选择仍 Development、领域清单 |
| `otel-docs` | opentelemetry.io/docs | merged | 三信号数据模型与关联、context 传播、Resource/schema_url、Collector receiver/processor/exporter/connector 概念面、部署形态 agent vs gateway 的官方术语 |
| `rampstack-monitoring` | rampstackco/claude-skills | merged | SLO 四要素、各 nine 的月度允许时长、错误预算的三档反馈、两级告警与"每周 >1–2 次即疲劳"的量化门、季度告警审计 |
| `otel-collector-contrib` | open-telemetry/opentelemetry-collector-contrib | merged | 被测运行时（0.160.0 官方镜像）：组件规范名、校验报错原文、默认值 —— 本 skill 12 条实测的取证对象 |
| `otel-spec` | open-telemetry/opentelemetry-specification | reference | 只读取证 OTEP 4430 存在，支撑"异常用日志记录而非 `recordException`" |
| `prometheus` | prometheus/prometheus | reference | 只读复核 Prometheus 侧版本门：原生直方图 2.40+、`_created` 2.39+、exemplar 2.26+、`info()` 为 3.x 实验特性 |
| `google-sre-workbook` | sre.google/workbook | reference | 多窗口多燃烧率的数字与"短窗为何存在"的理由；专有许可，结论全部重写 |
| `awesome-copilot-appinsights` | github/awesome-copilot | reference | 只读确认"厂商发行版 = OTel SDK + 一个 exporter"这条边界说法；产品面归 `azure` |
| `getsentry-sdk-skills` | getsentry/sdk-skills | reference | 只读交叉验证 semconv 领域清单（db / http / messaging / gen_ai / cache / queue）无漏项 |
| `dotnet-claude-kit` | codewithmukesh/dotnet-claude-kit | reference | 只读确认自动埋点与手动 span 的分工在 .NET 侧无矛盾；单语言内容未取 |

## 实测记录（Collector 0.160.0，本机 Docker）

被测体：`otel/opentelemetry-collector-contrib:latest`，`docker run --rm … --version` →
`otelcol-contrib version 0.160.0`。发送端：
`ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest`。
配置文件在 `/root/otelexp/`（`/tmp` 下 Docker 挂载不可见，已换路径）。

| # | 断言 | 命令 | 原始输出（节选） | 结论 |
|---|---|---|---|---|
| E0 | 版本 | `docker run --rm otel/opentelemetry-collector-contrib:latest --version` | `otelcol-contrib version 0.160.0` | 基准版本确定 |
| E1 | `memory_limiter` 不在首位会被拒绝 | `--config c1.yaml`（`processors: [resource, memory_limiter]`） | `Memory limiter configured {…"limit_mib": 128…}` … `Everything is ready. Begin running and processing data.`，无 warning | **推翻**：不校验、不告警。→ 裁决 3 |
| E2a | 缺 `check_interval` 的报错文本 | `validate --config c2.yaml` | `Error: processors::memory_limiter: 'check_interval' must be greater than zero` | 确认 ollygarden 的原文 |
| E2b | 缺 `limit_mib`/`limit_percentage` 的报错文本 | `validate --config c3.yaml` | `Error: processors::memory_limiter: 'limit_mib' or 'limit_percentage' must be greater than zero` | 确认 |
| E3 | 声明但未引用的组件导致启动失败 | `validate --config c4.yaml` 与真实启动 | `validate` 无输出（通过）；启动 `Everything is ready. Begin running and processing data.` | **推翻 dash0** → 裁决 2 |
| E4 | `batch` 处理器已弃用/会告警 | `--config c6.yaml`（pipeline 引用 `batch`） | 仅 `Everything is ready…`；`grep -iE 'warn|error|deprecat'` 无 deprecation 行 | **推翻"going away"** → 裁决 1 |
| E5 | exporter 侧 `sending_queue.batch` 可用 | `validate --config c8.yaml`（含 `sending_queue.batch.{flush_timeout,min_size}` + `tail_sampling`） | 无输出（通过） | 确认 opt-in 子块存在且 `tail_sampling` 最小配置合法 |
| E6 | 信号类型错配的报错 | `validate --config c5.yaml`（`hostmetrics` 放进 traces pipeline） | `Error: failed to build pipelines: failed to create "hostmetrics" receiver for data type "traces": telemetry type is not supported` | 确认：一条 pipeline 只处理一种信号，错配是启动期硬错误 |
| E7 | `otlp` receiver 默认 endpoint | `--config c10.yaml`（`grpc: {}`，不写 endpoint） | `Starting GRPC server {… "endpoint": "127.0.0.1:4317"}`；显式写 `0.0.0.0:4317` 时为 `[::]:4317` | 确认 ollygarden：默认 localhost，容器里必须显式写 `0.0.0.0` |
| E8 | `memory_limiter` 的 extension 形态在 contrib 里 | `validate --config c9.yaml` | `Error: … 'extensions' unknown type: "memory_limiter" … (valid values: [oidc pprof … k8s_observer])` | 确认 ollygarden：extension 形态未编进 stock contrib 发行版 |
| E9 | exporter 规范名 | `components` 子命令 | 存在 `otlp_grpc`、`otlp_http`（module `go.opentelemetry.io/collector/exporter/otlp*exporter v0.160.0`）；receiver 仍叫 `otlp`；`otlp` 作 exporter 名在 E5 中仍被接受 | 确认改名 + 别名保留 |
| E10 | 端到端：`debug` exporter 输出与 resource 处理器 | 后台跑 c7.yaml（`[memory_limiter, resource]`）+ `telemetrygen traces --traces 2` | `Resource SchemaURL: https://opentelemetry.io/schemas/1.40.0` / `service.name: Str(exp-svc)` / `deployment.environment.name: Str(exp)`；`Span #1 … Kind: Client … Parent ID:` 为空 | 确认 `debug` 的 `verbosity: detailed` 逐 span 打印；**resource 上带 schema_url**（语义约定迁移那一节的证据）；telemetrygen 的根 span 恰好是 `CLIENT` 且无父——正是 dash0「根 span 不能是 CLIENT」描述的形态 |
| E11 | OTTL `transform` 脱敏真的生效 | 后台跑 c11.yaml（`set(span.attributes["network.peer.address"], "REDACTED")`）+ telemetrygen | `-> network.peer.address: Str(REDACTED)`（两条 span 都命中） | 确认 |
| E12 | OTTL 新旧两种语法都还能用 | `validate --config c12.yaml`（旧式 `context: span` + `statements:` 块） | 无输出（通过）；E11 的扁平 `span.attributes[…]` 形式同样通过 | 确认 0.160.0 同时接受 context 推断式与显式 context 块 |

未在本机验证、标 `[official]` 的部分（research 备注也重复一次）：Prometheus TSDB 状态端点的字段
（无本机 Prometheus 实例）、Grafana/Mimir 侧的 `cortex_ingester_memory_series`、多窗口多燃烧率的
具体倍数、各语言 SDK 的实际行为（未跑真实应用）、K8s `k8sattributes` 的 pod 关联（无集群）。
`aws` / `az` / `gcloud` / `otelcol` 二进制本机均不存在，Collector 全部走官方镜像。

## 基线缺口

无 skill（`uv run tools/run_evals.py observability --baseline`，claude-opus-5 · medium）时未达成的
`expected_behavior`。判定方式：读 `answer.md` 的最终回答，并对 `events.jsonl` 全文做关键词检索
确认该判断在整轮里根本没出现（而不是只在最终摘要里被省略）。

**这个基线非常强**：它会自己 `docker run` 起 collector、写 promtool 单测、算采样率的数量级，
四个正例里大部分行为都达成了。所以第一轮 S3 出现了零区分度，按 Phase B 改写后重跑（见下）。

| 场景 | 未达成的行为 | 说明（检索证据） |
|---|---|---|
| 1 | `memory_limiter` 错序**不被 Collector 校验**、错序配置无警告启动 | 基线只说"需要放第一位以施加背压"，没有"不校验/不告警、因此是 review 门而非 CI 门"这层。`"does not enforce"` / `"不校验"` / `"不报错"` 在 `events.jsonl` 全为 0 命中 |
| 1 | `limit_mib` 比的是 Go heap 而非进程 RSS | `"Go heap"` 0 命中，`RSS` 无有效上下文。基线只提到"1024 MiB 与容器 limit 不对齐"，没有 heap/RSS 这个机理 |
| 2 | 语义约定迁移的控制面 `OTEL_SEMCONV_STABILITY_OPT_IN`（`http` / `http/dup`、`/dup` 优先） | 0 命中。基线**确实**把属性名改对了（`http.request.method` 68 命中、`url.full` 83、`http.response.status_code` 69），但完全不知道库侧是怎么切换的 |
| 2 | 异常改用日志记录、Span Event API 已有弃用计划（OTEP 4430） | `"4430"` / `"Span Event"` / `"exception.stacktrace"` 均 0 命中；基线在自己的修正代码里**保留了** `span.recordException(error)`（`recordError` 辅助函数） |
| 2 | 逐行 span 折叠为一个批量 span + `batch.size` 属性 | `"batch.size"` 0 命中。基线加了父 span，但仍是"每车一个 `expire_cart` span" |
| 2 | 直方图按 (bucket 数 + 3) 放大基数，因此先砍直方图的标签 | `"buckets + 3"` / `_created` 0 命中。基线发现了毫秒值喂秒级桶（真 bug），但没有放大倍数这条规则 |
| 4 | scrape 期唯一安全动作是按 `__name__` 整条丢弃指标 | `__name__` 0 命中。基线只说"回滚 labeldrop、去源头修" |
| 4 | 已入库序列用"计数器重置感知、可审计、可回滚"的 post-ingest 聚合降本 | `"post-ingest"` / `"counter-reset"` 0 命中 |
| 4 | 直方图 (bucket 数 + 3) 放大这条**规则** | 基线用 2841190 ÷ 402118 ≈ 7.07 反推出"约 7 个 bucket/用户"，是实证不是规则；`"buckets + 3"` 0 命中 |
| 3（改写后） | 双发窗口期内两个不同单位的指标名共存，而这是 `OTEL_SEMCONV_STABILITY_OPT_IN` 的 `/dup` 造成的 | 0 命中。**有 skill 时也未在回答里达成**，如实记录为两边都未达成 |

### S3 的改写（零区分度处置）

第一轮 S3 基线 10/10 全中，且我自己写错了一条判据：夹具原来的录制规则是
`sum without (pod, instance) (rate(...[5m]))`，这是**正确**写法（先 rate 再聚合），而判据却断言它
会混合计数器重置。按 Phase B 处置——不是降低标准，而是把夹具改成真的含事故级缺陷、把判据改写为
版本分界事实：

1. 录制规则改成 `rate(sum without (pod, instance) (http_requests_total{...})[5m:30s])`——先跨 pod
   求和再求速率，每次 pod 重启在汇总序列上都是一次计数器重置，语法合法、读着合理。
2. 新增 `ProviderLatency` 告警：对 `http_client_request_duration_seconds_bucket` 用 `> 800`，注释
   自承"same 800ms budget as before"。稳定 HTTP 约定把 `http.client.duration` 改名为
   `http.client.request.duration` **并把单位从 ms 改成 s**（官方 `docs/non-normative/http-migration.md`
   实读确认，桶边界也一并重算、去掉了 0 边界），所以这条规则从上线起就永不触发。
3. 判据补上迁移控制面（`OTEL_SEMCONV_STABILITY_OPT_IN` 的 `/dup` 双发期）。

重跑结果：前两条**基线也答对了**（`rate(sum` 57 命中并实测出 +111% 误差；单位错也抓到并给了
`p95 = 0.975s` 的反证），第三条两边都没答出。S3 因此仍是低区分度场景，如实记录，不改判。

## 评测结果

模型固定 claude-opus-5 · medium（`tools/run_evals.py` 默认，未传 `--model` / `--thinking`）。
"达成数"按上表同一套判定方式人工逐条判。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 collector review | claude-opus-5:medium | 无（baseline） | false | 8 / 10 | 未达成：`memory_limiter` 错序不被校验、`limit_mib` 是 Go heap 而非 RSS |
| 1 collector review | claude-opus-5:medium | 有 | **true** | 10 / 10 | 两个缺口都填补：明确写出"原配置 `validate` 退出 0 …『能启动』不是上线依据"、"放最后等于没有：启动无警告，代价是几天后的 OOMKill"、"`limit_mib` 比的是 Go heap 而非 RSS，容器 limit 要明显高于它"；并正确说出未引用的 `batch` "不是启动错误，是逐条导出" |
| 2 instrumentation | claude-opus-5:medium | 无（baseline） | false | 6 / 10 | 未达成：`OTEL_SEMCONV_STABILITY_OPT_IN`、异常改日志记录/OTEP 4430、`batch.size` 批量 span、直方图放大倍数。基线另外实测出两个我没写进判据的真 bug（`sdk.start()` 在 `import express` 之后导致自动埋点完全没挂上；属性打在 middleware span 而非根 span） |
| 2 instrumentation | claude-opus-5:medium | 有 | **true** | 10 / 10 | 四个缺口全部填补：`recordException` → 带 `exception.*` 的日志记录、`OTEL_SEMCONV_STABILITY_OPT_IN=http/dup` 必须进 pod env（并指出代码里设不了）、reconcile 改成"一个根 span + `batch.size` + 一条批量 UPDATE"、"`path` 把订单号塞进直方图，再乘桶数"。同样独立发现了 SDK 启动顺序缺陷与 `express.json()` 缺失 |
| 3 alerts + SLO（改写后） | claude-opus-5:medium | 无（baseline） | false | 11 / 12 | 未达成：`/dup` 双发期两个单位并存。其余全中，且用 promtool 双 pod 夹具把 sum-before-rate 量成"真实 2 rps 报 4.22 rps（+111%）" |
| 3 alerts + SLO（改写后） | claude-opus-5:medium | 有 | **true** | 11 / 12 | 同一条未达成。低区分度场景，不改判。有 skill 侧更严的地方在框架而非新增判据：按"会算错数字的排在只是没用的前面"排序、新增 `CheckoutSLIMetricsMissing`（"缺失序列的比率是『不存在』不是『触发』"，导出器坏掉会静默关掉整个 pager）、并拒绝用平均值凑 latency SLI 而把缺失前提写进 `known_gaps` |
| 4 production triage | claude-opus-5:medium | 无（baseline） | false | 6 / 9 | 未达成：按 `__name__` 整条丢弃是唯一安全的 scrape 期动作、post-ingest 计数器重置感知聚合、(bucket+3) 放大规则 |
| 4 production triage | claude-opus-5:medium | 有 | **true** | 9 / 9 | 三个缺口全部填补："紧急期只允许按 `__name__` 整条 drop …那是可见的损失"、"直方图再乘约 14×（每 bucket 一条 + `_sum`/`_count`/`_created`）"并据此反推 2.84M / 14 ≈ 20 万基础序列正好对上 `order_id` 量级、标识符移到 span 属性 / exemplar。还多出一条基线没有的判断：**14:48「自愈」不可验证**，因为 labeldrop 在 14:30 已污染曲线 |
| 5 负例（slugify 本地测试挂） | claude-opus-5:medium | 无（baseline） | false | 4 / 4 | 按普通本地 bug 处理 |
| 5 负例（slugify 本地测试挂） | claude-opus-5:medium | 有 | **false** ✅ | 4 / 4 | **负例通过**：`skill_read == false`，回答里没有 OpenTelemetry / trace / 指标 / 基数 / 告警 / SLO 任何字样，只讨论 `_NON_WORD` 删掉 `/` 与空 base 拼出 `-2` |

结论：**通过**。S1 两条、S2 四条、S4 三条基线未达成的行为在有 skill 时全部达成，且都是本 skill
正文里明确写出的不变量（`## Core rules` 13/14/6/10/12/19 与 `references/collector-pipelines.md`、
`references/cardinality.md`、`references/semantic-conventions.md`）。负例 `skill_read == false`。
S3 是低区分度场景，如实记录未改判。

## 备注

### 许可核实记录（全部实读 LICENSE，不只信 API 的 `spdx_id`）

| 仓库 | API `spdx_id` | 实读 LICENSE 首行 | 处理 |
|---|---|---|---|
| ollygarden/opentelemetry-agent-skills | Apache-2.0 | `Apache License Version 2.0, January 2004` | merged |
| dash0hq/agent-skills | Apache-2.0 | `Apache License Version 2.0, January 2004` | merged |
| grafana/skills | Apache-2.0 | `Apache License Version 2.0, January 2004` | merged |
| addyosmani/agent-skills | MIT | `MIT License / Copyright (c) 2025 Addy Osmani` | merged |
| rampstackco/claude-skills | MIT | `MIT License / Copyright (c) 2026 RampStack Co.` | merged |
| **o11y-dev/opentelemetry-skill** | **NOASSERTION** | `Apache License Version 2.0, January 2004` | merged（API 不可信，实读才定） |
| **open-telemetry/opentelemetry.io** | CC-BY-4.0 | `Creative Commons Attribution 4.0 International` | merged，`notes` 写署名 |
| open-telemetry/semantic-conventions | Apache-2.0 | `Apache License Version 2.0, January 2004` | merged |
| github/awesome-copilot（`skills/appinsights-instrumentation/LICENSE.txt`） | MIT（仓库级） | `MIT License / Copyright 2025 (c) Microsoft Corporation.` | reference（范围原因，非许可原因） |
| getsentry/sdk-skills | Apache-2.0 | `Apache License Version 2.0, January 2004` | reference（新鲜度 + 范围） |
| grafana/loki | AGPL-3.0 | —— | 不立为上游（AGPL 只能 reference，且内容已被 Apache-2.0 的 grafana/skills 覆盖） |
| Google SRE Workbook | —— | 网页版权声明 © Google，非开源许可 | reference，结论全部重写 |

一个仓库的许可是它自己的，不是它所记录的那个产品的：`open-telemetry/opentelemetry.io` 记录的是
Apache-2.0 的 OpenTelemetry，但**文档仓库本身**是 CC-BY-4.0；反过来 `o11y-dev/opentelemetry-skill`
的 API 报 NOASSERTION，实读却是干净的 Apache-2.0。两个方向都要实读才知道。

### 未来同步时要盯的上游

- `ollygarden/opentelemetry-agent-skills`：有 `.github/workflows/reconcile-otel-versions.yml`，跟着
  OTel 版本自动更新，组件改名与稳定度变化会先在这里出现。
- `open-telemetry/semantic-conventions`：`CHANGELOG.md` 是本 skill 所有版本门的真值源；每个小版本
  都可能把某个领域从 experimental 推到 stable，或搬走一个领域（v1.42.0 的 `gen_ai.*` 就是）。
- `otel/opentelemetry-collector-contrib` 镜像：本 skill 的 Collector 断言全部标了 0.160.0；升版本时
  重跑 `references/collector-pipelines.md` 顶部 `Verified against:` 那一行涉及的实验。

### 放弃的方向

- **各云监控产品面**（CloudWatch / Azure Monitor / Cloud Logging 的配额、计费、控制台流程）：按本波次
  Contract 归 `aws` / `azure` / `gcp`。本 skill 只写与后端无关的采集、语义与告警逻辑。
- **AI agent 自身的可观测性**（o11y-dev `references/ai-agents.md`、GenAI semconv）：属 `ai-engineering`
  主题，本仓库尚无该 skill，不引用、不硬凑。
- **eBPF / 无侵入自动埋点**（Pixie、Beyla、Odigos）：候选里没有合格上游，且与 OTel SDK 埋点是两条
  不同的技术路线，本轮不写。
- **Profiling（第四信号）**：Collector 里多数 profiles 组件仍是 Alpha/Development，semconv 的
  `general/profiles.md` 也还在演进，写进正文会立刻腐化。只在 Collector 那节提一句稳定度。

### 未达成项（不粉饰）

- **S3 仍是低区分度场景**：12 条判据里有 skill 与无 skill 都是 11 条达成，唯一未达成的那条
  （`/dup` 双发期内两个不同单位的指标名共存）两边都没答出。改写夹具后基线把 sum-before-rate 与
  单位错都抓到了，说明这两条对这个模型不构成缺口。不改判、不再第三次改写夹具去制造缺口。
- **`## Core rules` 第 25 条（说清信号不能得出什么）在两边都达成**，因此它不是本 skill 的区分点，
  只是正确性要求。
- **`aws` / `az` / `gcloud` / `otelcol` 二进制本机均不存在**，Collector 全部走官方 Docker 镜像；
  三朵云的托管可观测性产品面一律未实测，也按 Contract 不写。
- 本机**没有 Prometheus / Mimir / Loki / Tempo 实例**，所以 `references/cardinality.md` 的
  `status/tsdb` 字段名、churn 指标名、`info()` 的实验特性开关、原生直方图与 exemplar 的版本门
  全部标 `[official]` 而非 `[verified]`，来源是 `prometheus/prometheus` 与 grafana/skills 的复核。
- **多窗口多燃烧率的倍数与窗口对**（14.4×/1h+5m 等）标 `[official]`：来源 Google SRE Workbook
  第 5 章，专有许可只能 reference，数字对照该章核对过但未在本机测量。
- **各语言 SDK 未跑真实应用**：`references/instrumentation.md` 的代码片段是说明性的，未逐语言
  运行；唯一实跑的埋点侧证据是 telemetrygen 产出的 `CLIENT` 无父根 span（E10）。
- **K8s 相关断言未在集群验证**：`k8sattributes` 的 pod 关联、RBAC 静默失败、headless Service 下
  DNS 返回 pod IP，均标 `[official]`（本机无集群）。

### 一条被上游漏掉、由官方文档补上的事实

dash0 与 grafana 的重命名表都列了 `http.client.duration` → `http.client.request.duration`，
dash0 还注了单位 ms → s，但都没说**默认桶边界也一并重算并去掉了 0 边界**。实读官方
`docs/non-normative/http-migration.md` 才拿到这一条，并据此把"迁移 duration 指标要重新推导阈值
**和桶**"写进 `references/semantic-conventions.md`。同一份文档也给出 HTTP 稳定约定的发布版本
v1.23.1。这条后来成了 S3 改写后的判据之一。
