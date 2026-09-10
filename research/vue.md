# vue 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"Vue 3 agent skill SKILL.md github"`、`"nuxt 4 claude agent skills SKILL.md github"`
  - <https://www.skills.sh>（经搜索结果命中 `secondsky/claude-skills/nuxt-production`）
  - claudemarketplaces.com / claudeskills.info / mcp.directory 的 `vue-best-practices` 条目（用于发现同名分发副本）
  - 领域官方组织仓库：`vuejs/`（core、docs、pinia、router、test-utils）、`nuxt/`、`vuejs-ai/`
  - `github/awesome-copilot`：`instructions/vue.instructions.md`、`skills/unit-test-vue-pinia`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 通过：账号 Lynricsy，scopes `gist, read:org, repo, workflow`）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | vuejs-ai/skills `skills/vue-best-practices` | <https://github.com/vuejs-ai/skills> | 2839 | 2026-05-30 | MIT | Vue 3 组件/响应式/SFC/性能，21 个 reference | 1 | 1 | 3 | 2 | 2 | 9 | INCLUDE（主干） | 规则密度最高的社区仓库；组件拆分触发条件、性能后置、模板派生外提都可直接落地。抽查发现「基本类型一律 `shallowRef`」与官方相反（裁决 1），故正确性扣 1 |
