# typescript 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"TypeScript agent skill SKILL.md github type-level design"`、
    `"tsconfig strict verbatimModuleSyntax agent skill SKILL.md typescript build ESM package exports"`
  - <https://www.skills.sh>（经 web_search 的 skills.sh / skillsmp / tessl 索引结果间接命中）
  - VoltAgent/awesome-agent-skills、addyosmani/agent-skills（无 TypeScript 语言级条目）
  - `github/awesome-copilot`：`skills/` 与 `instructions/` 两处都按 `typescript|vitest|jest|tsconfig` 检索
  - 领域官方组织仓库：`microsoft/TypeScript`（releases + devblogs 公告）、`vitest-dev/vitest`（Context7）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 正常，账号 Lynricsy，全程登录态调用，未触发限流）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | mattpocock/skills `skills/engineering/codebase-design`（含 DEEPENING.md、DESIGN-IT-TWICE.md） | https://github.com/mattpocock/skills | 258595 | 2026-09-04 | MIT | 深模块设计词汇：module/interface/depth/seam/adapter，deletion test，端口与适配器分类 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 公认 TS 专家；词汇定义精确、有"拒绝的表述"节；语言无关但正是本 skill 缺的模块层 |
| 2 | mattpocock/skills `skills/engineering/domain-modeling` | 同上 | 258595 | 2026-09-04 | MIT | CONTEXT.md 术语表 + ADR 纪律 | 2 | 3 | 1 | 3 | 2 | 11 | MAYBE | 名为 domain-modeling，实为文档纪律（术语表/ADR），**没有类型层建模**；只取"术语一致性"一条思想，不进 references |
| 3 | mattpocock/skills `skills/engineering/improve-codebase-architecture` | 同上 | 258595 | 2026-09-04 | MIT | 扫描浅模块 → HTML 报告 → 逐个 grill | 2 | 3 | 2 | 3 | 2 | 12 | MAYBE | 主体是 HTML 报告生成流程与 sub-agent 编排，harness 绑定重；只取"探测浅模块的提问清单"与 deletion test 用法 |
| 4 | mcollina/skills `skills/typescript-magician`（+ 14 个 rules/） | https://github.com/mcollina/skills | 1913 | 2026-08-17 | MIT | 泛型、conditional/mapped/template literal、infer、品牌类型、收窄、断言函数、重载、错误诊断 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE | 类型层覆盖最完整；rules/ 每篇都有正误对照与陷阱（arrow function 不能写 `asserts`、narrowing 不跨回调） |
| 5 | shipshitdev/skills `skills/typescript-refactor`（43 条规则 / 8 类） | https://github.com/shipshitdev/skills | 35 | 2026-09-10 | NONE | 类型架构、收窄、现代特性、泛型、编译性能、错误安全、运行时、怪癖 | 1 | 3 | 3 | 3 | 0 | 10 | INCLUDE | 规则粒度与本仓库标准最接近；抽查 `arch-satisfies-over-annotation`、`generic-avoid-distributive-surprises`、`quirk-excess-property-checks`、`modern-verbatim-module-syntax` 四条全对。仓库根无 LICENSE → `license: NONE` |
| 6 | shipshitdev/skills `skills/typescript-expert` | 同上 | 35 | 2026-09-10 | NONE | 深度递归错误诊断、JS→TS 迁移、Biome/ESLint/Turborepo/Nx 选型 | 1 | 3 | 2 | 2 | 0 | 8 | MAYBE | 一半是工具选型（超出本 skill 边界）；只取"type instantiation excessively deep"的诊断顺序 |
| 7 | github/awesome-copilot `skills/javascript-typescript-jest` | https://github.com/github/awesome-copilot | 38858 | 2026-09-10 | MIT | Jest 结构、mock、异步、快照、常用 matcher | 3 | 3 | 1 | 2 | 2 | 11 | MAYBE | 官方仓库但这篇几乎全是模型已知常识（matcher 清单），且无 TS 侧配置；只用来核对测试章节覆盖面 |
| 8 | github/awesome-copilot `instructions/nodejs-javascript-vitest.instructions.md` | 同上 | 38858 | 2026-09-10 | MIT | Node ESM + Vitest 写法约定 | 3 | 3 | 1 | 2 | 2 | 11 | MAYBE | `applyTo` 只匹配 `.js/.mjs/.cjs`，本身不谈 TypeScript；仅作覆盖面核对 |
| 9 | Jeffallan/claude-skills `skills/typescript-pro`（5 个 references） | https://github.com/Jeffallan/claude-skills | 11403 | 2026-08-07 | MIT | 品牌类型、可辨识联合、工具类型、tsconfig、项目引用、路径映射 | 1 | 2 | 2 | 1 | 2 | 8 | MAYBE | 结构清楚，但 `references/configuration.md` 的"严格模式配置"整块已被 TS 6.0 作废（`baseUrl`、`moduleResolution: node`、显式 `esModuleInterop`、`target es5` 语境）→ 只取类型层示例，配置章节一律不采 |
| 10 | Paldom/node-skills `skills/node-typescript` + `skills/node-packaging` | https://github.com/Paldom/node-skills | 1 | 2026-09-10 | MIT | 按消费方式选 module/moduleResolution、verbatimModuleSyntax、isolatedDeclarations、declaration emit、strict 化棘轮、exports map、publint/attw | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 星数极低但内容是全部候选里唯一正确覆盖 TS 6/7 现状的（明确写出 `baseUrl`/`target es5`/`moduleResolution classic` 在 7 上是硬错误）；每条抽查都对 |
| 11 | giuseppe-trisciuoglio/developer-kit `plugins/developer-kit-typescript` | https://github.com/giuseppe-trisciuoglio/developer-kit | 343 | 2026-09-10 | MIT | NestJS、AWS CDK、Lambda、better-auth、Drizzle、clean architecture | 1 | 3 | 2 | 2 | 2 | 10 | REJECT | 目录名叫 typescript，内容全是框架/云 skill（NestJS、CDK、better-auth），语言层为零；落在本 skill 的否定边界内 |
| 12 | fallow-rs/fallow-skills `fallow/skills/fallow-review` | https://github.com/fallow-rs/fallow-skills | 121 | 2026-09-10 | MIT | 绑定 `fallow` CLI 的影响面评审 + hooks/statusline | 1 | 3 | 2 | 2 | 2 | 10 | REJECT | 整个 skill 围绕自家 Rust CLI 与 hook 脚本；脱离该工具无可迁移内容，属产品包装 |
| 13 | antfu/skills `instructions/{tsdown,vitest}.md` | https://github.com/antfu/skills | 5871 | 2026-06-23 | MIT | tsdown 打包、vitest 用法 | 2 | 1 | 2 | 2 | 2 | 9 | MAYBE | 作者自述 PoC；`instructions/` 绑定其个人工具链（tsdown/unocss）；只作 vitest 章节的交叉校验，不引用 |
| 14 | vercel-labs/native `skill-data/ts-core` | https://github.com/vercel-labs/native | 7647 | 2026-09-06 | Apache-2.0 | Native SDK 的 app-core 子集（Model/Msg/update、NS1001-NS1069 子集检查器） | 2 | 3 | 3 | 2 | 2 | 12 | REJECT | 是某个私有 SDK 的"受限 TypeScript 子集"说明书，规则（禁闭包、禁类）在通用 TS 里是错的 |
| 15 | AI-Riksarkivet/ra-skills `skills/writing-typescript` | https://github.com/AI-Riksarkivet/ra-skills | 0 | 2026-08-31 | Apache-2.0 | strict、unknown over any、Result 类型、Bun/Vite/Vitest | 0 | 3 | 2 | 2 | 2 | 9 | REJECT | 0 star、写死本仓库路径（`components/apps/frontend/`）与 SvelteKit 语境；主题已被 4/5/10 覆盖 |
| 16 | saeed-vayghan/gemini-agent-skills `.gemini/skills/typescript-pro` | https://github.com/saeed-vayghan/gemini-agent-skills | 34 | 2026-01-18 | MIT | 人设式"You are a senior TypeScript developer"清单 | 0 | 0 | 1 | 2 | 2 | 5 | REJECT | 8 个月未推送（量表新鲜度 0 直接淘汰）；正文是能力罗列而非可执行规则 |
| 17 | SpillwaveSolutions/mastering-typescript-skill | https://github.com/SpillwaveSolutions/mastering-typescript-skill | 30 | 2026-01-01 | NONE | 单 skill 的 TypeScript 教程 | 0 | 0 | 1 | 1 | 0 | 2 | REJECT | 9 个月未推送 + 无许可 + 教程式 |
| 18 | langgenius/mosoo-skills `skills/typescript-expert` | https://github.com/langgenius/mosoo-skills | 2 | 2026-08-04 | NONE | 通用 TypeScript 助手 | 0 | 2 | 1 | 1 | 0 | 4 | REJECT | 2 star、无许可、内容为通用复述 |
| 19 | benknightdark/neo-skills / pikakit/agent-skills | https://github.com/benknightdark/neo-skills | 7 / 0 | 2026-09-06 / 2026-09-10 | MIT / MIT | 个人 skill 集合中的 typescript 条目 | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | 个人收藏夹式仓库，内容为通用清单，无独有陷阱 |
| 20 | typescriptlang.org Handbook + TSConfig Reference | https://www.typescriptlang.org/tsconfig/ | — | 持续 | Proprietary（微软文档，`kind: docs`） | 语言与编译选项的权威定义 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 所有事实的最终裁决依据 |
| 21 | devblogs.microsoft.com 「Announcing TypeScript 6.0 / 7.0」 | https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/ | — | 2026-03-23 / 2026-07-08 | Proprietary（`kind: docs`） | TS 6.0 弃用清单、TS 7.0 默认值与硬错误、`--checkers`/`--builders`、`@typescript/typescript6` | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 本 skill 最高价值内容的唯一权威来源；`gh api repos/microsoft/TypeScript/releases` 核到 v7.0.2 (2026-08-20)、v6.0.2 (2026-03-23) |
| 22 | vitest.dev testing-types / TypecheckConfig | https://vitest.dev/guide/testing-types | — | 持续（v4.x） | MIT（`kind: docs`） | `--typecheck`、`expectTypeOf`、`*.test-d.ts` 默认 include | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 测试章节 TS 侧的权威来源（经 Context7 取自仓库内 docs 与 `defaults.ts`） |

