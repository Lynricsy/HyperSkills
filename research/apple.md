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

## 2026-09-29 上游同步

漂移报告中本 skill 只有 `avdlee-swiftui` 一条 `behind`（列出了 paths 下的具体提交，非 too-large 归因）；
`avdlee-update-apis`、`avdlee-concurrency` 为 repo moved / tracked paths unchanged，其余 OK，`apple-docs` 为
manual check。`--pin` 后核对：`avdlee-swiftui` 写入 9808b06，与本次审阅的 HEAD 一致。

### avdlee-swiftui（4c6a97d → 9808b06，paths: `skills/swiftui-expert-skill`）

区间内 11 个触及 paths 的提交：58fbb4d（弃用 API / ForEach / typo 修复）、94fac4e 与 eb2c49d（Xcode 27 指南及按主题重组）、
dbe7b3a / ee97b1f（Xcode 27.1）、6702cf7（可缩放布局）、6572a7f（iPhone Duo）、d074948 / 1e522cf / e4fb5a4（大屏分类与重排）、
065d3ba（合并 PR #81）。变更文件 24 个，新增 `document-apps.md`、`environment-patterns.md`、`iphone-duo.md`、
`modifier-patterns.md`、`styled-text-editing.md`、`toolbar-patterns.md`、`webkit-integration.md`。

所有 API 事实均用 Apple 文档 JSON（`developer.apple.com/tutorials/data/documentation/swiftui/…`）逐条核对，不采信上游转述：

| 上游变更 | 判定 | 处理 |
|---|---|---|
| `liquid-glass.md`：签名改为 `glassEffect(_:in: some Shape = DefaultGlassEffectShape())`，删去 `isEnabled:` | **更正** | 文档确认 `DefaultGlassEffectShape` 是 iOS 26 的真实 struct，且只有 `glassEffect(_:in:)` 一个重载。本 skill 原把 `DefaultGlassEffectShape` 列入「不存在的 API」、并建议用 `isEnabled:` 参数——两处都是错的，已改：删除该行，写明签名；关闭玻璃改用 `.identity` |
| `latest-apis.md`：`navigationBarHidden` → `toolbarVisibility` 标 iOS 18，旧版保留在回退分支 | **更正** | 文档：`toolbarVisibility(_:for:)` iOS 18，`toolbar(_:for:)` iOS 16（27 SDK 已标弃用）。原表 floor 写 iOS 15，已改 |
| `latest-apis.md`：`toolbarBackground(_:for:)` 仅 `Visibility` 重载弃用 | **更正** | 文档：`ShapeStyle` 重载未弃用。原表未区分，已改 |
| `latest-apis.md`：`@Animatable` 仅替代 1:1 转发的 `animatableData`，含钳制/归一化的保留手写 | 更正（细化） | 已改表格该行 |
| `sheet-navigation-patterns.md`：SDK 27 `alert`/`confirmationDialog` 的 `item:` 重载回部署到 iOS 15，无需运行时门控 | **更正** | 文档两者 introducedAt 均为 iOS 15 / macOS 12 / tvOS 15 / watchOS 8 / visionOS 1。原文把它放在「iOS 27 一律 gate」的列表里，已加例外说明 |
| `iphone-duo.md`、`layout-best-practices.md`、`sheet-navigation-patterns.md`：大屏/可折叠屏按屏幕结构选技术、双列重排、`ArrangementView`（27.1 beta）、`reservedRegions`、`onHingeChange` 只做效果 | 新增 | 基线实测大部分已会，只合入基线未达成的「重排保持单列阅读 / VoiceOver 顺序、辅助功能字号回单列」及嵌套限制、hinge 仅效果的简短规则（`design-hig.md` 一条） |
| `latest-apis.md` 等：SDK 27 软弃用补充（`AnimatableModifier`、`statusBarHidden` → `toolbarVisibility(_:for: .statusBar)`、`PresentationMode` 等） | 新增 | 基线全部已会（场景 6 EB1–EB3、EB6），**未合入** |
| `state-management.md`：`@State` 宏的一次性播种写法 | 新增 | 基线已会（场景 6 EB4），未合入；原「按迁移诊断修」表述保留 |
| `document-apps.md`、`webkit-integration.md`、`styled-text-editing.md`、`toolbar-patterns.md`、`environment-patterns.md`、`modifier-patterns.md`、`list-patterns.md`（reorder / swipeActionsContainer）、`image-optimization.md`（displayScale、AsyncImage 缓存） | 新增 / 重组 | 本 skill 已由 `apple-xcode27` 等覆盖 `ReadableDocument`、`WebView`、`reorderable`、`swipeActionsContainer`、`AsyncImage(request:)`、`@Entry` 默认值、`.if` 修饰符等；displayScale 基线已会（场景 5 EB5）。未合入新文件 |
| 其余：`focus-patterns.md`、`macos-*.md`、`performance-patterns.md`、`view-structure.md` 措辞、`agents/openai.yaml` | 噪声 / 重组 | 不改 |

