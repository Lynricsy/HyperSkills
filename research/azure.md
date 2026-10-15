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

## 2026-09-29 上游同步

依据 2026-09-29 `tools/check_upstream.py` 报告。报告中 9 个 `behind` 条目里 8 个是「diff too large」，
全部按完整 `<旧 pin>..<审阅 HEAD>` 区间用本地 blobless 克隆（azure-docs 用 `--filter=tree:0`）执行
`git log --oneline` 与 `git diff --stat`，只看 `SOURCES.yaml` 中该条目的 `paths`；未用日期窗口。
同时逐条核对了所有 tracked path 在新旧两端是否存在。

| 上游 | 区间 | 命中 paths 的提交 / 文件 | 判定 | 理由 |
|---|---|---|---|---|
| microsoft-azure-skills | 6be6587 → f07c053 | 9184881（Sync plugin files #239）：25 文件 +2/−2410。`skills/azure-cost` 整体移出到 `.github/plugins/azure-cost/skills/{cost-analysis,cost-estimation,cost-governance,cost-optimization}`（独立安装的 azure-cost 插件）；`azure-prepare` 版本 1.3.3→1.3.4，路由表一行改指 `cost-estimation` | 重新裁决（路径迁移） | 旧路径在 HEAD 已不存在，tracked path 改为新位置以免下次漏报。新插件内容均以 Cost Management MCP 工具（`query_costs`、`list_benefit_utilization` 等）驱动，按原裁决剥离；其中可独立成立的判断（预算只告警不止损、预留与节省计划区分、Advisor 先行）正文 `cost-and-quotas.md` 已有，无新增合入。`notes` 记录迁移 |
| awesome-copilot | 7568a48 → 997e95a（62 提交） | 无命中；9 个 tracked path 的 blob/tree SHA 两端一致 | 未变更 | 仅 re-pin |
| azure-functions-skills | 8242319 → 56dc5ce | 73deff3（#260）：`azure-functions-deploy/SKILL.md` +20，新增部署成功后运行内部遥测采集器的一步 | 噪声 | 厂商内部遥测步骤，与评审契约无关 |
| bicep | 6cff656 → c4c04db | ceb645d9f（#20324）：`Analyzers/Linter/Common/ModuleReferenceEnumeration.cs` +66，为未来的版本约束类 linter 规则建跨文件模块引用图；未新增或改动任何规则 | 噪声 | 规则名、默认等级不变。另发现 tracked path `docs/linter-rules` 在旧 pin 与 HEAD 都不存在（#5590 已删），从 `paths` 移除；linter 规则文档在 azure-docs 条目已跟踪的 `articles/azure-resource-manager/bicep`（`linter-rule-*.md` 52 篇） |
| avm | 6142d82 → c8c5562 | f6a9eeb、4e82382、6088ee0、b58f535、0ac8225（chore: synchronize AVM module catalogs）：2 个 CSV +622/−606 | 噪声 | 列结构不变。Resource 索引 537→553 行（新增 16 个子模块，无删除）；`ModuleStatus` 取值仍为 Available/Proposed/Orphaned/Deprecated，Orphaned 20→52。改动字段以 `TelemetryIdPrefix`、`ModuleOwnersGHTeam`、负责人为主。正文唯一点名的 `avm/res/storage/storage-account` 仍为 Available，`br/public:avm/res/...:X.Y.Z` 形态不变；「pin 前确认 ModuleStatus 为 Available」规则仍成立。research 初版举作 Orphaned 例子的 `analysis-services/server` 已转为 Available（正文未引用） |
| bicep-registry-modules（reference） | ff91fab → a1d42ab | 24 个提交、1670 文件 +16321/−5219：每个模块新增 `metadata.json`、遥测前缀回填、API 版本更新；0a2689ec 退役 `ORPHANED.md` 标记改由 `metadata.json` owners 表达 | 噪声 | 仅用于核对模块路径与版本形态，二者不变（storage-account `version.json` 两端均为 0.33）。正文不依赖 `ORPHANED.md`，孤儿状态仍以索引 CSV 的 `ModuleStatus` 为准 |
| azure-dev（reference） | 57ca1f6 → 973ffa9 | 16 个提交、11 文件 +1429/−234：`schemas/v1.0/azure.yaml.json` 语义比对无属性增删（主要是 c77aa335 格式化，另 `remoteBuild` 描述改写、新增 `azure.ai.eval` host）；alpha schema 新增 `layers`；`cli/azd/docs` 为扩展框架与并发限制文档 | 噪声 | 正文点名的 `infra.provider/path/module`、`services.*.project/language/host`、`hooks` 均仍在 v1.0 schema |
| microsoftdocs-agent-skills（reference） | 90ec55f → 326540f | 326540f、1e593dd、d5ad464（docs2skills 周更）：3 个 tracked SKILL.md +32/−33，链接标题与行号区间重排 | 噪声 | 生成式链接索引，无独立判断 |
| azure-docs | 7424897 → 37c2989（审阅），pin 747fd25 | 51 个提交、124 文件 +3579/−2446。关键：**4e003115d536（#320392）把每订阅角色分配上限从 4000 改为 5000**（`role-assignments-steps.md`、`troubleshoot-limits.md`、`role-assignments-list-portal.md`；`troubleshoot-limits.md` 仍注明该上限固定、不可提升；未跟踪的 `includes/role-based-access-control/limits.md` 在 HEAD 亦为 5,000）；256e3c41c64a（PowerShell 7.6 GA）：Flex Consumption 支持栈加入 PowerShell 7.6（与 7.4 并列）；5bb7e160a50d 删除 Flex 滚动更新的 preview 提示；b9d7153f040d（部署文章重构）后 `functions-deployment-slots.md` 写明 Consumption 计划有 2 个槽（生产 + 1 个 staging）；其余为 runtime 1.x 内容退役（7bfcd897b30a）、Service Bus trigger `cardinality`（9a08b45e2841）、部署与网络文章重构等 | 更正 | 见下「正文改动」。`pin` 时 HEAD 已前进到 747fd25，补审 `37c2989..747fd25` 的 paths：无命中，保留该 pin |

