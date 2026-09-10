# astro 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"Astro agent skill SKILL.md github astro islands content collections"`、`site:skills.sh astro`
  - <https://www.skills.sh>（`delineas/astro-framework-agents`、`astrolicious/agent-skills`、`withastro/astro` 两个官方 skill 均由此确认）
  - `github/awesome-copilot`：`gh api .../git/trees/main?recursive=1 | grep -i astro`，全仓只有 `instructions/astro.instructions.md`，`skills/` 树无 Astro 条目
  - 官方组织仓库：`withastro/astro`（`.agents/skills/`）、`withastro/docs`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- 版本基线：`gh api repos/withastro/astro/releases` → 当前 GA **astro@7.3.2（2026-09-08）**。
  正文全部对齐 7.3；`packages/astro/CHANGELOG.md` 的 `## 7.0.0` 段与 `guides/upgrade-to/v6.mdx`、
  `guides/upgrade-to/v7.mdx` 两份升级指南是「移除/变更」清单的直接依据。

### 动手前确认的当前状态（几块高频变动的区域）

| 主题 | 结论 | 依据 |
|---|---|---|
| 主版本 | astro@7.3.2（Node 22.12+、Vite 8、Zod 4、Rust 编译器） | releases API + CHANGELOG `## 7.0.0` |
| `astro:actions` | 早已稳定，`experimental.actions` 不存在；`accept: 'form'`、`Astro.getActionResult()`、`isInputError()`、`.orThrow()`、`Astro.callAction()` 为当前 API；v6 移除了 `serializeActionResult`/`deserializeActionResult` 顶层导出与 action context 上的 `rewrite()` | `guides/actions.mdx`、`upgrade-to/v6.mdx` |
| content layer | 唯一实现。`src/content.config.ts` + 必需 `loader`；v6 删掉 legacy collections 与 `legacy.collections` flag（连 v5 的隐式向后兼容一起删）；`glob()` 新增 `retainBody`(5.17)、`deferRender`(7.1) | `guides/content-collections.mdx`、`reference/content-loader-reference.mdx`、`upgrade-to/v6.mdx` |
| live collections | `src/live.config.ts` + `defineLiveCollection()`，已非 experimental（`reference/experimental-flags/` 下无对应条目）；7.0 新增 `cacheHint` | `guides/content-collections.mdx` |
| server islands | 稳定，`server:defer` + `slot="fallback"`，需 adapter；props 加密进 query，超 ~2KB 退化为 `POST`（不可缓存）；`ASTRO_KEY` 用于滚动发布 | `guides/server-islands.mdx` |
| view transitions | `<ClientRouter />`；`<ViewTransitions />` v6 移除；v7 移除 `TRANSITION_*` 常量、`isTransition*Event()`、`createAnimationScope()`；`handleForms` prop v6 移除 | `guides/view-transitions.mdx`、两份升级指南 |
| output 模式 | 只有 `'static' | 'server'`，**无 `hybrid`** | `reference/configuration-reference.mdx#output` |
| 新增（易被漏掉） | v7 顶层 `cache`/`routeRules`（route caching）、顶层 `fetchFile` + 保留名 `src/fetch.ts`（advanced routing）、`compressHTML: 'jsx'` 默认、Sätteri 取代 remark/rehype 默认、`@astrojs/db` 移除、agent 环境下 `astro dev` 自动后台化 | CHANGELOG `## 7.0.0`、`guides/caching.mdx`、`guides/routing.mdx` |

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | docs.astro.build（源 `withastro/docs`） | <https://docs.astro.build/en/getting-started/> | 1688 | 2026-09-09 | MIT（实读 LICENSE） | 全部 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（主干） | 官方文档，`.mdx` 源可逐行核对。许可实查为 MIT，因此按规则 **merged** 而非 reference |
| 2 | `withastro/astro` `.agents/skills/astro-code-review` | <https://github.com/withastro/astro> | 62461 | 2026-09-10 | MIT（API 报 NOASSERTION，实读 LICENSE 为 MIT + sveltejs/kit 附注） | 评审契约 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（只取口径） | 官方，但面向 Astro 贡献者的 PR 评审。可用的是「只报可合并相关问题、不改代码、给裁决而非摘要」这套评审姿态 |
| 3 | `withastro/astro` `.agents/skills/astro-developer` | 同上 | 62461 | 2026-09-10 | MIT | monorepo 开发 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（只取口径） | 官方，但内容是 monorepo 架构/pipeline/changeset 流程，对应用开发只有间接价值：三执行上下文（core / runtime-server / runtime-client）与「优先单元测试 + Container API」的取舍 |
| 4 | `github/awesome-copilot` `instructions/astro.instructions.md` | <https://github.com/github/awesome-copilot> | 38862 | 2026-09-10 | MIT | 应用开发全景 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | GitHub 官方，明确自述对齐 **Astro 7.x**；抽查 `content.config.ts` + loader、`astro/zod`、`compressHTML: 'jsx'` + `{" "}` 三条全部正确。偏「标准清单」而非陷阱手册，故具体性 2 |
| 5 | `gigio1023/astro-dev-skill` `skills/astro-dev` | <https://github.com/gigio1023/astro-dev-skill> | 13 | 2026-07-10 | MIT | Astro 7 + 迁移 | 1 | 2 | 3 | 3 | 2 | 11 | INCLUDE | 唯一一个把「已移除 API」做成 read-first 兼容性闸门的社区上游。抽查 `output: 'hybrid'` 已移除、`z` 来自 `astro/zod`、Sätteri 默认三条全对 |
| 6 | `incluud/astro-agent-skills`（4 个 skill） | <https://github.com/incluud/astro-agent-skills> | 9 | 2026-04-23 | MIT | 默认值 + 集合 | 1 | 1 | 2 | 3 | 2 | 9 | INCLUDE | 星数低但内容干净：`.astro` 优先、island 保持叶子、`src/content.config.*` vs `src/live.config.*`、`schema: ({ image }) => …`。抽查 3 条全对，无 legacy 残留 |
| 7 | `delineas/astro-framework-agents` `skills/astro-framework` | <https://github.com/delineas/astro-framework-agents> | 44 | 2026-04-01 | MIT | 全景 + 决策框架 | 1 | 1 | 3 | **0** | 2 | 7 | **REJECT（正确性 0）** | 15 个 reference，结构最完整，但抽查三条全错：`output: 'hybrid'` 被写成「80% 真实项目」的推荐模式、`references/content-collections.md` 与 content layer 并列保留 `type: 'content'/'data'` 与 `post.slug`、`client:visible={{threshold}}`。量表规定正确性 0 直接 REJECT，只作覆盖面对照（`relation: reference`） |
| 8 | `delineas/astro-framework-agents` `skills/learning-astro` | 同上 | 44 | 2026-04-01 | MIT | 教学 | 1 | 1 | 1 | 2 | 2 | 7 | REJECT | 面向人类学习者的概念讲义（component-model / content-layer / file-based-routing），教程式，不含可执行规则 |
| 9 | `astrolicious/agent-skills` `skills/astro` | <https://github.com/astrolicious/agent-skills> | 14 | 2026-03-20 | 无（API `null`） | CLI + 结构 | 1 | 1 | 1 | 1 | 0 | 4 | REJECT | 单文件用法概览，实质是「去看 docs.astro.build」。合法配置文件名仍列 `astro.config.cjs`（v6 已移除 CJS 配置）→ 一错。frontmatter 自称 `authors: "Astro Team"` 但不在 withastro 组织下 |
| 10 | `SpillwaveSolutions/publishing-astro-websites-agentic-skill` | <https://github.com/SpillwaveSolutions/publishing-astro-websites-agentic-skill> | 31 | 2026-01-02 | 无（API `null`，frontmatter 自称 MIT） | SSG + 部署 | 1 | 0 | 2 | — | 0 | ≤4 | REJECT（新鲜度 0） | >6 个月未推送，量表直接 REJECT。内容重心在 Firebase/GCP 部署与 mermaid，与本 skill 边界重叠也少 |
| 11 | `oimiragieo/agent-studio` `.claude/skills/astro-expert` | <https://github.com/oimiragieo/agent-studio> | 40 | 2026-07-14 | 无（API `null`） | 角色设定 | 0 | 2 | 0 | — | 0 | ≤4 | REJECT | frontmatter 全是 agent 专属字段（`model`、`tools`、`trust_score`、`provenance_sha`），正文是 `<identity>`/`<capabilities>` 角色扮演，无一条 Astro 事实 |
| 12 | `joncutrer/astrojs-expert-skill` | <https://github.com/joncutrer/astrojs-expert-skill> | 1 | 2026-03-28 | 无（API `null`） | 全景 | 0 | 1 | 1 | — | 0 | ≤4 | REJECT | 单人仓、1 star、无许可、无独立信号 |
| 13 | `achreftlili/deep-dev-skills` `astro-project-starter` | <https://github.com/achreftlili/deep-dev-skills> | 1 | 2026-03-01 | 无（API `null`） | 脚手架 | 0 | 1 | 1 | — | 0 | ≤4 | REJECT | 一次性建项脚手架，非长期规则 |
| 14 | `fusengine/codex-agent` `astro-seo` | <https://github.com/fusengine/codex-agent> | 0 | 2026-05-10 | MIT | SEO | 0 | 2 | 1 | — | 2 | 5 | REJECT（MAYBE 但越界） | 0 star；且 SEO/元数据属 `frontend-design` 与尚不存在的 SEO 主题，不在本 skill 边界内 |