## 深度审查

### mattpocock/skills `codebase-design`（114 行 SKILL.md + DEEPENING.md 37 行 + DESIGN-IT-TWICE.md 44 行）

- 结构：Glossary → Deep vs shallow → Principles → Designing for testability → Relationships → Rejected framings。
  frontmatter 只有 `name`/`description`，干净；无 agent 专属字段。
- 质量：术语定义带「_Avoid_: unit, component, service」这种反向约束，是本仓库标准里"术语全篇一致"的现成落地。
  `Rejected framings` 一节明确拒绝 Ousterhout 的"实现行数/接口行数"深度定义，理由是"奖励往实现里灌水"——这是判断，不是复述。
- agent 绑定：`improve-codebase-architecture` 里有 `disable-model-invocation: true`、`Call the Skill tool with "codebase-design"`、
  Tailwind/Mermaid CDN HTML 报告、`xdg-open`——全部剥离。
- 重叠：与本仓库 `code-review` 的 smell baseline 有交集（都会谈"这个模块该不该存在"），
  但 `code-review` 是对一个 diff 的评审，这里是设计一个模块的接口，落点不同。
- 采纳：deep/shallow、seam、adapter、leverage、locality、deletion test、"one adapter = hypothetical seam"、
  "interface is the test surface"、依赖四分类（in-process / local-substitutable / remote-owned / true-external）。
  ASCII 框图重画为本仓库风格。

