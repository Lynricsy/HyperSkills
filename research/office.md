# office 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-10（种子报告）
- 复核日期：2026-09-10（本文件全部 stars / `pushed_at` / license 于当日经 GitHub API 重新核对，匿名可用，未触发限流）
- 检索途径：
  - `web_search`：`agent skill SKILL.md docx pptx xlsx pdf office document generation github 2026`
  - 官方组织仓库：`anthropics/skills`、`openai/skills`、`github/awesome-copilot`、`googleworkspace/cli`
  - 聚合器（只用于发现，本身不作候选）：VoltAgent/awesome-agent-skills、ComposioHQ/awesome-claude-skills、addyosmani/agent-skills
  - 库官方文档：docx.js.org、PptxGenJS、openpyxl、python-docx、pypdf、pdfplumber、reportlab、pandoc、LibreOffice help
- GitHub API 核对方式：`https://api.github.com/repos/<owner>/<repo>` 取 `stargazers_count` / `pushed_at` / `license.spdx_id` / `archived`

补搜相对种子报告新增 3 个候选（#22–24），种子报告中 8 个标 *unverified* 的候选本次全部核实完毕。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | anthropics/skills `skills/docx` | https://github.com/anthropics/skills | 175538 | 2026-09-03 | Proprietary（skill 内 1467 B LICENSE.txt，禁复制 / 禁衍生 / 禁再分发） | Word 创建、OOXML 编辑、修订、评论 | 3 | 3 | 3 | 3 | 0 | 12 | **REFERENCE ONLY** | 内容质量最高，但 no-derivatives 许可禁止合入；只作主题清单与质量基准 |
| 2 | anthropics/skills `skills/pptx` | 同上 | 175538 | 2026-09-03 | Proprietary | pptxgenjs、模板填充、设计、QA | 3 | 3 | 3 | 3 | 0 | 12 | **REFERENCE ONLY** | 同上；其颜色论断经本机复测已过时（见冲突 C3） |
| 3 | anthropics/skills `skills/xlsx` | 同上 | 175538 | 2026-09-03 | Proprietary | 公式而非值、强制重算、openpyxl 陷阱、财务模型 | 3 | 3 | 3 | 3 | 0 | 12 | **REFERENCE ONLY** | 同上；其 `_xlfn` / LibreOffice 兼容清单经本机复测结论不同（见冲突 C2） |
| 4 | anthropics/skills `skills/pdf` | 同上 | 175538 | 2026-09-03 | Proprietary | 表单、表格、OCR、合并拆分 | 3 | 3 | 3 | 3 | 0 | 12 | **REFERENCE ONLY** | 同上；8 个表单脚本一个都不能抄 |
| 5 | openai/skills `skills/.curated/pdf` | https://github.com/openai/skills | 26819 | 2026-09-08 | **Apache-2.0**（skill 内 LICENSE.txt，10776 B，当日核实为 Apache 2.0 全文） | reportlab / pdfplumber / pypdf + 渲染质检 | 3 | 3 | 2 | 3 | 2 | 13 | **INCLUDE** | 唯一许可干净的第一方 PDF skill；「渲染后目视零缺陷才交付」的交付门是本 skill 的脊梁。仓库上游已标 deprecated，按冻结源处理 |
| 6 | github/awesome-copilot `skills/md-to-docx` | https://github.com/github/awesome-copilot | 38842 | 2026-09-10 | MIT | 纯 JS Markdown→Word | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE** | 厂商自有 MIT，零原生依赖；`scripts/md_to_docx.mjs` 按同一思路重写并扩展 |
| 7 | nexu-io/open-design `skills/pptx` | https://github.com/nexu-io/open-design | 95301 | 2026-09-10 | Apache-2.0 | 声称 pptx 导出 | 1 | 3 | 0 | — | 2 | 6 | **REJECT 为 merged / 降为 reference** | 审计结论：整个 skill 只有 1221 B，正文就是「去装 anthropics 上游」的目录条目，没有任何自有技术内容（见「open-design 审计」节） |
| 8 | SlideSpeak/slide-design-skill | https://github.com/SlideSpeak/slide-design-skill | 20 | 2026-06-25 | MIT | 幻灯片视觉设计 | 1 | 2 | 2 | 2 | 2 | 9 | **INCLUDE（部分）** | 「风格从 brief 推导而非从主题菜单挑」+ 四条代码强制的设计红线；引擎是 HTML 渲染器，与本 skill 无关，只取设计立场 |
| 9 | ourarash/markdown-docx-tool | https://github.com/ourarash/markdown-docx-tool | 0 | 2026-06-22 | MIT | pandoc + reference.docx | 0 | 2 | 3 | 3 | 2 | 10 | **INCLUDE（部分）** | 零 star，但 `custom-style` callout + reference.docx 的做法是「必须套用公司模板」场景的唯一正解；只取技术路径 |
| 10 | K-Dense-AI/scientific-agent-skills `skills/{pptx,xlsx}` | https://github.com/K-Dense-AI/scientific-agent-skills | 44212 | 2026-09-07 | 仓库 MIT / skill frontmatter 写 Proprietary | Anthropic 内容逐字复制 | 0 | 3 | 3 | 3 | 0 | 9→**REJECT** | 许可洗白：MIT 仓库内逐字搬运专有内容，frontmatter 仍写 `license: Proprietary`。合入它等于合入缺陷 |
| 11 | appautomaton/document-SKILLs | https://github.com/appautomaton/document-SKILLs | 158 | 2026-09-10 | MIT（标签不可信） | docx/pptx/xlsx/pdf | 0 | 3 | 2 | 2 | 0 | 7→**REJECT 为源** | 派生自 2025 年版 Anthropic 文档 skill 后改标 MIT。只借鉴两点结构惯例：PDF 参考按 forms/tables/ocr 拆分、脚本用 PEP 723 内联依赖 |
| 12 | claude-office-skills/skills | https://github.com/claude-office-skills/skills | 459 | 2026-01-31 | MIT | Office 集合 | 1 | 0 | 1 | — | 2 | 4 | **REJECT** | 7 个多月无推送，破 6 个月线；内容镜像官方 skill |
| 13 | tfriedel/claude-office-skills | https://github.com/tfriedel/claude-office-skills | 823 | 2026-04-01 | 无 | Office 工作流 | 1 | 1 | 1 | — | 0 | 3 | **REJECT** | 5 个多月无推送，且其 README 自己让用户改用 Anthropic 仓库 |
| 14 | JPeetz/agent-skills `document-processing` | https://github.com/JPeetz/agent-skills | 7 | 2026-09-07 | 无 | 四格式合一 | 0 | 3 | 1 | 1 | 0 | 5 | **REJECT** | 零采纳；且「四格式塞进一个 skill」正是我们要避免的形状——不过本仓库另有取舍，见「粒度决定」节 |
| 15 | dirnbauer/webconsulting-skills | https://github.com/dirnbauer/webconsulting-skills | 33 | 2026-07-27 | NOASSERTION，**仓库已归档** | 同上 | 0 | 1 | 1 | — | 0 | 2 | **REJECT** | 已归档，无维护 |
| 16 | Oddimus/openai-skills `skills/.curated/spreadsheet` | https://github.com/Oddimus/openai-skills | 0 | 2026-03-26 | 无 | openai/skills 的 fork | 0 | 0 | 1 | — | 0 | 1 | **REJECT** | 陈旧 fork；其 `spreadsheet` 已从上游删除 |
| 17 | hu568/md-to-word | https://github.com/hu568/md-to-word | 0 | 2026-08-06 | **AGPL-3.0** | MD→Word | 0 | 2 | 1 | — | 0 | 3 | **REJECT** | 零采纳，且 AGPL 与本仓库 MIT 不兼容 |
| 18 | jimmystridh/google-docs-skill | https://github.com/jimmystridh/google-docs-skill | 0 | 2026-02-08 | MIT | Google Docs | 0 | 0 | 1 | — | 2 | 3 | **REJECT** | 超 6 个月无推送；且 Google Workspace 不在本 skill 范围 |
| 19 | taylorwilsdon/google_workspace_mcp | https://github.com/taylorwilsdon/google_workspace_mcp | 3139 | 2026-09-08 | MIT | Workspace via MCP | 2 | 3 | 2 | — | 2 | 9 | **REJECT（范围外）** | 绑定 MCP 运行时，且属 Google Workspace，本 skill 的否定边界正是它 |
| 20 | bowenliang123/markdown-exporter | https://github.com/bowenliang123/markdown-exporter | 268 | 2026-08-13 | Apache-2.0 | 多格式导出 | 1 | 2 | 1 | 2 | 2 | 8 | **MAYBE→不采用** | 相对 pandoc 无边际价值，是薄 CLI 包装 |
| 21 | eugenelim/agent-ready-repo `markdown-to-docx` | https://github.com/eugenelim/agent-ready-repo | 21 | 2026-09-10 | Apache-2.0 | docxtpl + Jinja 模板 | 0 | 3 | 2 | 2 | 2 | 9 | **MAYBE→不采用** | docxtpl 品牌模板思路已被 pandoc reference.docx 路径覆盖，不必引入第三条路 |
| 22 | lamvu211/office-skills | https://github.com/lamvu211/office-skills | 4 | 2026-05-25 | MIT | Office 全格式 | 0 | 1 | 1 | — | 2 | 4 | **REJECT** | 补搜新增；4 star，越南语文档，四格式合一，无独有内容 |
| 23 | agent0ai/agent-zero `plugins/_office/skills/office-artifacts` | https://github.com/agent0ai/agent-zero | 19135 | 2026-09-09 | NOASSERTION | Office artifacts | 1 | 3 | 1 | — | 0 | 5 | **REJECT** | 补搜新增；绑定 agent-zero 的 `office_artifact` 工具，且优先 LibreOffice 原生格式，与「交付 OOXML」目标冲突 |
| 24 | officecli/officecli `skills/officecli` | https://github.com/officecli/officecli | 101 | 2026-08-10 | MIT | 自有 CLI 包装 | 1 | 2 | 1 | — | 2 | 6 | **MAYBE→不采用** | 补搜新增；要求安装其专有 CLI，portability 差于直接用库 |
| 25 | phodal/routa `tools/office-skills/.agents/skills/spreadsheets` | https://github.com/phodal/routa | 1812 | 2026-08-13 | MIT | 表格 skill | 2 | 2 | 1 | — | 2 | 7 | **MAYBE→不采用** | 种子报告标 unverified，本次核实：作者知名但该 skill 只是大工具仓里的附属品，无 openpyxl 层面的具体陷阱 |