其余仓库上游（aks-skills、sre-agent-skills、azure-landing-zone）为 up to date，随 `--pin` 对齐。`kind: docs`
（learn-azure）不在本次范围。

### 正文改动

- 角色分配上限 4000 → **5000**：`SKILL.md` 第 11 条与路由表、`references/entra-and-rbac.md`（小节标题、锚点、正文三处）、
  `references/cost-and-quotas.md`、`SOURCES.yaml` azure-docs `contributes`。
- `references/functions.md`：Flex Consumption 支持栈补 PowerShell 7.6；部署槽改为「Premium、Dedicated 与
  Consumption（生产外 1 个 staging 槽）」。后者在旧 pin 的文档表格里已写 Consumption 为 2，属旧有遗漏，本次文档改写时一并更正。
- 评测夹具 `evals/files/role-assignments.json` 的 `roleAssignmentsInSubscription` 3872 → 4872（保持距上限 128 条），
  场景 3 的两条 expected_behavior 同步改为 5000。
- `SOURCES.yaml`：microsoft-azure-skills 的 `skills/azure-cost` 改为 `.github/plugins/azure-cost/skills`；bicep 删去不存在的
  `docs/linter-rules`；两条 `notes` 记录原因。

### 评测结果（D2，场景 3）

模型 `workbuddy/deepseek-v4.1-flash`，thinking `max`，基线与有 skill 同模型；输出在
`/tmp/hs-evals-sync/SyncG7/azure/workbuddy-deepseek-v4.1-flash-max/{baseline,skill}/3/answer.md`。

| 场景 | 模式 | skill_read | 达成 | 说明 |
|---|---|---|---|---|
| 3 RBAC 导出（9 条） | 基线 | false | 5/9 | 把 4872 只当成「导出不全」，**未识别 5000 硬上限**；冗余分配只说冗余、未联系上限；未点名 Role Based Access Control Administrator；未给角色定义 GUID |
| 3 RBAC 导出（9 条） | 有 skill | true | 9/9 | 单列「4872/5000 固定上限、不可提额、剩 128 槽」，出路为组授权、上移管理组、删冗余；冗余 Contributor「白占配额」；给出 `ba92f5b4-…`、`4633458b-…`；Key Vault 写明需 `enableRbacAuthorization`。两处偏弱：未提 PIM eligible 不计入上限；RBAC Administrator 是在 CI 主体处点名而非 alice 处 |

结论：本次改动覆盖的行为（按 5000 读上限）基线未达成、有 skill 达成，通过。PowerShell 7.6 与部署槽两处为小事实更正，
无对应场景，未单独跑；负例场景 5 未改 description/Scope，未跑。

## 2026-09-30 上游同步（增量）

