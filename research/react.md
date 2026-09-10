# react 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-10
- 复核日期：2026-09-10（stars / `pushed_at` / license 全部当日用 GitHub API 复核；限流后改用仓库 HTML 与 `commits/HEAD.atom` 取推送时间）
- 检索途径：
  - 归档种子：`local://research-frontend.md`（前端 27 个候选，第 5/6/7/8/9/10/11/23/24/25/27 行与本 skill 相关）、`local://research-landscape.md`（布局模式与溯源惯例）
  - `web_search`：`"React 19 Next.js App Router agent skill SKILL.md github 2026"`、`site:skills.sh react nextjs shadcn skill`
  - <https://www.skills.sh> 搜索结果页（mindrally / laguagu / ovachiever / giuseppe-trisciuoglio / debbl 五个新候选由此发现）
  - 领域官方组织仓库：`vercel-labs/`、`vercel/next.js`（`canary` 分支 `skills/`）、`shadcn-ui/ui`、`openai/plugins`、`reactjs/react.dev`
- GitHub API 核对方式：`curl -s https://api.github.com/repos/<owner>/<repo>`（`stargazers_count` / `pushed_at` / `license.spdx_id`）
- 版本事实复核（写入正文的版本底线均来自这一步）：
  - npm registry：`next@16.3.4`、`react@19.3.0`、`@next/playwright@16.3.4`
  - react.dev 博客 `2025/10/01/react-19-2`：`<Activity>` 与 `useEffectEvent` 是 **React 19.2** 新增（现为稳定 API，文档侧栏标 `react-dom@19.3`）
  - `useActionState` / `useFormStatus` / `useOptimistic`：react.dev 稳定参考页存在
  - nextjs.org `config/next-config-js/cacheComponents` 与 `guides/instant-navigation` 两页当日可访问

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | vercel-labs/agent-skills `skills/react-best-practices/` | https://github.com/vercel-labs/agent-skills | 31,025 | 2026-08-28 | 仓库无 LICENSE；skill frontmatter 声明 MIT | 70 条性能规则，8 类按影响排序（`async-`/`bundle-`/`server-`/`client-`/`rerender-`/`rendering-`/`js-`/`advanced-`） | 3 | 3 | 3 | 3 | 1 | 13 | **INCLUDE** | 厂商自撰、CI 有测试用例（`packages/react-best-practices-build` + `test-cases.json`）、每条规则含 why/incorrect/correct，是本领域密度最高的素材 |
| 2 | vercel-labs/agent-skills `skills/composition-patterns/` | ↑ | ↑ | ↑ | ↑ | 8 条组合规则：布尔属性泛滥、compound components、state/actions/meta 上下文接口、lift state、显式变体、children vs render props、React 19 `ref` 与 `use()` | 3 | 3 | 3 | 3 | 1 | 13 | **INCLUDE** | 唯一成体系的组件 API 设计规则集；与性能规则互补不重叠。注意目录名是 `composition-patterns`，不是种子清单里写的 `vercel-composition-patterns`（那是 frontmatter 的 `name`） |
| 3 | vercel-labs/agent-skills `skills/react-view-transitions/` | ↑ | ↑ | ↑ | ↑ | `<ViewTransition>` + `addTransitionType`，5 个 references（CSS recipes、Next.js 集成、troubleshooting） | 3 | 3 | 2 | 2 | 1 | 11 | **MAYBE（本批不合入）** | 质量够，但属于「动效/转场」而非 React 工程；与 `frontend-design` 的动效节重叠。留给后续 motion 主题，避免两个 skill 对同一话题各说一套 |
| 4 | vercel-labs/agent-skills `skills/web-design-guidelines/` | ↑ | ↑ | ↑ | ↑ | 40 行 dispatcher，正文靠抓取 Vercel Web Interface Guidelines | 3 | 3 | 0 | 2 | 1 | 9 | **REJECT（越界）** | 本身几乎无内容，且其目标内容归 `frontend-design` skill；本 skill 不做视觉与 UX 评审 |
| 5 | vercel/next.js `skills/next-cache-components-optimizer/`（`canary`） | https://github.com/vercel/next.js/tree/canary/skills | 142,215 | 2026-09-10 | MIT | P→G 七阶段 instant-navigation 工作流；`reference/{patterns,real-app-patterns,red-test-robustness}.md` + `rig-template.md` + `test-template.md`；要求 Next.js 16.3+ | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE** | 官方且与框架版本同步发布；把「静态外壳」目标编码成 `@next/playwright` `instant()` 的失败测试，工程化程度是所有候选里最高的 |
| 6 | vercel/next.js `skills/next-cache-components-adoption/`（`canary`） | ↑ | ↑ | ↑ | MIT | 打开 `cacheComponents` 后的阻塞路由清理流水线；`cache-components-instant-false` codemod；`instant = false` 与就地修复的取舍；`references/per-page-decisions.md` | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE** | 与第 5 行互为前后半段：先能构建通过，再谈把外壳做大 |
| 7 | vercel/next.js `skills/next-partial-prefetching-adoption/`、`skills/next-dev-loop/`（`canary`） | ↑ | ↑ | ↑ | MIT | Partial Prefetching 采纳与 `<Link prefetch>` 审计；`/_next/mcp` + 浏览器交叉验证的开发环路 | 3 | 3 | 2 | 3 | 2 | 13 | **INCLUDE（仅作后续步骤引用）** | 只取「优化完成后下一步查什么」与「怎样在浏览器里验证一次修复」两点，写入 `nextjs-cache-components.md` 的收尾节，不复制其工作流全文 |
| 8 | openai/plugins `plugins/vercel/skills/nextjs/` | https://github.com/openai/plugins | 6,340 | 2026-09-08 | 无（仓库 API `license: null`） | App Router 语义 20 个 references：file-conventions、app-router-files、rsc-boundaries、async-patterns、runtime-selection、directives、functions、error-handling、data-patterns、route-handlers、metadata、image、font、bundling、scripts、hydration-error、suspense-boundaries、parallel-routes、self-hosting、debug-tricks | 3 | 3 | 3 | 3 | 0 | 12 | **INCLUDE** | Vercel 撰写、放在 OpenAI 插件仓库；是唯一覆盖完整 App Router API 语义的参考语料。frontmatter 是 Codex 专属（`metadata.priority` / `pathPatterns` / `bashPatterns` / `promptSignals`），合入时必须全部剥离 |
| 9 | shadcn-ui/ui `skills/shadcn/` | https://github.com/shadcn-ui/ui | 123,485 | 2026-09-10 | MIT | `rules/{styling,forms,composition,chat,icons,base-vs-radix}.md` + `cli.md` + `registry.md` + `customization.md` + `mcp.md` | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE** | 官方厂商 skill，且拒绝硬编码组件 API——改为让 agent 跑 `npx shadcn@latest docs <component>` 取当前文档，这是最强的抗腐化设计。合入时必须去掉 `user-invocable` / `allowed-tools`，并把 `` !`npx shadcn@latest info --json` `` 动态注入改成显式第一步命令 |
| 10 | addyosmani/agent-skills `skills/frontend-ui-engineering/` | https://github.com/addyosmani/agent-skills | 93,313 | 2026-09-08 | MIT | 组件目录共置、组合优于配置、容器/展示分离、6 行状态选型表、prop drilling 上限、skeleton 与乐观更新配方（其余为设计与 a11y） | 2 | 3 | 2 | 3 | 2 | 12 | **INCLUDE（仅架构与状态节）** | 公认专家（Chrome）、维护活跃；设计俗套表与 WCAG 节归 `frontend-design`，本 skill 只取架构/状态/加载态。注意其 `## See Also` 指向仓库级 `../../references/`，单 skill 安装不会带上（上游 issue #361），不能引用该路径 |
| 11 | anthropics/skills `skills/web-artifacts-builder/` | https://github.com/anthropics/skills | 175,538 | 2026-09-03 | 每 skill 各自 `LICENSE.txt` | React + Tailwind + shadcn 的 artifact 脚手架，`scripts/init-artifact.sh`、`bundle-artifact.sh`、打包好的组件 tar | 3 | 3 | 2 | 2 | 1 | 11 | **MAYBE → reference** | 内容强绑定 Claude artifact 运行时（预置 tar、固定目录），移植后会误导普通项目；只作为「从零脚手架惯例」对齐读物，不复制任何文字或脚本 |
| 12 | react.dev（`reactjs/react.dev`） | https://react.dev/reference | 11,794 | 2026-09-10 | CC-BY-4.0 | React 官方 API 参考与 “You Might Not Need an Effect” 等指南 | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE（docs）** | 正确性裁决方；`<Activity>` / `useEffectEvent` 的版本底线、`useActionState` 三件套、`cache()` 语义均以此为准 |
| 13 | nextjs.org/docs | https://nextjs.org/docs | —（vercel/next.js 同仓库，MIT） | 2026-09-10 | MIT | App Router 官方文档，含 `cacheComponents`、`instant-navigation`、`use cache` | 3 | 3 | 3 | 3 | 2 | 14 | **INCLUDE（docs）** | 数据获取与缓存语义的裁决方；版本底线核对入口 |
| 14 | vercel-labs/next-skills | https://github.com/vercel-labs/next-skills | 979 | 2026-06-23 | 无 | 曾经的 `next-best-practices` 等 | 3 | 0 | — | — | 0 | ≤4 | **REJECT** | README 已声明弃用并指向 `vercel/next.js`；`next-best-practices` 已删除，改为随框架分发的 bundled docs + 生成的 `AGENTS.md`。3 个月无推送，内容已被第 5–7 行取代 |
| 15 | agents-inc/skills `src/skills/web-meta-framework-nextjs/` | https://github.com/agents-inc/skills | 24 | 2026-09-06 | 无 | App Router 15–16 语义 + React 19 表单 hooks（`useActionState` / `useFormStatus` / `useOptimistic`）+ Cache Components，373 行 SKILL.md 加 `examples/` | 0 | 3 | 2 | 2 | 0 | 7 | **MAYBE → 不合入** | 24★、单组织、无许可、正文含仓库专属约定；唯一独有价值是 React 19 表单 hooks——该缺口改由 react.dev 官方参考页补齐（见「冲突与裁决」R5），不必引入未审核上游 |
| 16 | mindrally/skills `skills/nextjs-react-typescript` | https://github.com/mindrally/skills | 260 | 2026-09-03 | 未声明 | TS + React + App Router + shadcn + Radix + Tailwind 全栈打包 | 0 | 3 | — | — | 0 | ≤4 | **REJECT** | skills.sh 列出的路径在 `main`/`master` 上都取不到原文（raw 404），无法审计；且「一个 skill 打包整个栈」与本仓库「每生态一个 skill」的粒度冲突 |
| 17 | laguagu/claude-code-nextjs-skills `nextjs-shadcn` | https://github.com/laguagu/claude-code-nextjs-skills | 62 | 2026-09-02 | 未声明 | Next.js + shadcn 界面搭建与主题一致性 | 0 | 3 | 1 | — | 0 | ≤4 | **REJECT** | 62★、单作者、无许可；覆盖面是第 9 行官方 shadcn skill 的子集 |
| 18 | giuseppe-trisciuoglio/developer-kit `shadcn-ui` | https://github.com/giuseppe-trisciuoglio/developer-kit | 343 | 2026-09-10 | 未声明 | shadcn 组件模式、Zod 表单、主题 | 0 | 3 | 1 | — | 0 | ≤4 | **REJECT** | 通用开发工具箱里的一个子技能，内容为官方 shadcn skill 的旧快照（仍在讲 `space-y-*` 式布局），会与第 9 行的规则直接冲突 |
| 19 | ovachiever/droid-tings `nextjs-shadcn-builder` | https://github.com/ovachiever/droid-tings | 52 | 2025-11-25 | 未声明 | 新建 Next.js + shadcn 应用或迁移前端 | 0 | 0 | 1 | — | 0 | ≤4 | **REJECT** | 最近推送 2025-11-25，已超 6 个月无维护；Next.js 版本快照必然腐化 |
| 20 | debbl/shadcn-hooks `shadcn-hooks` | https://github.com/debbl/shadcn-hooks | 61 | 2026-06-01 | 未声明 | shadcn 风格 hooks 集 | 0 | 1 | 1 | — | 0 | ≤4 | **REJECT** | 61★、3 个月无推送；是组件库外围产物，不是 React 工程规则 |
| 21 | PyModel/react-frontend-skills | https://github.com/PyModel/react-frontend-skills | 3 | 2026-09-10 | MIT | 18 个 skill（React 19、Next 16、TS 7、Tailwind v4、shadcn） | 0 | 3 | 1 | — | 2 | 6 | **REJECT** | 3★、1 fork、0 watcher，却有 SEO 化 README；未经任何社区审核的版本快照集合 |
| 22 | gocallum/nextjs16-agent-skills | https://github.com/gocallum/nextjs16-agent-skills | 23 | 2026-01-21 | 无 | Next.js 16 skill 集 | 0 | 0 | 1 | — | 0 | ≤4 | **REJECT** | 近 8 个月无推送，版本快照已过期 |
| 23 | fusengine/agents | https://github.com/fusengine/agents | 25 | 2026-09-04 | MIT | 含 Next.js/React 相关 agent 定义 | 0 | 3 | 1 | — | 2 | 6 | **REJECT** | 25★ 单作者，形态是 agent 定义而非 skill；内容为官方规则的稀释版 |
| 24 | magnus919/agent-skills | https://github.com/magnus919/agent-skills | 76 | 2026-09-09 | MIT | 通用 skill 集，含前端条目 | 0 | 3 | 1 | — | 2 | 6 | **REJECT** | 76★、未经审核；无 React/Next 独有洞见 |
| 25 | gohypergiant/agent-skills | https://github.com/gohypergiant/agent-skills | 23 | 2026-09-09 | Apache-2.0 | 组织内部 skill 集 | 0 | 3 | 1 | — | 2 | 6 | **REJECT** | 23★，内容面向该组织自身技术栈 |
| 26 | EnderPuentes/ai-agent-skills | https://github.com/EnderPuentes/ai-agent-skills | 2 | 2026-06-23 | 无 | 个人 skill 集 | 0 | 1 | 0 | — | 0 | ≤4 | **REJECT** | 2★、3 个月无推送、无许可 |
| 27 | Impertio-Studio/{shadcn,TailwindCSS}-Claude-Skill-Package、grixalai/shadcn-ui__skill、supercent-io/skills-template | — | — | — | — | shadcn / Tailwind skill 包 | 0 | — | — | — | 0 | ≤4 | **REJECT（已消失）** | 三者当日 GitHub API 均返回 404（仓库删除或改名）。种子清单里的这几行不再是有效候选 |
| 28 | tailwindlabs/tailwindcss | https://github.com/tailwindlabs/tailwindcss | 97,491 | 2026-09-08 | MIT | **无官方 skill** | — | — | — | — | — | — | **REJECT（不存在）** | 截至 2026-09-10 官方未发布 skill。Tailwind 约定改由第 9 行 shadcn 的 `rules/styling.md` 承担，本仓库不单独立 `tailwind` skill——一个会腐化的文档快照 skill 危害大于收益 |
| 29 | JetBrains/skills `react-best-practices/`、`vercel-labs-web-design-guidelines/` | https://github.com/JetBrains/skills | 342 | 2026-06-29 | 无 | 第 1、4 行的镜像 | 3 | 0 | — | — | 0 | ≤4 | **REJECT（重复）** | 镜像仓库，2 个多月未同步；直接跟踪原始上游 |
| 30 | vuejs-ai/skills `vue-best-practices` | https://github.com/vuejs-ai/skills | 2,839 | 2026-05-30 | MIT | Vue 3 最佳实践 | 2 | 1 | 3 | — | 2 | — | **REJECT（越界）** | 与本 skill 无交集，仅用作负例评测的判定参照（本 skill 不得对 Vue 代码套用 React 规则）。主人已明确 `vue` 主题暂缓 |

