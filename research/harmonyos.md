# harmonyos 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

本 skill 针对 **HarmonyOS NEXT**（纯血鸿蒙，AOSP-free），**API version 12 起，默认生产基线
API 20+（6.0.0(20)）**。不覆盖早期兼容 Android 的 HarmonyOS 2/3/4（FA 模型 + Android 运行时）。
API 版本序（官方复核，见「冲突与裁决」#1）：
`26.0.0 > 6.1.1(24) > 6.1.0(23) > 6.0.2(22) > 6.0.1(21) > 6.0.0(20) > 5.1.1(19) > 5.1.0(18) > 5.0.5(17) > … > 5.0.0(12)`。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `gh search repos "harmonyos skills"` / `"arkts agent skill"` / `"harmony claude skill"`
  - `web_search`：`HarmonyOS NEXT agent skill SKILL.md github ArkTS 鸿蒙 skills`
  - 路线图种子（`docs/roadmap.md` 波次 8）
  - 领域官方组织：`openharmony/*`（GitHub 镜像，原生仓在 gitee/gitcode）、developer.huawei.com
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`，
  许可一律**实读 LICENSE 正文**，不只看 `spdx_id`。

### 许可实读结论（逐仓）

| 仓库 | API `spdx_id` | 实读 LICENSE 正文 | 结论 |
|---|---|---|---|
| `openharmony/docs` | `CC-BY-4.0` | 首行 `Attribution 4.0 International`，正文无 NonCommercial / NoDerivatives 条款 | **CC-BY-4.0，可 merged（需署名）** |
| `openharmony/interface_sdk-js` | `Apache-2.0` | 首行 `Apache License Version 2.0` | **Apache-2.0，可 merged** |
| `openharmony/applications_app_samples` | `NOASSERTION` | 实读为**混合许可**：`Testing Materials under this file are licensed under License Agreement for Testing Materials. All other materials under this file, including codes are licensed under Apache License V 2.0` | 代码 Apache-2.0，测试材料另有协议 → **按目录/材料类型逐个确认后才可 merged**；本轮未引用，故不采用 |
| `openharmony/{arkui_ace_engine,ability_ability_runtime,developtools_ace_ets2bundle,arkcompiler_ets_frontend}` | `Apache-2.0` | 均为 Apache-2.0 | 可 merged，但属引擎/运行时/构建链**实现**而非应用开发指南，本轮不采用 |
| `CoreyLyn/harmonyos-skills` | `MIT` | `MIT License / Copyright (c) 2026 corey` | MIT，可 merged |
| `web-infra-dev/midscene-skills` | `MIT` | `MIT License / Copyright (c) 2024-present Bytedance, Inc.` | MIT，可 merged |
| `EarFrog/harmonyos-arkts-skill` | `Apache-2.0` | `Apache License Version 2.0` | Apache-2.0，可 merged |
| `DengShiyingA/harmonyos-ai-skill` | `MIT` | `LICENSE` 存在，MIT | MIT，可 merged |
| `yibaiba/harmonyos-skills-pack` | `MIT` | `LICENSE` 存在，MIT | MIT，可 merged |
| `openharmonyinsight/openharmony-skills` | `null` | 仓库树中**无 LICENSE 文件** | NONE → 按「无许可但公开」处理，merged 且不逐字复制 |
| `linhay/harmony-next.skills` | `null` | `contents/LICENSE` → 404，**无 LICENSE** | NONE；**另有内容裁决，见下** |
| `liasica/harmonyos-skills` | `MIT` | `MIT License / Copyright (c) 2026 liasica` | 仓库自身 MIT，**但内容裁决降级，见下** |
| `KwaiAppTeam/ks-arkts-skills` | `null` | `contents/LICENSE` → 404 | NONE；**另有内容裁决** |
| `xiaowu5255/harmonyos-skills` | `null` | 无 LICENSE | NONE |
| `HarmonyOS-AI/Harmony-Skills` | `null` | 无 LICENSE | NONE |
| developer.huawei.com/consumer/cn/doc | 非 GitHub | 实读页脚：`华为开发者联盟 版权所有 ©2026` + `使用条款`，**无任何开放许可** | **Proprietary → 只能 `reference`** |

**内容裁决（与许可裁决分开）**：`linhay/harmony-next.skills`、`liasica/harmonyos-skills`、
`KwaiAppTeam/ks-arkts-skills` 三家的 `references/` 都是 **developer.huawei.com 文档的离线镜像**
（liasica README 自述「16800 篇，来源 developer.huawei.com/consumer/cn/doc/」；Kwai 的
`arkts_code_check_references/` 目录名就是华为文档的中文标题；linhay 自述「API 12-23 离线快照」）。
**仓库自己的许可不能覆盖它所镜像的第三方文档**——liasica 的 MIT 只覆盖 liasica 写的检索工具，
不覆盖华为的正文。这三家一律 `relation: reference`：只用来判断覆盖面与交叉校验，事实一律回到
`openharmony/docs`（CC-BY-4.0）或对官方页面实读取证。这与前几波 `redis.io/docs`（CC-BY-NC-SA）、
`learn.microsoft.com`（专有）vs `MicrosoftDocs/azure-docs`（CC-BY-4.0）是同一条规则的反向应用：
**一个仓库的许可是它自己的，不是它所记录的那个产品的。**

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `openharmony/docs` `en/application-dev/{quick-start,ui/state-management,application-models,arkts-utils,security,database,dfx,application-test,tools}` | https://github.com/openharmony/docs | 172 | 2026-08-22 | CC-BY-4.0 | ArkTS 语法约束全表（76 条 `arkts-*` 规则含 severity）、V1/V2 状态管理、Stage 模型、并发、权限、module.json5、hdc/uitest | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 唯一可合入的**一等事实来源**。ArkTS 规则清单、装饰器约束、TaskPool/Worker 对比表都能逐条落到具体文件与行 |
| 2 | `CoreyLyn/harmonyos-skills` `skills/harmonyos-dev`、`skills/harmonyos-review` | https://github.com/CoreyLyn/harmonyos-skills | 31 | 2026-07-23 | MIT | 先读工程配置再选 API、V1/V2 不混用、资源与订阅归属、证据门审查法 | 2 | 3 | 3 | 3 | 2 | **13** | INCLUDE | 写得最像工程规范：「本地 reference 是快照不是权威」「不得把未运行的检查说成通过」；抽查 3 条（V1/V2 边界内一致、`BusinessError` 处理、`ResultSet` 泄漏）与官方一致 |
| 3 | `DengShiyingA/harmonyos-ai-skill` `harmonyos-development` | https://github.com/DengShiyingA/harmonyos-ai-skill | 264 | 2026-07-25 | MIT | 版本/API level 清单、DevEco 版本配对、Kit 目录、API 23/24/26 变更 | 2 | 3 | 3 | 1 | 2 | **11** | INCLUDE | 星标最高的通用鸿蒙 skill，版本清单结构值得采用。**扣正确性**：把 ArkTS 说成 TypeScript 的 "superset"（官方定义是 restricts），且 6.0.2 发布日期与官方 overview-602 不一致（见裁决 #2） |
| 4 | `EarFrog/harmonyos-arkts-skill` | https://github.com/EarFrog/harmonyos-arkts-skill | 6 | 2026-08-01 | Apache-2.0 | 任务路由（ArkTS/ArkUI vs Native/NDK）、Native 调用链取证、`lib*.so`/Node-API 边界 | 1 | 3 | 3 | 3 | 2 | **12** | INCLUDE | 唯一把 ArkTS↔Native 调用链当成一条完整链路来审的上游；三条抽查（`externalNativeOptions`、`NAPI_MODULE` 注册、`types/lib*/index.d.ts` facade）与官方 NDK 文档一致 |
| 5 | `yibaiba/harmonyos-skills-pack` `skills/harmonyos-ark/arkts-modernization-guard` | https://github.com/yibaiba/harmonyos-skills-pack | 20 | 2026-04-03 | MIT | 14 条已知坏模式扫描规则（`@Prop` 收回调、`build()` 内副作用、`throw` 非 Error、`$r(变量)`、`@StorageLink` 绑 `@ObservedV2`） | 1 | 1 | 3 | 3 | 2 | **10** | INCLUDE | 规则表是本波次最接近「可证伪不变量」的社区产出；抽查 `arkts-limited-throw`、`@Event` 才是回调出口、`$r` 需静态字面量，均与官方一致。推送 >4 月扣新鲜度 |
| 6 | `openharmonyinsight/openharmony-skills` `skills/android-to-harmonyos-migration-workflow` | https://github.com/openharmonyinsight/openharmony-skills | 34 | 2026-09-04 | NONE | Android→鸿蒙映射表（Activity/Fragment/RecyclerView/Room/SharedPreferences → Page/Component/List+LazyForEach/RelationalStore/Preferences） | 1 | 3 | 2 | 2 | 0 | **8** | INCLUDE | 97 个 skill 里绝大多数面向 **OpenHarmony OS 贡献者**（C++、XTS、gitcode PR），与应用开发无关；只取迁移映射一节。映射表用 `router` 传参，已按裁决 #3 改写为 Navigation |
| 7 | `web-infra-dev/midscene-skills` `skills/harmony-automation` | https://github.com/web-infra-dev/midscene-skills | 306 | 2026-09-08 | MIT | 真机/模拟器视觉自动化：`@midscene/harmony` CLI、hdc 前置、单命令串行约束、无多指手势 | 2 | 3 | 3 | 3 | 2 | **13** | INCLUDE | 字节官方仓。注意路线图写的路径 `harmonyos-device-automation` 不存在，实际目录是 `skills/harmony-automation`（frontmatter `name` 才是 `harmonyos-device-automation`）——已更正 |
| 8 | `linhay/harmony-next.skills` `harmony-next` | https://github.com/linhay/harmony-next.skills | 347 | 2026-08-18 | NONE | DevEco/HVD/hdc/uitest/CDP 自动化 playbook、`blocked` 结构化返回约定、Empty Ability 冒烟骨架 | 1 | 3 | 3 | 2 | 0 | **9** | MAYBE→reference | 星标最高，但 `references/` 是华为专有文档镜像（内容裁决），且正文大量绑定作者自己的私有脚本与 macOS 路径。只借「工具不可用时返回结构化 blocked 而不是假装成功」这条约定，不复制内容 |
| 9 | `liasica/harmonyos-skills` `harmonyos` | https://github.com/liasica/harmonyos-skills | 17 | 2026-09-10 | MIT（仓库）/ 内容为华为专有 | 16800 篇华为文档离线镜像 + `rules/arkts-coding-rules.md` | 1 | 3 | 2 | 3 | 0 | **9** | MAYBE→reference | 内容裁决降级：MIT 只覆盖检索工具，不覆盖镜像的华为正文。用来交叉校验「官方文档里确实存在某条规则」 |
| 10 | `KwaiAppTeam/ks-arkts-skills` `arkts-code-check` | https://github.com/KwaiAppTeam/ks-arkts-skills | 30 | 2026-05-21 | NONE | ArkTS 编译错误索引 + 语言规则索引（正文是华为《从TypeScript到ArkTS的适配规则》等页面的抓取） | 1 | 1 | 2 | 3 | 0 | **7** | MAYBE→reference | 快手出品，索引切分方式有参考价值；正文是华为文档镜像，内容裁决降级 |
| 11 | `xiaowu5255/harmonyos-skills` `plugins/harmony-core/skills/{arkts-syntax,stage-model,arkts-concurrency,…}` | https://github.com/xiaowu5255/harmonyos-skills | 8 | 2026-09-07 | NONE | 按 plugin 分组的 30+ 个鸿蒙 skill（API 20-24） | 0 | 3 | 2 | 0 | 0 | **5** | REJECT | **正确性 0**：把「动态增删对象属性」归到 `arkts-no-structural-typing`（真实规则是 `arkts-no-prototype-assignment` / 运行时布局约束），并生造规则 id `arkts-no-destructuring`（官方是 `arkts-no-destruct-decls` 与 `arkts-no-destruct-assignment`）。规则 id 错了就会把 agent 引到不存在的编译诊断上 |
| 12 | `HarmonyOS-AI/Harmony-Skills` `arkts-rules`、`harmonyos-docs-lookup`、`harmonyos-sdk-api-lookup` | https://github.com/HarmonyOS-AI/Harmony-Skills | 0 | 2026-09-10 | NONE | ArkTS 规则 + 文档检索 + 实时预览 | 0 | 3 | 1 | 1 | 0 | **5** | REJECT | 0 星、组织名带 "HarmonyOS-AI" 但与华为无关；三个 skill 其中两个只是文档检索壳 |
| 13 | `mellow235/harmonyos_skills` | https://github.com/mellow235/harmonyos_skills | 3 | 2026-05-17 | MIT | 12 个编号目录，每个只有一个 `README.md` | 0 | 1 | 1 | 1 | 2 | **5** | REJECT | 仓库树里**没有任何 SKILL.md**，不是 Agent Skill；自述「鸿蒙 6.0」与 NEXT 主线不匹配 |
| 14 | `makerjackie/harmonyos-skills` `skills/{harmonyos-iap-integration,huawei-payment-integration,huawei-merccoupon-integration}` | https://github.com/makerjackie/harmonyos-skills | 0 | 2026-09-02 | MIT | IAP / 华为支付 / 商家券 | 0 | 3 | 2 | 1 | 2 | **8** | REJECT | 许可与新鲜度都够，但**范围裁决**：属「SaaS/产品 API 说明书」类，`docs/roadmap.md`「已排除主题」明确排除；且钱包/支付产品 API 在本 skill 的 `Scope` 否定范围内 |
| 15 | `imansmallapple/Harmonyos-Skills` `skills/harmonyos-dev` | https://github.com/imansmallapple/Harmonyos-Skills | 0 | 2026-02-19 | Apache-2.0 | 通用鸿蒙开发 | 0 | 0 | 1 | 1 | 2 | **4** | REJECT | 推送 >6 月（2026-02），非官方，直接 REJECT |
| 16 | `ximing/harmonyos-skills` `skills/harmonyos-{ability,arkui,kits,ndk,…}` | https://github.com/ximing/harmonyos-skills | 0 | 2026-08-25 | NONE | 11 个按 Kit 切分的 skill | 0 | 3 | 1 | 1 | 0 | **5** | REJECT | 0 星、无许可，正文是 Kit 目录清单式罗列；仓库里还塞了一份 `anthropics-skill-creator` 拷贝 |
| 17 | `YuJin99999/harmonyos-stage-v2-arkts-code` | https://github.com/YuJin99999/harmonyos-stage-v2-arkts-code | 0 | 2026-06-11 | NONE | Stage 模型 + V2 的 `.ets` 编码规范单文件 | 0 | 2 | 1 | 1 | 0 | **4** | REJECT | 0 星、无许可、单文件、无 references |
| 18 | `cangyeone/hongmeng-skill` | https://github.com/cangyeone/hongmeng-skill | 0 | 2026-07-11 | NONE | 单个 SKILL.md | 0 | 2 | 1 | 1 | 0 | **4** | REJECT | 0 星、无许可、内容量不足以评审 |
| 19 | developer.huawei.com/consumer/cn/doc（harmonyos-releases / harmonyos-guides / harmonyos-references / doccenter-deveco-studio） | https://developer.huawei.com/consumer/cn/doc/ | — | 持续 | **Proprietary** | HarmonyOS NEXT 独有：API 版本序与 `26.0.0` 格式调整、`build-profile.json5` 三个 SDK 字段、DevEco Studio / hvigor / 签名 / 上架、Kit API | 3 | 3 | 3 | 3 | 0 | **12** | INCLUDE→reference | **许可裁决**：页脚 `版权所有 ©2026` + 使用条款，无开放许可 → 只能 `reference`。事实只作核对依据，一字不复制；凡只在此处得到验证的结论标 `[official]` |
| 20 | `openharmony/arkcompiler_ets_frontend` | https://github.com/openharmony/arkcompiler_ets_frontend | 1 | 2026-09-11 | Apache-2.0 | ArkTS 前端编译器实现（linter 规则源码） | 3 | 3 | 3 | 3 | 2 | **14** | MAYBE | 许可与权威都满分，但它是**编译器源码**而不是给 agent 读的指南；本轮只用来确认 `arkts-*` 规则 id 真实存在于 linter 实现，不进 `SOURCES.yaml` |
| 21 | `openharmony/interface_sdk-js` `api/@ohos.*.d.ts` | https://github.com/openharmony/interface_sdk-js | 1 | 2026-09-10 | Apache-2.0（实读 LICENSE 正文：`Apache License Version 2.0`） | 公开 SDK 的 `.d.ts` 声明：API 形状 + `@since` / `@deprecated` / `@useinstead` 注解 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | **本轮补搜的最重要发现。** 这是「每条 API 声明都要能指出官方出处」的机器可核对来源：`@ohos.router.d.ts` 里每个全局 `pushUrl` 都带 `@deprecated since 18` + `@useinstead @ohos.arkui.UIContext:Router`；`@ohos.arkui.UIContext.d.ts` 里 `getRouter()`/`getPromptAction()` 是 `@since 10`、`isAvailable()` 是 `@since 20`。**并据此纠正了散文文档**（见裁决 #11）。星标低无关紧要——它是官方 SDK 本体 |
| 22 | `openharmony/applications_app_samples` | https://github.com/openharmony/applications_app_samples | 7 | 2026-08-22 | **混合**（实读 LICENSE：`Testing Materials` 归「License Agreement for Testing Materials」，**其余含代码为 Apache-2.0**） | 官方文档正文里 `<!-- @[...] -->` 注释指向的可运行样例 | 3 | 3 | 2 | 3 | 1 | **12** | INCLUDE→未采用 | 许可与质量都过门槛，但**按目录/按材料类型分别授权**，且本 skill 未引用任何样例代码（本机无 SDK 无法运行验证）。不进 `SOURCES.yaml`，留行备后续批次：若将来要引用样例，必须逐目录确认它不属于 `Testing Materials` |
| 23 | `openharmony/arkui_ace_engine` | https://github.com/openharmony/arkui_ace_engine | 14 | 2026-09-10 | Apache-2.0 | ArkUI 引擎 C++ 实现 | 3 | 3 | 3 | 3 | 2 | **14** | MAYBE | 同 #20：官方且许可干净，但是**引擎实现**而非应用开发指南。应用层事实从 #1/#21 取更直接，不进 `SOURCES.yaml` |
| 24 | `openharmony/ability_ability_runtime` | https://github.com/openharmony/ability_ability_runtime | 2 | 2026-09-10 | Apache-2.0 | Ability 运行时实现（Stage 模型调度） | 3 | 3 | 3 | 3 | 2 | **14** | MAYBE | 同上。生命周期契约以 #1 的 `application-models/uiability-lifecycle` 为准，实现细节不写进 skill |
| 25 | `openharmony/developtools_ace_ets2bundle` | https://github.com/openharmony/developtools_ace_ets2bundle | 0 | 2026-09-11 | Apache-2.0 | ArkTS→方舟字节码的构建链实现 | 3 | 3 | 3 | 3 | 2 | **14** | MAYBE | 同上。构建行为以 #19 的 hvigor 文档为准 |

### 立项依据（对 `docs/roadmap.md`「新增主题的判据」逐条核对）

候选 25 个（≥12 的下限满足）。**合格（总分 ≥8）上游 10 个**：#1 #2 #3 #4 #5 #6 #7 #19 #21 #22。
其中 **可 `merged` 的 8 个**：#1 #2 #3 #4 #5 #6 #7 #21（#19 因许可专有只能 `reference`，
#22 因许可按材料类型分割且本轮未引用而不采用）。最终写进 `SOURCES.yaml` 的 `merged` 上游
**8 个**。

逐条对判据：

| 判据 | 结论 |
|---|---|
| 第 1 条：对应一次真实任务的完整上下文 | 满足。写/审一个 `.ets` 页面不需要同时加载另一个同级 skill；`typescript` 只在「ArkTS 之外的 TS」时转交 |
| **第 2 条：≥3 个活跃（6 个月内有推送）且总分 ≥8 的上游** | **满足，且有余量：8 个可 merged 上游全部在 6 个月内有推送**（最旧的是 #5 `yibaiba`，2026-04-03，距调研日 2026-09-11 约 5.3 个月；其余在 2026-07-23 至 2026-09-10 之间）。门槛要求 3 个，实得 8 个 |
| 第 3 条：不是既有 skill 的子集 | 满足。ArkTS/ArkUI/Stage 模型与 `android`、`apple`、`typescript` 无重叠；边界句已写进 `## Scope` 与 `description` |
| 第 4 条：官方厂商特例 | **未动用，也不需要。** 特例要求官方文档 `kind: docs` 可 `merged`，而 developer.huawei.com 实读为专有、只能 `reference`（与波次 5 `elasticsearch` 未动用特例同理）。本 skill 走的是第 2 条的常规通道 |

