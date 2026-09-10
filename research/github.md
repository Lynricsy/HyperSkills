# github 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`"github actions" agent skill SKILL.md repository workflow hardening 2026`、
    `"gh pr" claude agent skill "SKILL.md" github pull request issue triage repository site:github.com`
  - `github/awesome-copilot` 全树枚举（`gh api repos/github/awesome-copilot/git/trees/main?recursive=1`），
    在 `skills/` 与 `instructions/` 两侧按 `github|pr-|issue|release|dependabot|gh-|actions` 过滤
  - `getsentry/skills`、`coderabbitai/skills`、`mcollina/skills`、`SethGammon/Citadel`、
    `alpha-omega-security/scrutineer`、`openai/skills`、`warpdotdev/oz-for-oss` 全树枚举
  - 官方组织仓库：`github/docs`（docs.github.com 的源）、`cli/cli`、`actions/starter-workflows`、
    `zizmorcore/zizmor`、`ossf/scorecard`、`step-security/secure-repo`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- `gh auth status`：已登录（account `Lynricsy`，scopes `gist, read:org, repo, workflow`），全程用登录态 API，未触发限流。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | github/awesome-copilot `skills/github-actions-hardening`（含 5 个 references） | https://github.com/github/awesome-copilot | 38860 | 2026-09-10 | MIT | Actions 加固 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | GitHub 官方仓库。触发器信任矩阵、注入 sink 清单、`env:` 安全模式、`permissions` 配方、SHA pin、OIDC 全都可执行；抽查 3 条（`pull_request` 派生 fork 只读无 secrets、`env:` 中转、第三方动作 SHA pin）与 docs.github.com 一致 |
