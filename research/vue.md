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

## 2026-09-29 上游同步

漂移报告（`tools/check_upstream.py`，2026-09-29）中本 skill 有 3 条 `behind`，均为 too-large，其余 `OK` / `manual check`。
按完整区间用 blobless clone 归因（`git log/diff <旧pin>..<HEAD> -- <paths>`），不用日期窗口。
pin 后逐条核对：写入的 commit 均等于审阅时的 HEAD。

| 上游 | 区间 | paths 内变更 | 判定 | 理由 |
|---|---|---|---|---|
| `onmax-nuxt-skills` | `50878f5..3bbba5a` | `9b069d6`「bundle ecosystem skills」及其后 `bc438e5` / `aa40aa0` / `de09c7b`（lint 修复与 bundle 重生成来回）：`skills/nuxt`、`skills/vue` 两棵树整体被替换，原手写文件（`nuxt-composables.md`、`gotchas.md` 等）全部删除，40 文件 +6370/−3207 | 重新裁决（不改正文） | 实读 `ecosystem-skills.json`：`nuxt` 与 `vue` 映射到 `antfu/skills`，由每周 CI 物化为副本（`skills/vue` 为 antfu 2026-01-31 生成版，`skills/nuxt` 为 2026-06-22 生成版）。本 skill 从该上游取用的全部内容来自 `50878f5` 的手写版本，HEAD 已不存在；今后该路径下的变化都是 `antfu-skills` 条目的重复。条目保留为已合入内容的署名，`notes` 写明取材提交是 `50878f5`、HEAD 的 pin 只是工具行为 |
| `antfu-skills` | `a74f281..d02c484` | `d02c484`（按最新上游文档重生成）：`skills/vue` 新增 `GlobalDirectives` 全局指令类型、`isShallow()`、`defineProps` 使用导入类型三小段；`skills/nuxt` 整体改为基于 **Nuxt 5.x（5.0.0-0）**：Nitro v3 / h3 v2、`nuxt/server` 显式导入、`createError` 改 `status`/`statusText`、typed routes、大小写敏感路由、`clearNuxtState` 重置语义等；另补「`await` 不改变 SSR HTML、只影响客户端导航」与「`useFetch` key 含调用位置」 | 新增（不合入） | Vue 侧三项是 API 参考条目，不在本 skill 的陷阱/失败模式定位（`contributes`）内。Nuxt 侧：releases API 实查当前 GA 仍为 `v4.5.2`（2026-08-05），Nuxt 5 属预发布，本 skill 既定不写 Nuxt 5（见上文「未来同步要盯」）；与 Nuxt 4 共通的两点（`await` 与 `lazy` 相互独立、key 含调用位置）正文已有（规则 25 与 `references/nuxt.md`），无需改 |
| `awesome-copilot` | `7568a48..997e95a` | 完整区间内 `instructions/vue.instructions.md`、`skills/unit-test-vue-pinia` 无提交、无 diff | 噪声（实际未变更） | 仅 re-pin |

**正文未变**（仅 `SKILL.md` 的 `metadata.version`、`SOURCES.yaml` 的 version / pin / notes），因此未跑 D2 行为评测。

遗留：Nuxt 5 GA 后需按 antfu 已跟进的 Nitro v3 变更重写 `references/nuxt.md` 的 server routes 一节（`createError({ statusCode, statusMessage })` 在 Nuxt 5 下改为 `status` / `statusText`）。

## 2026-10-15 上游同步

依据 2026-10-15 `tools/check_upstream.py --json` 报告与主代理归因（`/tmp/hs-attr/skills_real.json`），本 skill 只有
`onmax-nuxt-skills` 一条在 tracked paths 下确有提交。用 `gh api repos/onmax/nuxt-skills/compare/<旧pin>...<审阅HEAD>`
取完整 patch，逐文件读 diff 归因；其余条目（`vuejs-ai-skills`、`awesome-skills-code-review` up to date，`antfu-skills`
repo moved / paths unchanged，`awesome-copilot` too-large 但归因为空）随 `--pin` 对齐。

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| `onmax-nuxt-skills` | `3bbba5a → 46aaca0`（4 提交：`17cb3fa`、`e44b316`、`2bdce85`、`008232b`） | `skills/vue`：`SKILL.md` 版本号；`advanced-patterns.md` 加 `GlobalDirectives` 全局指令类型；`core-new-apis.md` 加 `isShallow()`；`script-setup-macros.md` 加「`defineProps` 可用导入类型」。`skills/nuxt`：整体切到 **Nuxt 5.x（`5.0.0-0`）**——Nitro v3 / h3 v2、`nuxt/server` 显式导入、`createError` 改 `status`/`statusText`、typed routes、大小写敏感路由、`clearNuxtState` 重置为初值、`payloadExtraction: 'client'`、无 `jiti` 的 config 加载；另有组件目录 `(group)` 分组与 `pattern`/`ignore` glob、`await` 与 `lazy` 的客户端语义、`useFetch` key 含调用位置 | 不合入（噪声 / 预发布 / 已覆盖） |