补充说明：第 10–14 行未做完整正确性抽查——它们在权威/新鲜/许可三项上已不可能达到 8 分，按量表提前判定，避免无意义的通读成本。

## 深度审查

**1. `withastro/docs`（主干）。** 唯一能作为事实基准的上游。按 `.mdx` 源读（`src/content/docs/en/**`）而非渲染页：渲染页含大量 base64 内联 SVG，噪声比正文多一个数量级。真正决定本 skill 形态的是三处：
`reference/directives-reference.mdx` 精确给出 `client:*` 的**完整选项集**（`client:idle` 只有 `timeout`，`client:visible` 只有 `rootMargin`），这是判定社区上游正确性的标尺；
`guides/upgrade-to/v6.mdx`（1791 行）+ `v7.mdx` 是移除清单的唯一权威来源；
`reference/content-loader-reference.mdx` 里 `retainBody` 与 `deferRender` 的区别（前者压数据存储体积，后者防构建 OOM）是文档里少见的「同一现象两种成因」条目，正好是 skill 该写的东西。

**2. `withastro/astro` 的两个官方 skill。** 名字很像应用开发 skill，实际不是：`astro-developer` 是 monorepo 上下文加载器（五种 Pipeline、`virtual:astro:*` 注册表、`pnpm -C packages/astro exec astro-scripts test`），`astro-code-review` 是 PR 评审策略（只读安全边界、merge requirement 提取、不实施修复）。按任务要求「只取口径与判定标准，不取仓库内部流程教程」处理：
- `astro-code-review` → 本 skill `audit-hydration` 的姿态与 `## Output format`：报告而非改写、逐条 `path:line`、显式声明丢弃了什么、结尾给裁决。
- `astro-developer` → 两条可迁移事实：三执行上下文（`core/` Node、`runtime/server/` 无 Node API、`runtime/client/` 浏览器）解释了为什么 `getImage()` 是服务端专用、为什么浏览器专属读取必须在挂载后；以及「优先单元测试，集成测试仅在无法单测时使用」的取舍，落到 references 的 Vitest + Container API 段。
- 其 monorepo 命令、changeset 流程、Pipeline 分类**一条未取**。

