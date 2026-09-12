# sqlite 调研记录

> 正式正文与4份参考已完成，评测唯一入口为 [`skills/sqlite/evals/`](../skills/sqlite/evals/)。下文保留Phase A/B当时记录；用户继续建设后的最新结论见文末，内容交付不等于已证明增益。

## 调研日期与检索途径

- 调研/复核日期：2026-09-12。Phase A/B历史记录与后续正式建设、验证分节保存。
- 检索：已登录 `gh api search/code`，分别检索 `filename:SKILL.md path:sqlite`、`filename:SKILL.md sqlite WAL`、`filename:SKILL.md "SQLite Expert"`、`filename:SKILL.md "sqlite" "busy_timeout"`；web_search 检索 `sqlite skill SKILL.md github WAL busy` 补出 domain-expert。
- 官方检查：`gh api search/code -X GET -f q='org:sqlite filename:SKILL.md'` 返回空列表。此结论只代表此次可索引GitHub范围内未发现，不声称证明SQLite全球没有skill；未发现可用官方例外。Turso不是SQLite维护组织；Litestream也不能代替SQLite官方身份。
- 所有 GitHub 正文、目录、许可与元数据只经 `gh api repos/...`，未匿名读GitHub。两次网络timeout后合理重试成功；没有认证失败或限流。
- 下表15项均实际读取contents API原始SKILL.md后评分；树API浏览其同目录引用。Stars/pushed_at/license为本次API结果，不是搜索摘要。
- 新鲜度按2026-09-12计算：≤1月3，≤3月2，≤6月1。仓库最近push不等于具体skill文件更新。

## 候选表

评分：权威0–3 / 新鲜0–3 / 具体0–3 / 正确0–3 / 许可0–2。正确性是下述明确三条抽查的结果，不是对整份上游的无条件背书。总分≥8且范围相符才INCLUDE；正确性0强制REJECT，范围不符同样拒绝。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `TerminalSkills/skills/skills/sqlite/SKILL.md` | https://github.com/TerminalSkills/skills/blob/main/skills/sqlite/SKILL.md | 149 | 2026-09-04T19:42:42Z | Apache-2.0 | 嵌入式/SQL/宿主（见理由） | 1 | 3 | 1 | 3 | 2 | 10 | INCLUDE | 连接初始化/在线备份；教程式，需删通用代码 |
| 2 | `chrishuffman5/domain-expert/plugins/database/skills/sqlite/SKILL.md` | https://github.com/chrishuffman5/domain-expert/blob/main/plugins/database/skills/sqlite/SKILL.md | 4 | 2026-08-09T17:35:21Z | MIT（实读LICENSE） | 嵌入式/SQL/宿主（见理由） | 1 | 2 | 3 | 0 | 2 | 8 | REJECT | EXCLUSIVE与generate_series两处错误，正确性0强制拒 |
| 3 | `pvillega/claude-templates/plugins/ct/skills/sqlite-wal/SKILL.md` | https://github.com/pvillega/claude-templates/blob/main/plugins/ct/skills/sqlite-wal/SKILL.md | 23 | 2026-08-03T21:02:56Z | NONE | 嵌入式/SQL/宿主（见理由） | 1 | 2 | 3 | 0 | 0 | 6 | REJECT | 回滚模式全串行、prepared statements一律不线程安全等过度断言 |
| 4 | `harness-studio/harness-studio/skills/sqlite-concurrency/SKILL.md` | https://github.com/harness-studio/harness-studio/blob/main/skills/sqlite-concurrency/SKILL.md | 9 | 2026-06-18T00:07:21Z | MIT | 嵌入式/SQL/宿主（见理由） | 1 | 2 | 3 | 1 | 2 | 9 | INCLUDE | 只取单语句原子更新与事务边界；aiosqlite线程解释错误必须剥离 |
| 5 | `benbjohnson/litestream-skills/skills/litestream/SKILL.md` | https://github.com/benbjohnson/litestream-skills/blob/main/skills/litestream/SKILL.md | 5 | 2026-01-12T13:23:52Z | Apache-2.0 | 嵌入式/SQL/宿主（见理由） | 2 | 0 | 3 | 3 | 2 | 10 | REJECT | 超过6个月，非SQLite维护方官方例外；仅覆盖面参考 |
| 6 | `RightNow-AI/openfang/crates/openfang-skills/bundled/sqlite-expert/SKILL.md` | https://github.com/RightNow-AI/openfang/blob/main/crates/openfang-skills/bundled/sqlite-expert/SKILL.md | 18177 | 2026-07-02T08:13:12Z | Apache-2.0 | 嵌入式/SQL/宿主（见理由） | 1 | 2 | 2 | 3 | 2 | 10 | INCLUDE | 短事务/单写者/覆盖索引；固定调优值与1MB BLOB断言不采用 |
| 7 | `CodeAtCode/oss-ai-skills/tool/sqlite/SKILL.md` | https://github.com/CodeAtCode/oss-ai-skills/blob/master/tool/sqlite/SKILL.md | 16 | 2026-09-10T08:33:00Z | GPL-3.0 | 嵌入式/SQL/宿主（见理由） | 1 | 3 | 2 | 0 | 2 | 8 | REJECT | GPL仅reference；上下文管理器自动close及必须WAL保证一致性错误 |
| 8 | `SimHacker/moollm/skills/sqlite/SKILL.md` | https://github.com/SimHacker/moollm/blob/main/skills/sqlite/SKILL.md | 52 | 2026-09-07T16:00:17Z | MIT | 嵌入式/SQL/宿主（见理由） | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE | 有清楚引擎边界与durability风险；剥离MOOLLM绑定 |
| 9 | `sitharaj88/claude-skills/skills/db-sqlite/SKILL.md` | https://github.com/sitharaj88/claude-skills/blob/main/skills/db-sqlite/SKILL.md | 1 | 2026-08-16T03:22:11Z | NONE | 嵌入式/SQL/宿主（见理由） | 0 | 3 | 2 | 1 | 0 | 6 | MAYBE | 无许可；WAL被暗示替代单写者约束 |
| 10 | `honki12345/my-agent-skills/sqlite/SKILL.md` | https://github.com/honki12345/my-agent-skills/blob/main/sqlite/SKILL.md | 0 | 2026-02-25T01:28:22Z | NONE | 嵌入式/SQL/宿主（见理由） | 0 | 0 | 2 | 0 | 0 | 2 | REJECT | 过期；100MB WAL限制过时，INTEGER PRIMARY KEY NULL解释错误 |
| 11 | `modbender/skill-library-mcp/data/sql/SKILL.md` | https://github.com/modbender/skill-library-mcp/blob/main/data/sql/SKILL.md | 14 | 2026-06-16T12:58:45Z | MIT | 嵌入式/SQL/宿主（见理由） | 1 | 2 | 1 | 0 | 2 | 6 | REJECT | 泛SQL；INCLUDE语法及绝对索引规则不适用SQLite |
| 12 | `modbender/skill-library-mcp/data/sql-toolkit/SKILL.md` | https://github.com/modbender/skill-library-mcp/blob/main/data/sql-toolkit/SKILL.md | 14 | 2026-06-16T12:58:45Z | MIT | 嵌入式/SQL/宿主（见理由） | 1 | 2 | 1 | 1 | 2 | 7 | REJECT | 泛SQL范围；只浅讲SQLite，不能合成引擎生命周期 |
| 13 | `tursodatabase/agent-skills/skills/turso-db/SKILL.md` | https://github.com/tursodatabase/agent-skills/blob/main/skills/turso-db/SKILL.md | 26 | 2026-07-22T16:23:09Z | MIT | 嵌入式/SQL/宿主（见理由） | 3 | 2 | 3 | 3 | 2 | 13 | REJECT | Turso自身官方但不是SQLite；Rust重写引擎、SDK及平台，不可套官方例外 |
| 14 | `0xDarkMatter/claude-mods/skills/sqlite-ops/SKILL.md` | https://github.com/0xDarkMatter/claude-mods/blob/main/skills/sqlite-ops/SKILL.md | 36 | 2026-08-23T14:16:57Z | MIT | SQLite与D1混合 | 1 | 3 | 3 | 0 | 2 | 9 | REJECT | DROP COLUMN不支持及LIKE只需BINARY错误；D1无PRAGMA亦错误 |
| 15 | `ChristopherDavenport/christopherdavenport-marketplace/backend/sqlite/skills/sqlite/SKILL.md` | https://github.com/ChristopherDavenport/christopherdavenport-marketplace/blob/main/backend/sqlite/skills/sqlite/SKILL.md | 1 | 2026-08-30T16:13:40Z | MIT | SQLite/Go | 1 | 3 | 3 | 0 | 2 | 9 | REJECT | synchronous持久化和ADD STORED两处错误 |

