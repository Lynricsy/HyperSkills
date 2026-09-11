# unity 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

**立项通道：常规通道（判据第 2 条）。** 官方厂商特例**不成立**——特例要求「官方文档
（`kind: docs`）可 merged」，而 Unity 官方文档正文是 CC BY-NC-ND 4.0、代码片段是 Unity
Companion License，两者都不允许改写分发；`Unity-Technologies/skills` 同样是 Unity Companion
License。三个官方上游全部只能 `reference`。本 skill 靠三个活跃、评分 ≥8 的第三方上游
（gamedev-skills、Nice-Wolf-Studio、wshobson）满足判据第 2 条。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `gh search code --filename SKILL.md "unity"`（60 条）、`gh search repos`
  - `web_search`：`"unity agent skill SKILL.md github"`
  - 领域官方组织仓库：`Unity-Technologies/`（skills、UnityCsReference、Graphics、InputSystem、
    EntityComponentSystemSamples）
  - `github/awesome-copilot`（全树 grep `unity` → **零命中**，不是候选）
  - docs.unity3d.com（Manual + Scripting Reference + `com.unity.test-framework` 包文档）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count,
  pushed:.pushed_at, license:.license.spdx_id}'`；**每个 NOASSERTION 都实读了 LICENSE 正文**。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gamedev-skills/awesome-gamedev-agent-skills `skills/unity/{unity-csharp-scripting,unity-physics,unity-build-pipeline,unity-scriptableobjects,unity-input-system,unity-animation,unity-navmesh,unity-tilemap-2d}` | https://github.com/gamedev-skills/awesome-gamedev-agent-skills | 943 | 2026-09-10 | Apache-2.0（实读 LICENSE 正文，根目录单一许可，无逐目录声明） | 脚本、物理、构建管线、SO 架构、输入、动画、NavMesh、Tilemap | 2 | 3 | 3 | 1 | 2 | 11 | INCLUDE / merged | 八个 skill 全部「Core workflow + Patterns + Pitfalls」结构，Pitfalls 全是可证伪的陷阱且已带 Unity 6.3 版本门。正确性扣分见「冲突与裁决」#1（`Rigidbody.velocity` 断言错误）。无 rendering / ui / testing / DOTS 覆盖 |
