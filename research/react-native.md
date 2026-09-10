# react-native 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"React Native agent skill SKILL.md github expo claude skills"`、
    `"react native" skill "New Architecture" OR TurboModule OR FlashList agent skills github 2026`、
    `site:skills.sh react-native expo skill`
  - <https://www.skills.sh>（`expo/skills`、`hairyf/skills`、`jezweb/claude-skills` 的 skill 页）
  - VoltAgent/awesome-agent-skills、addyosmani/agent-skills（无 React Native 条目）
  - 领域官方组织仓库：`expo/`、`callstackincubator/`、`react-native-community/`、`vercel-labs/`、
    `Shopify/`、`react-native-tvos/`
  - `github/awesome-copilot`：`skills/` 与 `instructions/` 全树 grep `react-native|expo|mobile`，
    只命中 `agents/gem-mobile-tester.agent.md` 与一个无关的 Illustrator 脚本，**没有** React Native 内容
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 正常：账号 Lynricsy，token scopes `gist, read:org, repo, workflow`）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `expo/skills`（`plugins/expo/skills/*`、`plugins/expo-experiments/skills/expo-migrate-module`） | https://github.com/expo/skills | 2514 | 2026-09-10 | MIT | Expo 全栈：expo-router、EAS Build/Update/app-stores、dev client、expo-module、brownfield、web→native、升级 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方 Expo 组织，21 个 skill 全是可执行规则（EAS Update 的 build/update/branch/channel/runtimeVersion 模型、two cold launches、native change 必须重新构建）。抽查 3 条（New Architecture 自 SDK 53 默认、`newArchEnabled`、`EXPO_PUBLIC_` 前缀）与 docs.expo.dev 一致 |
| 2 | `callstackincubator/agent-skills`（`skills/react-native-best-practices`、`upgrading-react-native`、`react-navigation`、`react-native-brownfield-migration`、`create-react-native-library`、`assess-react-native-migration`） | https://github.com/callstackincubator/agent-skills | 1642 | 2026-08-08 | MIT | 性能（FPS/TTI/bundle/memory）、升级（Upgrade Helper + rn-diff-purge）、react-navigation 7、brownfield、库脚手架 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE | Callstack 是 RN 领域公认专家（《Ultimate Guide to React Native Optimization》作者）。`references/` 40+ 篇全是带命令与版本护栏的规则（FlashList v1 vs v2、Hermes mmap 与 0.79 分界、Turbo Module 线程表）。唯一问题是绑定自家 `agent-device` CLI，需剥离 |
| 3 | `vercel-labs/agent-skills`（`skills/react-native-skills`，含 40 条 `rules/*.md`） | https://github.com/vercel-labs/agent-skills | 31033 | 2026-08-28 | NONE（API `license: null`，仓库无 LICENSE 文件；skill frontmatter 自称 MIT） | 列表性能 8 条、动画 3 条、原生导航、UI 模式、monorepo、React Compiler 交互 | 2 | 3 | 3 | 3 | 0 | 11 | INCLUDE | 规则粒度最细的一份（每条一个文件，incorrect/correct 成对）。抽查 3 条（native-stack 优于 JS stack、`onLayout` 优于 `measure()`、animate 只改 transform/opacity）与 reactnative.dev/react-navigation 文档一致。**许可 0 分**：仓库根无 LICENSE，按无许可规则以 `license: NONE` 合入，不复制任何原文 |
| 4 | `react-native-community/skills`（`upgrade-react-native`、`migrate-to-strict-api`） | https://github.com/react-native-community/skills | 27 | 2026-08-05 | MIT | RN 升级、Strict TypeScript API 迁移 | 3 | 2 | 3 | 3 | 2 | 13 | INCLUDE | star 低但组织是 RN 官方社区（0.84 发布公告直接推荐它的 `upgrade-react-native`）。`migrate-to-strict-api` 给出 0.87 默认、0.80–0.86 opt-in、`customConditions` 必须同时含 `react-native`、`no-deep-imports` autofix，这些在别处找不到 |
| 5 | reactnative.dev（New Architecture / Turbo Native Modules / Hermes / 0.84 与 0.82 发布公告 / Strict TypeScript API） | https://reactnative.dev/architecture/landing-page | — | 持续 | CC-BY-4.0（docusaurus 站点） | 架构事实、codegen 契约、版本分界 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `kind: docs`。所有版本敏感断言（0.82 New Architecture 唯一运行时、0.84 Hermes V1 默认 + Node 22.11 + iOS 预编译二进制 + legacy 代码默认编译掉但 interop 层保留、0.87 Strict API 默认）以此为准 |
| 6 | docs.expo.dev（EAS Update / runtime versions / new-architecture / development builds） | https://docs.expo.dev/eas-update/how-it-works/ | — | 持续 | 站点条款（技术事实取用，无原文复制） | EAS 概念模型与 CLI 流程 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `kind: docs`。校正 `expo/skills` 里的 EAS 事实，并提供 SDK↔RN 版本对应关系 |
| 7 | `maikotrindade/awesome-react-native-skills` | https://github.com/maikotrindade/awesome-react-native-skills | 11 | 2026-05-21 | GPL-3.0 | react-native-core / ecosystem / expo / performance / testing + callstack 的 brownfield 与 github-actions 副本 | 1 | 1 | 2 | 2 | 0 | 6 | MAYBE → reference | **GPL-3.0，按许可规则只能 `reference`**。它的 `react-native-core`/`react-native-testing` 主题清单用来核对本 skill 覆盖面（testing 与 accessibility 是否有缺口），正文不取一句。`react-native-brownfield-migration` 与 `github-actions` 是 callstack 上游的再分发，无独立价值 |
| 8 | `hairyf/skills`（`skills/react-native-expo`） | https://github.com/hairyf/skills | 25 | 2026-08-10 | MIT | 由 `expo/expo` 文档脚本生成的 Expo 手册（app config、Metro、CNG/prebuild、EAS） | 1 | 2 | 2 | 3 | 2 | 10 | MAYBE → 未采用 | 内容正确但本质是 Expo 文档的机器改写，覆盖面被 `expo/skills` + docs.expo.dev 完全包住；再引入一个上游只增加同步成本，不增加信息。仅用于交叉校验 CNG/prebuild 段落 |
| 9 | `jezweb/claude-skills`（`plugins/frontend/skills/react-native`） | https://github.com/jezweb/claude-skills | 1000 | 2026-07-02 | MIT | 列表性能、动画、导航、UI、状态、Expo 工作流 | 1 | 2 | 2 | 1 | 2 | 8 | MAYBE → 未采用 | 自述「This is a starting point」，规则是 vercel-labs 规则集的浓缩版，且带 `compatibility: claude-code-only` 与 `allowed-tools`。抽查 3 条：FlatList/FlashList 与 Reanimated 正确，但仍把 `estimatedItemSize` 当 FlashList 通用必填项（v2 已移除）→ 正确性扣分。信息全部被 3 号覆盖 |
| 10 | `secondsky/claude-skills`（`plugins/react-native-skills`） | https://github.com/secondsky/claude-skills | 217 | 2026-09-09 | MIT | 与 3 号逐字相同的 `rules/*.md` | 1 | 3 | 3 | 3 | 2 | 12→REJECT | REJECT | 逐文件比对为 `vercel-labs/agent-skills` 的 vendored 副本（同名 `AGENTS.md`/`metadata.json`/40 条规则）。收它等于把同一份内容 pin 两次，同步时会互相打架。取上游本身（3 号） |
| 11 | `ospfranco/rn-skills` | https://github.com/ospfranco/rn-skills | 13 | 2026-07-26 | MIT | JSI HostObject / NativeState / zero-copy buffer / 可替换后端的 C++ 模板 | 1 | 2 | 3 | 2 | 2 | 10 | MAYBE → reference 未采用 | 质量不差，但内容 100% 是 C++/JSI 实现体，正好落在本 skill 的否定边界（原生语言内部实现）之外的另一侧——它连「声明与桥接契约」都不讲，只讲 HostObject 的 C++ 写法。收进来会诱导 skill 越界写 C++ |
| 12 | `Shopify/flash-list`（`.claude/skills/*`） | https://github.com/Shopify/flash-list | 7206 | 2026-09-07 | MIT | 维护 FlashList 仓库本身的 issue/PR/triage/device 工作流 | 3 | 3 | 2 | 3 | 2 | 13→REJECT | REJECT | 星数与权威性都够，但这些 skill 是给 FlashList 维护者用的（修 issue、跑 PR 测试、triage），不是给应用开发者的 FlashList 用法。v2 的行为事实改从 `shopify.github.io/flash-list` 的 v2-changes 页与安装版本取证 |
| 13 | `rajivmanivannan/rn-new-arch-migration-skill` | https://github.com/rajivmanivannan/rn-new-arch-migration-skill | 2 | 2026-03-22 | MIT | 扫描依赖/JS/iOS/Android 产出 New Architecture 就绪度报告（只读，不改代码） | 0 | 1 | 2 | 1 | 2 | 6 | REJECT | 单人仓库、6 个月边缘新鲜度，且核心前提已过期：它面向「是否可以开启 New Architecture」，而 0.82 起 New Architecture 是唯一运行时，审计对象不存在了。明确排除 Expo 托管项目 |
| 14 | `react-native-tvos/skills` | https://github.com/react-native-tvos/skills | 3 | 2026-05-16 | MIT | react-native-tvos 的 TV 专属工作流 | 1 | 1 | 2 | 2 | 2 | 8 | REJECT | TV（焦点管理、10-foot UI、遥控器）不在本 skill 边界内；同理 callstack 的 `skills/react-native-tv-best-practices` 也不进 `paths` |
| 15 | `iFixit/expo-skills` | https://github.com/iFixit/expo-skills | 0 | 2026-07-16 | MIT | 单公司内部 Expo 约定 | 0 | 2 | 1 | 1 | 2 | 6 | REJECT | 0 star、公司内部约定（自家 monorepo 路径与内部包），不可迁移 |
| 16 | `bamlab/helpmeai` | https://github.com/bamlab/helpmeai | 0 | 2026-03-11 | MIT | skill 索引 JSON + 少量 RN 条目 | 0 | 1 | 1 | 1 | 2 | 5 | REJECT | 是一个 skill 分发索引而非内容仓库，且 6 个月未推送 |
| 17 | `clerk/skills`（`clerk-expo`） | https://github.com/clerk/skills | 71 | 2026-09-09 | NONE | Clerk 在 Expo 里的接入 | 1 | 3 | 2 | 2 | 0 | 8 | REJECT | 产品说明书（单一 SaaS SDK 接入），按批次约定排除单库包装类 |
| 18 | `github/awesome-copilot` | https://github.com/github/awesome-copilot | 38858 | 2026-09-10 | MIT | — | 3 | 3 | — | — | 2 | — | REJECT（无内容） | 按流程必查的官方目录。全树 grep `react-native|expo|mobile` 仅命中 `agents/gem-mobile-tester.agent.md`（一个测试用 agent 定义，非 RN 指南）。GitHub 官方目录里没有 React Native/Expo skill 或 instruction |
| 19 | `vercel-labs/vercel-react-native-skills` | https://github.com/vercel-labs/vercel-react-native-skills | — | — | — | — | — | — | — | — | — | — | 仓库不存在，剔除 | `gh api repos/vercel-labs/vercel-react-native-skills` 返回 404 Not Found。路线图旧种子已失效；实际存在的是 `vercel-labs/agent-skills` 的 `skills/react-native-skills`（3 号），本次以它替代 |
| 20 | `mahdidavoodi7/react-native-skills` | — | — | — | — | — | — | — | — | — | — | — | 仓库不存在，剔除 | 批次说明里点名排除的单库包装仓库；`gh api` 亦返回 404，无需再评 |

