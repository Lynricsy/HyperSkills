# apple 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-10
- 复核日期：2026-09-10（本次全量复核，25 个仓库经 GitHub API 匿名查询逐个核对 `stargazers_count` / `pushed_at` / `license.spdx_id` / `default_branch` / `archived`；候选表 33 行是这 25 个仓库中的单个 skill 目录）
- 检索途径：
  - 前期归档调研（30 个候选，含 API 403 时的 HTML 回退与 `unverified` 标记），本次全部重新核实
  - `web_search`：`"SwiftUI agent skill SKILL.md github 2026"` —— 未发现归档清单之外的新候选，返回结果全部落在已收录的 twostraws / AvdLee / dpearson2699 三家
  - 领域官方组织仓库：`superagents-lab/xcode27-skills`（Apple 从 Xcode 27 导出的官方 skill）、`developer.apple.com` 文档
  - 上游作者的姊妹仓库枚举（twostraws 与 AvdLee 各自的 SwiftUI / Concurrency / SwiftData / Testing 四件套）
- GitHub API 核对方式：`https://api.github.com/repos/<owner>/<repo>`，匿名可用，本次未触发限流
- 部署目标核实：读 <https://developer.apple.com/documentation/ios-ipados-release-notes>。当日状态为 **iOS 26.6 已发布、iOS 27 处于 RC**，因此默认部署目标定为 iOS 26，iOS 27 API 一律标注版本并要求门控

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | twostraws/SwiftUI-Agent-Skill `swiftui-pro/` | https://github.com/twostraws/SwiftUI-Agent-Skill | 4688 | 2026-04-20 | MIT | SwiftUI 全面评审：弃用 API、视图、数据流、导航、HIG、无障碍、性能、卫生 | 2 | 1 | 3 | 3 | 2 | 11 | INCLUDE | Paul Hudson；本领域唯一给出精确输出格式与三条示例的候选；4 KB SKILL.md + 9 个精简参考，信噪比最高 |
| 2 | AvdLee/SwiftUI-Agent-Skill `skills/swiftui-expert-skill/` | https://github.com/AvdLee/SwiftUI-Agent-Skill | 3508 | 2026-08-12 | MIT | 27 主题路由；Liquid Glass、本地化、Charts、macOS、Instruments 录制与分析 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE | 本领域最深；唯一自带可执行工具链（xctrace 录制 + trace 解析）；「每次任务先读 latest-apis」是本领域杠杆最高的规则 |
| 3 | AvdLee/SwiftUI-Agent-Skill `.agents/skills/update-swiftui-apis/` | 同上 | 3508 | 2026-08-12 | MIT | 重扫 Apple 文档以刷新 latest-apis 的元 skill | 2 | 2 | 2 | 2 | 2 | 10 | INCLUDE（reference） | 非面向用户；只借鉴其「如何重新同步弃用索引」的方法论，未复制内容 |
| 4 | superagents-lab/xcode27-skills `swiftui-specialist/` | https://github.com/superagents-lab/xcode27-skills | 312 | 2026-06-09 | NONE | Apple 官方导出：structure / dataflow / environment / modifiers / foreach / localization / animations / soft-deprecated-apis | 3 | 1 | 3 | 3 | 0 | 10 | INCLUDE（宽松策略 merged） | 作者是 Apple 本身，内容权威性无可替代；README 明示「不授予任何许可」，按项目宽松策略合入并署名 |
| 5 | 同上 `swiftui-whats-new-27/` | 同上 | 312 | 2026-06-09 | NONE | iOS 27 新 API 与破坏性变更（@State 宏化、@ContentBuilder、reorderable、swipeActions、文档型 App） | 3 | 1 | 3 | 3 | 0 | 10 | INCLUDE | 「模型一定不知道」价值最高的一份；@State 宏化的错误修法警告尤其重要 |
| 6 | 同上 `uikit-app-modernization/` | 同上 | 312 | 2026-06-09 | NONE | 多窗口现代化：UIScreen.main、interfaceOrientation、场景生命周期、非对称安全区 | 3 | 1 | 3 | 3 | 0 | 10 | INCLUDE | 「iOS 27 起未适配场景生命周期的 App 启动即崩溃」是硬事实，其它候选无一覆盖 |
| 7 | 同上 `test-modernizer/` | 同上 | 312 | 2026-06-09 | NONE | XCTest → Swift Testing 迁移 | 3 | 1 | 2 | 3 | 0 | 9 | INCLUDE（补充） | 与 #9/#10 重叠，仅作正确性校验 |
| 8 | 同上 `device-interaction/` | 同上 | 312 | 2026-06-09 | NONE | 设备/模拟器截图、UI 层级、触控 | 3 | 1 | 2 | 2 | 0 | 8 | REJECT（本 skill） | 属 `xcode-tooling` 主题，不在本 skill 范围（见路线图 Batch 5） |
| 9 | 同上 `audit-xcode-security-settings/`、`c-bounds-safety/` | 同上 | 312 | 2026-06-09 | NONE | 构建设置安全加固 / C -fbounds-safety | 3 | 1 | 3 | 3 | 0 | 10 | REJECT（本 skill） | 内容优质但与 Swift/SwiftUI 应用开发正交，强行并入会稀释 description 触发面 |
| 10 | YordiLorenzo/liquid-glass-skills `liquid-glass/` | https://github.com/YordiLorenzo/liquid-glass-skills | 4 | 2026-08-09 | MIT | Liquid Glass 材质：变体、容器采样、工具栏、UIKit/AppKit、无障碍、回退、已知 bug | 1 | 2 | 3 | 3 | 2 | 11 | INCLUDE | 全表工程质量最高的一份，与 star 数无关：每条规则带可用性底线 + 置信标签，并主动纠正 Apple 自己文档里的可用性错误 |
| 11 | 同上 `liquid-glass-motion/` | 同上 | 4 | 2026-08-09 | MIT | 玻璃动效：morphing、glassEffectID、相位/关键帧、滚动驱动、Metal、Reduce Motion | 1 | 2 | 3 | 3 | 2 | 11 | INCLUDE | 「morph 静默失效的四个前提」与「系统只降级自己的动效」两条是别处找不到的 |
| 12 | 同上 `apple-motion-feel/` | 同上 | 4 | 2026-08-09 | MIT | 动效手感启发式（单文件 8.5 KB） | 1 | 2 | 2 | 2 | 2 | 9 | INCLUDE（少量） | 相对姊妹 skill 偏薄，仅取「弹簧优先、时长+弹性参数化」并入 design-hig |
| 13 | AvdLee/Swift-Concurrency-Agent-Skill `skills/swift-concurrency/` | https://github.com/AvdLee/Swift-Concurrency-Agent-Skill | 1646 | 2026-08-12 | MIT | Swift 6 迁移、actor 隔离、Sendable、性能、Core Data、Observation | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE | 归档标 `pushed_at unverified`，本次核实为 2026-08-12（新鲜）；作者运营 swiftconcurrencycourse.com；「先读构建设置」与「Task 入口隔离对齐同步前缀」是最实用的两条 |
| 14 | twostraws/Swift-Concurrency-Agent-Skill `swift-concurrency-pro/` | https://github.com/twostraws/Swift-Concurrency-Agent-Skill | 528 | 2026-05-17 | MIT | 12 个参考：actors / structured / unstructured / cancellation / async-streams / bridging / interop / bug-patterns / diagnostics / hotspots / new-features / testing | 2 | 1 | 3 | 3 | 2 | 11 | INCLUDE | `bug-patterns.md` + `diagnostics.md` + `hotspots.md` 正是「模型实际会写错什么」，#13 无对应物 |
| 15 | twostraws/SwiftData-Agent-Skill `swiftdata-pro/` | https://github.com/twostraws/SwiftData-Agent-Skill | 406 | 2026-03-11 | MIT | @Model、关系与删除规则、谓词子集、索引、CloudKit、iOS 26 类继承 | 2 | 1 | 3 | 3 | 2 | 11 | INCLUDE | 归档标 unverified，本次核实推送 2026-03-11 = 5 个月 30 天，**刚好在 6 个月内**；抽查三条（`isEmpty == false` 运行时崩溃、`#Unique` 只能出现一次、CloudKit 禁用唯一约束）对照官方文档全部正确 |
| 16 | twostraws/Swift-Testing-Agent-Skill `swift-testing-pro/` | https://github.com/twostraws/Swift-Testing-Agent-Skill | 426 | 2026-05-17 | MIT | Swift Testing 核心规则、更好的测试、异步、新特性、XCTest 迁移 | 2 | 1 | 3 | 3 | 2 | 11 | INCLUDE | 归档标 unverified，本次核实通过（应急方案未触发）；「`#expect` 中前置感叹号会破坏宏展开」这类规则别处没有 |
| 17 | AvdLee/Swift-Testing-Agent-Skill `swift-testing-expert/` | https://github.com/AvdLee/Swift-Testing-Agent-Skill | 447 | 2026-08-07 | MIT | 期望、参数化、trait/tag、并行与隔离、异步等待、Xcode 工作流 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE | 归档清单未收录，本次补搜发现；比 #16 更新，并行与隔离一节补齐了 #16 的缺口 |
| 18 | dadederk/iOS-Accessibility-Agent-Skill `ios-accessibility/` | https://github.com/dadederk/iOS-Accessibility-Agent-Skill | 167 | 2026-03-09 | MIT | VoiceOver、Dynamic Type（UIKit+SwiftUI）、Voice Control、Switch Control、Full Keyboard Access、对比度、测试 | 2 | **0** | 3 | 3 | 2 | 10 | MAYBE → **reference** | 推送 2026-03-09 = 6 个月零 1 天，**新鲜度判 0**，按量表不得作为 merged 源。唯一覆盖 Voice Control / Switch Control / FKA 的候选，故降级为「主题清单」，正文全部依 Apple 官方文档重写 |
| 19 | Dimillian/Skills `swiftui-performance-audit/` 等 | https://github.com/Dimillian/Skills | 3951 | 2026-03-29 | MIT | Ice Cubes 作者的个人 skill 集：性能审计、UI 模式、并发专家 | 2 | 1 | 2 | 2 | 2 | 9 | INCLUDE（reference） | 归档标「许可 unverified」，本次核实为 **MIT**；但内容是个人杂集（同仓库含 react-component-performance），深度不及 #1/#2/#13，仅用于交叉验证性能排序 |
| 20 | dpearson2699/swift-ios-skills | https://github.com/dpearson2699/swift-ios-skills | 1092 | 2026-07-31 | NOASSERTION | ~86 个按框架切分的 skill（ActivityKit、AlarmKit、CarPlay、StoreKit、WidgetKit…） | 1 | 2 | 2 | 2 | 1 | 8 | INCLUDE（reference） | NOASSERTION 许可不明，只当作「小众框架覆盖图」核对本 skill 的范围声明有无遗漏，未读入任何文字 |
| 21 | rshankras/claude-code-apple-skills | https://github.com/rshankras/claude-code-apple-skills | 715 | 2026-07-24 | MIT | Apple 生命周期：产品验证、代码生成、App Store/ASO、ASC API、新鲜度 CI | 2 | 2 | 2 | 2 | 2 | 10 | INCLUDE（reference） | 其 SwiftUI 部分弱于 #1/#2；App Store / ASO 明确不在本批范围；其 `check-freshness.sh` 思路已由本仓库 `tools/check_upstream.py` 承接 |
| 22 | FloWritesCode/fwc-swiftui-skills | https://github.com/FloWritesCode/fwc-swiftui-skills | 90 | 2026-09-10 | MIT | 现代 SwiftUI + Liquid Glass（Cursor 取向） | 1 | 3 | 2 | 2 | 2 | 10 | REJECT | 全表最新且 MIT，但为扁平 `reference.md`（无 references/ 拆分），内容被 #10 完全覆盖且深度差一个数量级；合入只会重复 |
| 23 | n0an/App-Intents-Agent-Skill | https://github.com/n0an/App-Intents-Agent-Skill | 33 | 2026-09-08 | MIT | App Intents | 1 | 3 | 2 | 2 | 2 | 10 | REJECT（本 skill） | 质量合格但属独立主题；留给路线图的 `app-intents`，并入会撑爆本 skill 的 500 行预算 |
| 24 | conorluddy/ios-simulator-skill | https://github.com/conorluddy/ios-simulator-skill | 1245 | 2026-06-18 | MIT | 模拟器控制 | 1 | 1 | 2 | 2 | 2 | 8 | REJECT（本 skill） | 属 `xcode-tooling` 主题；本 skill 的 Instruments 脚本已覆盖性能侧的工具需求 |
| 25 | bocato/swift-testing-agent-skill | https://github.com/bocato/swift-testing-agent-skill | 80 | 2026-01-28 | MIT | Swift Testing | 1 | 0 | 2 | 2 | 2 | 7 | REJECT | 推送 2026-01-28，**超过 7 个月无更新**；#16/#17 更新更全 |
| 26 | vanab/swiftdata-agent-skill | https://github.com/vanab/swiftdata-agent-skill | 13 | 2026-02-08 | MIT | SwiftData | 0 | 0 | 2 | 2 | 2 | 6 | REJECT | 7 个月无更新 + 13 star；被 #15 完全覆盖 |
| 27 | vermont42/iOS-Design-Agent-Skill | https://github.com/vermont42/iOS-Design-Agent-Skill | 19 | 2026-03-22 | MIT | iOS/SwiftUI 设计评论 | 0 | 0 | 2 | 1 | 2 | 5 | REJECT | 单日仓库，建仓当天之后再无提交，距今 5.6 个月；4.7 MB 全是图片；设计侧已由 #1 的 design.md + Apple HIG 覆盖 |
| 28 | Nagarjuna2997/ios-agent-skill | https://github.com/Nagarjuna2997/ios-agent-skill | 32 | 2026-08-17 | MIT | 「生产级 iOS SwiftUI 指南」 | 0 | 2 | 1 | 1 | 2 | 6 | REJECT | 无可辨识作者背景，内容为教程式泛论，没有任何主流候选缺失的东西 |
| 29 | JordanCoin/ios-skills-collection | https://github.com/JordanCoin/ios-skills-collection | 5 | 2026-09-10 | NOASSERTION | `_router/` + 约 200 个「来自 28 位作者」的 skill | 0 | 3 | 1 | 1 | 0 | 5 | REJECT | 在不清晰的许可下再分发他人作品，正是本项目要避免的溯源风险；5 star |
| 30 | yigitkonur/plugin-swiftui | https://github.com/yigitkonur/plugin-swiftui | 1 | 2026-07-29 | NOASSERTION | 37 个 skill + MCP 工具，8.3 MB | 0 | 2 | 1 | 0 | 0 | 3 | REJECT | 1 star，许可不明，体量与声明不匹配且无法逐条核实 |
| 31 | conorluddy/marketplace | https://github.com/conorluddy/marketplace | 1 | 2026-09-04 | NONE | swift-accessibility / liquid-glass / ios-aso 三个 plugin | 0 | 3 | 1 | 1 | 0 | 5 | REJECT | 1 star、无 LICENSE 文件；Liquid Glass 侧被 #10 全面压制 |
| 32 | wei18/apple-dev-skills | https://github.com/wei18/apple-dev-skills | 19 | 2026-09-09 | MIT | 以 git submodule 聚合其它 Apple skill 仓库 | 1 | 3 | 1 | 2 | 2 | 9 | REJECT（作为源） | 本身不产生内容，聚合的正是本表已收录的上游；仅用作「有无遗漏上游」的交叉检查，结果无新增 |
| 33 | ApptitudeLabs/claude-code-ios-dev-setup | https://github.com/ApptitudeLabs/claude-code-ios-dev-setup | 6 | 2026-08-31 | NONE | Claude Code CLI 安装指南 | 0 | 2 | 1 | 1 | 0 | 4 | REJECT | 不是 Agent Skill，产物类型不符 |