| 2 | vuejs-ai/skills `skills/vue-debug-guides` | 同上 | 2839 | 2026-05-30 | MIT | 130+ 个单点陷阱（响应式、生命周期、defineModel、watch、provide/inject） | 1 | 1 | 3 | 3 | 2 | 10 | INCLUDE | 本 skill 的「失败模式」清单主要来源：`define-expose-before-await`、`definemodel-object-mutation-no-emit`、`watch-deep-same-object-reference`、`reactive-destructuring`、`refs-in-collections-need-value` 等抽查三条全部与官方一致 |
| 3 | vuejs-ai/skills `skills/vue-pinia-best-practices` | 同上 | 2839 | 2026-05-30 | MIT | Pinia 6 条陷阱（setup store 必须返回全部 state、解构破坏响应式、`getActivePinia`） | 1 | 1 | 3 | 3 | 2 | 10 | INCLUDE | 与 pinia.vuejs.org 逐条一致，`pinia-setup-store-return-all-state` 甚至覆盖了「返回 readonly 也会破坏 SSR」这一官方脚注 |
| 4 | vuejs-ai/skills `skills/vue-router-best-practices` | 同上 | 2839 | 2026-05-30 | MIT | 8 条导航守卫/参数变化陷阱 | 1 | 1 | 3 | 3 | 2 | 10 | INCLUDE | `router-param-change-no-lifecycle`（同组件换 param 不触发生命周期）与 `router-navigation-guard-next-deprecated` 是本 skill Router 一节的骨架 |
| 5 | vuejs-ai/skills `skills/vue-testing-best-practices` | 同上 | 2839 | 2026-05-30 | MIT | 11 条 Vitest/VTU 陷阱（composable 测试包装、Suspense、Teleport、快照） | 1 | 1 | 3 | 3 | 2 | 10 | INCLUDE | 「只有快照测试等于没测」「composable 用生命周期钩子必须包一层组件」两条是评测里 baseline 最容易漏的 |
| 6 | onmax/nuxt-skills `skills/nuxt` | <https://github.com/onmax/nuxt-skills> | 708 | 2026-09-08 | 无（API `license: null`） | Nuxt 4 数据获取/状态/路由/服务端/配置 7 个 reference | 1 | 3 | 3 | 3 | 0 | 10 | INCLUDE | 唯一把「`useFetch` / `useAsyncData` / `$fetch` 选型」写成可判定规则并点明「同 key 必须同 handler/同结构选项」的社区上游；`license: NONE` 按仓库许可政策合入，不复制原文 |
| 7 | onmax/nuxt-skills `skills/vue` | 同上 | 708 | 2026-09-08 | 无 | Vue 3.5 组件/响应式/测试/TS，`gotchas.md` 自述基于 vuejs-ai | 1 | 3 | 2 | 3 | 0 | 9 | INCLUDE | `defineModel` 的 `required: true` 防双次 emit、`useTemplateRef`、`data-allow-mismatch`、`useId` 等 3.5 新面全在这里；与 #1 重叠部分以官方文档去重 |
| 8 | antfu/skills `skills/nuxt` | <https://github.com/antfu/skills> | 5871 | 2026-06-23 | MIT | Nuxt 19 个 reference，含 data-fetching / SSR 最佳实践 | 2 | 1 | 3 | 2 | 2 | 10 | INCLUDE | SSR 一节最完整：「Nuxt instance unavailable」、模块级 state 跨请求泄漏、`await` 之后 composable 失去上下文；`createUseFetch` 已对照官方核实存在。「避免自动生成的 key」说法不准确（裁决 4），正确性扣 1 |
| 9 | antfu/skills `skills/vue` | 同上 | 5871 | 2026-06-23 | MIT | `<script setup>` 宏、响应式、内置组件 3 个 reference（由 vuejs/docs 生成） | 2 | 1 | 2 | 2 | 2 | 9 | INCLUDE | `effectScope`、`flush` 时机、`toValue`/`MaybeRefOrGetter` 的 composable 入参约定取自此处。其 `Discourage using Reactive Props Destructure` 与官方相反（裁决 2） |
| 10 | antfu/skills `skills/pinia` | 同上 | 5871 | 2026-06-23 | MIT | Pinia 9 个 reference（SSR、HMR、组件外使用、测试） | 2 | 1 | 3 | 3 | 2 | 11 | REJECT（范围收窄） | 内容合格，但 `antfu/skills` 已是本仓库 `frontend-design` 的上游，按波次约定 `paths` 只收 `skills/vue`、`skills/nuxt` 两个目录；Pinia 事实改由 #3 + pinia.vuejs.org 提供，覆盖面无损 |
| 11 | github/awesome-copilot `instructions/vue.instructions.md` | <https://github.com/github/awesome-copilot> | 38862 | 2026-09-10 | MIT | Vue 3 全景清单（响应式、宏、Pinia、Router、TS、测试、性能、SSR） | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | GitHub 官方维护，用作「覆盖面清单」核对本 skill 是否漏项；`ref()` 用于基本类型、`storeToRefs`、`InjectionKey`、`v-memo` 的表述与官方一致。教程式段落多，故具体性 2 |
| 12 | github/awesome-copilot `skills/unit-test-vue-pinia` | 同上 | 38862 | 2026-09-10 | MIT | Vue+Pinia 单测：`createTestingPinia` 各档位、VTU 断言纪律 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 全库唯一把「`createSpy: vi.fn` / `stubActions` / `initialState` / `setActivePinia(createPinia())` 各自何时用」写清的上游，直接构成测试 reference 的决策表 |
| 13 | awesome-skills/code-review-skill `reference/vue.md` | <https://github.com/awesome-skills/code-review-skill> | 1926 | 2026-09-08 | MIT | Vue 3 评审清单（响应式、props/emits、3.5 新特性、性能） | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE | 评审视角的组织方式（按主题给 ❌/✅ 对照）被用来定 `## Output format`；`shallowRef` + `triggerRef` 的用法与官方一致。正文为中文，仅取语义，不搬文字 |
| 14 | vuejs/docs（vuejs.org） | <https://vuejs.org/> | 3236 | 2026-09-07 | CC-BY-4.0（API 报 NOASSERTION，实读 LICENSE 为 CC BY 4.0） | Vue 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: docs`） | 所有版本敏感事实的裁决依据：Reactive Props Destructure（3.5+）与「传入函数须用 getter」、`shallowRef` 的真实定位、`data-allow-mismatch`、`useId`、`v-memo` |
| 15 | nuxt/nuxt `docs/`（nuxt.com） | <https://nuxt.com/docs> | 60836 | 2026-09-10 | MIT | Nuxt 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: docs`） | `useFetch` key 含调用位置、同 key 选项一致性清单、`deep` 默认 false、`createUseFetch` 宏约束、hydration 最佳实践都取自这里 |
| 16 | vuejs/pinia `packages/docs`（pinia.vuejs.org） | <https://pinia.vuejs.org/> | 14718 | 2026-09-06 | MIT | Pinia 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: docs`） | setup store 必须返回全部 state（含 readonly 会破坏 SSR）、`storeToRefs`、组件外使用、Pinia 4 的 `@vue/devtools-api` peer 依赖 |
| 17 | vuejs/router `packages/docs`（router.vuejs.org） | <https://router.vuejs.org/> | 4675 | 2026-09-07 | MIT | Vue Router 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: docs`） | Router 5 = v4 + unplugin-vue-router 合并（无破坏性变更）、typed routes、`RouteRecordInfo`/`TypesConfig`、守卫返回值语义 |
| 18 | vuejs/test-utils（test-utils.vuejs.org） | <https://test-utils.vuejs.org/> | 1158 | 2026-09-10 | MIT | Vue Test Utils 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（`kind: docs`） | `global.plugins` 挂载选项、`emitted()`、`findComponent`、`flushPromises` 的准确签名 |
| 19 | vinayakkulkarni/vue-nuxt-best-practices | <https://github.com/vinayakkulkarni/vue-nuxt-best-practices> | 40 | 2026-08-07 | MIT | Vue/Nuxt/SEO/GEO 四个 skill，规则拆成单文件 | 1 | 2 | 2 | 2 | 2 | 9 | MAYBE（仅校验） | Vue 规则集是 #1 的子集（`reactivity-*`、`template-*`、`component-v-memo`），未提供新事实；SEO/GEO 与 Cloudflare 部分超出本 skill 边界。仅用于确认 #1 的规则清单没有遗漏，不进 `paths` |
| 20 | secondsky/claude-skills（nuxt-content / bun-nuxt 等） | <https://github.com/secondsky/claude-skills> | 217 | 2026-09-09 | MIT | 插件式集合，Nuxt 相关目录全部围绕 Nuxt Content / Bun / Cloudflare / maz-ui | 1 | 3 | 2 | 2 | 2 | 10 | REJECT | 活跃且许可干净，但没有通用 Nuxt/Vue skill：命中的都是模块与平台包装（`nuxt-content`、`bun-nuxt`、`cloudflare-workers-frameworks`），属于第三方模块说明书，超出本 skill 边界 |
| 21 | Patrity/nuxt-skills | <https://github.com/Patrity/nuxt-skills> | 14 | 2026-05-28 | GPL-3.0 | 抓取 Nuxt / Nuxt UI 文档的脚本型 skill | 1 | 1 | 1 | 2 | 2 | 7 | REJECT | GPL-3.0 按仓库政策不得 merged；内容本身是「运行脚本去拉官方文档」，事实密度低，作为 reference 也无价值（官方文档已直接作为 `kind: docs` 上游） |
| 22 | uni-helper/skills `vue-best-practices` | <https://github.com/uni-helper/skills> | 103 | 2026-03-01 | MIT | uni-app 生态下的 Vue 规则副本 | 1 | 0 | 2 | 2 | 2 | 7 | REJECT | 最近推送 2026-03-01，已超 6 个月（新鲜度 0）；且内容是 #1 的再分发，另有 uni-app 小程序语境，与本 skill 边界冲突 |
| 23 | alexanderop/claude-skill-vue-development | <https://github.com/alexanderop/claude-skill-vue-development> | 30 | 2025-11-08 | 无（API `license: null`） | 单个 Vue 开发 skill | 0 | 0 | 1 | 1 | 0 | 2 | REJECT | 近 10 个月未推送，写作停留在 Vue 3.4 之前（无 `defineModel` 之后的面），无许可文件 |
| 24 | hyf0/vue-skills | <https://github.com/hyf0/vue-skills> | 2839 | 2026-05-30 | MIT | — | — | — | — | — | — | — | REJECT（重复） | `gh api repos/hyf0/vue-skills --jq .full_name` 返回 `vuejs-ai/skills`：这是同一仓库的旧路径重定向，与 #1–#5 完全重复。多个 skill 目录站（claudemarketplaces、mcp.directory）把它列成独立条目，实际不是 |

