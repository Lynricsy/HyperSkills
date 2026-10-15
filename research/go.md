# go 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `gh search repos`：`"golang skills"`、`"go agent skills"`、`"go-skills"`、`"golang agent skill"`
  - `web_search` / <https://www.skills.sh> / VoltAgent 目录（`categories/02-language-specialists/golang-pro.md`）
  - `github/awesome-copilot` 的 `skills/` 与 `instructions/` 两棵树（`gh api .../git/trees/main?recursive=1`）
  - 领域官方来源：go.dev 文档站、Go Wiki（`golang/wiki` 镜像）、uber-go/guide
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 正常，账号 Lynricsy，全程登录态，未触发限流）
- 事实核对用的本机工具链：`go1.26.6 linux/amd64`（当前 Go 稳定版为 1.27.1，2026-08-19 发布；
  1.26 与 1.27 均在支持期内）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | samber/cc-skills-golang `skills/golang-*`（46 个目录） | https://github.com/samber/cc-skills-golang | 3223 | 2026-09-07 | MIT | 语言、并发、context、错误、测试、基准、lint、性能、布局、依赖、安全、排错 | 2 | 3 | 3 | 2 | 2 | 12 | INCLUDE（主干） | 覆盖面最全、规则最可执行；扣正确分是因为「slice/map 必须显式初始化，绝不为 nil」与官方 Code Review Comments 的 `var t []string` 相反 |
| 2 | spf13/go-skills `go/` | https://github.com/spf13/go-skills | 641 | 2026-07-10 | null → NONE | 惯用法、包组织、接口、并发、错误、测试、stdlib 现代 API、net/http、slog | 3 | 2 | 3 | 3 | 0 | 11 | INCLUDE（权威裁决源） | 作者是前 Go team lead、Cobra/Viper/Hugo 作者；775 行全是「LLM 常写错的现代 Go」，抽查 stdlib/HTTP/测试三条全对；无 LICENSE 文件 → `license: NONE` |
| 3 | github/awesome-copilot `instructions/go.instructions.md` | https://github.com/github/awesome-copilot | 38858 | 2026-09-10 | MIT | 通用惯用法清单、按 `go.mod` 版本分支的建议、HTTP client 无状态化 | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE（补充） | GitHub 官方仓库、事实正确，但多为「小、清晰、惯用」这类模型已知常识；只取「按 `go` 指令版本分支给建议」与 HTTP client 不缓存 `*http.Request` 两点 |
| 4 | cxuu/golang-skills `skills/go-*`（20 个目录） | https://github.com/cxuu/golang-skills | 158 | 2026-06-20 | Apache-2.0 | 从 Google/Uber 风格指南蒸馏的并发、接口、错误、defensive、性能 | 1 | 2 | 3 | 3 | 2 | 11 | INCLUDE | goroutine 生命周期、sync 原语选择两节写得比 samber 更贴近官方措辞；`init()` 里不起 goroutine、同步范围最小化两条本仓采纳 |
| 5 | ashwingopalsamy/golangskills.com `skills/go-language-engineering` 等 | https://github.com/ashwingopalsamy/golangskills.com | 0 | 2026-08-29 | Apache-2.0 | 语言语义、测试与验证、性能诊断、项目与 API 设计 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE（结构） | 写法是「先确定本地契约再改」的判据式散文，代码极少；采纳其「按不变量选表示（值/指针/nil vs 空）」与「在一个所有者边界处理错误」的组织方式，不采纳其散文 |
| 6 | douglassantosreis/golang-profiling-analyzer `references/` | https://github.com/douglassantosreis/golang-profiling-analyzer | 0 | 2026-09-07 | MIT | pprof/trace/goroutine dump 的判读流程 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE（reference） | flat% vs cum%、`runtime.mallocgc` 是症状不是病因等判读法有价值；按波次计划定为 `relation: reference`，本仓 pprof 事实一律从 go.dev/doc/diagnostics 与 `go tool pprof` 自身文档重新取证 |
| 7 | go.dev `Effective Go` | https://go.dev/doc/effective_go | — | 官方持续维护 | 官方文档 | 语言惯用法、零值、接口、并发、错误 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（docs） | 冲突裁决的第一顺位依据 |
| 8 | Go Wiki `Code Review Comments` | https://go.dev/wiki/CodeReviewComments | — | 官方持续维护 | 官方文档 | 空 slice 声明、context、错误字符串、goroutine 生命周期、in-band errors、接收者选择 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（docs） | 直接推翻了 samber 的 nil-slice 规则；本 skill 多条 Core rule 的出处 |
| 9 | Go Wiki `Test Comments` | https://go.dev/wiki/TestComments | — | 官方持续维护 | 官方文档 | 测试失败信息格式、表驱动、`t.Helper` | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（docs） | `got/want` 失败信息格式与「测试不要断言实现细节」的官方措辞 |
| 10 | go.dev `Diagnostics` | https://go.dev/doc/diagnostics | — | 官方持续维护 | 官方文档 | profiling / tracing / race detector / debugging 的官方分类 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（docs） | pprof 与 trace 一节的取证来源 |
| 11 | go.dev 发行说明 1.22–1.27 | https://go.dev/doc/devel/release | — | 2026-08-19（1.27.0） | 官方文档 | 版本门槛：per-iteration loop var、`b.Loop`、`synctest`、`WaitGroup.Go`、`errors.AsType`、`goroutineleak` profile | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（docs） | 所有 `(Go 1.x+)` 标注的出处 |
| 12 | uber-go/guide | https://github.com/uber-go/guide | 17700 | 2026-04-15 | Apache-2.0 | Uber Go 风格指南 | 2 | 1 | 3 | 3 | 2 | 11 | INCLUDE（reference） | 不是 agent skill；用于交叉校验 cxuu 的蒸馏是否失真（抽查 goroutine 生命周期、`init()` 限制、mutable global 三条一致），正文不复制 |
| 13 | eduardo-sl/go-agent-skills `skills/(...)/go-*`（30+ 目录） | https://github.com/eduardo-sl/go-agent-skills | 71 | 2026-08-18 | MIT | 评审清单、架构、代码质量 | 1 | 3 | 2 | 2 | 2 | 10 | MAYBE → 不合入 | 内容与 samber 高度重叠且更浅；评审流程部分与本仓 `code-review` skill 撞车（本 skill 明确转交）。留行以免下批次重复评估 |
| 14 | wshobson/agents `plugins/systems-programming/agents/golang-pro.md` | https://github.com/wshobson/agents | 39554 | 2026-09-07 | MIT | subagent persona | 1 | 3 | 0 | 1 | 2 | 7 | REJECT | 是 subagent 人设文件而非 skill：整篇是「掌握 X、精通 Y」的能力清单，没有一条可执行规则；「Go 1.21+」的框架也已过时 |
| 15 | VoltAgent/awesome-claude-code-subagents `categories/02-language-specialists/golang-pro.md` | https://github.com/VoltAgent/awesome-claude-code-subagents | 24987 | 2026-09-07 | MIT | subagent persona | 1 | 3 | 0 | 1 | 2 | 7 | REJECT | 同上；另含 `tools:`/`model:` 等 agent 专属字段 |
| 16 | h0rn3t/golang-skills | https://github.com/h0rn3t/golang-skills | 3 | 2026-09-10 | Apache-2.0 | — | 0 | 3 | 3 | 3 | 2 | 11 | REJECT | 是 cxuu/golang-skills 的逐字 fork（描述、目录、内容一致），合入它等于重复计数上游 |
| 17 | giuseppe-trisciuoglio/developer-kit | https://github.com/giuseppe-trisciuoglio/developer-kit | 343 | 2026-09-10 | MIT | Java/TS/Python/PHP/AWS | 1 | 3 | 2 | 2 | 2 | 10 | REJECT | 1286 个文件里没有任何 Go 主题目录，与本 skill 无交集 |
| 18 | smallnest/chao-go-sync | https://github.com/smallnest/chao-go-sync | 44 | 2026-05-25 | MIT | 《深入理解 Go 并发编程》配套代码 | 2 | 2 | 3 | 3 | 2 | 12 | REJECT | 是书籍示例代码仓，不是 skill 也不是规范文本；可执行规则需自己从代码反推，不如直接用官方文档 |
| 19 | Raccoon-AI/claude-golang | https://github.com/Raccoon-AI/claude-golang | 1 | 2026-08-14 | null → NONE | 通用 Go 指令 | 0 | 3 | 1 | 2 | 0 | 6 | REJECT | 1 星、无许可、内容是泛化的 "write idiomatic Go" 指令 |
| 20 | thealish/golang-skill | https://github.com/thealish/golang-skill | 3 | 2026-02-25 | null → NONE | 单文件 SKILL.md | 0 | 2 | 1 | 2 | 0 | 5 | REJECT | 单文件、无许可、已 6 个月余未更新，内容被 samber 完全覆盖 |
| 21 | clawvpsai/gin-skill | https://github.com/clawvpsai/gin-skill | 6 | 2026-07-18 | null → NONE | Gin Web 框架 | 0 | 2 | 2 | 2 | 0 | 6 | REJECT | 单一 Web 框架说明书，属产品包装；本 skill 的边界是语言与工具链，不收框架 |
| 22 | getsentry/skills | https://github.com/getsentry/skills | 989 | 2026-09-07 | Apache-2.0 | — | 3 | 3 | — | — | 2 | — | REJECT | 203 个文件中检索不到任何 Go 语言主题目录（`languages/` 树下无 go），无可取内容 |