## 深度审查

### 1. twostraws/SwiftUI-Agent-Skill（`swiftui-pro`）—— 本 skill 的骨架来源

结构：`swiftui-pro/SKILL.md`（4145 B）+ `references/` × 9（accessibility 2.4 KB、api 3.1 KB、data 3.0 KB、design 2.7 KB、hygiene 1.1 KB、navigation 1.3 KB、performance 2.8 KB、swift 4.1 KB、views 3.2 KB）。仓库另有 `swiftui-pro/skills/swiftui-pro/` 一份镜像，`references` 是符号链接——为同时兼容 Claude plugin 与裸 skill 目录两种布局。本仓库扁平结构不需要这个双份布局。

frontmatter：`name` / `description` / `license: MIT` / `metadata: {author, version}`。正文完全与 agent 无关，Claude 与 Codex 只出现在打包层。这是本表唯一已经接近我们 frontmatter 规范的候选。

质量：刻意做小（全部参考约 35 KB）。九步编号评审流程，每步只点名一个参考文件，结尾一句「若只做局部评审，只加载相关参考」。Core Instructions 把 iOS 26 钉为新 App 默认部署目标、Swift 6.2+、SwiftUI 优先于 UIKit、未经询问不得引入第三方框架、一个类型一个文件。**它是唯一给出精确 OUTPUT FORMAT 的候选**（文件 → 行号 → 规则名 → before/after → 按影响排序的总结），并附三条示例。本 skill 的 `## Output format` 直接沿用这套形状并重写示例。