| 2 | github/awesome-copilot `skills/github-actions-efficiency`（含 references） | 同上 | 38860 | 2026-09-10 | MIT | Actions 效率 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 「先测量再改」的护栏（不得削减必需校验、不得无理由降并行）比一般缓存教程有价值；`gh run list/--log-failed` 取证路径明确 |
| 3 | github/awesome-copilot `skills/github-actions-runtime-upgrade-conventions` | 同上 | 38860 | 2026-09-10 | MIT | 动作版本升级 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 「一次一个动作一提交」「解析到 SHA 再 pin，注释写版本」「与 Dependabot 的分工」三条可执行 |
| 4 | github/awesome-copilot `instructions/github-actions-ci-cd-best-practices.instructions.md` | 同上 | 38860 | 2026-09-10 | MIT | Actions 全景 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（少量） | 607 行大半是模型已知常识与部署策略科普；只取 `actions/cache/restore` + `lookup-only: true` 调试缓存未命中、`fetch-depth`、`timeout-minutes`、environment 审批这几条 |
| 5 | github/awesome-copilot `skills/github-issues`（含 references/labels、search、sub-issues） | 同上 | 38860 | 2026-09-10 | MIT | Issue 管理 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `gh issue create` 不支持 `--type`（须走 `gh api`）、`-f 'labels[]=bug'` 在 zsh 下必须整体加引号、issue type 优先于等价标签——三条都是静默失败类知识 |
| 6 | github/awesome-copilot `skills/dependabot` | 同上 | 38860 | 2026-09-10 | MIT | 依赖更新 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `directory` 单数不支持 glob、`directories` 复数才支持；单文件约束；`github-actions` ecosystem 覆盖 workflow 固定 |
| 7 | github/awesome-copilot `skills/github-release` | 同上 | 38860 | 2026-09-10 | MIT | Releases | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 「不要用 `gh release list` 判断上一版，因为 Releases 是 tag 之上的可选层」+ `--sort=-version:refname` 语义排序 + 本地 tag 未推送的检查，都是真陷阱 |
| 8 | github/awesome-copilot `skills/repo-standardizer` | 同上 | 38860 | 2026-09-10 | MIT | 仓库治理 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（部分） | 治理审计命令齐全（`gh api .../rulesets`、`gh label list`、org membership 预检）；但 489 行里大半是 emoji 等级标签这类项目专属主张，正文只取审计与幂等 upsert 语义 |
| 9 | github/docs（docs.github.com 的源仓库） | https://github.com/github/docs | 20806 | 2026-09-10 | CC-BY-4.0 | 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 唯一权威。`securely-using-pull_request_target`、`secure-use`、`about-rulesets`、`about-code-owners`、`linking-a-pull-request-to-an-issue`、`immutable-releases` 六篇提供了所有社区上游都缺的当代事实 |
| 10 | getsentry/skills `skills/gha-security-review` | https://github.com/getsentry/skills | 989 | 2026-09-07 | Apache-2.0 | Actions 加固 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 唯一把「外部攻击者威胁模型」写成硬门的上游：五要素证据（入口/载荷/执行/影响/PoC），以及「安全模式不得上报」表，直接治好泛化告警 |
| 11 | getsentry/skills `skills/pr-writer` | 同上 | 989 | 2026-09-07 | Apache-2.0 | PR 描述 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | PR 正文是评审者封面信而非变更日志；禁止默认 Summary/Changes/Test Plan 三段；`Fixes` 关闭 vs 仅引用的区分 |
| 12 | getsentry/skills `skills/iterate-pr` | 同上 | 989 | 2026-09-07 | Apache-2.0 | PR 迭代 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 「等哪些 check、不等哪些」的区分（不等 approval / draft / REVIEW_REQUIRED / Codecov）是本类任务最常见的死等来源 |
| 13 | getsentry/skills `skills/pr-link-issue`、`skills/gh-review-requests` | 同上 | 989 | 2026-09-07 | Apache-2.0 | PR/评审队列 | 2 | 3 | 2 | 3 | 2 | 12 | INCLUDE（部分） | Sentry/Linear 专属流程剔除；只取「先读 PR body 再 append，不覆盖」和 `gh api notifications` + `requested_reviewers` + `orgs/{org}/teams/{slug}/members` 的评审队列取数路径 |
| 14 | zizmorcore/zizmor（`docs/usage.md`、`docs/audits.md`） | https://github.com/zizmorcore/zizmor | 6475 | 2026-09-09 | MIT | 静态审计工具 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 工具本身的权威文档：exit code 11–14 表示「有发现」而非报错、`--no-exit-codes`、persona 三档、离线/在线模式由 `GH_TOKEN` 决定、`--fix`。这些错了就会把 CI 门写坏 |
| 15 | alpha-omega-security/scrutineer `skills/zizmor` | https://github.com/alpha-omega-security/scrutineer | 208 | 2026-09-10 | MIT | zizmor 结果解读 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | OpenSSF Alpha-Omega 出品。「references 是评审指引，不是目标存在漏洞的证据」「不得把宽权限/可变 tag/`pull_request_target` 本身当成可利用漏洞」正是 scanner 结果的正确用法 |
| 16 | coderabbitai/skills `skills/autofix`（+ `skills/autofix/github.md`） | https://github.com/coderabbitai/skills | 171 | 2026-09-08 | MIT | 评审线程 | 2 | 3 | 2 | 3 | 2 | 12 | INCLUDE（部分） | 只取 `reviewThreads` GraphQL 游标分页与 `isResolved`/`isOutdated` 取数骨架；CodeRabbit 产品语境剔除 |
| 17 | warpdotdev/oz-for-oss `.agents/skills/{triage-issue,dedupe-issue,bootstrap-issue-config}` | https://github.com/warpdotdev/oz-for-oss | 307 | 2026-09-09 | MIT | Issue 分诊 | 2 | 3 | 2 | 3 | 2 | 12 | INCLUDE（部分） | 分诊输出保守化（证据驱动、`duplicate_of` 与 `follow_up_question` 互斥、只在特定条件下关闭 issue）；issue forms 引导（`bootstrap-issue-config`）与本 skill 的模板一节对齐 |
| 18 | github/awesome-copilot `skills/copilot-pr-autopilot`（含 `references/api-quirks.md`） | 同上 | 38860 | 2026-09-10 | MIT | Copilot 评审循环 | 3 | 3 | 3 | 2 | 2 | 13 | INCLUDE（仅 api-quirks） | 主线是 PowerShell 脚本驱动的 Copilot 专用循环，与本 skill 边界不合；但 `api-quirks.md` 里 `latestReviews` 陈旧投影、`gh api graphql -F` 会做类型推断（`String!` 必须用 `-f`）、`isOutdated ≠ isResolved` 三条是通用且已验证的 |
| 19 | SethGammon/Citadel `skills/{triage,pr-watch}` | https://github.com/SethGammon/Citadel | 921 | 2026-09-10 | MIT | Issue/PR 分诊 | 1 | 3 | 2 | 2 | 2 | 10 | MAYBE→部分合入 | 分诊分类法（type/severity/status 三维、needs-info 兜底）与循环熔断可用；但 `/marshal`、`.planning/`、`.claude/harness.json`、Windows `gh.exe` 硬编码路径全是产品耦合，且交叉引用其他 Citadel 命令，不可整体合入 |
| 20 | mcollina/skills `skills/octocat` | https://github.com/mcollina/skills | 1913 | 2026-08-17 | MIT | git+GitHub 混合 | 2 | 2 | 2 | 2 | 2 | 10 | MAYBE→部分合入 | 一半是本地 git（交互式 rebase、submodule、bisect），按边界划走。只取 `--body-file` 避免换行转义、`gh pr checks --watch` 后主动修、`gh help <command>` 先验证不熟的子命令三条 |
| 21 | openai/skills `skills/.curated/{gh-address-comments,gh-fix-ci}` | https://github.com/openai/skills | 26841 | 2026-09-08 | NONE（API `license: null`，仓库无 LICENSE 文件） | PR 评论/CI | 2 | 3 | 2 | 3 | 0 | 10 | INCLUDE（部分） | `gh pr checks --json` 字段会漂移、被拒时用 `gh` 回报的可用字段重试；`detailsUrl` 非 Actions 时只报 URL 不追（其他 CI 平台边界）。按无许可规则合入，不复制原句 |
| 22 | k1LoW/gh-pr-reviews `skills/triage-pr-reviews` | https://github.com/k1LoW/gh-pr-reviews | 19 | 2026-09-09 | MIT | 评审评论分诊 | 1 | 3 | 2 | 3 | 2 | 11 | MAYBE→部分合入 | 绑定作者自己的 `gh pr-reviews` 扩展，不作为默认路径。只作 `pulls/{n}/comments/{id}/replies` 端点与「同意/部分同意/不同意」分类的交叉校验 |
| 23 | cli/cli（`gh` 本体） | https://github.com/cli/cli | 46221 | 2026-09-10 | MIT | CLI 参数面 | 3 | 3 | 3 | 3 | 2 | 14 | reference | 正文里每个 `gh` 子命令的 flag 都用本机 `gh <cmd> --help` 核过（例：`gh pr review` 只有 `-a/-b/-F/-c/-r`）。未复制任何文本，故 reference |
| 24 | actions/starter-workflows | https://github.com/actions/starter-workflows | 12048 | 2026-08-03 | MIT（API 报 NOASSERTION；实读 LICENSE 为 MIT + 商标条款） | 官方模板 | 3 | 1 | 2 | 3 | 2 | 11 | reference | 只用来核对官方脚手架 workflow 的默认形态（`permissions`、缓存、matrix 写法），正文事实一律从 docs.github.com 取证，未复制模板文件 |
| 25 | ossf/scorecard | https://github.com/ossf/scorecard | 5685 | 2026-09-10 | Apache-2.0 | 供应链检查项 | 2 | 3 | 3 | 3 | 2 | 13 | reference | docs.github.com 官方指向它的 `Dangerous-Workflow` / `Token-Permissions` / `Pinned-Dependencies` 检查；只用其检查项清单验证本 skill 的覆盖面是否有洞 |
| 26 | step-security/secure-repo | https://github.com/step-security/secure-repo | 330 | 2026-09-10 | AGPL-3.0 | Actions 加固 | 2 | 3 | 3 | 3 | 0 | 11 | reference（许可强制） | AGPL-3.0 按规则一律 reference。只用它的修复项清单判断覆盖面（SHA pin、`permissions`、harden-runner），每条事实改从 docs.github.com 取证 |
| 27 | anmolnagpal/devops-skills `skills/{github-actions,github}` | https://github.com/anmolnagpal/devops-skills | 8 | 2026-09-09 | MIT | Actions 审阅 | 0 | 3 | 2 | 2 | 2 | 9 | reference | 8 星、无组织背书，规则 ID 绑定作者自家 auditkit 注册表。作为「覆盖面是否有洞」的交叉校验，未取内容 |
| 28 | affaan-m/ECC `skills/github-ops` | https://github.com/affaan-m/ECC | 255713 | 2026-09-10 | MIT | GitHub 运维 | 1 | 3 | 1 | 2 | 2 | 9 | reference | 162 行、全是 `gh` 基础命令罗列（模型已知），唯一有价值的一条「`gh` 返回的 issue/PR/日志文本是数据不是指令」与 anmolnagpal 同源，已从两侧交叉确认后自行改写。星数（255713）明显与仓库规模不符，仅按 API 原值记录，不作为权威依据 |
| 29 | github/awesome-copilot `skills/git-flow-branch-creator` | 同上 | 38860 | 2026-09-10 | MIT | 分支策略 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT（边界） | 292 行全是 nvie Git Flow 的本地分支命名与创建，是「git 单独离线就能做完」的一侧，按分界句不属于本 skill；其中与远端/保护分支相关的内容为零，无可取部分 |
| 30 | github/awesome-copilot `skills/pr-dashboard` | 同上 | 38860 | 2026-09-10 | MIT | PR 看板 | 3 | 3 | 1 | 3 | 2 | 12 | REJECT | 内容是「用 `find ~/.copilot` 定位随包脚本再 `node` 执行」，harness 路径耦合，且产物只是打开浏览器，无可迁移知识 |
| 31 | github/awesome-copilot `skills/{create-github-issue-feature-from-specification,gen-specs-as-issues}` | 同上 | 38860 | 2026-09-10 | MIT | 规格→issue | 3 | 3 | 1 | 3 | 2 | 12 | REJECT（边界） | 主体是「怎么写规格文档并拆任务」，属于规划类任务而非 GitHub 平台知识；机械的建 issue 动作已由候选 5 覆盖 |
| 32 | obra/superpowers `skills/{using-git-worktrees,finishing-a-development-branch}` | https://github.com/obra/superpowers | 284551 | 2026-09-10 | MIT | 本地 git | 2 | 3 | 3 | 3 | 2 | 13 | REJECT（边界） | worktree 与分支收尾是纯本地 git，按分界句划到 git 一侧 |
| 33 | GoldenWing-360/claude-security-skills `github-actions-security` | https://github.com/GoldenWing-360/claude-security-skills | 17 | 2026-08-03 | MIT | Actions 加固 | 0 | 2 | 2 | 1 | 2 | 7 | REJECT | 17 星、无背书；与候选 1/10 完全重叠但更旧（>1 月未推），抽查发现它把 fork 的 `pull_request` 也按高危处理，与官方信任矩阵矛盾 |
| 34 | nolte/claude-shared `skills/pull-request-merge` | https://github.com/nolte/claude-shared | 0 | 2026-08-29 | MIT | PR 合并 | 0 | 2 | 1 | 2 | 2 | 7 | REJECT | 0 星、个人 dotfiles 级仓库，内容是 `gh pr merge` 三行包装 |
| 35 | trailofbits/skills | https://github.com/trailofbits/skills | 7031 | 2026-09-09 | CC-BY-SA-4.0 | 安全审计 | 2 | 3 | 3 | 3 | 1 | 12 | REJECT（无相关内容） | 全树枚举确认没有 Actions / PR / Issue / 仓库治理相关的 skill，`.github/` 下只有它自己的 CI。与本 skill 无交集 |
| 36 | googleapis/release-please | https://github.com/googleapis/release-please | 7474 | 2026-09-03 | Apache-2.0 | 发布自动化 | 2 | 3 | 3 | 3 | 2 | 13 | REJECT（范围） | 是一个具体的发布机器人产品，不是 GitHub 平台知识；写进来等于给某个工具做说明书（标准第 3 节「不罗列多个可选库」） |