归因要点：

- 这批提交是 onmax 每周 bundle 任务把 `antfu/skills` 的物化副本同步进来（`ecosystem-skills.json` 把 `nuxt`、`vue`
  映射到 antfu，见 2026-09-29 节），内容与本 skill `antfu-skills` 条目在 `d02c484` 已审过的版本一致；`antfu-skills`
  自身本次 paths 无变化。
- Nuxt 5：`npm view nuxt dist-tags` 实查 `latest` 为 `4.6.1`，不存在任何 5.x 发布标签，Nuxt 5 仍是主干上的预发布；
  本 skill 只写 GA 线（`SKILL.md` Scope 与 `nuxt-docs` notes 已声明 Nuxt 5 不写），故全部 Nuxt 5 条目不合入。
- 与 Nuxt 4 共通的两点已覆盖：`await` 不改 SSR HTML、`lazy` 与 `await` 相互独立（`references/nuxt.md`「await, lazy
  and immediate」）；`useFetch` key 含调用位置、共享需显式 `key`（规则 25、`references/nuxt.md` 第 70–90 行）。
- Vue 侧三项是 API 参考条目（全局指令类型、`isShallow`、导入类型的 props），不在本 skill「陷阱 / 失败模式」的
  `contributes` 定位内，且 `defineProps` 导入类型自 3.3 起即为模型熟知能力。

结论：**正文未变**，仅 `SKILL.md` 的 `metadata.version`、`SOURCES.yaml` 的 version / pin 更新为 2026.10.15；
未新增评测场景，未跑 D2。`pin_check.py`：PIN CHECK CLEAN。遗留沿用上节：Nuxt 5 GA 后重写 `references/nuxt.md`
的 server routes 一节。

## 2026-10-15 文档上游复核

五个 docs 条目均以 GitHub 源文件为准（`gh api` 读取，Nuxt/Pinia/Router 读当前发布 tag），版本经 npm registry 核实：vue `latest` 3.5.44（`rc` 3.6.0-rc.11）、nuxt 4.6.1、pinia 4.1.0、vue-router 5.4.0、@vue/test-utils 2.5.1。