**3. `github/awesome-copilot`。** 权威性和新鲜度最高的第三方，且是唯一**自述对齐 Astro 7.x** 的社区级文件。价值不在深度而在「配对关系」：它把 `content.config.ts` + `loader` + `astro/zod` + 顶层 Zod 格式校验器当成一组同时给出，把 `server:defer` + `slot="fallback"` + adapter 当成一组，把 Rust 编译器的严格 HTML 与 `compressHTML: 'jsx'` 的 `{" "}` 补救当成一组——这几组正是分开写就会漏一半的地方。缺点是仍以「best practices 清单」体裁写，具体性给 2。

**4. `gigio1023/astro-dev-skill`。** 社区里唯一把「不要照抄的旧写法」提到 SKILL.md 顶层做成 Compatibility Gate 表的。它列的移除项（`Astro.glob()`、`entry.render()`、legacy collection 位置/类型、`output: 'hybrid'`、CJS 配置、`<ViewTransitions />`）与官方升级指南逐条吻合，也直接启发了本 skill 的 `## Read first` 指向 `references/removed-and-changed-apis.md`。另有两条判断被采纳：`markdown.processor` 要按项目是否依赖 remark/rehype 插件来选 Sätteri 或 unified；ClientRouter 的初始化应挂 `astro:page-load`、预绘制状态放 `astro:before-swap`。其 `tailwind.md`、`blog-recipes.md` 越界（视觉/内容配方）不取，`doc-endpoints.md` 绑定某个 agent 的文档检索工具不取。