## 深度审查

### 1. samber/cc-skills-golang（主干）

46 个 `skills/golang-*` 目录，每个都带 `SKILL.md` + `references/` + 自己的 `evals/evals.json`，
是本次候选里唯一做到「规则 + 反例 + 验证命令」三件套的仓库。

- **结构**：`Best Practices Summary` 编号清单 → 分主题小节 → `Common Mistakes` 表 → `Cross-References`。
  `Common Mistakes` 表（「错误 → 修法」两列）信息密度最高，本 skill 的 Core rules 大量对应到它。
- **frontmatter**：含 `user-invocable`、`allowed-tools`、`paths`、`metadata.openclaw.*`、
  `metadata.version`、`compatibility` 等大量 agent/harness 专属字段，按标准 §1.2 **全部剥离**。
- **agent 绑定**：正文开头一律有 `**Persona:**`、`**Thinking mode:** ... use \`ultrathink\``、
  `**Orchestration mode:** ... use \`ultracode\``、`> **Community default.**` 四段，以及
  `→ See \`samber/cc-skills-golang@golang-xxx\` skill` 形式的跨 skill 引用。这些是 Claude Code
  专属注入与上游自引用，全部删除（标准 §1.3）。
- **自家库目录必须剔除**：`golang-samber-do`、`golang-samber-hot`、`golang-samber-lo`、
  `golang-samber-mo`、`golang-samber-oops`、`golang-samber-ro`、`golang-samber-slog` 七个目录，
  以及 `golang-spf13-cobra`、`golang-spf13-viper`、`golang-stretchr-testify`、`golang-uber-dig`、
  `golang-uber-fx`、`golang-google-wire`、`golang-swagger`、`golang-graphql`、`golang-grpc`、
  `golang-database`、`golang-popular-libraries`、`golang-pkg-go-dev` 等，都是**单个第三方库的说明书**，
  属产品包装而非通用语言能力；`golang-cli`、`golang-continuous-integration`、`golang-observability`、
  `golang-dependency-injection`、`golang-design-patterns` 越出本 skill 的语言/工具链边界。
  最终只取 15 个通用目录（见「最终合入清单」）。
- **质量瑕疵**：满篇 `MUST`/`SHOULD`/`NEVER` 大写祈使（标准 §3 禁止照抄这种语气）；
  `golang-project-layout` 的核心动作是「先问用户要什么架构」，对 agent 是推诿而不是知识。

### 2. spf13/go-skills（权威裁决源）

单文件 775 行，没有 references。作者是前 Go team lead。它与其它候选的根本差别是**选题**：
整篇针对「LLM 会写出什么过时 Go」——`sort.Slice` 而非 `slices.Sort`、`math/rand` 而非 `math/rand/v2`、
`// +build`、`interface{}`、`tools.go`、`gorilla/mux`、`http.ListenAndServe` 不设超时、
`url := url` 循环变量拷贝、`time.Sleep` 当同步。这正是标准 §3「teach the failure, not the API」。

- **frontmatter**：只有 `name` + `description`，无 agent 专属字段，最干净。
- **许可**：仓库根无 LICENSE 文件，API `license: null`。按规则记 `license: NONE` 并写 notes；
  正文不复制任何句子，只取事实与裁决。