### 评测（`workbuddy/deepseek-v4.1-flash`、thinking `max`，基线与有 skill 同模型）

新增场景 5（iPhone Duo 适配，夹具 `LibraryScreens.swift`）与场景 6（Xcode 27 迁移评审，夹具 `Legacy27.swift`）。

| 场景 | 模式 | skill_read | 结果 | 证据摘录 |
|---|---|---|---|---|
| 5 iPhone Duo | 基线 | false | EB1 ✔ EB2 ◐ EB3 ✔ EB4 ✔ EB5 ✔ EB6 ✔ | 基线查了 Apple 文档与 Tech Talk；卡片用按容器宽度的 `LazyVGrid`（折痕时偶数列），未考虑阅读 / VoiceOver 顺序与辅助功能字号 |
| 5 iPhone Duo | 有 skill | **true** | EB1 ✔ **EB2 ✔** EB3 ✔ EB4 ✔ EB5 ✔ EB6 ✔ | 自定义 `CardColumnsLayout`，「视觉顺序 = 阅读顺序 = VoiceOver 顺序 = 单列顺序」，`dynamicTypeSize.isAccessibilitySize` 时强制一列；「`onHingeChange` 只该驱动可选效果，绝不能拿来算布局」 |
| 6 Xcode 27 迁移 | 基线 | false | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ EB5 ◐ EB6 ✔ | `item:` 重载只作「可选简化」，并称「文档页标 iOS 15+，但 … 仍写 27 → 采纳前在本地 SDK 核对」，保留 `isPresented` + `presenting:` |
| 6 Xcode 27 迁移 | 有 skill | **true** | EB1–EB4 ✔ **EB5 ✔** EB6 ✔ | 「`confirmationDialog(_:item:…)` … 需要 27 SDK 才能编译，但回部署到 iOS 15，所以 iOS 17 目标不需 gate」 |

结论：两个场景都通过 D2（基线未达成 / 部分达成的一条在有 skill 时达成）。负例（场景 4）未改 description / Scope，未重跑。
输出目录：`/tmp/hs-evals-sync/SyncG3/apple-b5`、`apple-b6`（基线）、`apple-s5`、`apple-s6`（有 skill）。

遗留风险：`ArrangementView`、`ReservedRegion`、iPhone Duo 相关 API 在 Apple 文档中仍标 beta（iOS 27.1），
正式版语义可能变化，下次同步需复核；液态玻璃两处更正只删除了错误说法、补写签名，覆盖该主题的场景 2
本次未重跑。

## 2026-10-15 上游同步

