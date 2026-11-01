# html-deck 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-19
- 复核日期：2026-09-19（下表全部 stars / `pushed_at` / license / `archived` 均于当日经**已登录 `gh`**（账号 Lynricsy）重新核对，无匿名 HTTP，无 `unverified` 项）
- 检索途径：
  - `web_search`：`html slide deck agent skill SKILL.md github`、`presentation skill claude code SKILL.md`、`slidev marp skill SKILL.md github`、`网页 PPT skill`、`site:skills.sh presentation`、`site:skills.sh slides`
  - 官方组织仓库逐目录核对：`anthropics/skills`（19 项）、`openai/skills`（`.curated` 39 项）、`github/awesome-copilot`（`skills/` 全量）
  - 聚合器（仅作发现来源）：VoltAgent/awesome-agent-skills、addyosmani/agent-skills
  - 框架与工具官方文档：revealjs.com、sli.dev、marp.app、marpit.marp.app、playwright.dev、decktape README.adoc
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id, archived:.archived}'`；版本号 `gh api repos/<o>/<r>/releases/latest --jq .tag_name`；上游正文 `gh api repos/<o>/<r>/contents/<path> --jq .content | base64 -d`

**真空位确认**：`anthropics/skills`、`openai/skills`、`github/awesome-copilot` 三个官方仓库均**无** slide / deck / presentation skill（`awesome-copilot` 按 `slide|deck|present|ppt` 过滤只命中 `react-container-presentation-component`，是 React 容器组件模式，与幻灯片无关）。HTML deck 在第一方生态里没有对手，缺口真实。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。
`—` 表示该行已因硬性规则（新鲜度 >6 月 / 无许可 / 非 skill / 目录核对为空）出局，未再抽查，不等于 0 分。

### A. Agent skill 生态

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | lewislulu/html-ppt-skill | https://github.com/lewislulu/html-ppt-skill | 8430 | 2026-09-14 | MIT | 36 主题 / 31 版式 / S 键双窗演讲者模式 + 逐字稿 | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE (merged)** | 演讲者模式与备注纪律是本 skill 明确覆盖项，本候选该主题最深且唯一给出双窗同步机制 |
| 2 | zarazhangrui/frontend-slides | https://github.com/zarazhangrui/frontend-slides | 29539 | 2026-06-23 | MIT | 零依赖单文件 deck：固定 1920×1080 舞台、风格发现、导出陷阱 | 3 | 2 | 3 | 3 | 2 | 13 | **INCLUDE (merged)** | 唯一同时覆盖舞台体系 + 风格选择流程 + 导出陷阱的高星 MIT 实现；richieto/frontend-slides(0★) 是其 fork，取上游 |
| 3 | event4u-app/agent-config `skills/html-deck` | https://github.com/event4u-app/agent-config | 10 | 2026-09-19 | MIT | 固定画布 deck 规范：保真底线、字号地板、Do NOT、导出陷阱 | 1 | 3 | 3 | 3 | 2 | 12 | **INCLUDE (merged)** | 星少但规则密度最高，且「固定画布 ≠ 响应式 UI ≠ 静态海报」的三分定义是本 skill 边界的最佳表述 |
| 4 | f-labs-io/agent-html-skills `html-slideshow-deck` | https://github.com/f-labs-io/agent-html-skills | 56 | 2026-09-02 | MIT | 8 类幻灯片型别、页数预算、反模式清单 | 1 | 3 | 3 | 3 | 2 | 12 | **INCLUDE (merged)** | 内容节奏维度最结构化（型别 → 用途 → 限额），并给出 HTML vs pptx 的分流判据 |
| 5 | first-fluke/oh-my-agent `oma-slide` | https://github.com/first-fluke/oh-my-agent | 1309 | 2026-09-19 | MIT | 动画型 deck 生成器 + 专有 CLI：几何校验、bundle、导出 | 2 | 3 | 3 | 2 | 2 | 12 | **INCLUDE (partial)** | 取「skill 负责判断与创作、确定性程序负责校验」的职责边界与 16 条 guardrail；命令绑定其专有 CLI，不可照搬（正确性扣 1：`oma slide validate` 的几何校验未能实际运行核实） |
| 6 | antfu/skills `skills/slidev` | https://github.com/antfu/skills | 5897 | 2026-06-23 | MIT | Slidev 路线：语法、动画、演讲者模式、导出，50+ 篇 references | 3 | 2 | 2 | 3 | 2 | 12 | **INCLUDE (逃生口)** | Slidev 作者本人维护；只取「何时该退到框架」的触发清单与「命令 + 可观察验收」写法，其 references 是官方文档镜像，不得内联 |
| 7 | SlideSpeak/slide-design-skill | https://github.com/SlideSpeak/slide-design-skill | 23 | 2026-06-25 | MIT | 1920×1080 deck 引擎，设计红线由代码门禁强制 | 2 | 2 | 3 | 3 | 2 | 12 | **INCLUDE (merged, 限定)** | 规则是常量与正则而非形容词：`TYPE_FLOOR_PX = 14`、`VOID_MAX_PX = 230`、eyebrow ≤ `ceil(n/3)`、正文/标题 Jaccard ≥0.6 判复述。评分分歧见冲突 C6 |
| 8 | bmad-labs/skills `slides-generator` | https://github.com/bmad-labs/skills | 15 | 2026-09-15 | MIT | React+Tailwind 工程导出单文件 slide.html | 1 | 3 | 2 | 1 | 2 | 9 | MAYBE（未采纳） | 需求采集问卷可借，但 React 构建路线与「零依赖单文件」默认冲突；正确性 1：其调色板 ID 化做法未能核实 |
| 9 | edu-ai-builders/visual-cognition-slides | https://github.com/edu-ai-builders/visual-cognition-slides | 83 | 2026-05-16 | MIT | 认知科学取向 HTML 课件：5 种画布 + clamp 字号梯 | 1 | 1 | 3 | 2 | 2 | 9 | **REFERENCE** | 画布枚举思路可参考，但 clamp/vw 字号梯与固定舞台等比缩放冲突（见 C7），且 `caption: clamp(9px,…)` 在投影下不可读，正确性扣 1 |
| 10 | nexu-io/open-design | https://github.com/nexu-io/open-design | 97024 | 2026-09-19 | Apache-2.0 | 桌面设计工作台，deck 是其一个 surface | 2 | 3 | 1 | 1 | 2 | 9 | **REFERENCE** | 不是 skill（按 `slide\|deck` 过滤全是应用源码）；价值仅在于 `apps/daemon/src/qa/deck-layout.ts` 证明版式 QA 可程序化 |
| 11 | starchild-ai-agent/official-skills `slide-creator` | https://github.com/starchild-ai-agent/official-skills | 27 | 2026-09-18 | null | 16:9 HTML deck + PDF 导出，按场景分流 | 1 | 3 | 2 | 1 | 0 | 7 | REJECT 为源 | 仓库级无 LICENSE → 不得 merged；场景分流思路与候选 4 重复，无独占贡献 |
| 12 | Akshar-code/deckmason | https://github.com/Akshar-code/deckmason | 0 | 2026-07-31 | MIT | 8 阶段 deck 工作流、31 主题、PPTX 双路径 | 0 | 2 | 2 | 0 | 2 | 6 | REJECT | 0★ 无社区验证，正文未逐行核实（正确性 0 = 未核实）；阶段化工作流已由候选 2/3 覆盖 |
| 13 | knight6669/knight-html-ppt-skill | https://github.com/knight6669/knight-html-ppt-skill | 4 | 2026-07-02 | MIT | 候选 1 的增强衍生 | 0 | 2 | 2 | 0 | 2 | 6 | REJECT | 自述派生自 lewislulu；上游 8430★ 且更新更近 → 取上游 |
| 14 | op7418/guizang-ppt-skill | https://github.com/op7418/guizang-ppt-skill | 26586 | 2026-08-07 | **AGPL-3.0** | 杂志风 / 瑞士风单文件 HTML 横滑 deck，含演讲者模式 | 3 | 2 | 3 | — | **0** | — | **REFERENCE only** | AGPL-3.0 是传染性 copyleft，与本仓库 MIT 不兼容（判例：`research/office.md` 对 hu568/md-to-word 的 AGPL REJECT）。只能 `relation: reference`：读其主题覆盖清单，不复制任何正文、模板 HTML、assets 或脚本 |
| 15 | softaworks/agent-toolkit `marp-slide` | https://github.com/softaworks/agent-toolkit | 2482 | 2026-03-05 | MIT | Marp 路线 skill | 2 | 0 | — | — | 2 | — | REJECT | 距今 6.5 个月 > 6 月硬线；Marp 事实直接引官方 marp-cli 文档更可靠 |
| 16 | yoanbernabeu/slidev-skills | https://github.com/yoanbernabeu/slidev-skills | 39 | 2026-01-30 | MIT | 20 个 Slidev skill | 1 | 0 | — | — | 2 | — | REJECT | >6 月；Slidev 路线由候选 6 覆盖 |
| 17 | claude-office-skills/skills `dev-slides` | https://github.com/claude-office-skills/skills | 474 | 2026-01-31 | MIT | Slidev 开发者演示 | 1 | 0 | — | — | 2 | — | REJECT | >6 月 |
| 18 | JetBrains/skills `slidev` | https://github.com/JetBrains/skills | 351 | 2026-06-29 | null | Slidev skill | 2 | 2 | — | — | 1 | — | REJECT | 与候选 6 同题材重复，且仓库级无 LICENSE（仅 README 自称 MIT）→ 取 antfu |
| 19 | eruto-skills/marp | https://github.com/eruto-skills/marp | 0 | 2026-08-13 | MIT | Marp deck 创建与质检 | 0 | 2 | — | — | 2 | — | REJECT | 0★ 无验证 |
| 20 | 6missedcalls/slidev-agent-skill | https://github.com/6missedcalls/slidev-agent-skill | 0 | 2026-02-27 | MIT | Slidev 生命周期脚本 | 0 | 0 | — | — | 2 | — | REJECT | >6 月 + 0★ |
| 21 | marcoshaber99/slidev-skills | https://github.com/marcoshaber99/slidev-skills | 6 | 2026-01-23 | null | Slidev 约束 | 0 | 0 | — | — | 0 | — | REJECT | >6 月 + 无许可 |
| 22 | ducnguyen221/agent-slide-studio | https://github.com/ducnguyen221/agent-slide-studio | 0 | 2026-09-17 | null | ImageGen 优先的 slide skill | 0 | 3 | — | — | 0 | — | REJECT | 无许可 + 0★ |
| 23 | ZeroAlcoholic/PresentationSkill-ClaudeCode | https://github.com/ZeroAlcoholic/PresentationSkill-ClaudeCode | 0 | 2026-06-01 | null | 印刷品质海报/deck | 0 | 2 | — | — | 0 | — | REJECT | 无许可；范围是印刷海报，非放映产物 |
| 24 | anthropics/skills | https://github.com/anthropics/skills | 177122 | 2026-09-10 | null | 19 个 skill 已列全 | — | — | — | — | — | — | 确认空 | 无任何 slide/deck skill（最近的是 pptx、canvas-design、web-artifacts-builder） |
| 25 | openai/skills | https://github.com/openai/skills | 27474 | 2026-09-08 | null | `.curated` 39 项已列全 | — | — | — | — | — | — | 确认空 | 无 slide/deck skill（最近的是 pdf、screenshot、playwright） |
| 26 | github/awesome-copilot | https://github.com/github/awesome-copilot | 39161 | 2026-09-18 | MIT | `skills/` 全量已过滤 | — | — | — | — | — | — | 确认空 | 唯一命中项与幻灯片无关 |