**因此不存在降格立项的问题**：主代理在派发时给出的「合格上游不足 3 个则改以官方文档为主干」
那条备用路径已被其本人撤回，且本主题从未落入该分支——Phase A 第一轮就已有 7 个可 merged
上游达标，补搜后为 8 个。

需要单独记一句取证上的错位：合格上游里权威性最高的 #19（评分 12）**不可合入**，而覆盖面最广
的可合入来源 #1 讲的是 OpenHarmony 而不是 HarmonyOS NEXT。补搜到的 #21（官方 SDK `.d.ts`，
Apache-2.0）正好补上最关键的一环——**API 可用性从此可机器核对**，这决定了本 skill 的取证
策略（见「备注」）。

## 深度审查

### #1 `openharmony/docs`（CC-BY-4.0）

- **结构**：不是 skill，是 31896 个路径的文档仓，中英双语平行（`en/` + `zh-cn/`）。每篇顶部带
  `<!--Kit: ArkTS-->`、`<!--Owner:-->` 元注释，正文里的示例代码指向 gitcode 上的可运行样例
  （分支名形如 `HarmonyOS-7.0-Release-20260722`）。
- **质量**：`quick-start/typescript-to-arkts-migration-guide.md`（3619 行）是全网唯一一份**带规则 id
  与 severity 的 ArkTS 约束全表**：76 条 `**Rule:** arkts-*`，其中 71 条 `Severity: error`、
  5 条 `warning`（`arkts-no-definite-assignment`、`arkts-no-globalthis`、`arkts-no-func-bind`、
  `arkts-no-classes-as-obj`、`arkts-limited-esobj`）。四大支柱在
  `#recipes-summarized`：Static Typing Is Enforced（禁 `any`）、Changing Object Layout in Runtime
  Is Prohibited、Semantics of Operators Is Restricted、Structural Typing Is Not Supported。
