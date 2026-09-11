# elasticsearch 调研记录

单一权威上游改写

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `gh api search/repositories`：`elasticsearch skill SKILL.md`、`elasticsearch agent skills`、
    `elasticsearch claude skill`、`opensearch agent skills`
  - `gh api search/code`：`filename:SKILL.md elasticsearch mapping`（40 条命中，逐条判断）
  - 领域官方组织仓库：`elastic/`（agent-skills、docs-content、elasticsearch、rally）、
    `opensearch-project/`、`vespa-engine/`
  - `github/awesome-copilot`（`skills/` 与 `instructions/` 全树 grep `elastic|search|lucene|opensearch`）
  - 社区聚合：`majiayu000/claude-skill-registry`、`TerminalSkills/skills`、`clawic/skills`、
    `khalilbenaz/claude-skills-collection`、`dkbnull/hello-skill`、`wshobson/agents`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` = Logged in to github.com account Lynricsy，全程登录态）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | elastic/agent-skills `plugins/elasticsearch/skills/*`（index-design、query-optimization、search-relevance、esql、cluster-health、ingest、reindex） | https://github.com/elastic/agent-skills | 575 | 2026-09-10 | Apache-2.0 | ES 索引设计 / 查询优化 / 相关性 / ES\|QL / 集群健康 / 摄取 / reindex | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged，主干） | Elastic 官方唯一的 agent skill 仓库，7 个 ES 子技能全部是「先取证再改」的可执行流程，含 profile / _analyze / _explain 的判据。仓库自身 LICENSE 是 Apache-2.0，与 Elasticsearch 产品的三重许可无关 |
| 2 | elastic/docs-content（elastic.co/docs 的源仓库） | https://github.com/elastic/docs-content | 47 | 2026-09-10 | **CC-BY-NC-ND-4.0**（API 报 NOASSERTION，实读 LICENSE 首行 `Attribution-NonCommercial-NoDerivatives 4.0 International`） | ES 9.x 全部官方文档 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE（**reference**） | 每条事实的最终裁决依据，但 ND（NoDerivatives）+ NC 条款禁止改写再分发，因此不得 merged。只做事实核对，不复制任何句子 |
| 3 | elastic/elasticsearch（产品本体） | https://github.com/elastic/elasticsearch | 77902 | 2026-09-10 | NOASSERTION → 实读为 **AGPL-3.0 / Elastic Licence 2.0 / SSPL-1.0 三重** | 版本与 release notes | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE（**reference**） | 只用 `releases` 与分支列表确认当前主版本 9.5.3 / 8.19.21。三重许可里没有一条是本仓库可 merged 的许可 |
| 4 | clawic/skills `skills/elasticsearch` | https://github.com/clawic/skills | 17 | 2026-07-27 | MIT | 症状导向的 ES 全栈（mapping / 查询 / 分片 / 堆 / 错误串 / 事故） | 1 | 2 | 3 | 3 | 2 | 11 | INCLUDE（merged） | 唯一一个第三方上游达到「陷阱清单」密度：错误字符串→成因表、分片与堆算术、搜索分诊七步、输出门。需剥离 Clawic/OpenClaw 的 `configPaths`、`requires`、`config.yaml` 绑定 |
| 5 | opensearch-project/opensearch-agent-skills `skills/opensearch-skills/search/opensearch-launchpad/*` | https://github.com/opensearch-project/opensearch-agent-skills | 52 | 2026-09-02 | Apache-2.0 | 检索方法选型（BM25 / dense / sparse / hybrid）与离线相关性评测 | 2 | 3 | 3 | 2 | 2 | 12 | INCLUDE（merged，仅取跨厂商语义） | 跨厂商第三方。检索方法的成本/精度对照与「先建判定集再调参」的评测纪律是引擎无关的；但 `neural` query、ml-commons、connector 等 API 只存在于 OpenSearch，一律不取，ES 侧写法全部重新取证 |
| 6 | elastic/rally `skills/running-benchmarks` | https://github.com/elastic/rally | 2029 | 2026-09-05 | Apache-2.0 | ES 基准测试方法学 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（merged，一节） | 官方压测框架自带的 skill。取「负载生成器与被测集群同机会互相扰动」「benchmark-only 拿不到主机级指标，只能当方向性数据」两条方法学约束 |
| 7 | vespa-engine/skills `elasticsearch-migration` | https://github.com/vespa-engine/skills | 15 | 2026-09-03 | Apache-2.0 | ES→Vespa 迁移的概念映射表 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE（**reference**） | 用它那张 ES 概念清单（mapping / analyzer / nested / dense_vector+kNN / ingest pipeline / reindex / alias）反查本 skill 的覆盖面漏洞。正文面向 Vespa，无可合入内容 |
| 8 | face0b1101/elasticsearch-skill | https://github.com/face0b1101/elasticsearch-skill | 1 | 2026-06-15 | CC-BY-4.0 | curl + REST 的 ES/Kibana 操作手册 | 0 | 1 | 2 | 2 | 2 | 7 | MAYBE（reference） | davidgeorgehope 那份的活跃分支，自述 "Tested against Elastic Stack 9.3.1"。只用来交叉验证 ES 9 的 API 路径是否仍然存在；星数 1、权威性为 0，不作为规则来源 |
| 9 | TerminalSkills/skills `skills/elasticsearch-search` | https://github.com/TerminalSkills/skills | 148 | 2026-09-04 | Apache-2.0 | 自定义分析器 / 聚合 / 索引管理的 curl 配方 | 1 | 3 | 2 | 1 | 2 | 9 | MAYBE（未采用） | 新鲜且有许可，但正文是「Task A/B/C + 大段 curl」的教程体，规则密度低；抽查发现它把 `number_of_shards: 3` 当作通用默认给出，与按数据量定分片的官方口径冲突。只用于覆盖面对照 |
| 10 | khalilbenaz/claude-skills-collection `skills/database-elasticsearch-guide` | https://github.com/khalilbenaz/claude-skills-collection | 22 | 2026-08-24 | MIT | 法语的 ES 通用指南 | 0 | 3 | 1 | 1 | 2 | 7 | MAYBE（未采用） | 349 个 skill 的批量集合，单个深度不足；决策表方向正确但无版本门与陷阱，且混入 ELK 全栈内容 |
| 11 | dkbnull/hello-skill `database/skills/elasticsearch` | https://github.com/dkbnull/hello-skill | 29 | 2026-07-02 | MIT | 中文 ES 开发规范 | 0 | 2 | 1 | 1 | 2 | 6 | MAYBE（未采用） | 「强制使用 8.x」「生产至少 3 节点」这类硬性约束在 9.x 已过时且缺乏取证；命名规范属团队约定，不是引擎知识 |
| 12 | wshobson/agents `plugins/llm-application-dev/skills/vector-index-tuning` | https://github.com/wshobson/agents | 39558 | 2026-09-07 | MIT | 通用向量索引调参（HNSW / 量化） | 1 | 3 | 2 | 1 | 2 | 9 | MAYBE（reference） | 引擎无关，参数名用 `efSearch`/`efConstruction`（FAISS/hnswlib 口径），ES 的字段是 `ef_construction` 与 `num_candidates`，直接套用会写错。仅用于确认 HNSW 取舍方向 |
| 13 | davidgeorgehope/elasticsearch-skill | https://github.com/davidgeorgehope/elasticsearch-skill | 27 | 2026-02-26 | 无 LICENSE（API `null`） | curl + REST 的 ES/Kibana 操作手册 | 0 | 0 | 2 | 2 | 0 | 4 | REJECT | 距今 6.5 个月未推送，越过量表的 >6 月红线；无许可文件。其内容已被 #8 的分支继承 |
| 14 | G1Joshi/Agent-Skills `skills/databases/elasticsearch` | https://github.com/G1Joshi/Agent-Skills | 12 | 2026-02-10 | MIT | ES 概览 | 0 | 0 | 1 | 2 | 2 | 5 | REJECT | >6 月未推送；正文是「Elasticsearch 是什么 + Quick Start」的百科式介绍，无任何陷阱 |
| 15 | chaterm/terminal-skills `database/elasticsearch` | https://github.com/chaterm/terminal-skills | 59 | 2026-03-03 | Apache-2.0 | 终端向 ES 运维 | 1 | 0 | 2 | 2 | 2 | 7 | REJECT | >6 月未推送，且非官方，不适用量表的官方豁免 |
| 16 | majiayu000/claude-skill-registry `skills/data/elasticsearch*`（5 个同名目录） | https://github.com/majiayu000/claude-skill-registry | 602 | 2026-09-10 | MIT | 聚合注册表 | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | 是别家 skill 的镜像聚合（同一主题收录了 5 份互相矛盾的副本），没有独立编辑判断，溯源会指向错误的作者 |
| 17 | github/awesome-copilot `agents/elasticsearch-observability.agent.md` | https://github.com/github/awesome-copilot | 38872 | 2026-09-10 | MIT | ES 作为可观测后端的告警排查 | 2 | 3 | 2 | 2 | 2 | 11 | REJECT（越界） | 全树只有这一处 Elastic 内容，且是 agent 定义而非 skill；主题是日志/告警排查流水线，正是本 skill 明确不覆盖的范围（波次 6 的 observability） |
| 18 | alibaba/obz-cli `skills/obz-elasticsearch` | https://github.com/alibaba/obz-cli | 27 | 2026-07-11 | Apache-2.0 | 多后端可观测 CLI 的 ES 适配 | 1 | 2 | 2 | 2 | 2 | 9 | REJECT（越界） | 讲的是用 obz CLI 查 ES 里的日志/指标/追踪，属可观测流水线 |
| 19 | PramodDutta/qaskills `seed-skills/elasticsearch-testing` | https://github.com/PramodDutta/qaskills | 223 | 2026-08-30 | MIT | 对 ES 做集成测试 | 1 | 3 | 1 | 2 | 2 | 9 | REJECT（越界） | 主题是测试框架编排，属 `test-driven-development` 的范围 |
| 20 | cookieMonsterDev/agents-skills `docs-skills/elasticsearch-docs` | https://github.com/cookieMonsterDev/agents-skills | 5 | 2026-08-20 | MIT | 官方文档链接索引 | 0 | 3 | 1 | 2 | 2 | 8 | REJECT | 通篇是「去查哪个文档页」的 URL 清单，本身不含任何引擎知识；这一职责由本 skill 的 reference 末行 sources 与 SOURCES.yaml 承担 |
| 21 | adekoyadapo/es-cluster-triage-agent | https://github.com/adekoyadapo/es-cluster-triage-agent | 1 | 2026-07-28 | 无 LICENSE | Kibana Agent Builder 里的 ES 日常运维 agent | 0 | 2 | 2 | 1 | 0 | 5 | REJECT | 1 星、无许可，且产物是部署进 Kibana Agent Builder 的工具定义，不是可移植的 skill |
| 22 | elastic/agent-skills `plugins/kibana/*`、`plugins/observability/*`、`plugins/security/*` | https://github.com/elastic/agent-skills | 575 | 2026-09-10 | Apache-2.0 | Kibana 看板 / SRE 分诊 / 安全告警 | 3 | 3 | 3 | 3 | 2 | 14 | REJECT（越界） | 质量与 #1 同级，但 Kibana 看板、SLO/告警、检测规则全部落在本 skill 声明不覆盖的范围内。留行以免下轮重复讨论：这些应归未来的 `observability` 与 `security-review` |

## 深度审查

### elastic/agent-skills（#1，主干）

- 结构：`plugins/<plugin>/skills/<skill>/{SKILL.md,references/*.md}`，ES 插件下 7 个技能。
  frontmatter 用 `name` / `description` / `metadata.{author,version,universal}` / `compatibility`，
  其中 `metadata.universal` 与 `compatibility` 都不在本仓库的顶层键白名单里（`compatibility` 在白名单，
  `metadata.universal` 不在），合入时剥离。
- 质量：每个技能都是「先取证（`GET /`、`GET /{index}/_mapping`、`profile: true`）→ 判定 → 改 → 复测」的闭环，
  并在 `Guidelines` 里写死反面做法（「不要用 `function_score` 模拟 pin」「profile 指名某个 clause 时不要先加分片」）。
  这正是标准第 3 节要的「teach the failure」。
- **agent 绑定（必须剥离）**：每个 SKILL.md 都有一段 `<!-- begin-partial: preamble -->`，强制
  「一切操作走 `elastic` CLI，不要直接调 HTTP API」，并在文末给 HTTP→CLI 的 `Operations` 映射表。
  本 skill 不绑定任何 CLI：正文一律写 REST 端点（`POST /{index}/_search`），因为 Dev Tools、curl 与各语言
  客户端都能直接对应，而 `elastic` CLI 是一个额外安装物。
- 重叠：`elasticsearch-ingest` 与 `elasticsearch-reindex` 有相当篇幅讲 `_bulk` NDJSON 格式与任务跟踪，
  与 #4 的 `bulk-indexing` 重叠；取 #1 的 API 细节 + #4 的失败模式（`errors` 标志、
  `es_rejected_execution_exception` 是限流信号而非重试信号）。
- 缺口：没有专门讲**向量与语义检索**（`dense_vector`、`knn` retriever、RRF、`semantic_text`）、
  **聚合精度**（`terms` 的 `doc_count_error_upper_bound`、`cardinality` 的 HLL 误差）、
  **data stream / ILM**、**安全**。这四块要另找上游或直接从官方文档取证。

### elastic/docs-content（#2）

- 内容按 `manage-data/`、`solutions/`、`deploy-manage/`、`explore-analyze/`、`troubleshoot/`、`reference/`
  分区，是 elastic.co/docs 的全部正文。
- **许可实读结论**：`LICENSE` 首行为
  `Attribution-NonCommercial-NoDerivatives 4.0 International`。NoDerivatives 明确禁止分发改编版本，
  NonCommercial 又排除商业再分发，两条都与本仓库 MIT 分发相冲突。
  → `relation: reference`，`license: CC-BY-NC-ND-4.0`。事实可以核对（事实本身不受版权保护），
  但**不复制任何句子、表格或代码块**。这与波次 4 的 graphql-spec 是同一类裁决。
- 这也意味着「官方厂商特例」在本 skill 里**不能**按「官方仓库 merged + 官方文档 merged」的原型成立，
  见下方「备注」的立项说明。

### clawic/skills `skills/elasticsearch`（#4）

- 结构：单个 241 行 SKILL.md + 24 个按阶段分组的 reference（diagnose / design / load / operate）。
- 质量：`Core Rules` 九条每条都带 why 与量化依据（堆 `min(RAM/2, 31g)` 与压缩指针阈值、
  `max_result_window` 10000 的 per-shard 代价、`refresh_interval: -1` 期间四小时产生约 14400 个段）。
  `Error Strings` 表是全部候选里唯一一份「异常类型 → 成因 → 第一步」的映射。
- **agent 绑定（必须剥离）**：frontmatter 有 `slug`、`homepage`、`changelog`、
  `metadata.clawdbot.{emoji,requires,os,configPaths,displayName}`、`metadata.openclaw.requires.config`；
  正文末尾的 `Configuration` 节把 `deployment` / `major_version` / `license_tier` / `client` /
  `target_shard_size_gb` 等做成写进 `~/Clawic/data/elasticsearch/config.yaml` 的用户变量。
  这是 harness 私有的配置机制，全部剥离；其中「分片目标大小是一个可调参数而不是常数」的语义保留为正文的显式参数。
- 与 #1 的重叠：mapping 的 text/keyword、filter context、reindex 三条完全重合，二者一致，按官方（#1）措辞裁决。
- 与 #1 的互补：分片与堆算术、错误串表、事故（红/黄集群、flood-stage、断路器）、深分页、
  `percolator` 反向搜索、`_rank_eval` —— #1 全无。

### opensearch-project/opensearch-agent-skills（#5）

- 结构：`skills/opensearch-skills/**` 深层嵌套（skill 里再套 skill），并带 `scripts/` 下的 Python 评测器与 React UI。
- 可用部分只有 `search/opensearch-launchpad/` 下的 `opensearch_semantic_search_guide.md`（489 行，
  BM25 / dense / sparse / hybrid 四种方法的精度—成本—规模对照）与 `evaluation_guide.md`（265 行，
  判定集构建、nDCG@k / MRR / Recall@k 的取用场景）。
- **不可用部分**：`neural` query、`ml-commons` 模型注册、connector、`agentic search`、PPL —— 这些都是
  OpenSearch 独有 API，ES 上不存在。任何写进正文的检索语法都必须重新按 ES 9 取证。
- agent 绑定：`mcp.json`、`scripts/opensearch_ops.py` 的 CLI 契约，全部不取。

### elastic/rally `skills/running-benchmarks`（#6）

- 只取两条方法学约束（见候选表）。Rally 自身的 track/challenge/pipeline 命令行不进正文——
  那是一个独立工具的使用手册，不是 ES 知识。

### vespa-engine/skills `elasticsearch-migration`（#7）

- 它的 `Concept mapping (cheat sheet)` 表把 ES 的 index / mapping / `_source` / analyzer / `nested` /
  alias / `_bulk` / reindex / `function_score` / `dense_vector`+kNN / sparse_vector+ELSER / ingest pipeline
  逐项列出。拿它当**覆盖面 checklist** 反查本 skill：据此补上了 `nested` 的展平陷阱与 `_source` 的
  存储模式两处，正文措辞与事实全部另行取证。它明确写着「不要把 ES 或 Vespa 文档抄进 skill」，与本仓库同调。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 是否绑定 `elastic` CLI | #1 每个技能都写「不要直接调 HTTP API，一律用 `elastic` CLI」；#4、#8、#9 全部用 REST/curl | 正文只写 REST 端点，不提任何 CLI | `elastic` CLI 是额外安装物且版本门槛 ≥0.2；REST 端点是 Dev Tools、curl 与全部官方客户端的共同底座。本机实测（见「实验验证」）也是直接对 REST 发起 |
| 2 | 新索引的默认分片数 | #9 给 `number_of_shards: 3` 作为模板默认；#1 只说「显式设置」；#4 给公式 `max(1, ceil(primary_gb / target_shard_size_gb))` | 采用 #4 的公式，并写明目标分片大小 10–50 GB（搜索型偏小、日志型偏大） | 官方 size-your-shards 指南的口径就是按数据量而非节点数；固定 3 是把一个未知量写死。#9 因此在候选表里降为 MAYBE |
| 3 | 单节点集群为什么是 yellow | #11 主张「生产至少 3 节点，禁止单节点」；#4 主张「单节点上 yellow 是副本未分配的预期状态，开发环境设 `number_of_replicas: 0`」 | 采用 #4 | 本机实测：9.5.3 单节点建索引后 `_cluster/health` 为 yellow，`unassigned.reason` = `INDEX_CREATED`（副本无处可放）。#11 把部署建议和健康语义混为一谈 |
| 4 | 动态映射对字符串的推断结果 | #1 说「第一份文档会把字符串锁成 `text`」；#4 说默认形态是 `text` + `fields.keyword` 多字段 | 采用 #4，并写明这是**动态映射**的行为：`text` 加一个 `ignore_above: 256` 的 `keyword` 子字段 | 本机实测：向无 mapping 的索引写入 `{"title":"Quick Brown"}` 后 `_mapping` 返回 `{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}`。#1 的说法漏了子字段，会让人以为动态映射下无法聚合 |
| 5 | HNSW 参数名 | #12 用 `M` / `efConstruction` / `efSearch` | 正文用 ES 的名字：`index_options.m`、`index_options.ef_construction`，查询侧用 `num_candidates`（ES 没有 `ef_search` 这个查询参数） | #12 是引擎无关的通用文，直接照抄会写出 ES 不接受的字段名 |
| 6 | 混合检索怎么融合 | #5（OpenSearch）主张 `hybrid` query + normalization processor；#4 主张 RRF | ES 侧写 `retriever` 树里的 `rrf` retriever | `hybrid` query 与 search pipeline 的 normalization processor 是 OpenSearch 独有；ES 的对应物是 RRF retriever。这是「跨厂商上游不可直译」的典型 |
| 7 | 聚合是否可以直接上 `text` 字段 | #14 的示例在 `text` 字段上做 `terms` 聚合；#1、#4 都禁止 | 禁止；写明失败信息是 `Fielddata is disabled on text fields by default`，修法是 `.keyword` 子字段而不是打开 `fielddata` | 本机实测复现了该异常（见「实验验证」第 3 条） |
| 8 | 版本基线 | #11 写 8.x；#9 写 8.10+；#8 自述测于 9.3.1；#1 写 8.x 或 9.x | 正文以 **9.5** 为基线，需要 8.x 才有的规则标 `(8.x+)`，9.x 才有的标 `(9.x+)` | `gh api repos/elastic/elasticsearch/releases`：v9.5.3（2026-09-03）是最新，8.19.21 是 8.x 末班车；本机实测实例即 9.5.3 |
| 9 | basic 上到底还剩什么语义检索能力 | 本 skill 初稿按实验 15 写「`semantic_text` 在 basic 可用」；#5（OpenSearch）默认集群内可做推理；#12 不涉及授权 | 改写为「Inference API 整体是 Enterprise，basic 上没有任何集群内推理：`semantic_text` 写入、ELSER、语义重排全部 403；向量只能在集群外生成」。并单列一条「授权失败是延迟的」 | 初稿只验证了建 mapping 就下结论，是取证不足。补测实验 21、22 后推翻，并以 `InferencePlugin.java` 的 `INFERENCE_API_FEATURE = ENTERPRISE` 交叉确认。教训：授权类结论必须端到端跑一遍，不能只看 `PUT` 是否 200 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| elastic-agent-skills | elastic/agent-skills `plugins/elasticsearch/skills/*` | merged | 主干：访问模式→字段类型的判定、多字段规则、映射爆炸检查项、profile 驱动的查询优化闭环、query rules 与 `multi_match` 的分工、ES\|QL 的定位、reindex 与 alias 切换流程 |
| elastic-docs | elastic.co/docs（elastic/docs-content） | reference | 每条事实的最终裁决依据（CC-BY-NC-ND-4.0，不复制任何文字） |
| elasticsearch-repo | elastic/elasticsearch | reference | 当前主版本与版本门（9.5.3 / 8.19.21）；三重许可，不取内容 |
| clawic-elasticsearch | clawic/skills `skills/elasticsearch` | merged | 分片与堆算术、错误字符串→成因表、搜索分诊七步、深分页、事故处置、输出门 |
| opensearch-launchpad | opensearch-project/opensearch-agent-skills | merged | 检索方法（BM25 / dense / sparse / hybrid）的精度—成本对照语义，以及「先建判定集再调参」的离线评测纪律 |
| elastic-rally | elastic/rally `skills/running-benchmarks` | merged | 基准测试的两条方法学约束：负载生成器与被测集群不同机；无法采集主机级指标的结果只是方向性数据 |
| vespa-es-migration | vespa-engine/skills `elasticsearch-migration` | reference | 覆盖面 checklist（ES 概念全集），用于反查漏洞 |
| wshobson-vector-tuning | wshobson/agents `plugins/llm-application-dev/skills/vector-index-tuning` | reference | 仅交叉确认 HNSW 的 recall/内存/构建时间取舍方向 |
| face0b1101-es | face0b1101/elasticsearch-skill | reference | 仅交叉确认 ES 9 上若干 REST 路径仍然存在 |

## 实验验证

本机 Docker 起单节点 `docker.elastic.co/elasticsearch/elasticsearch:9.5.3`
（`-e discovery.type=single-node -e xpack.security.enabled=false`，映射到 `localhost:9299`），
Lucene 10.5.1。以下每条声明都在该实例上实跑过。

启动命令：

```bash
docker run --rm --name es-lab -p 9299:9200 \
  -e discovery.type=single-node -e xpack.security.enabled=false \
  -e ES_JAVA_OPTS='-Xms1g -Xmx1g' \
  docker.elastic.co/elasticsearch/elasticsearch:9.5.3
```

`GET /` → `"number": "9.5.3"`，`"lucene_version": "10.5.1"`，
`"minimum_wire_compatibility_version": "8.19.0"`，`"minimum_index_compatibility_version": "8.0.0"`。
许可为 `basic`（`GET /_license` → `"type": "basic", "status": "active"`）。

| # | 声明 | 命令 | 实测结果 |
|---|---|---|---|
| 1 | 动态映射把 JSON 字符串推断成 `text` + `keyword` 多字段 | `PUT /lab1 {}`；`POST /lab1/_doc/1 {"title":"Quick Brown Fox","status":"active","price":9.99,"ts":"2026-09-11T00:00:00Z"}`；`GET /lab1/_mapping` | `title` 与 `status` 都得到 `{"type":"text","fields":{"keyword":{"type":"keyword","ignore_above":256}}}`；`price` → `float`（不是 `double`）；`ts` → `date`。裁决 4 据此成立 |
| 2 | `term` 打在 `text` 字段上静默返回 0 命中 | `GET /lab1/_search {"query":{"term":{"title":"Quick Brown Fox"}}}` | HTTP 200，`hits.total.value = 0`，无任何错误或警告 |
| 3 | 在 `text` 字段上做 `terms` 聚合直接失败 | `GET /lab1/_search {"aggs":{"t":{"terms":{"field":"title"}}}}` | `search_phase_execution_exception` 包裹 `illegal_argument_exception: Fielddata is disabled on [title] in [lab1]. …Please use a keyword field instead.` 真实原因嵌在 `failed_shards[].reason` 里 |
| 4 | 单节点集群 yellow 是副本无处安放 | `GET /_cluster/health`；`GET /_cat/shards/lab1?v&h=index,shard,prirep,state,unassigned.reason` | `status: yellow`，`unassigned_primary_shards: 0`；分片表显示主分片 STARTED、副本 `UNASSIGNED / INDEX_CREATED`。裁决 3 据此成立 |
| 5 | 分词链决定匹配 | `POST /lab1/_analyze {"field":"title","text":"Quick Brown Fox"}` | `[quick, brown, fox]`——与实验 2 的 `term` 值 `"Quick Brown Fox"` 不可能相等 |
| 6 | 索引期 `edge_ngram` 分析器若同时用于查询期会把查询也切成前缀 | 建 `ac` 分析器（`edge_ngram` 2–10）映射到 `name`；`POST /lab_ng/_analyze {"field":"name","text":"elastic"}` | 查询文本被展开为 `[el, ela, elas, elast, elasti, elastic]`，导致「所有前缀互相匹配」。修法是 `search_analyzer: standard` |
| 7 | 对象数组会跨对象串味，`nested` 才能保住组内关联 | `users` 映射为 `object`，写入 `[{first:Alice,last:Smith},{first:Bob,last:Jones}]`，再用 `filter: [term users.first=Alice, term users.last=Jones]` 查询 | `hits.total.value = 1`——一个本不存在的 Alice Jones 被匹配上 |
| 8 | 硬性上限的真实默认值 | `GET /lab1/_settings?include_defaults=true&flat_settings=true` | `index.mapping.total_fields.limit=1000`、`index.mapping.total_fields.ignore_dynamic_beyond_limit=false`、`index.mapping.depth.limit=20`、`index.mapping.nested_fields.limit=100`、`index.mapping.nested_objects.limit=10000`、`index.max_result_window=10000`、`index.max_terms_count=65536`、`index.max_docvalue_fields_search=100` |
| 9 | 超出字段数上限的报错文本 | 向新索引写入 1200 个字段的文档 | `Limit of total fields [1000] has been exceeded while adding new fields [1001]` |
| 10 | 深分页在窗口外直接报错 | `GET /lab1/_search {"from":10000,"size":10}` | `Result window is too large, from + size must be less than or equal to: [10000] but was [10010].` |
| 11 | **RRF 与 `linear` retriever 是 Enterprise 许可功能** | `GET /lab1/_search {"retriever":{"rrf":{...}}}`；同样试 `linear` | 两者都返回 HTTP 403 `security_exception: current license is non-compliant for [Reciprocal Rank Fusion (RRF)]` / `[linear retriever]`。`standard` retriever 在 basic 上正常。交叉验证：`x-pack/plugin/rank-rrf/.../RRFRankPlugin.java` 里 `RANK_RRF_FEATURE` 与 `LINEAR_RETRIEVER_FEATURE` 都声明为 `License.OperationMode.ENTERPRISE` |
| 12 | basic 上做混合检索的逃生口 | `bool.should` 里同时放 `match` 与带 `boost` 的 `knn` 子句 | 正常返回，分数是两侧之和（alpha 2.69 / beta 1.33）。这是 basic 许可下唯一免费的混合方式 |
| 13 | `dense_vector` 默认就开量化，且阈值按维度切换 | 依次建 dims=128/256/320/384/512/1024 的 `dense_vector`，读回 `_mapping` | ≤320 维 → `int8_hnsw`（`m:16, ef_construction:100`）；**≥384 维 → `bbq_hnsw` 且自动带 `rescore_vector.oversample: 3.0`**。ES 里没有 `ef_search` 这个查询参数，召回旋钮是 `num_candidates`。裁决 5 据此成立 |
| 14 | **向量默认不再回到 `_source`** | `GET /lab_vec/_doc/1`；`GET /lab_vec/_settings?include_defaults=true` | `_source` 只有 `txt`，`emb` 不见了；`index.mapping.exclude_source_vectors` 默认为 `true`。RAG 场景里「取回原始向量」需要显式关掉它 |
| 15 | `semantic_text` 不写 `inference_id` 也能建 | `PUT /lab_sem {"mappings":{"properties":{"body":{"type":"semantic_text"}}}}`；读回 `_mapping` | 建索引成功，`inference_id` 被解析为 `.elser-2-elasticsearch`。`GET /_inference/_all` 在 basic 上就有三个预置端点：`.elser-2-elasticsearch`(sparse_embedding)、`.multilingual-e5-small-elasticsearch`(text_embedding)、`.rerank-v1-elasticsearch`(rerank) |
| 16 | `_rank_eval` 在 basic 上可用 | `GET /lab1/_rank_eval` 带一条 `precision@10` 判定 | `metric_score: 1.0`，`details.q1.hits[].rating` 逐条回显。相关性改动可以离线量化，不必凭肉眼 |
| 17 | data stream 只接受 `create` | 建 `data_stream` 索引模板后 `POST /lab-logs-app/_doc`；再 `PUT /lab-logs-app/_doc/xyz` | 前者写入后端索引 `.ds-lab-logs-app-2026.09.10-000001`；后者报 `only write ops with an op_type of create are allowed in data streams` |
| 18 | `index.mode: logsdb` 自带排序 | `PUT /lab_logsdb {"settings":{"index.mode":"logsdb"}}`，读 settings | `index.sort.field` 默认变为 `['@timestamp']` |
| 19 | profile 会指名代价最大的 clause | `GET /lab1/_search {"profile":true,"query":{"bool":{"must":[{"wildcard":{"status.keyword":"*ctiv*"}}]}}}` | `profile.shards[0].searches[0].query` 顶层为 `MultiTermQueryConstantScoreBlendedWrapper` `status.keyword:*ctiv*`，5 096 401 ns；同索引上等价的 `TermQuery status.keyword:active` 只要 108 855 ns（约 47 倍）。前导通配符的代价在单文档索引上就已经可见 |
| 20 | 单桶 `terms` 聚合的误差字段确实会回报 | `GET /lab1/_search {"aggs":{"s":{"terms":{"field":"status.keyword","size":1,"shard_size":1}}}}` | 返回 `doc_count_error_upper_bound: 0` 与 `sum_other_doc_count: 0`——单分片单值时为 0，但这两个字段永远存在，是判断 `terms` 结果是否可信的唯一依据 |
| 21 | **Inference API 本身在 basic 上就是 403** | `POST /_inference/sparse_embedding/.elser-2-elasticsearch {"input":"hello"}` | `403 security_exception: current license is non-compliant for [inference]`。交叉验证：`x-pack/plugin/inference/.../InferencePlugin.java` 里 `INFERENCE_API_FEATURE` 声明为 `License.OperationMode.ENTERPRISE` |
| 22 | **`semantic_text` 的授权失败是延迟发生的** | 承实验 15：mapping 建成后 `POST /lab_sem/_doc {"body":"..."}` | 写入返回 `403 ... [inference]`。也就是说建索引成功、`GET /_inference/_all` 正常列出三个端点，只有真正写第一篇文档才暴露。只建索引的 CI 冒烟测试会绿灯放行 |

## 基线缺口

无 skill（`uv run tools/run_evals.py elasticsearch --baseline`，`anthropic/claude-opus-5` + medium）
时，各场景未达成的 `expected_behavior`。

**先说一件影响判定方式的事**：本机 Docker 可用，基线模型每一场都自己起了一个真实 ES 容器
（场景 2 起的是 9.5.3，场景 3 直接去读 `elastic/elasticsearch` 9.5 分支的 `LicensedFeature` 源码）
并当场做实验，因此第一版 `expected_behavior` 几乎被全部达成、毫无区分度。
按 `docs/workflow.md` Phase B 的要求改写了 `expected_behavior`——转向「版本分界事实」与
「会真造成事故的判断」，并重跑基线，才得到下表。这一点必须写下来：**这个 skill 要跟一个
有 Docker、肯花八分钟做实验的 Opus 5 比，能省的是时间与版本漂移，不是让它从不会到会。**

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 mapping 审查 | 首跑 `status: timeout` | 第一次跑满 900 秒预算被杀，没有产出 `answer.md`：整段预算花在起容器、逐批灌 1200 个字段复现限额上。单独重跑一次（`--only 1`）377 秒完成，下面两行按重跑的答复判定 |
| 1 mapping 审查 | #2 的后半（`ignore_dynamic_beyond_limit` 比报错更糟） | 它把 `total_fields.limit` 提到 2000 当止血，并写明「只买时间」，方向没错；但全文没提 `index.mapping.total_fields.ignore_dynamic_beyond_limit`——这个开关会把「拒绝写入」换成「字段被静默丢弃并标 `_ignored`」，是同一个决策点上更危险的一侧 |
| 1 mapping 审查 | #8 版本纪律 | 全文没有一处点出它是按哪个 Elasticsearch 版本推理的（夹具写的是 9.5），却给出了「`logsdb` 的 synthetic `_source` 需要 Enterprise，basic 下退回存原始 `_source`」这种强授权/版本相关断言，没有任何取证 |
| 2 相关性 | #4 `multi_match` + `cross_fields` 的分析器一致性 | 它换成了 `constant_score` 分数预算 + 多个短语子句，思路自洽且 nDCG 从 0.287 升到 0.997，但从未提到 `cross_fields` 要求所有字段同分析器——而 `title` 用 `english`、`description` 用 `standard` 正是这条的反例 |
| 2 相关性 | #2 的后半（brand 该退到 `filter` 的 `term`，由分面而非自由文本驱动） | 只判定了大小写这一层，修法仍把 brand 留在打分查询里（`brand 6` 的信号位），没有把它移出自由文本入口 |
| 4 慢查询 | #6 640 个索引与 60 天保留期自相矛盾 | 它算出 2133 分片/节点超过每 GB heap 20 分片的预算，也提了冷数据 `_shrink`，但接受了「60 天」这个说法（用 `210 × 60 × 2 / 3` 算每节点数据量），没有注意到 640 个索引意味着保留期根本没执行，因此没把「删掉过期索引」列为收益最大的动作 |
| 3 向量与混合检索 | 无 | 全部 8 条达成。它读了 9.5 分支源码，`INFERENCE_API_FEATURE` / `RANK_RRF_FEATURE` / `LINEAR_RETRIEVER_FEATURE` 三条门控、延迟 403、`bbq_hnsw` 的 384 维阈值、`exclude_source_vectors`、`filter` 必须放进 `knn` 内部，一条不落 |
| 5 负例（可观测） | 无（本就应该全部达成） | `skill_read = false`，答复完全落在连接池饱和与 OTel 埋点上，没有滑向 ES |

## 评测结果

模型两组相同：`claude-opus-5:medium`（`anthropic/claude-opus-5`，thinking=medium，
`tools/run_evals.py` 默认值，未传 `--model` / `--thinking`）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 events mapping 审查（8 条） | claude-opus-5:medium | 无（baseline） | false | 6/8：#1 #3 #4 #5 #6 #7。未达成 #2（只提了调大 `total_fields.limit`，没提 `ignore_dynamic_beyond_limit` 的静默丢字段）、#8（全程未声明按哪个版本推理，却断言 logsdb 的 synthetic `_source` 需要 Enterprise） | 首跑 900 秒 `timeout` 无产出；`--only 1` 重跑 377 秒完成，按重跑判定 |
| 1 events mapping 审查（8 条） | claude-opus-5:medium | 有 skill | **true** | **8/8** | #2 补上：明确写「绝不要调大 `total_fields.limit`、绝不要开 `fielddata: true`（把每个 distinct term 反解进 heap）」，并单独点名 `ignore_dynamic_beyond_limit: true` 会把「拒写」换成「字段进 `_ignored` 的静默丢数据」，只能当切换窗口内的兜底。#8 补上：首句即「本地 ES 9.5.3 / basic licence」，末段再声明「与生产同小版本同许可」，并把推算值标 `[INFERENCE]` 要求用 `_cat/indices` 复核 |
| 2 目录相关性（7 条） | claude-opus-5:medium | 无（baseline） | false | 5.5/7：#1 #3 #5 #6 #7 达成，#2 只达成前半（判出大小写，未把 brand 移出自由文本入口）。未达成 #4（改用 `constant_score` 分数预算，全程没提 `cross_fields` 要求所有字段同分析器） | 起了 9.5.3 容器复现，nDCG 0.287 → 0.997 |
| 2 目录相关性（7 条） | claude-opus-5:medium | 有 skill | **true** | **6.5/7** | #4 补上：明确写「`title` 用 english、`description` 用 standard，跨字段永远对不上，`cross_fields` 也因此不合法」，并在新索引方案里让两个字段共用 `en_text`/`en_text_search` 以使 `cross_fields` 合法——这正是 `nike air max` 能跨 brand+title 拼起来的机制。#2 仍只到 `term` + `case_insensitive: true`，未显式改为分面驱动的 `filter`，与基线同为部分达成。nDCG 0.4369 → 0.9912（hotfix，不需 reindex）/ 0.9986（新索引） |
| 3 basic 上的向量与混合检索（8 条） | claude-opus-5:medium | 无（baseline） | false | **8/8** | 无缺口。基线直接读 `elastic/elasticsearch` 9.5 分支源码，把 `INFERENCE_API_FEATURE` / `RANK_RRF_FEATURE` / `LINEAR_RETRIEVER_FEATURE` / `DISK_BBQ_LICENSE_ENFORCEMENT` 逐条列出，连 `InferenceLicenceCheck` 对第三方 service 也走 `INFERENCE_API_FEATURE` 这一点都挖到了 |
| 3 basic 上的向量与混合检索（8 条） | claude-opus-5:medium | 有 skill | **true** | **8/8** | 同样全中，但走的是查表而非读源码：132 秒对 395 秒（基线的 1/3），且开头就给出 `GET /` + `GET /_license` + `GET /_mapping` 的一分钟前置检查与延迟 403 的警告。这一场 skill 省的是时间与复现成本，不是能力 |
| 4 慢查询与容量（9 条） | claude-opus-5:medium | 无（baseline） | false | 8/9：#1 #2 #3 #4 #5 #7 #8 #9。未达成 #6（接受了「60 天保留期」的说法，用 `210 × 60 × 2 / 3` 算每节点数据量，没发现 640 个索引意味着保留期根本没执行） | — |
| 4 慢查询与容量（9 条） | claude-opus-5:medium | 有 skill | **true** | **9/9** | #6 补上：「保留策略没在跑：640 个每日索引 ≈ 21 个月，而声明的保留期是 60 天」，并把「执行保留策略砍回 60 天」列为立即可上线动作，还实测了扇出代价（1 索引 5 分片 3 ms vs 1045 分片 12 ms，修好后的查询 4.0× penalty）。另外给出五档 profile 对照表（原查询 `build_scorer` 32.9 ms → 去掉前导通配符 5.2 ms），以及 5 vs 40 分片的实测（修好后的查询 4 ms → 8 ms，2.00×），正面回答了「加分片会怎样」 |
| 5 负例：凌晨告警 + OTel 追踪（5 条） | claude-opus-5:medium | 无（baseline） | **false** | 5/5 | 答复落在连接池饱和（`pool.wait_ms=4380` / `used=40` / `pending=268`）与缺失埋点上 |
| 5 负例：凌晨告警 + OTel 追踪（5 条） | claude-opus-5:medium | 有 skill | **false** ✅ | 5/5 | **负例未被误触发**：description 的 `Do not use for ... alerting or tracing-driven incident investigation` 生效，答复开篇即「这个告警不需要 Elasticsearch 技能」，全文没有任何 ES 索引/查询建议。无需收紧 description |

结论：**通过**。基线共 4 条 `expected_behavior` 未达成（场景 1 的 #2 与 #8、场景 2 的 #4、场景 4 的 #6），
有 skill 时 4 条全部达成，其中 3 条来自 skill 正文里有明确规则的地方
（`ignore_dynamic_beyond_limit` 的静默丢数据、`cross_fields` 的分析器一致性、
`## Environment` 的「按生产同小版本复现并声明」），第 4 条（保留期与索引数自相矛盾）来自
`references/cluster-operations.md` 的分片预算与 `references/data-lifecycle.md` 的 ILM 语义。
负例两组 `skill_read` 均为 `false`。

值得记下的两点：

1. 场景 3 两组都是 8/8。在有 Docker、肯读上游源码的 Opus 5 面前，这个 skill 在「授权门控」
   这类可实验的事实上不会拉开能力差距，只把 395 秒压到 132 秒。**它真正拉开差距的地方是
   「不会想到去测」的判断**——`ignore_dynamic_beyond_limit` 是个开关而不是报错、
   `cross_fields` 对分析器的隐含要求、640 个索引与 60 天保留期自相矛盾。
2. 有 skill 的场景 4 主动声明了一处对正文的偏离（`now` 取整吃 request cache 在它构造的语料上
   没有收益，因为缓存资格取决于 range 能否在分片上被改写成 `match_all`），并把它排除在主要
   修复之外。这是期望的行为：正文给判断，实测可以推翻它，但要说出来。

## 备注

### Elastic 的许可处理结论（本 skill 最重要的溯源判断）

Elasticsearch 这个名字下面有四份互不相同的许可，**必须逐仓库分别判定，不能笼统按「Elastic 是
Elastic Licence」处理**：

| 对象 | 实际许可 | 本仓库的处理 |
|---|---|---|
| `elastic/agent-skills`（官方 skill 仓库） | **Apache-2.0**（LICENSE 实读） | `merged`，主干 |
| `elastic/rally`（官方压测框架） | **Apache-2.0** | `merged`，只取方法学两条 |
| `elastic/docs-content`（elastic.co/docs 的源） | API 报 NOASSERTION；LICENSE 首行是 **Attribution-NonCommercial-NoDerivatives 4.0 International** | **`reference`**。ND 禁止分发改编版本、NC 禁止商业再分发，与本仓库 MIT 分发直接冲突，无论改写得多彻底都不能 merged。只核对事实，不复制任何句子、表格或代码块 |
| `elastic/elasticsearch`（产品本体） | API 报 NOASSERTION；实为 **AGPL-3.0 / Elastic License 2.0 / SSPL-1.0 三重** | `reference`，`license: AGPL-3.0`（记最严格的那个开源选项）。只取两个不受版权保护的事实：当前主版本、两个 `LicensedFeature` 常量的授权档 |

`elastic/docs-content` 这条是本波最容易做错的地方，与波次 4 的 graphql-spec 是同一类：
**官方文档站几乎都在某个 GitHub 仓库里，`kind: docs` 的许可必须去那个仓库实读**，
不能因为「是官方文档」就默认可以 merged。

### 第三方上游是否充足

**充足，不需要动用「官方特例」的降格条款。** 立项时按官方特例准备
（官方仓库 + 官方文档 + ≥1 个社区/跨厂商上游），但实际检索出的合格上游多于下限：

- `merged` 4 个：`elastic/agent-skills`（官方，Apache-2.0，总分 14）、
  `clawic/skills`（社区，MIT，11）、`opensearch-project/opensearch-agent-skills`
  （跨厂商官方，Apache-2.0，12）、`elastic/rally`（官方，Apache-2.0，13）。
- 其中**非 Elastic 的 merged 上游有 2 个**（clawic、opensearch-project），两个都 ≥8 分，
  所以本 skill 并不是「只靠一家官方仓库改写」。
- 官方文档因许可只能 `reference`，这反而使「官方仓库 merged + 官方文档 merged」的特例原型
  在这里不成立——立项靠的是上面这 4 个 `merged`，是常规判据而不是特例。

标题下仍保留「单一权威上游改写」一行：事实层面唯一权威仍是 Elastic 官方
（`elastic/agent-skills` 提供主干、elastic.co/docs 提供最终裁决），
其余上游只在官方未覆盖的地方补位（分片与堆算术、错误串表、事故处置、检索方法选型、评测纪律）。

### 当前版本

`gh api repos/elastic/elasticsearch/releases`：**v9.5.3**（2026-09-03）是最新；
v9.4.6 与 **v8.19.21** 并行维护，8.19 是 8.x 末班车。分支列表到 `9.5` 为止。
正文以 9.5 为基线，版本敏感规则标 `(9.x+)` / `(8.x+)`。
`GET /` 在 9.5.3 上报告 `lucene_version: 10.5.1`、`minimum_wire_compatibility_version: 8.19.0`、
`minimum_index_compatibility_version: 8.0.0`——所以 7.x→9.x 必须经 8.x 中转，
7.x 建的索引要先 reindex 或归档。

### 是否实跑过 ES 实例

**跑过。** `docker.elastic.co/elasticsearch/elasticsearch:9.5.3` 单节点（`discovery.type=single-node`、
`xpack.security.enabled=false`、映射到 `localhost:9299`），basic 许可。
「实验验证」节 22 条声明全部在这个实例上实跑，命令与输出逐条记录在那张表里。
正文中标「Measured」的每一处都对应其中一行。三处因此推翻了上游或初稿的说法：
动态映射的真实产物（裁决 4）、单节点 yellow 的语义（裁决 3）、
以及 basic 上到底还剩什么语义检索能力（裁决 9，把初稿的「`semantic_text` 在 basic 可用」
推翻为「Inference API 整体是 Enterprise，且失败是延迟的」）。

### 未来同步时要盯的上游

- `elastic/agent-skills` 推送很频繁（调研当天仍在推）；`paths` 已收窄到 7 个 ES 子技能目录，
  Kibana / observability / security 三个 plugin 的变更会被 `paths` 过滤掉。
- `clawic/skills` 是唯一一个非官方的 `merged` 上游，2026-07-27 推送，是本 skill 里最不新鲜的
  合入源；下次同步时重点复核它的分片与堆数字是否还与官方 size-your-shards 指南一致。
- `elastic/docs-content` 是 `kind: docs`，`check_upstream.py` 只会报 `manual check`，
  需要人工打开链接比对；同时复核 LICENSE 是否仍是 CC-BY-NC-ND-4.0。
- 授权档位是 Elastic 的商业决策，可能随版本变动。下次同步必须重跑实验 11、21、22
  （RRF / linear retriever / Inference API / `semantic_text` 写入），不要沿用本次结论。

### 放弃的方向

- 不做 Kibana（看板、Lens、saved objects、Agent Builder、workflows）：`elastic/agent-skills`
  的 `plugins/kibana/*` 质量与主干同级，但整体落在声明不覆盖的范围内。
- 不做日志采集流水线与告警/SLO：同理排除了 `plugins/observability/*`、
  `github/awesome-copilot` 的 `elasticsearch-observability.agent.md`、`alibaba/obz-cli`。
  波次 6 的 `observability` 会接手，本 skill 只在 `## Scope` 直述不覆盖，不写 `use the ... skill`。
- 不做 OpenSearch 的独有 API：`neural` query、ml-commons、search pipeline、PPL 全部不进正文，
  只在 `## Scope` 末尾留一句「为 OpenSearch 写的建议必须在这里重新验证」。
