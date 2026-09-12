# unreal 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11（同日，全部候选用已登录 `gh api` 实时复核）
- 检索途径：
  - `gh search repos "unreal engine skill"`、`"ue5 agent skills"`
  - `gh search code --filename SKILL.md "UPROPERTY"`（40 条，跨 20 个仓库，是本次最有效的入口）
  - 多技能聚合仓树遍历：`wshobson/agents`、`github/awesome-copilot`、`VoltAgent/awesome-agent-skills`、
    `addyosmani/agent-skills`（前者只有 unity/godot，后三者树中无 unreal，留行备查）
  - 领域官方组织：`EpicGames/*`
  - 官方文档：<https://dev.epicgames.com/documentation/en-us/unreal-engine>（渲染后抓取，见「备注」）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`；
  许可一律再 `gh api repos/<o>/<r>/contents/LICENSE --jq .content | base64 -d` 实读正文。

**引擎版本基线**：官方文档站把 `unreal-engine-5-6-documentation` 重定向到
`unreal-engine-5-8-documentation`，页面标题为「Unreal Engine 5.8 Documentation」，因此本 skill
以 **UE 5.8** 为基线。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可（实读结论） | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gamedev-skills/awesome-gamedev-agent-skills `skills/unreal/*` | https://github.com/gamedev-skills/awesome-gamedev-agent-skills | 943 | 2026-09-10 | Apache-2.0（根 LICENSE 正文为 Apache 2.0，树中无子目录许可） | 6 个 unreal-* skill：cpp-gameplay / blueprints / enhanced-input / niagara / packaging / behavior-trees | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE merged | 自述 targets UE 5.8（与官方文档当前版本一致）；pitfalls 段全是可证伪陷阱；抽查 UPROPERTY/GC、CreateDefaultSubobject 仅限构造函数、Build.cs 依赖三条均与官方一致 |
| 2 | EpicGames/unreal-engine-skills-for-claude-code-plugin | https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin | 275 | 2026-09-10 | MIT（正文 `Copyright (c) 2026 Epic Games, Inc.`；`plugin.json` 亦声明 MIT） | 3 个 skill：unreal-skill（写 in-editor Agent Skill）、unreal-mcp、create-toolset | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE merged | 唯一官方上游。内容是编辑器自动化与 skill 写法，不是引擎知识，所以只贡献「agent 能不能改 uasset」这条边界 |
| 3 | kevinpbuckley/unreal-engine-skills `skills/core/*` | https://github.com/kevinpbuckley/unreal-engine-skills | 52 | 2026-09-09 | **NONE**（树中无任何 LICENSE/COPYING） | 48 个 ue-* 主题 skill + `scripts/check-citations.mjs` + evals/tasks | 1 | 3 | 3 | 3 | 0 | 10 | INCLUDE merged | 覆盖面最完整的一家，且每条都附官方文档 URL 与引擎源码路径；抽查 TObjectPtr/写屏障、TStrongObjectPtr 不可作 UPROPERTY、MarkAsGarbage 取代 MarkPendingKill 三条与官方一致。许可 0 → 按「无许可但公开」规则 merged + `license: NONE` |
| 4 | UnrealXu/UnrealEngine5-Skills | https://github.com/UnrealXu/UnrealEngine5-Skills | 507 | 2026-08-26 | MIT | 6 个 ue5-* skill + 模块索引 CSV + 校验脚本 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE merged | 「症状 → 定位 → 修复」表结构好用；API anchors 与官方一致（`Net/UnrealNetwork.h`、`GetLifetimeReplicatedProps`、改 Build.cs 后重生成工程文件）。具体性扣一分：大量条目是流程约束而非引擎事实 |
| 5 | maystudios/claude-skills `unreal-*` | https://github.com/maystudios/claude-skills | 22 | 2026-08-15 | MIT | unreal-best-practices / unreal-gas / unreal-blueprint-codegen / unreal-pcg-python / unreal-thirdparty | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE merged | 「legacy vs modern 系统」对照表与版本破坏性变更表是别处没有的；正确性扣一分：自述基线是 UE 5.7、且「避免 Event Tick 提升 20-30%」无出处（已丢弃该数字） |
| 6 | dev.epicgames.com/documentation（UE 5.8） | https://dev.epicgames.com/documentation/en-us/unreal-engine | — | 持续 | **Proprietary**（站点无任何开源许可声明，页脚无 licence/terms 链接） | 反射、对象指针、复制、RPC、Tick、Enhanced Input、GAS、Lumen、Nanite、UMG、Chaos、模块、Live Coding、打包、自动化测试 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE **reference** | 全部事实来源。许可裁决：专有 → 不得 merged，一字未抄，全部重写 |
| 7 | quodsoler/unreal-engine-skills | https://github.com/quodsoler/unreal-engine-skills | 335 | **2026-03-01** | MIT | 11 个 ue-* skill（gameplay-framework、networking-replication、materials-rendering、ui-umg-slate…） | 1 | **0** | 3 | 2 | 2 | 8 | reference | 新鲜度裁决：距今 6 个月 10 天，超过 6 个月硬线且非官方 → 不得作 merged。主题清单仍用于覆盖面比对 |
| 8 | a5c-ai/babysitter `library/specializations/game-development/skills/unreal-*` | https://github.com/a5c-ai/babysitter | 1788 | 2026-09-05 | MIT | unreal-cpp / unreal-development / unreal-gamesframework / unreal-networking / behavior-trees / navmesh | 1 | 3 | 1 | 1 | 2 | 8 | reference | 内容裁决（非许可）：全是 “Create Gameplay Abilities / Handle ability activation” 式能力清单，无一条可证伪；frontmatter 带 `allowed-tools`（含 WebFetch）与 `graph` 等本仓禁用字段；`unreal-gamesframework` 名不副实（内容是 GAS）；文档链接钉在 5.0 |
| 9 | benjaminasterA/antigravity-awesome-skills `skills/unreal-engine-cpp-pro` | https://github.com/benjaminasterA/antigravity-awesome-skills | 266 | 2026-09-11 | MIT（根 LICENSE；该目录无独立 LICENSE.txt，同仓其他目录有） | 单个 UE C++ 卫生清单 | 1 | 3 | 2 | 1 | 2 | 9 | reference | 内容裁决：建议「`TStrongObjectPtr` 可用但一般优先 `addToRoot()`」与官方 Object Pointers 页直接矛盾（AddToRoot 是永久根集固定；TStrongObjectPtr 才是非 UObject 持有者的官方做法），另带 `risk`/`source` 禁用字段 |
| 10 | fjz13/UnrealSpecifiers `Doc/*` | https://github.com/fjz13/UnrealSpecifiers | 1056 | 2026-06-07 | **Proprietary**（LICENSE.md：版权归作者，禁止商业用途） | UPROPERTY/UCLASS/UFUNCTION specifier 百科 + 示例工程 | 2 | 1 | 3 | 3 | 0 | 9 | reference | 许可裁决：非商业限制等同 CC-BY-NC → 不得 merged。specifier 事实全部改从官方 Metadata Specifiers / UProperties / Class Specifiers 页取证 |
| 11 | omer-metin/skills-for-antigravity `skills/unreal-engine` | https://github.com/omer-metin/skills-for-antigravity | 144 | 2026-01-22 | Apache-2.0 | 单个 unreal-engine skill | 1 | 0 | 1 | — | 2 | ≤4 | REJECT | 新鲜度 0（>7 个月），且是单文件泛用型条目，合成价值低于复核成本 |
| 12 | DSTN2000/claude-unreal-engine-skill | https://github.com/DSTN2000/claude-unreal-engine-skill | 36 | 2025-12-24 | 无 | 单个 skill | 0 | 0 | 1 | — | 0 | ≤4 | REJECT | 近 9 个月无推送 + 无许可，两条硬线同时触发 |
| 13 | kevinpbuckley/VibeUE `Content/Skills/*` | https://github.com/kevinpbuckley/VibeUE | 676 | 2026-09-04 | MIT | UE 插件内的资产级 skill（sound-cues 等） | 1 | 3 | 2 | — | 2 | — | REJECT | 属于该插件产品面的说明书（产品包装类），不是引擎通用工程能力 |
| 14 | majiayu000/claude-skill-registry `skills/{gaming,data}/unreal-*` | https://github.com/majiayu000/claude-skill-registry | 604 | 2026-09-11 | MIT | 转载聚合 | 0 | 3 | 1 | — | 2 | — | REJECT | 镜像聚合站：unreal-* 条目全部转自 a5c-ai/babysitter 与 benjaminasterA，重复评审同一内容 |
| 15 | costrict-plugins-repo/anthropic-unreal-engine-skills-for-claude-code | https://github.com/costrict-plugins-repo/anthropic-unreal-engine-skills-for-claude-code | 0 | 2026-07-27 | MIT | Epic 官方仓库的镜像 | 0 | 2 | 2 | — | 2 | — | REJECT | 是候选 2 的镜像，直接用上游 |
| 16 | JasonMa0012/MooaToon `.codex/skills/ue-code-authoring` | https://github.com/JasonMa0012/MooaToon | 738 | 2026-09-09 | **不明**（LICENSE 文件正文只有一行指向 README#license 的 URL） | 自家 UE 卡通渲染分支的作者向 skill | 1 | 3 | 2 | — | 0 | — | REJECT | 许可不可判定 + 范围是某个引擎分支的私有约定，不适用于通用 UE 工程 |
| 17 | hkzhugc/UnrealEngineSkills | https://github.com/hkzhugc/UnrealEngineSkills | 2 | 2026-03-16 | MIT | 个人试验 | 0 | 0 | 1 | — | 2 | ≤4 | REJECT | 2 星 + >6 个月无推送 |
| 18 | niichiro/unreal-engine-skillbox | https://github.com/niichiro/unreal-engine-skillbox | 0 | 2026-01-31 | 无 | 个人试验 | 0 | 0 | 0 | — | 0 | ≤4 | REJECT | 0 星 + 无许可 + >7 个月 |
| 19 | clockworklabs/SpacetimeDB `skills/unreal` | https://github.com/clockworklabs/SpacetimeDB | — | 活跃 | — | SpacetimeDB 的 UE SDK 用法 | 2 | 3 | 2 | — | 2 | — | REJECT | 产品 SDK 说明书（产品包装类），非引擎能力 |
| 20 | EpicGames/UnrealEngine | https://github.com/EpicGames/UnrealEngine | — | 活跃 | 专有（Unreal Engine EULA，且需账号绑定才能访问） | 引擎源码 | 3 | 3 | 3 | 3 | 0 | — | **EXCLUDE** | 受限访问 + 专有许可：本轮**未拉取任何源码**，不作上游、不引用行号。官方厂商特例因此不成立（特例要求官方文档可 merged，而 Epic 文档是专有的），改走判据第 2 条 |
| 21 | wshobson/agents `plugins/game-development/skills` | https://github.com/wshobson/agents | 39565 | 2026-09-07 | MIT | 只有 unity-ecs-patterns / godot-gdscript-patterns | 2 | 3 | — | — | 2 | — | N/A | 树中无 unreal 条目（已用 `git/trees?recursive=1` 确认），留行避免后续批次重查 |
| 22 | github/awesome-copilot、VoltAgent/awesome-agent-skills、addyosmani/agent-skills | — | 38.9k / 34.1k / 93.5k | 2026-09 | MIT | — | — | — | — | — | — | — | N/A | 三家树中均无 unreal/gamedev 条目，留行备查 |