- **agent 绑定**：无（纯文档）。frontmatter 不存在，无需剥离 agent 专属字段。
- **重叠**：#8 #9 #10 镜像的华为文档与本仓内容高度重合（OpenHarmony 是 HarmonyOS 的开源底座），
  但本仓是唯一带开放许可的那一份。**这就是它不可替代的原因。**
- **风险**：OpenHarmony ≠ HarmonyOS NEXT。API 版本字符串（`6.0.2(22)`、`26.0.0`）、DevEco Studio、
  AppGallery 上架、华为 Kit（Push/Map/IAP）只在 #19 有。凡属这类，本 skill 标 `[official]`。

### #2 `CoreyLyn/harmonyos-skills`（MIT）

- **结构**：两个 skill（`harmonyos-dev` / `harmonyos-review`），各带 `references/` 与 `evals/evals.json`。
  `harmonyos-dev` 6 个 reference（state-management、ui-components、data-persistence、network、
  permissions、performance），`harmonyos-review` 3 个（checklist、official-docs、report-template）。
- **frontmatter**：只有 `name` + `description`（block scalar），无 agent 专属字段，干净。
- **质量**：最高的一点是它把「事实来源顺序」写成了硬规则：工程配置 → 华为 API 参考 → 华为指南 →
  本地 reference，并明写「Treat local references as snapshots, not authority」和
  「Never describe an unrun check as passed」。`harmonyos-review` 的「A reportable finding needs
  all of the following」五项证据门与本仓 `code-review` / `security-review` 的取向一致。
- **agent 绑定**：`harmonyos-review` 的侦察命令写成 PowerShell 代码块（`rg -n --glob '*.ets' …`），
  合入时改为与平台无关的 `grep` 描述。
- **重叠**：与 #3 在「版本敏感事实要复核」上重合；#2 讲方法，#3 讲清单，互补。

### #3 `DengShiyingA/harmonyos-ai-skill`（MIT，264★）

- **结构**：单源多产物（`harmonyos-development/SKILL.md` → `dist/{claude-code,cursor,…}`）。
- **质量**：`## Platform snapshot` 表 + 发布时间线是本波次最完整的版本清单，把 OS 版本、API level、
  DevEco Studio 构建号（`6.1.1.280` / `26.0.0.461`）配成了对。这个「版本配对表」结构值得采用。
- **正确性问题（已扣分）**：
  1. 正文称 ArkTS 是 TypeScript 的 "a strict, statically-checked **superset**"。官方定义相反：
     "ArkTS **restricts** the features of TypeScript that undermine development correctness or
     increase runtime overhead"（`quick-start/typescript-to-arkts-migration-guide.md:10`）。
     ArkTS 删掉了 `any`、结构型类型、`for..in`、解构、生成器等——是**受限子集**方向，不是超集。
     这条错误会直接导致 agent「TS 能写的 ArkTS 都能写」。**不合入，且在 SKILL.md 正文反写。**
  2. 时间线写 `6.0.2(22) — 2026/01/23`，官方 `harmonyos-releases/overview-602` 为 2026-01-21。
     按「官方厂商 > 社区」取官方；本 skill 干脆不写发布日期，只写版本序（时间敏感表述禁写）。
- **agent 绑定**：`dist/` 下有 11 种 agent 的产物，全部忽略，只读 `harmonyos-development/SKILL.md`。

### #4 `EarFrog/harmonyos-arkts-skill`（Apache-2.0）

