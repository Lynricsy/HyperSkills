# android 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"Android Jetpack Compose Kotlin agent skill SKILL.md github 2026"`
  - <https://www.skills.sh>（经 web_search 的 skills.sh 索引结果间接命中）
  - VoltAgent/awesome-agent-skills（34k★ 目录，用于交叉确认已知条目，未发现表外的活跃 Android 候选）
  - 领域官方组织仓库：`android/`、`Kotlin/`（JetBrains）、`androidx/`、`google/`、`github/awesome-copilot`
  - `github/awesome-copilot`：`skills/` 与 `instructions/` 全树按 `android|kotlin|compose|gradle|jetpack`
    正则筛过，命中的只有 `skills/kotlin-springboot`、`skills/create-spring-boot-kotlin-project`、
    `skills/kotlin-mcp-server-generator`、`instructions/kotlin-mcp-server.instructions.md`——
    全部是 Kotlin 服务端 / MCP，落在本 skill 的否定边界外，**该仓库对 android 无可用内容**。
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 通过，账号 Lynricsy，全部候选均用登录态取值，无匿名请求、无限流）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | android/skills（`jetpack-compose/*`、`navigation/*`、`build-system/agp/*`、`testing/*`、`performance/*`、`system/edge-to-edge`、`security/android-intent-security`、`profilers/*`、`devtools/android-cli`） | https://github.com/android/skills | 7285 | 2026-09-07 | Apache-2.0 | 官方 Android 团队的任务型 skill 集，逐目录一个窄主题 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | Google LLC 署名，全部内容由 developer.android.com 生成或对齐；AGP 9 迁移、测试策略、edge-to-edge、R8 keep 规则均为可执行步骤。**主干** |
| 2 | Kotlin/kotlin-agent-skills（`skills/kotlin-tooling-*`） | https://github.com/Kotlin/kotlin-agent-skills | 1039 | 2026-08-24 | Apache-2.0 | JetBrains 官方 Kotlin 工具链 skill：AGP 9 + KMP、Java→Kotlin、Native 构建性能、CocoaPods→SPM | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | KMP 侧的官方对手方：`kotlin-tooling-agp9-migration` 精确记录 `com.android.kotlin.multiplatform.library` 拆模块规则，AGP 9 官方 release notes 也反向链接了它 |
| 3 | skydoves/compose-performance-skills | https://github.com/skydoves/compose-performance-skills | 502 | 2026-06-16 | Apache-2.0 | 26 个 Compose 性能窄 skill：稳定性推断、strong skipping、lazy 布局、modifier 顺序、Baseline Profile、R8 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE | Jaewoong Eum（GDE，Stream/Skydoves）；每条规则带 WRONG/RIGHT 对照与 `./gradlew` 验证命令，抽查 3 条（strong skipping 默认开启于 Kotlin 2.0.20、`featureFlags` 取代 `enableStrongSkippingMode`、debug 的 Live Literals 污染 compiler report）全部与官方一致。**性能主干** |
| 4 | aldefy/compose-skill（`skills/compose-expert`） | https://github.com/aldefy/compose-skill | 582 | 2026-07-23 | MIT（API 报 NOASSERTION；实读 LICENSE 为 MIT + 尾部注明 `references/source-code/` 摘自 AOSP，Apache-2.0） | Compose/CMP 大而全，30+ reference，含 side-effects、CompositionLocal、view interop、deprecated patterns | 2 | 2 | 3 | 2 | 2 | 11 | INCLUDE | 引用 androidx 源码「收据」，view interop 与 side-effect 清单是本 skill 缺口的良好补充；但 SKILL.md 混入插件安装横幅与 27-agent 兼容说明，属包装噪声，只取技术段落 |
| 5 | new-silvermoon/awesome-android-agent-skills（`.github/skills/**`） | https://github.com/new-silvermoon/awesome-android-agent-skills | 955 | 2026-07-27 | Apache-2.0 | 15 个中等粒度 skill：架构、ViewModel、data layer、Gradle build logic、协程、测试、可访问性、RxJava→协程迁移 | 1 | 2 | 2 | 2 | 2 | 9 | INCLUDE | 覆盖面正好补上 android/skills 缺的「架构 / ViewModel / 协程」层；ViewModel 一节对 Kotlin 显式后备字段的版本判定（2.3 实验、2.4 稳定）经 kotlinlang.org 核实为真，但一次性事件用 `SharedFlow` 与官方指南冲突（见裁决 #1） |
| 6 | Drjacky/claude-android-ninja | https://github.com/Drjacky/claude-android-ninja | 119 | 2026-08-02 | Apache-2.0 | 单 skill + 39 个 reference + `assets/convention/*.kt` 约定插件模板 | 1 | 2 | 3 | 2 | 2 | 10 | INCLUDE | 唯一一个把 Now-in-Android 式 **convention plugin / 多模块 / 版本目录** 落成可复制模板的候选；有 CI 校验脚本（行数、排版、链接、语气），工程纪律高于星数暗示 |
| 7 | mmiani/kotlin-kmp-claude-agent-skills（`skills/kotlin-*kmp*`、`kotlin-project-*`） | https://github.com/mmiani/kotlin-kmp-claude-agent-skills | 75 | 2026-08-15 | Apache-2.0（API 报 NOASSERTION；实读 LICENSE 为完整 Apache-2.0 正文 + `Copyright 2026 Mariano Miani`） | 14 个 KMP skill：源集层级、expect/actual 纪律、KMP Gradle 治理、CMP、KMP 测试 | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE | KMP 一节的骨架来源：「先抬到最高可共享源集，再考虑 expect/actual」的判定顺序与 kotlinlang.org 的 hierarchy template 指南一致。frontmatter 带 `allowed-tools`，合入时剥离 |
| 8 | Meet-Miyani/compose-skill | https://github.com/Meet-Miyani/compose-skill | 293 | 2026-06-09 | MIT | 单 skill + 40 个 reference，Compose/CMP 全生命周期（MVI、Ktor、Room、Paging、DataStore） | 1 | 2 | 2 | 2 | 2 | 9 | INCLUDE（补充） | 「不要强推迁移，尊重项目既有约定」与「向 `commonMain` 加 AndroidX 依赖前先确认目标发布了多平台构件」两条是别处没有的真陷阱；但 description 要求「只有用户点名才激活」，是 agent 绑定写法，不可照搬 |
| 9 | felipechaux/kmp-compose-multiplatform-skill | https://github.com/felipechaux/kmp-compose-multiplatform-skill | 74 | 2026-03-20 | MIT | KMP + CMP 单 skill，8 个 reference，Koin/Ktor/Room 清洁架构 | 1 | 1 | 2 | 2 | 2 | 8 | MAYBE（仅交叉校验） | 距今 5.7 个月，卡在 6 个月窗口边缘；内容与 #7 大量重叠且更泛，模块布局一节仅用作与 #7 的交叉印证，未单独贡献规则，故不进 SOURCES |
| 10 | maxrave-dev/kotlin-footguns | https://github.com/maxrave-dev/kotlin-footguns | 203 | 2026-08-29 | GPL-3.0 | 从一款生产音乐 App 挖出的 ~280 条 Kotlin/CMP/桌面 JVM 陷阱清单 | 1 | 3 | 3 | 2 | 0 | 9 | reference（许可强制） | GPL-3.0，按许可规则**只能** `relation: reference`。只用 `CATALOG.md` 的主题清单做覆盖面自检；其主体是桌面 JVM/JNA/mpv 与该 App 特有机制，与 Android 应用开发交集小，未取任何文字 |
| 11 | developer.android.com（架构、Compose、构建、测试、性能各指南） | https://developer.android.com/topic/architecture | — | 持续更新 | CC-BY-4.0（站点条款） | 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（docs） | 所有裁决的最终依据；UI 事件、UDF、测试分层、AGP 9 行为变更均以此为准 |
| 12 | kotlinlang.org（语言特性状态、协程、KMP 源集层级） | https://kotlinlang.org/docs/multiplatform-hierarchy.html | — | 持续更新 | Apache-2.0（Kotlin 文档仓库） | 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（docs） | 用于核实显式后备字段的稳定版本、默认层级模板、`expect/actual` 适用面 |
| 13 | github/awesome-copilot | https://github.com/github/awesome-copilot | 38858 | 2026-09-10 | MIT | 418 个 skill + 193 个 instruction | 3 | 3 | — | — | 2 | — | REJECT | 全树正则筛查后，Kotlin 相关条目只有 Spring Boot 与 MCP server，**无任何 Android / Compose / Gradle-Android 内容**。范围不匹配，非质量问题 |
| 14 | androidx/androidx（`.agents/skills/*`） | https://github.com/androidx/androidx | 6086 | 2026-09-10 | Apache-2.0 | `api_review`、`run_tests`、`manage_cl_workspaces`、`find-my-flags`、`ktdoc_quality` 等 | 3 | 3 | — | 3 | 2 | — | REJECT | 这些 skill 是**给 androidx 贡献者维护 androidx 本身**用的（AOSP CL 工作区、API 评审、feature flag 清理），不是应用开发内容。范围不匹配 |
| 15 | ayush016/android-lead-agent-skills | https://github.com/ayush016/android-lead-agent-skills | 77 | 2026-07-01 | MIT | 单 skill + 20 个 reference，Compose/性能/安全/通知/共享元素 | 1 | 2 | 2 | 1 | 2 | 8 | MAYBE（未采用） | frontmatter 硬钉 `compose_bom: "2024.09.00+"`、`min_sdk: 21`、`target_sdk: 35`，且携带 `compatibility.tools: [android_mcp, ...]` 这类 agent 绑定；正文把「每个界面都必须达到设计奖水准」写成硬规则，属风格强制而非工程规则。同主题在 #4/#6 有更新更准的版本 |
| 16 | haidrrrry/compose-kotlin-agent-skills | https://github.com/haidrrrry/compose-kotlin-agent-skills | 47 | 2026-07-08 | MIT | 「2026 企业版」Android/Kotlin 单库，含子 skill | 0 | 2 | 2 | 1 | 2 | 7 | MAYBE（未采用） | 权威性来自作者自己的三个玩具仓库；检索时即被标出把 Navigation `2.9.0` 归入「Navigation 3」，版本钉子与实际不符。无独有内容 |
| 17 | anhvt52/jetpack-compose-skills | https://github.com/anhvt52/jetpack-compose-skills | 96 | 2026-03-12 | MIT | Compose 代码生成与评审规则 | 1 | 1 | 2 | 2 | 2 | 8 | MAYBE（未采用） | 距今 6.0 个月整，压线；主题（Compose 评审规则）已被 #3 + #4 更细地覆盖，加入只会引入版本更旧的重复表述 |
| 18 | uselflabs/android-agent-skills | https://github.com/uselflabs/android-agent-skills | 9 | 2026-01-26 | 无（API `license: null`） | 少量 Android skill | 0 | 0 | 1 | — | 0 | 1 | REJECT | 距今 7.5 个月无推送，超过 6 个月窗口且非官方；无许可文件；9★ 无社区验证。按量表新鲜度 0 直接 REJECT |