| 2 | Nice-Wolf-Studio/unity-claude-skills `skills/unity-{scripting,lifecycle,performance,physics,physics-queries,graphics,ui,ui-patterns,testing,ecs-dots,editor-tools,scene-assets,async-patterns,platforms,packages-services,...}`（35 个 skill） | https://github.com/Nice-Wolf-Studio/unity-claude-skills | 30 | 2026-07-29 | MIT（实读 LICENSE 正文） | 覆盖面最全：rendering / ui / testing / DOTS / editor / 平台 / 内存，本波次唯一填上 gamedev-skills 空白的可合入上游 | 1 | 2 | 3 | 1 | 2 | 9 | INCLUDE / merged | 每个 skill 15–45 KB + references，`linearVelocity`/`linearDamping` 等 Unity 6 重命名全对，`[UxmlElement]` 取代 `UxmlFactory` 也对。正确性扣分见「冲突与裁决」#2（UI 系统推荐与官方文档相反） |
| 3 | wshobson/agents `plugins/game-development/skills/unity-ecs-patterns`（+ `references/details.md` 565 行） | https://github.com/wshobson/agents | 39565 | 2026-09-07 | MIT | DOTS/ECS：`ISystem` vs `SystemBase`、EntityQuery、ECB、Aspect、Baking、Jobs + NativeCollection 处置 | 2 | 3 | 2 | 3 | 2 | 12 | INCLUDE / merged | 抽查 3 条（`ISystem` 优于 `SystemBase`、托管类型破坏 Burst、结构性变更必须走 ECB）全部与官方 Entities 文档一致。SKILL.md 只有 62 行导航层，实质在 `references/details.md` |
| 4 | Unity-Technologies/skills（31 个 skill：`unity-cli`、`new-unity-project`、`ui-uitk`、`ui-ugui`、`ui-imgui`、`urp-postprocessing`、`migrate-birp-to-urp`、`optimize-{audio,text-mesh-pro,web}`、`physics-3d-collision`、`validate-urp-render-graph-renderer-feature`、`unity-package-management`、`manage-sprite-atlas` …） | https://github.com/Unity-Technologies/skills | 823 | 2026-09-10 | **Unity Companion License**（`LICENSE.md` 实读：「Unity Skills © 2026 Unity Technologies. Licensed under the Unity Companion License for Unity-dependent projects」——不是 OSI 开源许可，仅授权用于依赖 Unity 的项目） | 官方 skill 仓库 | 3 | 3 | 3 | 3 | **0** | 12 | **reference**（许可裁决） | 许可分 0 且量表注明「专有 = 不得作为 merged」。**未读取任何 SKILL.md 正文、未复制任何文字或脚本**；只用其 31 个目录名作覆盖面清单（与 GPL 上游同一处理方式），事实一律改从 docs.unity3d.com 与 UnityCsReference 取证 |
| 5 | docs.unity3d.com（Unity 6.6 Manual + Scripting Reference；`6000.3/` 路径用于 LTS 对照） | https://docs.unity3d.com/Manual/index.html | — | 2026-09-10（页脚 build 日期） | **正文 CC BY-NC-ND 4.0；代码片段 Unity Companion License**（`Manual/TermsOfUse.html` 实读） | 唯一权威事实源 | 3 | 3 | 3 | 3 | 0 | 12 | **reference**（许可裁决） | NC + ND 双重限制，命中 `docs/roadmap.md`「CC-BY-NC-* / CC-BY-ND-* → reference」。本 skill 全部官方事实都在此核对，但一句话都不照抄 |
| 6 | Unity-Technologies/UnityCsReference（`6000.3` / `6000.4` / `6000.6` / `master`=`6000.7` 分支） | https://github.com/Unity-Technologies/UnityCsReference | 12983 | 2026-09-11 | **Unity Reference-Only License**（`LICENSE.md` 实读，仅一行指向该许可） | `UnityEngine` C# 源码：`[Obsolete]` 实际文本、方法签名、内部注释 | 3 | 3 | 3 | 3 | 0 | 12 | **reference**（许可裁决） | 本 skill 的 `[verified]` 全部出自此处：逐版本 `git show` 对比声明，比散文文档更可靠且可机器核对（与波次 8 `harmonyos` 用 `.d.ts` 推翻散文结论同一手法）。不复制任何源码 |
| 7 | Unity-Technologies/Graphics（URP / HDRP / SRP core 包源码） | https://github.com/Unity-Technologies/Graphics | 2987 | 2026-09-09 | **Unity Companion License**（`LICENSE.md` 实读） | URP 版本与 `BatchRendererGroup`/GPU Resident Drawer 实现 | 3 | 3 | 3 | 3 | 0 | 12 | **reference**（许可裁决） | 仅用于确认 URP 侧 API 存在性；URP 的散文文档已迁出本仓库，事实取自 docs.unity3d.com |
| 8 | Unity-Technologies/EntityComponentSystemSamples | https://github.com/Unity-Technologies/EntityComponentSystemSamples | 8178 | 2026-09-10 | **Unity Companion License**（`LICENSE.md` 实读） | DOTS 官方示例 | 3 | 3 | 3 | 3 | 0 | 12 | **reference**（许可裁决） | 用于交叉校验 wshobson 的 DOTS 断言 |
| 9 | Besty0728/Unity-Skills `SkillsForUnity/unity-skills~/SKILL.md` | https://github.com/Besty0728/Unity-Skills | 1735 | 2026-09-11 | MIT（实读 LICENSE 正文） | 一个 Unity Editor 包，把 Addressables/Animator/Asset/Audio/Batch 等编辑器操作暴露成 agent 可调用的工具 | 1 | 3 | 2 | 2 | 2 | 10 | **reference**（内容裁决） | 许可宽松但内容是**该包自身的工具说明书**（产品包装类，命中已排除类别）。它教的是「怎么调用 SkillsForUnity 的 API」，不是「Unity 怎么用」；装不上这个包就一条都用不上 |
| 10 | Mindrally/skills `unity/SKILL.md` | https://github.com/Mindrally/skills | 260 | 2026-09-03 | Apache-2.0 | 62 行 Cursor rule 转写 | 1 | 3 | 1 | 1 | 2 | 8 | **reference**（内容裁决） | 分数刚到线但内容不值得合入：通篇「Write clear code」「Use profiler to identify bottlenecks」式空话，无一条带版本门或后果；frontmatter 有重复的 `---` 分隔符；`Always use TextMeshPro for text rendering` 是无条件断言（UI Toolkit 有自己的文本后端）。命中标准第 3 节「不重复模型已知的常识」 |
| 11 | dyCuong03/unity-agent-team `.claude/skills/{burst-safety,architect,...}` | https://github.com/dyCuong03/unity-agent-team | 7 | 2026-07-25 | MIT | 一套 Unity agent 编排（skill 缓存、置信度路由）+ 少量 Unity 规则 | 1 | 2 | 1 | 2 | 2 | 8 | **reference**（内容裁决） | 主体是 agent 编排基础设施（`skill-cache-freshness`、`dynamic-skill-reload`），属 harness 层而非 Unity 知识；仅 `burst-safety`（3.7 KB）与本 skill 相关，且被 wshobson 的 DOTS 内容覆盖 |
| 12 | chahat1709/professional-game-developer.skill | https://github.com/chahat1709/professional-game-developer.skill | 3 | 2026-08-25 | MIT | 引擎无关的「专业游戏开发者」通才 skill（3D 建模、技术美术、动画工程、资产管线…） | 0 | 2 | 1 | 1 | 2 | 6 | MAYBE→REJECT | 引擎无关，不落到 Unity 的任何可证伪不变量；`3d-modeling-technical-art.md` 之类与本 skill 范围无交集 |
| 13 | Ryan-focus/unity-claude-code-skill | https://github.com/Ryan-focus/unity-claude-code-skill | 1 | 2026-04-14 | MIT | 单个 11.5 KB SKILL.md + 四种语言 i18n 副本 | 0 | 1 | 1 | 1 | 2 | 5 | REJECT | 5 个月未动，内容是 i18n 副本占大头；单文件覆盖不到本 skill 的任何同构主题深度 |
| 14 | batihandev/unity-mcp-skills | https://github.com/batihandev/unity-mcp-skills | 6 | 2026-08-01 | MIT | `skills/{animator,asset,camera,cinemachine,...}` 全部是「通过某个 Unity MCP server 调用编辑器」的 recipe | 0 | 2 | 2 | 1 | 2 | 7 | REJECT | 产品包装类：依赖特定 MCP server 才成立，`recipes/_shared/*` 就是该 server 的调用约定 |
| 15 | tea-x-random/unity-game-skills | https://github.com/tea-x-random/unity-game-skills | 2 | 2026-07-10 | MIT | `unity-3d-generator`、`unity-aaa-graphics`（含 `prompt-library.md`）、`unity-analytics-liveops` | 0 | 2 | 1 | 1 | 2 | 6 | REJECT | 主体是生成式美术提示词库，不是引擎工程知识 |
| 16 | quanarmy/Unity-Agent-Skills | https://github.com/quanarmy/Unity-Agent-Skills | 0 | 2026-07-26 | MIT | 与 #9 同一份 `SkillsForUnity/unity-skills~/` 树 | 0 | 2 | 2 | 2 | 2 | 8 | REJECT | Besty0728/Unity-Skills 的派生副本（同名文件同字节数），0 星且落后于上游。重复候选不单独计分 |
| 17 | frederico-kluser/unity-gamedev-agent-skill | https://github.com/frederico-kluser/unity-gamedev-agent-skill | 0 | 2026-08-30 | MIT（API 报 NOASSERTION，**实读 LICENSE 正文为 MIT**） | 单个 21 KB skill + 40 KB 葡萄牙语架构文档 | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | 0 星、单人、主文档非英文；根 `SKILL.md` 只有 37 字节（占位）。许可判定已纠正 API 的 NOASSERTION |
| 18 | Ecobru-source/unity-agent-knowledge-bootstrap | https://github.com/Ecobru-source/unity-agent-knowledge-bootstrap | 1 | 2026-07-07 | **NONE**（树中无 LICENSE 文件） | 单个 9 KB SKILL.md | 0 | 2 | 1 | 1 | 0 | 4 | REJECT | 无许可 + 无实质内容；即使按「无许可但公开」规则也不值得合入 |
| 19 | 4Players/odin-agent-skills | https://github.com/4Players/odin-agent-skills | 0 | 2026-03-10 | MIT | ODIN 语音 SDK 接入 | 1 | 1 | 2 | 2 | 2 | 8 | REJECT | SaaS 产品包装类（命中 `docs/roadmap.md` 已排除类别），且语音服务不在本 skill 范围 |
| 20 | sickn33/agentic-awesome-skills | https://github.com/sickn33/agentic-awesome-skills | 46268 | 2026-09-09 | MIT | 巨型聚合仓库 | 1 | 3 | — | — | 2 | — | REJECT | 全树 grep `unity` **零个 Unity skill**（web_search 的 `unity-developer` 指向不存在的路径）。留行以免下轮重查 |
| 21 | github/awesome-copilot | https://github.com/github/awesome-copilot | 38900+ | 2026-09 | MIT | 418 skills + 193 instructions | 3 | 3 | — | — | 2 | — | REJECT | 全树 grep `unity` 零命中（只有 `extensions/*-canvas/game/*.js` 这类 Web 小游戏）。留行以免下轮重查 |