## 深度审查

### github/awesome-copilot（候选 1–8、18、29–31）

GitHub 官方仓库，418 个 `skills/*/SKILL.md` + 193 个 `instructions/*.instructions.md`，今日仍在推送。
frontmatter 只有 `name` + `description`（`copilot-pr-autopilot` 例外，`description` 写成营销文案），
无 agent 专属字段，剥离成本低。

结构上分两类：`skills/github-actions-hardening` 与 `skills/github-actions-efficiency`
是「瘦入口 + references 按需加载」的现代形态，正文只留路由与判据，细节全在 references——
这与本仓库标准第 2 节的 `## Topic router` 完全同构，是本 skill 的骨架来源。
另一类（`instructions/github-actions-ci-cd-best-practices`、`repo-standardizer`、`dependabot`、
`github-release`）是几百行的单文件长文，价值密度差别很大：`dependabot` 与 `github-release`
几乎每段都是可执行事实，`instructions/*` 有一半是「Your Mission / Deeper Dive」式的
Copilot 人格与部署策略科普，按标准第 3 节「不重复模型已知常识」大幅剔除。

`github-actions-hardening` 的 references 分工是 `triggers-and-privilege` / `injection` /
`permissions-and-tokens` / `supply-chain` / `report-format`，本 skill 的 references 沿用同一切分，
但合并成三个文件（触发器与权限合并到 `actions-hardening.md`，注入独立成节），因为本 skill
还要放 PR / Issue / 治理三块，reference 数量必须收紧。