依据：在 worktree 重跑 `uv run tools/check_upstream.py azure`（2026-09-30），2 条 `behind`。按完整区间归因：blobless 克隆到
`/tmp/hs-up/<owner>__<repo>`，对 `<旧 pin>..<HEAD>` 跑 `git log --oneline -- <paths>`、`git diff --stat` 与 `git diff`。
`--pin` 后核对写入的 commit 与审阅 HEAD 一致（bicep-registry-modules bd4ef88）；repo moved、tracked paths unchanged 的
awesome-copilot（997e95a → e7c25a4）、bicep（c4c04db → cec7951）、azure-docs（747fd25 → a3dfc42）随 `--pin` 前移。
收尾重跑时上游又前进：avm 到 50ff01c（又一次目录同步，两个被跟踪的 CSV 无变更）、azure-dev 到 0755722（见下表），补审后再次 `--pin`，写入值与之一致。
learn-azure 为 manual check，本次未处理。

| 上游 | 区间 | 命中提交/文件 | 判定 | 理由 |
|---|---|---|---|---|
| avm | c8c5562 → b9a9b9d（4 提交） | b9a9b9d：`BicepPatternModules.csv` 1 行——`avm/ptn/app/function-app` 由 Proposed 改为 Available（首发 2026-09）；`BicepResourceModules.csv` 无变更 | 噪声 | 目录数据的例行同步；本 skill 取的是「固定模块前先查 ModuleStatus」的规则本身，不列举具体模块状态，正文无该模块 |
| bicep-registry-modules | a1d42ab → bd4ef88（5 提交） | 9fff5c0：`avm/res/dev-test-lab/lab/tests/e2e/max/main.test.bicep` 存储账户名改用 `uniqueString(resourceGroup.id, serviceShort)` 隔离测试夹具 | 噪声 | 上游 e2e 测试夹具命名修正，不涉及 `br/public:avm/res/...` 路径形态与版本形式 |
| azure-dev | 973ffa9 → 95a1f83（首次 pin，tracked paths unchanged）→ 0755722（1 提交） | 0755722：`cli/azd/docs/environment-variables.md` 1 行——`AGENT_DEFINITION_PATH` 改为 AI agent 运行时不再支持、定义须写在 `azure.yaml` 的 `azure.ai.agent` 服务上 | 噪声 | azd 的 AI agent 扩展变量，本 skill 排除 AI/Foundry 范围，正文不含该变量 |

未合入原因：三条均无可合入内容，正文与 references 未改，未新增评测场景、未跑评测，也不需要安装冒烟。

## 2026-10-15 上游同步

依据：主代理 2026-10-15 `check_upstream.py --json` 报告与 `/tmp/hs-attr/skills_real.json`，7 条 paths 下确有提交。归因方法：
bicep-registry-modules、azure-dev、azure-docs、microsoft-azure-skills 用主代理缓存 `/tmp/hs-attr/<owner>__<repo>`，bicep、avm、
microsoftdocs-agent-skills 用 `gh repo clone --bare --filter=blob:none` 克隆到 `/tmp/hs-up/SyncG2/`，均对 `<pinned>..<head> -- <paths>`
跑 `git log`、`git diff --stat` 与 `git diff`（microsoft-azure-skills 另加 `-w --ignore-cr-at-eol` 剔除换行符噪声）逐文件读 diff。
`--pin` 后 `pin_check.py` CLEAN（avm 又前进到 593f926，差额 1 提交未碰跟踪的 CSV）；aks-skills、azure-functions-skills、
awesome-copilot 随 `--pin` 前移。learn-azure 为 manual check，未处理。

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| microsoft-azure-skills | f07c053 → d1736f3（7 提交） | 去换行噪声后 29 文件：AKS Automatic readiness 脚本与 MCP 集成、autoscaler 不再建议 `skip-nodes-with-system-pods=false`、Spot 改为 preferred affinity 且注明 PDB 挡不住 Spot 回收、Container Apps serverless GPU、Functions 触发器/Durable 排障新文档、Ubuntu 24.04 `ssh.socket`、check-quota.sh 修注入 | 噪声 | 本 skill 无 autoscaler profile、Spot affinity、SSH 排障内容；Spot 只写「有状态不上 Spot」与上游一致；GPU 一句仍成立（节点级 GPU 调度属 AKS）；触发器排障为新内容且属其诊断深度，未合入 |
| bicep | cec7951 → 20c8e39（3 提交） | `UseRecentAzPowerShellVersionRule` 默认最低版本 11.0 → 15.0；新增 `no-conflicting-version-constraints`、`no-incompatible-entrypoint-version` 两条 bicep.version 约束规则；重排格式 | 噪声 | 本 skill 不写 deploymentScripts 的 Az 版本，也不涉及 bicep.version 约束 |
| avm | 50ff01c → c5e54a7（3 提交，pin 时至 593f926） | 两个 CSV 例行同步：named-value 拼写、若干子模块路径、SQL server 行、owner 变更；表头未变 | 噪声 | 本 skill 只引用 `avm/res/storage/storage-account`，其行未变 |
| azure-docs | a3dfc42 → cc1910c（3 提交） | 30d833a：Functions 的 Azure OpenAI 扩展 2027-04-20 退役、Preview bundle ≥4.60.0 不再包含；bb63da0：Service Bus 扩展 4.x 已于 2025-03-31 退役，其 `Microsoft.Azure.ServiceBus` 库于 2026-09-30 退役；同区间 `flex-consumption-plan.md` 补 Free Trial / Azure for Students 默认区域配额 15 核；另有 deployment script 示例版本、stack what-if 保留期、deny assignment 预览措辞 | **事实更正 2 处**，其余噪声 | Flex 配额与 Service Bus 4.x 状态是本 skill 已写的事实（Core rule 15/16、`references/functions.md`），按官方文档改正；OpenAI 扩展本 skill 不覆盖（路由到 ai-engineering）；其余条目正文未涉及 |
| bicep-registry-modules | bd4ef88 → 61dcfb4（28 提交） | 全在 `avm/res/*` 具体模块：API 版本升级（hybrid-compute、azure-stack-hci 等）、测试夹具、CI/README 生成、NSG/SQL MI/Data Factory 修复 | 噪声 | 本 skill 只取 `br/public:avm/res/...` 路径形态与版本形式，无改动；storage-account 模块未被触及 |
| azure-dev | 0755722 → 28ef16e（17 提交） | 只动 `cli/azd/docs`：扩展 SDK/契约版本、`azd exec --shell` 歧义、pipeline config 安装扩展说明、重新登录清缓存；`schemas` 未变 | 噪声 | 本 skill 的 azd 内容（azure.yaml、hooks、`pipeline config --auth-type federated`）均未被改写 |
| microsoftdocs-agent-skills | 326540f → ba74e8f（1 提交） | `azure-container-apps/SKILL.md` 描述与目录行重新生成 | 噪声 | 仅生成元数据 |