## 深度审查

按总分靠前的8项深读（含最终因范围/正确性被拒的高分项）：13、7、8、1、6、4、14、15。
另补读2、3，因为它们是最直接的SQLite操作候选。所有正文已完整读取；
引用目录通过树API浏览，2实读四份reference开头与目录，14读concurrency-durability，
15读pragmas-and-tuning；其余无references的候选不虚构引用。

- **13 Turso（13）**：条件路由清楚，列出SDK和references目录；描述过长并带检索禁令。
  其“不支持VACUUM/WITHOUT ROWID、WAL唯一日志模式”明确是Turso约束，不能套在SQLite。
  浏览MVCC、sync、encryption等引用路径后决定整个候选排除，不以跨厂商官方身份凑立项。
- **7 CodeAtCode（10，正确性0）**：大篇教程与重复PRAGMA、CRUD，GPL-3.0不得merged。
  两次明确声称Python连接上下文管理器自动close；又称保证一致性必须WAL不能DELETE。
  可以仅看备份、迁移等主题清单，绝不将其样例导入。
- **8 SimHacker（11）**：短、边界清楚，WAL单写者、每连接FK与synchronous风险有价值；
  tier/related/tags、allowed-tools数组、MOOLLM/cursor-mirror与外部skill相对路径不可保留。
  同目录只有CARD/GLANCE/README，无独立references。与TerminalSkills重叠但对耐久性更谨慎。
- **1 TerminalSkills（10）**：入门教程式，frontmatter metadata含tags数组且category不兼容。
  有明确关闭连接的Python样例和在线.backup，不把安装/CRUD搬入。
  无references；_scores.json不是正确性证据。固定NORMAL/cache值不作为默认生产建议。
- **6 OpenFang（10）**：两字段frontmatter，纯正文无references，宿主绑定低。
  可取短事务、覆盖索引、单写者边界；固定cache/mmap以及“>1MB BLOB一律外置”缺少工作负载依据，
  不采用。其“所有PRAGMA一致”需拆成持久设置与每连接设置，而非反复切换journal_mode。
- **4 Harness Studio（9）**：无references；真实check-then-act和atomic-counter例子可用。
  FastAPI/aiosqlite语境强，错称await会让同一aiosqlite连接换线程/连接；官方明确一连接一线程队列。
  bootstrap mutex表声称多进程不受影响，随后又承认仅进程内有效；不采用其冷启动结论。
  所以只选其原子SQL/事务意图，不以高分掩盖错误。
- **14 0xDarkMatter（9，正确性0）**：有12份reference和脚本，读了并发引用；
  条件导航较好，但把D1与SQLite引擎说成同语义、DROP COLUMN都要重建、LIKE只需BINARY均危险。
  D1官方明列支持部分PRAGMA，原文“no PRAGMA surface”错误。不可合入。