与 #2 的关系：主题完全重叠，深度互补——twostraws 是 4 KB 清单，AvdLee 是 27 文件资料库。

### 2. AvdLee/SwiftUI-Agent-Skill（`swiftui-expert-skill`）—— 参考体量与工具链来源

结构：`SKILL.md`（12270 B）+ `references/` × 27 + `scripts/{record_trace.py, analyze_trace.py, instruments_parser/×11}`（约 2400 行 Python）。仓库还带 `.claude-plugin/`、`.codex-plugin/`、`.cursor-plugin/`、README 同步 workflow。

值得抄的模式：

- **「每次任务先读 latest-apis.md」**——本领域杠杆最高的一条规则，直接压制弃用 API 幻觉。本 skill 的 `## Read first` 就是它。
- **任务形态化的工作流**（review / improve / implement / record-a-trace / trace-driven-improvement），而不是只有一条评审流程。
- **Correctness Checklist**：约 15 条「违反即 bug」的不变量。本 skill 的 Core rules 以它为主干。
- **27 行 Topic Router 表**——token 延迟加载机制。
- **Instruments 集成**：`record_trace.py --list-devices/--attach/--stop-file`，带「模拟器上 SwiftUI 泳道为空，改用 Time Profiler」这个只有实测过才知道的注意事项；`analyze_trace.py --window/--fanin-for/--json-only`，以及解读规则（`main_running_coverage_pct` <25% 为阻塞、≥75% 为 CPU-bound；`swiftui-causes.top_sources` 中高边数的 `UserDefaultObserver.send()` 或 `EnvironmentWriter` 是结构性失效 bug）。
- **明确的不强制条款**：「不要强制特定架构（MVVM、VIPER）」「性能优化以建议形式给出」。本 skill 的 Scope 保留了这两条。