## 深度审查

### 1. `expo/skills`（INCLUDE，主干之一）

- 结构：`plugins/<plugin>/skills/<name>/{SKILL.md,references/,agents/openai.yaml,scripts/}`。21 个 skill 明确分成
  「OSS 框架层」（`expo-router`、`expo-module`、`expo-dom`、`expo-native-ui`、`expo-ui`、`expo-brownfield`、
  `expo-web-to-native`、`expo-project-structure`、`expo-upgrade`）与「EAS 付费服务层」（`eas-*` 7 个）。
- frontmatter：带 `version`、`allowed-tools`（如 `Bash(npx expo *), Bash(npx *eas-cli@*)`）等非规范字段，
  合入时必须剥离；`eas-*` 的 description 以 `EAS service (paid).` 开头，本仓库不做付费声明，改为在正文写清
  「EAS 是托管服务」。
- 质量：EAS Update 那篇是本次调研见到的最好一篇——它不教 CLI 参数，而是给一个可判定的模型
  （build / update / branch / channel / runtimeVersion 五个对象 + 匹配规则），再给「不要为了让更新立刻生效
  而调 `fallbackToCacheTimeout`」这类反向约束。`expo-web-to-native/references/false-friends.md` 是 web→native
  的错位对照表（`onClick`→`onPress`、相对 `fetch` 无 origin、`localStorage` 走 `expo-sqlite`、
  Stripe 数字商品会被商店拒审），信息密度极高。
