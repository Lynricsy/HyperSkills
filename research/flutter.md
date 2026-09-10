# flutter 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-10（种子调研）
- 复核日期：2026-09-10（本次全部候选用 GitHub REST API `/repos/{owner}/{repo}` 重新取
  `stargazers_count` / `pushed_at` / `license.spdx_id`，并对四个 INCLUDE 上游下载
  tarball 通读 `SKILL.md` 与 `references/`）
- 检索途径：
  - `web_search`：`"flutter skill SKILL.md github"`、`"dart agent skill"`、`site:skills.sh flutter`
  - <https://www.skills.sh>
  - VoltAgent/awesome-agent-skills、addyosmani/agent-skills
  - 领域官方组织仓库：`flutter/`、`dart-lang/`
  - 官方入口：`https://docs.flutter.dev/ai/ai-rules` 已重定向到 `/ai/get-started`，
    其推荐安装即 `npx skills add flutter/agent-plugins` 与 `npx skills add dart-lang/skills`
- GitHub API 核对方式：`curl -s https://api.github.com/repos/<owner>/<repo>`
  （匿名调用当日曾短暂 403 限流，改为串行重试后全部取到；无一条依赖 HTML 抓取）

关键结论（决定了整体选材）：**Google 官方同时提供 Flutter 与 Dart 两套 Agent Skills**，
均为 BSD-3-Clause，可再分发。社区候选只在官方留白处（状态管理、性能、测试深度）才有价值。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。
Stars / 推送 / 许可均为 2026-09-10 当日 API 值。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | flutter/agent-plugins `skills/flutter-*`(10)、`skills/dart-*`(镜像)、`rules/` | https://github.com/flutter/agent-plugins | 2925 | 2026-09-03 | BSD-3-Clause | 官方任务型技能：架构、响应式布局、布局报错、widget/integration 测试、widget preview、声明式路由与深链、本地化、JSON、http | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 厂商维护、活跃、许可宽松；`- [ ]` 清单 + `If X:` 分支 + 「run validator → review → fix」反馈环是全部候选中信噪比最高的结构 |
| 2 | dart-lang/skills `skills/dart-*`(14) | https://github.com/dart-lang/skills | 478 | 2026-09-09 | BSD-3-Clause | Dart 3 语言（pattern matching、primary constructors）、静态分析、运行时错误、mocks、coverage、ffigen/FFI assets、CLI、包冲突 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 全部候选中推送最新（复核前一日）；覆盖 Flutter 技能刻意留白的 Dart 语言面 |
| 3 | evanca/flutter-ai-rules `skills/*`(37 目录) | https://github.com/evanca/flutter-ai-rules | 637 | 2026-08-31 | MIT | riverpod / bloc / provider / change-notifier / best-practices / app-architecture / architecture-feature-first / dart-3-updates / effective-dart / testing / mockito / mocktail / patrol / errors / pre-caching / accessibility | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 社区最完整的一套；frontmatter 合规且带 `license:`；`ATTRIBUTION.md` 逐 skill 记录上游与许可，溯源纪律可直接借鉴 |
| 4 | sgruhier/superpowers-flutter `skills/{riverpod,bloc,go-router,auto-route,flutter-widget-rules,flutter-analyze,flutter-clean-architecture,dart,fpdart}` | https://github.com/sgruhier/superpowers-flutter | 5 | 2026-09-07 | MIT（仓库 LICENSE 为 MIT，API 因尾部署名段报 NOASSERTION） | Riverpod/Bloc/clean-arch 深度散文 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE（仅 flutter/dart 子集） | 唯一明确写出「`StateProvider`/`StateNotifierProvider`/`ChangeNotifierProvider` 是 legacy」的候选；provider 选型表、sealed state + Equatable、`select` 何时真正有效的解释均正确。星数低 → 作为内容捐赠者并固定 commit，不作为长期依赖 |
| 5 | Jeffallan/claude-skills `skills/flutter-expert/references/performance.md` | https://github.com/Jeffallan/claude-skills | 11399 | 2026-08-07 | MIT | Flutter 通用（Riverpod/Bloc/GoRouter/widgets/perf） | 1 | 2 | 2 | 1 | 2 | 8 | INCLUDE（仅性能参考） | references 分类法值得借鉴、性能清单可用；但正文 Riverpod 示例用 `StateNotifierProvider`（Riverpod 3 已 legacy），正确性扣分，其示例一律不采用。星数属聚合仓库整体，非该 skill |
| 6 | Harishwarrior/flutter-claude-skills `flutter-tester/references/` | https://github.com/Harishwarrior/flutter-claude-skills | 66 | 2026-07-12 | MIT | 分层测试模式、Riverpod 测试、widget 测试（约 51 KB） | 1 | 2 | 3 | 3 | 2 | 11 | INCLUDE（仅测试） | 测试深度超过官方；「永远不要 mock provider，改为 override 依赖」「每个测试新建 container」等规则抽查正确。推送两月，在窗口内但为保留项中最慢 |
| 7 | docs.flutter.dev platform-channels + internationalization | https://docs.flutter.dev/platform-integration/platform-channels | — | 持续更新 | CC-BY-4.0 | 平台通道 / Pigeon / 线程模型 / 后台 isolate；当前 l10n 流程 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（kind: docs） | 平台通道在全部候选中为空白，只能自官方文档撰写；同时用它纠正官方 skill 里过期的 `synthetic-package` 写法 |
| 8 | draz26648/flutter_craft_skills | https://github.com/draz26648/flutter_craft_skills | 21 | 2026-09-02 | MIT | 设计还原、design token、Figma→widget、golden | 1 | 3 | 2 | 2 | 2 | 10 | REJECT（本 skill） | 内容合格但属视觉设计域，归 `frontend-design`；合入本 skill 会稀释范围 |
| 9 | MiniMax-AI/skills `skills/flutter-dev` | https://github.com/MiniMax-AI/skills | 13540 | 2026-04-18 | MIT | Flutter 通用 + Riverpod/BLoC | 1 | 0 | 2 | 1 | 2 | 6 | REJECT | 推送 2026-04-18（近 5 个月，超窗口）；内容自述派生自 #5，取源不取抄本 |
| 10 | evanca `rules/` + `combined/`（同 #3 仓库） | https://github.com/evanca/flutter-ai-rules | 637 | 2026-08-31 | MIT | 同 #3 内容的 Copilot instructions 形态 | 2 | 3 | 3 | 3 | 2 | — | REJECT（作为 skill 源） | 非 `SKILL.md` 形态，与 #3 内容重复；仅作交叉校验 |
| 11 | ImL1s/flutter-claude-skills | https://github.com/ImL1s/flutter-claude-skills | 9 | 2026-09-07 | MIT | 66 个 skill | 0 | 3 | 1 | 0 | 2 | 6 | REJECT | 9★/0 fork，单作者四个月产出 66 个 skill，无外部验证，抽查质量参差 |
| 12 | Poorgramer-Zack/dart-expert-skills | https://github.com/Poorgramer-Zack/dart-expert-skills | 7 | 2026-08-11 | MIT | 按库拆分的模块化 skill | 0 | 2 | 2 | 2 | 2 | 8 | REJECT | 无外部验证，内容被 #3/#4 完全覆盖，合入只增维护面 |
| 13 | RobertAlvv/flutter-skills | https://github.com/RobertAlvv/flutter-skills | 10 | 2026-03-10 | 无 | 状态管理审计 | 0 | 0 | 2 | 1 | 0 | 3 | REJECT | 6 个月未推送 **且** 无许可 |
| 14 | AbdulManan-official/flutter-production-skill | https://github.com/AbdulManan-official/flutter-production-skill | 0 | 2026-06-16 | 无 | 生产 Flutter（含 GetX） | 0 | 1 | 2 | 0 | 0 | 3 | REJECT | 0★、无许可、主推 GetX（与官方分层与本 skill 默认栈冲突） |
| 15 | dagovalsusa/claude-flutter-skills | https://github.com/dagovalsusa/claude-flutter-skills | 1 | 2026-03-23 | MIT | Riverpod 3、Freezed、go_router、Flame | 0 | 0 | 2 | 2 | 2 | 6 | REJECT | 1★、单次提交、近 6 个月停更 |
| 16 | cleydson/flutter-claude-code | https://github.com/cleydson/flutter-claude-code | 53 | 2026-03-04 | 无 | Claude Code Flutter 配置 | 0 | 0 | 1 | 1 | 0 | 2 | REJECT | >6 个月停更、无许可、且是 agent 配置而非 skill |
| 17 | ToastyToast25/claude-code-dart-flutter | https://github.com/ToastyToast25/claude-code-dart-flutter | 7 | 2026-01-22 | MIT | Dart/Flutter CC 配置 | 0 | 0 | 1 | 1 | 2 | 4 | REJECT | 约 8 个月停更 |
| 18 | thruthesky/flutter-skill | https://github.com/thruthesky/flutter-skill | 6 | 2026-03-11 | 无 | Flutter skill | 0 | 0 | 1 | 1 | 0 | 2 | REJECT | 停更 + 体量极小 + 无许可 |
| 19 | vp-k/flutter-craft | https://github.com/vp-k/flutter-craft | 12 | 2026-08-10 | 无 | Flutter 工作流 skill | 0 | 2 | 2 | 1 | 0 | 5 | REJECT | 无许可（宽松策略下可合入，但内容被官方完全覆盖，不值得增加溯源负担） |
| 20 | nylo-core/claude-code | https://github.com/nylo-core/claude-code | 4 | 2026-04-11 | MIT | Nylo 框架 skill | 1 | 1 | 2 | 2 | 2 | 8 | REJECT | 绑定小众框架 Nylo，与「Flutter 生态通用」范围不符 |
| 21 | FlutterFlow/shadertoy_to_flutter_skill | https://github.com/FlutterFlow/shadertoy_to_flutter_skill | 15 | 2026-04-24 | MIT | Shadertoy→Flutter shader 移植 | 2 | 1 | 3 | 2 | 2 | 10 | REJECT（本 skill） | 厂商出品但范围极窄（单一转换任务），作为将来可选附加 skill 记录 |
| 22 | anasfik/FlutterGuard | https://github.com/anasfik/FlutterGuard | 24 | 2026-08-24 | 无 | Flutter 安全/lint 工具 | 0 | 3 | 2 | 1 | 0 | 6 | REJECT | 是工具而非 skill；安全域归后续 `security-review` |
| 23 | lh17708357536-gif/flutter-cn-overseas-app-skills | https://github.com/lh17708357536-gif/flutter-cn-overseas-app-skills | 20 | 2026-07-13 | MIT | 国内 App 出海发布 | 0 | 2 | 1 | 1 | 2 | 6 | REJECT | 属发布/合规域，与本 skill 范围无交集 |

