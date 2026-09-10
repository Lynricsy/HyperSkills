# frontend-design 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-10（种子调研）
- 复核日期：2026-09-10（本次全部重新核对，见下）
- 检索途径：
  - `web_search`：`"frontend design skill SKILL.md github"`、`"web interface guidelines skill"`、`site:skills.sh ui design`
  - <https://www.skills.sh>
  - addyosmani/agent-skills、antfu/skills、JetBrains/skills（三个聚合/镜像仓库，用于反查原始源）
  - 领域官方组织仓库：`anthropics/`、`vercel-labs/`、`GoogleChrome/`、`w3c/`
- GitHub API 核对方式：`https://api.github.com/repos/<owner>/<repo>` 取 `stargazers_count` / `pushed_at` / `license.spdx_id`；
  许可以仓库根 `LICENSE` 为主，`anthropics/skills` 无仓库根许可，改读 **每个 skill 目录自己的 `LICENSE.txt`**。
- 规范事实核对：直接读 <https://www.w3.org/TR/WCAG22/> 正文与 <https://web.dev/articles/vitals>，不采信任何上游 skill 的转述。

### 本次复核的三项关键结论

1. **`anthropics/skills/skills/frontend-design/LICENSE.txt` 是 Apache License 2.0，不是 docx/pptx/xlsx/pdf 那份专有文本。**
   （读取 `raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/LICENSE.txt`，开头为
   `Apache License / Version 2.0, January 2004`，10 174 字节。）
   因此计划中的应急方案（改为 `relation: reference`）**不触发**，本条按 `merged` 处理。
2. **`GoogleChrome/modern-web-guidance` 的 `unverified` 标记已消除**：仓库存在，2 166★，`pushed_at` 2026-09-07，
   `license.spdx_id = Apache-2.0`。CLI 也在本机实测通过（见下方「深度审查」）。
3. **`emilkowalski/skills`（36 568★、2026-08-21、MIT）与 `leonxlnx/taste-skill`（85 902★、2026-08-24、MIT）
   两个 `unverified` 候选核实通过**，均在 6 个月推送窗口内且许可明确，因此计划中「放弃动效上游」的应急方案不触发。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。
