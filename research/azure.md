# azure 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `gh search repos "azure skills agent in:name,description"`、`"azure agent-skills"`、`"azure bicep skill claude"`、`"entra skills agent"`
  - `web_search`：`azure agent skills SKILL.md github claude`
  - 领域官方组织仓库：`microsoft/`、`Azure/`、`MicrosoftDocs/`、`github/awesome-copilot`
  - `gh api repos/<o>/<r>/git/trees/main?recursive=1` 逐个列 `skills/*/SKILL.md`，再 `contents/<path>` 读原文
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`（已登录 `gh`，账号 Lynricsy）
- 许可一律实读 `LICENSE` / `LICENSE-CODE` / `LICENSE.md` 正文，不信 API 的 `spdx_id`

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | microsoft/azure-skills `skills/*`（29 个 skill） | https://github.com/microsoft/azure-skills | 1473 | 2026-09-10 | MIT（实读 LICENSE） | prepare/validate/deploy 流水线、diagnostics、quotas、cost、reliability、kubernetes、entra-app-registration、compute、storage | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged，主干） | Microsoft 官方 agent plugin。`azure-quotas` 的「ARM 资源类型与配额资源名无 1:1 映射，必须先 `az quota list` 按 `localizedValue` 匹配」是本 skill 拿不到别处的可执行事实；`azure-prepare → azure-validate → azure-deploy` 三段式是唯一一个把 what-if 当作发布门的上游 |
| 2 | github/awesome-copilot `skills/azure-*` + `instructions/{azure-verified-modules-bicep,bicep-code-best-practices,azure-naming}` | https://github.com/github/awesome-copilot | 38879 | 2026-09-10 | MIT（仓库级；`skills/azure-role-selector/LICENSE.txt` 实读亦为 MIT/Microsoft） | AVM+Bicep 规则、CAF 命名表、azd、deployment preflight、pricing、resource-health、well-architected-review、update-avm-modules-in-bicep、entra-agent-user | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | GitHub 官方仓库，Azure 相关 11 个 skill + 3 个 instruction。`azure-naming` 的逐资源长度/字符/作用域表与 `azure-deployment-preflight` 的 what-if 变更符号表（`+ - ~ = * !`）是本 skill 命名与预检两节的骨架 |
| 3 | Azure/AKS-Skills `skills/*` | https://github.com/Azure/AKS-Skills | 4 | 2026-09-10 | MIT（实读 LICENSE，Copyright Microsoft Azure） | AKS 控制面 Day-0/Day-1 决策、Automatic readiness、成本、GPU、抓包 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | Star 数低但属 `Azure/` 官方组织。`aks-cluster-setup` 明确区分 Day-0（pod IP 模型、API server 访问，建后不可改）与 Day-1（可后开），正是本 skill AKS 一节的组织方式 |
| 4 | Azure/azure-functions-skills `templates/skills/*` | https://github.com/Azure/azure-functions-skills | 17 | 2026-09-10 | MIT（实读 LICENSE，Copyright Microsoft Corporation） | Functions create/deploy/diagnostics/best-practices/health-status/inventory | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（merged） | 官方。`azure-functions-best-practices` 的「证据先于建议、报告先于修改、改动需批准」评审契约被吸收成本 skill 的 review workflow；但正文大量依赖 MCP 工具名，事实密度低于 azure-skills |
| 5 | Azure/bicep `docs/` + 随发行版的 linter 规则集 | https://github.com/Azure/bicep | 3640 | 2026-09-11 | MIT | Bicep 语言与 linter 规则名、默认等级、`bicepconfig.json` schema | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | 本 skill 的 linter 事实全部用本机 `bicep 0.47.16` 实跑核对（见「本机实测」），不是读文档抄的 |
| 6 | Azure/Azure-Verified-Modules `docs/static/module-indexes/*.csv` + 规范页 | https://github.com/Azure/Azure-Verified-Modules | 580 | 2026-09-10 | MIT | AVM 命名/版本/所有权规范，Bicep 资源模块索引（539 行） | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | 索引 CSV 带 `ModuleStatus` 列（`Available` / `Orphaned`），"pin 到一个 Orphaned 模块"这条陷阱只有读了索引才知道 |
| 7 | Azure/bicep-registry-modules `avm/res/**` | https://github.com/Azure/bicep-registry-modules | 736 | 2026-09-10 | MIT | AVM 模块实现与 README 示例 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（reference） | 只用来核对 `br/public:avm/res/{service}/{resource}` 路径形态与版本号形式，未复制模块代码 |
| 8 | MicrosoftDocs/azure-docs | https://github.com/MicrosoftDocs/azure-docs | 10970 | 2026-09-10 | **CC-BY-4.0（实读 LICENSE 正文 = Attribution 4.0 International）** | learn.microsoft.com/azure 绝大多数文章的开源源仓库 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged，notes 写署名） | 关键裁决：learn.microsoft.com 站点条款是专有，但同样的 Azure 文章正文以 CC-BY-4.0 发布在这个仓库里。配额、RBAC 上限、Flex Consumption 规格等事实按 CC-BY-4.0 采用并署名 |
| 9 | ricmmartins/azure-sre-agent-skills `skills/01..08` | https://github.com/ricmmartins/azure-sre-agent-skills | 70 | 2026-08-24 | MIT（实读 LICENSE，Copyright Ricardo Martins） | WAF 评审、合规治理、容量规划、FinOps、事后复盘、Defender secure score | 2 | 2 | 3 | 2 | 2 | 11 | INCLUDE（merged） | 社区专家（Microsoft FTE 个人仓）。WAF 五支柱评分表与 FinOps 的「未附着磁盘 / 空闲 IP / 过大 SKU」清单可用；但为 Azure SRE Agent 平台写的，若干 prompt 结构对通用 agent 无意义，须剥离 |
| 10 | Azure/azure-dev（azd）`schemas/`、`cli/azd/docs/` | https://github.com/Azure/azure-dev | 568 | 2026-09-11 | MIT | `azure.yaml` schema、`azd` 命令面、hooks、remote environments | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（reference） | 用于核对 `azure.yaml` 字段与 `azd provision --preview`、`azd env set-secret` 等命令是否仍存在；内容取自 awesome-copilot 的 `azure-developer-cli`，此仓库只作校验 |
| 11 | learn.microsoft.com/azure（站点） | https://learn.microsoft.com/azure | — | 持续 | **Proprietary（实读 /legal/termsofuse）** | 全量 Azure 产品文档 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE（**reference**，不得 merged） | 见「冲突与裁决 #1」。站点 TOU 的 "Personal and Non-Commercial Use Limitation" 明文禁止未经书面同意的修改、分发与派生；"Notice Specific to Documents" 只在「非商业、不修改」前提下授权复制。事实从 #8 的 CC-BY-4.0 仓库取，站点只作人工比对入口 |
| 12 | MicrosoftDocs/Agent-Skills `skills/azure-*`（205 个） | https://github.com/MicrosoftDocs/Agent-Skills | 740 | 2026-09-07 | **CC-BY-4.0（LICENSE 正文实读）+ LICENSE-CODE = MIT** | 每个 Azure 服务一个 skill，内容是分类后的 Learn 文档 URL 索引 | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE（**reference**） | 由 `docs2skills/1.0.0` 生成，正文是「分类 → 标题 → Learn URL」表 + 要求 agent 用 MCP 在线抓取；没有可合入的判断与陷阱，只有覆盖面地图。用它校验服务边界写法（`Not for Azure Policy (use azure-policy)`）与权威 URL，不复制内容，故 `reference` 而非 `merged` |
| 13 | danieletten/azure-landing-zone-workload-integration | https://github.com/danieletten/azure-landing-zone-workload-integration | 5 | 2026-08-04 | MIT（实读 LICENSE） | 把工作负载接入既有企业 Landing Zone（订阅/管理组/策略继承） | 1 | 2 | 2 | 2 | 2 | 9 | INCLUDE（reference） | 单 skill、体量小，但订阅与资源组结构一节缺少「工作负载落到既有 ALZ 时应先读什么」的清单，用它做交叉校验 |
| 14 | johnlokerse/azure-bicep-github-copilot `.github/skills/*` | https://github.com/johnlokerse/azure-bicep-github-copilot | 14 | 2026-07-24 | **无 LICENSE 文件（API `license: null`，仓库内亦无）** | convert-bicep-to-avm、strong types、去重参数、format、run-bicep-in-console | 1 | 2 | 2 | 2 | 0 | 7 | MAYBE（reference） | 「把手写资源逐个换成 AVM 模块」的迁移顺序有参考价值，但无许可 + 个人仓 + 两个月未动。按许可规则可作 `license: NONE` 的 merged，此处选择更保守的 reference：其结论已被 #2、#6 官方来源覆盖，无需承担无许可风险 |
| 15 | OptimNow/cloud-finops-skills `skills/cloud-finops` | https://github.com/OptimNow/cloud-finops-skills | 50 | 2026-09-09 | **CC-BY-SA-4.0（API 报 NOASSERTION，实读 LICENSE.md 为 CC BY-SA 4.0）** | FinOps Foundation 对齐的跨云成本知识 | 1 | 3 | 2 | 2 | 2 | 10 | MAYBE（reference） | 跨云、非 Azure 专属；CC-BY-SA 的传染性对本仓库 MIT 发布是负担，且成本一节的 Azure 事实已由 #1 `azure-cost`、#9 FinOps 覆盖。只作清单交叉校验 |
| 16 | microsoft/skills | https://github.com/microsoft/skills | 3007 | 2026-09-10 | MIT | Azure SDK 用法与 Microsoft AI Foundry 的 agent 构建 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT（越界） | 官方且活跃，但内容是 SDK 说明书与 Foundry/LLM 应用开发，正好落在本 skill 明文排除的两块：语言 SDK（→ `csharp-dotnet` 等）与 LLM 应用开发（本库尚无对应 skill）。留行以免下轮重议 |
| 17 | microsoft/azure-devops-skills | https://github.com/microsoft/azure-devops-skills | 47 | 2026-07-16 | MIT | Azure DevOps Boards/Pipelines/Repos 的 MCP 用法 | 3 | 1 | 2 | 3 | 2 | 11 | REJECT（越界） | Azure DevOps 是 CI/工作项平台，不是 Azure 控制面；与 `github`（CI）职责同类，不归本 skill。分数够但范围不符 |
| 18 | Azure/amg-skills | https://github.com/Azure/amg-skills | 2 | 2026-04-17 | MIT-0（实读） | Azure Managed Grafana 巡检 | 3 | 0 | 2 | 2 | 2 | 9 | REJECT（越界 + 陈旧） | Grafana 看板与告警属 `observability` 边界；且近 5 个月未更新 |
| 19 | BagelHole/DevOps-Security-Agent-Skills（`compliance/`、`devops/` 下的 azure 子目录） | https://github.com/BagelHole/DevOps-Security-Agent-Skills | 1081 | 2026-05-22 | MIT | 80+ 跨云 DevOps/安全/合规 skill | 1 | 1 | 1 | 2 | 2 | 7 | MAYBE→不采用 | 星数高但每个 skill 都很薄，Azure 部分只有 `azure-monitor-audit`、`azure-devops` 两个，且近 4 个月未动。无 Azure 专属新增事实 |
| 20 | DanWahlin/github-azure-agentic-journeys | https://github.com/DanWahlin/github-azure-agentic-journeys | 38 | 2026-07-29 | MIT | 端到端 demo「旅程」（Container Apps 部署、n8n/Superset/Grafana on Azure） | 2 | 2 | 1 | 2 | 2 | 9 | REJECT | 是可跑的示例工程，不是规则集；`journey-*` skill 只是本仓库自身的运行器 |
| 21 | Azure/documentdb-agent-kit / AzureCosmosDB/cosmosdb-agent-kit | https://github.com/AzureCosmosDB/cosmosdb-agent-kit | 54 | 2026-09-02 | MIT | Cosmos DB 数据建模、RU、向量检索 | 3 | 3 | 3 | 3 | 2 | 14 | REJECT（越界） | 质量够，但是数据库产品用法，归数据类 skill 的范畴（本库 `mongodb` / `postgres` 已各管各的），不属本 skill 的控制面定位 |
| 22 | dragosruiu/azure-agent-skills、gardlt/azure-agent-skills、zer0big/azure-agent-skills-demo | https://github.com/dragosruiu/azure-agent-skills | 0 | 2026-05-15 起 | MIT / 无 / 无 | — | 0 | 1 | 0 | 0 | 0 | 1 | REJECT | 0 star、无内容或纯演示；`gardlt`、`zer0big` 两个无许可 |

## 深度审查

### 1. microsoft/azure-skills（主干）

29 个 skill，两份拷贝（`skills/` 与 `.github/plugins/azure-skills/skills/`，内容一致，跟踪 `skills/`）。frontmatter 是合规的 `name` / `description` / `license` / `metadata.{author,version}`，没有 agent 专属字段，唯一要剥的是正文里大量的 `mcp_azure_mcp_*` 工具名和 `> **AUTHORITATIVE GUIDANCE — MANDATORY COMPLIANCE**` 这类全大写训诫（标准第 3 节禁止满篇 ALL-CAPS）。

质量分布很不均匀：

- `azure-quotas`（277 行）是全批次密度最高的一份。核心判断「ARM 资源类型 ≠ 配额资源名，必须先 `az quota list` 再按 `localizedValue` 匹配，拿 `name` 字段去 `az quota show`」以及「REST/Portal 的 `No Limit` 不表示无限，而表示配额 API 不支持该类型」都是会直接造成事故的事实。
- `azure-diagnostics`（156 行）给出了「先查 Resource Health → 再看活动日志 → 再查日志/指标 → 最后看最近变更」的定序，本 skill 的 diagnose workflow 沿用这个次序。
- `azure-reliability`（388 行）最长，但大半是服务清单罗列。
- `azure-compute`（33 行）、`azure-cost`（46 行）近乎占位，只是转交给 MCP 工具，无可合入内容。
- `microsoft-foundry/*`、`azure-ai*`、`azure-aigateway` 属 LLM 应用开发，本 skill 明文不覆盖，整组跳过。
- `azure-kusto*` 是 KQL 图查询，与 `observability`/`elasticsearch` 更近，跳过。

与其他候选的重叠：`azure-kubernetes` 与 Azure/AKS-Skills 大面积重叠，且后者更细（见「冲突与裁决 #3」）。

### 2. github/awesome-copilot（Azure 部分）

11 个 `skills/azure-*` + 3 个 Bicep/命名 instruction。是唯一把 **Bicep 代码规范** 与 **CAF 命名规则** 写成可执行表格的上游。

- `instructions/azure-naming.instructions.md`（259 行）：逐资源的缩写 / 作用域 / 长度 / 合法字符 / 示例。含「storage account、container registry、Data Explorer cluster 不允许连字符」这条最常被 agent 写错的规则。
- `instructions/azure-verified-modules-bicep.instructions.md`（206 行）：AVM 发现、版本 pin、符号引用替代 `resourceId()`、输出不得含密钥。缺点是通篇 ✅/❌ emoji 清单（标准要求祈使 + why，需重写），且「用 `azure_get_schema_for_Bicep` 工具」是 Copilot 专属工具名，必须剥。
- `skills/azure-deployment-preflight`（217 行）：`targetScope` → `az deployment {group,sub,mg,tenant} what-if` 的映射表，以及 `--validation-level Provider` 失败时退到 `ProviderNoRbac` 的策略。what-if 变更符号表（`+` create / `-` delete / `~` modify / `=` nochange / `*` ignore / `!` deploy）直接可用。
- `skills/azure-developer-cli`（135 行）：azd 项目结构与守则，写得克制（无 emoji、祈使语气），是本批次写作质量最高的一份，几乎可以整段吸收（仍需重写为本仓库的 workflow 形态）。
- `skills/azure-role-selector` 只有 7 行正文 + 一份 MIT LICENSE.txt，全部依赖 Azure MCP 工具，无可合入内容。
- `skills/azure-pricing`（190 行）绑定 Copilot Studio 费率表，时效性差，只取「先用 Retail Prices API 查当前单价再算，不要凭记忆报价」这一条判断。
- `skills/azure-architecture-autopilot` 带 Python 脚本与 PNG 资产，是完整的架构生成器；体量与定位都超出本 skill，只借它的 `service-gotchas.md` 主题划分。

### 3. Azure/AKS-Skills

7 个 skill，`aks-cluster-setup`（155 行）质量最高。它的组织原则——**Day-0 决策（pod IP 模型、API server 访问、节点子网）建后不可改，Day-1 特性可后开**——比 microsoft/azure-skills 的 `azure-kubernetes` 更有用，因为它把「哪些错误必须重建集群才能修」单列出来。`aks-cost-optimization` 只有 22 行（占位）。`evals/holmesgpt-eval/SKILL.md` 是仓库自身的评测夹具，不是 skill。

### 4. Azure/azure-functions-skills

12 个 skill 的两份拷贝（`templates/skills/` 与 `.github/plugins/`，跟踪 `templates/skills/`）。`azure-functions-best-practices` 的价值不在事实而在**契约**：证据先于建议、报告先于改动、任何写操作需显式批准、只报设置名不报设置值。这套 review 契约被吸收进本 skill 的 `review-a-function-app` workflow 与 `## Output format`。事实层（Flex Consumption 规格、runtime 版本、extension bundle 区间）它全部推给 MCP，所以那些数字一律改从 MicrosoftDocs/azure-docs 取证。

### 5. MicrosoftDocs/Agent-Skills

205 个 `azure-*` skill，由 `docs2skills/1.0.0` 批量生成。正文结构统一：`## Category Index` 表（Troubleshooting / Best Practices / Decision Making / Limits & Quotas / Security / Configuration / Integrations）+ 每类下的「标题 → Learn URL」表，并要求 agent 通过 `mcp_microsoftdocs:microsoft_docs_fetch` 在线抓取。

结论：**覆盖面地图一流，可合入内容为零**。它没有一条独立判断——所有知识都在 URL 后面。frontmatter 还有 `compatibility: Requires network access` 与 `metadata.generated_at` / `metadata.generator`（后两个不在本仓库白名单内）。因此定为 `reference`：用它确认本 skill 的服务边界表述（`Not for Azure Policy (use azure-policy)` 这种写法）与权威文档 URL，不复制任何内容，也就不触发 CC-BY-4.0 的署名义务；仍在 `SOURCES.yaml` 的 `notes` 里写明许可，以便日后若改为 merged 时不会漏署名。

### 6. ricmmartins/azure-sre-agent-skills

8 个编号 skill，为 Azure SRE Agent 平台设计。`01-well-architected-review`（236 行）把 WAF 五支柱拆成可打分的检查项；`04-finops-intelligence`（272 行）给出「未附着托管磁盘 / 未关联公网 IP / 停止但未释放的 VM / 过大 SKU / 无预留」的浪费清单与对应 Resource Graph 查询形态。两者都值得合入，但需剥离：为 SRE Agent 写的 `proactive` 触发约定、固定的报告 JSON schema、以及对 Defender secure score API 的直接依赖。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | Microsoft Learn 的 Azure 文档能不能 `merged` | 波次 6 任务书要求实读 MS Learn 条款；roadmap 把 `learn.microsoft.com/azure` 列为 `kind: docs` | **站点 = `Proprietary` + `reference`；同样的文章正文从 `MicrosoftDocs/azure-docs`（CC-BY-4.0）取，`merged` 并署名** | 实读 <https://learn.microsoft.com/en-us/legal/termsofuse>：「Personal and Non-Commercial Use Limitation」写明未经 Microsoft 书面同意不得 modify / distribute / create derivative works；「Notice Specific to Documents」仅在「非商业 + 不修改」前提下授权复制。而 `MicrosoftDocs/azure-docs` 的 `LICENSE` 实读正文为 Attribution 4.0 International（另有 `LICENSE-CODE` = MIT）。一个仓库的许可是它自己的——文档内容在 GitHub 上是 CC-BY-4.0，在站点上受 TOU 约束 |
| 2 | MicrosoftDocs/Agent-Skills 该 merged 还是 reference | 任务书预设「merged 时在 notes 写署名」 | **reference** | 实读 3 个 skill 后确认其正文是 `docs2skills` 生成的 URL 索引，没有可改写的判断；把链接表重排成本仓库格式既无价值又会引入署名义务。许可仍记为 CC-BY-4.0（LICENSE 实读）+ LICENSE-CODE MIT，`notes` 写明「链接索引，未复制内容」 |
| 3 | AKS 默认网络模型：Azure CNI Overlay 还是 kubenet | microsoft/azure-skills `azure-kubernetes` 未给默认值；Azure/AKS-Skills 主张 Azure CNI Overlay 为默认，kubenet 仅在极端 IP 紧张时；许多社区材料仍以 kubenet 为默认 | **Azure CNI Overlay 为默认；kubenet 视为遗留并写明退役日期** | 官方文档明确 kubenet「Retires on March 31, 2028」，并要求在退役前迁移到 Azure CNI Overlay；Overlay 支持「API server 支持的最大节点数 × 每节点 250 pod」。两个官方上游中更新、更具体的一方胜出 |
| 4 | Functions 的无服务器默认托管方案 | Azure/azure-functions-skills 把结论推给 MCP；awesome-copilot 的 Functions instruction 仍以 Consumption(Y1) 为默认 | **Flex Consumption 为默认无服务器方案，Consumption 仅在必须跑 Windows 时** | 官方文档原话 "Flex Consumption is the recommended serverless hosting plan for Azure Functions"，并列出 Consumption 不支持 VNet 集成、最大 200 实例（Flex 1000）。Consumption 仍是 Windows 上唯一的无服务器选项 |
| 5 | Bicep 输出里放密钥算不算「会被 CI 拦住」 | awesome-copilot 的 AVM instruction 写「Never include secrets or keys in outputs」并把 `az bicep build` 列为 MANDATORY 验证 | **规则保留，但必须同时说明默认不会拦** | 本机实测 `bicep 0.47.16`：`outputs-should-not-contain-secrets` 默认是 Warning，`bicep build` 退出码仍为 0；只有在 `bicepconfig.json` 把该规则升到 `error` 后 `build` 才退 1。上游把「有规则」当成「有门」，是错的，正文按实测写 |
| 6 | `use-recent-api-versions` 是否默认生效 | 多份社区材料把它当作默认 lint | **默认关闭** | 本机实测：不写 `bicepconfig.json` 时，2021-04-01 的 API 版本不产生任何诊断；显式开启并设 `maxAgeInDays` 后才报「1989 days old」 |
| 7 | 服务主体 + client secret 还是工作负载身份联合（OIDC） | 多个上游示例仍用 `az ad sp create-for-rbac` 产出的 secret | **CI 一律 OIDC 联合凭据；secret 仅在联合不可用时，且必须有到期告警** | awesome-copilot `azure-developer-cli` 明确 "Use short-lived federated credentials where the provider supports them"；Azure/AKS-Skills 亦主张「Use Microsoft Entra ID everywhere. Avoid static credentials」。两个官方来源一致，社区示例更旧 |
| 8 | 成本一节写到多深 | ricmmartins FinOps skill 给出完整 FinOps 流程；awesome-copilot `azure-pricing` 带内嵌费率表 | **只写「怎么拿到当前数字」和「哪些形状是浪费」，不内嵌任何费率** | 标准第 3 节禁止时间敏感表述；费率表一定会腐化。`azure-pricing` 的 `COPILOT-STUDIO-RATES.md` 正是反例 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| microsoft-azure-skills | microsoft/azure-skills | merged | 配额发现工作流与资源名映射陷阱、诊断定序（Resource Health → 活动日志 → 日志/指标 → 变更）、prepare/validate/deploy 发布三段式、Entra 应用注册与凭据形态 |
| awesome-copilot | github/awesome-copilot | merged | CAF 命名规则表、AVM + Bicep 编写规范、what-if 预检矩阵与变更符号、azd 项目结构与守则、WAF 评审清单 |
| aks-skills | Azure/AKS-Skills | merged | AKS Day-0 与 Day-1 决策划分、节点池与可靠性默认值、Entra + Azure RBAC 集群访问 |
| azure-functions-skills | Azure/azure-functions-skills | merged | Function App 评审契约（证据先行、报告先于改动、只报设置名）与诊断分流 |
| bicep | Azure/bicep | merged | linter 规则名与默认等级、`bicepconfig.json` 规则升级语义（全部本机实测） |
| avm | Azure/Azure-Verified-Modules | merged | AVM 模块命名与版本规范、`ModuleStatus`（Available / Orphaned）这一 pin 前必查项 |
| azure-docs | MicrosoftDocs/azure-docs | merged | 配额与上限、RBAC 4000 上限、Flex Consumption 规格与区域核数配额、kubenet 退役日期等全部数字事实（CC-BY-4.0，署名 Microsoft Corporation） |
| sre-agent-skills | ricmmartins/azure-sre-agent-skills | merged | WAF 五支柱评审的可打分形态、成本浪费形状清单 |
| bicep-registry-modules | Azure/bicep-registry-modules | reference | 核对 `br/public:avm/res/...` 路径与版本形态 |
| azure-dev | Azure/azure-dev | reference | 核对 `azure.yaml` 字段与 `azd` 命令面仍然存在 |
| microsoftdocs-agent-skills | MicrosoftDocs/Agent-Skills | reference | 服务覆盖面地图与权威文档 URL；生成式链接索引，未复制内容 |
| learn-azure | learn.microsoft.com/azure | reference | 人工比对入口；站点条款专有，不得 merged |
| azure-landing-zone | danieletten/azure-landing-zone-workload-integration | reference | 交叉校验「接入既有 Landing Zone 前应确认什么」 |

## 本机实测（Phase C 事实取证）

本机**没有** `az` / `azd`，因此所有 `az ...` 命令行与需要订阅的操作一律标 `[official]`，未声称 `[verified]`。
可离线验证的部分用 **Bicep CLI 0.47.16（`bicep-linux-x64`，本机下载运行）** 实跑：

| # | 断言 | 命令 | 结果 |
|---|---|---|---|
| 1 | `secure-parameter-default`、`outputs-should-not-contain-secrets`、`no-hardcoded-env-urls`、`use-resource-symbol-reference` 默认为 Warning | `bicep build t.bicep --stdout` | 4 条 Warning，**exit 0** |
| 2 | `bicepconfig.json` 把规则升到 `error` 后构建失败 | 同上 + `analyzers.core.rules.outputs-should-not-contain-secrets.level = "error"` | 报 Error，**exit 1** |
| 3 | `use-recent-api-versions` 默认关闭 | 无 `bicepconfig.json` 时对 `2021-04-01` 无诊断；显式开启并设 `maxAgeInDays: 730` 后报 `'2021-04-01' is 1989 days old` | 确认默认关闭 |
| 4 | `bicep lint` 的退出码跟随最高诊断等级 | `bicep lint t.bicep` | 有 error 级规则时 exit 1，只有 warning 时 exit 0 |
| 5 | 角色分配的 GUID 名与 `existing` 作用域可编译 | `bicep build ra.bicep --stdout` | 生成 `"name": "[guid(resourceId(...), parameters('principalId'), variables('contributor'))]"`，exit 0 |
| 6 | 评测夹具 `main.bicep` 本身可编译 | `bicep build skills/azure/evals/files/main.bicep --stdout` | 5 条 Warning，**exit 0**——夹具成立的前提（"builds fine locally so CI passes"）为真 |
| 7 | AVM Bicep 资源模块索引含 `ModuleStatus` 列且存在 `Orphaned` 条目 | `gh api .../BicepResourceModules.csv` | 539 行，首屏即出现 `analysis-services/server ... Orphaned` |
| 8 | SKILL.md 里 16 个内置角色的定义 GUID 全部正确 | 逐个在 `MicrosoftDocs/azure-docs` 的 `articles/role-based-access-control/built-in-roles/{privileged,general,storage,security,containers,integration,monitor}.md` 里比对 | 16/16 命中且落在正确的 `## <角色名>` 小节下 |
| 9 | Service Bus 绑定的 `host.json` schema 随扩展版本变化 | 对官方绑定参考的 `extensionv5` 与 `functionsv2` 两个 tab 逐项比对 | 5.x 为扁平 `maxConcurrentCalls`（默认 16）/ `maxAutoLockRenewalDuration`（默认 `00:05:00`）；4.x 为 `messageHandlerOptions.maxConcurrentCalls` / `maxAutoRenewDuration`。夹具里「bundle `[2.*, 3.0.0)` + 扁平写法」确实会被静默忽略 |

未验证项（标 `[official]`，全部对官方文档复核过数字，但本机跑不了）：`az` / `azd` 全部命令、what-if
输出形态与变更符号、`az quota` 的实际返回、AKS 创建参数与建成后的不可变性、Function App 设置的生效行为、
Resource Health 与活动日志的实际内容、Cost Management 与 Retail Prices API 的返回。

写作期被官方文档**纠正过的初稿断言**（记录下来以免下次重犯）：Container Apps 工作负载配置文件环境的
最小子网是 `/27` 而不是 `/23`（`/23` 是遗留的 Consumption-only 环境）。已按文档改正。

## 基线缺口

无 skill（`uv run tools/run_evals.py azure --baseline`，claude-opus-5 · medium）时，各场景未达成的
`expected_behavior`。**基线很强**：场景 1/3/4 一次就命中大半，场景 2 第一轮近乎全中（零区分度）。
按 Phase B 的要求，把场景 2 与场景 3 的 `expected_behavior` 改写为**版本分界事实**与**会造成事故的判断**
后 `--only 2` / `--only 3` 重跑基线，下表按重跑后的答案判定。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 Bicep 评审 | linter 默认等级与退出码：`bicep build` 对 `outputs-should-not-contain-secrets` 只报 warning 且 exit 0，须在 `bicepconfig.json` 把规则升到 `error` 才成为 CI 门 | 基线正确识别了「输出里有密钥」，但把 CI 当成已经能拦住它 |
| 1 Bicep 评审 | `use-recent-api-versions` 默认关闭 | 基线建议升级 API 版本，却没说「为什么现在没有任何提示」 |
| 1 Bicep 评审 | Azure Verified Modules（`br/public:avm/res/...` + 精确版本 pin） | 基线全程手写 `resource` 块，完全没提 AVM |
| 2 AKS 脚本（重跑后） | AKS Automatic 是推荐的生产默认（预置 Standard 层、Node Auto Provisioning、最多 5000 节点、pod readiness SLA） | 基线整篇只在 Base SKU 上调参数 |
| 2 AKS 脚本（重跑后） | Free/Standard/Premium 的具体数字：Free 无财务背书 SLA 且建议 <10 节点；Standard 带 AZ 99.95%、不带 99.9%，最多 5000 节点 | 基线只说「free 无 SLA」，没有任何数字与节点上限 |
| 2 AKS 脚本（重跑后） | AKS 保留网段 `169.254.0.0/16`、`192.0.2.0/24`、`172.30.0.0/16`、`172.31.0.0/16`，以及由此导致 `172.16.0.0/12` 是非法 pod CIDR | 基线正确指出 CIDR 不可改，却不知道有一类网段会被直接拒绝 |
| 2 AKS 脚本（重跑后） | Premium 层必须与 `--k8s-support-plan AKSLongTermSupport` 同时设置；Azure CNI Overlay 每节点 250 pod 上限 | 基线提到版本支持窗口，但没给出延长支持的实际开法 |
| 3 RBAC 导出（重跑后） | 每订阅 4000 条角色分配的硬上限、不可提升、管理组作用域与 PIM eligible 不计入 | 基线两轮都把 `3872` 读成「这只是样本」，完全没识别出它离硬上限只剩 128 条 |
| 3 RBAC 导出（重跑后） | `Role Based Access Control Administrator` 作为 User Access Administrator 的最小权限替代 | 基线只建议把 UAA 转成 PIM eligible |
| 3 RBAC 导出（重跑后） | 用角色定义 GUID 而非显示名给出替换授权 | 基线全程只用角色名 |
| 3 RBAC 导出（重跑后） | `Key Vault Secrets User` 在 access-policy 模式的 vault 上被接受但不生效 | 基线把 RBAC/access-policy 之分当成提权路径，没指出它会让替换授权静默失效 |
| 4 Functions | Flex Consumption 是推荐的无服务器目标及其规格（仅 Linux、512/2048/4096 MB、1000 vs 200 实例、区域 250 核配额） | 基线明确选择 EP1 并把 Flex 推迟为「单独立项」，全部规格未出现 |
| 4 Functions | Flex Consumption 支持的 Node 版本是 22/24 | 基线写「Node 20/22」——Node 20 不在 Flex 支持列表内 |
| 4 Functions | 迁到 Flex 时必须删掉 `WEBSITE_RUN_FROM_PACKAGE` 与 `WEBSITE_CONTENTAZUREFILECONNECTIONSTRING` | 基线反而把「这两个设置零改动平移」当成选 EP1 的理由 |
| 5 负例 | —（按设计应无缺口） | 基线把它当成纯 Terraform 资源身份问题回答，正确 |

## 评测结果

两组均为 `anthropic/claude-opus-5` · thinking `medium`（`tools/run_evals.py` 默认，未传
`--model` / `--thinking`）。场景 2、3 的基线为改写 `expected_behavior` 后的重跑；场景 5 的
「有 skill」为收紧 `description` 末尾 `Do not use for …` 后的重跑。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Bicep 评审（9 条） | claude-opus-5 · medium | 无 | false | 6/9 | 命中命名、GUID、Owner 降权、符号引用、输出密钥、`allowBlobPublicAccess`。缺 linter 默认等级与退出码、`use-recent-api-versions` 默认关闭、AVM |
| 1 Bicep 评审（9 条） | claude-opus-5 · medium | 有 | **true** | 8/9 | 三条缺口里补上两条：开篇即「5 warnings, exit=0，CI 门禁形同虚设」，并新增 `bicepconfig.json` 把四条规则提到 `error` + 打开 `use-recent-api-versions`，还做了反证（加回 `listKeys()` 输出 → exit 1）。**AVM 仍未提及**，是唯一未填补的一条 |
| 2 AKS 脚本（10 条） | claude-opus-5 · medium | 无 | false | 6/10 | 命中 kubenet 退役、CIDR 不可改、AZ、vnet-subnet-id、B 系列、MI/ACR/`--admin`。缺 AKS Automatic、Free/Standard 具体数字与节点上限、保留网段、Premium+LTS |
| 2 AKS 脚本（10 条） | claude-opus-5 · medium | 有 | **true** | 9/10 | 逐条给出保留网段 `169.254.0.0/16`/`192.0.2.0/24`/`172.30.0.0/16`/`172.31.0.0/16` 与 `172.16.0.0/12` 为何非法；点名 AKS Automatic 为官方推荐生产默认；Free 无财务背书 SLA 且建议 <10 节点、有 AZ 99.95% / 无 AZ 99.9%；补上 `CriticalAddonsOnly` 污点与节点池命名规则。仅 Premium + `--k8s-support-plan AKSLongTermSupport` 与每节点 250 pod 未出现 |
| 3 RBAC 导出（9 条） | claude-opus-5 · medium | 无 | false | 5/9 | 命中 Owner+OIDC、`*` 自定义角色、冗余分配、PIM、Storage 管理面/数据面。**把 `3872` 读成「这只是样本」**，未识别 4000 上限 |
| 3 RBAC 导出（9 条） | claude-opus-5 · medium | 有 | **true** | 9/9 | 单列一节「容量：会变成部署故障」，写明 3872/4000 = 96.8%、上限硬且工单提不了、组分配与管理组上移是出路；给出 `f58310d9-…`、`ba92f5b4-…`、`4633458b-…` 三个 GUID；点明 `enableRbacAuthorization` 未开时角色分配「被接受但完全无效，且不报任何错」 |
| 4 Functions（9 条） | claude-opus-5 · medium | 无 | false | 6/9 | Service Bus schema 漂移这条基线自己就挖出来了（很强）。但选择 EP1、把 Flex 推为「单独立项」，Node 版本写成 20/22，且把两个死设置当作「零改动平移」的优点 |
| 4 Functions（9 条） | claude-opus-5 · medium | 有 | **true** | 8/9 | 直接定 Flex Consumption 为目标并把 `Node|18` 标为前置阻塞（Flex 只收 22/24）；删掉 `WEBSITE_RUN_FROM_PACKAGE` 与 `WEBSITE_CONTENTAZUREFILECONNECTIONSTRING`；补上区域 250 核配额与新旧应用共用 `AzureWebJobsStorage` 争抢 singleton lease 的坑。未逐一列出 512/2048/4096 MB 与 1000 vs 200 实例 |
| 5 负例 Terraform（4 条） | claude-opus-5 · medium | 无 | false | 4/4 | 纯 Terraform 资源身份回答，未漂到 Azure |
| 5 负例 Terraform（4 条） | claude-opus-5 · medium | 有 | **false** | 4/4 | 第一轮 `skill_read=true`（虽未产生 Azure 内容），收紧 `description` 的 `Do not use for Terraform, HCL or .tf files, including the azurerm provider …` 后重跑，`skill_read=false` |

结论：**通过**。五个场景里有四个存在基线未达成的行为，四个在有 skill 时全部或大部分被填补：
场景 3 从 5/9 到 9/9（4000 上限这条基线两轮都漏、有 skill 后成为独立章节），场景 2 从 6/10 到 9/10，
场景 4 从 6/9 到 8/9，场景 1 从 6/9 到 8/9。负例 `skill_read=false`。
未填补项如实记录：场景 1 的 AVM 建议、场景 2 的 Premium+LTS 与 250 pod/节点、场景 4 的 Flex 实例规格表——
这三条都写在 `SKILL.md` 与 references 里，但模型在这几次作答中没有用上，属于 skill 有内容而未被触发，不改判。

## 备注

- **许可实读结论（本波次重点）**
  - `learn.microsoft.com`：**专有**。TOU 的「Personal and Non-Commercial Use Limitation」禁止未经书面同意的 modify / copy / distribute / create derivative works；「Notice Specific to Documents」的复制授权附带「非商业 + 不得修改」两个条件，与本仓库「重写后以 MIT 发布」直接冲突。→ `relation: reference`，`license: Proprietary`。
  - `MicrosoftDocs/azure-docs`：`LICENSE` 正文为 **CC-BY-4.0**，`LICENSE-CODE` 为 MIT。同一批文章在 GitHub 上是自由的，在站点上不是。数字事实从这里取，`notes` 写署名。
  - `MicrosoftDocs/Agent-Skills`：`LICENSE` = **CC-BY-4.0**，`LICENSE-CODE` = MIT。许可上可以 merged，但内容不值得 merged（生成式链接索引），故按内容判定为 reference。
  - `johnlokerse/azure-bicep-github-copilot`：仓库内**无任何 LICENSE 文件**，API `license: null`。按规则可作 `NONE` merged，本次选更保守的 reference。
  - `OptimNow/cloud-finops-skills`：API 报 `NOASSERTION`，实读 `LICENSE.md` 为 **CC-BY-SA-4.0**（署名 OptimNow / Jean Latière）。未采用。
- **下次同步要盯的上游**：`microsoft/azure-skills`（每日在动，`skills/` 下 29 个 skill 的版本号在 frontmatter `metadata.version`）、`Azure/Azure-Verified-Modules` 的 `BicepResourceModules.csv`（模块可能从 `Available` 变 `Orphaned`）、`MicrosoftDocs/azure-docs` 中 Flex Consumption 与 AKS 网络两篇（规格与退役日期会变）。
- **放弃的方向**：Azure DevOps（属 CI 平台）、Cosmos DB 与 Azure SQL 的数据建模（属数据类 skill）、Microsoft Foundry / Azure OpenAI 的应用开发（本库尚无 `ai-engineering`，正文明说「no skill in this library covers it yet」而不是硬转交）、Azure Managed Grafana（属 `observability`）。
