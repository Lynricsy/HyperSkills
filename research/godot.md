# godot 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：—
- 检索途径：
  - `gh search repos godot skill --limit 50`、`gh search repos gdscript agent skill`
  - `gh search code 'godot filename:SKILL.md'`
  - 领域官方组织仓库：`godotengine/godot`（引擎本体）、`godotengine/godot-docs`（官方文档源）
  - 路线图种子：gamedev-skills/awesome-gamedev-agent-skills、wshobson/agents、
    thedivergentai/GD-Agentic-Skills、docs.godotengine.org
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- 许可一律实读：`gh api repos/<o>/<r>/contents/LICENSE --jq .content | base64 -d`

### 立项判据核对（`docs/roadmap.md`「新增主题的判据」第 2 条）

走**常规通道**，不用官方厂商特例。活跃（6 个月内有推送）且总分 ≥8 的可合成上游有
**7 个**（远超下限 3）：`godotengine/godot`（14）、`godotengine/godot-docs`（14）、
awesome-gamedev 的 `skills/godot/*`（13）、`haxqer/godot-skill`（12）、
`wshobson/agents`（11）、`abagames/headless-godot-skill-kit`（10）、
`jame581/GodotPrompter`（10）。许可全部实读通过，全部可 `merged`。

本波条件最好的一个：引擎本体 MIT、官方文档 CC-BY-3.0，两者都可 merged，所以每条 API
声明都能对**机器可读的事实源**核对，而不是对散文核对。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | godotengine/godot `doc/classes/*.xml` + `modules/**`（@ `4.7.2-stable`） | https://github.com/godotengine/godot | 116958 | 2026-09-10 | MIT（实读 LICENSE.txt 全文 = Expat MIT） | 全部 API 的机器可读声明 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 一等事实源。`doc/classes/*.xml` 带 `deprecated=`/默认值/参数语义；`modules/multiplayer/scene_rpc_interface.cpp` 与 `editor/editor_node.cpp` 直接给出 RPC id 分配与新建项目写入的设置。推翻了三条散文结论（见「冲突与裁决」1/3/6） |
| 2 | godotengine/godot-docs `tutorials/{rendering,migrating,export,...}` | https://github.com/godotengine/godot-docs | 5716 | 2026-09-10 | CC-BY-3.0（API `NOASSERTION`；实读 `LICENSE.txt` = Creative Commons Attribution 3.0 Unported，无 NC / 无 ND） | 渲染器对比、迁移指南、导出 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 三后端特性对比表与 4.4→4.7 每版 breaking/behavior 变更表，是版本门的唯一权威来源。CC-BY 需署名，`notes` 已写 |
| 3 | gamedev-skills/awesome-gamedev-agent-skills `skills/godot/godot-nodes-scenes` | https://github.com/gamedev-skills/awesome-gamedev-agent-skills | 943 | 2026-09-10 | Apache-2.0（实读根 LICENSE；全树只有一个 LICENSE，无逐目录授权） | 场景树、实例化、autoload | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | `change_scene_to_file` 延迟语义、`instance()`→`instantiate()`、`%Unique` 的 rename-proof 论证都对 |
| 4 | 同上 `skills/godot/godot-gdscript` | 同上 | 943 | 2026-09-10 | Apache-2.0 | GDScript 2.0、生命周期、注解 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 整数除法、`_process` vs `_physics_process`、3.x→4.x 注解迁移准确 |
| 5 | 同上 `skills/godot/godot-signals-groups` | 同上 | 943 | 2026-09-10 | Apache-2.0 | signals、groups | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE | 结构与 `bind`/`CONNECT_ONE_SHOT`/`call_group` 静默忽略都对；「重复连接会多次触发」一条错，实测推翻（裁决 1） |
| 6 | 同上 `skills/godot/godot-physics` | 同上 | 943 | 2026-09-10 | Apache-2.0 | 物理体、层/掩码、射线 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | layer/mask 单向检测、`exclude` 要 `Array[RID]`、`force_raycast_update()` 都对 |
| 7 | 同上 `skills/godot/godot-ui-control` | 同上 | 943 | 2026-09-10 | Apache-2.0 | Control、Container、Theme | 1 | 3 | 3 | 1 | 2 | 10 | INCLUDE | 容器接管布局、`rect_*` 改名、`mouse_filter` 吞点击都对；`anchors_preset = …` 代码样例实测为静默空操作（裁决 3） |
| 8 | 同上 `skills/godot/godot-export` | 同上 | 943 | 2026-09-10 | Apache-2.0 | 导出预设、CLI、Web | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE | 预设名精确匹配、COOP/COEP、`--quit-after` 是帧数都对；「`res://` 写入会失败」一条不准确，实测是静默成功后读回旧值（裁决 6） |
| 9 | 同上 `skills/godot/godot-multiplayer` | 同上 | 943 | 2026-09-10 | Apache-2.0 | ENet、`@rpc`、权威、复制 | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE | 「所有 `@rpc` 方法被校验和覆盖」方向对但机制说反了，源码核对后改写（裁决 2） |
| 10 | 同上 `skills/godot/godot-csharp` | 同上 | 943 | 2026-09-10 | Apache-2.0 | C# 绑定差异 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | `partial`、`EventHandler` 后缀、struct 值语义、`double` delta 都对，正好是本 skill 只保留的「与 GDScript 的差异」部分 |
| 11 | 同上 `skills/godot/{godot-resources,godot-shaders,godot-3d-essentials,godot-animation,godot-audio,godot-tilemap,godot-2d-movement}` | 同上 | 943 | 2026-09-10 | Apache-2.0 | 其余 7 个主题 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE（部分） | `godot-resources` 供 `.tres`/`.res` 与 `local_to_scene` 骨架；`godot-2d-movement` 供 `move_and_slide` 约定。其余（shaders/animation/audio/tilemap/3D）只用其主题清单判断覆盖面，不进正文——超出本 skill 的五主题同构约定 |
| 12 | haxqer/godot-skill `skill/godot` | https://github.com/haxqer/godot-skill | 82 | 2026-08-24 | MIT（实读 LICENSE） | 4.7 实测的 headless 自动化 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 唯一自称「verified on Godot 4.7」且给出可核对断言的社区上游：`inference_on_variant` 默认为 error、`TileMap`→`TileMapLayer`（4.3+）、`parent="."` 的 `.tscn` 静默失败、4.7 新增 `Control.offset_transform_*`。三条抽查全部经本机或 XML 核实 |
| 13 | wshobson/agents `plugins/game-development/skills/godot-gdscript-patterns` | https://github.com/wshobson/agents | 39565 | 2026-09-07 | MIT（实读根 LICENSE，全树仅此一个 LICENSE） | GDScript 模式 | 2 | 3 | 2 | 2 | 2 | 11 | INCLUDE | 路线图种子。`@export_group`/`@export_range`/私有下划线约定与状态机骨架可用；正文偏教程，只取模式不取叙述 |
| 14 | abagames/headless-godot-skill-kit `.agents/skills/headless-godot` | https://github.com/abagames/headless-godot-skill-kit | 13 | 2026-04-26 | MIT（实读 LICENSE） | headless CLI / CI | 1 | 1 | 3 | 3 | 2 | 10 | INCLUDE | 全仓库唯一把 headless 当一等工作流的上游：强制 `--path`、日志落盘、沙箱里覆盖 `XDG_*`、禁止把 `.tscn` 当文本编辑。与本机实验结论一致 |
| 15 | jame581/GodotPrompter `skills/{godot-testing,godot-debugging,godot-ui,csharp-godot,...}` | https://github.com/jame581/GodotPrompter | 694 | 2026-08-12 | MIT（实读 LICENSE） | 30+ 主题 skill + 路由 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE（部分） | 「不给菜单路径/面板位置，因为那是最容易幻觉的部分」这条编辑边界值得抄。但全仓绑定自有 hook + `~/.godot-prompter/state/<sha256>.json`，属 agent 专属机制，必须剥离 |
| 16 | thedivergentai/GD-Agentic-Skills `skills/godot-*`（129 个） | https://github.com/thedivergentai/GD-Agentic-Skills | 689 | 2026-09-09 | **LGPL-3.0**（实读 LICENSE = GNU LGPL v3） | 4.7 never-list 百科 | 1 | 3 | 2 | 2 | 0 | 8 | INCLUDE **as reference** | **许可裁决**：LGPL → 按 `docs/roadmap.md` 只能 `reference`。只用其 129 个目录名判断覆盖面（确认本 skill 的七个 reference 覆盖了它的核心 sector）；每条事实改从 `doc/classes` 或官方文档取证。另有内容问题：人格化 persona（"Aurelius"）+ 95 条 never-list 分文件加载，形态与本仓库不兼容 |
| 17 | zimo-xiao-zheng/godot-ui-integration | https://github.com/zimo-xiao-zheng/godot-ui-integration | 110 | 2026-08-23 | MIT（实读 LICENSE） | UI 集成工作流 | 1 | 3 | 2 | 2 | 2 | 10 | INCLUDE（部分） | 「`.tscn` 是视觉事实源，运行时代码只填数据不搭布局」这条不变量进了 UI reference。其余内容强依赖 Godot MCP 与设计审批流程，属产品/流程包装，不取 |
| 18 | Randroids-Dojo/Godot-Claude-Skills `skills/godot` | https://github.com/Randroids-Dojo/Godot-Claude-Skills | 41 | 2026-01-19 | MIT（实读 LICENSE） | GdUnit4 / 部署 | 1 | 0 | 2 | 2 | 2 | 7 | MAYBE → 仅校验 | 推送 2026-01-19，距调研日 7.7 个月 > 6 个月，新鲜度 0。GdUnit4 的 `GdUnitCmdTool.gd --run-tests` 命令形状用于交叉校验测试一节；PlayGodot 依赖作者自己 fork 的 Godot，不取 |
| 19 | akira399/dsh-godot-skill `.dsh/skills/godot-4-development` | https://github.com/akira399/dsh-godot-skill | 23 | 2026-08-28 | MIT（实读 LICENSE） | 官方特性列表整理 | 1 | 3 | 1 | 2 | 2 | 9 | MAYBE → 仅校验 | 自述「整理自官方特性列表」，本质是文档目录的重排，属**生成式链接索引**；按「内容裁决」降为校验用途，只用来确认覆盖面没漏大块 |
| 20 | alexmeckes/godot-claude-skills `skills/godot-{code-gen,scene-design,shader,live-edit,interactive}` | https://github.com/alexmeckes/godot-claude-skills | 33 | 2026-03-24 | MIT（实读 LICENSE） | 编辑器实时编辑 | 1 | 1 | 1 | 1 | 2 | 6 | MAYBE → 不取 | 五个 skill 全部围绕作者自己的 live-edit 工具链，脱离该工具没有独立价值 |
| 21 | aigengame/godot-agent `.agents/skills/*` | https://github.com/aigengame/godot-agent | 39 | 2026-09-09 | MIT | agent 编排 | 1 | 3 | 1 | 1 | 2 | 8 | REJECT | 13 个 skill 里只有 `design-godot-modular-architecture` 与 Godot 相关，其余是 worktree/subagent/review 编排，属 `ai-engineering` 与 `skill-authoring` 范围 |
| 22 | godot-fun/godot-agent `.cursor/skills/*` | https://github.com/godot-fun/godot-agent | 151 | 2026-09-11 | MIT | 素材流水线 | 1 | 3 | 1 | 2 | 2 | 9 | REJECT | 539 个文件里 skill 全是 ffmpeg/图像处理（`audio-to-ogg`、`image-remove-background`、`storyboard-*`），是素材加工而非引擎工程；且带 `.cursor/` agent 专属布局 |
| 23 | majiayu000/claude-skill-registry `skills/{gaming,development,testing}/godot*` | https://github.com/majiayu000/claude-skill-registry | 604 | 2026-09-11 | MIT | 聚合 registry | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | 同一个 `godot` skill 在 `data/`、`development/`、`gaming/` 下重复登记三份，内容互相不一致；聚合器而非作者，无独立权威 |
| 24 | Kothulhu94/Claude-GDSkill | https://github.com/Kothulhu94/Claude-GDSkill | 45 | 2025-10-24 | **无许可**（API `license: null`，树中无 LICENSE） | GDScript 助手 | 0 | 0 | 1 | 1 | 0 | 2 | REJECT | 推送 2025-10-24，距调研日 10.6 个月，新鲜度 0 直接 REJECT；且无许可文件 |
| 25 | bgrenat/godot-game-dev-studio | https://github.com/bgrenat/godot-game-dev-studio | 13 | 2026-07-29 | LGPL-3.0 | 工作室编排 | 0 | 2 | 1 | 1 | 0 | 4 | REJECT | LGPL 且内容是多 agent 角色扮演编排，非引擎知识 |
| 26 | willnationsdev/godot-skills | https://github.com/willnationsdev/godot-skills | 44 | 2019-04-11 | MIT | — | 0 | 0 | 0 | 0 | 2 | 2 | REJECT | 名字撞车：这是 Godot 3.0 的技能/能力系统**游戏插件**，不是 agent skill。7 年未动 |
| 27 | Glade-tool/glade-mcp | https://github.com/Glade-tool/glade-mcp | 210 | 2026-09-02 | MIT | Godot MCP server | 1 | 3 | 2 | 2 | 2 | 10 | REJECT（范围） | 是一个 MCP server 产品而非 skill；怎么造 MCP server 归 `mcp-server`，怎么用某个 MCP 产品不立项（`docs/roadmap.md`「SaaS 产品包装类」） |
| 28 | docs.godotengine.org（渲染后端与导出章节网页版） | https://docs.godotengine.org/en/stable/ | — | 持续 | CC-BY-3.0 | 官方文档站 | 3 | 3 | 3 | 3 | 2 | 14 | 并入 #2 | 网页版就是 `godotengine/godot-docs` 的构建产物。已直接跟踪仓库（可 pin commit、可按 `paths` 检测变更），不再单列一个 `kind: docs` 条目 |