**5. `incluud/astro-agent-skills`。** 9 star，但四个 skill 里没有一条 legacy 残留，是本波所有社区上游中「正确性」唯一满分的。可取的是默认值层面的表述：`.astro` 优先、island 保持小而叶子、不要凭空发明目录结构；以及 `schema: ({ image }) => z.object({ cover: image() })` 这个容易被漏掉的写法（用 `z.string()` 存封面路径是集合驱动页面布局抖动的常见来源）。其 `docs-lookup`/`create-component` 是工具包装，`astro-best-practices` 的无障碍段属 `frontend-design`，均不取。

**6. `delineas/astro-framework-agents`。** 结构上最像本 skill 想要的形态：15 个 reference + 9 个 rule 文件 + 三个决策框架（output 模式、hydration 策略、client/server island 取舍）。但它是「版本沉积型」仓库——同一个 reference 里 `## Setup (Astro 5+ Content Layer API)` 和 `### Content Collections (\`type: 'content'\`)` 并存，`references/ssr-adapters.md` 把 `output: 'hybrid'` 单列一节并在 SKILL.md 里称其覆盖「80% 真实项目」。抽查三条全错，按量表正确性 0 → REJECT。它的价值降级为覆盖面对照表：确认本 skill 没有漏掉 Astro 的任何主题面（i18n 与 styling 是有意划出边界，不是遗漏）。

## 冲突与裁决

