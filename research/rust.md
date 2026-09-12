# rust 调研记录

> Phase A 来源门通过；Phase B 四场景基线已实跑并复核，14/14行为达成，未证明技能增益。停留Phase B，不写正文、不发布骨架。

## 调研日期与检索途径

- 调研与API复核：2026-09-12；六个月活跃截止2026-03-12。
- 使用已登录 `gh api` 读取仓库元数据、递归树、原始contents/base64及HEAD；未匿名访问GitHub。
- 首次 `search/code` 发生连接timeout，已知仓库API重试成功；没有认证失败或限流。
- Web检索 `rust SKILL.md github best practices skills` 得到Apollo、leonardomso、full-stack、ytakano、pgdog等线索；搜索摘要不用于评分。补查actionbook及github/awesome-copilot。
- 原文获取：`gh api repos/<repo>/contents/<path>`；元数据：`gh api repos/<repo> --jq '{stars:.stargazers_count,pushed:.pushed_at,license:.license.spdx_id}'`；HEAD：`gh api repos/<repo>/commits/<default_branch> --jq .sha`。用下列HEAD作为复核锚点；本阶段未写正式SOURCES合并关系。
- 官方对照使用Rust Reference、std、Cargo Book、Edition Guide、Rustonomicon及Tokio rustdoc；Context7解析 `/websites/rs_tokio_tokio` 后查询Sender::send/reserve取消语义，与rustdoc一致。

## 立项结论与权威重估

**按现有判据可立项，无需官方厂商例外。** 共实读14候选（8仓），4项INCLUDE，其中明确可重写的3项是full-stack的cargo-build、unsafe-ffi，以及github的Rust instructions；均六个月活跃且≥8。另1项仅reference（pgdog AGPL）；ytakano是7分MAYBE。同仓不同skill允许计数，但2份主干同仓高度相关，不能伪称3个独立专家背书。

路线图“仅Apollo一份通用权威”不足以继续阻止立项，亦不应改成“Apollo天然主干”：Apollo确为生产Rust团队，但不是Rust语言维护方；chapter_09把`&mut T`写成不Send、把Cell限制为Copy，三条抽查两错，按硬门REJECT。GitHub组织维护的文件是跨厂商社区规范，也不是rust-lang官方；保守权威分1。full-stack只有4 stars，按活跃社区1分，不冒充专家；其Cargo和unsafe内容的可执行性与官方一致性使其仍过8分。

ytakano API个人资料只确认用户名及个人站链接，没有可核验的专家履历；actionbook README有ZhangHanDong工具配置示例，不足以证明本技能作者身份。本轮两者均按社区1分，未用推测提高权威分。未发现可直接使用的rust-lang官方通用agent skill，故不援引官方例外。

## 候选表