### mcollina/skills `typescript-magician`（SKILL.md + 14 个 rules/）

- 结构：SKILL.md 是索引 + 两个 before/after 例子，细节全在 `rules/*.md`，与本仓库 SKILL.md + references 同构。
- frontmatter：`metadata.tags` 非规范字段，剥离。
- 质量：`type-narrowing.md` 的「Control Flow Analysis Limitations」（把 type predicate 结果存进变量后不再收窄）、
  「Narrowing Doesn't Persist Across Callbacks」，以及 `opaque-types.md` 的「assertion function 必须用 `function` 声明，
  箭头函数会报 'Assertions require every name in the call target to be declared with an explicit type annotation'」
  ——都是真实踩坑，不是 API 复述。
- 缺口：完全不谈 tsconfig / 模块解析 / 发包 / 测试；`utility-types.md` 一类偏基础。
- 采纳：收窄与泛型章节的主体、品牌类型、断言函数语法陷阱、distributive 行为。

### shipshitdev/skills `typescript-refactor`（43 条规则，每条一个 reference 文件）

- 结构：SKILL.md 是带优先级表的索引（arch/narrow/modern/generic/compile/error/perf/quirk 八个前缀），
  每条规则一个 40–60 行文件，格式统一：title/impact/impactDescription/tags + Incorrect/Correct + Reference 链接。