Stars / 推送 / 许可均为 2026-09-10 当日 GitHub API 值。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | anthropics/skills `skills/frontend-design/` | https://github.com/anthropics/skills | 175538 | 2026-09-03 | Apache-2.0（skill 内 `LICENSE.txt`，本次核实） | 视觉方向、排版、反 AI 俗套、UX 文案 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | 生态里唯一把「AI 味」写成可判别特征簇的文档；两遍流程（设计计划 → 复核 → 构建 → 自评）可直接落成 workflow |
| 2 | vercel-labs/web-interface-guidelines `command.md` | https://github.com/vercel-labs/web-interface-guidelines | 858 | 2026-08-18 | MIT | ~150 条可机械检查的 UI/a11y/perf/i18n 规则 + `file:line` 输出契约 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | 本领域规则密度最高的单一文件；每条都能对着代码行判定 |
| 3 | GoogleChrome/modern-web-guidance | https://github.com/GoogleChrome/modern-web-guidance | 2166 | 2026-09-07 | Apache-2.0 | Baseline 推理、现代 CSS/HTML 平台特性检索（npm CLI） | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged) | 唯一覆盖 Baseline 与回退协商的上游；已发布 npm 包，可移植不腐坏；本机 143 条指南实测可检索 |
| 4 | W3C WCAG 2.2 | https://www.w3.org/TR/WCAG22/ | n/a | W3C Recommendation | W3C Document License | a11y 规范正文 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE (merged, kind=docs) | 所有 a11y 数值的裁决方；纠正了两处上游转述错误 |
| 5 | addyosmani/agent-skills `skills/frontend-ui-engineering/` | https://github.com/addyosmani/agent-skills | 93313 | 2026-09-08 | MIT | AI 默认→生产质量对照表、状态选择表、WCAG 模式、骨架屏/乐观更新 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE (merged) | 8 行「AI 默认 → 为什么是问题 → 生产质量」对照表与 Anthropic 的俗套簇几乎不重叠，可叠加 |
| 6 | addyosmani/agent-skills `skills/performance-optimization/` | ↑ | 93313 | 2026-09-08 | MIT | Core Web Vitals、measure-first 五步、瓶颈分诊树 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE (merged) | CWV 阈值抽查与 web.dev 完全一致；「先测量再改」的流程是本 skill 性能章的骨架 |
| 7 | emilkowalski/skills `skills/review-animations/` + `STANDARDS.md` | https://github.com/emilkowalski/skills | 36568 | 2026-08-21 | MIT | 动效评审：频率表、easing 决策序、时长表、物理性、可中断性 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE (merged) | Sonner / Vaul 作者；把「该不该动」写成频率决策表，是其他上游都缺的一层 |
| 8 | emilkowalski/skills `skills/emil-design-eng/` | ↑ | 36568 | 2026-08-21 | MIT | 组件设计与 UI 打磨哲学 | 2 | 3 | 2 | 3 | 2 | 11 | INCLUDE (merged, 部分) | 半数内容是 React 组件库实践，与 `react` skill 重叠；只取动效与打磨判断 |
| 9 | antfu/skills `skills/antfu-design/`（+ 5 个 references） | https://github.com/antfu/skills | 5870 | 2026-06-23 | MIT | 语义 token、暗色对等、三拨盘、反俗套、微交互、偏差纠正 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE (merged，仅框架无关部分) | UnoCSS 耦合的一半（`@unocss-include`、Attributify、shortcuts 配置）不取；取拨盘、反俗套、偏差纠正、微交互 |
| 10 | leonxlnx/taste-skill `skills/taste-skill/` | https://github.com/leonxlnx/taste-skill | 85902 | 2026-08-24 | MIT | 反俗套 landing/portfolio 框架：brief inference、三拨盘、GSAP 骨架 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE (merged，仅拨盘与 design read 语义) | 三拨盘与 design read 的**源头**（antfu 三份 reference 都在末尾署名它）。87 KB 单文件、GSAP 耦合、范围限于 landing/portfolio，正文不取；只取语义并重写 |
| 11 | nextlevelbuilder/ui-ux-pro-max-skill `references/{quick-reference,pro-rules}.md` | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | 126547 | 2026-09-10 | MIT | 10 类共 ~230 条 UX 指南（含 119 条核心） | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE (merged，仅两份 markdown) | 抽查 4 条 WCAG 相关规则（2.5.8 AA=24×24、2.4.11 AA、2.4.13 AAA、44pt=Apple）**全部标注正确**，是唯一没搞错触控目标的社区上游；但整体是 `${CLAUDE_PLUGIN_ROOT}` + CSV 搜索运行时，不 vendor |
| 12 | wshobson/agents `plugins/ui-design/skills/accessibility-compliance/` | https://github.com/wshobson/agents | 39546 | 2026-09-07 | MIT | WCAG 2.2 泛化清单 + `references/details.md` | 1 | 3 | 1 | 1 | 2 | 8 | REJECT（仅作对照） | 内容是「用语义 HTML」这类模型已知的通识，无行级可判定规则；且触控目标事实混淆（见「冲突与裁决」R2）。a11y 由候选 2 + 4 覆盖，无需合入 |
| 13 | vercel-labs/agent-skills `skills/web-design-guidelines/` | https://github.com/vercel-labs/agent-skills | 31025 | 2026-08-28 | MIT（frontmatter 声明，仓库无根许可） | 40 行分发器，指示 agent 去 WebFetch Vercel 指南 | 3 | 3 | 0 | 3 | 1 | 10 | REJECT（改用其目标） | 独立内容近乎为零，价值全在它指向的候选 2；且它要求 `WebFetch`，被本仓库 `docs/skill-standard.md` 1.3 节禁用 |
| 14 | anthropics/skills `skills/canvas-design/` | https://github.com/anthropics/skills | 175538 | 2026-09-03 | 未读（本 skill 不需要） | 海报/画布设计 + ~40 个 OFL 字体 | 3 | 3 | 3 | — | — | — | REJECT（范围外） | 印刷/画布而非 web UI；且捆绑数十 MB 字体，属于未来 `design-assets` 主题 |
| 15 | anthropics/skills `skills/web-artifacts-builder/` | ↑ | 175538 | 2026-09-03 | 未读（本 skill 不需要） | React+Tailwind+shadcn artifact 脚手架 + `.sh` 脚本 | 3 | 3 | 2 | — | — | — | REJECT（范围外） | 绑定 Claude artifact 运行时；脚手架惯例属于 `react` skill |
| 16 | Lombiq/Tailwind-Agent-Skills `tailwind-4-docs` | https://github.com/Lombiq/Tailwind-Agent-Skills | 70 | 2026-04-09（分支 `dev`） | BSD-3-Clause | Tailwind v4 文档本地快照 + 索引 | 1 | 1 | 1 | 1 | 2 | 6 | REJECT | 70★、5 个月未更；且形态是文档快照——快照类 skill 的陈旧是致命的，合入即在仓库里固化过期文档 |
| 17 | JetBrains/skills `ui-website-style/` | https://github.com/JetBrains/skills | 342 | 2026-06-29 | 无（NONE） | 某私有 dashboard + Docusaurus 站点的设计系统 | 1 | 2 | 3 | 3 | 0 | 9 | REJECT | token / 组件名硬编码到一个私有代码库，作为通用 skill 无意义（作为「仓库内设计系统 skill」的模板倒是好例子） |
| 18 | JetBrains/skills 其余项（`modern-web-guidance/`、`vercel-labs-web-design-guidelines/`、`react-best-practices/`、`vue-*`、`figma/`、`theme-factory/`） | ↑ | 342 | 2026-06-29 | 无（NONE） | 候选 2/3/13 及 React/Vue 上游的镜像 | 1 | 2 | — | — | 0 | — | REJECT（重复镜像） | 镜像仓库；一律从原始源同步（候选 3 的 frontmatter 本身就署名 Google Chrome） |
| 19 | antfu/skills `skills/web-design-guidelines/`、`skills/vue-best-practices/` | https://github.com/antfu/skills | 5870 | 2026-06-23 | MIT | 候选 13 与 vuejs-ai 的 vendored 副本 | 2 | 2 | — | — | 2 | — | REJECT（重复镜像） | 同上，同步原始源 |
| 20 | PyModel/react-frontend-skills | https://github.com/PyModel/react-frontend-skills | 3 | 2026-09-10 | MIT | 18 个 React 19 / Next 16 / Tailwind v4 / shadcn skill | 0 | 3 | 1 | 0 | 2 | 6 | REJECT | 3★ / 1 fork / 0 watcher 而 README 高度 SEO 化；匿名作者、无任何评测证据，正确性无法抽查（正确 0 → 按量表直接 REJECT）；且全是版本快照，会腐坏 |
| 21 | Impertio-Studio/{shadcn,TailwindCSS}-Claude-Skill-Package、grixalai/shadcn-ui__skill、supercent-io/skills-template、magnus919/agent-skills、gohypergiant/agent-skills、EnderPuentes/ai-agent-skills、gocallum/nextjs16-agent-skills、fusengine/agents | — | 22–302（skills.sh 报数，未经 API 核对） | 未核对 | 未核对 | 各类 shadcn / tailwind / nextjs / a11y skill | 0 | — | 1 | 0 | 0 | ≤4 | REJECT | 单作者小仓库、许可与新鲜度不可核；多为框架版本快照。视觉/UX 层已被候选 1/2/5/9 完全覆盖 |
| 22 | vercel-labs/next-skills | https://github.com/vercel-labs/next-skills | n/a | 已废弃（README 声明迁移） | — | — | — | 0 | — | — | — | — | REJECT | 上游自己声明迁移到 `vercel/next.js`；且属于 `react` skill 范围 |