## 深度审查

### 1. android/skills（Apache-2.0，主干）

- **许可实读结论（本批次特殊处理项）**：仓库全树 `543` 个条目，`LICENSE` 相关文件**只有根目录 `LICENSE.txt` 一个**
  （`[x for x in tree if "LICENSE" in x.upper()]` → `['LICENSE.txt']`）。实读该文件：标准 Apache License 2.0 全文 +
  尾部标准 boilerplate。每个 `SKILL.md` 的 `license:` 字段写的是字符串 `Complete terms in LICENSE.txt`，
  指向的就是这唯一一份根许可。逐目录检查过 `jetpack-compose/{adaptive,migration,theming}`、`navigation/{navigation-3,navigation-event}`、
  `build-system/agp/agp-9-upgrade`、`testing/testing-setup`、`performance/r8-analyzer`、`profilers/android-profiler`、
  `system/edge-to-edge`、`security/android-intent-security`、`devtools/android-cli`：**无任何目录携带独立 LICENSE，
  无一例外均落在根 Apache-2.0 之下**，因此全部按 `merged` 处理，无需逐目录降级。
- **结构**：一目录一窄主题，`SKILL.md` 是编号步骤，`references/` 大多是 developer.android.com 的 Markdown 快照
  （路径形如 `references/android/develop/ui/compose/...`）。这意味着它的事实密度极高但**没有跨主题的规则层**——
  没有「Compose 状态管理总则」「架构总则」这种东西，因为官方把那些留给了文档站。