- **抽查三条**（对照官方）：`b.Loop()`（`go doc testing.B.Loop` 本机确认）、
  `synctest.Test`（`go doc testing/synctest` 本机确认）、
  Go 1.22 起 `net/http.ServeMux` 支持方法与路径参数（go1.22 发行说明确认）——全对。
- **末节「Go 工具链不是 bug 源」**很有价值：明确禁止在排错时怀疑 `go build` 缓存，
  给出四条按概率排序的真实原因。本 skill 的 tooling 一节采纳这条。

### 3. cxuu/golang-skills

20 个 `skills/go-*`，自述蒸馏自 Google Go Style Guide 与 Uber Go Style Guide。
`go-concurrency` 的 `Goroutine Lifetimes` 一节几乎复述 Go Wiki 的原文并加了三条可执行细则
（能等待、`init()` 里不起 goroutine、同步范围限制在函数内）。frontmatter 干净
（只有 `name` + `description`）。缺点是有 `references/GOROUTINE-PATTERNS.md` 这类全大写文件名，
以及「Atomic 示例可能用 `go.uber.org/atomic`」这种含糊的兼容性声明。

### 4. ashwingopalsamy/golangskills.com

单人仓库、0 星，但组织方式独特：三套 collection（engineering / distributed-systems / fintech），
每个 skill 只有 40–60 行，全是判据式散文，几乎没有代码。`go-language-engineering` 的
「先确定本地契约（输入、零值行为、别名、可变性、错误身份、并发暴露、导出兼容性）再动手」
是本 skill `## Workflows` 里 `implement` 第一步的来源。其 `distributed-systems-*` 与
`fintech-*` 两套整体越界（消息投递语义、对账、清算），不取。

### 5. github/awesome-copilot `instructions/go.instructions.md`

373 行，GitHub 官方仓库，事实正确但绝大部分是模型已知常识（「接口要小」「happy path 左对齐」）。
另有一整段教 agent 「不要在文件里写两个 package 声明」——这是给弱模型的保姆式提示，本仓不收。
唯一值得合入的两点：**按 `go.mod` 的 `go` 指令版本分支给建议**（`>= 1.25` 用 `WaitGroup.Go`，
`>= 1.22` 用增强 `ServeMux`）这一写法，以及 HTTP client 结构体不得缓存 `*http.Request` 的规则。

### 6. douglassantosreis/golang-profiling-analyzer

四个 reference：pprof 判读、goroutine 模式、静态分析清单、Docker 内 profiling。
`pprof-analysis-guide.md` 讲清了 flat% 与 cum% 的读法，以及
「`runtime.mallocgc` / `runtime.growslice` / `runtime.mapassign` 出现在 `top` 顶部是症状不是病因」。
按波次计划定为 `relation: reference`：判读**流程**参考它，每条**事实**改从 go.dev/doc/diagnostics
与 `go tool pprof` 的官方文档取证后自己写。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 空 slice / map 的声明 | samber `golang-code-style`：「slice 与 map MUST 显式初始化，绝不为 nil」；Go Wiki：优先 `var t []string`，仅在 JSON 序列化需要 `[]` 而非 `null` 时才用非 nil 空 slice | 采用官方：默认 `var t []T`；只有当零值会经 JSON 暴露成 `null`、或写入 map 时才显式 `make` | 官方文档 > 社区；`https://go.dev/wiki/CodeReviewComments#declaring-empty-slices` 明确「nil slice 是首选风格」 |
| 2 | 项目布局 | samber `golang-project-layout`：先问用户选 clean/hexagonal/DDD，给 `cmd/ internal/ pkg/ api/ web/` 分型表；spf13：默认扁平，只按**领域**（`auth/`、`billing/`、`jobs/`）分包且只一层，明确拒绝 `service/`/`repository/`/`controller/` 分层 | 采用 spf13 | 公认专家（前 Go team lead）> 社区；且 samber 的做法是把决策推回给用户，对 agent 不可执行。`internal/` 的用途按官方 `go` 命令语义写（阻止外部模块导入），不作为默认分层手段 |
| 3 | 通道传指针还是传拷贝 | samber `golang-concurrency`：「MUST 传拷贝，传指针会造成隐形共享内存」 | 不采用这条绝对化说法。改写为：通过通道传递即**移交所有权**——发送后不得再触碰该值；传大结构体的指针没问题，前提是发送方之后不再写它 | 官方 Effective Go 的表述是「Do not communicate by sharing memory; share memory by communicating」，关注点是所有权而非拷贝；一律拷贝会让传 `*bytes.Buffer`、`*http.Request` 这类正常做法变成违规 |
| 4 | 缓冲通道 | samber：「默认无缓冲，用缓冲需要实测理由」；awesome-copilot：「知道容量时用缓冲通道」 | 采用 samber 的方向但改成可判定形式：缓冲大小要么是 0，要么等于确定的生产者/消费者数量；任何「随手 100」的缓冲是掩盖背压 | samber 更新更具体；awesome-copilot 的说法无法判定「知道容量」 |
| 5 | 并行子测试的清理 | samber/cxuu 都只说「独立测试 SHOULD 用 `t.Parallel()`」，没人提父测试的 `defer` 与并行子测试的时序 | 本仓自行验证并写成硬规则：父测试函数在并行子测试运行**之前**返回，所以父级 `defer os.RemoveAll(dir)` 会先执行；用 `t.TempDir()` 或 `t.Cleanup` | `[verified]`：本机 go1.26.6 跑最小复现，输出顺序为 `DEFER in parent` → `SUBTEST a` → `SUBTEST b` |
| 6 | goroutine 泄漏怎么发现 | samber：`go.uber.org/goleak` + `runtime.NumGoroutine()` + `/debug/pprof/goroutine`；并声称 goroutine leak profile 在 1.26 是 `GOEXPERIMENT`、1.27 起 GA | 两者都写：测试里用 `goleak`，生产上 Go 1.27+ 直接用 `goroutineleak` profile。samber 的版本说法经核实**正确** | go1.27 发行说明「Goroutine leak profile … now generally available … `/debug/pprof/goroutineleak`」 |
| 7 | 测试文件命名 | samber：测试文件 MUST 按**源文件**命名，且测试函数顺序 SHOULD 与源文件一致 | 只保留前半条（`foo.go` → `foo_test.go`），删掉「函数顺序必须一致」 | 官方无此要求，且它把每次源文件重排都变成测试文件重排；标准 §3「每段都要值它的 token」 |
| 8 | 加不加 testify | samber：testify 作为 helper，配 `assert.New(t)` 作用域陷阱一节；spf13：拒绝重型断言/mock 框架，用手写 fake + `go-cmp` | 默认按 spf13（stdlib + `go-cmp`），逃生口是「仓库已经在用 testify 时跟随，并且每个子测试自建 `assert.New(t)`」 | 公认专家 > 社区；同时保留 samber 那条真实陷阱（父级 `assert.New(t)` 会把子测试失败记到父测试上） |
| 9 | 错误检查 API | samber：Go 1.26+ 优先 `errors.AsType[T](err)`，更早版本用 `errors.As(err, &target)` | 采用，并标注 `(Go 1.26+)` | `[verified]`：本机 go1.26.6 编译运行 `errors.AsType[E](err)` 通过 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `samber-golang` | samber/cc-skills-golang（15 个通用 `skills/golang-*` 目录） | merged | 主干覆盖面：并发原语选择表、goroutine 检查清单、错误处理的「单一处理原则」、表驱动/并行/fuzz/goleak/synctest 的测试矩阵、`golangci-lint` 工作流、依赖与 `govulncheck`、pprof/benchstat 的度量纪律、以及各主题的 Common Mistakes 表 |
| `spf13-go` | spf13/go-skills `go/` | merged | 现代 stdlib 清单（`slices`/`maps`/`cmp`/`iter`/`math/rand/v2`/`omitzero`/typed atomics/`tool` 指令）、领域分包布局、`net/http` 超时与优雅关停、中间件即函数、generics 的用与不用、「工具链不是 bug 源」的排错纪律 |
| `cxuu-golang` | cxuu/golang-skills（`go-concurrency`、`go-interfaces`、`go-error-handling`、`go-performance`、`go-defensive`） | merged | goroutine 生命周期三条细则（能等待、`init()` 里不起 goroutine、同步范围限定在函数内）、sync 原语选型的官方措辞 |
| `ashwin-go` | ashwingopalsamy/golangskills.com（`go-language-engineering`、`go-testing-and-verification`、`go-performance-and-diagnostics`、`go-project-and-api-design`） | merged | implement 工作流的第一步「先确定本地契约」，以及「按不变量选值/指针、nil vs 空只在序列化区分时才保留」的判据 |
| `awesome-copilot-go` | github/awesome-copilot `instructions/go.instructions.md` | merged | 按 `go.mod` 的 `go` 指令版本分支给建议这一写法；HTTP client 结构体不缓存 `*http.Request` |
| `go-effective-go` | go.dev/doc/effective_go | merged (docs) | 零值可用、接口即行为、「share memory by communicating」的准确表述 |
| `go-wiki-codereview` | go.dev/wiki/CodeReviewComments | merged (docs) | 空 slice 声明、context 传递规则、错误字符串格式、in-band errors、接收者一致性、goroutine 生命周期 |
| `go-wiki-testcomments` | go.dev/wiki/TestComments | merged (docs) | `got/want` 失败信息格式、断言可观察行为 |
| `go-doc-diagnostics` | go.dev/doc/diagnostics | merged (docs) | profiling / tracing / race detector 的官方分类与采集方式 |
| `go-release-notes` | go.dev/doc/devel/release（1.22–1.27） | merged (docs) | 所有 `(Go 1.x+)` 版本门槛标注 |
| `douglas-pprof` | douglassantosreis/golang-profiling-analyzer | reference | pprof 判读流程（flat% vs cum%、`runtime.mallocgc` 是症状）的对齐参考；事实全部改从官方文档取证，未复制文字 |
| `uber-go-guide` | uber-go/guide | reference | 交叉校验 cxuu 的蒸馏是否失真；正文未复制 |