聚合器（仅用于发现）：VoltAgent/awesome-agent-skills、ComposioHQ/awesome-claude-skills、addyosmani/agent-skills（工程类，无 Office）。

## 深度审查

### anthropics/skills 四件套（#1–4，REFERENCE ONLY）

`skills/{docx,pptx,xlsx,pdf}/LICENSE.txt` 是同一份 1467 B 专有许可（blob `c55ab42224874608473643de0a85736b7fec0730`），明文禁止
「Extract these materials … Reproduce or copy … **Create derivative works based on these materials** … Distribute, sublicense, or transfer」。
同仓库其余 skill 用的是另一份 11345 B 宽松许可（blob `4f881c52…`），说明这四个是**故意的例外**。

**本 skill 对这四个上游的使用方式，逐条说明：**

1. 只读取了各 `SKILL.md` 的**章节标题**（`^#{2,4} ` 行），用于列出「一个 Office skill 必须覆盖哪些主题」的清单：
   - docx：`Creating with docx-js — gotchas` / `Verify the output` / `Editing existing documents` / `Comments` / `Dependencies`
   - pptx：`Scripts` / `Creating with pptxgenjs — gotchas` / `Editing existing decks and templates` / `Design Ideas` / `Color Palettes` / `Typography` / `Spacing` / `Avoid (Common Mistakes)` / `QA (Required)` / `Content QA` / `File QA` / `Visual QA` / `Converting to Images` / `Dependencies`
   - xlsx：`Requirements for every output` / `Recalculate (mandatory …)` / `Choosing formulas that survive verification` / `openpyxl gotchas` / `Financial models` / `Dependencies`
   - pdf：`pypdf - Basic Operations` / `pdfplumber - Text and Table Extraction` / `reportlab - Create PDFs` / `Command-Line Tools` / `Common Tasks`（水印、抽图、加密、扫描件）