同波其他 skill 也把 awesome-copilot 当上游，`paths` 只列本 skill 实际读过的 11 个路径。

### getsentry/skills（候选 10–13）

Apache-2.0，989 星，7 天内推送。已是本仓库 `python`、`code-review` 等 skill 的上游，
`paths` 只列本 skill 用到的 5 个目录。

`gha-security-review` 与 awesome-copilot 的 `github-actions-hardening` 是本次最重要的一对：
两者都做 Actions 加固，但取向不同。前者是「审计员」——先钉死威胁模型（攻击者**无**写权限），
再要求每条发现给出五要素证据，并列出一张「安全模式不得上报」表；后者是「编写者」——
按 7 步扫一遍工作流并给 before/after 修复。本 skill 两者都要：编写时用后者的清单，
审计时用前者的证据门，因此 `## Workflows` 里分成 `write-workflow` 与 `audit-workflows` 两条。

`iterate-pr` 的价值集中在「等哪些 check」这一张表；它的 4 个 `uv run scripts/*.py`
是 Sentry 内部脚本（依赖 Sentry 的 review bot 名单），本 skill 不复制脚本，只把
`gh pr checks` / `gh run view --log-failed` 的回退路径与「不等 approval / draft /
REVIEW_REQUIRED / Codecov」的判据写进正文。

`pr-writer` 的 `metadata` 干净，正文是本次读到的 PR 描述规范里最克制的一份，
直接决定本 skill 的 `## Output format` 一节。

### github/docs（候选 9）

`license.spdx_id` = `CC-BY-4.0`（仓库 LICENSE 是 CC-BY-4.0 覆盖文档内容，代码部分 MIT），
按许可规则可 merged，`notes` 写署名。这一条是本次调研最关键的发现：**所有社区上游都落后于
官方当前行为**。具体：

1. `actions/checkout` 现在**默认拒绝**在 `pull_request_target` 里 checkout fork 的 PR head，
   必须显式设 `allow-unsafe-pr-checkout: true` 才能绕过（该 input 就是为了在评审与静态分析里
   显眼而这样命名的）。候选 1、10、14、15、26 全都还在教「不要 checkout PR head」而不知道
   这件事已经有了内建拦截与一个具名逃生口。
2. `pull_request_target` 触发的工作流对默认分支作用域的 cache 是**只读**的，保存会失败但
   步骤与 job 继续、只在日志里留 warning。
3 关闭关键字（`Closes #N` 等）**只有当 PR 指向仓库默认分支时才被解释**；指向其他分支时
   关键字被完全忽略，既不建链接、合并也不关 issue。这条没有任何一个社区上游提到。
4. CODEOWNERS 与 gitignore 的差异：`!` 取反、`[ ]` 字符区间都**不生效**；同一 pattern 写在
   两行只保留最后一个 owner；最后匹配的 pattern 胜出（所以更泛的 pattern 必须写在前面）；
   文件必须在 PR 的 base 分支上；owner 必须有 write 权限否则静默丢弃；draft PR 不请求 code owner。
5. rulesets 与 branch protection 并存且**聚合**，同一规则的不同版本取最严格者；无优先级概念；
   仓库/组织各 75 个上限；只读权限也能查看生效的 rulesets。
6. 不可变 release：tag 锁死到 commit、资产不可改删、自动生成 release attestation，
   且删掉仓库重建也不能复用旧 tag；官方建议的顺序是「先建 draft → 挂全资产 → 再发布」。

正文里凡与社区上游冲突的地方，一律以本仓库为准。

### zizmorcore/zizmor + alpha-omega-security/scrutineer（候选 14–15）