- agent 绑定：`expo-skill-feedback` 会调 `npx submit-expo-feedback` 上报遥测，且每个 SKILL.md 尾部都有
  「Submitting Feedback」段——**遥测与反馈段一律不合入**。
- 与其他候选重叠：与 3 号在「用 `expo-image`、原生 tabs、原生 modal」上重叠，与 2 号在 brownfield 与升级上重叠。

### 2. `callstackincubator/agent-skills`（INCLUDE，主干之一）

- 结构：`skills/<name>/{SKILL.md,references/*.md,agents/openai.yaml}`，`references` 用
  `js-*` / `native-*` / `bundle-*` 前缀分组，SKILL.md 只做「问题 → 从哪篇开始」的路由。这套形态与本仓库的
  `## Topic router` 天然对齐。
- frontmatter：只有 `name`/`description`/`license`，干净。
- 质量：版本护栏写得非常自觉——「FlashList v2 不再需要 `estimatedItemSize`，不要把它当缺失项报出来」、
  「0.79+ Android 默认不压缩 JS bundle，改查 `react { enableBundleCompression }` 而不是手写
  `androidResources.noCompress`」、「同步 Turbo Module 方法阻塞 JS 调用方，线程名与调度随版本变化，
  以 profiler 为准」。`upgrade-helper-core.md` 给出 rn-diff-purge 的 `RELEASES` 与原始 diff URL、
  `RnDiffApp` 占位符重映射、一次性安装而非逐包安装、gradle-wrapper.jar 也要换。