- 质量抽查（对照官方文档）：
  - `arch-satisfies-over-annotation`：注解会把字面量拓宽、`satisfies` 保留 —— 对。
  - `generic-avoid-distributive-surprises`：`[T] extends [U]` 关闭分发 —— 对，且与 Handbook 的
    Distributive Conditional Types 一致。
  - `quirk-excess-property-checks`：中间变量绕过多余属性检查、`satisfies` 能补回来 —— 对。
  - `modern-verbatim-module-syntax`：语义描述对，但引用的是 TS 5.0 release notes，未提 TS 6/7 语境。
  0 错，正确性 3。
- 许可：仓库根目录**没有 LICENSE 文件**（`gh api .../git/trees/master` 确认），
  `skills/typescript-expert/licenses/` 只覆盖那一个 skill 的上游 —— 按规则记 `license: NONE`。
- 采纳：类型架构 / 收窄 / 泛型 / 错误安全 / 怪癖五类的规则**语义**（不复制任何句子），
  编译性能一类只取"显式导出返回类型"与"项目引用"两条并改写。

### Paldom/node-skills `node-typescript` + `node-packaging`

- 1 star，但这是唯一一个"知道现在是 TypeScript 7 时代"的候选：明确写出
  `baseUrl`/`target: es5`/`moduleResolution: classic` 在 7 上是硬错误、`@typescript/typescript6` 回退包、
  "按消费方式（发布的未打包 Node 包 vs 打包应用）选 `nodenext` vs `bundler`"这一决策轴。
- 质量：`Gotchas` 一节全是失败模式（"`bundler` 解析在本地能过、消费者侧炸"），符合"teach the failure"。
- 缺口：不谈类型层建模，`references/tsconfig-playbook.md` 未取（本 skill 的配置块以官方公告 + 本机 tsc 实测为准）。
- 采纳：消费模型决策轴、strict 化棘轮（先量化错误面 → 分 flag/分目录 → CI 只卡"不新增"）、
  `isolatedDeclarations` 适合库不适合应用的判断、发包侧 `publint` / `arethetypeswrong` 验证门。

### Jeffallan/claude-skills `typescript-pro`

- 结构合规（SKILL.md + 5 个 references + 表格路由），11.4k star，但 `references/configuration.md`（446 行）
  是一份 **TypeScript 5.x 时代的配置清单**：推荐 `baseUrl` + `paths`、把 `esModuleInterop`/`allowSyntheticDefaultImports`
  写成需要显式开启、`moduleResolution: node` 标为"legacy, avoid"却仍列出、`target: ES2022` + 手写 `strict` 全家桶。
  在 TS 7.0.2 上照抄这份配置会直接报 TS5102（`baseUrl` removed）。
- 正确性 1（两处以上与当前编译器行为冲突）。类型层示例（品牌类型、可辨识联合、DeepReadonly）无误。
- 采纳：仅类型层示例作交叉校验；配置章节全部不采，并在冲突裁决里留证。

### github/awesome-copilot 的两份测试文件

- `skills/javascript-typescript-jest`：45 行，八成是 matcher 清单与"用 describe/it"这类模型已知内容，
  没有一条 TS 侧配置（ts-jest vs @swc/jest、`isolatedModules`、类型断言测试）。
- `instructions/nodejs-javascript-vitest.instructions.md`：`applyTo` 只匹配 `.js/.mjs/.cjs`，
  正文是 JS 编码规约（"never use null"），与 TypeScript 无关。