## 深度审查

### vuejs-ai/skills（#1–#5，主干）

一个仓库拆成 7 个 skill：`vue-best-practices`（工作流 + 21 reference）、`vue-debug-guides`（130+ 个单点陷阱，每个一文件）、`vue-pinia-best-practices`、`vue-router-best-practices`、`vue-testing-best-practices`、`vue-options-api-best-practices`、`vue-jsx-best-practices`。

- **结构**：`vue-best-practices/SKILL.md` 是编号工作流（确认架构 → 基础 → 可选特性 → 性能 → 自查），reference 用 `impact: HIGH/MEDIUM` frontmatter 排序。`vue-debug-guides` 是纯索引 + 一文件一陷阱，颗粒度最适合改写成 `## Core rules`。
- **frontmatter**：`description` 用 `MUST be used for…` / `ALWAYS use…` 命令式，`metadata.version: "18.0.0"` 不是日期版本，`author: github.com/vuejs-ai`——全部需按标准第 1 节剥离重写。子 skill 还把 `version`/`license`/`author` 平铺在顶层（非白名单形状）。
- **质量**：陷阱条目普遍带「现象 → 原因 → 修法 → 官方链接」，可用性高。少数条目是模型早已知道的常识（`ref-value-access`、`v-else-must-follow-v-if`），按「不重复模型已知常识」丢弃。
- **agent 绑定**：`.claude-plugin/marketplace.json`、`CLAUDE.md` 与 `Use vue skill` 触发前缀是 Claude Code 专属，不合入。
- **重叠**：`vue-options-api-best-practices` 与 `vue-jsx-best-practices` 整体不取——本 skill 只写 Composition API + `<script setup>` 一种默认做法（标准第 3 节「只给一个默认方案」）；Options API 只在「迁移到 Composition API」语境下被提及。