- agent 绑定：性能与验证流程大量依赖自家 `agent-device` CLI 与 `@callstack/inspector`。本 skill 改写为
  「React Native DevTools 的 Profiler + 设备/模拟器手动复现」，把厂商工具降级为可选项。
- 与其他候选重叠：`react-navigation` 与 `expo/skills` 的 `expo-router` 是两条路线（见冲突表 3）。
- 不采用的目录：`react-native-tv-best-practices`（TV 越界）、`github-actions`（属 CI，不在边界内）、
  `plugins/vendored/*`（`agent-device`/`dogfood` 是厂商工具说明书）。

### 3. `vercel-labs/agent-skills` 的 `skills/react-native-skills`（INCLUDE，规则层）

- 结构：`SKILL.md` + 40 个 `rules/<prefix>-<slug>.md` + 一份合并后的 `AGENTS.md` + `metadata.json`。
  每条规则一个文件，固定含 incorrect/correct 成对代码，正是「教失败而非教 API」的形态。
- frontmatter：`metadata.author: vercel`、`metadata.version`，需剥离；`rules/*.md` 的 frontmatter 有
  `impact`/`impactDescription`/`tags` 三个私有字段。
- 质量：`list-performance-*` 8 条是本次最系统的列表规则集；`ui-measure-views`（用 `onLayout` 而非
  `measure()`）、`rendering-text-in-text-component`（裸字符串放在 `View` 里会抛错）、
  `react-compiler-reanimated-shared-values`（React Compiler 与 Reanimated shared value 的交互）
  都是别处没有的具体坑。
- 许可：仓库根**没有 LICENSE 文件**（`gh api repos/vercel-labs/agent-skills/license` → 404），
  只有 skill frontmatter 写 `license: MIT`。按批次许可规则，视同「无许可但公开」：`license: NONE` + notes，
  不复制任何原文。
- 与其他候选重叠：9 号、10 号都是它的下游；`ui-*` 与 `expo/skills` 的 `expo-native-ui` 重叠。

### 4. `react-native-community/skills`（INCLUDE，升级与类型层）

- 结构：仓库根直接是两个 skill 目录（`upgrade-react-native/`、`migrate-to-strict-api/`），后者带
  `references/library-compatibility.md`。
- frontmatter：`migrate-to-strict-api` 有 `metadata.author: react-native-community`，并在正文写
  `Invoke with /migrate-to-strict-api`（slash command 绑定），合入时都要去掉。
- 质量：Strict API 那篇的关键信息无可替代——`customConditions` 是**替换**而非合并继承配置，
  所以 0.80–0.86 opt-in 必须同时写 `["react-native", "react-native-strict-api"]`；
  `node_modules` 内部报错要靠升级库或 `paths` 重定向到无类型 stub（`@ts-ignore` 无效，因为报错点在库文件里）；
  `types_generated/index.d.ts` 是深导入→根导入映射的唯一真源。
- 权威性：RN 0.84 发布公告在「Upgrading」一节直接推荐该仓库的 `upgrade-react-native`，可视作官方背书。

### 5. reactnative.dev / docs.expo.dev（INCLUDE，`kind: docs`）