## 深度审查

### 1. vercel-labs/agent-skills — `react-best-practices`（总分 13，INCLUDE）

- **结构**：`SKILL.md`（149 行，纯规则索引）+ `rules/<prefix>-<name>.md` 一文件一规则（含 `title` / `impact` / `impactDescription` / `tags` frontmatter，正文是 why + incorrect + correct）+ 编译版 `AGENTS.md` + `metadata.json` + `rules/_sections.md`（定义 8 个分节的顺序与影响等级）。
- **frontmatter**：`name: vercel-react-best-practices`（**与目录名 `react-best-practices` 不一致**，按 Agent Skills 规范这是错的，合入时按本仓库标准取目录名）、`description`、`license: MIT`、`metadata.author/version`。
- **质量**：规则 ID 带分类前缀且按影响排序，agent 可以直接分诊；内容跟得上当前 React（`<Activity>`、`useEffectEvent`、`after()`、`toSorted()`）。抽查三条对照官方文档：`rerender-derived-state-no-effect` 对齐 react.dev “You Might Not Need an Effect”；`advanced-effect-event-deps` 对齐 react.dev `useEffectEvent#effect-event-in-deps`；`server-cache-react` 关于 `React.cache()` 浅比较与 Next.js `fetch` 自动记忆化的说明与 react.dev / nextjs.org 一致。三条全对。
- **agent 绑定**：无。规则文件是纯 markdown，可直接重写。
- **与其他候选的重叠**：约 30% 是 Next.js 专属（`server-*` 全部、`bundle-dynamic-imports` 用 `next/dynamic`、`async-api-routes`、`server-after-nonblocking`）。这是本 skill 最重要的**拆分决策**（见裁决 R1）。`async-*` / `server-parallel-*` 与第 8 行 `data-patterns.md` 的「避免瀑布」一节直接重叠（见裁决 R2）。