**候选数：21（≥12）。可合入且 ≥8 分：3 个（#1 #2 #3）→ 判据第 2 条满足。**

## 深度审查

### #1 gamedev-skills/awesome-gamedev-agent-skills（Apache-2.0，merged 主干）

- 结构：`skills/<engine>/<engine>-<topic>/SKILL.md` + 可选单个 `references/*.md`。每个
  SKILL.md 121–145 行，固定为 `When to use` / `Core workflow` / `Patterns` / `Pitfalls` /
  `References` / `Related skills`。
- frontmatter：只有 `name` + `description`，无 agent 专属字段，剥离成本为零。
- 质量：Pitfalls 节是本仓库最想要的那种写法——每条都是「症状 → 原因 → 改法」，且已经带
  `Unity 6.3 LTS` 版本标注。`unity-physics` 的触发器矩阵、`unity-build-pipeline` 的
  `link.xml` / 托管剥离 / Addressables 独立内容构建都是直接可用的不变量。
- agent 绑定：`Related skills` 指向同仓库的 `physics-tuning`、`steam-publish` 等，合入时
  必须全部删掉（本库无这些 skill）。
- 空白：**没有 rendering、ui、testing、DOTS、editor-tooling、assets/memory 主题**。本波次
  要求的五个同构主题里，它只覆盖 `scripting`、`physics`、`build`。

### #2 Nice-Wolf-Studio/unity-claude-skills（MIT，merged 补全）

- 结构：35 个 `skills/unity-*/SKILL.md`（11–45 KB）+ 1–4 个 `references/*.md`。
- frontmatter：含 `globs:` 这个 agent 专属字段，合入时必须剥离（标准第 1.2 节）。
  `description` 末尾统一写 `Based on Unity 6.3 LTS documentation`。
- 质量：正是 #1 缺的那些主题的唯一可合入来源——`unity-graphics`（URP/HDRP/Shader Graph/
  材质）、`unity-ui`（UI Toolkit/uGUI/TMP/data binding）、`unity-testing`（Test Framework）、
  `unity-ecs-dots`、`unity-editor-tools`（custom inspector / property drawer / editor window）、
  `unity-performance`（profiler / memory）、`unity-scene-assets`（Addressables）。
- 风险：`description` 自述「基于 Unity 6.3 LTS 文档」，即内容是**文档改写**。Unity 文档是
  CC BY-NC-ND，上游自己按 MIT 分发不改变 Unity 的原始许可；因此合入时只取其**主题结构与
  清单语义**，每条事实都在 docs.unity3d.com / UnityCsReference 上重新取证后用自己的话写。
  这和 CC-BY-SA 上游（trailofbits）的处理方式一致。
- 重叠：与 #1 在 scripting / physics 上重叠约 60%，#1 的 Pitfalls 更锋利，#2 的 API 表更全。
  重叠部分以 #1 的结论为准，缺的 API 形状从 UnityCsReference 补。

### #3 wshobson/agents `unity-ecs-patterns`（MIT，merged 窄面）