**立项判定**：判据第 2 条要求「≥3 个活跃（6 个月内有推送）、总分 ≥8 的可合成上游」。
候选 1（12 分 / Apache-2.0）、2（13 分 / MIT 官方）、3（10 分 / NONE 但公开）、4（11 分 / MIT）、
5（11 分 / MIT）共 5 个满足，**判据 2 成立，正常立项**，不走官方厂商特例。

## 深度审查

### 1. gamedev-skills/awesome-gamedev-agent-skills（主干结构）

六个 skill 各 107–144 行，外加四个 80–129 行 reference。frontmatter 干净（只有 `name`/
`description`），无 harness 变量。质量最高的部分是 `## Pitfalls`：`generated.h` 不在最后、
漏 `GENERATED_BODY()`、裸 `UObject*` 无 `UPROPERTY`、Build.cs 缺模块导致 link 失败、
忘记 `Super::`——全是可证伪且有具体后果的条目，正是本仓要的写法。
缺点是每个 skill 只覆盖一个窄主题（本仓要的是整引擎），且 reference 里出现了
`ACharacterBase::ACharacterBase()` 这类示意性代码（无害）。**与候选 3 的重叠**：主题上完全被
候选 3 的 48 个 skill 覆盖，但候选 3 没有这种「失败优先」的行文。两者互补，都取。