## 基线缺口

无 skill（`uv run tools/run_evals.py go --baseline`，claude-opus-5 / medium）时，各场景未达成的
`expected_behavior`：

> 第一版评测的场景 1、2 基线 5/5 全达成，没有区分度。按 `docs/workflow.md` Phase B 的要求改写：
> 场景 1 把「等价的有界并发结构」收紧为「必须点名 `errgroup.WithContext` + `SetLimit`」并新增
> `wg.Go` 与「泄漏的回归防线」两条；场景 2 的夹具增加 `*ValidationError` 与包装后的裸类型断言，
> 并新增 `errors.Join` 一条。下表是改写后重跑的基线。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 fetcher.go | 用 `errgroup.WithContext` + `g.SetLimit(workers)` 替换手写 worker pool | 基线自己又手写了一遍 `jobs chan int` + `WaitGroup` 池；结构正确但没想到标准答案，整段样板代码本可省掉 |
| 1 fetcher.go | 保留 `WaitGroup` 时用 `wg.Go(func(){...})`（Go 1.25+） | 基线写的是 `wg.Add(workers)` + `defer wg.Done()`，是 1.24 及以前的写法 |
| 1 fetcher.go | 给泄漏留一条长期回归防线（`goleak` 或 `goroutineleak` profile） | 基线写了一次性冒烟脚本并在答复里声明「验证完删掉了」，没有任何东西能防止泄漏重新出现 |
| 2 store.go | `validate` 只报第一个坏字段 → 用 `errors.Join` 一次报全 | 完全未提及；九条修复清单里没有这一项 |
| 2 store.go | 裸类型断言改用 `errors.AsType[*ValidationError](err)`（Go 1.26+） | 部分达成：基线正确识别了「`%w` 包装后 `err.(*ValidationError)` 是死分支」并换成 `errors.As`，但不知道 1.26 起有泛型形式，也没有按 `go` 指令分档 |
| 3 cache_test.go | 用 `testing/synctest` 取代 `time.Sleep` | 基线改成了「长 TTL 断言未过期 + 短 TTL 轮询 + 2s deadline 兜底」，并明说「没上时钟注入」——仍是墙钟测试，只是把 flaky 换成了慢 |
| 3 cache_test.go | benchmark 改写为 `for b.Loop()`（Go 1.24+） | 基线给的是 `b.ResetTimer()`，即 1.23 及以前的写法 |

基线全部达成的行为（skill 不需要重新教）：数据竞争与 `go test -race`、未 `close` 的通道导致收集
goroutine 泄漏、`time.Sleep` 当同步、`http.DefaultClient` 无超时、`for range workers`、
`errors.Is` 取代 `==`、`%w` 取代 `%v`、log-and-return 双重处理、被丢弃的 `Exec` 错误、
错误串大小写、并行子测试与父级 `defer` 的时序、`t.Errorf("bad")` 无诊断信息。