候选 28 行；活跃 + 总分 ≥8 且许可允许 merged 的有 7 个上游（第 1/2/3–11/12/13/14/15 组），
满足第 2 条的「至少 3 个」。

## 深度审查

### gamedev-skills/awesome-gamedev-agent-skills `skills/godot/*`（主干）

15 个目录、每个 `SKILL.md` 120–170 行加一个 77–113 行的 reference，全部标注
"Targets **Godot 4.7**"。frontmatter 只有 `name` + `description`（折叠式 `>`），没有任何
agent 专属字段，剥离成本近于零。结构统一：`When to use` / `Core workflow` /
`Patterns`（4 段带注释代码）/ `Pitfalls` / `References` / `Related skills`。

质量特征是**先讲坑再讲 API**，与本仓库标准第 3 节一致，例如
`change_scene_to_file()` 是延迟的、`exclude` 必须是 `Array[RID]`、`call_group` 对缺方法
的节点静默忽略、`res://` 在导出后只读。抽查时发现三条不准确（见「冲突与裁决」），
其余均与 `doc/classes` 一致。

与其他候选的重叠：它与 GD-Agentic-Skills 的主题清单高度重叠，但后者 LGPL 不可合入；
与 haxqer 的重叠很小——haxqer 是 headless 自动化派，awesome-gamedev 是概念教学派，两者
互补。

**问题**：`Related skills` 大量引用同仓库里不存在于本库的 skill 名
（`physics-tuning`、`save-systems`、`game-ai`、`steam-publish`、`card-game`…），全部
按标准第 1.3 节作为上游交叉引用残留删除，改成本库的 `Do not use for …` 边界。

### godotengine/godot（一等事实源）

用法与波次 8 的 `openharmony/interface_sdk-js` 相同：**声明/源码优于散文**。

- `doc/classes/*.xml` 是官方类参考的机器可读形式，810 个文件。带 `deprecated="…"`
  属性（4.7 里 60 个类有）、每个 `<member>` 的 `default=` 属性、`<method>` 的
  `qualifiers=`。判断「某属性的默认值是什么」「某类是否已弃用」只看这里。
- `modules/multiplayer/scene_rpc_interface.cpp` 决定 RPC 的线上表示，散文文档没有写。
- `editor/editor_node.cpp::get_initial_settings()` 决定新建项目写入哪些非默认设置——
  这是「升级来的项目和新建项目行为不同」的唯一权威出处。

### godotengine/godot-docs

`tutorials/rendering/renderers.rst` 的七张对比表是三后端选型的唯一完整来源，并且带着
反直觉的项（SSAO 在 Compatibility 支持、在 Mobile 不支持；Web 只有 Compatibility）。
`tutorials/migrating/upgrading_to_godot_4.{1..7}.rst` 七份给出逐版 breaking change 与
behavior change，是 `(Godot 4.x+)` 版本门的取值依据。

### haxqer/godot-skill

82 star 但内容密度最高的社区上游。`SKILL.md` 是一个纯路由表（"Read X only when Y"），
下面挂 12 个 reference。真正有价值的是它的断言可核对：`inference_on_variant` 出厂即
error（本机 `--check-only` 实测确认）、`.tscn` 里每个节点都写 `parent="."` 会零报错地把
所有 `Control` 堆在 (0,0)、POT 生成是编辑器专属。

**问题**：整体围绕自带的 `scripts/core/dispatcher.gd` 与 `run_project.py`，属该 skill 的
自有工具链；本 skill 不复制工具，只取它验证出来的引擎事实与 headless 约定。