依据：2026-10-15 `check_upstream.py --json`（`/tmp/hs-upstream.json`）与归因清单 `/tmp/hs-attr/attribution.md`，两条
`behind`：twostraws-swiftui、avdlee-swiftui；avdlee-update-apis 为「tracked paths unchanged」，随 `--pin` 前移。
归因方法：`gh api repos/<o>/<r>/compare/<pinned>...<head>` 读 tracked paths 的完整 patch。事实核对只用一手来源：
`swiftlang/swift` 源码（`gh api`）、developer.apple.com 的文档 JSON（`/tutorials/data/documentation/…json`）与
iOS & iPadOS 27 发行说明。`--pin` 后 `pin_check.py` 输出 `PIN CHECK CLEAN`。

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| twostraws-swiftui | be297ff → f980071（1 提交：f980071「Updated for Xcode 27.2 and iPhone Duo」，2.0.0） | Core Instructions：iOS 27 为新 App 默认部署目标、Swift 6.4、Xcode 27.1 可用、先读部署目标再给版本相关建议 | **状态更新**：2026-09-10 裁决 A2 定 iOS 26 的理由是「iOS 27 处于 RC」。复核：Apple 发行说明索引已列 iOS & iPadOS 27 与 27.2；`swiftlang/swift` 有 `swift-6.4.0-RELEASE`（2026-09-15），`utils/availability-macros.def` 中 `SwiftStdlib 6.4: anyAppleOS 27.0`；Xcode 27.1 发行说明含 iOS 27.1 SDK 与 Swift 6.4。据此把 Scope 与 `latest-apis.md` 的默认目标改为 iOS 27（Xcode 27 / Swift 6.4），「既有项目保持部署目标、更新的 API 门控」不变 |
| 同上 | 同上 | `api.md`：`ForEach(items.enumerated(), …)` 标为 iOS 26+，更早目标保留 `Array(...)` | **事实更正**：本 skill `latest-apis.md` 与 `swiftui-lists-foreach.md` 写「Swift 6.1 起 `enumerated()` 条件遵循 `RandomAccessCollection`」且无 OS 限制。`swiftlang/swift` `stdlib/public/core/EnumeratedSequence.swift` 的 `Collection` 扩展标 `@available(SwiftStdlib 6.2, *)`，而 `SwiftStdlib 6.2: anyAppleOS 26.0`——是 Swift 6.2 标准库、需 iOS 26 运行时。两处改为「iOS 26 / macOS 26 起无需包装，更早目标保留 `Array(...)`，不算问题」 |
| 同上 | 同上 | 新增 `resizability.md`（iPhone Duo、`== .regular`、`safeAreaBar`、垂直工具栏）、`localization.md`、`performance-plus.md`；`api.md` 新增软弃用（`accentColor`、`colorScheme()`、`coordinateSpace(name:)`、`Color.cgColor`）、`@Entry` 默认值、语义化工具栏位置、`ToolbarOverflowMenu`；`hygiene.md`：iOS 27 SDK 必须声明启动屏、`UIRequiresFullScreen`；`views.md`：`reorderable()`、`swipeActionsContainer()` | 多数已覆盖（`latest-apis.md` 已有 `accentColor`、`colorScheme(`、`coordinateSpace(name`、`reorderable`、`swipeActionsContainer`、`LocalizedStringResource`/`#bundle` 等）。启动屏要求与 `== .regular` 进入场景 7 测基线：基线已会，**未合入** |
| avdlee-swiftui | 9808b06 → 204dba7（2 提交：d137c91、f333989） | `sheet-navigation-patterns.md` 新增「Tab Bar and Sidebar (iOS 27+)」：iPhone 上 `.sidebarAdaptable` 不能形变，`defaultTabBarPlacement(.sidebar)` 选侧边栏，iPadOS 上无效改用 `defaultAdaptableTabBarPlacement`；`isTabViewSidebarAvailable`；`layout-best-practices.md` 断点用 size class、不要在两个自适应容器间按 size class 切换；`iphone-duo.md` 检查极端尺寸；f333989 删去 iPhone Mirroring 一句 | **新增 → 基线缺口，合入**：Apple 文档 JSON 核实 `defaultTabBarPlacement(_:)` 与 `isTabViewSidebarAvailable` 均为 iOS 27.0，`defaultAdaptableTabBarPlacement(_:)` 为 iOS 18.0，摘要写明「在 iPhone 等静态解析平台生效、iPadOS 上无效」。场景 7 基线称「iPhone 上要侧边栏只能自建导航」（E3 ✘），有 skill 时达成。其余布局建议本 skill `design-hig.md` 已覆盖，未合入 |

### 评测（omp + `openai/gpt-6.1-sol`，thinking `medium`）

新增场景 7（夹具 `evals/files/LedgerInfo.plist`、`evals/files/LedgerRoot.swift`）：用 Xcode 27 构建提交、部署目标保持 iOS 17；
plist 无启动屏，根视图 `.sidebarAdaptable` 期望宽屏 iPhone 显示侧边栏，列表用 `sizeClass != .compact` 与
`ForEach(Array(entries.enumerated()), …)`。E2 是本次 `enumerated()` 更正的哨兵。

| 场景 | 模式 | skill_read | 结果 | 证据摘录 |
|---|---|---|---|---|
| 7 | 基线 | false | E1 ✔ E2 ✔ E3 ✘ E4 ✔ | 查了 iOS 27 发行说明，补 `UILaunchScreen`；`#available(iOS 26.0, *)` 才去掉 `Array(...)`；改 `== .regular`；但称「`.sidebarAdaptable` 在 iPhone 上不提供侧边栏，宽屏 iPhone 要侧边栏只能自建导航」 |
| 7 | 有 skill（改后正文） | **true** | E1 ✔ E2 ✔ E3 ✔ E4 ✔ | `#available(iOS 27.0, *)` 分支 `.defaultTabBarPlacement(sizeClass == .regular ? .sidebar : .tabBar)`，注明 iPadOS 上无效、iOS 17–26 保留标签栏；「`Array(entries.enumerated())` 在 iOS 17 路径仍必需，`enumerated()` 的集合遵循只在 iOS 26 起可用」；列表改 `NavigationSplitView` 并指出 `!= .compact` 把未定的 size class 当成宽屏 |

读取核查：有 skill 运行读了 `skill://apple` 下的 SKILL.md 与 6 篇 references 及 Apple 文档页，没有读到 `evals/`。
D2 判定：基线未达成的 E3 在有 skill 时达成；E1、E4 基线已会，对应内容（启动屏要求、`== .regular`）不合入，场景留作哨兵。
负例（场景 4）未改 description / Scope，未重跑。输出目录：`/tmp/hs-evals-sync/SyncG3/apple-b7`（基线）、`apple-s7`（有 skill）。

### 正文改动