- 用途：所有版本分界事实的取证源，且用来推翻上游里已经过期的说法。
- 关键取证：`/architecture/landing-page`（0.76 起 New Architecture 默认、JSI 取代 bridge、
  同步 layout effect、并发特性）、`/docs/turbo-native-modules-introduction`（spec 必须 `Native` 前缀、
  `codegenConfig` 四个字段、`getEnforcing` vs `get`、iOS 走 `pod install`、
  Android 走 `generateCodegenArtifactsFromSchema`）、`/docs/hermes`（`global.HermesInternal` 探测、
  bundled Hermes）、`/blog/2026/02/11/react-native-0.84`（Hermes V1 默认、Node 22.11 下限、
  iOS 预编译二进制默认、legacy 架构代码默认编译掉而 **interop 层保留**、0.82 起 New Architecture 唯一运行时）、
  `/docs/strict-typescript-api`（0.87 默认）。
- Expo 侧：SDK↔RN 对应（SDK 53+ New Architecture 默认；SDK 56 对应 RN 0.85）、
  EAS Update 的 runtime version 策略、`EXPO_PUBLIC_` 前缀语义。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | FlashList 是否需要 `estimatedItemSize` | 9 号（jezweb）与大量社区材料：列表优化必须传 `estimatedItemSize`；2 号（callstack）：v1 需要，v2 起该属性连同 `estimatedListSize`/`estimatedFirstItemOffset` 已废弃，不要报为缺失 | 采纳 2 号：**先读安装的 FlashList 主版本**，v2+ 不传任何 estimated* 属性 | 「更新 > 更旧」+ 官方 FlashList v2-changes 页；本机 `npm view @shopify/flash-list version` = 2.3.2，v2 已是当前线 |
