# postgres 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `gh search repos "postgres skill"` / `"postgresql agent skills"`、`gh search code --filename SKILL.md postgres`
  - <https://www.skills.sh>、VoltAgent/awesome-agent-skills
  - 领域官方组织仓库：`supabase/`、`neondatabase/`、`microsoft/`、`timescale/`、`google/`、`prisma/`、
    `paradedb/`、`github/awesome-copilot`
  - postgresql.org（版本策略页、当前文档）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`

**当前稳定版本核实**：<https://www.postgresql.org/support/versioning/>（2026-08-13 更新）显示受支持的
主版本为 18（当前小版本 18.6，2025-09-25 首发，2030-11-14 EOL）、17、16、15、14；19 处于 Beta 3，
**尚未 GA**。因此正文以 **PostgreSQL 18** 为基准，版本门槛标注覆盖 14–18，不写 19 的任何内容。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | supabase/agent-skills `skills/supabase-postgres-best-practices` | https://github.com/supabase/agent-skills | 2592 | 2026-08-12 | MIT | 34 条规则文件，覆盖索引/连接/RLS/schema/锁/数据访问/监控/高级 | 3 | 2 | 3 | 3 | 2 | 13 | INCLUDE | 自述「for Postgres running anywhere」，绝大多数规则与 Supabase 无关；每条含错误/正确 SQL 对照。Supabase 语境集中在 `auth.uid()`、`anon/authenticated/service_role` 角色名与 6543/5432 端口，可整段剥离 |
| 2 | neondatabase/postgres-skills `skills/postgres-best-practices` | https://github.com/neondatabase/postgres-skills | 31 | 2026-08-25 | Apache-2.0 | 13 个 reference：schema/索引/查询优化/查询模式/诊断/逻辑复制/热备/隔离级别/备份/安全/批量装载/连接池/大版本升级 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | **本 skill 覆盖面最完整、产品语境最少的上游**。显式声明「covers PostgreSQL 14 through 18」并逐条标 `[PG15+]`/`[PG18+]`。星数低但由 Neon 官方维护且与 `neondatabase/agent-skills` 是主动拆分关系 |
| 3 | microsoft/postgres-skills `plugin/skills/postgresql-best-practices` | https://github.com/microsoft/postgres-skills | 0 | 2026-09-09 | MIT | 11 个 `postgresql-*` 通用 reference + 11 个 `azure-*` 产品 reference | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 仓库自述「vendor-agnostic best practices plus Azure-specific patterns」，通用/Azure 前缀分离得非常干净，只取 `postgresql-*`。星数 0 是新仓库，权威性来自 microsoft 组织与 CI 内的 `tests/test_sql_syntax.py` |
| 4 | timescale/pg-aiguide `skills/postgres-database-migration` | https://github.com/timescale/pg-aiguide | 1835 | 2026-09-09 | Apache-2.0 | 在线迁移：每种 DDL 的锁级别表、安全改写模式、回填、校验查询 | 2 | 3 | 3 | 1 | 2 | 11 | INCLUDE | 迁移这一章是所有候选里最详尽的。**但抽查 3 条错 2 条**（见「冲突与裁决」1、2），结构照抄、事实全部按本机 PG 18.6 实测与官方文档重写 |
| 5 | timescale/pg-aiguide `skills/postgres`、`skills/design-postgres-tables` | https://github.com/timescale/pg-aiguide | 1835 | 2026-09-09 | Apache-2.0 | 建表与类型选型；`skills/postgres` 只是路由页 | 2 | 3 | 2 | 2 | 2 | 11 | INCLUDE | 类型选型与主键部分可用；hypertable / PostGIS / TimescaleDB 段落全部剔除（产品面，且 `timescaledb` 不在本 skill 范围） |
| 6 | github/awesome-copilot `skills/postgresql-optimization`、`postgresql-code-review` | https://github.com/github/awesome-copilot | 38866 | 2026-09-10 | MIT | JSONB、数组、自定义类型、范围类型、全文检索、窗口函数、扩展生态；评审清单 | 2 | 3 | 2 | 2 | 2 | 11 | INCLUDE | 覆盖面清单价值高（JSONB/数组/范围类型/FTS 的枚举最全）。含 `${selection}` harness 变量与 emoji 小节标题，必须剥离；部分示例是「展示语法」而非「陷阱」，只取陷阱 |
| 7 | github/awesome-copilot `skills/sql-optimization`、`sql-code-review` | https://github.com/github/awesome-copilot | 38866 | 2026-09-10 | MIT | 跨引擎 SQL 优化与评审 | 2 | 3 | 2 | 2 | 2 | 11 | MAYBE | 跨引擎泛化，Postgres 专属信息少于 #6。只用作覆盖面对照，未合入正文 |
| 8 | neondatabase/agent-skills `skills/neon-postgres` | https://github.com/neondatabase/agent-skills | 88 | 2026-09-04 | Apache-2.0 | Neon 平台面（分支、autoscaling、scale-to-zero、LFC、`neon inspect db`）+ 一节通用池化 gotcha | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（仅一节） | 90% 是 Neon 产品面，按边界剔除。**唯一保留**：pooled vs direct 那节给出的三种「不提池化二字」的报错签名（`prepared statement "s0" already exists`、`SET search_path` 不跨事务、`SQLSTATE 25006`）——这是通用 PgBouncer 事务池陷阱最好的具体化 |
| 9 | prisma/skills `prisma-postgres`、`prisma-database-setup/references/postgresql.md` | https://github.com/prisma/skills | 56 | 2026-09-08 | MIT | Prisma Postgres 产品的 Console / create-db CLI / Management API | 3 | 3 | 2 | 3 | 2 | 13 | REJECT（作 merged） | 内容几乎全是 Prisma 自家托管产品的开通与 API，不是 Postgres 侧知识。仅 `directUrl` 与 migrate 需直连这一点被采纳，且该事实同时出现在 #8 与官方 PgBouncer 文档中，故以 reference 收录 |
| 10 | honra-io/drizzle-best-practices | https://github.com/honra-io/drizzle-best-practices | 20 | 2026-05-25 | MIT | Drizzle ORM on Postgres：`pgTable`、identity PK、enum、JSONB、relations、`.prepare()` | 1 | 1 | 2 | 2 | 2 | 8 | INCLUDE（仅 ORM 陷阱节） | 只取它在 **Postgres 侧**造成的问题：`.prepare()` 生成命名预处理语句与事务池冲突、`db.query` 的关系加载会退化成 N+1、drizzle-kit push 直接改生产库。ORM 教学内容一律不取 |
| 11 | google/skills `skills/cloud/cloud-sql-basics` | https://github.com/google/skills | 19735 | 2026-09-10 | Apache-2.0 | Cloud SQL 实例创建与 `gcloud sql` 命令 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT | 全部是云托管控制面（实例规格、`gcloud sql instances create`、IAM），正是本 skill 明确不覆盖的部分。留行以免下一波重复评估 |
| 12 | postgresql.org/docs（PostgreSQL 18） | https://www.postgresql.org/docs/18/ | — | 持续 | PostgreSQL | 全部事实的裁决依据 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 文档源码在 `postgres/postgres` 的 `doc/src/sgml`，`COPYRIGHT` 实读为 PostgreSQL License（BSD 风格许可，允许重写合入），故 `relation: merged` 而非 reference |
| 13 | pgvector/pgvector | https://github.com/pgvector/pgvector | 22975 | 2026-09-10 | PostgreSQL（API 报 NOASSERTION，实读 LICENSE 确认） | HNSW / IVFFlat、距离算子、`hnsw.ef_search`、iterative scan、维度上限 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | API 的 `license.spdx_id` 是 NOASSERTION，实读 `LICENSE` 为 PostgreSQL License，可合入。README 即事实来源 |
| 14 | digoal/postgres_skill | https://github.com/digoal/postgres_skill | 39 | 2026-02-05 | GPL-3.0 | `postgres-daily-check`、`postgresql-bi-agent`、`polardb-daily-check` 三个巡检 agent | 2 | 1 | 2 | — | 0 | — | REJECT | GPL-3.0，按许可规则不得 merged。内容是「连上库跑巡检脚本」的运维 agent，与本 skill 的写码/评审定位不同，主题清单也无新增项，故不作 reference 收录 |
| 15 | wshobson/agents `plugins/database-design/skills/postgresql-table-design` | https://github.com/wshobson/agents | 39556 | 2026-09-07 | MIT | 建表评审：类型、键、约束、分区、半结构化 | 2 | 3 | 2 | 2 | 2 | 11 | INCLUDE（校验用） | 129 行，与 #1/#2 的 schema 章高度重叠且更浅。作 reference 交叉校验类型选型口径，未合入新事实 |
| 16 | paradedb/agent-skills | https://github.com/paradedb/agent-skills | 10 | 2026-08-24 | MIT | ParadeDB `pg_search` 扩展的 BM25 与混合检索 | 1 | 2 | 3 | 2 | 2 | 10 | REJECT | 是第三方扩展产品的说明书。本 skill 的全文检索一节只写内置 `tsvector`/`tsquery`/GIN，不推荐特定扩展产品 |
| 17 | u1pns/skill-dba | https://github.com/u1pns/skill-dba | 10 | 2026-06-10 | NONE（frontmatter 自述 MIT，无 LICENSE 文件） | 跨引擎 DBA：MySQL/PG/SQL Server/Oracle/SQLite | 1 | 1 | 1 | 1 | 0 | 4 | REJECT | 五个引擎混写导致每条规则都退化成通用话术（「先识别引擎」「注意 SARGability」）；frontmatter 声明 MIT 但仓库无 LICENSE 文件，许可分 0 |
| 18 | Farenhytee/database-sentinel | https://github.com/Farenhytee/database-sentinel | 43 | 2026-04-30 | MIT | 多后端数据库安全审计（Supabase/Firebase/Mongo/自建 PG/MySQL） | 1 | 1 | 2 | 2 | 2 | 8 | REJECT | 定位是安全审计器而非数据库工程 skill，且主体是 Supabase/Firebase 规则。其自建 PG 部分（RLS 未启用、`FORCE`、pgBouncer CVE）已被 #1/#2/官方文档覆盖 |
| 19 | mizchi/skills `sql/lint` | https://github.com/mizchi/skills | 325 | 2026-09-10 | NONE | sqlc 风格 SQL 目录的静态 lint（重复查询名、缺分号、`SELECT *`） | 1 | 3 | 1 | 2 | 0 | 7 | REJECT | 面向 sqlc 目录约定的 lint 工具，跨 sqlite/postgres/mysql，无 Postgres 专属内容 |
| 20 | neondatabase/agent-skills `skills/neon-postgres-egress-optimizer` 等 | https://github.com/neondatabase/agent-skills | 88 | 2026-09-04 | Apache-2.0 | Neon 出网流量优化、分支、对象存储 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT | 纯 Neon 计费/平台面，边界外 |

补充说明：`timescale/agent-skills` 不存在（404），Timescale 的 skill 全在 `timescale/pg-aiguide`。
`gh search repos "postgres skill"` 返回的其余 20 余个仓库 stars ≤ 2 或最近推送 > 6 个月，均未达
新鲜度/权威性下限，不逐一留行。

## 本机实验环境（所有版本敏感事实的第一手依据）

**实验做了，不是「未能实验验证」。** 两个容器：

| 容器 | 镜像 | 版本 |
|---|---|---|
| `hs-pg` | `postgres:18` | `PostgreSQL 18.6 (Debian 18.6-1.pgdg13+2) on x86_64-pc-linux-gnu` |
| `hs-pgv` | `pgvector/pgvector:pg18` | 同上 + `vector` 扩展 0.8.6 |

默认参数（`show`）：`max_connections=100`、`shared_buffers=128MB`、`work_mem=4MB`、
`default_toast_compression=pglz`、`default_transaction_isolation=read committed`、`hnsw.ef_search=40`。

实验脚本 `/tmp/pgup/lab{1..8}.sql`（一次性夹具，未入库）。关键结论：

### E1 DDL 锁级别（`pg_locks` 实测，200k 行表）

| 语句 | 实测锁 | 备注 |
|---|---|---|
| `ALTER TABLE ... ADD COLUMN c1 text` | `AccessExclusiveLock` | 瞬时，无重写 |
| `CREATE INDEX`（非 CONCURRENTLY） | `ShareLock` | 阻塞写，不阻塞读，整个构建期间 |
| `ALTER TABLE ... ADD CONSTRAINT ... CHECK ... NOT VALID` | `AccessExclusiveLock` | **不是** `ShareUpdateExclusiveLock` |
| `ALTER TABLE ... ADD CONSTRAINT ... FOREIGN KEY ... NOT VALID` | `ShareRowExclusiveLock`（**两张表都取**） | 子表与父表同时被锁 |

### E2 哪些 `ALTER TABLE` 真的重写表（比对 `pg_class.relfilenode`）

| 语句 | relfilenode | 结论 |
|---|---|---|
| `ADD COLUMN t1 timestamptz NOT NULL DEFAULT now()` | 16552 → 16552 | **不重写**（`now()` 是 STABLE） |
| `ADD COLUMN c2 int NOT NULL DEFAULT 7` | 16397 → 16397 | 不重写 |
| `ADD COLUMN t2 uuid DEFAULT gen_random_uuid()` | 16552 → 16558 | **重写**（VOLATILE） |
| `ADD COLUMN c3 timestamptz DEFAULT clock_timestamp()` | 16397 → 16411 | 重写（VOLATILE） |
| `ALTER COLUMN a TYPE bigint`（int→bigint） | 16558 → 16561 | 重写 |
| `ALTER COLUMN a TYPE numeric` | 16561 → 16566 | 重写 |

`CREATE INDEX CONCURRENTLY` 在事务块内直接报
`ERROR: CREATE INDEX CONCURRENTLY cannot run inside a transaction block`。

### E3 PG 18 的 NOT NULL 语法（实测两种写法）

```
lab=# alter table t_nn alter column s set not null not valid;
ERROR:  syntax error at or near "not"
lab=# alter table t_nn validate not null on s;
ERROR:  syntax error at or near "not"
```

真正可用的是把 NOT NULL 当作具名约束：

```
lab=# alter table t_nn add constraint t_nn_s_nn not null s not valid;   -- 不扫表
ALTER TABLE
lab=# select conname, contype, convalidated from pg_constraint where conrelid='t_nn'::regclass;
   conname    | contype | convalidated