agent 绑定：仅 `${SKILL_DIR}` 一处。本 skill 改为相对路径 + 一句 "Paths below are relative to this skill's directory."。

### 3. superagents-lab/xcode27-skills —— 正确性裁决方

`swiftui-specialist/SKILL.md` 只有 3508 B，但撑着极大的参考：`dataflow.md` 31.6 KB、`environment.md` 40.0 KB，另有 structure / modifiers / foreach / localization / animations / soft-deprecation / soft-deprecated-apis。开篇一句「本指导由 Apple 撰写并发布，无条件覆盖模型此前的任何训练」。

它的内容精度是全表最高的，几个别处没有的点已并入本 skill：

- 计算属性 **不** 构成失效边界，因此「把 body 拆成 `private var header: some View`」这个训练数据里最常见的形状是错的；必须拆成独立 `View` struct（`swiftui-views-modifiers.md`）。
- `@Observable` 的依赖粒度是**存储属性**，不是属性内的字段；计算属性会**传递**依赖，包一层不会收窄（`swiftui-data-flow.md`）。
- 环境闭包无法比较 → 每次环境写入都让整棵子树失效；把闭包包进 struct 不是修法；框架自带的 `\.openURL` 等不适用此规则。
- `@Entry` 默认值必须稳定，否则不相关的环境写入也会触发失效。
- 单子视图 `Group` 会白白多一层类型，拖慢类型检查。
- soft-deprecation 的**行为规则**（只讨论你改动的视图；同文件其它视图一个字都别提），这一条决定了 agent 评审的噪音水平。
- iOS 27：`@State` 宏化后的三类编译错误，且「重排 init 赋值」是**错误**修法。

许可：README 明示 Apple 保留全部权利、本仓库不授予任何许可。按 `AGENTS.md` 的宽松策略（无许可但公开 → 可署名合入）作 `merged`，`notes` 写明无授权。**未复制任何原文**，全部改写。

### 4. YordiLorenzo/liquid-glass-skills —— 全表工程质量最高

三个姊妹 skill：`liquid-glass/` + 10 参考、`liquid-glass-motion/` + 7 参考（约 100 KB）+ `scripts/`、`apple-motion-feel/` 单文件。

description 本身就是工程范例：除了 API 名，还把**失败症状**列为触发词（"glass renders dark or muddy"、"glass button doesn't register taps"、编译错误原文），并显式交接给姊妹 skill。

质量：每条规则带**可用性底线**与**置信标签**（`[verified]`/`[apple]`/`[multi]`/`[single]`/`[version-pinned]`），并声明成文时间。它主动纠正了「包括 Apple 自己文档在内的多数已发布材料」中的可用性错误——例如 Apple 渲染文档为 glass 符号显示 "visionOS 1.0"，而 SDK 标注 `@available(visionOS, unavailable)`。它还给出了一份**「不存在的 API」清单**，其中 `scrollExtensionMode(.underSidebar)` 出自 **Xcode 27 自带的 model-context 文档**并附完整示例代码——由此得出一条采信规则：Xcode 内置的面向 LLM 文档不权威。这一整套本 skill 全数继承。

溯源注意：`liquid-glass-motion/scripts/` 是 AvdLee 解析器的衍生物，带 `ATTRIBUTION.md` 与内嵌的 AvdLee LICENSE。若同时合入 #2 与本项会带两份解析器——本 skill 只保留一份（源自 AvdLee 的谱系，且已重写精简），两位作者都进 `SOURCES.yaml`。