另有枚举后判定为领域外的：`cometchat/cometchat-skills`（厂商 SDK 集成）、
`devsemih/appstore-review-skill`、`minosdevs/appstore-approval-audit`（发布域）、
`kane313/flutter-figma-skills`、`abhiabby3008/flutter-reverse-engineering-skill`、
`Jaywalker-not-a-whitewalker/flutter-release-pipeline`。

## 深度审查

### flutter/agent-plugins（官方，#1）

- **结构**：`skills/<name>/SKILL.md` 单文件，无 `references/`、`scripts/`；另有 `rules/`
  （纯 `.md` 与 Cursor `.mdc`，含 2026-09-02 新增的 `flutter-hot-reload`）、
  `.agents/agents/<persona>/`、以及 `tool/generator/`（Dart CLI，可生成 / 校验 / lint / 同步 skill，
  `tool/.dart_skills_githash` 固定所镜像的 dart-lang/skills commit）。
- **frontmatter**：`name` + `description` + `metadata.{model,last_modified}`，无 `license:`。
  `metadata.model: models/gemini-3.1-pro-preview` 说明是自 docs.flutter.dev 生成后人工审阅。
  这些 `metadata` 字段属 agent 专属扩展，合入本仓库时全部剥离。
- **质量**：每个 skill 同一模板——`## Contents` → 概念 → `## Workflow:` + `- [ ]` 清单 →
  `If X:` 分支 → `## Examples`（可编译 Dart）。路由 skill 一路给到 `AndroidManifest.xml`、
  `assetlinks.json`、`apple-app-site-association` 与 `adb` / `xcrun simctl` 验证命令。