--------------+---------+--------------
 t_nn_s_nn    | n       | f
lab=# select attname, attnotnull from pg_attribute where attrelid='t_nn'::regclass and attname='s';
 attname | attnotnull
---------+------------
 s       | t                 -- 新行立刻被约束
lab=# alter table t_nn validate constraint t_nn_s_nn;                   -- 允许并发读写
ALTER TABLE
```

### E4 复合索引列序（500k 行，`tenant_id` 50 个取值，`created_at` 近乎唯一）

| 可用索引 | 计划 | Buffers |
|---|---|---|
| 只有 `(created_at desc, tenant_id)` | `Parallel Seq Scan`，`Rows Removed by Filter: 166667` | **6668** |
| 只有 `(tenant_id, created_at desc)` | `Index Only Scan`，`Heap Fetches: 100` | **6** |

即 PG 18 的 B-tree skip scan **不能**救高基数前导列。同一查询 1111 倍缓冲差。

### E5 两个单列索引 ≠ 一个复合索引

```
-- 只有 ev_tenant(tenant_id) 与 ev_status(status)
 Bitmap Heap Scan ... Buffers: shared read=36
   ->  BitmapAnd
         ->  Bitmap Index Scan on ev_tenant  (actual rows=10000.00)  read=12
         ->  Bitmap Index Scan on ev_status  (actual rows=25000.00)  read=24