工具与工具的正确用法分别来自这两处。zizmor 官方文档给出参数面与退出码语义；
scrutineer 的 `skills/zizmor` 给出**结果解读纪律**：references 是评审指引不是漏洞证据、
不得把宽权限 / 可变 tag / `pull_request_target` / 自托管 runner / 单纯的插值本身当成
可利用漏洞、不得臆造仓库外的信任策略。这一节与 getsentry 的证据门互为印证，一并合入。

scrutineer 的 frontmatter 带 `scrutineer.*` 专属字段与 `compatibility`（指向 `./src`、
`./report.json` 等其编排器的工作区约定），全部剥离。

### 其余部分合入的上游（候选 16–22）

- `coderabbitai/skills`：`reviewThreads(first:100, after:$cursor)` 的游标分页骨架 +
  `isResolved` / `isOutdated` 字段选择。与候选 18 的 `latestReviews` 陈旧投影警告拼在一起，
  构成本 skill 里「取评审线程的唯一正确姿势」。
- `warpdotdev/oz-for-oss`：分诊结论保守化与 issue forms 的引导；它的 `triage_result.json`
  schema 与 Warp 支持流程（`warp:needs-support`）是产品耦合，剔除。
- `SethGammon/Citadel`：三维标签分类法与「同一失败重试 2 次后停」的熔断。
- `mcollina/skills`、`openai/skills`、`k1LoW/gh-pr-reviews`：各取 1–3 条前述具体事实。