### thedivergentai/GD-Agentic-Skills

129 个 `godot-*` 目录，是本主题覆盖面最广的上游，但两道门都不过：**许可**是 LGPL-3.0
（只能 reference），**内容**是人格化 persona 加 95 条 never-list 的分层加载协议。用途限于
用它的目录名核对本 skill 的七个 reference 有没有漏掉整块主题（结论：其
`godot-2d-physics` / `godot-physics-3d` / `godot-autoload-architecture` /
`godot-characterbody-2d` / `godot-ui-rich-text` 都落在本 skill 的
physics / nodes-and-scenes / ui 三个 reference 内；genre 类目录 `godot-genre-moba` /
`godot-genre-rts` / `godot-rpg-stats` 属游戏类型模板，不在本 skill 范围）。

### jame581/GodotPrompter

30+ 个主题 skill，694 star，MIT。可取的是一条**编辑边界**：明确禁止给菜单路径、
dock 布局、工具栏位置，理由是「这些在 Godot 版本间移动，是任何回答里最容易被幻觉的
部分」。本 skill 的 UI 与 build 两个 reference 照此办理——只写 Inspector 属性名与节点
类型，不写点击路径。不可取的是 hook + `~/.godot-prompter/state/<sha256(path)>.json`
状态文件机制，属 agent 专属。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 重复连接同一个信号会怎样 | awesome-gamedev `godot-signals-groups`：「Duplicate connections fire handlers multiple times」，并给出 `if not sig.is_connected(cb)` 的防护 | **同一个 Callable 的第二次 connect 被拒绝**：返回 `ERR_INVALID_PARAMETER`(31)、打印 `Signal 'x' is already connected to given callable …`、连接数仍为 1、handler 仍只跑一次。真正会叠加的只有**每次都新建的 Callable**：两个词法相同的 lambda 是两个 Callable，连接数 2、handler 跑 2 次；而 `m.bind(0)` 两次仍判为相等，第二次被拒。`CONNECT_REFERENCE_COUNTED` 才允许重复登记，且只计数不叠加触发 | 本机实测（实验 2）+ `doc/classes/Object.xml` `connect`：「A signal can only be connected once to the same Callable. If the signal is already connected, this method returns ERR_INVALID_PARAMETER and generates an error, unless the signal is connected with CONNECT_REFERENCE_COUNTED」 |
| 2 | `@rpc` 方法集不一致会怎样 | awesome-gamedev `godot-multiplayer`：「Godot checksums all `@rpc` methods in a script; mismatches break silently…Argument names/count are not checked, but the set of RPCs and their annotations are」 | 机制说反了。线上包里携带的是**按方法名排序后的序号**（`names.sort_custom(...)`；`uint16_t id = (uint16_t)i`），不是名字也不是注解集合。所以增删或**重命名**任何一个 `@rpc` 方法都会让其余方法的 id 平移，对端就会执行另一个函数。md5 只在**确认节点路径**的那个包里带一次（`get_rpc_md5` 把名字按 id 顺序拼接后取 md5），不匹配时仅 `ERR_PRINT("The rpc node checksum failed. Make sure to have the same methods on both nodes. Node path: …")` 然后继续跑 | `modules/multiplayer/scene_rpc_interface.cpp` `_parse_rpc_config` / `get_rpc_md5` / `_process_rpc`；`modules/multiplayer/scene_cache_interface.cpp:119-122`（@ `4.7.2-stable`） |
| 3 | 代码里怎么设置 anchor 预设 | awesome-gamedev `godot-ui-control` Pattern 1：`anchors_preset = Control.PRESET_FULL_RECT` | **该赋值是静默空操作**。`anchors_preset` 是 `PROPERTY_USAGE_INTERNAL` 的编辑器面向属性，setter `_set_anchors_layout_preset` 在 `stored_layout_mode` 不是 `LAYOUT_MODE_UNCONTROLLED` 或 `LAYOUT_MODE_ANCHORS` 时直接 return；代码里新建的 Control 处于 Position 模式，所以 `anchor_right` 仍是 0.0。正确写法是方法 `set_anchors_preset()` | 本机实测（实验 6）：`set("anchors_preset", 15)` 后 `anchor_right=0.0`，`set_anchors_preset(15)` 后 `anchor_right=1.0`；`scene/gui/control.cpp:1014-1026` 与 `:4946` |
| 4 | `queue_free()` 之后多久对象失效 | awesome-gamedev `godot-nodes-scenes`：「`queue_free()`（deletes at end of frame）」；`doc/classes/Node.xml`：「Queues this node to be deleted at the end of the current frame」 | 两方都对，但都不足以指导 `await`。实测：`queue_free()` 后 `await get_tree().process_frame` **一次**，`is_instance_valid()` 仍为 `true`；**第二次**之后才为 `false`。原因是 `process_frame` 在 `_process` 之前发出，而删除发生在该帧所有 deferred 调用之后。正文写「跨过一次 `process_frame` 的代码仍会看到有效实例」，而不是「帧末失效」 | 本机实测（实验 2）+ `doc/classes/Node.xml` `queue_free`：「the node will only be freed after all other deferred calls are finished」 |
| 5 | 新建 4.7 项目和升级来的 4.7 项目一样吗 | 所有候选都默认「同一个引擎版本 = 同一个行为」 | 不一样，且差异不在任何 skill 里。`EditorNode::get_initial_settings()` 给新项目写入四个**非默认值**：`physics/3d/physics_engine="Jolt Physics"`（引擎默认 `DEFAULT` = GodotPhysics3D）、`display/window/stretch/mode="canvas_items"`（默认 `disabled`）、`display/window/stretch/aspect="expand"`（默认 `keep`）、`rendering/rendering_device/driver.windows="d3d12"`（默认 `vulkan`）。所以从 4.5 升上来的项目跑的是另一个 3D 物理引擎，4.7 那批 Jolt 行为变更（`WorldBoundaryShape3D.plane.d` 符号反转、`SoftBody3D` 质量）对它无效，而对新项目有效 | `editor/editor_node.cpp:8346-8353`（@ `4.7.2-stable`）+ `doc/classes/ProjectSettings.xml` 四个 `default=` 属性 + `godot-docs` `upgrading_to_godot_4.7.rst` |
| 6 | 导出后写 `res://` 会怎样 | awesome-gamedev `godot-export`：「Writing to `res://` at runtime **fails** in exports (read-only, packed)」 | 不是失败，是**静默无效**，危害更大。实测导出版里 `FileAccess.open("res://data.json", WRITE)` 返回有效句柄、`get_open_error()` 为 0、`store_string` 正常，但随后 `get_file_as_string("res://data.json")` 仍返回打包进 pck 的旧内容；字节被写到了进程工作目录下的一个影子文件。同时 `ProjectSettings.globalize_path("res://")` 在导出版返回**空字符串**，连写到哪儿都记不下来。在编辑器里这套代码完全正常（`res://` 就是项目目录），所以缺陷一定活到发布 | 本机实测（实验 4：编辑器 / 导出两次运行对比，pck 内容 `{"packed": true, "level": 1}` 始终胜出） |
| 7 | GDScript 的类型推断有多严 | awesome-gamedev `godot-gdscript`：「Use `:=` for inferred types」；haxqer：「never use `:=` where the right-hand side has no concrete static type … Godot rejects those at parse time — with `inference_on_variant` shipping set to error」 | haxqer 对，且比它说的更硬。`debug/gdscript/warnings/inference_on_variant` 的出厂默认值是 **2 = Error**（相邻的 `untyped_declaration`、`inferred_declaration` 默认都是 0 = 忽略），实测 `var a := d["k"]` 与 `var b := untyped_fn()` 是 `Parse Error: Cannot infer the type of "a" variable because the value doesn't have a set type`，脚本根本加载不了 | `doc/classes/ProjectSettings.xml` `debug/gdscript/warnings/inference_on_variant` `default="2"`；本机实测（实验 7） |
| 8 | `_ready()` 会不会重跑 | awesome-gamedev `godot-nodes-scenes`：「`_ready()` on the child only runs _after_ it enters the tree」（只讲首次） | 关键点是**只跑一次**。实测 `add_child` → `remove_child` → `add_child` 不会再跑 `_ready()`；必须先 `request_ready()`。对象池把节点摘下再挂回时，初始化不会重来 | 本机实测（实验 8）+ `doc/classes/Node.xml` `_ready`：「This method may be called only once for each node … This can be bypassed by requesting another call with request_ready」 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `godot-engine` | godotengine/godot `doc/classes` + `modules/multiplayer` + `editor/editor_node.cpp` + `scene/gui/control.cpp` @ `4.7` | merged | 一等事实源：默认值、`deprecated=` 标记、RPC id 分配机制、新建项目写入的设置、`anchors_preset` 的 gate |
| `godot-docs` | godotengine/godot-docs `tutorials/{rendering,migrating,export,scripting,ui,physics,networking,performance}` | merged | 三后端特性对比、逐版 breaking/behavior 变更（版本门取值）、导出与 Web 要求 |
| `awesome-gamedev-godot` | gamedev-skills/awesome-gamedev-agent-skills `skills/godot/*` | merged | 七个 reference 的主题划分与坑位清单骨架；`Pitfalls`-first 的写法 |
| `haxqer-godot` | haxqer/godot-skill `skill/godot` | merged | 4.7 实测的 headless 约定、`inference_on_variant`、`.tscn` 手写陷阱、TileMap/Parallax 弃用门 |
| `wshobson-godot` | wshobson/agents `plugins/game-development/skills/godot-gdscript-patterns` | merged | `@export_group`/`@export_range`、私有下划线约定、状态机骨架 |
| `abagames-headless-godot` | abagames/headless-godot-skill-kit `.agents/skills/headless-godot` | merged | headless/CI 工作流：`--path` 固定、日志落盘、`XDG_*` 覆盖、禁止文本编辑 `.tscn` |
| `godot-prompter` | jame581/GodotPrompter `skills/*` | merged | 编辑边界（不写菜单路径 / dock 位置）、GdUnit4 与测试一节的主题划分 |
| `zimo-godot-ui` | zimo-xiao-zheng/godot-ui-integration | reference | `.tscn` 为视觉事实源、运行时代码不搭布局这条不变量的来源核对 |
| `gd-agentic-skills` | thedivergentai/GD-Agentic-Skills | reference | **许可裁决**（LGPL-3.0）：只用 129 个目录名核对覆盖面 |
| `randroids-godot` | Randroids-Dojo/Godot-Claude-Skills | reference | GdUnit4 命令形状交叉校验；新鲜度 0（>6 个月）不作内容来源 |
| `dsh-godot` | akira399/dsh-godot-skill | reference | **内容裁决**：官方特性列表的重排（生成式索引），只作覆盖面核对 |