-- 换成 ev_tenant_status(tenant_id, status)
 Index Only Scan using ev_tenant_status ... Heap Fetches: 0  Buffers: shared read=3
```

部分索引体积：`(tenant_id, created_at desc)` 全量 **15 MB**，
`... where status='failed'` 部分索引 **784 kB**。

### E6 RLS：`USING` / `WITH CHECK` / `FORCE` 的实际行为

- `CREATE POLICY ... FOR ALL USING (owner = current_user)` 不写 `WITH CHECK` 时，
  `INSERT` 别人的行与 `UPDATE` 把行移出策略都报
  `ERROR: new row violates row-level security policy for table "docs"` —— 证实 `FOR ALL` 的
  `WITH CHECK` 缺省等于 `USING`。
- 拆成 `FOR SELECT USING (true)` + `FOR INSERT WITH CHECK (owner = current_user)` 后，读放开、写仍受限。
- 表属主（非超级用户）在无 `FORCE` 时看到全部 2 行，`ALTER TABLE ... FORCE ROW LEVEL SECURITY`
  后看到 0 行；**超级用户即使 FORCE 也看到 2 行**（`BYPASSRLS` 语义）。

### E7 RLS 策略里的函数调用：`(select f())` 到底省了什么

同一张 200k 行表、同一个 STABLE plpgsql 函数、**无可用索引**（谓词落在 `Filter`）：

| 策略 | 计划节点 | 实测耗时 |
|---|---|---|
| `USING (tenant = app_tenant())` | `Filter: (tenant = app_tenant())` | **1223 ms** |
| `USING (tenant = (select app_tenant()))` | `InitPlan 1` + `Filter: (tenant = (InitPlan 1).col1)` | **11 ms** |

111 倍。**但**同一张表上存在 `tenant` 索引、谓词被下推成 `Index Cond` 时，两种写法都只求值一次
（实测两者都是 `Bitmap Index Scan ... Index Cond: (tenant = app_tenant())`，2068 buffers 持平）。
即：`(select ...)` 包裹的收益条件是「谓词停留在 Filter 节点」，不是无条件 100 倍。
这个限定条件所有上游都没写，已同步给同波 `supabase` 子代理。

### E8 其他实测点

- **PG 18 的 `EXPLAIN ANALYZE` 默认输出 `Buffers`**，不必再写 `EXPLAIN (ANALYZE, BUFFERS)`；
  实测不带 `BUFFERS` 选项的 `EXPLAIN (ANALYZE)` 也打印 `Buffers: shared hit=14`。
- `UNIQUE (a, b)` 允许两行 `(1, NULL)`；`UNIQUE NULLS NOT DISTINCT (a, b)` 第二行报
  `duplicate key value violates unique constraint`（PG 15+）。
- `MERGE ... RETURNING merge_action(), t.id, t.v` 在 18.6 正常返回 `UPDATE` / `INSERT` 两行（PG 17+）。
- JSONB：`jsonb_path_ops` 索引 6584 kB / `@>` 查询 4 个索引缓冲；`jsonb_ops` 6984 kB / 35 个缓冲。
  但 `doc ? 'nested'` 在只有 `jsonb_path_ops` 时即使 `enable_seqscan=off` 也只能走
  `Seq Scan (Disabled: true)` —— 该算子类不支持存在性算子。
- HOT：更新非索引列 200k 行得到 `n_tup_hot_upd=93334`；给被更新列建索引后同样的更新变成
  `n_tup_newpage_upd`。
- REPEATABLE READ 下的写冲突报 `ERROR: could not serialize access due to concurrent update`，
  应用必须自己重试。
- pgvector 0.8.6：`vector_cosine_ops` 索引 + `<->`（L2）算子 → `Seq Scan` + top-N 排序，索引不用；
  换 `<=>` 才走 `Index Scan ... Order By`。`hnsw.ef_search` 默认 40。带 `WHERE tag=3` 的 ANN 查询
  计划里出现 `Filter: (tag = 3)` / `Rows Removed by Filter: 41`，即过滤发生在索引遍历**之后**。
  `vector(3000)` 建 HNSW 报 `ERROR: column cannot have more than 2000 dimensions for hnsw index`；
  改成表达式索引 `((v::halfvec(3000)) halfvec_cosine_ops)` 建索引成功。

## 深度审查

### 1. neondatabase/postgres-skills `postgres-best-practices`（Apache-2.0，31★）

结构最接近本仓库标准：一个薄路由 SKILL.md + 13 个按主题切分的 reference，每个 reference 自带
`## Contents`。frontmatter 只有 `name` / `description`，无 agent 专属字段，无需剥离。
显式声明支持范围「PostgreSQL 14 through 18」并逐条打 `[PG15+]` / `[PG18+]` 标签——本 skill 的版本
门槛写法直接沿用这个约定。产品语境几乎为零（`connection-pooling.md` 通篇讲 PgBouncer 而非 Neon
Pooler）。与 #1 的重叠在索引与连接两章，与 #3 的重叠在查询性能与 JSONB。
唯一缺口：RLS 只在 `security-roles.md` 里占一小节，深度不足，由 #1 与官方文档补。