## 深度审查

### 1. anthropics/skills `frontend-design`（INCLUDE, merged）

- **结构**：扁平 2 文件（`SKILL.md` + `LICENSE.txt`），约 9.4 KB 散文，无 `references/`、无 `scripts/`。
- **frontmatter**：`name` / `description` / `license: Complete terms in LICENSE.txt`。agent 无关，无工具声明。
- **许可（关键）**：`LICENSE.txt` = **Apache-2.0**（本次实读确认）。与 `skills/{docx,pptx,xlsx,pdf}/LICENSE.txt`
  那份「禁止复制、衍生、再分发」的专有文本不同。→ 可 `merged`。
- **质量**：生态里最强的「不要产出通用 UI」文档。不是空话，它点名了五个具体的生成式设计特征簇：
  ① 暖奶油底（近 `#F4F1EA`）+ 高对比衬线 display + 陶土色强调（近 `#D97757`，恰是 Claude 自家交互色，出现即为 tell）；
  ② 近黑底 + 单一亮酸绿/朱红强调；③ 报纸大报式 hairline 分隔 + 零圆角 + 密集分栏；
  ④ SaaS 卡片套件（内容切成同尺寸圆角卡、所有元素同一圆角、同一 `rgba(0,0,0,.1)` 灰阴影、渐变洗底当装饰）；
  ⑤ 模板 chrome（每个标题上方 tracked ALL-CAPS eyebrow、`A · B · C` 中点串、`WORD — fragment` 间隔破折号标签、
  用 `#0B0B0B`/`#111` 冒充黑、小数据标签用等宽、按钮/链接文字后缀 `→`）。
  还给了两遍流程、一条真实的 CSS 特异性告警（`.section` 与元素选择器互相抵消导致段间距失效）、以及完整的 UX 文案章。
- **agent 绑定**：无。
- **重叠**：文案章与候选 2 的 Content & Copy 重叠，但 Anthropic 的是**生成型**（该选什么），Vercel 的是**评估型**
  （该标什么），互补不冲突；俗套清单与候选 5 的 AI 默认表、候选 9 的 anti-slop 在具体项上基本不相交，可叠加。

### 2. vercel-labs/web-interface-guidelines `command.md`（INCLUDE, merged）

- **结构**：单仓库单文件，7.7 KB，14 个规则分节 + 一节 anti-patterns + 输出格式。
- **frontmatter**：是 **command** 形状（`description` + `argument-hint`），不是 skill 形状——重打包时必须补 `name`，
  并去掉 `argument-hint`（本仓库禁用该字段）。正文第一行 `Review these files for compliance: $ARGUMENTS` 是命令占位符，也要去掉。
- **质量**：每一行都能对着代码机械判定：`Icon-only buttons need aria-label`、`Flex children need min-w-0`、
  `Placeholders end with …`、`<img> needs explicit width and height`、模态里 `overscroll-behavior: contain`、
  `Intl.*` 优先于硬编码格式。刻意极简（"sacrifice grammar for brevity"）。
- **agent 绑定**：内容 agent 无关；只有候选 13 的包装器是 Claude 专属（因为它说「用 WebFetch」）。
- **重叠**：Performance / Animation 两节与 `react` skill 的 `rendering-*`/`js-*` 规则同题不同层（CSS/DOM vs React API），
  a11y 节是候选 5、11 的超集且最具体——本 skill 的 review 清单以它为主干。

### 3. GoogleChrome/modern-web-guidance（INCLUDE, merged）

- **结构**：npm 包 + `skills/modern-web-guidance/SKILL.md`；三步用法 `search` → `retrieve` → 核对。
- **frontmatter**：`name` + 多行 `description`（含 trigger / do-not-trigger 清单）。正文有 `MANDATORY`、`MUST` 全大写腔调，
  重写时按本仓库写作规范降调。
- **本机实测**（`[verified]`）：`npx -y modern-web-guidance@latest search "avoid layout shift from images"` 1.9 s 返回
  5 条带 `similarity` 的 JSON；`list` 返回 **143** 条指南，分类分布
  `ui-behaviors 29 / performance 24 / forms 16 / visual-design 16 / css 15 / ui-atoms 10 / js 8 / security 7 / ui-components 7 / built-in-ai 4 / webmcp 3 / accessibility 2 / html 1 / privacy 1`。
- **独有价值**：Baseline 推理与回退策略协商——「Baseline Widely available 默认可直接用；非 Widely available 必须按指南给回退，
  除非用户声明了自定义浏览器支持策略」。以及 `Baseline YYYY` 目标的判定规则（feature 的 "Baseline since" 年份 ≤ YYYY 即满足）。
  这一层没有任何其他上游覆盖，也正是「旧 skill 误导新模型」问题在平台层的解药。
- **注意**：`--skill-version` 旗标用于让 CLI 判断 SKILL.md 是否过期（不匹配则 stderr 警告）。我们**不**固化上游的
  `2026_09_04-7de96777` 值，因为它会随包更新而过期，而本仓库不跟包版本走；正文只写不带该旗标的调用。

### 4. addyosmani/agent-skills（两个 skill，INCLUDE, merged）

- **结构**：`skills/<name>/SKILL.md`（334 / 496 行）+ **仓库级** `references/`（`accessibility-checklist.md`、
  `performance-checklist.md`）。已知移植缺口：按 skill 安装不会带走仓库级 `references/`，所以必须显式单独拉取——本次已拉。