### onmax/nuxt-skills（#6、#7）

- **结构**：`skills/nuxt/SKILL.md` 只 56 行 + 7 个 reference，「Reference map」和「Ownership boundaries」两节写得很干净，明确把模块（Nuxt UI、Content、SEO）踢给各自 skill——这个边界写法与本仓库标准同构，直接借用其思路给本 skill 的 `## Scope`。
- **质量**：`nuxt-composables.md` 是全部候选里唯一把「同一个 key 的 `useAsyncData` 必须共享一致的 handler/`deep`/`transform`/`pick`/`getCachedData`/`default`，但 `server`/`lazy`/`immediate`/`dedupe`/`watch` 可以不同」写出来的——与 nuxt.com 完全一致。
- **agent 绑定**：`skills/vue/SKILL.md` 的「Loading Files」复选框列表和 `nuxt-ui`/`reka-ui`/`vueuse` 交叉引用是该仓库自有 skill 名，必须剥离（本仓库没有这些 skill）。
- **许可**：仓库无 LICENSE 文件（`gh api ... license` 无 SPDX），按许可规则表以 `license: NONE` + notes 合入，只取事实不搬文字。
- **重叠**：`skills/vue/references/gotchas.md` 自述「Based on vuejs-ai/skills」，与 #1/#2 重叠；重叠处一律回到官方文档核对后再写。

### antfu/skills（#8、#9）

- **结构**：每个 skill 带 `GENERATION.md`，说明 reference 是从官方文档仓库生成的。因此它的事实等价于官方文档的一个快照，价值集中在「把官方文档重排成决策表」这件事上（如数据获取选型表、SSR 错误信息对照表）。
- **frontmatter**：`metadata.source`、`metadata.author: Anthony Fu` 需剥离。
- **agent 绑定**：`instructions/*.md` 是 Copilot instruction 形态，`skills/antfu-design` 已由本仓库 `frontend-design` 使用。
- **`paths` 收窄理由**：本波约定「antfu/skills 已是 `frontend-design` 上游，`paths` 只列 vue / nuxt」。实测收窄不掉覆盖面——被排除的 `skills/pinia` 全部内容都能在 #3（Pinia 陷阱）与 pinia.vuejs.org（`kind: docs`，MIT）之间取到，且后者权威更高。`skills/vue-best-practices`、`skills/vue-router-best-practices`、`skills/vue-testing-best-practices`、`skills/vueuse-functions` 在 antfu 仓库里是从 vuejs-ai 同步的副本（带 `SYNC.md` 与独立 `LICENSE.md`），收在 #1–#5 名下更准确，因此也不列入。

### github/awesome-copilot（#11、#12）

- `instructions/vue.instructions.md` 的 `applyTo` 是 Copilot 专属 glob，剥离。正文是「全景清单」而非陷阱集，正好用来做覆盖面自查：逐节比对后本 skill 补上了 `<style scoped>` 的 `:deep()`/`v-bind()`、`customRef`、`defineSlots`/`defineOptions`、`effectScope` 这几处原本会漏的面。
- `skills/unit-test-vue-pinia` 是测试 reference 的主干：`createTestingPinia({ createSpy: vi.fn })` 作为组件测试默认、`stubActions: false` 只在需要跑真实 action 时打开、纯 store 测试用 `setActivePinia(createPinia())`、`wrapper.vm` 视为例外——四档区分是别处没有的。

### awesome-skills/code-review-skill（#13）