## 本机实验

Godot **可以真装**：官方 Linux 版自带 `--headless`。以下全部在本机跑过，命令与原始输出
照抄。

### 环境

```console
$ gh release download 4.7.2-stable --repo godotengine/godot \
    --pattern 'Godot_v4.7.2-stable_linux.x86_64.zip'
$ ./Godot_v4.7.2-stable_linux.x86_64 --headless --version
4.7.2.stable.official.ed1daf0bf
```

导出模板同样装了真的（`Godot_v4.7.2-stable_export_templates.tpz`，1.28 GB，解包到
`~/.local/share/godot/export_templates/4.7.2.stable/`，`version.txt` 为 `4.7.2.stable`），
所以下面的导出实验是真导出，不是模拟。

### 实验 1 — 整数除法 / 重复 connect / `add_child` 命名 / 唯一名

```console
$ godot --headless --quit-after 120
== int division: 5/2 = 2 | 5.0/2 = 2.5
== is_node_ready in _ready: true
== connect err first=0 second=31 is_connected=true
== handler hits after one emit with two connect attempts: 1
== after queue_free same frame: is_instance_valid=true is_queued_for_deletion=true still child=true
== add_child names: Bullet / @Node@3 / Bullet2
== get_node_or_null missing = <Object#null>
== %Unique on node with no owner: <Object#null>
== physics_ticks_per_second = 60 max_fps=0
ERROR: Signal 'ping' is already connected to given callable 'Node(main.gd)::_on_ping' in that object.
   at: connect (core/object/object.cpp:1562)
```

三个节点都叫 `Bullet`：第一个保留 `Bullet`，第二个（默认 `force_readable_name=false`）
变成 `@Node@3`——**进程级计数器**决定的名字，所以多人游戏里各端会分歧；第三个传了
`true` 才得到 `Bullet2`。

### 实验 2 — `queue_free` 精确时序 / Callable 同一性 / NodePath 代价

```console
$ godot --headless
== queue_free: after 1 process_frame -> valid=true
== queue_free: after 2 process_frame -> valid=false
== after free(): valid=false
== bind(0) twice: err=0,31 connections=1
== hits with two bind(0) connects: 0
== lambdas: connections=2
== hits with two distinct lambdas: 2
== ref-counted connect err=0,0 connections=1
== hits with 2x CONNECT_REFERENCE_COUNTED: 1
== resolved deep node: L7
== 200000 iters usec: get_node(String)=75321  get_node(NodePath)=16516  cached=1653
== is_instance_valid(freed)=false
```

八层深的路径、20 万次：字符串路径 75.3 ms（0.377 µs/次）、`NodePath` 常量 16.5 ms
（0.083 µs/次）、缓存引用 1.65 ms（0.008 µs/次）。**字符串路径约为缓存引用的 45 倍，
`NodePath` 约为 10 倍**——这就是「每帧 `get_node("…")` 要挪进 `@onready`」的量级依据。

（`hits with two bind(0) connects: 0` 是因为 `bind(0)` 给只收 1 个参数的 handler 追加了
第二个实参：`ERROR: … Method expected 1 argument(s), but called with 2.`，正好也验证了
`bind` 是**追加**实参。）

### 实验 3 — `--check-only` 的报错形状

```console
$ godot --headless --check-only --script res://bad.gd
SCRIPT ERROR: Parse Error: Expected ":" after "if" condition.
          at: GDScript::reload (res://bad.gd:6)
ERROR: Failed to load script "res://bad.gd" with error "Parse error".
   at: load (modules/gdscript/gdscript_resource_format.cpp:46)
$ echo $?
1
```

同一个文件里第 4 行的 `var x: int = "not an int"` 和第 5 行的未声明标识符都没有被报出来：
**解析在第一个语法错误处停止**，所以 `--check-only` 是一道「能不能解析」的门，不是完整
类型检查。退出码 1，可以在 CI 里 gate。

### 实验 4 — 导出后写 `res://`（最重要的一条）

```console
$ godot --headless --export-release "Linux" build/x
ERROR: Invalid export preset name: Linux.
The following presets were detected in this project's `export_presets.cfg`:
$ godot --headless --export-release "Linux/X11" /tmp/gdlab/build/gdlab.x86_64
ERROR: Prepare Template: The given export path doesn't exist.
ERROR: Project export for preset "Linux/X11" failed.
$ mkdir -p build/linux && godot --headless --export-release "Linux/X11" build/linux/gdlab.x86_64
[ DONE ] savepack
$ echo $?
0
```

预设名精确匹配；输出目录必须先存在。导出成功后对比编辑器运行与导出版运行：

```console
# 编辑器里运行（res:// 就是项目目录）
res:// globalized -> /tmp/gdlab/
packed read #1: {"packed": true, "level": 1}
overwrote res://data.json
packed read #2: {"packed": false, "level": 99}

# 导出版运行（pck 里是 {"packed": true, "level": 1}）
res:// globalized ->
packed read #1: {"packed": true, "level": 1}
overwrote res://data.json          <- FileAccess.open(..., WRITE) 成功，err=0
packed read #2: {"packed": true, "level": 1}   <- 读回来还是打包内容
$ ls build/linux4
data.json  g.pck  g.x86_64        <- 字节落到了工作目录下的影子文件
```

写入**没有报错**、`FileAccess.get_open_error()` 为 0，但读回来永远是 pck 里的旧内容，
而且 `globalize_path("res://")` 返回空串。第二次启动结果相同。所以「保存到 `res://`」这
类代码在编辑器里表现完全正常，导出后静默丢数据。

### 实验 5 — 导出的 Resource 在实例间共享

```console
# enemy.tscn 的 @export var stats 指向 res://stats.tres
a.stats id=-9223372009575021102 b.stats id=-9223372009575021102 same=true
after a.stats.hp = 1 -> b.stats.hp = 1
resource_local_to_scene = false

# 把 stats.tres 加上 resource_local_to_scene = true 之后
local_to_scene: same resource? false local=true
a.hp=1 b.hp=50
```

两次独立的 `PackedScene.instantiate()` 拿到的是**同一个** Resource 实例；改一个改全部。
`resource_local_to_scene = true` 才让每个场景实例各持一份副本。
（脚本里写 `@export var stats: Stats = Stats.new()` 不受影响——默认表达式每实例求值一次；
出问题的是在 Inspector 里把一个 `.tres` 挂上去的那种。）

### 实验 6 — `anchors_preset` 是空操作；Container 接管布局

