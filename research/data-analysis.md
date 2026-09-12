# data-analysis 调研记录

## 调研日期与检索途径

- 调研 / 复核日期：2026-09-12。
- 本轮结论：通过常规立项门，不使用官方特例。已实读 15 个候选，来自 6 个仓库；至少 DuckDB、Polars、Anthropic、K-Dense 四家提供六个月内活跃、评分 ≥8 的相关上游。并非以同仓路径数量冒充独立来源。
- 当前阶段：Phase A 完成；Phase B 首轮基线1–4已完成，16/16全部达成；保留原场景并追加场景5待Main执行。尚未开始规则正文 / topic references 重写；没有技能效果结论。
- 检索：`pandas polars data analysis SKILL.md github`；从 roadmap 的 duckdb/duckdb-skills 起步，搜索结果发现 polars-inc/skills、TerminalSkills、K-Dense、Gonzih；通过 GitHub API 目录树发现 Anthropic 通用分析候选。
- GitHub 内容一律使用已登录 `gh api`：`repos/<repo>` 核验 stars/pushed_at/license；`git/trees/HEAD?recursive=1` 核验真实路径和 HEAD；`contents/<path>` base64 解码读原文。没有匿名 GitHub 请求，没有把搜索摘要当原文。
- 官方事实交叉核验用 pandas 3.0.5、Polars stable、DuckDB current、SciPy 1.18、NIST EDA 文档；另经 Context7 `/websites/pola_rs_api_python_stable` 查询 join validation / count 语义。
- 活跃度严格按仓库 pushed_at，非 skill 文件更新时间；新鲜度按 ≤1月3 / ≤3月2 / ≤6月1。大型 monorepo 的最近推送不能证明每个 skill 同日改过。

## 候选表