2. **未复制任何文字**：`SKILL.md`、`references/*.md` 的正文一律未进入本仓库。
3. **未复制任何脚本**：其 `scripts/office/`（`soffice.py`、`validate.py`、`validators/*`，约 79 KB Python）与 `schemas/`（约 40 个 XSD，约 700 KB）、`docx/scripts/{accept_changes,comment,merge_runs}.py`、`pptx/scripts/{add_slide,clean,thumbnail}.py`、`xlsx/scripts/recalc.py`、`pdf/scripts/*`（8 个）一个都没有读入或改写。本 skill 的 6 个脚本全部自写。
4. **未复制任何数据文件**：其 `docx/scripts/templates/*.xml`（评论六部件模板）与全部 XSD 未使用；`references/docx-tracked-changes-comments.md` 的评论部件清单由 ECMA-376 语义与本机实验重写。
5. `SOURCES.yaml` 中四条均为 `relation: reference`，`license: Proprietary`，`notes` 写明未复制内容。校验器亦拒绝 `Proprietary` + `merged`。
6. 冲突处理上，凡其论断与本机复现结果不一致，**以本机复现为准并在下节记录**（C2、C3）。这既是正确性要求，也进一步说明本 skill 的规则并非转述而来。

其 frontmatter 只用 `name` / `description` / `license`，`description` 极长且含显式负触发（"Do NOT use for PDFs, spreadsheets, Google Docs…"）——这条**惯例**（不是文字）被本仓库标准第 1.1 节吸收：description 必须含否定边界。

### openai/skills `.curated/pdf`（#5，INCLUDE）

当日核实 `skills/.curated/pdf/LICENSE.txt` = Apache-2.0 全文（10776 B），因此可 merged。SKILL.md 约 2.3 KB，只有 `name` / `description`。
内容骨架：render→inspect→fix 循环、`uv pip install reportlab pdfplumber pypdf`、poppler 安装行、临时目录约定、质量期望（无裁切文字、无黑块、只用 ASCII 连字符、不留工具 token）、最终检查。
无表单支持，表格/OCR 也没有——这三块由本 skill 自写。
最有价值的一句是交付门的定位：**「渲染出的 PNG 目视零缺陷之前不交付」**，本 skill 把它扩展成三层门（库往返 / 转换 / 目视）。

### github/awesome-copilot `skills/md-to-docx`（#6，INCLUDE）

MIT，厂商自有，当日仍在推送。`SKILL.md` + `scripts/md-to-docx.mjs` + `scripts/package.json`，纯 JS（`docx` 9+、`marked` 15+），无 pandoc / LibreOffice / 原生二进制。
特性：YAML front matter→标题页、H1–H3 目录、PNG 内嵌（从 PNG 头读尺寸并缩放到 6 英寸）、Calibri + `#1F3864` 标题、表格隔行底色、Consolas 代码块。
缺口：只支持 PNG。本仓库的 `scripts/md_to_docx.mjs` 按同一思路**重写**，并补上 JPEG/GIF/BMP、嵌套/有序列表、块引用、`ImageRun` 的显式 `type`（见 C1）、以及「不支持的图片格式给出可见提示而非静默丢弃」。

### SlideSpeak/slide-design-skill（#8，部分 INCLUDE）

20 star，2026-06-25 推送（在 6 个月线内），MIT。本体是一个把 brief 渲染成 1920×1080 HTML 幻灯片的引擎（`npm install`，可选 `FAL_KEY` 生成配图），**与本 skill 的 pptx 管线无关**。
可用的是它的设计立场：「**风格是推导出来的，不是从主题菜单里挑的**」，以及四条由代码而非提示词强制的红线——可读字号、不留空白带、不用 logo 与商标、不编数字。
这四条重写后进入 `references/pptx-design.md`（「Decide before drawing」与「Avoid list」）。其 HTML/React 渲染栈、`docs/INTEGRATION.md`、`docs/SKILL-FORMAT.md` 均未使用。

### ourarash/markdown-docx-tool（#9，部分 INCLUDE）

0 star、MIT、2026-06-22。权威性 0 分，但它是**唯一**认真处理「Word 输出必须套公司模板」的候选：pandoc + 随包 `reference.docx` + `custom-style` callout（Note / Tip / Important / Warning / Risk / Caution / InfoBox / Decision / Open Question）+ DOCX 后处理（宽表自适应、表后间距、去掉生成的标题书签）。
取用的是技术路径与两条硬约束：callout 的 `::: {custom-style="Name"}` 写法，以及**样式名在模板中不存在时 pandoc 静默不加样式**。其 `reference.docx`、`scripts/*.sh|ps1|py`、Mermaid 包装均未使用；本 skill 改为教用户用 `pandoc --print-default-data-file=reference.docx` 自建模板。

### open-design 审计（#7，从 merged 降为 reference）

计划要求「必须与 anthropic-pptx 逐段文本比对，凡雷同段落不采用」。**审计结果：无需比对，因为没有可比的正文。**

`nexu-io/open-design@main:skills/pptx/SKILL.md` 全文 1221 B，结构如下：

- frontmatter：`name: pptx`、一段 description、`triggers:` 列表、`od:` 命名空间（`mode: deck`、`category: slides`、
  `upstream: "https://github.com/anthropics/skills/tree/main/skills/pptx"`）