- **缺陷（本次复核发现）**：`flutter-setup-localization` 仍写 `synthetic-package: true` 与
  `package:flutter_gen/gen_l10n/app_localizations.dart`；当前官方文档
  （docs.flutter.dev 内部化页）已改为生成到 `arb-dir` 并用相对路径 import。
  本 skill 采用官方文档写法，并把旧写法折叠进 `Old pattern` 区块。
- **留白**：架构 skill 只讲 ChangeNotifier-MVVM，完全不提 Riverpod / Bloc；无独立性能 skill；
  无平台通道 skill。这三处正是 #3/#4/#5/#7 的合入理由。

### dart-lang/skills（官方，#2）

- **结构**：仅 `skills/<name>/SKILL.md`（14 个）+ `repo_tool/`（Dart lint 工具与
  `skills_lint.yaml`）+ `resources/dart_skills.yaml`（生成源）+ CI 校验流水线。与 #1 同一生成血统。
- **覆盖**：`dart-use-pattern-matching`、`dart-use-primary-constructors`（含 Dart 3.13 起默认可用、
  3.12 需实验开关的版本门槛，这是本 skill `dart-language.md` 里版本标注的来源）、
  `dart-run-static-analysis`、`dart-fix-runtime-errors`、`dart-generate-test-mocks`、
  `dart-collect-coverage`、`dart-use-ffigen`、`dart-setup-ffi-assets`。
