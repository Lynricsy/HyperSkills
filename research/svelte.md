# svelte 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"Svelte 5 SvelteKit agent skill SKILL.md github"`
  - `gh api search/repositories`：`"svelte in:name in:description skill"`、`"sveltekit skills agent"`、`"svelte-skills"`（各取 stars 前 20）
  - <https://www.skills.sh>（经 web_search 命中 `ejirocodes/agent-skills/svelte5-best-practices`）
  - 官方组织仓库：`sveltejs/`（`ai-tools`、`svelte`、`kit`、`cli`、`svelte-evals`、`svelte.dev`）
  - `github/awesome-copilot`（`skills/` 与 `instructions/` 都搜过，Svelte 相关仅 `instructions/svelte.instructions.md` 一份）
  - <https://svelte.dev/docs/ai/skills>（官方 skill 索引页，指向 `sveltejs/ai-tools`）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- `gh auth status`：`✓ Logged in to github.com account Lynricsy`，全程未限流。

### 版本事实（写正文前先核实，不凭记忆）

| 事实 | 核实方式 | 结论 |
|---|---|---|
| Svelte 当前稳定版 | `gh api repos/sveltejs/svelte/releases` | `svelte@5.57.0`（2026-08-28） |
| SvelteKit 当前稳定版 | `gh api repos/sveltejs/kit/releases` | `@sveltejs/kit@2.70.3`（2026-08-18）；`3.0.0-next.27`（2026-09-08）为预发布 |
| remote functions 稳定性 | `documentation/docs/20-core-concepts/60-remote-functions.md` @ `@sveltejs/kit@2.70.3` + 实读 <https://svelte.dev/docs/kit/remote-functions> | **仍是实验特性**。`Available since 2.27`，必须同时开 `kit.experimental.remoteFunctions` 与 `compilerOptions.experimental.async`；原文写明「likely to contain bugs and is subject to change without notice」 |
| `await` 表达式稳定性 | `sveltejs/ai-tools` 的 `references/await-expressions.md` + `documentation/docs/03-template-syntax/19-await-expressions.md` | 实验特性（5.36+），`experimental.async` 开关将在 Svelte 6 移除 |
| 官方 form actions 与 remote functions 的关系 | `30-form-actions.md` @ 2.70.3 首段 NOTE | 官方原话：form actions「feature-complete and will continue to work」，但「new development is focused on remote functions, which are intended to become the recommended way」 |
| `createContext` 可用版本 | `documentation/docs/06-runtime/02-context.md` | Svelte 5.40+ |
| `{@attach}` / 函数绑定 / clsx `class` / `<svelte:boundary>` / `$props.id()` | 各自文档的 “Available since” | 5.29 / 5.9 / 5.16 / 5.3 / 5.20 |
| `refreshAll` 是否可用于 v2 | 读 `packages/kit/src/runtime/app/navigation.js` 与 `client.js` @ tag `@sveltejs/kit@2.70.3` | 源码里**有** `refreshAll`，但「deprecate `invalidateAll`」这条 breaking 只在 `3.0.0-next.*` 的 CHANGELOG 里；v2 文档通篇用 `invalidateAll`。正文按 v2 写 `invalidateAll`，v3 差异表里写 `refreshAll` |
| `@sveltejs/mcp` CLI 真的能跑 | 本机实跑 `npx -y @sveltejs/mcp@latest list-sections` 与 `svelte-autofixer ./Bad.svelte` | 都退出 0；autofixer 对故意写坏的组件报出 `event_directive_deprecated` 与 `non_reactive_update` 两条（输出见「备注」） |

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | sveltejs/ai-tools `packages/opencode/skills/svelte-core-bestpractices` | https://github.com/sveltejs/ai-tools | 323 | 2026-09-09 | MIT | Svelte 5 写法口径 + 9 个 reference | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | Svelte 团队本体。176 行全是「该用什么、不该用什么」，含 legacy 替换清单；抽查 `$derived` 表达式 vs `$derived.by`、`createContext`、effect 不在服务端跑三条全对 |
| 2 | sveltejs/ai-tools `packages/opencode/skills/svelte-code-writer` | 同上 | 323 | 2026-09-09 | MIT | `@sveltejs/mcp` CLI 用法 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 官方给出的「取文档 + 校验」闭环。本机实跑通过，直接变成本 skill 每个 workflow 的验证门 |
| 3 | sveltejs/svelte `documentation/docs` | https://github.com/sveltejs/svelte | 88089 | 2026-09-10 | MIT | Svelte 语言与运行时全量文档 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 一切 Svelte 侧事实的裁决依据 |
| 4 | sveltejs/kit `documentation/docs` + `packages/kit/CHANGELOG.md` | https://github.com/sveltejs/kit | 20802 | 2026-09-10 | MIT | SvelteKit 全量文档 + 破坏性变更清单 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 同上；CHANGELOG 是 v3 差异表唯一可靠来源。**注意 main 已是 v3 预发布**，见裁决 1 |
| 5 | github/awesome-copilot `instructions/svelte.instructions.md` | https://github.com/github/awesome-copilot | 38862 | 2026-09-10 | MIT | Svelte 5 + SvelteKit 2 通用规范 | 3 | 3 | 2 | 3 | 2 | **13** | INCLUDE | GitHub 官方。首段就把 `await` 与 remote functions 标为需开关的实验特性，与官方一致；具体性扣分是因为大量条目是「keep components small」这类通用话 |
| 6 | sveltejs/cli `documentation/docs` | https://github.com/sveltejs/cli | 505 | 2026-09-05 | MIT | `sv create/add/check/migrate` | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | `sv migrate` 的任务化说明（prerequisite task、`@migration-task` 标记、一次一个 task 提交）是迁移 workflow 的骨架；`sv add vitest/playwright` 是测试节的入口 |
| 7 | spences10/svelte-claude-skills | https://github.com/spences10/svelte-claude-skills | 220 | 2026-09-09 | null | 6 个 Svelte/SvelteKit skill + 20 个 reference | 2 | 3 | 3 | 2 | 0 | **10** | INCLUDE（`license: NONE`） | 社区里最完整的失败案例库（optional chaining 断依赖、effect 自激死循环、runes 写在函数里、class 实例过不了序列化）。扣正确性分：两处与官方冲突，见裁决 2、3 |
| 8 | sveltejs/svelte-evals `assets/default-project` | https://github.com/sveltejs/svelte-evals | 15 | 2026-03-03 | MIT | 官方评测工程的测试装置 | 3 | 0 | 3 | 3 | 2 | **11** | INCLUDE（超期例外） | >6 个月未推送，按量表本应 REJECT；但它是 Svelte 团队自己的 harness，且其 `vite.config.ts` 与今天 `sv add vitest` 生成的快照一致（对照 `sveltejs/cli` 的 `create-with-all-addons` 快照），故按「官方且内容仍准确」例外保留 |
| 9 | ejirocodes/agent-skills `svelte/skills/svelte5-best-practices` | https://github.com/ejirocodes/agent-skills | 6 | 2026-06-25 | MIT | runes/snippets/events/TS/迁移/Kit/性能 7 个 reference | 1 | 2 | 2 | 2 | 2 | **9** | INCLUDE（补充） | 唯一把「`+page.js` 里读 `STRIPE_SECRET_KEY` 等于把密钥发给浏览器」写成安全问题而非风格问题的上游，这个框架被采纳。其余内容与 1/7 重叠 |
| 10 | fubits1/svelte-skills `plugins/svelte-5/skills/testing-svelte` | https://github.com/fubits1/svelte-skills | 10 | 2026-07-25 | MIT | `vitest-browser-svelte` + Playwright 测试纪律 | 1 | 2 | 3 | 3 | 2 | **11** | INCLUDE（仅测试节） | 「render-only 测试证明不了组件能用」「不要用 `if (items.length)` 跳过交互」「locator 严格模式下先收窄再 `.first()`」——这些是官方文档没写的实操纪律。其 `plugins/frontend/*`（CSS、pixel-perfect、web-design-guidelines）属 `frontend-design` 范围，未取 |
| 11 | full-stack-skills/svelte-skills | https://github.com/full-stack-skills/svelte-skills | 4 | 2026-08-06 | NOASSERTION → NONE | 16 个按官方文档章节切分的 skill | 0 | 3 | 1 | 2 | 0 | **6** | MAYBE → `relation: reference` | 实读 LICENSE：内容是 imageio/BSD 等第三方声明，**不是许可授予**；README 却挂 Apache-2.0 badge，仅 `skills/svelte-awesome/LICENSE.txt` 有真 Apache 全文。授予不明 → 按无许可处理。正文为中文、逐节复述 svelte.dev，机器生成特征明显，只用作「主题清单是否覆盖全」的对照 |
| 12 | spences10/skills（`svelte-runes`、`sveltekit-data-flow`、`sveltekit-structure`、`sveltekit-remote-functions` 等） | https://github.com/spences10/skills | 15 | 2026-07-19 | null | 与 #7 同名的 Svelte skill | 2 | 2 | 3 | 2 | 0 | 9 | REJECT | 同作者、同名 skill 的**较旧快照**（#7 的 `svelte-runes` 多出 `attachments.md`、`migration-gotchas.md`，`common-mistakes.md` 从 821 行重整为 593 行）。合入会把一个来源算两次。另：计划书里的种子路径 `skills/<name>` 有误，该仓库 skill 在仓库根目录 |
| 13 | spences10/svelte-skills-kit | https://github.com/spences10/svelte-skills-kit | 92 | 2026-04-29 | null | 同作者早期 Svelte skill 集 | 2 | 1 | 2 | 2 | 0 | 7 | REJECT | #7 的前身，>4 个月未推送，内容被 #7 取代 |
| 14 | claude-skills/sveltekit-svelte5-tailwind-skill | https://github.com/claude-skills/sveltekit-svelte5-tailwind-skill | 30 | 2025-10-28 | null | SvelteKit 2 + Svelte 5 + Tailwind v4 | 1 | 0 | 2 | ? | 0 | ≤5 | REJECT | 近 11 个月未推送（Svelte 5.16 的 clsx `class`、5.29 的 `{@attach}`、5.40 的 `createContext` 全在它之后），且一半篇幅是 Tailwind——属 `frontend-design` 范围 |
| 15 | splinesreticulating/claude-svelte5-skill | https://github.com/splinesreticulating/claude-svelte5-skill | 1 | 2025-11-25 | MIT | 单文件 Svelte 5 + SvelteKit skill | 0 | 0 | 2 | ? | 2 | ≤5 | REJECT | >9 个月未推送，1 star，单人仓库，无独有内容 |
| 16 | antstanley/shadcn-svelte-skill | https://github.com/antstanley/shadcn-svelte-skill | 6 | 2026-09-10 | MIT | shadcn-svelte 组件库用法 | 1 | 3 | 2 | ? | 2 | — | REJECT（越界） | 组件库与视觉约定，归 `frontend-design`；本 skill 明确不覆盖组件库内部 |
| 17 | jporre/sveltekit-verticalslices | https://github.com/jporre/sveltekit-verticalslices | 6 | 2026-09-07 | MIT | `b0`–`b10` 工作流 skill + agents | 1 | 3 | 2 | ? | 2 | — | REJECT（越界） | 内容是「从对话到 issue 到 worktree 到 ship」的流程编排，属 `planning`/`github` 范围，不含 Svelte 技术规则 |
| 18 | poolcamacho/sveltekit-{routing,testing,performance,authentication,architecture-review} | https://github.com/poolcamacho/sveltekit-testing | 0 | 2026-07-13 | MIT | 单主题 SvelteKit skill ×5 | 0 | 2 | 1 | ? | 2 | ≤5 | REJECT | 0 star、同日批量创建的单人仓库群，内容为教程式复述，无独有陷阱 |
| 19 | big-yellow-duck/sveltekit-project-skills | https://github.com/big-yellow-duck/sveltekit-project-skills | 0 | 2026-09-08 | null | SvelteKit 项目约定 | 0 | 3 | 1 | ? | 0 | ≤4 | REJECT | 0 star、个人项目约定，无许可，无权威性 |
| 20 | e-vicius/svelte-skills | https://github.com/e-vicius/svelte-skills | 0 | 2026-08-09 | MIT | Svelte skill 集 | 0 | 3 | 1 | ? | 2 | ≤5 | REJECT | 0 star，个人仓库，内容与官方文档重合且更少 |
| 21 | sveltejs/svelte.dev（站点仓库） | https://github.com/sveltejs/svelte.dev | 329 | 2026-09-10 | null | 文档站源码 + tutorial/blog | 3 | 3 | 1 | 3 | 0 | — | REJECT（作为仓库） | 站点仓库**无 LICENSE 文件**（API `license: null`）。文档正文并不住在这里，而是从 `sveltejs/svelte` / `kit` / `cli` 的 `documentation/docs` 同步过来的（那三个都是 MIT）。因此以 `kind: docs`（`svelte-dev-docs`，license MIT）收录**发布出来的文档内容**，站点自有内容（布局、blog、tutorial 文案）一概不用 |
| 22 | svelte.dev 发布文档（`kind: docs`） | https://svelte.dev/docs | — | 持续 | MIT（实查，见 #21） | 稳定版文档 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | **它决定本 skill 把哪个版本当「当前」**：站点服务的是 v2 稳定线（`svelte.config.js`、`$env/static/private`、`$lib`、`invalidateAll`），而 `sveltejs/kit@main` 已是 v3 预发布 |