- 正文四节：`> Curated from Anthropic's official skills repository.`、`## What it does`（复述 description 一句）、
  `## Source`（列出上游 URL 与 category）、`## How to use`（原话大意：这只是让 agent 在规划时发现该 skill 的**目录条目**，
  要跑完整流程请自行去上游装原始 assets / scripts / references，并给了一行 `open <上游 URL>`）

结论：

1. **无自有技术内容**：没有 pptxgenjs 陷阱、没有模板填充流程、没有 references/、没有 scripts/、没有设计规则。
2. **不是许可洗白**：它没有搬运 Anthropic 的正文，只是指向 URL；与 anthropic-pptx 的文本重合仅限于「pptx」这类不可版权化的词，
   不存在雷同段落，因此「凡雷同段落不采用」这条规则实际上无触发点。
3. 因此它的 Apache-2.0 是可靠的，但**可合入的内容为零**。`SOURCES.yaml` 保留该条目并改为 `relation: reference`，
   `contributes` 写「审计后确认贡献为零」，`notes` 记录上述审计，避免半年后有人再花时间重新评估它。

### 粒度决定：为什么本仓库是一个 `office` 而不是四个 skill

种子报告基于 body size 与 description 消歧推荐拆成四个 sibling。本仓库采用**一个 `office`**，理由是仓库层面的约束不同：

- 本仓库标准第 2.1 节把 `SKILL.md` 限死 ≤500 行并要求「进阶披露」：11 个 `references/*.md` 承担全部格式细节，
  `SKILL.md` 只有路由表 + 交付门 + Core rules。真正被加载的 token 量由 topic router 决定，而不是由 skill 个数决定。
- 四层交付门（库往返 / soffice 转换 / 目视渲染 / xlsx 重算）与字体替换规则是**四个格式共用的**。拆成四个 skill 会让这套门重复四遍，
  也会让 `scripts/render_preview.py` 需要在四处各存一份或引入 `_shared/`（而所有主流 agent 的发现都是一级扁平扫描，`_shared/` 不可靠）。
- `docs/roadmap.md` 的粒度是「一类事情 = 一个 skill」，本 skill 的那类事情是「交付一个 Office / PDF 文件」。
- 消歧靠 description 的否定边界（Google Workspace / HTML / 纯分析）而非靠 skill 个数——负例评测场景 4 就是在测这一点。

