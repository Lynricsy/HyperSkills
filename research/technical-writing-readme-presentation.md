# technical-writing：README 呈现层扩展 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。
> 本文件记录的是对**已有 skill `technical-writing` 的一次更新**，不是新建 skill。
> 原始调研见 `research/technical-writing.md`；本文件只覆盖新增的 README 呈现层。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 起因：`technical-writing` 的 `references/readme.md`（149 行）只有**内容纪律**，
  对首屏构图、视觉资产、`<details>`、GitHub alerts、mermaid、TOC 与锚点、
  跨渲染器可移植性、「读起来像 AI 写的」这七件事**零覆盖**。
  全 skill `grep -i 'shields|badge|banner|logo|screenshot|GIF|mermaid|details>|
  prefers-color-scheme|anchor|back to top|table of contents|AI-generated|slop'`
  只命中 `readme.md` 那 4 行徽章段与 `plain-english.md` 里「图片不会被翻译」一句。
- 检索途径：
  - 用户点名的上游 `fralapo/awesome-agent-skills` 的 `skills/awesome-readme`（完整读完 SKILL.md + 8 个 reference，共 3237 行）
  - 该 skill frontmatter `analyzed_repos` 里列出的**一手上游**逐个取回
  - GitHub 官方文档 `docs.github.com/en/get-started/writing-on-github/*` 与
    `.../customizing-your-repository/about-readmes`
  - PyPA packaging guide、shields.io 实测、npm 包页实测
  - 英文维基百科 `Wikipedia:Signs_of_AI_writing`（上游 `humanizer` skill 的一手来源）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars,pushed,license}'`；
  **许可一律另读 LICENSE 正文**，下表「许可」列即实读结果。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可（实读） | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GitHub Docs `writing-on-github` + `about-readmes` | <https://docs.github.com/en/get-started/writing-on-github> | — | 持续 | CC-BY-4.0（站点条款） | 渲染行为、锚点规则、alerts、`<picture>`、`<details>`、mermaid、README 查找顺序、大小上限 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE merged | 唯一能定义「GitHub 到底渲染什么」的一手来源；本次全部 `[official]` 断言出自此处 |