- 结论：两者都不足以支撑测试章节，仅用于确认"我没漏掉什么主题"。测试章节改从 vitest 官方文档取证。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | tsconfig 基线该长什么样 | Jeffallan `configuration.md` / mcollina 隐含 TS 5.x：显式写 `strict` 全家桶、`baseUrl` + `paths`、`esModuleInterop: true`；Paldom：显式配置但按 TS 6/7 现状 | 采 Paldom 的"显式配置"原则，配置项本身以 TS 6.0/7.0 公告为准：`baseUrl` 删除、`esModuleInterop` 不可为 false（写了也是噪音）、`strict` 已是默认 | 官方厂商 > 社区；且本机 `tsc@7.0.2` 实测 `baseUrl` → TS5102、`moduleResolution: node` → TS5108 |
| 2 | `types` 与 `rootDir` 要不要显式写 | 全部社区候选都没提 | 必须显式写 | TS 6.0 公告：`types` 默认 `[]`、`rootDir` 默认 `./`；本机实测空 tsconfig 下 `process` 报 TS2591 |
| 3 | `moduleResolution` 选哪个 | Jeffallan：`bundler`（列 `node` 为 legacy 但仍给出）；Paldom：按消费方式选 `nodenext` 或 `bundler` | 采 Paldom：发布的未打包包 → `nodenext`；打包应用/Bun → `bundler`；`node`/`node10`/`classic` 已被移除 | TS 6.0 公告 deprecations + 本机实测 TS5108 |
| 4 | enum vs 联合字面量 | shipshitdev `perf-union-literals-over-enums`：一律用联合字面量；mcollina：不表态 | 采联合字面量为默认，逃生口是"需要运行时遍历/反查"时用 `as const` 对象 + `keyof typeof` | 与 `erasableSyntaxOnly` 一致（本机实测：`enum` 在 `erasableSyntaxOnly` 下报 TS1294），Node 的 type-stripping 也拒绝 enum |
| 5 | 显式返回类型：全写还是只写导出 | shipshitdev `compile-explicit-return-types`：导出函数都写；mcollina `generic-infer-over-annotate`（同仓库另一条）：让 TS 推断 | 分层裁决：**导出的公共 API 写显式返回类型**（声明发射与增量构建），**模块内部让它推断**（避免过度约束）。`isolatedDeclarations` 打开时这就是硬性要求 | 两条规则的适用域不同，非真冲突；`isolatedDeclarations` 实测 TS9013 佐证 |
| 6 | Result 类型 vs 抛异常 | shipshitdev `error-result-type`：一律 Result；AI-Riksarkivet：Result over throwing | 不采"一律"。裁决为：**跨模块接口的预期失败**用可辨识联合返回；**违反不变量**继续抛。理由是 Result 会污染整条调用链，且 TS 没有 checked exception 之外的强制手段 | 与本仓库 `code-review` 的"提出移动而非只提问题"一致；shipshitdev 自己的 "When NOT to use" 一节也给了同样的边界 |
| 7 | 品牌类型的实现方式 | mcollina `opaque-types`：`__brand` 属性，并附 `unique symbol` 变体；Jeffallan：`readonly __brand` | 采 `declare const brand: unique symbol` 变体为默认，`__brand` 字符串属性作为不需要跨包共享时的简化写法 | mcollina 自己指出 `__brand` 可能与真实属性撞名；`unique symbol` 不会 |
| 8 | 「domain modeling」指什么 | mattpocock `domain-modeling`：CONTEXT.md 术语表 + ADR；本 skill 计划：类型层建模（让非法状态不可表示） | 本 skill 只做类型层建模；术语一致性作为一条 Core rule 保留，ADR/CONTEXT.md 流程不进本 skill | ADR 与需求文档属于未来 `planning` / `technical-writing` 的范围，本波不存在这些 skill，故只写"不覆盖" |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `mattpocock-codebase-design` | mattpocock/skills（`skills/engineering/codebase-design`、`skills/engineering/improve-codebase-architecture`） | merged | 深模块词汇（module/interface/depth/seam/adapter/leverage/locality）、deletion test、依赖四分类与"replace, don't layer"的测试策略 |
| `mcollina-ts-magician` | mcollina/skills（`skills/typescript-magician`） | merged | 收窄与泛型主体、品牌类型、断言函数语法陷阱、控制流分析的失效场景、分发式条件类型 |
| `shipshitdev-ts-refactor` | shipshitdev/skills（`skills/typescript-refactor`） | merged | 类型架构 / 收窄 / 现代特性 / 错误安全 / 怪癖五类规则的语义与优先级排序（全部改写，未复制句子；仓库无 LICENSE） |
| `paldom-node-ts` | Paldom/node-skills（`skills/node-typescript`、`skills/node-packaging`） | merged | 按消费模型选 module/moduleResolution 的决策轴、strict 化棘轮、declaration 发射与 exports map 的验证门 |
| `awesome-copilot-ts-tests` | github/awesome-copilot（`skills/javascript-typescript-jest`、`instructions/nodejs-javascript-vitest.instructions.md`） | reference | 仅用于核对测试章节的覆盖面；两篇内容都不含 TS 侧配置，未取任何文字 |
| `jeffallan-ts-pro` | Jeffallan/claude-skills（`skills/typescript-pro`） | reference | 类型层示例的交叉校验；其 `references/configuration.md` 与 TS 7 冲突，作为反例记录在冲突裁决 1 |
| `ts-handbook` | typescriptlang.org Handbook + TSConfig Reference | reference | 所有语言与编译选项事实的裁决依据。微软文档为专有版权，按仓库规则记 `reference`：只读取行为、本机复验后用自己的话重写，不复制任何句子、表格或示例 |
| `ts-release-notes` | devblogs.microsoft.com 「Announcing TypeScript 6.0 / 7.0」 | reference | TS 6.0 弃用清单、TS 7.0 新默认值与硬错误、并行化开关、`@typescript/typescript6` 回退。同为专有文档，处理方式同上 |
| `vitest-docs` | vitest.dev testing-types / config | merged | `--typecheck`、`expectTypeOf`、`*.test-d.ts` 的默认 include、`checker` 选项 |