- `SKILL.md` Scope：新 App 默认部署目标 iOS 27（Xcode 27、Swift 6.4），既有项目保持目标并门控更新的 API。
- `references/latest-apis.md`：页首验证说明补「iOS 27 与 Swift 6.4 已于 2026-09 发布」；iOS 27 小节改为「默认目标；低于 27 的项目门控」；新增 `.sidebarAdaptable` 在 iPhone 上的 `defaultTabBarPlacement(.sidebar)`；`enumerated()` 旧模式条目限定 iOS 26+。
- `references/swiftui-lists-foreach.md`：`enumerated()` 的可用性更正。
- `SOURCES.yaml`：twostraws、avdlee `contributes`；re-pin；版本号 `2026.10.15`。

遗留风险：`ArrangementView` 等 iOS 27.1 API 在 `design-hig.md` 仍标 beta；Xcode 27.1 发行说明详情页仍写 RC，下次同步复核。
iOS 27 SDK 正式版本身未在本机（无 Xcode）编译验证，「Verified against: iOS 27 RC SDK」措辞保留。

## 2026-10-15 上游新增内容评估

来源：`tenequm/skills` 新增的 `skills/swift-dev/SKILL.md`（MIT，HEAD db4b27c；评估报告 NewS3 定为 MERGE 限定条目）。
Xcode 27 构建破坏项（ld64 移除、Swift Build 产物路径、导出方法改名等）属于裁决 A12 排除的 xcode-tooling，不评。
核实方式：本机 Swift 6.3.3（Linux，swift-foundation 的 `#Predicate` 宏与 SIL 诊断与 Apple 平台同源）实编译；
SwiftData / SwiftUI 签名查 developer.apple.com 文档 JSON（`/tutorials/data/documentation/…json` 与 `/tutorials/data/index/swiftui`）。

| 候选 | 核实证据 | 基线 | 结论 |
|---|---|---|---|
| `ModelConfiguration.cloudKitDatabase` 默认 `.automatic`，有 CloudKit entitlement 即开同步，不要同步传 `.none` | 文档：`init(_:schema:isStoredInMemoryOnly:allowsSave:groupContainer:cloudKitDatabase:)` 默认 `.automatic`；`.automatic` 摘要「使用 entitlements 中的主 ubiquity 容器启用托管 CloudKit 同步」 | 场景 8 E1 ✔ | **不合入**（基线已会，场景留作哨兵） |
| `#Predicate` 中写 `.high` / `Priority.high` 编译失败，先赋给局部常量 | 实编译：`$0.priority == .high` → "Member access without an explicit base is not supported in this predicate"；`Priority.high` → "key path cannot refer to enum case 'high'"；局部 `let` 版本编译并 `evaluate` 为 true | 场景 8 E3 ◐（绕开谓词、全量取回后内存过滤） | **合入** `swiftdata.md` Predicates |
| SwiftUI `.modelContainer(...)` 不接受 `migrationPlan`，需自建 `ModelContainer(for:migrationPlan:configurations:)` | SwiftUI 文档索引里 `modelContainer` 只有 `(_:)` 与 `(for:inMemory:isAutosaveEnabled:isUndoEnabled:onSetup:)` 两族（View / Scene），均无 migrationPlan；`ModelContainer` 有 `init(for:migrationPlan:configurations:)` | 场景 10 E2 ✘（写出不存在的 `.modelContainer(for:migrationPlan:)`） | **合入** `swiftdata.md` Model rules |
| Swift 6 下 `versionIdentifier` 必须 `static let` | 实编译：存储型 `static var` 报 "nonisolated global shared mutable state"；**计算型 `static var` 合法**，上游说法过宽 | 场景 10 E1 ✔（用计算属性） | **不合入**（基线已会；上游表述不准确） |
| 主 actor 默认隔离下 `Codable` 一致性被隔离，`@concurrent` 中解码报错，纯数据类型声明 `nonisolated struct` | 实编译（`-default-isolation MainActor`）：报 "main actor-isolated conformance of 'Report' to 'Decodable' cannot be used in nonisolated context"；`nonisolated struct` 消除。另测：raw-value 枚举的 `Codable` 不受影响 | 场景 8 E2 ✔ | **不合入**（基线已会；`swift-concurrency-bugs.md` 已有该诊断条目） |
| region-isolation 错误只在 SIL 阶段报，`-typecheck` 看不到 | 实编译：同一文件 `-typecheck` 无错，`-emit-sil -o /dev/null` 报 "sending 'b' risks causing data races" | 场景 8 E4 ✘（只说 typecheck 不复现构建设置、缺 iOS SDK） | **合入** `SKILL.md` Environment 与 `swift-concurrency-bugs.md` |
| Swift Testing：跨模块 `x == .init(...)` 误导性重载错误，根因是逐成员初始化器为 internal | 实编译（SwiftPM 6.3.3）：可选值报 "cannot convert value of type 'Grant?' to expected argument type '(any (~Copyable & ~Escapable).Type)?'"，非可选报 "'Grant' and '()'"；写全类型名报 "missing argument for parameter 'from'" | 场景 9 E1 ✔ E2 ✔ E3 ◐（修法给全，未提写全类型名） | **不合入**（核心诊断基线已会，场景留作哨兵） |
| 从主 actor await `@ModelActor` 实测跑在主线程 | 上游自述的社区观察；Apple 文档 `ModelActor` / `DefaultSerialModelExecutor` 未说明执行线程，无法核实 | — | **不合入**（未核实） |