## 深度审查

**1. sveltejs/ai-tools `svelte-core-bestpractices`（14 分，主干）**
176 行 SKILL.md + 9 个 reference（`attach` 170 行、`await-expressions` 187、`snippet` 400、`svelte-reactivity` 61、`each`/`render`/`bind`/`inspect`/`hydratable`）。frontmatter 只有 `name` + `description`，无 agent 专属字段，但 description 写着 "Load this skill whenever…"，属 agent 指令口吻，重写。结构上它是「按 rune 分节 + 结尾一份 legacy 替换清单」，没有 workflow、没有验证门、没有 review 输出契约——这三块是本 skill 自己加的。它与 #7 的重叠面很大，但方向相反：官方讲「该怎么写」，#7 讲「会怎么错」，正好互补。
唯一需要注意的：它把 `$effect` 的替代品列了四条（`{@attach}`、事件处理器、`$inspect`、`createSubscriber`），本 skill 全部保留，因为这四条正是基线答案里缺的判断依据。

**2. sveltejs/ai-tools `svelte-code-writer`（14 分）**
64 行，本身不含任何 Svelte 知识——它是 `@sveltejs/mcp` CLI 的说明书（`list-sections` / `get-documentation` / `svelte-autofixer`）。价值在于官方明确表态「不确定语法就去取文档，不要凭记忆」，并给了一个可执行的校验器。本机实跑确认三个子命令都在（输出见备注），于是把 `svelte-autofixer` + `sv check` 定为 implement / migrate 两个 workflow 的门。它还提醒 shell 里传 runes 要把 `$` 转义成 `\$`，这条写进 `## Environment`。