### 2. vercel-labs/agent-skills — `composition-patterns`（总分 13，INCLUDE）

- **结构**：与 `react-best-practices` 同构（`rules/` + `AGENTS.md`），8 条规则分 4 类：`architecture-`（2）、`state-`（3）、`patterns-`（2）、`react19-`（1）。
- **质量**：所有例子来自同一个真实场景（聊天 composer 的 channel / thread / edit / forward 四种形态），因此「布尔属性泛滥 → compound components → 上下文接口 → lift state」是一条完整的重构链，而不是四条孤立建议。`state-context-interface` 提出的 `{ state, actions, meta }` 三段式上下文接口是本批候选里唯一可直接照做的依赖注入范式。
- **agent 绑定**：无。
- **重叠**：与第 10 行 addyosmani 的「组合优于配置」同向但更深一层（addy 停在 `<Card><CardHeader>` 级别，Vercel 给到 provider 契约级别）；两者叠加即可，无冲突。`react19-no-forwardref` 与 React 19 的 `ref` 作为普通 prop、`use(Context)` 一致（react.dev 核对通过）。

### 3. vercel/next.js — `next-cache-components-optimizer` + `next-cache-components-adoption`（总分 14，INCLUDE，配对）

- **结构（optimizer）**：`SKILL.md` 477 行 + `reference/patterns.md`（9 个 before→after 阻塞形态）+ `reference/real-app-patterns.md` + `reference/red-test-robustness.md` + `rig-template.md` + `test-template.md`。frontmatter 只有 `name` + `description`（合规）。
- **结构（adoption）**：`SKILL.md` 249 行 + `references/{per-page-decisions,dev-only-validations}.md`。
- **质量**：这是一个**工作流型** skill 而非知识型：阶段 P→G 每段以门收尾，且显式区分「不变量（验证环路）」与「你的部分（rig）」。它的核心洞见——`instant()` 是尺子不是秒表、没有可信 RED 就不要开始优化、`instant()` 通过不等于外壳非空（`fallback={null}` 的空壳陷阱）——在其他任何候选里都没有对应物。
- **agent 绑定**：轻度。`next-dev-loop` 与 `agent-browser` 的安装建议是工具偏好，可改写为「用你手上的浏览器自动化验证」。
- **重叠**：`patterns.md` 的「把 `await` 推进 Suspense 子组件」与第 1 行 `async-suspense-boundaries`、第 8 行 `suspense-boundaries.md` 部分重叠，但目标不同：前两者为了首屏更快，Cache Components 为了让路由能被预渲染成静态外壳。合入时统一在 `nextjs-cache-components.md` 里讲，正文其它地方不重复。
- **版本门**：Next.js 16.3+ 且 `cacheComponents: true`。当日 `next@16.3.4`，门是合理的、且必须写进正文（低于 16.3 的项目照做会得到错误结论）。