### 评测（omp + `openai/gpt-6.1-sol`，thinking `medium`）

新增场景 8（夹具 `TallyStore.swift`、`Tally.entitlements`：后台导入 + 待处理条目查询 + CI 只跑 `swiftc -typecheck`）、
场景 9（`GrantTests.swift`、`Grant.swift`：跨模块 `.init(...)` 编译错误）、场景 10（`TallyApp.swift`：版本化 schema 与迁移计划）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 8 后台导入 | gpt-6.1-sol medium | 无 | false | E1 ✔ E2 ✔ E3 ◐ E4 ✘ E5 ✔ | 自行加 `cloudKitDatabase: .none` 与 `nonisolated`；`pendingEntries` 全量取回后 `.filter { $0.status == .pending }`；称 typecheck 不够的理由是「不复现默认隔离设置、命令行工具无 iOS SDK」，未提 SIL |
| 8 后台导入 | gpt-6.1-sol medium | 有 | true | E1 ✔ E2 ✔ **E3 ✔ E4 ✔** E5 ✔ | `let pending = EntryStatus.pending` 后 `#Predicate { $0.status == pending }`；「Region-isolation diagnostics also run during SIL generation. CI needs a full build, or at minimum `swiftc -emit-sil -o /dev/null`」；读了 SKILL.md、`swiftdata.md`、`swift-concurrency-bugs.md` 等 |
| 9 测试编译错误 | gpt-6.1-sol medium | 无 | false | E1 ✔ E2 ✔ E3 ◐ | 指出 internal 逐成员初始化器与误导性重载诊断，给出 `public init` / `@testable import` / 比较字段；未提写全类型名 |
| 10 迁移计划 | gpt-6.1-sol medium | 无 | false | E1 ✔ E2 ✘ E3 ✔ | 计算型 `versionIdentifier`；`.modelContainer(for: Entry.self, migrationPlan: TallyMigrationPlan.self)`——该重载不存在 |
| 10 迁移计划 | gpt-6.1-sol medium | 有 | true | E1 ✔ **E2 ✔** E3 ✔ | 自建 `ModelContainer(for:migrationPlan:configurations:)` 后 `.modelContainer(container)`；读了 `swiftdata.md` |

D2 判定：基线未达成的 场景 8 E3/E4、场景 10 E2 在有 skill 时达成。场景 9 基线已达成核心行为，对应内容未合入，未跑有 skill。
负例（场景 4）未改 description / Scope，未重跑。输出目录：`/tmp/hs-evals-M3/apple-b8`、`apple-b9`、`apple-b10`（基线）、`apple-s8`、`apple-s10`（有 skill）。

### 正文改动

- `SKILL.md` Environment：`swiftc -typecheck` 不算编译，region-isolation 错误来自 SIL，用完整构建或 `swiftc -emit-sil -o /dev/null`；路由表 SwiftData 行补「migrations」。
- `references/swiftdata.md`：Model rules 增「迁移计划不能经 SwiftUI `.modelContainer(for:)` 传入，自建容器」；Predicates 增「枚举 case 不能直接写在谓词里，先赋局部常量」。
- `references/swift-concurrency-bugs.md`：「Sending 'x' risks causing data races」条目补 SIL 阶段与验证命令。
- `SOURCES.yaml`：新增 `tenequm-swift-dev`（merged，paths `skills/swift-dev/SKILL.md`）。

遗留：本机无 Xcode，枚举谓词在 SwiftData 存储层的运行时翻译（局部常量版本）未在设备上验证，只验证到宏展开与 `Predicate.evaluate`。同日复核：正文原写「过滤仍在 store 中执行」超出了已验证范围，已删去该保证，改为注明验证边界、要求在真实 `ModelContainer` + `context.fetch` 上确认后再依赖；宏编译层面的修正保留。

## 2026-10-15 文档上游复核

范围：`apple-docs`（唯一 `kind: docs` 条目）的 `contributes`：正文所有版本门槛、API 拼写与无障碍数字。developer.apple.com 为前端渲染，改读其文档 JSON（`/tutorials/data/documentation/<path>.json` 的 `metadata.platforms`）、框架符号索引（`/tutorials/data/index/{swiftui,uikit,swiftdata,observation,appkit,foundation,webkit,testing,swift}`）、HIG JSON（`/tutorials/data/design/human-interface-guidelines/accessibility.json`）与开发者发布 RSS。API 拼写用脚本把 `SKILL.md` 与全部 references 反引号内的 `name(` 调用逐一对照索引，未命中的只剩用户代码、SwiftPM 设置与正文已标为「编造」的 `scrollExtensionMode`，外加下表三处。

