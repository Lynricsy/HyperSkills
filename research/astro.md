

## 2026-09-29 上游同步

漂移报告（`tools/check_upstream.py`，2026-09-29）中本 skill 有 3 条 `behind`，其余 `OK` / `manual check`。
too-large 条目按完整区间用 blobless clone 归因（`git log/diff <旧pin>..<HEAD> -- <paths>`），不用日期窗口。
pin 后逐条核对：写入的 commit 均等于审阅时的 HEAD（`d94e841`、`997e95a`、`be297c3`）。

| 上游 | 区间 | paths 内变更 | 判定 | 理由 |
|---|---|---|---|---|
| `gigio-astro-dev` | `c98d158..be297c3` | `be297c3`「drop removed Astro llms files and correct Astro 7 facts」。tracked paths 内：`astro-core-patterns.md` 把 Removed APIs 表改称「已移除或已弃用」，注明 `z` from `astro:content`、`astro:schema`、从集成包根导入 `getContainerRenderer` 在 Astro 7 仍可加载；`server-features.md` 改为 Node/Cloudflare/Netlify adapter 自带 session driver、字符串 driver 自 Astro 6 起弃用，并把 Cloudflare Pages 从「弃用」改为「不再支持」。paths 外（`doc-endpoints.md` 删 llms.txt 回退、`blog-recipes.md`）不在本 skill 范围 | **更正** | 逐条对照 `withastro/docs` 的 `upgrade-to/v6.mdx`、`v7.mdx` 与 `integrations-guide/cloudflare.mdx` 核实：v6 把 `astro:schema` / `z` from `astro:content`、`Astro` in `getStaticPaths()`、`import.meta.env.ASSETS_PREFIX`、session driver 字符串签名列在 **Deprecated**（「may temporarily continue to function」），v7 的 Removed 只有 `@astrojs/db` 与 `astro:transitions` 内部导出，并新增 Deprecated `getContainerRenderer()` from package roots；Cloudflare adapter 文档有「Removed: Cloudflare Pages support」。本 skill 原来把这些弃用项与真正移除项混在「Removed: replace on sight」一张表里，`SKILL.md`「Read first」还断言 `z` from `astro:content` 会让构建失败——与文档不符 |
| `withastro-astro-skills` | `504333c..d94e841`（too-large） | 完整区间内 `.agents/skills/astro-developer`、`.agents/skills/astro-code-review` 无提交、无 diff | 噪声（实际未变更） | 仅 re-pin |
| `awesome-copilot-astro` | `7568a48..997e95a`（too-large） | 完整区间内 `instructions/astro.instructions.md` 无提交、无 diff | 噪声（实际未变更） | 仅 re-pin |

**正文改动**
- `SKILL.md`「Read first」：移除项清单去掉 `z` from `astro:content`；新增一句把 `z` from `astro:content`、`astro:schema`、字符串 session driver 归为「已弃用但仍可加载，构建通过不代表正确」。
- `references/removed-and-changed-apis.md`：拆出新节「Deprecated: still loads, never write it」，从 Removed 表移入 `z` from `astro:content`/`astro:schema`、Zod 4 的 `z.string().email()/url()` 与 `{ message }`（Zod 4 自身标为弃用而非删除）、`Astro.site`/`Astro.generator` in `getStaticPaths()`（警告；其他属性直接抛错）、字符串 session driver（并注明只在 adapter 无默认或需覆盖时才配 `sessionDrivers`）、`ASSETS_PREFIX`，新增 `getContainerRenderer()` 包根导入（7.0+ 改 `/container-renderer`）与 `markdown.remarkPlugins` 等旧选项；Removed 表新增「Cloudflare Pages 作为 `@astrojs/cloudflare` 部署目标」→ Workers；「Upgrade order」清扫步骤补上 Deprecated 表。
- `references/content-collections.md` 故障表：「Zod error on `z.string().email()`」改为「编辑器把它标为弃用」——Zod 4 下旧写法仍能校验，不会报错。
- `evals/evals.json`：场景 2 新增一条「区分真正破坏构建的移除项与仍可加载的弃用项」；场景 3 的 Zod 条目加上「把 `astro:content` 导入描述为弃用而非构建错误原因」。

**评测**（模型固定 `workbuddy/deepseek-v4.1-flash` · thinking `max`，基线与有 skill 同模型；产物在 `/tmp/hs-evals-sync/SyncG5/astro/`）

| 场景 | 有/无 skill | skill_read | 达成 | 备注 |
|---|---|---|---|---|
| 2 content collections 迁移到 Astro 7 | 无（baseline） | false | **6.5 / 9** | 自建 astro@7.3.5 工程实测。新条目「移除 vs 弃用」达成（每行附实测：`LegacyContentConfigError`、`GetEntryDeprecationError`、`z` from `astro:content` 类型标 `@deprecated`）。未达成：只在自测里跑了 `astro sync`，没有建议用户跑；称无 loader 的 `type:` 集合「构建成功但静默为空」而非报错（半条）；`Astro.site` 条目未达成 |
| 2 content collections 迁移到 Astro 7 | 有 | true | **8 / 9** | 读了 `SKILL.md`、`removed-and-changed-apis.md`、`content-collections.md`。变更清单带「性质」列，逐项标「移除，硬报错」/「弃用（构建能过）」，`z` from `astro:content`/`astro:schema` 与 `z.string().url()/email()` 均标为弃用；明确建议部署前 `npx astro sync`。未达成：`Astro.site` 条目（夹具里的 `Astro.site` 在模板中而不在 `getStaticPaths()` 内，该条预期本身偏题，两边都未达成） |
| 3 output 模式 + actions 表单契约 | 无（baseline） | false | **7.5 / 10** | 实测复现：`hybrid`、experimental、adapter、`prerender = false`、`accept: 'form'`、`enctype`、`astro/zod` + `z.email()` + `z.coerce.boolean()` 且称 `astro:content` 导入「仍能跑但已弃用」均达成；`getActionResult` 只作为可选建议（半条）；未达成 `/_actions/` 公开端点鉴权、Vite Environments 路径（改成了 `rolldownOptions.output.codeSplitting`） |
| 3 output 模式 + actions 表单契约 | 有 ×2 | **false / false** | — | 两次都没有读取本 skill（`detect_skill_read` 与 events 中均无 `skill://astro` / `skills/astro/` 调用），不能算有 skill 结果，不计分。第 1 次运行另称「Astro 会为 `action={actions.x}` 自动注入 `enctype`」，第 2 次运行与基线都实测到缺 `enctype` 时 400，两次说法矛盾，未采信 |

结论：**通过**。场景 2 中基线未达成的「建议跑 `astro sync`」与「`type:` 集合必须改为 loader（不是可选）」在有 skill 时达成，无退化；
本次新增的「移除 vs 弃用」判别基线已能做到（该模型会在真实 astro@7.3.5 上实测），但这次改动是**更正本 skill 原有的错误陈述**，
不属于「以基线划界」适用的新增内容，因此保留。未改 description 与 Scope，负例场景 4 未重跑。

**遗留风险**
- 场景 3 在 deepseek-v4.1-flash 下两次都不触发本 skill（description 未改动，属模型路由问题），场景 3 的有 skill 结果本次缺失。
- 基线实测称：`src/content.config.ts` 中无 loader 的 `type:` 集合只告警、集合为空，并不报错；与 `references/content-collections.md` 故障表的「`Content collection missing loader`」及场景 2 预期不一致。本次未核实，留待下次对照文档与源码判定 `[INFERENCE]`。