**3. sveltejs/kit `documentation/docs`（14 分，但有陷阱）**
`main` 分支的 CHANGELOG 头部是 `3.0.0-next.27`，文档里 adapter 写在 `vite.config.js`、私有环境变量是 `$app/env/private`、`$lib` 已变 `#lib`、server-only 目录规则也变了。而 <https://svelte.dev/docs/kit/adapters> 实读为 `svelte.config.js`、`$env/static/private`——站点服务的是 v2。所以**不能拿 main 的文档写正文**。本 skill 全部稳定事实改从 tag `@sveltejs/kit@2.70.3` 的 `documentation/docs` 取，main 只用来抽 v3 破坏性清单（`packages/kit/CHANGELOG.md` 里 `^- breaking` 共 70+ 条，筛出会破坏应用代码的 12 条做成表）。

**4. spences10/svelte-claude-skills（10 分）**
6 个 skill、20 个 reference。frontmatter 带 `metadata.last_updated` / `verified_against`（专属字段，剥离），正文末尾还有一段写给 LLM 的 "PROGRESSIVE DISCLOSURE GUIDELINES" 注释（剥离）。内容质量分两层：**runes 层很强**——`common-mistakes.md` 的 optional-chaining 断依赖、runes 写在普通函数里、`$effect` 自激死循环、把深响应式误当坏掉（实际该用 `$state.raw`）这四条，官方文档都只是隐含，它写成了可判定的反例。**SvelteKit 层有错**：`throw redirect()` 与「load 返回值必须 JSON-serializable」两条都与官方相反（裁决 2、3），`load-functions.md` 的示例里 `+page.svelte` 还写着 `export let data`（Svelte 4 语法出现在一个 Svelte 5 skill 里）。因此 runes 侧按其失败清单合入，SvelteKit 侧只取「决策矩阵」的结构，事实一律改从官方取。