`openai/skills` 全树无 LICENSE 文件、API `license: null`，按规则 `license: NONE`，
`notes` 写明未逐字复制。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 第一方 `actions/*` 用版本 tag 要不要报 | awesome-copilot：`actions/*` 风险较低但仍建议 SHA pin，`@main`/`@master` 一律 HIGH；getsentry：**不得**上报第一方 `actions/*` 的 tag 引用 | 分层：漏洞报告里第一方 tag 不算发现（getsentry 胜）；编写与加固基线里一律 SHA pin（awesome-copilot 胜）。正文把两者写成不同 workflow 的判据，而不是一条自相矛盾的规则 | docs.github.com `secure-use`：「Pinning an action to a full-length commit SHA is currently the only way to use an action as an immutable release」，同时承认 tag「more convenient and is widely used」；且官方现在提供仓库/组织级「要求 SHA pin」策略——说明这是策略选择而非普适漏洞 |
| 2 | `${{ }}` 出现在 `with:` 输入里是否安全 | getsentry：安全，`with:` 是字符串参数不经 shell；awesome-copilot：取决于该动作自己是否把输入插进 shell | awesome-copilot 胜 | `actions/github-script` 的 `script:` 本身就是一个 `with:` 输入，且会被当 JS 执行；官方 `secure-use` 的推荐修法之一正是「改用一个把 context 当参数接收的 action」，即安全性由被调用方决定 |
| 3 | `pull_request_target` + checkout PR head 的定性 | 所有社区上游：一律 CRITICAL / RCE | 保留 CRITICAL 定性，但正文必须同时写清：checkout 步骤本身不执行代码，漏洞由**随后运行被检出代码的那一步**完成；且 `actions/checkout` 现在默认就拦，需 `allow-unsafe-pr-checkout: true` 才能绕过 | docs.github.com `securely-using-pull_request_target`（官方 > 社区，且更新 > 更旧）。少了这两点，评审要么错报（只 checkout 不执行的 labeler）要么给出已经不成立的修复建议 |
| 4 | Issue 分类用标签还是 issue type | Citadel / ECC / oz-for-oss：`bug`/`feature`/`question` 标签体系；awesome-copilot `github-issues`：org 配了 issue types 就用 `type`，不要再打等价标签 | awesome-copilot 胜；正文写「有 issue type 用 type，没有才退回标签」 | GitHub 官方仓库主张，且 issue type 是 org 级规范元数据；两套并行会产出重复维度 |
| 5 | 建 issue 用 `gh issue create` 还是 `gh api` | ECC / Citadel：`gh issue create`；awesome-copilot：`gh api repos/{o}/{r}/issues`，因为 CLI 没有 `--type` | 按需要的字段分流：只要 title/body/label/assignee 用 `gh issue create`；要 issue type 或 REST 独有字段走 `gh api` | 本机 `gh issue create --help` 确认无 `--type`；给一条默认 + 一个逃生口，符合标准第 3 节 |
| 6 | 关联 issue 写 `Fixes #N` 就够了吗 | getsentry `pr-writer`：`Fixes` 关闭、`Refs` 仅链接；其余上游：直接写 `Fixes #N` | 都不完整。正文必须先判断 base 分支：**PR 不指向默认分支时关闭关键字被完全忽略**，此时改用 PR 侧栏手动 link 或在 issue 上留链接 | docs.github.com `linking-a-pull-request-to-an-issue`：「The special keywords … are interpreted only when the pull request targets the repository's default branch」 |
| 7 | 取 PR 评审状态用哪个 GraphQL 字段 | `copilot-pr-autopilot/api-quirks`：`latestReviews` 是有陈旧缓存的投影，必须用 `reviews(last:100)`；coderabbit：用 `reviewThreads` 分页 | 两者不冲突，按目的分流：判「有没有新评审」用 `reviews(last:100)`，逐条处理未解决意见用 `reviewThreads` 游标分页；两处都不用 `latestReviews` | api-quirks 是同一 GitHub 官方仓库内的实测记录（20+ 轮），且与「取当前状态」的语义一致 |
| 8 | zizmor 非零退出是不是失败 | scrutineer 的包装脚本用 `--no-exit-codes` 抹平；zizmor 文档：11–14 表示「有发现」，1/2/3 才是错误 | 正文写清 11–14 与 1/2/3 的区别，CI 门里按需选 `--no-exit-codes`；不把「有发现」当命令失败 | zizmor 官方 `docs/usage.md` 退出码表。把两者混同会让 CI 要么永绿要么永红 |
| 9 | 本地分支策略 / rebase / 提交粒度归谁 | `octocat`、`git-flow-branch-creator`、`superpowers` 的 worktree 与分支收尾都混在 GitHub 技能里 | 一律剔除，按分界句划到 git 一侧：能离线只靠 git 完成的不属于本 skill | 本波 contract 的硬性分界；也避免与将来的本地 git skill 重复 |
| 10 | 其他 CI 平台的失败要不要追 | `openai/skills` `gh-fix-ci`：`detailsUrl` 不是 Actions run 就只报 URL | 采纳，写成边界 | 与本 skill 的否定范围一致（不覆盖 GitLab CI / Jenkins / CircleCI） |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `awesome-copilot` | github/awesome-copilot（11 个路径） | merged | Actions 加固的 7 步骨架与信任矩阵、注入 sink 清单与 `env:` 修法、`permissions` 配方、效率审计护栏、动作版本升级纪律、Issue/label/issue-type 操作面、Dependabot 生态与 `directories` glob、Releases 的 tag-vs-Release 陷阱、治理审计命令、PR 评审线程的 API quirks |
| `getsentry-skills` | getsentry/skills（5 个路径） | merged | 外部攻击者威胁模型与五要素证据门、安全模式白名单、PR 描述规范与标题类型、CI check 等待判据、PR body 追加不覆盖、评审队列取数 |
| `github-docs` | docs.github.com（github/docs） | merged | 全部权威事实：`allow-unsafe-pr-checkout` 与 `pull_request_target` 的 cache 只读、SHA pin 策略、OIDC、关闭关键字仅对默认分支生效、CODEOWNERS 与 gitignore 的差异、rulesets 聚合与最严格者胜、不可变 release 与 release attestation、workflow execution protections |
| `zizmor` | zizmorcore/zizmor | merged | `zizmor` 的输入收集、persona 三档、离线/在线模式判定、退出码 11–14 语义、`--fix`、SARIF/GitHub 注解输出 |
| `scrutineer` | alpha-omega-security/scrutineer `skills/zizmor` | merged | scanner 结果的解读纪律：指引不等于证据、不得把硬化缺口当可利用漏洞、不得臆造仓库外配置 |
| `coderabbit-skills` | coderabbitai/skills `skills/autofix` | merged | `reviewThreads` 游标分页与 `isResolved`/`isOutdated` 字段选择 |
| `oz-for-oss` | warpdotdev/oz-for-oss（3 个路径） | merged | Issue 分诊结论的保守化规则与 issue forms 引导 |
| `citadel` | SethGammon/Citadel `skills/{triage,pr-watch}` | merged | 三维分诊分类法（type / severity / status）与迭代循环的熔断条件 |
| `octocat` | mcollina/skills `skills/octocat` | merged | `--body-file` 规避换行转义、`gh pr checks --watch` 后主动修、不熟的 `gh` 子命令先 `gh help` 验证 |
| `openai-skills` | openai/skills `skills/.curated/{gh-address-comments,gh-fix-ci}` | merged | `gh pr checks --json` 字段漂移的重试策略、非 Actions 的 check 只报 URL |
| `gh-pr-reviews` | k1LoW/gh-pr-reviews `skills/triage-pr-reviews` | merged | 内联评审回复端点与「同意/部分同意/不同意」分类的交叉校验 |
| `gh-cli` | cli/cli | reference | 正文所有 `gh` 子命令 flag 的核对来源（本机 `gh <cmd> --help`），未复制文本 |
| `starter-workflows` | actions/starter-workflows | reference | 官方脚手架 workflow 默认形态的交叉校验 |
| `scorecard` | ossf/scorecard | reference | `Dangerous-Workflow` / `Token-Permissions` / `Pinned-Dependencies` 检查项用于覆盖面自查 |
| `secure-repo` | step-security/secure-repo | reference | AGPL-3.0，按规则仅用其修复项清单判断覆盖面，事实全部改从官方文档取证 |

## 基线缺口