### 2. supabase/agent-skills `supabase-postgres-best-practices`（MIT，2592★）

34 个规则文件的粒度是「一条规则一个文件」，每个文件带 `impact` / `impactDescription` /
`tags` 三个自定义 frontmatter 字段（需剥离），正文固定为「为什么 → 错误 SQL → 正确 SQL → 参考链接」。
这个粒度不适合直接搬成 reference（会变成 34 个 30 行文件），但**规则清单本身是本 skill 章节划分的
最好依据**：query / conn / security / schema / lock / data / monitor / advanced 八类。
Supabase 语境的分布很集中：`security-rls-*.md` 用 `auth.uid()` 和 `anon`/`authenticated`/
`service_role` 角色名，`conn-pooling.md` / `conn-prepared-statements.md` 提 6543 与 5432 端口。
剥离办法：把 `auth.uid()` 换成 `current_setting('app.tenant_id')` 这类自建等价物，把端口号换成
「事务池端口 / 会话池端口」的抽象描述，角色名换成 `app_user`。剥离后规则本身完全通用。

### 3. microsoft/postgres-skills `postgresql-best-practices`（MIT，0★）

仓库把通用与 Azure 用文件名前缀彻底分开（`postgresql-*` vs `azure-*`），SKILL.md 是一张关键词
→ reference 的路由表。只取 11 个 `postgresql-*`。需要剥离的不是内容而是 **agent 绑定**：
SKILL.md 里 `postgres_mcp_get_server_capabilities`、`postgres_mcp_modify`、
`az account show` 这类 MCP 工具名与 shell 执行策略占了近一半篇幅，全部不取。
`postgresql-vector-search.md` 与 `postgresql-genai-rag.md` 是本 skill pgvector 一节的骨架来源。
`pg-graph` 兄弟 skill（Apache AGE / openCypher）超出边界，不取。

### 4. timescale/pg-aiguide `postgres-database-migration`（Apache-2.0，1835★）