| 上游 id | 核对的事实 | 当前官方页面 | 结论 |
|---|---|---|---|
| vue-docs | Reactive Props Destructure（3.5+）：编译器自动前置 `props.`，传入函数需包成 getter；`onWatcherCleanup`（3.5+，须同步调用）与 `flush: 'post'`；`data-allow-mismatch`、`useId`、`useTemplateRef`（均 3.5+）；`v-memo`（3.2+）；`shallowRef` 用途 | vuejs/docs `src/guide/components/props.md`、`essentials/watchers.md`、`api/ssr.md`、`api/composition-api-helpers.md`、`api/built-in-directives.md`、`best-practices/performance.md`（main 40aa88a，2026-09-15） | 一致。09-11 后仅 8 个文档提交，其一（#3459）补「子组件 scoped 样式不作用于插槽内容」，与 `references/components.md`「`:slotted()`/`:deep()`」一致 |
| vue-docs | 当前 GA 3.5，3.6 仍为预发布 | npm `vue` dist-tags | 一致（notes 中版本号 3.5.42 → 3.5.44） |
| nuxt-docs | `useFetch` key 含调用位置；共享 key 时必须一致（`handler`/`deep`/`transform`/`pick`/`getCachedData`/`default`）与可不同（`server`/`lazy`/`immediate`/`dedupe`/`watch`）；`deep` 默认 `false`；`createUseFetch` 是须导出的编译宏、`useFetch` 为保留名；`await` 与 `lazy` 相互独立；私有 runtimeConfig 仅服务端；`componentIslands` 默认 `'auto'` | nuxt/nuxt v4.6.1 `docs/1.getting-started/10.data-fetching.md`、`docs/4.api/2.composables/use-fetch.md`、`create-use-fetch.md`、`docs/3.guide/6.going-further/10.runtime-config.md`；`packages/schema/src/config/experimental.ts`（`componentIslands` `$resolve` → `'auto'`） | 一致。4.6 新增 `defineUseFetchAddon`、`runtimeConfig.appSecret`（`app` 前缀键保留给 Nuxt）——不涉本 skill 现有规则，仅记录 |
| pinia-docs | setup store 必须返回全部 state、设 readonly 同样破坏 SSR/devtools/插件；`storeToRefs` 含插件属性、action 可直接解构；`$reset` 仅 option store；Pinia 4 ESM-only（`type: module`）、`@vue/devtools-api` 为必需 peer（`optional: false`） | vuejs/pinia v4.1.0 `packages/docs/core-concepts/index.md`、`state.md`、`packages/pinia/package.json` | 一致。4.1.0 新增 `getStores()`、修复 `$patch` 对象语法触发 shallow ref——正文无相反断言 |
| router-docs | 守卫返回值（`false` 取消、路由地址重定向、`undefined`/`true` 放行）；参数变化用 `beforeRouteUpdate`/`onBeforeRouteUpdate`；`RouteRecordInfo` 类型化路由；`scrollBehavior` 的 `savedPosition` 仅 popstate；v5 合入 unplugin-vue-router，v4 用户除 IIFE 外无破坏性变更 | vuejs/router v5.4.0 `packages/docs/guide/advanced/navigation-guards.md`、`essentials/dynamic-matching.md`、`advanced/typed-routes.md`、`advanced/scroll-behavior.md`、`migration/v4-to-v5.md` | 一致。5.4.0 的破坏性变更与「默认恢复 hash/top」均限 experimental 路由器，不影响 `createRouter` 的 `scrollBehavior` |
| vue-test-utils-docs | `global.plugins`、`emitted()`、`findComponent`、`nextTick` 与 `flushPromises` 的区别、`shallow: true` | vuejs/test-utils main `docs/guide/advanced/async-suspense.md`、`essentials/event-handling.md`、`advanced/stubs-shallow-mount.md`、`docs/api/index.md` | 一致（2.5.1 仅类型与构建修复） |

正文未改；五个条目 `synced_at` 更新为 2026-10-15，notes 中的「当前版本」同步为本次实查值。

## 2026-11-01 上游同步

`--pin` 写入 `198f0cd`、`525c01d`、`7de210b`、`5269f7e`，与快照 HEAD 一致。

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| vuejs-ai-skills | c9d355f → 198f0cd（11 提交） | `310c195` 组件边界改为按职责划分：「3+ UI 区块、CRUD 必拆」等硬阈值改为 review 信号，单一使用者的抽取也合法，拆分只增加转发时不拆；`1715919`…`813324` v-memo 重写：依赖按引用比较，行可被替换时列入 `item`、原地修改时列入字段；子组件 props 不变本就不重渲染，v-memo 只省 VNode 创建与 diff；`1f441dd` 3.5+ 响应式 props 解构示例；`16479ee` SFC 段顺序统一为 script→template→style | **采纳上游自我更正**：`components.md` 的「Concrete triggers」改为 review 信号；`performance.md` 示例改 `[item, item.id === selectedId]` 并写明按引用比较、收益范围，「stale forever」改为「直到某个依赖变化」。解构示例与 SFC 顺序本 skill 已有 |
| onmax-nuxt-skills | 46aaca0 → 525c01d（`1155ef9`） | `core-cli.md`：Nuxt CLI v4（4.6+），`nuxt init` 移除改用 `npm create nuxt@latest`，4.5.1 安全修复后 `nuxt upgrade --dedupe`；`core-config.md`：Node 22.21+/24.11+/26+、`NUXT_E*` 错误码 | **触发事实更正**：`SKILL.md` Environment 原写「Node.js 20+」。npm engines 实查：nuxt 4.5.2 `^22.19.0`、4.6.3 `^22.22.3 \|\| ^24.15.0 \|\| >=26`，vitest 5.0.5 `^22.12.0`（vite 8.3.5 仍 `^20.19`）；改为 Node 22.12+ 并列 Nuxt 4.6 要求 |
| antfu-skills / awesome-copilot | 噪声 | paths 未变 | 只 re-pin |