| 2 | PyPA《Making a PyPI-friendly README》 | <https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/> | — | 持续 | CC-BY-SA-4.0（站点条款） | PyPI 用 `readme_renderer` 渲染 manifest 指定的文件；`twine check` | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE merged | 「README 是多渲染器产物」这个命题的官方依据；但它不写哪些 HTML 会被剥离，矩阵靠实测 |
| 3 | `Wikipedia:Signs of AI writing` | <https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing> | — | 持续 | CC-BY-SA-4.0 | 结构性与词汇性 AI 腔特征、检测可靠性的反面告诫 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE merged | `humanizer` 与上游 `voice-and-prose.md` 的共同一手来源，且比两者都准（见冲突裁决 #3、#4） |
| 4 | `RichardLitt/standard-readme` `spec.md` | <https://github.com/RichardLitt/standard-readme> | 6364 | 2026-06-17 | MIT（LICENSE 首行 `The MIT License (MIT)`） | 首屏各块的硬性约束：描述 <120 字符、与包管理器和仓库描述一致、banner/badges 无自己的标题 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE merged | 全场唯一给出**可机器核对的跨产物不变量**的候选 |
| 5 | `anuraghazra/github-readme-stats` `readme.md` | <https://github.com/anuraghazra/github-readme-stats> | 79842 | 2026-08-31 | MIT（LICENSE 首行 `MIT License` / `Copyright (c) 2020 Anurag Hazra`） | 第三方挂件的真实代价：公共实例 best-effort、限流、各卡默认缓存 24h/144h/240h/48h | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE merged | 由挂件**作者自己**写明的限制，比任何二手评价都可信 |
| 6 | `fralapo/awesome-agent-skills` `skills/awesome-readme` | <https://github.com/fralapo/awesome-agent-skills> | **0** | 2026-09-04 | MIT（LICENSE 首行 `MIT License` / `Copyright (c) 2026 Jacopo Latrofa`） | 呈现层的**覆盖图**：首屏、视觉、徽章、TOC、`<details>`、反 AI 腔 | 1 | 3 | 2 | 1 | 2 | 9 | INCLUDE merged（仅覆盖图） | 0 星、自述「mined」的二手汇编；抽查 3 条规则有 2 条被实测推翻（见「流行但有坑」）。取它的**题目清单**，答案全部回一手 |
| 7 | `badges/shields` | <https://github.com/badges/shields> | 27180 | 2026-09-11 | Apache-2.0（LICENSE-APACHE 正文；另有 LICENSE-MIT 双许可） | 徽章服务本体 | 3 | 3 | 2 | 3 | 2 | 13 | reference | 行为全部对**线上服务**实测得出，仓库文本一字未取；不作 merged |
| 8 | `othneildrew/Best-README-Template` | <https://github.com/othneildrew/Best-README-Template> | 16349 | 2026-04-18 | Unlicense（LICENSE.txt 首行 `The Unlicense`） | 首屏模板、TOC、back-to-top | 1 | 1 | 2 | **0** | 2 | 6 | reference（反例） | 正确性 0：其招牌的 `<a name="readme-top">` + back-to-top 在渲染后的 HTML 里 9 个 href 对 1 个 id。作为**反证**收录 |
| 9 | `matiassingers/awesome-readme` | <https://github.com/matiassingers/awesome-readme> | 21434 | 2026-09-10 | CC0-1.0（**无 LICENSE 文件**；`readme.md` 末尾 CC0 徽标 + "has waived all copyright"，API 报 `null`） | 精选 README 与工具链接列表 | 1 | 3 | 0 | — | 1 | 5 | REJECT | 是链接目录，不含任何可执行规则；许可虽为 CC0 也无内容可取。API 的 `null` 是「没有 LICENSE 文件」，不是「无许可」 |
| 10 | `abhisheknaiidu/awesome-github-profile-readme` | <https://github.com/abhisheknaiidu/awesome-github-profile-readme> | 31037 | 2026-03-03 | CC0-1.0（LICENSE 首行 `Creative Commons Legal Code` / `CC0 1.0 Universal`） | GitHub profile README 展示集 | 1 | 1 | 1 | — | 2 | 5 | REJECT（**范围裁决**） | profile README 是个人主页不是项目文档，本次明确写入 SKILL.md 的否定范围 |
| 11 | `dguo/make-a-readme`（makeareadme.com） | <https://www.makeareadme.com/> | 734 | 2024-07-13 | MIT（LICENSE 首行 `MIT License` / `Copyright (c) 2017 Danny Guo`） | README 分节建议与模板 | 1 | 0 | 1 | 3 | 2 | 7 | REJECT（**新鲜度 + 内容裁决**） | >6 月未推送；内容正确但每条都是「加个 Visuals 小节会更好」这类**无后果**建议，本库标准要求删掉。它对呈现层的全部覆盖就是一段 3 行的 Visuals |
| 12 | `kefranabg/readme-md-generator` | <https://github.com/kefranabg/readme-md-generator> | 11133 | 2022-09-20 | MIT（LICENSE 首行 `MIT License`） | 交互式 README 生成器 | 1 | 0 | 1 | — | 2 | 4 | REJECT（**新鲜度裁决**） | 近 4 年未推送；且它是工具不是规则，其产出正是本 skill 要判为「模板占位文本」的东西 |
| 13 | `blader/humanizer` | <https://github.com/blader/humanizer> | 46746 | 2026-09-06 | MIT（LICENSE 首行 `MIT License`） | 反 AI 腔 | 1 | 3 | 2 | 2 | 2 | 10 | REJECT（**内容裁决**） | 星很高，但它自述即是维基百科「Signs of AI writing」的再包装。一手就在 #3，取二手只会引入转述误差（上游 `voice-and-prose.md` 正是这样把 em dash 规则抄错的） |
| 14 | `DenverCoder1/readme-typing-svg` | <https://github.com/DenverCoder1/readme-typing-svg> | 9311 | 2026-08-31 | MIT（LICENSE 首行 `MIT License`） | 打字动画 SVG 挂件 | 1 | 3 | 1 | — | 2 | 7 | REJECT（作为内容源） | 只作为**被评估对象**出现在 `badges-and-widgets.md`；不取其文本 |
| 15 | `star-history/star-history` | <https://github.com/star-history/star-history> | 9480 | 2026-09-05 | MIT（LICENSE 首行 `MIT License`） | 星标曲线挂件 | 1 | 3 | 1 | — | 2 | 7 | REJECT（作为内容源） | 同上 |
| 16 | 本库已收的 `mblode-docs-writing` / `copilot-docs` / `addyosmani-skills` | 见 `SOURCES.yaml` | — | — | MIT | 已合入的文档规则 | — | — | — | — | — | — | 已收，无新增 | 逐个 grep 确认：三者对首屏、视觉、徽章、锚点、跨渲染器、AI 腔**全部零覆盖**，所以这次的缺口不是漏读造成的 |

## 深度审查

### `awesome-readme`（上游，0 星）

结构：SKILL.md 315 行 + 8 个 reference（`anti-patterns` 301、`badges` 280、
`examples` 297、`profile-readme` 279、`sections` 504、`templates` 613、
`visuals` 278、`voice-and-prose` 370）。