- **agent 绑定**：正文多处提到 Dart MCP 工具（`analyze_files`、`dart_fix`），合入时一律改写为
  CLI 命令，避免绑定特定 MCP 服务。

### evanca/flutter-ai-rules（#3）

- **结构**：`skills/<name>/SKILL.md` + 可选 `references/`、`agents/openai.yaml`（agent 覆盖，剥离）；
  根目录另有 `rules/`、`combined/`（含 `__under_6K.md` 上下文预算变体）与多 agent 插件清单。
- **质量**：`riverpod` 十节结构 + `ref.watch/read/listen/onDispose` 决策表，规则非显而易见
  （`ProviderScope` 放 `runApp` 而非 `MyApp`；`await` 后检查 `context.mounted`；mock Notifier 要
  subclass 而非 `implements`；autoDispose provider 在测试中用 `container.listen`）。
  `testing` skill 的「这个测试真的会因为代码坏掉而失败吗」是本 skill 测试章节的判据来源。
- **重叠**：与 #4 在 Riverpod / Bloc 上重叠，两者都是 Riverpod-3 正确的；#3 偏 API 面与 codegen，
  #4 偏结构纪律，互补合并。
- **不合入**：firebase-*、genkit、revenuecat、store-listing、inclusive-design、code-review——
  分属其他 HyperSkills 领域。其 `accessibility` skill 是通用 Web a11y（POUR / ARIA），
  与 Flutter 无关，因此本 skill 的 `accessibility.md` 改由 Flutter 语义 API 与
  `flutter_test` 的 `meetsGuideline` 体系重写，只保留其审计顺序的思路。