### 4. openai/plugins — `plugins/vercel/skills/nextjs`（总分 12，INCLUDE）

- **结构**：`SKILL.md` 197 行是一张纯目录，20 个 `references/*.md`（3,528 行）承载全部内容 + `agents/openai.yaml`。
- **frontmatter**：`name`、`description`，其余全是 Codex 专属：`metadata.priority`、`metadata.docs`、`metadata.sitemap`、`metadata.pathPatterns`、`metadata.bashPatterns`、`metadata.promptSignals.{phrases,allOf,anyOf,noneOf,minScore}`。按本仓库标准第 1.2 节全部剥离。
- **质量**：以「检测规则」而非「教程」组织，正合 skill 的用法。`rsc-boundaries.md` 给出可机械判定的表（`'use client'` + `async` = 非法；`Date` / `Map` / class 实例 / 函数不可序列化，Server Action 是唯一例外）；`error-handling.md` 抓住了 `redirect()` 抛异常不能被 try-catch 吞掉这个高频真 bug；`parallel-routes.md` 明确 `default.tsx` 缺失导致刷新 404、关闭 modal 必须 `router.back()`。抽查三条：async client component 非法、`useSearchParams` 需 Suspense 边界、v16 `middleware.ts` → `proxy.ts`（`proxyConfig`），三条与 nextjs.org 一致。
- **许可**：仓库 API `license: null`。按本仓库宽松策略可 merged，`SOURCES.yaml` 的 `notes` 记录无授权、以署名方式使用。
- **重叠**：与第 1 行的分工见裁决 R2；`bundling.md` 的 `serverExternalPackages` / `transpilePackages` / `dynamic(ssr:false)` 与 `bundle-*` 规则互补（一个讲「怎么修构建报错」，一个讲「怎么减体积」）。
- **缺口**：`self-hosting.md` 371 行里 Docker / PM2 / nginx 篇幅大而与 React 工程关系弱，只取「`output: 'standalone'`、多实例 ISR 必须配 cache handler、`static/` 要单独复制」三条硬事实。

### 5. shadcn-ui/ui — `skills/shadcn`（总分 14，INCLUDE）

