# data-analysis 调研记录

> 正式正文与4份参考已完成，评测唯一入口为 [`skills/data-analysis/evals/`](../skills/data-analysis/evals/)。下文保留Phase A/B当时记录；用户继续建设后的最新结论见文末，内容交付不等于已证明增益。

## 调研日期与检索途径

- 调研 / 复核日期：2026-09-12。
- 本轮结论：通过常规立项门，不使用官方特例。已实读 15 个候选，来自 6 个仓库；至少 DuckDB、Polars、Anthropic、K-Dense 四家提供六个月内活跃、评分 ≥8 的相关上游。并非以同仓路径数量冒充独立来源。
- 准备期记录：Phase A完成后先运行场景1–4，16/16达成，再追加场景5；后续20/20结果和正式建设分节记录，不据此宣称技能增益。
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

## Phase B构建准备交付（历史记录）

当时保留评测定义与原始输入，不发布Scope骨架。原5场景与10份夹具现已原样迁入[正式评测目录](../skills/data-analysis/evals/)，不再维护准备目录副本或骨架恢复命令。用户随后要求正式建设，按[路线图](../docs/roadmap.md)使用同模型medium和独立输出完成后续对照；历史基线保持不变。

## Phase C 正式建设（2026-09-12）

用户在已知上轮停在 Phase B、尚无正文后明确要求“好，正式开始构建skill”。
本轮按该决定完成正文，不再以强基线无缺口为由停在准备态。此前 5 场景
20/20 无 skill 基线与逐项证据全部保留；这些行为仍是非区分项，不能据此
宣称本 skill 带来增益，也没有编造新的 baseline 失败。

### 实际落点

- `skills/data-analysis/SKILL.md`：任务型范围、16 条硬规则，以及 Data contract、
  Inference、Partition invariance、Reproduction 四个具名门；沿用项目已有引擎
  与 LazyFrame 等消费者契约，明确排除数据库运维、Office/PDF 交付、通用 Python、
  训练、专用科学格式与连接器平台。
- `references/statistical-design.md`：估计目标与权重、记录身份和独立单位之别、
  配对/聚类/重复测量、全缺失资格总体、Welch 的有限适用范围、p 值与等效性边界。
- `references/pandas.md`：CSV 的 dtype 与缺失标记必须共同声明；null merge、
  基数验证、缺失分组与 subtotal、两端本地日历转 UTC、跨块身份状态。
- `references/polars.md`：惰性消费者边界、表达式命名、null/NaN、独立全局分母分支、
  UDF 四种优化承诺及纯函数/schema 要求；streaming 非内存上限保证，sink 不抹除
  上游状态；不强推所有数据都迁移到 Polars。
- `references/duckdb.md`：显式 CSV 类型/nullstr/force_not_null、原生粒度核对、
  SUM DISTINCT 的错误修复、空集/未知度量、WHERE/HAVING 与显示边界、
  spill 限制与有界输出。没有合入错误的 xls 读取宏或自动安装扩展。
- `SOURCES.yaml`：4 个本次实读仓库作为 merged，10 个实读官方文档作为 reference；
  每个 reference 的尾注均使用对应来源 id，贡献说明英文且指出实际路径。
- 原 `research/evals/data-analysis/` 经 `shutil.copytree` 原样复制到安装目录
  `evals/`，没有改评测定义、期望或原始故障夹具。旧归档路径由 Main 集成时处理。
  未新增脚本；没有证据支持值得长期维护的重复自动化工具。

### 本次实读与裁决延续

通过已登录 `gh api` 重新读取四仓 main 的 HEAD，均与上方快照一致：
Polars `70bec73cd09722411492dfd3613c73bb6df979b8`；
DuckDB skills `7feda8e01e22bc0886c86123f3884947e36d8c69`；
Anthropic `a6d8653261a4cf3353c145648fece23bad949278`；
K-Dense `c1ed16d97dd61ff50a3bd46dd353e4a55fd77f34`。
重新读取了 SOURCES 所列 SKILL 原文、Polars lazy-api，以及 Polars/DuckDB 根
LICENSE、Anthropic data/LICENSE、K-Dense LICENSE.md。K-Dense 的 `LICENSE`
路径返回 404 后通过根目录定位为 `LICENSE.md`，未把失败读取当许可证据。
四仓许可分别 MIT、MIT、Apache-2.0、MIT。

官方 API/机制再次实读：pandas 3.0.5 read_csv、merge、timeseries 的 DST 段；
Polars 1.44.2 join、map_batches 和 streaming guide；DuckDB CSV、aggregates、
workload tuning（GitHub latest release 为 1.5.5）；SciPy 1.18.0 ttest_ind。
官方文档所在仓库的 license API 返回 pandas/SciPy BSD-3-Clause、
Polars/DuckDB web MIT。文档仅用于事实核对，不复制整段文档。