`google-workspace` 仍是独立主题（工具链、认证、依赖完全不重叠），已在 `docs/roadmap.md` Batch 5 之外单列。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| C1 | docx-js `ImageRun` 是否必须给 `type` | 种子计划：必须；docx 9.7.1 构造与打包都不抛错 | **必须给**，且理由改写为「静默产出不可读包」 | 本机复现：省略 `type` 时媒体部件写成 `word/media/<hash>.undefined` 且无 content-type；`soffice` 仍能转 PDF，`python-docx` 抛 `KeyError: no content type for partname`。这同时证明「库往返」与「转换」两道门不可互相替代 |
| C2 | LibreOffice 能否算 `XLOOKUP` / `FILTER` / `UNIQUE` / `SORT` / `SEQUENCE` / `XMATCH` | anthropic-xlsx（经种子报告转述）：这六个 LibreOffice 完全算不了 | **不采用该说法。** 真正的规则是：① 裸函数名 → `#NAME?` / `#VALUE!`；② 加 `_xlfn.` 前缀后**可以算**（`_xlfn.XLOOKUP`→20，`_xlfn.XMATCH`→2，`_xlfn.UNIQUE`→10，`_xlfn.SEQUENCE`→1，`_xlfn.IFS`、`_xlfn.TEXTJOIN`、`_xlfn.TEXTAFTER` 均正确）；③ `FILTER` / `SORT` 需要 `_xlfn._xlws.` 双段前缀，`_xlfn.FILTER` / `_xlfn.SORT` 仍是 `#NAME?`；④ **真正的杀手是动态数组不 spill**——openpyxl 不写 spill 元数据，`_xlfn.SEQUENCE(3)` 只在锚点格得到 `1`，相邻格为空，而截断的数组**不是错误值**，重算扫描报 0 错误 | 本机 LibreOffice 26.2.5.2 + openpyxl 3.1 的 21 条公式测试矩阵（见「备注」）。裁决口径「更新 > 更旧」+ 官方文档语义（`_xlfn.` 是 OOXML 文件格式对 2007 后函数的存储形式），并据此把正文规则改成「宁可写非 spill 等价式」 |
| C3 | pptxgenjs 颜色 `#` 前缀是否损坏文件 | anthropic-pptx（经种子报告转述）：`#` 前缀或 8 位 hex **会损坏文件** | **不采用。** pptxgenjs 4.0.1 的 `createColorElement` 先 `replace('#','')`，因此 `'#1F3864'` 正常产出 `srgbClr val="1F3864"`；8 位 hex `'1F3864FF'` 与 CSS 名 `'navy'` 则被**静默替换为 `000000`**，只在 stderr 打一条 `console.warn`，文件照样写出、照样能打开。正文规则改为「六位 hex 或 `pptx.SchemeColor`；8 位与颜色名会变黑」 | 本机复现 4 组颜色 + 读 `node_modules/pptxgenjs/dist/pptxgen.cjs.js:745-763` 源码确认逻辑 |
| C4 | 是否自写 OOXML XSD 校验器 | Anthropic 用约 79 KB Python + 约 700 KB XSD 做 schema 校验；本仓库不能抄 | **不写。** 交付门改为三层：① 库往返打开（python-docx / python-pptx / openpyxl / pypdf）；② `soffice --headless --convert-to pdf` 成功；③ `pdftoppm` 渲染后逐页目视。xlsx 追加 `scripts/xlsx_recalc.py` 重算并扫错误格；修订追加 pandoc accept/reject 双向核对 | 计划硬约束；且本机实验证明这三层的覆盖面互补（C1 的 `.undefined` 只有第①层能抓，畸形 zip 只有第②层能抓，溢出只有第③层能抓） |
| C5 | 修订（tracked changes）用什么门验证 | 直觉做法：渲染看图 | **不用渲染。** LibreOffice 导出 PDF 会同时画出删除与插入文本，正确的修订标记渲染出来是 `net 6030`，看起来像 bug。改用 `pandoc --track-changes=reject` 必须还原原文、`--track-changes=accept` 必须显示新文本 | 本机复现：同一份 `w:del`+`w:delText`+`w:ins` 文档，reject→`net 60`、accept→`net 30`、PDF→`net 6030` |
| C6 | 读取 docx 的默认行为 | 直觉：`pandoc -f docx` 得到文档内容 | 正文写明 **pandoc 默认等于 `--track-changes=accept`**，会静默返回「已接受」的文本，隐藏文档还有待审修订这一事实；读可能带修订的文档必须 `--track-changes=all` | 本机复现：带未接受修订的文档，`pandoc -f docx -t markdown` 输出 `net 30`（新值） |
| C7 | 字体白名单是静态清单还是可执行检查 | 种子计划：给一份 LibreOffice 度量兼容白名单（Arial、Calibri、Cambria、Times New Roman、Courier New…） | **改成可执行检查 + 分层白名单。** 本机 `fc-match` 实测：Arial→Liberation Sans、Times New Roman→Liberation Serif、Courier New→Liberation Mono（均度量兼容）；**Calibri→Noto Sans、Cambria→Noto Serif**（Carlito / Caladea 未安装，度量**不**兼容）；Aptos→Noto Sans。所以静态白名单会骗人，正文要求先跑 `fc-match <font>` 确认替换字体，并给出安装 Carlito/Caladea 的命令 | 本机 `fc-match` / `fc-list` 输出（见「备注」）。Aptos 依然全局禁用 |
| C8 | 编辑既有文件 vs 重新生成 | 无上游冲突，但是 agent 最常见的错误路径 | Core rules 写死「编辑既有文件，绝不用抽取结果重建」，理由是抽取有损（样式、页眉、域、修订全丢） | pandoc / markitdown 的抽取输出本身即证据 |
| C9 | pypdf 复选框赋值 | 直觉：`True` 或 `"Yes"` | 必须用带斜杠的外观状态名（如 `"/Yes"`），且状态名要从 widget 的 `/AP /N` 键读。`True` / `"Yes"` / `"1"` / `"/1"` 全部**静默**留在 `/Off` | 本机复现（pypdf 6.18.0）：只有 `"/Yes"` 使 `/V` 与 `/AS` 变为 `/Yes` |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| anthropic-docx | anthropics/skills `skills/docx` | **reference** | Word 主题覆盖清单与质量基准；未复制任何内容 |
| anthropic-pptx | anthropics/skills `skills/pptx` | **reference** | 幻灯片主题覆盖清单（含 QA 三分层与设计小节的存在性）；未复制任何内容 |
| anthropic-xlsx | anthropics/skills `skills/xlsx` | **reference** | 表格主题覆盖清单（公式而非值、强制重算、财务模型约定）；未复制任何内容 |
| anthropic-pdf | anthropics/skills `skills/pdf` | **reference** | PDF 主题覆盖清单（表单 / 表格 / OCR / 合并拆分）；未复制任何内容 |
| openai-pdf | openai/skills `skills/.curated/pdf` | merged | render→inspect→fix 循环与「目视零缺陷才交付」交付门；PDF 三库分工 |
| copilot-md-to-docx | github/awesome-copilot `skills/md-to-docx` | merged | 零原生依赖的 Markdown→Word 路径与 front matter 标题页 / 目录 / 图片按头部尺寸缩放 |
| open-design-pptx | nexu-io/open-design `skills/pptx` | **reference** | 审计后确认贡献为零；条目保留以记录审计结论 |
| slidespeak-design | SlideSpeak/slide-design-skill | merged | 「风格从 brief 推导」与四条设计红线 → `references/pptx-design.md` |
| ourarash-md-docx | ourarash/markdown-docx-tool | merged | pandoc + reference.docx 与 `custom-style` callout 路径 |
| docx-js-docs / pptxgenjs-docs / openpyxl-docs / python-openxml-docs / pypdf-docs / pdfplumber-docs / reportlab-docs / pandoc-docs / libreoffice-docs / ecma-376 | 各官方文档 | merged (docs) | 全部 API 语义与 OOXML 标记语义的来源 |

## 评测先行与评测改写

`evals/evals.json` 共 5 个场景（4 正例 + 1 负例）。第一版跑完默认模型基线后发现**区分度不足**：
会话默认模型（opus-5）在原 4 个场景里几乎全达成。按 `docs/skill-standard.md` 第 6 节
「基线全部达成 = 评测无区分度，必须改写」，做了两处改写并重跑相应基线：

1. 场景 1（xlsx）原来只要求「增长率一处可改」，太容易。改写为**必须做一次跨表查表**
   （区域 → COGS 率），从而把 `_xlfn.` 前缀与动态数组截断这两个真实陷阱逼到台面上。
2. 新增场景 5（PDF AcroForm 填表 + 勾选复选框），针对 pypdf 复选框必须传带斜杠的
   on-state 名这一条已本机复现的静默失败。
3. 场景 2 的行为 1 在四组跑完后把措辞从「并说明 8 位 hex 会变黑」收紧为
   **产物可核查**的形式（生成脚本里不得出现 8 位 hex / `rgb()` / CSS 颜色名）。
   query 未变，故四组产物仍是有效证据；判定改为直接检查落盘的生成脚本（见「备注」的核查命令）。

另外**额外多跑了一组** smol 模型的无 skill 基线（Contract 只要求三组），因为默认模型基线太强，
不跑 smol 基线就无法诚实回答「smol 上 skill 填了哪些缺口」。

## 基线缺口