评分：权威/新鲜/具体/正确/许可；总分≥8仍可被正确性0的硬门否决。新鲜度按仓库pushed_at，不冒充skill路径修改日期。所有行均实读入口；深审见后文。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | apollographql/skills `skills/rust-best-practices/SKILL.md` | [原文](https://github.com/apollographql/skills/blob/c288eb80629dd2309eed81f23d693f66a452d043/skills/rust-best-practices/SKILL.md) | 112 | 2026-07-29T20:58:59Z | MIT | rust-best-practices | 2 | 2 | 3 | 0 | 2 | 9 | REJECT | 专家组织仍有基础事实错误：&mut T Send、Cell仅Copy，不能把品牌当正确性 |
| 2 | leonardomso/rust-skills `SKILL.md` | [原文](https://github.com/leonardomso/rust-skills/blob/fd2a861ab0406a4ac536a55274d14ea6fd1ca9c9/SKILL.md) | 504 | 2026-06-14T22:51:13Z | MIT | 通用265规则 | 1 | 2 | 3 | 0 | 2 | 8 | REJECT | 取消表把Mutex::lock算安全，read_exact错误解释；不能直接搬265条 |
| 3 | full-stack-skills/rust-skills `skills/rust-concurrency/SKILL.md` | [原文](https://github.com/full-stack-skills/rust-skills/blob/d7adb07ef99144976e0c8d9459750b559d2e2f4c/skills/rust-concurrency/SKILL.md) | 4 | 2026-09-11T15:49:49Z | Apache-2.0 | rust-concurrency | 1 | 3 | 3 | 0 | 2 | 9 | REJECT | Send/Sync定义及Arc<Mutex<T>>无条件线程安全均错；监督清单仅作覆盖参照 |
| 4 | full-stack-skills/rust-skills `skills/rust-cargo-build/SKILL.md` | [原文](https://github.com/full-stack-skills/rust-skills/blob/d7adb07ef99144976e0c8d9459750b559d2e2f4c/skills/rust-cargo-build/SKILL.md) | 4 | 2026-09-11T15:49:49Z | Apache-2.0 | rust-cargo-build | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | Cargo语义、最小矩阵及版本预检适合主干 |
| 5 | full-stack-skills/rust-skills `skills/rust-api-design/SKILL.md` | [原文](https://github.com/full-stack-skills/rust-skills/blob/d7adb07ef99144976e0c8d9459750b559d2e2f4c/skills/rust-api-design/SKILL.md) | 4 | 2026-09-11T15:49:49Z | Apache-2.0 | rust-api-design | 1 | 3 | 3 | 0 | 2 | 9 | REJECT | 模块命名UpperCamelCase及Cargo强制kebab-case均错 |
| 6 | ytakano/rust_skills `skills/rust-c-ffi-safety/SKILL.md` | [原文](https://github.com/ytakano/rust_skills/blob/9692ab77d916cb5aeb7f190651b76861c8a876f0/skills/rust-c-ffi-safety/SKILL.md) | 18 | 2026-07-23T07:00:40Z | NONE | rust-c-ffi-safety | 1 | 2 | 3 | 1 | 0 | 7 | MAYBE / reference | FFI边界具体；无LICENSE，UTF8有效性与安全不变量混称，仅参考 |
| 7 | ytakano/rust_skills `skills/rust-hardening/SKILL.md` | [原文](https://github.com/ytakano/rust_skills/blob/9692ab77d916cb5aeb7f190651b76861c8a876f0/skills/rust-hardening/SKILL.md) | 18 | 2026-07-23T07:00:40Z | NONE | rust-hardening | 1 | 2 | 3 | 1 | 0 | 7 | MAYBE / reference | 把严格团队政策当通用Rust；C ABI panic说成UB已不准确 |
| 8 | pgdogdev/pgdog `.claude/skills/rust/SKILL.md` | [原文](https://github.com/pgdogdev/pgdog/blob/a8d2201a5945b94377cf550c1044cf58faa25a8b/.claude/skills/rust/SKILL.md) | 5479 | 2026-09-11T23:10:28Z | AGPL-3.0 | rust | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE / reference | 实际Rust应用的通用规范，但AGPL-3.0不得merged |
| 9 | existential-birds/beagle `plugins/beagle-rust/skills/rust-code-review/SKILL.md` | [原文](https://github.com/existential-birds/beagle/blob/d1a74899fbfec74974d1818e4cac7c3d54d44b65/plugins/beagle-rust/skills/rust-code-review/SKILL.md) | 81 | 2026-08-10T01:06:03Z | Apache-2.0 | rust-code-review | 1 | 2 | 3 | 0 | 2 | 8 | REJECT | unsafe_op默认deny错误，raw-pointer间接可达被当引用传递不可变错误 |
| 10 | existential-birds/beagle `plugins/beagle-rust/skills/rust-best-practices/SKILL.md` | [原文](https://github.com/existential-birds/beagle/blob/d1a74899fbfec74974d1818e4cac7c3d54d44b65/plugins/beagle-rust/skills/rust-best-practices/SKILL.md) | 81 | 2026-08-10T01:06:03Z | Apache-2.0 | rust-best-practices | 1 | 2 | 3 | 0 | 2 | 8 | REJECT | Vec::new总分配与if-let guard在then内已释放均错 |
| 11 | actionbook/rust-skills `skills/m01-ownership/SKILL.md` | [原文](https://github.com/actionbook/rust-skills/blob/5c40d3ad785193231b7d0dbfb8e1eb447e5edd94/skills/m01-ownership/SKILL.md) | 1453 | 2026-08-23T11:09:39Z | NONE | m01-ownership | 1 | 3 | 2 | 1 | 0 | 7 | MAYBE / reference | 所有权设计优先有价值；clone成本表过度概括，README徽章不足完整许可 |
| 12 | github/awesome-copilot `instructions/rust.instructions.md` | [原文](https://github.com/github/awesome-copilot/blob/7568a482ce2df38f8965ab5336a3220db796a4ba/instructions/rust.instructions.md) | 38915 | 2026-09-11T20:50:01Z | MIT | instructions | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE | GitHub跨厂商规范非Rust官方；语义正确但教学内容需删 |
| 13 | full-stack-skills/rust-skills `skills/rust-unsafe-ffi/SKILL.md` | [原文](https://github.com/full-stack-skills/rust-skills/blob/d7adb07ef99144976e0c8d9459750b559d2e2f4c/skills/rust-unsafe-ffi/SKILL.md) | 4 | 2026-09-11T15:49:49Z | Apache-2.0 | rust-unsafe-ffi | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | unsafe proof obligation和真实FFI/Miri边界最贴合 |
| 14 | full-stack-skills/rust-skills `skills/rust-workspace/SKILL.md` | [原文](https://github.com/full-stack-skills/rust-skills/blob/d7adb07ef99144976e0c8d9459750b559d2e2f4c/skills/rust-workspace/SKILL.md) | 4 | 2026-09-11T15:49:49Z | Apache-2.0 | rust-workspace | 1 | 3 | 3 | 0 | 2 | 9 | REJECT | 把member profile说成error且lint继承与本地覆盖混写，不能照搬 |

### API HEAD锚点

| 仓库 | 默认分支 | 实读HEAD |
|---|---|---|
| apollographql/skills | main | `c288eb80629dd2309eed81f23d693f66a452d043` |
| leonardomso/rust-skills | master | `fd2a861ab0406a4ac536a55274d14ea6fd1ca9c9` |
| full-stack-skills/rust-skills | main | `d7adb07ef99144976e0c8d9459750b559d2e2f4c` |
| ytakano/rust_skills | main | `9692ab77d916cb5aeb7f190651b76861c8a876f0` |
| pgdogdev/pgdog | main | `a8d2201a5945b94377cf550c1044cf58faa25a8b` |
| existential-birds/beagle | main | `d1a74899fbfec74974d1818e4cac7c3d54d44b65` |
| actionbook/rust-skills | main | `5c40d3ad785193231b7d0dbfb8e1eb447e5edd94` |
| github/awesome-copilot | main | `7568a482ce2df38f8965ab5336a3220db796a4ba` |

## 正确性抽查与官方依据

每项抽查三条；额外发现的明确错误也计入硬门，不用“样本外”逃避。下列编号用于深审与裁决，可直接打开官方原文复核。

- O1 [Tokio select cancellation safety](https://docs.rs/tokio/latest/tokio/macro.select.html)：read/read_buf/recv安全；read_exact不安全；Mutex::lock会丢公平队列位置。
- O2 [Tokio Mutex](https://docs.rs/tokio/latest/tokio/sync/struct.Mutex.html)：async guard专门允许跨await；短同步数据操作通常用同步锁；不保证业务事务自动恢复。
- O3 [Cargo features](https://doc.rust-lang.org/cargo/reference/features.html)：normal依赖feature取并集、additive、default-features不是否决票、feature名称允许下划线等、dep:及?/语法。
- O4 [Cargo workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html)：virtual resolver显式声明、workspace继承是显式opt-in、member profiles忽略、default-members影响默认选择。
- O5 [Rust Reference UB](https://doc.rust-lang.org/reference/behavior-considered-undefined.html)：bool仅0/1、struct各字段有效、raw pointer间接可达与引用/Box传递不可变不是同一回事；str的UTF8约束不可混称所有字节模式本身立即UB。
- O6 [from_raw_parts](https://doc.rust-lang.org/std/slice/fn.from_raw_parts.html)：单allocation、初始化、非空且对齐（即便len=0）、isize::MAX、借用期间无非法写入。
- O7 [Sync](https://doc.rust-lang.org/std/marker/trait.Sync.html) / [Send](https://doc.rust-lang.org/std/marker/trait.Send.html)：`T: Sync`等价`&T: Send`；`&mut T: Send`要求T:Send；Arc/Mutex有泛型条件。
- O8 [Cell](https://doc.rust-lang.org/std/cell/struct.Cell.html)：Cell<T>本身不要求Copy，get才有Copy限制；replace/take可移动非Copy值。
- O9 [unsafe_op_in_unsafe_fn](https://doc.rust-lang.org/edition-guide/rust-2024/unsafe-op-in-unsafe-fn.html)：Edition2024默认warn，不是deny。
- O10 [API naming](https://rust-lang.github.io/api-guidelines/naming.html)：modules snake_case、conversion命名及成本、feature规范不是Cargo强制kebab-case。
- O11 [Result](https://doc.rust-lang.org/std/result/)：recoverable errors、?传播、must_use；项目panic禁令不是语言规定。
- O12 [Vec guarantees](https://doc.rust-lang.org/std/vec/struct.Vec.html#guarantees)：Vec::new不分配；借用slice参数无需强迫所有权。
- O13 [Nomicon FFI unwinding](https://doc.rust-lang.org/nomicon/ffi.html#ffi-and-unwinding)：Rust panic遇不允许unwind ABI安全abort，foreign exception进入不允许unwind的Rust路径才UB；C-unwind须按契约选择。
- O14 [Sender send/reserve](https://docs.rs/tokio/latest/tokio/sync/mpsc/struct.Sender.html)：send失选丢消息，reserve使等待容量与传递值分离；Context7已独立取证。

| 候选 | 规则1 | 规则2 | 规则3 | 正确性 |
|---|---|---|---|---|
| 1 Apollo | Result传播正确 O11 | &mut T不Send错误 O7 | Cell只支持Copy错误 O8 | 0 |
| 2 leonardomso | read比read_exact适合循环select正确 O1 | Mutex::lock取消安全错误 O1 | read_exact拥有内部payload buffer错误：API借用调用者buffer，丢的是操作进度；取消后状态不能重置 O1 | 0 |
| 3 concurrency | Send可跨线程转移正确 O7 | 把Sync定义的主体写成&T而非T错误 O7 | Arc<Mutex<T>>无条件Send+Sync错误（T:Send必要）O7 | 0 |
| 4 cargo-build | additive/unification正确 O3 | virtual resolver显式正确 O4 | dep:与?/语义正确 O3 | 3 |
| 5 api-design | modules UpperCamelCase错误 O10 | Cargo强制kebab-case错误 O3 | From/借用slice原则正确 O10/O12 | 0 |
| 6 ytakano FFI | bool域0/1正确 O5 | null/single allocation/lifetime必要正确 O6 | 把无效UTF8直接归为str值立即UB过强，需区分validity和安全不变量 O5 | 1 |
| 7 hardening | 忽略Result不是成功正确 O11 | Vec越界panic正确 O12 | Rust panic跨C边界一概UB错误 O13 | 1 |
| 8 pgdog | &str借用API正确 O12 | Result传播正确 O11 | must_use用途正确 O11 | 3 |
| 9 beagle review | unsafe_op默认deny错误 O9 | 把&Foo内*mut指向的数据自动纳入共享引用传递不可变错误 O5 | safe API不能导致UB正确 O5 | 0 |
| 10 beagle practices | Vec::new总分配错误 O12 | if-let guard在then使用借用期间就释放错误（借用有效性O5） | Drop不适合异步fallible close的方向正确 O13 | 0 |
| 11 actionbook ownership | 从owner/lifetime定位而非无脑clone正确 O12 | Rc不Send正确 O7 | clone固定alloc+copy错误：Arc clone只共享计数 O7 | 1 |
| 12 github instructions | Result及?正确 O11 | 只读参数借slice正确 O12 | Send/Sync auto trait及unsafe手工实现契约正确 O7 | 3 |
| 13 unsafe-ffi | safe wrapper需满足所有前置条件正确 O5/O6 | padding不可当已初始化序列化正确 O5 | unwind必须依ABI契约正确 O13 | 3 |
| 14 workspace | member profiles导致error错误（官方是ignored）O4 | virtual永远构建所有成员遗漏default-members O4 | members显式继承workspace.package正确 O4 | 0 |

## 深度审查

按未硬拒前的总分取前列8项（4、13、12、8、1、3、5、14）通读入口并浏览链接；另对2、6、9、10做风险驱动扩展。浏览不等于执行上游示例；本批按合同没有运行测试。

### 4. full-stack rust-cargo-build（主干候选）

入口按preflight、router、workflow、规则、验证拆分，frontmatter含标准name/license/description，没有harness注入。实读 `references/dependencies-features-resolver.md`（约3.5KB），涵盖dep:、?/、resolver2/3及虚拟workspace；引用以任务命名，有明确read-when。主要问题是面太大，router达十多主题，和rust-workspace重叠。只取特征统一、有效配置、MSRV矩阵，不合并发布注册表、跨平台链接器教程和缓存调优大全。

### 13. full-stack rust-unsafe-ffi（主干候选）

入口先证明义务再讲unsafe操作、ABI、验证，符合本技能要解决的真实边界。frontmatter可迁移，删其他rust-*依赖即可独立。实读 `references/references.md`，只有类型表和两个官方链接，深度不够，正文必须直接用O5/O6/O13闭合前置条件，不能将短reference当充分证明。Miri不能任意执行foreign code的边界写得好。不要默认加unsafe，只覆盖已经需要它的代码。

### 12. github rust.instructions.md（跨厂商补充）

是Copilot instruction，不是SKILL.md；原文已读。frontmatter `applyTo`须删除，description重写为Rust触发词与否定边界。没有本地references目录，内联链接指向Book/API Guidelines/RFC；本轮实读官方API Naming（O10）与std Result（O11）。通用性强，深度主要是借用API、错误和trait契约，测试与目录教学重复模型常识，基线没有缺口不得保留。GitHub组织名不等于Rust维护方，权威保守计1。

### 8. pgdog rust（仅覆盖参照）

通用规范包含Result、Cow、builder和tokio，但绑allowed-tools且例子/样式很多；没有本地reference router。原文末尾profiling命令及std语义已浏览/对照，不执行项目代码。与Apollo/Beagle基础条目大量重叠；AGPL-3.0是API明确结果，只可reference，不能为“凑第3个merged”复制文字或改写其专有表达。

### 1. Apollo rust-best-practices（从主干降为拒绝）

入口短，9章router，allowed-tools偏Claude但容易剥离；实读chapter_04（约7KB）、chapter_09（约9.5KB）。误导不止风格：指针表的Send/Sync与Cell错误直接影响safe/unsafe API设计。chapter_04还允许某些invariant expect，与入口“never expect”矛盾；unsafe泛化不能依公司handbook裁决。品牌、112 stars及MIT不覆盖正确性0的硬门。保留其候选与失败证据，不作为merged。

### 3. full-stack rust-concurrency（覆盖参照，拒绝正文）

入口长且教学较多；实读 `references/production-async-services.md`（约6.6KB），有actor监督、关闭顺序、backpressure和blocking队列预算。它明确rmux常量不是通用默认，值得借鉴结构；但入口Sync定义及无条件Arc<Mutex<T>>保证错误，硬拒。与Cargo/unsafe同仓不意味着整仓内容都合格。async取消场景的事实改从Tokio官方取得。

### 5. full-stack rust-api-design（拒绝）

入口约500行级教学，前置依赖多个同级skills且“Authority”标示容易令读者误当官方原文。浏览资源清单并打开其API Guidelines Naming官方链接；发现模块命名、feature约束错误，且Copy≤16 bytes与Apollo≤24 bytes矛盾都是武断阈值。不要迁移该套多reference；所有权驱动接口仅从官方与实际基线取必要规则。

### 14. full-stack rust-workspace（拒绝）

入口长、层级分界和项目规模例子重复，frontmatter无注入但大量同级跳转。实读 `references/workspace-dependencies.md`：成员profile说成error（实际ignored），`[lints] workspace=true`再混本地覆盖的例子也不可直接采用。主文“virtual默认全成员”没有default-members条件，根包被一概当反模式，与自己的小workspace例外冲突。用cargo-build+官方Workspaces替代，不能把目录重排作为feature问题修复。

### 其他风险驱动扩展

- leonardomso入口实读全部265规则索引；实读 `rules/async-cancel-safety.md`、`rules/async-no-lock-await.md`。规则之间再互链且main metadata.sources是数组，不符合扁平string metadata约定。取消示例还缺EOF/closed receiver结束条件，容易busy loop；“spawn包装取消”若丢handle会脱离监督。准确抽查已硬拒。
- ytakano `rust-c-ffi-safety`实读入口并浏览 `EvaluationCatalog.md` 的前10类合法/非法C例，主题区分度高；但有效性、安全不变量、可以运行时验证的条件要拆开。全树无LICENSE，README也无许可段，记录NONE，不从名气推许可。
- Beagle review实读入口并浏览 `references/unsafe-deep.md`（安全契约/指针/MaybeUninit/UnsafeCell段）；正文强制加载另一个review-verification skill，有跨技能耦合。unsafe/reference推论有误，不能搬。
- Beagle practices实读入口并浏览 `references/coding-idioms.md` 前6.5KB；Vec::new分配和if-let guard寿命例子错误，与Apollo表面相似不是互相佐证。
- actionbook ownership入口实读，README及递归树实读：无LICENSE文件，README有MIT徽章及末尾“MIT License - see LICENSE”声明，但指向的文件在树中缺失，不能宣称已读取完整MIT grant。按缺失许可保守记NONE，不提升许可分。`user-invocable:false`、meta-cognition层级及相关技能网造成harness耦合；只保留覆盖参照。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 锁跨await | leonardomso一律禁止；Tokio明确async guard为此设计 | 默认短同步临界区；需要跨await维护I/O资源排他时允许async mutex，并单独审业务取消状态 | O2 |
| 2 | 取消安全 | 第三方表称Mutex::lock安全、spawn即可避丢状态 | 区分内存安全、队列公平性、业务取消安全；逐个await写出拥有状态及放弃后后果；接收safe不使封装自动safe | O1/O14 |
| 3 | Send/Sync | Apollo表与full-stack速查省略/写错泛型条件 | 按std条件推导；不以unsafe impl消除编译错误 | O7/O8 |
| 4 | Cargo isolated build | 全workspace/全features green被当充分 | 正常依赖统一可掩盖依赖遗漏；直接声明需要的features，并单独构建消费者库及支持的最小矩阵 | O3/O4 |
| 5 | FFI“验证” | 某些清单暗示null/len检查能证明安全 | 数字检查不能证明allocation、生命周期、初始化、aliasing；外部契约/owner必须承载这些义务 | O5/O6 |
| 6 | Rust panic跨C | hardening一概称UB并强制panic=abort | 依ABI与unwind来源区分safe abort、C-unwind、foreign exception；不擅改整个release profile | O13 |
| 7 | 语言版本 | Beagle把unsafe_op默认deny；宽泛“Rust2024”标签 | 默认warn；项目可明确deny；edition不等于每个API/MSRV | O9/O4 |
| 8 | Copy大小与分配 | Apollo24B、full-stack16B、Beagle Vec::new分配 | 无统一字节阈值；公开Copy承诺与实测性能分开，Vec::new零分配按std | O12 |

## 最终合入清单（Phase C 候选，非已合入）

仅在基线显示相应缺口后落实，pin使用上方实读HEAD或重读后更新。不能把此表写成已完成SOURCES。

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| full-stack-cargo | full-stack-skills/rust-skills `skills/rust-cargo-build` | merged候选 | effective dependency graph, feature unification and compatibility matrix |
| full-stack-unsafe | 同仓 `skills/rust-unsafe-ffi` | merged候选 | safe-wrapper proof obligations and FFI verification limits |
| github-rust | github/awesome-copilot `instructions/rust.instructions.md` | merged候选 | borrowed public interfaces and explicit error contracts |
| tokio-cancellation | docs.rs/tokio select / Sender / Mutex | docs，merged候选 | cancellation ownership, queue admission and task lifetime semantics |
| rust-memory-contracts | Rust Reference + std from_raw_parts + marker | docs，merged候选 | validity, allocation/lifetime and Send/Sync obligations |
| cargo-contracts | Cargo Book features/workspaces | docs，merged候选 | feature and MSRV constraints, not package-layout opinion |
| pgdog-rust | pgdogdev/pgdog `.claude/skills/rust` | reference | coverage only; AGPL-3.0, no wording copied |
| ytakano-ffi | ytakano/rust_skills `skills/rust-c-ffi-safety` | reference | legal/illegal foreign value coverage only; NONE |

## 建设范围与Phase B评测

冻结范围是同一个Rust工程任务上下文：所有权/借用驱动API、错误、async取消/任务生命周期、Send/Sync、锁跨await、unsafe/FFI契约、Cargo workspace/feature/MSRV与验证工具。排除Tauri配置/IPC、智能合约、单个Web框架教程；不加宏大全、数值计算库目录、数据库或embedded分支。

评测定义归档于 `research/evals/rust/evals.json`，三个正例+一个近似负例；实跑时位于 `skills/rust/evals/`。所有预期是行为、边界及错误，不考指定文案。runner逐文件按basename扁平复制，以下每组内文件名均唯一。

| 场景 | 文件 | 区分点 | Main执行时的前置条件 |
|---|---|---|---|
| 1 非Clone Job取消丢失 | Cargo.toml、cancel.rs | 满队列pending send丢弃Job；错误返回所有权；accept线性化与同步竞争 | Tokio固定1.53.1、Cargo可下载依赖；runtime current_thread，无sleep竞态 |
| 2 C回调borrow逃逸 | ffi.rs、packet.h | bool域先于typed reference验证；空null slice；调用期生命周期不能伪装任意'a | 仅review+Rust侧修复，不提供真实C库，不运行故意UB |
| 3 workspace掩盖feature | materialize_workspace.py | cli激活codec/alloc掩盖sdk缺失直接要求；resolver2/3与1.74承诺 | Python标准库生成workspace；本地path依赖，无网络；MSRV须有1.74 toolchain |
| 4 Tauri负例 | 无 | 同有Rust关键词但纯capability配置，不应加载rust | 路由判定无需Rust构建 |

场景1的destroyed bitmask在调用方恢复前记录Job生命周期，ID仅1/2；这是受控夹具而非泛用资源追踪器。场景3materialize只创建指定小目录，拒绝覆盖已有文件，不安装依赖或运行Cargo。场景2真实可检查的是契约边界，不能以普通测试对非法指针“返回错误”声称验证健全性。

## 基线缺口

**Main已实跑，复核最终产物与events后没有发现本轮预期中的未达成行为。**
模型为 `openai/gpt-5.6-sol`，thinking `medium`；四份result.json均为
`status: ok`、`baseline: true`、`skill_read: false`。本代理只审阅已有证据，
没有重跑模型、测试或安装。

证据根目录：

- 运行结果 `R=/tmp/hs-five-20260912/evals/rust/openai-gpt-5.6-sol-medium/baseline`
- 最终产物 `W=/tmp/hs-five-20260912/workspaces/rust-openai-gpt-5.6-sol-medium-baseline-`
- 下表 `R/1/events.jsonl:2194` 等为实际NDJSON行号；`W1/cancel.rs`表示
  `${W}1/cancel.rs`，仅是本记录的简写，不是skill正文的harness变量。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 非Clone Job取消 | 无，4/4达成 | 从send移交改为reserve后移交；原始Job退回，成功与取消都有实际测试 |
| 2 FFI边界 | 无，4/4达成 | 必须连同最终ffi.rs判断；最终answer只总结同一运行中复审后的修正，不是全部实现 |
| 3 feature/MSRV | 无，4/4达成 | 修复独立SDK依赖边，实际安装并使用1.74.0，不是仅口头承诺 |
| 4 Tauri负例 | 无，2/2达成 | 不读rust，不改Rust/Cargo，按window及shell open真实权限边界答复 |

本轮基线包括runner提供的完整agent回合、工具和内置复审/修正流程，
不是无工具单次裸模型回答。场景1和2均在同一回合修正过中间产物；
判定对象是该基线配置的最终可见行为，不能截取中间草稿制造技能缺口。
也不能将闭包测试中选择Job 3/4而非Job 2判为失败——实际检查的是原对象身份与生命周期，
不是偶然ID文案。负例的`skill_read:false`在baseline配置下是预期控制结果，
尚不能证明将来启用skill后的description不会误触发。

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 | openai/gpt-5.6-sol / medium | 无 | false | 1–4，4/4 | result耗时282.0s；初始bitmask=4，最终恢复时bitmask=0；4 tests passed |
| 2 | openai/gpt-5.6-sol / medium | 无 | false | 1–4，4/4 | result耗时291.6s；owned Packet与明确unsafe边界；4个纯Rust测试通过 |
| 3 | openai/gpt-5.6-sol / medium | 无 | false | 1–4，4/4 | result耗时233.7s；isolated SDK E0425→成功，真实1.74.0检查通过 |
| 4 | openai/gpt-5.6-sol / medium | 无 | false | 1–2，2/2 | result耗时184.4s；仅shell:allow-open，不扩大为通配权限 |

### 逐条证据

| 场景/预期 | 观察到的最终行为 | 决定性证据 |
|---|---|---|
| 1.1 丢失定位 | send先取得Job，失选时drop future连带drop Job | `R/1/answer.md:3-5`；初始运行`R/1/events.jsonl:76`输出bitmask=4 |
| 1.2 返回原对象 | Cancelled(Job)/Closed(Job)，reserve成功后同步permit.send | `W1/cancel.rs:19-42`；tests `:99-154`检查payload分配地址与drop标记 |
| 1.3 竞争策略 | biased取消分支优先，拿permit与send间无await | `W1/cancel.rs:31-41`；同时就绪测试`:156-169` |
| 1.4 实跑三路径 | 满队列取消、关闭、成功及同时就绪共4测试；main持有returned Job后读drop标记 | `R/1/events.jsonl:2194`，真实`cargo fmt --check && cargo test && cargo run --quiet`，4 passed；恢复时bitmask=0 |
| 2.1 bool有效性 | RawPacket.enabled为u8，经match才产生安全Packet | `W2/ffi.rs:5-17,52-79` |
| 2.2 lifetime边界 | pub unsafe copy_packet，返回拥有Vec的Packet，不导出任意'a slice | `W2/ffi.rs:13-29,40-55,75-79`；`R/2/answer.md:18-43`纠正callback也须unsafe或受真实注册层封装 |
| 2.3 null及证明义务 | len=0先返回空Vec，非空null返回错误；头部/单allocation/initialized/unmodified写入Safety义务 | `W2/ffi.rs:45-75`；`R/2/answer.md:5-14` |
| 2.4 真实合法用例及限制 | 保留4096；测试disabled、enabled-empty、owned copy、invalid flag；没有运行非法指针或外部C | `W2/ffi.rs:60-78,82-150`；`R/2/events.jsonl:3321` strict rustc test为4 passed；`R/2/answer.md:45-60`明确未链接外国库 |
| 3.1 feature来源 | cli normal dependency开启alloc，workspace统一掩盖sdk遗漏 | `R/3/answer.md:5-13`；events`:70`隔离失败E0425，`:77`原workspace成功 |
| 3.2 依赖修复 | sdk自己的codec边添加features=["alloc"]，保持default-features=false | `W3/workspace/sdk/Cargo.toml:8`；`R/3/answer.md:17-33` |
| 3.3 不以resolver3/全features遮蔽 | 说明resolver3不隔离normal feature且1.74不支持；all-features会掩盖遗漏 | `R/3/answer.md:35-38` |
| 3.4 工具链实证 | 当前隔离sdk及workspace成功；安装1.74后同样两条成功 | `R/3/events.jsonl:720,726,734,786,791,889`；`:786`为`cargo +1.74.0 check --workspace`，`:791`为`cargo +1.74.0 check -p sdk`，`:889`确认rustc/cargo1.74.0 |
| 4.1 不读Rust技能 | result记录false，答复只谈Tauri能力配置 | `R/4/result.json:4-8`；`R/4/answer.md:1-31` |
| 4.2 最小授权及边界 | secondary独立capability仅shell:allow-open；指出shell全局URL正则不能表达每window不同URL白名单 | `R/4/answer.md:10-31,33-74`，不以扩权掩饰产品限制 |

### 下一次开始重写需要什么

**本轮不追加无止境知识题，也不以措辞、风格或中间草稿失败强造差异。**
来源门通过只表示“有可构建素材”，不表示“应发布技能”。下一次真正进入Phase C需要：

1. 在冻结范围内出现一项真实工程任务，当前完整baseline最终交付仍违反可观察契约；
   保存最小夹具、真实约束与失败产物，注明具体损失（状态/资源、soundness、API或兼容性）。
2. 用相同provider/model/thinking、相同runner条件运行该场景，逐项记录失败；
   工具/网络缺失不能自动算作Rust知识缺口。
3. 仅针对该缺口编写最少正文/reference，再用相同场景跑with-skill；
   至少一项baseline失败→with-skill达成，保留负例与原有通过场景防退化，才有增益证据。

后续具备真实新缺口时的命令（现在不执行；输出换新目录，保留本轮证据）：

```bash
uv run tools/new_skill.py rust --category framework
cp -R research/evals/rust/. skills/rust/evals/
uv run tools/run_evals.py rust --baseline \
  --model openai/gpt-5.6-sol --thinking medium \
  --out /tmp/hs-rust-next-baseline
# 只有实测缺口已经支持Phase C重写之后：
uv run tools/run_evals.py rust \
  --model openai/gpt-5.6-sol --thinking medium \
  --out /tmp/hs-rust-next-with-skill
```

最终结论：14/14 baseline预期达成；当前技能增益未证实，
**停在Phase B，保留本轮调研、夹具与运行结果，禁止将Scope骨架作为正式技能发布。**

## 当前交付状态与限制

- Phase A：14原文、8仓元数据/HEAD、前列深审与官方抽查已完成。真实门槛通过依赖3个可merged技能，其中2个同仓；不是3个独立Rust专家。
- Phase B：调研、冻结范围、3正例+1负例及夹具已完成；Main实跑baseline，逐条审阅已有events和最终产物后14/14达成。临时Scope/SOURCES骨架已移出安装目录，原始故障夹具保留在 `research/evals/rust/`，没有复制baseline修复或伪造merged。
- Phase C/D/E：未执行，没有正式规则或reference正文、NOTICE、with-skill或安装冒烟。Main的baseline在隔离workspace中实际运行了Cargo/rustc及测试，场景3还安装1.74；这不是本代理重跑校验。本代理只更新research，不复制baseline修复回原始错误夹具，不修改共享文件、生成物或提交。
- 许可：full-stack Apache-2.0由API及LICENSE原文双重确认；Apollo、leonardomso、GitHub为API MIT；Beagle API Apache-2.0；pgdog API AGPL-3.0仅reference；ytakano和actionbook树无LICENSE，README已检查，NONE且本轮不合入。
- 上游README中的专家身份、背景代理能力、工具来源均不作为事实继承。来源候选与冻结范围不变；下一步不是无条件写正文，而是等待真实任务产生本轮尚未证实的最终行为缺口，按上节命令与证据门再启动。

本次交付为构建准备，不是新skill发布。恢复命令见上节；`new_skill.py`会保留已有调研记录。找到真实缺口后才重写正文、登记实际来源、执行有skill对照与安装/静态检查。当前安装目录与生成目录表不增加Rust。