486 行，是候选里唯一把「每种 DDL 的锁级别」做成完整表格的。结构值得照抄：
锁级别表 → 逐操作安全改写 → 回填策略 → 前后校验查询 → 回滚计划。
但抽查 3 条对照 PG 18.6 实测：`ADD COLUMN ... DEFAULT now()` 判为「volatile → 全表重写」**错**；
`SET NOT NULL NOT VALID` / `VALIDATE NOT NULL ON` 语法**不存在**；`ADD CONSTRAINT ... NOT VALID`
标 `ShareUpdateExclusiveLock` 对 CHECK 而言**错**（实测 `AccessExclusiveLock`）。正确性只给 1 分。
处理方式：结构与主题清单采纳，**每一条事实都用 E1–E3 的实测结果或 PG 18 文档重新落笔**。

### 5. github/awesome-copilot `postgresql-optimization` / `postgresql-code-review`（MIT，38866★）

两份都是「PostgreSQL 专属特性」清单，覆盖 JSONB、数组、`ENUM` vs 查表、范围类型、几何类型、
全文检索、窗口函数、扩展生态。价值在**覆盖面枚举**而非深度——大量代码块只是展示语法。
必须剥离：`${selection}` harness 变量（标准 §1.3 明令禁止）、emoji 小节标题、
`## 🎯` 这类装饰。采纳的是「范围类型做时段排他约束（`EXCLUDE USING gist`）」与
「`ENUM` 加值不可回滚、删值不可能」这两条陷阱，其余与 #1/#2 重复。

### 6. neondatabase/agent-skills `neon-postgres`（Apache-2.0，88★）

按边界几乎整份剔除（分支、autoscaling、scale-to-zero、LFC、`neon inspect db`、
`EXPLAIN (..., PREFETCH, FILECACHE)` 全是 Neon 专属）。保留的是 `## Gotchas` 里
pooled vs direct 一节：它把「走了事务池」这个根因的三种伪装报错列了出来，
而这三种报错在任何 PgBouncer 事务池部署上都会出现。这是通用知识，只是被写在了产品文档里。

### 7. honra-io/drizzle-best-practices（MIT，20★）