### B. 框架与运行时

| # | 仓库/文档 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 27 | hakimel/reveal.js（`v6.0.2`） | https://github.com/hakimel/reveal.js | 72312 | 2026-09-18 | MIT | 固定画布等比缩放、fragments、speaker view、`?print-pdf`、scroll view | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE** | 唯一既能 `file://` 零构建打开、又把 `width/height/minScale/maxScale/pdfMaxPagesPerSlide` 写成可验证默认值的框架 |
| 28 | slidevjs/slidev（`v53.0.0`） | https://github.com/slidevjs/slidev | 48746 | 2026-09-16 | MIT | Vite+Vue Markdown deck：canvasWidth、presenter 路由、`slidev export` | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE** | 导出与演讲者模式命令全文档化，且缩放/裁切行为可由 `packages/client/internals/SlideContainer.vue` 源码验证 |
| 29 | marp-team/marp-cli（`v4.5.1`） | https://github.com/marp-team/marp-cli | 3826 | 2026-09-08 | MIT | Markdown → 自包含 HTML / PDF / PNG / 备注 txt | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE** | 唯一一条命令产出真正单文件 HTML 的官方路径（模板把 CSS/JS 内联）；`--pdf-notes`/`--pdf-outlines`/`--allow-local-files` 可直接写死 |
| 30 | marp-team/marp-core（`v4.4.0`，v5 为 `next` RC） | https://github.com/marp-team/marp-core | 1154 | 2026-09-04 | MIT | Marp Markdown 层：`size:`、`<!-- fit -->`、auto-scaling | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE** | 唯一明确写出「自动缩放只作用于水平方向，内容仍可能从底部溢出」的上游文档，正是 deck 最常见缺陷 |
| 31 | marp-team/marpit（`v3.2.3`） | https://github.com/marp-team/marpit | 1378 | 2026-09-04 | MIT | 主题 CSS 尺寸模型、分页属性、scoped style | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE** | 主题契约可机器校验：尺寸必须绝对单位、一主题一尺寸、`attr(data-marpit-pagination)` 必须出现 |
| 32 | impress/impress.js（`v2.0.0`） | https://github.com/impress/impress.js | 38169 | 2026-07-23 | MIT | 3D 无限画布演示 | 2 | 2 | 2 | 1 | 2 | 9 | **REFERENCE** | 无页面尺寸契约、无演讲者备注、无导出（PDF 只能靠 decktape 插件）；只作「非线性画布」心智模型参考 |
| 33 | FormidableLabs/spectacle（`10.2.3`） | https://github.com/FormidableLabs/spectacle | 10161 | 2026-04-12 | MIT | React/JSX 组件式 deck | 2 | 1 | 1 | 1 | 2 | 7 | MAYBE（未采纳） | 需要 React 工具链，与「浏览器直接打开」目标冲突；新鲜度仅 1 |
| 34 | gnab/remark（`v0.15.0`） | https://github.com/gnab/remark | 13001 | 2024-06-19 | MIT | 浏览器内 Markdown 幻灯片 | 2 | 0 | — | — | 2 | — | REJECT | 距今 >2 年，新鲜度 0；其单文件理念由 Marp 覆盖 |
| 35 | webslides/WebSlides（`1.5.0`） | https://github.com/webslides/WebSlides | 6324 | 2022-12-10 | MIT | CSS 版式模板集 | 1 | 0 | — | — | 2 | — | REJECT | 2022-12 停更 |
| 36 | rajgoel/reveal.js-plugins（`4.6.0`） | https://github.com/rajgoel/reveal.js-plugins | 815 | 2025-06-23 | MIT | reveal 第三方插件集 | 1 | 0 | — | — | 2 | — | REJECT | >6 月 |
| 37 | maaslalani/slides（`v0.9.0`） | https://github.com/maaslalani/slides | 11660 | 2026-07-08 | MIT | 终端 TUI 放映 Markdown | 2 | 2 | — | — | 2 | — | REJECT（范围外） | 产物是终端渲染，不是浏览器 deck，无 PDF / 演讲者视图 |

### C. 导出与自动化质检

| # | 仓库/文档 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 38 | microsoft/playwright | https://github.com/microsoft/playwright | 96349 | 2026-09-19 | Apache-2.0 | 逐页截图、PDF、DOM 几何度量 | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE** | 一个依赖同时覆盖度量 + 截图 + PDF；`printBackground` / `preferCSSPageSize` 默认值由 `types.d.ts` 原文确认并本机复测 |
| 39 | astefanutti/decktape（`v3.16.1`） | https://github.com/astefanutti/decktape | 2426 | 2026-07-13 | MIT | 13 种框架插件 + `generic` 按键遍历 → PDF/PNG | 3 | 2 | 3 | 3 | 2 | 13 | **INCLUDE** | 不改造第三方 deck 工程即可导出；本机实测 3 页 PDF + 3 张 PNG 成功，并复现 3 个真实陷阱 |
| 40 | Chromium headless CLI（`--print-to-pdf` / `--screenshot`） | https://developer.chrome.com/docs/chromium/headless | — | — | BSD-3-Clause（chromium/chromium） | 零 Node 依赖的导出回退 | 3 | 3 | 2 | 3 | 2 | 13 | **INCLUDE** | 容器/CI 无 Node 时的唯一回退；本机实测出 3 页 960×540pt 且背景完整。具体性扣 1：无官方 flag 参考页，纸张只能由 CSS `@page` 决定 |
| 41 | puppeteer/puppeteer | https://github.com/puppeteer/puppeteer | 95590 | 2026-09-18 | Apache-2.0 | Chrome 自动化；decktape 的底层 | 3 | 3 | 2 | 3 | 2 | 13 | **REFERENCE** | 能力与 Playwright 100% 重叠，skill 并列两套 API 会让验证门出现两种写法；保留为 decktape 报错解释来源 |

### D. 设计数值锚点

| # | 仓库/文档 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 42 | carbon-design-system/carbon `packages/grid` | https://github.com/carbon-design-system/carbon | 9464 | 2026-09-19 | Apache-2.0 | 设计系统栅格源码常量（16 列、32px 沟槽） | 3 | 3 | 3 | 3 | 2 | 14 | **REFERENCE** | 数值可信，但它是断点驱动的响应式栅格，deck 是固定画布；只作「沟槽应是枚举而非任意值」的旁证，栅格数值由本仓库自行在 1920 画布上推导 |
| 43 | w3c/wcag `understanding/20/visual-presentation.html` | https://github.com/w3c/wcag | 1490 | 2026-09-18 | NOASSERTION（W3C Document License） | 行长 ≤80 字符（CJK 40）、行距 ≥1.5 | 3 | 3 | 3 | 3 | 1 | 13 | **未采纳** | 数值本身正确，但本仓库的 WCAG 与排版数值唯一出处是 `skills/frontend-design`（`SKILL.md:47`、`:52`），html-deck 引用它而不重复数字（见边界表） |

## 深度审查

### 三条产物路线（这是本 skill 的结构决定因素）

调研把候选自然分成三条互不兼容的产物路线，**尺寸模型、溢出行为、备注写法、导出命令四项全部不同**，不能写成通用建议：

| 路线 | 代表 | 单文件 / `file://` | 溢出默认行为 | 导出命令 |
|---|---|---|---|---|
| A 手写单文件固定舞台 | 候选 1/2/3/4/7/14 | 是（目标即此） | 由作者决定，默认裁切 | Playwright / Chromium headless |
| B Markdown 工程 | Marp（29/30/31） | **是**，`marp x.md -o x.html` 模板把 CSS/JS 内联 | 只水平自动缩放，纵向仍溢出 | `marp --pdf --pdf-notes --pdf-outlines` |
| C 应用工程 | Slidev（28）、reveal.js（27） | Slidev **否**（Vite SPA，`--base` 必须以 `/` 开头结尾）；reveal 是多文件但可 `file://` 打开 | Slidev 硬裁切（`.slidev-slide-content` 固定 px + `overflow-hidden`）；reveal 不自动缩，PDF 里过高的页自动分成多页 | `slidev export`（需 `playwright-chromium`）/ `?print-pdf` 打印 |