### sgruhier/superpowers-flutter（#4）

- **结构**：`skills/<name>/SKILL.md`，含 `UPSTREAM_VERSION`、`scripts/upstream-diff.sh`
  与定时 `upstream-check.yml`（与本仓库 `check_upstream.py` 同思路）。
- **质量**：全部候选中散文质量最高。provider 选型表、providers 即 DI 容器（明确对照 get_it）、
  sealed state + Equatable（并解释「没有 Equatable 时同值重建仍会触发通知」）、
  `AsyncNotifier.build()` 抛错才是 `AsyncError` 的正确解释、`select` 只在真正会重建的那层才有收益。
- **风险**：5★、单作者、仓库很新。缓解方式：固定 commit、只取 flutter/dart 子集、
  所有规则对照 riverpod 官方文档与 `flutter_bloc` 文档抽查后再写。
- **剥离**：跨 skill 引用（`superpowers-flutter:bloc` 这类前缀）、继承自 obra/superpowers 的通用
  工作流 skill、以及项目专属的 get_it/fpdart 强制约定（本 skill 只作为「规模化时的选项」出现）。

### Jeffallan/claude-skills `flutter-expert`（#5）

`references/` 六分法（riverpod-state / bloc-state / gorouter-navigation / widget-patterns /
project-structure / performance）+「Load When」路由表，是本 skill topic router 的结构参考。
`performance.md` 仅 99 行，内容正确但浅（const、select、RepaintBoundary、cacheWidth、compute、
16 ms 预算），作为清单种子合入，其余全部不取——其 Riverpod 示例使用 `StateNotifierProvider`。

### Harishwarrior/flutter-claude-skills `flutter-tester`（#6）