只有 `reference/vue.md` 一个文件与本 skill 相关，中文写作。取其组织方式（按主题给 ❌/✅ 对照 + Review Checklist）与 `shallowRef` + `triggerRef` 的配对用法；文字一律重写为英文。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 基本类型该用 `ref` 还是 `shallowRef` | vuejs-ai `reactivity.md`：「Always use `shallowRef()` instead of `ref()` for primitive values」，antfu `vue/SKILL.md`：「For performance, prefer `shallowRef` over `ref`」；awesome-copilot 与 code-review-skill：基本类型用 `ref`，`shallowRef` 留给大对象 | **`ref()` 为默认**，`shallowRef` 只用于大型/不可变结构与外部实例（Chart、SDK client、`markRaw` 场景） | 官方 `api/reactivity-advanced.md`：`shallowRef` 「is typically used for performance optimizations of large data structures, or integration with external state management systems」；`guide/best-practices/performance.md` 明确深响应式开销「should only affect very specific use cases」（单渲染访问 10 万+ 属性）。基本类型不存在深代理，`shallowRef` 对它没有收益，只会在后续换成对象时埋一个「改嵌套属性不更新」的坑 |
| 2 | Reactive Props Destructure 该不该用 | antfu `vue/SKILL.md`：「Discourage using Reactive Props Destructure」；vuejs-ai `prop-defineprops-scope-limitation`：只说作用域限制；onmax `components.md`：3.5+ 推荐解构并用原生默认值 | **3.5+ 可以解构 `defineProps()` 的返回值**，并作为类型化 props 声明默认值的首选写法；同时必须写死两条边界：①编译器只转换「同一个 `<script setup>` 块里直接解构宏调用」的情形，`const props = defineProps(); const { x } = props` 不被转换；②把解构出的 prop 传给 `watch` 或外部函数时要包 getter（`watch(() => x, …)`、`useComposable(() => x)`）或让被调方 `toValue` | 官方 `guide/components/props.md#reactive-props-destructure`（3.5+ 徽章）与 `api/sfc-script-setup.md`：编译器自动前置 `props.`；`#passing-destructured-props-into-functions` 明确 `watch(x, …)` 会被编译器警告，正解是 `watch(() => x, …)`。官方文档新于 antfu 的 2026-01 生成快照，且「官方厂商 > 公认专家」 |
| 3 | Pinia setup store 能不能有私有 state | vuejs-ai `pinia-setup-store-return-all-state`：必须全部返回，可用 `_` 前缀表意；部分社区写法用闭包做私有 state | **必须返回全部 state ref；`readonly()` 包一层也不行** | 官方 `core-concepts/index.md`：「you **must** return **all state properties** … Not returning all state properties or **making them readonly** will break SSR, devtools, and other plugins」。上游只说了「不返回」，官方多出「readonly 也算」，正文按官方写（评测场景 2 专门覆盖这一条） |
| 4 | `useAsyncData` 的自动 key 是否该避免 | antfu `best-practices-data-fetching.md`：「❌ Avoid: Auto-generated Keys（Key is auto-generated from file/line - can cause issues）」；onmax：只要求「可复用的包装器必须给显式 key」 | **自动 key 本身没问题**，它由调用位置生成，所以「同一 URL 在两个组件里调用 = 两个 key = 两次请求」；需要共享数据时给同一个显式 `key`，写在可复用 composable 里时必须给显式 key（否则每个调用点各一份缓存） | 官方 `getting-started/data-fetching.md#keys`：`useFetch` 由 URL + options + 调用位置生成 key，「two `useFetch` calls with the same URL in different components have **different** keys」。antfu 的表述把「行为」说成「缺陷」，会让模型给出无意义的「到处加 key」建议；onmax 的表述与官方一致，采用 onmax |
| 5 | Nuxt 里 `data` 是深响应还是浅响应 | 三个社区上游都没提；antfu/onmax 的示例都直接 `data.value` 整体替换（隐含正确但未说明原因） | **`deep` 默认 `false`，`data` 是 shallowRef**：改 `data.value.x` 不触发渲染，必须整体替换、显式 `deep: true` 或 `refresh()` | 官方 `api/composables/use-async-data.md` 选项表：`deep` 默认 `false`，「Return data in a deep ref object. Defaults to `false` for improved performance (shallow ref object)」。这是社区上游集体缺失的一条，评测场景 3 用它做区分度 |
| 6 | Vue 当前 GA 与 Nuxt 当前 GA | 上游分别写「Based on Vue 3.5」（antfu）、「Current stable: Vue 3.5+」（onmax）、未标注（vuejs-ai） | 正文写死 **Vue 3.5**（`(3.5+)` 标注版本敏感规则）与 **Nuxt 4**；Vue 3.6 处于 RC，不进正文 | `gh api repos/vuejs/core/releases`：最新非预发布为 `v3.5.42`（2026-08-27），`v3.6.0-rc.7`（2026-09-04）仍是 prerelease。`gh api repos/nuxt/nuxt/releases`：`v4.5.2`（2026-08-05）为最新非预发布，3.21.x 仍在维护。配套：`gh api repos/vuejs/router/releases` → `v5.3.1`；`gh api repos/vuejs/pinia/releases` → `v4.0.3` |
| 7 | Vue Router 4 → 5 是否有破坏性变更 | 上游全部按 v4 写，未提 v5 | **v4 用户升级 v5 无破坏性变更**（除 iife 构建不再内联 `@vue/devtools-api`）；v5 的实质变化是把 unplugin-vue-router 的文件路由与 typed routes 并入核心 | `router/packages/docs/guide/migration/v4-to-v5.md`：「Vue Router 5 is a _boring_ release, it merges unplugin-vue-router into the core package with no breaking changes」。正文只写「Router 5 起文件路由与类型化路由内置，`unplugin-vue-router` 的导入路径改为 `vue-router/vite`」 |
| 8 | Pinia 4 是否需要额外依赖 | 上游全部按 Pinia 2/3 写安装命令 | 安装 Pinia 必须同时装 `@vue/devtools-api`（v4 起为必需 peer 依赖），且 v4 仅 ESM | `pinia/packages/docs/getting-started.md`：「Since v4, you must also install `@vue/devtools-api`, which is a required peer dependency」；`v4.0.0` release notes：「ESM only and upgrading `@vue/devtools-api`」 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `vuejs-ai-skills` | vuejs-ai/skills（`vue-best-practices`、`vue-debug-guides`、`vue-pinia-best-practices`、`vue-router-best-practices`、`vue-testing-best-practices`） | merged | 主干失败模式清单：响应式丢失的各条路径、`defineModel` 对象变更不 emit、`defineExpose` 必须在 `await` 前、深 watch 新旧同引用、生命周期/`provide` 必须同步注册、setup store 必须返回全部 state、同组件换 param 不触发生命周期、守卫返回值取代 `next()`、composable 测试需包装组件、只有快照等于没测；以及「性能是功能完成后的独立一遍」这个工作流顺序 |
| `onmax-nuxt-skills` | onmax/nuxt-skills（`skills/nuxt`、`skills/vue`） | merged | Nuxt 数据原语选型（`useFetch` / `useAsyncData` / `$fetch`）与同 key 选项一致性、`useState` 的请求隔离语义、`useRequestFetch` 与 header 转发边界、`callOnce` 用于跨 SSR/导航的副作用；Vue 3.5 面：`defineModel({ required: true })` 防双次 emit、`useTemplateRef`、`useId`、`data-allow-mismatch`、`Teleport defer`；以及「按所有权划边界」的 Scope 写法 |
| `antfu-skills` | antfu/skills（`skills/vue`、`skills/nuxt`） | merged | SSR/上下文类失败的完整对照：「Nuxt instance unavailable」的四种合法上下文、模块级 `ref` 在服务端跨请求泄漏、`await` 之后 Nuxt composable 失去上下文、浏览器库必须动态导入；Vue 侧的 `effectScope`、`flush` 时机、`toValue`/`MaybeRefOrGetter` 入参约定与「composable 返回 refs 而非 reactive」 |
| `awesome-copilot` | github/awesome-copilot（`instructions/vue.instructions.md`、`skills/unit-test-vue-pinia`） | merged | 覆盖面清单（据此补齐 `defineSlots`/`defineOptions`、`customRef`、`<style scoped>` 的 `:deep()` 与 `v-bind()`）；测试决策表：`createTestingPinia` 的 `createSpy`/`stubActions`/`initialState` 各档何时用、纯 store 测试用 `setActivePinia(createPinia())`、`wrapper.vm` 作为例外而非默认 |
| `awesome-skills-code-review` | awesome-skills/code-review-skill（`reference/vue.md`） | merged | 评审视角的主题分组与 `shallowRef` + `triggerRef` 的配对用法；`## Output format` 的按主题分组 + 检查清单形状 |
| `vue-docs` | vuejs.org（源在 vuejs/docs，CC-BY-4.0） | merged | 所有版本敏感事实的裁决依据：Reactive Props Destructure 的转换范围与「传函数须包 getter」、`shallowRef` 的真实定位、深响应式开销的真实量级、`data-allow-mismatch`、`useId`、`v-memo`、hydration mismatch 成因 |
| `nuxt-docs` | nuxt.com（源在 nuxt/nuxt `docs/`，MIT） | merged | `useFetch` key 含调用位置、同 key 选项一致/可变清单、`deep` 默认 false、`createUseFetch` 的宏约束与保留函数名、`await` 与 `lazy` 的独立语义、hydration 最佳实践、server components 的 `componentIslands: 'auto'` |
| `pinia-docs` | pinia.vuejs.org（源在 vuejs/pinia，MIT） | merged | setup store 必须返回全部 state 且不得 readonly、`storeToRefs` 的准确语义（action 可直接解构）、组件外使用必须延迟到 pinia 安装之后、`$patch`/`$reset`/`$subscribe`、Pinia 4 的 ESM-only 与 `@vue/devtools-api` peer 依赖 |
| `router-docs` | router.vuejs.org（源在 vuejs/router，MIT） | merged | 守卫返回值语义、参数变化的响应方式、typed routes 的 `RouteRecordInfo` + `TypesConfig` 形状、Router 5 合并 unplugin-vue-router 且对 v4 用户无破坏性变更 |
| `vue-test-utils-docs` | test-utils.vuejs.org（源在 vuejs/test-utils，MIT） | merged | `global.plugins` 挂载选项形状、`emitted()`/`findComponent`/`flushPromises` 的准确用法、`shallow` 的取舍 |