六个独立实现（候选 1/2/3/4/7/14）在没有互相引用的情况下全部收敛到「固定 16:9 舞台 + 整体等比缩放 letterbox」，这是路线 A 作为默认值的最强证据。

### 逐候选要点（前 8 名）

- **lewislulu/html-ppt-skill（14）**：备注写进 `div.notes`（默认 `display:none`），S 键开双窗；演讲者预览用 `?preview=N` 加载同一份 deck，保证配色/字体/视口与观众视图一致；双窗同步用 `postMessage` + `BroadcastChannel`。逐字稿规则「每页 150–300 字 ≈ 2–3 分钟，写成提示信号而非朗读稿」。不可用：36 主题 / 31 版式的资产库（体量与本仓库结构不匹配）、写死的 macOS Chrome 路径。
- **zarazhangrui/frontend-slides（13）**：固定舞台 8 条不变量 + 内容密度两档；「先生成 3 张风格预览再让用户选」的风格发现流程；切页禁用 `display:none/block`（会被版式类的 `display:flex` 覆盖导致全部幻灯片同时可见）；导出脚本以 `.slide` 选择器找页，类名不同的 deck 会「0 slides found」。不可用：Vercel 部署章节（属托管）、上百个模板文件、PPTX 抽取（属 `office`）。
- **event4u-app/agent-config `html-deck`（12）**：给出本 skill 最需要的三分定义——固定画布 deck ≠ 响应式 UI ≠ 静态海报；字号地板 1080p 下正文 ≥24px、标题 60–96px；「版式预算」写在文件顶部注释块，之后每页只能从预算里取；`localStorage` 按 `location.pathname` 派生 key 导致同路径两个 deck 共享页码。不可用：其自有体系交叉引用（surface-agent-contracts、Q13/CP5 编号）。
- **f-labs-io/agent-html-skills（12）**：8 类幻灯片型别各带限额（代码页 ≤10 行、要点 ≤3 条）；五段结构与页数预算（15 分钟 ≈ 12–15 页）；SVG `<text>` 不自动换行，可变文本要么按字符估宽要么用 `foreignObject`。不可用：`${CLAUDE_PLUGIN_ROOT}` 与 "Publish to Claude.ai" 等宿主耦合段落（本仓库校验器直接禁这些 token）。
- **first-fluke/oh-my-agent `oma-slide`（12）**：职责边界表（判断/创作归 skill，几何校验与导出归确定性程序）；校验失败最多自动修 3 轮再交人；动画一律包在 `@media (prefers-reduced-motion: no-preference)`；导航控件必须有可见 focus 态。不可用：全部 `oma slide *` 命令与 `OMA_*` 环境变量。
- **antfu/skills `slidev`（12）**：每条命令都配一条可观察验收（dev → 端口加载成功；export → 产物存在）；SKILL.md 只做路由、按需读 references。不可用：50+ 篇 references 是官方文档镜像（其 `SYNC.md` 自述为同步产物），只能以「见 sli.dev」方式引用。
- **SlideSpeak/slide-design-skill（12）**：`scripts/validate-skill.ts:178` 的 `TYPE_FLOOR_PX = 14`（作用域是风格包而非 "anywhere"，文档措辞与实现不符）；`engine/occupancy.ts:33` 的 `VOID_MAX_PX = 230`（=1080 的 21.3%）；`:226` `MIN_CONTRAST = 3.0` 与 WCAG 大字号阈值一致，`:230` `CONTRAST_FAIL = 2.2` 是其自订硬失败线、**不是**规范数值；eyebrow ≤ `ceil(n/3)`；正文与标题词集 Jaccard ≥0.6 判「正文只是复述标题」；导出前先跑 occupancy，失败 `exit 1`。
- **reveal.js / Slidev / Marp 三者的事实差异**：见上方路线表与冲突 C2。

### 与本仓库既有 skill 的边界（逐条有文件行号依据）