三份参考共约 51 KB：`layer_testing_patterns.md`（repository / DAO / provider / service 分层）、
`riverpod_testing_guide.md`（`createContainer` 助手、AsyncNotifier 初始态与变更、
错误传播、`ref.onDispose` 生命周期、边界情况）、`widget_testing_guide.md`（固定 surface size、
key 命名约定、pump vs pumpAndSettle、对话框与 GoRouter 导航测试）。
合入其中「新建 container、override 依赖而非 mock provider、给测试触达的 widget 加 key、
先设定确定的 view size」等做法。`owasp-mobile-security-checker/` 不取（安全域）。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| F1 | 应用架构 | 官方 #1：分层 UI/Logic/Data + `lib/{data,domain,ui}` 混合目录、ChangeNotifier-MVVM；#3：feature-first，禁止顶层 `blocs/`、`widgets/` 桶，状态管理无关；#4：严格 clean architecture + get_it | 官方分层作为**基线语义**（谁能调用谁、repository 是 SSOT）；#3 的 feature-first 作为**目录策略**（`lib/features/<f>/{data,domain?,ui}`）；clean-arch + get_it 仅作规模化升级选项，不进 Core rules | 层次约束来自厂商文档（更权威）；目录策略两者不矛盾，feature-first 在多人协作下删除与迁移成本更低（#3 引 LeanCode 40 项目经验）；clean-arch 是少数派且成本高 |
| F2 | 状态管理选型 | 官方只讲 ChangeNotifier；#3/#4 讲 Riverpod 与 Bloc；#4 默认 Bloc | 不强制选型：Core rule 1 规定读 `pubspec.yaml` 检测——`riverpod*` → Riverpod 3；`flutter_bloc` → Bloc；都没有 → 官方 ChangeNotifier-MVVM | 「一个默认方案 + 一个逃生口」在这里落为「跟随项目既有栈」；擅自引入第二套状态库是真实的破坏性行为 |
| F3 | Riverpod 版本卫生 | #5（及 #9）示例用 `StateNotifierProvider`；#4 明确其为 legacy；#3 用 codegen 的 `@riverpod` | 一律采用 `Notifier`/`AsyncNotifier` + `NotifierProvider`/`AsyncNotifierProvider`；`StateProvider`/`StateNotifierProvider`/`ChangeNotifierProvider` 只在「legacy 与迁移」表里出现；codegen 标为可选 | 更新 > 更旧；Riverpod 3 把这些 provider 移入 legacy 入口，官方迁移文档已给出对应关系 |
| F4 | Mock 库 | 官方 #2 倾向 `mockito` + codegen；#3 两者都给；#4 统一 mocktail | 默认 mocktail（无 codegen、CI 少一步、不会出现陈旧 `.mocks.dart`），逃生口：项目已有 mockito + build_runner 时沿用；纯 HTTP 场景允许 `package:http/testing.dart` 的 `MockClient` | 社区默认已明显偏向 mocktail；官方倾向 mockito 源于其自身仓库历史而非技术优势。基线评测显示模型默认就会用 `MockClient`，因此在 skill 里把「默认 mocktail、何时用 MockClient」写成明确规则 |
| F5 | 目录：官方 `lib/{data,domain,ui}` vs feature-first | 见 F1 | 正文只写 feature-first 一种；`architecture.md` 里记录官方分层语义与升级路径 | 「正文只写裁决后的一种做法」 |
| F6 | 本地化生成产物位置 | 官方 skill #1：`synthetic-package: true` + `package:flutter_gen/gen_l10n/...`；docs.flutter.dev 当前页：生成到 `arb-dir`，相对路径 import | 采用官方文档写法；旧写法折叠进 `<details>` 的 Old pattern 区块并说明迁移动作 | 同一厂商内部，文档页比生成时间更早的 skill 更新；且旧写法在新 SDK 上直接报 URI 无法解析 |
| F7 | `ListView(shrinkWrap: true)` 是否可用于 `Column` 内 | #1 布局 skill 只给 `Expanded`；社区常见做法是 `shrinkWrap` | 正文写明 `shrinkWrap` 会关闭懒加载，是性能问题不是修复；给 `Expanded` 或 slivers | 官方约束 + 可验证的渲染行为 |
| F8 | 测试金字塔比例 | #6 给出分层比例建议；#3 强调「测试必须能因真实缺陷而失败」 | 采用 #3 的判据作为硬规则，比例只作为选层表出现，不写覆盖率目标 | 与本仓库 `docs/skill-standard.md` 的测试观一致：测试是长期负担，不是工作量证明 |
| F9 | MCP 工具引用 | #1/#2 正文直接引用 Dart MCP 工具名 | 全部改写为 `flutter`/`dart` CLI 命令 | 规范禁止 harness/agent 专属绑定；CLI 在任何 agent 下都可用 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| flutter-official | flutter/agent-plugins @ 9b8106d | merged | 工作流清单形态、分层语义、响应式布局与布局报错解码、widget/integration 测试、路由与原生深链配置、本地化、JSON、http |
| dart-official | dart-lang/skills @ c530d2c | merged | Dart 3 语言（模式匹配、primary constructors 及版本门槛）、analyzer 配置与 `dart fix`、运行时错误分诊、mocks、coverage、ffigen/FFI |
| evanca-rules | evanca/flutter-ai-rules @ b75d631 | merged | Riverpod/Bloc/Provider 主干、feature-first 目录策略、测试有效性判据、mocktail/patrol、常见 Flutter 报错目录 |
| sgruhier-flutter | sgruhier/superpowers-flutter @ 4c0034f | merged | Riverpod 3 正确性与 provider 选型、sealed state + 值相等、autoDispose/family 纪律、go_router/auto_route 模式、编号 widget 规则 |
| jeffallan-flutter | Jeffallan/claude-skills @ 882ef55 | merged | 仅 `references/performance.md` 的性能清单种子（其 Riverpod 示例弃用） |
| harish-flutter-tester | Harishwarrior/flutter-claude-skills @ 114379a | merged | 分层测试模式、Riverpod 容器测试、widget 测试深度 |
| flutter-docs | docs.flutter.dev（platform-channels、internationalization） | merged (kind: docs) | 平台通道 / 标准编解码类型映射 / 线程与后台 isolate / Pigeon；当前 l10n 流程 |