## 评测结果

人工判定，逐条读 `/tmp/hs-evals/go/anthropic-claude-opus-5-medium/{baseline,skill}/<n>/answer.md`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 fetcher.go 并发审查 | claude-opus-5:medium | 无（baseline） | false | 3/6：数据竞争 + `-race`、未 close 通道导致泄漏 + `time.Sleep` 当同步、`DefaultClient` 无超时 | 未达成：点名 `errgroup.WithContext`+`SetLimit`、`wg.Go`、泄漏的长期回归防线。自己手写了 `jobs chan int` + `wg.Add/Done` 池，冒烟脚本用完即删 |
| 1 fetcher.go 并发审查 | claude-opus-5:medium | 有 | true | 4/6：前 3 条同上 + **写出 `fetcher_test.go` 并用 `goleak.VerifyTestMain` 作为泄漏的回归防线**（基线缺口填补） | 未达成：仍未点名 `errgroup`，且这一轮退回 `wg.Add/Done`。同配置的上一轮（加 `review` 工作流之前）反过来：用了 `wg.Go`、点名了 `errgroup` 作为等价写法，但没留回归防线。两轮合起来 6 条全被覆盖过，单轮稳定性不足 |
| 2 store.go 错误处理 | claude-opus-5:medium | 无（baseline） | false | 5/7：`errors.Is`、`%w`、log-and-return、被吞的 `Exec` 错误 + `u.Name` 死赋值、错误串大小写；裸类型断言只做到 `errors.As` | 未达成：`errors.Join`（完全未提）、`errors.AsType`（不知道 1.26 起的泛型形式） |
| 2 store.go 错误处理 | claude-opus-5:medium | 有 | true | 7/7：**`errors.AsType[*ValidationError]`** 与 **`errors.Join` 累积全部校验失败**（两条基线缺口填补），其余同基线 | 两条缺口都填补 |
| 3 cache_test.go 修 flaky | claude-opus-5:medium | 无（baseline） | false | 3/5：父级 `defer` 与并行子测试的时序、共享实例 + `-race`、`t.Errorf("bad")` 无诊断 | 未达成：`testing/synctest`（改成了 2s deadline 轮询，明说「没上时钟注入」）、`for b.Loop()`（给的是 `b.ResetTimer`） |
| 3 cache_test.go 修 flaky | claude-opus-5:medium | 有 | true | 5/5：**`synctest.Test` + 假时钟 + `synctest.Wait()`** 与 **`for b.Loop()`**（两条基线缺口填补），并主动标注 `synctest` 需要 `go` 指令 ≥ 1.25 | 两条缺口都填补；额外补了「到期前应能读到」的对照断言 |
| 4 Python 并发抓取（负例） | claude-opus-5:medium | 无（baseline） | false | 2/2 | — |
| 4 Python 并发抓取（负例） | claude-opus-5:medium | 有 | **false** | 2/2：未加载 go skill，答复只讲 asyncio / ThreadPoolExecutor，无一行 Go | 负例通过 |

结论：**通过**。七条基线未达成的行为里，有 skill 时填补了五条——`errors.Join`、
`errors.AsType[T]`（Go 1.26+）、`testing/synctest`、`for b.Loop()`（Go 1.24+）、
以及给泄漏留 `goleak` 回归防线。剩下两条（点名 `errgroup`、`wg.Go`）在两轮有-skill 运行中
各命中过一次但不稳定。负例 `skill_read == false`。

## 备注

### 评测迭代

第一版评测的场景 1、2 基线 5/5 全达成（Opus 5 对「有夹具的 Go 代码审查」本身就很强），
按 `docs/workflow.md` Phase B「基线全部达成即改写评测」重写后才出现缺口。改写方向是把
「等价即可」的宽松判据换成**版本门槛型知识**（`wg.Go` / `errors.AsType` / `synctest` /
`b.Loop`）与**长期护栏型判据**（回归防线），这正是模型自身知识与 skill 的真实差值所在。

场景 1 第一轮有-skill 跑完后发现：SKILL.md 有 `## Output format` 讲评审报告格式，
却没有对应的 `review` 工作流，而场景 1 恰是评审任务。补上 `### review` 工作流（含
「每条泄漏/竞态都要点名回归防线」一步）后重跑，模型确实写出了带 `goleak.VerifyTestMain`
的回归测试。这是评测直接驱动 skill 结构修改的一例。

### 许可与上游处理

- **samber 自家库目录一律剔除**：`golang-samber-{do,hot,lo,mo,oops,ro,slog}` 是作者自己
  七个库的说明书，`golang-{spf13-cobra,spf13-viper,stretchr-testify,uber-dig,uber-fx,
  google-wire,swagger,graphql,grpc,database,popular-libraries,pkg-go-dev}` 是单个第三方
  库的用法。它们是产品包装而非通用语言能力，一旦合入，skill 就会变成「用哪个库」的推荐清单，
  与「怎么写对 Go」无关。`SOURCES.yaml` 的 `paths` 只列实际读过的 16 个通用目录。
- **spf13/go-skills 无 LICENSE 文件**（`gh api` 返回 `license: null`），按仓库规则记
  `license: NONE`，`notes` 写规定原文
  「No licence file; used under the repository's permissive-attribution policy, no text
  copied verbatim」。它是本 skill 权重最高的裁决源（项目布局、测试库选择、现代 stdlib），
  正文一句未抄，全部按事实重写并对照 go.dev 复核。
- **`douglas-pprof` 与 `uber-go-guide` 为 `relation: reference`**：前者按波次计划定为
  reference（pprof 判读流程参考，事实改从 go.dev/doc/diagnostics 取证），后者不是 agent
  skill、仅用于交叉校验 cxuu 的蒸馏是否失真。两者均未复制文字。
- 无 GPL/AGPL/LGPL/专有上游进入本 skill，因此没有 reference-only 的许可强制项。

### 本机核实的事实

在 go1.26.6 上实跑确认，未凭记忆下笔：