### 5. AvdLee/Swift-Concurrency-Agent-Skill 与 twostraws/Swift-Concurrency-Agent-Skill

AvdLee（1646★，2026-08-12）：`Fast Path` 要求先读 `Package.swift` / `.pbxproj` 判定语言模式、严格并发级别、默认隔离与 upcoming features——**这是并发建议正确与否的前提**，其它候选都没有。另有「Task 入口隔离要对齐同步前缀」这一非常具体的判据，以及 12 行诊断 → 最小安全修法表。

twostraws（528★，2026-05-17）：参考拆分最干净的一份。`hotspots.md`（grep 目标）、`bug-patterns.md`（模型实际会写错的失败模式）、`diagnostics.md`（strict-concurrency 编译错误 → 修法）、`new-features.md`（Swift 6.2：默认主 actor 隔离、全局 actor 隔离的一致性、`nonisolated` async 留在调用者 actor、`@concurrent`、`Task.immediate`、`isolated deinit`、任务命名与优先级升级）。AvdLee 无对应物。

两者拆成本 skill 的 `swift-concurrency.md`（隔离/Sendable/结构化/迁移）与 `swift-concurrency-bugs.md`（grep 目标 + 失败模式 + 诊断 + 测试）。

### 6. twostraws/SwiftData-Agent-Skill

`swiftdata-pro/` + 5 参考（core-rules、predicates、indexing、cloudkit、class-inheritance）。定位明确写着「LLM 实际会犯的错」。最有价值的是**编译通过但运行时崩溃**的那一类：`$0.cast.isEmpty == false` 崩溃而 `!$0.cast.isEmpty` 正常；对计算属性 / `@Transient` / 自定义 `Codable` 结构体建谓词会崩；正则表达式谓词会崩。这类事实无法从 API 签名推出，正是 skill 的价值所在。抽查三条对照 Apple 文档全部正确，正确性给 3。

### 7. dadederk/iOS-Accessibility-Agent-Skill —— 降级为 reference 的理由

结构：`ios-accessibility/` + 17 参考，按「核心概念 / UIKit 实现 / SwiftUI 实现」三段式切分 VoiceOver 与 Dynamic Type，另有 voice-control、switch-control、full-keyboard-access、testing-manual、testing-automated。

内容质量确实高：「无障碍是非确定性的，按置信度排序给方案并说明取舍」这个 Agent Behavior Contract 是全表独一份；反模式清单（标签里不要写 trait 名、别给交互元素加 `accessibilityHidden`、导航栏/工具栏不要跟随 Dynamic Type 放大而应使用 Large Content Viewer）非常具体；`accessibilityUserInputLabels` 用于 Voice Control 的说明是本领域几乎无人提及但价值极高的一条。

**但它的最近推送是 2026-03-09，距调研日 6 个月零 1 天。** 按量表新鲜度判 0，且它不是官方厂商，因此不满足「>6 月直接 REJECT 除非官方」的例外。裁决：不作为 merged 源，降级为 `relation: reference`，**只用它的主题清单决定 `accessibility.md` 要覆盖什么**；正文全部依据 Apple 无障碍官方文档与 WCAG 2.2 重写。这样既不丢覆盖面，也不违反量表。

### 8. AvdLee/Swift-Testing-Agent-Skill —— 补搜新增