裁决顺序：官方厂商 > 公认专家 > 社区；更新 > 更旧。社区上游星数普遍偏低（最高 44），因此**每条规则都对照 `withastro/docs` 源码核实**，冲突一律以官方为准。

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | `output` 的合法取值 | delineas（44★）：`static` / `server` / **`hybrid`** 三种，且 `hybrid` 是「80% 真实项目」的推荐值，并给出 `output: 'hybrid'` 的完整配置示例。gigio1023：`output: 'hybrid'` 属**已移除**写法，不得写进新代码 | **以官方为准：只有 `'static' | 'server'`**。混合站点 = 默认 `'static'` + 按路由 `export const prerender = false`。正文（Core rules 9、`references/routing-and-rendering.md`、`removed-and-changed-apis.md`）三处均按此写，并显式说明 `output: 'server'` 不增加任何能力、只是翻转默认值 | `reference/configuration-reference.mdx#output`：`**Type:** 'static' | 'server'`；`guides/on-demand-rendering.mdx` 的 `'server' mode` 一节；基线评测第 3 场也独立给出了同一结论 |
| 2 | content collections 的 `type` 与 `slug` | delineas：`references/content-collections.md` 在 content layer 章节之后仍保留 `### Content Collections (type: 'content')` / `### Data Collections (type: 'data')` 两节，路由示例用 `post.slug`（另一处又注明「Astro 5+ 用 `post.id`」，自相矛盾）。incluud / gigio1023 / awesome-copilot：`loader` 必填，禁用 `type:`，路由键是 `id` | **以官方为准：`type:` 与 `entry.slug` 均不存在**。v6 删除 legacy collections 及 `legacy.collections` flag，连 v5 遗留的隐式向后兼容一起删。正文只写 `loader` + `entry.id` + 独立 `render(entry)`，并把 legacy 写法列入 `removed-and-changed-apis.md` | `guides/upgrade-to/v6.mdx`「Removed: legacy content collections」「Legacy: content collections backwards compatibility」两节；`guides/content-collections.mdx` 全文只有 `loader`/`id` |
| 3 | `client:visible` 的选项 | delineas：`client:visible={{ rootMargin: "200px", threshold: 0.5 }}`，注释「50% 可见时 hydrate」 | **以官方为准：`client:visible` 只接受 `rootMargin`**，没有 `threshold`。多写的键被静默忽略——这类错误比报错更危险，因此本 skill 单列 `## Directive options that exist` 一节并写进 Core rules 4：`client:idle` 只有 `timeout`、`client:visible` 只有 `rootMargin` | `reference/directives-reference.mdx` 的 `client:visible` 段仅记 `rootMargin`（4.1.0 起），`client:idle` 段仅记 `timeout`（4.15.0 起） |
| 4 | 合法的配置文件扩展名 | astrolicious：CLI 会查找 `astro.config.js` / `.mjs` / **`.cjs`** / `.ts` | **以官方为准：CommonJS 配置在 v6 被移除**，只支持 `.mjs`、`.js`、`.ts`、`.mts`。正文 `references/routing-and-rendering.md` 的项目结构与 `removed-and-changed-apis.md` 的版本底线表都按此写 | `guides/upgrade-to/v6.mdx`「Removed: support for CommonJS config files」 |
| 5 | 大集合的性能开关 | delineas：「>1000 条时用 `glob({ retainBody: false })`，显著减小数据存储体积」 | **部分正确，官方细化后采纳**：`retainBody: false`（5.17+）解决的是**部署体积/平台大小上限**；构建期 **OOM** 要用 `deferRender: true`（7.1+）。两者成因不同，正文在 `references/content-collections.md` 里并列并给出「体积用前者、OOM 用后者」的选择句 | `reference/content-loader-reference.mdx` 的 `retainBody` 与 `deferRender` 两段；后者明确说明默认的 sync 期急切渲染是大集合 OOM 的原因 |
| 6 | live collections 的引入版本 | delineas：「Live Loader（Astro 6+）」 | **以官方为准，不写版本归属**：文档把 live collections 与 build-time collections 并列为两类正式集合，`reference/experimental-flags/` 下已无相关条目，仅 `cacheHint` 标注 `Since 7.0.0`。按标准「不写时间敏感表述」，正文只写当前形态（`src/live.config.ts` + `defineLiveCollection()` + 需要 adapter + 三条限制），不写它是哪一版引入的 | `guides/content-collections.mdx#live-content-collections`；`reference/experimental-flags/index.mdx` 现存条目仅 6 个，无 live collections |
| 7 | `client:idle` / `client:visible` 的适用场景 | incluud：把 `client:visible` 列为「deferred UI」的首选、`client:idle` 为「lower-priority enhancement」。delineas：`client:visible` 用在首屏元素上等于白付一个 observer；`client:idle` 在低端机上可能延迟 10 秒以上 | **以官方的优先级定义为准，并保留社区观察但重新落地到机制上**：文档标注 `client:load` = High、`client:idle` = Medium、`client:visible` = Low，且 `client:visible` 的适用场景写明是「below the fold」。因此正文写成机制推论而非道听途说——`IntersectionObserver` 对已在视口内的元素首次回调即触发（所以等于 `client:load` 加一个 observer）；`timeout` 选项的存在本身就说明 `requestIdleCallback` 可能迟迟不来。两条均标 `[official]`，不依赖 delineas | `reference/directives-reference.mdx` 各指令的 **Priority** 与 **Useful for** 字段、`client:idle` 的 `timeout` 说明 |
| 8 | Markdown 渲染管线 | delineas / incluud / astrolicious：默认 remark/rehype，直接给 `markdown.remarkPlugins` 示例。gigio1023：Astro 7 默认 Sätteri，按项目插件需求选 `markdown.processor` | **以官方为准：v7 默认 Sätteri**，`@astrojs/markdown-remark` 不再默认安装；`remarkPlugins`/`rehypePlugins`/`remarkRehype` 仍可用但必须先装该包并设 `markdown.processor: unified()`。正文在 `references/assets-integrations-and-build.md` 单列一节，并要求「建议插件前先检查这些选项」 | CHANGELOG `## 7.0.0`「Makes Sätteri the default Markdown processor」；`guides/upgrade-to/v7.mdx` 同名小节 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `withastro-docs` | docs.astro.build（源 `withastro/docs`，MIT 实查） | merged | 主干。全部技术事实：island 双向模型与指令完整选项集、props 序列化边界、content layer（loader 选项、Zod 4 schema、references、live collections）、路由与 `getStaticPaths` 约束、output 模式与 adapter、`astro:actions` 与 HTML 表单契约、middleware 与 `next(path)` 语义、sessions、`astro:env`、view transitions 与脚本重执行规则、图片与 Fonts API、route caching、advanced routing、CLI、以及 5→6→7 的移除与默认值变更全表 |
| `withastro-astro-skills` | `withastro/astro` `.agents/skills/{astro-code-review,astro-developer}`（MIT 实读） | merged | 评审姿态与 `## Output format`（只报值得动的问题、不擅自改写、声明丢弃项、结尾裁决）；三执行上下文推出的 `getImage()` 服务端专用与浏览器专属读取时机；「优先单元测试 → Container API」的测试取舍 |
| `awesome-copilot-astro` | `github/awesome-copilot` `instructions/astro.instructions.md`（MIT） | merged | Astro 7.x + Zod 4 基线的独立确认，以及必须成组出现的几组事实：`content.config.ts`+loader+`astro/zod`+顶层校验器、`astro sync` 时机、`ClientRouter` 来自 `astro:transitions`、`server:defer`+fallback+adapter、Rust 编译器严格 HTML、`compressHTML: 'jsx'` 与 `{" "}` |
| `gigio-astro-dev` | `gigio1023/astro-dev-skill`（MIT） | merged | read-first 移除 API 索引这一形态与其大部分清单；`markdown.processor` 的 Sätteri/unified 取舍；保留名 `src/fetch.ts`；ClientRouter 挂 `astro:page-load`、预绘制放 `astro:before-swap`；「需要 cookie/session/action/POST 的路由必须按需渲染」 |
| `incluud-astro-skills` | `incluud/astro-agent-skills`（MIT） | merged | `.astro` 优先与 island 保持叶子的默认值；build-time vs live 用 `src/content.config.*` / `src/live.config.*` 表达的决策；`schema: ({ image }) => …` 的封面图校验写法；显式禁用 `type: 'content'/'data'` |
| `delineas-astro-framework` | `delineas/astro-framework-agents`（MIT） | **reference** | 仅覆盖面对照：用它的 15 个 reference 主题清单确认本 skill 未漏掉 Astro 的任何主题面。正确性 0（裁决 1/2/3）→ 不作内容来源，任何 reference 的 sources 脚注中都不出现 |