| 上游 id | 核对的事实 | 当前官方页面 | 结论 |
|---|---|---|---|
| apple-docs | 默认部署目标 iOS 27 / Xcode 27 / iOS 27 已发布 | https://developer.apple.com/news/releases/ （RSS：Xcode 27 (27A266a) 2026-09-14；iOS 27.0.1 (24A446) 2026-09-28；Xcode 27.2 仍为 beta） | 一致；`contributes` 原写「iOS 26 为默认、iOS 27 在 RC」已过时，改写 |
| apple-docs | iOS 27 条目：`visibilityPriority(_:)` iOS 27 / macOS 26.1；`ToolbarOverflowMenu` 仅 iOS/iPadOS/Catalyst/visionOS 27；`reorderable()`（`DynamicViewContent`）与 `reorderContainer(for:isEnabled:move:)`、`swipeActionsContainer()` 无 tvOS；`defaultTabBarPlacement(_:)`、`isTabViewSidebarAvailable` 27；`defaultAdaptableTabBarPlacement(_:)` iOS 18；`alert`/`confirmationDialog` 的 `item:` 重载回溯 iOS 15 / macOS 12 / tvOS 15 / watchOS 8 / visionOS 1；`AsyncImage(request:)`、`asyncImageURLSession(_:)`、`ReadableDocument`/`WritableDocument` 27；`toolbarMinimizationBehavior(_:for:)` 27（旧拼写无页面）；`appearsActive` iOS 18 / macOS 10.15 | `https://developer.apple.com/documentation/swiftui/<symbol>` | 一致 |
| apple-docs | iOS 26 条目与替换表门槛 | 同上 | **已变化 → 更正**（原文与官方不符）：① `dragContainer(for:…)`、`onDragSessionUpdated(_:)` 为 **iOS 27 / macOS 26**（`DragConfiguration` 才是 26），原列在「iOS 26 新增、统一 `#available(iOS 26)`」下；② `ControlSize.extraLarge` 是 iOS 17 / macOS 14；③ `Tab(role: .search)` 的 API 是 iOS 18；④ `@Animatable` / `@AnimatableIgnored` 宏文档标注自 iOS 13 / macOS 10.15 可用（需 26 SDK 编译），原表与 `swiftui-animation.md` 写「iOS 26+」；⑤ `autocorrectionDisabled(_:)` 文档标注自 iOS 13，原表写 iOS 16。按「正确门槛、不做多余 gate」改写 `latest-apis.md` 与 `swiftui-animation.md` |
| apple-docs | API 拼写 | SwiftUI 符号索引 | **已变化 → 更正**：`sliderNeutralValue(_:)` 不存在（是 iOS 26 `Slider` 初始化器的 `neutralValue:` 参数）；`navigationTransitionSource(id:namespace:)`/`navigationTransitionDestination(...)` 不存在（`latest-apis.md` 与 `swiftui-navigation.md` 两处），实际为 `matchedTransitionSource(id:in:)`（View iOS 18；`ToolbarContent` iOS 26）+ `.navigationTransition(.zoom(sourceID:in:))`；`.rect(cornerRadius:style: .concentric)` 不存在（`RoundedCornerStyle` 只有 `circular`/`continuous`），同心圆角为 `ConcentricRectangle()` 或 `.rect(corners: .concentric)`（`Edge.Corner.Style.concentric`，26） |
| apple-docs | 触控目标与对比度 | https://developer.apple.com/design/human-interface-guidelines/accessibility | **已变化 → 更正**（原文即与 HIG 不符）：HIG 表为「默认控件尺寸 / 最小控件尺寸」——iOS/iPadOS 与 watchOS 44×44 / 28×28 pt，macOS 28×28 / 20×20 pt，visionOS 60×60 / 28×28 pt，tvOS 66×66 / 56×56 pt。正文把 44 pt 写成「iOS 最小、严格执行」，Mac 写「约 28 pt」。`accessibility.md`、`design-hig.md`、`liquid-glass.md`、`uikit-appkit-interop.md` 四处改为默认值/最小值表述。对比度：HIG 表为 ≤17 pt 4.5:1、≥18 pt 3:1、粗体任意字号 3:1，与 WCAG 的 14 pt 粗体门槛不同，`accessibility.md` 补注 |
| apple-docs | `ControlActiveState` 弃用版本 | https://developer.apple.com/documentation/swiftui/controlactivestate | **更正**：文档 `deprecatedAt` 为 macOS **27.2**（提示改用 `appearsActive`），原写「macOS 27」 |
| apple-docs | 无障碍尺寸（AX5 测试）、`glassEffect(_:in:)` / `GlassEffectContainer` 26 且无 visionOS | 同上 | 一致 |