- **frontmatter**：极简（仅 `name` + `description`），agent 无关。
- **质量**：`frontend-ui-engineering` 的 8 行 AI 默认表（紫/靛通吃、渐变过量、`rounded-2xl` 一刀切、通用 hero、
  lorem 式文案、到处超大 padding、库存卡片网格、重阴影）是**调色板/圆角/阴影层**的俗套，与 Anthropic 的
  **构图/排版层**俗套正交；状态选择表（local / lifted / context / URL / server / global）与骨架屏、乐观更新配方都可用。
  `performance-optimization` 的 CWV 阈值（LCP ≤2.5s / INP ≤200ms / CLS ≤0.1）与 web.dev 原文一致，
  五步流程 MEASURE → IDENTIFY → FIX → VERIFY → GUARD 与症状分诊树可直接重写。
- **发现的事实问题**：仓库级 `references/accessibility-checklist.md` 标题写 "WCAG 2.1 AA compliance"，
  其 Content 小节却列 `Touch targets ≥ 44x44px on mobile`。WCAG 2.1 **没有** AA 级触控目标条款，
  44×44 是 2.1/2.2 的 SC 2.5.5 Enhanced（AAA）。本 skill 采用 W3C 原文，不采用这条表述（见 R2）。
- **重叠**：a11y 节是候选 2 的子集；组件架构与状态选择属于 `react` skill 的层，本 skill 只取视觉/UX 层。

### 5. emilkowalski/skills（INCLUDE, merged）

- **结构**：`review-animations/{SKILL.md, STANDARDS.md}`、`emil-design-eng/SKILL.md`（27 KB）、
  另有 `animate/`、`animation-vocabulary/`、`improve-animations/` 等 11 个兄弟 skill。
- **质量**：`STANDARDS.md` 是本领域最具体的动效数值来源，且**先问「该不该动」再问「怎么动」**：
  频率表（每天 100+ 次的操作永不加动效；键盘触发的动作永不加动效）、easing 决策序（进出用 `ease-out`、
  屏内移动用 `ease-in-out`、hover 用 `ease`、恒速用 `linear`；**UI 上永不用 `ease-in`**）、
  时长表（按压 100–160ms / tooltip 125–200ms / 下拉 150–250ms / 模态抽屉 200–500ms，UI 动效上限 300ms）、
  物理性（永不 `scale(0)`，从 `0.9–0.97` 起；popover 从触发点缩放而模态例外保持居中）、
  可中断性（CSS transition 可中途改向，keyframes 会从零重启）、`@starting-style` 无 JS 入场。
- **agent 绑定**：无。少量 React / Framer Motion 专属条目（`useSpring`、`initial={false}`、
  「Framer Motion 的 `x`/`y` 简写不走硬件加速」）——这些归 `react` skill，本 skill 只留框架无关部分。
- **重叠**：与候选 2 的 Animation 节（8 条）、候选 9 的 micro-interactions、候选 11 的第 7 类（26 条）三方重叠；
  Emil 的最深且带数值，冲突时以它为准（见 R3）。

### 6. antfu/skills `antfu-design`（INCLUDE, merged，仅框架无关部分）

- **结构**：`SKILL.md` + 13 个按角色前缀命名的 references（`core-*` / `best-practices-*` / `features-*` / `advanced-*`）。
- **frontmatter**：`name` / `description` / `metadata.author` / `metadata.version`（日期版本 `2026.06.22`）。
- **可取部分**：`core-design-read`（读 brief → 一句 design read → 三拨盘 + Tooling/Marketing 两套基线值）、
  `best-practices-anti-slop`（破折号禁令、`#000`/`#fff` 禁令、Jane Doe 效应、fake-perfect 数字、filler verbs、
  假 `<div>` 产品截图、装饰状态点、scroll 提示、章节编号 eyebrow、中点配额）、
  `best-practices-bias-correction`（一页一个强调色、Inter 不作反射式默认、衬线纪律、反居中偏置、圆角/配色一致性锁）、
  `features-micro-interactions`（同心圆角 = 外半径 = 内半径 + padding、光学对齐、按上下文选边框还是阴影、
  `tabular-nums`、`text-balance`/`text-pretty`、`will-change` 节制、最小命中区）、`advanced-pattern-vocabulary`（模式词汇表）。
- **不取部分**（UnoCSS 耦合）：`core-starter-kit`、`core-tokens-and-combinations`、
  `best-practices-class-utilities-over-attributify`、`features-floating-vue-overrides`，以及所有 `shortcuts` 配置块与 `@unocss-include`。
- **溯源惯例**：三份 reference 末尾的 HTML 注释都署名 `Leonxlnx/taste-skill`，`features-micro-interactions` 署名
  `jakubkrehel/make-interfaces-feel-better`。这直接决定了候选 10 必须单列（见「最终合入清单」的 notes）。

### 7. leonxlnx/taste-skill（INCLUDE, merged，仅语义）

- **审计结论**：MIT、85 902★、2026-08-24 推送，许可与活跃度都过关，但**形态不可合入**：
  单个 `skills/taste-skill/SKILL.md` 87 126 字节（远超本仓库 500 行 / references 600 行上限），
  含大量 GSAP 代码骨架，且自我限定范围为「landing / portfolio / redesign，不含 dashboard、数据表、多步产品 UI」。
  仓库本体也高度商业化（赞助位、联盟链接、`.cc` 营销站）。
- **裁决**：不取其正文与代码，只取**三拨盘（VARIANCE / MOTION / DENSITY）与一句式 design read 的语义**，
  并全部用自己的话重写。因为这两样是我们确实采用的东西，而 antfu 的三份 reference 都署名它为源头，
  只署名 antfu 会构成误标来源——所以 `relation: merged` 而不是 `reference`。
- **与 antfu 的差异**：antfu 给了 Tooling / Marketing 两套基线值（2-3/2-3/7-9 与 7-8/5-7/3-4），
  taste-skill 只给一套 `8/6/4` 且偏 landing。本 skill 采用 antfu 的双基线（更新、覆盖面更广，且明确了 tooling 场景）。

### 8. nextlevelbuilder/ui-ux-pro-max-skill（INCLUDE, merged，仅两份 markdown）

