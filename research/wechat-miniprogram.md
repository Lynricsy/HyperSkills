# wechat-miniprogram 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`微信小程序 agent skill SKILL.md github miniprogram claude skills`
  - `gh api orgs/wechat-miniprogram/repos?per_page=100&sort=pushed`（官方组织全量列目录，
    这是本轮最有价值的一步：路线图里没有的 `api-typings`、`glass-easel`、`skyline-skills`、
    `ai-mode-skills`、`miniprogram-simulate` 都是这样找到的）
  - `gh api search/code`（在 `dcloudio/uni-app` 内定位 `docs/compiler/platform.md`）
  - npm registry：`miniprogram-ci`、`miniprogram-api-typings`、`glass-easel`
  - 官方文档站 developers.weixin.qq.com（浏览器渲染后取正文；静态 `curl` 只能拿到首屏）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`，
  许可一律另读 `contents/LICENSE` 正文。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。
新鲜度以 2026-09-11 为基准（≤1 月 3 / ≤3 月 2 / ≤6 月 1 / >6 月 0）。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可（实读结论） | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | wechat-miniprogram/api-typings `types/wx` | https://github.com/wechat-miniprogram/api-typings | 805 | 2026-09-01 | MIT（LICENSE 正文 "MIT License … Copyright (c) 2019"） | `wx.*` / Page / Component / Behavior 官方 TS 声明 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | 机器可核对的 API 事实源：setData 1024kB 上限、storage 1MB/10MB、页面栈十层、code 五分钟有效、`this.renderer` 联合类型、各 API 的基础库版本门，全部直接读声明与其文档注释 |
| 2 | wechat-miniprogram/glass-easel（含 `glass-easel-skills/glass-easel`） | https://github.com/wechat-miniprogram/glass-easel | 329 | 2026-09-10 | MIT（LICENSE 正文为 MIT 条款，首行是裸 "Copyright 2023 wechat-miniprogram"，无 "MIT License" 标题） | 新一代组件框架本体 + 官方 skill | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | 官方 skill 形态且**同时有源码可核对**：`replaceDataOnPath` / `spliceArrayDataOnPath` / `applyDataUpdates` / `groupUpdates` / `updateData` 全部在 `dist/glass_easel.d.ts` 中验证到；另贡献 `wx:key` 的条件式用法、slot 模式代价、`dataDeepCopy` / `propertyEarlyInit` |
| 3 | wechat-miniprogram/skyline-skills `skills/*` | https://github.com/wechat-miniprogram/skyline-skills | 53 | 2026-06-03 | MIT（LICENSE 正文为 MIT 条款，"Copyright 2024 wechat-miniprogram"） | Skyline 渲染引擎官方 skill 集 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE (merged) | 配置三件套、WebView→Skyline 行为差异表、局部滚动布局、渐进迁移粒度。抽查三条（`navigationStyle: custom` 必填、`defaultDisplayBlock`/`defaultContentBox` 的作用、`scroll-view type="list"` 直接子节点按需渲染）与官方文档一致 |
| 4 | wechat-miniprogram/miniprogram-simulate | https://github.com/wechat-miniprogram/miniprogram-simulate | 536 | 2026-06-30 | MIT（实读） | 自定义组件单测工具 | 3 | 2 | 2 | 3 | 2 | 12 | INCLUDE (merged) | 官方文档指定的单测路径；贡献 `load/render/attach` 流程与"它不模拟什么"这条边界 |
| 5 | dcloudio/uni-app `docs/` | https://github.com/dcloudio/uni-app | 41608 | 2026-09-11 | Apache-2.0（API 与 LICENSE 一致） | uni-app 官方仓库内文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | 条件编译语法、`%PLATFORM%` 常量全表、**未定义平台名时 `#ifdef` 失效而 `#ifndef` 生效**这条致命默认行为、`mp-weixin` 启用 glass-easel 的两种配置（并给出 glass-easel 自 3.8.12 支持 WebView 渲染这一版本分界） |
| 6 | NervJS/taro | https://github.com/NervJS/taro | 37672 | 2026-09-08 | **MIT**（API 报 NOASSERTION；LICENSE 正文为 "MIT License / Copyright (c) 2018 O2Team"） | Taro 官方仓库 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE (merged) | 本机 `taro init` 实跑，产物目录、`defineAppConfig`、`build:<platform>` 脚本集、`designWidth/deviceRatio/pxtransform`、`compiler: webpack5\|vite` 均为实测 |
| 7 | developers.weixin.qq.com/miniprogram/dev | https://developers.weixin.qq.com/miniprogram/dev/framework/ | — | 持续 | **Proprietary**（页脚 "Copyright © 2012-2026 Tencent. All Rights Reserved."） | 官方文档 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE (reference) | **许可裁决**：专有，只作事实取证不逐字复制。数据更新算法、同层渲染现状、路由与生命周期顺序、分包体积、启动流程、授权 scope、隐私协议接口全部以此为准 |
| 8 | miniprogram-ci（npm 2.1.31） | https://www.npmjs.com/package/miniprogram-ci | — | 2.1.31 | **NONE**（`package.json` 写 MIT，但发布包内无 LICENSE 文件） | 官方 CI 编译模块 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE (reference) | **许可裁决**：按本项目规则，许可只在元数据里声明、树中无 LICENSE → 记 NONE、只能 reference。实际用法是读 `dist/@types/**/*.d.ts` 验证 API 形状 |
| 9 | wechat-miniprogram/ai-mode-skills | https://github.com/wechat-miniprogram/ai-mode-skills | 197 | 2026-09-10 | MIT（实读） | 官方「小程序 AI 模式」技能生成器 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE 但降 reference | **内容裁决**（非许可裁决）：主题是把既有小程序能力改造成 `wx.modelContext` 原子接口，属产品包装，落在本 skill 的排除范围。分数够高但不合入 |
| 10 | TencentCloudBase/CloudBase-AI-Toolkit `config/.claude/skills/miniprogram-development` | https://github.com/TencentCloudBase/CloudBase-AI-Toolkit | 1102 | 2026-09-11 | MIT | CloudBase 工具箱内的小程序开发 skill | 2 | 3 | 2 | 2 | 2 | 11 | INCLUDE 但降 reference | **内容裁决**：规范核心是 CloudBase 与 Nightly `wechatide` CLI，前者是本 skill 明示排除项，后者本机无法验证（Nightly 工具仅 Win/macOS）。在范围内的部分（项目结构、`miniprogram-ci` 兜底）是常识 |
| 11 | sonofmagic/skills `skills/weapp-vite/*`、`skills/weapp-tailwindcss/*` | https://github.com/sonofmagic/skills | 2 | 2026-09-03 | MIT（实读） | 第三方工具链 skill 集 | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE 但降 reference | **内容裁决**：全部是作者自家包（weapp-vite / wevu / weapp-tailwindcss）的说明书。标准第 3 节要求「只给一个默认方案 + 一个逃生口」，不能把第三方库写成默认方案 |
| 12 | Sun-sunshine06/miniprogram-skills | https://github.com/Sun-sunshine06/miniprogram-skills | 22 | 2026-07-20 | MIT | 脚手架对齐 / DevTools 诊断 | 1 | 2 | 1 | 2 | 2 | 8 | MAYBE，未合入 | 规则停留在「每个页面要有 .json」「组件要声明 component: true」这一层，无版本分界事实，也无「违反会怎样」。抽查未发现错误，但也没有独有事实可取 |
| 13 | TencentCloudBase/awesome-miniprogram-skills | https://github.com/TencentCloudBase/awesome-miniprogram-skills | 37 | 2026-06-18 | MIT | 路线图指定的「主干」 | 1 | 1 | 1 | 1 | 2 | 6 | REJECT | **路线图种子不成立**。实际内容是一组 CloudBase 云函数示例小程序（bill / hospital / taxi / payment…），每个目录带 `cloudbaserc.json` + `cloudfunctions/`，正落在本 skill 明示排除的「云开发 CloudBase」范围内，不是小程序工程规则集 |
| 14 | whinc/super-skills `miniprogram-automation`、`miniprogram-ci` | https://github.com/whinc/super-skills | 40 | 2026-09-11 | 无（`license: null`） | 路线图指定种子 | 1 | 3 | 0 | 0 | 0 | 4 | REJECT | **路线图种子已失效**：仓库树中 `.scratch/remove-miniprogram-add-claude-plugin/`（含 `04-remove-miniprogram-scope.md`）显示小程序范围已被整体移除，当前 `plugins/` 下只剩 engineering / learning / web，两个目标 skill 都不存在 |
| 15 | uni-helper/skills `skills/uniapp` | https://github.com/uni-helper/skills | 104 | 2026-03-01 | MIT（实读） | uni-app 文档派生 skill | 1 | 0 | 1 | 2 | 2 | 6 | REJECT | 路线图已标「推送时间临界 → 复核」：2026-03-01 距今 6 个月 10 天，新鲜度 0。内容本身是 unidocs 自动生成的主题索引表（`GENERATION.md` 自述），不是规则集 |
| 16 | joneqian/claude-skills-suite `skills/wechat-miniprogram` | https://github.com/joneqian/claude-skills-suite | 32 | 2026-02-10 | MIT | 个人 skill 合集 | 1 | 0 | 1 | 1 | 2 | 5 | REJECT | 推送 7 个月前，新鲜度 0 |
| 17 | PowellWells/wechat-starter | https://github.com/PowellWells/wechat-starter | 0 | 2026-07-04 | MIT | 新手从零建项目 | 0 | 2 | 1 | 1 | 2 | 6 | REJECT | 零星标、面向「从需求收敛到 DevTools 预览」的入门引导，与本库「teach the failure」定位相反 |
| 18 | mzopedia/develop-wechat-ai-miniprograms | https://github.com/mzopedia/develop-wechat-ai-miniprograms | 0 | 2026-07-26 | MIT | 单文件交付 SOP | 0 | 2 | 1 | 1 | 2 | 6 | REJECT | 零星标；核心内容仍是 AI Mode Skills + CloudBase，双重排除 |
| 19 | TencentCloudBase/mp-skills | https://github.com/TencentCloudBase/mp-skills | 9 | 2026-06-22 | 无（`license: null`） | AI mode skill 脚手架 | 1 | 1 | 1 | 1 | 0 | 4 | REJECT | 主题是生成 AI mode skill；无许可文件 |
| 20 | didi/mpx | https://github.com/didi/mpx | 3932 | 2026-09-11 | Apache-2.0 | 第三个跨端框架 | 2 | 3 | 2 | 3 | 2 | 12 | 分数够但**范围裁决**不收 | 与 Taro / uni-app 功能重叠。标准第 3 节：「只给一个默认方案 + 一个逃生口，不罗列多个可选库」。收进来只会让 `cross-platform.md` 变成选型目录 |
| 21 | wechat-miniprogram/computed | https://github.com/wechat-miniprogram/computed | 696 | 2026-08-24 | MIT（实读） | 官方 computed/watch 辅助库 | 3 | 3 | 2 | 3 | 2 | 13 | 分数够但未合入 | 它解决的问题（派生字段不该反复 setData）已被官方内建的 `observers` + `pureDataPattern` 覆盖，本 skill 写内建方案。作为可选库写进去违反「一个默认方案」 |
| 22 | wechat-miniprogram/miniprogram-demo | https://github.com/wechat-miniprogram/miniprogram-demo | 7227 | 2026-09-03 | MIT | 官方示例小程序 | 3 | 3 | 1 | 3 | 2 | 12 | 分数够但未合入 | 示例代码集，无规则性内容；具体性 1 |

立项门槛核对（`docs/roadmap.md`「新增主题的判据」第 2 条）：活跃（6 个月内推送）、总分 ≥8 且可 merged 的上游共 **6 个**
（api-typings 14、glass-easel 14、uni-app 14、taro 13、skyline-skills 12、miniprogram-simulate 12），远超下限 3，
走**常规通道**立项，不用官方厂商特例——顺带说明，本主题也用不了特例：官方文档站是专有许可、只能 `reference`，
与波次 5 `elasticsearch`、波次 8 `harmonyos` 的情形相同。

## 深度审查

**wechat-miniprogram/api-typings（14）.** 单一 `types/wx` 目录，18 个 `.d.ts`、62581 行，`lib.wx.api.d.ts`
占 36799 行。每个 API 的 JSDoc 直接带官方文档正文与「最低基础库」链接，等于一份可被 `tsc` 检查的文档快照。
本轮从中直接取到的硬事实：`setData` 单次 1024kB 上限与 `undefined` 被跳过、storage 单 key 1MB / 总 10MB、
`navigateTo` 文档里的「页面栈最多十层」、`wx.login` code「有效期五分钟」、`ComponentOptions` 的
`styleIsolation` 六个取值与 `pureDataPattern`(2.8.2)/`virtualHost`(2.11.2)、Page 实例上的
`renderer: 'webview' | 'skyline'`、组件 `lifetimes` 全集与 2.2.3 起 `lifetimes` 优先于旧式声明。
这正是波次 8 `harmonyos` 用 `.d.ts` 推翻散文结论的同一套路，本轮复用。

**wechat-miniprogram/glass-easel（14）.** 仓库根下既有运行时源码（`glass-easel/`）又有官方 skill
（`glass-easel-skills/glass-easel/`，1 个 SKILL.md + 7 个 reference）。skill 的 `best-practices.md` 486 行，
全是带取舍的具体建议，质量高于本轮任何社区候选。frontmatter 干净（无 agent 专属字段）。
交叉校验：skill 里出现的 6 个数据更新 API 全部能在 npm `glass-easel@1.2.0` 的 `dist/glass_easel.d.ts`
里找到同名同形签名，其中 `setData` 的注释「Inside observers, it is recommended to use `updateData` instead」
与官方文档《高级数据更新方法》一字对应。

**wechat-miniprogram/skyline-skills（12）.** 6 个 skill、40+ reference，结构规整但写法是「MUST / NEVER」
清单式，且 frontmatter 只有 `name`/`description`。重叠面：与 `api-typings` 无重叠，与官方文档高度重叠
（它本身就是文档的 skill 化），价值在于把分散在十几页文档里的迁移决策压成一张差异表。新鲜度 1 是它唯一的弱项。

**dcloudio/uni-app `docs/`（14）.** 仓库内 `docs/` 是从 gitcode 的 unidocs 同步过来的（文件头有
`GENERATED BY docs-sync` 与 hash），但落在 Apache-2.0 仓库里，可 merged。`docs/compiler/platform.md`
390 行，把条件编译的全部平台常量、三种注释语法、两类语法陷阱（JSON 尾逗号、重复 import）讲全了。
最有价值的一句是未定义平台名时的降级行为——这是「构建成功但发错分支」这类事故的唯一成因说明。

**NervJS/taro（13）.** 仓库本身是 monorepo，文档在独立站点；能 merged 的是它的行为本身。本机
`taro init`（4.2.1，React + Webpack5 + Sass）生成了 24 个文件，`config/index.ts`、`src/app.config.ts`、
`package.json` 的 11 个 `build:*` 脚本都是实测产物。`--framework` 不是 4.2.1 的 flag（只有
`--name/--description/--typescript/--build-es5/--npm/--template-source/--clone/--template/--css/--autoInstall`），
且 `--npm npm`、`--css none` 都会被 Rust 侧枚举拒绝——非交互脚手架文档与实现不一致，这条记在备注。

**TencentCloudBase/CloudBase-AI-Toolkit（11）.** 223 行 SKILL.md，`description` 写得很完整，但正文的
「Activation Contract → Then also read」把七成路由指向 `../auth-wechat-miniprogram`、
`../cloudbase-document-database-in-wechat-miniprogram`、`../cloudbase-wechat-integration` 等兄弟 skill，
本身不自足；规范条款集中在 Nightly DevTools 的 `wechatide` CLI 与消息推送/客服消息，两者都在本 skill 范围外。
在范围内的条款（`project.config.json` 先读、页面文件四件套齐全、`miniprogram-ci` 作为兜底）没有独有信息。

**sonofmagic/skills（11）.** `weapp-vite`、`wevu`、`weapp-tailwindcss` 三组，写作质量不错（`wevu-best-practices`
里「小程序路由栈不提供标准前进语义，`router.forward()` 返回预期的 aborted failure，不应当按浏览器 bug 处理」
这类条目是真陷阱）。但这些结论都绑在作者自己的运行时上，且 `weapp-tailwindcss-setup` 里连
「当前包 manifest 的 Node engine 是 `^22.18.0 || >=24.11.0`」这种包版本细节都写进了规则，腐化速度太快。

**Sun-sunshine06/miniprogram-skills（8）.** 6 个 skill，`miniapp-official-scaffold-alignment` 的
「Core Rules」有一条值得一提——"Write 'not yet specified' instead of inventing missing spec details"——
但那是通用 agent 纪律，不是小程序知识。其余是脚手架清单。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | `setData` 的主要代价是什么 | (a) 业界通识 + 基线模型：跨线程 JSON 序列化，代价 ∝ payload 字节数；(b) 官方《合理使用 setData》：影响因素依次是「调用组件的 Shadow 树总节点量」和「更新的数据量」，**前者影响比后者更大** | 采 (b)，并在 SKILL.md `## Read first` 里显式点名 (a) 是反的 | 官方厂商 > 社区；且 (b) 有《数据更新策略》的算法说明作机制支撑（虚拟树更新是对整棵 Shadow 树的深度优先遍历） |
| 2 | 「把多次 setData 合并成一次」是不是普适优化 | (a) 官方性能页：「通过组合更新等方式，对连续的 setData 调用尽可能的进行合并」；(b) 官方《数据更新策略》：绑定映射表更新只在「单独更新一个数据字段」且该字段不被 `wx:if`/`wx:for`/`let:` 及其子孙使用时才启用，否则退回全树遍历 | 两条都写，并给出判据：字段已被 `wx:if`/`wx:for` 用到、或本来就要改多个字段 → 合并；两个独立的纯插值字段 → 分开各走快路径；只是怕中间态被看见 → 用 `groupSetData` | 同为官方、无新旧之分，因此不裁掉任何一条，改为写清各自成立的前提。SKILL.md 规则 2 与 `references/data-updates.md`「What this means for batching」即此裁决 |
| 3 | `setData` 是同步还是异步 | (a) `api-typings` 的 `setData` 注释：「将数据从逻辑层发送到视图层（异步），同时改变对应的 `this.data` 的值（同步）」；(b) 官方《高级数据更新方法》：「`setData` 对 WXML 模板的更新是**同步**的（除了在数据监听器内被调用时）」 | 写成：在 glass-easel 组件框架下，模板更新同步完成，返回后即可访问组件树与节点信息；在数据监听器内等价于 `updateData`。不笼统说「setData 是异步的」 | 更新 > 更旧：(b) 在组件框架章节，描述的是 glass-easel 的现行语义；(a) 的注释沿用 WebView/exparser 时代的跨线程叙述。两者描述的不是同一件事，因此加框架限定而不是二选一 |
| 4 | 原生组件是否还需要 `cover-view` 覆盖 | (a) 大量社区文章与基线模型：原生组件层级最高，`z-index` 无效，必须用 `cover-view`；(b) 官方《原生组件说明》：「当前所有原生组件（除 input 组件 focus 状态）均已支持同层渲染」「除事件相关，同层渲染下已无以下限制」，`cover-view` 组件页建议改用 `view` | 采 (b)。正文写「同层渲染已覆盖除聚焦态 input 外的全部原生组件，`cover-view` 只保留给 `bindrendererror` 触发后的降级路径」 | 官方现行文档 > 社区旧文。这条同时被写进评测场景 3 |
| 5 | 同层渲染解除了哪些限制、没解除哪些 | 官方文档同页给出两份清单，一份标注「同层渲染下已无以下限制」，一份没有 | 事件相关限制（只支持 `bindeventname`、不支持 `catch`/`capture`）、CSS 限制（`position: fixed`、CSS 动画、祖先 `overflow: hidden` 裁剪）、`picker-view` 内不可用、遮挡 vConsole、工具用 web 组件模拟 —— 这些全部保留 | 文档原文的括注范围；不做推断 |
| 6 | 分包体积上限到底是多少 | (a) 基线模型两次给出「整包 20MB」；(b) 官方《分包加载》：「整个小程序所有分包大小不超过 30M（服务商代开发的小程序不超过 20M）；单个分包/主包大小不能超过 2M」 | 采 (b)，并在 `ci-testing-release.md` 里把 `__FULL__`/`__APP__`/分包 三种 `name` 与各自的上限对齐 | 官方文档；(a) 把服务商特例当成了通例 |
| 7 | `wx:key` 是否应当无条件添加 | (a) 通识：列表必须加 `wx:key`；(b) 官方 glass-easel skill：仅追加/尾部删除的列表**省略 key** 可以启用更快的比较子算法；重排、中间插删、含状态子组件时必须加 | 采 (b)，写成条件式规则，并保留「重复 key 会被加后缀且有额外开销」「index 作 key 在移动时等于没加」两条 | 官方 skill；且与 `spliceArrayDataOnPath` 的列表更新建议是同一篇 |
| 8 | glass-easel 是不是只能配 Skyline | (a) Skyline 文档：选用 Skyline 必须选用 glass-easel；(b) dcloudio/uni-app `docs/mp/mp-weixin-glass-easel.md`：「从微信小程序基础库版本 3.8.12 开始，glass-easel 组件框架提供了对 WebView 渲染引擎的支持」 | 两条都成立且不冲突：渲染引擎依赖组件框架，反向不依赖。正文写成「Skyline 需要 glass-easel；glass-easel 不需要 Skyline（WebView 自 3.8.12 起支持）」 | (b) 带明确版本分界，且来自 Apache-2.0 的官方仓库文档，可直接引用 |
| 9 | `TencentCloudBase/awesome-miniprogram-skills` 作主干 | 路线图把它列为主干上游 | 推翻：**内容裁决** REJECT，改以 `wechat-miniprogram/*` 官方组织的四个仓库为主干 | 实读仓库树：`skills/*/cloudbaserc.json` + `cloudfunctions/` + `mcp.json`，是 CloudBase 云函数示例小程序集合，与本 skill 的排除项直接冲突 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `wx-api-typings` | wechat-miniprogram/api-typings @ 6092df91 | merged | `wx.*`/Page/Component 的签名、硬上限与版本门；SKILL.md 里标 `[verified]` 的条目基本都源于此 |
| `wx-glass-easel` | wechat-miniprogram/glass-easel @ 4aeef5fb | merged | 高级数据更新 API、observer 语义、深拷贝选项、`wx:key` 条件式规则、slot 模式、`virtualHost` |
| `wx-skyline-skills` | wechat-miniprogram/skyline-skills @ 050bb071 | merged | Skyline 配置三件套、WebView 差异表、局部滚动布局、迁移粒度 |
| `wx-miniprogram-simulate` | wechat-miniprogram/miniprogram-simulate @ f6044fd0 | merged | 组件单测流程与其能力边界 |
| `dcloud-uni-app` | dcloudio/uni-app @ 8d4be0f3 | merged | 条件编译语法与常量、未定义平台的降级行为、mp-weixin 的 glass-easel 开关与 3.8.12 分界 |
| `taro` | NervJS/taro @ d6d69e30 | merged | Taro 工程结构、构建目标、`designWidth`/`pxtransform` 契约（本机实跑） |
| `wx-official-docs` | developers.weixin.qq.com | reference | 数据更新算法、同层渲染现状、路由与生命周期顺序、分包体积、启动流程、授权与隐私（**专有，只取证不复制**） |
| `miniprogram-ci` | npm miniprogram-ci 2.1.31 | reference | upload/preview/packNpm 选项形状与 robot 范围（**无 LICENSE 文件 → NONE**） |
| `wx-ai-mode-skills` | wechat-miniprogram/ai-mode-skills @ 9bd1f25a | reference | 内容裁决降级，仅用于确认覆盖面 |
| `cloudbase-ai-toolkit` | TencentCloudBase/CloudBase-AI-Toolkit @ 3ec840b5 | reference | 内容裁决降级，仅作项目结构/CI 路由的交叉校验 |
| `sonofmagic-skills` | sonofmagic/skills @ e0e4e51e | reference | 内容裁决降级，仅在项目使用非官方工具链时作交叉校验 |

## 基线缺口

无 skill（`uv run tools/run_evals.py wechat-miniprogram --baseline`，claude-opus-5 · medium）时，各场景未达成的
`expected_behavior`。**注意：基线 agent 可以联网**，场景 2、3 它确实抓取了官方文档，所以整体基线很强；
下表只记真实未达成项。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 setData/双线程 | 官方代价排序（调用组件的 Shadow 树节点量 > 更新数据量） | 基线把 `onPageScroll` 轮询排第 1、列表无虚拟化排第 2、全量回写排第 3。定位准，但**始终没有说出官方的因子排序**，也没有把「拆行组件」作为首要手段，而是推荐 `recycle-view` 虚拟化 |
| 1 | 绑定映射表快路径的启用条件 | 完全缺失。而且基线在同一份答复里建议「js:20/24 两次 setData 可合并」——按官方策略这恰好会让两次单字段更新失去快路径 |
| 1 | `Page` 构造参数中的自定义数据被逐实例深拷贝 | 基线指出了 `CATEGORY_TREE.flatten()` 在模块求值期执行（另一回事），但没有提深拷贝这条 |
| 1 | `setUpdatePerformanceListener` / 1024kB 上限 / `pureDataPattern` | 三者均未出现。基线给的是「按建议顺序改」，没有给测量手段 |
| 2 分包与配置 | 具体体积上限 | 未给出 2MB/30MB。反而编造了「同一分包内页面共享 2M 预下载额度，打包时校验」（见下节） |
| 2 | `lazyCodeLoading` 打开后全局 `usingComponents` 成为每页依赖 | 未提。基线把全局组件的问题归到「独立分包依赖主包」上（也对，但不是这条） |
| 3 原生组件 | CSS 限制清单（CSS 动画 / 祖先 `overflow: hidden` 裁剪 / `picker-view` 内不可用 / 遮挡 vConsole） | 只提了 `position: fixed` |
| 3 | `animation="{{dockAnim}}"` 吸底栏的动画机制 | 完全没有涉及夹具里的这一处 |
| 4 CI | `__FULL__` 的上限 | 基线明确写「`__FULL__` 是整包（上限 20MB）」——错，应为 30MB（20MB 仅限服务商代开发） |
| 5 负例 | — | 全部达成，未读本 skill（基线模式本就无 skill，此项在有 skill 组才有意义） |

### 基线胡编内容（原样记录）

这是本题材最有价值的一类缺口，按要求原文抄录：

1. 场景 2，关于分包预下载：

   > 同时官方限额：**同一分包内页面共享 2M 预下载额度，打包时校验** —— 两个包一起挂在首页，很容易在打包阶段被额度校验拦下。

   官方《分包预下载》没有这条规则；「2M」是单包体积上限，被安到了「预下载额度」上，并凭空加了
   「打包时校验」。

2. 场景 3，关于同层渲染的起始版本：

   > map 自 2.7.0、video 自 2.4.0 起同层。

   官方文档里这两个数字是别的意思：2.7.0 是「支持在样式中声明 z-index 指定**原生组件之间**的层级」，
   2.4.4 是「基础库 2.4.4 以下版本，原生组件不支持在 scroll-view、swiper、movable-view 中使用」。
   基线把两个无关的版本号重组成了「某组件自某版本起支持同层渲染」这样一条不存在的分界。

3. 场景 4，关于整包上限：

   > `__FULL__` 是**整包**（上限 20MB），2MB 是**单包**上限。

   单包 2MB 正确，整包上限是 30MB；20MB 只适用于服务商代开发的小程序。基线把特例当成了通例。

4. 场景 3 末尾的一条未经核实的推断，以断言形式给出：

   > 另有一条与 video 相关的坑：若页面或全局开了 `enablePassiveEvent`，video 可能出现非预期表现。

三条事实性错误全部集中在**数字与版本分界**上，这正好印证了「中文生态训练数据稀疏 → 结构对、数字错」
的假设，也决定了本 skill 的 Core rules 必须把每个数字与版本门写死。

评测未改写量规：基线并非零区分度，上表有 9 条真实未达成项，题目与夹具一字未改，也未重跑。

## 评测结果

模型固定 claude-opus-5 · medium（`tools/run_evals.py` 默认），两组同模型。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 setData/双线程 | claude-opus-5:medium | 无（baseline） | false | 5/9 | 见基线缺口表 |
| 2 app.json/分包 | claude-opus-5:medium | 无（baseline） | false | 6/8 | 含 1 条编造限额 |
| 3 原生组件层级 | claude-opus-5:medium | 无（baseline） | false | 5/7（另 1 条部分） | 含 1 条编造版本分界 |
| 4 CI 上传 | claude-opus-5:medium | 无（baseline） | false | 7/8 | 含 1 条错误上限（20MB） |
| 5 负例（Vue/Vite Web） | claude-opus-5:medium | 无（baseline） | false | 3/3 | 基线模式无 skill 可读 |
| 1 setData/双线程 | claude-opus-5:medium | 有 | **true** | 8/9（第 8 条部分） | 逐条见下 |
| 2 app.json/分包 | claude-opus-5:medium | 有 | **true** | 7/8（第 8 条部分） | 逐条见下 |
| 3 原生组件层级 | claude-opus-5:medium | 有 | **true** | 6/7（第 3 条部分） | 逐条见下 |
| 4 CI 上传 | claude-opus-5:medium | 有 | **true** | 8/8 | 逐条见下 |
| 5 负例（Vue/Vite Web） | claude-opus-5:medium | 有 | **false** | 3/3 | 负例通过：未读本 skill |

逐条判定（只列有无 skill 之间发生变化的行为）：

| 场景 | 行为 | 无 skill | 有 skill |
|---|---|---|---|
| 1 | 官方代价排序：调用组件的 Shadow 树节点量 > 更新数据量，拆行组件优于 payload diff | 未达成 | **达成**——开篇即给出①②两因子与「①比②更重要」，并把「拆 `<feed-row>`」列为第 1 步、手写 diff 判为驳回 |
| 1 | 绑定映射表快路径条件（单字段 + 不喂 `wx:if`/`wx:for`/`let:`） | 未达成 | **达成**——且据此把「一次发 6 个字段」「每秒改 2 个字段」单独列为问题 |
| 1 | `Page` 构造参数非函数字段逐实例深拷贝 | 未达成 | **达成**（L16-17 条目） |
| 1 | 测量手段 `setUpdatePerformanceListener` | 未达成 | **部分达成**——列在「未执行的检查」里并要求改完对比，但正文没写 1024kB 上限 |
| 2 | 具体体积上限 2MB/包、30MB/总 | 未达成（编造「2M 预下载额度」） | **达成**（列在未执行检查中，数字正确） |
| 2 | `lazyCodeLoading` 打开后全局 `usingComponents` 成为每页依赖 | 未达成 | **达成**（L52-58 条目） |
| 2 | 独立分包语义 | 部分（getApp/app.wxss） | **部分**——仍只覆盖 `getApp({allowDefault:true})` 与 `app.wxss`，未提「不能定义 App」「onLaunch 延后」 |
| 3 | `animation="{{dockAnim}}"` 吸底栏的动画机制 | 未达成（完全未涉及） | **达成**——指出逐帧跨线程驱动、Skyline 下已被 worklet 取代，改 WXSS transition |
| 3 | 原生组件 CSS 限制清单 | 部分（只提 fixed） | **部分**（仍只提 fixed；CSS 动画/祖先 `overflow: hidden` 未提） |
| 4 | `__FULL__` 的上限 | 未达成（写成 20MB） | **达成**——「`__FULL__` 上限是 30MB，2MB 是单包上限」，并改为逐条校验 |
| 1–4 | 编造的数字与版本分界 | 4 处 | **0 处** |

结论：**通过**。至少一条（实际是 7 条）基线未达成的行为在有 skill 时达成，其中三条是基线**答错**而非
漏答——分包总上限、`__FULL__` 上限、同层渲染的版本分界，有 skill 后全部纠正，且新增答复中没有出现
任何编造的数字或版本门。负例 `skill_read == false`，未被误触发。

仍未达成的两条（场景 2 的独立分包完整语义、场景 3 的 CSS 限制清单）都写在 references 里而没被读到：
`subpackages-startup.md` 与 `native-components.md` 各有一节覆盖它们，但 SKILL.md 的 Core rules 12、15
已是压缩版，模型选择不展开。这属于「信息在库里、本轮没被检索」，不改判为达成。

## 备注

### 未验证清单（全部标 `[official]`，不是 `[verified]`）

本机没有微信开发者工具（仅 Windows/macOS），也没有真机，因此以下**全部未实测**，
SKILL.md 与 references 中一律标 `[official]` 并注明出处：

1. 数据更新算法的实际性能表现（虚拟树更新 vs 绑定映射表更新的耗时差）——只核对了算法选择条件的文字规则。
2. `setUpdatePerformanceListener` 的返回字段与量级。
3. 同层渲染的真机行为、`bindrendererror` 的触发条件与失败率。
4. 原生组件的 CSS 限制（`position: fixed` / CSS 动画 / 祖先 `overflow: hidden`）。
5. Skyline 的全部内容：三件套配置的编译期报错文案、`rendererOptions` 各项的实际效果、
   worklet 动画、`scroll-view type="list"` 的按需渲染、`wx.preloadSkylineView` 的收益。
6. 分包体积上限与 `preloadRule` 的实际拦截行为——数字取自官方《分包加载》，未上传验证。
7. 启动流程各阶段耗时、按需注入/用时注入的实际收益、初始渲染缓存。
8. 页面栈十层上限、`switchTab` 生命周期表、悬垂页面行为。
9. 登录、授权 scope、`wx.openSetting`、隐私协议接口的真机行为（需要真实 appid 与用户）。
10. `miniprogram-ci` 的**运行时行为**：upload / preview / packNpm 都需要真实 appid 与上传密钥，
    未执行。已验证的只是 2.1.31 发布包里 `dist/@types/**/*.d.ts` 声明的 API 形状
    （`IUploadOptions`、`IPreviewOptions`、`ICreateProjectOptions`、`ICompileSettings`、
    `getLatestVersion`、`cloud.*`、以及 `ci` 导出里**没有** `submitAudit`）。
11. `miniprogram-simulate` 的 `load/render/attach` 未实跑（需要一个真实小程序项目目录）。
12. uni-app 的条件编译行为未实跑（需要 HBuilderX 或 uni CLI 工程）；结论取自
    `dcloudio/uni-app` 仓库内的官方文档。
13. 审核驳回原因一节：只写了「由代码导致、可在仓库里查出来」的那一类，且未经真实提审验证。

### 已实测（`[verified]` 的依据）

| 实测项 | 手段 | 结果 |
|---|---|---|
| `wx.*` / Page / Component 声明 | `npm i miniprogram-api-typings@5.2.3`，逐条 grep `types/wx/*.d.ts` | setData 1024kB 上限、`undefined` 被跳过、storage 1MB/10MB、页面栈十层、code 五分钟、`renderer: 'webview' \| 'skyline'`、`ComponentOptions` 六种 `styleIsolation`、`pureDataPattern`(2.8.2)、`virtualHost`(2.11.2)、`groupSetData`(2.4.0)、组件 `lifetimes` 全集 |
| glass-easel 数据更新 API | `npm i glass-easel@1.2.0`，grep `dist/glass_easel.d.ts` | `replaceDataOnPath` / `spliceArrayDataOnPath` / `applyDataUpdates` / `groupUpdates` / `updateData` / `setData` 六者签名确认；`setData` 注释确认「observer 内推荐 updateData」 |
| miniprogram-ci API 形状 | `npm i miniprogram-ci@2.1.31`，读 `dist/@types/**` | `robot?: number`、`privateKey` vs `privateKeyPath`、`ICompileSettings` 十二个键、`IUploadResult.subPackageInfo`、`qrcodeOutputDest` 必填、导出表中无 `submitAudit`；包内**无 LICENSE 文件** |
| Taro 工程产物 | `npx taro init`（4.2.1，React + Webpack5 + Sass） | 24 个文件的目录结构、`defineAppConfig`/`definePageConfig`、11 个 `build:*` 脚本、`designWidth: 750` + `deviceRatio` + `mini.postcss.pxtransform`、`compiler: 'webpack5'` |
| 各上游许可 | `gh api repos/<r>/contents/LICENSE \| base64 -d` 逐个实读 | 见候选表「许可（实读结论）」列。**NervJS/taro 的 API `spdx_id` 是 NOASSERTION，正文是 MIT** —— 与 `vercel/ai`、`pytorch/pytorch` 同一类坑，第三次遇到 |
| 官方文档许可 | 浏览器渲染后读页脚 | `Copyright © 2012-2026 Tencent. All Rights Reserved.` → Proprietary → reference |

### 工具与流程上的观察

- `taro init` 的非交互 flag 与实现不一致：`--framework` 不存在（4.2.1 的 `--help` 无此项），
  `--npm npm` 触发 `value "npm" does not match any variant of enum NpmType`，
  `--css none` 触发 `value "none" does not match any variant of enum CSSType`。最终用 PTY 交互完成。
  下次同步 `cross-platform.md` 时如果要重跑脚手架，直接走 PTY。
- 微信官方文档站是 Vue SSR + 懒渲染，`curl` 只能拿到首屏几百字（`runtime_setData.html` 只出到
  「最有效…」就截断了）。必须用浏览器渲染后取 `#docContent` 的 `innerText`。
- 文档站有一批路径已迁移：`framework/view/data-update.html`、
  `framework/component/native-component.html` 都 404；现行路径分别是
  `framework/component-framework/data-updates.html` 与 `component/native-component.html`。
  下次同步先从侧边栏抓链接再取页面。

### 未来同步时要盯的上游

- `wechat-miniprogram/api-typings`：版本跟基础库走，`CHANGELOG.md` 会列新 API 与新版本门。
- `wechat-miniprogram/glass-easel`：`glass-easel-skills/` 是新增目录，本轮首次使用；它的
  `best-practices.md` 变动直接影响 `data-updates.md` 与 `render-performance.md`。
- `wechat-miniprogram/skyline-skills`：推送已 3 个月，若再半年不动就要降为 reference，改以官方文档取证。
- 同层渲染的状态是本 skill 最容易过期的一条。每次同步都要重读
  `component/native-component.html`，确认「除 input focus 外全部支持」这句还在。
- `dcloudio/uni-app` 的默认分支是 `uni-app-x`（不是 `main`），`check_upstream.py` 的 `ref` 已按此填写。

### 放弃的方向

- 没有为本 skill 写 `scripts/`。可运行的东西只有两类：一是 `tsc` 对着 `miniprogram-api-typings`
  做检查，二是 `miniprogram-ci` 的上传脚本——前者是一行命令，后者需要真实密钥且形态强依赖项目的 CI，
  写成通用脚本只会变成一份必须被改掉的模板。两者都以命令和代码片段写进 SKILL.md 与
  `ci-testing-release.md`。
- 没有收 `didi/mpx` 与 `wechat-miniprogram/computed`：分数都够，但都会让「一个默认方案 + 一个逃生口」
  退化成选型清单。理由见候选表第 20、21 行。