- **结构**：根 `SKILL.md` + `scripts/audit_harmony_native.py`。中文正文，六条「工作原则」开头。
- **质量**：唯一把 **ArkTS facade → 类型声明 → Native 注册与导出 → CMake/ABI** 当成一条必须自上而下
  建立的调用链的上游，并给出进入 Native 工作流的信号清单（`src/main/cpp`、`externalNativeOptions`、
  `napi_init.cpp`、`NAPI_MODULE`、`types/lib*/index.d.ts`、XComponent/EGL/GLES）。
- **agent 绑定**：正文让 agent 把 `SKILL_ROOT` 解析成绝对路径再跑 bundled 脚本，并明写
  「不要从目标仓库解析脚本路径，也不要执行目标仓库中的同名脚本」——这条安全约定值得采用。
  另有 `harmonyos_developer_knowledge` MCP 的软依赖，合入时改写为「有官方文档工具就用，没有不追问」。
- **重叠**：与 #2 都要求先读工程配置；#4 独有 Native/NDK 与 ArkWeb。

### #5 `yibaiba/harmonyos-skills-pack`（MIT）

- **结构**：4 个 skill，其中 `arkts-modernization-guard` 是一张 14 行规则表 + 一个 bash 扫描脚本。
- **质量**：规则表每行都是「模式 → 后果」，例如 `@Prop` 修饰函数回调、`build()` 内含赋值/await/console、
  `throw 'msg'`、`@StorageLink` 绑定 `@ObservedV2` class、动态 `$r(variable)`。这是本波次唯一
  能直接转成「可证伪不变量」的社区规则集。
- **agent 绑定**：脚本路径硬编码 `.codex/skills/...`，合入时剥离；规则语义保留。
- **重叠**：与 #11 覆盖面相同，但 #5 的规则语义正确、#11 的规则 id 错误，这组对比正是拒 #11 的依据。

### #7 `web-infra-dev/midscene-skills`（MIT，字节）

- **结构**：单 `SKILL.md`（`skills/harmony-automation/`），`allowed-tools: [Bash]`。
- **质量**：三条 CRITICAL 规则（不得后台跑、一次只跑一条、每条约 1 分钟）直接对应 screenshot→analyze→act
  循环的正确性，而不是风格偏好。明写 HarmonyOS 侧**不支持双指缩放**（底层自动化层不暴露多点触控），
  这种「能力边界」正是 skill 该写的东西。
- **agent 绑定**：`allowed-tools` 是规范白名单字段，但本仓统一不写；`MIDSCENE_MODEL_*` 环境变量与
  模型清单属产品配置，合入时压缩成一行前置条件。
- **重叠**：无。设备验证这一段其他候选都只到 `hdc` 为止。

### #19 developer.huawei.com/consumer/cn/doc（Proprietary → reference）

- **结构**：指南 / API 参考 / 版本说明 / 最佳实践 / FAQ / 变更预告六个分类。
- **质量**：HarmonyOS NEXT 独有事实的唯一权威来源：API 版本序与 `26.0.0` 起的格式调整、
  `compatibleSdkVersion`/`targetSdkVersion`/`compileSdkVersion` 三字段语义与
  `minAPIVersion`/`targetAPIVersion` 产物字段的映射、DevEco Studio 与 hvigor、签名与上架、华为 Kit。
- **许可**：实读页脚无开放许可 → `reference`。本 skill 对这里得到的每条事实标 `[official]`，
  正文只写结论不复制表述，并在「备注」列出完整未验证清单。

### #21 `openharmony/interface_sdk-js`（Apache-2.0）

- **结构**：5818 个路径，`api/@ohos.*.d.ts` 与 `zh-cn/api/@ohos.*.d.ts` 平行。不是 skill、
  也不是文档，是**公开 SDK 的类型声明本体**——DevEco 与 ArkTS 编译器实际消费的那份契约。
- **质量**：每个导出都带 `@since` / `@deprecated` / `@useinstead` / `@syscap` / `@atomicservice`
  注解，且区分 `dynamic` 与 `static`（`@since 9 dynamic` / `@since 23 static`）。这是本仓库
  「版本敏感规则标注可用性底线」这条写作规则在鸿蒙生态里唯一**可机器核对**的依据。
- **本轮用到的三处取证**：
  - `api/@ohos.router.d.ts:274-276`、`302-304`、`331-333`——每个全局 `pushUrl` 重载都带
    `@deprecated since 18` + `@useinstead @ohos.arkui.UIContext:Router#pushUrl`。
  - `api/@ohos.arkui.UIContext.d.ts:5045-5047`、`5178-5180`、`5190-5192`——
    `isAvailable()` `@since 20`、`getRouter()` `@since 10`、`getPromptAction()` `@since 10`。
  - `api/@ohos.abilityAccessCtrl.d.ts:229-232`——`checkAccessToken()` `@since 9 dynamic`
    / `@since 23 static`；旧的 `verifyAccessToken` 带 `@since 8` + `@useinstead ... #checkAccessToken`。
- **agent 绑定**：无。
- **重叠**：与 #1 互补而非重复——#1 讲「为什么与怎么做」，#21 讲「从哪个版本开始、有没有被
  废弃」。两者冲突时按裁决 #11 取 #21。
- **风险**：它是 OpenHarmony 的 SDK 声明。HarmonyOS NEXT 的闭源 Kit（Push/Map/IAP 等）不在
  其中，那些仍然只能从 #19 取并标 `[official]`。日更频率高（调研当日仍在推送），同步时
  `check_upstream.py` 会频繁报 `behind`，但 `paths` 已收窄到本 skill 实际引用的 5 个文件。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | HarmonyOS 7 对应哪个 API 版本 | 社区/搜索摘要有说 API 23、API 26、`7.0.0(26)` 各种版本；#3 写 `26.0.0 Beta1 = API 26` | **不写 `7.0.0(x)` 这种字符串。** 官方版本序为 `26.0.0 > 6.1.1(24) > 6.1.0(23) > 6.0.2(22) > 6.0.1(21) > 6.0.0(20)`，自 `26.0.0` 起 API 版本号**格式本身**变了（不再带 `(n)` 后缀），HarmonyOS 7 配套 SDK 即 `26.0.0` | 实读 `developer.huawei.com/consumer/en/doc/harmonyos-releases/app-compatibility-scenarios`：`NOTE The API version number format has been adjusted since 26.0.0` + 版本序原文 `[official]` |