| 2 | 是否要教「如何开启 New Architecture / 如何回退」 | 13 号整个 skill 以「审计 New Architecture 就绪度」为前提；2 号仍保留 `newArchEnabled` 相关排查；官方 0.84 公告：0.82 起 New Architecture 是唯一运行时，0.84 起 legacy 代码默认不编译进 iOS 包，interop 层保留 | 正文只写「0.76+ 默认、0.82+ 唯一运行时」；不写开关矩阵，把 `newArchEnabled=false` 归入 `## Old patterns` 折叠块 | 官方厂商 > 社区；且「更新 > 更旧」 |
| 3 | 导航用 react-navigation 还是 Expo Router | 2 号（callstack `react-navigation`，只支持 v7）；1 号（`expo-router`，且 SDK 56+ 禁止直接从 `@react-navigation/*` 导入，要走 `expo-router/react-navigation`） | 不选边：**按项目已装依赖决定**（有 `expo-router` → Expo Router 且遵守 SDK 56+ 的重导出规则；否则 react-navigation 7）。两边共同的硬规则（原生 stack 优于 JS stack、原生 tabs、safe-area）提升为 Core rules | 两个上游都是各自框架的权威，冲突源于框架不同而非对错；标准第 3 节要求「一个默认方案 + 一个逃生口」，此处默认由依赖检测给出 |
| 4 | 静态 API 还是动态 API（react-navigation 7） | 2 号：已有项目跟随现状，新项目优先 Static API | 直接采纳 | 唯一主张者且与 react-navigation 7 官方文档一致 |
| 5 | Android JS bundle 压缩/Hermes mmap 怎么写 | 2 号给了 `androidResources { noCompress += ["bundle"] }`，同时注明 0.79+ 默认已不压缩，应改查 `react { enableBundleCompression }` | 正文只写 0.79+ 的现状（默认已可 mmap，不要手加 `noCompress`），旧写法进 `## Old patterns` | 「不写时间敏感表述」+ 弃用内容折叠 |
| 6 | 原生模块内部实现要不要写 | 2 号 `native-turbo-modules.md` 给了完整 Swift/Kotlin 实现；11 号（ospfranco）全是 C++/JSI HostObject | 本 skill 只写**声明与桥接契约**（TS spec、`codegenConfig`、注册名、同步/异步语义、线程约束），Swift/Objective-C 内部实现转 `apple`，Kotlin/Java 转 `android` | 波次 1 边界契约；避免与同波 `apple`/`android` 重复 |
| 7 | 性能验证工具链 | 2 号大量依赖自家 `agent-device` CLI 与 `@callstack/inspector`；1 号在 brownfield 验证里也要求 `agent-device` | 改写为 React Native DevTools 的 Profiler + 设备手动复现；厂商 CLI 只在「已装」时作为逃生口一句话提及 | 标准第 1.3 节禁止 agent 专属绑定；一个 skill 不能强制安装某厂商 CLI |
| 8 | EAS Update 迟迟不生效怎么处理 | 社区常见答案：把 `fallbackToCacheTimeout` 调大以便启动时等更新；1 号：不要为了让更新立刻可见而改它，这是拿启动延迟换更新时效 | 采纳 1 号，并把「release build 需要最多两次冷启动」写成可判定步骤 | 官方厂商；且该主张有明确的代价说明 |
| 9 | React Native 0.84 的 Node 下限 | 官方 0.84 发布公告：「requires Node.js v22.11 or later」；npm 上 `react-native@0.84.0` 的 `engines.node` 实际是 `>= 20.19.4`，到 0.87.1 才收紧为 `^22.13.0 \|\| ^24.3.0 \|\| >= 26.0.0` | 正文不写「0.84 起 Node 22.11」，改为「读目标版本自己的 `engines.node`」并给出 0.87 的实际约束 | 本机 `npm view react-native@<v> engines` 实查（0.83.10/0.84.0 = `>= 20.19.4`，0.85.0/0.86.3 = `^20.19.4 \|\| ^22.13.0 \|\| ^24.3.0 \|\| >= 25.0.0`，0.87.1 = `^22.13.0 \|\| ^24.3.0 \|\| >= 26.0.0`）。发布公告与实际发布物冲突时，以装得上/装不上的那个为准 |
| 10 | Jest preset 从哪里来 | 社区与旧模板：`preset: 'react-native'`；实测 `react-native` 包 0.86.3 仅剩 `jest-preset.js` 一个文件，0.87.1 起 `/jest*` 全部不存在，`@react-native/jest-preset@0.87.1` 独立发布 | 正文写「用 `@react-native/jest-preset`（Expo 用 `jest-expo`）；0.87 起包内 preset 已移除」 | jsDelivr 文件清单实查 + `npm view @react-native/jest-preset version` |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `expo-official` | `expo/skills` | merged | Expo Router 路由约定与 SDK 56+ 的 `expo-router/react-navigation` 规则；EAS Build/Update/app-stores 流程与 build/update/branch/channel/runtimeVersion 模型；development build vs Expo Go；`expo prebuild`/CNG；Expo module（config plugin、native module 声明）；brownfield 的 Expo 轨；web→native 错位对照 |
| `callstack-rn` | `callstackincubator/agent-skills` | merged | 性能骨架（FPS/TTI/bundle/memory 的 measure→fix→re-measure 循环）与列表、TextInput、view flattening、Hermes/bundle 规则；升级流程（Upgrade Helper + rn-diff-purge 版本对 diff、`RnDiffApp` 占位符、一次性安装、双平台构建门）；react-navigation 7 的 Static API 与原生导航；brownfield 的 bare 轨与 XCFramework/AAR 打包；`create-react-native-library` 脚手架 |
| `vercel-rn-rules` | `vercel-labs/agent-skills` | merged | 列表性能 8 条规则的语义（虚拟化、item memo、稳定回调、内联对象、item type）、`onLayout` 优于 `measure()`、裸文本必须在 `Text` 里、原生 navigator 优先、monorepo 原生依赖归属、React Compiler 与 Reanimated shared value 的交互 |
| `rn-community` | `react-native-community/skills` | merged | Strict TypeScript API 迁移（0.87 默认 / 0.80–0.86 opt-in、`customConditions` 替换语义、`no-deep-imports` autofix、`types_generated/index.d.ts` 映射、`node_modules` 内报错的处理）与官方推荐的升级 skill 口径 |
| `rn-docs` | reactnative.dev | merged (`kind: docs`) | 架构与版本分界的取证：New Architecture（JSI/Fabric/TurboModules）、Turbo Native Module 的 spec 与 codegen 契约、`getEnforcing` vs `get`、Hermes 与 `global.HermesInternal`、0.82/0.84/0.87 的分界事实、interop 层的能力与限制 |
| `expo-docs` | docs.expo.dev | merged (`kind: docs`) | EAS Update 的 runtime version 与兼容性判定、channel/branch 语义、development build 与 Expo Go 差异、SDK↔RN 版本对应、`EXPO_PUBLIC_` 语义 |
| `maiko-awesome-rn` | `maikotrindade/awesome-react-native-skills` | reference | GPL-3.0，只用其 `react-native-core`/`react-native-testing`/`react-native-ecosystem` 主题清单核对覆盖面（据此补齐 testing 与 Reanimated/gesture 两处），正文未取任何文字 |

## 基线缺口