产物：`SKILL.md`（7 章节固定顺序）+ 14 个 references + `evals/`（4 场景，含 1 负例）。无 `scripts/`
——本领域没有比 `flutter analyze` / `flutter test` 更值得自写的检查器，写一个只会与 SDK 竞争。

## 基线缺口

无 skill（`uv run tools/run_evals.py flutter --baseline`，会话默认模型，2026-09-10）时各场景的判定。
四个场景 `skill_read` 均为 `false`（符合预期，`--no-skills`）。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 Riverpod 评审 | 「按文件分组 + 每条带严重度 + 收尾一行合并判定」**未达成** | 其余 5 条全部达成：指出 `StateNotifier`/`StateProvider` 在 Riverpod 3 已 legacy、给出 `AsyncNotifier` 重写、`const` 缺失、`Column` 应改 `ListView.builder`、`await` 后缺 `context.mounted`。输出按「严重/过时/质量」分组而非按文件，未给逐条严重度标签，判定句放在开头而非结尾 |
| 2 深链配置 | 全部达成 | 基线给出了 `GoRoute` 路径参数、`autoVerify` intent-filter、`assetlinks.json`（含双指纹）、AASA + Associated Domains、`adb`/`xcrun simctl` 验证命令。此场景对默认模型无区分度，保留用于第二模型与回归 |
| 3 测试 | 「同时点名 `flutter analyze` 作为第二道门」**未达成** | 基线用 `package:http/testing.dart` 的 `MockClient`（无 codegen，达成第 1 条改写后的期望）、断言了实际请求 URI、失败路径用 `throwsA(isA<WeatherException>())`；但只跑 `dart test`，从未提及 analyze |
| 4 负例（SwiftUI） | 全部达成，且 `skill_read == false` | 基线按 SwiftUI 审查并指出 `@State` 不应接收传入值，未提及任何 Flutter/Dart 内容 |

结论：默认模型的裸模型能力在本领域已经很强，缺口集中在**约定类知识**（评审输出契约、验证门），
这正是 skill 应该提供的部分；场景 1 的输出契约与场景 3 的 analyze 门构成本次的可测缺口。

**评测口径的一处修订（Phase D 后）**：场景 3 原第 1、2 条期望写的是「必须用 mocktail」与
「必须 `registerFallbackValue`」。三个 arm（基线 / 默认 + skill / @smol + skill）都选择了
`package:http/testing.dart` 的 `MockClient`，而这**正是本 skill 明文允许的逃生口**
（`references/testing.md`、`references/json-http.md`：不需要 `verify` 交互时 `MockClient` 合法）。
原期望编码的是一条 skill 并未主张的规则，属评测本身的缺陷，因此改写为「无 codegen 的边界打桩
（mocktail 或 `MockClient`），且不引入 mockito + build_runner；若用 mocktail 的 `any()` 传 `Uri`
则须 `registerFallbackValue`」与「断言实际发出的请求」。改写后的两条可以直接对已落盘的三份
`answer.md` 判定，无需重跑；判定结果见下表（两条在三个 arm 均达成，即无区分度，
区分度由第 4 条承担）。

## 评测结果