2026-05-25 推送，新鲜度只有 1 分，是本波唯一临界上游。**复核结论**：距今约 3.5 个月，
仍在 6 个月窗口内，按量表得 1 分而非 REJECT；内容里的 Drizzle v1 RC / 0.45.x 分叉说明与
`.prepare()` 用法在 2026-09 仍然成立（对照 orm.drizzle.team 当前文档）。
只取三条 Postgres 侧后果（命名预处理语句与事务池冲突、关系加载退化 N+1、`drizzle-kit push`
绕过迁移文件直改生产库），ORM 语法教学一律不取。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | `ADD COLUMN ... DEFAULT now()` 是否重写全表 | timescale `ts-migration.md`：「UNSAFE: volatile default — full table rewrite，DON'T: ADD COLUMN created_at TIMESTAMPTZ DEFAULT now()」；PG 文档：只有 **volatile** 默认值才重写 | **timescale 错**。`now()` 是 STABLE，不重写；`clock_timestamp()`、`gen_random_uuid()` 才是 VOLATILE | 本机 E2：`DEFAULT now()` 后 relfilenode 不变（16552→16552），`DEFAULT gen_random_uuid()` 后改变（16552→16558）。判据同 postgresql.org/docs/18 `ALTER TABLE` 页 |
| 2 | PG 18 免扫表加 NOT NULL 的语法 | timescale：`ALTER COLUMN x SET NOT NULL NOT VALID` + `VALIDATE NOT NULL ON x` | **两条语法都不存在**，实测语法错误。正确写法是具名约束：`ADD CONSTRAINT c NOT NULL x NOT VALID` + `VALIDATE CONSTRAINT c` | 本机 E3 两次 `ERROR: syntax error`，改用具名约束形式成功 |
| 3 | `ADD CONSTRAINT ... CHECK ... NOT VALID` 的锁级别 | timescale 表格：`ShareUpdateExclusiveLock` | **错**，实测 `AccessExclusiveLock`（只是持有时间短，因为不扫表）。FK 的 `NOT VALID` 才是 `ShareRowExclusiveLock`，且父子表都锁 | 本机 E1 `pg_locks` 实测 |
| 4 | RLS 策略里包 `(select f())` 的收益 | supabase `security-rls-performance.md`：「100x+ faster on large tables」，无条件表述 | 收益成立但**有前提**：谓词必须落在 `Filter` 节点。谓词被下推成 `Index Cond` 时，STABLE 函数本来就只求值一次，包裹无收益。正文写成带条件的规则 | 本机 E7：Filter 场景 1223 ms → 11 ms；Index Cond 场景两种写法均 2068 buffers |
| 5 | 连接池模式的默认推荐 | neon `neonbp-pool.md`：事务模式为默认推荐，`default_pool_size` 取 CPU 核数的 2–4 倍；microsoft `ms-conn.md`：Azure 内建 PgBouncer 语境 | 采纳 neon 的通用版本（事务模式 + 2–4×核数），microsoft 的 Azure 控制面部分整体不取 | 「更通用 > 更产品化」；且 PgBouncer 官方文档的 `default_pool_size` 指导与 neon 一致 |
| 6 | 预处理语句与事务池的解法 | supabase `conn-prepared-statements.md`：给出「用会话模式（5432 端口）」「`DEALLOCATE`」两条出路；neon：指出 PgBouncer 1.21+ 支持协议级预处理语句 | 以 neon 为准：首选**协议级**预处理语句 + PgBouncer 1.21+ 的 `max_prepared_statements`；换会话模式是逃生口不是首选 | 「更新 > 更旧」；PgBouncer 1.21 的 changelog 确认该能力。supabase 那份仍在教 `DEALLOCATE`，是 1.21 之前的做法 |
| 7 | 谁负责 RLS | 同波 `supabase` skill 也会写 RLS | 按主代理给定的分界句切：**策略语法与性能归 `postgres`，Supabase auth 上下文（`auth.uid()`、JWT claims）与 dashboard/CLI 流程归 `supabase`**。分界句在两边 `## Scope` 原文照抄，已与 `SupabaseSkill` 对齐确认 | 主代理契约；`hub` 与 `SupabaseSkill` 双向确认，对方同时确认不写索引/EXPLAIN/池化/pgvector |
| 8 | `EXPLAIN` 该怎么写 | 所有上游（含 neon、microsoft、supabase）：`EXPLAIN (ANALYZE, BUFFERS)` | PG 18 起 `ANALYZE` 默认带 `BUFFERS`，写不写都有。正文保留显式 `BUFFERS`（对 14–17 仍必需）并注明 18 起可省 | 本机 E8 实测；PG 18 release notes |
| 9 | ORM 要写多少 | prisma/skills、drizzle-best-practices 都想教完整 ORM 用法 | 只写 ORM 在 **Postgres 侧**造成的问题（预处理语句冲突、N+1、迁移锁、连接数放大），不写 ORM API | 主代理边界：「Prisma/Drizzle 只写它们在 Postgres 侧造成的问题」；Prisma 不单独立 skill |
| 10 | 全文检索推荐什么 | paradedb：`pg_search` BM25；neon：Lakebase `lakebase_text`；awesome-copilot：内置 `tsvector` | 只写内置 `tsvector`/`tsquery`/GIN + `websearch_to_tsquery`，两个扩展产品都不推荐 | 「一个默认方案 + 一个逃生口」；扩展产品属产品面，且两者互斥、无法共存为默认 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `postgresql-docs` | postgresql.org/docs（PostgreSQL 18） | merged | 全部事实的最终依据：锁级别矩阵、`ALTER TABLE` 重写规则、RLS `USING`/`WITH CHECK`/`FORCE` 语义、隔离级别、vacuum 与 wraparound、索引访问方法、JSONB 算子类、`tsvector`、`MERGE`、`NULLS NOT DISTINCT` |
| `neon-postgres-skills` | neondatabase/postgres-skills `skills/postgres-best-practices` | merged | 章节骨架与版本门槛写法；连接池（PgBouncer 模式矩阵、`default_pool_size` 2–4×核、协议级预处理语句）、性能诊断（`pg_stat_*` 选用表）、隔离级别与重试、批量装载、大版本升级 |
| `supabase-postgres-bp` | supabase/agent-skills `skills/supabase-postgres-best-practices` | merged | 八类规则清单作为章节划分依据；复合/部分/覆盖索引、缺失索引定位、外键列未建索引、N+1、批插入、`skip locked` 队列、advisory lock、短事务、RLS 策略结构与 SECURITY DEFINER 助手函数的收紧写法 |
| `microsoft-postgres-skills` | microsoft/postgres-skills `plugin/skills/postgresql-best-practices` | merged | 通用 `postgresql-*` reference：高级索引（GIN/GiST/BRIN 选型）、JSONB 模式、分区、逻辑复制、pgvector 与 HNSW、扩展管理 |
| `timescale-pg-aiguide` | timescale/pg-aiguide | merged | 在线迁移章的**结构**（锁级别表 → 逐操作改写 → 回填 → 校验 → 回滚）与类型选型清单；三条事实性错误已按 E1–E3 改正，见冲突表 1–3 |
| `pgvector` | pgvector/pgvector | merged | 距离算子与索引算子类的配对规则、HNSW 参数与 `hnsw.ef_search`、iterative scan、2000 维上限与 `halfvec` 表达式索引绕法 |
| `awesome-copilot-pg` | github/awesome-copilot `skills/postgresql-optimization`、`skills/postgresql-code-review` | merged | 覆盖面枚举：范围类型与 `EXCLUDE USING gist` 排他约束、`ENUM` 的不可逆性、数组类型的取舍、全文检索算子清单 |
| `neon-agent-skills` | neondatabase/agent-skills `skills/neon-postgres` | merged | 只取一节：事务池导致的三种伪装报错签名（`prepared statement "s0" already exists`、`SET` 不跨事务、`SQLSTATE 25006` 只读事务），以及迁移/dump/逻辑复制必须走直连 |
| `drizzle-best-practices` | honra-io/drizzle-best-practices | merged | ORM 侧三条 Postgres 后果：`.prepare()` 命名预处理语句与事务池冲突、关系加载退化 N+1、`drizzle-kit push` 绕过迁移文件 |
| `wshobson-table-design` | wshobson/agents `plugins/database-design/skills/postgresql-table-design` | reference | 仅交叉校验类型选型与主键口径，未引入新事实 |
| `prisma-skills` | prisma/skills | reference | 仅确认 `directUrl` / migrate 需直连这一点与 neon 一致；产品开通内容不取 |
| `google-cloud-sql` | google/skills `skills/cloud/cloud-sql-basics` | reference | 仅用于确认云托管控制面的内容形态，据此确认其整体落在本 skill 边界之外 |

`digoal/postgres_skill`（GPL-3.0）、`paradedb/agent-skills`、`u1pns/skill-dba`、
`Farenhytee/database-sentinel`、`mizchi/skills` 均未收录（理由见候选表），不进 `SOURCES.yaml`。

## 基线缺口