- **结构**：`SKILL.md` 277 行 + `rules/{styling,forms,composition,chat,icons,base-vs-radix}.md` + `cli.md` + `registry.md` + `customization.md` + `mcp.md` + `evals/evals.json` + `agents/openai.yml`。
- **frontmatter**：`name`、`description`、`user-invocable: false`、`allowed-tools: Bash(npx shadcn@latest *)...`——**Claude Code 口味**，必须剥离；正文第 14–18 行用 `` !`npx shadcn@latest info --json` `` 做上下文注入，本仓库校验器直接拒绝该写法，必须改成显式的「第一步跑这条命令」。
- **质量**：最强的一点是它不硬编码组件 API，而是要求 agent 跑 `npx shadcn@latest docs <component>` 再取文档；规则本身也全是可机械检查的（`gap-*` 而非 `space-y-*`、`size-*` 而非 `w-* h-*`、图标用 `data-icon` 且不加尺寸类、校验态 `data-invalid` + `aria-invalid`、覆盖层组件不手写 `z-index`、registry 不许猜）。`base` 与 `radix` 的 API 差异（`asChild` vs `render`、`nativeButton={false}`、`Select` 的 `items` prop）是真实踩坑点。
- **agent 绑定**：中度但可机械剥离（见上）。
- **重叠**：其 `rules/styling.md` 实质就是 Tailwind 规则——这是「本批不立 `tailwind` skill」的最强论据（第 28 行）。与 `frontend-design` 的语义 token 主张同向；两者放在不同 skill 里，本 skill 只讲「shadcn 项目里怎么写 class」。
- **裁剪**：`rules/chat.md`（250 行聊天原语）与 `registry.md`（277 行 registry 作者向）不是通用 React 工程内容，只在 `shadcn-ui.md` 里各留一段指路与「不许猜 registry」的硬规则。

### 6. addyosmani/agent-skills — `frontend-ui-engineering`（总分 12，INCLUDE 部分）

- **结构**：单文件 `SKILL.md` 328 行，无 `references/`；`## See Also` 指向仓库级 `../../references/accessibility-checklist.md`。
- **frontmatter**：只有 `name` + `description`（合规）。
- **质量**：架构与状态两节具体可用——目录共置样式、组合优于配置的正反例、容器/展示分离（含 loading / error / empty 三态）、6 行状态选型表、prop drilling 不超过 3 层、skeleton 与 TanStack Query 乐观更新配方。其余（AI 俗套表、WCAG、响应式断点）归 `frontend-design`。
- **agent 绑定**：无，但**可移植性有缺陷**：单 skill 安装不会带上仓库级 `references/`（上游 issue #361），所以 `## See Also` 那行在安装后是死链——合入时不能保留该引用。
- **重叠**：状态选型表与 Vercel `state-*` 规则层次不同（一个选方案，一个设计上下文契约），叠加使用。

### 7. anthropics/skills — `web-artifacts-builder`（reference）