可取的：**题目清单**。它是唯一一个把「首屏构图 / 视觉资产 / 徽章 / TOC /
`<details>` / 反 AI 腔」当成一个整体来组织的候选，本次四个新 reference 的
目录结构基本对应它的覆盖面。

不可取的（逐条）：

- frontmatter 带 `version` / `source` / `analyzed_repos` / `analyzed_examples`
  等非规范键，按本库标准必须剥离。
- `templates.md`（613 行）按项目类型给 8 套完整模板。本库标准明确反对这种脚手架：
  模板会被整段粘贴，占位文本留在成品里正是它自己 `anti-patterns.md` 的第 1 条。
- `badges.md` 是 280 行的 URL 目录。URL 目录会过期，而失效模式不会——本次只写后者。
- `profile-readme.md` 范围外。
- 三条规则被实测推翻，见下节。

### GitHub 官方文档

用到的页面与各自贡献：

| 页面 | 取到的事实 |
|---|---|
| `basic-writing-and-formatting-syntax` | 锚点 slug 生成规则（小写化、空格转连字符、其余标点删除）；自定义锚点 `<a name=...>` **不进** 自动生成的 Outline；alerts 的五种类型与「每页一两个、不要连用、不能嵌套」；`<picture>` 受支持；建议用相对链接 |
| `about-readmes` | README 查找顺序 `.github` → 根 → `docs`；**渲染超过 500 KiB 截断**；标题自动生成 Outline |
| `organizing-information-with-collapsed-sections` | `<details>` / `<summary>` / `open` |
| `quickstart-for-writing-on-github` | `<picture>` + `prefers-color-scheme` 的官方写法，并明确 `<img>` 是「两个 source 都不匹配时」的兜底，`alt` 要写给读屏器 |
| `creating-diagrams` | mermaid / geoJSON / topoJSON / STL |
| `attaching-files` | 图片与 GIF 10 MB 上限；视频免费 10 MB、付费 100 MB；支持 PNG/GIF/JPEG/SVG/mp4/mov/webm；推荐 H.264 |

## 「流行但有坑」——被实证推翻的上游做法

这一节是本次更新最有价值的部分：四条广为流传的做法，实测后不成立。

### 1. `<a name="readme-top">` + back-to-top 不是可移植构造

`Best-README-Template`（16349★）的招牌写法，上游 `awesome-readme` 原样抄进
SKILL.md 第 6 条 Style Rule。拉它自己的仓库上下文渲染结果：

```bash
gh api repos/othneildrew/Best-README-Template/readme \
  -H 'Accept: application/vnd.github.html+json' > brt.html
grep -o 'href="#readme-top"' brt.html | wc -l          # 9
grep -o 'id="user-content-readme-top"' brt.html | wc -l # 1
```

**9 个链接对 1 个 id，而且那个 id 已经被改名成 `user-content-readme-top`。**
渲染后的 HTML 自身不自洽。**注意:到此为止全是 DOM 层面的测量;**
**「点击时 github.com 靠前端 JS 把 `#readme-top` 映射到 `user-content-readme-top`」是推论,不是测量。**
主代理用无头浏览器复核时,该页 `window.scrollY` 恒为 0、无法可靠测量滚动行为,
因此**机制未验证**,reference 里只写「渲染产物自身解析不了这个片段」,不写机制。
GitHub 自己给标题生成的 permalink 也是同样的错位
（`<a id="user-content-about-the-project" href="#about-the-project">`）。

对 PyPI 侧还更糟——它改的是**另一端**（见下条），所以两边合起来是：
`<a id>` 的 id 不动、href 被改；`<a name>` 的 `name` 属性直接被删。
手写锚点在 PyPI 上是**静默死链**。

### 2. 契约文件第 2 节关于 PyPI 的结论需要修正

`local://readme-renderer-facts.md` 写「PyPI：两端都重写……所以手写锚点在 PyPI 上是通的」。
实测不成立。探针 `/tmp/probe/p2.md` 经 `readme_renderer.markdown.render` 输出：

```html
<p><a id="readme-top" rel="nofollow"></a>
<a rel="nofollow"></a></p>                       <!-- <a name="readme-top2"> 的 name 被整个删掉 -->
...
<p align="right"><a href="#user-content-readme-top" rel="nofollow">back to top</a></p>
<h2 id="user-content-about-the-project">About The Project<a href="#user-content-about-the-project"></a></h2>
```

即：**标题**两端都被改写（`id` 与 TOC 链接都变成 `user-content-*`，因此对得上）；
**作者手写的 `<a id>`** 只有 href 被改写，id 原样保留，两端对不上；
`<a name>` 连属性都没了。结论仍然是「Markdown 标题 slug 是唯一可移植的页内跳转」，
但理由与契约文件写的相反，reference 里按实测写。复现命令见下方「复现命令」。