全部结果目录：`/tmp/hs-evals/flutter/<default|smol>/<baseline|skill>/<n>/`（`answer.md` + `result.json`）。
基线为会话默认模型 `--no-skills`；有 skill 两组分别为会话默认模型与 `@smol`。判定由人工读 `answer.md` 完成。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Riverpod 评审 | default | 无 | false | 5/6（缺输出契约） | 分组按严重度而非文件，无逐条严重度标签，判定句在开头 |
| 1 | default | 有 | **true** | **6/6** | 逐条 `L<line> blocking/important/minor`，按文件分组，收尾 `结论：rework` |
| 1 | @smol | 有 | **true** | **6/6** | 同上；额外指出 `filterProvider` 是 legacy `StateProvider` 且为死代码 |
| 2 深链 | default | 无 | false | 5/5 | 裸模型即可完整覆盖，本场景无区分度 |
| 2 | default | 有 | **true** | 5/5 | 补充了「嵌套路由才有回退栈」「router 只构造一次」「`extra` 不可序列化」 |
| 2 | @smol | 有 | **true** | 5/5 | 显式引用 `skill://flutter/references/navigation.md` 与其版本标注 |
| 3 测试 | default | 无 | false | 3/4（缺 analyze 门） | 只跑 `dart test` |
| 3 | default | 有 | **true** | **4/4** | 跑了 `dart format` + `dart analyze` + `dart test`，并做了变异检验 |
| 3 | @smol | 有 | **true** | **4/4** | 同样 `dart analyze` + `dart test` + 变异检验（改 `!= 200` 后两测均失败） |
| 4 负例（SwiftUI） | default | 无 | false | 3/3 | — |
| 4 | default | 有 | **false** | 3/3 | 明说「这是 SwiftUI，不走 flutter skill」，全程无 Flutter 内容 |
| 4 | @smol | 有 | **false** | 3/3 | 同上 |

结论：**通过**。

- 基线未达成、有 skill 达成的行为共两条，两种模型都达成：
  1. **场景 1 的评审输出契约**——按文件分组 + 每条 `path:line` + `blocking/important/minor`
     severity + 收尾一行合并判定。基线两次运行（含改写期望后的重跑）都是自创分组、无逐条严重度、
     判定句在开头；default 与 @smol 带 skill 后都严格产出 SKILL.md `## Output format` 的形状。
  2. **场景 3 的验证门**——把 `flutter analyze`（此环境无 Flutter SDK，退化为 `dart analyze`）
     与 `dart test` 一起作为必须通过的门。基线只跑测试。
- 负例场景两种模型 `skill_read` 均为 `false`，且回答里没有任何 Flutter/Dart 迁移建议，
  说明 description 的否定边界（`Do not use for ... SwiftUI ...`）生效。
- 副产品观察：@smol 带 skill 的场景 1 质量与 default 基本持平（同样识别 Riverpod 3 legacy、
  给出 `AsyncNotifier` 重写、抽出 `_TodoHeader`/`_TodoTile` widget 类），说明 skill 主要在
  「约定与结构」维度抬升较弱模型，而非补足其 Flutter 知识。

## 备注

- **许可**：BSD-3-Clause（两个官方仓库）要求保留版权与免责声明，由 `build_catalog.py` 生成的
  `NOTICE.md` 承担；MIT 三家同理；docs.flutter.dev 为 CC BY 4.0，仅取技术事实、措辞全部原创。
  sgruhier 仓库 GitHub API 报 NOASSERTION，实际 `LICENSE` 为 MIT（已在 `SOURCES.yaml` 备注）。
- **同步时要盯的上游**：`dart-lang/skills` 近乎日更（primary constructors 章节随语言演进）；
  `flutter/agent-plugins` 的 `rules/` 会先于 `skills/` 出现新规则；`evanca/flutter-ai-rules`
  的 `ATTRIBUTION.md` 变化意味着其上游许可面变化。
- **放弃的方向**：Firebase/FlutterFire（属后端域）、发布与商店（属发布域）、
  设计还原与 Figma（属 `frontend-design`）、Flame 游戏引擎、安全扫描（属 `security-review`）、
  以及「不 vendor 官方 Dart skills 而只做引用」这一方案——引用方案在离线或未安装官方 skill 的
  环境下直接失效，与本仓库「单 skill 自足」的定位冲突。
- **未来可选附加**：`FlutterFlow/shadertoy_to_flutter_skill`（shader 移植）如需可单独立项。