| 事实 | 命令 | 结果 |
|---|---|---|
| 父测试 `defer` 早于并行子测试执行 | `go test -v` 最小复现 | `DEFER in parent` → `SUBTEST a` → `SUBTEST b` |
| `errors.AsType[T]` 存在 | 编译运行 `errors.AsType[E](err)` | `e true` |
| `b.Loop`、`t.Context`、`t.Chdir`、`t.Output`、`t.Attr` | `go doc testing.*` | 全部存在 |
| `testing/synctest.Test`、`sync.WaitGroup.Go` | `go doc` | 全部存在 |
| `slices.Clip/All/Sorted/Collect`、`maps.All`、`sync.OnceValue`、`context.AfterFunc/WithoutCancel`、`crypto/rand.Text`、`math/rand/v2.N`、`iter.Seq` | `go doc` | 全部存在 |
| `GOMAXPROCS` 感知 cgroup 配额 | `go doc runtime.GOMAXPROCS` | 「`GODEBUG=containermaxprocs=0` is default for language version 1.24 and below」→ 1.25 起默认开启 |
| `runtime/pprof` 内置 profile 列表（1.26） | 运行 `pprof.Profiles()` | `allocs block goroutine heap mutex threadcreate`，无 `goroutineleak` |
| `goroutineleak` profile 1.27 起 GA | go1.27 发行说明 | 「now generally available … `/debug/pprof/goroutineleak`」 |
| Go 当前稳定版 | go.dev/doc/devel/release | 1.27.1（1.27.0 于 2026-08-19 发布）；1.26 与 1.27 在支持期 |
| golangci-lint v2 合并 `gosimple`/`stylecheck` 进 `staticcheck`、formatters 独立分节 | golangci-lint.run 迁移指南 | 确认；另有 `golangci-lint migrate` 命令 |
| golangci-lint v2 模块路径 | `gh api .../contents/go.mod` | `github.com/golangci/golangci-lint/v2` |

### 未做与后续

- **没有写 `scripts/`**：这个 skill 的每一个动作都是一条现成的 `go` 子命令
  （`go vet`、`go test -race`、`go tool pprof`、`go tool benchstat`、`govulncheck`），
  再包一层脚本只会在参数上撒谎。
- **`net/http` 服务端一节的归属**：写进了 `references/stdlib-modern-apis.md` 而不是单独
  reference。它是标准库用法（超时、优雅关停、中间件即函数、1.22 起的 `ServeMux` 路由），
  不是 Web 框架内容，与边界一致。
- **下次同步要盯的上游**：`samber/cc-skills-golang` 更新频繁（每周），且有
  `update-library-skill` / `update-modernize-skill` 两个自动化 workflow；
  `github/awesome-copilot` 每天都动，`paths` 已收窄到 `instructions/go.instructions.md`
  一个文件以滤掉噪声。
- **`cxuu/golang-skills` 有一个逐字 fork**（`h0rn3t/golang-skills`，3★，推送更新）。
  下次复核时不要把它当成第二个独立上游。

## 2026-09-30 上游同步

依据：`/tmp/upstream-report-0930.txt`（2026-09-30 `check_upstream.py`）中本 skill 有 1 条 `behind`（`awesome-copilot-go`，
`diff too large`）。按完整区间归因：blobless 克隆到 `/tmp/hs-up/github__awesome-copilot`，对 `7568a48..15ed97c`
跑 `git log --oneline -- instructions/go.instructions.md` 与 `git diff --stat`，并用 `git rev-parse <commit>:<path>`
比对两端 blob。`--pin` 后核对：写入的 commit 与审阅 HEAD 一致（awesome-copilot 15ed97c；repo moved、tracked paths
unchanged 的 spf13-go 前移到 9ac6eca、ashwin-go 前移到 d071a92）。五条 go.dev docs 为 manual check，本次未处理。

| 上游 | 区间 | 命中提交/文件 | 判定 | 理由 |
|---|---|---|---|---|
| awesome-copilot-go | 7568a48 → 15ed97c（64 提交，329 文件） | `instructions/go.instructions.md` 0 提交，两端 blob 同为 `83a24b7` | 噪声 | 区间改动全在其他目录；too-large 只是 compare 上限 |

未合入原因：无可合入内容，正文与 references 未改，未新增评测场景、未跑评测，也不需要安装冒烟。

## 2026-10-15 上游同步

依据 2026-10-15 `tools/check_upstream.py` 报告：`awesome-copilot-go`（138 commits）一条 `behind`，为 diff too large to attribute to paths。主代理已在 shallow blobless 裸仓库缓存（`/tmp/hs-attr/github__awesome-copilot`）上按完整 `<旧pin>..<审阅HEAD>` 区间、限该条目 `paths` 归因为空；本次复跑 `git log --oneline <pinned>..<head> -- <paths>` 仍为空，并用不依赖提交历史完整性的树对比 `git diff --stat <pinned> <head> -- <paths>` 与两端 `git ls-tree` 复核（结果为空、所有追踪路径在两端均存在），未用日期过滤。

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| awesome-copilot-go | 15ed97c → 3cf7c7e（138 commits，全仓 827 个文件变更） | 无：`instructions/go.instructions.md` 区间内无提交、树对比为空 | 未变更，仅 re-pin |

其余仓库上游（`samber-golang`（19a0626 → 8e899e2，1 commits）为 `repo moved, tracked paths unchanged`；`spf13-go`、`cxuu-golang`、`ashwin-go`、`douglas-pprof`、`uber-go-guide` 为 up to date）随 `--pin` 一并对齐；pin 写入的 commit 与审阅 HEAD 逐条一致（8e899e2、9ac6eca、91f0c2e、d071a92、3cf7c7e、45573dd、1d60a91），`pin_check.py` 结果 PIN CHECK CLEAN。5 条 `kind: docs` 条目为 manual check，本次未改。

结论：behind 条目在追踪 paths 下均无上游提交，正文未变，未新增评测场景、未跑评测；仅 re-pin 并把版本号改为 2026.10.15。

## 2026-10-15 上游新增内容评估

依据：主代理的上游新增文件评估（NewS4 F：leeovery/agentic-skills `go/skills/go-testing`、`go-concurrency` MERGE，`go-types` 的 json/v2 一条 MAYBE）。原文用已登录 `gh api` 按审阅 HEAD `88b5924` 读取（MIT，仓库根 LICENSE）。leeovery 此前只被 laravel 追踪，本 skill 新增 upstream 条目 `leeovery-go`（paths 只含 go-testing、go-concurrency）。事实全部对照本机 go1.27.1 的 `go doc` 与实跑核实（VM 内 Go 1.27.2）。

### 候选与裁决