评测：`evals/evals.json` 场景 7 第一条原写「不用 `@Animatable` 宏，因为它需要 iOS 26」，与 ④ 冲突，改为「直接遵循 `ViewModifier` + `Animatable`，或使用 `@Animatable` 宏（需 26 SDK、文档标注自 iOS 13 可用，无需 gate）」，两种答法均可达成。

另记（未合入）：文档 JSON 已对 `foregroundColor(_:)`、`cornerRadius(_:antialiased:)`、`tabItem(_:)`、`AnimatableModifier`、`statusBarHidden(_:)` 等软弃用 API 标出 `deprecatedAt: 27.2`；Xcode 27.2 仍为 beta（RSS 2026-10-14 为 beta 3），正式发布后这些将从「无警告的软弃用」变成真实弃用警告，届时需复核 `latest-apis.md`「soft-deprecated 不报警」一句。

## 2026-10-15 D2 回归

覆盖提交：`d604f89`（上游同步：默认目标 iOS 27、`enumerated()` 门槛、iPhone 上 `defaultTabBarPlacement(.sidebar)`）、`a343b38`（tenequm 新增：`#Predicate` 枚举 case、迁移计划自建容器、SIL 阶段诊断）、`26a1803`（文档复核：可用性门槛、三处不存在的 API 拼写、HIG 控件尺寸、`ControlActiveState` 27.2，场景期望同步）、`2ef72b2`（删去未验证的「过滤仍在 store 中执行」）。

编号说明：上节写「场景 7 第一条」改了 `@Animatable` 期望，按 `evals.json` / `run_evals.py --only` 的 1 起编号，那是**场景 6**（`Legacy27.swift`）；场景 7 是 Ledger（`LedgerInfo.plist`）。两个场景本轮都跑。

选场景与理由：

- 场景 6：今天改了第一条期望且从未重跑，必选，两侧新跑。
- 场景 7：今天新增；`latest-apis.md` 在其有 skill 结果（10:32）之后又被 `26a1803` 改过，有 skill 重跑；基线（`/tmp/hs-evals-sync/SyncG3/apple-b7`，10:28）query、期望与当前逐字一致、夹具首读逐行一致，复用（副本 `/tmp/hs-d2/D2G5/reused/apple-b7`），判定沿用上文。
- 场景 8：今天新增；E3 直接对应 `swiftdata.md` Predicates 段（13:33 刚改），有 skill 重跑；基线（`/tmp/hs-evals-M3/apple-b8`）逐字一致，复用（副本 `reused/apple-b8`），判定沿用上文。
- 场景 10：今天新增；有 skill 重跑。基线（`/tmp/hs-evals-M3/apple-b10`）跑时 E1 还是「`static let`, not `static var`」，之后改为允许计算属性，场景已改，基线重跑。
- 场景 9：上文已记基线达成核心行为、对应内容未合入，未选。
- **新增场景 11**（夹具 `ComposeScreen.swift`，部署目标 iOS 18、Xcode 27）：`26a1803` 的更正（`navigationTransitionSource`/`Destination`、`sliderNeutralValue`、`.rect(cornerRadius:style: .concentric)` 不存在；`dragContainer` 为 iOS 27；`Tab(role: .search)` iOS 18、`ControlSize.extraLarge` iOS 17 不需 26 门控；HIG 44 pt 默认 / 28 pt 最小）此前没有任何场景覆盖，按简报新增。签名与门槛已对照 developer.apple.com 文档 JSON（`metadata.platforms`）。
- 场景 4：负例。