无 skill 时未达成的 `expected_behavior`（判定依据是逐个读 `answer.md` 与落盘产物）：

| 场景 | 模型 | 未达成的行为 | 说明 |
|---|---|---|---|
| 1 xlsx | default | b4 重算 + 错误格扫描并报告 | 用 LibreOffice headless 重算并报了数值，但没有做也没有报告「错误格扫描」（`#NAME?` / `#REF!` / 未计算格），即没有一道可失败的门 |
| 1 xlsx | @smol | b4 同上 | 同样只报数值联动，无错误扫描 |
| 2 pptx | default | b1 颜色写法（改写前的措辞） | 产物核查后按收紧措辞判定为达成；见上节说明 |
| 2 pptx | @smol | b1（同上）、**b3 度量兼容字体** | `build-deck.js` 用 `Georgia` 标题 + `Trebuchet MS` 正文，两者在 Linux 上都没有度量兼容替代字体，于是它「逐页目视无溢出」的结论对真实 Word 折行没有保证 |
| 3 修订 | default | 无（三条全达成） | 该模型自行用 LibreOffice UNO 做了 accept / reject 双向核对 |
| 3 修订 | @smol | **b3 双向解析验证** | 只把文件转成 fodt 看有没有 `text:tracked-changes` 区块，属结构检查；没有解析出 accept / reject 两个文本来对照 |
| 5 PDF 表单 | default / @smol | 无（三条全达成） | 两个模型都自己从 `/AP /N` 读出了 `/Yes` |
| 4 负例 | default / @smol | 无 | `skill_read == false`，且都改用 Sheets API / 导出往返回答 |

## 评测结果

`skill_read` 取自 `result.json`；行为判定为人工读 `answer.md` + 核查落盘产物。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 xlsx 查表模型 | default | 无 | false | b1 b2 b3（3/4） | VLOOKUP（2007 前函数，无需前缀）；重算但无错误扫描 |
| 1 | default | 有 | **true** | **b1 b2 b3 b4（4/4）** | 选 INDEX/MATCH 并写明「裸 XLOOKUP 重算成 `#NAME?`、加 `_xlfn.` 后动态数组被静默截断」；跑 `xlsx_recalc.py`，报 12 个公式 0 错误 |
| 1 | @smol | 无 | false | b1 b2 b3（3/4） | 同默认基线 |
| 1 | @smol | 有 | **true** | **b1 b2 b3 b4（4/4）** | 同样 INDEX/MATCH + 理由；报 `xlsx_recalc.py 干净（0 错误）` |
| 2 pptx 投资 deck | default | 无 | false | b1 b2 b3（3/3） | Arial + 六位 hex + 渲染 6 页目视 |
| 2 | default | 有 | **true** | b1 b2 b3（3/3） | Arial 并写出 `fc-match → Liberation Sans，等宽度替代，所以渲染里的折行就是观众看到的折行`；150 dpi 渲染 6/6 |
| 2 | @smol | 无 | false | b1 b2（2/3） | **b3 未达成**：Georgia + Trebuchet MS |
| 2 | @smol | 有 | **true** | **b1 b2 b3（3/3）** | 改用 Arial 并注明「有度量兼容替代字体」；渲染 6/6 逐页看 |
| 3 docx 修订 | default | 无 | false | b1 b2 b3（3/3） | 自行用 UNO 做 accept / reject |
| 3 | default | 有 | **true** | b1 b2 b3（3/3） | pandoc reject 复现原文、accept 显示 net 30；并主动说明「渲染显示 `net 6030` 属正常，不能拿渲染当门」 |
| 3 | @smol | 无 | false | b1 b2（2/3） | **b3 未达成**：只看 fodt 结构 |
| 3 | @smol | 有 | **true** | **b1 b2 b3（3/3）** | pandoc reject / accept / all 三条都跑了 |
| 4 负例 Google Sheets | default | 无 | false | 2/2 | — |
| 4 | default | 有 | **false** ✅ | 2/2 | 明确回答「office skill 排除 Google Docs/Sheets/Slides」，给导出往返与 Sheets API 两条路 |
| 4 | @smol | 无 | false | 2/2 | — |
| 4 | @smol | 有 | **false** ✅ | 2/2 | 同上 |
| 5 PDF 表单 | default | 无 | false | b1 b2 b3（3/3） | 自行从 `/AP /N` 读出 `/Yes` |
| 5 | default | 有 | **true** | b1 b2 b3（3/3） | 用 `pdf_form_fields.py list` 回读 + 渲染 2/2 页 |
| 5 | @smol | 无 | false | b1 b2 b3（3/3） | 同默认基线 |
| 5 | @smol | 有 | **true** | b1 b2 b3（3/3） | 用 `pdf_form_fields.py` 全流程 |

结论：**两种模型都满足「至少一条基线未达成的行为在有 skill 时达成」**。

- 默认模型（opus-5）：填补 1 条——场景 1 的 b4（把「重算并报告错误格扫描」变成一道会失败的门，
  由 `scripts/xlsx_recalc.py` 承担）。这个模型本身极强，本 skill 对它的边际价值主要是
  **把验证从「我算过」变成一条会非零退出的命令**，以及统一的交付报告格式。
- smol 模型：填补 3 条——场景 1 的 b4、场景 2 的 b3（度量兼容字体，直接决定目视检查是否可信）、
  场景 3 的 b3（修订必须双向解析验证，不能看渲染）。
- 负例两组都 `skill_read == false`，说明 description 的否定边界（Google Docs/Sheets/Slides）有效。
- 副产物：两组有 skill 的场景 2 都独立指出 `pptx.md` 把 `LAYOUT_16x9` 写成 13.33×7.5 是错的。
  本机复核确认（`LAYOUT_16x9` = 10×5.625、`LAYOUT_WIDE` = 13.33×7.5），已修正并补进「失败模式」。
  另据默认模型报告，本机复现出 `addChart` 顶层 `fill: {color}` 会抛
  `TypeError: (colorStr || "").replace is not a function`，也已补进 `pptx.md`。