- 结构：62 行导航层 SKILL.md + 565 行 `references/details.md`（8 个编号 pattern + 性能清单）。
- 质量：DOTS 是本 skill 最容易写错的一块，这份是唯一一个把 `ISystem`/`SystemBase` 选择、
  `EntityCommandBuffer` 的必要性、`NativeArray` 处置、chunk 利用率讲到可执行程度的可合入上游。
- 边界：只覆盖 DOTS。它的 `Don't over-architect` 正好支撑本 skill 要写的「DOTS 适用边界」
  一节——绝大多数项目不该上 DOTS。

### #4 Unity-Technologies/skills（Unity Companion License，reference）

- **许可实读结论**：`LICENSE.md` 正文为「Unity Skills © 2026 Unity Technologies. Licensed
  under the Unity Companion License for Unity-dependent projects」。Unity Companion License
  不是 OSI 批准的开源许可，只授权在依赖 Unity 的项目中使用，不允许本仓库这种通用改写分发。
- 出处与复查命令（同步时原样重跑，不要只看 `gh api repos/...` 的 `license.spdx_id`，它报
  `NOASSERTION`）：

  ```bash
  gh api repos/Unity-Technologies/skills/contents/LICENSE.md --jq .content | base64 -d
  ```

  本次读取的树是 `main@d54932a923f9d7479a4ca59c421606db8b9cb27e`。许可正文链接指向
  <https://unity3d.com/legal/licenses/unity_companion_license>。
- 处理：`relation: reference`。**未读取任何 `SKILL.md` / `references/` / `resources/*.cs`
  正文**，只从 `git/trees` 拿到 31 个目录名当覆盖面清单。本 skill 因此补上了
  `migrate-birp-to-urp`（BiRP→URP 迁移）、`ui-uitk` vs `ui-ugui` vs `ui-imgui` 三分、
  `validate-urp-render-graph-renderer-feature`（Render Graph 校验）、`manage-sprite-atlas`
  这几个原本会漏掉的主题，事实全部另行取证。

### #5 docs.unity3d.com（CC BY-NC-ND 4.0 + Unity Companion License，reference）

- **许可实读结论**：`Manual/TermsOfUse.html` 明确二分——「Code snippets … licensed under the
  Unity Companion License」「All other information in the Unity Manual and Scripting Reference
  is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 4.0
  International (CC BY-NC-ND)」。NoDerivatives 直接禁止改写，NonCommercial 也与本仓库 MIT
  不兼容。→ `reference`。
- 出处页（同步时按原样重查这一页，不要用记忆或其他页面替代）：
  <https://docs.unity3d.com/Manual/TermsOfUse.html>，页脚记录本次读取的构建为
  「Built from job ID 75126244. Built on: 2026-09-10」，文档版本 Unity 6.6 (6000.6)。
  该页还是本仓库唯一能确认「代码片段」与「其余内容」分属两种许可的地方——不要只看
  `unity.com/legal` 的许可列表页，那里没有这条二分。
- 因此**官方厂商特例不成立**，与波次 5 `elasticsearch`、波次 8 `harmonyos` 同一情形。

### #6 Unity-Technologies/UnityCsReference（Unity Reference-Only License，reference）

- **许可实读结论**：`LICENSE.md` 全文一行——「For terms of use, see
  https://unity3d.com/legal/licenses/Unity_Reference_Only_License」。仅供阅读参考。→ `reference`。
- 用法：按分支 `git show <branch>:<path>` 逐版本比对声明。这是本 skill 全部 `[verified]`
  标注的唯一依据，也是推翻两条上游散文结论的依据（见「冲突与裁决」#1、#3）。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | `Rigidbody.velocity` 在 Unity 6 里还能不能用 | gamedev-skills `unity-physics` Pitfalls：「**`Rigidbody.velocity` doesn't exist in Unity 6.3 LTS** — use `linearVelocity`」 / Nice-Wolf 只列 `linearVelocity` 不提旧名 | **两者都不准确**。正文写：`velocity`/`drag`/`angularDrag` 仍然存在，但带 `[Obsolete(... (UnityUpgradable) -> linearVelocity)]`，是**编译警告 + API Updater 自动改写**，不是编译错误 | `UnityCsReference@6000.3:Modules/Physics/ScriptBindings/Rigidbody.deprecated.cs:13,17,21` 三条 `[Obsolete]` 属性实读。「不存在」会让人以为旧代码编不过，从而误判升级工作量 |