**5. github/awesome-copilot `instructions/svelte.instructions.md`（13 分）**
178 行，`applyTo` glob 剥离。它的价值不在细节而在**定调**：开头就声明 targets Svelte 5.x + SvelteKit 2.x，并把 `await` 表达式与 remote functions 标注为「require opt-in config flags and may change before they stabilize」；这与官方一致，因此本 skill 的规则 24（「推荐实验特性必须点名开关」）拿它做第二来源。它还明确 "Prefer attachments (`{@attach}`, Svelte 5.29+) over actions (`use:`)"，与官方 legacy 清单一致，两方独立同意即写成硬规则（规则 11）。其余大量条目（"follow single responsibility"、"keep components small"）是通用软话，不取。

**6. sveltejs/svelte-evals（11 分，超期例外）**
不是 skill，是官方评测工程。`assets/default-project/vite.config.ts` 给出了当前官方测试装置的确切形状：一份 Vite 配置 + 两个 Vitest project（client 跑 `src/**/*.svelte.{test,spec}` 于 browser mode/Playwright provider，server 跑其余于 node，并 `exclude: ['src/lib/server/**']`），加 `expect: { requireAssertions: true }`。这套配置与 `sveltejs/cli` 今天生成的 `create-with-all-addons` 快照一致（同样是 `vitest-browser-svelte` + `page.getByRole` + `await expect.element`），所以「文件名即配置」这条规则站得住。

**7. fubits1/svelte-skills `testing-svelte`（11 分，仅测试节）**
frontmatter 有 `user-invocable`（剥离），正文引用了 `svelte-5:msw`、`svelte-5:storybook-vitest` 两个兄弟 skill（跨引用残留，删除；Storybook/MSW 出本 skill 范围）。留下的是官方文档不写的测试纪律，其中「用 `if (items.length > 0)` 守卫跳过交互 = 把坏夹具变成绿测试」这条附了真实事故（autocomplete 测试只验「有选中项」而没验选中的值，漏掉 onChange 返回对象而非字符串的 bug），值得原样保留语义。

