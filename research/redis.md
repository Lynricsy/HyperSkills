# redis 调研记录

单一权威上游改写

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"redis skill SKILL.md github"`、`"redis" caching best practices skill`
  - <https://www.skills.sh>（经 `web_search` 的 site 检索间接覆盖）
  - VoltAgent/awesome-agent-skills（34040★，MIT，pushed 2026-09-07）目录内无独立 redis skill
  - `gh api search/repositories?q=redis+skill`、`q=redis+agent-skills`（两轮，各取前 30–40）
  - `github/awesome-copilot` 的 `skills/` 与 `instructions/`：全树 grep `redis|valkey|cache|memcach`，
    只命中 `skills/upstash-redis`（`instructions/` 无 redis 条目）
  - 领域官方组织：`redis/`（agent-skills、docs、redis、redis-py、redis-vl-python、node-redis、go-redis）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- 目录列举：`gh api repos/<o>/<r>/git/trees/<ref>?recursive=1`；读文件
  `gh api repos/<o>/<r>/contents/<path> --jq .content | base64 -d`
- `gh auth status`：已登录 github.com（账号 Lynricsy，scopes gist/read:org/repo/workflow），全程未限流。

### 当前稳定版本核实

`gh api repos/redis/redis/releases` 的最新非 prerelease 是 **8.10.1**（2026-08-17），
同批还发布了 8.8.2 / 8.6.6 / 8.4.6 / 8.2.9 / 7.4.11 / 7.2.16 / 6.2.24 —— 即 Redis 同时维护多条
8.x 线。正文以 **8.10** 为基准写作，凡需要高于 7.2 的规则一律加版本门（如 `(7.4+)`、`(8.0+)`、`(8.4+)`）。
本地实验实例 `redis:8-alpine` 报告 `redis_version:8.10.1`，与 releases 一致。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | redis/agent-skills `skills/redis-core` | https://github.com/redis/agent-skills | 146 | 2026-09-08 | MIT | 数据结构选型、键命名 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE (merged) | 官方主干。67 行，选型表 + 键名约定；深度浅（没有编码阈值、没有过期/淘汰），但表格就是覆盖面清单 |
| 2 | redis/agent-skills `skills/redis-connections` | 同上 | 146 | 2026-09-08 | MIT | 池化/多路复用、流水线、SCAN、CSC、超时 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | 本波最具体的一份：Lettuce/NRedisStack 多路复用不能承载阻塞命令这一条别处没有 |
| 3 | redis/agent-skills `skills/redis-clustering` | 同上 | 146 | 2026-09-08 | MIT | hash tag、CROSSSLOT、读副本 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | `{user:1001}` 而非 `{1001}` 的理由（跨命名空间撞槽）是实战级细节 |
| 4 | redis/agent-skills `skills/redis-search` | 同上 | 146 | 2026-09-08 | MIT | FT.CREATE / 查询 DSL / 向量 / 混合检索 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | 220 行 SKILL + 21 个 reference，是整个候选池里唯一系统覆盖 RQE 的；`FT.HYBRID` 标了 8.4 版本门 |
| 5 | redis/agent-skills `skills/redis-security` | 同上 | 146 | 2026-09-08 | MIT | requirepass/ACL/TLS/网络/改名命令 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE (merged) | ACL 类别表与 `~cache:*` 例子可用；`rename-command` 建议需按 8.x 现状复核（见冲突 5） |
| 6 | redis/agent-skills `skills/redis-observability` | 同上 | 146 | 2026-09-08 | MIT | INFO 指标、SLOWLOG、MEMORY DOCTOR | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE (merged) | 指标 + 告警阈值表直接可用；Redis Insight 段是产品面，剥离 |
| 7 | redis/agent-skills `skills/redis-semantic-cache` | 同上 | 146 | 2026-09-08 | MIT | LangCache 语义缓存 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE (部分 merged) | 只取与产品无关的语义：相似度阈值取值区间、按任务分缓存、属性过滤。LangCache 的 SDK/REST/cache_id 是 Redis Cloud 预览产品面，剥离 |
| 8 | redis/agent-skills `skills/iris-development` | 同上 | 146 | 2026-09-08 | MIT | Redis Cloud「Iris」agent 记忆服务 | 3 | 3 | 2 | 3 | 2 | — | REJECT | 范围外：整份是托管 agent-memory 产品（session/LTM API、auth token、cloud service 开通），不是 Redis 侧知识 |
| 9 | redis.io/docs（源：redis/docs） | https://redis.io/docs/latest/ | 80 | 2026-09-10 | **CC-BY-NC-SA-4.0** | 官方文档全站 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE (**reference**) | 实读 `redis/docs` 的 LICENSE：全站是 CC-BY-**NC**-SA-4.0（禁商用），另有「原 redis-doc 的部分」按 CC-BY-SA-4.0。NC 不是开源许可 → 按标准第 9 节「专有 = 不得作为 merged」处理为 reference，只据以核实事实并全部改写 |
| 10 | redis/redis（服务端源码与 LICENSE.txt） | https://github.com/redis/redis | 76310 | 2026-09-10 | RSALv2 / SSPLv1 / AGPLv3 三选一 | 服务端本体 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE (**reference**) | 实读 LICENSE.txt：Redis 8 起三重许可（RSALv2 / SSPLv1 / AGPLv3），7.2 及更早为 BSD-3。三者都不可 merged → reference，仅用于确认版本线与默认配置，事实改由本机实例实测 |
| 11 | github/awesome-copilot `skills/upstash-redis` | https://github.com/github/awesome-copilot | 38872 | 2026-09-10 | MIT | cache-aside、会话滑动过期、限流 | 2 | 3 | 3 | 2 | 2 | 12 | INCLUDE (merged) | GitHub 官方目录收录、Upstash 撰写。缓存/会话/限流的键形状与 checkpoint 写法可用；但「每条命令一次 HTTP」「不要 JSON.stringify」是 Upstash REST 客户端专属，与自管 Redis 相反 → 正确性扣 1，产品面全部剥离 |
| 12 | redis/redis-vl-python（RedisVL） | https://github.com/redis/redis-vl-python | 425 | 2026-09-10 | MIT | 向量索引、语义缓存、embedding 缓存 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | 官方 Python 库，`redisvl/extensions/cache/llm/semantic.py` 与 `docs/user_guide/03_llmcache.ipynb` 给出语义缓存的真实参数（距离阈值而非相似度、TTL、按 embedding 模型分索引），补上第 7 项剥离产品面后的空缺 |
| 13 | iamdemetris/lude-kit `skills/stacks/redis-expert` | https://github.com/iamdemetris/lude-kit | 0 | 2026-07-17 | Apache-2.0（API 报 NOASSERTION，实读 LICENSE 为 Apache-2.0） | 持久化/淘汰/Sentinel/Cluster/Streams/Lua | 1 | 2 | 1 | 2 | 2 | 8 | MAYBE (**reference**) | 通篇 persona（"You are a senior Redis operator"）+ agent 路由（`route to senior-backend-engineer` / `postgres-expert`），按标准 1.2/1.3 不可合入；但它的触发词清单是本池唯一同时点到 RDB/AOF、Sentinel、hot key、LATENCY DOCTOR、EVALSHA 的，用作覆盖面对照 |
| 14 | redis/redis-py | https://github.com/redis/redis-py | 13632 | 2026-09-10 | MIT | 官方 Python 客户端 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE (**reference**) | 只用于交叉核对客户端侧默认值（连接池上限、`socket_timeout` 默认 None、RESP3 与 `CacheConfig`）。客户端 API 本身不是本 skill 主体，未合入代码 |
| 15 | simba-git/redis-best-practices | https://github.com/simba-git/redis-best-practices | 1 | 2026-01-24 | MIT | rules/*.md（hash-tags、pipelining、pooling…） | 1 | 0 | 2 | 2 | 2 | 7 | REJECT | 文件名与内容与 redis/agent-skills 的 references 一一对应，是官方仓库之前的个人版；>6 个月未推送且已被官方版取代，无独立信息 |
| 16 | barbaragit/redis-operations-skills | https://github.com/barbaragit/redis-operations-skills | 0 | 2026-06-18 | 无（API `license: null`） | Redis Cloud / Redis Software 支持工单式 runbook | 0 | 1 | 2 | 1 | 0 | 4 | REJECT | 范围外：`redis-cloud-account-signup`、`redis-cloud-api-429-troubleshooting`、`redis-azure-acre-amr-connection-limits` 等全是托管产品控制面与账号问题；且带 `agents/openai.yaml` 专属绑定 |
| 17 | AzureManagedRedis/amr-migration-skill | https://github.com/AzureManagedRedis/amr-migration-skill | 2 | 2026-07-28 | MIT | ACRE→AMR 迁移、SKU、az CLI | 1 | 2 | 2 | 2 | 2 | 9 | REJECT（范围） | 分数够但整份是 Azure 托管控制面（SKU 规格、`az redis` 命令、IaC 模板），正是本 skill 声明不覆盖的部分 |
| 18 | majiayu000/claude-skill-registry `skills/data/caching-strategist` | https://github.com/majiayu000/claude-skill-registry | 602 | 2026-09-10 | MIT（仓库级；skill 自身 frontmatter 无 license） | 应用层缓存分层、TTL 常量、失效触发 | 0 | 3 | 1 | 1 | 1 | 6 | REJECT | 双重问题：①主题正是本 skill 明确不覆盖的「应用侧缓存架构」；②仓库是抓取聚合站（`skills/ai-llm/prompt-caching-<某人>-<某仓>` 这种目录名），来源与许可不可溯 |
| 19 | alphaparkinc/genpark-vercel-kv-redis-cacher-skill | https://github.com/alphaparkinc/genpark-vercel-kv-redis-cacher-skill | 9 | 2026-07-16 | 无（API `license: null`） | Vercel KV 缓存封装 | 0 | 2 | 1 | 1 | 0 | 4 | REJECT | 单一 SaaS 产品包装（Vercel KV），无 Redis 侧知识 |
| 20 | agents-infrastructure/alicloud-agent-skills `skills/alicloud-redis` | https://github.com/agents-infrastructure/alicloud-agent-skills | 2 | 2026-02-19 | NOASSERTION | 阿里云 Redis 实例/备份/参数/监控 | 1 | 1 | 2 | 2 | 1 | 7 | REJECT（范围） | references 是 `instance.md`/`backup.md`/`parameter.md`/`account.md`——托管控制面 OpenAPI，本 skill 不覆盖；许可 NOASSERTION 也未澄清 |
| 21 | fcenedes/redis_sa_skills | https://github.com/fcenedes/redis_sa_skills | 3 | 2026-09-10 | 无（API `license: null`） | agent 能力台账 / 委派编排 | 0 | 3 | 1 | 1 | 0 | 5 | REJECT | 名字含 redis，内容是 agent 委派与记忆编排（`agent-delegation-routing` 等），仅一处 `redis-array-mirror.md` 提到 Redis |
| 22 | lviladrich/database-decision | https://github.com/lviladrich/database-decision | 0 | 2026-02-26 | MIT | 选型决策（含 Redis 一节） | 0 | 1 | 1 | 1 | 2 | 5 | REJECT | 跨数据库选型清单，Redis 只占一小节且无可执行规则 |
| 23 | Scalar4eg/skill-redis-java | https://github.com/Scalar4eg/skill-redis-java | 3 | 2024-08-05 | 无（API `license: null`） | Java Redis 示例工程 | 0 | 0 | 1 | 1 | 0 | 2 | REJECT | 2024 年的示例代码仓，非 skill，>6 个月未推送 |
| 24 | wshobson/agents（全仓 grep `redis|cach`） | https://github.com/wshobson/agents | 39558 | 2026-09-07 | MIT | — | — | — | — | — | — | — | REJECT（无命中） | 39.6k★ 的大仓，`git/trees?recursive=1` 全树只命中 `plugins/developer-essentials/skills/turborepo-caching`，与 Redis 无关 |

**立项判据（官方厂商特例）**：官方仓库 `redis/agent-skills`（MIT，merged，6 个可用 skill）
+ 官方文档 `redis.io/docs`（`kind: docs`）+ 官方库 `redis/redis-vl-python`（MIT，merged）
+ 跨厂商社区上游 `github/awesome-copilot skills/upstash-redis`（MIT，merged）。
merged 上游 3 个、reference 4 个，满足特例组合。注意本例中官方文档因 **CC-BY-NC-SA-4.0** 落在
reference 一侧（见冲突与裁决 1），特例要求的「官方文档 merged」不成立，因此额外引入
RedisVL 与 awesome-copilot 两个 MIT 上游把 merged 数量补到 3。

## 本机实验（Redis 8.10.1，`docker run redis:8-alpine`）

正文中标 `[verified]` 的规则来自下列实测。容器：
`docker run -d --name hs-redis redis:8-alpine redis-server --enable-debug-command yes --save ''`。
`docker exec hs-redis redis-cli INFO server` → `redis_version:8.10.1`、`redis_mode:standalone`。
`MODULE LIST` → `search 81000`、`bf 81001`、`timeseries 81000`、`vectorset 1`、`ReJSON 81000`
（即 8.x 官方镜像自带查询引擎、JSON、向量集合，无需单独装 Redis Stack）。

### E1 编码阈值与 `OBJECT ENCODING`

`CONFIG GET` 实测默认值（与「到 128 就升级」的流传说法不符）：

```
hash-max-listpack-entries  512      hash-max-listpack-value  64
zset-max-listpack-entries  128      zset-max-listpack-value  64
set-max-intset-entries     512      set-max-listpack-entries 128
list-max-listpack-size     -2       (即按 8 KB 大小而非条数)
```

实测转换点：

| 操作 | 结果 |
|---|---|
| Hash 128 / 129 个字段 | 都是 `listpack`（阈值是 512，不是 128） |
| Hash 单值 64 / 65 字节 | `listpack` → `hashtable` |
| Set 纯整数 `1 2 3` | `intset` |
| 同一 Set 加入一个字符串 | `listpack` |
| Set 129 个字符串成员 | `hashtable` |
| ZSet 128 / 129 个成员 | `listpack` → `skiplist` |
| String `12345` / `short` / 45 字符 | `int` / `embstr` / `raw`（embstr 上限 44） |

### E2 过期语义

```
SET k v EX 100 ; SET k v2          → TTL -1     # 普通 SET 清掉 TTL
SET k v3 EX 100 ; SET k v4 KEEPTTL → TTL 100
SET k2 v EX 100 ; APPEND k2 x      → TTL 100    # APPEND 保留
SET k3 vvvv EX 100 ; SETRANGE k3 1 z → TTL 100  # SETRANGE 保留
SET g v EX 100 ; GETSET g w        → TTL -1     # GETSET 清掉
HSET h3 f 1 ; EXPIRE h3 100 ; HSET h3 g 2 → TTL 100   # 加字段不影响键 TTL
SET c 1 EX 100 ; INCR c            → TTL 100
SET a1 v EX 100 ; SET b1 w ; RENAME a1 b1 → TTL 100    # TTL 随值搬走，覆盖目标
HSET sess a 1 b 2 ; HEXPIRE sess 100 FIELDS 1 a ; HTTL sess FIELDS 2 a b → 100, -1
```

`INFO stats` 在一个 `PX 100` 的键过期后给出 `expired_keys:1`、`expired_keys_active:1`
—— 即主动过期周期确实会在无人访问时回收该键。

### E3 淘汰策略

`CONFIG SET maxmemory 3mb` 后逐个写 1 KB 值：

| 策略 | 结果 |
|---|---|
| `noeviction` | 第 1078 次写入返回 `OOM command not allowed when used memory > 'maxmemory'.` |
| `volatile-lru`，且**所有键都没有 TTL** | **同一个 OOM 错误**——没有可淘汰候选时 `volatile-*` 退化成 `noeviction` |
| `allkeys-lru` | 写入返回 `OK`，服务端淘汰旧键 |

这条是选错策略的真实后果：把策略设成 `volatile-lru` 却不给缓存键设 TTL，等于设了 `noeviction`。

### E4 事务与脚本的原子性

```
MULTI ; INCR counter ; LPUSH str x ; INCR counter ; EXEC
→ 1 / WRONGTYPE... / 2      GET counter → 2      # 运行期错误不回滚，前后两条都生效
MULTI ; INCR counter2 ; NOSUCHCOMMAND a ; EXEC
→ ERR unknown command ... ; EXECABORT Transaction discarded    GET counter2 → (nil)
EVAL "redis.call('SET',KEYS[1],'first') redis.call('LPUSH',KEYS[2],'x') redis.call('INCR',KEYS[2]) return 1" 2 la lb
→ WRONGTYPE ...    GET la → "first"    TYPE lb → list        # 脚本中途报错，之前的写入留下
```

结论：`MULTI/EXEC` 与 Lua 都提供**隔离**（中途不插入别的命令）而**不提供回滚**；入队期错误
（命令不存在、参数个数不对）才会整体放弃。

`FUNCTION LOAD` + `FCALL` 实测可用（`redis-cli -x FUNCTION LOAD REPLACE < lib.lua`），
比较-并-删除的锁释放函数返回 0 / 1 符合预期。

### E5 向量集合（Redis 8 内置 `vectorset`）

```
VADD vs VALUES 3 1 0 0 a   → 1
VSIM vs VALUES 3 1 0 0 WITHSCORES COUNT 2 → a 1 / c 0.996941864490509
VINFO vs → quant-type int8  hnsw-m 16  vector-dim 3 ...
```

注意 `quant-type` 默认是 **int8**（有损量化），不是 float32；需要无损时得显式 `NOQUANT`。

## 深度审查

### 1. redis/agent-skills（官方，MIT，146★，2026-09-08，HEAD `a84871d0`）

仓库形态：`plugins/redis-development/skills/<name>/{SKILL.md,references/*.md}`，另有
`evals/<plugin>/<skill>/{evals.json,model-matrix.json,baselines/}` 与
`packages/redis-development-build`（自建评测基线工具链）。这是本池中唯一带评测基线的上游，
说明维护方式是工程化的而非一次性提交。

frontmatter：`name` / `description` / `license: MIT` / `metadata.author: Redis, Inc.` /
`metadata.version`。没有 `allowed-tools`、没有 `paths`、没有 harness 变量——**不需要剥离任何
agent 专属字段**，这在本轮所有波次里少见。正文里的相对链接
（`[references/pooling.md](references/pooling.md)`）符合「SKILL.md → reference 一层」。

8 个 skill 的逐个判定：

| skill | 行数 | 判定 | 说明 |
|---|---|---|---|
| `redis-core` | 67 | merged（覆盖面 + 反模式） | 选型表 8 行、键名 5 条。深度止步于「用 Hash 不要用序列化字符串」；没有编码阈值、大 key、内存核算，也完全没有过期/淘汰 |
| `redis-connections` | 122 | merged（本波最有用的一份） | 池 vs 多路复用的客户端归属表、`KEYS→SCAN` / `SMEMBERS→SSCAN` 对照、RESP3 客户端缓存、超时次序。**「多路复用连接不能承载 `BLPOP`」**是别处没有的实战点 |
| `redis-clustering` | 82 | merged | hash tag 的槽计算、`CROSSSLOT` 触发面（`MGET`/`SDIFF`/pipeline/Lua）、`{user:1001}` 优于 `{1001}` 的理由、副本读的一致性代价 |
| `redis-search` | 220 + 21 refs | merged | 三个查询命令的选择表带最低版本（`FT.HYBRID` 8.4.0）、字段类型选择表、HNSW/FLAT 取舍、别名零停机换索引。`references/aggregate-pipeline.md` 381 行，超出本仓库 reference 建议篇幅，只取其 `GROUPBY/REDUCE` 语义 |
| `redis-security` | 106 | merged（部分） | ACL 三个示例用户、命令类别表、`bind`/`protected-mode`、防火墙。末尾的 `rename-command` 建议按现状降级（见冲突 4） |
| `redis-observability` | 77 | merged（部分） | `INFO` 指标 + 告警阈值表、`SLOWLOG`/`MEMORY DOCTOR`/`CLIENT LIST`/`FT.PROFILE` 对照。Redis Insight 一节是产品面 |
| `redis-semantic-cache` | 88 | merged（仅语义） | 整份围绕 Redis Cloud LangCache（预览）：`cache_id`、`api_key`、REST 端点。剥离后剩下的可用语义只有阈值区间与按任务分缓存 |
| `iris-development` | 91 + 9 refs | REJECT | 托管 agent-memory 产品（session/LTM API、auth token、开通流程），与本 skill 无关 |

**未覆盖的空白**（本 skill 必须自己补，也正是它相对官方 skill 的增量）：过期语义与
`maxmemory-policy` 的真实后果、持久化与数据丢失窗口、`MULTI`/Lua 的原子性边界、
分布式锁的保证、Pub/Sub 与 Stream 消费组的取舍、缓存雪崩/穿透/击穿、编码与内存核算、
`SCAN` 的保证、`INFO`/`LATENCY` 的默认关闭状态。

### 2. redis.io/docs（源 redis/docs，80★，2026-09-10，HEAD `e75ba0a1`）

Hugo 站点，`content/{commands,develop,operate,integrate,apis,glossary}`。有
`AI_AGENT_DEVELOPER_GUIDE.md`、`for-ais-only/` 与 `.agents/`——官方自己维护给 agent 读的入口。
内容质量与新鲜度都是 3 分（每日推送、命令页带 `Available since` 与 `ACL categories`）。
**问题在许可**：实读 `LICENSE` 第一段为
「The Redis Website and Documentation ... is licensed under the Creative Commons
Attribution-**NonCommercial**-ShareAlike 4.0 International License」，另有一句说明「原
redis-doc 的部分」按 CC-BY-SA-4.0（实读 `redis/redis-doc` 的 LICENSE 确认为 CC-BY-SA-4.0）。
NC 条款不属于开源许可 → 见冲突 1 的裁决。

### 3. redis/redis-vl-python（RedisVL，官方，MIT，425★，2026-09-10，HEAD `2f8d3d39`）

不是 skill 仓库，是官方 Python 库，但 `redisvl/extensions/cache/llm/semantic.py` 与
`docs/user_guide/03_llmcache.ipynb`、`10_embeddings_cache.ipynb` 是本池里唯一把语义缓存写成
可运行参数的地方：距离阈值（不是相似度）、TTL、按 embedding 模型分索引、embedding 缓存与
响应缓存分离。同时 `redisvl/index` 揭示了 RQE 索引 schema 的落地形态。MIT，可合入。

### 4. github/awesome-copilot `skills/upstash-redis`（MIT，38872★，2026-09-10，HEAD `7568a482`）

GitHub 官方目录里唯一的 Redis 条目（全树 grep `redis|valkey|cache|memcach` 只此一条，
`instructions/` 无）。作者 `metadata.author: Upstash`。结构是「Step N + Checkpoint」，
这个「每步以可验证 checkpoint 收尾」的形状与本仓库的具名验证门一致。
可用的是 cache-aside 的键形状、会话滑动过期、限流器按 `prefix` 隔离键、`Retry-After`
响应头；不可用的是 REST/HTTP 客户端语义（每命令一次 HTTP、值自动序列化、
「不要 `JSON.stringify`」），这些在自管 Redis 上是相反的。见冲突 7。

### 5. iamdemetris/lude-kit `skills/stacks/redis-expert`（Apache-2.0，0★，2026-07-17，HEAD `b41c7a6a`）

API 报 NOASSERTION，实读根 `LICENSE` 是标准 Apache-2.0（`Copyright 2026 LudeSkills
contributors`）——按规则可 merged，但**内容形态不可用**：整份是 persona
（`## Role` / "You are a senior Redis operator"），`description` 末尾还写
`route to senior-backend-engineer` / `postgres-expert`，是别的 agent 名字，属标准 1.3
禁止的上游交叉引用残留。0★、无评测。
价值只在它的触发词清单：本池唯一同时点到 RDB/AOF、Sentinel、hot key、`LATENCY DOCTOR`、
`EVALSHA`、Valkey 的候选，用作覆盖面对照 → `relation: reference`。

### 6. redis/redis 与 redis/redis-py

`redis/redis`（76310★）的 `LICENSE.txt` 明确：Redis 8 起三重许可 RSALv2 / SSPLv1 / AGPLv3，
7.2 及更早为 BSD-3。三者都不能作为 merged 上游 → reference。
它的价值是 `releases` 端点（确认 8.10.1 为当前稳定）与 `redis.conf` 默认值，
而后者本 skill 一律改用本机实例 `CONFIG GET` 实测（见「本机实验」）。
`redis/redis-py`（MIT，13632★）只用于交叉核对客户端侧默认值，未合入 API 代码 → reference。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 官方文档能否 merged | 前四波的教训是「官方文档若许可允许就该 merged」；本例 `redis/docs` 的 LICENSE 是 CC-BY-**NC**-SA-4.0 | **reference**。事实据它核实但全部改写，且不复制任何表格、清单或段落结构 | 实读 `gh api repos/redis/docs/contents/LICENSE`。NC（禁商用）不是开源许可，标准第 9 节「专有 = 不得作为 merged」适用。merged 数量改由 redis/agent-skills、RedisVL、awesome-copilot 三个 MIT 上游满足 |
| 2 | 「上游许可」= Redis 本体许可？ | Redis 8 是 RSALv2/SSPLv1/AGPLv3，容易被整体套到 redis/* 各仓库 | 只看每个仓库自己的 LICENSE：`redis/agent-skills` = MIT → merged；`redis/redis-vl-python` = MIT → merged；`redis/redis` 本体 → reference | 逐仓 `gh api repos/<r>/contents/LICENSE` 实读 |
| 3 | Hash listpack 阈值 | 大量二手材料（及旧版 redis.conf 注释）写 `hash-max-listpack-entries` 默认 128 | 默认是 **512**；正文不背数字，规则落在「用 `CONFIG GET hash-max-listpack-*` 读当前实例，再判断有没有降级」 | 本机 8.10.1 实测 E1：128 与 129 个字段都是 `listpack`；`CONFIG GET` 返回 512 |
| 4 | 危险命令怎么禁 | `redis-security` 给 `rename-command FLUSHALL ""`；官方 security/ACL 文档以 ACL 为首选 | 默认用 ACL 类别（`-@dangerous`、`-@admin`），`rename-command` 只作为无 ACL 的旧实例逃生口，并注明它会让客户端库与集群工具静默失败（它们发的是原命令名） | `COMMAND INFO keys` 实测 `KEYS` 属 `@keyspace @read @slow @dangerous`——ACL 一条 `-@dangerous` 覆盖同一意图，且不改变线协议 |
| 5 | 命中率告警阈值 | `redis-observability` 写「hit ratio < 80% 告警」 | 只对 cache-aside 用途成立。正文写清 `keyspace_hits/misses` 是**实例级**、不分前缀，会话/队列/去重/锁这类用途本来就以 miss 为常态；混用实例时该指标无意义，要按前缀在应用侧自测 | `INFO stats` 实测只有全局 `keyspace_hits` / `keyspace_misses` 两个字段，无 per-prefix 维度 |
| 6 | 语义缓存阈值方向 | `redis-semantic-cache` 用「相似度阈值」，越大越严（0.9 / 0.95）；RedisVL 的参数是 `distance_threshold`，越小越严 | 正文只写「按你的客户端用的是相似度还是距离确认方向；先量一批真实 prompt 对的分布再定值，不要抄常数」，并给出误命中的具体后果 | `redisvl/extensions/cache/llm/semantic.py` 的参数名；`VSIM ... WITHSCORES` 实测返回的是相似度（1.0 为完全一致） |
| 7 | Upstash 的客户端语义 | upstash-redis 说「每条命令一次 HTTP」「值自动序列化，不要 `JSON.stringify`」 | 只取键形状、TTL 纪律、限流器前缀隔离；正文明确 Redis 侧存的是字节串，序列化与反序列化是应用的事 | Upstash 是 REST 网关产品；自管 Redis 走 RESP over TCP，`GET` 返回 bulk string |
| 8 | `volatile-lru` 是不是安全默认 | 社区常把它当「只淘汰有 TTL 的键，所以更安全」 | 纯缓存实例用 `allkeys-lru`/`allkeys-lfu`；当数据源用 `noeviction`；`volatile-*` 只在同实例混放持久数据与缓存**且每个缓存键都有 TTL**时用 | 本机实测 E3：`volatile-lru` 且无键带 TTL 时，写入返回与 `noeviction` 完全相同的 `OOM command not allowed when used memory > 'maxmemory'.` |
| 9 | List 能不能当队列 | `redis-core` 的选型表把 List 标为 "Queue"；`redis-connections` 把 `BLPOP` 列为「队列消费者的正当用法」 | 分级：至多一次可接受 → `BLMOVE` 到 per-worker 处理列表（仍需回收器）；不能丢 → Stream + 消费组（`XREADGROUP` / `XACK` / `XAUTOCLAIM`）。正文不把裸 `LPOP`/`RPOP` 写成队列方案 | 本机实测 E7：`XREADGROUP` 后 `XPENDING` 保留 2 条未确认条目，`XAUTOCLAIM` 可被另一个消费者接管；List 无对应机制 |
| 10 | `MULTI` 与 Lua 的「原子性」 | `redis-connections` 写「`pipeline(transaction=True)` 只在真正需要原子性时用」，读者会理解为可回滚 | 正文写「提供隔离，不提供回滚」，并区分入队期错误（`EXECABORT`，整体放弃）与运行期错误（前后命令都生效） | 本机实测 E4：`MULTI; INCR c; LPUSH str x; INCR c; EXEC` 后 `GET c` = 2；Lua 中途 `WRONGTYPE` 后先前的 `SET` 仍在 |
| 11 | TAG 比 TEXT「快 10×」 | `redis-search` 给了倍数但没给条件 | 正文不写倍数，改写为「TEXT 会分词 + 词干化，精确值放 TEXT 会**静默失配**」，并给实测例子 | 本机实测 E7：`sku` 建为 TEXT 时 `FT.SEARCH idx '@sku:ABC-123'` 返回 **0** 条（`FT.EXPLAIN` 显示 `-123` 被当作 token 处理）；同一索引 `@status:{active}` 精确命中 1 条，`@name:headphone` 因词干化命中 2 条 |
| 12 | 向量该用 Vector Set 还是 RQE 的 VECTOR 字段 | `redis-core` 把 "Vector similarity" 指向 Vector Set；`redis-search` 把向量写成 `FT.CREATE ... VECTOR` | 二分写清：需要与属性/全文条件组合、需要索引现有 Hash/JSON → RQE `VECTOR` 字段；只要独立 KNN 集合、要省内存 → Vector Set（`VADD`/`VSIM`），并注明其默认 `quant-type int8` 是有损量化 | `MODULE LIST` 实测 `search` 与 `vectorset` 是两个独立引擎；`VINFO` 实测 `quant-type int8`、`hnsw-m 16` |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `redis-agent-skills` | redis/agent-skills（MIT，官方）`skills/redis-core`、`redis-connections`、`redis-clustering`、`redis-search`、`redis-security`、`redis-observability`、`redis-semantic-cache` | merged | 主干与覆盖面：数据结构选型、键命名、池化 vs 多路复用（含多路复用不能承载阻塞命令）、流水线、`KEYS→SCAN` 家族替换、RESP3 客户端缓存、超时次序、hash tag 与 `CROSSSLOT` 面、副本读的一致性代价、RQE 的三命令选择与字段类型选择、HNSW/FLAT 取舍、别名换索引、ACL 类别与最小权限用户、`INFO` 指标清单与 `SLOWLOG`/`MEMORY DOCTOR` 分工、语义缓存的阈值区间与按任务分缓存 |
| `redisvl` | redis/redis-vl-python（MIT，官方） | merged | 语义缓存的真实参数形态：距离阈值而非相似度常数、缓存条目自带 TTL、embedding 缓存与响应缓存分离、按 embedding 模型/维度分索引 |
| `awesome-copilot-redis` | github/awesome-copilot（MIT）`skills/upstash-redis` | merged | cache-aside 的键形状与「每个缓存键都必须有 TTL」的纪律、会话滑动过期的显式再设、限流器按 `prefix` 隔离键空间、429 与 `Retry-After` 的对应关系；「每步以可验证 checkpoint 收尾」的写法 |
| `redis-io-docs` | redis.io/docs（`kind: docs`，CC-BY-NC-SA-4.0） | reference | 每条事实的核实来源（命令的 `Available since`、ACL 类别归属、`maxmemory-policy` 语义、RDB/AOF 的丢失窗口、Cluster 规范的槽计算与 hash tag、Stream 消费组语义）。因 NC 条款不 merged，未复制任何文字或表格结构 |
| `redis-oss` | redis/redis（RSALv2 / SSPLv1 / AGPLv3） | reference | 版本线核实（`releases` → 8.10.1 为当前稳定）与 `LICENSE.txt` 的许可事实本身；默认配置改由本机实例 `CONFIG GET` 实测取得 |
| `redis-py` | redis/redis-py（MIT，官方客户端） | reference | 交叉核对客户端侧默认值：连接池行为、`socket_timeout`/`socket_connect_timeout` 默认为 None、RESP3 与 `CacheConfig` 的开启方式 |
| `lude-kit-redis` | iamdemetris/lude-kit（Apache-2.0）`skills/stacks/redis-expert` | reference | 仅用于覆盖面对照（RDB/AOF、Sentinel、hot key、`LATENCY DOCTOR`、`EVALSHA`）。persona 与 agent 路由内容按标准 1.2/1.3 不可合入，未取任何文字 |

## 基线缺口

无 skill（`uv run tools/run_evals.py redis --baseline`，`anthropic/claude-opus-5` + medium）时，
各场景未达成的 `expected_behavior`。基线答复路径
`/tmp/hs-evals/redis/anthropic-claude-opus-5-medium/baseline/<n>/answer.md`。

**本表已按重跑结果修正。** 第一轮基线跑完后本任务被额度中断，`/tmp` 随后被系统清理，
第一轮的 `answer.md` 全部丢失（场景 1 那次还是 900s `timeout`，没有答复文件）。
按「不保留无法复现的结论」，整表按第二轮重跑（4/4 `ok`，214.1s / 80.8s / 174.5s / 69.4s）
重新判定。与第一轮记录相比，重跑基线**更强**，以下四条第一轮记为缺口的行为在重跑中已达成，
已从表中删除：`BLMOVE` + 回收器这条中间路线（场景 2）、`SSCAN`（场景 2）、
「Hash 的 TTL 在键上」（场景 2）、「把计数器移出脚本」与 `CLUSTER COUNTKEYSINSLOT`（场景 3）。

基线的实际水位：场景 1 命中 7 条里的 5 条，场景 2 命中 8 条里的 7 条，
场景 3 命中 9 条里的 8 条，场景 4（负例）完全按预期作答。缺口因此不是「基线不会 Redis」，
而是**只剩下几条会直接造成生产事故、而基线两轮都稳定漏掉的**。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 cache_service.py | Bloom 过滤器 | 负缓存哨兵（`"\x00miss"` + 60s）给得很好，但没提 `BF.RESERVE`/`BF.EXISTS`——Redis 8 自带 `bf` 模块（本机 `MODULE LIST` 实测 `bf 81001`）。id 空间被攻击者控制时，负缓存的上界仍是 `QPS/60 × 不同 id 数`，Bloom 才是真正的前门 |
| 1 cache_service.py | 明确说出丢数据窗口 | 给了 `save ""` 并把理由写成「24gb 下 fork 的 COW 放大」，但没说清 `appendonly no` + `save 3600 1 ...` 的真实语义是「最坏丢一小时的写入」，也没明确下结论「这是 Postgres 前面的缓存，所以这个窗口无所谓」。给了正确的配置，缺了做决定的那句话 |
| 2 worker.py | 流没有上限 | **两轮都漏**。全篇没有 `MAXLEN` / `XTRIM`：把 List 换成 Stream 之后，队列从「会丢消息」变成「无上限增长」，故障形态换了一种而不是消失。这是本轮最稳定的缺口 |
| 3 cluster_client.py | hash tag 的取字规则 | **两轮都漏**。给了 `f"user:{{{user_id}}}:profile"` 这个写法（连 f-string 花括号转义都点到了），也警告了常量 tag，但始终没说「只有**第一个** `{` 到其后**第一个** `}` 之间的子串参与哈希」。没有这条规则，`{a}b{c}`、`{}`、`}x{` 这三种写法只能靠试 |
| 4 slow_orders_plan.sql（负例） | —（无缺口，预期） | 基线完全按 Postgres 索引题作答：读出 `Rows Removed by Filter: 3918442` 与 `read=418291`，给出 `(merchant_id, status, created_at DESC)` 复合索引、`CONCURRENTLY`、部分索引备选，并明确不建议 `INCLUDE`；没有任何 Redis 建议。`skill_read: false`。这条场景的作用是当 `description` 否定边界的回归测试，基线达成即是预期结果 |

## 评测结果

两轮均为 `anthropic/claude-opus-5` + `medium`（`tools/run_evals.py` 默认，未传 `--model`/`--thinking`）。
基线 4/4 `ok`（214.1s / 80.8s / 174.5s / 69.4s），有 skill 4/4 `ok`
（753.3s / 172.1s / 219.9s / 83.6s）。答复路径
`/tmp/hs-evals/redis/anthropic-claude-opus-5-medium/{baseline,skill}/<n>/answer.md`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 cache_service.py（7 条） | claude-opus-5:medium | 无（baseline） | false | 5/7：`volatile-lru` 退化为 `noeviction`、抖动、单飞锁 + CAS 释放、负缓存哨兵、裸 `SET` 抹掉 TTL、`KEYS` → 反向索引（后两条合并计为 2 条，共 5 条达成） | 未达成：Bloom 过滤器；未说出 `appendonly no` + `save 3600 1` 的一小时丢失窗口、也未下「这是缓存所以无所谓」的结论 |
| 1 cache_service.py（7 条） | claude-opus-5:medium | 有 skill | **true** | **7/7** | 两条缺口都被填补：加了 UUID 形状校验 + `BF.EXISTS` Bloom 前门（并自己处理了「Bloom 的不存在被当作终局 404」这个可用性→正确性的升级），并明确写出「丢失窗口 1h → ~1s」。另外自己起了 Redis 8.10.1 容器把 14 条断言逐条量出来（`[4] volatile-lru + 无 TTL 键 -> OOM；allkeys-lfu 同负载无报错 evicted_keys=5352`） |
| 2 worker.py（8 条） | claude-opus-5:medium | 无（baseline） | false | 7/8：List 无 ack 丢单、Stream + 消费组 + `XACK` + `XAUTOCLAIM`、`BLMOVE` 退路、at-least-once + 幂等守卫、`SMEMBERS` O(N) 与 ZSET/`SSCAN`/HLL 替代、`LRANGE 0 -1` + ZSET 截断、String→Hash + `HEXPIRE`、Hash TTL 在键上 | 未达成：**流的上限**（全篇无 `MAXLEN`/`XTRIM`）。第一轮基线也漏这条 |
| 2 worker.py（8 条） | claude-opus-5:medium | 有 skill | **true** | 7/8 | **填补了 `MAXLEN`**：`XADD stream:orders * order <json> MAXLEN ~ 100000`。同时按 skill 的输出契约按影响面分组（`data-loss` → `availability` → `correctness` → `cost/latency`，每行 `path:line - finding`），并起容器实测 `SMEMBERS` 2.3M 成员服务端 499.9ms、Bitmap 524KB vs Set 106MB、`ZRANGE REV 0 19` 比 `LRANGE 0 -1` 快 17 倍。**回退了一条**：本轮没提 `BLMOVE` 中间路线（基线提了），故仍是 7/8 |
| 3 cluster_client.py（9 条） | claude-opus-5:medium | 无（baseline） | false | 8/9：`CRC16` 跨槽与 `CROSSSLOT`、hash tag 修法（含 f-string 花括号转义）、反对常量 tag、`checkout` 的同槽/移出计数器两条路、`batch_prices` 非事务管道按节点路由、`leaderboard:global` 单键单槽即 4x 分片、副本读 opt-in + 异步 + 读己之写、`per_request_client` 每请求槽发现、`CLUSTER COUNTKEYSINSLOT` | 未达成：hash tag 的取字规则（第一个 `{` 到其后第一个 `}`）；也没有在真集群上验证（自述「环境无 redis-server」/本轮改为桩化） |
| 3 cluster_client.py（9 条） | claude-opus-5:medium | 有 skill | **true** | 8/9 | **填补了「裸 id 作 tag 的危害」这条具体表述**：明确写「用 `{1001}` 会把 `order:{1001}`、`invoice:{1001}` 无谓地压到同一槽」，而基线只警告了常量 tag。更重要的是它执行了 skill 的验证门「在真实 3 主集群上跑，不是单节点」：起了 3 主 3 从 Redis 8，先复现三处旧错误，再用 `commandstats` 证明副本读生效（三个 slave `get=399/403/399`，master 仅 2 次）、16 个排行榜分片键分布 4/4/8、各节点 `DBSIZE` 408/409/407。仍未逐字说出取字规则 → 8/9 |
| 4 slow_orders_plan.sql（负例，3 条） | claude-opus-5:medium | 无（baseline） | **false** | 3/3 | 按 Postgres 索引题作答：`Rows Removed by Filter: 3918442` → `(merchant_id, status, created_at DESC)`，部分索引备选，无任何 Redis 建议 |
| 4 slow_orders_plan.sql（负例，3 条） | claude-opus-5:medium | 有 skill | **false** | 3/3 | 开场即「这是 Postgres 索引选择问题，和 Redis 无关」。`description` 的否定边界（`Do not use for ... tuning a relational or document database`）挡住了邻接题，未触发本 skill，**无需修改 description** |

结论：**通过**。基线未达成的 4 条行为在有 skill 时有 3 条达成——
场景 1 的 Bloom 过滤器、场景 1 的持久化丢失窗口、场景 2 的 `MAXLEN`/`XTRIM`
（场景 3 的「裸 id tag 危害」这条具体表述也从「只警告常量 tag」收紧到了逐字命中）。
负例两轮 `skill_read` 均为 `false`。

仍未被填补的两条，如实记录：

1. **场景 3 的 hash tag 取字规则**：`references/cluster-and-connections.md` 里写了
   「只有**第一个** `{` 到其后**第一个** `}` 之间的子串参与哈希」并给了 `{}`、`}x{` 的反例，
   但答复没有逐字复述——它直接给出了正确的键名并在真集群上验证，属于「做对了但没解释」。
   不改 skill：把规则搬到 `SKILL.md` 的 Core rules 只会把一条参考材料抬进主线预算，
   而该场景的 8/9 已经包含了这条规则要防的两个失败（实体作用域、反对裸 id）。
2. **场景 2 的 `BLMOVE` 中间路线**：有 skill 时反而没提。原因可以定位：
   `SKILL.md` 的 `build-a-queue-that-does-not-lose-messages` 把 `BLMOVE` 放在倒数第二条
   （"If a List has to stay"），而答复按影响面排序后把 List 整体判为 `data-loss` 并直接给了
   Stream。这是取舍而不是遗漏（Stream 确实是更好的答案），故不改；若要强制出现，
   得把「先给最小改动再给正解」写进 Output format，而那会让每次评审都变长。

旁证（不计入判定）：两轮有 skill 的答复（场景 1、2、3）都自己起了真实 Redis 实例
（场景 3 起的是 3 主 3 从集群）并给出服务端实测数字；基线只有场景 1 用了 fakeredis 桩，
场景 3 干脆没有任何运行验证。这正是每个 workflow 以具名验证门收尾的直接效果。

## 备注

### Redis 的许可处理结论

三个独立的许可问题，必须分开看，不能互相套用：

1. **服务端本体** `redis/redis`：实读 `LICENSE.txt` —— Redis 8 起为三重许可，
   RSALv2 / SSPLv1 / AGPLv3 三选一；7.2 及更早为 BSD-3-Clause。三者都不是可 merged 的许可，
   故 `relation: reference`，`license: AGPL-3.0-only OR SSPL-1.0 OR RSALv2`。
   本 skill 不含任何来自源码树的文字；正文里的默认值全部由本机实例 `CONFIG GET` 实测得到。
2. **官方文档** `redis/docs`（即 redis.io/docs）：实读 `LICENSE` —— 全站
   **CC-BY-NC-SA-4.0**（含 NonCommercial 条款），仅「原 redis-doc 的那部分」为 CC-BY-SA-4.0
   （实读 `redis/redis-doc` 的 LICENSE 确认）。NC 不是开源许可，按 `docs/skill-standard.md`
   第 9 节「专有 = 不得作为 merged」处理为 **reference**：据它核实事实，不复制任何文字、
   表格或清单结构。**这是前四波「官方文档若许可允许就该 merged」这条经验的反例**，
   也是本波必须实查许可的直接证据。
3. **官方 skill 仓库** `redis/agent-skills` 与官方库 `redis/redis-vl-python`：各自的
   `LICENSE` 都是 MIT → merged。上游仓库的许可与它所记录的产品的许可无关，只看仓库自己的。

因为第 2 条落在 reference 一侧，「官方厂商特例」要求的「官方文档 merged」在本 skill 不成立；
merged 数量改由三个 MIT 上游（`redis-agent-skills`、`redisvl`、`awesome-copilot-redis`）满足，
reference 四个（`redis-io-docs`、`redis-oss`、`redis-py`、`lude-kit-redis`）。

### 当前稳定版本

`gh api repos/redis/redis/releases` 的最新非 prerelease 为 **8.10.1**（2026-08-17），
同批维护 8.8.2 / 8.6.6 / 8.4.6 / 8.2.9 / 7.4.11 / 7.2.16 / 6.2.24。正文以 8.10 为基准，
高于 7.2 的规则一律加版本门：`(7.4+)` 字段 TTL、`(8.0+)` 向量集合与 `HGETEX`/`HGETDEL`、
`(8.4+)` `FT.HYBRID`。

### 是否实跑过实例

**跑过。** `docker run -d --name hs-redis redis:8-alpine redis-server --enable-debug-command yes --save ''`，
`INFO server` 报 `redis_version:8.10.1`。E1–E7 七组实验的命令与输出见上文「本机实验」节，
所有标 `[verified]` 的规则都出自其中。实测纠正了三处流传说法：
`hash-max-listpack-entries` 默认是 512 而非 128；`volatile-lru` 在无 TTL 键时与 `noeviction`
返回完全相同的 OOM 错误；`MULTI`/Lua 运行期出错不回滚。另外实测到两个未预期的事实：
`TEXT` 字段上 `@sku:ABC-123` 返回 0 条（分词把 `-` 切开）、向量集合默认 `quant-type int8`。

**注意**：实验容器与 `/tmp` 下的实验脚本在本任务中途被系统清理，命令与输出已按原样记录在
「本机实验」节，重跑需重新起容器。`SCAN` 的重复元素在那一轮实测里**没有**观察到
（`rounds=539 unique_returned=5380 duplicates=0`，含中途删掉 15000 键触发缩容），
因此正文按官方保证写「可能重复」，并注明本地未观察到——不把一次未复现当成保证。

### 未来同步时要盯的上游

- `redis/agent-skills`：活跃（自带评测基线与 CI），`skills/redis-search` 的 references 增长最快；
  新增 skill 要先判断是不是又一个 Redis Cloud 产品包装（`iris-development` 就是）。
- `redis/docs`：许可若从 CC-BY-NC-SA 改为更宽松，本 skill 的 `redis-io-docs` 可升为 merged。
- `redis/redis` 的 `releases`：8.x 线推进很快，`FT.HYBRID` 之后的新命令都需要重核版本门。

### 放弃的方向

- **Valkey**：`lude-kit-redis` 把它列进触发词。本 skill 不覆盖 Valkey 的分叉差异——
  它是另一个产品，且前四波没有对应主题；正文不提，以免写出无法核实的等价性声明。
- **LangCache**：官方 `redis-semantic-cache` 的主体。Redis Cloud 预览产品，属托管控制面，
  只保留与产品无关的语义（阈值方向、按任务分缓存、条目 TTL），API 全部剥离。
- **`scripts/`**：考虑过写一个「导出 `INFO` + `--bigkeys` + `CONFIG GET` 快照」的脚本，
  但它只是把三条 `redis-cli` 命令串起来，且需要连接串与凭据，没有超出正文的可运行价值，
  故不提供。