- **frontmatter**：`name` / `description` / `license` / `metadata.{author,last-updated,keywords}`。
  `last-updated`、`keywords` 是上游专属字段，本仓库白名单不含，合入时剥离。
- **质量**：`agp-9-upgrade` 的 `references/ksp-kapt.md` 给出了「怎么判断一个注解处理器是否支持 KSP」的可执行判据
  （jar 内是否存在 `services/com.google.devtools.ksp.processing.SymbolProcessorProvider`），这类判据在社区候选里一条都找不到。
  `buildconfig.md` 记录的 `BuildConfigField(type="String", value="\"...\"")` 引号陷阱同理。
- **agent 绑定**：`profilers/android-profiler` 依赖 `$SKILL_ROOT` 变量和 `android` CLI 二进制；
  `devtools/android-cli` 整篇是 `android` CLI 的安装与用法。前者的变量写法被本仓库禁用，后者是工具说明书，
  两者的**结论**（Perfetto 采集 → 分析的分诊顺序）可用，正文不引入变量与安装脚本。
- **重叠**：与 #2 在 AGP 9 上重叠，但 #1 面向非 KMP 应用、#2 面向 KMP（AGP 9 官方 release notes 正是这样分流的），两者互补而非冲突。

### 2. Kotlin/kotlin-agent-skills（Apache-2.0）