**8. full-stack-skills/svelte-skills（6 分，reference）**
16 个 skill 精确对应 svelte.dev 的章节切分（`svelte-runes`/`svelte-template-syntax`/`svelte-styling`/`svelte-special-elements`/`svelte-lifecycle`/`svelte-legacy-apis`/`svelte-runtime`/`svelte-cli`/`svelte-ai`/`svelte-misc`/`svelte-reference`/`svelte-awesome` + `sveltekit-overview`/`sveltekit-data`/`sveltekit-config`/`sveltekit-advanced`），正文中文、逐条复述文档，与该组织的 `tauri-skills` 同构，机器生成特征明确。当作「章节清单」核对了一遍本 skill 的 topic router：`svelte-lifecycle`（`onMount`/`onDestroy`）与 `svelte-legacy-apis`（stores、slots）落在 `migration.md`，`svelte-special-elements` 落在 `components-and-templates.md`，`sveltekit-config` 落在 `sveltekit-hooks-and-deployment.md`，无遗漏。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | **该按 SvelteKit 2 还是 3 写** | `sveltejs/kit@main` 的文档：adapter 在 `vite.config.js`、`$app/env/private`、`#lib`、`refreshAll`。svelte.dev 与 tag `@sveltejs/kit@2.70.3` 的同名文档：`svelte.config.js`、`$env/static/private`、`$lib`、`invalidateAll` | **正文以 2.70.x 为准**；v3 单独做成 `migration.md` 末尾一张「预发布」差异表，并把「先读 `package.json` 判版本」写成规则 1 | 发布线是事实：`gh api repos/sveltejs/kit/releases` 里 v3 全部带 `-next.N`，v2.70.3 是最新正式版；实读 <https://svelte.dev/docs/kit/adapters> 与 `$env-static-private` 页确认站点服务 v2。拿 main 文档当现状会直接生成不能构建的配置 |
| 2 | `throw redirect()` / `throw error()` | spences10（#7、#12）：`sveltekit-data-flow` SKILL.md 的 Notes 写 "ALWAYS `throw redirect()/error()`"；`error-redirect-handling.md` 通篇 `throw` | **去掉 `throw`**：SvelteKit 2 里两个函数自己抛 | 官方迁移指南 `60-appendix/30-migrating-to-sveltekit-2.md` 首节标题即 "`redirect` and `error` are no longer thrown by you"，并说明 `svelte-migrate` 会自动改。社区上游把语义写反了（这已是连续几个波次出现的同类问题） |
| 3 | server `load` 返回值的序列化边界 | spences10 `load-functions.md`：「Return values must be JSON-serializable」「class instances aren't serializable」，修复方案是手摊成普通对象 | **改为 devalue**：JSON 能表达的 + `BigInt`/`Date`/`Map`/`Set`/`RegExp` + 重复/循环引用都能过；真正过不去的是 class 实例、函数、`Symbol`，且官方给了 `transport` hook 这条正路 | `20-core-concepts/20-load.md`（@2.70.3）第 209 行原文；`30-advanced/20-hooks.md` 的 `transport` 节给出 `src/hooks.js` + `encode`/`decode`。社区说法虽然「安全」，但会诱导把 `Date` 转成字符串再解析回来——基线答案 2 恰好只答对了一半（说了 devalue，但没给 `transport`） |
| 4 | `$:` 语句块该变 `$effect` 还是 `$derived` | spences10 `migration-gotchas.md` 翻译表：`$: { ... }` → `$effect(...)`；官方 `svelte-core-bestpractices`：「use `$derived` and `$effect` instead of `$:`，**but only use effects when there is no better solution**」；`sv migrate` 遇到判不准的会产出 `run()` from `svelte/legacy` | **赋值型的 `$:` 块一律 `$derived`**，只有真副作用才 `$effect`；把「审查每一个 `run()`」写进迁移 workflow 的门 | `02-runes/04-$effect.md` 的 "When not to use `$effect`" 节；`07-misc/07-v5-migration-guide.md` 的 `run` 小节说明 `run` 是「判不准」的兜底而非目标形态。基线答案 1 正是在这里把 `$: { liveTotal = ... }` 判对、却把 `$: if (query.length > 2) dispatch(...)` 塞进了 `$effect` |
| 5 | `use:action` 是否该迁移 | 官方 `svelte-core-bestpractices` legacy 清单：`use {@attach ...} instead of use:action`；awesome-copilot：`Prefer attachments over actions`；基线（无 skill）答案：「action 在 Svelte 5 未废弃，`{@attach}` 是可选替代，不属于移植必需项」 | **写成硬规则（规则 11）**：新代码与迁移中经手的 DOM/第三方集成都用 `{@attach}` | 两个独立权威来源（Svelte 团队 + GitHub）同向；`03-template-syntax/09-@attach.md` 给出理由——attachment 在 effect 里跑，读到的 state 变化会重跑，action 不会。基线的「非必需」判断在语法上没错，但把一个语义升级说成风格选择 |
| 6 | `$state.raw` 的定位 | spences10 `common-mistakes.md` 第 5 条把它列在「深响应式其实没坏」下面，作为性能优化选项；官方 `svelte-core-bestpractices` 把它写成 API 响应的**默认**选择 | **按官方**：只被整体替换的值（API 响应、轮询结果、大表）默认 `$state.raw` | `02-runes/02-$state.md` 的 `$state.raw` 节：「can improve performance with large arrays and objects that you weren't planning to mutate anyway」。两方其实不矛盾，但语气决定行为——基线答案 1 通篇没提 `$state.raw`，尽管夹具里 `rows` 每 5 秒被整体替换 |
| 7 | `invalidateAll()` 的使用尺度 | spences10 `client-auth-invalidation.md`：客户端登录后调 `invalidateAll()`；官方 `20-load.md`：优先 `depends()` + `invalidate(id)`，`invalidateAll` 重跑当前页所有 load | **两者都保留但分层**：默认 `depends`/`invalidate`，只有「作用域确实无法收窄」（登录改了 `event.locals`）才 `invalidateAll` | `20-load.md` 的 "Manual invalidation" 节；同文件明确 server load 不会自动依赖它 fetch 过的 URL（SvelteKit 2 移除了 `dangerZone.trackServerFetches`），所以 server load 必须显式 `depends`——这条基线答案完全没提 |
| 8 | 表单校验失败用 `fail` 还是 `error` | 夹具（与真实代码常见写法）用 `throw error(400, ...)`；官方 `30-form-actions.md`：`fail(status, data)` 回填 `form` prop，`error()` 渲染 `+error.svelte` | **`fail` 管无效输入，`error` 管页面无法提供** | `30-form-actions.md` "Validation errors" 节，含「回填用户已填值」的示例 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `svelte-ai-tools` | sveltejs/ai-tools（`svelte-core-bestpractices` + `svelte-code-writer`） | merged | Svelte 5 写法口径与 legacy 替换清单；`@sveltejs/mcp` 取文档 + `svelte-autofixer` 校验闭环（本 skill 各 workflow 的验证门） |
| `svelte-core` | sveltejs/svelte `documentation/docs` | merged | 所有 Svelte 侧事实：runes 语义与版本门槛、依赖追踪规则、snippet/attach/boundary/绑定、Vitest 与 `$effect.root`、v4→v5 迁移全表 |
| `sveltekit-core` | sveltejs/kit `documentation/docs`（v2 取自 tag 2.70.3）+ `packages/kit/CHANGELOG.md`（v3 差异） | merged | 所有 SvelteKit 侧事实：路由文件、load 分工、devalue 与 `transport`、失效与 `depends`、page options、form actions、hooks、adapter、v1→v2 与 v3 差异表 |
| `sv-cli` | sveltejs/cli `documentation/docs` + vitest 快照 | merged | `sv check`/`sv add`/`sv migrate` 的准确用法与迁移纪律 |
| `svelte-evals` | sveltejs/svelte-evals `assets/default-project` | merged | 官方测试装置的确切形状（client/server 双 project、browser mode、`vitest-browser-svelte`） |
| `spences10-svelte` | spences10/svelte-claude-skills | merged（`license: NONE`） | runes 层失败案例库；SvelteKit 层只取决策矩阵结构，事实按裁决 2、3 改写 |
| `ejirocodes-svelte5` | ejirocodes/agent-skills `svelte/skills/svelte5-best-practices` | merged | 「`+page.js` 里的密钥会进浏览器」的安全框架；callback props 替代 `createEventDispatcher` |
| `awesome-copilot` | github/awesome-copilot `instructions/svelte.instructions.md` | merged | Svelte 5 + Kit 2 定调；实验特性必须点名开关；attachments 优于 actions 的第二来源 |
| `fubits1-svelte` | fubits1/svelte-skills `plugins/svelte-5/skills/testing-svelte` | merged | 测试纪律：必须有交互与后果断言、断言前置条件而非跳过、locator 优先、在跨线边界打桩 |
| `svelte-dev-docs` | svelte.dev 发布文档 | merged（`kind: docs`，MIT 实查） | 决定「当前版本」是 v2；每条稳定事实与读者会去核对的页面一致 |
| `full-stack-skills-svelte` | full-stack-skills/svelte-skills | reference | 仅用其 16 个 skill 的章节切分核对 topic router 覆盖面；无许可授予且内容机器生成，未合入任何文字 |

## 基线缺口