- **15 ChristopherDavenport（9，正确性0）**：7份reference，正文与pragmas引用直接冲突：
  正文说synchronous随文件持久化，引用说每连接；演示ALTER ADD STORED不被SQLite支持。
  固定读池CPU倍数、Go性能比例、禁用DELETE等均不应传递。
- **2 Domain Expert（8，正确性0）补审**：四reference结构合理但很长；LICENSE实读为MIT加免责，
  与frontmatter Public Domain矛盾，按LICENSE记录。EXCLUSIVE不分WAL、generate_series内建版本断言错误。
- **3 sqlite-wal（6，正确性0）补审**：最接近所需难点，BUSY_SNAPSHOT和版本风险有价值；
  但回滚日志“serializes everything”、prepared statements任何mode都不线程安全等过度断言，
  以及“JSON索引必须generated column”、全平台固定参数不可信。无许可证与references，不作主干。

## 正确性三条抽查

表中“正确”只由下列三条抽查计分。即使抽查全对，也删除未取证的其他建议。
官方链接是事实来源，不把社区表述当官方结论。

| # | 抽查1 | 抽查2 | 抽查3 | 结果 |
|---|---|---|---|---|
| 1 | WAL允许读写并发 [W] | FK需开启 [F] | 在线备份API/.backup [B] | 3/3 |
| 2 | WAL中EXCLUSIVE阻止读取 [T]：错 | generate_series自3.46内建 [G]：错 | STRICT可用类型 [S]：对 | 1/3，0分 |
| 3 | BUSY_SNAPSHOT需重启事务 [I]：对 | 回滚模式全部访问串行 [I/T]：错 | 所有线程模式prepared statement均不安全 [H]：错 | 1/3，0分 |
| 4 | 单语句n=n+1原子更新 [T/U]：对 | check-then-act IMMEDIATE [I]：对 | aiosqlite跨await自动换连接 [A]：错 | 2/3，1分 |
| 5 | WAL是SQLite复制日志 [W] | 写提交进入WAL [W] | 长读阻checkpoint [W] | 3/3；只抽引擎相关断言，版本过期仍拒 |
| 6 | WAL单写者 [W] | 短显式事务 [T] | 覆盖索引避免回表 [Q] | 3/3 |
| 7 | with sqlite3.connect自动close [P]：错 | 一致性必须WAL不能DELETE [W]：错 | 备份API [B]：对 | 1/3，0分 |
| 8 | FK每连接 [F] | STRICT可拒无损转换失败 [S] | synchronous影响断电耐久性 [W] | 3/3 |
| 9 | STRICT 3.37+ [S]：对 | FK开启 [F]：对 | 单写连接或WAL（作为替代）[W]：错 | 2/3，1分 |
| 10 | FK每连接 [F]：对 | >100MB应不用WAL [W]：过时 | INTEGER PRIMARY KEY允许保存NULL [S]：错 | 1/3，0分 |
| 11 | SQLite支持INCLUDE列索引 [Q]：错 | 函数列不能索引 [Q]：错（表达式索引） | 事务成组原子 [T]：对 | 1/3，0分 |
| 12 | BEGIN/COMMIT [T]：对 | WAL读并发 [W]：对 | 一般索引例子INCLUDE不标方言 [Q]：不适用SQLite | 2/3，1分；泛SQL范围拒 |
| 13 | SQLite本身支持VACUUM [B] | SQLite支持WITHOUT ROWID [S] | SQLite默认rollback非WAL [W] | 上游把相反说法限定为Turso，没有据此诬判错误；范围拒 |
| 14 | WAL持久 [W]：对 | DROP COLUMN不支持 [L]：错 | D1无PRAGMA [D]：错 | 1/3，0分 |
| 15 | synchronous随文件持久 [R]：错 | ALTER ADD STORED [C]：错 | STRICT 3.37+ [S]：对 | 1/3，0分 |

证据索引：
- [I] https://www.sqlite.org/isolation.html
- [W] https://www.sqlite.org/wal.html （全页实读，包括WAL-reset修复）
- [F] https://www.sqlite.org/foreignkeys.html#fk_enable
- [S] https://www.sqlite.org/stricttables.html
- [B] https://www.sqlite.org/backup.html
- [T] https://www.sqlite.org/lang_transaction.html
- [U] https://www.sqlite.org/lang_update.html
- [Q] https://www.sqlite.org/optoverview.html
- [G] https://www.sqlite.org/series.html
- [H] https://www.sqlite.org/threadsafe.html
- [A] https://aiosqlite.omnilib.dev/en/stable/
- [P] https://docs.python.org/3/library/sqlite3.html#sqlite3-connection-context-manager
- [L] https://www.sqlite.org/lang_altertable.html
- [R] https://www.sqlite.org/pragma.html#pragma_synchronous
- [C] https://www.sqlite.org/gencol.html
- [D] https://developers.cloudflare.com/d1/sql-api/sql-statements/

## 冲突与裁决

| 冲突点 | 社区主张 | 裁决与官方依据 |
|---|---|---|
| 锁错误 | 加busy_timeout就行 | 区分仍被占的锁、WAL旧快照升级；后者释放快照重跑事务，不能只重试UPDATE [I] |
| 并发模式 | WAL永不阻塞、回滚模式全串行 | WAL仍单写者；回滚模式允许多个读者及写事务早期读者，写主文件阶段需排斥读者 [I/T/W] |
| 耐久性 | NORMAL safe所以统一设置 | NORMAL保一致性不保证断电后所有已确认提交；按耐久性要求选，不继承固定调优配方 [W] |
| 外键 | 设置过一次就够 | 每连接、事务外开启并回读；事务内修改无错误但无效，integrity_check不代替foreign_key_check [F] |
| 类型 | STRICT不允许任何转换 | 允许无损转换；ANY在STRICT保留原值/类型；版本≥3.37 [S] |
| 备份 | 主文件+两个sidecar顺序复制即可 | 在线备份API/VACUUM INTO；WAL是持久状态，不能任意删除或分离 [W/B] |
| 引擎版本 | 系统CLI版本就是应用版本 | 查实际连接SELECT sqlite_version()/sqlite_source_id()；WAL-reset修复为3.51.3及3.50.7/3.44.6回移 [W] |
| 宿主 | D1/Turso都等于SQLite | D1平台配置给cloudflare；Turso重写引擎不拿来替代SQLite事实 [D] |
| 迁移 | 直接ADD STORED或改schema文本 | 受版本/语法限制；复杂变更按官方重建顺序，保留索引触发器，FK检查失败不发布 [C/L] |