- 6 个 skill，其中 `kotlin-backend-jpa-entity-mapping` 属 Kotlin 服务端，落在本 skill 否定边界外，不取。
- `kotlin-tooling-agp9-migration`（21 KB）：AGP 9 下 KMP 模块必须换成 `com.android.kotlin.multiplatform.library`，
  且「KMP + Android Application 插件不能在同一个 Gradle 子项目」，需要把 app 抽成独立子项目——这条与 AGP 9 官方
  release notes 的 NOTE 完全一致，是 KMP 一节最硬的事实。
- `kotlin-tooling-java-to-kotlin`（含框架探测表、保留 git 历史的两步提交法）与 `kotlin-tooling-native-build-performance`
  质量高但主题偏；前者取「先探测框架再转换、用两次提交保留 rename 历史」的结论，后者不取（Kotlin/Native 构建，不是 Android）。
- `kotlin-tooling-cocoapods-spm-migration`（33 KB）是 KMP-iOS 侧的深水区，与本 skill 的 KMP 一节边界（只到「Android 开发者
  需要知道的 KMP 形态」）比过深，只用于确认 KMP 一节不要越界写 iOS 集成细节。

### 3. skydoves/compose-performance-skills（Apache-2.0）

- 26 个窄 skill，分 `recomposition/ stability/ lists/ modifiers/ side-effects/ measurement/ build/ audit/ hot-reload/`。
  每个 SKILL.md 结构一致：When to use / When NOT / Prerequisites / Workflow / Patterns（WRONG-because + RIGHT）/
  Mandatory rules / Verification / References。这是本批次里**唯一自带验证门**的候选。
- 抽查三条对照官方：① strong skipping 自 Kotlin 2.0.20 默认开启、关闭方式为
  `composeCompiler { featureFlags.add(ComposeFeatureFlag.StrongSkipping.disabled()) }`，旧属性 `enableStrongSkippingMode`
  已 `@Deprecated` —— 与 Compose 编译器 Gradle 插件文档一致；② 无捕获 lambda 由编译器发为单例、不参与自动 `remember`
  —— 与编译器行为一致；③ debug 构建的 Live Literals 会污染 compiler report 与 Layout Inspector 计数 —— 与官方
  「性能测量必须在 release」一致。三条全对。
- `hot-reload/*`（Compose Hot Reload + MCP）与 `stability/using-stability-analyzer-ide-plugin`（IDE 插件）
  属工具面，不取；`audit/`、`measurement/`、`build/configuring-r8-for-compose` 全取。
- 局限：只谈 Compose 性能，不谈架构、构建、测试、View 体系。必须与 #1/#5/#6 拼装。

### 4. aldefy/compose-skill（MIT，实读）

- `skills/compose-expert/SKILL.md` 19 KB，`references/` 30 个文件，另有 `references/source-code/*.md`
  从 androidx/androidx 摘录源码片段（LICENSE 尾部已声明这部分是 AOSP Apache-2.0）。
- 有用的独有面：`side-effects.md`、`composition-locals.md`、`view-composition.md`（View↔Compose 互操作）、
  `deprecated-patterns.md`、`production-crash-playbook.md`。
- 噪声：SKILL.md 前 1/3 是插件安装横幅、迁移公告、27 个 agent 的兼容说明和「session_start 自动探测」这类
  harness 绑定描述；`agents/openai.yaml` 是 agent 配置。全部剥离。
- 正确性抽查扣 1 分：`styles-experimental.md` 把 Compose Styles API 当作可推荐做法呈现，而官方
  `jetpack-compose/theming/styles` skill 自己第一句就写着「EXPERIMENTAL，需要 alpha 依赖与 opt-in」。
  本 skill 不写 Styles API。

### 5. new-silvermoon/awesome-android-agent-skills（Apache-2.0）

- 15 个 skill 分 6 类，粒度中等（每个 2–8 KB），是唯一系统覆盖「架构 / ViewModel / data layer / 协程」的候选。
- `android-viewmodel` 对 Kotlin 显式后备字段的版本判定正确（2.3.0 实验需 `-Xexplicit-backing-fields`，2.4.0 稳定），
  已对照 kotlinlang.org 语言特性状态页核实。