### 3. 「每节最多一个 em dash」是错的

上游 `voice-and-prose.md` 第 7 条：`Rule for READMEs: one em dash per section maximum.`
它声称改编自维基百科「Signs of AI writing」。而该页自己写的是：em dash **频率**
是弱信号，只应与其他指标合用；OpenAI 在 GPT-5.1 上已刻意抑制；
2026 年 7 月的一项研究发现当代模型里只有一个用得比专业写作者更多，ChatGPT 用得更少。
真正可机械检查的是**空格包裹的 em dash**（` — `），这与常见排版规范相反。
本次按一手写，并在 `human-voice.md` 的「什么不是特征」里明确指出计数法会误伤。

### 4. 「粗体前导的项目符号列表」在 README 里不是 AI 特征

同一页维基百科在 `Inline-header vertical lists` 一节里明说，这个习惯是 LLM
**从 readme 等材料里学来的**。也就是说，在 README 里按这条判 AI 是反向误伤。
上游把它列进「AI tells」，本次把它列进 `human-voice.md` 的「什么不是特征」。

### 5. 附带推翻的两条

- 上游 `anti-patterns.md` 3.9：「绝对 GitHub blob URL → 改相对路径」。
  GitHub 官方也推荐相对路径。但相对路径在 PyPI 与 npm 上**一定坏**（见冲突裁决 #1）。
- `standard-readme` 建议把静态徽章本地托管以「避免追踪」。实测 GitHub、PyPI、npm
  **三家都走自己的图片代理**（`camo.githubusercontent.com`、
  `pypi-camo.freetls.fastly.net`、npm 页面上同样是 `camo.githubusercontent.com`），
  第三方主机看到的是代理不是读者。本地托管的正当理由是缓存与宕机，不是隐私。

## 实测矩阵与测得的数字

### 渲染器

| 构造 | GitHub | PyPI (`readme_renderer[md]`) | npm 包页 |
|---|---|---|---|
| `align` 属性 | 保留 | 保留 | 保留（tsup/mermaid/zod 页面共 6–8 处） |
| `style=` / `class=` / `<style>` / `<center>` / `<font>` / `<marquee>` | 剥离 | 剥离 | 未测 |
| `<details>` / `<summary>` | 保留 | 保留 | **保留**（`mermaid` 包页 1 处） |
| `<details open>` 的 `open` | 保留 | **剥离** | 未测 |
| `<picture>` + `<source>` | 保留 | `<source>` 剥离 | **保留**（`tsup` 包页 picture=1 source=1） |
| `<video>` | **保留** | 剥离 | 未测 |
| `> [!WARNING]` | 样式化 callout | `<aside class="admonition">` | **退化为普通引用块，字面量 `[!WARNING]` 可见** |
| ` ```mermaid ` | 渲染为图 | `<pre lang="mermaid">` | 未渲染为图 |
| 标题锚点 | 生成 | 生成 | **不生成**（`mermaid` 21 个标题 / `zod` 10 个标题，`id` 全为空；两页共 39 个 `#` 链接全死） |
| 外链图片 | camo 代理 | pypi-camo 代理 | camo 代理 |

`<h1 align="center">` 这类 HTML 标题在 GitHub 上**照样生成锚点**
（`Best-README-Template` 的 `<h3 align="center">Best-README-Template</h3>`
→ `id="user-content-best-readme-template"`），所以「居中标题会丢失章节链接」这个
常见担心不成立。

### shields.io 与代理的缓存

| 端点 | `Cache-Control` |
|---|---|
| GitHub Actions workflow status | `max-age=60` |
| npm version | `max-age=300` |
| GitHub stars | `max-age=1800` |
| PyPI version | `max-age=10800` |
| GitHub license | `max-age=14400` |
| 静态 `badge/label-msg-green` | `max-age=432000` |
| `contrib.rocks/image` | `max-age=259200` |
| `camo.githubusercontent.com`（叠加在上面） | `max-age=120` |

`?cacheSeconds=3600` 对 license 徽章**无效**（仍是 14400），因为低于该服务的下限。

### shields 的失效模式

```
GET https://img.shields.io/nosuchbadge/foo/bar            -> HTTP 200, <title>404: badge not found</title>
GET https://img.shields.io/github/v/release/definitely/notarealrepo123
                                                          -> HTTP 200, <title>release: no releases or repo not found</title>
```

**坏徽章返回 200。** 按状态码做的链接检查会全部通过，读者却看到一枚写着
「not found」的徽章。唯一有效的检查是读 SVG 的 `<title>`。