| 主题 | 已覆盖者 | html-deck 的处置 |
|---|---|---|
| 二进制 `.pptx` 创建/编辑/模板填充 | `office`（`SKILL.md:17-20`、`:84`、`:151`） | **留空**，写进 Not covered 并指回 `office`；`office/SKILL.md:25` 已声明 HTML 交付物不属于它，两边措辞天然咬合，无需改 `office` |
| 版式家族与类型比例 | `office`（`references/pptx-design.md:26-38`，六种版式） | **引用分类，重写表达**：pt/英寸 → CSS px 与 1920 栅格 |
| 字号梯级与最小字号 | `office`（`pptx-design.md:40-59`，pt） | **必须重写**：单位不可迁移，换算依据见 C5 |
| 调色板规模、重点色数量 | `office`（`pptx-design.md:61-78`）、`frontend-design`（`SKILL.md:40`、`:45`） | **引用**，只补「deck token 必须能被导出脚本读到」 |
| 对比度与 WCAG 数值 | `frontend-design`（`SKILL.md:47`，标 `[official]`） | **引用，绝不重复数字**；只补「投影环境按渲染图实测而非按 token 计算」 |
| 字体族数量、measure、行距 | `frontend-design`（`SKILL.md:52`） | **引用**；只重写 deck 特有部分（投影距离、固定画布下的 px 梯级） |
| 动效数值与 reduced-motion | `frontend-design`（`SKILL.md:57-58`） | **引用**；只补「分步显现是内容节奏而非装饰动效」 |
| 「机器味」版式识别 | `frontend-design`（`SKILL.md:37`、`:43`、`:56`） | **引用**；只重写 deck 特化配额（密度档混用、callout 连续上限、正文不得复述标题） |
| 网页 UI 可访问性（焦点、触控目标、表单） | `frontend-design`（`SKILL.md:48-49`） | **留空**，只保留键盘翻页与焦点可见这一最小交集 |
| AI 配图生成、provenance、披露 | `generative-media`（`SKILL.md:17-26`、`:113-125`） | **引用**；html-deck 只负责图片槽位、比例与压字 scrim |
| 图片艺术指导 | 无人覆盖（`generative-media/SKILL.md:40-41` 明确不管） | **本 skill 覆盖**（槽位比例、裁切安全区、文字压图） |
| 素材转码/裁剪 | `media-processing` | **留空** |
| 文档类叙事（README/教程/ADR） | `technical-writing`（`SKILL.md:17-28`） | **留空**；讲稿叙事顺序属本 skill |
| 演讲者模式、备注、计时 | **仓库内无任何 skill 提及**（跨 4 文件检索 `speaker`/`notes`/`presenter` 无命中） | **本 skill 独占** |
| 交付前渲染核验 | `office`（`SKILL.md:35-38`、`:100-103`，方法是人工读 PNG） | **引用立场，重写方法**：改为脚本度量 + 人工读图双门 |
| PDF/PNG 导出 | `office`（`SKILL.md:135`，LibreOffice 路径） | **本 skill 覆盖**：headless 浏览器路径与 LibreOffice 无关 |

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| C1 | 默认路线 | 候选 1/2/3/4/7/14 = 手写单文件固定舞台；候选 6 = Slidev 工程；候选 29 = Marp Markdown | **默认路线 A（手写单文件固定舞台）**，Marp / Slidev / reveal.js 作为逃生口，各给明确触发条件 | 六个独立实现无交叉引用却收敛到同一形态；且用户诉求（"直接能打开、能发给别人"）只有路线 A 与 Marp 满足，而路线 A 对版式自由度更高 |
| C2 | 溢出由谁兜底 | Marp 文档：auto-scaling 可缓解；社区普遍认为「框架会自动缩」 | **没有任何框架兜底纵向溢出，必须靠渲染后度量发现** | `marp-core/docs/markdown.md` 原文：auto scaling is only horizontal，内容仍会从底部溢出；`slidev` `SlideContainer.vue` 的 `scale = min(w/W, h/H)` 只按画布算、`.slidev-slide-content` 固定 px + `overflow-hidden` = 硬裁切；reveal 不自动缩且导出 PDF 时过高的页自动分页（除非 `pdfMaxPagesPerSlide: 1`） |
| C3 | 截图确定化 | Playwright `screenshot({animations:'disabled'})` 常被当作确定化手段 | **只对 CSS 动画/过渡有效，对 canvas/rAF 无效**；canvas 页不做像素 diff，改为在页面侧确定化（`addInitScript` 覆盖 `Math.random`/`Date.now`，或 deck 暴露冻结钩子） | 本机实测同页两张 `animations:'disabled'` 截图 sha256 前 16 位 `6c9bca92278f03de` ≠ `adc2096d1345406f`；headless 仍推进 rAF（实测 56 帧） |
| C4 | PDF 背景丢失的原因 | 通行说法：开 `printBackground` 即可 | **两个独立原因，必须双保险**：导出端 `printBackground: true`（默认 false）+ 页面端 CSS `print-color-adjust: exact`（含 `-webkit-` 前缀） | 本机 A/B：无 exact 的 deck 默认导出全白 `(255,255,255)`；写了 exact 后即使不传 `printBackground` 也导出完整渐变 `(27,33,64)`——与通行说法相反，故两条都写 |
| C5 | 字号地板的数值与单位 | SlideSpeak `TYPE_FLOOR_PX = 14`（CSS px）；event4u 正文 ≥24px@1080p；f-labs ≥24pt；`office/pptx-design.md:52` ≥12pt；visual-cognition caption `clamp(9px,…)` | **在 1080p 画布上：任何文字 ≥24px，正文 32–40px，标题 56–64px，宣言页 80–108px**；丢弃 9px 与裸 14px | 换算而非照抄：`office` 的 pt 梯级基于 `LAYOUT_WIDE` 13.33×7.5 in = 540 pt 高的版面，1080 px 画布高 ÷ 540 pt = **px = pt × 2**。于是 12 pt→24 px、16–20 pt→32–40 px、28–32 pt→56–64 px、40–54 pt→80–108 px。该换算独立复现了 event4u 的 24px 地板与 60–96px 标题区间，可交叉印证；SlideSpeak 的 14px 是网页组件地板而非投影地板，不适用 |
| C6 | SlideSpeak 评分分歧（8 vs 12） | 只读其 43 行 `SKILL.md` → 具体性 1；读到 `engine/*.ts` 常量 → 具体性 3 | **按实际参考的内容计分 = 12**，但 merged 贡献严格限定为阈值与节奏配额 | 量表衡量的是「我们真正取用的内容」，而非入口文件长度；取用对象是 `occupancy.ts`/`validate-skill.ts` 的常量 |
| C7 | 字号用 `clamp()+vw` 还是固定 px | visual-cognition：全套 `clamp(min, vw, max)` 梯级；路线 A 多数实现：固定 px + 整体 `transform: scale()` | **固定 px + 舞台整体等比缩放**；禁止在幻灯片内部使用 vw/vh/clamp 或响应式断点 | 舞台已整体缩放，内部再用 vw 会二次缩放；更致命的是导出时视口尺寸与预览不同，vw 字号随之改变，**预览通过不代表导出通过**，验证门就失效了。`event4u` 同样禁止幻灯片内部用响应式单位 |
| C8 | 演讲者模式能否 `file://` 跑 | 各 skill 含糊表述「双击打开即可」；本 skill 起初裁决为「一律要求本地 HTTP 服务」 | **裁决修正（依据基线实测）**：`file://` 下可用的是「同源子窗口 + 父窗口直接写其 DOM」；`window.open('')` 打开的 about:blank 子窗口继承 opener 源，父窗口可直接读写 `child.document`。**不要**把 `localStorage` 当同步通道——`file://` 下所有本地文档共享同一个源，两份 deck 会撞同一个 key。reveal 的 speaker view 确实需要 HTTP 服务，那是它插件实现的事实，不是通用规律 | 本机实测（Chromium 1243，headless，`file://`）：`window.open('')` → `sameOriginDom: true`，父窗口写入后子窗口 DOM 读回 `slide 2`；`localStorage.setItem/getItem` 在 `file://` 下**成功**（origin 为 `file://`，即全部本地文件共用）；`BroadcastChannel` 在两个 `file://` 窗口间**实际送达**（`["ping"]`）。marp-cli `normal-view.ts` 的 `storage.available` 门控与 reveal 官方要求本地 HTTP 仍为 `[official]` 事实，但只约束这两个框架自身 |
| C9 | decktape 能否无人值守 | README 的 `generic` 模式看似自动停机 | **必须显式 `--slides 1-N` 给上界** | 本机实测：停机条件是「按键后 body 子树不再 mutation」，末页仍执行 `classList.toggle`（写同值 class 也算 attribute mutation）导致导到第 17 页仍不停 |
| C10 | 单文件 deck 能否运行期加载数据 | 部分实现把内容放外部 JSON | **单文件 deck 内不得运行期 `fetch`** | 本机实测 `file://` 下 `fetch()` 被 Chromium 直接拒绝（`URL scheme "file" is not supported`，非 CORS 可绕）；需要外部资源就必须起 `python3 -m http.server`，那就不再是"发过去双击打开" |
| C11 | 切页用什么机制 | 多数实现用 `.slide{display:none}` + `.active{display:flex}` | **用 `visibility`/`opacity`/`pointer-events`，不用 `display` 开关** | 基线产物 `quarterly-brief.html:42` 正是 `display:none/flex` 写法，结果打印路径必须再注入 `display:flex !important` 才能出多页（`:95`）——`display` 既被版式类占用、又被打印样式争夺，是同一处代码的两次返工 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| lewislulu-html-ppt | lewislulu/html-ppt-skill | merged | 演讲者模式双窗结构、备注绝不上台、逐字稿 150–300 字/页规则 |
| zarazhangrui-frontend-slides | zarazhangrui/frontend-slides | merged | 固定舞台不变量、风格发现流程、`display:none` 切页陷阱、导出选择器陷阱 |
| event4u-html-deck | event4u-app/agent-config `skills/html-deck` | merged | 三分定义（固定画布 / 响应式 UI / 静态海报）、字号地板与版式预算、`localStorage` pathname 陷阱 |
| flabs-slideshow-deck | f-labs-io/agent-html-skills `html-slideshow-deck` | merged | 幻灯片型别限额、页数预算、SVG 文本不换行 |
| slidespeak-design | SlideSpeak/slide-design-skill | merged | 可度量阈值（空白上限、eyebrow 配额、正文复述标题判定）与「导出前必须过门禁」的流程位置 |
| ohmyagent-oma-slide | first-fluke/oh-my-agent `oma-slide` | merged | skill/确定性程序职责边界、失败最多自动修 3 轮、reduced-motion 与可见 focus 两条 guardrail |
| antfu-skills-slidev | antfu/skills `skills/slidev` | merged | 退到 Slidev 的触发清单与「命令 + 可观察验收」写法 |
| revealjs | hakimel/reveal.js | merged | 固定画布缩放模型、`r-fit-text`/`r-stretch` 限制、`?print-pdf` 与 `pdfMaxPagesPerSlide`、speaker view 需 HTTP |
| slidev | slidevjs/slidev | merged | canvasWidth/aspectRatio 模型、硬裁切行为（源码级）、`slidev export` 与 presenter 路由 |
| marp-cli | marp-team/marp-cli | merged | 单文件 HTML 产物机制、`--pdf-notes`/`--pdf-outlines`/`--allow-local-files`、演讲者视图的 localStorage 依赖 |
| marp-core | marp-team/marp-core | merged | auto-scaling 只作用于水平方向这一硬事实 |
| marpit | marp-team/marpit | merged | 主题尺寸契约：绝对单位、一主题一尺寸、尺寸即 PDF 页面尺寸 |
| playwright | microsoft/playwright | merged | `printBackground`/`preferCSSPageSize` 默认值与 `print` 媒体语义；度量 + 截图 + PDF 单依赖方案 |
| decktape | astefanutti/decktape | merged | 第三方 deck 工程的按键遍历导出与其三个陷阱 |
| chromium-headless | Chromium headless CLI 文档 | merged | 零 Node 依赖导出回退：`--no-sandbox`、`@page` 决定纸张、`--virtual-time-budget` |
| guizang-ppt | op7418/guizang-ppt-skill | **reference** | AGPL-3.0，仅读其主题覆盖清单（双视觉系统、版式锁定、演讲者模式、配图与封面），未复制任何正文、模板、assets 或脚本 |
| open-design-deck-qa | nexu-io/open-design | reference | 存在性证据：版式 QA 可程序化（`apps/daemon/src/qa/deck-layout.ts`） |
| impress-js | impress/impress.js | reference | 非线性画布心智模型；无尺寸契约/备注/导出，不作主线 |
| visual-cognition-slides | edu-ai-builders/visual-cognition-slides | reference | 画布枚举思路；其 clamp/vw 字号梯与 9px caption 经裁决不采纳（C5、C7） |
| carbon-grid | carbon-design-system/carbon | reference | 「沟槽是枚举而非任意值」的旁证；响应式断点体系不适用固定画布 |
| puppeteer | puppeteer/puppeteer | reference | decktape 报错解释来源；API 与 Playwright 重叠，不并列写入 |

## 基线缺口

无 skill（`uv run tools/run_evals.py html-deck --baseline`）时，各场景未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明（证据） |
|---|---|---|
| 1 建 deck | **b1 固定画布内不得用视口单位** | 产物用 `vmin` 建字号体系（`quarterly-brief.html` 中 `vmin/vw/clamp` 命中 9 处，根 `font-size: 1.6vmin`），并自称「排版以 vmin 为基准，不同投影比例同比缩放」——恰恰是 C7 禁止的做法 |
| 1 建 deck | **b2 度量只做了一半** | 答案报告「逐元素测量相对页面边界的溢出量，最大 0px」＝ 只做了 `getBoundingClientRect` 越界，没有对 `overflow:hidden` 容器查 `scrollHeight > clientHeight`；实测证明前者在裁切场景下会漏报 |
| 1 建 deck | **b3 字号地板与字号报告** | 产物含 `font-size: 12px` 与 `.5em` 链式缩小，低于 1080p 画布 24px 地板；答案全篇未给出任何实际字号 |
| 1 建 deck | **b4 切页机制** | `:42` `.slide.active { display: flex; }` + 打印时 `:95` 注入 `display: flex !important`，即 C11 的返工现场 |
| 2 导出 | b4 字体就绪 | 答案未提截图前等待字体（该 deck 只用系统字体栈，未暴露问题，但规则未被遵守）。b1/b2/b3 **基线已达成**（双保险背景、960×540pt 纸张、pdftoppm 像素采样），这三条不作为缺口 |
| 3 演讲者模式 | **b3 失联检测与恢复** | 状态单一来源成立（父窗口独占），但没有观众窗口被关闭/失联的检测与恢复 |
| 3 演讲者模式 | **b4 每页时长估算** | 备注写成提示信号且不编造未知信息，但没有每页计划时长 |
| 3 演讲者模式 | （断言修正，不计为缺口） | 原 b1/b3 写死「一律要 HTTP」「必须用 BroadcastChannel」。基线的 `window.open('')` 同源子窗口方案促使本机复测，结论是两条断言都错（见 C8），断言已按可观察契约改写，基线与有 skill 均按新契约重判 |
| 4 负例 pptx | 无（全部达成，`skill_read == false`） | 基线正确走 pptx 路线并指出位图化风险 |
| 5 负例 落地页 | 无（全部达成，`skill_read == false`） | 基线按响应式网页处理，未引入放映机制 |