- `gradle-build-performance`（8 KB）覆盖配置缓存、并行、KSP 替代 kapt、模块图，与 #6 的约定插件互补。
- 冲突见裁决 #1（一次性事件）。

### 6. Drjacky/claude-android-ninja（Apache-2.0）

- 单 skill + 39 reference + `assets/`（21 个 convention plugin 的 Kotlin 源码 + `libs.versions.toml.template` +
  `detekt.yml.template` + `proguard-rules.pro.template`）。
- 独有价值集中在 `modularization.md`、`dependencies.md`、`gradle-setup.md` 与 `assets/convention/*`：
  把 `build-logic/` 约定插件的写法（`AndroidApplicationComposeConventionPlugin`、`AndroidFeatureConventionPlugin`、
  `AndroidLibraryJacocoConventionPlugin`、`GradleManagedDevices.kt`）落成可直接改的模板。
- 明确的「brownfield 优先」纪律：动手前先读 `settings.gradle.kts` + `gradle/libs.versions.toml` + app 模块构建文件，
  再决定能不能套模板。这条与 #8 的「不要强推迁移」同向，进 Core rules。
- 扣分点：版本钉子写在 assets 模板里（`libs.versions.toml.template`），会随时间腐化；本 skill 只取**结构**，不搬版本号。

### 7. mmiani/kotlin-kmp-claude-agent-skills（Apache-2.0，实读）

- 14 个 skill，命名规范（`kotlin-<域>-<主题>`），每个 11–21 KB，写法是「评审维度 + 官方默认 + 反模式」。
- `kotlin-platform-kmp-bridges` 的判定阶梯——先看能否放进 `commonMain`，再看中间源集，再看普通接口注入，
  最后才是 `expect/actual`——是 KMP 一节的核心结构。
- frontmatter 含 `allowed-tools: Read, Grep, Glob`。本仓库白名单虽然允许 `allowed-tools`，但那是给本仓库自己的
  skill 用的；从上游继承一份工具限制没有意义，剥离。

### 8. Meet-Miyani/compose-skill（MIT，补充）

- 40 个 reference，覆盖到 Paging/DataStore/Ktor 这类库层，超出本 skill 的边界（库说明书）。
- 只取两条跨库的判断规则（见候选表第 8 行），其余不取。
- `description` 写「Only use when the user explicitly mentions "compose-skill"」是典型的 agent 绑定反模式，
  与本仓库「触发条件全部写进 description」的要求相反，不参考其 description 写法。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | ViewModel 的一次性事件（导航、Snackbar）怎么表达 | new-silvermoon `android-viewmodel`：用 `SharedFlow(replay=0, extraBufferCapacity=1)` + `tryEmit`，在 `LaunchedEffect` 里 collect。Meet-Miyani：MVI 的 `Effect` 通道。官方：**源自 ViewModel 的 UI 动作必须落到 UI state 上** | 采官方：事件建模为 state 字段（如 `userMessage: String?`），UI 消费后回调 ViewModel 清除。唯一逃生口是需要「恰好一次」投递语义时用 `Channel` + `receiveAsFlow`，并说明代价 | 官方厂商 > 社区。<https://developer.android.com/topic/architecture/ui-layer/events>：「UI actions that originate from the ViewModel should always result in a UI state update… makes events reproducible after configuration changes and guarantees that UI actions won't be lost」。`SharedFlow(replay=0)` 在配置变更/进程重建时会丢事件，正是该页要消除的失败模式 |