## 最终合入清单

**立项门通过**：4项六个月内活跃且≥8分、范围相符的候选（1/4/6/8），来自4仓库。
不是“单一权威上游改写”，没有官方例外。评分不是来源整体正确率；4只采用已核实片段。
当前没有重写正文，以下是Phase C候选贡献，最终是否merged由基线实际缺口决定。

| id | 上游 | 计划relation | 贡献 |
|---|---|---|---|
| terminalskills-sqlite | TerminalSkills/skills skills/sqlite | merged | 连接生命周期、备份入口；不带CRUD课程 |
| moollm-sqlite | SimHacker/moollm skills/sqlite | merged | 耐久性警惕、引擎与工具边界 |
| openfang-sqlite | RightNow-AI/openfang crates/openfang-skills/bundled/sqlite-expert | merged | 短事务/单写者/索引观测 |
| harness-sqlite | harness-studio/harness-studio skills/sqlite-concurrency | merged | 仅原子SQL和check-then-act事务意图；不带错误aiosqlite解释 |
| sqlite-official | sqlite.org上列引擎文档 | reference | 官方语义校准；未假定文档许可即代码public-domain许可 |
| domain-expert-sqlite | chrishuffman5/domain-expert | reference | 只取诊断主题清单，事实均重新官方取证 |
| sqlite-wal-community | pvillega/claude-templates | reference | BUSY_SNAPSHOT覆盖与版本风险主题 |
| litestream | benbjohnson/litestream-skills | reference | 灾备覆盖面；过期不计立项 |
| oss-ai-sqlite | CodeAtCode/oss-ai-skills | reference | GPL，不拷贝文本/代码，仅参考覆盖面 |

## 建设范围与评测准备

category=framework。只覆盖嵌入式SQLite及文件生命周期，不讲通用Python/ORM API，
排除Cloudflare D1/Supabase平台配置和Turso引擎扩展。
评测现归档于 `research/evals/sqlite/`，含4正例+1近似负例（原3正例后追加复杂迁移场景5）。临时Scope/SOURCES骨架已移出安装目录。夹具都是单文件、stdlib、临时目录，
不依赖系统sqlite3 CLI，不联网、不接生产库；files使用扁平复制后的basename。

| 场景 | 夹具 | 可判定行为 |
|---|---|---|
| WAL快照升级与外部提交 | reservation.py | 旧快照失效；重读后拒绝3件请求，库存1；不重放外部副作用 |
| 完整性ok却丢已提交订单 | backup_job.py | writer保持打开；一致性备份恢复(17,950)，不只看integrity_check |
| 外键静默失效与类型迁移 | import_orders.py | 事务外每连接FK；独立拒FK/类型两路径；失败迁移保留有效记录 |
| D1绑定/远程迁移近似负例 | 无 | 不读取sqlite，使用cloudflare平台指导 |
| 复杂AUTOINCREMENT父表重建 | catalog_migration.py | 保留历史ID高水位、子表、索引/触发器/视图；失败全状态不变 |

第一例保持“竞争写在首次读之后”的真实顺序，避免把题目变成一行BEGIN IMMEDIATE即可；
不能重复执行竞争写，必须分辨数据库事务重放和外部已完成行为。
第三例分别验证两个约束，否则先触发FK异常会掩盖amount仍是宽松类型的错误。

## 基线缺口

Main已完成原始场景1–4基线，模型 **openai/gpt-5.6-sol、medium**。
答案及events表明三个原始夹具的消费者错误均被修复；不能把未提某个备选方案算成实质缺口。
场景3原夹具没有索引/触发器/历史AUTOINCREMENT状态，不能用通用migrate函数未保存这些对象
来判它在该场景失败。因此保留原场景，追加包含真实对象与历史ID契约的场景5；补测6/6达成，仍未发现消费者合同缺口。

## 评测结果

| 场景 | 模型 | 有/无skill | skill_read | 达成行为 | 备注 |
|---|---|---|---|---|---|
| 1 | openai/gpt-5.6-sol、medium | baseline | false | E1–E3达成；E4恢复安全达成，未说明IMMEDIATE预防备选 | 未构成消费者失败 |
| 2 | openai/gpt-5.6-sol、medium | baseline | false | E1–E3达成；E4恢复隔离/检查数据达成，未显式给FK检查 | 现有夹具无FK，不以措辞算增益 |
| 3 | openai/gpt-5.6-sol、medium | baseline | false | E1/E2/E4达成；E3类型及版本分支达成；E5有效数据保留与失败回滚达成 | 既有fixture无索引触发器，不加隐藏失败条件 |
| 4 | openai/gpt-5.6-sol、medium | baseline | false | E1不读sqlite、E2平台配置与remote目标达成 | 无本技能增量 |
| 5 | openai/gpt-5.6-sol、medium | baseline | false | 6/6 | 下一ID901；保留子表/索引/触发器/视图；负价全状态不变 |

证据目录：`/tmp/hs-five-20260912/evals/sqlite/openai-gpt-5.6-sol-medium/baseline/`。
逐条读各场景result.json/answer.md，并从events.jsonl抽取真实toolResult：

- 1/events.jsonl行591、1438：`accepted False / remaining 1`；行928、1797：
  `competing_commits: 1`。答案说明517旧快照、全事务回滚重读、三次上限。