| 候选 | 结论 | 理由 |
|---|---|---|
| 事实更正：`concurrency.md` 写 `time.After` 每次迭代分配的 timer「活到触发为止」 | **更正** | Go 1.23 起（模块 `go` 行 ≥1.23）未引用、未 Stop 的 Timer/Ticker 立即可回收；剩下的理由只是热循环里每次分配。正文改写该段，Common mistakes 一行改为「hot loop」并注明 1.23 以下才是泄漏 |
| synctest：bubble 内 `httptest.NewServer` 走真实网络、不是持久阻塞，时钟停住 → 用 `httptest.NewTestServer(t, h)`（Go 1.27+），低版本用假 `RoundTripper` | **合入**（`testing.md` synctest 节） | 场景 5 基线 EB2 ◐（解释对、改用手写 RoundTripper，不知道 NewTestServer）；有 skill 用 `NewTestServer` |
| synctest：裸 `time.Sleep` 与被测 ticker 同一假时刻醒来，计数少一 → `synctest.Sleep`（Go 1.27+）或 Sleep + Wait | **合入**（同上，标 [verified]） | 场景 5 基线已用 Sleep + Wait；本条作为上一条的同节补充写入，并经本机实跑证实（见核实）；不单独计缺口 |
| synctest 其余：持久阻塞表、bubble 内不能 `t.Run`、泄漏时 deadlock panic、时钟从 2000-01-01 起 | 不合入 | 场景 5 基线已把 `synctest.Test` 移进每行的 `t.Run` 并理解持久阻塞；先写进的 `t.Run` 一条已按此删除 |
| Shutdown 用 `context.WithTimeout(context.WithoutCancel(ctx), grace)` 代替 `Background()` | 不合入 | `stdlib-modern-apis.md` 的 `Background()` 写法本身正确（注释说明了 ctx 已取消）；保留 ctx 值属风格改进，无评测缺口 |
| go-types：json/v2 不要半个模块迁移、名字区分大小写、`time.Duration` 无默认编码、nil slice → `[]`、`omitempty` 语义变化 | 不合入 | 场景 6 基线（与有 skill）都用 v2 + `jsonv1.DefaultOptionsV1()` + 严格 UTF-8/重复键选项保住全部旧行为；事实已对照 `go doc encoding/json` 的 v1/v2 差异清单核实，可留待日后 |
| go-errors、go-interfaces、go-quality、go-architecture、go-actions | 不合入、不追踪 | 已覆盖或与本 skill 立场冲突（禁 go-cmp/testify） |

### 核实

- `go doc time.After` / `time.NewTimer`（go1.27.1）："As of Go 1.23, the garbage collector can recover unreferenced, unstopped timers"；golang/website `_content/doc/go1.23.md`「Timer changes」：仅当主模块 `go.mod` 的 `go` 行 ≥1.23.0 时启用。
- `go doc testing/synctest`：持久阻塞清单不含 mutex、I/O、系统调用；`synctest.Sleep` "exactly equivalent to time.Sleep(d); synctest.Wait()"；`synctest.Test` 文档写明 `T.Run`、`T.Parallel`、`T.Deadline` must not be called。`go doc net/http/httptest.NewTestServer`：默认用内存网络。`api/go1.27.txt` 含 `httptest.NewTestServer` 与 `synctest.Sleep`。
- 本机实跑场景 5 夹具：原文件 panic `testing: t.Run called inside synctest bubble`；把 `synctest.Test` 移进 `t.Run` 但保留 `httptest.NewServer` → 30 s 超时挂住；换 `NewTestServer` + 裸 `time.Sleep` → `-count=20` 稳定失败 `got 0 want 1` / `got 2 want 3`；再换 `synctest.Sleep` → `-count=50` 通过。
- json/v2：`go doc encoding/json`「Migrating to v2」差异清单；`go doc encoding/json.FormatDurationAsNano`；`src/encoding/json/v2/arshal_time.go` 的 `format:nano` 等取值。

### 评测结果

模型 `openai/gpt-6.1-sol` medium（run_evals 默认，VM 内 omp），产物在 `/tmp/hs-evals/go/omp-openai-gpt-6.1-sol-medium/`；逐条读 `answer.md` 与 `workspace/` 人工判定。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 5 | gpt-6.1-sol medium | 无 | False | EB1 ✔ EB2 ◐ EB3 ✔ EB4 ✔ | 87 s。行内 `t.Run` 包 `synctest.Test`；手写 `RoundTripper` 代替真实服务器并说明 socket I/O 不让时钟前进；Sleep 后 `synctest.Wait()`；`-race -count=100` 通过 |
| 5 | gpt-6.1-sol medium | 有 | True | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ | 101 s。`httptest.NewTestServer(t, …)`；Sleep 前后 `synctest.Wait()`；先取消并等待 poller 再关服务器；`-race` 100 次通过 |
| 6 | gpt-6.1-sol medium | 无 | False | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ | 146 s。v2 + `DefaultOptionsV1()` + `AllowInvalidUTF8(false)`/`AllowDuplicateNames(false)`，大小写、Duration、nil slice、omitempty 全保持旧行为 |
| 6 | gpt-6.1-sol medium | 有 | True | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ | 130 s。与基线同一做法；无回归 |

结论：`time.After` 一段按官方文档更正；NewTestServer / synctest.Sleep 填补场景 5 EB2 缺口，合入；json/v2 与其余 synctest 规则基线已具备，不合入，场景 6 留作哨兵。

## 2026-10-15 文档上游复核

按 manual check 要求逐条对照，接在今天的上游同步与新增内容评估之后。读 go.dev 页面，并用本机 go1.27.1 实跑能实跑的项。