不立 SOURCES 的 REJECT 候选：`astrolicious/agent-skills`（无许可 + CJS 配置错误 + 总分 4）、
`delineas` 的 `learning-astro`、`SpillwaveSolutions`、`oimiragieo/agent-studio`、`joncutrer`、
`achreftlili`、`fusengine`。理由见候选表。

## 基线缺口

无 skill（`uv run tools/run_evals.py astro --baseline`，anthropic/claude-opus-5 · medium）时，各场景未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 hydration 审计 | 「`client:visible` 只接受 `rootMargin`（不发明 `threshold`）」 | 基线通篇没有触及指令的选项面：既没给 `rootMargin` 建议（重 island 在慢网下来不及 hydrate 的实际补救），也没有「多写的键会被静默忽略」这层边界意识。这正是社区上游写错（裁决 3）而模型无从校正的地方 |
| 1 hydration 审计 | 「把只做汉堡菜单开关的导航 island 换成 `.astro` 里的 `<script>`」 | 基线把 `SiteNav` 从 `client:load` 降到 `client:idle`（还建议 `client:media`），仍然发运整个 React runtime。「降级不等于删除，一个开关不值一个 island」这条取舍没有出现 |
| 2 content collections 迁移 | 「改完后跑 `astro sync` 重新生成集合类型」 | 基线的 API 替换表 7 条全对，但没有提 `.astro/types.d.ts` 需要重新生成。这是改完集合配置后第一个假类型错误的来源 |
| 3 output 模式 + actions | Zod 4 形式（`z` 的来源、`z.email()`、`z.coerce.boolean()`） | **基线在这里改错了方向**：把 `astro:content` 换成了 `astro:schema`（v6 起同样弃用），并保留 `z.string().email()`；checkbox 用 `z.boolean().default(false)` 而非 `z.coerce.boolean()` |
| 3 output 模式 + actions | 「actions 是 `/_actions/<name>` 公开端点，每个 handler 必须自行鉴权」 | 基线给出了完整可用的修正文件，但通篇未提这条安全事实。这是 actions 最容易被误当成「内部函数」的一点 |
| 3 output 模式 + actions | 「`vite.build.rollupOptions.output` 迁到 `vite.environments.client.build.rollupOptions.output`」 | 基线原样保留了旧路径，未识别 Vite Environments API 带来的位置变更——`manualChunks` 会静默失效，不报错 |
| 4 负例 | 无（4 条全部达成，`skill_read == false`） | 作为「skill 不应被邻接任务误触」的对照保留 |