`LICENSE.txt` 为每 skill 单独提供，本批只作阅读对齐，不复制任何文字或脚本，因此无需判定其许可文本细节。其价值只在「从零起一个 React + Tailwind + shadcn 项目时的目录与依赖惯例」，本 skill 的 `add-shadcn-component` 工作流已由官方 CLI（`npx shadcn@latest init --preset`）覆盖，故 `relation: reference`。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| R1 | Vercel 的 `server-*`、`bundle-dynamic-imports`、`async-api-routes`、`server-after-nonblocking` 是 React 规则还是 Next 规则？ | 上游把它们和通用 React 规则混在同一个 `rules/` 目录里 | **归入 `nextjs-*` 参考**：`server-*` 与 `async-api-routes`、`server-after-nonblocking` 进 `nextjs-data-and-caching.md`；`bundle-dynamic-imports`（`next/dynamic`）与 `bundle-*` 其余条目进 `rules-bundle-client.md`，但 `next/dynamic` 的写法标注 Next.js 专属并在 `nextjs-ops-and-debug.md` 的构建节交叉说明。`rules-*.md` 四份只留框架无关的 React/JS 规则 | 任务书明确要求；且混放会让非 Next 的 React 项目读到 `after()` / `next/dynamic` 这类不存在的 API |
| R2 | 数据获取语义：Vercel 规则 vs openai-plugins `data-patterns.md` 重叠且措辞不同 | Vercel 讲「怎样更快」（`Promise.all`、`React.cache`、LRU、`after()`）；openai-plugins 讲「用哪种机制」（Server Component 读 / Server Action 写 / Route Handler 对外） | **语义以 openai-plugins + nextjs.org 为准，性能以 Vercel 规则为准**。`nextjs-data-and-caching.md` 先给「读写机制选择表」，再接 Vercel 的性能规则条目 | 官方厂商文档 > skill 措辞；两者不真冲突，只是层次不同 |
| R3 | shadcn 的 Tailwind 约定 vs 其他候选的样式主张 | 第 18 行候选仍在教 `space-y-*`；`frontend-design` skill 讲语义 token 但不讲 shadcn 具体类名 | **shadcn `rules/styling.md` 是本仓库唯一的 Tailwind 约定来源**（`gap-*`、`size-*`、`truncate`、`cn()`、`data-icon`、`data-invalid`、覆盖层不手写 z-index、无 `dark:` 手写覆盖） | 任务书要求；官方厂商 > 社区快照；且这些规则可机械检查 |
| R4 | shadcn 上游的动态注入 `` !`npx shadcn@latest info --json` `` | 上游依赖 harness 在加载时执行命令注入项目上下文 | **改写为工作流第一步的显式命令**：`add-shadcn-component` 的第 1 项就是「跑 `npx shadcn@latest info --json`，从输出读 `aliases` / `isRSC` / `tailwindVersion` / `base` / `iconLibrary` / `resolvedPaths` / `packageManager`」 | 本仓库标准第 1.3 节禁用动态注入，校验器会报错；且只有部分 harness 会执行该语法，注入失败时 agent 会静默地凭猜测工作 |
| R5 | React 19 表单 hooks（`useActionState` / `useFormStatus` / `useOptimistic`）没有任何 INCLUDE 上游覆盖 | 唯一覆盖它们的是第 15 行 24★ 无许可仓库 | **不引入该上游**，改从 react.dev 官方参考页撰写，写入 `architecture-and-state.md` 的「Server Action 表单状态」小节，并在 `SOURCES.yaml` 记 `react-docs` 贡献此节 | 官方文档 > 未审核社区仓库；缺口用官方一手材料补，不用二手转述 |
| R6 | 版本敏感 API 的可用性底线 | 上游或不标（Vercel `rendering-activity` 直接用 `<Activity>`）或标得含糊 | 正文一律标底线：`<Activity>` / `useEffectEvent` 标 `(React 19.2+)`；`ref` 作为普通 prop、`use(Context)` 标 `(React 19+)`；Cache Components / `export const instant` / `@next/playwright` `instant()` 标 `(Next.js 16.3+)`；`proxy.ts` 标 `(Next.js 16+)`；`next experimental-analyze` 标 `(Next.js 16.1+)`；`optimizePackageImports` 标 `(Next.js 13.5+)` | react.dev 19.2 发布博客与 nextjs.org 当日复核（见「调研日期」节）。不写「2026 年以前用旧写法」这类时间敏感表述 |
| R7 | React Compiler 是否让 `memo` / `useMemo` 规则失效 | Vercel 在 `rerender-memo`、`rendering-hoist-jsx`、`rerender-split-combined-hooks` 各挂一句「启用 React Compiler 后不必手动 memo」 | **在 `rules-rendering-rerender.md` 顶部统一写一次前置判断**（`babel-plugin-react-compiler` / `reactCompiler` 配置存在 → 跳过纯 memo 化条目，仍保留正确性条目），条目里不再逐条重复 | 本仓库标准第 3 节「术语一致、不罗列」；且逐条重复会让模型误以为每条都有例外 |
| R8 | 组件内定义组件 / 依赖数组 / 派生状态等条目在 Vercel 归「性能」 | 上游把 `rerender-no-inline-components`、`js-tosorted-immutable` 放在性能分类 | 正文按**后果**而非上游分类归位：这两条会导致状态丢失与 prop 变异（正确性 bug），写进 `Core rules` 而不只是性能参考 | 上游自己的 impact 描述就是「prevents remount」「prevents mutation bugs」；Core rules 的定义是「违反即 bug」 |
| R9 | `instant()` 通过是否等于路由已经「instant」 | 空壳（`fallback={null}` 包住整页）也能让 `instant()` 通过；`export const instant = false` 让校验跳过但导航依旧阻塞 | 正文把「非空外壳」写成 `make-route-instant` 工作流的独立判定项，并明确 `instant = false` 是「接受阻塞」的记录手段，不是达标手段 | 上游 optimizer SKILL.md 与 adoption SKILL.md 都反复强调，属真实陷阱 |
| R10 | addyosmani 的 `## See Also` 指向仓库级 `references/` | 上游正文有该引用 | 合入时删除该引用；本 skill 的 a11y 相关内容一律不写，由 `frontend-design` 承担 | 上游 issue #361：单 skill 安装不复制仓库级 `references/`，保留即死链；且本仓库标准第 4 节禁止 reference 互链与越界内容 |
| R11 | Vercel `rerender-memo-with-default-value` 的因果解释是否正确 | 上游主张「memo 组件的非原始默认参数值（`onClick = () => {}`）会因每次渲染产生新实例、无法通过 `memo()` 的严格相等比较，从而打破 memo 化」 | **判定上游解释错误，规则本身保留但重写理由**：`memo` 比较的是父组件传入的 props 对象，而默认参数是在组件函数体执行时才生效——调用方不传该 prop 时两次渲染看到的都是 `undefined`，浅比较通过，memo 并未被打破。真正的代价在组件内部：该新身份会流入 hook 依赖数组与被 memo 的子组件，导致每次渲染都失效。正文按后者写，并明确指出上游措辞不成立 | React `memo` 语义（react.dev `memo` 参考页：比较发生在渲染之前，对 props 做浅比较）。本轮基线评测里默认模型独立指出了同一点，与本裁决一致——这也是把它写清楚的额外理由：如果正文照抄上游说法，模型会正确地反驳这个 skill |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `vercel-react-bp` | vercel-labs/agent-skills `skills/react-best-practices/`、`skills/composition-patterns/` | merged | 按影响排序的性能规则（保留规则 ID、why、incorrect、correct）与组合 / 状态契约规则 |
| `addy-frontend-ui` | addyosmani/agent-skills `skills/frontend-ui-engineering/` | merged | 目录共置、组合优于配置、容器/展示分离、状态选型表、prop drilling 上限、skeleton 与乐观更新 |
| `nextjs-cache-components` | vercel/next.js（`canary`）`skills/next-cache-components-optimizer/`、`skills/next-cache-components-adoption/`、`skills/next-partial-prefetching-adoption/`、`skills/next-dev-loop/` | merged | Cache Components / instant navigation 工作流（阶段与门、9 个阻塞形态的 before→after、`instant()` 测试模板、采纳期的 `instant = false` 取舍、优化后的 Partial Prefetching 检查） |
| `openai-plugins-nextjs` | openai/plugins `plugins/vercel/skills/nextjs/` | merged | App Router 语义全集：file conventions、RSC 边界、async params、runtime、directives、functions、error handling、data patterns、route handlers、metadata、image、font、bundling、scripts、hydration、suspense、parallel routes、self-hosting、debug |
| `shadcn-official` | shadcn-ui/ui `skills/shadcn/` | merged | shadcn 工作流（info → docs → add → 复查）、样式 / 表单 / 组合 / 图标规则、base 与 radix 的 API 差异、registry 硬规则 |
| `anthropic-web-artifacts` | anthropics/skills `skills/web-artifacts-builder/` | reference | 从零脚手架惯例的对齐读物；未复制任何文字或脚本 |
| `react-docs` | https://react.dev/reference | merged (docs) | 正确性裁决与版本底线；React 19 表单 hooks 一节的一手来源 |
| `nextjs-docs` | https://nextjs.org/docs | merged (docs) | 数据获取与缓存语义裁决、`cacheComponents` / `instant-navigation` 版本事实 |

## 基线缺口

无 skill（`uv run tools/run_evals.py react --baseline`，默认模型，四个场景 `skill_read` 全为
`False`）时的逐条判定。基线答案存于 `/tmp/hs-evals/react/default/baseline/<n>/answer.md`。