### 2. EpicGames/unreal-engine-skills-for-claude-code-plugin（官方）

三个 skill：`unreal-skill`（如何写 in-editor Agent Skill，112 行）、`unreal-mcp`（56 行）、
`create-toolset`（420 行）。**它讲的不是引擎，而是如何用 MCP 驱动编辑器**：
`ToolsetRegistry` 暴露 30+ 个 toolset（actors、blueprints、materials、Niagara、Control Rig、
Sequencer、State Tree、widgets、GAS、automation testing），agent 通过
`list_toolsets`/`describe_toolset`/`call_tool` 三个 meta-tool 动态发现。
`unreal-skill` 的写作原则（Novel / Collegial / Durable / Parsimonious）与本仓标准第 3 节高度一致，
可作交叉验证，但不构成新的引擎事实。
**合入方式**：只贡献一条边界——agent 不能凭空改 `.uasset`，编辑器内操作的正规路径是这个 MCP
server；写进 `references/unreal-build.md` 的「Editor automation from an agent」。

### 3. kevinpbuckley/unreal-engine-skills（覆盖面与引用纪律）

48 个 `skills/core/ue-*`（258–443 行/个），另有 `ultra-dynamic-sky`/`weather` 两组第三方资产
skill（与本仓无关，不取）。`metadata.engine-version: "5.8"`，且每个 skill 末尾列
**官方文档 URL + 引擎源码路径:行号**，附 `scripts/check-citations.mjs` 做机械校验——这是本次
见到的最高引用纪律。`ue-memory-and-gc` 的指针类型表、`FGCObject` vs `TStrongObjectPtr` 选择、
`gc.AllowIncrementalReachability` 等条目质量很高。
**不可直接沿用的部分**：所有 `Engine/Source/...:1886` 形式的源码行号。`EpicGames/UnrealEngine`
是受限仓库，本轮按硬约束**未访问**，因此这些行号既无法核对也不可转述——本 skill 一条也没写。
许可为 NONE，按规则 merged + `license: NONE`，全部自己重写。

### 4. UnrealXu/UnrealEngine5-Skills