无 skill（`uv run tools/run_evals.py github --baseline`，Claude Opus 5 · medium）时，各场景未达成的
`expected_behavior`。基线整体很强——场景 1 的注入、`env:` 修法、`permissions`、pwn request、
特权隔离全部自力达成，场景 3 的 CODEOWNERS 六条也全中。缺口集中在三处：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 | 「要求第三方动作 pin 到 40 位 SHA 并在尾注写版本」 | 基线在功能性 bug 表里点了一句 `peter-evans/create-or-update-comment@v4` 未按 SHA 固定，但修复时的处置是**把这个动作删掉换 `gh` CLI**，理由写「不用我瞎编 commit SHA」。既没有提出 pin 要求，也没有给出「解析 release → 取 SHA → 尾注写版本」的做法；其余 4 个 `actions/*` 引用全部保持 `@v4` 且未说明这是策略选择 |
| 1 | 「AWS 长期密钥应改用 OIDC + `id-token: write`」 | 完全未提。基线把 `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` 原样保留在特权 job 里，只加了一个 `environment: pr-preview` 审批闸门。审批能挡住未经批准的下发，但密钥本身仍是永久有效的仓库 secret——这是本次最干净的一条缺口 |
| 1 | （附带）`allow-unsafe-pr-checkout` 与 `pull_request_target` 的 cache 只读 | 不在 `expected_behavior` 里，但基线不知道 `actions/checkout` 现在默认就拦 fork PR head，因此把「不要 checkout PR head」当成纯人工纪律；也不知道特权 workflow 的 cache 保存会失败并只留 warning |
| 2 | 「把描述重写成评审者封面信：保留根因/入口指引/破坏性变更，删掉文件清单、`npm test` 输出与 checklist」 | 部分未达成。基线正确地把根因与破坏性变更提到正文、把 "Notes to self" 拆成 Review guide，但**把文件清单保留成了一张带说明的表格**，并且把未勾选的 Docs checklist 项「补上具体缺口」而不是删掉。也就是说它做了「整理模板」而不是「换成封面信」 |
| 3 | 「已有 branch protection 与新 ruleset 并存且聚合，同一规则取最严格者，必须先读现有 protection」 | 完全未提。基线只写「推荐用 Rulesets，不用 legacy branch protection」，把两者当成互斥的二选一；既没说两者会叠加、也没说没有优先级概念、更没有去读 `repos/{owner}/{repo}/branches/main/protection`。这会导致它对「这个分支到底要求几个 approval」给出错误结论 |
| 4（负例） | 无 | 基线正确地只用本地 git 作答（`git reset --soft` / `rebase -i` + 备份分支 + `--force-with-lease`），未触碰 `gh`、PR 或仓库设置 |

第一版评测里场景 3 的 7 条基线全部达成，无区分度；按 `docs/workflow.md` Phase B 的要求补写了
第 8 条（rulesets 与 branch protection 的聚合语义）并重跑基线，缺口出现。

## 评测结果

模型固定 `anthropic/claude-opus-5` · thinking `medium`（`tools/run_evals.py` 默认值，两组同模型）。
人工逐条读 `answer.md` 判定。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 workflow 加固 | claude-opus-5:medium | 无（baseline） | false | 5 / 7：注入✓、`env:` 中转✓、`permissions:`✓、pwn request✓、特权隔离✓ | 未达成：SHA pin（只在 bug 表里点了一句 `peter-evans/...@v4`，修复时直接删掉该动作并写「不用我瞎编 commit SHA」，未提出 pin 要求也未给出取 SHA 的做法，其余 4 个 `actions/*` 仍是 `@v4`）；OIDC（完全未提，AWS 长期密钥原样保留，只加 environment 审批） |
| 1 workflow 加固 | claude-opus-5:medium | 有 | true | **7 / 7** | 两条缺口都被填补：所有 `uses:` 都 pin 到用 `gh api` 现查的真实 40 位 SHA 并带 `# v4` 尾注（还说明 `aws-actions/configure-aws-credentials` 的 `v4` 是附注标签、已二次解引用取 commit）；AWS 改为 `aws-actions/configure-aws-credentials` + `id-token: write` 并要求删除并轮换两个 secret。另外自带 skill 独有事实：现版 `actions/checkout` 已默认拒绝在 `pull_request_target` 下检出 fork head，除非 `allow-unsafe-pr-checkout: true` |
| 2 PR 生命周期 | claude-opus-5:medium | 无（baseline） | false | 5 / 6：关闭关键字对非默认分支无效✓、`--body-file`✓、先读整条分支 diff✓、内联回复走线程（`-F in_reply_to`）✓、`gh pr checks --watch`✓ | 未达成：改写成评审者封面信——把文件清单保留成一张带说明的表格，还把未勾选的 Docs checklist 项「补上具体缺口」，即整理了模板而没有换成封面信 |
| 2 PR 生命周期 | claude-opus-5:medium | 有 | true | **6 / 6** | 缺口被填补：明确列出删掉的东西及原因（`Summary`/`Changes`/`Test Plan` 脚手架、六行文件清单、粘贴的 `npm test` 输出、checklist），只留根因、破坏性影响、阅读起点。附带把关键字改成 `Refs #412` 并要求合并后 `gh issue close 412`，且给出 `-f` vs `-F` 的类型推断陷阱 |
| 3 CODEOWNERS + 分支规则 | claude-opus-5:medium | 无（baseline） | false | 7 / 8：`!` 取反✓、`[Dd]` 字符区间✓、最后匹配者胜与重排✓、同 pattern 两行只留最后一个 owner✓、文件本身不构成闸门✓、base 分支与 write 权限✓、给出可执行的规则配置（Web UI 步骤 + `codeowners/errors` 校验）✓ | 未达成：ruleset 与既有 branch protection 的聚合语义——基线写「推荐用 Rulesets，不用 legacy branch protection」，当成互斥二选一，未提叠加、无优先级、取最严者，也没有去读 `branches/main/protection` |
| 3 CODEOWNERS + 分支规则 | claude-opus-5:medium | 有 | true | **8 / 8** | 缺口被填补：明确写「rulesets 与遗留 branch protection rule 同时生效、取最严者，没有优先级」，并要求应用前先 `gh api repos/{owner}/{repo}/branches/main/protection` 读一遍。规则改为 `gh api .../rulesets -X POST` 的真实 payload（`~DEFAULT_BRANCH`、`bypass_actors: []`、`deletion` + `non_fast_forward` + `pull_request`），并建议忙碌仓库先用 `enforcement: evaluate` |
| 4 负例（本地 squash 三个 commit） | claude-opus-5:medium | 无（baseline） | **false** | 3 / 3 | 只用本地 git 作答：备份分支 + `git reset --soft HEAD~3` + `rebase -i` 备选 + `--force-with-lease`，未触碰 `gh`、PR、仓库设置 |
| 4 负例（本地 squash 三个 commit） | claude-opus-5:medium | 有（skill 可见） | **false** | 3 / 3 | skill 未被加载，符合边界预期；答案仍是纯本地 git（备份 ref + `reset --soft`，并以 `git diff backup/pre-squash` 为空作为验收），没有被 skill 拉偏 |