| 2 | ArkTS 与 TypeScript 的关系 | #3：ArkTS 是 TS 的 "statically-checked superset"；#11：ArkTS 的 `interface` 「不支持实现细节」 | **ArkTS 是受限的 TypeScript**：保留大部分 TS 语法，但禁用破坏正确性或增加运行时开销的特性（76 条 `arkts-*`）。"superset" 说法不合入，并在 `## Core rules` 第 1 条反写 | `openharmony/docs` `quick-start/typescript-to-arkts-migration-guide.md:10`：「ArkTS restricts the features of TypeScript…」`[verified]`（本机实读文件） |
| 3 | 页面导航用 `router` 还是 `Navigation` | #6 迁移映射表用 `router` 传 Bundle 参数；#5 把 `pushUrl` 列为 deprecated；#1 两者都有文档 | **一律 `Navigation` + `NavPathStack`。** `@ohos.router` 模块标题已是「(Not Recommended)」，且全局 `router.pushUrl` **自 API 18 起 deprecated**，替代是 `UIContext.getRouter().pushUrl` | `openharmony/docs` `reference/apis-arkui/js-apis-router.md`：模块标题 `(Not Recommended)`；`router.pushUrl<sup>(deprecated)</sup>`「supported since API version 9 and deprecated since API version 18」`[verified]` |
| 4 | ArkUI 全局 API 能不能直接用 | 多数候选示例直接写 `router.pushUrl(...)`、`promptAction.showToast(...)` | **多实例场景一律走 `UIContext`。** Stage 模型下一个 ArkTS 引擎可以承载多个 UI 实例，全局 API 靠调用链推断实例，异步与非 UI API 会推断失败 → 弹到错误的窗口或静默失效。替代 API 自 **API 18** 起可用（`isAvailable` 自 API 20） | `openharmony/docs` `ui/arkts-global-interface.md`：「In the stage model, multiple UI instances can coexist within a single ArkTS engine… asynchronous APIs and non-UI APIs may fail to trace context correctly」+ 替代表 `[verified]` |
| 5 | V1 与 V2 状态管理能否混用 | #2：同一组件边界内保持一致；#3/#11：未给版本门；#1 有两篇互相排斥的文档 | **按 API 版本分档写**：`arkts-custom-component-mixed-scenarios.md` 的混用规则**只适用于 API ≤18**；自 **API 19** 起改用 `UIUtils.enableV2Compatibility()` / `UIUtils.makeV1Observed()`。正文写 API 19+ 做法，API ≤18 的老规则放 `## Old patterns` 折叠块 | `openharmony/docs` `ui/state-management/arkts-custom-component-mixed-scenarios.md` NOTE：「The rules for mixed use described in this topic apply only to API version 18 and earlier」+ `arkts-v1-v2-mixusage.md` 标题「(API Version 19 and Later)」`[verified]` |
| 6 | TaskPool 还是 Worker | #1 明写「TaskPool is recommended in most scenarios」；社区常按「长任务用 Worker」一句话概括 | **默认 TaskPool；只有三种情况用 Worker**：单任务运行超过 3 分钟、一组相互依赖且需保持线程上下文的同步任务、需要长期占用线程并自行管理生命周期。并写清后果：TaskPool 单任务上限 3 分钟（不含 Promise/await 的 I/O 等待）、同进程最多 64 个 Worker、Worker 不支持取消、Worker 优先级设置自 API 18 起才有 | `openharmony/docs` `arkts-utils/taskpool-vs-worker.md` Table 1 + Use Case Comparison `[verified]` |
| 7 | `@Prop` 能不能接回调 | #5 列为 P0 坏模式；#1 的 V2 文档给出正解 | **回调是组件的输出，用 `@Event`（V2）**；V1 的状态装饰器不支持 function 类型，V2 状态变量支持 function 但传给 V1 装饰器时运行时校验会拦 | `openharmony/docs` `ui/state-management/arkts-new-event.md`（`@Event` 只接 arrow function，装饰非函数不生效）+ `arkts-custom-component-mixed-scenarios.md`（「the V2 state variable supports the function type, but the V1 state variable decorator does not」）`[verified]` |
| 8 | `@Observed`+`@ObjectLink` 还是 `@ObservedV2`+`@Trace` | #11 只讲 V1；#1 两套都在 | **新代码用 `@ObservedV2` + `@Trace`（API 12+）**，它能直接观测嵌套类属性；V1 必须用 `@ObjectLink` 把嵌套类拆开代理。两者不得混用：V1 装饰器不能与 `@ObservedV2` 同用，V1 也不能用装饰器接收 `@ObservedV2` 类（编译报错） | `openharmony/docs` `arkts-new-observedV2-and-trace.md`（「must come in pairs」「must be instantiated using the **new** operator」）+ `arkts-v1-v2-mixusage.md` Constraints 1–2 `[verified]` |
| 9 | 设备验证怎么做 | #8 给私有 DevEco 脚本 + macOS 路径；#7 给视觉自动化 CLI | **两段式**：能力探测与证据采集用官方 `hdc` / `uitest`（跨平台、无额外依赖）；需要按自然语言操作 UI 时用 `@midscene/harmony`。不采用 #8 的私有脚本与 `devecostudio://` 私有接口——版本敏感且不可移植。保留 #8 的「工具不可用就返回结构化 blocked，不要假装跑过」这条约定 | 官方厂商 > 社区；`openharmony/docs` `dfx/hdc.md` + `application-test/uitest-guidelines.md` `[verified]`；#7 为字节官方 MIT |
| 10 | 本 skill 面向 HarmonyOS 还是 OpenHarmony | #6 全仓面向 OpenHarmony OS 贡献者；#1 是 OpenHarmony 文档；#2/#3/#4/#7 面向 HarmonyOS NEXT 应用 | **面向 HarmonyOS NEXT 应用开发**。平台契约（ArkTS 语法、ArkUI 装饰器、Stage 模型、module.json5）两者共享，从 #1 取证；版本字符串、DevEco、上架、华为 Kit 只在 #19，标 `[official]`。OS 自身开发（内核、C++ 子系统、XTS）不在范围 | 任务书边界 + `docs/roadmap.md` 波次 8 |
| 11 | 「`UIContext` 替代 API 从哪个版本开始可用」——散文文档与 SDK 声明不一致 | #1 的 `ui/arkts-global-interface.md` 原文：「In the sample code, `isAvailable` is available since API version 20, **with other APIs available since version 18**」，读起来像是替代 API 在 API 18 才出现；#21 的 `api/@ohos.arkui.UIContext.d.ts` 里 `getRouter()`、`getPromptAction()` 都标 `@since 10`，`isAvailable()` 标 `@since 20` | **以 SDK 声明为准**：`UIContext` 访问器自 **API 10** 就有；**API 18 是全局 `router` 函数被废弃的时点**，不是替代品出现的时点。正文改写为「访问器 `@since 10`，`isAvailable()` `@since 20`，所以『UIContext 太新我们用不了』从来不成立」 | 「官方厂商 > 社区」在两份官方材料之间不分胜负，改用「**声明 > 散文**」：`.d.ts` 是编译器与 IDE 实际消费的契约，散文那句话的主语其实是「示例代码里用到的 API」。#21 `api/@ohos.router.d.ts:274-276` 逐条可核：`@since 9 dynamiconly` / `@deprecated since 18` / `@useinstead @ohos.arkui.UIContext:Router#pushUrl` |


## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `openharmony-sdk-js` | `openharmony/interface_sdk-js` @ `8eba85d` (Apache-2.0) | merged | API 可用性的机器可核对来源：`@since` / `@deprecated` / `@useinstead` 注解。据此把 router 废弃版本、`UIContext` 访问器版本、`checkAccessToken` 版本从 `[official]` 升级为 `[verified]`，并纠正了散文文档（裁决 #11） |
| `openharmony-docs` | `openharmony/docs` @ `f41b934` (CC-BY-4.0) | merged | ArkTS 76 条 `arkts-*` 约束与 severity、V1/V2 装饰器语义与约束、V1↔V2 混用版本门、Stage 模型与 UIAbility 生命周期、`UIContext` 替代全局 API、TaskPool/Worker 对比、`module.json5` 与权限声明、Preferences、hdc/uitest |
| `corey-harmonyos` | `CoreyLyn/harmonyos-skills` @ `cd2be39` (MIT) | merged | 事实来源顺序（工程配置 > 官方参考 > 本地 reference）、V1/V2 边界内一致、资源与订阅归属、审查的五项证据门与严重级定义 |
| `earfrog-arkts` | `EarFrog/harmonyos-arkts-skill` @ `f08c86e` (Apache-2.0) | merged | 任务路由与 Native 工作流触发信号、ArkTS↔Native 调用链自上而下取证、「不执行目标仓库同名脚本」约定 |
| `dengshiying-harmonyos` | `DengShiyingA/harmonyos-ai-skill` @ `4aab51a` (MIT) | merged | 版本 / API level / DevEco 构建号配对表结构；ArkTS "superset" 说法与发布日期已按裁决 #2 拒收 |
| `yibaiba-ark` | `yibaiba/harmonyos-skills-pack` @ `93bc8b7` (MIT) | merged | 已知坏模式清单（`@Prop` 收回调、`build()` 内副作用、`throw` 非 Error、动态 `$r()`、`@StorageLink` 绑 `@ObservedV2`、spread 触发全量重渲染） |
| `midscene-harmony` | `web-infra-dev/midscene-skills` @ `dec1d1c` (MIT) | merged | 设备自动化循环约束（串行、不后台、单次一动作）与 HarmonyOS 侧能力边界（无多指手势）、hdc 前置检查 |
| `oh-insight-migration` | `openharmonyinsight/openharmony-skills` @ `5ae988c` (NONE) | merged | Android→鸿蒙对照的组件/存储/上下文映射骨架（导航一列已按裁决 #3 从 `router` 改写为 `Navigation`） |
| `huawei-docs` | developer.huawei.com/consumer/cn/doc (Proprietary) | reference | API 版本序与 `26.0.0` 格式调整、`build-profile.json5` 三个 SDK 字段语义、DevEco Studio / hvigor / 签名 / 上架、华为 Kit 可用性。许可裁决：只核对，不复制 |
| `linhay-harmony-next` | `linhay/harmony-next.skills` @ `880420c` (NONE) | reference | 覆盖面校验 + 「工具缺失返回结构化 blocked」约定。内容裁决：`references/` 是华为专有文档镜像 |
| `liasica-harmonyos` | `liasica/harmonyos-skills` @ `8f252f3` (MIT 仓库 / 专有内容) | reference | 交叉校验官方规则是否存在。内容裁决：MIT 不覆盖被镜像的华为正文 |
| `kwai-arkts` | `KwaiAppTeam/ks-arkts-skills` @ `76b420d` (NONE) | reference | ArkTS 编译错误索引的切分方式。内容裁决：正文为华为文档镜像 |

## 基线缺口