未进 `paths` 的候选：#10（antfu `skills/pinia`，范围收窄）、#19（vinayakkulkarni，仅覆盖面校验）、#20（secondsky，模块包装）、#21（Patrity，GPL-3.0）、#22（uni-helper，>6 月且为再分发）、#23（alexanderop，停更无许可）、#24（hyf0，重定向重复）。

## 基线缺口

无 skill（`uv run tools/run_evals.py vue --baseline`，模型 `claude-opus-5:medium`，四场景 `skill_read=False`）
时，各场景未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 响应式丢失 | 第 7 条：用 watcher 清理回调 + `AbortController` 取消过期请求 | 基线识别出了竞态，但**主动拒绝** `AbortController`，改用手写 `latestRequest` token 计数器，并写了一段理由（「语义需求只是丢弃过期响应」）。手写 token 不取消在途连接，也不覆盖组件卸载后的写入；官方给出的做法是 `onWatcherCleanup(() => controller.abort())`。其余 8 条（props 二次解构、`watch` 源、`reactive` 重赋值、缺 `.value`、computed 副作用、改 prop、`v-if`+`v-for`、模板派生下沉）全部达成 |
| 2 Pinia + 测试 | 第 4 条（`createTestingPinia` 作为 mount 插件 + 纯 store 测试用 `setActivePinia(createPinia())`）、第 6 条（`createTestingPinia` 默认 stub actions，需要真实执行才传 `stubActions: false`） | 基线正确诊断出「没有 `createPinia`/`setActivePinia`」并重写了 9 个用例，但全程**从未提到 `createTestingPinia`**，因而也没有 stub/spy 的档位选择；它靠 mock `fetch` 绕过 `onMounted` 的真实网络，而不是用 action stub。第 1、2、3、5 条（返回全部 state、`readonly` 同样破坏、`storeToRefs`、删掉快照与 `wrapper.vm` 断言）达成 |
| 3 Nuxt 水合与去重 | 第 7 条：用返回的 `status`/`error` 渲染加载与错误态 | 基线三个症状全部命中，包括最不直观的「`data` 默认 `deep: false`」（还跑了实测）与私有 `runtimeConfig` 的密钥泄漏警告，但改写后的组件仍然直接用 `data`，没有引入 `status`/`error` 分支。第 1–6 条达成 |
| 4 负例（Next.js RSC） | 无（负例本身即达成） | `skill_read=False`，按 RSC 请求瀑布流作答（`Promise.all` + 先发起后 await），无任何 Vue/Nuxt/Pinia 内容。三条预期行为全部达成 |