无 skill（`uv run tools/run_evals.py svelte --baseline`，Claude Opus 5 / medium）时，各场景未达成的 `expected_behavior`。四个场景 `skill_read` 均为 `false`（正确，基线模式）。基线本身相当强——场景 1 真的编译了组件，场景 3 真的搭了一个临时 SvelteKit 工程跑通了六条断言——所以缺口全部是「知识」而非「执行力」。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 runes 迁移 | `$state.raw` 完全未提 | 夹具里 `rows` 每 5 秒被 API 整体替换，正是 `$state.raw` 的教科书场景；基线通篇当普通 `$state` 处理 |
| 1 | 未警告模块级 `$state` 在 SSR 下跨用户共享 | 基线把 `writable` 直接换成 `export const filters = $state({...})`，把 store 的老问题原样搬进 runes，且明确说「不使用 SSR 时可以」这层前提也没提；`createContext` 未出现 |
| 1 | `use:drawSparkline` → `{@attach}` 被明确拒绝 | 原话「action 在 Svelte 5 未废弃，`{@attach}` 是可选替代，不属于移植必需项」——与官方 legacy 清单相反（裁决 5） |
| 1 | keyed `{#each}` 被明确拒绝并给了错误理由 | 原话「rows 每 5 秒被整体替换，对象 identity 全变，加 key 会导致每 tick 全量销毁重建」；实际按 `row.id` 加 key 恰好避免销毁重建。基线自己在同一段里发现了 `row.id` 存在 |
| 1 | `$: if (query.length > 2) dispatch(...)` 被搬进 `$effect` | 官方指引是「响应用户交互的代码直接放事件处理器」；基线注明「副作用，不能用 `$derived`」，只考虑了两个选项 |
| 1 | 未提 `npx sv migrate svelte-5`、`svelte-autofixer`、`sv check` | 基线自己写脚本调 `compile()` 验证（有效但不可复用），官方三件套一个没提 |
| 2 数据流 | `export let data` → `$props()` 未提及 | 三个文件里唯一没被碰的 Svelte 5 违规；`+page.svelte` 交付时仍是 `export let data` |
| 2 | `$page`（`$app/stores`）→ `$app/state` 未提及 | 同上，deprecated 导入原样留下 |
| 2 | `transport` hook 未提及 | 只给了「在 universal load 里用纯数据重建 `Invoice`」一条路；官方的 `src/hooks.js` + `encode`/`decode` 未出现（裁决 3 的另一半） |
| 2 | server load 不追踪自身 fetch / `depends` 未提及 | 原话「`fetch('/api/exchange-rates')` + `invalidate()` 那对本来就是对的，没动」——恰好因为那对在 universal load 里才成立，基线没说明这个前提，也没提 `depends('app:…')` |
| 2 | `await parent()` 造成的瀑布未提及 | `+page.ts` 里 `await parent()` 排在独立的 `fetch` 之前，基线未识别 |
| 3 表单 | 「SvelteKit 2 里 `redirect`/`error` 自己抛」未说明 | 交付的代码里确实写成了 `redirect(303, ...)`（无 `throw`），但答复从未解释这是 v2 的规则，读者学不到；判为部分达成 |
| 3 | 组件未迁到 runes 模式 | 明确写「保留了原文件的 Svelte 4 风格 `export let`，没擅自迁移到 runes」；`form`/`data` 仍是 `export let` |

结论：三个正例共 **13** 条缺口（场景 1 六条、场景 2 五条、场景 3 两条），集中在两类——**（a）Svelte 5 runes 模式的路由侧写法**（`$props()`、`$app/state`）在基线里被系统性跳过；**（b）官方明确表态但社区口径相反的四条**（`{@attach}`、keyed each、`$state.raw`、`transport`）基线全部答成了社区版本。评测有区分度，进入 Phase C。

## 评测结果