无 skill（`uv run tools/run_evals.py harmonyos --baseline`，Claude Opus 5 · medium，5/5
`status: ok`，`skill_read` 全 False，耗时 225–362 s，`events_bytes` 436 KB–1.2 MB，
`stderr.log` 全 0 字节）时，各场景未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 ArkTS 违规 | #4 `router.pushUrl` 的两项理由 | 只指出 `params` 对象字面量非法、闭包不能跨页传递，**完全没提**全局 `router` API 形式自 API 18 起 deprecated，也没提 `@ohos.router` 已不推荐、应改 `Navigation`。把 `import promptAction from '@ohos.promptAction'` 归为「统一 Kit 导入」的风格问题 |
| 1 ArkTS 违规 | #5 `promptAction` 全局调用在 Stage 模型下不可靠 | 一个字都没提。多 UI 实例与 `UIContext` 替代 API 在这道题里完全缺失（同一模型在场景 4 里却提到了——说明它知道，但不会在读代码时想起来） |
| 1 ArkTS 违规 | #6 的后半：标准模式门 | 区分了 error/warning（`arkts-no-globalthis`、`arkts-no-func-bind` 标了 warning），但**没有**提到 ArkTS 语法检查只在标准模式下强制、标准模式由 `compatibleSdkVersion >= 10` 选择。于是「这条诊断到底拦不拦构建」无法判断 |
| 2 状态装饰器 | #3 `@Provider`/`@Consumer` 的初始化规则 | 判出 `@Consumer` 在 `@Component` 里非法，但没说 V2 的 `@Provider`/`@Consumer` 必须本地初始化、禁止从父组件初始化——与 V1 `@Provide` 恰好相反，这正是迁移时最容易写错的一条 |
| 2 状态装饰器 | #5 API 版本门（**核心缺口**） | 全程没有出现 `enableV2Compatibility` / `makeV1Observed`，也没提混用规则只适用于 API ≤18、API 19 起有新 API。夹具**故意**写了一行未使用的 `import { UIUtils } from '@kit.ArkUI'`，基线注意到了它（「`import { UIUtils }` 未使用」）却把它当成死代码清理项，没能反推出这是 V1→V2 迁移的入口 |
| 2 状态装饰器 | #6 的前半：`@Monitor` 观察整个数组 | 说了 `@Once` 必须配 `@Param`（达成），但没指出 `@Monitor` 观察整个数组时看不到单项变化、也看不到内置类型 API 触发的变化 |
| 3 module.json5 | #2 的后半：`usedScene.when` | 抓到 `$string:` 资源引用要求，也质疑了 `READ_CONTACTS` 的 `when: "always"` 不合调用时机，但**漏掉** `READ_IMAGEVIDEO` 的 `usedScene` 根本没有 `when`（该字段必填且只能 `inuse`/`always`） |
| 3 module.json5 | #3 `minAPIVersion`/`targetAPIVersion` | **未达成，且给出的修法是错的**（原文见下「基线错误」F1）。它判出「放错文件」，却开出「属于 app.json5」的处方；官方规定这两个标签在 `app.json5` 里也是构建自动生成、**不可手工配置**，真正的输入是工程级 `build-profile.json5` 的 `compatibleSdkVersion`/`targetSdkVersion` |
| 3 module.json5 | #5 运行期鉴权契约 | 完全没提。`checkAccessToken` 每次调用前复查、用户拒绝后不再弹窗、需引导到设置页——这三条在一道「审 module.json5」的题里被当成不相关，但它们恰恰是权限声明之外的另一半 |
| 3 module.json5 | #6 entry 模块权限的作用域 | 没提 entry 模块声明的权限已对整个应用生效、不应在 feature 模块重复 |
| 4 迁移评审 | #3 的具体数字 | 拒了「一个常驻 Worker 干全部后台活」，但理由换成了进程冻结与队头阻塞（都是真的），**没有**给出 TaskPool 单任务 3 分钟上限（不含 await 的 I/O）、同进程最多 64 个 Worker、Worker 不支持取消这三条硬数字。审查者因此无法判断「多长算长」 |
| 4 迁移评审 | #5 的第三项 | 缓存授权结果、拒绝后不再弹窗都判到了，但没提在 `onWindowStageCreate` 里申请必须等 `loadContent()`/`setUIContent()` 完成 |
| 5 负例 | — | 三条全部达成：停在 Compose 语境（`MutableStateFlow` 持可变 `data class` 不触发重组、total 未派生、`items()` 需稳定 key），未引入任何 ArkTS/ArkUI/鸿蒙装饰器 |

### 基线没有胡编 API——这是本次调研最反直觉的结果

立项时的预期是：中文生态 + 训练数据少 = 基线大量胡编 API。**实测不成立，必须如实记录。**

场景 1 里基线给出了 20 余条 `arkts-*` 规则 id **并附带数字错误码**，逐条对
`openharmony/docs` `quick-start/typescript-to-arkts-migration-guide.md` 的
`**Error code:**` 行核对，**全部正确**：`arkts-no-var`=10605005、
`arkts-no-any-unknown`=10605008、`arkts-no-props-by-index`=10605029、
`arkts-no-structural-typing`=10605030、`arkts-no-untyped-obj-literals`=10605038、
`arkts-no-obj-literals-as-types`=10605040、`arkts-no-func-expressions`=10605046、
`arkts-as-casts`=10605053、`arkts-no-delete`=10605059、`arkts-no-in`=10605066、
`arkts-no-destruct-decls`=10605074、`arkts-no-for-in`=10605080、
`arkts-limited-throw`=10605087、`arkts-no-implicit-return-types`=10605090、
`arkts-no-nested-funcs`=10605092、`arkts-no-spread`=10605099、
`arkts-no-globalthis`=10605137、`arkts-no-func-bind`=10605140、
`arkts-no-as-const`=10605142、`arkts-limited-stdlib`=10605144、
`arkts-strict-typing-required`=10605146。一条不差。

它还独立给出了几条本 skill 初稿没有的真事实，均已复核后补入正文：router 页面栈上限
32 页、超限错误码 `100003`（`reference/apis-arkui/js-apis-router.md:1482`、
`arkts-apis-uicontext-router.md:1446`）；`installationFree` 是构建自动生成、手工配置不生效
（`quick-start/module-configuration-file.md:135`）；`startWindowIcon`/`startWindowBackground`
是非可缺省标签、被 `startWindow` 取代（同文件 303–305 行）；HarmonyOS 用 musl 而 Android
用 bionic，现有 `.so` 二进制不能复用。

**结论：这个题材的基线缺口不是「不知道 API」，而是「知道规则、不知道版本门与实例边界」。**
缺口集中在四类：① 版本分界（标准模式门、API 18 的 `UIContext`/router、API 19 的
`enableV2Compatibility`）；② 生成字段 vs 输入字段（`minAPIVersion` 那一条还给错了方向）；
③ 并发的硬数字；④ 声明与运行期鉴权的另一半。本 skill 的 `## Core rules` 正是按这四类写的。

### 基线错误（原样记录）

| # | 场景 | 基线原文 | 复核结论 |
|---|---|---|---|
| F1 | 3 | 「**第 14-15 行 `minAPIVersion` / `targetAPIVersion` 放错文件** — 这两个不是 module.json5 的标签（标签表里没有），属于 **app.json5**。写在这里会触发 schema 校验错误且不生效。」 | 半对半错。「不是 module.json5 标签」正确（已核 `module-configuration-file.md`，无此标签）；但处方错误——`app-configuration-file.md:102-103` 明写这两个标签「automatically generated during application build and **cannot be manually configured**」，分别对应工程级 `build-profile.json5` 的 `compatibleSdkVersion` 与 `targetSdkVersion`（后者缺省时由 `compileSdkVersion` 生成）。正确修法是**删掉**，不是搬到 `app.json5` |
| F2 | 4 | 「顺带一提第 7 条本身：全局 `promptAction.showToast` / `AlertDialog.show` / `router` **自 API 18 起已废弃**」 | 只有全局 `router` API 形式是 deprecated（`js-apis-router.md`：`pushUrl<sup>(deprecated)</sup>`「deprecated since API version 18」）。`@ohos.promptAction` **没有被废弃**——`js-apis-promptAction.md` 的措辞是「It is recommended that you use the prompt APIs provided by **UIContext**」，理由是 UI 上下文歧义，不是废弃。把「建议」升级成「废弃」是过度断言。本 skill 在 `references/arkui-navigation.md` 里显式写了这条区分 |
| F3 | 1 | 「`@State` **必须本地初始化**、不支持可选属性」 | 前半正确（`arkts-state.md:139`：必须初始化，否则编译报错）；后半无官方依据——`@State` 自 API 11 起支持 `undefined`/`null` 与框架联合类型（`arkts-state.md:35`），唯一被明确禁止的类型是 `Function`（第 36 行；API 23 起从运行时报错改为编译报错）。夹具那行 `@State selected?: FeedItemLike` 的真实问题是**缺初始值**，不是「不支持可选」 |
| F4 | 4 | 「Preferences 的 key/value 上限**随版本变化**（OpenHarmony 3.2 是 80B/8192B，5.0 放宽到 1024B/16MB）」 | 现行文档（`data-persistence-by-preferences.md:38-40`）只给 key ≤1024 字节、string value ≤16 MB，**没有**版本限定，也查不到 80B/8192B 的出处。作为未经证实的历史数字记录；本 skill 只写当前文档给出的限额 |