分数次序：权威 / 新鲜 / 具体 / 正确 / 许可。INCLUDE 表示允许选取经核实部分，不代表全文可信；正确性为抽查，不是运行所有上游示例。因明显越界而 REJECT 的候选即使总分 ≥8 也不作为建设主干。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 1 | duckdb/duckdb-skills `skills/query/SKILL.md` | [原文](https://github.com/duckdb/duckdb-skills/blob/main/skills/query/SKILL.md) | 540 | 2026-04-23T13:56:22Z | MIT | 本地文件 SQL | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 官方；Friendly SQL 与结果边界可取，删 session / slash-command 绑定 |
| 2 | duckdb/duckdb-skills `skills/read-file/SKILL.md` | [原文](https://github.com/duckdb/duckdb-skills/blob/main/skills/read-file/SKILL.md) | 540 | 2026-04-23T13:56:22Z | MIT | 文件探测 | 3 | 1 | 3 | 1 | 2 | 10 | INCLUDE | 限取 schema/样本探测，xls 被误路由为 read_xlsx |
| 3 | duckdb/duckdb-skills `skills/convert-file/SKILL.md` | [原文](https://github.com/duckdb/duckdb-skills/blob/main/skills/convert-file/SKILL.md) | 540 | 2026-04-23T13:56:22Z | MIT | 文件转换 | 3 | 1 | 2 | 3 | 2 | 11 | INCLUDE | 只取本地派生 CSV/Parquet；不做 Office 交付 |
| 4 | polars-inc/skills `polars/SKILL.md` | [原文](https://github.com/polars-inc/skills/blob/main/polars/SKILL.md) | 79 | 2026-08-21T12:46:49Z | MIT | 通用本地 dataframe 分析 | 3 | 3 | 3 | 1 | 2 | 12 | INCLUDE | 官方且不是 Polars Cloud 包装；streaming 保证过强需校正 |
| 5 | TerminalSkills/skills `skills/pandas/SKILL.md` | [原文](https://github.com/TerminalSkills/skills/blob/main/skills/pandas/SKILL.md) | 149 | 2026-09-04T19:42:42Z | Apache-2.0 | pandas 清洗/merge | 1 | 3 | 2 | 1 | 2 | 9 | INCLUDE | 显式 dtype、validate 有用；“推断必读全文两遍”不成立 |
| 6 | TerminalSkills/skills `skills/polars/SKILL.md` | [原文](https://github.com/TerminalSkills/skills/blob/main/skills/polars/SKILL.md) | 149 | 2026-09-04T19:42:42Z | Apache-2.0 | Polars 教程 | 1 | 3 | 1 | 1 | 2 | 8 | INCLUDE | 只作交叉；select 同名表达式缺 alias |
| 7 | TerminalSkills/skills `skills/data-analysis/SKILL.md` | [原文](https://github.com/TerminalSkills/skills/blob/main/skills/data-analysis/SKILL.md) | 149 | 2026-09-04T19:42:42Z | Apache-2.0 | 通用 EDA / 图表 | 1 | 3 | 1 | 3 | 2 | 10 | INCLUDE | 基本检查正确但通用教程比重大；100K 行就采样不能作精确指标默认 |
| 8 | TerminalSkills/skills `skills/pandas-ai/SKILL.md` | [原文](https://github.com/TerminalSkills/skills/blob/main/skills/pandas-ai/SKILL.md) | 149 | 2026-09-04T19:42:42Z | Apache-2.0 | LLM 产品接入 | 1 | 3 | 1 | 3 | 2 | 10 | REJECT | SmartDataframe/API key/chat 包装，不是本地确定性分析；只核通用数据部分，不合入产品API |
| 9 | K-Dense-AI/scientific-agent-skills `skills/polars/SKILL.md` | [原文](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/polars/SKILL.md) | 44498 | 2026-09-12T02:09:21Z | MIT | Polars 教程 / 引用集 | 1 | 3 | 2 | 0 | 2 | 8 | REJECT | 同名表达式与引用中的过滤下推改变统计问题；正确性0硬拒绝 |
| 10 | K-Dense-AI/scientific-agent-skills `skills/exploratory-data-analysis/SKILL.md` | [原文](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/exploratory-data-analysis/SKILL.md) | 44498 | 2026-09-12T02:09:21Z | MIT | 本地 EDA / 观测层级 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 数据字典、缺失、重复测量、样本局限很具体；排除生信格式和自家工具 |
| 11 | K-Dense-AI/scientific-agent-skills `skills/statistical-analysis/SKILL.md` | [原文](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/statistical-analysis/SKILL.md) | 44498 | 2026-09-12T02:09:21Z | MIT | 统计推断 | 1 | 3 | 2 | 1 | 2 | 9 | INCLUDE | 仅取设计/效应量/非显著解释；“p-value says an effect exists”错误 |
| 12 | anthropics/knowledge-work-plugins `data/skills/analyze/SKILL.md` | [原文](https://github.com/anthropics/knowledge-work-plugins/blob/main/data/skills/analyze/SKILL.md) | 23981 | 2026-09-12T02:12:56Z | Apache-2.0 | 通用分析交付 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE | 非领域维护方，权威保守记1；支持 CSV，不依赖专属 SaaS |
| 13 | anthropics/knowledge-work-plugins `data/skills/validate-data/SKILL.md` | [原文](https://github.com/anthropics/knowledge-work-plugins/blob/main/data/skills/validate-data/SKILL.md) | 23981 | 2026-09-12T02:12:56Z | Apache-2.0 | 指标/人口/偏差核验 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 粒度、分母、join 膨胀、平均的平均与复现直接相关 |
| 14 | anthropics/knowledge-work-plugins `data/skills/statistical-analysis/SKILL.md` | [原文](https://github.com/anthropics/knowledge-work-plugins/blob/main/data/skills/statistical-analysis/SKILL.md) | 23981 | 2026-09-12T02:12:56Z | Apache-2.0 | 描述统计与推断 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE | 抽查独立样本 t 检验、效应与区间、离群点先调查；不照搬样本量30等固定阈值 |
| 15 | Gonzih/skills-science `skills/polars-data/SKILL.md` | [原文](https://github.com/Gonzih/skills-science/blob/main/skills/polars-data/SKILL.md) | 0 | 2026-03-23T22:18:54Z | NONE（README/frontmatter称MIT） | Polars 大片代码 | 0 | 1 | 2 | 0 | 1 | 4 | REJECT | weekday误写0=Mon；streaming必然内存安全的保证错误；无LICENSE文件 |

### 三条规则抽查与评分依据

以下是实际核查的事实，不是对全上游示例的测试结果。API 本身之外的工程阈值视为启发式，不能冒充官方保证。

| 候选 | 抽查三项（正确 / 错误） | 官方依据 |
|---|---|---|
| 1 | FROM-first省略SELECT正确；GROUP BY ALL正确；count()等于count(*)正确 | [DuckDB Friendly SQL](https://duckdb.org/docs/current/sql/dialect/friendly_sql.html) |
| 2 | DESCRIBE拿schema正确；count(*)数行正确；xls交给read_xlsx错误 | [Friendly SQL](https://duckdb.org/docs/current/sql/dialect/friendly_sql.html)、[aggregates](https://duckdb.org/docs/current/sql/functions/aggregates.html)、[Excel：不支持xls](https://duckdb.org/docs/current/core_extensions/excel.html) |
| 3 | COPY导出CSV/Parquet、Excel扩展LOAD、xlsx读写范围正确 | [Excel](https://duckdb.org/docs/current/core_extensions/excel.html)及其COPY示例；仅评分通用转换范围，不认可隐式扩展安装/任意输出覆盖 |
| 4 | count非空正确；join validate默认m:m不检查正确；“streaming令超RAM数据必完成”错误 | Context7返回Polars count/join；[streaming fallback](https://docs.pola.rs/user-guide/concepts/streaming/) |
| 5 | CSV dtype显式声明正确；merge validate唯一性检查正确；推断必读全文两遍错误（low_memory分块推断，不等于固定两遍全读） | [pandas read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)、[merge](https://pandas.pydata.org/docs/reference/api/pandas.merge.html) |
| 6 | scan惰性计划正确；group_by聚合正确；select(name,name/1000)同名输出示例错误 | [Polars col](https://docs.pola.rs/api/python/stable/reference/expressions/col.html)、[streaming](https://docs.pola.rs/user-guide/concepts/streaming/)；官方skill亦明确DuplicateError |
| 7 | 读表先核列/缺失、区分数值/分类概要、检测离群点而非自动删三项方向正确 | [pandas read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)、[NIST EDA](https://www.itl.nist.gov/div898/handbook/eda/section1/eda11.htm) |
| 8 | pd.read_csv读入CSV正确；示例最大GDP是USA正确；人口均值134.6百万正确 | [pandas read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)与原文数组直接算术。仅检查通用数据事实，未核PandasAI版本API；产品边界已足够排除，不把此分数作产品API背书 |
| 9 | collect(engine='streaming')正确；with_columns两次value无alias错误；best_practices把聚合后value>100移至聚合前错误，改变条件总体 | [Polars streaming](https://docs.pola.rs/user-guide/concepts/streaming/)、[DuckDB聚合与HAVING区别](https://duckdb.org/docs/current/sql/functions/aggregates.html)；非同义“优化” |
| 10 | 保留缺失与真零区别正确；把重复测量层级列入设计正确；EDA不直接作确认性/因果结论正确 | [NIST EDA](https://www.itl.nist.gov/div898/handbook/eda/section1/eda11.htm)、[SciPy独立样本要求](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html)、[pandas缺失读取](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html) |
| 11 | 独立/配对区分正确；Welch用于不等方差方向正确；p值说明效应存在错误，实际上是零假设下尾概率 | [SciPy ttest_ind](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html)；Pingouin两个文档URL返回404，未声称核实其列名/auto模式 |
| 12 | schema先行正确；缺失检查正确；聚合粒度核验正确 | [pandas read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)、[DuckDB aggregates](https://duckdb.org/docs/current/sql/functions/aggregates.html) |
| 13 | 多对多膨胀正确；分母必须和统计单位一致正确；100×50+10×200再除110=63.636…正确 | [pandas merge](https://pandas.pydata.org/docs/reference/api/pandas.merge.html)、[DuckDB aggregates](https://duckdb.org/docs/current/sql/functions/aggregates.html)与直接算术；COUNT DISTINCT仅修计数，不修收入 |
| 14 | 独立样本t检验设计正确；差异区间与点估计应同时报告正确；先调查离群再决定处理正确 | [SciPy ttest_ind](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html)、[NIST EDA](https://www.itl.nist.gov/div898/handbook/eda/section1/eda11.htm) |
| 15 | weekday写0=Mon错误；超RAM保证错误；scan构建惰性计划正确 | [weekday实际1=Mon](https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.dt.weekday.html)、[streaming](https://docs.pola.rs/user-guide/concepts/streaming/) |

## 深度审查

对最高分候选 1、4、10、13、12、14、3 共七项通读原文，并浏览适用 references；没有 references 的目录以 GitHub tree 确认，而非假定遗漏。

### 1. DuckDB query（12）

- 结构是逐步 slash command，不是独立通用 skill；frontmatter `argument-hint`、`$@` 和 `/duckdb-skills:*` 都须删除。
- 可取：先实际取 schema、文件 ad-hoc 路径、结果大小控制、执行后报告 SQL 和数字。不能把原文1M行/10GB阈值作为内存承诺。
- 无附属 references。Friendly SQL主干在SKILL内；不合并 ATTACH state.sql、HOME状态文件、扩展安装或云认证。
- 和Polars重叠的是“问题→schema→执行→结果”；通用工作流只写一次，DuckDB语法放 `references/duckdb.md`。

### 2. Polars official（12）

- 原文description越界抢占所有Python数据工作，但明确排除Cloud/On-Prem/GPU，属于开源本地分析能力而非SaaS产品包装。
- 通读正文，浏览 `insight-recipes.md`、`lazy-api.md`、`pandas-to-polars.md`；树中另有 contexts/expressions。
- 有价值：null filter语义、null join默认、表达式命名、schema、源类型、动态分组排序、len/count、sink。
- 原文“collect_schema不读数据”对CSV推断过于绝对；“所有数据都lazy”“所有查询collect一次”是厂商默认策略，不应压倒诊断、验证和真实内存约束。
- pandas-to-polars把合法list参数和合法`pl.col(...).sum()`写入Wrong栏，是风格偏好误作API错误；不合入。速率倍数、anti join恒快1.5倍也不取。
- streaming可能回落内存，最终DataFrame仍要装得下。统一由官方user-guide裁决，不能照搬必完成承诺。

### 3. K-Dense exploratory-data-analysis（12）

- 原文范围是授权本地科学数据、自动化能力矩阵和安全读取；大部分生信/影像/格式CLI超出本skill。
- 通读正文，浏览 `references/general_scientific_formats.md`。保留数据字典、观察单位/重复测量层级、缺失不同含义、原始文件不覆盖、样本范围不能假装总体、结论强度匹配证据。
- `allowed-tools`是宿主限制；强制拒symlink/多硬链和512MiB上限是其脚本能力，不是通用分析准则。脚本和安装大表不带入。
- 与Anthropic validate互补：前者输入/观测设计，后者业务指标核对。无基线前不假定需要全部内容。
- README论文引文请求不是本轮重写输出的默认义务；保留许可证署名，不注入未经用户要求的论文引用。

### 4. Anthropic validate-data（12）

- 通读完整检查表、常见陷阱、输出模板、复现说明；目录无references。`../../CONNECTORS.md`、`argument-hint`、slash commands全部剥离。
- 很强的任务级上游：总体定义、join膨胀、分母漂移、不完整周期、平均的平均、追踪单笔和双算法核算。
- 限制：`COUNT(DISTINCT id)`不修复其他列的SUM；不把“收入不得负、百分数都0–100”套在净退款/增长率上；UTC标准化不等于本地业务日按UTC切。
- 来源是分析任务包装而非某个专有数据SaaS；本地CSV路径可独立完成，不要求warehouse MCP。

### 5. Anthropic analyze（11）

- 通读问题分层、取数、分析、验证、交付；无references但有外部CONNECTORS链接。
- “无warehouse就请用户上传CSV”必须改成先读已提供本地文件，不能已有数据还追问。只取结论带证据、可重跑SQL、局限。
- 与validate高度重叠，预计不独立加正文篇幅；scope和输出形状候选。

### 6. Anthropic statistical-analysis（11）

- 无references；`user-invocable:false`不是规范字段。原文描述统计、异常、检验、偏差都在单文件。
- 不自动删离群点、观察与因果分开、效应量/不确定性可取；30事件阈值、所有同比都优先等处过于绝对，不照搬。
- 非正态就Mann–Whitney不等于测试同一个均值问题；本轮只考虑观察单位、重复样本、描述性结论边界，不扩成全统计推断百科。

### 7. DuckDB convert-file（11）

- 无references，read-file跨skill依赖必须去掉；参数占位符和隐式安装剔除。
- 贡献限于分析派生物保存，不能因支持xlsx就侵占office；保存CSV/Parquet需明确类型、输出路径和不覆盖raw。
- 与query合成一个DuckDB topic，不独立建convert技能。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 默认数据引擎 | Polars官方抢占所有任务；Terminal通用分析固定pandas；DuckDB固定SQL | 沿用用户/项目引擎；未指定时根据本地任务选一个，不强制迁移。库知识放topic references | 本skill任务范围与最小干预原则 |
| 2 | null key联接 | pandas会匹配双方null；Polars默认不匹配；普通SQL不匹配 | 数据契约优先，未知身份不能互相认领；迁移时显式保持语义 | pandas merge官方警告；Polars join官方 |
| 3 | 多对多指标膨胀 | validate建议COUNT DISTINCT；教程直接连接明细 | 先定义度量粒度，分别消重/汇总事实再join，独立核对金额；不以SUM DISTINCT修数值 | pandas merge笛卡尔积示例；DuckDB aggregate语义 |
| 4 | 缺失与0 | 教程fill/drop；K-Dense明确不同含义 | 保留未知及未观测总体，报告已知subtotal和缺失覆盖；不得把不能计算的总体均值伪装精确 | pandas NA读入契约；NIST EDA |
| 5 | 时区 | validate推荐UTC；业务分析需要当地日期 | UTC用于绝对时刻；按声明地区的本地日历端点构造半开区间，保留DST重复时刻 | 时间戳身份和业务日定义；评测2给出显式日历契约 |
| 6 | 性能下推 | K-Dense示例把HAVING式条件移到原始行 | 不允许改变统计总体；先证明等价再优化，lazy优化器不是语义改写许可证 | DuckDB WHERE/HAVING示例 |
| 7 | 内存 | Polars skill和Gonzih承诺streaming内存安全 | streaming是执行模式，不是内存上限保证；检查回退/状态/结果大小；大结果sink而非collect | Polars streaming官方文档 |
| 8 | 统计证据 | K-Dense措辞p值证明效应；其他段落区分不显著 | p值在零假设下解释，重复行不是独立样本；效果方向、missingness和设计先于显著性 | SciPy ttest_ind；NIST EDA |

## 最终合入清单

这是Phase C候选，不代表正文已写或已经合入。临时Scope/SOURCES骨架已移出安装目录；未来按真实缺口与实际采用段落登记relation和contributes，不预先认领贡献。

| id | 上游 | relation（计划） | 贡献 |
|---|---|---|---|
| polars-official | polars-inc/skills `polars` | merged | 仅经校正的惰性执行、schema、null/count、join与结果sink，放polars.md |
| duckdb-official | duckdb/duckdb-skills `query`（read/convert补充） | merged | 本地SQL取数、显式类型、聚合NULL与输出规模，放duckdb.md |
| anthropic-data | anthropics/knowledge-work-plugins `data/skills/{analyze,validate-data,statistical-analysis}` | merged | 粒度、分母、观测单位、独立核算和复现输出 |
| kdense-eda | K-Dense `exploratory-data-analysis` | merged | 缺失与观测层级、输入范围、可复现分析 |
| pandas-docs | pandas官方API | reference | CSV默认NA、dtype、merge null匹配/validation，放pandas.md事实依据 |
| polars-docs | Polars user guide/API | reference | 校正性能承诺与版本API；Phase C按实际引用登记SOURCES |
| duckdb-docs | DuckDB current docs | reference | SQL聚合、类型与CSV依据；Phase C按实际引用登记 |

### 已读取快照

| 仓库 | ref | HEAD |
|---|---|---|
| duckdb/duckdb-skills | main | `7feda8e01e22bc0886c86123f3884947e36d8c69` |
| polars-inc/skills | main | `70bec73cd09722411492dfd3613c73bb6df979b8` |
| TerminalSkills/skills | main | `56037efc04d0ffd20a0a85b18894115df74bd70f` |
| K-Dense-AI/scientific-agent-skills | main | `c1ed16d97dd61ff50a3bd46dd353e4a55fd77f34` |
| anthropics/knowledge-work-plugins | main | `a6d8653261a4cf3353c145648fece23bad949278` |
| Gonzih/skills-science | main | `3c09573c3037d46c7a1a06aa48ac16883d687d76` |

## 建设范围

- 单一任务：本地数据到可复现结论。通用规则只考虑契约/缺失、join基数和指标粒度、分母、重复观测、时间窗口、数值核对、执行规模和可复现性。
- 后续topic候选：`pandas.md`、`polars.md`、`duckdb.md`；不拆新skill，不写语言教程，不预设需要脚本。
- 排除数据库运维、Office/PDF交付、通用Python语法与包工具、模型训练、SaaS连接器和生信专用格式。
- 临时骨架由 `uv run tools/new_skill.py data-analysis --category task` 生成，仅用于Phase B准备；现已移出安装目录，评测和原始故障夹具归档于 `research/evals/data-analysis/`。

## 基线缺口

首轮基线已由Main实跑完成，模型为 **openai/gpt-5.6-sol，medium**。本代理阅读实际代码、answer及events后，16/16项全部达成。追加Polars管线场景5由Main复现、实跑并审阅，另4/4达成；累计20/20，未发现可支持正文的实质缺口。

证据根目录：
`/tmp/hs-five-20260912/evals/data-analysis/openai-gpt-5.6-sol-medium/baseline/`。
下面 `N/events:L` 指此目录下 `N/events.jsonl` 的物理行号；
代码路径均在 `/tmp/hs-five-20260912/workspaces/data-analysis-openai-gpt-5.6-sol-medium-baseline-N/`。

| 场景 | 逐项评分 | 实际证据 |
|---|---|---|
| 1 revenue E1 | 达成 | 修复的revenue_draft.sql以settled_refund_events和refunds_by_order分层，去掉lines事实连接；1/answer:23–31说明处理；revenue_analysis.py:54–75验证退款身份 |
| 1 E2 | 达成 | 1/events:3533输出6订单/5已知/1未知/net subtotal265；1/answer:48明确gross300与refund35 |
| 1 E3 | 达成 | 同一执行输出North165/South60/Unknown40及各订单数；1/answer:21明确不认领空VIP |
| 1 E4 | 达成 | 1/answer:12–19将总体均值标未知；没有强制要求可选的已知均值53，所以不扣分 |
| 1 E5 | 达成 | 1/events:4048执行脚本、按订单总体检查6，独立Decimal核算300-(10+5+20)=265；1/events:4111再次执行输出；源CSV只读 |
| 2 local-day E1 | 达成 | analyze_business_day.py:45–48由IANA本地两端午夜分别转UTC；2/events:91与1258打印25h区间 |
| 2 E2 | 达成 | 代码:50–85按event_id去重并用绝对UTC比较；2/events:1319逐条列出e1/e2/e3/e4 |
| 2 E3 | 达成 | 2/events:1258实跑4笔/3人/100；1319另一路核算一致 |
| 2 E4 | 达成 | 代码是可运行入口，不依赖系统时区；2/events:1289、1294的再次执行结果一致 |
| 3 participant E1 | 达成 | analyze.py:92–111全局SQLite reading_id查重；3/answer:16保留r1/r2/r6 |
| 3 E2 | 达成 | 3/events:3650最终代码运行A50/B40/-10；3/answer:5–23逐参与者解释 |
| 3 E3 | 达成 | analyze.py:132–149保留全缺失参与者人口计数；3/answer:25–31定义实际估计总体与选择偏倚 |
| 3 E4 | 达成 | 3/answer:33–37不支持改善，区分观察方向、小样本、缺失策略和因果条件 |
| 3 E5 | 达成 | analyze.py:214–238磁盘SQLite、temp_store FILE、全局identity和两级聚合；3/events:5239验证交换分片/批大小1不变，非只在嘴上说增量 |
| 4 negative E1 | 达成 | 4/result.json skill_read=false；4/answer开头以写锁/事务为对象，无统计内容 |
| 4 E2 | 达成 | 4/answer讨论正常COMMIT/ROLLBACK、backup、WAL持久性；无删除数据库或journal/WAL的常规修复建议 |

评分只判断现有expected_behavior：标准库/SQLite实现不是违规，未要求使用特定数据引擎；未要求的性能基准、额外输出字段或文档措辞不作缺口。首轮结论是**无区分度**，不是技能有效。

### 追加场景5：不透明UDF的优化承诺改变统计总体

- 文件：`evals/files/revenue_share.py`（PEP 723固定Polars1.44.2）、`share_orders.csv`。接口真实返回LazyFrame，调用方会继续filter/select并选择引擎。
- 业务定义：每笔completed订单金额 / 全公司completed已知金额subtotal；region、排名、limit只是展示，不重定义分母；unknown保留null。
- 原管线用map_batches在当前frame上求和，却显式声明predicate_pushdown、slice_pushdown与streamable。区域过滤可越过UDF，使North分母成为400；分批执行也不满足全局求和语义。这不是把外部文字当答案的题，而是要修复一个真实引擎边界。
- 正确答案：completed已知subtotal1000；North前二n2=.3、n1=.1；South的s1=.6、s2=0；未截断North中n3=null；cancelled n4不参与。不能称subtotal为完整已对账收入。
- 允许原生表达式、全局聚合与join等任意保持语义的lazy解法，不要求特定代码形状；禁止的整表collect/硬编码/全局禁优化均是query显式的现有消费者约束。
- 官方依据已实读：[Polars1.44.2 LazyFrame.map_batches](https://docs.pola.rs/api/python/stable/reference/lazyframe/api/polars.LazyFrame.map_batches.html)：streamable要求分批与全数据产生相同结果；包含聚合时不得允许predicate pushdown；schema必须准确。较新默认pushdown为false，夹具显式true因此不依赖默认值。
- Main实跑原夹具得到North的0.75/0.25，证实错误可复现；补测模型将完整completed分支聚合后cross join回明细，保留LazyFrame API、null及后续组合能力。没有把修复回填到原始故障夹具。

## 评测结果

| 场景 | 模型 | 有/无skill | skill_read | 达成行为 | 备注 |
|---|---|---|---|---|---|
| 1 | openai/gpt-5.6-sol medium | 无 | false | 5/5 | 非区分项 |
| 2 | openai/gpt-5.6-sol medium | 无 | false | 4/4 | 非区分项 |
| 3 | openai/gpt-5.6-sol medium | 无 | false | 5/5 | 非区分项 |
| 4 | openai/gpt-5.6-sol medium | 无 | false | 2/2 | 基线负例通过不证明with-skill触发率 |
| 5 | openai/gpt-5.6-sol medium | 无 | false | 4/4 | North/South、null、下游筛选与两引擎实跑一致，仍无区分度 |

场景5逐项证据：answer.md:5–16解释不安全的predicate/slice pushdown及streamable承诺；workspace/revenue_share.py:21–41实际使用全局聚合分支与惰性cross join。events工具结果`call_qteklESXvuuNd1yGxZ7da5QE`和`call_j48Az8YwlK4QN2xLnW2Jdqct`均输出North的0.3/0.1；`call_oXCMbHmiVdX5IerO1rDn36W0`和`call_93LKaxbvPJnptI2tTKHEc46x`均输出South的0.6/0；`call_nWvNhmAxTv5VfkLzJ4Hhh9eI`输出组合、空值、地区和引擎检查通过。没有with-skill运行，没有技能有效性结论。

## 备注

- DuckDB、Polars、K-Dense实读根LICENSE；Anthropic逐目录实读`data/LICENSE`为Apache-2.0。Terminal根LICENSE为Apache-2.0。未遇GPL/专有候选合入。
- Gonzih树无LICENSE文件，README末尾及frontmatter仅自称MIT；按NONE且许可分1保守记录，不合入。
- 官方身份不是正确性豁免；Polars错误风格表、streaming保证、DuckDB xls误支持已明确剔除。K-Dense Polars即使高stars仍按正确性0拒绝。
- 未读取/合并原仓脚本，不对其运行安全和所有API作通过承诺。没有更改共享docs、生成物、日志，没有commit/push。

## 构建准备交付

保留[评测定义](evals/data-analysis/evals.json)和原始输入，不发布Scope骨架或修改安装目录计数。恢复时执行 `uv run tools/new_skill.py data-analysis --category task`，然后 `cp -R research/evals/data-analysis/. skills/data-analysis/evals/`；已有调研记录不会被覆盖。使用[路线图](../docs/roadmap.md)中的同模型medium命令与新输出目录；下一次先取得真实最终行为缺口，再写最少规则并运行有skill对照。