| 2 | 新项目的运行时 UI 该选哪个系统 | Nice-Wolf `unity-ui`：「**UI Toolkit is the recommended system for new projects**」、把 uGUI 标成 `legacy` / Unity 官方文档：运行时**推荐 uGUI**，UI Toolkit 是 Alternative；Editor 推荐 UI Toolkit，IMGUI 是 Alternative | **按官方文档**：运行时默认 uGUI，UI Toolkit 用于「大量 UI + 多分辨率 + 无贴图渲染 + 世界空间 UI + 自定义 shader」；Editor 一律 UI Toolkit。uGUI 不是 legacy（IMGUI 才是「legacy, not recommended for runtime UI」） | `docs.unity3d.com/Manual/UI-system-compare.html`（Unity 6.6）与 `6000.3/Documentation/Manual/UI-system-compare.html`（Unity 6.3 LTS）**两个版本的推荐表完全一致**，排除了「文档滞后」的解释。官方厂商 > 社区 |
| 3 | `FindObjectsByType` 的正确调用形式 | Nice-Wolf / 社区普遍：`FindObjectsByType<T>(FindObjectsSortMode.None)` 最快 / gamedev-skills：只说 `Find*` 贵 | 正文写**版本分界**：6.3 LTS 上 `FindObjectsSortMode.None` 是推荐形；**Unity 6.4 起** `FindObjectsSortMode` 整个枚举、带该参数的 `FindObjectsByType` 重载、以及 `FindFirstObjectByType` 全部标记 `[Obsolete]`，改用无排序参数的重载与 `FindAnyObjectByType` | 逐分支实读：`6000.3` 上 `FindObjectsSortMode` 无 `[Obsolete]` 且 `FindFirstObjectByType` 干净；`6000.4`/`6000.5`/`6000.6`/`master(6000.7)` 上三者全部 `[Obsolete]`，理由是「InstanceID will be replaced in the future with EntityId」。这正是升级编辑器后凭空长出几百条警告的原因 |
| 4 | CI 里 `-quit` 的地位 | gamedev-skills `unity-build-pipeline`：「`-quit` ensures the editor closes；Exit code is 0 on success」 / 官方 CLI 文档：`-quit`「can hide some error messages」，跑测试时不受支持，遇到异步代码会挂死 | 正文写：退出码必须由 `-executeMethod` 的方法用 `EditorApplication.Exit(code)` 自己给；`-quit` 只是兜底，跑 `-runTests` 时**必须不加** | `docs.unity3d.com/Manual/EditorCommandLineArguments.html`（`-quit` / `-executeMethod` 两条）+ `com.unity.test-framework@1.5` 命令行参考末尾的 Note。官方 > 社区 |
| 5 | Unity 6 的默认版本基线该写哪个 | 上游一律写 `Unity 6.3 LTS (6000.3)` / 官方文档当前默认版本是 Unity 6.6，`UnityCsReference` 已有 `6000.7` 分支 | 正文以 **Unity 6.3 LTS（6000.3）为默认基线**（项目不声明版本时），同时把 6.4/6.6 的差异写成显式版本门 `(Unity 6.4+)` / `(Unity 6.6)` | Unity 6.3 是当前 LTS（2025-12 发布，标准支持到 2027-12）；6.6 是 2026-09-01 发布的 Update 流，只支持到下一个版本。生产项目锁 LTS，所以基线取 LTS，新差异标版本门 |
| 6 | `MaterialPropertyBlock` 算优化还是反优化 | 社区常见说法：用 MPB 避免材质实例化、省内存 | 正文写：MPB **定义上就让该 renderer 与 SRP Batcher 不兼容**，并且让它被 GPU Resident Drawer 静默排除；URP 下要做逐实例差异应优先材质变体或 shader 的逐实例属性 | `Manual/SRPBatcher-Materials.html`「The GameObject mustn't use MaterialPropertyBlocks」+ `Manual/urp/gpu-resident-drawer.html`「Does not have MaterialPropertyBlocks set on them」 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `gamedev-unity` | gamedev-skills/awesome-gamedev-agent-skills `skills/unity/*` | merged | 主干骨架：MonoBehaviour 生命周期取舍、`FixedUpdate` 分工、序列化陷阱、物理触发器/层、构建管线（IL2CPP、托管剥离、`link.xml`、Addressables 独立内容构建）、ScriptableObject 架构 |
| `nicewolf-unity` | Nice-Wolf-Studio/unity-claude-skills `skills/unity-*` | merged | 补全 gamedev-skills 缺的主题结构：rendering（URP/材质/Shader Graph）、ui（UI Toolkit/uGUI/TMP）、assets & memory（Addressables/图集/压缩）、editor tooling、testing、`Awaitable` 与协程取舍 |
| `wshobson-unity-ecs` | wshobson/agents `plugins/game-development/skills/unity-ecs-patterns` | merged | DOTS/ECS：`ISystem` vs `SystemBase`、EntityQuery、`EntityCommandBuffer`、Baking、Jobs + NativeCollection 处置，以及「多数项目不该上 DOTS」的适用边界 |
| `unity-official-skills` | Unity-Technologies/skills | reference | **仅目录名作覆盖面清单**（Unity Companion License，未读正文、未复制任何文字或脚本）：补上 BiRP→URP 迁移、UI 三系统分工、Render Graph renderer feature 校验、Sprite Atlas 管理、`unity-cli` 这几个主题 |
| `unity-docs` | docs.unity3d.com（Manual + Scripting Reference + `com.unity.test-framework` 包文档） | reference | 全部 `[official]` 事实的出处：碰撞/触发器矩阵、SRP Batcher 与 GPU Resident Drawer 的兼容条件、UI 系统官方推荐、Editor 命令行参数、Test Framework 命令行参数 |
| `unity-cs-reference` | Unity-Technologies/UnityCsReference（`6000.3`/`6000.4`/`6000.6`） | reference | 全部 `[verified]` 事实的出处：`[Obsolete]` 实际文本与版本分界、`Awaitable` 的一次性/无同步上下文约束、`destroyCancellationToken` 的 `MissingReferenceException`、`Rigidbody` 重命名 |
| `unity-graphics` | Unity-Technologies/Graphics | reference | 确认 URP/SRP core 侧 `BatchRendererGroup`、GPU Resident Drawer 实现存在性与包版本 |

## 基线缺口

