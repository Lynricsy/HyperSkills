# 主题路线图

粒度：**一个生态 / 一类事情 = 一个 skill**。下列种子上游来自建设期的领域调研，
**执行每个批次前必须按 `docs/workflow.md` Phase A 重新复核** stars、`pushed_at`、许可——
这些数据会随时间变化，路线图只负责记住「往哪儿找」，不负责记住「当时是什么样」。

星标数与推送时间标注的是调研当时（2026-09）的观测值，仅用于判断量级，不作为合入依据。

## Batch 1（已完成）

`apple`、`flutter`、`office`、`frontend-design`、`react`、`skill-authoring`、
`test-driven-development`、`debugging`、`code-review`。

## Batch 2 — 平台与语言

| skill | category | 种子上游 | 备注 |
|---|---|---|---|
| `android` | platform | android/skills（7.3k★）、Kotlin/kotlin-agent-skills（1k★）、Compose 相关 | 与 `apple` 对称；Compose 与 View 体系都要覆盖 |
| `react-native` | platform | expo/skills（2.5k★）、vercel-labs `vercel-react-native-skills`、react-native-community/skills | 与 `react` 划清边界：RN 专属 API 归此处 |
| `typescript` | framework | mattpocock/skills（258k★）：`domain-modeling`、`codebase-design`、`setup-ts-deep-modules` 等 | 类型层建模为主，不重复 `react` 的组件规则 |
| `go` | framework | samber/cc-skills-golang（3.2k★）、spf13/go-skills | |
| `python` | framework | getsentry/skills `languages/python.md` 部分 | 上游覆盖偏薄，需补搜 |
| `java-spring` | framework | 需补搜 | 尚未找到合格上游 |
| `rust` | framework | **暂缓** | 调研时无合格上游（无活跃、高认可度的 Rust agent skill） |

## Batch 3 — 后端与数据

| skill | category | 种子上游 |
|---|---|---|
| `postgres` | framework | supabase/agent-skills `supabase-postgres-best-practices`（2.6k★）、neondatabase/agent-skills、prisma/skills（9 个） |
| `supabase` | framework | supabase/agent-skills |
| `firebase` | framework | firebase/agent-skills（439★） |
| `django` | framework | 需补搜 |
| `fastapi` | framework | 需补搜 |
| `graphql` | framework | 需补搜 |

## Batch 4 — 云与基础设施

| skill | category | 种子上游 | 许可注意 |
|---|---|---|---|
| `terraform` | framework | hashicorp/agent-skills（864★） | **MPL-2.0 文件级 copyleft**：合入的文件必须保留 MPL 头 |
| `containers` | platform | getsentry `infrastructure/`、microsoft `azure-kubernetes` | Docker + Kubernetes 合为一个 skill |
| `github-actions` | task | getsentry `gha-security-review` | |
| `azure` | platform | microsoft/azure-skills（1.5k★） | |
| `gcp` | platform | google/skills（~20k★） | |
| `aws` | platform | 需补搜 | |

## Batch 5 — 任务类型

| skill | category | 种子上游 |
|---|---|---|
| `security-review` | task | getsentry/skills（988★）——本领域最佳单 skill 模板 |
| `web-testing` | task | microsoft/playwright-cli、anthropics `webapp-testing`、vercel-labs/agent-browser、addyosmani `browser-testing-with-devtools` |
| `planning` | task | obra/superpowers `brainstorming`、`writing-plans`、`executing-plans` |
| `git-workflow` | task | mattpocock `resolving-merge-conflicts`、`git-guardrails`；obra `finishing-a-development-branch`、`using-git-worktrees` |
| `mcp-server` | task | anthropics `mcp-builder` |
| `technical-writing` | task | mattpocock `edit-article`、`teach` |
| `data-analysis` | task | 需补搜 |

## 用户明确暂缓

| 主题 | 上游 | 暂缓原因 |
|---|---|---|
| `vue` | vuejs-ai/skills（2.8k★，2026-05-30） | 用户暂不需要 |
| `google-workspace` | googleworkspace/cli（30.8k★，Apache-2.0，可近原样合入） | 用户暂不需要 |

## 已排除主题（写明原因，避免反复讨论）

| 类别 | 例子 | 排除原因 |
|---|---|---|
| Anthropic 内部 / 营销类 | `brand-guidelines`、`internal-comms`、`academy-guide`、`discernment-nudge` | 与本仓库的工程定位无关，且多为专有许可 |
| SaaS 产品包装类 | Lark、HeyGen、RunComfy 等 | 本质是某个产品的 API 说明书，随产品变动腐化，且不构成通用工程能力 |
| joke skill | `caveman` | 无工程价值 |
| 营销文案类 | 各类 copywriting skill | 与仓库范围（软件工程）不符 |

## 新增主题的判据

一个主题值得单独立 skill，当且仅当：

1. 它对应一次真实任务的完整上下文——不需要同时加载另一个同级 skill 才能干活；
2. 至少存在 3 个活跃（6 个月内有推送）、评审量表总分 ≥8 的上游可供合成；
3. 它不是既有 skill 的子集。`swiftui` 属于 `apple`，`tailwind` 属于 `react` / `frontend-design`，
   都不单独立项。