**结论**：基线在场景 1 有 4 条未达成、场景 3 有 2 条未达成，缺口集中在「固定画布的单位纪律」「度量的完整性」「字号地板」「切页机制」「现场失联恢复与时长」——这正是 skill 的 Core rules 与 presenter-mode workflow 必须钉死的内容。场景 2 基线表现很强，只保留字体就绪一条，不虚报缺口。

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 建 deck | Claude Opus 5 / medium | 无（基线） | false | b5 | b1 用 vmin、b2 只量越界、b3 有 12px 与未报字号、b4 `display` 切页 |
| 1 建 deck | 同上 | **有** | true | **b1 b2 b3 b4 b5（5/5）** | 两次有 skill 运行（description 定稿前 11 页 / 定稿后 10 页）结论一致：从 `assets/deck-shell.html` 起手，`deck_qa.mjs` 0 error 0 warning，逐张读 PNG 后又修了门禁看不出的构图问题（内容顶部堆叠、下方约 400px 死白 → 居中并加大正文而非缩字号），PDF 页数 = 幻灯片数、1440×810pt、背景采样为深色底 |
| 2 导出 | Claude Opus 5 / medium | 无（基线） | false | b1 b2 b3 | b4 未等字体（该 deck 仅系统字体，未暴露） |
| 2 导出 | 同上 | **有** | true | **b1 b2 b3 b4（4/4）** | 额外按字号地板发现夹具的 13px caption（归一化 20px）并修到 18px（=27px）；给出 `display:none` → PDF 只有 1 页的因果 |
| 3 演讲者模式 | Claude Opus 5 / medium | 无（基线） | false | b1 b2（2/4） | 按**修正后**的断言重判（原 b1/b3 写死了「一律要 HTTP」「必须用 BroadcastChannel」，已被实测推翻，见 C8）。基线达成 b1（明确说明选用同源子窗口因而 `file://` 可用）与 b2；未达成 b3（状态单一来源成立，但没有失联检测与恢复）与 b4（无每页时长）。其 b1 论证里「`file://` 下 BroadcastChannel 不可靠」一句与本机实测不符，判定只取其「交代适用条件并据此选型」的可观察结果 |
| 3 演讲者模式 | 同上 | **有（补丁前）** | true | b2 b3 b4（3/4） | 达成 b3（关窗 → LOST → 重开落回当前页）与 b4（备注为提示信号、每页 `Planned:` 时长，`pdftotext \| grep -cE 'Planned:\|未知'` = 0）；**未达成 b1**——交付说明没写清这套实现能不能双击使用 |
| 3 演讲者模式 | 同上 | **有（补丁后）** | true | **b1 b2 b3 b4（4/4）** | 在 `SKILL.md` presenter-mode workflow 增加「交付说明必须写清打开方式」一条与对应门禁后复跑：答案开头即写「双击就能演讲，不用起服务器」并给出选型理由（两个独立加载的 `file://` 文档互读 DOM 会 `SecurityError`，故用 `window.open('')` 子窗口）；备注在绘制观众窗前 `remove()` 整个 template；19 项 Playwright 排练全过，含弹窗被拦截的横幅降级 |
| 4 负例 pptx | Claude Opus 5 / medium | 无（基线） | false | 3/3 | 正确走 pptx |
| 4 负例 pptx | 同上 | 有 | **false** ✅ | **3/3** | description 定稿后不再读取本 skill，直接用 python-pptx 生成 9 页原生 OOXML，并实测客户视角的「改表格数字 / 改图表数据 / 新增两页」三项操作 |
| 5 负例 落地页 | Claude Opus 5 / medium | 无（基线） | false | 3/3 | 按响应式网页处理 |
| 5 负例 落地页 | 同上 | 有 | **false** ✅ | **3/3** | 产出 `index.html`/`styles.css`/`app.js`，滚动吸附按断点分级、手机关闭吸附；未引入翻页键位、备注或逐页 PDF |

结论：**通过**。基线未达成的 6 条行为在有 skill 时全部达成（场景 1 的 b1/b2/b3/b4、场景 3 的 b3/b4），两条负例均 `skill_read == false`。其中场景 3 的 b1 在首轮有 skill 运行中反而退步（基线达成、有 skill 未达成），据此给 presenter-mode workflow 补了显式交付项与门禁，复跑后 4/4——这是评测真正发挥作用的一次。有 skill 的运行另外发现了基线完全没看到的三个缺陷：夹具 13px caption、观众窗口未套固定画布缩放、首版构图约 400px 死白区。

### description 路由迭代（负例 `skill_read` 的实测过程）

负例一开始判定失败：技能被挂载时，模型会先打开 `skill://html-deck` 确认边界再转出去。事件流显示它在读取**之前**就已经识别出格式差异（"HTML rather than true pptx"、"slide decks rather than website"），所以读取动机是「确认 Scope」，不是「没看懂请求」。据此逐版实测：

| 版本 | description 要点 | 场景 4（pptx） | 场景 5（落地页） |
|---|---|---|---|
| v1 | `…HTML slide decks…; not editable .pptx.` | READ | — |
| v2 | `…run as HTML in a browser; PowerPoint and .pptx work belongs to the office skill.` | READ | — |
| v3 | `Creates .html slide decks…exports them to PDF and PNG.`（无 Office 词） | READ | — |
| v4 | `Builds single-file web pages that present as slides…` | **false** | READ（"web pages" 反过来把网页需求吸进来） |
| v5 | `Builds decks a browser presents full-screen one slide at a time…` | READ | READ |
| **v6（定稿）** | `Creates browser HTML slide decks. Do not load for editable PowerPoint files or responsive websites; those are the office and frontend-design skills.` | **false** | **false** |

有效的不是换同义词，而是把**动作指令**（不要加载 + 指名接管者）写进 description。两条正例（场景 2、3）在 v6 下仍会加载本技能，已单独确认。

方法学教训两条，均来自本次踩坑：

1. 先写过一个「首个工具调用即判定」的快速探针，它把「先读 deck 文件、随后读 skill」误判成 no-read，导致我差点据此改描述。判定必须是不对称的：**观测到读取可以立即结论，没观测到必须等运行结束**。
2. 一度想把负例的判定口径从「不读取」改写成「交付物正确」来消除失败——那是搬动靶心。判定恢复原样，改的是 description，直到实测为 false。

## 备注

- **许可红线**：`op7418/guizang-ppt-skill` 是 AGPL-3.0。本仓库 MIT，AGPL 传染性 copyleft 不兼容，判例见 `research/office.md` 对 hu568/md-to-word 的处置。它只能是 `relation: reference`：可以读、可以对齐主题覆盖，不得复制任何文字、模板 HTML、`assets/`、`references/` 或 `scripts/`。本 skill 的所有版式与校验数值均另有出处或本机推导（见 C5）。
- **`w3c/wcag` 未纳入**：数值正确但会与 `skills/frontend-design` 争夺 WCAG 数值的唯一出处。跨 skill 重复数字迟早发散，宁可引用。
- **后续同步要盯的上游**：`marp-team/marp-core` v5 目前是 `next` tag 的 RC（CHANGELOG 顶部 v5.0.2），转正式版时默认高亮器由 highlight.js 换成 Shiki，`.hljs-*` 失效；`slidevjs/slidev` 主版本号推进快（当前 v53）。
- **放弃的方向**：Spectacle（React 工具链与零依赖目标冲突）、impress.js 主线化（无尺寸契约与导出）、把 Marp/Slidev 的官方文档镜像进 references（体量与维护成本不成比例，改为引用官方站点）。

## 2026-09-30 上游同步

依据 2026-09-30 `tools/check_upstream.py` 报告。所有 `behind` 条目都在 blobless 克隆里按完整
`<旧pin>..<审阅HEAD>` 区间、只限该条目 `paths` 核对（`git log` + `git diff --stat` + `git diff`），未用日期过滤。
报告里标为 `diff too large` 的四条（event4u、antfu、open-design、carbon）改用 `git ls-tree` 比较两端的追踪路径。
本节替换了 2026-09-29 一轮被中断、未提交的改动：那轮把 event4u、playwright、carbon、puppeteer 钉在了当时的中间提交上，
而且 `frameworks.md` 的核验命令有错（见下文 C1），这次都按审阅 HEAD 重做了。