归档清单未收录。本次按「同一作者的姊妹仓库」思路补搜发现：447★、2026-08-07 推送、MIT，比 twostraws 的测试 skill 更新。9 个参考中 `parallelization-and-isolation.md` 与 `async-testing-and-waiting.md` 补齐了 twostraws 版本的缺口（并行默认、共享夹具隔离、如何用可等待条件替代 sleep）。两者一并 merged。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| A1 | Liquid Glass 采用尺度 | AvdLee：「仅在用户明确要求时采用 Liquid Glass」；twostraws：「iOS 26 存在，且是新 App 的默认部署目标」；YordiLorenzo：优先用自动获得玻璃的系统组件，自定义 `glassEffect` 只给独特元素 | **新建 iOS 26+ 代码通过系统组件（工具栏 / 标签栏 / 表单 / 搜索 / 分栏侧边栏）自动获得玻璃；向既有 App 添加自定义 `glassEffect` 表面必须由用户明确要求。** 两条都写进 Core rules（14）与 `liquid-glass.md` 的 Adoption stance | 三方主张并不真冲突：twostraws 说的是部署目标，AvdLee 说的是自定义表面。拆开表述即消解。系统组件重编译即获玻璃是 Apple 官方立场 |
| A2 | 默认部署目标 | twostraws 钉 iOS 26；Apple 的 whats-new-27 已在讲 iOS 27 API | **默认 iOS 26**，iOS 27 API 一律标注 `(iOS 27+)` 并要求门控 | 当日读 developer.apple.com 的 iOS/iPadOS 发行说明：26.6 为已发布最新版，27 处于 RC。已写入 `latest-apis.md` 顶部 `Verified against:` |
| A3 | 是否强制架构 | AvdLee 明确「不要强制 MVVM/VIPER」；多数低分候选推销分层架构 | **不强制**，只鼓励把逻辑与视图分离以便测试 | 官方厂商 > 专家 > 社区；Apple 自己也从不规定应用架构。写进 Scope |
| A4 | 性能优化的语气 | AvdLee：「性能优化以建议形式给出，不是要求」；部分候选把性能规则写成硬性 | **除非用户要求做性能专项，否则性能条目按建议给出**；但「失效来源」类结构性 bug 仍进 Core rules | 过度重构可读性代价高；`swiftui-performance.md` 开头明写这条 |
| A5 | 计算属性拆分视图 | twostraws：强烈建议拆成独立 `View` struct（理由：可读性 + 效率）；Apple：**理由是失效边界**，计算属性被内联进父 body，完全不减少更新成本 | 采用 **Apple 的理由**表述：这是更新成本缺陷，不是可读性偏好 | 官方厂商 > 专家。理由不同会导致 agent 的评审严重度判断不同，必须统一 |
| A6 | Instruments 脚本来源 | AvdLee 原版（约 2400 行、11 个模块）；YordiLorenzo 的衍生版（带 ATTRIBUTION + 内嵌 LICENSE） | **只保留一份**，谱系取 AvdLee，并**重写精简为 4 个模块**；`SOURCES.yaml` 同时列出 AvdLee（merged）与 YordiLorenzo（merged），NOTICE 由此同时署名两人 | 避免同一解析器在仓库里存在两份；YordiLorenzo 的贡献是在其材质/动效内容，脚本本身是衍生 |
| A7 | 无障碍触控目标尺寸 | 社区材料常把 44×44 pt 当成通用规则并套到 macOS | **触摸平台 44×44 pt（Apple iOS 指南）；WCAG 2.2 AA SC 2.5.8 是 24×24 CSS px；macOS 不适用，标准常规控件约 28 pt** | YordiLorenzo 已指出「Mac 上的 44 pt」是错误移植；WCAG 数值查 W3C 原文。三个数字分别标注适用范围，写进 `accessibility.md` 与 `design-hig.md` |
| A8 | visionOS 上的 Liquid Glass | 社区常见「visionOS 不支持任何玻璃 API」的一刀切；Apple 渲染文档又显示 "visionOS 1.0" | **按符号区分**：`glassEffect` / `GlassEffectContainer` / `glassEffectID` / `Glass` / 玻璃按钮样式 / `scrollEdgeEffectStyle` 在 visionOS 不可用；`backgroundExtensionEffect` / `ConcentricRectangle` / `tabBarMinimizeBehavior` 可用。文档与 SDK 冲突时以 SDK 为准 | YordiLorenzo `[verified]` 级核实；一刀切会让 agent 拒绝生成 visionOS 上本可用的 API |
| A9 | `@unchecked Sendable` 的定位 | AvdLee：需要文档化不变量与移除计划；twostraws：不要用它修编译错误，唯一正当用途是内部加锁且可证明线程安全的类型 | 合并为一条 Core rule（19）+ `swift-concurrency.md` 的 Escape hatches 节，采用 twostraws 更严格的表述并保留 AvdLee 的「文档化不变量 + 移除计划」要求 | 两者不冲突，取交集更强的版本 |
| A10 | `Task {}` 与取消传播 | twostraws `bug-patterns`：循环里的非结构化 task「没有取消传播」 | 表述为「没有取消传播、没有错误收集、没有完成信号」，修法是 task group | 基线评测中模型实测指出 `Task {}` 与 `Task.detached` **都**不参与父任务取消传播，与该表述一致；措辞避免暗示 `Task {}` 有传播 |
| A11 | Swift Testing 覆盖 UI 测试 | 部分材料暗示 Swift Testing 可全面替代 XCTest | **Swift Testing 不支持 UI 测试**，`XCUIApplication` + `XCTestCase` 是当前唯一选项，且这不是遗留选择 | twostraws 与 AvdLee 的测试 skill 一致，Apple 文档亦然。写进 `testing.md` 的 Scope 与 UI tests 节 |
| A12 | 是否合入 App Store / 模拟器 / 安全设置等主题 | rshankras、conorluddy、superagents-lab 各自提供了这些主题的优质内容 | **全部排除**，留给路线图的 `xcode-tooling` / `app-store-connect` | 本 skill 的 description 触发面已经很宽，继续扩张会让 SKILL.md 突破 500 行预算并稀释触发精度 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| twostraws-swiftui | twostraws/SwiftUI-Agent-Skill `swiftui-pro/` | merged | 九步评审顺序、Core Instructions、输出格式与示例、views/data/navigation/design/accessibility/performance/swift/hygiene 各条规则 |
| avdlee-swiftui | AvdLee/SwiftUI-Agent-Skill `skills/swiftui-expert-skill/` | merged | Correctness Checklist、Topic Router 模式、read-first 弃用索引、本地化/滚动/焦点/动画、Instruments 录制与分析工作流及解读规则 |
| avdlee-update-apis | 同仓库 `.agents/skills/update-swiftui-apis/` | reference | 弃用索引的重扫方法论，用于本 skill 的同步流程；未复制内容 |
| yordi-liquid-glass | YordiLorenzo/liquid-glass-skills `liquid-glass/`、`liquid-glass-motion/`、`apple-motion-feel/` | merged | 玻璃硬规则 + 可用性底线 + 置信标签、可用性纠错表、不存在的 API 清单、迁移卫生、morph 四前提、Reduce Motion 门控、Metal 约束 |
| apple-xcode27 | superagents-lab/xcode27-skills `swiftui-specialist/`、`swiftui-whats-new-27/`、`uikit-app-modernization/`、`test-modernizer/` | merged | 视图失效边界、数据流粒度、环境比较、ForEach identity、条件修饰符禁令、soft-deprecation 行为规则、iOS 27 破坏性变更、UIKit 场景生命周期 |
| avdlee-concurrency | AvdLee/Swift-Concurrency-Agent-Skill `skills/swift-concurrency/` | merged | 构建设置摄取表、Task 入口隔离、最小安全修法阶梯、并发工具选择表、Swift 6 迁移验证循环 |
| twostraws-concurrency | twostraws/Swift-Concurrency-Agent-Skill `swift-concurrency-pro/` | merged | grep 目标、失败模式目录、strict-concurrency 诊断映射、Swift 6.2 行为变更 |
| twostraws-swiftdata | twostraws/SwiftData-Agent-Skill `swiftdata-pro/` | merged | 模型与关系规则、临时持久化 ID、谓词子集（含编译通过但运行时崩溃的一类）、索引、CloudKit、iOS 26 类继承 |
| twostraws-testing | twostraws/Swift-Testing-Agent-Skill `swift-testing-pro/` | merged | Swift Testing 约定、期望规则、参数化陷阱、`withKnownIssue` 语义、XCTest 映射表 |
| avdlee-testing | AvdLee/Swift-Testing-Agent-Skill `swift-testing-expert/` | merged | 异步测试与等待、并行与隔离、trait/tag、XCTest 在 UI 测试上的边界 |
| dadederk-a11y | dadederk/iOS-Accessibility-Agent-Skill `ios-accessibility/` | reference | Voice Control / Switch Control / Full Keyboard Access 的主题清单与非确定性框架；正文依 Apple 文档重写 |
| dimillian-skills | Dimillian/Skills `swiftui-performance-audit/` 等 | reference | 上架 App 视角的性能分诊顺序，用于校验本 skill 的优先级排序 |
| dpearson-swift | dpearson2699/swift-ios-skills | reference | 小众框架覆盖图，仅用于检查 Scope 声明有无遗漏 |
| rshankras-apple | rshankras/claude-code-apple-skills | reference | 新鲜度 CI 思路；确认 App Store / ASO 不进本 skill |
| apple-docs | developer.apple.com（`kind: docs`） | merged | 全部版本底线、API 拼写、无障碍数值的正确性裁决方，含用于确定默认部署目标的 iOS/iPadOS 发行说明 |