- **结构**：`.claude-plugin/` + `.claude/skills/{ui-ux-pro-max,design-system,brand,banner-design}/`，
  含 `scripts/*.cjs|*.py`、`data/*.csv`、`templates/`，整体约 8 MB。
- **质量分裂判定**：`SKILL.md` 本身写得比它的名声好（显式的查询契约、「重试一次后必须声明这是回退」、
  「零结果检索绝不可当作有数据来讲」、不假设技术栈）。但整体是 `python scripts/search.py` over CSV 的外壳，
  且路径依赖 `${CLAUDE_PLUGIN_ROOT}` —— 被本仓库 1.3 节禁用，不可移植。126k★ 反映的是传播度（13.5k fork + 营销站），不是内容深度。
- **只取**：`references/quick-reference.md`（10 类共约 230 条，含 119 条核心）与 `references/pro-rules.md`
  （职业化 UI 规则 + 交付前清单）两份**静态 markdown**；丢弃搜索运行时、CSV 语料、`--persist` 设计系统机制。
- **正确性抽查（4 条，全对）**：`web-target-size` = 24×24 CSS px 并标 WCAG 2.2 AA；
  `focus-not-obscured` 标 AA（= SC 2.4.11，正确）；`focus-appearance` 标 AAA（= SC 2.4.13，正确）；
  `touch-target-size` 44×44pt 明确归给 Apple、48×48dp 归给 Material（未冒充 WCAG）。
  这是本次审查的所有社区上游中**唯一**没有把 44×44 说成 WCAG 最低要求的。
- **重叠**：第 1、3、5、6、7 类与候选 2 大面积重叠；去重后本 skill 只保留候选 2 没写、且确实是判断题的条目
  （如 `+n` 溢出摘要必须可操作、只读态与禁用态必须可区分、错误摘要必须可聚焦并链接到字段）。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| R1 | 生成 vs 评估 | Anthropic 给「该选什么」（俗套簇、两遍流程、文案生成）；Vercel 给「该标什么」（150 条可判定规则 + `file:line`） | 不是冲突，拆成两个 workflow：`design-direction` 用 Anthropic，`review-ui` 用 Vercel。文案规则同样两分：生成期用 Anthropic 的语气/命名原则，评审期用 Vercel 的可检查条目（Title Case、计数用数字、主动语态） | 两者是不同任务形态，触发词也不同；标准 3 节「只给一个默认方案」是针对同一任务的多个做法，不适用于两个任务 |