`style=` 取 `flat` / `flat-square` / `plastic` / `for-the-badge` / `social`；
传 `bogus` 不报错，静默回落到默认——拼错样式没有任何提示。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | README 里用相对还是绝对路径 | GitHub 官方文档：用相对路径，clone/fork 都能用 ／ 实测：相对路径在 PyPI 与 npm 页面上一定 404 | **按发布面分流**：只在 forge 上读 → 相对；同时作为包描述发布 → 全部绝对且钉 tag | 两边各自都对，冲突只存在于「同一文件多处渲染」这个前提下。写进 `readme-portability.md` |
| 2 | README 能放在哪 | 现有 `readme.md`：「`docs/README.md` 是没人会看到的文件」 ／ GitHub 官方：`.github` → 根 → `docs` 都会被渲染，取第一个 | 保留「放在代码顶层」这条规则，但把理由改对：GitHub 会优先取 `.github/`，所以真正的风险是**根目录那份成了没人维护的那份**，而包构建取的正是根目录那份 | 官方文档 > 本库旧表述。已改 `references/readme.md:29-34` |
| 3 | em dash 是不是 AI 特征 | 上游 `voice-and-prose.md`：每节最多一个 ／ 维基百科（其自称上游）：频率是弱信号，空格包裹才是习惯性痕迹 | 取维基百科；`human-voice.md` 用「空格包裹」作为可 grep 项，并把「按数量判」列进「什么不是特征」 | 一手 > 二手转述；且一手给了 2026 年的研究结论 |
| 4 | 粗体前导列表 | 上游：AI tell ／ 维基百科：这是 LLM 从 readme 学去的习惯 | 在 README 语境下不算特征 | 同上 |
| 5 | 徽章数量上限 | 上游：5–8 个，`cap at 8` ／ 本库标准：不写没有依据的魔法数 | 换成三条可检查的判据（首屏占位、依赖数量、区分度），并说明多数项目落在 3–6 | `docs/skill-standard.md`「无魔法数」；数字本身无出处 |
| 6 | 反 AI 腔放哪 | 扩写 `plain-english.md` ／ 新建 `human-voice.md` | **新建**。`plain-english.md` 的问题是「非母语读者能不能读懂」，来源是 Google 风格指南；反 AI 腔的问题是「读者信不信」，来源是维基百科。两者判据、来源、执行时机都不同，合并会让 `plain-english.md` 失焦，也违反「一个事实一个家」 | 本库标准第 4 节 |
| 7 | profile README 要不要收 | 上游有 `profile-readme.md`（279 行） | 不收，并写进 SKILL.md 的否定范围 | 它没有「带着任务来的读者」、没有能跑的 quick start、没有可核对的源码，本 skill 的每条规则套上去都是错位 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `github-writing-docs` | docs.github.com/writing-on-github + about-readmes | merged | 全部 `[official]` 渲染行为：slug 规则、自定义锚点不进 Outline、自动 TOC、`<picture>`、`<details>`、alerts 的用量约束、mermaid、相对链接、README 查找顺序、500 KiB 截断、上传上限与媒体格式 |
| `pypa-readme` | PyPA packaging guide | merged | PyPI 用 manifest 指定的文件 + `readme_renderer` 渲染；`twine check` |
| `wikipedia-ai-signs` | Wikipedia:Signs of AI writing | merged | `human-voice.md` 的整体结构：结构性 vs 词汇性特征、词表会过期、可 grep 的机械信号、检测不可靠的两条告诫 |
| `standard-readme` | RichardLitt/standard-readme `spec.md` | merged | 描述 <120 字符且与包管理器 / 仓库描述三处一致；banner 与 badges 无自己的标题；TOC 的 100 行阈值与二级标题覆盖 |
| `awesome-readme-skill` | fralapo/awesome-agent-skills `skills/awesome-readme` | merged | 呈现层的覆盖图；有后果的结构性反模式（占位文本、碎图、空节 / coming soon、死服务徽章、引用式链接定义放文件底部） |
| `github-readme-stats` | anuraghazra/github-readme-stats | merged | 挂件作者自述的限制与各卡默认缓存 |
| `shields` | badges/shields | reference | 只作为被实测对象；未取任何文本 |
| `best-readme-template` | othneildrew/Best-README-Template | reference | 反例证据（9:1 锚点错位） |

## 基线缺口

无 skill（`uv run tools/run_evals.py technical-writing --baseline --only N`，
Claude Opus 5 / medium）时逐条记录。**基线整体很强**——这一版 Opus 在
场景 9（AI 腔）几乎满分——所以下面只列真正未达成与**编造**的部分，原文照抄。

### 场景 6（给 tilekit 写 README，基线 66.5 s）

产出的 README 本身质量高，事实核对到位。未达成：