模型 `openai/gpt-6.1-sol` medium（VM 内 omp），新跑产物 `/tmp/hs-d2/D2G5/apple/omp-openai-gpt-6.1-sol-medium/`，逐条读 `answer.md`、`workspace/` 与 `events.jsonl` 人工判定。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 6 | gpt-6.1-sol medium | 无 | False | E1–E6 全 ✔ | 172 s。直接遵循 `ViewModifier, Animatable`；`.statusBar` iOS 27、`toolbarVisibility` iOS 18、iOS 17 用 `toolbar(.hidden, …)`；引 TN3211；`item:` 重载回溯 iOS 15 |
| 6 | gpt-6.1-sol medium | 有 | True | E1–E6 全 ✔ | 118 s。用 `@Animatable` 宏并写明「the macro back-deploys to iOS 13」、无运行时门控——即改后的第一条期望；其余同基线 |
| 7 | gpt-6.1-sol medium | 无（复用 `reused/apple-b7`） | False | E1 ✔ E2 ✔ E3 ✘ E4 ✔ | 判定见上文 |
| 7 | gpt-6.1-sol medium | 有 | True | E1 ✔ E2 ✔ E3 ✔ E4 ◐ | 183 s。`#available(iOS 27.0, *)` 下 `defaultTabBarPlacement(sizeClass == .regular ? .sidebar : .tabBar)`；保留 `Array(entries.enumerated())` 并注明 iOS 26 运行时。E4：列表改 `NavigationSplitView` 去掉了 `!= .compact`，但没讲 `nil` 不能当宽屏（本 skill 无此内容，与改动无关） |
| 8 | gpt-6.1-sol medium | 无（复用 `reused/apple-b8`） | False | E1 ✔ E2 ✔ E3 ◐ E4 ✘ E5 ✔ | 判定见上文 |
| 8 | gpt-6.1-sol medium | 有（r1，`2ef72b2` 正文） | True | E1 ◐ E2 ✔ **E3 ◐** E4 ✔ E5 ✔ | 145 s。读了 `swiftdata.md` 后**放弃谓词**：`fetch` 全部再 `.filter { $0.status == .pending }`，注释「Codable enum predicates are not reliably store-translatable」——正是 `2ef72b2` 新加的「未在真实容器上确认」一句诱发的，退回到基线水平（上文 a343b38 时有 skill 为 ✔）。副本 `/tmp/hs-d2/D2G5/apple-s8-r1` |
| 8 | gpt-6.1-sol medium | 有（r2，修正后正文） | True | E1 ◐ E2 ✔ **E3 ✔** E4 ✔ E5 ✔ | 108 s。`let pending = EntryStatus.pending` 后 `#Predicate { $0.status == pending }`，并说明谓词的 store 翻译仍待真机验证。E1 两轮都只说「避免 unique 约束受 CloudKit 要求影响」，未讲默认 `.automatic` 因 entitlement 开启同步（本 skill 无此内容） |
| 10 | gpt-6.1-sol medium | 无 | False | E1 ✔ E2 ✔ E3 ✔ | 43 s。计算型 `versionIdentifier`；这次自建了 `ModelContainer(for:migrationPlan:)` 再 `.modelContainer(container)`（上文那次基线写了不存在的重载，属基线波动），未说明原因 |
| 10 | gpt-6.1-sol medium | 有 | True | E1 ✔ E2 ✔ E3 ✔ | 66 s。同样自建容器；`@Attribute(originalName: "amountCents")`、`category` 默认 "General" |
| 11（新增） | gpt-6.1-sol medium | 无 | False | E1–E6 全 ✔ | 174 s。联网读 Apple 文档 JSON 后逐项答对（含 `dragContainer` 27、`extraLarge` 17、44/28 pt） |
| 11（新增） | gpt-6.1-sol medium | 有 | True | E1–E6 全 ✔ | 283 s。`matchedTransitionSource` 用在按钮视图上（iOS 18），并注明 `ToolbarContent` 重载需 26；`ConcentricRectangle()` + 圆角矩形回退；`dragContainer` 门控升到 27；去掉 `Tab(role: .search)` 与 `extraLarge` 的 26 门控；24 pt 关闭按钮按「44 默认、28 最小、WCAG 是 CSS px」判 |
| 4（负例） | gpt-6.1-sol medium | 有 | **False** | E1 ✔ E2 ✔ | 51 s。只按 Flutter 作答 |

### 正文修正（有证据）

场景 8 r1 的回退直接来自 `2ef72b2` 的措辞：它如实删去了未验证的 store 保证，但只留下「未确认、依赖前先在设备上测」，模型据此把过滤挪到内存。修正 `references/swiftdata.md` Predicates 段：保留验证边界（只验证到宏展开与 `Predicate.evaluate`），改为「局部常量写法仍放在谓词里；用模拟器或设备上的测试覆盖这次 fetch；不要用全量取回再内存过滤来回避不确定性；若 fetch 真的失败，改存原始值（存储型 `String` 属性 + 枚举计算访问器）并在其上过滤」。没有新增任何未验证的 store 行为断言。r2 重跑 E3 恢复 ✔，其余不变。`build_catalog`（catalog already current）、`validate_skills.py skills/apple` 0 error 0 warning、安装冒烟（`npx skills@latest add /tmp/hs-wt/D2G5 --skill apple --agent universal --copy --yes`，安装后 `references/` 与工作树逐字一致）均通过。

结论：今天各处改动相关的行为在有 skill 时均达成（场景 6 E1 的宏答法、场景 7 E2/E3、场景 8 E3/E4、场景 10 E2、场景 11 全部），修正后不比基线差；场景 11 基线联网即可答对，留作哨兵。负例 `skill_read == false`。

遗留：场景 8 E1、场景 7 E4 的解释深度属模型波动，与本次改动无关；`#Predicate` 局部常量写法的 store 翻译仍待在真实 `ModelContainer` 上验证。