遗留项核实：**Nuxt 5 仍未发布**——`npm view nuxt versions` 无任何 5.x，`gh api repos/nuxt/nuxt/releases` 最新 v4.6.3（2026-10-27），server 段不按 Nuxt 5 重写。但其中 `createError` 一项已在 4.x 生效：
v4.6.3 文档 `create-error.md`/`server.md` 只用 `status`/`statusText`，`NuxtError` 中 `statusCode`/`statusMessage` 自 v4.3.0 标 `@deprecated`（源码注释「remove in Nuxt 5」）。
`references/nuxt.md` 改为 `createError({ status, statusText })` 并注明弃用，「Verified against」改为 Nuxt 4.6。另记（未写入）：Nuxt 4.6 新增 `nuxt/server` 导入面，Nuxt 3 已于 2026-07-31 EOL。

## 2026-11-01 上游新增内容评估

工作单 C 为空；未发现分配给本 skill 的新增文件。

## 2026-11-01 新候选检索

`gh search repos`（`vue skills`、`nuxt skills`，`--created >2026-08-01`）只返回 caiqianha/vue-skills（2★，MIT）、KIMJINWOO4/vue-skills-ci（1★）、xushicheng/…（0★，无许可），
均为个人练习仓库，未达复核门槛（stars/权威 0–1），不入候选表；awesome-agent-skills 与 awesome-copilot 区间内无 Vue/Nuxt 新条目。

## 2026-11-01 文档上游复核

| 上游 id | 核对的事实 | 当前官方页面 | 结论 |
|---|---|---|---|
| vue-docs | v-memo / v-once 语义；当前 GA | https://vuejs.org/api/built-in-directives.html#v-memo；`gh api repos/vuejs/core/releases` 最新非预发布 v3.5.44（3.6.0-rc.14 仍预发布） | 一致；`performance.md` 按依赖按引用比较补充 |
| nuxt-docs | useFetch key 含调用位置、`deep` 默认 false、`createUseFetch` 须为导出声明、`useFetch` 保留名、`componentIslands` 默认 `'auto'`（`packages/schema/src/config/experimental.ts` `val ?? 'auto'`）；createError 字段 | nuxt/nuxt v4.6.3 `docs/4.api/2.composables/use-fetch.md`、`create-use-fetch.md`、`docs/4.api/3.utils/create-error.md` | createError **已变化 → 更正**；其余一致 |
| pinia-docs | Pinia 4 ESM-only、`@vue/devtools-api` 必需 peer | npm pinia 4.1.0 peerDependencies `@vue/devtools-api ^8.2.1`；v4.1.0 发布说明（新增 `getStores()`，无破坏性变更） | 一致 |
| router-docs | v5 合入 unplugin-vue-router、守卫语义 | npm vue-router 5.4.0（与上次复核同版本） | 一致 |
| vue-test-utils-docs | 2.5 挂载选项与 `flushPromises` | npm @vue/test-utils 2.5.1（同上次） | 一致 |

## 2026-11-01 D2 回归