| 未达成的 `expected_behavior` | 证据（基线产物原文） |
|---|---|
| 图片必须有非空 `alt` | 第 1 行 `<img src="assets/logo.svg" width="72" align="right" alt="">` —— `alt` 为空 |
| 徽章集合包含许可徽章 | 只有 CI 与 npm 两枚，没有 Apache-2.0 许可徽章；答复里写「无徽章汤：只有 CI + npm 两枚」把「少」当成了目标本身 |
| 单一徽章风格 | CI 用 GitHub 自带 `actions/workflows/ci.yml/badge.svg`，npm 用 shields，两种视觉风格并排 |
| 演示 GIF 给显式 `width` | 第 18 行 `![tilekit pack running in a terminal](assets/demo.gif)` —— 2.8 MB 的 GIF 没有 `width` |
| （呈现层增量，基线完全未考虑）该包发布到 npm，相对图片路径与 `docs/` 链接在包页上不解析 | 全文 `assets/demo.gif`、`docs/guide.md`、`CHANGELOG.md`、`LICENSE` 均为相对路径 |
| 代码块可直接粘贴 | 第 13–16 行用 `$ npx tilekit pack sprites/` 带 `$` 提示符 |

### 场景 7（美化过头的 README，基线 98.3 s）

基线抓到了 `<style>`、`<center>`、`<marquee>`、`<picture>` 无兜底、emoji slug、
徽章墙、死服务、不存在的文件，很强。**编造与判错**：

| 类型 | 基线原文 | 实测事实 |
|---|---|---|
| **编造** | 「`<video src="assets/demo.mp4">` \| GitHub 不允许原始 `<video>` 标签，PyPI 同样剥离」 | GitHub **保留** `<video>`；只有 PyPI 剥离。前半句是编的 |
| **编造** | 「`<h1 style=...>` 而非 Markdown `#` → 文档**没有真正的一级标题**，PyPI 项目页顶部无标题」 | `<center>` 被剥离但里面的 `<h1>` 保留；HTML 标题在 GitHub 上照样生成锚点 |
| **编造** | 「`hits.dwyl.com` 还是第三方追踪像素」 | GitHub 与 PyPI 都经自家图片代理取图，第三方看不到读者 |
| **判错失效模式** | 「`github/licence` 拼错（shields 的 endpoint 是 `license`）→ 徽章 404」 | 返回的是 **HTTP 200 + 一枚写着 `404: badge not found` 的徽章**；按状态码做的检查不会报警 |
| **推理反了** | 「`<details open>` 包 5 行代码：既然默认展开，折叠毫无意义」 | `open` 在 PyPI 上被剥离。而基线自己刚论证过「维护者的用户主要从 PyPI 落地」——在那一侧，安装与 quick start 正是被折叠的 |
| 计数错 | 「共 8 处 back to top」 | 夹具里是 9 处 |

### 场景 8（GitHub 好看、npm 坏掉，基线 181.6 s）

基线给出的根因方向正确（多渲染器 + tarball 不含 `docs/`），`[!WARNING]` 退化也答对。**编造**：

| 类型 | 基线原文 | 实测事实 |
|---|---|---|
| **编造** | 「`<picture>`/`<source>` 主题切换 \| 主题切换失效/被清洗，最好情况只剩 `<img>`，最坏只剩 alt 文本」 | npm **保留** `<picture>` 与 `<source>`（`tsup` 包页 picture=1、source=1） |
| **编造** | 「`<details><summary>` 包着选项表 \| 折叠行为不可靠，整张选项表可能看不见」 | npm **保留** `<details>`（`mermaid` 包页 1 处） |
| **过度修改** | 「去掉 `<picture>`/`<video>`/`<details>`」 | 其中两项本来就能用，被误删 |
| **漏掉决定性事实** | 只说了 emoji slug 那一条锚点问题 | npm **完全不生成标题锚点**：`mermaid` 21 个标题、`zod` 10 个标题，`id` 全为空，两页共 39 个 `#` 链接全部是死链。整张 Contents 在 npm 上没有一条能点 |

### 场景 9（AI 腔，基线 48.0 s）

基线表现非常好：点名了 promotional adjectives、`not just X — it's Y`、
`testament to`、`empowering developers`、`Exciting times ahead!`、
`Let me know if you need any clarification`、`utilize`/`in order to`/`Simply`，
并把 `CREATE INDEX CONCURRENTLY` 的真实缺口和 1.9 s vs 26 s 基准补了进去。
未达成的只有：未提任何**机械可 grep**的信号（空格包裹的 em dash、弯引号、
`utm_source=openai` 一类痕迹），也没有区分「结构性特征」与「会过期的词表」。
**这一条的基线区分度确实低**，如实记录。