## 评测结果

模型固定 `anthropic/claude-opus-5` · `medium`（`tools/run_evals.py` 默认），基线与有 skill 各一遍。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 hydration 审计与 island 状态共享 | claude-opus-5:medium | 无（baseline） | false | **4 / 6** | 达成：`SiteFooter` 直接删指令、底部重组件降到 `client:visible`、每个 `client:*` 各自为根导致 Context 断裂（含 `SiteNav` 是第三个根）、库存改 `server:defer`。未达成：指令选项面、导航改 `<script>` |
| 1 hydration 审计与 island 状态共享 | claude-opus-5:medium | 有 | true | **6 / 6** | 两处缺口均被填补：给出 `client:visible={{ rootMargin: "200px" }}` 并写明「只接受 `rootMargin`，别塞别的选项（会被静默忽略）」；`SiteNav` 明确「删除指令（不是降级——降级仍然装载框架 runtime）」并改用 `.astro` 内 `<script>`。输出严格按本 skill 的 `## Output format`（`path:line - category` + Cost/Fix + Verdict），并主动声明丢弃了一条低收益发现 |
| 2 content collections 迁移到 Astro 7 | claude-opus-5:medium | 无（baseline） | false | **7 / 8** | 达成：改路径、`loader`、`astro/zod` + Zod 4 形式、`entry.id`、`getEntry()`、`render(post)`、`import.meta.glob`、`import.meta.env.SITE`。未达成：`astro sync` |
| 2 content collections 迁移到 Astro 7 | claude-opus-5:medium | 有 | true | **8 / 8** | 缺口填补：给出 `npx astro sync` 并说明「必须先跑，否则 `.astro/types.d.ts` 是旧的，会报假类型错误」。另外正确地把 `heroImage` 改用 `image()` 留作单独变更，理由是不应把行为变更混进升级 diff |
| 3 output 模式 + actions 表单契约 | claude-opus-5:medium | 无（baseline） | false | **7 / 10** | 达成：`hybrid` 已移除 → `static` + 按路由 `prerender = false`、加 adapter、删 experimental flags、`prerender = false`、`accept: 'form'`、`enctype`、`Astro.getActionResult()`。未达成：Zod 4 形式（反而改成了已弃用的 `astro:schema`）、`/_actions/` 公开端点鉴权、Vite Environments 路径 |
| 3 output 模式 + actions 表单契约 | claude-opus-5:medium | 有 | true | **10 / 10** | 三处缺口全部填补：`z` 来自 `astro/zod` + `z.email()` + `z.coerce.boolean()`；handler 内注明「每个 action 都是公开端点 `/_actions/signup`，授权必须写在 handler 里」并改用 `ActionError`；`vite.environments.client.build.rollupOptions.output`。另外补了 `isInputError()` 逐字段错误渲染与成功后 `Astro.redirect()` |
| 4 负例：React `useEffect` 重复请求 | claude-opus-5:medium | 无（baseline，`skills: []`） | false | 4 / 4 | 作为 React hook 依赖问题回答，未加载本 skill |
| 4 负例：React `useEffect` 重复请求 | claude-opus-5:medium | 有（`skills: []`） | **false** | 4 / 4 | 负例达标：`skill_read == false`，开头即判定「这不是 Astro 的 hydration 问题，是 island 内部纯 React 的自激振荡」，未误触本 skill |