覆盖提交 `d512876`（components.md、performance.md、nuxt.md、SKILL.md Environment）。原有场景无一覆盖 v-memo 与 server handler 的 `createError`，新增回归场景 5
（夹具 `ProjectRows.vue`：`v-memo="[project.id, project.id === props.selectedId]"`，`refresh()` 整体替换对象，改名后行不更新直到切换选中；`projects-id.patch.ts`：三处 `createError({ statusCode, statusMessage })`）。
场景 3（Nuxt，读 `nuxt.md`）作回归，场景 4 为负例。产物 `/tmp/hs-d2/G01-web-ui/vue/omp-openai-gpt-6.1-sol-medium/`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 5 | gpt-6.1-sol medium | 无 | false | 1✔ 2✔ **3✘** **4◐** 5◐ | 249 s，在 Nuxt 4.6.0 实跑验证。v-memo 改 `[project, …]` 并说明 `refresh()` 换对象；未提「只在测得的热点用 v-memo、可直接删除」。`createError` 改 `status`/`statusText`，但称旧写法「仍受支持」「迁到新的可移植 API」，未说已弃用；另改从 `nuxt/server` 显式导入（4.6 新导入面）。未声称「永久陈旧」，也未解释切换选中即恢复 |
| 5 | gpt-6.1-sol medium | 有 | true | 1✔ 2✔ **3✘** **4✔** 5◐ | 193 s，读 `SKILL.md`、`nuxt.md`、`reactivity.md`，**未读 `performance.md`**。v-memo 修法同基线；`createError` 明确判为弃用并改 `status`/`statusText`（未写 4.3 / Nuxt 5 时间点）；3、5 同基线 |
| 3 | gpt-6.1-sol medium | 有 | true | 1✔ 2✔ 3✔ 4✔ 5✔ 6✔ 7✔ | 204 s，读 `nuxt.md`、`reactivity.md`，在 Nuxt 4.6.3 / Vue 3.5.44 实跑。显式 `projects` key + `useNuxtData`、整体替换数组、裸 `$fetch` → `useFetch`、`localStorage` 挪到 `onMounted`、`useState` 序列化时间、`config.public.maxProjects` 并去掉密钥判断、补加载/错误态；无回退（第 7 条首次达成） |
| 4（负例） | gpt-6.1-sol medium | 有 | **false** | 1✔ 2✔ 3✔ | 20 s，`Promise.all` 拆瀑布，无 Vue/Nuxt 建议 |

结论：无回退，负例未误读。`createError` 更正在有 skill 时生效（基线只当作可选迁移，不知已弃用）。v-memo 更正与基线同水平：基线已会「按引用比较、列入对象本身」；
`performance.md` 的新增说明（收益范围、只用于测得的热点）未被读取，场景 5 第 3 条两侧都未达成——本次是上游自我更正而非新增规则，不据此加 Core rule，场景 5 留作哨兵。
components.md 拆分阈值改为 review 信号、Environment 的 Node 版本无行为差异可测，未单独设场景。

### 主代理补齐门禁：Node 版本更正补场景

上一行「Node 版本无行为差异可测」不成立：升级依赖后 Docker/CI 的 Node 版本选择是可观察行为。新增场景 6（`evals/files/nuxt-package.json`、`nuxt-Dockerfile` 两阶段
`node:20.18-alpine`、`nuxt-ci.yml` 的 `node-version: 22.11.0`）。`npm view nuxt@4.6.3 engines` 为 `^22.22.3 || ^24.15.0 || >=26.0.0`，与正文一致。
产物 `/tmp/hs-d2/fix/vue/omp-openai-gpt-6.1-sol-medium/`，有 skill 运行晚于 `d512876`。components.md 拆分阈值改为 review 信号属措辞调整，仍不单设场景。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 6（新增） | gpt-6.1-sol medium | 无 | False | EB1–EB3 ✔ | 39 s。直接读 npm registry 的 engines，两阶段镜像与 CI 都改 22.22.3，并指出 22.12 只满足 Vitest |
| 6（新增） | gpt-6.1-sol medium | 有 | True | EB1–EB3 ✔ | 57 s。同上，逐行标 blocking |

结论：基线已会，场景 6 留作哨兵；有 skill 无回退。

## 2026-11-04 description 维护（两层写法）

旧：`Develops Vue and Nuxt applications with Composition API, Pinia and routing.`  
新：`Develops Vue 3 and Nuxt web applications with the Composition API, Pinia and Vue Router. Use when editing .vue files, composables, Pinia stores, router guards or Nuxt pages, or when a value changes but the UI does not, including reactivity lost by destructuring props.`（首句 88 字符，全长 268 字符）

依据：`docs/skill-standard.md` 1.1.1（首句自足并点名领域，随后用 `Use when` 列具体触发场景；`Not for` 只保留实测过的排除词）；调研来源与冲突裁决见该节依据表。A 复核 `## Scope` 与 2026-09-12 压缩前的长描述作为触发词来源；C 只改 description 与版本号，正文与上游 pin 不变；D 静态门 `uv run --locked tools/check_repository.py` 通过。
路由对照：本 skill 不在本轮抽样内（抽样 9 个 skill，见 `research/python.md` 同日记录），未测量新描述的选择率。