| R2 | web 最小交互目标尺寸 | wshobson `details.md` 的 Mobile 小节写 `44x44dp minimum`，Button 示例注释写 `Minimum touch target size (44x44px)`（其 SC 表格里 2.5.8 = 24×24 是对的，属于表述混淆）；addyosmani 仓库级 a11y 清单在 "WCAG 2.1 AA" 标题下写 `Touch targets ≥ 44x44px`；ui-ux-pro-max 正确区分；antfu 写「最小命中区 40×40px」（自有工程约定，未称 WCAG） | **以 W3C 原文为准**：SC 2.5.8 Target Size (Minimum) = **Level AA，至少 24×24 CSS px**，带 Spacing（24 CSS px 直径圆不相交）/ Equivalent / Inline / User Agent Control / Essential 五项例外；**SC 2.5.5 Target Size (Enhanced) = Level AAA，44×44 CSS px**。44×44 另见 Apple HIG 的 44pt 与 Material 的 48dp（平台指南，非 WCAG）。正文必须写对并标出条款号与级别 | 直接读 <https://www.w3.org/TR/WCAG22/> 正文；官方规范 > 任何 skill 转述。同时 WCAG 2.1 根本没有 AA 级目标尺寸条款，addyosmani 的标题归类也错 |
| R3 | 动效数值 | Vercel（8 条，无数值）；ui-ux-pro-max 第 7 类（26 条，含「退场为入场的 60–70%」「stagger 30–50ms」「spring 优先」）；Emil `STANDARDS.md`（频率表 + easing 决策序 + 分档时长 + 300ms 上限 + 可中断性）；antfu（stagger 约 100ms、`tap-scale` 不低于 0.96） | 数值以 **Emil** 为准（最具体、有取值理由、作者是 Sonner/Vaul）；stagger 采用 Emil 的 30–80ms（antfu 的 100ms 与 ui-ux-pro-max 的 30–50ms 都落在或贴近该区间，不单列）；Emil 独有的「该不该动」频率表置于动效章之首，因为它能一次性砍掉大部分无谓动效；Vercel 的 8 条保留在 review 清单里（它们是可机械判定的，与数值不冲突） | 「公认专家 > 社区」+「更具体 > 更泛」；且 Emil 每条都给了为什么（`ease-out` 200ms 主观上快于 `ease-in` 200ms） |
| R4 | 三拨盘的基线值 | taste-skill：单一基线 `8/6/4`（偏 landing）；antfu：Tooling `2-3/2-3/7-9` 与 Marketing `7-8/5-7/3-4` 两套 | 采用 antfu 的**双基线**，并保留 taste-skill 的拨盘定义与 design read 句式 | 「更新 > 更旧」（2026-06-23 的 antfu 版把 dashboard/devtools 场景补齐了），且本 skill 范围不限于 landing |
| R5 | Inter / 默认字体 | addyosmani 的示例大量使用 Tailwind 默认（隐含 Inter）；antfu 明确「Inter 不作反射式默认」，并点名 Fraunces / Instrument Serif 不作默认 display 衬线；Anthropic 说「不要用你在任何别的项目上都会拿的默认字族」 | 采用「Inter / Fraunces / Instrument Serif 不作反射式默认」，并要求为选定字体给出一句理由 | 三方同向，antfu 最具体（点名了具体字体）；Anthropic 是官方厂商，给了原则 |
| R6 | 破折号 | antfu / taste-skill：可见文案中**零** em dash（U+2014）与 en dash（U+2013），只允许 `-`；Anthropic：把 `WORD — fragment` 间隔破折号列为模板 chrome tell（针对特定用法，不是全面禁令） | 采用全面禁令（可见 UI 文案不出现 U+2014 / U+2013），并说明替代手法（句号、逗号、括号、冒号、换行、分栏；范围用 `-`） | 更严格且可机械检查（一次 grep 就能判定），与 Anthropic 的观察不矛盾——它禁的是该字符最常见的那种用法 |
| R7 | 阴影还是边框 | addyosmani：「重阴影是 AI 默认，除设计系统指定外用微弱或不用阴影」；antfu：按上下文——密集/结构性表面用 hairline 边框，悬浮/营销卡片用分层且带背景色调的阴影 | 采用 antfu 的**按上下文**规则，并把 addyosmani 的观察收窄为它真正想说的：**同一套阴影不分层级地铺在每张卡上**才是 tell | 两者本不冲突，addyosmani 的表述过宽；antfu 给了可执行的判据（表面类型） |
| R8 | 圆角 | addyosmani：`rounded-2xl` 一刀切是 AI 默认；Anthropic：所有元素同一圆角不分层级是 SaaS 卡片套件的特征；antfu：形状一致性锁 + 同心圆角（外半径 = 内半径 + padding） | 三条合成一条可判定规则：**一套圆角刻度 + 嵌套时同心**。违反判据是「圆角值只有一个」或「父子圆角相等而父有 padding」 | 三方同向，antfu 提供了唯一可计算的判据 |
| R9 | Baseline 与回退 | modern-web-guidance：Baseline Widely available 默认免回退；非 Widely available 必须按指南给回退，除非用户声明策略；其他上游完全没有这一层 | 直接采用，并把「先 `search` 再 `retrieve`，不要凭记忆断言某特性能不能用」写成 `modernize-css` workflow 的第一步 | 唯一来源且是官方厂商（Google Chrome）；这条正是本仓库「不让旧知识误导模型」的核心手段 |
| R10 | ui-ux-pro-max 的移动/原生条目 | 其 10 类中大量条目是 iOS/Android 原生（Tab Bar、Top App Bar、haptic、Dynamic Type、safe area）；本 skill 范围是 web | 只取 web 适用条目；原生条目全部丢弃（Apple 平台内容归 `apple` skill） | 本 skill 的 `## Scope` 已明确排除原生移动 UI，正文混入原生条目会诱发跨平台编造 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `anthropic-frontend-design` | anthropics/skills `skills/frontend-design/` (Apache-2.0) | merged | 五类生成式设计特征簇、两遍设计流程（计划 → 对照 brief 复核 → 构建 → 自评）、排版方向原则、UX 文案生成原则、CSS 特异性陷阱 |
| `vercel-wig` | vercel-labs/web-interface-guidelines `command.md` (MIT) | merged | 14 类可机械检查的 UI/a11y/表单/动效/性能/i18n 规则、anti-pattern 清单、`file:line` 输出契约 |
| `addy-frontend-ui` | addyosmani/agent-skills `skills/frontend-ui-engineering/` + 仓库级 `references/accessibility-checklist.md` (MIT) | merged | AI 默认 → 为什么是问题 → 生产质量对照表、间距刻度纪律、语义色 token、a11y 模式与 live region 表、空/错误态 |
| `addy-performance` | addyosmani/agent-skills `skills/performance-optimization/` + 仓库级 `references/performance-checklist.md` (MIT) | merged | Core Web Vitals 目标与五步 measure-first 流程、按症状分诊、回归守卫 |
| `antfu-design` | antfu/skills `skills/antfu-design/`（框架无关的 5 份 reference，MIT） | merged | 三拨盘与 design read、anti-slop 硬清单、偏差纠正（排版/色彩/布局/材质）、微交互打磨（同心圆角、光学对齐、边框 vs 阴影）、模式词汇表 |
| `leonx-taste` | leonxlnx/taste-skill `skills/taste-skill/` (MIT) | merged | VARIANCE / MOTION / DENSITY 三拨盘与一句式 design read 的**语义源头**（antfu 三份 reference 均署名它）。未采用其正文、GSAP 骨架或任何代码 |
| `emil-animations` | emilkowalski/skills `skills/review-animations/`（含 `STANDARDS.md`）与 `skills/emil-design-eng/` (MIT) | merged | 「该不该动」频率决策表、easing 决策序、分档时长与 300ms 上限、物理性（永不 `scale(0)`、原点感知）、可中断性与 `@starting-style`、stagger 30–80ms |
| `uiux-pro-max` | nextlevelbuilder/ui-ux-pro-max-skill `references/{quick-reference,pro-rules}.md` (MIT) | merged | 去重后补入 Vercel 未覆盖的 UX 判断题（溢出摘要可操作、只读 vs 禁用、错误摘要可聚焦、图表的文本替代与色盲安全） |
| `chrome-mwg` | GoogleChrome/modern-web-guidance (Apache-2.0) | merged | Baseline 分级与回退策略协商、自定义浏览器支持策略的判定规则、`search` / `retrieve` / `list` 工作流（本机实测） |
| `w3c-wcag22` | W3C WCAG 2.2 (W3C Document License, kind=docs) | merged | 全部 a11y 数值与条款级别的裁决来源（2.5.8 AA 24×24、2.5.5 AAA 44×44、1.4.3、1.4.11、1.4.10、1.4.12、2.4.7、2.4.11、2.4.13、2.5.7、3.2.6、3.3.7、3.3.8、2.2.2、2.3.3、1.4.13） |
| `web-dev-vitals` | web.dev `articles/vitals` (CC-BY-4.0, kind=docs) | merged | Core Web Vitals 阈值与「75 分位、按移动/桌面分段」的判定方法 |
| `wshobson-a11y` | wshobson/agents `plugins/ui-design/skills/accessibility-compliance/` (MIT) | reference | 仅作对照：其触控目标表述混淆促成了 R2 的核对，未采用其任何内容 |