无 skill（`uv run tools/run_evals.py unity --baseline`，Claude Opus 5 · medium，5/5 `ok`，
`skill_read` 全部 `false`）时，各场景未达成的 `expected_behavior`。基线水位很高——Opus 5
对 Unity 的通识掌握得相当好，五条里往往四五条达成——所以缺口全部集中在**版本分界**与
**官方兼容性清单**这两类「记不住、且记错会造成事故」的事实上，这正是 Phase B 要求的量规形态。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1（GC 锯齿审查） | Unity 6.4 的 `FindObjectsByType` 分界 | 基线正确指出 `FindObjectsOfType` 已废弃，但把 `FindObjectsByType<Enemy>(FindObjectsSortMode.None)` 当作**推荐写法**给出。该重载与 `FindObjectsSortMode` 枚举自 **6.4 起整体 `[Obsolete]`**，`FindFirstObjectByType` 同时让位给 `FindAnyObjectByType`。不只是漏了分界，而是主动推荐了升级后会长出警告的形式。另外五条（缓存 `GetComponent`/`GameObject.Find`/`Camera.main`、`CompareTag`、字符串与 `Debug.Log` 分配、`RaycastAll` 分配、`transform.position` 写 Rigidbody + `linearVelocity` 重命名、`Update` 里 `StartCoroutine`）全部达成，且额外发现了方向向量未归一化与 `Vector3.Distance` 的 `sqrt`。 |
| 2（序列化） | `Dictionary` 的 6.6 分界 | 基线断言「`Dictionary<string,int>` 不在 Unity 序列化器支持类型里（不支持泛型字典）」，无任何版本限定。自 **Unity 6.6** 起 `[SerializeField] Dictionary<TKey,TValue>` 已是受支持的字段类型（6.3 LTS 手册仍把 dictionary 列在不支持的 multilevel types 里）。其余四条达成。**反向修正**：基线在此题上比本 skill 初稿更准确——它指出 `[SerializeField]` 放在自动属性上是 **CS0592 编译失败**而非静默无效；经 `UnityCsReference@6000.3` 复核（`SerializeField` 声明为 `[AttributeUsage(AttributeTargets.Field)]`）确认基线正确，已据此改写 Core rule 1 与 `unity-serialization.md`，并收紧该条量规。 |
| 3（URP SetPass） | GPU Resident Drawer 的逐对象排除项 | 基线明确断言「`OnBecameVisible` 是红鲱鱼，与合批完全无关；GRD 排除的是 `OnRenderObject` 这类逐实例渲染回调，不是可见性回调」——与官方 URP 文档**正好相反**：排除项是 `OnWillRenderObject` / `OnBecameVisible` / `OnBecameInvisible`，而 `OnRenderObject` 根本不在清单里。夹具刻意给每个箱子挂了 `OnBecameVisible`，基线把它判成无关项。同时漏了 ≤128 材质与 Light Probe *Use Proxy Volume* / *Anchor Override* 两条前置，`UnityPerDraw` 也只提到 `UnityPerMaterial` 一半。其余五条（MPB 不兼容、`renderer.material` 克隆、shader CBUFFER、SRP Batcher 降的是状态切换而非 draw call、`Standard` 洋红）达成。 |
| 4（CI 构建） | `Editor` 文件夹要求；`-accept-apiupdate` | 基线把退出码、`-quit`、`-logFile -`、`BuildReport.steps[].messages`、`-nographics`、许可、`BuildOptions.Development` 全部讲对，但**完全未提** `-executeMethod` 要求目标脚本位于 `Editor` 文件夹（夹具刻意把它放在 `Assets/CI/BuildScript.cs`，注释里也写明了路径），也未提批处理模式下不带 `-accept-apiupdate` 时 API Updater 不运行、表现为无法解释的编译错误。前者是该夹具最隐蔽的一处缺陷。 |
| 5（负例，`skills: []`） | —（不适用） | 基线模式下没有 skill 可读，`skill_read=false`。回答完全落在 dotnet 工具链（`dotnet-counters` 计数器名、`ServerGarbageCollection` 应改 csproj 而非 `runtimeconfig.json`、`[MemoryDiagnoser]`），并主动纠正了提问里「csproj job attribute」的错误前提。此场景的意义在「有 skill」那一轮：确认 `skill_read` 仍为 `false`。 |

## 评测结果

两轮都是 `anthropic/claude-opus-5` · thinking `medium`（`tools/run_evals.py` 默认，未传
`--model` / `--thinking`），5/5 `status=ok`，无超时。夹具与题目在两轮之间**一字未改**；
第 2 场的 `expected_behavior` 在基线跑完后按 Phase B 收紧成版本分界口径（见备注），
属于量规改写而非 prompt 改写，因此基线转录仍按新量规重判、未重跑。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 GC 锯齿审查 | claude-opus-5 / medium | 无（baseline） | false | 5 / 6 | 缺 Unity 6.4 分界，且主动推荐了 6.4 起废弃的 `FindObjectsSortMode.None` 形式 |
| 1 GC 锯齿审查 | claude-opus-5 / medium | 有 | **true** | **6 / 6** | 「6000.3 上 `FindObjectsByType` 是正解；升到 6.4 后 `FindObjectsSortMode` 与 `FindFirstObjectByType` 也会变 `[Obsolete]`（EntityId 取代 instance-ID 排序），所以缓存注册表比换 API 更耐放」——分界给对，并据此改了建议的优先级 |
| 2 序列化 | claude-opus-5 / medium | 无（baseline） | false | 4 / 5 | 「不支持泛型字典」无版本限定；其余四条达成 |
| 2 序列化 | claude-opus-5 / medium | 有 | **true** | **5 / 5** | 「6.3 LTS 把 Dictionary 归为 multilevel type 直接丢弃（6.6 才支持）」；并把 `[SerializeField]` 放属性上判为 `CS0592`（`AttributeTargets.Field`）且指出「设计师看到的 Inspector 是上一次成功编译的旧版本」，把两种失败模式分开了 |
| 3 URP SetPass | claude-opus-5 / medium | 无（baseline） | false | 5 / 6 | GRD 排除项判反：断言 `OnBecameVisible` 无关、`OnRenderObject` 才被排除 |
| 3 URP SetPass | claude-opus-5 / medium | 有 | **true** | **6 / 6** | 「被排除的是**可见性**回调（`OnWillRenderObject`/`OnBecameVisible`/`OnBecameInvisible`），`OnRenderObject` 不在名单上」，Forward+ / `Keep All` / MPB 三重失效逐条点出，并补上 `UnityPerDraw` 与「`UnityPerMaterial` 布局在每个 pass 必须一致」 |
| 4 CI 构建 | claude-opus-5 / medium | 无（baseline） | false | 5 / 7 | 缺 `Editor` 文件夹要求与 `-accept-apiupdate` |
| 4 CI 构建 | claude-opus-5 / medium | 有 | **true** | **7 / 7** | 「`Assets/CI/` → `Assets/Editor/CI/`。不在 `Editor` 目录里 `-executeMethod` 解析不到」「缺 `-accept-apiupdate`：batch mode 下 API Updater 不跑」；并把 `-quit` 保留在激活调用、从构建调用移除 |
| 5 负例（`skills: []`） | claude-opus-5 / medium | 无（baseline） | false | 3 / 3 | 全落在 dotnet 工具链 |
| 5 负例（`skills: []`） | claude-opus-5 / medium | 有 | **false** ✅ | **3 / 3** | 有 skill 可读但**没有读**。全文 `unity`/`MonoBehaviour` 出现 0 次；并纠正了提问的三个错误前提（`ServerGarbageCollector` 实际是 `System.GC.Server` / csproj 的 `ServerGarbageCollection`；Web SDK 默认已是 Server GC；`[MemoryDiagnoser]` 是 diagnoser 而非 job 属性） |