| 2 | strong skipping 之后还需不需要管类型稳定性 | 社区常见说法（也是 #16 的暗示）：Kotlin 2.0.20 之后一切 restartable composable 都 skippable，稳定性不重要了。skydoves `using-strong-skipping-correctly` + `stabilizing-compose-types`：仍然重要——不稳定参数退化为 `===` 比较，每次新分配的 `List` 都判不等 | 采 skydoves：正文写「strong skipping 让它 *可* 跳过，但不稳定参数用 `===` 比，新分配的集合永远跳不过」，并保留稳定性修复动作 | 更新 > 更旧，且与编译器实际行为一致；官方 Compose 性能文档同样保留「稳定类型」章节。这是本 skill 最容易被基线模型答错的一条 |
| 3 | AGP 9 迁移由谁定义 | android/skills `agp-9-upgrade`（非 KMP 路径）与 Kotlin/kotlin-agent-skills `kotlin-tooling-agp9-migration`（KMP 路径）步骤不同：前者「移除 `org.jetbrains.kotlin.android`，迁 kapt→KSP，否则 `com.android.legacy-kapt`」，后者「换 `com.android.kotlin.multiplatform.library`，把 app 拆成独立子项目」 | 两者都对，按项目形态分流：非 KMP 走前者，KMP 走后者。正文写成一个带分叉点的清单，不二选一 | AGP 9.0 官方 release notes 显式地把两个 skill 分别推荐给「non-KMP app」与「KMP app」，并写明「新的 KMP 集成不支持 KMP 与 Android Application 插件在同一子项目」 |
| 4 | 默认 ProGuard 文件 | 老工程与部分社区材料仍写 `getDefaultProguardFile("proguard-android.txt")` | 采官方：AGP 9 起 `getDefaultProguardFile()` 只支持 `proguard-android-optimize.txt`（`android.r8.proguardAndroidTxt.disallowed` 默认 `true`），因为 `proguard-android.txt` 内含 `-dontoptimize` | AGP 9.0 release notes 的默认值变更表；skydoves `configuring-r8-for-compose` 独立给出同一结论（「用错默认文件 = R8 优化 pass 根本没跑」） |
| 5 | Compose 行为测试放哪个源集 | 社区材料多默认「Compose UI 测试 = 仪器化测试 = `androidTest`」 | 采官方 `testing-setup`：Compose/Espresso 行为测试放 `test` 源集用 Robolectric 跑；只有明确要求真机（或需要系统 UI 交互、SQLite 引擎、edge-to-edge 渲染）时才放 `androidTest` | Google 官方 skill 的 Step 6/Step 7/Step 12 分工；Robolectric 路径的反馈环快一个数量级，且 Room DAO 因 SQLite 引擎差异**必须**在设备上测——这两条一起才是完整规则 |
| 6 | 是否推荐 Compose Styles API / `Modifier.styleable` | aldefy `styles-experimental.md` 作为可用做法呈现；官方 `jetpack-compose/theming/styles` 自述 EXPERIMENTAL，要求 `compileSdk 37+`、Compose foundation `1.12.0-alpha01+` 并 opt-in | 不写入本 skill。理由：处于 alpha，且本仓库禁止时间敏感表述，写一个 alpha API 只会在 6 个月内变成错误内容 | 标准第 3 节「不写时间敏感表述」+「版本敏感规则标注可用性底线」；一个还没有稳定底线的 API 无法标注 |
| 7 | 一次性把 XML View 全量迁 Compose，还是保留互操作 | 社区候选普遍把「迁到 Compose」当默认终点 | 采官方 `migrate-xml-views-to-jetpack-compose`：按屏幕/组件增量迁移，长期允许 `ComposeView` / `AndroidView` 双向互操作共存；先选「最优候选屏幕」，保持像素与行为等价 | 官方 10 步迁移法的第 1 步就是「识别最优 XML 迁移候选」，而不是「全量替换」；aldefy `view-composition.md` 同向 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `android-official` | android/skills | merged | AGP 9 迁移清单（built-in Kotlin、kapt→KSP/legacy-kapt、BuildConfig、新 DSL/变体 API、默认值翻转）、测试分层与源集归属、R8/keep 规则纪律、edge-to-edge 与 insets、Intent/导出组件安全、Navigation 3 与类型安全导航、XML→Compose 增量迁移法、自适应布局、Perfetto 分诊顺序 |
| `jetbrains-kotlin` | Kotlin/kotlin-agent-skills | merged | KMP 分支下的 AGP 9 形态（`com.android.kotlin.multiplatform.library`、app 独立子项目）、Java→Kotlin 转换纪律 |
| `skydoves-compose-perf` | skydoves/compose-performance-skills | merged | Compose 三阶段模型与状态读下沉、稳定性推断与 strong skipping 的真实语义、lazy 列表 key/contentType、modifier 链顺序语义、release 才可测量、Baseline Profile + Macrobenchmark、Compose 的 R8 配置 |
| `aldefy-compose` | aldefy/compose-skill | merged | 副作用 API 选择表、CompositionLocal 使用边界、View↔Compose 互操作、已废弃 Compose 模式清单 |
| `silvermoon-android` | new-silvermoon/awesome-android-agent-skills | merged | 分层架构与 data layer 单一真相源、ViewModel/UI state 建模与显式后备字段、协程作用域与生命周期感知收集、Gradle 构建性能、可访问性检查项 |
| `drjacky-ninja` | Drjacky/claude-android-ninja | merged | `build-logic/` 约定插件与多模块结构、版本目录组织、brownfield 优先纪律 |
| `mmiani-kmp` | mmiani/kotlin-kmp-claude-agent-skills | merged | KMP 源集层级判定阶梯、`expect/actual` 最小化原则、CMP 与 Android-only AndroidX 构件的边界 |
| `meetmiyani-compose` | Meet-Miyani/compose-skill | merged | 「尊重既有约定，不强推迁移」、向 `commonMain` 添加 AndroidX 依赖前先核实多平台构件可用性 |
| `maxrave-footguns` | maxrave-dev/kotlin-footguns | reference | GPL-3.0，仅用其主题目录做覆盖面自检，未取任何文字 |
| `android-docs` | developer.android.com | merged | UI 事件与 UDF 的官方裁决、架构分层定义、AGP 9 行为变更与兼容矩阵、测试基础、性能与 Baseline Profile 指南 |
| `kotlin-docs` | kotlinlang.org | merged | 语言特性稳定状态（显式后备字段等）、协程与 Flow 语义、KMP 默认源集层级模板 |