基线整体很强（Opus 5 medium），区分度集中在 4 条：三条「官方文档里明确、社区上游普遍缺失」的规则（watcher 清理 API、`createTestingPinia` 的四档用法、`status`/`error` 契约），加上一条 skill 必须坚持的默认方案（取消而非 token 计数）。评测保留原样，未改写。

## 评测结果

两组均为 `uv run tools/run_evals.py vue [--baseline]`，模型固定 `claude-opus-5:medium`（`tools/run_evals.py` 默认，未传 `--model` / `--thinking`）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 响应式丢失（`ProductFilters.vue`） | claude-opus-5:medium | 无（baseline） | false | 8 / 9：1 props 二次解构、2 `watch` 源需 getter、3 `reactive` 重赋值、4 缺 `.value`、5 computed 副作用、6 改 prop、8 `v-if`+`v-for`、9 模板派生下沉 | 未达成第 7 条：识别出竞态但明确拒绝 `AbortController`，改用手写 `latestRequest` token，并写了理由段 |
| 1 响应式丢失（`ProductFilters.vue`） | claude-opus-5:medium | 有 | true | **9 / 9** | 第 7 条填补：`onWatcherCleanup(() => controller.abort())` 在第一个 `await` 之前同步注册 + `controller.signal`，并写明「防抖只是缩小窗口，不能消除竞态」。输出也换成了本 skill 的 `## Output format`（`path:line - severity` + Verdict） |
| 2 Pinia + 测试（`useCartStore.ts` 等三文件） | claude-opus-5:medium | 无（baseline） | false | 4 / 6：1 setup store 必须返回全部 state、2 `readonly` 同样破坏、3 `storeToRefs`、5 删除快照与 `wrapper.vm` 断言 | 未达成第 4 条与第 6 条：全程未提 `createTestingPinia`，改用手动 mock `fetch` 绕开 `onMounted` 的真实请求，因此也没有 stub/spy 档位的选择 |
| 2 Pinia + 测试（`useCartStore.ts` 等三文件） | claude-opus-5:medium | 有 | true | **6 / 6**（第 6 条为行为达成、未逐字复述） | 第 4 条填补：组件层 `createTestingPinia({ createSpy: vi.fn, initialState })`，store 层 `setActivePinia(createPinia())` 跑真实 action。第 6 条按语义达成——用 spy 断言 `loadFromServer` 被调用、把「真实执行」放进纯 store 测试，但未显式说出「需要真跑就传 `stubActions: false`」。另外自建临时工程跑了 12 个用例并逐项差分回退验证 |
| 3 Nuxt 水合与去重（`dashboard.vue`、`ProjectQuota.vue`） | claude-opus-5:medium | 无（baseline） | false | 6 / 7：1 key 含调用位置导致重复请求、2 `data` 是 shallowRef、3 裸 `$fetch` 双请求、4 `localStorage` → `useCookie`、5 `new Date()` → `useState`、6 私有 runtimeConfig 且不得放 `public` | 未达成第 7 条：改写后的组件仍直接用 `data`，没有 `status`/`error` 分支 |
| 3 Nuxt 水合与去重（`dashboard.vue`、`ProjectQuota.vue`） | claude-opus-5:medium | 有 | true | 6 / 7 | 第 1–6 条全部达成且论证更准（把私有 config 同时判为第二处 mismatch）。第 7 条仍未达成：该场景的提问是「诊断并修复」，模型按 review 形态输出，未重写加载/错误态。为此把 `status`/`error` 契约从 `references/nuxt.md` 上提进 Core rule 24 后 `--only 3` 复跑一次，仍未触发——判定为该任务形态下无法强制的一条，如实记为未填补 |
| 4 负例（Next.js RSC `page.tsx`） | claude-opus-5:medium | 无（baseline） | **false** | 3 / 3 | 按 RSC 请求瀑布流作答：`Promise.all` + 先发起后 await，无任何 Vue/Nuxt/Pinia 内容 |
| 4 负例（Next.js RSC `page.tsx`） | claude-opus-5:medium | 有 | **false** | 3 / 3 | 负例成立：`skill_read == false`，答复仍是纯 RSC（`Promise.all`、`<Suspense>` 流式、`React.cache` 去重、`revalidate`），未加载本 skill |