F1 与 F2 都属于「能说服人的错」——F1 会让人把配置搬到另一个同样不能手改的地方，F2 会让人
以为一批没废弃的 API 要立刻替换。这两条是本 skill 相对基线最实在的增量。

## 评测结果

模型固定 Claude Opus 5 · medium（`tools/run_evals.py` 默认，两次运行未传 `--model` /
`--thinking`）。基线 5/5 `ok`，有 skill 5/5 `ok`；有 skill 的耗时全面下降
（257→128、336→99、225→80、362→94 秒），负例反而略升（353→126，因为基线那次自建了一个
Android library 模块做验证）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 ArkTS 违规（`FeedPage.ets`） | Opus 5 medium | 无 | false | #1 #2 #3 达成；#4 #5 #6 未达成 | 规则 id 与错误码全对；缺 API 18 的 router/UIContext 与标准模式门 |
| 1 ArkTS 违规 | Opus 5 medium | 有 | **true** | **#1–#6 全部达成** | 开篇即「受限子集，不是 strict 预设」；加了 `compatibleSdkVersion >= 10` 才是 standard 模式；`router` 全局形式 API 18 废弃 + 改 `Navigation`；`promptAction` 改 `UIContext`；还正确地把 `[...this.items]`（拷贝进数组字面量）与纯 `build()` 判为**合法、不要一起改** |
| 2 状态装饰器（`CartPage.ets`） | Opus 5 medium | 无 | false | #1 #2 #4 达成；#3 #5 #6 未达成 | 诊断准确但没有版本门；注意到 `UIUtils` 未使用却当死代码处理 |
| 2 状态装饰器 | Opus 5 medium | 有 | **true** | **#1–#6 全部达成** | 补上 `@Consumer` 必须本地初始化/禁止父级初始化；点名 `UIUtils.enableV2Compatibility()`（API 19+）并判断它救不了「派生值手工同步」这个病；明确 `@Monitor` 观察不到数组元素级变化 |
| 3 module.json5 | Opus 5 medium | 无 | false | #1 #4 达成；#2 部分；#3 #5 #6 未达成 | #3 给了错的修法（F1） |
| 3 module.json5 | Opus 5 medium | 有 | **true** | #1 #2 #3 #4 达成；**#5 #6 仍未达成** | #3 完全纠正：「根本不是 module.json5 的标签……搬到 app.json5 同样不是修法」；#2 补上 `READ_IMAGEVIDEO` 缺 `when`。另外命中了 skill 新增的 `startWindow` 必填与深链 `uris` 只限 scheme 未限 host/path 两条。**#5（运行期 `checkAccessToken` 复查 / 拒绝后不再弹窗 / 引导设置页）与 #6（entry 模块权限已全应用生效）仍未提及**——如实记录，见「未达成项」 |
| 4 迁移评审（`migration-plan.md`） | Opus 5 medium | 无 | false | #1 #2 #4 #6 #7 #8 达成；#3 #5 部分 | 判得很好但缺硬数字；#4 附带 F2 的过度断言 |
| 4 迁移评审 | Opus 5 medium | 有 | **true** | **#1–#8 全部达成** | #3 补齐三条硬数字（TaskPool 单任务 3 分钟不含 await I/O、64 Worker 上限、Worker 不可取消）；#5 补上「`onWindowStageCreate` 里申请须等 `loadContent()`/`setUIContent()` 完成」；#4 的措辞改为「`UIContext` 替代品自 API 18 起可用」，**没有**重复基线 F2 那句「promptAction 已废弃」 |
| 5 负例（`CartScreen.kt`，Jetpack Compose） | Opus 5 medium | 无 | false | 3/3 达成 | — |
| 5 负例 | Opus 5 medium | 有 | **false** ✅ | 3/3 达成 | 开口即「纯 Compose/Kotlin 的状态问题，跟 HarmonyOS 无关，按 Android 侧规范处理」，随后只用 `MutableStateFlow`/`update`/`copy`/`items(key=)` 作答，全程未出现 ArkTS、ArkUI 或任何鸿蒙装饰器。`description` 末尾的 `Do not use for native Android … use the android skill` 无需收紧 |

结论：**通过。** 基线未达成的行为在有 skill 时被填补了 **11 条**：场景 1 的 #4 #5 #6、
场景 2 的 #3 #5 #6、场景 3 的 #2（`when` 缺失）与 #3（并纠正了基线给出的错误修法）、
场景 4 的 #3 #5，以及场景 4 #4 处基线的过度断言被消除。负例 `skill_read == false`，
且四个正例全部 `skill_read == true`。

### 未达成项（不粉饰）

| # | 未达成 | 判断 |
|---|---|---|
| 1 | 场景 3 的 `expected_behavior` #5：运行期鉴权契约（每次调用前 `checkAccessToken`、用户拒绝后不再弹窗、引导设置页） | 有 skill 时仍未提及。诚实的解释是：题干是「审这份 `module.json5`」，模型把范围严格限制在这个文件里，而运行期契约在 `.ets` 侧。这条写进 `expected_behavior` 时就偏出了夹具边界——是**评测设计的问题**，不是 skill 缺内容（`references/stage-model.md` 的「Runtime authorization」一节四条全在，场景 4 的同类行为也达成了）。不改题目、不改判，记在这里 |
| 2 | 场景 3 的 `expected_behavior` #6：entry 模块权限已对整个应用生效 | 同上，夹具里只有一个 `entry` 模块，没有 feature 模块可对比，触发条件不存在。内容在 `references/stage-model.md` 的 HAP/HAR/HSP 与权限两节 |
| 3 | 本机无法运行 HarmonyOS 工具链 | Linux 上无 DevEco Studio、无 HarmonyOS SDK、无 `hvigorw`/`codelinter`/`hdc`，也没有设备或模拟器。因此 `hvigorw`、`codelinter`、`hdc`、`uitest`、`@midscene/harmony` 的命令形式全部标 `[official]`，未实跑。SKILL.md 的 `## Environment` 与 `references/build-sign-verify.md` 末节都写明了这个边界 |

## 备注

### 事实取证策略（本 skill 与其他 skill 不同的地方）

合格上游里权威性最高的 `developer.huawei.com`（评分 12）**不可合入**，而唯一可合入的一等
事实来源 `openharmony/docs`（CC-BY-4.0）讲的是 OpenHarmony 而不是 HarmonyOS NEXT。
这个错位决定了取证方式：

- **平台契约**（ArkTS 语法规则与错误码、ArkUI 装饰器语义与约束、Stage 模型生命周期、
  `module.json5` schema、TaskPool/Worker 参数、Preferences/RDB 限额、`hdc`/`uitest`）
  两个体系共享，全部落到 `openharmony/docs` 的具体文件，本机 `base64 -d` 实读后标
  `[verified]`。
- **API 可用性与废弃**（某接口从哪个版本开始有、有没有被废弃、替代品是什么）以
  `openharmony/interface_sdk-js` 的 `.d.ts` 注解为准，也标 `[verified]`——这是三类来源里
  唯一**机器可核对**的一类，也是它在裁决 #11 里能推翻散文文档的原因。
- **HarmonyOS NEXT 独有事实**（API 版本序与 `26.0.0` 起的格式调整、三个 SDK 字段语义、
  `hvigorw` 任务与参数、`signingConfigs.material` 字段、AppGallery 上架）只在华为站点，
  实读页面复核后标 `[official]`，一字不复制。
- 判定原则：**能在本机文件里读到的标 `[verified]`，只在网页上读到的标 `[official]`。**
  不存在「凭记忆写」的第三类。
- 一处需要记录的时序问题：Phase D 那次「有 skill」评测跑的是**纠正前**的正文，当时
  `references/arkui-navigation.md` 还照抄散文文档写着「`UIContext` 替代品自 API 18 起可用」，
  所以场景 1 与场景 4 的答卷也复述了 API 18。裁决 #11 之后正文与 `evals.json` 的该条
  `expected_behavior` 都已改为「访问器 `@since 10`」。**未据此重跑评测**——被纠正的是一个
  版本号，不是行为（两次答卷都正确地拒绝了全局 API 并给出 `UIContext` 替代），重跑不会改变
  任何一条达成/未达成的判定。如实记录，不改判。

### 未验证清单（完整）

以下全部标 `[official]`：读了官方页面，但本机没有工具链/设备可以实跑。凡本清单内的条目，
同步上游时应优先复核。