结论：**通过。** 四个正例各有一条基线未达成的行为在有 skill 时达成，且四条恰好各对应一类
Core rule——rule 11（6.4 `Find*` 分界）、rule 1 + 3（`CS0592` 与 `Dictionary` 6.6 分界）、
rule 21（GRD 逐对象排除项）、rule 25 + `unity-build.md`（`Editor` 文件夹与
`-accept-apiupdate`）。负例 `skill_read=false`，`description` 末尾用提问自己的词汇
（`ASP.NET Core`、`dotnet-counters`、`BenchmarkDotNet`）点名排除项，一次就成，无需收紧重跑。
顺带一个可观测的副作用：有 skill 时四个正例的耗时都比基线短（117.7/78.7/110.2/101.2 s 对
165.3/155.0/238.9/136.5 s）——答案已经在 reference 里，模型不必自己重建推理链。

## 备注

### 许可实读结论（本 skill 最重要的一条产出）

四个官方上游**全部只能 `reference`**，逐一实读：

| 上游 | 实读文件 | 许可 | 结论 |
|---|---|---|---|
| Unity-Technologies/skills | `LICENSE.md` | Unity Companion License（仅授权依赖 Unity 的项目，非 OSI 开源） | `reference`；未读任何 SKILL.md / references / resources 正文，未复制一个字或一行脚本，只用 `git/trees` 拿到的 31 个目录名作覆盖面清单 |
| docs.unity3d.com | `Manual/TermsOfUse.html` | 代码片段 Unity Companion License；**其余全部内容 CC BY-NC-ND 4.0** | `reference`；NC + ND 双重限制 |
| Unity-Technologies/UnityCsReference | `LICENSE.md` | Unity Reference-Only License | `reference`；仅阅读声明以取证 |
| Unity-Technologies/Graphics、EntityComponentSystemSamples | 各自 `LICENSE.md` | Unity Companion License | `reference` |

由此**官方厂商特例（判据第 4 条）不成立**——特例要求官方文档可 merged，而 Unity 文档是
CC BY-NC-ND。与波次 5 `elasticsearch`、波次 8 `harmonyos` 同一情形，走常规通道，靠
gamedev-skills（Apache-2.0, 11 分）、Nice-Wolf-Studio（MIT, 9 分）、wshobson/agents
（MIT, 12 分）三个可合入上游满足判据第 2 条。

另外两个「许可通过但内容不值得合入」的**内容裁决**：Besty0728/Unity-Skills（MIT, 1735★，
但 SKILL.md 是其自家 Editor 包的工具说明书，属产品包装类）与 Mindrally/skills `unity`
（Apache-2.0, 260★，62 行 Cursor rule 转写，无一条带版本门或后果）。frederico-kluser 的
API `NOASSERTION` 实读为 MIT——又一例不能只信 `spdx_id`。

### 声明源优于散文源

本 skill 的 `[verified]` 全部来自逐版本 `git show <branch>:<path>` 读 `UnityCsReference`
的 C# 声明，这个手法推翻了三条散文结论：

1. gamedev-skills 的「`Rigidbody.velocity` doesn't exist in Unity 6.3 LTS」——实际带
   `[Obsolete(... (UnityUpgradable) -> linearVelocity)]`，是警告 + 自动改写。
2. 社区普遍的「`FindObjectsByType<T>(FindObjectsSortMode.None)` 是最优形」——6.4 起该重载
   本身 `[Obsolete]`。分界通过 `6000.3` 干净、`6000.4` 已废弃逐分支二分确定。
3. 本 skill 初稿的「`[SerializeField]` 放在自动属性上静默无效」——`SerializeField` 声明为
   `[AttributeUsage(AttributeTargets.Field)]`，实为 `CS0592` 编译失败。**这一条是基线评测
   的答案纠正了我的初稿**，随后用声明源确认，再改写 Core rule 1 与 `unity-serialization.md`。

### 未验证清单（本机无 Unity Editor，全部标 `[official]`）