## 备注

### 许可红线执行结果

- `anthropic-{docx,pptx,xlsx,pdf}` 四条：`relation: reference`、`license: Proprietary`，
  只读取了各 `SKILL.md` 的**章节标题**用作主题清单，未复制任何正文、脚本、XSD 或模板 XML。
  详见「深度审查」第一节的逐条说明。校验器亦拒绝 `Proprietary` + `merged`。
- `open-design-pptx`：审计后从 merged 降为 reference，贡献为零，条目保留以记录结论。
- `hu568/md-to-word` 因 AGPL-3.0 与本仓库 MIT 不兼容而 REJECT（种子报告未核出许可）。
- `ecma-376` 无明确再用授权，只取元素语义，示例全部自写，`notes` 已记录。

### 本机实验：每条陷阱的复现证据

环境：LibreOffice 26.2.5.2 / poppler 26.07 / pandoc 3.10.2 / qpdf 12.4 / tesseract 5.5.3 /
node v26.7.0（docx 9.7.1、pptxgenjs 4.0.1、marked 18.0.12）/ python 3.12（openpyxl 3.1、
python-docx 1.2、python-pptx 1.0、pypdf 6.18.0、pdfplumber、reportlab）。

| 规则 | 复现方式 | 观测结果 |
|---|---|---|
| `ImageRun` 缺 `type` | 打包后分别用 python-docx 打开与 soffice 转换 | `python-docx` 抛 `KeyError: no content type for partname '/word/media/<hash>.undefined'`；soffice 照样转出 PDF |
| `PageBreak` 直接放在 section | 打包后转 PDF 数页数 | 直放 = 1 页（分页被忽略）；放进 `Paragraph` = 2 页 |
| `TextRun` 直接放在 section | 转 PDF 后 `pdftotext` | 文本 `bare run` **完全消失**（只剩 `p`）；python-docx 也只看到 1 段 |
| pptxgenjs 颜色 | 写 4 组颜色后读 `ppt/slides/slide1.xml` 的 `srgbClr val` | `1F3864`→`1F3864`；`#1F3864`→`1F3864`（`#` 被 strip）；`1F3864FF`→`000000`；`navy`→`000000`；源码 `pptxgen.cjs.js:745-763` 确认只 `console.warn` |
| pptxgenjs 改写入参 | `addText("t", opts)` 后打印 `opts` | 新增 `color` / `objectName` / `line` / `lineSpacing` / `lineSpacingMultiple` / `_bodyProp` |
| pptxgenjs 布局常量 | 读 `presLayout` | `LAYOUT_16x9` 10×5.625、`LAYOUT_16x10` 10×6.25、`LAYOUT_4x3` 10×7.5、`LAYOUT_WIDE` 13.33×7.5 |
| `addChart` 顶层 fill | 四种写法各写一次 | `fill:{color}` 抛 `TypeError: (colorStr \|\| "").replace is not a function`；`fill:"0B1B33"` / `plotArea.fill` / `chartArea.fill` 正常 |
| python-pptx 无删除 slide API | `dir(prs.slides)` | 只有 `add_slide` |
| `data_only=True` 破坏公式 | openpyxl 写公式 → `data_only=True` 读 → 存 → 再读 | 两次都是 `None`，公式已被值（空）覆盖 |
| 合并单元格非锚点 | `ws["B1"] = x`（`A1:C1` 已合并） | `AttributeError: 'MergedCell' object attribute 'value' is read-only` |
| 公式不被解析 | 写 `=Q3 Data!A1` | openpyxl 无异常；重算得 `#VALUE!` |
| `_xlfn.` 矩阵 | 21 条公式写入后 soffice 重算再读 | 裸名：`XLOOKUP`/`XMATCH`/`UNIQUE`/`SORT`/`SEQUENCE`→`#NAME?`，`FILTER`→`#VALUE!`；带前缀：`_xlfn.XLOOKUP`→20、`_xlfn.XMATCH`→2、`_xlfn.IFS`→`big`、`_xlfn.TEXTJOIN`→`10,20,30`、`_xlfn.TEXTAFTER`→`b`、`_xlfn.UNIQUE`→10、`_xlfn.SEQUENCE`→1、`_xlfn._xlws.FILTER`→20、`_xlfn._xlws.SORT`→10；而 `_xlfn.FILTER` / `_xlfn.SORT` 仍 `#NAME?` |
| 动态数组不 spill | 上表同批，检查相邻列 | 锚点格有值，右侧两格为空，且**重算扫描报 0 错误** |
| 修订双向语义 | 手写 `w:del`+`w:delText`+`w:ins`+ 段落标记删除，再用 pandoc 解析 | reject → `net 60` 且终止句在；accept → `net 30` 且终止句消失；PDF 渲染 → `net 6030` |
| pandoc 默认接受修订 | `pandoc -f docx -t markdown` | 输出 `net 30`（新值），修订待审这一事实被隐藏 |
| zip 目录前缀 | 用 `d/` 前缀重打包 | python-docx `There is no item named '[Content_Types].xml'`；soffice 也拒绝。无前缀 + content types 放首位则两者都通过 |
| `[Content_Types].xml` 顺序 | 分别放首位与末位 | python-docx / pandoc / soffice 三者都接受；写在首位只是与 Office 产物一致 |
| pypdf 复选框 | 依次传 `True` / `"Yes"` / `"1"` / `"/1"` / `"/Yes"` | 只有 `"/Yes"` 使 `/V` 与 widget `/AS` 变为 `/Yes`，其余静默留在 `/Off` |
| 合并表单字段撞名 | 同一份表单 append 两次 | 4 页、6 个 widget、**只有 3 个字段名** → 填一个会同时改两处 |
| 字体替换 | `fc-match` | Arial→Liberation Sans、Times New Roman→Liberation Serif、Courier New→Liberation Mono（均度量兼容）；**Calibri→Noto Sans、Cambria→Noto Serif**（Carlito / Caladea 未装，度量不兼容）；Aptos→Noto Sans |
| pandoc `custom-style` 缺失 | 写一个模板里不存在的样式名 | 仍写出 `<w:pStyle w:val="NoSuchStyle"/>`，无告警，渲染回落默认格式 |