## 基线缺口

无 skill（`uv run tools/run_evals.py android --baseline`，`anthropic/claude-opus-5` · thinking=medium，
四场景全部 `status: ok`、`skill_read: false`）时，逐条人工读 `answer.md` 判定，未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 Compose 评审 | 「strong skipping（Kotlin 2.0.20+）下不稳定参数按 `===` 比较，因而新分配的 `List` 仍然跳不过」 | 基线答案通篇把跳过机制解释为「类型稳定性 + `equals`」，**完全没有提到 strong skipping**，因此也没解释为什么 `List<Article>` 参数在 strong skipping 时代仍然有害。其余 6 条（`@Immutable` 契约被破坏、`key`、`collectAsStateWithLifecycle` + 不传 `Flow`、`derivedStateOf`、`offset { }` 相位下沉、modifier 顺序）全部达成——基线在 Compose 上很强，缺口精确地落在这一条 |
| 2 AGP 9 迁移 | 「`getDefaultProguardFile("proguard-android.txt")` 已不受支持，必须换成 `proguard-android-optimize.txt`」 | 基线**答反了**：原文写「`proguard-android-optimize.txt` 是顺手的优化建议，非迁移必需——不想改就保留原文件名」。AGP 9 的 `android.r8.proguardAndroidTxt.disallowed` 默认为 `true`，保留原文件名会直接构建失败。这是本次唯一一条基线给出**错误结论**的行为 |
| 3 测试规划 | 「Compose/Espresso 行为测试可以放在 `test` 源集用 Robolectric 跑，`androidTest` 留给真机场景」 | 基线明确写「**不加** Robolectric」，且整篇没有讨论 Compose 行为测试的源集归属。其余 5 条（`WhileSubscribed` 需先订阅、DAO 走 `androidTest` + in-memory Room、Fake 优先、`MainDispatcherRule` + `runTest`、不测 plumbing）达成 |
| 4 负例（React Native） | —（负例无缺口概念） | 基线正确地按 React Native 处理，未给出 Compose/Gradle 建议；用于验证有 skill 时 `skill_read` 仍为 `false` |

## 评测结果

两次运行同模型同思考档（`anthropic/claude-opus-5` · `medium`，`tools/run_evals.py` 默认），
四场景 `status` 全为 `ok`。判定方式：人工通读 `/tmp/hs-evals/android/anthropic-claude-opus-5-medium/{baseline,skill}/<i>/answer.md`
（场景 1、4 另读了 agent 写回的源文件）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Compose 评审（`NewsScreen.kt`） | claude-opus-5:medium | 无（baseline） | false | 6 / 7 —— 缺「strong skipping 下 `===` 比较」 | 145.9 s。其余全部命中，包括 `@Immutable` 契约、`key`、`derivedStateOf`、`offset { }` 相位下沉 |
| 1 | claude-opus-5:medium | 有 | **true** | 6.5 / 7 —— **补上 strong skipping `===`**；modifier 顺序只给了修正链、未复述原因 | 101.7 s。首句即「强跳过用 `===` 比较行参数 → 相等 → 行被跳过」，正是基线缺的那条 |
| 2 AGP 9 迁移（`app-build.gradle.kts` + `libs.versions.toml`） | claude-opus-5:medium | 无（baseline） | false | 6 / 7 —— **`proguard-android.txt` 一条答反**（称「非迁移必需，不想改就保留」） | 256.9 s |
| 2 | claude-opus-5:medium | 有 | **true** | 7 / 7 —— **`android.r8.proguardAndroidTxt.disallowed` 默认 true、`proguard-android.txt` 被拒绝** | 105.0 s。并连带列出 `strictFullModeForKeepRules`、`optimizedResourceShrinking`、`failOnMissingFiles` 的连锁影响 |
| 3 测试规划（`BookmarksViewModel.kt`） | claude-opus-5:medium | 无（baseline） | false | 5 / 6 —— 缺「Compose 行为测试可放 `test` + Robolectric」 | 116.5 s |
| 3 | claude-opus-5:medium | 有 | **true** | 5 / 6 —— 同一条仍未达成（见结论说明）；`WhileSubscribed` 一条答得更准（显式引「skill 规则 22」并给出 `backgroundScope.launch { … }`），并新增 `MainDispatcherRule` 与 `runTest` 必须共享 scheduler 的陷阱 | 100.9 s。DAO 归 `androidTest` 的理由复述为「设备自带 SQLite」，但未点名 `inMemoryDatabaseBuilder` |
| 4 负例（`ProductList.tsx`，React Native） | claude-opus-5:medium | 无（baseline） | false | 3 / 3 | 143.5 s |
| 4 | claude-opus-5:medium | 有 | **false** ✅ | 3 / 3 —— 未加载 android skill，全部按 React Native 处理（memo/useCallback/StyleSheet/keyExtractor/FlashList 尺寸、`Intl` 提升），未出现 Compose、Gradle、Baseline Profile、R8 建议 | 114.9 s。负例判据满足 |