| 上游 | 区间 | 命中提交 / 文件 | 判定 | 理由 |
|---|---|---|---|---|
| event4u-html-deck | 107a210 → fd4a41a（226 提交），补审 fd4a41a → 3369ae2（35 提交） | `dist/agent-src/skills/html-deck` 两端都是 3 个文件，两段 `git diff` 都为空 | 噪声 | 追踪路径没有变化。第一次 pin 之后上游又前进，补审新增区间后重新 pin |
| antfu-skills-slidev | a74f281 → d02c484 | e98e476「chore!: remove vendored skills」删除了 `skills/slidev` 共 56 个文件 | 需更正（Phase B 重新裁决） | 这份 vendored 副本的 `SYNC.md` 注明它来自 `slidevjs/slidev` 的 `skills/slidev`（a1609ff）。原件仍在，所以把该路径并入已有的 `slidev` 条目（`paths: [packages/client, skills/slidev]`），并删除 `antfu-skills-slidev` 条目，`frameworks.md` 的 sources 注释同步去掉这个 id。原件从 a1609ff 到 30a0a54 有 5 个提交：0e24a64 加入 editable PPTX 导出，需更正正文（见 C1）；04a9eff 加入内置 MCP server，属 Slidev 工具使用，不是 deck 规则，不合入；b610bdf 加入 magic-move 动画参数，是文档镜像内容，不合入；9d5f45e（Tweet 支持 URL）和 1877b30（修链接）是噪声 |
| ohmyagent-oma-slide | f81c5a4 → ce19702 | 仓库有移动，追踪路径未变 | 噪声 | — |
| marpit | 0d4ad4e → 8b82169 | 仓库有移动（dependabot），追踪路径未变 | 噪声 | — |
| playwright | 07f1a61 → e37ddf1（94 提交） | `types.d.ts` 命中 10 个提交：`page.webmcp`（含一次 revert 与重提）、`Tracing.start` 返回 Disposable、`resourceType` 补全、WebKit `checkVisibility`、`locator.within()`、`page.content({includeShadow})`、`Temporal.Now` 跟随 clock、Firefox 支持 `isMobile` | 噪声 | `scripts/deck_qa.mjs` 只用到 `page.screenshot`、`page.pdf({printBackground, preferCSSPageSize})` 和 `page.evaluate`。逐个 hunk 核对，这三个 API 的签名与语义都没有变化 |
| open-design-deck-qa | f5707c8 → 5b19dfa（38 提交） | `apps/daemon/src/qa` 两端都是 2 个文件，diff 为空 | 噪声 | — |
| carbon-grid | 8472cca → 40f8d5c（41 提交） | `packages/grid/scss` 两端都是 5 个文件，diff 为空 | 噪声 | — |
| puppeteer | 5cf7e20 → 02c2a3d（15 提交） | 6ab0419 新增 `HTTPResponse.asFetchResponse` 两页文档 | 噪声 | 只作 reference，与 decktape 的失败输出无关 |

pin 写入的 commit 与上表审阅 HEAD 逐条一致：3369ae2、ce19702、8b82169、e37ddf1、5b19dfa、40f8d5c、02c2a3d；
slidev 仍为 30a0a54，这次新增的 `skills/slidev` 路径也在这个提交上审过。
up to date 条目随 `--pin` 对齐；`kind: docs` 条目不在本次范围。

### C1 事实更正：Slidev / Marp 的 PPTX 导出并非都是位图

旧的 `frameworks.md` 写的是「三条浏览器路线的 `.pptx` 输出都是每页一张位图，文本不可编辑」，这句话已经不成立：

- Slidev 0e24a64 在 v52.20.0 首次发布（`git tag --contains` 的结果是 v52.20.0、v52.20.1、v53.0.0）。按 30a0a54 的 `docs/guide/exporting.md` 的 Editable PPTX 节：
  `--format pptx-editable` 把页面重建成原生形状，文字可编辑。SVG（含 Mermaid 和图标）、canvas、iframe、视频、KaTeX、
  CSS 渐变、`filter`/`backdrop-filter`/`mix-blend-mode`/`clip-path` 仍会保留为图片；无法重建的页会单独回退成图片并打印原因；
  字体只写名字、不嵌入；正常流中的 `::before`/`::after` 装饰会被丢弃（代码行号是其中之一）；不支持 `--per-slide`。
  `packages/slidev/node/commands/pptx/walker.ts` 里可以找到对应代码（`unplaceablePseudos`、`filter`/`mixBlendMode`/`clipPath`、KaTeX 判定）。
- marp-cli ffc4128 的 README 写明 `--pptx --pptx-editable` 属于实验功能：需要同时装好浏览器和 LibreOffice Impress；主题样式复杂时可能报错或产出不完整；
  不支持演讲者备注。
- 本机实测（@slidev/cli 53.0.0 + playwright-chromium，3 页夹具含 Mermaid 和带行号的代码块）：
  `pptx` 导出每页的 `<a:t>` 都是 0；`pptx-editable` 导出三页分别为 2 / 1 / 22，其中 Mermaid 页只有标题这一个文本 run。
  上一轮草稿给的核验命令是 `grep -c '<a:t>'`，它数的是行数；slide XML 只有一行，所以 editable 版第 1 页数出来是 1，实际是 2 个 run。
  已改为逐页 `grep -o '<a:t>' | wc -l`。

正文改动：`references/frameworks.md` 的 PowerPoint 小节（两种 editable 模式的限制与逐页核验命令），Slidev 触发行加上
「同一源出可编辑 PowerPoint 副本」；`SKILL.md` 的 Scope 写明「Slidev/Marp 导出给人改措辞的 PowerPoint 副本」属于本技能，
「以可编辑 PowerPoint 本身为交付物」仍归 office。同一条核心规则里补了「退出到框架后用它的功能，不要手工重做」。

### 评测（场景 6 新增；场景 4 负例的 expected_behavior 第 2 条同步改了措辞）

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 6 magic-move + 给市场部的 PPT 副本 | workbuddy/deepseek-v4.1-flash / max | 无（基线） | false | b2 b3 b4；b1 部分 | 复用 2026-09-29 的运行（`/tmp/hs-evals-sync/SyncG8/.../baseline/6`，query 与 expected_behavior 与现文件逐字相同）。模型选了 Slidev，并读 CLI 源码找到了 `pptx-editable`，但没说明 Vite SPA 的代价；b5（`playwright-chromium`）未达成 |
| 6 | 同上 | 有（第 1 轮：`frameworks.md` 已更正，`SKILL.md` Scope 仍写「可编辑 PowerPoint 归 office」） | true | b4；b3 部分 | 退步。没读 `frameworks.md`，按 Scope 转去 python-pptx 另建一条管线，magic-move 也手写，没有走 Slidev |
| 6 | 同上 | 有（第 2 轮：Scope 与退出规则已改） | true | b4 | 退步。模型绕过 `skill://`，直接 glob 到 `/root/.omp/agent/skill-repositories/hyperskills/skills/html-deck/references/frameworks.md`，也就是全局安装的旧版本（仍写「全是位图」），并据此否定 Slidev 导出。这是评测环境污染（见遗留）。于是把关键事实直接写进 `SKILL.md` Scope |
| 6 | 同上 | 有（第 3 轮，定稿） | true | b2 b3 b4；b1 部分 | 选 Slidev，理由是 magic-move、Mermaid 和同源可编辑 PPTX；实测 `pptx` 可编辑字符为 0，`pptx-editable` 为 532；说明 Mermaid 仍是图片、字体不嵌入；逐页数文本 run 并做往返改稿。b1 的代价说明与 b5 仍未达成，与基线相同 |

结论：更正的依据是事实，不是基线缺口。基线自己能从源码找到 `pptx-editable`，而旧正文会把有 skill 的模型带偏（第 1、2 轮都退步）。
定稿后有 skill 的结果与基线持平，没有退步。b1 的代价说明和 b5 都已经写在 `frameworks.md` 的触发表和 Slidev Export 节里，
但两种模式都没有输出，这次不再为它们加正文。场景 4 负例依赖 description 路由，这次没改 description，未重跑。

冒烟：`validate_skills.py` 0 error，`build_catalog.py --check` 通过；执行 `npx skills@latest add <worktree> --skill html-deck --agent universal --copy`
后，`.agents/skills/html-deck` 的 16 个文件与 worktree 用 `diff -r` 比对完全一致。

### 遗留

- 评测环境里有全局安装的 HyperSkills 旧版本（`/root/.omp/agent/skill-repositories/hyperskills/skills/`）。有 skill 的运行可能读到旧文件而不是 worktree 版本，
  所有 worktree 评测都受影响。本节第 2 轮就是这样被污染的。

## 2026-10-15 上游同步