```console
via set('anchors_preset'): anchor_right=0.0 anchor_bottom=0.0 get=0
via set_anchors_preset(): anchor_right=1.0 anchor_bottom=1.0
anchors_preset usage flags = 14

Control.mouse_filter default = 0 (STOP=0 PASS=1 IGNORE=2)
Label.mouse_filter = 2 | ColorRect = 0 | Panel = 0 | TextureRect = 1 | Button = 0
child position after container sort = (0.0, 0.0) size = (200.0, 50.0) anchor_right=0.0
```

把子节点的 `position` 设成 `(999, 999)` 并调用 `set_anchors_preset(PRESET_FULL_RECT)`，
两帧后 VBoxContainer 把它改回 `(0, 0)`、尺寸强制为 `(200, 50)`、anchor 仍是 0——容器
里的 anchor 与 position 一律被丢弃。`mouse_filter` 的默认值也在这里定下来：`Control`、
`Panel`、`ColorRect` 都是 STOP（吞事件），`Label` 被覆盖为 IGNORE，`TextureRect` 为 PASS。

### 实验 7 — `:=` 推断出 Variant 是硬错误

```console
$ godot --headless --check-only --script res://main.gd
SCRIPT ERROR: Parse Error: Cannot infer the type of "a" variable because the value doesn't have a set type.
          at: GDScript::reload (res://main.gd:8)
SCRIPT ERROR: Parse Error: Cannot infer the type of "b" variable because the value doesn't have a set type.
          at: GDScript::reload (res://main.gd:9)
ERROR: Failed to load script "res://main.gd" with error "Parse error".
```

`var a := d["k"]`（Dictionary 读）与 `var b := untyped_fn()`（无返回类型的函数）都是
**解析错误**，不是警告。

### 实验 8 — `_ready()` 只跑一次；信号在接收方被释放时自动断开

```console
add #1 -> _ready count = 1 is_node_ready=true
re-add #2 (no request_ready) -> count = 1 is_node_ready=true
re-add #3 (after request_ready) -> count = 2

connections: 2
connections after freeing receiver: 1
handler ran
survived emit after receiver freed
```

### 实验 9 — CI 三连坑：`class_name`、退出码、`--import`

```console
$ rm -rf .godot && godot --headless        # 全新 clone，没有 .godot/
SCRIPT ERROR: Parse Error: Could not find type "Stats" in the current scope.
          at: GDScript::reload (res://main.gd:10)
ERROR: Failed to load script "res://main.gd" with error "Parse error".
# 进程不退出：主场景加载了但没有脚本，主循环一直跑，只能 timeout 杀掉

$ godot --headless --import && godot --headless
local_to_scene: same resource? false local=true
class_name Stats resolved: 1
$ cat .godot/global_script_class_cache.cfg
list=[{ "base": &"Resource", "class": &"Stats", ..., "path": "res://stats.gd" }]

$ rm -rf .godot && godot --headless --quit-after 300; echo "EXIT CODE=$?"
SCRIPT ERROR: Parse Error: Could not find type "Stats" in the current scope.
EXIT CODE=0
```

三条都进了正文：`class_name` 全局类型来自 `.godot/global_script_class_cache.cfg`，那是
编辑器/`--import` 的文件系统扫描产物，全新 clone 上第一次 headless 运行解析不出来；
不带 `--quit-after` 时主场景脚本解析失败会让进程**永不退出**；带 `--quit-after` 时
**退出码是 0**，所以只看退出码的冒烟测试对完全坏掉的构建也会通过。

### 实验 10 — 用真引擎解析检查评测夹具

```console
$ godot --headless --path /tmp/gdfix --check-only --script res://player.gd
SCRIPT ERROR: Parse Error: Identifier "hp_bar" not declared in the current scope.
SCRIPT ERROR: Parse Error: Identifier "sprite" not declared in the current scope.
SCRIPT ERROR: Parse Error: Preload file "res://fx/corpse.tscn" does not exist.
ERROR: Failed to load script "res://player.gd" with error "Parse error".

$ godot --headless --path /tmp/gdfix --check-only --script res://wave_spawner.gd
SCRIPT ERROR: Parse Error: Preload file "res://enemies/grunt.tscn" does not exist.
SCRIPT ERROR: Parse Error: Cannot infer the type of "GRUNT" constant because the value doesn't have a set type.
SCRIPT ERROR: Parse Error: Identifier "LootTable" not declared in the current scope.
```

夹具 `player.gd` 里「`hp_bar` / `sprite` 从未声明」这条不是推断，是引擎报出来的；
scenario 1 的 `expected_behavior` #5 因此有据。另外两个夹具的报错（缺 preload 目标、
缺 autoload）是把单个文件从工程里摘出来造成的，不是夹具设计缺陷。

### 版本门的取值核对：跨分支 `doc/classes` 取证

`(Godot 4.x+)` 一律不凭记忆、也不只凭 milestone，而是**按引擎的版本分支逐个取同一个
`doc/classes` 文件再比对**——某个成员 / 注解 / `deprecated=` 属性最早出现在哪个分支上，
那个分支号就是版本门。这是 `harmonyos` 用 `.d.ts` 声明的同构手法。

分支清单（`gh api repos/godotengine/godot/branches --jq '.[].name'`）：
`1.0 … 3.6 4.0 4.1 4.2 4.3 4.4 4.5 4.6 4.7 master`。取文件：

```bash
gh api "repos/godotengine/godot/contents/doc/classes/<Class>.xml?ref=<branch>" \
  --jq .content | base64 -d
```

#### 取证的两个坑：`doc/classes` 的 schema 本身变过

**粗粒度 `grep -c 'deprecated='` 会给出错误答案。** 属性名在 4.3 改过一次，而且类级与方法级
用的是同一个属性名，所以必须**同时匹配两种写法并区分层级**。实测 `TileMap.xml`：

| 分支 | `deprecated=` 命中 | `is_deprecated` 命中 | 类级弃用？ | 方法级 |
|---|---|---|---|---|
| 4.1 | 0 | 0 | 无 | 无（`<class>` 标签上还带着 `version="4.1"`） |
| 4.2 | **3** | **3** | **无** | `force_update` / `get_navigation_map` / `set_navigation_map`，全部写作 `is_deprecated="true"`，无说明文本 |
| 4.3 | 4 | 0 | **有**：`deprecated="Use multiple [TileMapLayer] nodes instead. …"` | 同样那三个方法，改成带说明文本的 `deprecated="…"` |
| 4.5 | 4 | 0 | 有 | 同上 |

也就是说：在 4.2 的 `TileMap.xml` 上数 `deprecated=` 会得到 **3**，看起来像是「4.2 就弃用了」，
但那 3 次全是**方法级**的旧式标记 `is_deprecated="true"`，类级一次都没有。取证必须锚在类标签上：

```bash
# 类级弃用（4.3 起的写法）
grep -oE '<class name="TileMap"[^>]*deprecated="[^"]*"' TileMap.xml
# 4.2 及更早的旧写法，且区分层级
grep -oE '<(class|method|member) name="[^"]+"[^>]*is_deprecated="true"' TileMap.xml
```

本报告里那张表用的是 `re.search(r'<class name="X"[^>]*?deprecated="([^"]{0,60})')`，天然只看类标签，
所以结果没受影响；但换成 `grep -c` 就会误判。第二个坑是 4.1 及更早的 `<class>` 标签带
`version="4.x"` 属性而 4.2 起没有——任何跨 4.1/4.2 边界的差分脚本都要容忍这一点。

对 4.2–4.7 六个分支各取一次，结果（`ABSENT` = 该分支上不存在）：