结论：**通过**。四条基线未达成的行为在有 skill 时全部达成（场景 1 的第三方动作 SHA pin、场景 1 的
OIDC 取代长期云密钥、场景 2 的封面信改写、场景 3 的 ruleset 聚合语义），负例两组
`skill_read` 均为 `false`。

## 备注

- **本地 git 内容被整批剔除**。按本波 contract 的分界句（能离线只靠 git 完成的归本地 git 一侧），
  以下内容按边界排除：`github/awesome-copilot` 的 `skills/git-flow-branch-creator`（通读全文 292 行，
  是 nvie Git Flow 的本地分支命名与创建，其中与远端/保护分支相关的内容为零）、
  `mcollina/skills` `skills/octocat` 里的交互式 rebase / 冲突解决 / submodule / bisect /
  分支清理（通读后只保留 3 条 GitHub 侧事实）；`obra/superpowers` 的 `using-git-worktrees` 与
  `finishing-a-development-branch`、`getsentry/skills` 的 `skills/create-branch` 与 `skills/commit`
  在全树枚举时按主题直接排除，未取其内容。
  正文里出现 `git` 命令的地方只有两类：取 diff 与 tag 这类**读操作**（`git diff <base>...HEAD`、
  `git tag --sort=-version:refname`），以及为 GitHub 侧动作提供坐标。`## Scope` 用 contract
  给定的英文原句写了这一半，且按要求**没有**指向任何尚不存在的 skill 名。
- **许可注意**：
  - `github/docs`（docs.github.com 的源）SPDX 为 `CC-BY-4.0`，按规则 merged，`notes` 里写了署名
    与实际查阅的 9 个页面路径。这是本 skill 事实的主要来源，挂 reference 会与实际写法自相矛盾。
  - `openai/skills` 全树无 LICENSE 文件、API `license: null` → `license: NONE` 并按规定写 notes。
  - `step-security/secure-repo` 为 AGPL-3.0 → 强制 `reference`，只用其修复项清单核对覆盖面，
    对应事实全部改从 docs.github.com 取证。
  - `actions/starter-workflows` API 报 `NOASSERTION`；实读 LICENSE 为标准 MIT 正文 + 一句
    「本许可不授予使用贡献者名称、标志或商标的权利」，因此 SPDX 记作 `MIT`，notes 写明来由。
    它 2026-08-03 推送，新鲜度只有 1 分，本就只作交叉校验，`relation: reference`。
  - `trailofbits/skills`（CC-BY-SA-4.0）经全树枚举确认无 Actions / PR / Issue / 治理相关内容，
    因此没有 CC-BY-SA 上游，不涉及「只取结构语义」那条规则。
- **临界与异常上游的复核结论**：
  - `mcollina/skills` 最近推送 2026-08-17，距调研日 25 天，仍在 6 个月窗口内，新鲜度 2 分；
    但内容一半属于本地 git 一侧，最终只取 3 条事实。
  - `actions/starter-workflows` 2026-08-03，同样在窗口内但已 1 个多月未动，仅作 reference。
  - `affaan-m/ECC` 的 `stargazers_count` 为 255713、`obra/superpowers` 为 284551，与仓库规模
    明显不符。已用 `gh api` 复查 `fork`/`parent` 字段确认两者都不是 fork。候选表按 API 原值记录，
    但评分中不把这个数字当权威依据（ECC 权威性给 1，最终 reference）。
- **未来同步时要盯的**：`github/docs` 是 `kind: docs`，`check_upstream.py` 只会报 `manual check`，
  必须人工比对；优先复查 `actions/reference/security/securely-using-pull_request_target`
  （`allow-unsafe-pr-checkout` 与 cache 只读这两条是本 skill 相对社区上游的主要增量，
  GitHub 一旦调整默认行为，`references/actions-triggers-and-injection.md` 的第 4 条与
  「What actions/checkout blocks now」一节要同时改）。
- **放弃的方向**：没有写 `scripts/`。本 skill 的每个动作都是一两条 `gh` 命令或一段 GraphQL 查询，
  包装成脚本只会在 `gh` 的字段漂移上再加一层需要维护的间接层——上游里凡是这么做的
  （`getsentry/skills` 的 4 个 `uv run` 脚本、`copilot-pr-autopilot` 的 10 个 PowerShell 脚本、
  `pr-dashboard` 的 `find ~/.copilot`）都因此绑死在自己的环境上。