无 skill（`uv run tools/run_evals.py react-native --baseline`，模型 `claude-opus-5:medium`）时，各场景未达成的
`expected_behavior`。基线本身很强（5 个场景全部产出可用答案，场景 3 甚至真装了 0.79.7 与 0.87.1 两套
依赖跑 `tsc` 取证），所以缺口集中在**版本分界事实**与**平台交付生命周期**这两类「读过文档才知道」的知识上：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 Turbo Module 迁移 | #5「New Architecture 自 0.82 起是唯一运行时；未迁移的 legacy 模块靠 interop 层继续工作，所以迁移买的是 codegen 类型安全与懒加载，不是修崩溃」 | 基线把 spec / `codegenConfig` / `getEnforcing` vs `get` / 同步方法阻塞都写对了，但全程没有给出版本分界；只在验证步骤里顺带提了一次 interop 层，没有说明「不迁移也不会崩」这个前提，读者会以为这是一次抢救 |
| 2 列表性能 | 无 | 基线全部达成，包括「FlashList v2 不要传 `estimatedItemSize`」这一条。该场景在有 skill 时只能验证不倒退，不构成缺口 |
| 3 版本升级 | #1 的一半（用了 Upgrade Helper，但没有说 diff 里的 `RnDiffApp` 是占位符、要重映射并按合并而非覆盖处理）、#4「0.84 起 Hermes V1 为默认引擎，退出方式是 `hermes-compiler` override / `hermesV1Enabled=false` + 从源码构建，而不是应用层开关」 | Hermes V1 一个字都没提。这是 0.84 最大的运行时变化，升级后如果出现引擎相关的行为差异，不知道这条就无从下手 |
| 4 EAS Update | #4「release build 通常先跑缓存里的更新、在后台下载，下一次启动才应用；手工验证需要最多两次完整冷启动（终止而非切后台）」 | 基线把 channel/branch 错配与「原生依赖不能 OTA」这两个真故障都抓住了，但没有给验证方法；按它的步骤修完，用户很可能在第一次重启没看到变化后又去改 runtimeVersion |
| 5 Next.js（负例） | 无（本就是负例：`skill_read == false`，答复完全在 React 侧，未提 React Native/Expo/FlashList） | 基线行为已正确，本场景验证的是「有 skill 时不被误触发」 |

## 评测结果

夹具与查询完全相同，两组唯一差别是 `--no-skills` / `--skills react-native`。判定依据是
`/tmp/hs-evals/react-native/anthropic-claude-opus-5-medium/{baseline,skill}/<i>/answer.md` 全文。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Turbo Module 迁移 | claude-opus-5:medium | 无（baseline） | false | #1 #2 #3 #4 #6（5/6） | spec + `codegenConfig` + `getEnforcing`/`get` + 同步方法阻塞全对，还正确指出「只有 iOS 实现所以该用 `get`」。**#5 未达成**：没有 0.82 分界，也没说明未迁移的模块靠 interop 层照常工作 |
| 1 Turbo Module 迁移 | claude-opus-5:medium | 有 | true | #1 #2 #3 #4 #5 #6（6/6） | 开头即给 Stack 行与「靠 interop 层还能跑，迁移买的是 codegen 类型安全 + 懒加载，不是修崩溃」，结尾写「0.76 起默认、0.82 起唯一运行时，不需要 `newArchEnabled`」。额外把 `describeDevice()` 在 render 路径同步调用判为本文件真正的缺陷 |
| 2 列表性能 | claude-opus-5:medium | 无（baseline） | false | #1 #2 #3 #4 #5 #6（6/6） | 基线已知道 FlashList v2 自测量、不该传 `estimatedItemSize`，并给了 `dumpsys gfxinfo` + Hermes profiler 的前后测量。无缺口 |
| 2 列表性能 | claude-opus-5:medium | 有 | true | #1 #2 #3 #4 #5 #6（6/6） | 同样全达成，另外加了「把 2000 行换成 200 行耗时不应变化」作为虚拟化生效的判定式，以及「只回滚 `Intl` 提升这一项再测」的单变量验证。等价，不倒退 |
| 3 版本升级 | claude-opus-5:medium | 无（baseline） | false | #2 #3 #5 #6（4/6，#1 半条） | 极其扎实（真装了 0.79.7 与 0.87.1 两套依赖跑 `tsc`），Node engines、Strict API、0.82 强制新架构、双平台构建门都对。**#1 只有一半**：用了 Upgrade Helper，但没说 diff 里的 `RnDiffApp` 是占位符、要重映射并合并而非覆盖。**#4 完全未达成**：Hermes V1 一字未提 |
| 3 版本升级 | claude-opus-5:medium | 有 | true | #1 #2 #3 #5 #6 达成，#4 部分（约 5.5/6） | #1 补齐：「remap `RnDiffApp`/`com.rndiffapp` 为真实名并**合并**（绝不整文件覆盖）」。#4 部分达成：把 0.84 的 Hermes V1 与 iOS 预编译二进制列为三个原生地板之一，并给了 `RCT_USE_PREBUILT_RNCORE=0 RCT_REMOVE_LEGACY_ARCH=0` 的临时手段，但没有给 Hermes V1 自身的退出方式（`hermes-compiler` override / `hermesV1Enabled=false`）。另外自行按 `engines.node` 实查而非采信发布公告，与冲突裁决 9 一致 |
| 4 EAS Update | claude-opus-5:medium | 无（baseline） | false | #1 #2 #3 #5 #6（5/6） | 两个真故障（channel `production-v5` vs branch `production`、mmkv 是原生依赖不能 OTA）都抓住了，也没有建议动 `fallbackToCacheTimeout`。**#4 未达成**：没有给 release build 的「最多两次冷启动」验证方法 |
| 4 EAS Update | claude-opus-5:medium | 有 | true | #1 #2 #3 #4 #5 #6（6/6） | #4 补齐并写成可执行步骤：「完全终止 App（不是切后台）→ 打开（下载）→ 再终止 → 再打开（生效）」，同时明确「不要为了跳过第二次去调 `fallbackToCacheTimeout`，那是拿启动延迟换即时性」，并给出 `channel:view` / `branch:view` 查证命令 |
| 5 Next.js（负例） | claude-opus-5:medium | 无（baseline） | false | #1 #2 #3（3/3） | 完全在 React 侧作答：state 下沉 + `useDeferredValue`，未提 React Native |
| 5 负例 | claude-opus-5:medium | 有 | **false** | #1 #2 #3（3/3） | 关键结果：skill 可用但未被加载（`skill_read == false`）。答复全文对 react native / expo / flashlist 的匹配数为 0，说明 description 的否定边界生效 |