### 脚本端到端验证（在 `/tmp/hs-office/e2e`）

```
$ node .../scripts/md_to_docx.mjs report.md out.docx
wrote out.docx (10286 bytes)
$ python -c "import docx; d=docx.Document('out.docx'); ..."
python-docx OK paras=23 tables=1
$ uv run .../scripts/render_preview.py out.docx
out-1.png / out-2.png / out-3.png        # 已逐页目视：标题页、目录页、正文（标题/粗斜体/超链接/表格底色/项目符号/有序编号/代码底纹/引用竖线/分隔线）

$ node mkdemo.mjs                        # references/docx.md 的 docx-js 写法
wrote demo.docx 9562
$ uv run .../scripts/render_preview.py demo.docx
demo-1.png / demo-2.png

$ python mkxlsx.py                       # references/xlsx.md 的假设区 + 公式写法，外加一处故意 =1/0
wrote demo.xlsx
$ uv run .../scripts/xlsx_recalc.py demo.xlsx
demo.xlsx: 12 formula cell(s) recalculated, 1 problem(s)
  Model!B11  #DIV/0!  <-  =1/0
EXIT=1                                   # 发现错误即非零退出 ✅

$ uv run .../scripts/office_unpack.py demo.docx d/
unpacked 19 part(s) into d
$ uv run .../scripts/office_pack.py d/ demo2.docx
packed 19 part(s) into demo2.docx
$ soffice --headless --convert-to pdf demo2.docx
convert ... -> demo2.pdf                 # 成功 ✅

$ uv run .../scripts/pdf_form_fields.py list form.pdf
form.pdf: 3 field(s), 2 page(s)
  vendor_name  [text]  value=''
  amount  [text]  value=''
  approved  [button]  value='/Off'  states=['/Off', '/Yes']
$ uv run .../scripts/pdf_form_fields.py fill form.pdf filled.pdf --set vendor_name="Acme Ltd" --set approved=/Yes
wrote filled.pdf / vendor_name = 'Acme Ltd' / approved = '/Yes'          EXIT=0
$ uv run .../scripts/pdf_form_fields.py fill form.pdf x.pdf --set nope=1
error: field 'nope' not found. Available: vendor_name, amount, approved   EXIT=2
$ uv run .../scripts/pdf_form_fields.py fill form.pdf y.pdf --set approved=Yes
error: 'Yes' is not a state of checkbox 'approved'. Use one of ['/Off', '/Yes'] ... EXIT=2
```

### references 里的代码块逐个跑过

在 `/tmp/hs-office/refcheck` 把 `docx.md` / `xlsx.md` / `pptx.md` / `pdf.md` /
`pdf-forms-tables-ocr.md` 的可执行代码块抽出来原样运行：docx 骨架 + 表格 + 图片三块打包后
python-docx 均可打开；xlsx 骨架跑完 `xlsx_recalc.py` 报 `11 formula cell(s), 0 problems`；
pptx 骨架产出 13.33×7.5 的 deck 并渲染目视确认；pdf 的 platypus / 合并拆分旋转 / 抽取 /
元数据 / 水印 / 加密块全部执行成功（`encrypted: True`）；表单覆盖层块打印出真实坐标
（`{'text': 'Vendor', 'x0': 72.0, 'top': 62.48, ...}`），据此把参考里原本举例用的坐标改成实测值。
发现并修掉的自有错误共 4 处：`LAYOUT_16x9` 尺寸、pandoc `--print-default-data-file` 写法、
pandoc 样式名清单里的 `Source Code`（该版本实为 `VerbatimChar`）、覆盖层示例坐标。

### 安装冒烟与静态门

```
$ npx skills@latest add /root/Projects/Ling/HyperSkills --skill office --agent universal --copy --yes
✓ office (copied) → ./.agents/skills/office
$ ls .agents/skills/office            # SKILL.md SOURCES.yaml evals references scripts
$ ls .agents/skills/office/references | wc -l   # 11
$ uv run tools/validate_skills.py skills/office 2>&1 | grep -v NOTICE
FAIL office / 1 skill(s): 1 error(s)   # 仅剩 NOTICE.md is missing（由主代理生成）
```

校验器最初报了两条 `dynamic command injection '!\``：来自 `#REF!` / `#VALUE!` 这类以 `!` 结尾的
错误值紧挨着反引号。改为不加代码反引号书写即消除，规则本身未变。

### 未来同步时要盯的上游

- `openai/skills` 已标 deprecated：按冻结源处理，不必追新；若仓库归档，`check_upstream.py` 会报 MISSING。
- `anthropics/skills` 四条是 reference：同步时只需重读章节标题，确认没有出现本 skill 完全没覆盖的新主题。
- pptxgenjs / docx / openpyxl / pypdf 是行为来源：**升级大版本后必须重跑本节的复现矩阵**，
  因为本 skill 有 4 条规则直接依赖具体版本行为（颜色回退、布局常量、`_xlfn.` 支持、复选框状态名）。
- 字体：`fc-match Calibri` 在本机不是 Carlito。若目标环境装了 `fonts-crosextra-carlito`，
  `references/render-qa-fonts.md` 的判断会变，故该规则写成「先跑 `fc-match` 再决定」而非静态清单。

### 放弃的方向

- 自写 OOXML XSD 校验器（C4）：成本远高于收益，三层门 + 重算 + 修订双向核对已覆盖实测中出现的全部失败模式。
- `google-workspace`：本 skill 的否定边界，独立主题。
- docxtpl / 自有 CLI（`officecli`、`bowenliang123`）：与既有两条 Markdown→Word 路径重复。