保留既有裁决：streaming 可能回退且结果仍需内存；map_batches 的 pushdown/
streamable 是语义承诺而非性能按钮；CSV 标识符字符串不自动取消 NA 解析；
pandas null-null merge 与普通 SQL/Polars 默认不同；UTC 瞬时标准化不能替代
业务本地日期；重复观测不等于独立样本。没有按原 fixture 数字编写正文，
没有照搬厂商默认引擎、固定采样阈值或生信工具安装表。

### 验证状态

按本批分工，未运行 formatter、lint、测试、构建、安装冒烟、模型评测、
全库校验或 check_upstream --pin；未生成 NOTICE/目录索引等共享产物，
未提交或推送。以上版本标签表示本轮对照阅读的官方文档基线，不表示示例
已经实跑。with-skill、代码示例冒烟、安装及结构校验明确待 Main 统一执行。
正式正文已交付；技能增益结论仍为未证明，不将“内容完整”混同“评测有效”。

## Phase D 统一验证与实际行为对照（2026-09-12）

Main 已完成上节列出的安装、示例冒烟、结构检查及原5场 with-skill。
定义和10份原始夹具逐字节迁至
[正式评测目录](../skills/data-analysis/evals/)，未修改题目、判据或原始导出。
模型固定 `openai/gpt-5.6-sol`、`--thinking medium`；真实 assistant 消息也核对一致。

令 `R=/tmp/hs-five-build-20260912/evals/data-analysis/openai-gpt-5.6-sol-medium/skill`，
`W=/tmp/hs-five-build-20260912/workspaces/data-analysis-openai-gpt-5.6-sol-medium-skill-`。
`N/A`、`N/E` 分别为 `R/N/answer.md`、`R/N/events.jsonl`，`WN` 为编号工作区。
基线保留在 `/tmp/hs-five-20260912/evals/data-analysis/openai-gpt-5.6-sol-medium/baseline/`。

### 逐项判读

| 场景 | 秒 | 读取本 skill | pass / partial / fail |
|---|---:|---|---|
| 1 订单粒度、重传退款及未知金额 | 337.7 | 是 | 4 / 1 / 0 |
| 2 DST 业务日与事件身份 | 168.1 | 是 | 4 / 0 / 0 |
| 3 跨分片身份与参与者等权 | 331.8 | 是 | 5 / 0 / 0 |
| 4 SQLite 锁诊断近似负例 | 153.2 | 否 | 2 / 0 / 0 |
| 5 Polars 惰性全局分母 | 245.5 | 是 | 4 / 0 / 0 |

全部 `status=ok` 只表示运行结束。下表按原20条复合判据计分，不以输出流畅度、
答案长度或脚本存在替代实际行为。