| 断言 | 文件 | 4.2 | 4.3 | 4.4 | 4.5 | 4.6 | 4.7 | 定出的门 |
|---|---|---|---|---|---|---|---|---|
| `@export_tool_button` | `modules/gdscript/doc_classes/@GDScript.xml` | — | ABSENT | 有 | 有 | 有 | 有 | `(4.4+)` |
| `@abstract` | 同上 | — | ABSENT | ABSENT | 有 | 有 | 有 | `(4.5+)` |
| `Dictionary.get_typed_key_builtin`（类型化字典） | `Dictionary.xml` | ABSENT | ABSENT | 有 | 有 | 有 | 有 | `(4.4+)` |
| `RenderingServer.get_current_rendering_method` | `RenderingServer.xml` | ABSENT | ABSENT | 有 | 有 | 有 | 有 | `(4.4+)` |
| `rendering/rendering_device/fallback_to_opengl3` | `ProjectSettings.xml` | ABSENT | ABSENT | 有 | 有 | 有 | 有 | `(4.4+)` |
| `rendering/rendering_device/fallback_to_vulkan` | 同上 | ABSENT | 有 | 有 | 有 | 有 | 有 | `(4.3+)` |
| `Control.offset_transform_enabled` | `Control.xml` | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | 有 | `(4.7+)` |
| `CollisionShape2D.one_way_collision_direction` | `CollisionShape2D.xml` | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | 有 | `(4.7)` |
| `InputEvent.DEVICE_ID_MOUSE` | `InputEvent.xml` | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | 有 | `(4.7)` |
| `TileMap` 的 `deprecated=` | `TileMap.xml` | ABSENT | 有 | 有 | 有 | 有 | 有 | `(4.3+)` |
| `ParallaxBackground` 的 `deprecated=` | `ParallaxBackground.xml` | ABSENT | **ABSENT** | **ABSENT** | 有 | 有 | 有 | `(4.5+)` |
| `Parallax2D` 这个类本身 | `Parallax2D.xml` | ABSENT | 有 | 有 | 有 | 有 | 有 | `(4.3+)` |
| `Control.accessibility_live` 的 `enum=` | `Control.xml` | — | — | — | `DisplayServer.*` | `DisplayServer.*` | `AccessibilityServer.*` | 4.7 改枚举归属 |
| `AudioStreamPlayer2D/3D.area_mask` 的 `default=` | `AudioStreamPlayer{2D,3D}.xml` | — | — | — | — | `1` | `0` | `(4.7)` |
| `RichTextLabel.add_image` 的参数类型 | `RichTextLabel.xml` | — | — | — | — | `int/int/bool/bool` | `float/float/int/int` | `(4.7)` |
| `RichTextLabel.ImageUnit` 常量 | 同上 | — | — | — | — | ABSENT | `IMAGE_UNIT_{PIXEL,PERCENT,EM}` | `(4.7)` |

**这一步推翻了两条散文结论**（和 `harmonyos` 那次一样，都是「声明赢散文」）：

1. **haxqer 把两个节点弃用并成「4.3+ node deprecations（`TileMap` → `TileMapLayer`、
   `ParallaxBackground` → `Parallax2D`）」。** 分支 diff 显示 `TileMap.xml` 的
   `deprecated=` 最早出现在 `4.3`，而 `ParallaxBackground.xml` 的 `deprecated=` 最早出现在
   **`4.5`**；`Parallax2D` 只是在 4.3 被**加入**。也就是说 4.3 / 4.4 项目继续用
   `ParallaxBackground` 是完全合规的。正文 `references/godot-nodes-and-scenes.md` 因此
   拆成两个门写，并说明 `Parallax2D` 是 `Node2D` 而 `ParallaxBackground` 是 `CanvasLayer`
   （两者的 `inherits=` 属性），所以替换是结构重排而非改名。
2. **官方迁移指南 `upgrading_to_godot_4.7.rst` 把 `area_mask` 默认值变更写在
   `AudioStreamPlayer` 名下。** 分支 diff 显示 `AudioStreamPlayer.xml` 里**根本没有
   `area_mask` 这个成员**；有的是 `AudioStreamPlayer2D.xml` 与 `AudioStreamPlayer3D.xml`，
   在 4.6 上 `default="1"`、在 4.7 上 `default="0"`。照指南去 `AudioStreamPlayer` 上找这个
   属性会找不到。正文已按声明改写。

#### 第三个事实源：`misc/extension_api_validation/`

`misc/extension_api_validation/<from>-stable/GH-<pr>.txt` 是**引擎自己维护的 extension API
破坏性变更台账**——每个文件对应一个打破 GDExtension ABI 的 PR，内容就是
`validate_extension_api.sh` 针对 `extension_api.json` 跑出来的 diff。目录按**起始版本**命名，
所以 4.6→4.7 那一批在 `misc/extension_api_validation/4.6-stable/` 下。例如
`4.6-stable/GH-112617.txt` 原文：

```
Validate extension JSON: API was removed: classes/RichTextLabel/enums/ImageUpdateMask/values/UPDATE_WIDTH_IN_PERCENT
Validate extension JSON: Error: Field 'classes/RichTextLabel/methods/add_image/arguments/10': type changed value in new API, from "bool" to "enum::RichTextLabel.ImageUnit".
Validate extension JSON: Error: Field 'classes/RichTextLabel/methods/add_image/arguments/1': type changed value in new API, from "int" to "float".
```

**相对跨分支 `doc/classes` diff 的优势**：

1. **已经 diff 好了**，不用取两份文件再比，也不会踩上面那个 schema 变更的坑。
2. **粒度到参数**：给出「第 10 个实参由 `bool` 变 `enum::RichTextLabel.ImageUnit`、默认值由
   `false` 变 `0`」这种 `doc/classes` 里看不出来的细节（XML 里那个参数的 `type` 只写 `int`）。
3. **自带归因**：文件名就是 PR 号，直接能查到原始讨论与迁移建议。
4. **是引擎维护者自己写的且 CI 强制**，不是第三方整理，也不是散文：
   `.github/workflows/linux_builds.yml:261` 调用 `./misc/scripts/validate_extension_api.sh`，
   所以台账不会漏记它覆盖的那一类变更。

**局限，必须同时用另外两个手段兜底**：

1. **只覆盖「被 PR 记录下来的破坏性 API 形状变更」。** 静默的**行为**变化完全不在里面——本
   skill 里 Jolt 的 `WorldBoundaryShape3D.plane.d` 符号反转、`SoftBody3D` 质量与
   `linear_stiffness` 的重新解释、Glow 默认混合模式改成 Screen、`CanvasItem` 不再加抗锯齿
   feather，签名一个都没动，所以台账里一条都没有。这类只能读迁移指南的 behavior changes 节。
2. **不覆盖「新增」**。新增成员不破坏 ABI，所以 `@abstract`、`Control.offset_transform_*`、
   `InputEvent.DEVICE_ID_MOUSE` 这些「某版本才有」的门，台账里查不到，只能靠跨分支 diff。
3. **不覆盖非 ClassDB 的东西**：GDScript 注解、项目设置默认值、`.tscn` 文件格式、编辑器写入
   的新建项目默认值，全都不在 `extension_api.json` 里。
4. **目录命名容易读反**：`misc/extension_api_validation/README.md` 写的是「Add new entries to
   the `{TAG}` folder」，`{TAG}` 是**当前开发所基于的那个 tag**，所以 `4.6-stable/` 装的是
   4.6 之后（即 4.6→4.7）的变更，不是 4.5→4.6 的。同一个 README 也确认了内容语义：
   「the expected output of `--validate-extension-api` when run against the
   `extension_api.json`」，且只有以 `Validate extension JSON:` 开头的行有效，其余是给人看的
   说明。

所以三个手段是分工关系，不是替代关系：**跨分支 `doc/classes` diff 定「有/没有」与默认值，
`extension_api_validation` 定「签名怎么变」，迁移指南的 behavior changes 定「签名没变但行为
变了」**。已把该目录加入 `SOURCES.yaml` 的 `paths`。

仍然只有 milestone 证据（分支 diff 不适用，因为不是 API 形状变更）的三条，列在此处以示区分：

| 标注 | 依据 |
|---|---|
| Jolt 成为新项目默认 `(4.6+)` | `doc/classes/ProjectSettings.xml` 原文 +`editor/editor_node.cpp:8350`（不是 API 形状，是编辑器写入的值） |
| `.tscn` 去掉 `load_steps`、写入节点唯一 id `(4.6)` | `upgrading_to_godot_4.6.rst`（GH-103352 / GH-106837）——文件格式，不在 `doc/classes` 里 |
| Glow 默认混合模式改为 Screen `(4.6)`、`LinearToSRGB` 不再钳制 `(4.7)` | 迁移指南的 behavior changes 节；纯渲染表现，本机无 GPU 无法实测 |

### 未在本机验证的清单（标 `[official]`，不标 `[verified]`）

以下无法在 Linux headless 上验证，全部以 `godotengine/godot` 的 `doc/classes/*.xml`、
引擎源码或 `godot-docs` 为据：

1. Forward+ / Mobile / Compatibility 的**画面差异**与逐项特性支持（headless 不创建
   RenderingDevice；本机 GPU 是 QEMU 虚拟显卡，无 Vulkan）。来源：
   `tutorials/rendering/renderers.rst` 的七张对比表。
2. Web 导出的实际运行与 COOP/COEP 行为（需要浏览器与 HTTP 服务）。
3. Android / iOS / macOS 导出与签名（需要 SDK、keystore、Apple 工具链）。
4. Jolt 与 GodotPhysics3D 的**数值差异**（`WorldBoundaryShape3D.plane.d` 符号、
   `SoftBody3D` 质量与 `linear_stiffness`）。来源：`upgrading_to_godot_4.7.rst`。
5. C# / .NET 侧的一切（本机装的是非 .NET 版编辑器；`mono_linux_x86_64` 另需 .NET SDK）。
   `references/godot-csharp-interop.md` 的每条都是 `[official]`。