| 上游 id | 核对的事实 | 当前官方页面 | 结论 |
|---|---|---|---|
| go-effective-go | 有用的零值、接口隐式满足与组合、"share memory by communicating" | https://go.dev/doc/effective_go | 一致 |
| go-wiki-codereview | 空切片 `var t []string`；`Context` 作首参、不放进 struct；错误串不大写不加标点；不用 `_` 丢弃错误；in-band 错误；接收者类型一致；import 分组；安全相关用 `crypto/rand`；goroutine 生命周期 | https://go.dev/wiki/CodeReviewComments | 一致 |
| go-wiki-testcomments | `YourFunc(%v) = %v, want %v` 的 got/want 失败信息；断言可观察行为 | https://go.dev/wiki/TestComments | 一致 |
| go-doc-diagnostics | profiling / tracing / race detector / debugging 四分法；采集方式为 `go test` 标志或 `net/http/pprof` 端点 | https://go.dev/doc/diagnostics；本机 `go help testflag`（`-cpuprofile`/`-memprofile`/`-blockprofile`/`-mutexprofile`/`-trace`）与 `go doc net/http/pprof`（`/debug/pprof/profile?seconds=30`、`heap`、`allocs`、`trace`） | 一致（`references/performance-profiling.md` 的命令全部在上述输出中出现） |
| go-release-notes | 1.22 每迭代循环变量与 ServeMux 路由；1.23 iterator；1.24 `b.Loop`、`t.Context`、`omitzero`、tool 指令；1.25 `testing/synctest`、`WaitGroup.Go`、容器感知 GOMAXPROCS；1.26 `errors.AsType` | https://go.dev/doc/go1.22 … go1.26 | 一致 |
| go-release-notes | 1.27：`goroutineleak` profile GA（含 `/debug/pprof/goroutineleak`）；`go test` 默认跑 `stdversion`；`synctest.Sleep`；`httptest.NewTestServer`；`encoding/json/v2` 与 `jsontext` | https://go.dev/doc/go1.27（go1.27.0 2026-08-19 发布） | 一致。本机 go1.27.1：`go doc` 能查到 `synctest.Sleep`、`httptest.NewTestServer(t testing.TB, handler http.Handler)`、`errors.AsType`、`sync.WaitGroup.Go`；`go 1.21` 模块里调用 `slices.Concat` 时 `go test` 报 `slices.Concat requires go1.22 or later (module is go1.21)` |

结论：五个 docs 条目全部一致，正文未改；SOURCES 五个条目 `synced_at` 改为 2026-10-15，go-release-notes 的 `notes` 补记 go1.27.1
复核。

## 2026-10-15 D2 回归

覆盖提交：33d4d2d（`concurrency.md` 的 `time.After` 回收语义更正；`testing.md` 合入 `httptest.NewTestServer` 与 `synctest.Sleep`；
新增场景 5、6）。b96a909 只动版本号与 SOURCES，abe9af5 只动 research / SOURCES。

复用判定：今天已有的有 skill 结果（`/tmp/hs-evals/go/.../skill/5` 11:45、`skill/6` 12:01）早于 33d4d2d（12:03），按规则不可复用，
重跑。基线复用 `/tmp/hs-evals/go/omp-openai-gpt-6.1-sol-medium/baseline/{5,6}`（11:39、11:41）：query 与 expected_behavior 与当前
`evals.json` 逐字一致，场景加入后夹具与期望未再改动（工作区副本与仓库不同是 agent 自己的编辑）。

选场景：场景 5、6（今天新增）；**新增场景 7**（夹具 `evals/files/relay/`：`go 1.24` 模块中循环内 `time.After` 与未 Stop 的
ticker，评审意见称两者都泄漏）直接考察 `time.After` 更正——既有场景没有覆盖；期望 4 是夹具里顺带的真 bug（心跳每次重置空闲
超时），与更正无关。负例：场景 4。

运行：`uv run tools/run_evals.py go --only N [--baseline] --out /tmp/hs-d2/D2G2`（omp + gpt-6.1-sol medium，VM），产物在
`/tmp/hs-d2/D2G2/go/omp-openai-gpt-6.1-sol-medium/`。场景 5 有 skill 首轮 4 次因模型服务 `503 No available providers` 中止，
第 5 次完成。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 5 | gpt-6.1-sol medium | 有 | True | 1✔ 2◐ 3✔ 4✔ | 280 s。读 `testing.md`；`synctest.Test` 移进每行 `t.Run`；用手写 `RoundTripper` 代替真实服务器（go.mod 为 1.27，正文要求此时用 `httptest.NewTestServer`）；`time.Sleep` 前后 `synctest.Wait()`；`-race -count=100` 通过。产物另存 `/tmp/hs-d2/D2G2-go-skill5-run1` |
| 5（复跑） | gpt-6.1-sol medium | 有 | True | 1✔ 2◐ 3✔ 4✔ | 69 s。同样读 `testing.md` 后选手写 `RoundTripper`。产物 `/tmp/hs-d2/D2G2/go/omp-openai-gpt-6.1-sol-medium/skill/5` |
| 5 | gpt-6.1-sol medium | 无（复用） | False | 1✔ 2◐ 3✔ 4✔ | 复用 `baseline/5`（见上节）：同样手写 `RoundTripper` |
| 6 | gpt-6.1-sol medium | 有 | True | 1✔ 2✔ 3✔ 4✔ | 148 s。v2 + `jsonv1.DefaultOptionsV1()` 加严格 UTF-8 / 重复键选项，保住旧行为，新增回归测试；`go test -race` 通过 |
| 6 | gpt-6.1-sol medium | 无（复用） | False | 1✔ 2✔ 3✔ 4✔ | 复用 `baseline/6` |
| 7（新增） | gpt-6.1-sol medium | 有 | True | 1✔ 2✔ 3✔ 4✔ | 157 s。读 `concurrency.md`；两条阻塞意见都驳回（`go 1.24`，未引用、未 Stop 的 timer / ticker 可回收，剩下的只是每次迭代一次分配），说明旧语义下两条都成立且取决于主模块；实测复现心跳重置空闲超时并改为只在收到消息时 `Reset` 的单个 timer |
| 7（新增） | gpt-6.1-sol medium | 无 | False | 1✔ 2✔ 3✔ 4✔ | 139 s。基线同样驳回两条并复现心跳 bug |
| 4（负例） | gpt-6.1-sol medium | 有 | False | — | 31 s。按 Python asyncio / 线程池作答，未加载 skill |

（编号按 `expected_behavior` 从 1 起数。）

结论：`time.After` 更正无回退（场景 7 两侧全部达成，属消除正文错误陈述）；场景 6 无回退；负例 `skill_read == false`。
**场景 5 期望 2 在有 skill 时两次都未达成**：合入的 `httptest.NewTestServer` 规则模型读到了（两次都读了 `testing.md`），
但仍选择手写 `RoundTripper`，与基线相同；今天合入时记录的「有 skill 用 `NewTestServer`」是 33d4d2d 提交前的一次运行。
本轮未改正文（时间与预算所限，未做「改写 → 重跑」验证）。

遗留：场景 5 期望 2——建议下一轮把 `testing.md` 该条改成以 `NewTestServer` 为默认做法并写明理由（同一个 handler 仍走真实的
client / transport / handler 路径，手写 `RoundTripper` 会跳过），只把 `RoundTripper` 留作 1.27 以下的退路，然后重跑场景 5。
各场景只有 1–2 次运行。
