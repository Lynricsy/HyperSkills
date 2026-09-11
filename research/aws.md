# aws 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `gh api search/repositories`：`aws skills agent SKILL.md in:name,description,readme stars:>20 pushed:>2026-03-01`
  - `gh api search/code`：`filename:SKILL.md aws iam`
  - `web_search`：`AWS agent skills SKILL.md github claude skills aws`
  - 领域官方组织仓库：`awslabs/`、`aws/`、`aws-samples/`、`github/awesome-copilot`
  - 路线图 `docs/roadmap.md` 波次 6 的种子清单
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`（已登录账号 `Lynricsy`，5000 次/小时）
- 许可核对方式：**每个 repo 都实读了 `LICENSE` 文件正文**（`gh api repos/<r>/contents/LICENSE --jq .content | base64 -d`），不只看 API 的 `spdx_id`。

### docs.aws.amazon.com 的许可（实读结论）

AWS 文档站没有 `LICENSE` 文件，许可条款写在 <https://aws.amazon.com/terms/>（AWS Site Terms，
Last Updated: June 4, 2025）的 **LICENSE AND SITE ACCESS** 一节。原文：

> The materials hosted on docs.aws.amazon.com are licensed as follows: documentation
> (e.g., user guides, developer guides, other publications) is licensed under CC-BY-SA-4.0,
> while any code therein is licensed under MIT-0.

结论：**docs.aws.amazon.com 的散文部分是 CC-BY-SA-4.0，其中的代码是 MIT-0**，不是专有。
按 `docs/roadmap.md`「许可处理规则」表，CC-BY-SA-4.0 → `relation: merged`，但**只取结构与
事实语义，全部用自己的话重写**，不复制任何句子。SOURCES.yaml 的 `license` 记为
`CC-BY-SA-4.0`，`notes` 写明代码片段部分为 MIT-0。

这条和波次 5 的教训相反方向：redis.io/docs 是 CC-BY-NC-SA-4.0（NC 不可用），elastic 文档是
CC-BY-NC-ND-4.0（NC+ND 不可用），而 AWS 文档站明确给了 SA（可用，需同样条款/署名）。
**许可必须一站一站读，不能按「大厂文档站大概都一样」推断。**

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | awslabs/agent-plugins `plugins/aws-serverless/skills/*` | https://github.com/awslabs/agent-plugins | 892 | 2026-09-10 | Apache-2.0（实读 LICENSE 正文为 Apache 2.0 全文） | Lambda / API Gateway / Step Functions / SAM+CDK 部署 / durable functions / managed instances / microVMs | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | AWS 官方 labs。`api-gateway/SKILL.md` 的 REST/HTTP/WebSocket 对比表、11 条 critical pitfalls、service-limits 表是本 skill 无服务器一节的主干；`aws-lambda/SKILL.md` 的配额表与 idempotency 规则同样可用。抽查 3 条（HTTP API 30s 硬超时、REST 29s 可提、Lambda 900s/6MB）全部对上官方 quota 页 |
| 2 | awslabs/agent-plugins `plugins/deploy-on-aws/skills/*`、`plugins/databases-on-aws/skills/dsql` | 同上 | 892 | 2026-09-10 | Apache-2.0 | 部署服务选型（Beanstalk / ECS / Lambda / Amplify）、架构图、Aurora DSQL | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | `deploy` 是一个薄路由 skill（67 行），价值在「按工作负载形态选托管服务」的判据；`dsql` 299 行，是 DSQL 乐观并发控制与 DPU 计量的唯一权威二手来源 |
| 3 | aws/agent-toolkit-for-aws `skills/core-skills/*` | https://github.com/aws/agent-toolkit-for-aws | 2582 | 2026-09-10 | Apache-2.0（实读 LICENSE 正文为 Apache 2.0 全文） | IAM / CloudFormation / CDK / 计费 / 容器 / 数据库 / 网络 / 安全 / 可观测 / SDK | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | AWS 官方（`aws/` 组织本身）。`aws-iam` 的 "Verified Edge Cases" 一节（ForAllValues 空集真、PassRole 提权、资源策略绕过 boundary、角色链 1 小时上限）与 `aws-cdk` 的 deadly embrace / 逻辑 ID 替换 / hotswap 与 express 的区别，是本 skill 的 IAM 与部署两节主干。注意同一批 skill 在 `plugins/aws-core/skills/` 下有一份镜像，取 `skills/core-skills/` 这份 |
| 4 | aws-samples/sample-well-architected-skills-and-steering | https://github.com/aws-samples/sample-well-architected-skills-and-steering | 258 | 2026-08-27 | MIT-0（实读 LICENSE 正文为 "MIT No Attribution"） | Well-Architected 六支柱 review、成本/可靠性/运维卓越 playbook、agentic-AI lens | 3 | 2 | 2 | 3 | 2 | 12 | INCLUDE | AWS 官方 sample。结构是 `powers/<name>/POWER.md` + `steering/references/lenses/<lens>/<QID>.md`（每个 WA 问题一个文件），不是标准 skill 布局；价值在把六支柱拆成可勾选问题，本 skill 的 `well-architected.md` 取其问题分组语义，不取文件结构 |
| 5 | github/awesome-copilot `skills/aws-*` | https://github.com/github/awesome-copilot | 38879 | 2026-09-10 | MIT | WA review、成本优化、CloudWatch 调查、资源健康诊断、资源查询、CDK Python | 2 | 3 | 2 | 2 | 2 | 11 | INCLUDE | GitHub 官方仓库但内容社区贡献。6 个 `skills/aws-*` 都是 workflow 型（步骤 + AWS CLI 命令 + 生成 GitHub issue），CLI 调用具体可用；但把「生成 GitHub issue」写死在流程里，属于 agent 绑定，合入时必须剥离。`aws-cloudwatch-investigation`(333 行) 是 CloudWatch 产品面（Logs Insights 查询语法、指标维度）最细的一份 |
| 6 | aws-samples/sample-agent-skills-for-builders | https://github.com/aws-samples/sample-agent-skills-for-builders | 47 | 2026-08-27 | Apache-2.0 | API Gateway authorizer 安全、AgentCore、负责任 AI 评估 | 3 | 2 | 2 | 3 | 2 | 12 | INCLUDE | AWS 官方 sample，标准 skill 布局（`skills/<name>/SKILL.md` + `references/`）。本 skill 只取 `api-gateway-authorizer-security`（authorizer 缓存键与 IAM policy 格式的陷阱）；其余是 Bedrock AgentCore，按边界契约属于本库尚未覆盖的主题，不取 |
| 7 | docs.aws.amazon.com | https://docs.aws.amazon.com/ | — | 持续 | CC-BY-SA-4.0（散文）/ MIT-0（代码），见上节实读结论 | 全部服务的配额、API、定价、Well-Architected | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 所有数字（Lambda 配额、API Gateway 超时、CloudFormation `DescribeEvents` 的 `EventFilter`）都以此为准，上游 skill 与它冲突时以它为准 |
| 8 | itsmostafa/aws-agent-skills | https://github.com/itsmostafa/aws-agent-skills | 1153 | 2026-09-07 | MIT（实读 LICENSE 为标准 MIT） | 18 个服务各一个 skill：iam / lambda / s3 / dynamodb / ec2 / ecs / eks / rds / vpc / cloudformation / cloudwatch / cognito / eventbridge / api-gateway / sqs / sns / bedrock / stepfunctions | 1 | 3 | 1 | 2 | 2 | 9 | MAYBE → reference | 星标高但内容是教程式服务说明书（"Core Concepts / Common Patterns / CLI Reference"），几乎每条都是模型已知的常识，正好违反本仓库标准第 3 节「不重复模型已知的常识」。只作覆盖面清单与 CLI 子命令名的交叉校验，`relation: reference` |
| 9 | zxkane/aws-skills | https://github.com/zxkane/aws-skills | 361 | 2026-06-15 | MIT（实读 LICENSE，Copyright (c) 2025 Mengxin Zhu） | CDK/SST 开发、serverless EDA、成本运维、Bedrock AgentCore、MCP 配置 | 1 | 1 | 2 | 2 | 2 | 8 | MAYBE → reference | 推送 2026-06-15，已近 3 个月。内容重心在 AgentCore（本库无对应 skill）与 SST（第三方框架），与本 skill 的控制面定位交集小。`aws-cost-operations` 的巡检清单可用作交叉校验，`relation: reference` |
| 10 | whchoi98/aws-skills-for-claude-code | https://github.com/whchoi98/aws-skills-for-claude-code | 20 | 2026-04-06 | NOASSERTION（实读：仓库无 LICENSE 文件，README 未声明） | aws-iam / aws-vpc / aws-eks 等 | 1 | 1 | 1 | — | 0 | ≤4 | REJECT | 20★、5 个月未推送、无许可文件、内容为韩语混英的命令速查。新鲜度与具体性都不达标，许可 0 分 |
| 11 | TerminalSkills/skills `cloud-cli/aws-cli` | https://github.com/TerminalSkills/skills | 148 | 2026-09-04 | Apache-2.0 | AWS CLI 子命令速查 | 1 | 3 | 1 | 2 | 2 | 9 | MAYBE → 不取 | 是「CLI 手册的压缩版」，本仓库标准明确排除这类内容（`aws --help` 就能给出同样信息）。不作为上游 |
| 12 | boisenoise/skills-collections `skills/aws-{ec2,eks,iam}` | https://github.com/boisenoise/skills-collections | 9 | 2026-09-10 | NOASSERTION | 三个 AWS 服务 skill | 0 | 3 | 1 | — | 0 | ≤4 | REJECT | 9★ 个人聚合仓，无许可声明，内容为其他仓库的再打包 |
| 13 | thimslugga/agent-skills `codex/aws-iam` | https://github.com/thimslugga/agent-skills | 0 | 2026-08-12 | MIT | aws-iam | 0 | 2 | 1 | — | 2 | ≤4 | REJECT | 0★ 个人仓，无外部采纳信号 |
| 14 | ordiy/aws-cli-skills | https://github.com/ordiy/aws-cli-skills | 0 | 2026-03-16 | Apache-2.0 | aws-iam 等 CLI skill | 0 | 1 | 1 | — | 2 | ≤4 | REJECT | 0★、半年未动 |
| 15 | akjalbani/aws-agentic-skill | https://github.com/akjalbani/aws-agentic-skill | 1 | 2026-06-08 | 无（API `license: null`） | aws-iam | 0 | 1 | 1 | — | 0 | ≤4 | REJECT | 1★、无许可 |
| 16 | wshobson/agents | https://github.com/wshobson/agents | 39558 | 2026-09-07 | MIT | 仅 `plugins/cloud-infrastructure/skills/terraform-module-library/references/aws-modules.md` | 2 | 3 | 1 | — | 2 | ≤5 | REJECT（本 skill） | 39.5k★ 但整仓只有一份 AWS 内容，且是 Terraform 模块清单——按边界契约归 `terraform`，不归本 skill |
| 17 | awslabs/mcp | https://github.com/awslabs/mcp | 9681 | 2026-09-10 | Apache-2.0 | AWS MCP server 实现 | 3 | 3 | 3 | 3 | 2 | 14 | 不取（范围外） | AWS 官方，质量高，但它是 MCP server 的源码而非 skill 内容；按边界契约 MCP server 开发属本库尚未覆盖的主题。仅用于确认 `aws-serverless-mcp-server` 等工具名的拼写 |
| 18 | aws-powertools/powertools-lambda-python | https://github.com/aws-powertools/powertools-lambda-python | 3285 | 2026-09-09 | MIT-0 | Lambda 幂等、批处理、结构化日志、参数 | 3 | 3 | 3 | 3 | 2 | 14 | 不取（重叠） | 官方且高质量，但它是一个库的文档；本 skill 只需要「用 Powertools Idempotency 而不是自己写去重」这一条判据，该判据已由候选 1 提供。埋点细节按边界契约归 `observability` |

INCLUDE 7 项（#1–#7，其中 #1/#2 同一仓库合为一个 upstream id），MAYBE→reference 2 项（#8、#9），
REJECT 5 项，范围外 4 项。合计 18 行，满足下限 12。

## 深度审查

### aws/agent-toolkit-for-aws（总分 14，主干之一）

- **结构**：两套并行目录——`skills/core-skills/<name>/SKILL.md`（23 个）与
  `plugins/aws-core/skills/<name>/SKILL.md`（同名镜像）。两份内容一致，`skills/` 是给
  `npx skills add` 用的扁平入口，`plugins/` 是给 Claude Code plugin marketplace 用的。
  跟踪 `skills/core-skills/`。
- **frontmatter**：只有 `name`、`description`、`metadata.version`（值是 `"1"`/`"2"` 这种序号，
  不是日期）。`aws-containers` 还带 `allowed-tools: Read`。合入时 `metadata.version` 必须
  改成本仓库的日期版本，`allowed-tools` 不带过来。
- **质量**：`aws-iam/SKILL.md` 只有 110 行，但几乎每行都是「模型会答错的那一条」——
  `ForAllValues` 对缺失键求值为真、`iam:PassRole` + 计算服务创建 API 的提权组合、
  Redshift Serverless 信任策略要同时写两个 service principal、角色链最长 1 小时。
  这正是本仓库标准第 3 节要的写法，可以近乎逐条对应地重写。
  `aws-cdk/SKILL.md` 的 "Critical Warnings" 四条（deadly embrace、construct id 改名导致替换、
  `UPDATE_ROLLBACK_FAILED`、非空 S3 桶 destroy 后残留）同理。
- **agent 绑定**：很重。`aws-cloudformation` 和 `aws-containers` 都有一整节
  "Guardrail — where this skill's own files live (MCP vs local install)"，讲的是通过 AWS MCP
  的 `retrieve_skill` 工具加载时引用文件不在磁盘上——这是 AWS 自家 MCP 的实现细节，
  与本仓库无关，**整节删除**。`call_aws`、`aws___read_documentation`、`retrieve_skill`
  等 MCP 工具名，以及 `Metadata.AWSToolsMetrics.AWSAgentToolkit` 归因标记（要求在用户模板里
  写入 AWS 的埋点键）也一并删除——后者尤其不能带进来，那是替 AWS 在用户基础设施里打标记。
- **重叠**：`aws-serverless`（67 行）与候选 1 的 `aws-lambda`（172 行）主题重叠，后者细得多，
  取后者。`aws-observability` 与本库 `observability` skill 重叠，按边界契约只取 CloudWatch
  产品面（配额、计费），埋点内容不取。

### awslabs/agent-plugins（总分 14，主干之一）

- **结构**：`plugins/<plugin>/skills/<skill>/SKILL.md` + `references/*.md`，另有
  `.mcp.json`、`hooks/hooks.json`、`scripts/validate-template.sh`。`aws-serverless` 一个 plugin
  下就有 6 个 skill（lambda / api-gateway / step-functions / serverless-deployment /
  durable-functions / managed-instances / microvms）。
- **frontmatter**：`name` + `description` + `argument-hint`（Claude Code 专属，必须剥离），
  部分带 `metadata.tags`（不在本仓库白名单，剥离）。
- **质量**：`api-gateway/SKILL.md` 206 行是这批里最强的一份——REST/HTTP/WebSocket 三列对比表
  把「选错 API 类型等于重写」这件事讲清楚了，11 条 critical pitfalls 每条都是事故来源
  （边缘优化端点不在边缘缓存、`/ping` 是保留路径、413 是唯一不能自定义的 gateway response、
  REST API 改配置后必须重新 deploy）。`aws-lambda/SKILL.md` 的配额表与官方 quota 页逐条核对
  后发现**一处已过期**：它写「Function timeout 900 seconds」而官方页现在写
  900 秒、但 Lambda Managed Instances 的异步与 ESM 调用可达 5,400 秒（90 分钟）。裁决见下。
- **agent 绑定**：极重。每个 skill 都有 "MCP Server Unavailable → 告诉用户 'AWS Serverless MCP
  not responding' 并停止" 的错误分支，以及 "IaC framework selection / Language selection：
  未指定时 ALWAYS use CDK / ALWAYS use TypeScript" 的硬性默认。前者删除；后者作为**判据**
  保留但改写成有理由的选型建议，不写成 ALWAYS。
- **重叠**：`aws-serverless-deployment` 与候选 3 的 `aws-cdk` 在 CDK 最佳实践上重叠；
  前者偏项目脚手架，后者偏故障与重构，两者互补，各取一半。

### aws-samples/sample-well-architected-skills-and-steering（总分 12）

- **结构**：不是 skill 仓库，是「一套 steering 文档 + 14 个工具的适配器」。真正的内容在
  `powers/aws-well-architected-framework-review/steering/references/lenses/<lens>/<QID>.md`，
  每个 WA 问题（`SEC01`、`COST03`、`AGENTOPS01` …）一个文件。`adapters/` 下是
  Claude Code / Cursor / Copilot / Gemini 等各自的包装，对本仓库无用。
- **质量**：把六支柱拆成带编号的问题是有价值的，但单个问题文件多是 WA 官方问题的转述。
  本 skill 取「问题分组」与「每个支柱最容易出事的那几条」，不取逐问题清单——
  照抄 WA 全量问题会变成一份 400 行的勾选表，属于本仓库标准第 3 节说的「空话」。
- **许可**：MIT-0（MIT No Attribution），实读确认正文是 "Permission is hereby granted…
  to deal in the Software without restriction… " 且**没有**保留版权声明的条件。可 merged。

### github/awesome-copilot `skills/aws-*`（总分 11）

- 6 个 skill 全部是 workflow 型：`## Prerequisites` → `### Step N` → 每步给 AWS CLI 命令。
- `aws-cloudwatch-investigation`（333 行）是 CloudWatch 产品面最细的一份：Logs Insights 查询
  语法、`aws logs start-query` 的轮询模式、指标维度组合。这一份是本 skill `cloudwatch.md` 的主干。
- `aws-cost-optimize`（194 行）的资源发现命令序列（`describe-nat-gateways`、
  `describe-db-instances` 等）可直接用，但每个 skill 都以「创建 GitHub issue / EPIC issue」
  收尾，这是 agent 绑定，剥离。
- `aws-well-architected-review`（184 行）的六支柱勾选表比 aws-samples 那份更紧凑，
  两份交叉后取并集里「能落到具体资源属性」的条目。

### aws-samples/sample-agent-skills-for-builders（总分 12）

- 标准 skill 布局，有 `.github/workflows/validate-skills.yml` 和 `skill-security-scan.yml`，
  说明维护方对 skill 质量有 CI 约束。
- 26 个 skill 里绝大多数是 Bedrock AgentCore（runtime / gateway / browser / memory /
  identity / code-interpreter）。按边界契约，LLM 应用开发本库尚无 skill，不取。
- 只取 `api-gateway-authorizer-security`：Lambda authorizer 的缓存键默认是整个 identity
  source、TOKEN 型 authorizer 返回的 IAM policy 会被按缓存键复用到不同资源上——这两条是
  真实的越权来源，候选 1 的 `references/authentication.md` 没写到这个粒度。

### itsmostafa/aws-agent-skills（总分 9，降为 reference）

- 18 个服务 skill，每个都是 `## Core Concepts` / `## Common Patterns` / `## CLI Reference` /
  `## Best Practices` / `## Troubleshooting` 的模板化结构，frontmatter 带非标准字段
  `last_updated` 与 `doc_source`。
- 抽查 `iam/SKILL.md`：前 70 行讲「什么是 principal / policy / role / trust relationship」，
  然后给一段创建 Lambda 服务角色的 CLI。这些是模型已经会的东西，写进本 skill 是纯浪费 token。
- 因此定 `relation: reference`：用它的 18 个服务名核对本 skill 的覆盖面有没有漏，
  不合入任何内容。

### zxkane/aws-skills（总分 8，降为 reference）

- 推送停在 2026-06-15，新鲜度只有 1 分。6 个 skill 中 `aws-agentic-ai`（AgentCore）与
  `aws-sst-development`（SST 框架）在本 skill 范围外，`aws-mcp-setup` 是产品配置说明书。
- `aws-cost-operations` 与 `aws-cdk-development` 有交叉校验价值，但两者的内容都被候选 1、3
  覆盖且更新。定 `relation: reference`。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | Lambda 函数最大超时 | awslabs `aws-lambda`：900 秒（15 分钟），无例外 | 官方文档：默认 900 秒；**使用 Lambda Managed Instances 的函数，异步调用与事件源映射调用（Amazon MQ、DocumentDB 除外）最大 5,400 秒（90 分钟）**。正文写 900 秒并标注 LMI 例外 | 官方 <https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html>；「更新 > 更旧」，且本地 `cfn-lint 1.56.3` 的错误信息 E3717 也印证了这个分界（"greater than the maximum of 900 for functions without 'CapacityProviderConfig' (Lambda Managed Instances)"） |
| 2 | REST API 集成超时能不能提到 300 秒 | awslabs `api-gateway`：「50ms-29s（Regional/Private 可提到 300s）」，多处把 300s 写成确定上限 | 官方配额页只写「Regional 与 private API 的集成超时**可提**（edge-optimized 不可提）」，并加注「提到 29 秒以上**可能需要相应降低账号的 Region 级节流配额**」，**没有**给出 300 秒这个上限 | 官方 <https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-execution-service-limits-table.html>。正文只写「可提、edge-optimized 不可提、代价是节流配额」，不写具体上限数字——写一个官方没承诺的数字会让人按它做架构决策 |
| 3 | 查失败栈事件用哪个 API | itsmostafa / 多数社区 skill：`aws cloudformation describe-stack-events`；AWS 官方 toolkit：必须用 `describe-events --filters FailedEvents=true`，且明确说 `describe-stack-events` 不支持 `--filters` | 采用官方 toolkit 的说法。已核对 CloudFormation API 参考：`DescribeEvents` 存在，接受 `Filters`（`EventFilter` 对象，唯一字段 `FailedEvents: Boolean`），按 operation id 分组，并返回 early-validation 与 Hook 失败事件；`DescribeStackEvents` 的请求参数里没有任何过滤字段 | <https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_DescribeEvents.html>、`API_EventFilter.html`。「官方厂商 > 社区」且可直接验证 |
| 4 | 默认 IaC 框架 | awslabs 全系列：未指定时 **ALWAYS use CDK + TypeScript**；aws/agent-toolkit `aws-cloudformation`：简单工作负载（<50 资源）或团队无 CDK 经验时推荐 CloudFormation | 正文写成有判据的选型而不是 ALWAYS：纯 Lambda+API+表的无服务器应用用 SAM，需要跨栈抽象/多环境合成/单元测试的用 CDK，团队已有 YAML 资产或需要交给非开发者读的用 CloudFormation；需要 Terraform 时转交 `terraform` skill | 两家官方口径不一致，说明「默认 CDK」是产品倾向而非工程结论；本仓库标准第 3 节要求「只给一个默认方案 + 一个逃生口」，而这里的默认取决于工作负载形态，所以给判据表 |
| 5 | Express 模式与 hotswap 是不是一回事 | awslabs `aws-cloudformation`：明确要求回答 CDK+Express 问题时必须讲清区别；部分社区内容把两者混为「快速部署」 | 采用官方区分：Express 走完整 CloudFormation、无 drift、但默认关闭回滚且失败后**不能回滚只能向前修**；`--hotswap` 绕过 CloudFormation 直接调服务 API、**故意制造 drift**、且对不可 hotswap 的资源静默跳过仍报成功。两者都禁止用于生产 | aws/agent-toolkit `aws-cdk` 与 `aws-cloudformation` 两份官方 skill 口径一致，且 `aws-cdk` 给出了 `--revert-drift` 的恢复路径 |
| 6 | AWS App Runner 还能不能推荐 | 多数社区 skill 仍把 App Runner 列为「最简单的容器托管」 | 不推荐。官方 `aws-containers` skill 写明 App Runner 自 2026-04-30 起 sunset——不接受新客户、不再有新功能，存量客户迁往 ECS Express Mode | aws/agent-toolkit `aws-containers`（官方）+ AWS 文档 App Runner Availability Change 页。「更新 > 更旧」 |
| 7 | 权限边界能不能兜住 `iam:PassRole` 提权 | 常见直觉：挂了 boundary 就安全 | 不能。boundary 只做交集不做授予；且官方明确：**同账号内以 IAM 用户/角色 ARN 作 `Principal` 的资源型策略不受该主体权限边界限制**。评测场景 1 把这条做成了断言 | aws/agent-toolkit `aws-iam` "Policy Evaluation" 条目 + IAM 用户指南权限边界评估逻辑页 |
| 8 | `ForAllValues` 条件运算符 | 社区常写成「限制只能用这几个 tag key」 | `ForAllValues:*` 对**缺失或为空的键求值为真**（空集上的全称量化为真），所以不带任何 tag 的请求也能通过。必须在同一个 `Condition` 块里对**同一个上下文键**加 `Null: {"<key>": "false"}` | aws/agent-toolkit `aws-iam`（官方）给出了完整 JSON 示例；IAM 用户指南多值上下文键页同义 |
| 9 | CloudWatch 归谁 | 本波次 `observability` skill 也覆盖指标与告警 | 按边界契约：OTel 埋点、Collector、语义约定、RED/USE、告警与 SLO 方法论归 `observability`；CloudWatch 自身的配额、计费维度（自定义指标按条计费、Logs 默认永不过期）、Logs Insights 查询语法、控制台流程归本 skill。两边 SKILL.md 都写这条 | `docs/roadmap.md` 波次 6 契约 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `awslabs-agent-plugins` | awslabs/agent-plugins（Apache-2.0）@ `9898ddc…` | merged | 无服务器主干：Lambda 配额与幂等规则、API Gateway 三种类型的选型表与 11 条陷阱、Step Functions Standard/Express 语义与 JSONata 迁移、SAM/CDK 部署实践、按工作负载选托管服务的判据 |
| `aws-agent-toolkit` | aws/agent-toolkit-for-aws（Apache-2.0）@ `1c0dfd4…` | merged | IAM 边缘行为（策略评估、PassRole、条件运算符、STS/Organizations）、CloudFormation 校验三层与 `describe-events`、CDK deadly embrace 与逻辑 ID 替换、成本 API 陷阱、EKS/ECS 控制面与 App Runner sunset |
| `aws-wa-samples` | aws-samples/sample-well-architected-skills-and-steering（MIT-0）@ `276eccf…` | merged | Well-Architected 六支柱的问题分组与每个支柱的高频失分点，落成本 skill 的权衡表 |
| `aws-builder-samples` | aws-samples/sample-agent-skills-for-builders（Apache-2.0）@ `b4d5595…` | merged | API Gateway Lambda authorizer 的缓存键与策略复用越权 |
| `awesome-copilot-aws` | github/awesome-copilot（MIT）@ `7568a48…` | merged | CloudWatch 调查流程与 Logs Insights 用法、成本资源发现命令序列、WA review 勾选项 |
| `aws-docs` | docs.aws.amazon.com（CC-BY-SA-4.0 散文 / MIT-0 代码） | merged | 全部数字与 API 事实的最终依据：Lambda 配额、API Gateway 超时与节流、CloudFormation `DescribeEvents`/`EventFilter`、IAM 策略评估逻辑、定价维度 |
| `itsmostafa-aws` | itsmostafa/aws-agent-skills（MIT）@ `4ab904a…` | reference | 18 个服务名用于核对覆盖面；内容教程化，未合入 |
| `zxkane-aws` | zxkane/aws-skills（MIT）@ `68530c6…` | reference | 成本巡检清单与 CDK 实践的交叉校验；重心在 AgentCore/SST，范围外，未合入 |

## 基线缺口

无 skill（`uv run tools/run_evals.py aws --baseline`，Claude Opus 5 · medium）时，各场景未达成的
`expected_behavior`：

基线运行时间 2026-09-11，5 个场景全部 `status: ok`、`skill_read: false`（`--baseline` 传
`--no-skills`，所以基线的 `skill_read` 恒为 false，不作为负例的判据）。逐条判定：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 IAM 策略评审 | `ForAllValues:StringEquals` 对缺失键为真（空集全称量化），必须在同一 `Condition` 里对同一上下文键加 `Null: "false"` | 基线把 `ForAllValues` + `aws:TagKeys` 解释成「只限键不限值」，并据此讲了一个 ABAC 改 tag 值的攻击。方向对但不是这条：它完全没有意识到**不带任何 tag 的请求直接通过**，也没给出 `Null` 修补 |
| 1 IAM 策略评审 | 同账号内以 IAM 用户/角色 ARN 作 `Principal` 的资源型策略不受该主体权限边界限制 | 基线正确指出 boundary 是黑名单写法且挡不住 PassRole，但对 `_artifact_bucket_policy` 授权给 `user/ci-bot` 只讲了「静态密钥 + 供应链注入」，没有点出这条策略绕过 `ci-bot` 自己的权限边界 |
| 2 SAM 模板 | REST 与 HTTP 超时的确切分界：HTTP API 30s 不可提；REST 29s 默认，**只有 Regional 与 private 可提、edge-optimized 不可提**，且提升可能要以 Region 级节流配额为代价 | 基线只写了「HTTP API 集成超时硬上限 ~30s」，用了约等号，且完全没提 REST 侧的可提/不可提分界。用户若据此改用 REST edge-optimized，会踩到同一堵墙 |
| 2 SAM 模板 | `AWSLambda_FullAccess` 本身在能 PassRole 的函数上是提权路径 | 基线把两个 `*FullAccess` 归到「顺手的安全债」并换成最小权限，正确但没说明为什么这一个比另一个危险 |
| 3 栈恢复 | 用 `aws cloudformation describe-events --filters FailedEvents=true`；`describe-stack-events` 不支持过滤且不返回 early-validation 与 Hook 失败事件 | **明确未达成**：基线的「阶段 1：取真实状态」第一条命令就是 `aws cloudformation describe-stack-events --stack-name $SN --output json`，并把它当成拿到完整事件的手段。这是本批次最干净的一个缺口 |
| 4 成本 | 用脚本而不是散文做算术，并说明成本数据上的模型心算不可信 | 未达成：基线全程在正文里做乘法（`620M × 0.18s × 1.7275GB ≈ 192.8M GB-s`、`$0.428/hr × 730 × 38`），没有落成任何可复跑的脚本 |
| 4 成本 | Cost Explorer `--time-period` 的 End 是**排他**的，`End=2026-08-31` 少算 8 月 31 日 | 未达成：基线接受了输入里的 `"End": "2026-08-31"` 并按整月推算，完全没有质疑窗口 |
| 4 成本 | AWS Budgets 的 API 只在 `us-east-1` 应答 | 未达成：基线建议开 Budgets 与 Cost Anomaly Detection，但没有这条区域约束 |
| 4 成本 | 交付形态 | 基线把全部内容写进 `.agent-logs/0001-*.md`，最终回答只有 3 行指路。评测抓取的最终文本本身不含任何方案；本表按它实际产出的日志文件判定，并把这一点记在备注 |
| 5 负例（Terraform） | — | 基线（无 skill）完整用 Terraform 语汇作答：`for_each`、9 个 `moved` 块、`cidrsubnet` 的 netnum 保序、`terraform validate` 通过。这正是期望行为，缺口只可能出现在「有 skill」那一轮是否误读本 skill |

达成的部分同样记录，避免下轮重复造同样的场景：场景 1 的 PassRole 提权路径、两处 confused
deputy、`secretsmanager:*`；场景 2 的 95 秒同步调用必须离开请求路径、可见性超时 < 函数超时
导致重复投递、明文 Stripe 密钥；场景 3 的 logical ID 改名即替换、deadly embrace、
`UPDATE_ROLLBACK_FAILED` 恢复、SCP 属环境级且被拒主体是 `cfn-exec-role`；场景 4 的
NAT→gateway endpoint、CloudWatch 基数、arm64/gp3、按可逆性排序——基线在没有 skill 时都答出来了。
**基线很强，缺口集中在「具体哪一条 API / 哪一个分界数字」这类必须查证才能答对的事实上**，这也
正是本仓库标准第 3 节说的「teach the failure, not the API」应该覆盖的部分。

## 评测结果

两轮都用 `tools/run_evals.py` 的默认模型与思考档（`anthropic/claude-opus-5` · `medium`），
5 个场景全部 `status: ok`，无超时。判定方式：逐条读 `answer.md`（场景 3 与基线场景 4 的正文
写进了 `.agent-logs/`，按其实际产出的文件判定），严格计分——一条 `expected_behavior` 里
有并列子句时，缺一句即记未达成。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 IAM 策略评审 | claude-opus-5:medium | 无（基线） | false | 6/8：PassRole 提权链、`iam:PassedToService` 收敛、boundary 是黑名单、两处 confused deputy、`secretsmanager:*`、`simulate-custom-policy` | 缺 `ForAllValues` 空集真值 + `Null` 守卫；缺「资源型策略以同账号 IAM 主体为 Principal 时不受其权限边界限制」 |
| 1 IAM 策略评审 | claude-opus-5:medium | 有 | **true** | **8/8** | 两条缺口都补上：「对空集的全称量化恒真，缺 `"Null": {"aws:TagKeys": "false"}` 守卫」与「资源策略把同账号主体写成 Principal 时，该主体的权限边界不适用 —— 所以只看身份策略会低估实际权限」。验证门也从只有 `simulate-custom-policy` 扩成 `simulate-custom-policy --permissions-boundary-policy-input-list` + `accessanalyzer validate-policy` |
| 2 SAM 模板 504 + 重复扣款 | claude-opus-5:medium | 无（基线） | false | 6/8：95s 必须离开请求路径、可见性超时 < 函数超时、幂等表、DLQ + `ReportBatchItemFailures`、明文密钥、最小权限 | 超时只写「HTTP API 硬上限 ~30s」，没有 REST 侧 29s 可提/edge-optimized 不可提的分界；`AWSLambda_FullAccess` 只当成一般安全债 |
| 2 SAM 模板 504 + 重复扣款 | claude-opus-5:medium | 有 | **true** | **8/8** | 写出「API Gateway v2 集成超时硬上限 30 秒，不可调（REST API 才有 29s 可调，且仅 Regional/private）」；并复述了本 skill 实测过的 cfn-lint 覆盖面：「cfn-lint 不会校验 `AWS::Serverless::Function` 的超时越界，原模板同样能 lint 通过」——这是 skill 里 `[verified]` 那张表直接起作用的地方 |
| 3 栈卡死恢复 | claude-opus-5:medium | 无（基线） | false | 7/8：改名即替换、级联噪音、deadly embrace、`continue-update-rollback`、SCP 属环境级、被拒主体是 `cfn-exec-role`、`overrideLogicalId` | **用错 API**：恢复序列第一步就是 `aws cloudformation describe-stack-events ... --output json`，并把它当作「取完整事件」的手段 |
| 3 栈卡死恢复 | claude-opus-5:medium | 有 | **true** | **8/8** | 明确写了「工具误用：作业用的是 `describe-stack-events`，该 API 无 filter 参数且从不返回早期校验失败与 Hook 失败 —— 序列第 1 步要求改用 `describe-events --filters FailedEvents=true` 重取」。另外补了基线没有的 `aws-cdk-lib/assertions` 断言 logical id 的 CI 护栏 |
| 4 成本降 30% | claude-opus-5:medium | 无（基线） | false | 4/8：NAT→gateway endpoint、CloudWatch 基数 + EMF + 保留期、arm64 与 gp3、按可逆性排序且承诺放最后 | 全程散文心算；未发现 `End=2026-08-31` 排他；Budgets 无 `us-east-1` 约束；1,769 MB 只说「降内存同时降 CPU」，没点出它正好是 1 vCPU 分界。最终回答仅 3 行指向 `.agent-logs` |
| 4 成本降 30% | claude-opus-5:medium | 有 | **true** | **6/8** | 两条关键缺口补上：用 `eval` 跑 Python 算基线与各波节省（事件流可见 `cost baseline + savings model` 这段代码），并直接指出「Cost Explorer 的 end 是排他的，8/31 整天没算进去，真实 8 月约 $43,215，30% 目标是 $12,964 而不是 $12,546」。还额外用 skill 里的 EKS 扩展支持事实反推出「$1,520 ÷ 8 = $190/集群/月，标准控制面 $73、扩展支持 $438 → 有集群已掉进扩展支持计费，且默认开启、到期自动升级」。仍未达成：Budgets API 只在 `us-east-1` 应答；1,769 MB = 1 vCPU 分界 |
| 5 负例（Terraform `count`→`for_each`） | claude-opus-5:medium | 无（基线） | false | 3/3 | `--no-skills` 下的对照，说明这道题本身就应该用 Terraform 语汇作答 |
| 5 负例（Terraform `count`→`for_each`） | claude-opus-5:medium | 有（`skills: []`） | **false** ✅ | **3/3** | 本 skill **未被读取**，回答全程在 Terraform 语汇内：state 地址、9 个 `moved` 块、`cidrsubnet` netnum 保序、splat 对 map 失效、`terraform plan` 零变更作为验收门，没有滑向 AWS VPC 架构或 AWS CLI。`description` 末尾的 `Do not use for Terraform HCL (use the `terraform` skill)` 生效，无需收紧后重跑 |

结论：**达成**。基线未达成而有 skill 时达成的行为共 **6 条**，分布在 4 个正例场景里：

1. 场景 1 —— `ForAllValues` 对缺失键为真，必须加同键 `Null` 守卫。
2. 场景 1 —— 同账号资源型策略以 IAM 主体为 `Principal` 时不受其权限边界限制。
3. 场景 2 —— HTTP API 30s 不可提 / REST 29s 仅 Regional 与 private 可提的确切分界。
4. 场景 3 —— 必须用 `describe-events --filters FailedEvents=true`，`describe-stack-events` 不支持过滤。
5. 场景 4 —— 成本算术必须落成可复跑的脚本。
6. 场景 4 —— Cost Explorer `--time-period` 的 End 排他，直接改变了目标金额。

负例 `skill_read == false`，无需收紧 `description` 重跑。

## 备注

### 许可

- **docs.aws.amazon.com = CC-BY-SA-4.0（散文）+ MIT-0（代码）**，出处是 AWS Site Terms 的
  LICENSE AND SITE ACCESS 一节（实读原文见本文件开头）。按仓库规则以 `merged` 合入，但只取
  结构与事实，全部自己重写。下次同步时要重读这一段——它是写在一个会改版的条款页里，不是
  一个受版本控制的 LICENSE 文件。
- 五个 repo 上游的 LICENSE 正文都实读过：两个 Apache-2.0 全文、一个 MIT No Attribution、
  两个标准 MIT。MIT-0（aws-samples/sample-well-architected-skills-and-steering）确认**没有**
  保留版权声明的条件。
- 合入时剥离的 agent 绑定，逐项记在 `SOURCES.yaml` 的 `notes` 里，其中一条值得单独点名：
  aws/agent-toolkit-for-aws 的 `aws-cloudformation` skill 要求 agent 在用户的每个模板里写入
  `Metadata.AWSToolsMetrics.AWSAgentToolkit` 归因标记。那是替上游在用户基础设施里打埋点，
  **不能带进来**。

### 本机实测与未验证项

本机**没有** `aws` CLI、没有 `sam`、没有 `cdk`，也没有任何 AWS 凭据，所以
`aws iam simulate-principal-policy`、`aws cloudformation validate-template`、`sam validate`、
`cdk synth` 这些原计划的验证都**没有执行**。skill 正文里凡是依赖这些命令的断言一律标
`[official]` 并给出官方文档依据，不冒充实测。

实际跑通并标 `[verified]` 的只有 `cfn-lint 1.56.3`（`uv tool install cfn-lint`，纯 Python，
离线）：

| 输入 | 结果 |
|---|---|
| `AWS::S3::Bucket` 的 `BucketNam` 拼写错误 | `E3002 ... Did you mean 'BucketName'?` |
| `AWS::Lambda::Function` `Timeout: 901` | `E3717 901 is greater than the maximum of 900 for functions without 'CapacityProviderConfig' (Lambda Managed Instances)` |
| `AWS::Serverless::Function` `Timeout: 901` | **无告警** |
| `AWS::Lambda::Function` `MemorySize: 12000`（上限 10,240） | **无告警** |
| `evals/files/orders-api-template.yaml`（HTTP API 30s 与 `Timeout: 300` 冲突、可见性超时 30s < 消费者 120s） | **exit 0，零告警** |

最后一行是这次调研最有用的副产品：夹具本身是一个能通过全部静态检查的错误模板，所以
「cfn-lint 通过」只能说明 schema 合法。这条写进了 SKILL.md 的 `## Environment` 与
`references/deployment.md`，并在评测里被有 skill 的那一轮复述出来。

另外用官方文档实读复核、写进正文的关键数字：Lambda 900s 与 Lambda Managed Instances 的
5,400s 例外、1,769 MB = 1 vCPU、6 MB/1 MB/200 MB 三种负载上限、控制面 API 合计 15 rps；
HTTP API 30s 不可提与 REST 29s 的可提范围及其节流配额代价；CloudFormation `DescribeEvents`
的 `EventFilter.FailedEvents`；VPC 网关端点无附加费用；EKS 标准支持 14 个月 + 扩展支持
12 个月、默认开启、到期自动升级、就地升级 7 天可回滚；EKS Pod Identity 与 IRSA 的差异。

### 下轮同步要盯的上游

- `awslabs/agent-plugins` 与 `aws/agent-toolkit-for-aws` 都是每天在动的活跃仓库，
  `check_upstream.py` 的 `paths` 已经收窄到实际参考的 skill 目录，噪音可控。
- `aws/agent-toolkit-for-aws` 同一批 skill 在 `skills/core-skills/` 与 `plugins/aws-core/skills/`
  下各有一份。本次跟踪前者；若上游哪天只更新其中一份，`check_upstream` 会漏报，需要人工确认。
- App Runner 的 sunset（2026-04-30）与 ECS Express Mode 的替代关系，值得在下次同步时确认
  官方页面是否还在。

### 放弃的方向

- **Bedrock / AgentCore**：aws-samples/sample-agent-skills-for-builders 与 zxkane/aws-skills
  的大半内容都在这里，质量也不差，但按波次 6 的边界契约，LLM 应用开发本库尚无 skill，
  写进 `aws` 会越界。SKILL.md 的 `## Scope` 明确写「no skill in this library covers it yet」。
- **`aws-cli` 速查型上游**（TerminalSkills/skills 等）：`aws <service> help` 就能给出同样内容，
  收录等于用 token 复述手册。
- **逐条抄 Well-Architected 问题清单**：aws-samples 那份把六支柱拆成一个问题一个文件，
  照搬会得到一份 400 行的勾选表。`references/well-architected.md` 改成「每个支柱真正逼出的
  决策 + 跨支柱权衡表 + 一份四行 ADR 模板」，这是对基线唯一可能有增量的形态。