### 场景 10（负例：profile README）

基线 `skill_read=false`（`--no-skills` 下必然如此），真正的检验在带 skill 一侧。

## 评测结果

`uv run tools/run_evals.py technical-writing --only N [--baseline]`，
模型固定 `anthropic/claude-opus-5` + `medium`（未传 `--model` / `--thinking`）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 6 | opus-5 medium | 无 | false | 9 项中 4 项 | 见上「基线缺口」 |
| 7 | opus-5 medium | 无 | false | 12 项中 7 项 | 3 处编造、1 处失效模式判错、1 处推理反向 |
| 8 | opus-5 medium | 无 | false | 9 项中 4 项 | 2 处编造、1 处决定性事实漏掉 |
| 9 | opus-5 medium | 无 | false | 7 项中 6 项 | 区分度低 |
| 10 | opus-5 medium | 无 | false | 3 项中 3 项 | 基线必然如此，不计分 |
| 6 | opus-5 medium | 有 | **true** | 9 项中 7 项 | 首屏顺序、pre-1.0 状态行与 issue 渠道、`alt` 写成完整句、`width="720"`、许可徽章、引用式徽章定义放底部、因发布到 npm 而把图片与链接全改成钉 `main` 的绝对 URL。未达成：没放 npm 版本徽章；没用上 `atlas-light/dark` 那对暗色模式图 |
| 7 | opus-5 medium | 有 | **true** | 12 项中 11 项 | 用了新的 README review 输出契约，逐条给「构造 / 在哪坏 / 怎么改」。基线的 5 处编造与判错全部没有重犯：`<video>` 只归给 PyPI、`<h1>` 没有被说成「不存在」、`hits.dwyl` 不再被称作追踪像素、back-to-top 数对了（9 处）、`<details open>` 的理由改对成「PyPI 一侧安装与 quick start 被折叠」。**新引入 1 处错误**：称「PyPI strips `<details>`/`<summary>`」，实测 PyPI 保留 `<details>`、只剥离 `open`；另称 GitHub 会「strip `<a name>`」，实际是改写成 `user-content-` 前缀（结论不变） |
| 8 | opus-5 medium | 有 | **true** | 9 项中 9 项 | 决定性事实答出：「手写 Contents 五条全死（npm 不生成标题锚点）」；没有重犯基线对 `<picture>`/`<details>` 的编造；**实际去 fetch 了三枚徽章**并报出 `build: repo or workflow not found` / `npm: package not found` / `license: package not found`，同时点明「徽章服务出错返回 HTTP 200，所以链接检查器放过了」 |
| 9 | opus-5 medium | 有 | **true** | 7 项中 7 项 | 基线唯一缺口（机械可 grep 的信号）补上：明确 grep 了空格包裹的 em dash、弯引号、`utm_source` / `oaicite` / `contentReference`，并按「结构性特征」分类命名。结构与标题集未动 |
| 10 | opus-5 medium | 有 | **false** | 3 项中 3 项 | 负例通过：没有读 `skills/technical-writing/SKILL.md`，按个人主页作答，未做文档类型分类、未要求 quick start / 状态行 / 许可链接。它还顺手 curl 了各挂件端点，发现 `github-readme-stats.vercel.app` 返回 `503 DEPLOYMENT_PAUSED`——恰好是本次 `badges-and-widgets.md` 写的那个失效模式的现场实例 |

结论：**通过。** 四个正例全部 `skill_read=true`，负例 `skill_read=false`。
基线未达成的行为在有 skill 时达成的有：

1. 场景 8 —— 「npm 不生成标题锚点，页内链接全死」这条决定性事实，基线完全没提，有 skill 时答出。
2. 场景 8 —— 基线编造「npm 剥离 `<picture>`/`<details>`」并据此误删两个本来可用的构造；
   有 skill 时两者都被保留，因为矩阵是实测的。
3. 场景 7 —— 基线编造「GitHub 不允许 `<video>`」「没有真正的一级标题」「`hits.dwyl` 是追踪像素」，
   有 skill 时三条全部消失。
4. 场景 7 / 8 —— 徽章失效模式从「404」改成正确的「HTTP 200 + 徽章上写着 not found」，
   场景 8 还真的按 reference 给的命令读了 `<title>`。
5. 场景 6 —— `alt=""` → 完整句 `alt`，无 `width` → `width="720"`，缺许可徽章 → 补上，
   相对路径 → 因该包发布到 npm 而改为绝对 URL（基线完全没考虑这一层）。
6. 场景 9 —— 从「只点名词汇与句式」到「同时跑机械 grep 并区分结构性与词汇性特征」。