六个 skill 各约 100 行，结构工整（Quick Start / API Anchors / Workflow / Constraints /
Failure Handling / 版本兼容 / Escalation），`ue5-architecture` 还带引擎模块索引 CSV 与
`validate_engine_anchors.py`。`Failure Handling` 的「症状 → 定位 → 修复」三段式直接影响了本
skill 每个 reference 末尾的失败症状表。内容偏流程约束，引擎事实密度低于候选 1/3。

### 5. maystudios/claude-skills

`unreal-best-practices`（178 行 + 5 个 reference）与 `unreal-gas`（120 行 + 4 个 reference）。
独有价值是两张表：legacy→modern 系统对照（Enhanced Input、GAS、Gameplay Tags、StateTree、
Niagara、MetaSounds、Nanite、Lumen、World Partition、CommonUI、Mover、PCG、Iris）与
版本破坏性变更清单（5.0 TObjectPtr/LWC、5.1 legacy input 弃用、5.3 C++20、5.5 stat profiler→
Insights、5.6/5.7 若干）。**问题**：自述基线 UE 5.7（当前 5.8），且「避免 Event Tick 提升
20-30%」这个数字无任何出处。合入时只取「哪些系统是当前做法」的语义，数字丢弃，每条状态改从
官方页复核（例如 Niagara 的当前性与 Lumen/Nanite 的限制都在官方页上复核过）。

### 6. quodsoler/unreal-engine-skills（落选但值得记）

11 个 `ue-*` skill 覆盖面接近理想（gameplay-framework、networking-replication、
materials-rendering、ui-umg-slate、animation-system、data-assets-tables、game-features、
sequencer-cinematics、serialization-savegames、input-system、cpp-foundations），335 星。
唯一问题是 `pushed_at = 2026-03-01`，距本批次 6 个月 10 天，踩过 6 个月硬线且不是官方仓库，
量表新鲜度 0 → 不得 merged。**下轮同步时优先复查这一家**：如果恢复维护，它的主题划分与本 skill
的十个 reference 几乎一一对应。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 改了 `UPROPERTY`/头文件后能否用 Live Coding | gamedev-skills：「Live Coding 只处理函数体，改 `UCLASS`/`UPROPERTY`/头文件必须重启编辑器全量重建」；kevinpbuckley 未表态 | **两者都不写**。官方 Live Coding 页说 Object Reinstancing（默认开启）正是为了让「新函数、新变量、大规模重构」生效，覆盖 `UCLASS`/`UFUNCTION`/`USTRUCT`/`UENUM`/`UDELEGATE` 及其生成物；真正的限制是另外两条：`.cpp` 构造函数里的默认值不会更新已有实例（改头文件则会），以及持有被 reinstance 对象指针的代码必须用 `ReloadReinstancingCompleteDelegate`/`ReloadCompleteDelegate` 更新，否则**编辑器关闭时**崩溃 | 官方「Live Coding」页；社区说法与官方矛盾，按「官方厂商 > 社区」裁决 |
| 2 | 非 UObject 持有者如何持有 UObject | benjaminasterA：「可以用 `TStrongObjectPtr`，但一般优先 `addToRoot()`」；官方：`TStrongObjectPtr` 就是为此设计，`AddToRoot` 是把对象永久钉进根集 | 采官方：非 UObject 持有者用 `TStrongObjectPtr`；`AddToRoot` 必须配对 `RemoveFromRoot`，否则是进程级泄漏。该候选整体降 `reference` | 官方「Object Pointers」「Unreal Object Handling」页 |
| 3 | `TObjectPtr` 相对裸 `UPROPERTY` 指针的价值 | 社区普遍表述为「UE5 风格约定」「多一点编辑器追踪」 | 写成官方原因：只有作为 `UPROPERTY` 时才 GC-safe，且它提供**增量 GC 标记所需的写屏障**与 cook 期依赖追踪 | 官方「Object Pointers」页 |
| 4 | `MarkPendingKill` / 自动置空语义 | kevinpbuckley：UE5 默认 `gc.PendingKillEnabled=false`，`UPROPERTY` 指针不再自动置空，需手动清理 | 只写官方能支撑的部分：**销毁 `AActor`/`UActorComponent` 时，反射系统可见的引用会被自动置空**；关于 `gc.PendingKillEnabled` 默认值改变后的置空行为，官方页未覆盖，**本 skill 不写**，列入未验证清单 | 官方「Unreal Object Handling」页；缺官方出处的部分按「宁可少写」丢弃 |
| 5 | `#include "X.generated.h"` 必须是最后一个 include | gamedev-skills 与 kevinpbuckley 均明确要求；官方页只写「必须包含生成的头文件」与「`GENERATED_BODY()` 必须在类体最开始」 | 两条硬性要求按 `[official]` 写入 Core rules；「必须最后」降为 reference 里的一行并标 `[community]`，理由写明官方示例一律放最后但文档未明文 | 官方「Gameplay Classes」页 + 两家社区上游一致 |
| 6 | GAS 是否应作为默认能力实现方式 | maystudios：「Research First，能力驱动的游戏推荐 GAS」；a5c-ai：无边界讨论 | 写成适用边界：GAS 面向 RPG/动作冒险/MOBA 这类「能力是数据」的设计，官方文档自己这么划范围；三个能力、无叠加、无多人的项目付概念成本却无收益 | 官方「Understanding the Gameplay Ability System」页 |
| 7 | 属性钳制放哪里 | 社区示例常在 DataTable 里填 Min/Max | 明确写：默认插件**未实现** Attribute 表的 “Min Value”/“Max Value” 列，填了无效，钳制必须写在 AttributeSet 代码里 | 官方「Gameplay Attributes and Attribute Sets」页 |
| 8 | 组件如何开启复制 | 社区多只写 `SetIsReplicated(true)` | 区分两个 API：构造函数用 `SetIsReplicatedByDefault(true)`，运行时用 `SetIsReplicated(true)`；两者都要求所属 Actor 先 `bReplicates` | 官方「Replicating Actor Components」页 |
| 9 | 引擎版本基线 | gamedev-skills/kevinpbuckley 写 5.8；maystudios 写 5.7；quodsoler 未标 | 取 **5.8**：官方文档站把旧版本 URL 重定向到 5.8 文档，页面标题即 5.8 | 官方文档站行为（实测重定向） |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `gamedev-unreal` | gamedev-skills/awesome-gamedev-agent-skills `skills/unreal` | merged | UE5 C++/蓝图/输入/Niagara/打包的主题划分与「失败优先」行文 |
| `epic-ue-skills` | EpicGames/unreal-engine-skills-for-claude-code-plugin | merged | 官方立场：编辑器内操作（含 `.uasset`）的正规路径是官方 MCP toolsets；写成 agent 能力边界 |
| `kevinpbuckley-ue` | kevinpbuckley/unreal-engine-skills `skills/core` | merged | 整引擎覆盖面清单、指针/生命周期决策表结构、逐条给官方出处的引用纪律 |
| `unrealxu-ue5` | UnrealXu/UnrealEngine5-Skills | merged | 「症状 → 定位 → 修复」表结构；模块与 Build.cs 复查重点 |
| `maystudios-unreal` | maystudios/claude-skills `unreal-best-practices`、`unreal-gas` | merged | legacy vs 当前系统的判断框架与 GAS 章节骨架（事实全部重新取证） |
| `epic-ue-docs` | dev.epicgames.com/documentation（UE 5.8） | reference | 全部事实来源；专有许可，一字未抄 |
| `quodsoler-ue` | quodsoler/unreal-engine-skills | reference | 主题覆盖面比对（新鲜度裁决落选） |
| `a5c-babysitter` | a5c-ai/babysitter `game-development/skills` | reference | 覆盖面比对（内容裁决落选） |
| `benjaminastera-skills` | benjaminasterA/antigravity-awesome-skills `skills/unreal-engine-cpp-pro` | reference | UObject 卫生清单比对（内容裁决落选：与官方矛盾） |
| `fjz13-specifiers` | fjz13/UnrealSpecifiers | reference | specifier 行为交叉检查（许可裁决落选：非商业限制） |