基线整体很强：RSC 边界、瀑布、派生状态、原地变异这些「模型已知」的条目基本都能命中，这本身是
有用的信号——说明 skill 不该再重复讲这些，价值必须落在「可引用的规则 ID」「必须去取当前文档的
工作流」「版本门与前置判断」上。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1（App Router 审查） | 「引用具体规则 ID `bundle-dynamic-imports`」 | 基线正确地建议了 `next/dynamic`，但没有任何可引用的规则标识，无法在团队里形成一致的复查语言 |
| 1 | 「指出 barrel 导入并引用 `bundle-barrel-imports`（或建议 `optimizePackageImports`）」 | 基线把 recharts/lucide-react 归为「重量级依赖 → 懒加载」，完全没提 barrel 入口本身的 200–800ms 冷启动成本，也没提 Next.js 的 `optimizePackageImports` 这条首选修法 |
| 2（重渲染审查） | 「引用具体规则 ID」 | 同上，零 ID |
| 2 | 「把手动 memo 化建议置于 React Compiler 前置判断之下，并说明怎么检查」 | 基线只在末尾脚注了一句「若启用了 React Compiler 则这些 `useMemo` 都可移除」，既没有把它当作前置判断，也没说怎么检查（`package.json` 的 `babel-plugin-react-compiler` / `next.config.*` 的 `reactCompiler`） |
| 3（shadcn 改写） | 「先跑 `npx shadcn@latest info --json` 读真实项目上下文」 | 基线直接从 `components.json` 推断，虽然结论大多正确，但错过了 `resolvedPaths` / 已安装组件列表 / `packageManager` 等只有 CLI 才给的字段 |
| 3 | 「用 `npx shadcn@latest docs <component>` 取当前组件 API」 | 基线改为抓取网页文档。方向对，但没有走 CLI 这条抗腐化路径 |
| 3 | 「两选项按钮组换成 `ToggleGroup`」 | 基线**明确拒绝**了这一项，理由是「三套 registry 的受控 API 不兼容，本地无法校验签名」。这恰好是缺口所在：`base` vs `radix` 的 API 差异表 + 「跑 docs 取签名」的工作流，正是让这个改动变得安全的知识 |
| 3 | 「明确 `gap-*` 取代 `space-y-*` / `size-*` 取代 `w-N h-N` 这两条规则」 | 基线用 `Field orientation="horizontal"` 与 `size="icon"` 间接绕开了，没有把它们表述为项目级 class 约定，后续代码仍会写回 `space-y-*` |
| 4（负例，Vue） | —（无缺口，符合预期） | 基线把它当 Vue 3 组合式 API 审查，未套用任何 React/Next 规则，`skill_read == False`。负例的意义在于确认有 skill 时也不被误触发 |

## 评测结果

基线按流水线要求只在默认模型上跑（Phase B），有 skill 的两组分别用默认模型与 `@smol`。
结果目录：`/tmp/hs-evals/react/{default,smol}/{baseline,skill}/<n>/`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 App Router 审查 | 默认 | 无 | False | 5 / 7 | 缺「引用规则 ID」与「barrel 导入 + `optimizePackageImports`」 |
| 1 | 默认 | 有 | True | 7 / 7 | 输出格式完全照 `## Output format`；ID 覆盖 `rsc-boundary-at-leaves`、`rsc-no-async-client`、`async-parallel`、`bundle-barrel-imports`（recharts 与 lucide-react 各一条）、`bundle-dynamic-imports`、`rerender-no-inline-components`、`js-tosorted-immutable`；含 Verdict 与「主动丢弃」节 |
| 1 | `@smol` | 有 | True | 7 / 7 | 同上，并额外指出 `invoices` 只用 `.length` 应换 `count()`、recharts 图表缺系列子元素 |
| 2 重渲染审查 | 默认 | 无 | False | 5 / 7 | 缺「引用规则 ID」；React Compiler 只在末尾脚注一句，未作前置判断也未说怎么检查 |
| 2 | 默认 | 有 | True | 7 / 7 | 首轮 ID 选得不准（把 `useState` 非惰性初始化标成 `rerender-derived-state-no-effect`）；见下「Phase C 回修」。回修后精确引用 `rerender-lazy-state-init`、`rerender-simple-expression-in-memo`、`rerender-dependencies`、`rerender-use-deferred-value`，并显式复述 R11 的纠正 |
| 2 | `@smol` | 有 | True | 7 / 7 | 首轮同样把 `rerender-simple-expression-in-memo` 误标成 `rerender-no-inline-components`；回修后 ID 全部正确，且额外补上 `rerender-split-combined-hooks` 的拆分写法 |
| 3 shadcn 改写 | 默认 | 无 | False | 4 / 8 | 缺 `info --json`、缺 `docs <component>`、**明确拒绝**换 `ToggleGroup`、未把 `gap-*` / `size-*` 表述为约定 |
| 3 | 默认 | 有 | True | 8 / 8 | 先跑 `info --json` 与 `docs`（本环境 CLI 报 `Invalid configuration` 而失败，如实说明并改读官方 base 版文档）；换成 `FieldGroup`/`Field`/`FieldError`、`data-invalid` + `aria-invalid`、`ToggleGroup`（Base UI 的数组受控 API）、`InputGroup` + `InputGroupAddon`、tabler 图标、去掉 Card 颜色覆盖；主动追问用哪个 registry；还把 `bundle-barrel-imports` 推广到 `@tabler/icons-react` |
| 3 | `@smol` | 有 | True | 8 / 8 | 同上；`ToggleGroup` 的数组受控值明确注明「这条是从 docs 查到的，凭记忆会写错」，正是 rule 16 想要的行为 |
| 4 负例（Vue SFC） | 默认 | 无 | False | 3 / 3 | 按 Vue 3 审查，未套 React 规则 |
| 4 | 默认 | 有 | **False** | 3 / 3 | 事件流中零个 React 规则 ID；agent log 里明确写「文件是 Vue SFC，会话中挂载的 `react` skill 明确声明不适用于 Vue，因此未加载该 skill」 |
| 4 | `@smol` | 有 | **False** | 3 / 3 | 首句即「这是 Vue SFC 不是 React，所以 react skill 明确排除，没有加载它」 |