## 基线缺口

无 skill 基线跑了两个模型：`uv run tools/run_evals.py frontend-design --baseline` 与
`... --baseline --model @smol`。四个场景全部 `status: ok`、`skill_read: false`。

首轮基线时场景 4 在默认模型上 900 s 超时（agent 试图真的去动数据库），因此把 query 收紧为
「只读文件、只做静态分析、不装不起不查任何数据库、不写文件」，重跑后 97.6 s 完成。
这是评测夹具的修正，不是 skill 的修正。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 review landing.html | **输出格式** | 两个模型都用 `L5` / `L49` 这种行号写法，外加中文前言与结尾「最该先动的三处」总结段。要求的是 `landing.html:49` + 按文件分组 + 无前言 |
| 1 | **俗套特征命名** | 两个模型都没把靛蓝→紫渐变、三层堆叠阴影、`A · B · C` 中点串、`→` 后缀、单词换色斜体强调、可见文案里的 em dash 认成生成式设计特征。默认模型只碰到了「`--radius: 1rem` 一个值套三种尺度」和一句泛泛的「模板级泛泛之谈」；`@smol` 这一轴完全空白 |
| 1 | **`Loading...` → `Loading…`** | 两个模型都没提。默认模型把它当死代码报了（这是对的，但不是同一条） |
| 1 | **占位内容的性质** | `John Doe` 两个模型都认出来了，`1234567` 与 `03/04/2026` 也都报了；但 `99.99%` / 恰好 `50%` 作为「fake-perfect 假精度」、`Acme` 作为 startup-slop 名、`Elevate` / `seamlessly` 作为 filler verb，两个模型都没有归类到这一层 |
| 2 design direction | **一句式 design read** | 两个模型都没给 `Reading this as: …` 这一行；默认模型改成了一段「先说没被说出口的核心问题」，`@smol` 给了一个「视觉概念」标题 |
| 2 | **ASCII 线框** | 默认模型给的是 mermaid 叙事流程图（不是版面线框），`@smol` 给的是编号段落清单。两者都没有线框 |
| 2 | **对照俗套簇复核并说明改了什么** | 两个模型都没有这一步，而且都**落在簇 1 里**：默认模型 `#F4F1EA` 纸白 + Fraunces 衬线 display + 铁锈橙/黄铜；`@smol` `#F4F1EA` + Newsreader 衬线 + `#B0812F` 黄铜，正文还用了 Inter Tight。两者都自己列了「反模式清单」（渐变紫、玻璃拟态、库存图），却都没检查自己刚选的方向 |
| 3 target size | 无缺口 | 两个模型基线都答对了 24×24 AA / 44×44 AAA / Apple 44pt 与五项例外。此场景无区分度，保留作回归护栏 |
| 4 负例 | 无缺口 | 两个模型基线都 `skill_read: false` 且纯按 SQL 作答（扇出、`LOWER()` + 前导 `%`、`NOT IN`、缺 `order_items(order_id)` 索引），并建议 `EXPLAIN (ANALYZE, BUFFERS)` |

## 评测结果

两模型 × 有/无 skill × 4 场景 = 16 次运行，全部 `status: ok`。
结果目录 `/tmp/hs-evals/frontend-design/<default|smol>/<baseline|skill>/<n>/`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 | default | 无 | false | 6 / 9 | 缺输出格式、俗套特征命名、`Loading…`；占位内容只报到「格式不对」一层 |
| 1 | default | 有 | **true** | **9 / 9** | 43 条发现全部 `landing.html:<line> - 问题；修法`，无前言。命名了渐变、三层阴影、单半径、ALL-CAPS eyebrow、中点串、`→` 后缀、斜体单词强调、em dash、`99.99%`/`50%`/`1234567`、`Loading...`；并指出居中卡片压深色渐变是「最常见的生成式布局」 |
| 1 | @smol | 无 | false | 6 / 9 | 与默认模型同样的三处缺口，俗套一轴完全空白 |
| 1 | @smol | 有 | **true** | **9 / 9**（其中 7/9 条俗套项） | 36 条发现，格式完全正确。渐变、堆叠阴影、单半径、eyebrow、`→`、em dash、`Loading...`、`John Doe`、`99.99%`、`1234567`、Inter 反射式默认全部命中；中点串只报成「假导航」、斜体只报成合成斜体，没归到「拼接式强调」那一层 |
| 2 | default | 无 | false | 4 / 7 | 缺 design read 行、ASCII 线框、俗套复核；且方向本身落在簇 1（`#F4F1EA` + Fraunces + 铁锈橙） |
| 2 | default | 有 | **true** | **7 / 7** | 给出 design read 行、三拨盘（6/2/5）并说明为何覆盖营销基线、5 个具名 hex、Archivo + IBM Plex Mono 各带一句理由、1280 与 320 两张 ASCII 线框、独立的「Cliché gate」段落说明四处改动。还主动指出 SKILL.md 里那个 worked example 对同一 brief 已是默认答案，照抄等于跳过 gate |
| 2 | @smol | 无 | false | 4 / 7 | 同样缺三项，方向同样落在簇 1（`#F4F1EA` + Newsreader + `#B0812F`），正文还用 Inter Tight |
| 2 | @smol | 有 | **true** | **7 / 7** | design read 行、三拨盘（6/4/4）、6 个具名 hex（含暗色对等值）、Mona Sans + Martian Mono 各带理由、ASCII 线框、「Cliché gate — what changed」段落列出三处改动；同样识破了 worked example 是默认答案 |
| 3 | default | 无 | false | 4 / 4 | 无区分度 |
| 3 | default | 有 | **true** | 4 / 4 | 答案更紧凑，并补上了 `axe-core` 4.8+ 与 Lighthouse 旧 48px 启发式的判定差异 |
| 3 | @smol | 无 | false | 4 / 4 | 无区分度 |
| 3 | @smol | 有 | **true** | 4 / 4 | 同上 |
| 4 | default | 无 | **false** | 3 / 3 | 负例，正确不触发 |
| 4 | default | 有 | **false** | 3 / 3 | 负例通过：`skill_read == false`，答案里 typography / WCAG / Core Web Vitals / 对比度 相关词出现 0 次 |
| 4 | @smol | 无 | **false** | 3 / 3 | 负例，正确不触发 |
| 4 | @smol | 有 | **false** | 3 / 3 | 负例通过 |