- 2/events.jsonl行65：旧备份`restored [] / live [(17,950)]`；行818修复后两者均`[(17,950)]`。
  行589代码使用独立只读source.backup、关闭destination再发布；没有关闭live writer。
- 3/events.jsonl行2892、3267、3525：独立missing-customer/text拒绝、FK violation结果、
  failed migration旧行保留与clean STRICT成功；行3553/3603补证FK拒绝及迁移失败数据不变。
- 4/result.json：skill_read=false；answer.md采用Wrangler环境/--remote，不使用本地SQLite文件操作。

这些模型运行链接SQLite **3.53.1**；Main此前三个原始夹具使用**3.53.4**，新增场景5的`uv run`使用**3.53.1**。不要把不同Python运行环境混成同一次验证。

### 追加场景5的区分度与透明契约

`catalog_migration.py`建立真实products AUTOINCREMENT父表、unique SKU index、shipments
ON DELETE CASCADE子表、price_audit触发器、public_catalog视图及user_version=1。
曾插入并删除ID900，表中只有ID1；票据ID不得复用在夹具docstring与用户query都明确。
有效数据库要求成功迁移并逐个exercise消费者；无效数据库价格-5，要求报告ID1并完整回滚。
失败比较覆盖schema、sequence、子表、审计与FK开关，而非只检查“没有抛异常”。

官方依据补充：https://www.sqlite.org/autoinc.html 明确AUTOINCREMENT使用历史已提交最大ROWID，
状态在sqlite_sequence，而非仅由当前MAX(id)决定。此为真实应用文件迁移责任，不是隐藏谜题。
Main已实跑原夹具：有效文件因暂时失效的public_catalog视图导致迁移被拒，负价文件因CHECK失败被拒；两者均回滚。随后同模型补测完成，最终migrate保存sqlite_sequence并恢复schema对象，在事务外关闭/恢复FK，成功后新ID901、shipments仍为(41,1)，审计与视图正常，四项消费者非法输入独立拒绝；负价报告ID1/-5，完整快照不变。

补测证据：5/answer.md:14–40；workspace/catalog_migration.py:46–112为实际修复。events工具结果`call_6cdtfSpZUjF8xEyWnqrXbCLY`及`call_qd9RzvdoDA8nqOzlEaPQBM1Z`均显示`next issued id 901`、保留发货/审计、四种rejected、`foreign key violations []`和`state unchanged True`。六项全部达成，不把原题缺少备选解释改写成实质失败，也不把本次基线修复冒充skill正文增益。

## 许可、证据限制与后续阶段

- API返回domain-expert NOASSERTION；实读LICENSE是MIT加免责声明；不用frontmatter的Public Domain。
- pvillega、sitharaj、honki的递归树未发现LICENSE文件，记录NONE，不伪造MIT。
- GPL候选只能reference；不复制任何其文字或样例。无许可候选没有选作merged。
- Phase A/B已完成调研、评测准备及五场基线；没有进入正式skill的Phase C/D/E，不发布空骨架。
- 子代理未运行格式化/lint/构建/测试/安装冒烟/模型评测/全库校验，未commit/push。
- Main已实跑三个原始夹具，实际链接SQLite 3.53.4：reservation输出517 SQLITE_BUSY_SNAPSHOT、
  remaining 1；backup输出integrity ok、restored []、live [(17,950)]；import输出FK setting 0，
  非法记录以text类型保留。此为Main回传执行证据，证明夹具可复现，并非模型基线结果。

### 读取修订与待执行项

以下为已登录 `gh api repos/<repo>/commits/<default_branch>` 返回的HEAD（不是搜索摘要）。

| 上游 | 读取时HEAD |
|---|---|
| TerminalSkills/skills | `56037efc04d0ffd20a0a85b18894115df74bd70f` |
| chrishuffman5/domain-expert | `795808b8b41b8a529c0c9b88892fae9f5904611c` |
| pvillega/claude-templates | `e1d904d4e1015c6af14cde4d557515c6d6f1e291` |
| harness-studio/harness-studio | `caa0c9b8a36ac6397ac70a8e551410790106d626` |
| benbjohnson/litestream-skills | `7d48f5f3638c8c4b8b94693297f0369d75308349` |
| RightNow-AI/openfang | `acf2587e46be174c10200489c9a2d23a39a98aeb` |
| CodeAtCode/oss-ai-skills | `4bc721667ca970db59529cbcd20f61a69aa362d4` |
| SimHacker/moollm | `541bf236194bddca05a12008505df0931c86ee85` |
| sitharaj88/claude-skills | `fb8d7127c7d053cffb7587e29fc0d48e0c842780` |
| honki12345/my-agent-skills | `29a85e0f1cec40d9ad5411c93a1188e3171f79ba` |
| modbender/skill-library-mcp | `5934c483768f9f8c792b8b7c0bb6f45a77df3edf` |
| tursodatabase/agent-skills | `34ced52fd1bd32e802622126e299cfa886d68441` |
| 0xDarkMatter/claude-mods | `285cd8e21f2a3069a74a113a29fafa4133087c05` |
| ChristopherDavenport/christopherdavenport-marketplace | `611d9835ec22d3b5ceba07afafc4b3ddce719e1f` |

SOURCES.yaml当前四个候选均为reference，诚实反映尚无正文合入。Phase C确定贡献后才改merged，
并执行仓库pin工具；所以现在不应声称满足最终SOURCES至少一项merged的发布门。

官方ALTER页面另有重要更新：3.53.0新增ALTER COLUMN SET/DROP NOT NULL；不能继续笼统声称
SQLite不支持任何ALTER COLUMN。此项与实际链接版本一起纳入基线后的迁移范围评估。

## Phase B构建准备交付（历史记录）