正文改动（均为事实更正，依据 MicrosoftDocs/azure-docs cc1910c）：
- Core rule 15 与 `references/functions.md`：Flex Consumption 区域配额默认 250 核（512,000 MB），Free Trial 与 Azure for Students 为
  15 核（30,720 MB）——`articles/azure-functions/flex-consumption-plan.md`。
- Core rule 16 与 `references/functions.md`：Service Bus 扩展 4.x 已退役（2025-03-31），其 `Microsoft.Azure.ServiceBus` 库 2026-09-30 退役，
  因此 bundle 不匹配的修法是换到 bundle v4 / 扩展 5.x，而不是写 4.x 形状的设置——`migrate-service-bus-version-4-version-5.md`、
  `functions-bindings-service-bus.md`。

结论：两处事实更正按官方文档改正文，无新增行为规则，未新增评测场景；未跑 D2（场景 4 已覆盖 bundle 区间这一行为，本次未重跑）。

## 2026-10-15 上游新增内容评估

候选来自 Azure/azure-functions-skills（MIT，`a747a49e45a4`）与 microsoft/azure-skills（MIT，`d1736f313f7a`）区间内新增文件。
每条要点合入前对照 Microsoft Learn 核实：
- In-process 停止支持 2026-11-10：`migrate-dotnet-to-isolated-model`（ms.date 2026-09-14）与 `dotnet-isolated-process-guide` 脚注 3 一致；
  Linux Consumption 不能跑 .NET 10（同页脚注 4）；`Azure.Functions.Sdk` 1.0.0 为项目 SDK、显式引用 Worker、Worker 最低版本
  2.50.0/2.0.0/1.16.0、只做 solution restore 会跳过扩展 post-restore hook（AZFW0108）、不要动 `obj/azure_functions.g.csproj`（AZFW0109）、
  System.Text.Json 静默忽略 `[JsonProperty]`、`FUNCTIONS_WORKER_RUNTIME` 与代码分两步发布会出现 AZFD0013 —— 均已核实。
  上游「迁模型与升 TFM 必须分两阶段」是上游自己的流程主张，MS Learn 的 .NET 10 标签页是一次完成，不采纳。