结论：**通过**。两种模型都出现「基线未达成 → 有 skill 达成」：

- **默认模型**：场景 1 的输出格式、俗套特征命名、`Loading…`、占位内容归类四项由未达成转为达成（6/9 → 9/9）；
  场景 2 的 design read 行、ASCII 线框、俗套复核三项由未达成转为达成（4/7 → 7/7），且方向从簇 1 移出。
- **`@smol`**：场景 1 同样 6/9 → 9/9（俗套一轴从完全空白到 7/9 命中，输出格式完全正确）；
  场景 2 同样 4/7 → 7/7。
- 负例四次运行全部 `skill_read: false`，无误触发。
- 场景 3 在两个模型的基线上都已达成，无区分度。保留它的理由是它守的是一个**易错事实**
  （社区上游普遍把 44×44 说成 AA 最低要求），一旦本 skill 的 `accessibility.md` 写错，
  这个场景会立刻从「模型自己答对」退化为「被 skill 带错」。它是回归护栏，不是区分度来源。

## 备注

### 与计划的偏离及理由

1. **`anthropic-frontend-design` 保持 `merged`**。计划的应急方案假设它可能是专有许可；实读
   `LICENSE.txt` 为 Apache-2.0，因此应急方案未触发。
2. **`leonx-taste` 从 `reference` 改为 `merged`**。计划写的是「审计后决定」。审计结论是形态不可合入
   （87 KB 单文件、GSAP 耦合、范围仅 landing/portfolio），但我们确实采用了它的三拨盘与 design read 语义，
   而 antfu 的三份 reference 全部署名它为源头。只署名 antfu 会误标来源，所以按 `merged` 记录，
   并在 `notes` 明确未采用其正文与代码。
3. **`emil-animations` 新增为 merged 上游**。计划只把 emil 列为「核实后 merged」，核实通过（MIT、
   36 568★、2026-08-21）。它带来了其他所有上游都缺的一层：**「该不该动」的频率决策表**，
   以及可引用的 easing / 时长数值。动效冲突按 R3 以它为准。
4. **新增 `web-dev-vitals`（docs）**。CWV 阈值不应只靠 addyosmani 的转述，直接对 web.dev 原文核对了
   LCP 2.5s / INP 200ms / CLS 0.1 与「75 分位、按移动/桌面分段」的判定方法。
5. **`wshobson-a11y` 记为 `reference` 而非纯 REJECT 行**。它没有贡献任何内容，但它的表述混淆是
   R2 那次 W3C 核对的起因，记录在案比只在候选表里留一行 REJECT 更能解释 `accessibility.md`
   为什么要专门开一节讲「被引错的数字」。
6. **references 共 11 个**（计划列表实际也是 11 项，文中写「10 个」）。在 ±3 容差内，且计划列出的每个
   主题都有落点。
7. **无 `scripts/`**，与计划一致；`modern-web-guidance` 以 npx 方式在 `## Environment` 说明。
8. **`## Read first` 章节省略**。本 skill 没有「过期 API 索引」这类必读文件，
   `modern-css-platform.md` 的作用是把 Baseline 判定交给工具而不是固化事实。
9. **评测过程中修了一次 SKILL.md**。两个模型都指出 SKILL.md 里的 `design-direction` worked example
   对「手工钎焊钢架」这个 brief 本身已经是默认答案。这是真问题：例子会被照抄。
   因此在例子前加了一句「照抄形状，不要照抄内容」，并对两个模型重跑了场景 2，
   上表里场景 2 的「有 skill」四行是重跑后的结果，与仓库里 SKILL.md 的当前内容一致。

### 未来同步时要盯的上游

- `vercel-labs/web-interface-guidelines`：单文件、规则会增删，是 `review-checklist.md` 的主干，优先级最高。
- `GoogleChrome/modern-web-guidance`：guide 语料随 npm 包自更新，仓库变更主要影响
  `modern-css-platform.md` 的 goal → id 映射表；同步时重跑一次 `list` 核对 id。
- `anthropics/skills` `skills/frontend-design/`：俗套特征簇会随模型行为变化而更新，这是本 skill
  最容易过期的一节。
- `emilkowalski/skills`：`review-animations/STANDARDS.md` 的数值是动效章的唯一数值来源。
- W3C WCAG：下一版规范（或 2.2 的勘误）会直接改动 `accessibility.md` 的表格。

### 放弃的方向

- **不做 Tailwind 专章**。没有官方 Tailwind skill（`tailwindlabs/tailwindcss` 无 skill 目录），
  唯一候选 `Lombiq/Tailwind-Agent-Skills` 是 5 个月未更的文档快照。Tailwind 层的约定由
  `react` skill 的 shadcn 样式规则承担，本 skill 只写与框架无关的 CSS 事实。
- **不写原生移动 UI**。`uiux-pro-max` 里大量 iOS/Android 条目（Tab Bar、haptic、Dynamic Type、
  safe area 的原生部分）一律丢弃，避免与 `apple` skill 冲突并诱发跨平台编造。
- **不合入 `anthropics/skills` 的 `canvas-design` 与 `web-artifacts-builder`**，范围外。
- **不做完整设计系统生成器**（`ui-ux-pro-max` 的 `--persist` 机制、192 个调色板 CSV）。
  那是搜索语料而不是判断规则，且依赖 harness 专属路径。