当时只保留评测与原始故障，不发布Scope骨架。原5场景与4份夹具现已原样迁入[正式评测目录](../skills/sqlite/evals/)，不再维护准备目录副本或骨架恢复命令。用户随后要求正式建设，后续对照沿用同模型medium及独立输出。首轮部分扩展解释没有覆盖，仍不笼统写成“21/21全达成”，也不据此宣称消费者失败。

## Phase C 正式构建（2026-09-12）

用户获知上轮只有Phase A/B与评测准备、没有正文后，明确要求“好，正式开始构建skill”。
本轮据此继续建设，不因强基线尚无消费者缺口再次停笔；这是用户继续决定，
不是对基线的重新判负，也不是已经证明with-skill增益。

已恢复 `skills/sqlite/`，直接完成可安装正文与四份按条件读取的reference，
没有保留Scope-only骨架或新增脚本。`research/evals/sqlite/` 的原5场定义和
4个原始故障夹具使用文件复制恢复至 `skills/sqlite/evals/`，无内容转换；
归档旧路径由Main统一移除。正文版本2026.09.12，category=framework。

| 文件 | 实际结构与重点 | 本轮来源落点 |
|---|---|---|
| SKILL.md | 20条不变量；连接诊断、配置、备份恢复、迁移/导入、查询调优五流程；具名验证门；边界与报告模板 | 四个准入社区skill的重写贡献及官方事实 |
| references/connections-and-transactions.md | 连接归属/语句结束；原子SQL；按错误码和阶段恢复；旧快照完整重算，不重放外部副作用 | TerminalSkills、harness、OpenFang；transaction/isolation/busy_handler/pragma |
| references/wal-backup-and-recovery.md | WAL拓扑与耐久性；修复分支；checkpoint三返回值；引擎备份、恢复隔离、业务事实检验 | TerminalSkills、moollm；wal/backup/vacuum/pragma |
| references/types-and-migrations.md | affinity与STRICT；NULL/FK；版本化ALTER；复杂依赖重建；sqlite_sequence历史水位及失败不变 | moollm；datatype3/stricttables/foreignkeys/lang_createtable/lang_altertable/autoinc |
| references/query-plans-and-indexes.md | 观测而非追求无SCAN；复合/覆盖/表达式/部分索引；统计策略；结果等价与写成本 | OpenFang；eqp/optoverview/expridx/partialindex/lang_analyze |

本轮重新以已登录 `gh api` 获取四库default branch及HEAD，按该40位SHA读取完整SKILL.md
及许可原文；HEAD与前表一致。没有匿名GitHub HTTP、重搜候选、pin或修改其他skill。
四项实际重写后在SOURCES标为merged，并逐项记录文件落点及被剥离的错误/固定调优。
RightNow-AI的license API识别为NOASSERTION，但实际返回并完整读取LICENSE-APACHE，
文本明确Apache License Version 2.0，故按实读许可记Apache-2.0，不复制API的未知判断。

官方页面本轮实读，未从历史摘要冒充取证。额外裁决：

- ALTER COLUMN SET/DROP NOT NULL从3.53.0可用，native ALTER不再被笼统禁止；
  冗余NOT NULL时DROP不保证一次移除全部，要求检查结果。
- WAL-reset主线3.51.3及后续已修复，3.50.7/3.44.6是回移分支；
  不能只比较是否小于3.51.3，也不假定发行包版本等于应用加载引擎。
- 复杂重建先建新表、复制、移除可能暂时无效的依赖、删旧、改新名、重建依赖；
  incoming FK、外部trigger和view不能只靠tbl_name过滤；保存历史sequence而非MAX(id)。
- 官方backup后半段说明并发写会使增量备份重启；不承诺固定开始时刻快照，
  只承诺完成的一致性快照，精确新鲜度需要应用标记/协调。
- 本轮明确实读 https://www.sqlite.org/copyright.html ，其public-domain声明包含
  code **and documentation**。SOURCES官方docs记录reference、license NONE并解释
  无需许可而非未知继承，不假造MIT/CC0；官方文本未原样复制。

### 证据与待Main执行

历史结果保持不变：原始消费者错误被无skill模型修复；场景5基线6/6，
首轮某些扩展解释仍是partial explanation，不转写为消费者失败或正文增益。
本轮只有来源取证和正文建设，没有运行测试、格式化、lint、构建、安装冒烟、
模型评测或全库校验，未提交/推送。with-skill对照、原始夹具字节校验、
结构及引用校验、生成NOTICE/目录和安装证明统一待Main执行。

## Phase D 实际 with-skill 审阅（2026-09-12）

本节覆盖原5场、21条 `expected_behavior`，依据[原评测定义](../skills/sqlite/evals/evals.json)、
各场最终 `answer.md`、最终workspace代码和 `events.jsonl` 的真实toolResult逐条判读。
`status=ok`只表示运行结束，不作为达成证明；读到的skill/reference内容也不算模型已解释或已执行。
本轮审阅没有重跑任何模型、夹具、测试、编译或安装命令，没有改正文、评测或夹具。

证据缩写（本节均为绝对路径，不与历史baseline混用）：

- `R` = `/tmp/hs-five-build-20260912/evals/sqlite/openai-gpt-5.6-sol-medium/skill`；
  `Rn`表示`R/n`，答案行号记`Rn/answer.md:L`，事件行号记`Rn/events.jsonl:L`。
- `Wn` = `/tmp/hs-five-build-20260912/workspaces/sqlite-openai-gpt-5.6-sol-medium-skill-n`。
- 历史baseline仍以本文件Phase B既有判读为准；没有重跑或将历史结果统一改成21/21。

### 五场汇总与真实导航

五份`result.json`均记录唯一被评测模型`openai/gpt-5.6-sol`、`thinking=medium`、
`baseline=false`。实际assistant消息的`provider=openai/model=gpt-5.6-sol`可分别在
R1/R2/R3/R5事件行23及R4行25核对；以下时长来自各自`duration_s`，不是纯推理耗时。
正例实际链接SQLite均为3.53.1。

