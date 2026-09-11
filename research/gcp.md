# gcp 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"Google Cloud GCP agent skill SKILL.md github gcloud IAM Cloud Run"`
  - `gh api search/repositories?q=gcp+skills`、`q=google-cloud+agent+skills`（按 stars 排序，各取前 20）
  - `gh api search/code?q=org:GoogleCloudPlatform+filename:SKILL.md`（407 命中，人工过滤）
  - 领域官方组织仓库：`google/`、`GoogleCloudPlatform/`、`gemini-cli-extensions/`、`github/awesome-copilot`
  - 官方文档：`cloud.google.com/docs`（许可实读，见「备注」）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` = Logged in to github.com account Lynricsy，全程用已登录配额，未用匿名 API）
- 本机实测环境：Google Cloud SDK **584.0.0**（core 2026.09.04，gsutil 5.37），从
  `dl.google.com/dl/cloudsdk/channels/rapid` 下载到 `/tmp/google-cloud-sdk`，只跑 `--help`
  等离线只读命令，未认证、未创建任何计费资源。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

多技能仓库内的单个 skill 各算一个候选（`docs/workflow.md` Phase A）。`google/skills` 的
`skills/cloud/` 下共 117 个目录，下表按主题归组列出与本 skill 范围相关的那些；
`agent-platform-*`、`gemini-*`、`genkit-*`、`bigquery-*`、`managed-airflow-*`、
`datalineage-*` 等与本 skill 范围无关的组不单列。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | google/skills `skills/cloud/gcloud` | https://github.com/google/skills/blob/main/skills/cloud/gcloud/SKILL.md | 19751 | 2026-09-10 | Apache-2.0 | gcloud CLI 校验、数据削减、危险操作 denylist、项目/位置作用域 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 本 skill 的 CLI 纪律骨架。`--limit/--filter/--format` 强制、`--quiet` 必带、`gcloud help <leaf>` 非传递性校验三条，都是本机 584.0.0 复核后成立的 |
| 2 | google/skills `skills/cloud/cloud-run-basics` | https://github.com/google/skills/blob/main/skills/cloud/cloud-run-basics/SKILL.md | 19751 | 2026-09-10 | Apache-2.0 | Cloud Run service / job / worker pool 部署、必需角色 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 唯一写清 worker pool 与「从源码部署但不构建」(`--no-build`) 的上游；job 的 `--tasks`/`--max-retries`/`--task-timeout` 默认值与本机 help 一致 |
| 3 | google/skills `skills/cloud/iam-helper-for-policy-management` + `iam-helper-for-troubleshooting` + `iam-helper-for-privileged-access-management` | https://github.com/google/skills/tree/main/skills/cloud | 19751 | 2026-09-10 | Apache-2.0 | allow(v1) / deny(v2) 策略、PAM 临时提权、访问排障 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | deny policy 的 attachment-point 模型、`allUsers`/基本角色拒绝护栏、mutating 操作先计划后确认，全部采纳 |
| 4 | google/skills `skills/cloud/gke-cluster-creation` + `gke-upgrades` + `gke-networking` + `gke-basics` | https://github.com/google/skills/tree/main/skills/cloud | 19751 | 2026-09-10 | Apache-2.0 | GKE 控制面：Autopilot vs Standard、golden path、发布通道、升级 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 只取控制面（集群/节点池/网络模式/通道/Workload Identity）；`containers` 已用过的清单层内容不重复取 |
| 5 | google/skills `skills/cloud/google-cloud-storage-basics` + `google-cloud-storage-bucket-architect` | https://github.com/google/skills/tree/main/skills/cloud | 19751 | 2026-09-10 | Apache-2.0 | GCS 桶架构、存储类别、位置、生命周期 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 桶命名/位置/类别的决策序，与 gemini-cli-extensions 的同名 skill 是同源同步副本（见深度审查） |
| 6 | google/skills `skills/cloud/cloud-logging-query-generation` + `cloud-logging-configuration-basics` | https://github.com/google/skills/tree/main/skills/cloud | 19751 | 2026-09-10 | Apache-2.0 | LQL 语法、审计日志 `protoPayload`、日志桶/视图/接收器 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | LQL 硬规则（只用双引号、布尔大写、`SEARCH()` 而非 `:` 猜 `methodName`）是模型最常写错的部分 |
| 7 | google/skills `skills/cloud/google-cloud-waf-*`（security / reliability / cost-optimization / operational-excellence / performance-optimization / sustainability 六支柱） | https://github.com/google/skills/tree/main/skills/cloud | 19751 | 2026-09-10 | Apache-2.0 | Google Architecture Framework 六支柱评审 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 支柱清单与「先给全量标准建议、再追问」的评审协议可用；正文多为原则性论述，只取结构与可落地条目 |
| 8 | google/skills `skills/cloud/cloud-sql-basics` | https://github.com/google/skills/blob/main/skills/cloud/cloud-sql-basics/SKILL.md | 19751 | 2026-09-10 | Apache-2.0 | Cloud SQL 实例创建、Auth Proxy、版本 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 正文本身偏 quickstart；价值在 Enterprise vs Enterprise Plus 的编辑版分界与 Auth Proxy 连接方式 |
| 9 | google/skills `skills/cloud/cloud-monitoring-metric-selection` + `cloud-monitoring-promql-query` | https://github.com/google/skills/tree/main/skills/cloud | 19751 | 2026-09-10 | Apache-2.0 | 指标类型选择、MQL/PromQL、`listTimeSeries` | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 只取 Cloud Monitoring 的**产品面**（指标类型/对齐/配额/计费）；告警与 SLO 方法论归 `observability` |
| 10 | google/skills `skills/cloud/google-cloud-solution-architecture` | https://github.com/google/skills/blob/main/skills/cloud/google-cloud-solution-architecture/SKILL.md | 19751 | 2026-09-10 | Apache-2.0 | 参考架构选型与图示 | 3 | 3 | 2 | 2 | 2 | 12 | INCLUDE | 作为计算形态选型（Cloud Run / GKE / GCE / Functions）的交叉校验；其 Graphviz 图按标准第 3 节弃用 |
| 11 | google/skills `skills/cloud/cloud-build-basics` + `google-cloud-recipe-auth` | https://github.com/google/skills/tree/main/skills/cloud | 19751 | 2026-09-10 | Apache-2.0 | Cloud Build 触发器与服务账号、ADC/WIF 认证链 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | `recipe-auth` 是少见地把 ADC 查找顺序、模拟(impersonation)、WIF 讲全的官方来源 |
| 12 | gemini-cli-extensions/google-cloud-storage | https://github.com/gemini-cli-extensions/google-cloud-storage | 25 | 2026-08-31 | Apache-2.0 | GCS basics / bucket-architect / diagnostic / fuse / security-assessment | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `google-cloud-storage-diagnostic` 与 `gcs-security-assessment` 两个 skill 在 `google/skills` 里没有对应项，是本 skill GCS 排障与公开访问审计一节的来源 |
| 13 | google/agents-cli `skills/google-agents-cli-deploy` | https://github.com/google/agents-cli/blob/main/skills/google-agents-cli-deploy/SKILL.md | 5904 | 2026-09-03 | Apache-2.0 | Cloud Run / Agent Engine 部署流程 | 3 | 3 | 2 | 2 | 2 | 12 | MAYBE→reference | 部署段几乎全是 agent 产品自身的脚手架（`agents deploy`），Cloud Run 侧不超出候选 2；只作覆盖面校验，`relation: reference` |
| 14 | GoogleCloudPlatform/cloud-run-mcp `skills/cloud-run` | https://github.com/GoogleCloudPlatform/cloud-run-mcp/blob/main/skills/cloud-run/SKILL.md | 629 | 2026-09-10 | Apache-2.0 | `gcloud run` 子命令清单 | 3 | 3 | 1 | 3 | 2 | 12 | MAYBE→reference | 内容是 `gcloud run --help` 的转录（命令一览表），模型已知或一条 help 就能拿到，属标准第 3 节的 dead weight；只用来确认没漏掉 `multi-region-services`、`compose up` 这类新子命令 |
| 15 | BagelHole/DevOps-Security-Agent-Skills `infrastructure/cloud-gcp/*` + `compliance/auditing/gcp-audit-logs` | https://github.com/BagelHole/DevOps-Security-Agent-Skills | 1081 | 2026-05-22 | MIT | GKE / Cloud SQL / Cloud Functions / Compute / 网络 / 审计日志 | 1 | 1 | 2 | 2 | 2 | 8 | INCLUDE（弱） | 社区，非官方；3.7 个月未推送。内容是教程式命令清单，抽查 3 条：`--workload-pool` 写法正确、Autopilot/Standard 对比正确、但「Prerequisites: 启用 API」一节直接 `gcloud services enable` 与官方 gcloud skill 的「不得主动启用 API」冲突（见冲突表 #4）。只作覆盖面对照 |
| 16 | OptimNow/cloud-finops-skills `skills/cloud-finops` | https://github.com/OptimNow/cloud-finops-skills | 50 | 2026-09-09 | CC-BY-SA-4.0（实读 `LICENSE.md`，API 报 NOASSERTION） | 三云 FinOps 方法论、成本异常排查 | 1 | 3 | 2 | 2 | 2 | 10 | INCLUDE（结构） | 按 `docs/roadmap.md` 许可规则，CC-BY-SA-4.0 只取结构与清单语义并全部改写。贡献：成本归因（标签/项目/计费导出）的排查顺序 |
| 17 | cloud.google.com/docs（Cloud Run / IAM / Cloud SQL / Storage / Logging / GKE / Architecture Framework） | https://cloud.google.com/docs | — | 持续 | CC-BY-4.0（页脚实读，见备注） | 全部事实的最终权威 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 所有版本号、默认值、配额、计费数字以此为准；代码示例 Apache-2.0 |
| 18 | github/awesome-copilot | https://github.com/github/awesome-copilot | 38879 | 2026-09-10 | MIT | — | 3 | 3 | — | — | 2 | — | REJECT | 全树 grep `gcp|google|gke|bigquery|cloud-run` 只命中 `skills/bigquery-pipeline-audit`（BigQuery 数据管道审计，不在本 skill 范围）。无 GCP 控制面内容可取 |
| 19 | GoogleCloudPlatform/cloud-foundation-fabric `skills/*` | https://github.com/GoogleCloudPlatform/cloud-foundation-fabric | 5000+ | 2026-09 | Apache-2.0 | `fabric-builder`、`fast/prerequisites`、`contributing` | 3 | 3 | 2 | 3 | 2 | — | REJECT | 三个 skill 全是「怎么给 Fabric 这个 Terraform 模块库贡献代码」，属 `terraform` 的 HCL 面，按波次 6 边界不归本 skill |
| 20 | GoogleCloudPlatform/vertex-ai-samples `skills/vertex-*`、google/skills `skills/cloud/gemini-api`、`agent-platform-*` | https://github.com/GoogleCloudPlatform/vertex-ai-samples | 2500+ | 2026-09 | Apache-2.0 | Vertex AI / Gemini API / Agent Engine | 3 | 3 | 3 | 3 | 2 | — | REJECT（越界） | LLM 应用开发。路线图把它归 `ai-engineering`（波次 8，尚未存在）；本 skill 的 `description` 写「no skill in this library covers it yet」，不引用 |
| 21 | majiayu000/claude-skill-registry `skills/data/gcloud-expert` | https://github.com/majiayu000/claude-skill-registry | 602 | 2026-09-10 | MIT | — | — | — | — | — | — | — | REJECT | `web_search` 给出的路径在仓库树中不存在（`gh api .../git/trees/main?recursive=1` grep `gcloud|gcp` 只有 `skills/ai-ml/gcp-batch-inference` 与 llm-council 目录）。属搜索结果幻觉，留行以免下轮重查 |
| 22 | hajekim/agent-harness-gcp-skills | https://github.com/hajekim/agent-harness-gcp-skills | 1 | 2026-03-28 | MIT | GCP 杂项 | 0 | 1 | 1 | — | 2 | 4 | REJECT | 1 star、5.5 个月未推送，个人练习仓 |
| 23 | amon339/gcp-compliance-skill | https://github.com/amon339/gcp-compliance-skill | 4 | 2026-06-08 | MIT | GCP 合规检查 | 0 | 1 | 1 | — | 2 | 4 | REJECT | 4 star，合规扫描属 `security-review`（波次 7，尚未存在）范围 |
| 24 | cybercloudskills/cyber-cloud-skills | https://github.com/cybercloudskills/cyber-cloud-skills | 51 | 2026-08-21 | 无许可（API `license: null`） | 云安全 | 0 | 3 | 1 | — | 0 | 4 | REJECT | 无许可 + 云安全审计属 `security-review` 范围，与本 skill 的控制面定位不重合 |

## 深度审查

### 1. `google/skills`（Apache-2.0，19.8k★，2026-09-10）

仓库根 `LICENSE` **实读为 Apache License 2.0 全文**，不是只信 API 的 `spdx_id`。目录结构是
`skills/<domain>/<skill>/{SKILL.md,references/,scripts/,assets/}`，`skills/cloud/` 下 117 个
skill 目录。frontmatter 用 `name` + `description` + `metadata.category`，`category` 取值是
Google 自己的分类词（`CloudInfrastructureAndServices`、`Serverless`、`Databases`、
`WellArchitectedFramework`…），不在本仓库 `platform|framework|task|meta` 白名单里，合入时按
标准 1.2 剥离。

质量分布很不均匀，必须逐个挑：

- **`gcloud`（272 行）——最高价值。** 它不讲 gcloud 是什么，只讲 agent 用 gcloud 时会出事的地方：
  `gcloud help <leaf>` 的校验不可从父命令组传递；`list` 不带 `--limit/--filter/--format`
  会把上下文窗打爆；不带 `--quiet` 在无 TTY 环境里会永久挂起等确认；省略 `--region/--zone`
  会触发交互式选择提示。还有一份明确的 denylist（IAM 变更、`delete`、`billing`、
  `organizations`、`kms`、`infra-manager deployments apply`、主动 `services enable`）。
  这正是标准第 3 节要的「teach the failure, not the API」。缺点：通篇 ALL-CAPS
  `MANDATORY`/`NEVER`/`FORBIDDEN`，并且第 4 条禁止用网络搜索查 gcloud 语法——这条是
  Gemini CLI 的产品约束，不是通用工程事实，合入时改写为「以 `gcloud help` 的输出为准，
  不要凭记忆写旗标」。
- **`cloud-run-basics`（382 行）。** 覆盖 service/job/worker pool 三种资源与所需角色。写得实，
  但仍是 how-to：大段解释 Artifact Registry 与 Docker Hub 的取舍。`--tasks`/`--max-retries`
  默认 3/`--task-timeout` 默认 10 分钟上限 168 小时这些数字与本机 `gcloud run jobs create --help`
  一致，采纳。**它没有讲并发默认值、修订版本流量拆分、`--min` 与 `--min-instances` 的区别**——
  这三点是本 skill 要补的，来源改为官方文档 + 本机 help。
- **IAM 三件套。** `iam-helper-for-policy-management`（112 行）短而准：v1 allow / v2 deny 的
  二元模型、attachment point 的三种前缀、「先出计划再确认」的 mutating 协议、拒绝
  `allUsers` + 基本角色的护栏。`iam-helper-for-privileged-access-management`（312 行）是
  PAM（`gcloud pam` 授权批准）的完整流程，本 skill 只取「临时提权优于长期绑定」这一条结论。
  `iam-helper-for-troubleshooting`（66 行）是 Policy Troubleshooter 的调用壳，价值低，只取
  「排障先跑 troubleshooter 再改策略」的顺序。
- **GKE 组（27 个 skill）。** `gke-cluster-creation`（356 行）给了四套模板与
  golden-path Autopilot 的完整 `gcloud container clusters create-auto` 命令行，含
  `--enable-private-nodes --enable-master-authorized-networks --enable-dns-access
  --enable-secret-manager --scoped-rbs-bindings` 与完整 `--monitoring=` 组件列表。
  这是控制面内容，本 skill 取。`gke-upgrades`/`gke-networking` 取发布通道与 VPC-native /
  Workload Identity。**`gke-manifest-generation`、`gke-app-onboarding`、`gke-workload-*`
  一律不取**——`containers` 已经用过 `gke-app-onboarding`，且清单层归它。
- **WAF 六支柱。** 每个 skill 是一份「原则 + 相关产品 + 评估问题」的结构化提纲，正文抽象
  （"Align cloud spending with business value"）。只取结构与产品映射，原则性论述不搬。
- **`cloud-sql-basics`（122 行）。** 主体是 quickstart，`references/` 目录索引里的
  Enterprise/Enterprise Plus 分界、读池、PITR、Advanced DR 才是有用部分。注意它用
  `POSTGRES_18` 举例——本机 584.0.0 的 `--database-version` 枚举确实已包含 `POSTGRES_18`，
  与之一致。
- **`cloud-logging-query-generation`（142 行）。** 规则型，质量高：LQL 只用双引号、布尔大写、
  `gce_instance` 的 name/id 混淆、猜 `protoPayload.methodName` 时必须用 `SEARCH()` 而非
  `=`（版本前缀）也不能用 `:`（子串误命中）。全部采纳。

### 2. `gemini-cli-extensions/google-cloud-storage`（Apache-2.0，25★，2026-08-31）

五个 skill：`google-cloud-storage-basics`、`-bucket-architect`、`-diagnostic`、`-fuse`、
`gcs-security-assessment`。前两个与 `google/skills` 同名目录内容高度同源（Google 内部同一份
素材的两处发布），取任一即可，本 skill 记 `google/skills` 为主、本仓库为补。
**`-diagnostic`（265 行）与 `gcs-security-assessment`（103 行）在 `google/skills` 中没有对应项**：
前者是 403/404/延迟/一致性问题的分诊表，后者是公开访问、UBLA、PAP、CMEK 的审计清单。
这两个是本仓库被选中的真正理由。星数低（25）不影响评分——权威性看的是组织而非 star。

### 3. `BagelHole/DevOps-Security-Agent-Skills`（MIT，1081★，2026-05-22）

`infrastructure/cloud-gcp/` 下 6 个 skill（`gcp-gke`、`gcp-cloud-sql`、`gcp-cloud-functions`、
`gcp-compute`、`gcp-networking`、`terraform-gcp`）。frontmatter 规范（含 `license: MIT`），
写法是「When to Use + Prerequisites + 命令块 + 表格」，属教程式。抽查三条：Standard/Autopilot
对比表正确；`--workload-pool=${PROJECT_ID}.svc.id.goog` 写法正确；但 Prerequisites 一节把
`gcloud services enable container.googleapis.com compute.googleapis.com` 当作 agent 可以直接
执行的准备步骤，与官方 `gcloud` skill 的 denylist 冲突。定位为覆盖面对照，`relation: reference`，
不合入文字。

### 4. `OptimNow/cloud-finops-skills`（CC-BY-SA-4.0，50★，2026-09-09）

GitHub API 报 `NOASSERTION`；**实读 `LICENSE.md` 为 Creative Commons Attribution-ShareAlike
4.0 International**（"Copyright 2025–2026 OptimNow (Jean Latière)"）。按 `docs/roadmap.md`
「许可处理规则」，CC-BY-SA-4.0 = merged，但只取结构与清单语义，全部用自己的话重写。
单 skill `skills/cloud-finops`（163 行），三云通用，GCP 侧贡献的是成本归因的排查顺序
（先计费导出 → 再标签/项目维度 → 再 Recommender），不是具体数字。

### 5. `GoogleCloudPlatform/cloud-run-mcp` 与 `google/agents-cli`

两者都是官方、都活跃，但内容对本 skill 增量很小。`cloud-run-mcp/skills/cloud-run` 是
`gcloud run` 的子命令目录（109 行表格），`agents-cli` 的 deploy skill 是该 CLI 自身的部署脚手架。
均记 `relation: reference`。前者唯一的增量是提醒 `gcloud run` 现在有
`multi-region-services` 与 `compose up` 两个子命令组——已在本机 584.0.0 确认存在。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | Cloud Run 最大并发的默认值 | 社区与多数教程：固定 80。`google/skills` 的 `cloud-run-basics`：未提及。本机 `gcloud run deploy --help`：只写 "server default value"，不给数字 | **通过 gcloud CLI 或 Terraform 创建服务时默认 = 80 × vCPU 数；通过控制台创建默认 = 80；上限 1000；该默认只在服务首次创建时生效，后续部署修订版本不再套用** | 官方文档 <https://cloud.google.com/run/docs/about-concurrency> 原文。这是「更新 > 更旧」：固定 80 是旧行为，社区资料尚未跟上 |
| 2 | `--min-instances` 与 `--min` 是不是一回事 | 几乎所有社区资料只提 `--min-instances`；`cloud-run-basics` 也只用 `--min-instances` | **两者不同**：`--min-instances`/`--max-instances` 不可变地写在每个修订版本上，改它就要部署新修订；`--min`/`--max` 是服务级、在所有接流量的修订版本之间分配、可以不部署就改 | 本机 `gcloud run deploy --help`（584.0.0）逐字：`--min-instances` "This setting is immutably set on each new Revision"；`--min` "can be modified without deploying a new Revision" `[verified]` |
| 3 | 默认 Compute Engine 服务账号是否自动获得 `roles/editor` | 老资料：一律自动获得。Google 文档：取决于组织政策 | **取决于 `iam.automaticIamGrantsForDefaultServiceAccounts` 是否强制执行；2024-05-03 之后创建的组织默认已强制（即不再自动授予 Editor），更早的组织默认未强制（自动授予 Editor）** | 官方 <https://cloud.google.com/iam/docs/service-account-types> 原文。写成带日期分界的事实，而不是「通常会」 |
| 4 | agent 能否主动 `gcloud services enable` | `google/skills` 的 `gcloud` skill：明确禁止（可能触发资源置备与计费）。`cloud-run-basics` 与 BagelHole：把 `gcloud services enable` 当作第一步直接给出 | **采纳禁止方**：启用 API 需要用户批准，先假定已启用；失败后从错误信息里拿到要启用的 API 名再请求批准 | 「官方厂商 > 社区」；且两个官方来源冲突时取限制更严的那个——启用 API 的副作用不可由 agent 单方面承担 |
| 5 | Cloud SQL 实例的默认区域 | 多数资料默认写 `us-central1` | **`gcloud sql instances create` 的 `--region` 默认值是 `us-central`（旧式区域名），不是 `us-central1`** | 本机 `gcloud sql instances create --help`：`--region=REGION; default="us-central"` `[verified]`。实例区域创建后不可改，写错就得重建 |
| 6 | GCS 桶创建时是否默认开启统一桶级访问 | 控制台新建桶的向导默认勾选；社区因此常说「默认开启」 | **通过 API / `gcloud storage buckets create` 创建时默认关闭**（`--uniform-bucket-level-access ... Default is False`），必须显式指定 | 本机 `gcloud storage buckets create --help` `[verified]`。同理 `--location` 不给默认落在 `us` 多区域 |
| 7 | Cloud Logging 查询「没有结果」意味着什么 | 无 | **`gcloud logging read` 默认 `--freshness=1d`**：查一天以前的事件会静默返回空，不报错 | 本机 `gcloud logging read --help`：`[--freshness=FRESHNESS; default="1d"]` `[verified]`。这是本 skill 最便宜的一条救命规则 |
| 8 | GKE 集群不指定发布通道时落在哪 | `gke-cluster-creation`：未说明；社区：有说「无通道」的 | **不指定通道也不指定版本时进入 REGULAR 通道并启用节点自动升级；只指定版本不指定通道时，进入该版本可用的最成熟通道（先 STABLE、再 REGULAR、最后 RAPID）** | 本机 `gcloud container clusters create-auto --help` 的 `--release-channel` 说明 `[verified]` |
| 9 | IAM 改动多久生效 | 社区：「立即」 | **通常约 2 分钟，可能 7 分钟或更久**；改组成员身份的传播路径更长 | 官方 <https://cloud.google.com/iam/docs/access-change-propagation> 表格原文 |
| 10 | GCS 存储类别最短存储时长 | 社区常写 Nearline 30 / Coldline 90 / Archive 365，但常漏掉「提前删除按剩余时长计费」和新增的 Rapid 类别 | **Nearline 30 天、Coldline 90 天、Archive 365 天，提前删除或转类按剩余时长补收；另有 Rapid 存储类别（仅 Rapid Bucket 可用，单可用区，无最短时长）** | 官方 <https://cloud.google.com/storage/docs/storage-classes> 表格原文 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `gcp-docs` | cloud.google.com/docs | merged | 全部版本号、默认值、配额与计费数字的最终权威 |
| `google-skills` | google/skills `skills/cloud/{gcloud,cloud-run-basics,cloud-sql-basics,google-cloud-storage-basics,google-cloud-storage-bucket-architect,iam-helper-for-*,gke-cluster-creation,gke-upgrades,gke-networking,cloud-logging-*,cloud-monitoring-metric-selection,google-cloud-waf-*,google-cloud-solution-architecture,cloud-build-basics,google-cloud-recipe-auth}` | merged | CLI 纪律、denylist、IAM v1/v2 模型、GKE golden path、LQL 硬规则、WAF 六支柱结构 |
| `gcs-extension` | gemini-cli-extensions/google-cloud-storage `skills/{google-cloud-storage-diagnostic,gcs-security-assessment}` | merged | GCS 403/404/延迟分诊表与公开访问审计清单 |
| `optimnow-finops` | OptimNow/cloud-finops-skills `skills/cloud-finops` | merged（仅结构，CC-BY-SA-4.0 全文改写） | 成本归因排查顺序 |
| `bagelhole-devops` | BagelHole/DevOps-Security-Agent-Skills `infrastructure/cloud-gcp` | reference | 覆盖面对照，无文字合入 |
| `cloud-run-mcp` | GoogleCloudPlatform/cloud-run-mcp `skills/cloud-run` | reference | `gcloud run` 子命令面的完整性校验 |
| `google-agents-cli` | google/agents-cli `skills/google-agents-cli-deploy` | reference | Cloud Run 部署面的覆盖校验 |

## 基线缺口

无 skill（`uv run tools/run_evals.py gcp --baseline`，anthropic/claude-opus-5 · medium，
5 场景全部 `status: ok`、`skill_read: false`）时，各场景未达成的 `expected_behavior`。
判定依据是 `/tmp/hs-evals/gcp/anthropic-claude-opus-5-medium/baseline/<N>/answer.md`，
结论在此原样记录（`/tmp` 会被清理，产物不保留）。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 Cloud Run | EB1 并发默认值 | 答案把文件里的 `containerConcurrency: 80` 直接说成「这就是 Cloud Run 默认值」，没有区分 CLI/Terraform 创建时的 **80 × vCPU**（此服务 4 vCPU → 320）与控制台的固定 80，也没提 1000 上限。按它的口径，用户会以为这台 4 vCPU 的服务默认并发就是 80 |
| 1 Cloud Run | EB3 `--min`/`--max` 与 `--min-instances`/`--max-instances` | 全程只用 `--min-instances`/`--max-instances`，没有意识到服务级的 `--min`/`--max` 可以不部署新修订版就改。运维改容量被迫滚镜像 |
| 2 IAM | EB1 默认服务账号的 Editor | 说了「摘 editor」，但没给出 `iam.automaticIamGrantsForDefaultServiceAccounts` 这个约束名，也没有 2024-05-03 组织创建时间的分界——而夹具里明写组织建于 2022，正是自动授予仍然生效的那一侧 |
| 2 IAM | EB2 CI 的下载密钥 | 答案（11 行摘要）完全没提 CI 那把 2024 年下载、从未轮换的 JSON key，既没有 Workload Identity Federation，也没有 `iam.disableServiceAccountKeyCreation` |
| 2 IAM | EB4 传播延迟 | 没有任何传播延迟提示。它给的验证方式是「主动尝试违反」，改完立刻验证在 2–7 分钟窗口内会得到假阴性 |
| 3 GCS | EB4 创建期默认值 | 认出了 `location` 不可变与 UBLA 关闭，但没有说 `gcloud storage buckets create` 的 `--location` 默认落在 `us` 多区域、`--uniform-bucket-level-access` 默认 False——而它自己建议「迁到单区域桶」，新桶正会踩这两个默认 |
| 3 GCS | EB5 生命周期异步 | 不但没提「配置变更最长 24 小时生效、期间可能仍按旧配置执行」，还写下相反的结论：「生命周期动作只会**延迟**执行，所以永远落在安全侧」。把放宽规则后旧配置仍可能删对象的风险说反了 |
| 4 Cloud SQL / Logging | EB1 `--freshness` | 给了 6 条 `gcloud logging read`，全部只靠 `timestamp>=` 过滤，没有 `--freshness`。默认 `--freshness=1d` 会让这些查 4 天前的命令**静默返回空**，用户会以为日志已过期 |
| 4 Cloud SQL / Logging | EB4 `us-central` | 判成「不是合法 GCP 命名……说明这份 yaml 是手工编辑或脱敏过的」。实际上 `us-central` 是 Cloud SQL 的合法旧式区域名，且正是 `gcloud sql instances create --region` 的默认值——真实成因（用了默认区域）被当成了夹具造假 |

负例（场景 5）基线 `skill_read: false`，三条 `expected_behavior` 全部达成：只谈探针/资源/securityContext，
没有编造 GKE、Autopilot、Workload Identity、Artifact Registry 维度。基线负例通过不算缺口，
但它确认了负例查询本身不会误触发。

## 评测结果

两组均为 `anthropic/claude-opus-5` · thinking `medium`（`tools/run_evals.py` 默认，未传
`--model` / `--thinking`），5 场景全部 `status: ok`，无超时。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Cloud Run 调参与灰度 | claude-opus-5 · medium | 无（基线） | false | 3/5（EB2、EB4、EB5） | 把 80 当成固定默认；只用 revision 级伸缩旗标 |
| 1 Cloud Run 调参与灰度 | claude-opus-5 · medium | 有 | true | **5/5** | 明写「CLI/Terraform 创建默认 80 × vCPU（4 vCPU = 320），Console 才是平的 80，上限 1000，且只在创建时算一次」；并区分 `--min`/`--max`（服务级、不发版可改）与 `--min-instances`/`--max-instances`（revision 级不可变）。107 s |
| 2 IAM 审计 | claude-opus-5 · medium | 无（基线） | false | 2/5（EB3、EB5） | 11 行摘要，正文写进了 `.agent-logs`；漏掉 CI 密钥、组织策略约束名与传播延迟 |
| 2 IAM 审计 | claude-opus-5 · medium | 有 | true | **5/5** | 点名 `iam.automaticIamGrantsForDefaultServiceAccounts`，并用夹具里的「组织创建于 2022」直接推出「早于 2024-05-03 → 自动授予生效」；WIF 一节带 attribute condition 与 `repository_id` 数字 ID 的理由；「撤销绑定不是止血：IAM 变更典型 2 分钟、可达 7 分钟以上，且已签发令牌仍有效」；验证步骤标注「变更后 ≥7 分钟」。250 s |
| 3 GCS 降本 | claude-opus-5 · medium | 无（基线） | false | 3/5（EB1、EB2、EB3） | 漏掉创建期默认值；并写反了生命周期异步的方向（「只会延迟执行，所以永远落在安全侧」） |
| 3 GCS 降本 | claude-opus-5 · medium | 有 | true | 4/5（EB1、EB2、EB3、EB5） | EB5 被填补且纠正：「生命周期变更最长 24 小时生效，期间仍可能按旧配置执行」。**EB4 只部分达成**：说了 `location: US` 是 multi-region 且创建后不可变、UBLA 与 90 天可逆窗口，但没有复述 `gcloud storage buckets create` 的 `--location` 默认 `us`、`--uniform-bucket-level-access` 默认 False 这两个创建期默认。153 s |
| 4 Cloud SQL + 日志查询 | claude-opus-5 · medium | 无（基线） | false | 3/5（EB2、EB3、EB5） | 6 条 `gcloud logging read` 全无 `--freshness`，查 4 天前必然空；把 `us-central` 误判成夹具造假 |
| 4 Cloud SQL + 日志查询 | claude-opus-5 · medium | 有 | true | **5/5** | 开篇即写「`--freshness` 默认 1d，filter 里的 `timestamp>=` 不会覆盖它，会返回空、exit 0、无警告」，全部命令带 `--freshness=10d`；并把 `region: us-central` 判为「`gcloud sql instances create` 省略 `--region` 时的默认值，强烈提示没人显式选过区域，区域不可变」。127 s |
| 5 负例：K8s 清单加固 | claude-opus-5 · medium | 无（基线） | false | 3/3 | — |
| 5 负例：K8s 清单加固 | claude-opus-5 · medium | 有 | **false** | 3/3 | skill 可用但未被读取。答案只谈 startupProbe/liveness/readiness、requests/limits、`securityContext` 与配套 `emptyDir`，没有出现 gcloud、GKE、Autopilot、Workload Identity、Artifact Registry 任一维度 |

结论：**通过**。9 条基线未达成的行为中有 8 条在有 skill 时达成（场景 1 的 EB1/EB3、场景 2 的
EB1/EB2/EB4、场景 3 的 EB5、场景 4 的 EB1/EB4），其中场景 3 的 EB5 与场景 4 的 EB4 还纠正了基线
里两个方向性错误的结论。唯一未完全达成的是场景 3 的 EB4（创建期默认值只答了一半）。负例两组
`skill_read` 均为 false，`description` 末尾的 `Do not use for …` 不需要收紧。

## 备注

### cloud.google.com 文档许可的实读结论

**CC-BY-4.0（正文）+ Apache-2.0（代码示例），可以 merged，需在 `notes` 写署名。**

证据两处，都是实读而非推断：

1. 抓取一个具体文档页 `https://cloud.google.com/run/docs/deploying`，页脚原文为
   "Except as otherwise noted, the content of this page is licensed under the Creative Commons
   Attribution 4.0 License, and code samples are licensed under the Apache 2.0 License."
2. 抓取其指向的 `https://developers.google.com/site-policies`，原文为 "Google Developers
   documentation is largely licensed under Creative Commons Attribution 4.0, allowing reuse and
   modification with attribution"，并说明带上述页脚的页面「free to use nearly everything on the
   page in your own creations」，商标与品牌资产除外。

因此 `SOURCES.yaml` 的 `gcp-docs` 记 `license: CC-BY-4.0`、`relation: merged`，`notes` 写明
署名与「无逐字复制」。这与波次 5 的三个反例（redis.io/docs = CC-BY-NC-SA-4.0、
elastic 文档 = CC-BY-NC-ND-4.0、hashicorp/terraform = BUSL-1.1）不同：那三个的限制项
（NC / ND / BUSL）在本页脚里都不存在。

`google/skills` 的许可同样是实读仓库根 `LICENSE` 确认为 Apache-2.0 全文，不是只看 API 的
`spdx_id`；`OptimNow/cloud-finops-skills` 的 API `spdx_id` 是 `NOASSERTION`，实读 `LICENSE.md`
为 CC-BY-SA-4.0，按 `docs/roadmap.md` 的规则只取结构、全文改写。

### 本机验证到什么程度

装了 Google Cloud SDK **584.0.0**（core 2026.09.04，gsutil 5.37）到 `/tmp/google-cloud-sdk`，
**未认证、未创建任何计费资源**，只跑 `--help` 这类离线只读命令。因此下列事实标 `[verified]`：

- `gcloud run deploy`：`--min-instances` "immutably set on each new Revision" vs `--min`
  "can be modified without deploying a new Revision"；`--cpu-boost` "Enabled by default when
  unspecified on new services"；`--ingress` `default="all"`；`--concurrency` 帮助只说 "server
  default value"（不给数字，所以并发默认值改从官方文档取）
- `gcloud sql instances create`：`--region` `default="us-central"`、`--database-version`
  `default="MYSQL_8_0"`、`--availability-type` zonal "This is the default"、`--backup`
  "Enabled by default"、`--retained-transaction-log-days` Enterprise 默认与上限均为 7 /
  Enterprise Plus 14 与 35、枚举含 `POSTGRES_18`/`MYSQL_9_7`/`SQLSERVER_2025_*`
- `gcloud storage buckets create`：`--location` 缺省为 `us`、`--uniform-bucket-level-access`
  "Default is False"、`--soft-delete-duration` "Default is 7 days"
- `gcloud logging read`：`--freshness` `default="1d"`、`--order` `default="desc"`
- `gcloud container clusters create-auto`：`--release-channel` 的缺省推导规则（无通道无版本 →
  REGULAR；有版本无通道 → STABLE→REGULAR→RAPID）、`extended` 通道 24 个月、`--tier` 已标
  DEPRECATED
- `gcloud iam policies` 为 deny policy（v2）命令组；`gcloud quotas {info,preferences,adjuster}`
  的形态与 `--allow-quota-decrease-below-usage` 这类护栏旗标

标 `[official]` 而**未在本机验证**的（需要真实项目与计费，不做）：Cloud Run 并发默认
80 × vCPU / Console 80 / 上限 1000、请求超时 300 s / 3600 s、request-based vs instance-based
计费的行为差异、IAM 传播 2–7 分钟、`iam.automaticIamGrantsForDefaultServiceAccounts` 的
2024-05-03 分界、GCS 最短存储时长与强一致性、生命周期 24 小时窗口、Cloud Logging 各桶保留期与
$0.50/GiB 定价、Cloud Monitoring 配额表、GKE Autopilot 的 0.25 vCPU / 0.5 GiB 下限与
1:1–1:8 比例、每节点 110 Pod 与 /24、$0.10 每集群每小时与 $74.40 免费额度、
$0.50/小时扩展支持附加费。这些全部对 cloud.google.com 对应页面逐条核对过原文。

### 与其他 skill 的边界

- `containers`：GKE 只写控制面（集群与节点池创建、Autopilot vs Standard、发布通道与升级策略、
  VPC-native 与 IP 规划、Workload Identity Federation for GKE、DNS 端点与授权网络、集群计费）。
  清单、Helm、Kustomize、探针、资源限制、Pod 安全一律转交，`references/gke-control-plane.md`
  顶部一句话声明。`containers` 用过的 `gke-app-onboarding` 没有再取。
- `terraform`：本 skill 出现 IaC 时只用 Google 自己的工具（组织策略、Infrastructure Manager、
  Config Connector），HCL 一律转交。
- `observability`：OTel 埋点、Collector、语义约定、RED/USE、SLO、告警路由转交；Cloud Logging /
  Cloud Monitoring 的**产品面**（LQL、桶/接收器/视图、保留期、配额、计费）留在本 skill，
  `references/logging-monitoring.md` 顶部与 `## Scope` 两处都写明。
- `debugging`：`## Workflows` 的「Investigate a production failure from signals」结尾写
  「Where a local failure can be reproduced, use the `debugging` skill」。
- 尚不存在的主题（Firebase、Gemini / Vertex AI 应用开发）写成「No skill in this library covers
  either yet; say so rather than improvising」，不引用 `ai-engineering`。

### 未达成项

1. 场景 3 的 EB4 在有 skill 时只部分达成：答案没有复述 `gcloud storage buckets create` 的两个
   创建期默认（`--location` 落在 `us` 多区域、UBLA 默认 False）。这两条在
   `references/cloud-storage.md` 的第一张表与 SKILL.md Core rule 21 里都写着，但该场景的问题
   聚焦在「改现有桶的生命周期」，模型没有走到「新建替换桶」那一步。不改判、不粉饰。
2. 没有写 `scripts/`。考虑过一个「读 `get-iam-policy` 输出、标出基本角色 / `allUsers` /
   默认服务账号」的脚本，但它做的事 `--format` 与 `--filter` 一条命令就能做完
   （`gcloud projects get-iam-policy P --flatten=bindings --filter=...`），按标准第 5 节属于
   没有可运行价值的脚手架，故不产出。
3. `NOTICE.md` 未生成（按分工由主代理跑 `tools/build_catalog.py`）。
   `uv run tools/validate_skills.py skills/gcp` 当前输出为 1 error（`NOTICE.md is missing`）、
   0 warning，符合预期。

### 下次同步要盯的上游

- `google/skills`：`skills/cloud/` 下 117 个目录且推送频繁，`SOURCES.yaml` 的 `paths` 已列出
  实际取用的 20 个目录，靠它过滤噪声。重点盯 `gcloud`、`cloud-run-basics`、
  `iam-helper-for-policy-management`、`gke-cluster-creation`。
- Google Cloud SDK 的默认值会随版本漂移。本 skill 多条 Core rule 绑在 584.0.0 上；同步时先
  `gcloud version`，再重跑一遍 `--help` 核对 `--freshness`、`--region`、
  `--uniform-bucket-level-access`、`--cpu-boost` 四个默认。
- `gemini-cli-extensions/google-cloud-storage` 与 `google/skills` 的 GCS skill 是同源双发布。
  若上游把 `-diagnostic`/`gcs-security-assessment` 并入 `google/skills`，本 skill 的
  `gcs-extension` 条目可以合并掉。