**先记本轮从清单里移出的四条**——补搜到 `openharmony/interface_sdk-js`（Apache-2.0）之后，
它们已升级为 `[verified]`，因为本机实读了 SDK 声明文件本身：

| 项 | 依据 |
|---|---|
| 全局 `router` 函数自 API 18 起废弃，替代为 `UIContext:Router` | `api/@ohos.router.d.ts:274-276` `@deprecated since 18` + `@useinstead` |
| `UIContext.getRouter()` / `getPromptAction()` 自 API 10 可用 | `api/@ohos.arkui.UIContext.d.ts:5178-5192` `@since 10` |
| `UIContext.isAvailable()` 自 API 20 可用 | 同文件 `5045-5047` `@since 20` |
| `AtManager.checkAccessToken()` 自 API 9（dynamic）/ API 23（static） | `api/@ohos.abilityAccessCtrl.d.ts:229-232` |

仍未验证的条目：

| 项 | 出处 | 为什么没验 |
|---|---|---|
| API 版本序 `26.0.0 > 6.1.1(24) > … > 5.0.5(17)` 与 `26.0.0` 起版本号格式调整 | `harmonyos-releases/app-compatibility-scenarios`（实读） | 需要 SDK Manager 才能看到本地可选版本 |
| `compatibleSdkVersion` / `targetSdkVersion` / `compileSdkVersion` 三字段语义、HarmonyOS 下 `compileSdkVersion` 不应显式配置、OpenHarmony 下必填 | `doccenter-deveco-studio/ide-hvigor-build-profile-app`（实读） | 无工程可编译验证 |
| 版本隔离型行为变更按 `targetSdkVersion` 呈现旧行为 | `harmonyos-releases/app-compatibility-scenarios`（实读） | 需要两台不同 API 版本的设备 |
| `hvigorw` 全部任务与参数（`assembleHap`/`assembleApp`/`assembleHsp`/`assembleHar`、`buildInfo -p json`、`--mode module -p module=x@default`、`--no-daemon`、`--analyze=*`、`prune`、`taskTree`） | `doccenter-deveco-studio/ide-hvigor-commandline`（实读） | `hvigorw` 不存在于本机 |
| `hvigorw` 需要 JDK + Node.js 在 `PATH` | 同上 | 同上 |
| `buildModeSet` 默认含 `debug`/`release`/`test`，`test` 由测试框架自动选用；`debuggable` 仅 release 缺省 false | `ide-hvigor-build-profile-app`（实读） | 同上 |
| `signingConfigs.material` 七个字段与 `.p12`/`.cer`/`.p7b` 角色；`signAlg` 当前仅 `SHA256withECDSA`；密码以密文存储；相对路径以**工程根**为起点 | `ide-hvigor-build-profile-app`（实读） | 无签名材料，也不应在本机生成 |
| `products[].signingConfig` 缺省 = 完全不签名 | 同上 | 同上 |
| 打包 APP 时校验各 HAP/HSP 的 `compatibleSdkVersion`/`targetSdkVersion` 一致 | 同上 + `packing-tool` | 无多模块工程 |
| 关联注册应用自动签名自 DevEco Studio 6.0.0 Beta5 起支持 | `ide-signing-auto`（实读） | 无 IDE |
| ArkGuard / 字节码混淆的配置位置与影响 | `bytecode-obfuscation-*` 系列 | 未跑构建 |
| `codelinter --format json` 的输出形状 | Huawei 命令行工具文档 | `codelinter` 不存在于本机 |
| `hdc` 子命令（`list targets -v`、`install`、`file send/recv`、`shell aa/bm/hilog/hidumper/uitest`）、`hdc shell -b <bundle>` 落在 debug 应用工作目录而非数据沙箱 | `dfx/hdc.md`（本机实读文件，但命令未执行） | 无设备/模拟器 |
| `uitest dumpLayout` / `screenCap` / `uiInput click` 的坐标是设备物理像素 | `application-test/uitest-guidelines.md` + `dfx/hdc.md` | 同上 |
| 模拟器需 DevEco Studio 内登录华为账号，纯 CLI 启动不是受支持路径 | 华为文档 + `linhay-harmony-next` 的实践记录 | 无 IDE/账号 |
| `@midscene/harmony@1` 的 `connect`/`launch`/`runhdcshell` 与 `MIDSCENE_MODEL_*` 环境变量；HarmonyOS 侧不支持双指缩放 | `midscene-harmony` SKILL.md（实读） | 无设备，也未配置视觉模型 |
| AppGallery 发布校验会因 `user_grant` 权限声明不完整而驳回 | `security/AccessToken/declare-permissions`（本机实读，明写 "used for application release verification"） | 无法提交真实包验证 |
| `requestPermissionOnSetting` 的可用版本与同组约束 | 华为文档（基线也引用了，未逐条复核） | 无设备；正文只写「引导到设置页」这一行为，不写版本与同组细节 |
| `ohos.permission.LOCATION` 必须与 `APPROXIMATELY_LOCATION` 同时申请 | 基线提出，华为定位文档（未逐条复核） | **未写入正文**；只在评测判定里作为基线的附带结论记录 |
| Asset Store Kit `SECRET` 字段上限 1–1024 字节 | 基线提出（未复核） | **未写入正文**；正文只写「密钥进 key store，`Preferences` 只放密文」 |
| `workScheduler` 单次回调约 2 分钟上限、最小重复间隔 20 分钟；`requestSuspendDelay()` 最多 3 分钟 | 基线提出（未复核） | **未写入正文**；`references/android-migration.md` 只写「`WorkManager` 无对应物，改用平台的后台任务机制重新设计」，不给未复核的数字 |
| `Preferences` 限额的历史版本值（80 B / 8192 B） | 基线提出，现行文档无版本限定（见 F4） | **未写入正文**；只写当前文档的 1024 B / 16 MB |

### 许可要盯的地方

- `openharmony/docs` 是 CC-BY-4.0，`NOTICE.md` 必须带署名。同步时**要重读 LICENSE**：它是
  唯一可合入的一等事实来源，一旦上游改许可，本 skill 的取证链就断了。
- `linhay-harmony-next`、`liasica-harmonyos`、`kwai-arkts` 三家永久 `reference`。即使它们
  将来加上 MIT/Apache 的 LICENSE 文件，**内容裁决仍然成立**——镜像的华为正文不是它们的。
  这条要写在后续同步的检查表里，避免下一轮误以为「许可变了就能 merged」。
- `oh-insight-migration` 目前无 LICENSE（`license: NONE`）。该仓库 97 个 skill 里只有 1 个
  在本 skill 范围内，其余面向 OpenHarmony OS 贡献者；同步时只看
  `skills/android-to-harmonyos-migration-workflow`。

### 后续同步要盯的上游

| 上游 | 盯什么 |
|---|---|
| `openharmony/docs` | `quick-start/typescript-to-arkts-migration-guide.md`（规则数量与 severity 变化）、`ui/state-management/arkts-new-*`（V2 在 ArkTS 卡片上的可用版本仍在推进）、`arkts-v1-v2-mixusage.md`、`quick-start/module-configuration-file.md` |
| developer.huawei.com | 版本说明与「变更预告」：`26.0.0` 之后的版本号格式、新的版本隔离型行为变更、DevEco Studio 与 SDK 的配对 |
| `web-infra-dev/midscene-skills` | `skills/harmony-automation` 的能力边界（双指手势是否开放）与 CLI 参数 |
| `CoreyLyn/harmonyos-skills` | 推送频率低但质量高，`references/` 若扩充值得重读 |

### 放弃的方向

- **Native/NDK 深入**。`earfrog-arkts` 提供了完整的 Node-API/XComponent/EGL 路线，但本机
  无法验证任何一环，且它自己构成一个完整主题。本 skill 只写到「JNI 不适用，边界是 Node-API
  + `.d.ts` facade + `externalNativeOptions`，四层逐层验证」，把细节留给迁移场景。
- **华为 Kit 逐个展开**（Push / Map / IAP / Scan / Share）。属产品 API 说明书，`docs/roadmap.md`
  已排除这一类；`makerjackie/harmonyos-skills` 因此被 REJECT。
- **ArkTS 1.2 / 静态 ArkTS**（`openharmonyinsight` 的 `arkts-static-spec`、`arkts-sta-playground`）。
  面向编译器与 OS 贡献者，不是应用开发者的当前工作面。
- **仓颉（Cangjie）**。仍在 beta，应用生态几乎为零。
- **`wechat-miniprogram`、`unity`、`godot`、`unreal`** 在本波次尚不存在，正文遇到相关边界时
  按约定写「no skill in this library covers it yet」——实际上本 skill 的否定范围没有落到这四个
  主题上，所以正文里并未出现这句话。