模型均为 `claude-opus-5:medium`（`tools/run_evals.py` 默认，未传 `--model` / `--thinking`）。判定方式：人工通读 `/tmp/hs-evals/svelte/anthropic-claude-opus-5-medium/{baseline,skill}/<n>/answer.md` 及该目录里被改写的夹具文件。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Svelte 4→5 迁移 | claude-opus-5:medium | 无（baseline） | false | **5 / 11** — 达成 1、2、4、5、9 | 未达成 3（`$: if (query…) dispatch` 塞进 `$effect`）、6（`$state.raw` 完全未提）、7（模块级 `$state` 的 SSR 跨用户泄漏未警告，`createContext` 未出现）、8（明确拒绝 `{@attach}`，称「不属于移植必需项」）、10（明确拒绝 keyed each，理由是「对象 identity 全变」，恰好写反）、11（`sv migrate`/autofixer/`sv check` 全未提，自己写脚本调 `compile()`）。答复质量很高（真编译过），缺口全在知识面 |
| 1 | claude-opus-5:medium | 有 | **true** | **9 完全 + 2 部分 / 11** | 全部 6 条基线缺口填补：`rows` 由父组件用 `$state.raw` 声明并解释「prop 写入不创建代理」；store 改成 `Filters` 类 + `createContext()`，并原话警告 `export const filters = $state({…})` 在 SSR 下「一个服务进程一份值」是跨请求泄漏，还补上「非 Svelte 代码通过 `.subscribe()` 消费就保留 store」；`use:drawSparkline` 改 `{@attach fromAction(drawSparkline, () => ({ rows: visible }))}`（`fromAction` 是官方 `svelte/attachments` API，比直接重写 action 更保守）；`{#each visible as row (row.id)}` 且 `selected === row` 改为 `selected?.id === row.id`；搜索派发移入 `oninput` 处理函数并说明「用 `$effect` 翻译会在 `rows` 重算后重跑，丢掉『用户输入了』的语义」；开篇即说明 `sv migrate`/`sv check`/autofixer 为何在该目录跑不了。两处部分达成：未点名 `createEventDispatcher` 已弃用（只写「回调 props」），未给调用方 `{#snippet toolbar()}` 示例 |
| 2 SvelteKit 数据流 | claude-opus-5:medium | 无（baseline） | false | **5 / 10** — 达成 1、2、4、5、6 | 未达成 3 的后半（只给「在 universal load 重建 `Invoice`」，`transport` hook 未出现）、7（`export let data` 交付时仍在）、8（`$page` from `$app/stores` 原样留下）、9（原话「`fetch` + `invalidate()` 那对本来就是对的，没动」，未说明该结论只因它在 universal load 里成立，也未提 `depends`）、10（`await parent()` 排在独立 `fetch` 之前未识别） |
| 2 | claude-opus-5:medium | 有 | **true** | **10 / 10** | 四条基线缺口全部填补：`+page.svelte` 改 `let { data }: PageProps = $props()` 与 `import { page } from '$app/state'`；`+page.server.ts` 注释指出摊平的备选路径是「在 `src/hooks.ts` 的 transport 里注册 transporter」（`encode`/`decode` 两个函数名未点出，属细节缺失）；表格里直接写「server load 的 fetch **不追踪**，必须 `depends('app:x')`」并落地到代码，还额外发现原代码解构了 `depends` 却从未调用、导致刷新按钮是假的；`+page.ts` 注释「先发起请求再 `await parent()`，否则两者会被串行化」。devalue 一条比基线更进一步：明确「`Date` 和 `Map` 反而完全没问题，不需要你手动转」。并把 `auditToken` 判为最该先修的一项（凭据已进 SSR HTML）。自述用 `svelte-autofixer` 跑到 `issues: []`，首轮被它拦下一处 effect 内赋值 |
| 3 form actions | claude-opus-5:medium | 无（baseline） | false | **7 / 9 适用** — 达成 1、3、4、5、6、7、8 | 未达成 2（交付代码里确实写成了无 `throw` 的 `redirect(303, …)`，但答复从未说明这是 SvelteKit 2 的规则，读者学不到）、9（明确写「保留了原文件的 Svelte 4 风格 `export let`，没擅自迁移到 runes」）。第 10 条（remote functions 稳定性）不适用：未推荐 remote functions |
| 3 | claude-opus-5:medium | 有 | **true** | **9 / 9 适用** | 两条基线缺口填补：原话「SvelteKit 2 里 `error()`/`redirect()` 自己 throw，去掉多余的 `throw`；POST 后的重定向 302 → 303」；组件改 `let { data, form }: PageProps = $props()` 并说明「`export let data` / `on:submit` 是 legacy 语法，和 runes 不能混」。另外自己踩到并修掉一个本 skill 没写进 expected 的点：`$state(form?.email ?? data.lastEmail)` 只捕获初始值，autofixer 报 `state_referenced_locally`，改为 `$derived` + `update({ reset: false })`。第 10 条同样不适用 |
| 4 负例（Vue `reactive` 重赋值） | claude-opus-5:medium | 无（`skills: []`） | **false** | 3 / 3 | 按 Vue 3 回答：重新绑定 `state` 换掉了模板与 `computed` 追踪的 proxy，须改属性写入；顺带指出 `props.initial` 被直接塞进 `reactive` 会写穿父组件状态。零 Svelte 建议 |
| 4 | claude-opus-5:medium | 有（`skills: []`） | **false** | 3 / 3 | 同样未加载 svelte skill，且首句主动说明理由：「这是个 Vue SFC（不是 Svelte，svelte skill 明确排除 Vue，所以没加载它）」。全文唯一一次出现 "svelte" 就是这句；修复给的是 `state.filters = fresh` 与 `ref`/`shallowRef` 逃生口，无 runes 建议 |

结论：**通过**。基线未达成的 13 条行为里，有 skill 时 13 条全部达成（场景 1 六条、场景 2 五条、场景 3 两条），远超「至少一条」的通过标准；三个正例 `skill_read == true`，负例两次运行 `skill_read == false` 且答复未偏向 Svelte。填补的缺口集中在两类，与「基线缺口」节的诊断一致：**（a）路由侧的 runes 写法**（`$props()`、`$app/state`），基线系统性跳过；**（b）官方明确表态但社区口径相反的四条**（`{@attach}`、keyed each、`$state.raw`、`transport`），基线全部答成社区版本。此外「模块级 `$state` 在 SSR 下跨用户共享」这条——基线把 store 的老问题原样搬进 runes 且毫无警告——是本 skill 最有价值的单条规则。

## 备注

### remote functions 稳定性核实结论

计划书要求「先确认当前版本与 remote functions 的稳定性状态再写」。结论：**截至 2026-09-11 仍是实验特性**。三条独立证据：

1. `gh api repos/sveltejs/kit/releases` 里最新正式版是 `@sveltejs/kit@2.70.3`（2026-08-18），v3 全部带 `-next.N`。
2. tag `@sveltejs/kit@2.70.3` 的 `documentation/docs/20-core-concepts/60-remote-functions.md` 顶部写 `Available since 2.27`，紧接着「This feature is currently experimental, meaning it is likely to contain bugs and is subject to change without notice」，并要求在 `svelte.config.js` 里同时开 `kit.experimental.remoteFunctions` 与 `compilerOptions.experimental.async`。
3. 实读 <https://svelte.dev/docs/kit/remote-functions>，同样是 `Available since 2.27` + Experimental 标记。

配套事实：`compilerOptions.experimental.async`（Svelte 5.36+）本身也是实验开关，官方说该 flag 会在 Svelte 6 移除；开启它会改变整个应用的 effect 执行顺序（block effect 先于同组件的 `$effect.pre`），所以它不是「按路由决定」的选项。正文因此把 remote functions 写成「新项目可考虑、必须点名开关」，并保留 form actions 为默认路径——依据是官方 `30-form-actions.md` 首段 NOTE 的原话（form actions 已 feature-complete 且会继续可用，但新开发聚焦 remote functions）。

另外 v3 的 `vite.config.js` 写法与 v2 的 `svelte.config.js` 写法不同，正文只写 v2 形态，v3 形态在 `migration.md` 的差异表里。

### 无许可 / 许可异常上游的处理