残留问题（如实记录，未在本次修复）：场景 7 把 PyPI 对 `<details>` 的处理说反了。
`readme-portability.md` 的矩阵里这一行写的是「`<details>` 保留、`open` 剥离」，
两行相邻；模型把相邻两行读并了。下次同步时可考虑把 `open` 那一行并进同一行表述。

## 复现命令

```bash
# GitHub：仓库上下文下的真实渲染管线（与仓库首页同一条）
gh api repos/othneildrew/Best-README-Template/readme \
  -H 'Accept: application/vnd.github.html+json' > brt.html
grep -o 'href="#readme-top"' brt.html | wc -l
grep -o 'id="user-content-readme-top"' brt.html | wc -l

# GitHub：未提交文件
gh api /markdown -f mode=gfm -f text="$(cat probe.md)"

# PyPI：上传时真正使用的渲染库
uv run --with 'readme_renderer[md]' python -c \
  "from readme_renderer.markdown import render; print(render(open('probe.md').read()))"

# PyPI：是否代理图片
curl -sL https://pypi.org/project/rich/ | grep -oE '<img[^>]*src="[^"]{0,120}'

# npm：包页 DOM（用 browser 工具打开 https://www.npmjs.com/package/<pkg> 后 evaluate）
#   document.querySelector('#readme') 下统计 h1..h4 的 id 空值数、details/picture/source 数、
#   blockquote 内是否残留字面量 [!WARNING]
#   实测包：mermaid、zod、tsup、axios
# 先用注册表 API 筛出含目标构造的包，避免盲试：
curl -s https://registry.npmjs.org/tsup/latest | jq -r '.readme' | grep -c '\[!WARNING\]'

# shields：缓存与失效模式
curl -sI 'https://img.shields.io/github/license/othneildrew/Best-README-Template' | grep -i cache-control
curl -s  'https://img.shields.io/nosuchbadge/foo/bar' | grep -o '<title>[^<]*</title>'
curl -s  'https://img.shields.io/github/v/release/definitely/notarealrepo123' | grep -o '<title>[^<]*</title>'
curl -sI 'https://contrib.rocks/image?repo=anuraghazra/github-readme-stats' | grep -i cache-control

# 许可实读
gh api repos/<owner>/<repo>/contents/LICENSE --jq '.content' | base64 -d | head -4
```

## 未验证清单

写进 reference 时一律标注为「未测」，不得当作支持：

- **npm**：`<video>`、`<details open>` 的 `open`、`style=`/`class=`/`<center>`/`<marquee>`、
  任务列表、脚注、`loading="lazy"`。npm 前端闭源，只能靠「找到一个恰好用了该构造的已发布包」
  来观测，上述构造暂未找到合适样本。**已测到的那几行才写进矩阵，其余留空为「未测」。**
- **npm 的 README 刷新时机**：基线声称「只在 `npm publish` 新版本时刷新」并给了 npm 文档链接。
  本次未独立验证，故未写入 reference。
- **crates.io**（`comrak` + `ammonia`）：两者均开源可本机实测，本次未做，reference 中不出现。
- **VS Code / JetBrains 的 Markdown 预览**：未测。
- **pkg.go.dev、Docker Hub、GitLab、Gitea、Codeberg**：未测。
- **GitHub 私有仓库图片与 camo 的鉴权行为**、社交预览卡（Open Graph）：未测。
- **`<details>` 内容是否被浏览器的页内查找命中**：`readme-presentation.md` 写的是
  「展开前不被 find-in-page 命中」，这是浏览器行为而非渲染器行为，未在本次矩阵中实测，
  按 `[community]` 对待；若要升级为 `[verified]` 需在具体浏览器版本上验证。
- 缓存数字（`max-age`）是**本次测得的当前值**，服务方可随时调整；reference 中它们支撑的结论是
  「不同徽章的时效相差一个数量级，构建状态接近实时、许可与版本不是」，这个结论比具体秒数耐用。

## 备注

- 本次未新建 skill 目录，`skills/` 仍为 53 个。
- `NOTICE.md` 未跑 `tools/build_catalog.py`，而是直接调用 `tools/_common.py:render_notice`
  只重写了本 skill 的 `NOTICE.md`，避免动到全仓生成文件。
  `THIRD_PARTY_NOTICES.md` / `marketplace.json` / 根 `README.md` 仍待主代理统一生成。
- 后续同步要盯的上游：`github-writing-docs`（alerts 与 `<picture>` 的支持面在变）、
  `github-readme-stats`（缓存默认值写在它 readme 里）、`shields`（样式集合）。
- 本次刻意**没有**写进 skill 的方向：按项目类型给 README 模板、徽章 URL 目录、
  profile README、GIF 录制工具清单（工具会换，且与「页面说什么」无关）。