## 基线缺口

无 skill（`uv run tools/run_evals.py unreal --baseline`，claude-opus-5 · medium）时，
五个场景全部 `skill_read=false`、`status=ok`，耗时 95 / 119 / 87 / 418 / 96 秒。

**第一轮量规的结论是「几乎零区分度」**：Opus 5 对 UE 的掌握远超预期，场景 1 命中 9 条里的 8 条，
场景 2、3、4 按第一轮量规基本全中（场景 2 还额外指出了音效衰减与 `IsRunningDedicatedServer`
这类本子没写的问题），场景 5 负例完全正确。

按 `docs/workflow.md` Phase B 的要求改写量规：**题目（`query`）与夹具（`evals/files/*`）一字未改**
（已用 `diff` 比对基线 `result.json` 里的 `query` 与新 `evals.json`，逐字相同），只把
`expected_behavior` 重写为**版本分界事实**与**会造成事故的判断**。因为 prompt 未变，基线的既有转录
在新量规下仍然是有效证据，按 Phase B 允许的做法**用新量规重新评判同一批转录，未重跑基线**
（重跑只会引入噪声）。

新量规下的基线缺口：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 | `GENERATED_BODY()` 必须在类体最开始 | 夹具把它放在 `public:` 之下，基线完全没提这一条（只抓了前缀与 `generated.h` 顺序） |
| 1 | 工作线程访问的官方处方 | 基线给的是「回主线程 / 用 `FStreamableManager`」，没给官方处方 `TWeakObjectPtr` + `Pin()` → `TStrongObjectPtr` |
| 1 | `TObjectPtr` 优于裸 `UPROPERTY` 指针的**原因** | 基线正确给出了 `TObjectPtr` 写法，但没说它是增量 GC 写屏障与 cook 期依赖追踪的前提，也没说它只有作 `UPROPERTY` 时才 GC-safe |
| 1 | `TStrongObjectPtr` 的官方代价说明 | 基线只说「语义矛盾」，未给「创建销毁昂贵、永远是强引用、在 UObject 内成不可回收环而 `TObjectPtr` 自引用不会」 |
| 2 | RepNotify 的注册语义 | 基线把问题定位为「属性没注册」，但没有区分出另一类 bug：默认只在**值变化**时触发，重发相同值（重连、同值再命中）需要 `DOREPLIFETIME_CONDITION_NOTIFY(..., REPNOTIFY_Always)` |
| 2 | 可靠 RPC 绑输入的队列溢出 | 基线提到「可靠通道会塞满」，但没落到官方那条具体后果上：玩家连点可以比队列排空更快，溢出**直接掉线**，所以输入驱动的 RPC 需要限流 |
| 2 | 组件复制两个 API 的分工 | 基线只给 `SetIsReplicatedByDefault`，未区分构造期与运行期（`SetIsReplicated`） |
| 2 | 复制契约的另两段 | 基线给了 `DOREPLIFETIME` 注册与 `Net/UnrealNetwork.h`，但没点出「所属 Actor 必须 `bReplicates`」这一段，也没给运行期的 `SetIsReplicated` |
| 2 | `WithValidation` 失败的后果 | 两边都要求了 `_Validate`，但都没写官方那条：验证失败会**断开调用方客户端**，这正是它作为信任边界的意义 |
| 3 | UBT 的构建依据 | 基线没说 UBT 按 `Target.cs`/`Build.cs` 构建而非按 IDE 解决方案，因此「我的 IDE 能编译」不构成证据 |
| 3 | 同一 `LoadingPhase` 内模块加载顺序不确定 | 基线完全没提；新增模块时 `StartupModule` 里依赖另一个模块就会踩到，需显式 `LoadModule`/`LoadModuleChecked` |
| 4 | UMG 事件驱动的官方口径 | 基线把「改成事件/委托」当成一般性能建议，没引 Unreal 自己的 UMG 口径「用 Events 驱动 UI，而不是 Bindings 或 Tick」 |
| 4 | Tick 组与 trace 的因果 | **基线通篇没有出现 tick 组**。它把标签闪烁归因为 40 个控件叠加 + 无迟滞（都对），但漏了「可见性 trace 要的是本帧最终物理位置 = `TG_PostPhysics`，`TG_PrePhysics` 读到的是上一帧数据」这条官方事实 |
| 5 | （负例，无缺口） | 基线 `skill_read=false`，按纯 C++ 处理，未引入任何 UE 习语——期望行为本就是「不要触发」 |