| 上游 | API `license` | 实读结果 | 处理 |
|---|---|---|---|
| spences10/svelte-claude-skills | `null` | 仓库无 LICENSE 文件 | `license: NONE`，`relation: merged`，`notes` 写明 "No licence file; used under the repository's permissive-attribution policy, no text copied verbatim" |
| spences10/skills、spences10/svelte-skills-kit | `null` | 同上 | 未收录（内容被上一行取代） |
| full-stack-skills/svelte-skills | `NOASSERTION` | **实读 LICENSE**：内容是 `# Third-Party Notices` + imageio 2.37.0 的 BSD-2-Clause 等第三方声明，**没有对本仓库的许可授予**；README 挂 Apache-2.0 badge；仅 `skills/svelte-awesome/LICENSE.txt` 是真的 Apache-2.0 全文 | 授予不明 → 视同无许可：`license: NONE`，`relation: reference`，一字未取 |
| sveltejs/svelte.dev | `null` | 站点仓库无 LICENSE 文件 | 不作为 repo 上游。文档正文来自 `sveltejs/svelte` / `kit` / `cli` 的 `documentation/docs`（三者均 MIT），故以 `kind: docs`（`svelte-dev-docs`，license MIT）合入**文档内容**，站点自有内容（布局、blog、tutorial 文案）未使用 |
| big-yellow-duck/sveltekit-project-skills、claude-skills/sveltekit-svelte5-tailwind-skill 等 | `null` | — | 已 REJECT，不涉及许可处理 |

`kind: docs` 的许可按前两波教训实查而非填 `NOASSERTION`：三个文档源仓库的 `license.spdx_id` 逐个取过，均为 MIT。

### `@sveltejs/mcp` CLI 本机验证

`SKILL.md` 的验证门引用了官方 CLI，先在本机确认可用（工作目录 `/tmp`）：

```
$ npx -y @sveltejs/mcp@latest list-sections
List of available Svelte documentation sections with their intended use cases...
- title: sv migrate, use_cases: migration, upgrading svelte versions, ... path: cli/sv-migrate
（退出码 0）

$ cat autofix-test/Bad.svelte
<script>
  let count = 0;
  let doubled = 0;
  $effect(() => { doubled = count * 2; });
</script>

<button on:click={() => count++}>{doubled}</button>

$ npx -y @sveltejs/mcp@latest svelte-autofixer ./autofix-test/Bad.svelte
{
  issues: [
    'Using `on:click` to listen to the click event is deprecated. Use the event attribute `onclick` instead
     https://svelte.dev/e/event_directive_deprecated at line 7, column 8',
    '`doubled` is updated, but is not declared with `$state(...)`. Changing its value will not correctly trigger updates
     https://svelte.dev/e/non_reactive_update at line 3, column 6'
  ],
  suggestions: [],
  require_another_tool_call_after_fixing: true
}
（退出码 0）
```

两条诊断正是本 skill 规则 2 与规则 3 覆盖的错误，说明这个门确实能挡住机械迁移的产物。首次运行需要网络（`npx` 下载包），`## Environment` 里注明了无网络时应声明「无法确认 API」而不是凭记忆。

### 计划书种子的更正

- 计划书写的 `spences10/skills` 路径是 `skills/{svelte-runes,sveltekit-data-flow,sveltekit-structure,sveltekit-remote-functions}`；实际该仓库的 skill 在**仓库根目录**（`svelte-runes/SKILL.md` 等），没有 `skills/` 前缀。
- 更重要的是这四个 skill 在 `spences10/svelte-claude-skills`（220★，2026-09-09）里有更新的版本，路径为 `.claude/skills/<name>`。本 skill 收录后者，前者 REJECT（同源较旧快照）。
- `sveltejs/mcp` 已改名为 `sveltejs/ai-tools`（两个名字的 `full_name` 都返回 `sveltejs/ai-tools`）；CLI 包名仍是 `@sveltejs/mcp`。
- 计划书里 `sveltejs/ai-tools` 的种子写作 `svelte-code-writer`；实际该仓库有两个 skill，另一个 `svelte-core-bestpractices` 才是内容主干（`svelte-code-writer` 只是 CLI 说明书）。两个都收录。

### 未来同步时要盯的

1. **SvelteKit 3 正式发布**：会把 `migration.md` 末尾那张「预发布」表变成主线，同时 `sveltekit-routing-and-load.md` 的 `$env/*`、`$lib`、`invalidateAll` 与 `sveltekit-hooks-and-deployment.md` 的 `svelte.config.js` 全部要改。规则 1 的版本判定是为此准备的。
2. **remote functions 脱离实验**：`sveltekit-forms-and-mutations.md` 的「Choosing between actions and remote functions」一节需要重写默认选择。
3. **`experimental.async` 在 Svelte 6 移除 flag**：`runes-and-reactivity.md` 的「Async reactivity (experimental)」节届时并入主线。
4. `sveltejs/svelte-evals` 若继续不推送，且 `sv add vitest` 的生成物与它分叉，就该降为 reference（目前两者一致，见深度审查 6）。

### 放弃的方向

- **Tailwind / shadcn-svelte / 组件库**（`antstanley/shadcn-svelte-skill`、`claude-skills/sveltekit-svelte5-tailwind-skill`、`fubits1` 的 `plugins/frontend/*`）：归 `frontend-design`，本 skill 的 `## Scope` 明确排除。
- **Storybook / MSW**：`fubits1` 有专门 skill，但属测试工具选型而非 Svelte 语义，且会把测试节撑成工具目录。`references/testing.md` 只写官方 `sv add vitest` / `sv add playwright` 一条默认路径。
- **`svelte-package` / 组件库发布**：`spences10-svelte` 的 `svelte-deployment/references/library-authoring.md` 与 kit 的 `packaging` 文档都有，但受众是库作者而非应用开发者，本波不做。
- **流程编排类**（`jporre/sveltekit-verticalslices`）：属 `planning` / `github` 范围。