| 场景 | 逐条结果 | skill_read | 时长/s | 实际成功读取（toolResult事件行） |
|---|---|---|---:|---|
| 1 WAL库存竞争 | 3 pass / 1 partial / 0 fail | true | 221.7 | SKILL行35 → `connections-and-transactions.md`行64 |
| 2 在线备份 | 4 pass / 0 partial / 0 fail | true | 204.2 | SKILL行35 → `wal-backup-and-recovery.md`行71 |
| 3 导入与类型迁移 | 3 pass / 2 partial / 0 fail | true | 251.7 | SKILL行31 → `types-and-migrations.md`行72 |
| 4 纯D1近似负例 | 2 pass / 0 partial / 0 fail | false | 168.9 | sqlite可用但无读取；Cloudflare官方迁移/环境/CLI正文行154/157/160 |
| 5 复杂父表重建 | 6 pass / 0 partial / 0 fail | true | 261.4 | SKILL行34 → `types-and-migrations.md`行68 |

合计 **18 pass、3 partial、0 fail（21条）**。四个正例均先读正文再读对应的一份reference，
未见重复读取同一SQLite reference；`query-plans-and-indexes.md`本组没有读取，
因为没有查询规划场景，不能据此断言导航失效或该引用已被验证。
D1场景没有读取cloudflare skill正文，而是查询Cloudflare文档并读取官方页面；
这满足“路由到平台指导”，不虚报加载了不存在于本场读取记录的skill。

### 21条逐项评分与最终证据

`partial`表示复合预期中有明确未覆盖子项；不折算成pass，也不自动等同消费者故障。

| 条号 | 评分 | 可复核证据与边界 |
|---|---|---|
| 1.E1 | pass | R1/answer.md:15–20明确旧WAL快照、517及timeout不能刷新；事件103实跑原夹具为`error 517 SQLITE_BUSY_SNAPSHOT`。 |
| 1.E2 | pass | W1/reservation.py:13–22、31–38先rollback后重开并重读；18–19只在attempt=0调用竞争回调。事件809最终`accepted False / remaining 1`；初始5、竞争减4、请求3仍在代码49–59，未改题。 |
| 1.E3 | pass | W1/reservation.py:6、10–39上限两事务，只重试首次写阶段的BUSY_SNAPSHOT，不缓存跨事务库存、不重放回调；R1/answer.md:33–39给有界策略。事件809证明实际退出并拒绝。 |
| 1.E4 | partial | W1/reservation.py:13保留首次BEGIN，仅在竞争commit之后的恢复使用IMMEDIATE；事件809未死锁。R1/answer.md:26–38解释恢复提前拿写权限，但没有明确区分“正常情况下首次读前IMMEDIATE预防”与“本同线程夹具首次拿锁会阻挡回调”的理由。消费者恢复安全已达成，缺的是扩展解释。 |
| 2.E1 | pass | R2/answer.md:5–13解释WAL提交与有效但陈旧主文件；事件120实证旧备份`restored orders []`且live有`(17,950)`。 |
| 2.E2 | pass | W2/backup_job.py:23–30使用stdlib `Connection.backup`；43–60让writer保持打开到备份后查询。事件571为`integrity ok`、restored与live均`[(17,950)]`。关闭的是备份专用source连接，不是writer。 |
| 2.E3 | pass | W2/backup_job.py:7–36只清理独立暂存文件；不删除源WAL/SHM、不改journal、不停止writer。保留原夹具先checkpoint建表、后提交订单的顺序（46–51）；不是靠新增checkpoint让主文件复制蒙混通过。 |
| 2.E4 | pass | R2/answer.md:55–67给独立目录、无旧sidecar、integrity/FK/业务/版本/sequence检查，停止并关闭所有用户，保存旧库与恢复侧文件，隔离发布和重开验收。本项要求解释restore流程；不把该文字流程算成已实跑服务恢复。 |
| 3.E1 | pass | R3/answer.md:5解释事务内PRAGMA静默无效；W3/import_orders.py:32–39事务外启用并回读，53–56每导入连接在BEGIN前调用；事件126原状态`import FK setting 0`，3341独立FK拒绝。 |
| 3.E2 | partial | 现有孤儿确实被发现：W3/import_orders.py:80–88用LEFT JOIN，事件3341报告`missing customers: [(2,999)]`，答案7不信integrity ok。但要求的`foreign_key_check`只在成功重建后136–138执行；坏库在101–103已经抛错，没有用该PRAGMA暴露旧孤儿的执行证据。不是漏掉孤儿的消费者故障，但指定诊断子项未达成。 |
| 3.E3 | partial | W3/import_orders.py:23–29、95–123实查链接版本并按3.37.0分支构造合法STRICT DDL；事件3341选择STRICT且真实拒绝TEXT，无ADD STRICT/BOOLEAN/DECIMAL。R3/answer.md:6、40解释affinity和版本，却未说明STRICT仍允许无损转换；代码46的Python int-only是更窄导入策略，不能充当STRICT无损转换解释。 |
| 3.E4 | pass | W3/import_orders.py:181–190分别用缺失客户+整数金额、现存客户+非数字金额；241–254再绕过应用层独立测试数据库约束。事件3341同时有导入两种拒绝及迁移后FK/TEXT两种拒绝，非一条非法记录由先触发约束遮蔽。 |
| 3.E5 | pass | W3/import_orders.py:99–148单事务显式复制、保存并恢复orders索引/trigger SQL、检查后commit、异常rollback。事件3341报告订单2原值/text/客户999、有效订单1仍`(1,1,250)`且schema相同，干净副本重建成功。夹具没有索引/trigger，保存路径是代码证据，不能声称已动态验证这些对象或更广依赖。 |
| 4.E1 | pass | R4/result.json为skill_read=false；全部读取调用没有sqlite正文或引用。事件154/157/160是真实Cloudflare官方页面toolResult，平台边界正确。 |
| 4.E2 | pass | W4/wrangler.jsonc:6–26分别声明preview/production数据库；R4/answer.md:45–75同时指定`--env production --remote`、区分local与`--preview`，无本地WAL/busy_timeout/文件复制建议。事件674只证明`jq empty`语法成功；UUID为占位值，答案84明确未执行远程操作。 |
| 5.E1 | pass | W5/catalog_migration.py:61–62、97–143、156–160单事务重建AUTOINCREMENT，保存历史sequence并取原/新水位较大者，不用当前MAX(id)替代；事件2084给新STRICT schema与`next issued id 901`；事件3141独立断言结果再次证明水位900→下一ID901。 |
| 5.E2 | pass | W5/catalog_migration.py:51–58在事务外关FK，145–149检查，161–170恢复并回读；原incoming FK及ON DELETE CASCADE定义24–27未改。事件2084保留`shipments [(41,1)]`、`orphan shipment rejected`、`foreign key violations []`；3141核对FK=1。 |
| 5.E3 | pass | W5/catalog_migration.py:82–95、114–120保存products显式索引/trigger和具名public_catalog并恢复；事件2084为`duplicate SKU rejected`、audit`[(1,1200,1300)]`、catalog`[(1,'BOOK',1300),(901,'NEW',700)]`；事件3135实际断言代码及3141结果复核三项消费者行为。 |
| 5.E4 | pass | W5/catalog_migration.py:105–109有INTEGER/NOT NULL/CHECK/STRICT；145–157所有检查后事务内设user_version=2并commit。事件2084独立negative/text rejected且保留产品1；事件3135/3141断言版本2与STRICT标记。 |
| 5.E5 | pass | W5/catalog_migration.py:69–80报告原ID/价格/存储类，158–170回滚并恢复FK；snapshot:173–182包含products、shipments、audit、完整非内部schema、sequence、version、FK。事件2084明确`id=1 price_cents=-5 storage=integer / state unchanged True`，3141独立断言before=after、FK=1、user_version=1。 |
| 5.E6 | pass | 最终代码13–43与185–240保留两数据库及原消费者检查，未删除负价或绕过检查；异常回滚后重新抛出，水位来源为sqlite_sequence。事件2084/3141同时展示成功全合同与失败完整不变，不将中途失败或模型自述代替最终结果。 |