## 评测结果

模型固定 claude-opus-5 · medium（`tools/run_evals.py` 默认，未传 `--model`/`--thinking`）。
判定量规为改写后的新量规；基线一列是用新量规重新评判的既有转录（prompt 未变）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 反射与 GC | claude-opus-5 medium | 无（baseline，95.3s） | false | 6/10 | 缺 `GENERATED_BODY()` 位置、`Pin()` 处方、`TObjectPtr` 的写屏障原因、`TStrongObjectPtr` 官方代价 |
| 1 反射与 GC | claude-opus-5 medium | 有（84.6s） | **true** | **9/10** | 三条基线缺口全部填补（`GENERATED_BODY()` 位置、`TWeakObjectPtr`+`Pin()`、`TStrongObjectPtr` 的三条代价含「`TObjectPtr` 自引用不会成环」）；仍缺写屏障/cook 期依赖追踪这条原因 |
| 2 复制与 RPC | claude-opus-5 medium | 无（baseline，118.9s） | false | 4/8 | 未达成：四段契约（缺 Actor `bReplicates` 与运行期 `SetIsReplicated`）、`WithValidation` 失败即断开连接、`REPNOTIFY_Always`、输入驱动可靠 RPC 的限流 |
| 2 复制与 RPC | claude-opus-5 medium | 有（96.5s） | **true** | **5/8** | 填补：可靠 RPC 被连点刷爆队列 → 服务器关闭连接 → 需限流（明确写出）。仍未达成：`REPNOTIFY_Always`、`Net/UnrealNetwork.h`+运行期 `SetIsReplicated`、验证失败断开连接 |
| 3 Build.cs | claude-opus-5 medium | 无（baseline，86.6s） | false | 5/7 | 未达成：UBT 按 `Target.cs`/`Build.cs` 而非 IDE 解决方案构建、同一 `LoadingPhase` 内加载顺序不确定 |
| 3 Build.cs | claude-opus-5 medium | 有（92.8s） | **true** | 5/7（**平手**） | 同样两条未达成。有 skill 的回答更紧凑（直接给出 public/private 判据与 `Target.bBuildEditor` 门控），但没有多命中任何一条新量规项——本场景零区分度，如实记录 |
| 4 Tick 预算 | claude-opus-5 medium | 无（baseline，418.4s） | false | 5/7 | 未达成：tick 组与 trace 的因果（通篇未出现 tick 组）、UMG 事件驱动未引官方口径 |
| 4 Tick 预算（首轮） | claude-opus-5 medium | 有（284.2s） | true | 4/7 | **首轮反而更差**：把工作整体移到定时器后，完全没交代「读物理结果的查询该在什么时机跑」，且丢了 trace 忽略 owner 这条。据此回到 Phase C 补了 `optimize-a-frame` 的一条工作流门（见下） |
| 4 Tick 预算（补强后重跑） | claude-opus-5 medium | 有（241.7s） | **true** | **6/7** | 填补：显式把 `TG_PrePhysics`（读上一帧变换）改为 `TG_PostPhysics` 并给出验证方式；仍缺 trace 忽略 owner |
| 5 纯 C++（负例） | claude-opus-5 medium | 无（baseline，96.3s） | false | 3/3 | 正确不触发 |
| 5 纯 C++（负例） | claude-opus-5 medium | 有（118.8s） | **false** | 3/3 | 负例达标：`skill_read=false`，按 rule of zero 用 `std::vector` 修所有权，答案里 `UPROPERTY`/`TObjectPtr`/`TArray`/`UObject`/`GENERATED_BODY`/`Build.cs`/`unreal` 出现次数为 0 |