## 本机核对（Phase A/B 期间实测，用于 `[verified]` 标注）

环境：`/tmp/ts-verify`，`npm i -D typescript@7` → `tsc` 7.0.2。

| 命题 | 命令 | 结果 |
|---|---|---|
| `types` 默认 `[]` | 空 `compilerOptions` + 用 `process.cwd()` | `error TS2591: Cannot find name 'process'. …add 'node' to the types field` |
| `strict` 默认 true | 空 `compilerOptions` + 隐式 any 参数 + `const s: string = null` | `TS7006` + `TS2322` |
| `baseUrl` 已移除 | `{"baseUrl":"./src"}` | `error TS5102: Option 'baseUrl' has been removed.` 并建议 `"paths": {"*": ["./src/*"]}` |
| `moduleResolution: node` 已移除 | `{"moduleResolution":"node"}` | `error TS5108: Option 'moduleResolution=node10' has been removed.` |
| `erasableSyntaxOnly` 拒绝 enum / 参数属性 | `enum`、`const enum`、`constructor(private x)` | 三处 `TS1294` |
| `isolatedDeclarations` 要求显式类型 | 无类型注解的 getter 与返回类实例的导出函数 | `TS9009`、`TS9013` |
| `verbatimModuleSyntax` + `nodenext` + 无 `"type":"module"` | 顶层 `export` | `TS1287: A top-level 'export' modifier cannot be used on value declarations in a CommonJS module when 'verbatimModuleSyntax' is enabled` |

`gh api repos/microsoft/TypeScript/releases` 与 `npm view typescript`：`latest = 7.0.2`（2026-08-20 发布），
6.0.2 于 2026-03-23 发布，`next = 7.1.0-dev`。

## 基线缺口