复杂迁移的覆盖范围必须单列：场景5真实覆盖incoming FK、products所属trigger、
独立命名view、唯一索引及已删除900的sequence历史状态。**没有外部表所属trigger、
额外view或view依赖链夹具**；最终代码82–95也仅搜`tbl_name='products'`索引/trigger并
单取`public_catalog`，不是通用依赖图迁移器。不能由本次6/6宣称所有外部依赖都能保留；
同样不能给未在原query/expected/夹具内的通用化要求新增隐藏扣分。
场景3的完整依赖覆盖更窄，应沿用同一限制。

### 历史对照与严格增益限制

- 历史1.E4的扩展解释缺失本轮仍为partial；本轮虽采用IMMEDIATE恢复，不等于解释齐全。
- 历史2.E4未显式给FK检查，本轮答案给出完整检查项，记为解释覆盖改善；
  原备份消费者基线已经修复，不能把补写PRAGMA名称当成恢复能力增益。
- 历史3.E2基线已用foreign_key_check暴露旧坏数据，本轮用LEFT JOIN正确识别孤儿，
  但指定诊断方法未展示；这是本次覆盖回退，不应被“最终导入修好”抹去。
  3.E3当前遗漏无损转换说明，也不把版本和类型拒绝已有证据一并抹成失败。
- 原三个消费者错误和复杂迁移在无skill基线已修复，场景5基线就是6/6；
  两配置都满足的消费者条目为非区分项，D1负例也不是正文收益。
- 当前是同一强模型、同一medium的单次五场with-skill；baseline是此前独立批次，
  不是同时配对重复试验。未测其他模型、重复方差、held-out触发率或生产环境。
  不宣称D2“闭合真实缺口”通过，不把18/21当成功率增益，也不为了强行制造差异重启知识题。
- 用户在获知强基线后明确继续正式建设，故仍交付完整skill；该产品决定与
  “已证明skill提升消费者结果”的科学主张严格分开。三个partial不阻碍如实记录已完成正文，
  但禁止写成全项通过；本节没有提交或推送声明。

### 公共结构、安装与本机机制证据

以下为Main本轮已执行并回传的公共验证事实，本审阅者未重跑：

- 五个正式skill各有4份reference；SQLite安装包共12文件，每包仅一个`SKILL.md`。
- `uv run tools/validate_skills.py`：60 skill(s)，0 errors、0 warnings；
  `build_catalog --check`：current 60。
- `check_upstream`检查五主题19条仓库型来源记录全部up_to_date；`--pin`更新0。
- 隔离`npx skills`安装恰好五包，源目录与安装复制全部文件逐字节一致，
  证明正文、引用及SQLite评测资源一起可达，不只是根文件存在。
- 原五主题25场定义和31份夹具字节未改；SQLite原5场与4夹具唯一现址为
  [skills/sqlite/evals](../skills/sqlite/evals/)。旧research副本已安全删除，
  前文旧路径只作历史叙述，不恢复双份目录。
- Main另用本机Python实际链接SQLite **3.53.4**执行机制实验：
  native `ALTER COLUMN SET NOT NULL`确实拒绝NULL，DROP后接受；
  commit后backup恢复`[(1,0),(2,None)]`，`integrity_check=ok`、`foreign_key_check`空。
  这与模型运行的3.53.1分开记录；只证明本机语法与提交后备份机制，
  **不是电源断电、网络文件系统或生产恢复演练**，也不是额外with-skill模型得分。