| 原判据 | 裁决 | 可复核证据 |
|---|---|---|
| 1.E1 订单事实粒度 | pass | W1/analyze_revenue.py:1–186、revenue_draft.sql:1–91；按 refund_id 去重并先聚合 settled 退款，不联接 order_lines 放大事实、不使用 SUM(DISTINCT gross) |
| 1.E2 总人口及金额账本 | partial | 1/A:1–46、1/E:3404、4342 报告6单、退款35、已知净额265及1笔未知；但没有单列已知 gross=300。计算结果未错，缺的是该复合判据要求的 gross 报告项，不把能由265+35推导当作已经报告 |
| 1.E3 地区及未归属人口 | pass | 1/E:3404、4029、4342；North 3/165/1未知，South 2/60，Unknown 1/40；空客户不匹配 VIP，标识符保留字符串 |
| 1.E4 未知均值不伪装为精确总均值 | pass | 1/A 给已知金额5单均值53，明确全部6单均值未知；没有把265/6报告为精确值 |
| 1.E5 可重跑执行与独立对账 | pass | 1/E:3404、4342 实际运行本地脚本；1/E:4029 另在 eval 中独立遍历原订单/退款，得到6=5+1、地区净额合计265、唯一退款35与重传行40。不是调用同一分析函数回显结果；原4份 CSV 字节未改 |
| 2.E1 本地午夜构成25小时半开区间 | pass | W2/analyze_dst_events.py:43–46、82–86；边界为11-02 04Z至11-03 05Z，以 America/New_York 日期推导而非24小时偏移 |
| 2.E2 事件身份与重复墙上时间 | pass | W2/analyze_dst_events.py:49–80；跨输入以 event_id 去重，e2/e3 两个01:30仍各保留，e3重传只算一次 |
| 2.E3 实际数值及纳入清单 | pass | 2/E:121、148 得到 e1/e2/e3/e4、4次购买、3用户、100美元；机器时区改为 Asia/Tokyo 仍一致 |
| 2.E4 可重跑时间解释 | pass | W2/analyze_dst_events.py:1–108；读取绝对时间后统一到 UTC，再按业务日筛选，原输入未改 |
| 3.E1 全局 measurement 去重 | pass | W3/analyze_pilot.py:119–175；磁盘主键 reading_id 跨分片去重，r2只算一次，不删除 p01 的其他不同读数 |
| 3.E2 参与者等权点估计 | pass | 3/E:444、517；A中 p01=0、p02=100，A=50；B三人各40，B=40，B-A=-10 |
| 3.E3 保留全缺失参与者 | pass | W3/analyze_pilot.py:179–220；左联接完整参与者人口，A共3人、仅2个已观测结果；3/A:25–48 不把 p05 当0或外推全组均值 |
| 3.E4 推断单位与因果限制 | pass | 3/A:50–83；Welch 在参与者均值上计算，SE50、df1、宽区间约[-645.31,625.31]，不声称改善、重复读数独立或因果成立 |
| 3.E5 增量磁盘状态与执行 | pass | W3/analyze_pilot.py:98–220 使用磁盘唯一键及参与者聚合，不把无界 ID 集合留在 Python 内存；3/E:439 独立对账-10，444正常执行，449重复整个分片后仍-10，517最终执行成功 |
| 4.E1 SQLite 负例不读取分析 skill | pass | 4/result.json skill_read=false，事件无本 skill/参考读取；4/A 聚焦 SQLite writer 与事务 |
| 4.E2 不删除数据库或 WAL 解锁 | pass | 4/A:1–263；明确拒绝删除数据库、WAL 或 journal，采用事务/连接诊断而非破坏性“清理” |
| 5.E1 不透明 UDF 优化承诺错误 | pass | 5/A:5–16；解释地区谓词下推改变全公司分母，分批归一化不能给全局份额；5/E:788 原结果为0.75/0.25 |
| 5.E2 保持可组合 LazyFrame | pass | W5/revenue_share.py:21–46；完整 completed 流做原生聚合后 cross join，显示筛选与 limit 在后，不 Python 全量 collect、不硬编码1000、不全局关优化 |
| 5.E3 正确份额与未知值 | pass | 5/E:1613 修复后 North 为0.3/0.1；2044 未截断 n3仍null；5/A 明确1000是已知 completed 小计，不是全部收入精确总额 |
| 5.E4 引擎与显示人口保持 | pass | 5/E:2044 实际比较 auto/streaming，North含0.3/0.1/null、South含0.6/0，下游筛到 n1 仍0.1 |

实际参考导航：场景1读 duckdb，场景3读 statistical-design，场景5读 polars；
场景2只用主文，负例不读本 skill。**pandas 参考没有在模型对照中被打开**，
不能将安装可达误写成模型导航覆盖。场景1实际执行的是 stdlib Python，
其 DuckDB SQL 因该评测环境缺少 DuckDB 未执行，答案已说明；Python 消费者通过。

### 参考代码、安装与结构的独立冒烟

Main 从四份参考抽取可运行代码，在 Python3.12 与 pandas3.0.5、Polars1.44.2、
DuckDB1.5.5、SciPy1.18.0 的临时隔离环境实际运行，得到：

- pandas：字符串身份、NULL不互配、23小时和25小时业务日边界通过；
- Polars：NULL不互配、全局分母不受显示筛选/limit改变、全未知输入、
  auto与streaming结果一致；
- DuckDB：明确CSV NULL策略、重复键检测、覆盖率及Parquet导出通过；
- SciPy：Welch统计量约-1.2247449，p约0.2878641、df4，
  mean(a)-mean(b) 的95%区间约[-3.2669579,1.2669579]。

这证明参考示例在所列版本可执行，不为场景1未执行的 SQL 冒领运行证据，
不增加原20条之外的模型得分。五主题合并工作区全库校验60 skill、
0 error/0 warning，目录 current 60；19条仓库型来源记录全部 up_to_date，
pin更新0。隔离安装恰好五包，data-analysis 的18个文件与源逐字节一致。

### 结论与限制

基线20/20，本轮 **19 pass / 1 partial / 0 fail**。1.E2 的已知 gross
报告项覆盖不足如实保留；不把其余正确净额和人口结果包装成20/20。
没有发现被正文关闭的基线失败，D2增益未证明；用户明确要求继续正式建设，
因此交付完整内容及原样证据，不换弱模型、不增补知识题制造优势。

每配置每场单次，不能推断跨模型或重复运行稳定性。场景3附加 CLI 的
`--state-db` 会重建内部同名表，只应使用专用分析状态库，不能据此推荐把任意既有
数据库当临时库；默认临时文件路径不改原CSV。本次没有把该评测辅助脚本作为
skill脚本发布，也没有审定其中手写 Student-t 数值实现为通用统计库替代品。