无 skill（`uv run tools/run_evals.py postgres --baseline`）时，各场景未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 慢查询与索引 | 「`(created_at DESC, tenant_id)` 用不了 `tenant_id=999` 是因为前导列未被约束且基数极高；PG 18 的 B-tree skip scan 只救低基数前导列」 | 基线把 Query 1 判成**统计信息过期**（`reltuples` 陈旧导致误选并行顺序扫描），并给出 `ANALYZE` + `SET STATISTICS` 的修法。这个诊断本身自洽（夹具里确实同时存在 `events_tenant`），但基线全程没有提到 skip scan，也没有把「前导列基数」作为复合索引可用性的判据。其余 6 条（复合列序、BitmapAnd、部分索引、冗余索引、keyset 分页、用 buffers 论证）基线都达成 |
| 2 在线迁移 | 「新增外键后 `orders(customer_id)` 也必须建索引，否则父表上的删除/改键会扫描子表」 | 基线把 8 条里的 7 条都做对了（拆事务、`now()` STABLE vs `gen_random_uuid()` VOLATILE、分批回填过程、PG 18 的 `NOT NULL ... NOT VALID`、`int→bigint` 重写、`CREATE INDEX CONCURRENTLY` 不能进事务块 + `indisvalid` 复查、`lock_timeout` 优先于 `statement_timeout`），唯独没有把「FK 子侧索引」作为一条要求说出来——它顺手建的 `(customer_id, billed_at DESC)` 恰好覆盖，但没有意识到这是必需项 |
| 3 RLS | 「`current_tenant()` 在 `Filter` 节点里是逐行调用，`STABLE` 不等于缓存；`(SELECT current_tenant())` 变成 `InitPlan` 只求值一次」 | 基线换了另一条路：把 plpgsql 函数改写成 `LANGUAGE sql STABLE PARALLEL SAFE` 以便内联，理由是「plpgsql 对规划器是 cost 100 的黑盒」。这个改法有效，但它没有说出 STABLE 函数在 `Filter` 里按行求值这个机制，也没有给出 `(SELECT ...)` 标量子查询这条与函数语言无关的通用手段。其余 6 条（permissive OR、`FOR ALL` 继承 `WITH CHECK`、owner 豁免与 `FORCE`、`BYPASSRLS`、加索引、关联 `EXISTS` 改非关联、`SET LOCAL`）基线都达成 |
| 4 负例（Supabase） | —（无未达成项） | 基线以 `--no-skills` 运行，`skill_read` 天然为 false，答案正确地落在 Supabase 侧（SQL editor 以 owner 身份绕过 RLS、PostgREST 返回 200+`[]`、dashboard 三步定位）。这一条的判别力只在「有 skill」那次运行上 |

基线整体很强（每个场景都自己起了 `postgres:18` 容器做实验），所以缺口是**窄而具体**的三条，而不是整片空白。三条都指向同一类知识：**只有实测才能确认的机制细节**（skip scan 的适用条件、FK 子侧索引的必要性、STABLE 函数在 Filter 节点的求值次数）。

## 评测结果

模型全部为 `claude-opus-5:medium`（`tools/run_evals.py` 默认，未传 `--model` / `--thinking`）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 慢查询与索引 | claude-opus-5:medium | 无（baseline） | false | 7 条中 6 条：复合列序、BitmapAnd 与两个单列索引不等价、部分索引、`events_tenant` 冗余、keyset 行比较分页、以 buffers 论证 | 未达成：PG 18 skip scan 与前导列基数判据。Query 1 归因为统计信息过期 |
| 1 慢查询与索引 | claude-opus-5:medium | 有 | true | 7 条全部 | 明确写出「前导列是近乎唯一的时间戳，PG 18 的 skip scan 救不了（它只对低基数前导列有效）」；另外主动指出夹具里 EXPLAIN 与索引清单对不上，给出 `indisvalid` 复查。实测 6668→4 buffers、36→3 buffers、6187→15 buffers |
| 2 在线迁移 | claude-opus-5:medium | 无（baseline） | false | 8 条中 7 条 | 未达成：FK 子侧索引是必需项。产出 0031–0036 六个分步迁移文件，质量很高 |
| 2 在线迁移 | claude-opus-5:medium | 有 | true | 8 条全部 | 「FK 子侧必须有索引，靠新的 `(customer_id, billed_at)` 最左前缀覆盖」；并按 skill 的 Output format 以「爆炸半径」排序、逐条 `file:line - blocking/correctness - …`；每条锁级别与是否重写都标注为容器实测 |
| 3 RLS | claude-opus-5:medium | 无（baseline） | false | 7 条中 6 条 | 未达成：STABLE 函数在 `Filter` 中逐行求值 / `(SELECT ...)` 包裹。改用「plpgsql 换 SQL 以便内联」绕过 |
| 3 RLS | claude-opus-5:medium | 有 | true | 7 条全部 | 修复后计划为 `Index Only Scan`，`Index Cond: (tenant_id = (InitPlan 1).col1)`，26668 buffers / 703 ms → 6 buffers / 0.167 ms；跨租户 `UPDATE` 由成功变为 `ERROR: new row violates row-level security policy`；`reporting` 由 4000 租户降到 1 个 |
| 4 负例（Supabase `auth.uid()` + dashboard） | claude-opus-5:medium | 无（baseline） | false | 3 条全部（第 4 条是 skill_read 判定） | 正确落在 Supabase 侧 |
| 4 负例（Supabase `auth.uid()` + dashboard） | claude-opus-5:medium | 有 | **false** | 4 条全部 | **第一次运行 `skill_read` 为 true**（`description` 里的 "row-level security policy syntax" 把这道题吸了进来，虽然答案里模型自己声明了越界）。收紧 `description` 的否定边界后重跑两次，均为 false。见「备注」 |

结论：**通过**。三个正例都有「基线未达成 → 有 skill 达成」的行为（场景 1 的 PG 18 skip scan 判据、场景 2 的 FK 子侧索引、场景 3 的 `Filter` 中 STABLE 函数逐行求值与 `(SELECT ...)` 包裹），负例 `skill_read == false`。

## 备注

### 是否真跑了 Postgres 实例