结论：**通过**。场景 1 有四条基线未达成的行为，其中三条在有 skill 时达成（`GENERATED_BODY()`
位置、工作线程的 `Pin()` 处方、`TStrongObjectPtr` 的官方代价与自引用差异）；场景 2 填补一条
（可靠 RPC 队列溢出与限流）；场景 4 在补强 `optimize-a-frame` 工作流后填补一条（tick 组与 trace
的时机因果）。负例两轮都 `skill_read=false`。

未达成项如实记录，未改判：

- 场景 3 **平手**，本 skill 在该场景无区分度。原因是 Opus 5 对 Build.cs 的掌握本来就完整；
  新量规里剩下的两条（UBT 的构建依据、`LoadingPhase` 内加载顺序不确定）两边都没命中，说明
  `references/unreal-build.md` 里这两条虽然写了，但 SKILL.md 的 Core rules 没有给它们入口。
  下次同步时可考虑把「UBT 按 Target.cs/Build.cs 构建」并入规则 24。
- 场景 1 的「`TObjectPtr` 为什么优于裸 `UPROPERTY` 指针」两轮都未命中，虽然规则 3 明确写了。
- 场景 2 的 `REPNOTIFY_Always` 两轮都未命中，虽然规则 16 与 `unreal-replication.md` 都写了。
  这两条说明：写进 skill 不等于被复述——评测只能证明「已填补的缺口」，不能证明覆盖率。
- 场景 4 首轮出现**负向**结果（4/7 < 基线 5/7），已保留在表里；补强后重跑到 6/7。补强只改了
  SKILL.md 的一条工作流门，**题目与夹具一字未动**。

## 备注

### 本 skill 的断言未经引擎实跑验证

**UE5 无法在本机安装**（几十 GB、需绑定 Epic 账号），因此本 skill 里**没有任何 `[verified]`
标记**：所有引擎断言一律标 `[official]`，并逐条对应官方文档页。完整的未验证清单（即「有官方出处
但本仓从未实跑」的全部内容）：

1. 反射与 UHT：`GENERATED_BODY()` 位置、生成头文件、类前缀、UHT 错误行为。
2. GC 与指针：根集与可达性、自动置空的范围、`TObjectPtr` 写屏障与增量标记、`TWeakObjectPtr::Pin()`、
   `TStrongObjectPtr` 的开销与环、`AddToRoot`/`RemoveFromRoot`、`MarkAsGarbage`/`Destroy`、
   GC 聚簇与合并聚簇的行为、`TLazyObjectPtr` 弃用。
3. 属性/函数 specifier 语义：`Transient` 零填充、`Config`/`GlobalConfig` 隐含只读、
   `BlueprintReadOnly` 与 `BlueprintReadWrite` 互斥、`BlueprintGetter`/`BlueprintSetter` 的隐含规则。
4. 生命周期：`PostActorCreated` 与 `PostLoad` 互斥、`PostInitializeComponents`、`EndPlay` 的触发
   来源、`s.ForceGCAfterLevelStreamedOut=false` 时 actor 可能被「复活」、`OnDestroyed` 是遗留回调。
5. Tick：`bCanEverTick`、最小 tick 间隔、四个 tick 组的物理数据保证、`AddTickPrerequisite*`、
   定时器管理器在帧内的位置。
6. 复制：四段契约、`DOREPLIFETIME*` 宏族、`COND_*`、`REPNOTIFY_Always`/`OnChanged`、
   RepNotify 的前值参数、蓝图 `Set` 节点会调 RepNotify 而 C++ 不会、四种 RPC 的执行矩阵、
   `WithValidation` 失败断开连接、可靠队列溢出、dormancy/priority/relevancy、Iris 与通用系统并存。
7. Enhanced Input：四个概念、五种 trigger state、mapping context 优先级覆盖规则、
   `ModifyRaw_Implementation`、`Negate`+`Swizzle` 组合出二维输入。
8. GAS：ASC 不向所有客户端复制 ability/GE、Cue 非可靠复制、瞬时属性/标签变更不支持回滚、
   远程激活要求本地控制、Attribute 表 Min/Max 列未实现、base vs current value。