### Phase C 回修（评测驱动的一次修改）

首轮有 skill 的场景 2 暴露一个真实缺陷：两种模型都引用了规则 ID，但**挑的是 `Core rules` 里
最近似的那条**，而不是打开 `references/rules-rendering-rerender.md` 取准确 ID。原因是 SKILL.md
的 Core rules 每类只点名一条 ID，模型凭它就近代偿了。据此在 `review-performance` 的
`Gate — CITED AND ORDERED` 里加了一条硬要求：ID 必须取自实际读过的 reference 的 `Contents`，
找不到对应 ID 就用 `correctness`，并给出「非惰性 `useState` 应是 `rerender-lazy-state-init`」
这个具体反例。改完只重跑场景 2（`--only 2`，两种模型），两者 ID 全部精确，默认模型还在日志里
写下「读了 `references/rules-rendering-rerender.md` 取准确 rule id，而非从 Core rules 的 20 条里
挑最近似的（skill 明确禁止这种代偿）」——缺口确认被填补。

结论：**通过，两种模型都通过**。

- 场景 1：基线未达成的「引用规则 ID」与「barrel 导入」两条，在默认模型与 `@smol` 有 skill 时
  均达成。
- 场景 2：基线未达成的「引用规则 ID」与「React Compiler 前置判断」两条，两种模型有 skill 时均
  达成（ID 精确性经上述回修后成立）。
- 场景 3：基线未达成的四条（`info --json`、`docs`、`ToggleGroup`、`gap-*` / `size-*` 约定），
  两种模型有 skill 时均达成。
- 场景 4 负例：两种模型 `skill_read` 均为 `False`，且都显式说明「本 skill 声明不适用于 Vue」。

## 备注

### 偏离计划的决定

1. **上游目录名纠正**：任务书写 `skills/vercel-composition-patterns/`，实际目录是
   `skills/composition-patterns/`（`vercel-composition-patterns` 是它 frontmatter 的 `name`）。
   `SOURCES.yaml` 按真实路径记录，否则 `check_upstream.py` 的漂移检查会永远查不到文件。
2. **`nextjs-cache-components` 一个 id 覆盖四个上游 skill**：除计划里的 optimizer 与 adoption
   外，`paths` 还包含 `next-partial-prefetching-adoption` 与 `next-dev-loop`——因为
   `nextjs-cache-components.md` 的「优化之后」节引用了前者的判定，「按路线走一遍」节引用了后者
   的浏览器验证顺序。同仓库同分支合并成一个 id 比拆四个更利于同步。
3. **`references/` 恰好 12 个，与计划完全一致**，未做增删。`rules-*.md` 四份只留框架无关规则，
   Next 专属规则（`server-*`、`async-api-routes`、`server-after-nonblocking`）按 R1 全部下沉到
   `nextjs-data-and-caching.md`。
4. **纠正了一条上游规则的因果解释**（R11），而不是照抄。这是本次唯一「与上游明确不一致」的地方，
   `SOURCES.yaml` 的 `notes` 里也记了一份。
5. **新增一个上游未提供的小节**：`architecture-and-state.md` 的「Form state with Actions」，
   来源是 react.dev（R5）。含 `useFormStatus` 必须在 `<form>` 的子组件里调用这个高频坑。

### 评测夹具的已知瑕疵（下次同步时修）

`evals/files/components.json` 被 shadcn CLI 3.x/4.x 判为 `Invalid configuration`（`tailwind.config`
为空 + `style: nova` / `base: base` 的组合）。两种模型都如实报告了这个失败并改读官方文档，行为
正确、评测的区分度也不受影响（「先跑 CLI」这一条依然被观察到），因此本轮没有为此重跑评测。
下次同步这个 skill 时把夹具换成一份 CLI 能接受的配置，让 `info --json` 真正跑通。

另一处观察：默认模型在场景 2 与场景 4 把审查正文写进了 `.agent-logs/`，最终回答只留一句指路，
于是 `run_evals.py` 抽取的 `answer.md` 只有一行。这是会话侧 MCP 日志工具的行为，不是 skill 缺陷；
判定时读了 `events.jsonl` 与那份 agent log。若后续想让评测更好判，可在场景 `query` 里加一句
「把完整报告写在回答里」。

### 未来同步要盯的上游

- `vercel/next.js` 的 `skills/` 在 **canary** 分支上，随框架版本走，是本 skill 里变动最快的上游。
  Cache Components 的 API（`instant`、`cacheLife`、`exposeTestingApiInProductionBuild`）仍在演进，
  每次同步都要重核版本门。
- `shadcn-ui/ui` 的 `skills/shadcn` 几乎每天有推送，`rules/*.md` 的具体类名约定可能变；
  `shadcn-ui.md` 里那份 class 约定是本仓库唯一的 Tailwind 来源，漂移代价高。
- `vercel-labs/agent-skills` 仓库根仍无 LICENSE，只有 skill frontmatter 声明 MIT。若上游哪天补了
  一个不兼容的根许可，需要重新评估 `relation`。
- `openai/plugins` 无许可声明，按项目宽松策略合入。若上游补了限制性许可，该条要降级为
  `reference`，届时 `nextjs-app-router.md` / `nextjs-rendering.md` 需按 nextjs.org 重写。

### 放弃的方向

- `react-view-transitions`（候选 3）：质量够但属动效领域，留给后续 motion 主题，避免与
  `frontend-design` 对同一话题各说一套。
- 独立的 `tailwind` skill（候选 28）：官方无 skill，第三方均为会腐化的文档快照；Tailwind 约定
  由 `shadcn-ui.md` 承担。
- React 18 及更早的写法：只在 `composition-patterns.md` 与 `rules-js-advanced.md` 各留一处
  `<details>` 折叠块（`forwardRef` / handler-in-a-ref），主线一律只写当前做法。