本机没有也装不上 Unity Editor（Unity Hub 不提供无账号的无头安装，且 Editor 本体需要许可
激活）。因此**没有任何事实来自本机运行 Unity**。以下全部标 `[official]`，出处已列：

1. 碰撞 / 触发器消息矩阵（六种 collider 类型两两组合）——`Manual/collider-types-interaction.html`。
2. SRP Batcher 的行为语义（降的是 render-state 切换、按 shader variant 合批）与兼容条件
   （`UnityPerDraw` / `UnityPerMaterial` CBUFFER、不得用 MPB、非 particle）——
   `Manual/SRPBatcher.html`、`Manual/SRPBatcher-Materials.html`。
3. GPU Resident Drawer 的全部前置与逐渲染器排除项——`Manual/urp/gpu-resident-drawer.html`。
4. Built-in 管线 shader 在 URP 下渲染洋红、无运行时回退。
5. UI 系统官方推荐表（运行时 uGUI / Editor UI Toolkit）与差异项（无 in-scene authoring、
   无 serialized events）——`Manual/UI-system-compare.html`，6.3 与 6.6 两版对照。
6. Unity 序列化规则（字段条件、支持类型列表、`[Serializable]` 不继承、`[SerializeReference]`
   的四种能力、`[MakeSerializable]`、属性不序列化）——`Manual/script-serialization-rules.html`，
   6.3 与 6.6 两版对照确定 `Dictionary` 分界。
7. Editor 命令行参数语义（`-batchmode` 异常退 1、`-executeMethod` 要求 `Editor` 文件夹与
   自设退出码、`-quit` 会隐藏错误消息且与异步代码冲突、`-logFile -`、`-nographics` 关日志
   且不能烤 GI、`-accept-apiupdate`、`-serial` 必须配 `-batchmode`）——
   `Manual/EditorCommandLineArguments.html`。
8. Unity Test Framework 命令行参数（`-testPlatform` 取值、`-quit` 在跑测试时不受支持、
   无统一退出码契约须解析 NUnit XML、`-playerHeartbeatTimeout` 默认 10 分钟、
   `-runSynchronously` 仅 EditMode 且过滤 `[UnityTest]`）——`com.unity.test-framework@1.5`。
9. 构建期行为：托管剥离与 `link.xml`、IL2CPP 需平台 C++ 工具链、Addressables 内容独立构建、
   Addressables 资产跨组重复打包、贴图/音频导入设置的运行时含义、`Resources/` 全量入包。
10. 所有性能数量级描述（贴图 ≫ 网格 > 音频 > shader variant > 托管堆、Boehm GC 非分代
    非压缩、Incremental GC 摊平而不减少分配）——官方文档与上游一致陈述，本机无法复现。
11. DOTS 的行为断言（`ISystem` 优于 `SystemBase`、结构性变更须走 ECB、Burst 失败静默回退、
    chunk 利用率随 archetype 分裂下降、Entities Graphics 与 GameObject 互不渲染）——
    交叉校验 wshobson + `Unity-Technologies/EntityComponentSystemSamples`（reference）。

可机器核对、已实测的部分（标 `[verified]`）：`UnityCsReference` 的 `[Obsolete]` 文本与版本
分界、`SerializeField`/`SerializeReference` 的 `AttributeUsage`、`Awaitable` 的一次性与
无同步上下文约束（源码注释）、`destroyCancellationToken` 的 `MissingReferenceException`
分支、`UxmlFactory`/`UxmlTraits` 的 `[Obsolete]`、`Rigidbody`/`Physics` 重命名、
`RaycastCommand.ScheduleBatch` 签名、`BuildReport`/`BuildStep`/`BuildStepMessage`/
`BuildSummary` 的成员、`BuildOptions.StrictMode`、`NamedBuildTarget.Android` 与
`SwitchActiveBuildTarget(NamedBuildTarget, BuildTarget)` 重载。

### 未达成项

- **没有一行 C# 经过 Unity 编译器**，`references/unity-build.md` 的 `BuildScript` 与
  `unity-dots.md` 的系统示例都只做到「每个 API 成员在 `UnityCsReference@6000.3` 里存在且
  签名匹配」这一级。`scripts/` 因此故意不写：本仓库要求脚本在本机跑通，而任何有价值的
  Unity 脚本都需要 Editor。
- URP 的散文文档已迁出 `Unity-Technologies/Graphics`，所以 URP 事实只能取自
  docs.unity3d.com，无法用源码二次核对（只核对了 API 存在性）。
- Nice-Wolf-Studio 的推送时间是 2026-07-29（约 1.5 个月），是三个 merged 上游里最旧的；
  下次同步优先盯它，重点看它是否修正了 UI 系统推荐那条与官方相反的结论。
- `NOTICE.md` 由主代理的 `tools/build_catalog.py` 生成，本 skill 未自造；
  `validate_skills.py skills/unity` 目前只剩这一条 error、0 warning。

### 下次同步要盯的上游

- `UnityCsReference` 的 `6000.4`+ 分支：`FindObjectsSortMode` 一类的 `[Obsolete]` 还在往前
  推进（`instanceID` → `EntityId` 的迁移已经影响 `Physics` 的 contact API 与
  `Physics.BakeMesh`），这批会继续产生新的版本门。
- `Manual/script-serialization-rules.html`：`Dictionary` 在 6.6 落地后，`[MakeSerializable]`
  与 serialization rules analyzer 也是新增面，下一个 LTS（6.7）会把它们变成默认基线。
- Unity-Technologies/skills 的目录集合（只看目录名，不读正文）：新增目录意味着官方认为
  值得单独成篇的主题，是覆盖面漏洞的免费指示器。