6. `physics_interpolation` 的视觉效果（无渲染）。
7. 多人联机的真实双端行为：RPC id 平移与 checksum 报错是**源码核对**，不是双进程实测。
8. `MultiplayerSpawner` / `MultiplayerSynchronizer` 的编辑器内配置面板。
9. GdUnit4 / GUT 的运行（都是第三方 addon，未安装；命令形状取自
   Randroids-Dojo/Godot-Claude-Skills 并与官方 CLI 文档对齐，标 `[community]`）。
10. 4.7 的 `Control.offset_transform_*` 与新节点（`AreaLight3D`、`VirtualJoystick`、
    `DrawableTexture2D`）的行为——只核对了它们在 `doc/classes` 中存在。

## 基线缺口

无 skill（`uv run tools/run_evals.py godot --baseline`，Claude Opus 5 · medium，五个场景
全部 `status=ok`、`skill_read=false`，耗时 113–260 s）时的逐条判定。

**基线非常强**，不是零区分度：Opus 5 自己就抓到了 `velocity * delta`、`_process` 里跑
`move_and_slide()`、`free()` 的立即销毁、整数除法、Resource 共享、预设名不匹配、输出目录、
`--quit-after` 是帧数且退出码为 0，甚至抓到了 **RPC 按排序后下标寻址** 和
**lambda 与具名方法在重复 connect 上的区别**。所以不需要按 Phase B 改写量规——缺口全部
落在**只有声明/源码/实测才能给出的那一层**，而且基线在这些地方给的是**错误答案**，不是
沉默，这比沉默更危险。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 player.gd | #4 导出后写 `res://` 的机制 | 基线断言「导出版 `res://` 被打包成只读 `.pck`，`FileAccess.open` 返回 `null`，代码没有空值检查所以 `f.store_string` 在 null 上报错」。**实测相反**（实验 4）：句柄有效、`get_open_error()` 为 0、`store_string` 正常，读回来才是旧内容。基线给出的修复能用，但给出的**因果是错的**，按它去查日志里的 null 会什么也查不到 |
| 1 | #7 `anchors_preset` 是空操作 | 基线把每帧写 `anchors_preset` 判成「最贵的一条：触发 Control 重算锚点并 `queue_sort()`，整棵 UI 子树每帧重排」。实测该赋值**什么都没做**（实验 6），既不重排也不设锚点；真正的缺陷是覆盖层永远没有铺满 |
| 1 | #9 `_ready()` 只跑一次 | 基线说 `remove_child` + `add_child` 会「触发 EXIT_TREE/ENTER_TREE，重置节点内部状态与计时器」，并建议**删掉**这两行。实测 `_ready()` 根本不会重跑（实验 8），必须 `request_ready()`；删掉重挂等于删掉了池化意图 |
| 1 | #6 路径查找代价的量级与排序 | 基线正确指出每帧绝对字符串路径贵，但没有给出 `String` / `NodePath` / 缓存引用三者的相对代价，因此无法回答「改成 `NodePath` 常量够不够」 |
| 1 | #10 `RayCast2D` 在 `_process` 里读是过期的 | 完全没提。基线只讨论了 `is_on_floor()` 的时序 |
| 2 wave_spawner.gd | #6 `await` 一帧之后节点仍然有效 | 基线断言「`queue_free()` 在帧末删除，await 一帧后**必然失效**，`roll` 被静默跳过」。实测（实验 2）一帧后仍 `true`，两帧后才 `false`——所以 `roll` 是**跑在一个已判死的节点上**，掉落不稳定的原因与基线说的正好相反 |
| 2 | #3 `duplicate()` 是浅拷贝 | 基线把 `duplicate()` 和 `resource_local_to_scene` 当等价方案并列，没有说 `duplicate()` 默认不复制嵌套的 `Array`/`Dictionary`/`Resource`，而夹具的 `LootEntry` 数组正是嵌套的 |
| 2 | #5 两个 connect 站点要分开判 | 基线只判了 `respawn_all()` 里的具名方法重连（判对了），完全没提 `start_wave` 里每次新建的 `func(amount): …`——那才是真正会叠加的那个 |
| 3 project.godot + 导出 | #1 新建项目写入的四个设置 | 基线只找到 `display/window/stretch/mode`/`aspect` 两个，**漏掉 `physics/3d/physics_engine="Jolt Physics"` 与 `rendering/rendering_device/driver.windows="d3d12"`**。前者意味着这个升级项目跑的是另一个 3D 物理引擎，是本场景里后果最重的一条 |
| 3 | #2 SSAO 的后端支持 | 基线断言「SSAO / 体积雾**两者都是 Forward+ 专属**，切到 compatibility 后静默消失」。官方对比表里 **SSAO 在 Compatibility 是支持的**、在 Mobile 才不支持；只有体积雾是 Forward+ 专属。另外没提运行时必须读 `RenderingServer.get_current_rendering_method()` |
| 3 | #6 `class_name` 缓存 | 基线要求加 `--import`，理由是「fresh clone 没有导入缓存，release 导出拿不到 `.import` 产物」。真正的失败面是 `.godot/global_script_class_cache.cfg` 缺失导致 `Could not find type … in the current scope`（实验 9），而且那条错误还会让不带 `--quit-after` 的运行**永不退出** |
| 4 net_player.gd | #4 RPC 参数不能携带 `Node` | 基线说「`Node` 参数按 NodePath 编码，名字不一致时解析成 null 或错误节点」。实际是**根本无法编码**：RPC 实参只序列化纯数据，`Object`/`Node`/`Resource`/`Callable` 都不行 |
| 4 | #3 的后半：引擎自带的 checksum | 基线抓到了「按排序后下标寻址」（很强），但结论是「代码层面无法自愈，必须自己在连接时做构建哈希握手」——它不知道引擎**已经**带了一个 md5（随节点路径确认包发一次），不匹配时只 `ERR_PRINT` 然后继续跑。少了这条就不会去日志里找 `The rpc node checksum failed` |
| 4 | #6 `MultiplayerSynchronizer` | 基线把每帧广播改成手写的 20 Hz 限频 RPC 加插值，没有指出引擎为此提供的就是 `MultiplayerSynchronizer`（它只在生成侧提到了 `MultiplayerSpawner`） |
| 5 PlayerController.cs（负例） | 无缺口 | 基线模式下没有任何 skill 可读，`skill_read=false` 平凡成立；回答全程在 Unity 语境内（`FixedUpdate`、`OnDisable` 退订、`[SerializeField]` 缓存），没有出现 Godot 概念。该场景的真正判定在「有 skill」那一轮 |

## 评测结果

两组都是 Claude Opus 5 · medium（`tools/run_evals.py` 默认，未传 `--model` / `--thinking`），
题目与夹具在两轮之间**一字未改**，所以可比。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 player.gd | Opus 5 medium | 无（基线） | false | 6 / 10（#1 #2 #3 #5 #8 达成，#10 半达成） | #4 给了**相反**的因果（说 `FileAccess.open` 返回 null），#6 没给量级，#7 判成「最贵的一条」而非空操作，#9 建议删掉池化两行 |
| 1 player.gd | Opus 5 medium | 有 | **true** | 10 / 10（#10 的射线半条未提） | 四条基线缺口全部填上：`res://` 写入静默 no-op + `globalize_path` 返回空串、45x / 10x 量级、`anchors_preset` setter 早退、`request_ready()`。额外按 `## Output format` 输出（`path:line` + 严重度 + before/after + 未执行检查单列 + 一句结论 `rework`），并把 `mouse_filter` 默认值作为 `lead` 而非 finding |
| 2 wave_spawner.gd | Opus 5 medium | 无（基线） | false | 4 / 7（#1 #2 #4 #7 达成） | #6 断言 await 一帧后**必然失效**（实测相反），#3 没提浅拷贝，#5 只判了具名方法那一处 |
| 2 wave_spawner.gd | Opus 5 medium | 有 | **true** | 5 / 7（#1 #2 #4 #5 #6 达成） | 关键缺口 #6 精确填上：「一次 await 后 `is_instance_valid()` 仍为 `true`，两次才清零……这个判断什么也没判断」。但 #3 的浅拷贝一句没写，#7 的 `waves[_index]` 越界保护**比基线退步**（基线写了，有 skill 没写） |
| 3 project.godot + 导出 | Opus 5 medium | 无（基线） | false | 5 / 8（#3 #4 #5 #7 #8 达成） | #1 只找到 stretch 两项，漏掉 Jolt 与 `driver.windows`；#2 把 SSAO 误判成 Forward+ 专属；#6 的 `--import` 理由不对 |
| 3 project.godot + 导出 | Opus 5 medium | 有 | **true** | 8 / 8 | 四个新建项目默认值全部点名并各自给后果；主动写出 `ok - environment/ssao/enabled=true 在 Compatibility 下可用（只有 Mobile 不支持）`，即**纠正了基线的错判**；`class_name` 缓存与 `Could not find type` 报错形状、`--quit-after` 退出码 0 的断言方式都给了 |
| 4 net_player.gd | Opus 5 medium | 无（基线） | false | 5 / 7（#1 #2 #5 #7 达成，#3 半达成） | #3 抓到了下标寻址但不知道引擎自带 checksum；#4 的机制说错（以为按 NodePath 编码）；#6 手写限频 RPC 而未指出 `MultiplayerSynchronizer` |
| 4 net_player.gd | Opus 5 medium | 有 | **true** | 7 / 7 | #3 补全到可操作：直接算出**本脚本的实际 id**（`apply_damage=0, award_kill=1, die=2, push_state=3`）并给出「引擎只在建立节点路径缓存那一次打印 `The rpc node checksum failed`，然后照常继续跑」「把这行日志当致命错误」；#4 改为「`Object/Node/Resource/Callable` 无法被 RPC 序列化，这个调用必然编码失败」 |
| 5 PlayerController.cs（负例） | Opus 5 medium | 无（基线） | false | 4 / 4（平凡） | 基线模式无 skill 可读 |
| 5 PlayerController.cs（负例） | Opus 5 medium | 有 | **false** ✅ | 4 / 4 | **负例通过**：在 `--skills godot` 下 agent 没有读取本 skill。回答全程 Unity 语境（`FixedUpdate`、`Time.fixedDeltaTime`、`OnDisable` 退订静态事件、`[SerializeField]`），未出现 `_physics_process`、`move_and_slide`、`queue_free`、`@onready`、`PackedScene` 等任何 Godot 概念。`description` 结尾的 `Do not use for … Unity, Unreal …` 用了题目自己的词（Unity、URP、MonoBehaviour），一轮即过，未需收紧重跑 |