结论：**通过**。基线未达成的 4 条行为中填补了 3 条（场景 1 第 7 条、场景 2 第 4 与第 6 条），其中场景 1 的第 7 条是基线**主动选择了相反做法**、有 skill 时改回官方做法，区分度最强；负例两组 `skill_read` 均为 `false`。唯一未填补的是场景 3 第 7 条（`status`/`error`），已在上表说明并保留为已知缺口。

## 备注

- **当前 GA 版本核实**（不凭记忆，见裁决 6）：Vue `3.5.42`（3.6 仍为 RC，正文不写）、Nuxt `4.5.2`、Vue Router `5.3.1`、Pinia `4.0.3`。版本敏感规则一律用 `(3.5+)` / `(Nuxt 4+)` 形式标注可用性底线。
- **antfu `paths` 收窄理由**：`antfu/skills` 已作为 `antfu-design` 被 `frontend-design` 使用；本 skill 只列 `skills/vue`、`skills/nuxt`。其 `skills/pinia` 内容合格但可被 `vuejs-ai-skills` + `pinia-docs` 完全替代（后者权威更高），`skills/vue-best-practices` 等目录是 vuejs-ai 的同步副本（带独立 `LICENSE.md` 与 `SYNC.md`），归在 `vuejs-ai-skills` 名下更准确。
- **许可注意**：`onmax/nuxt-skills` 无 LICENSE 文件（`license: NONE`），按仓库许可政策合入，一字未抄。`vuejs/docs` 的 GitHub API 返回 `NOASSERTION`，实读 LICENSE 为 CC BY 4.0（图片除外），故 `license: CC-BY-4.0` 并在 `notes` 写署名。`Patrity/nuxt-skills` 为 GPL-3.0，按规则不得 merged，且内容无 reference 价值，直接 REJECT 未列入 `SOURCES.yaml`。
- **未来同步要盯**：Vue 3.6 转 GA 后需复核 Vapor mode 与新响应式实现是否改变 `shallowRef`/`v-memo` 相关建议；Nuxt 5 的 Nitro v3 变更（`nuxt/server` 导入路径、`createError` 返回值、route rules `status` 重命名）目前只在 Nuxt 5 升级文档中，Nuxt 5 GA 后需重写 Nuxt reference 的 server 一节。
- **放弃的方向**：Options API 与 JSX/render function 两条线（vuejs-ai 有专门 skill）不写默认路径，只在迁移语境提及；VueUse 函数目录（antfu `vueuse-functions`，300+ 文件）不收——它是 API 目录而非陷阱集，且 `frontend-design` 与本 skill 都不需要逐函数索引。