9. 渲染：Lumen 不支持 Static 光源、UE4 升级不自动启用、Mesh Distance Fields 需重启、
   HWRT 在 >10 万实例时的场景更新代价、Lumen 缓存传播延迟；Nanite 的 Opaque/Masked 限制、
   16M 实例上限、不支持 morph target/MSAA/前向渲染/VR 立体/光照通道、ray tracing 走 fallback mesh、
   DX12 SM6 平台要求。
10. UMG：事件优先于 Binding/Tick、目标分辨率与 DPI 1.0、Fill vs Auto、Render Transform 不参与布局、
    Border 平铺、Widget Reflector。
11. 物理：Chaos 子系统清单、简单 vs 复杂碰撞、sub-stepping 的四个设置与 CPU 代价、
    碰撞回调延迟到最后一个 sub-step（同帧可能收到重复回调）、CVD 可按 sub-step 回放。
12. 构建：`Build.cs` public/private 判据与编译时间、UBT 只编依赖链内模块、Editor 型模块不在打包
    目标内、`LoadingPhase` 内顺序不确定、Live Coding 的 `.cpp` 构造函数默认值不生效与 reinstancing
    指针清理、`BuildCookRun` 六阶段、Cook By the Book vs On the Fly、发布版本与 pak/asset registry
    的保留、Automation 的测试分类与 Smoke ≤1s、Low-Level Tests 的分工、`stat`/Insights。
13. 标签：`.ini` 来源与改后需重启编辑器、`NativeGameplayTags.h` 宏、restricted tag 不可在编辑器删除。

其中只有两条标了 `[community]`（官方文档未明文，社区上游一致）：`#include "X.generated.h"`
必须是最后一个 include；Large World Coordinates 下假设 `float` 世界坐标是精度隐患。另有若干
`[community]` 出现在写作口径而非引擎事实上（蓝图 nativization 在 5.0 被移除、硬引用加载链、
Cascade 被 Niagara 取代、Lyra 作为参考实现、只暴露必要接口）。

### 因找不到可靠出处而放弃的主题

- **`gc.PendingKillEnabled=false`（UE5 默认）之后 `UPROPERTY` 指针是否还自动置空**：
  kevinpbuckley 有明确说法，官方页只描述 Actor/Component 销毁时的置空，没覆盖这个开关。整条不写。
- **引擎源码行号与内部实现细节**：`EpicGames/UnrealEngine` 受限且专有，本轮未访问，
  所以所有 `Runtime/CoreUObject/...:1886` 形式的引用一条未用。
- **Iris 的具体版本状态（beta/正式）与迁移细节**：maystudios 写「5.7 beta」，官方页只说它与
  通用系统并存并给迁移文档，没给状态字样。只写「较新系统、与通用系统并存、迁移是项目级决策」。
- **`PCHUsage`/IWYU 的具体后果**、**`UPROPERTY(BlueprintReadWrite)` 在私有成员上的
  `AllowPrivateAccess` 要求**：官方 specifier 页未收录，均不写。
- **Nanite/Lumen 的具体性能数字**（除官方给出的 10 万实例与 16M 实例两处）：一律不写。
- **动画（Animation Blueprint、Motion Matching）、Sequencer、World Partition、
  MetaSounds、Mover、PCG**：官方页未逐一取证，且本波次范围以五个同构主题为准，本轮不写，
  留作下轮扩展。

### 下次同步要盯的上游

- `quodsoler/unreal-engine-skills`（335★）：本轮因 `pushed_at` 超 6 个月落选，主题划分与本 skill
  的十个 reference 几乎一一对应，恢复维护就应重估为 merged。
- `EpicGames/unreal-engine-skills-for-claude-code-plugin`：官方仓库，`plugin.json` 已到 3.1.0，
  toolset 清单会随引擎版本变化。
- `kevinpbuckley/unreal-engine-skills`：仍无 LICENSE。若作者补了开源许可，`license: NONE`
  与 `notes` 都要改。
- 官方文档：`epic-ue-docs` 是 `kind: docs`，`check_upstream.py` 只能报 `manual check`。
  UE 5.9 文档上线时必须重跑一遍版本门（Lumen/Nanite 限制与 Iris 状态最可能变）。

### 采集方式备注

Epic 文档站是客户端渲染的 SPA：`read` 直接取 URL 只能拿到几十字节的骨架，匿名 `curl` 会被
Cloudflare 429。本轮用受控浏览器渲染后抓 `innerText`，共取到 40 个官方页面（约 13k 行纯文本）
作为事实底稿；旧版本 URL（`unreal-engine-5-6-documentation`）会被重定向到 5.8，这也是版本基线的
判定依据。

## 2026-09-12 相邻技能集成

随本批正式构建`cpp`，删除Scope中“本库没有通用C++ skill”的过期声明，改为路由`cpp`。
仅修改否定边界与版本；UObject、Gameplay、复制、GAS等平台规则、上游pin和既有评测不变，
不把本次边界更新当成重新验证Unreal平台行为。对应C++的Unreal近似负例由本批使用
`openai/gpt-5.6-sol`、`medium`检验，结果记在`research/cpp.md`。