结论：**通过**。四个正例每一个都有「基线未达成、有 skill 达成」的行为，合计填补
**11 条**基线缺口，其中六条基线给的是**错误答案**而非沉默（`res://` 写入机制、
`anchors_preset`、`_ready` 重入、`await` 一帧、SSAO 的后端支持、RPC 携带 `Node`）——
这类缺口比沉默更值得填，因为错误答案会把排查方向带偏。负例 `skill_read=false`。

### 如实记录的未达成项与量规缺陷

不粉饰、不改判：

1. **场景 2 #3 的浅拷贝一句，有 skill 那轮也没写出来。** `references/godot-resources.md`
   有独立小节讲 `duplicate()` 默认浅拷贝，但 agent 只读了它需要的部分就下结论了。这是
   覆盖不足还是 routing 不足暂不能断定，如实记为未达成。
2. **场景 2 #7（`waves[_index]` 越界）有 skill 那轮比基线退步。** 基线写了，有 skill 没写。
   推测是注意力被资源共享这条主线吸走；无论原因，这是一次退步，记录在案。
3. **场景 1 #10 的后半（`RayCast2D` 在 `_process` 里读是过期的）两轮都未提。** 共享
   Resource 那半条两轮都达成。
4. **量规缺陷（我的错，不是模型的错）：场景 2 #5 说 `start_wave` 里的
   `func(amount): _on_enemy_hit(enemy, amount)` 会「真正叠加」。** 复核夹具后不成立——
   那个 lambda 是在 `for` 循环里连到**每个新建 enemy 自己的信号**上，每个 enemy 只连一次，
   不会叠加。两轮都正确地只把具名方法重连判成噪音，没有一个声称 lambda 叠加，也就是说
   **两个回答都比我的量规更准**。按「不改判」的要求，这条按「达成」计入并在此标明量规有
   缺陷；按「题目与夹具一字不改」的要求，没有动 `evals.json` 与夹具。
5. `evals/files/ci-export.sh` 的 `cd "$(dirname "$0")/.."` 被两轮都判成一条额外缺陷
   （脚本与 `project.godot` 同级，`..` 会跑到父目录）。这是夹具的真实缺陷，不在我的
   `expected_behavior` 里，两轮都抓到了，不构成区分度。

## 备注

### 许可注意事项

- `godotengine/godot-docs` 是 **CC-BY-3.0**（API 报 `NOASSERTION`，实读 `LICENSE.txt`
  确认是 Attribution 3.0 Unported，无 NC、无 ND），所以可 merged，但**必须署名**；
  `SOURCES.yaml` 的 `notes` 已写「Juan Linietsky, Ariel Manzur and the Godot community,
  CC-BY-3.0」。
- `thedivergentai/GD-Agentic-Skills` 是 **LGPL-3.0**，只能 `reference`；全程只用它的 129 个
  目录名核对覆盖面，未取一字。
- `zimo-xiao-zheng/godot-ui-integration`、`akira399/dsh-godot-skill` 是**内容裁决**（许可
  都是 MIT）：前者是设计审批流程 + Godot MCP 依赖，后者是官方特性列表的重排（生成式链接
  索引）。`Randroids-Dojo/Godot-Claude-Skills` 是**新鲜度裁决**（>6 个月）。三者都记
  `reference`，理由已分别写进 `notes`。
- 引擎与 awesome-gamedev、wshobson 三个仓库都只有一个根 `LICENSE`，逐目录检查过，没有
  `anthropics/skills` 那种逐目录授权的情况。

### 下次同步要盯的上游

1. **`godotengine/godot` 的 `ref: "4.7"`**（不是 `master`）。4.7.2 的 tag commit 与 master
   已 `diverged`（151 ahead / 2241 behind），pin master 会跟到没进任何已发布 4.7 的事实。
   4.7.3 出来时 `check_upstream.py` 会报 `behind`，那时重跑一遍跨分支 diff。
2. **`misc/extension_api_validation/`**。已加入 `paths`。4.8 出来时
   `misc/extension_api_validation/4.7-stable/` 里的每个 `GH-*.txt` 就是需要复核的签名变更
   清单。但**不能只看它**：它不记新增、不记非 ClassDB 的东西（GDScript 注解、项目设置默认
   值、`.tscn` 格式、新建项目写入值）、也不记签名未变的行为变化。同步时三样一起跑：跨分支
   `doc/classes` diff（注意 `deprecated=` / `is_deprecated=` 两种写法与类级/方法级之分）、
   这个台账、迁移指南的 behavior changes 节。
3. **`gamedev-skills/awesome-gamedev-agent-skills`** 推送很频繁（调研当日就有提交），
   但 `paths: skills/godot` 会过滤掉其他引擎目录的噪声。
4. **`godotengine/godot-docs` 的 `tutorials/rendering/renderers.rst`**。三后端对比表是本
   skill 唯一无法本机验证的一整节，上游改表就必须同步。

### 放弃的方向

- **不做 shader 一节。** `awesome-gamedev` 有 `godot-shaders`，但本波三个引擎约定了
  `scripting` / `rendering` / `ui` / `physics` / `build` 五个同构主题，着色器语言本身不在
  其中；`references/godot-rendering.md` 只写「哪个后端支持哪类 shader 特性」这条选型相关
  的部分。
- **不做动画 / 音频 / TileMap 的专题 reference。** 同上，超出五主题同构约定；`TileMap` 只
  以「已弃用节点」的形式出现在 `godot-nodes-and-scenes.md`。
- **不做 `scripts/`。** 本 skill 的所有可运行价值都是单条 `godot --headless …` 命令，
  已经写在 `## Environment` 与 `references/godot-build.md` 里。再包一层 Python wrapper
  只会多一个需要维护的间接层，而且上游 haxqer 的 `dispatcher.gd` 已经证明这条路会长成一个
  独立工具链。
- **不写 GdUnit4 的深度用法。** 它是第三方 addon，本机未安装，只给了命令形状并标
  `[community]`；另外给了一个零依赖的 `extends SceneTree` 断言脚本作为默认方案。

### NOTICE.md 的一次往返（已闭环）

`NOTICE.md` 在 Phase D 之后被生成过一次，随后我按主代理的取证要求修订了 `SOURCES.yaml`
的三条 `notes`（`godot-engine` 加了跨分支取证方法与 `misc/extension_api_validation` 路径、
`godot-docs` 记了 `area_mask` 的文档纠正、`haxqer-godot` 改了 `ParallaxBackground` 的版本
门），于是 `validate_skills.py` 报了 `NOTICE.md is stale`。主代理已重新生成，现在
`uv run tools/validate_skills.py skills/godot` 是 **0 error 0 warning**。

教训记一条：**改 `SOURCES.yaml` 的任何字段都会让 `NOTICE.md` 过期**，因为 NOTICE 是
`contributes` 与 `notes` 的派生产物。后续同步时，先改完 `SOURCES.yaml` 再生成 NOTICE，
不要反过来。