无 skill（`uv run tools/run_evals.py typescript --baseline`，Claude Opus 5 · medium）时，
各场景未达成的 `expected_behavior`。四个正例场景基线都跑得很强——它每次都真的 `npm i -D typescript@7`
并跑编译器，所以凡是「编译器会自己报出来」的事实它都拿到了。剩下的缺口正好落在**编译器不会报、
只能靠知识**的那一类，这也是本 skill 的价值所在。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 域建模 | （无）6/6 全达成 | 基线自建反例脚本验证了 7 条非法用法全被拒。本场景无区分度，保留作回归 |
| 2 tsconfig 迁移 | 「注意到 `dom.iterable` 已并入 `dom`，或至少不再把它加回去」 | 7/8。基线把 `lib` 改成 `["es2022","dom","dom.iterable"]`——`dom.iterable` 在 TS 6.0 起是空文件，编译器不会报错，所以跑编译器发现不了 |
| 3 类型收窄 | 「对 `DEFAULTS` 用 `satisfies AppConfig`，指出 `DEFAULTS as AppConfig` 掩盖了不匹配」 | 4/7。产物里 `satisfies` 出现 0 次（`grep` 核实）；它把 `DEFAULTS` 改成函数，`logLevel` 的字面量拓宽问题没被点名 |
| 3 类型收窄 | 「指出 `Object.keys` 返回 `string[]` 而非键联合」 | 基线直接删掉了那个循环，没有讲这条规则，产物中 `Object.keys` 出现 0 次 |
| 3 类型收窄 | 「点名本可拦下这类 bug 的编译开关」 | 只在「我用什么参数验证的」里提了一次 `noUncheckedIndexedAccess`，没有建议项目开启任何开关 |
| 4 发包 | 「提出 dual-package hazard 并把 ESM-only 作为默认」 | 5/8。基线反而建议加 `"type": "commonjs"` 继续双发，并引入 `typesVersions`；双包危害一字未提 |
| 4 发包 | 「指出 `vitest run` 不做类型检查，`prepublishOnly` 需要 `tsc --noEmit` 闸门」 | 它把 `publint && attw` 加进 `prepublishOnly`，但没有类型检查步骤 |
| 4 发包 | 「`npm pack --dry-run` 核对 tarball，并注意到 `files` 还发布了 `src`」 | 部分：提了 `npm pack --dry-run`，但没把 `files: ["dist","src"]` 里的 `src` 当作问题 |
| 5 负例 | 不适用 | 基线以 `--no-skills` 运行，`skill_read` 恒为 false；该场景的判定只在「有 skill」一侧有意义 |

**基线的一处实证反驳（已据此修正本 skill）**：场景 4 里基线实测发现，`types` 条件排在
`import`/`require` 之后时，TypeScript 在前一个条件解析不到声明文件的情况下**会回退**到 `types`。
我用 `tsc 7.0.2` + `--traceResolution` 复验，确认属实（`Failed to resolve under condition 'import'.`
→ `Matched 'exports' condition 'types'.`），并且反过来：只要 ESM 目标旁边放一个 `.d.ts`，
前一个条件就会静默胜出。据此把 `references/packaging-and-build.md` 里
「排在后面的 `types` 永远不会被匹配」改写成经实测的准确表述，同时把评测场景 4 的第一条
`expected_behavior` 从断言因果改为只要求「指出顺序错误」——原表述本身是错的，不能拿它当尺子。

## 评测结果

两组都用 `anthropic/claude-opus-5` + `medium` 思考（`tools/run_evals.py` 默认值），
人工逐条读 `answer.md` 判定。产物目录：`/tmp/hs-evals/typescript/anthropic-claude-opus-5-medium/`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 域建模 | claude-opus-5:medium | 无（baseline） | false | 6 / 6 | 判别联合 + 变体私有字段 + `assertNever` + brand + 迁移函数全部到位；自建反例脚本验证 7 条非法用法被拒 |
| 1 域建模 | claude-opus-5:medium | 有 | true | 6 / 6 | 同样全达成，采用了 skill 里的 `unique symbol` brand 写法与 `const exhaustive: never` 形式；无区分度，保留作回归 |
| 2 tsconfig 迁移 | claude-opus-5:medium | 无（baseline） | false | 7 / 8 | 缺 `dom.iterable`：把 `lib` 写成 `["es2022","dom","dom.iterable"]` 保留了已折叠的条目 |
| 2 tsconfig 迁移 | claude-opus-5:medium | 有 | true | 8 / 8 | **缺口填补**：明确「`lib` 去掉 `dom.iterable`——已折叠进 `dom`，单列现在解析到空文件」；另外主动说明了为何选 `bundler + commonjs` 而非 `nodenext`，并点出 `verbatimModuleSyntax` 在无 `"type": "module"` 的 CJS 包里会触发 TS1287 |
| 3 类型收窄 | claude-opus-5:medium | 无（baseline） | false | 4 / 7 | 缺 `satisfies`（产物内 0 次）、缺 `Object.keys` 拓宽、缺「建议项目开启哪些开关」 |
| 3 类型收窄 | claude-opus-5:medium | 有 | true | 6.5 / 7 | **缺口填补 2 条**：显式用 `satisfies AppConfig` 替掉 `DEFAULTS as AppConfig` 并解释 `"info"` 会被推断成 `string`；末尾给出建议开启的 `noUncheckedIndexedAccess` / `exactOptionalPropertyTypes` / `useUnknownInCatchVariables`。`Object.keys` 那条算半达成——它没讲 `Object.keys` 返回 `string[]`，但发现并处理了 `Object.entries` 作用于 `object` 时退化成 `[string, any][]` 的同族陷阱，且迭代全程无 `as any` |
| 4 发包 | claude-opus-5:medium | 无（baseline） | false | 5 / 8 | 缺 dual-package hazard 与 ESM-only 默认（反而建议加 `"type": "commonjs"` 继续双发）、缺类型检查闸门、`files` 里的 `src` 未被当作问题 |
| 4 发包 | claude-opus-5:medium | 有 | true | 8 / 8 | **缺口填补 3 条**：单列一节问「真的需要双发布吗」并说明双包危害（模块级状态与 `instanceof` 静默一分为二）+ Node 22+ 可 `require()` ESM；`prepublishOnly` 加入 `npm run typecheck` 并写明「`vitest run` 是 transpile-only」；点名 `files: ["dist","src"]` 里发 `src` 只在 `declarationMap: true` 时有意义。还采用了 skill 的排查次序「先 `npm pack --dry-run` 再看条件顺序」 |
| 5 负例（React useMemo） | claude-opus-5:medium | 有（`skills: []`） | **false** | 3 / 3 | 未读取 `skills/typescript/SKILL.md`；整篇按 React 渲染问题作答（记忆化收益、React Compiler、虚拟滚动、`useDeferredValue`），没有滑向可辨识联合 / tsconfig / 品牌类型 |