依据：主代理 2026-10-15 的 `check_upstream.py --json`（`/tmp/hs-upstream.json`）与归因结果（`/tmp/hs-attr/attribution.md`、
`skills_real.json`）。paths 下确有提交的是 flabs-slideshow-deck、ohmyagent-oma-slide、revealjs、playwright、decktape、carbon-grid、
puppeteer；event4u-html-deck、open-design-deck-qa 为 too-large，主代理按完整区间归因为空，判噪声。归因方法：oma-slide、
playwright、carbon 用主代理的 blobless 裸仓库缓存（`/tmp/hs-attr/<owner>__<repo>`）对 `<pin>..<head> -- <paths>` 跑
`git log` / `git diff --stat` / 逐提交 `git show`；其余用 `gh api .../compare/<pin>...<head>` 取 patch，只读 paths 内文件。
`--pin` 后 `pin_check.py` 报 `PIN CHECK CLEAN`；slidev（30a0a54 → 73053ab）、marpit（8b82169 → 9f20751）为 repo moved、
tracked paths unchanged，随之前移。chromium-headless 为 manual check，本次未处理。

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| ohmyagent-oma-slide | ce19702 → 83bc99d（2 提交） | 742b594「remove reduced-motion defaults」：删掉 guardrail「prefers-reduced-motion required」、`animation-patterns.md` 的「Reduced-Motion Guard Reference」、`viewport-base.css` 的 `prefers-reduced-motion: reduce` 覆盖、checklist 与 design-doctrine 的对应条目，示例动画全部去掉 `@media` 包裹；提交说明只写「Remove mandatory reduced-motion guidance」，没有给理由。ff11f05「correct execution contracts and unsafe templates」：Canva MCP 工具名改成官方远端名（`search-designs`、`upload-asset-from-url` 等）并删掉不存在的 `create_design` 资产数组流程；`deck-stage.js` 的 `goTo` 不再 clamp 非整数索引、`postMessage` 索引不再 `Number()` 强转；交叉淡化说明改为「共享 CSS 固定 350ms，不读 `--slide-transition-duration`」；预览页改为内联 CSS/JS | 不跟随 / 噪声。本 skill 的「动画放进 `@media (prefers-reduced-motion: no-preference)`」（`SKILL.md`、`references/single-file-deck.md`）依据是 W3C WCAG 技术 C39（用 `prefers-reduced-motion` 满足 SC 2.3.3），社区上游无理由删除不构成更正，按「官方 > 社区」保留，并在 `SOURCES.yaml` notes 记录。ff11f05 全部是它自己的 Canva 集成与运行时 `deck-stage.js`，本 skill 不含 Canva 路线，`assets/deck-shell.html` 也不是它的 stage 脚本 |
| flabs-slideshow-deck | d4f259e → a9ddeb2（1 提交） | 1.4.0 加一条默认规则：完整文档外壳，`<!doctype html>`、`<html lang>`、`<head>` 先写 `<meta charset="utf-8">`、viewport、`<title>`，理由是缺 charset 时 `file://` 打开会乱码 | 已覆盖：`assets/deck-shell.html` 前 5 行就是 doctype、`lang`、`<meta charset="utf-8">`、`<title>`，正文要求从它开始 |
| revealjs | f8c9ec3 → e240e17（2 提交） | `js/reveal.js`：`syncSlide()` 对当前页显式重新启动嵌入内容（背景 iframe）；`js/controllers/backgrounds.js`：同步时清掉 `backgroundImage`（渐变残留） | 噪声：运行时 bug 修复，正文不涉及 `syncSlide` |
| playwright | e37ddf1 → 5c42a39（17 提交命中 `types.d.ts`） | 与 web-testing 同一批：`CDPSession.send` 的 `timeout` / `signal`、`APIRequestContext` cookie 方法、`page.getByRef()`、WebAuthn `signCount`、撤回 evaluate 的 `world` 与 Map/Set 序列化、修正调用不存在 API 的示例（screencast、`selectOption`、`routeWebSocket`）、`within()` 描述、`headersArray()`、coverage 等 | 噪声：`scripts/deck_qa.mjs` 只用 `page.evaluate`、`page.screenshot`、`page.pdf({ printBackground, preferCSSPageSize })`，不用 CDPSession，也没传 `world` / `serialize`；逐 hunk 看，这三个 API 只有 evaluate 的可选参数被撤回，签名其余部分与 pdf/screenshot 语义未变 |
| decktape | 0ab408f → 6aa7ec0（1 提交） | `plugins/remark.js` 在导出前注入 `@page { size: auto !important; margin: 0 !important }`，修 remark 固定 4:3 `@page` 导致的 PDF 裁切 | 噪声：正文的 decktape 路线只讲 reveal.js 与「不改动的第三方 deck」，不涉及 remark 插件 |
| carbon-grid（reference） | 40f8d5c → c866811（2 提交） | f3dfa98 给 css-grid 加 `box-sizing: border-box`；b1d8da3 修注释错字 | 噪声：只作「gutter 是小枚举」的旁证；`assets/deck-shell.html` 本来就是 `* { box-sizing: border-box; }` |
| puppeteer（reference） | 02c2a3d → d1b9a21（7 提交） | `docs/api` 16 个文件：ConsoleMessage 的 `page()` / `frame()` / `worker()`、`HTTPRequest.asFetchRequest`、拦截与额外请求头接受 `Headers`、WebSocket 最大载荷、网络模拟改走 `emulateNetworkConditionsByRule`、`emulateMediaFeatures` 支持更多特性、Service Worker 请求也受黑白名单约束 | 噪声：只用来解释 decktape 的失败输出，这些新 API 不改变 decktape 的启动与报错 |
| event4u-html-deck、open-design-deck-qa | 3369ae2 → be11ed6；5b19dfa → 14fee23 | too-large，按完整区间对 paths 归因为空 | 噪声 |

结论：没有事实更正，也没有需要评测的新增规则。正文与 references 未变；`SOURCES.yaml` 只改 re-pin、`version` 与
ohmyagent-oma-slide 的 notes（记录上游删除 reduced-motion 而本 skill 保留的依据）；`metadata.version` 改为 2026.10.15。正文未变，未跑 D2。

## 2026-10-15 文档上游复核