## 基线缺口

`uv run tools/run_evals.py apple --baseline`。场景 1 首轮四条 `expected_behavior` 全部达成 —— **评测无区分度**，据此改写：夹具 `Row.swift` 改为让 `header`/`footer` 计算属性真正被 `body` 使用（首轮它们是死代码，模型只会报「未使用」而不会触及失效边界规则），并加入在 `body` 内构造的 `Binding(get:set:)`；第 4 条期望拆成两条更具体的规则。下表为改写后的基线结果。

两种模型各跑一遍无 skill 基线（默认模型与 `@smol`），逐条人工判定。

| 场景 | 模型 | 未达成的行为 | 说明 |
|---|---|---|---|
| 1 Row.swift 评审 | default | **EB4**：`header` / `footer` 计算属性的失效边界 | 只把两者当作 Liquid Glass 适配点（建议改 `.searchable` / `.safeAreaBar`），完全没有触及「计算属性被内联进父 body、不构成失效边界、必须拆成独立 `View` struct」这条规则 |
| 1 Row.swift 评审 | default | **EB3 部分**：输出格式 | 有 `Row.swift:20` 这类 file:line，但只在文末给一份整文件改写版，没有逐条 before/after 代码对 |
| 1 Row.swift 评审 | @smol | **EB4**：同上 | 完全未提及 `header` / `footer`；连它们存在都没写 |
| 1 Row.swift 评审 | @smol | **EB3 部分**：同上 | 同样是「表格 + 文末整段修正版」，非逐条 before/after |
| 2 GlassPanel.swift 评审 | default | **EB2**：`opacity < 1` 让折射静默塌陷 | 明确写「HIG 里我**没有**检索到禁止对 glass 用 opacity 的绝对规则……按强建议、不按文档禁令陈述」，把它降级成去强调的样式取舍 |
| 2 GlassPanel.swift 评审 | @smol | **EB2**：同上 | 直接改写了文件，把 `.opacity(isDimmed ? 0.6 : 1)` **保留在玻璃子树内**（只是挪到 `glassEffect` 之前）并加注释「暗化作用于内容」；折射照样塌陷，规则未被识别 |
| 3 FeedLoader.swift 评审 | default | **EB1 部分**：`cached[id]` 强解包 | 命中了 actor 去重问题（「actor 只保证互斥不保证去重」），但最终答复未指出挂起期间被清空导致强解包崩溃这一条 |
| 3 FeedLoader.swift 评审 | @smol | 无（四条全达成） | 该场景对 `@smol` 无区分度；区分度由场景 1、2 提供 |
| 4 Flutter 负例 | default / @smol | 无（`skill_read == false`，按 Flutter 惯例作答） | 负例行为符合预期 |