结论：**通过**。基线未达成的三条里有两条在有 skill 时达成——
场景 1 的 strong skipping `===` 语义，与场景 2 的 `proguard-android.txt` 在 AGP 9 被拒绝
（后者基线不只是漏答，而是给出了会导致构建失败的**错误**结论）。负例 `skill_read == false`。

场景 3 那一条两边都未达成，原因是评测项本身设计偏弱：夹具 `BookmarksViewModel.kt` 里没有任何
Composable，两次运行都合理地判断「本任务不需要 Compose 行为测试」，因此这条 `expected_behavior`
在这个夹具上不可观测。规则本身在 `SKILL.md` Core rule 20 与 `references/testing.md` 的源集表里
写得很明确；下次同步本 skill 时应把这条改成夹具里真有 Composable 的场景，或移到独立场景，
而不是继续挂在这个夹具上。

## 备注

- **android/skills 的 LICENSE 实读结论**：全仓仅根 `LICENSE.txt` 一份，内容为标准 Apache-2.0；
  各 skill 目录 frontmatter 的 `license: Complete terms in LICENSE.txt` 指向的就是它。逐目录确认无独立许可文件，
  因此 9 个被引用目录全部按 Apache-2.0 `merged` 处理，无需单独降级。已写入 SOURCES.yaml 的 `notes`。
- **GPL 上游降级说明**：maxrave-dev/kotlin-footguns 为 GPL-3.0，按许可规则表只能 `relation: reference`。
  实际用法是拿 `CATALOG.md` 的主题清单核对本 skill 的覆盖面（结论：其 A/B/C 三组里与 Android 应用开发相关的
  主题——Compose 状态、Room 迁移、R8 keep 规则、构建变体密钥——本 skill 已由其他上游覆盖；其余为桌面 JVM/JNA/
  媒体引擎，属本 skill 边界外）。未复制任何文字、脚本或数据。
- **API license 字段与实读不一致的两例**：aldefy/compose-skill 与 mmiani/kotlin-kmp-claude-agent-skills 的
  GitHub API 均报 `NOASSERTION`（前者 LICENSE 尾部追加了 AOSP 源码片段的 Apache-2.0 说明，后者 Apache 头部被改写），
  实读后分别为 MIT 与 Apache-2.0，均可 `merged`。已在 SOURCES.yaml `notes` 记录。
- **上游 frontmatter 剥离项**：`metadata.last-updated`、`metadata.keywords`（android/skills）、
  `allowed-tools`（mmiani）、`compatibility.tools`（ayush016，未采用）、`metadata.platforms` / `metadata.standard`
  （haidrrrry，未采用）、`version` 顶层键（aldefy）。本仓库 frontmatter 只保留 skill-standard 第 1 节规定的字段。
- **未来同步要盯的上游**：android/skills（推送极频繁，`paths` 已收窄到 9 个目录）、
  Kotlin/kotlin-agent-skills（AGP 10 时会再改一次 KMP 插件形态）、skydoves/compose-performance-skills。
- **放弃的方向**：Compose Styles API（alpha，见裁决 #6）、Compose Hot Reload（工具面）、
  `android` CLI 说明书（工具说明书，且需要外部安装脚本）、Paging/Ktor/DataStore 等库说明书（库文档而非平台规则）。