结论：**通过**。三个正例共有 6 条基线未达成的行为在有 skill 时达成——`client:visible` 的选项边界、
导航 island → `<script>`、`astro sync`、Zod 4 形式（且纠正了基线改向已弃用 `astro:schema` 的错误）、
actions 公开端点鉴权、Vite Environments 的 `rollupOptions` 路径；没有任何一条从达成退回未达成；
负例 `skill_read == false`。

## 备注

**许可注意**
- `withastro/astro` 的 GitHub API 报 `NOASSERTION`：实读 `LICENSE` 为标准 MIT，尾部附一段说明
  `packages/create-astro` 与 `packages/astro` 中源自 `sveltejs/kit` 的部分同样适用该许可，
  与本 skill 取用的 `.agents/skills/**` 无关。故按 MIT / merged 处理。
- `withastro/docs` 的 `LICENSE` 实读为 MIT（Copyright (c) 2022 withastro）。按前两波的教训 2，
  官方文档许可允许即应为 **merged**——挂 reference 等于声明本 skill 的事实不来自官方文档，
  与实际写法自相矛盾。
- 无 GPL / AGPL / LGPL / 专有上游，无需 reference-only 降级。
- 唯一的 `license: NONE` 候选（`astrolicious/agent-skills`）已因总分 4 被 REJECT，未进 SOURCES。

**临界上游复核**
- `SpillwaveSolutions`（2026-01-02）距调研日 >8 个月，量表新鲜度 0 → REJECT，不作主题清单用途
  （其重心是 Firebase/GCP 部署，与本 skill 边界重叠极少）。
- `delineas`（2026-04-01）与 `incluud`（2026-04-23）都在 6 个月窗口内（4.5 / 4.6 个月），
  新鲜度 1 分成立；`delineas` 的落选原因是正确性而非活跃度。

**评测夹具的一处修正**
首轮基线的第 2 场指出夹具 `legacy-blog-route.astro` 把「原始路径」注释写成 HTML 注释放在
`---` 之前，会让 Rust 编译器把整段 frontmatter 当模板解析并报 `Expected } but found :`。
这是夹具自身的缺陷（真实 `.astro` 文件必须以 `---` 开头）。三个 `.astro` 夹具已改为在
frontmatter 内用 `//` 注释标注原始路径，并**重跑了全部基线**，以保证基线与有 skill 两组输入完全一致。

**未来同步时要盯的上游**
- `withastro/docs`：`kind: docs`，`check_upstream.py` 只能报 `manual check`。重点盯
  `guides/upgrade-to/`（新增 v8 即意味着本 skill 的移除表要整段重写）、
  `reference/experimental-flags/`（稳定化会改配置形态）、`reference/directives-reference.mdx`
  （指令选项集是本 skill 的判定标尺）。
- `withastro/astro` 的 `.agents/skills/`：官方若新增面向**应用开发者**的 skill（现有两个都不是），
  应立即升为主干上游。
- `delineas/astro-framework-agents`：结构最完整的社区上游，若清掉 `output: 'hybrid'`、
  legacy collections 与 `client:visible` 的 `threshold`，正确性可回到 2–3 分并重新具备 merged 资格。
- `github/awesome-copilot`：`instructions/astro.instructions.md` 已对齐 7.x，是最省力的版本漂移哨兵。

**放弃的方向**
- Starlight（文档站主题）、i18n 路由、styling/Tailwind：前者是独立产品面，后两者分别越界到
  尚不存在的 i18n 主题与 `frontend-design`。本 skill 在 `## Scope` 直述不覆盖。
- 不写 `scripts/`：Astro 的批量操作已由 `astro add` / `@astrojs/upgrade` / `astro sync` 覆盖，
  自造脚本只会与官方 CLI 争夺同一职责。