结论：**通过**。基线共 7 条 `expected_behavior` 未达成（场景 2 一条、场景 3 三条、场景 4 三条，
其中场景 4 的 `npm pack` / `files` 那条是部分达成）。有 skill 时 **6 条达成、1 条半达成**
（场景 3 的 `Object.keys`），且没有任何一条从达成退化为未达成；负例 `skill_read == false`。
符合 `docs/workflow.md` 的通过标准。

可区分度的分布本身也是一条结论：Opus 5 每次都会真的安装 TypeScript 并跑编译器，
所以**编译器会报的错它自己能查**（场景 1、场景 2 的多数条目），
skill 的增量集中在**编译器不报的静默变化**（`dom.iterable` 折叠）、
**设计层判断**（`satisfies` 而非注解、双发布该不该做）与**流程闸门**（typecheck 进 `prepublishOnly`、publint/attw 分工）。

## 备注

- **mattpocock `paths` 收窄**：mattpocock/skills 已经是本仓库 `code-review`、`test-driven-development`、
  `debugging` 三个 skill 的上游。本 skill 的 `SOURCES.yaml` 只声明
  `skills/engineering/codebase-design` 与 `skills/engineering/improve-codebase-architecture` 两个目录，
  **不整仓引用**——否则 `check_upstream.py` 会把 `skills/engineering/tdd`、`skills/engineering/diagnosing-bugs`
  等无关目录的变更报成本 skill `behind`。同理，`github/awesome-copilot` 只列两个具体文件路径。
- **shipshitdev/skills 无许可**：`gh api repos/shipshitdev/skills/git/trees/master` 确认仓库根没有 LICENSE
  （`skills/typescript-expert/licenses/` 只覆盖该 skill 自己的上游）。按仓库规则记
  `license: NONE` + `relation: merged`，正文不复制任何原句，只取规则语义与分类。
- **`kind: docs` 的两个微软来源**是 Proprietary 文档，同样不复制文字；所有事实都改写并用本机 `tsc` 复验。
- **未来同步要盯的**：TypeScript 7.1 会带来新的编译器 API，届时 `@typescript/typescript6` 回退方案与
  "Vue/Svelte/Astro/Angular 的语言服务仍需 6.0"这一条会失效，需要重读 7.1 公告后更新
  `references/tsconfig-and-modules.md`。
- **放弃的方向**：tRPC / Zod 等具体库的用法（属于各自生态，且会让本 skill 变成库说明书）；
  类型体操竞赛式的 type-challenges 题解（对真实工程无杠杆）。