结论：场景 1 的 EB4 与场景 2 的 EB2 在**两种模型的基线下都未达成**，是本 skill 要填补的核心缺口。首轮评测中场景 1 四条全部达成、无区分度，已按 `docs/workflow.md` 要求改写夹具与期望（见本节开头）。

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Row.swift | default | 无 | false | EB1 ✔ EB2 ✔ EB3 ◐ EB4 ✘ EB5 ✔ | 失效边界规则完全缺席 |
| 1 Row.swift | default | 有 | **true** | EB1 ✔ EB2 ✔ EB3 ✔ **EB4 ✔** EB5 ✔ | 「Line 55+63：`header`/`footer` 是计算属性，会被内联进父 body……只有真正的 `View` 类型才引入新的失效边界」；输出严格按 `## Output format` 的 file → line → 规则 → before/after → 排序总结 |
| 1 Row.swift | @smol | 无 | false | EB1 ✔ EB2 ✔ EB3 ◐ EB4 ✘ EB5 ✔ | 同上 |
| 1 Row.swift | @smol | 有 | **true** | EB1 ✔ EB2 ✔ EB3 ✔ **EB4 ✔** EB5 ✔ | 「Lines 55 and 63: `header` and `footer` are computed properties, so they do not introduce an invalidation boundary」；另外主动声明「未发现的伪问题」，噪音更低 |
| 2 GlassPanel.swift | default | 无 | false | EB1 ✔ EB2 ✘ EB3 ✔ EB4 ✔ | 显式否认 opacity 规则的存在 |
| 2 GlassPanel.swift | default | 有 | **true** | EB1 ✔ **EB2 ✔** EB3 ✔ EB4 ✔ | 「玻璃视图上的 `opacity < 1` 会让折射静默塌陷……能编译、能渲染，只是不再像玻璃」；另额外命中 `allowsHitTesting` 无效、纯黑背景、`scaleEffect` 缩放已合成材质 |
| 2 GlassPanel.swift | @smol | 无 | false | EB1 ✔ EB2 ✘ EB3 ✔ EB4 ✔ | 把 opacity 留在玻璃子树内 |
| 2 GlassPanel.swift | @smol | 有 | **true** | EB1 ✔ **EB2 ✔** EB3 ✔ EB4 ✔ | 「玻璃视图（或其任意祖先）不得设置 `opacity < 1`……折射会静默失效」，并给出把变暗移到背景层的修法 |
| 3 FeedLoader.swift | default | 无 | false | EB1 ◐ EB2 ✔ EB3 ✔ EB4 ✔ | 未提强解包崩溃 |
| 3 FeedLoader.swift | default | 有 | **true** | **EB1 ✔** EB2 ✔ EB3 ✔ EB4 ✔ | 「actor 重入 —— check-then-act 跨 `await`，外加 `await` 之后强解包」；本轮还自建临时 SwiftPM 包实测「原实现 10 次下载、去重版 1 次」 |
| 3 FeedLoader.swift | @smol | 无 | false | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ | 该场景对 `@smol` 无区分度 |
| 3 FeedLoader.swift | @smol | 有 | **true** | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ | 额外命中 `Task.sleep(nanoseconds:)` → `Task.sleep(for:)`、`CancellationError` 先于错误分支处理，并按 skill 的迁移循环给出「先清一类再重编译」的顺序 |
| 4 Flutter 负例 | default | — | **false** | EB1 ✔ EB2 ✔ | 明确写「本仓注册的 `apple` skill 写了 Do not use for Flutter，所以我没加载它」，随后按 Flutter 惯例评审 |
| 4 Flutter 负例 | @smol | — | **false** | EB1 ✔ EB2 ✔ | 「the `apple` skill explicitly excludes Flutter, so it doesn't apply here」 |

图例：✔ 达成 / ◐ 部分达成 / ✘ 未达成。

结论：**两种模型都通过**。

- **默认模型**：基线未达成的 EB（场景 1 的 EB4、场景 3 的 EB1、场景 1 的 EB3 输出格式）在有 skill 时全部达成；场景 2 的 EB2 从「明确否认该规则存在」翻转为「按硬规则报告并给出修法」。
- **`@smol`**：基线未达成的 EB（场景 1 的 EB4 与 EB3、场景 2 的 EB2）在有 skill 时全部达成。`@smol` 有 skill 的输出质量与默认模型基线相当甚至更整齐（主动列出「未发现的伪问题」），说明 skill 对弱模型的抬升更明显。
- **负例**：两种模型的 `skill_read` 均为 `false`，且都是**读了 description 的否定边界后主动拒载**，而不是没被触发 —— description 的 `Do not use for Flutter or React Native apps` 起了作用。
- **触发**：三个正例在两种模型下 `skill_read` 均为 `true`。

## 备注

- **许可红线**：`apple-xcode27` 的上游 README 明示 Apple 保留全部权利、不授予许可。按 `AGENTS.md` 宽松策略以 `relation: merged` + `license: NONE` + `notes` 声明合入，**未复制任何原文**，全部规则以自己的话重写。若后续项目策略收紧，此条应最先降级为 `reference`，届时 `swiftui-data-flow.md` / `swiftui-views-modifiers.md` / `swiftui-lists-foreach.md` 需改由 Apple 官方文档重写。
- **`dadederk-a11y` 的复查触发条件**：一旦其推送时间刷新到 6 个月内，可将 `relation` 提升为 `merged` 并把其 UIKit 侧实现细节并入 `accessibility.md`。
- **脚本谱系**：`scripts/instruments_parser/` 是 AvdLee 解析器的重写精简版（11 模块 → 4 模块：`xctrace` / `xml` / `lanes` / `report`），保留 `--list-devices`、`--attach`、`--stop-file`、`--template` 与 `--window`、`--fanin-for`、`--json-only`、`--list-runs`、`--list-logs`、`--list-signposts` 的全部语义，并补上了上游没有的可执行前置检查（`xctrace` 不在 PATH、输出路径已存在、stop-file 已存在、系统级录制未确认）。本机为 Linux，无 `xctrace`，只做 `py_compile` 与 `--help` 冒烟 + 错误路径冒烟；SKILL.md 与 `swiftui-performance.md` 均注明仅 macOS 可运行。
- **未来同步要盯的上游**：`apple-xcode27`（Apple 每个 Xcode 大版本会更新导出内容，是弃用索引与 iOS 新版本破坏性变更的第一来源）、`avdlee-swiftui`（`latest-apis.md` 与 Instruments 脚本）、`yordi-liquid-glass`（版本钉死的 bug 条目需随 OS 更新复查）。
- **放弃的方向**：App Store / ASO、模拟器与设备交互、Xcode 构建设置安全审计、C `-fbounds-safety`、App Intents / WidgetKit 等单框架主题 —— 均见路线图，不进本 skill。