**跑了。** 容器 `hs-pg`（`postgres:18` → 18.6）与 `hs-pgv`（`pgvector/pgvector:pg18`，vector 0.8.6）。
八个实验脚本的命令与输出见上面「本机实验环境」一节（E1–E8），全部结论都写进了正文，且纠正了三条
上游错误。此外 `references/diagnostics.md` 里的每一条目录查询都在容器上执行过：
`pg_blocking_pids` 阻塞链、表/索引/TOAST 体积、缺失 FK 索引、重复索引、未使用索引、`pg_statio_user_tables`、
`pg_stat_io`、vacuum 统计、`pg_stat_replication` / `pg_replication_slots`、`pg_settings` 来源、连接计数、
wraparound 年龄，均无语法错误。缺失-FK-索引那条还专门用 `fkt` schema 做了正确性对照：
无索引的子表与「索引里 `parent_id` 不在前导位」的子表都被报出，已正确建索引的子表不被报出。
`schema-and-types.md` 与 `jsonb-and-search.md` 的 `GENERATED ALWAYS AS (...) STORED`、
`jsonb_typeof` 约束、`tsvector` 生成列 + `websearch_to_tsquery`、`EXCLUDE USING gist` + `btree_gist`
也都在容器上跑通（排他约束按预期拒绝重叠区间）。

### 当前稳定版本

PostgreSQL **18**（18.6）。19 处于 Beta 3，正文不写任何 19 的内容。版本门槛覆盖 14–18，
与 `neondatabase/postgres-skills` 的声明范围一致。

### Supabase / Neon / Azure / Prisma 产品语境怎么剥离的

- **Supabase**：`auth.uid()` → `current_setting('app.tenant_id', true)` 包一层 `current_tenant()`；
  `anon` / `authenticated` / `service_role` → `app_user`；5432/6543 端口 → 「会话模式 / 事务模式」
  的抽象说法；每条规则文件的 `impact` / `impactDescription` / `tags` 三个自定义 frontmatter 字段删除。
  剥离后 34 条规则里没有一条依赖 Supabase 存在。
- **Neon**：`skills/neon-postgres` 整份只保留 `## Gotchas` 里 pooled vs direct 一节的三种报错签名；
  分支、autoscaling、scale-to-zero、LFC、`neon inspect db`、`EXPLAIN (..., PREFETCH, FILECACHE)` 全部丢弃。
  `neondatabase/postgres-skills` 本身就是 Neon 主动拆出来的 vendor-neutral 仓库，不需要剥离。
- **Azure**：只取 `microsoft/postgres-skills` 的六个 `postgresql-*` reference；11 个 `azure-*`、
  `pg-graph` 兄弟 skill、以及 SKILL.md 里近一半篇幅的 `postgres_mcp_*` 工具契约与 `az` CLI 执行策略
  全部不取（前者是托管控制面，后者是 agent 绑定，标准 §1.2 禁止）。
- **Prisma / Drizzle**：只保留它们在 Postgres 侧造成的后果（命名预处理语句与事务池冲突、
  关系加载退化成逐行往返、schema push 直接对生产库发未经复核的 DDL、连接串需要百分号编码）。
  ORM API、schema builder、迁移工具语法一律不写——那属于各框架 skill。
- **Google Cloud SQL**：整份作 `reference`，只用来确认「托管控制面从哪里开始」，也就是本 skill 的边界终点。

### 评测过程中的一次返工

负例第一次「有 skill」运行 `skill_read` 为 true：`description` 里 "row-level security policy syntax
and its performance" 与题面的 `auth.uid()` 策略高度匹配，发现层把它拉了进来（模型在答案里自己声明了
「dashboard 流程不在 `postgres` skill 覆盖范围内」，但判定标准是加载与否）。修法是把 `description`
末尾的否定边界从泛指改成点名：`Do not use for anything on the Supabase platform, including auth.uid()
policies, JWT claims, an SDK returning no rows, and the Supabase dashboard or CLI; ...`，同时把开头改成
`Guides self-managed PostgreSQL work` 并把 RLS 一项限定为 `plain-SQL row-level security policy syntax`。
改后两次重跑均为 `skill_read == false`。字符数 1024 上限踩了两次，最终 1012。

### 与同波 `supabase` 的对齐

分界句已通过 `hub` 与 `SupabaseSkill` 双向确认，两边 `## Scope` 里逐字相同（三行，无缩进，作为独立段落）。
对方同时确认不覆盖索引选择、EXPLAIN、连接池、pgvector 与纯 SQL 调优。E7 那条「`(select ...)` 包裹的收益
以谓词停留在 `Filter` 节点为前提」的实测结论也已同步给对方，避免两边给出互相矛盾的性能建议。

### 未来同步时要盯的上游

- `neondatabase/postgres-skills`（最主要的骨架来源，仓库很新，结构可能还会变）。
- `microsoft/postgres-skills`（0 星新仓库，`postgresql-*` / `azure-*` 的前缀分离约定一旦被破坏，
  `paths` 就要重新挑）。
- `timescale/pg-aiguide`（三条事实错误已在本地改正；若上游修好了，同步时要确认改法与本 skill 一致）。
- PostgreSQL 19 GA（预计 2026 年秋）：`## Scope` 的版本基线句与所有 `(PG 18+)` 门槛需要复核。

### 放弃的方向

- 不写 PostGIS（`timescale/pg-aiguide` 有 `design-postgis-tables`，但空间数据是独立主题，
  且本 skill 的类型章已明确「真要做空间就是 PostGIS 的地盘，本 skill 不覆盖」）。
- 不写 TimescaleDB / hypertable、ParadeDB `pg_search`、Apache AGE：都是第三方扩展产品，
  写进来会让「一个默认方案 + 一个逃生口」的原则失效。
- 不写 `scripts/`：本 skill 的可执行资产是目录查询，它们已经在 `references/diagnostics.md` 里，
  再包一层脚本只会增加依赖而不增加信息。