结论：**通过**。基线未达成、有 skill 时达成的行为共三条半：

1. 场景 1 #5 —— New Architecture 自 0.82 起是唯一运行时，未迁移模块靠 interop 层继续工作，因此迁移
   买的是 codegen 类型安全与懒加载而非修崩溃（基线完全没有这层版本分界）。
2. 场景 3 #1 的后半 —— `RnDiffApp` 是占位符，要重映射并按合并而非覆盖处理。
3. 场景 3 #4 —— 0.84 起 Hermes V1 为默认引擎（部分达成：给了分界与 iOS 从源码构建的临时手段，
   未给 Hermes V1 自身的退出开关）。
4. 场景 4 #4 —— release build 的「最多两次冷启动」验证方法，以及不要用
   `fallbackToCacheTimeout` 抵消它。

没有任何一条基线已达成的行为在有 skill 时倒退；场景 2 两组等价（6/6），场景 5 负例在两组中
`skill_read` 都是 `false`，即 skill 存在时也不会被 React/Next.js 任务误触发。

## 备注

- **许可注意**：`vercel-labs/agent-skills` 仓库根无 LICENSE 文件（`gh api .../license` → 404），
  仅 skill frontmatter 自称 MIT。按批次规则记为 `license: NONE` 并在 `notes` 写明「无许可文件，
  按仓库的宽松署名惯例使用，未逐字复制」。`maikotrindade/awesome-react-native-skills` 为 GPL-3.0，
  只能 `relation: reference`。
- **种子更正**：路线图种子 `vercel-labs/vercel-react-native-skills` 与 `mahdidavoodi7/react-native-skills`
  均返回 404（仓库不存在），已从候选中剔除；前者的实际替代是 `vercel-labs/agent-skills`
  的 `skills/react-native-skills`。
- **临界上游复核**：`maikotrindade/awesome-react-native-skills` 推送于 2026-05-21（约 3.7 个月），
  在 6 个月窗口内，但因 GPL 只作 reference；`rajivmanivannan/rn-new-arch-migration-skill`
  推送于 2026-03-22（约 5.7 个月），已接近窗口边缘且前提过期，REJECT。
- **未来同步要盯**：`expo/skills` 与 `callstackincubator/agent-skills` 更新很快（前者本次调研当天仍有推送）；
  `react-native-community/skills` 的 `migrate-to-strict-api/references/library-compatibility.md`
  是一份会持续变化的库兼容清单，本 skill 只引用其存在而不复制清单内容，避免过期。
- **放弃的方向**：TV（callstack 的 `skills/react-native-tv-best-practices`、`react-native-tvos/skills`）、
  CI workflow（callstack 的 `skills/github-actions`）、C++/JSI HostObject 写法（ospfranco）——
  前两者越界，第三者落在原生实现侧。