- AKS 错误码：exit 50/51/52 与 `VMExtensionError_*` 对应、52 的自定义 DNS 需条件转发 `privatelink.<region>.azmk8s.io` 到 168.63.129.16、
  `ZonalAllocationFailed` 用 `maxSurge=0` + `maxUnavailable>0`、`OverconstrainedAllocationRequest` 去掉 PPG、`LinkedAuthorizationFailed`
  授权到被链接作用域 —— 均见 learn.microsoft.com/troubleshoot/azure/azure-kubernetes/error-codes/*。
  `NodePoolMcVersionIncompatible` 官方为「节点池落后控制面超过 **2** 个 minor 或高于控制面」（评估报告写的 3 个有误，按官方）。
- AKS 升级：维护窗口不开启自动升级（`planned-maintenance`）、N-3 将掉到 N-4 时强制升到 N-2、Stopped 节点池启动时才应用、
  Automatic 固定 `stable` + `NodeImage`、节点 OS 通道改动最长 24 小时生效（`auto-upgrade-cluster`、`auto-upgrade-node-os-image`）。
- AKS GPU：`gpuProfile.driver`、`nvidia.managementMode`、`migStrategy` 创建后不可改；仅驱动（driver only）不广播 `nvidia.com/gpu`；
  删除 KAITO Workspace 需另删其 GPU 节点池（`aks-managed-gpu-nodes`、`ai-toolchain-operator` 清理一节）。

| 候选 | 结论 | 理由 |
|---|---|---|
| azure-functions-update（in-process → isolated） | 不合入 | 场景 6 基线 6/6：自行引用 MS Learn 给出截止日期、Linux Consumption 不支持 .NET 10 → Flex（无 slot）、`Azure.Functions.Sdk`、AZFW0108、`[JsonProperty]` 静默失效 |
| aks-known-issues（节点池错误码对照） | 不合入 | 场景 7 基线 5/5：按嵌套码判 exit 52、条件转发到 168.63.129.16、`maxSurge 0`/`maxUnavailable 1`、Dsv5 不支持 Ephemeral |
| aks-troubleshooting v1.2.1（自动升级证据等） | 不合入 | 场景 8 基线 4/4：通道 `none`、窗口不开启升级、24 小时、Stopped 池、Automatic 通道固定 |
| aks-gpu-inference（gpuProfile、KAITO 清理） | 不合入 | 场景 9 基线 4/4：driver-only 无 device plugin、profile 不可原地改、删 Workspace 需另删节点池 |
| **事实更正**：`aks-control-plane.md` 生产集群示例 `Standard_D4s_v5` + `--node-osdisk-type Ephemeral` | 更正 | Dsv5 页面「Ephemeral OS Disk: Not Supported」（无本地 temp 盘），该组合直接 `VMCannotFitEphemeralOSDisk`；改为 `Standard_D4ds_v5`（temp 150 GiB ≥ AKS 默认 128 GiB 门槛，Ddsv5 页面 Ephemeral Supported），并在 Node pools 一节补一句 SKU 需有足够本地盘、类型与大小按池固定（`aks/concepts-storage`） |

评测（omp + `openai/gpt-6.1-sol` medium，VM；场景 6–9 为本次新增，留作哨兵）：

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 6 Functions in-process → .NET 10 isolated | gpt-6.1-sol medium | 无 | false | EB1–EB6 全部 | 选 Flex 新应用；EB6 中 slot 部分以「Flex 无 slot / 若留 Premium 则 setting 不设 slot sticky」体现 |
| 7 三个节点池失败 | gpt-6.1-sol medium | 无 | false | EB1–EB5 全部 | npcache 建议改 Managed 或换支持 Ephemeral 的 SKU，并指出 runbook 组合错误 |
| 8 自动升级「坏了」/ Automatic 改通道 | gpt-6.1-sol medium | 无 | false | EB1–EB4 全部 | |
| 9 GPU Pending + 删 KAITO Workspace | gpt-6.1-sol medium | 无 | false | EB1–EB4 全部 | 先按 `kaito.sh/workspace` 标签确认节点池再删 |

结论：四个候选基线均已达成，均不合入；只做上述事实更正（无需评测）。SOURCES 不变（无上游内容合入）。
产物：`/tmp/hs-evals-MergeM2/azure/omp-openai-gpt-6.1-sol-medium/baseline/{6,7,8,9}`。

## 2026-10-15 文档上游复核

`learn-azure` 只是人工比对入口：正文事实取自 `azure-docs`（MicrosoftDocs/azure-docs，今日已 re-pin）。本次在渲染后的
learn.microsoft.com 页面上逐条比对那些数字是否仍与站点一致。

| 上游 id | 核对的事实 | 当前官方页面 | 结论 |
|---|---|---|---|
| learn-azure | 每订阅 5000 个角色分配、固定不可提额；每管理组 500 个 | [Troubleshoot Azure RBAC limits](https://learn.microsoft.com/en-us/azure/role-based-access-control/troubleshoot-limits) | 一致 |
| learn-azure | 每订阅 980 个资源组、部署历史 800 条、标签 50 个 | [Azure subscription and service limits](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits) | 一致 |
| learn-azure | Flex Consumption 实例 512 / 2,048 / 4,096 MB 对应 0.25 / 1 / 2 核；区域默认配额 250 核（512,000 MB），可经容量评审提额 | [Flex Consumption plan](https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-plan) | 一致 |
| learn-azure | 每个应用或用户分配托管标识最多 20 个联合身份凭据 | [Workload identity federation considerations](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-considerations) | 一致 |

4 组事实全部一致，正文未改，仅 `learn-azure` 的 `synced_at` 更新为 2026-10-15。

## 2026-10-15 上游同步（当日增量）

收尾复跑 `check_upstream` 时 azure-docs 在 pin（cc1910c）之后又前进到 caabee6（24 提交，13 个碰到 `articles/azure-functions`）。
在缓存裸仓库上 `git log/diff cc1910c..caabee6 -- <paths>` 完整区间归因：

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| azure-docs | cc1910c → caabee6 | `migration/migrate-plan-consumption-to-flex.md`、`scenario-migrate-linux-consumption-to-flex.md`、`functions-bindings-dapr*.md`、`functions-hosted-skills-reference.md` | 迁移文档两处更正；Dapr 扩展退役与 Hosted Skills 不在本 skill 范围 |

更正 `references/functions.md`「Migrating Consumption to Flex Consumption」清单（事实更正，不跑 D2）：

- 原第一条「Confirm Linux」会被读成「只有 Linux 应用能迁」。官方迁移文档（92423fc 起）已支持 Windows Consumption → Flex：Flex 跑在 Linux 上，Windows 应用须先去掉 Windows 专属依赖（Windows API、原生二进制、路径与大小写假设、证书存储、.NET Framework / Windows RID）；PowerShell managed dependencies 不受支持，模块须打包进应用根目录 `Modules`；去不掉时改选 Windows Premium。
- 新增「轮询式 Blob 触发器须改为 `source: EventGrid`，且私有化目标须先解决事件投递」：Event Grid push 投递不支持私有终结点（`articles/event-grid/consume-private-endpoints.md`），VNet 集成也不提供入站可达性。原清单同时建议 `publicNetworkAccess: Disabled`，两者叠加会让 Blob 触发静默失效，故把关闭公网访问的条目标注为「在 Event Grid 检查之后」。

`--pin` 写入 azure-docs = caabee6（等于审阅 HEAD）；另两条 awesome-copilot 等条目随 pin 前移，check 报 tracked paths unchanged。

## 2026-10-15 D2 回归

覆盖提交：fb5c0dd（上游同步：Flex 默认配额 250 核 / Free Trial 与 Azure for Students 15 核；Service Bus 扩展 4.x 及其库已退役，
bundle 不匹配改到 v4 / 扩展 5.x）、8e28959（`aks-control-plane.md` Ephemeral OS 盘机型 `Standard_D4ds_v5`；新增场景 6–9）、
f56f2ee（`functions.md` Consumption → Flex 迁移清单：Windows 应用可迁、PowerShell managed dependencies 不支持、轮询 Blob 触发改
Event Grid 且与私有化冲突）。b141cac 只动 research / SOURCES。这些更正当时未跑模型；场景 6–9 只跑过基线。

复用判定：今天没有任何有 skill 结果，全部新跑。场景 6–9 基线复用 `/tmp/hs-evals-MergeM2/azure/omp-openai-gpt-6.1-sol-medium/baseline/{6,7,8,9}`
（11:28–11:32）：四份 `result.json` 的 query 与 expected_behavior 与当前 `evals.json` 逐字一致，8e28959 加入场景后夹具与期望未再改动。

选场景：
- 场景 4（`functionapp.json`）：期望 3 含 250 核配额、期望 5 为 bundle 区间，覆盖 fb5c0dd 两处更正。
- 场景 6、7、8、9：今天新增，必选（7 直接考察 Ephemeral 机型更正；6 涉及迁往 Flex）。
- **新增场景 10**（夹具 `evals/files/flex-migration/app-inventory.md`）：没有既有场景覆盖 f56f2ee 的迁移清单更正。夹具是一个
  Windows Consumption 的 PowerShell 应用：`managedDependency`、轮询 Blob 触发、`Cert:\CurrentUser\My` 与 `D:\local\Temp`，
  目标是私有终结点 + 关闭公网访问的 Flex。
- 负例：场景 5。

运行：`uv run tools/run_evals.py azure --only N [--baseline] --out /tmp/hs-d2/D2G2`（omp + gpt-6.1-sol medium，VM），产物在
`/tmp/hs-d2/D2G2/azure/omp-openai-gpt-6.1-sol-medium/`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 4 | gpt-6.1-sol medium | 有 | True | 1✔ 2✔ 3◐ 4✔ 5✔ 6✔ 7✔ 8◐ 9✔ | 94 s。读 `functions.md`；bundle 升到 `[4.*, 5.0.0)` 载入扩展 5.x，「Do not move settings into the obsolete `messageHandlerOptions` schema … the old Service Bus SDK family is already retired」（与更正一致）；3：Linux、2048 MB 有，只写「check regional quota」，未给 250 核与 1000 / 200；8：把 `maxConcurrentCalls` 失效归因于版本不匹配，称 prefetch 0 不是原因 |
| 4 | gpt-6.1-sol medium | 无 | False | 1◐ 2◐ 3✘ 4◐ 5✔ 6✔ 7✘ 8◐ 9✔ | 67 s。首推 Elastic Premium，Flex 只作备选；未给 Flex 规格与配额；Node 24 但未说 Flex 只接受 22 / 24；未提迁 Flex 时删 `WEBSITE_RUN_FROM_PACKAGE` 等；bundle 升级正确，未提扩展 4.x 已退役 |
| 6 | gpt-6.1-sol medium | 有 | True | 1✔ 2✔ 3✔ 4✔ 5✔ 6◐ | 142 s。读 `functions.md` 并联网核对；新建 Linux Flex 应用（无 slot，需要 slot 则 Premium）；`Azure.Functions.Sdk` + Worker 2.50+；单独 `dotnet restore OrderSync.csproj`；`[JsonProperty]` 被 System.Text.Json 静默忽略；6：Flex 下改用 `functionAppConfig.runtime`，本地 settings 设 `dotnet-isolated`，未提 AZFD0013（目标无 slot，期望里的 slot 交换不适用） |
| 6 | gpt-6.1-sol medium | 无（复用） | False | 1–6 全部 | 复用 MergeM2 `baseline/6`（见上节新增内容评估） |
| 7 | gpt-6.1-sol medium | 有 | True | 1✔ 2✔ 3✔ 4✔ 5✔ | 77 s。读 `aks-control-plane.md`（今日改过的 Ephemeral 段）；npcache：`Standard_D4ds_v5` 的 150 GiB 临时盘可容 128 GiB OS 盘，或保留 D4s_v5 改 `Managed`，并要求改 runbook；npapps `maxSurge=0` / `maxUnavailable=1`；npbatch 嵌套码 exit 52、条件转发到 168.63.129.16 |
| 7 | gpt-6.1-sol medium | 无（复用） | False | 1–5 全部 | 复用 MergeM2 `baseline/7` |
| 8 | gpt-6.1-sol medium | 有 | True | 1✔ 2◐ 3✔ 4✔ | 94 s。通道 `none`、维护窗口只排期不开启；推荐 `stable`、24 小时生效；Stopped 池启动时才应用；Automatic 通道固定，需要时改用 Base SKU。2：未提维护运行为尽力而为 |
| 8 | gpt-6.1-sol medium | 无（复用） | False | 1–4 全部 | 复用 MergeM2 `baseline/8` |
| 9 | gpt-6.1-sol medium | 有 | True | 1✔ 2✔ 3✔ 4◐ | 145 s。删 Workspace 不删其节点池，按 `kaito.sh/workspace` 确认后另删；driver-only 无 device plugin；装 device plugin 修复，gpuProfile 不可原地改；4：VM 内无 Azure 登录故未执行，给出「核实后再删」的命令序列，未明确要求用户确认 |
| 9 | gpt-6.1-sol medium | 无（复用） | False | 1–4 全部 | 复用 MergeM2 `baseline/9` |
| 10（新增） | gpt-6.1-sol medium | 有 | True | 1◐ 2✔ 3✔ 4✔ | 243 s。读 `functions.md`（今日改过的迁移清单）；判 No-go：Event Grid 推送到不了私有终结点、VNet 集成不给入站，建议 Event Grid → 队列 → 队列触发；轮询 Blob 触发改 `source: EventGrid`；Az 模块打包进 `Modules/`；`Cert:\` 与 `D:\local\Temp` 改 Linux 写法。1：未提去不掉 Windows 依赖时改选 Windows Premium |
| 10（新增） | gpt-6.1-sol medium | 无 | False | 1◐ 2✔ 3✔ 4✔ | 160 s。联网后同样 No-go，结论与有 skill 一致，同样未提 Windows Premium 备选 |
| 5（负例） | gpt-6.1-sol medium | 有 | **True** | — | 76 s。首个动作即 `read skill://azure`，随后只按 Terraform `count` → `for_each` 作答。原始产物另存 `/tmp/hs-d2/D2G2-azure-skill5-run1` |
| 5（负例，复跑） | gpt-6.1-sol medium | 有 | **True** | — | 67 s。同样先 `read skill://azure`。产物 `/tmp/hs-d2/D2G2/azure/omp-openai-gpt-6.1-sol-medium/skill/5` |

（编号按 `expected_behavior` 从 1 起数。）

结论：
- 三组更正在有 skill 时无回退：场景 4 有 skill 按「扩展 4.x 已退役、升 bundle v4」作答，整体明显好于基线（基线首推 Premium、
  漏掉 Flex 事实）；场景 7 给出 `Standard_D4ds_v5` 并要求改 runbook；场景 10 有 skill 达成迁移清单三项更正。场景 6–10 基线
  也都能联网查官方文档答出，更正属消除正文错误陈述。250 核配额在场景 4 两侧都没被点名（有 skill ◐、基线 ✘）。
- **负例未通过**：场景 5（Terraform `count` 删元素导致子网重建）两次运行 `skill_read == true`。description 与 Scope 今天都未改
  （fb5c0dd 的 SKILL.md 改动只在规则 15 / 16 与版本号），这是 VM 口径下首次跑该负例暴露的既有路由歧义（2026-09 旧口径曾为此
  收紧过 description，后经本地 description 收敛改回单句）。本轮不改 description：按 `docs/workflow.md`「本地 description 维护的
  阶段映射」，需在固定正例、近似负例与保留样本上先记旧描述的路由基线再同条件对照，建议后续按该流程单独处理。

遗留：负例 5 的路由歧义（见上）；场景 4 的 250 核配额未被点名、场景 10 未提 Windows Premium 备选（两侧相同）。各场景只有 1 次运行。

## 2026-10-15 description 维护（路由）

旧：`Manages Azure architecture, Bicep deployments, identity and cloud services.`  
新：`Manages Azure architecture, Bicep deployments, identity and cloud services; not Terraform or HCL.`（97 字符）

方法：`docs/workflow.md`「本地 description 维护」。隔离 VM（omp 18.8.7 + `openai/gpt-6.1-sol` medium），每次只挂载本 skill，模型在系统提示里只看到 `name: description` 与「Matching skill → MUST read」；探针只判定是否读取 skill（`detect_skill_read`），不评答案。判定：读了=read；`agent_end` 正常结束、无 provider 错误且未读=not_read；超时未读 / 空事件流 / provider 错误=不确定，不计入。样本固定于 `/tmp/hs-desc/samples.json`：D2 失败的负例为调优负例（3 次），既有正例场景各 1 次，另写保留负例 / 保留正例各 1 条（2 次，只用于验收）。旧、新描述同模型同条件各跑一遍。约束：omp 渲染 skill 列表时把超过 100 字符的描述截断到词边界，所以新描述 ≤100 字符，否则排除限定词会被截掉；真实宿主第二次会话起看到的是 smol 模型压缩后的 ≤12 词提示，本对照只覆盖首次会话的原文路由。

| 样本 | 类型 | 内容 | 旧描述（期望结果次数） | 新描述 |
|---|---|---|---|---|
| N5 | 调优负例 | 场景 5：hub_network.tf 里删掉 subnets 变量中的 "data" 之后，plan 显示要销毁重建 mgmt 和 bastion … | 0/3 | 3/3 |
| P1 | 正例 | 场景 1：Review main.bicep before we ship it. It builds fine locally so CI pass… | 1/1 | 1/1 |
| P2 | 正例 | 场景 2：provision-aks.sh is what we were about to run for our first production… | 1/1 | 1/1 |
| HN | 保留负例 | 新写：After upgrading the azurerm provider from 3.x to 4.x, `terraform plan`… | 0/2 | 2/2 |
| HP | 保留正例 | 新写：Should our new internal API run on Azure Container Apps or App Service… | 2/2 | 2/2 |

结论：调优负例（Terraform `count`→`for_each`）0/3 → 3/3 未读，保留负例（azurerm provider 升级）0/2 → 2/2；正例与保留正例全部读取。采用新描述。