| 上游 id | 核对的事实 | 当前官方页面 | 结论 |
|---|---|---|---|
| chromium-headless | 页面位置 | 原 URL `developer.chrome.com/docs/chromium/headless` 301 到 [/docs/automation-and-testing/headless](https://developer.chrome.com/docs/automation-and-testing/headless)，该页只讲 Headless 模式本身（Chrome 132.0.6793.0 起旧模式拆成 `chrome-headless-shell`）；CLI 参数移到 [/docs/automation-and-testing/headless-cli](https://developer.chrome.com/docs/automation-and-testing/headless-cli) | **页面迁移 → 更新 url**：`url` 改为 headless-cli 页 |
| chromium-headless | `--print-to-pdf`、`--no-pdf-header-footer`、`--screenshot` 配 `--window-size` | headless-cli 页 | 一致 |
| chromium-headless | `--virtual-time-budget` 快进计时器与加载，代替猜测的 sleep | headless-cli 页 §--virtual-time-budget | 一致 |
| chromium-headless | root 下不加 `--no-sandbox` 不产出文件；无 `@page` 时 PDF 为 Letter | 官方页面均未记载（本条一直是本地实测）；本机 Chromium 153.0.8010.52 重跑：stderr `Running as root without --no-sandbox is not supported`、目录里无 PDF；加 `--no-sandbox` 后无 `@page` 的页面 `MediaBox [0 0 612 792]` | 一致（重新实测） |

正文未改；`chromium-headless` 的 `url`、`synced_at`（2026-10-15）与 notes 更新。

## 2026-11-01 上游同步

依据：主代理 2026-11-01 的 `check_upstream.py --json`（`/tmp/hs-upstream-2026-11-01.json`）与工作单 `/tmp/hs-sync/html-deck.md`。
event4u、oma-slide、playwright、carbon 用主代理的 blobless 裸仓库缓存（`/tmp/hs-attr/<owner>__<repo>`）对 `<pin>..<head> -- <paths>`
读树 diff；decktape、guizang、puppeteer 用 `gh api .../compare/<pin>...<head>` 读 paths 内文件的 patch。`--pin` 后写入的 9 个变动
`commit` 与审阅 HEAD 逐条一致，无越界差额。

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| event4u-html-deck | be11ed6 → 5a66c1b | 3a9b54d：`SKILL.md` 第 4 步改为先调用其品牌解析器 `./agent-config brand:status --json`，只用解析器报告有效的 `sources[]`，无有效来源时把配色标为 `corpus-sourced` | 无影响，只 re-pin：宿主专属命令与交叉引用，按原 notes 本来就不搬 |
| ohmyagent-oma-slide | 83bc99d → 6f772a1 | dce69cc 新增 `native-pptx` 路线（调用上游 hugohe3/ppt-master 生成可编辑 PPTX，含路线选择表、Python 依赖须经用户同意、`resources/native-pptx.md`、checklist 一节）；a5b8582 删掉运行时溯源与历史散文，把 frontend-slides 风格预设的署名移到 `style-presets.LICENSE` | 无影响，只 re-pin：可编辑 PPTX 是 `office` skill 的地界（本 skill Scope 只为核对时描述 Slidev/Marp 的 pptx 模式）；本 skill 采纳的「判断与确定性校验分离」「三轮修复上限」未变 |
| playwright | 5c42a39 → deb7e86 | `types.d.ts`：7d0dcc2 `clock.fastForward` / `runFor` 的 `ticks` 须为有限数；a6fb02f `connectOverCDP` 的 `noDefaults` 也保留字体 | 无影响，只 re-pin：`scripts/deck_qa.mjs` 只用 `evaluate` / `screenshot` / `pdf`，不用 clock 与 CDP 连接 |
| decktape | 6aa7ec0 → 7b07b51 | `README.adoc`：3ed6f14 Docker 镜像改为 Debian slim + Puppeteer 管理的 Chrome for Testing（amd64/arm64）；18df73c / b51950d / 2b29d69 容器以 UID 1000 的 `node` 用户运行，挂载目录无写权限时 `EACCES`，给出 `--user "$(id -u):$(id -g)"`、rootless Podman `--userns=keep-id:uid=1000,gid=1000`、SELinux `:z`；npm 安装段新增「DeckTape requires Node.js 22.12 or later」 | **事实更正**（见下）：3.17.0（2026-10-19 发布，`npm view decktape` 为 `latest`）的 `package.json` `engines` 从 `>=18` 改为 `>=22.12.0`，而正文命令是 `npx -y decktape@latest`。顺带本机重跑三条陷阱，发现第 2 条已在 3.17.0 修复。Docker 段不用：正文走 npx |
| guizang-ppt（reference，AGPL-3.0） | c91369c → 93d21bf | 3b89211 / 889206a / cea2fd3 / ee0ecb5 / 93d21bf：主题改为 `<html data-theme>` 切换、品牌色经脚本生成受约束主题（不直接用用户 hex）、语义色变量 `--accent-ink` / `--accent-display` / `--accent-on`（浅色强调色当小字时自动加深）、中文强调不用斜体改加字重、新增共享组件手册 `gz-components.md` | 无影响，只 re-pin：AGPL 只作题目覆盖清单，不复制任何文字。「中文无斜体字形、浏览器合成斜体」与「强调色当文字需过对比度」属排版与配色，`frontend-design` 已有「不依赖合成斜体」（`typography.md`、`review-checklist.md`），本 skill `layout-and-type.md` 明确把对比度交给 `frontend-design`；CJK 斜体一条记为跨组线索 |
| carbon-grid（reference） | c866811 → 6351ab5 | 20865ea `_breakpoint.scss`：`breakpoint-between` 上界减 0.02px 防止相邻断点重叠 | 无影响：只作「gutter 是小枚举」的旁证，本 skill 是固定画布不用断点 |
| puppeteer（reference） | d1b9a21 → 7231774 | `docs/api` 31 个文件：`HTTPRequest.page()` / `worker()` / `content()`、`Locator.filter` / `map` 传参、`ConsoleMessageLocation.scriptId`、`page.tabInfo()`、`setGeolocation(null)`、`Browser.restrictNetwork` 黑白名单、`wsOptions.handshakeTimeout`；a1149f3 澄清 `emulateMediaType('screen')` 与 `page.pdf()` 的关系 | 无影响：只用来解释 decktape 的失败输出，新 API 不改变其启动与报错 |
| slidev | 73053ab → a42aff2 | paths 未变 | 噪声，只 re-pin |
| open-design-deck-qa（reference） | 14fee23 → 12d970e | 主代理裸仓库树 diff 确认 paths 无变化 | 噪声，只 re-pin |

### decktape 3.17.0 实跑核对

本机 Node v26.11.1、系统 Chromium 156.0.8078.47，夹具为 `evals/files/sample-deck.html`（3 页）与临时的「每次按键重写 class」3 页 deck：

- 正文命令原样（`cd` 进输出目录、相对文件名、`--slides 1-3`、`--chrome-path=/usr/bin/chromium --chrome-arg=--no-sandbox`）在 3.17.0 上产出 `out.pdf` 与 `shots/out_{1,2,3}_1280x720.png`。
- 陷阱 1（找不到浏览器）：`HOME` 与 `PUPPETEER_CACHE_DIR` 指向空目录、不给 `--chrome-path`，3.17.0 报 `Error: Could not find Chrome (ver. 155.0.8059.79)`，栈来自 `puppeteer-core` 的 `ChromeLauncher.launch` —— 仍成立。
- 陷阱 2（截图目录拼接）：`--screenshots-directory=/tmp/g02-dt/dt-png` 加绝对输出路径 `/tmp/g02-dt/abs.pdf`，3.16.1 报 `ENOENT … path: '/tmp/g02-dt/dt-png2/tmp/g02-dt/abs2_1_1280x720.png'`；3.17.0 正常写出 `dt-png/abs_{1,2}_1280x720.png` —— **已修复**（v3.16.1...v3.17.0 区间里与输出路径相关的是 #424「Fail fast when the output directory is not writable」与 #426「Extract filesystem helpers into libs/files.js」，未逐行定位到具体修复行）。
- 陷阱 3（`generic` 不停止）：不给 `--slides`，3.17.0 对 3 页 deck 跑满 60 s 被 `timeout` 杀掉（退出码 124）—— 仍成立。

### 正文改动

- `references/export-and-qa.md` decktape 一节：新增 3.17.0 需要 Node.js 22.12+、旧 Node 升级或钉 `decktape@3.16.1`；陷阱 1、3 标注 3.17.0 复验仍成立；陷阱 2 改为「3.16.1 及以前」，并注明 3.17.0 已修复、`cd` + 相对名两版都可用。
- `SOURCES.yaml`：decktape 加 `notes` 记录版本核对；chromium-headless 的 `synced_at` 与 `notes`（Chromium 156 复测）。
- `evals/evals.json` 新增场景 7（夹具 `evals/files/vendor-deck.html`：不可修改、只能键盘翻页、末页仍改 class 的合作方 deck，CI 为 Node v20.18 + 空 puppeteer 缓存 + root），作为本次更正的回归场景。

## 2026-11-01 上游新增内容评估

| 候选 | 来源（许可） | 归属 / 增量 | 结论 |
|---|---|---|---|
| `skills/revealjs/SKILL.md` | TerminalSkills/skills（Apache-2.0，188★） | reveal.js 6 使用手册：npm 安装、插件注册、`?print-pdf` + headless Chrome、`pdfSeparateFragments` / `pdfMaxPagesPerSlide` / `showNotes: 'separate-page'`。这些在 `references/frameworks.md` 已有，且官方 hakimel/reveal.js 已被追踪 | REJECT（无增量；官方源已追踪） |
| `.claude-plugin/directory/skills/oma-slide/SKILL.md` | first-fluke/oh-my-agent（MIT） | bd2e575 为插件目录生成的无 hook 入口，内容是 `.agents/skills/oma-slide` 的副本 | REJECT（生成副本；原路径已追踪） |
| `native-pptx` 路线所依赖的 hugohe3/ppt-master | first-fluke/oh-my-agent 新引用（MIT） | 可编辑 PPTX 生成，属 `office` skill | 不评（跨组线索，交主代理） |

## 2026-11-01 新候选

检索：`gh search repos "slides skill" --updated '>2026-10-15'`、`gh search code playwright --filename SKILL.md`（顺带筛幻灯片类）、
`VoltAgent/awesome-agent-skills` 近 60 提交的 README 新增行（命中 arifszn/slide-wright）。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 30 | arifszn/slide-wright | https://github.com/arifszn/slide-wright | 66 | 2026-10-24 | MIT | reveal.js（CDN）主题生成 + 两页预览确认门 + `check-deck.mjs` | 1 | 3 | 2 | 1 | 2 | 9 | MAYBE（未采纳） | 自称「单个自包含 HTML」却从 CDN 加载 reveal.js，与本 skill 离线双击可开的单文件契约冲突（正确 1）；可编辑 PPTX 导出属 `office`。唯一潜在增量是 `check-deck.mjs` 的「文本块相互重叠」检测（`scripts/deck_qa.mjs` 现查裁切、字号地板、字体未载入，不查重叠），需先建评测证明缺口，留待下轮 |
| 31 | crawfordxx/xiaoma-studio | https://github.com/crawfordxx/xiaoma-studio | 16 | 2026-10-23 | MIT | 代码驱动动效视频（每帧是 t 的纯函数）+ 附带 HTML 幻灯片与落地页 | 0 | 3 | 2 | — | 2 | — | REJECT（范围） | 创建于 2026-10-13，主体是渲染成 MP4 的动效视频引擎（storyboard、拼图自检、音频合成、`qa.py` 查响度与跳帧），幻灯片也走同一 f(t) 渲染，不是本 skill 的固定画布放映产物；其 `lint.mjs` 的文字重叠检查与 slide-wright 同类，并入上一行的留待项。`slides skill` 检索的其余命中（bento、handdrawn、research-slides 等）均 ≤1★ 或无许可，留行以免重查 |

## 2026-11-01 文档上游复核

| 上游 id | 核对的事实 | 当前官方页面 | 结论 |
|---|---|---|---|
| chromium-headless | `--print-to-pdf`、`--no-pdf-header-footer`、`--screenshot` 配 `--window-size` | [headless-cli](https://developer.chrome.com/docs/automation-and-testing/headless-cli)（Last updated 2024-10-21） | 一致 |
| chromium-headless | `--virtual-time-budget` 快进计时器，代替猜测的 sleep | 同页 §--virtual-time-budget | 一致 |
| chromium-headless | root 下不加 `--no-sandbox` 不产出文件；无 `@page` 时 PDF 为 Letter | 页面未记载（本地实测项）；本机 Chromium 156.0.8078.47 重跑：stderr `Running as root without --no-sandbox is not supported`、无 PDF；加 `--no-sandbox` 后无 `@page` 的 deck `MediaBox [0 0 612 792]` | 一致（重新实测） |

`synced_at` 改为 2026-11-01，notes 更新为 Chromium 156 的复测记录。

## 2026-11-01 D2 回归

覆盖提交：5f3a70f（`export-and-qa.md` decktape 一节更正、新增场景 7）。口径 omp + `openai/gpt-6.1-sol` medium，隔离 VM，
单场景串行，输出 `/tmp/hs-d2/G02-web-misc/html-deck/omp-openai-gpt-6.1-sol-medium/`。基线（场景与夹具与提交内容一致）在提交前跑，
有 skill 与负例在提交后跑。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 7 合作方 deck 键盘翻页导出（今日新增，回归 decktape 更正） | gpt-6.1-sol medium | 无 | false | ◐1 ✔2 ✔3 ✘4 ✘5 | 129 s。没用 decktape，自写 `puppeteer-core` 脚本（系统 Chromium、`--no-sandbox`）逐页按 `ArrowRight` 打印并用 `pdf-lib` 合并，不改 HTML；从 DOM 数出 5 页并断言 PDF 页数 = PNG 数 = 5。路线本身可行，但未涉及 decktape 的版本与 Node 要求、截图目录行为 |
| 7 | gpt-6.1-sol medium | 有 | true | ✔1 ✔2 ✔3 ✔4 ✔5 | 143 s。decktape `generic --key=ArrowRight`、`--slides=1-5`（指出末页仍改 class 致自动终止不可靠）、`--chrome-path=/usr/bin/chromium` + `--no-sandbox`；「固定 3.16.1：3.17.0 要求 Node ≥22.12，不适合 Node 20.18」；`cd /srv/exports` 后用相对名 `vendor.pdf` 避开 3.16.1 的截图目录拼接；`pdfinfo` + `pdftotext` 逐页核对标题顺序 |
| 5 负例（响应式落地页） | gpt-6.1-sol medium | 有 | false | 3/3 | 386 s。按响应式网页做：桌面整屏吸附、手机自然滑动与折叠菜单、带校验的订阅表单；未引入翻页键位、备注或逐页 PDF |

结论：通过。场景 7 的 E4（3.17.0 的 Node 22.12 要求）与 E5（截图目录按版本处理）基线 ✘、有 skill ✔，均来自今日更正；
负例 `skill_read=false`，description 今日未改。
