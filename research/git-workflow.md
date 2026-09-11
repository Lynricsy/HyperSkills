# git-workflow 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`"git worktree rebase merge conflict agent skill SKILL.md github"`
  - 路线图种子（`docs/roadmap.md` 波次 7 `git-workflow` 行）
  - VoltAgent/awesome-agent-skills、addyosmani/agent-skills
  - 官方组织仓库：`github/awesome-copilot`、`getsentry/skills`、`microsoft/skills`、`anthropics/skills`、`git/git`
  - 逐仓库列目录定位 git 相关 skill：
    `gh api repos/<o>/<r>/git/trees/HEAD?recursive=1 --jq '.tree[].path'` 后按
    `git|commit|branch|worktree|merge|conflict|rebase` 过滤
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` = 已登录 `Lynricsy`，全程用其 5000 次/小时配额，无匿名调用）
- 许可一律实读文件：`gh api repos/<o>/<r>/license --jq .content | base64 -d`，
  `git/git` 另读 `COPYING`。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | obra/superpowers `skills/using-git-worktrees` | https://github.com/obra/superpowers | 284825 | 2026-09-11 | MIT（实读） | worktree 建立与隔离检测 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | git-dir/common-dir 比较 + submodule 假阳性护栏是别处没有的；`check-ignore` 前置校验也是真陷阱 |
| 2 | obra/superpowers `skills/finishing-a-development-branch` | 同上 | 284825 | 2026-09-11 | MIT（实读） | 分支收尾与 worktree 清理 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 「先捕获 worktree 路径再 cd」「remove 被拒即意味着文件无副本」两条是实操级 |
| 3 | mattpocock/skills `skills/engineering/resolving-merge-conflicts` + `docs/engineering/resolving-merge-conflicts.md` | https://github.com/mattpocock/skills | 259035 | 2026-09-04 | MIT（实读） | 冲突解决纪律 | 2 | 3 | 2 | 3 | 2 | 12 | INCLUDE | SKILL.md 仅 14 行，价值全在「先读 primary source，再动 hunk」「不许 --abort」「提交前跑项目自带检查」三条纪律 |
| 4 | mattpocock/skills `skills/misc/git-guardrails-claude-code` | 同上 | 259035 | 2026-09-04 | MIT（实读） | 危险命令清单 | 2 | 3 | 2 | 3 | 2 | 12 | INCLUDE（reference） | 清单本身有用，但主体是 Claude Code PreToolUse hook 安装，本仓库标准禁止 harness 字段，故只对齐不复制 |
| 5 | melodic-software/claude-code-plugins `plugins/source-control/skills/resolve-conflicts` | https://github.com/melodic-software/claude-code-plugins | 16 | 2026-09-11 | MIT（实读） | 冲突意图恢复 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 按操作类型区分 `MERGE_HEAD`/`REBASE_HEAD`/`CHERRY_PICK_HEAD`/`REVERT_HEAD` 的恢复表，以及 `git show <op-head>` 静默为空的陷阱，是全部候选里最精确的一份 |
| 6 | 1995parham/parham-plugins `plugins/git-worktree/skills/git-worktree` | https://github.com/1995parham/parham-plugins | 0 | 2026-08-20 | MIT（实读） | worktree 心智模型 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 零星标但内容最强：per-worktree vs shared 清单含 `refs/stash` 共享这一条，本机实验独立证实 |
| 7 | addyosmani/agent-skills `skills/git-workflow-and-versioning` | https://github.com/addyosmani/agent-skills | 93429 | 2026-09-08 | MIT（实读） | 分支模型 + 提交纪律 + 发布 | 2 | 3 | 2 | 3 | 2 | 12 | INCLUDE | trunk-based 默认、变更尺寸阈值、pre-commit 卫生序列可用；semver/tag/changelog 半篇越界（→ `github`），已剔除 |
| 8 | github/awesome-copilot `skills/git-commit` | https://github.com/github/awesome-copilot | 38883 | 2026-09-10 | MIT（实读） | conventional commit 执行 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 官方；type 表、两种 breaking 形式、git safety protocol（不改 config、不 --no-verify、hook 失败改新提交）直接可用 |
| 9 | github/awesome-copilot `skills/conventional-branch` | 同上 | 38883 | 2026-09-10 | MIT（实读） | 分支命名语法 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 字符级规则（无下划线、无连续 `-`/`.`、trunk 名不加前缀）是可证伪的，且 `git check-ref-format` 可校验 |
| 10 | github/awesome-copilot `skills/commit-message-storyteller` | 同上 | 38883 | 2026-09-10 | MIT（实读） | 提交信息叙事 | 3 | 3 | 2 | 2 | 2 | 12 | INCLUDE | 「why 而非 what」的正文形状可用；其余是 prompt 脚手架（问用户三个问题），对 agent 无价值，已剔除 |
| 11 | github/awesome-copilot `skills/git-flow-branch-creator` | 同上 | 38883 | 2026-09-10 | MIT（实读） | git-flow 分支创建 | 3 | 3 | 2 | 2 | 2 | 12 | INCLUDE（并入 #9 的 paths） | 292 行但大半是 git-flow 专属流程；仅取默认分支探测与命名回退顺序 |
| 12 | github/awesome-copilot `skills/conventional-commit` | 同上 | 38883 | 2026-09-10 | MIT（实读） | conventional commit 模板 | 3 | 3 | 1 | 2 | 2 | 11 | MAYBE（未采用） | 主体是一段 XML prompt 模板，内容与 #8 完全重叠且更弱；本仓库标准要求正文只给一种做法，故不入 SOURCES |
| 13 | getsentry/skills `skills/commit` | https://github.com/getsentry/skills | 990 | 2026-09-07 | Apache-2.0（实读） | 提交信息机械规则 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 「一个 `-m` 一段、不要字面 `\n`、不开交互编辑器」是自动化场景唯一正确的做法，别处都没写；加上不写 PII |
| 14 | getsentry/skills `skills/create-branch` | 同上 | 990 | 2026-09-07 | Apache-2.0（实读） | 分支创建 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `git symbolic-ref refs/remotes/<remote>/HEAD` 探测默认分支 + 固定回退顺序 + 冲突后缀，非交互可跑 |
| 15 | fvadicamo/dev-agent-skills `plugins/github-workflow/skills/git-commit` | https://github.com/fvadicamo/dev-agent-skills | 73 | 2026-09-06 | MIT（实读） | 提交格式 | 1 | 3 | 2 | 2 | 2 | 10 | INCLUDE（reference） | 「先读项目自身约定」与 heredoc 形式有价值但来自更权威的 #8/#13；正文含 `` !`git log` `` 动态注入，本仓库标准禁止，故不复制 |
| 16 | albertdobmeyer/openskill-forge `skills/git-workflows` | https://github.com/albertdobmeyer/openskill-forge | 1 | 2026-05-20 | MIT | 进阶 git 操作总览 | 0 | 1 | 2 | 2 | 2 | 7 | MAYBE（未采用） | 534 行教程式罗列（rebase -i / bisect / worktree / subtree / sparse），只用来核对覆盖面是否有遗漏；>3 月未动，匿名作者，不入 SOURCES |
| 17 | git/git `Documentation` | https://github.com/git/git | 63103 | 2026-09-10 | **GPL-2.0（实读 COPYING）** | git 官方文档 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE（reference，强制） | 许可处理规则：GPL → 只能 reference。仅用作主题索引与旗标名核对，每条事实改由本机 git 2.55.0 实跑与本地 man page 取证 |
| 18 | mattpocock/skills `skills/misc/setup-pre-commit` | https://github.com/mattpocock/skills | 259035 | 2026-09-04 | MIT | pre-commit 框架安装 | 2 | 3 | 2 | 2 | 2 | 11 | MAYBE（未采用） | 讲的是 `pre-commit` 这个 Python 框架的装配，属产品用法；本 skill 从 git 侧覆盖 hook（`core.hooksPath`、`--no-verify`、密钥扫描 hook），不引入框架依赖 |
| 19 | raine/workmux `skills/workmux` | https://github.com/raine/workmux | 2395 | 2026-09-10 | MIT | workmux CLI 说明书 | 1 | 3 | 2 | 2 | 2 | 10 | REJECT | 实读后确认是 `workmux` 这个 tmux+worktree 编排 CLI 的说明书（`disable-model-invocation: true`），不是 git 实践；属「SaaS/产品包装类」排除项 |
| 20 | kenoxa/spine `skills/run-merge` | https://github.com/kenoxa/spine | 2 | 2026-09-10 | MIT | 冲突仲裁 | 0 | 3 | 2 | 0 | 2 | 7 | REJECT | 搜索命中的路径在 HEAD 上已 404（`gh api .../contents/skills/run-merge/SKILL.md` → 404），现改名 `skills/spine-worktree`，且内容绑定 Spine 自有的 Session V2 契约与 `.scratch` 桥，不可移植 |
| 21 | NousResearch/hermes-agent `skills/autonomous-ai-agents/merge-reconciler` | https://github.com/NousResearch/hermes-agent | 244285 | 2026-09-11 | MIT | 并行 agent 冲突仲裁 | 2 | 3 | — | 0 | 2 | — | REJECT | 路径在 HEAD 上 404，仓库树里已无任何 git/merge 相关 skill；无法实读即不评分 |
| 22 | microsoft/skills | https://github.com/microsoft/skills | 3007 | 2026-09-10 | MIT | — | 3 | 3 | — | — | 2 | — | REJECT | 列树后确认无 git/commit/branch 相关 skill，仅 Azure/Kusto 等；本主题无候选 |
| 23 | anthropics/skills | https://github.com/anthropics/skills | 175703 | 2026-09-10 | 无（API `license: null`） | — | 3 | 3 | — | — | 0 | — | REJECT | 列树后 git 相关命中只有 `skills/docx/scripts/merge_runs.py`（Word 文档处理），与本主题无关；未逐目录读 LICENSE.txt，因为没有要合入的目录 |
| 24 | conventional-commits/conventionalcommits.org | https://github.com/conventional-commits/conventionalcommits.org | 9232 | 2026-03-11 | MIT（实读） | Conventional Commits 规范 | 3 | 1 | 2 | 3 | 2 | 11 | MAYBE（未采用） | 规范本体；type 表与 breaking 两形式已由 #8（GitHub 官方 skill）转述且更贴合 agent 用法，再加一个上游只增加同步负担 |

## 深度审查

### obra/superpowers `using-git-worktrees` / `finishing-a-development-branch`（13 分，前两名）

167 + 225 行，frontmatter 只有 `name`/`description`，无 agent 专属字段，可直接对齐本仓库标准。结构是
Step 0..6 的强流程 + 两张表（Quick Reference / Common Rationalizations）。质量最高的部分不是命令，
而是**每一步的失败模式**：

- Step 0 用 `git rev-parse --git-dir` 与 `--git-common-dir` 比较判断是否已在 worktree 里，并显式指出
  submodule 会产生同样的不等式，必须用 `--show-superproject-working-tree` 排除。本机实验证实两者都成立。
- 「有 native worktree 工具就不要用 `git worktree add`」这条是 agent 特有的真问题：harness 自己管理的
  worktree 与 git 建的互不可见。
- `finishing` 里「先捕获 `WORKTREE_PATH` 再 cd」是一个真正的顺序 bug 护栏；
  「removal 被拒 = 文件只存在于该目录，绝不自行 `--force`」在本机实验里复现为
  `fatal: ... contains modified or untracked files`。

弱点：Step 2/3 的项目 setup 与 baseline 测试是通用工程动作（npm install / cargo build 罗列），
与 `test-driven-development` 重叠，本 skill 只保留「每个 worktree 必须自己 bootstrap 一次」这一结论。
`Announce at start: "I'm using the ... skill"` 属上游 harness 约定，剥离。

### 1995parham/parham-plugins `git-worktree`（12 分，内容质量第一）

258 行，0 星，但这是所有候选里唯一把 worktree 的**状态归属**写全的：per-worktree（HEAD、index、
工作树、MERGE_HEAD/rebase/bisect 状态、`refs/bisect/*`、`refs/worktree/*`、
`extensions.worktreeConfig` 下的 `--worktree` 配置）vs shared（objects、`refs/heads/*`、
`refs/remotes/*`、tags、hooks、config，以及 **`refs/stash`**）。
`refs/stash` 共享这一条我本机独立验证为真（见「本机实验」E4），这是并行 agent 场景最容易踩的坑，
而 obra 与 addyosmani 两份都没提。另有「untracked/ignored 文件不会跟过来」和
「独立工作分树、依赖工作共树」的判定规则，均采纳。

星数为 0 意味着权威性只能给 1 分，所以它的每条主张都必须本机复核过才用——实际复核了三条
（`refs/stash` 共享、分支互斥锁、`.git` 是文件而非目录），全部为真。

### melodic-software `resolve-conflicts`（12 分，冲突主干之一）

101 行 + `reference/`。最有价值的是按操作类型分列的意图恢复表，以及两条精确的负面知识：
`git show MERGE_HEAD -- <path>` 在「incoming 分支上不是 tip 的那个提交改了该路径」时**静默为空**；
rebase 时 ours/theirs 语义反转（ours = 被 rebase 到的 upstream，theirs = 你自己被重放的提交）。
后者是本 skill 的 Core rule 13。

frontmatter 带 `user-invocable`、`disable-model-invocation`、`argument-hint`、
`metadata.workflow-stage`，全部为 agent 专属字段，按标准 1.2 剥离；跨 plugin 的相对链接
（`../worktree/reference/gather-block.md`）按标准 4 禁止 reference 互链，删除。它关于
「一个 Bash 调用只放一条命令」的建议是其 harness 的限制，与 git 无关，剔除。

### getsentry `commit` / `create-branch`（14 分，并列最高）

62 + 68 行，短但每条都是可执行约束。它是唯一写出**自动化提交的机械正确形式**的候选：
`git commit -m "..." -m "..." -m "..."`（一段一个 `-m`），并明确禁止字面 `\n` 与交互编辑器。
这两条在其它候选里全部缺失，而它们正是 agent 实际会犯的错。`create-branch` 的默认分支探测链
（`git symbolic-ref refs/remotes/<remote>/HEAD` → `main` → `master` → 当前分支）与冲突后缀
（`-2`、`-3`）也直接采纳。Sentry 自有的 type 集（`ref`、`meta`、`license`）作为「项目自有约定优先」
的例子保留一句，不作为默认。

### github/awesome-copilot（官方，权威 3）

`git-commit` 的 type 表与 breaking 两形式是本 skill 提交章节的骨架；`Git Safety Protocol` 四条
（不改 git config、不擅自 force/hard reset、不擅自 `--no-verify`、hook 失败改新提交而非 amend）
与 mattpocock 的危险命令清单互相印证，合成 Core rules 2 与 hooks reference 的 `--no-verify` 一节。
`conventional-branch` 的字符级规则是可证伪的，且能用 `git check-ref-format --branch` 机器校验——
这正是本仓库要的那种规则，而不是「用有意义的名字」。
`conventional-commit` 与 `git-commit` 严重重叠且更弱（XML 模板），按「只给一个默认方案」剔除。

### addyosmani `git-workflow-and-versioning`（12 分，范围最宽也最需要裁）

355 行，前半（trunk-based、atomic commits、分离关注点、尺寸阈值、save-point、pre-commit 卫生、
bisect/blame/log -S 入门）与本 skill 范围重合；后半（semver、tag、changelog、release checklist）
越界：发布机制归 `github`，changelog 写作在本库尚无 skill。裁掉后半是本次最大的一处取舍，
理由写在 SOURCES 的 `notes`。它的 `CHANGES MADE / THINGS I DIDN'T TOUCH / POTENTIAL CONCERNS`
汇报模板很好，但那是 `code-review` 与 `planning` 的产物形状，不放进 git skill。

### git/git `Documentation`（许可强制 reference）

`gh api repos/git/git --jq .license.spdx_id` 返回 `NOASSERTION`，**实读 `COPYING` 确认是 GPL-2.0**
（"the only valid version of the GPL as far as this project is concerned is _this_ particular
version (ie v2)"）。按 `docs/roadmap.md` 许可处理规则，GPL 一律 `reference`，只用其主题清单判断
覆盖面。因此本 skill 的每条行为事实改由两个本地来源取证：
（a）`/usr/share/man/man1/git-*.1.gz` 本机 man page（`gc.reflogExpire` 90 天、
`gc.reflogExpireUnreachable` 30 天、`core.logAllRefUpdates` 在 bare 仓库默认 false、
`bisect run` 退出码契约均由此核对）；（b）`/tmp` 下一次性仓库实跑（见下节）。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | `--force-with-lease` 够不够安全 | 多数候选（含 addyosmani、awesome-copilot 的 safety protocol）把 `--force-with-lease` 当作安全的 force push；无一提 `--force-if-includes` | 正文写明裸 lease 会被任意一次 `fetch` 解除，必须叠加 `--force-if-includes`（2.30+）或显式 `=<ref>:<sha>` | 本机实验 E1 端到端复现「fetch 后 lease 放行、同事提交消失」，并复现 `--force-if-includes` 拒绝；官方 man page 核对旗标可用版本 |
| 2 | 冲突风格用哪个 | 无候选提及 `merge.conflictStyle`；本机全局配置是 `diff3` | 正文统一推荐 `zdiff3`（2.35+），并说明改配置不会重渲已冲突文件，要 `git checkout --merge` | 本机实验 E3a 实测三种风格输出差异：`diff3` 会把两侧共有行复制进标记内，`zdiff3` 提到标记外 |
| 3 | rerere 是纯增益还是有副作用 | 无候选提及 rerere | 正文写成「启用 rerere 时必须先 diff 它做了什么」，并写出两种误导状态 | 本机实验 E2/E3c：无 autoUpdate 时文件无标记但 index 为 `UU`；开 autoUpdate 时直接 `M `（已 staged），`git commit` 会封存未审解法 |
| 4 | `--abort` 是不是退路 | mattpocock：永不 `--abort`；melodic：只有在决定放弃整合本身时才 abort | 取 melodic 的更精确版本：abort 是对「这次整合要不要做」的决定，不是解法变难时的出口 | 「更新 > 更旧」+ melodic 表述覆盖了 mattpocock 的意图且不绝对化；`--abort` 确实会恢复工作树（本机确认），把它说成绝对禁止是错的 |
| 5 | 提交信息主题长度 | getsentry：≤70；awesome-copilot：<72；fvadicamo：≤50 | 采 70，并要求先读仓库自身最近 20 条主题 | 「官方厂商 > 社区」下 getsentry 与 GitHub 官方接近；50 是 fvadicamo 的项目私有约定，不可作为默认 |
| 6 | hook 失败后 amend 还是新提交 | awesome-copilot：一律新提交；addyosmani：未表态 | 采「新提交」，但补上「分支只属于你时 amend 无害」的逃生口 | hook 失败时提交根本没生成，对共享分支而言 amend 会改掉别人引用的 SHA；本机确认 `--amend --no-edit` 在同一秒内甚至不产生新 SHA，所以「amend 一定是重写」也是错的 |
| 7 | 分支是否已落地的判据 | addyosmani/obra 隐含用 `git branch --merged` / `git branch -d` | 正文改为 `git cherry -v <base> <branch>`（patch-id），并说明 `--merged` 对 squash 合并天生无效 | 本机实验 E8 实测：squash 合并后的分支出现在 `--no-merged` 里，而 `git cherry` 输出 `-` |
| 8 | worktree 目录放哪 | obra：`.worktrees/` 项目内优先（须 ignore）；parham：兄弟目录优先 | 正文给两种布局并要求「一个仓库选一种并保持一致」，不排序 | 两方都成立且各有理由（harness 隔离 vs 人手操作），属标准第 3 节「多种做法皆可 → 启发式」 |
| 9 | `bisect run` 的 126/127 语义 | git 官方 man page：1–127（125 除外）视为 bad，126/127 属「脚本里的普通错误」 | 正文给「文档 vs 实测」双列表，并要求把 `bogus exit code` 视为脚本坏了 | 本机实测 git 2.55.0：126 与 127 都报 `error: bogus exit code N for 'good' revision` 并继续走，与文档表述不符——以实测为准并如实标注分歧 |
| 10 | 密钥扫描 hook 的正则 | 多份候选用 `grep -i "password\|secret\|api_key"` 管道 | 正文改用 `git diff --cached -i -G '<ERE>'`，并注明 `(?i)` 不可用 | 本机实测：`git diff -G '(?i)...'` → `fatal: invalid regex`，`--perl-regexp` 也不救，必须用 `-i` 旗标 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| obra-worktrees | obra/superpowers `skills/using-git-worktrees` | merged | 隔离检测（git-dir vs common-dir + submodule 护栏）、worktree 目录须先确认被 ignore、优先用 harness 自带工具、sandbox 拒绝时的降级 |
| obra-finishing | obra/superpowers `skills/finishing-a-development-branch` | merged | 分支收尾全流程：先验证再整合、确认 base、把整合决定交给用户、只清理自己建的 worktree、remove 被拒的处理 |
| mattpocock-conflicts | mattpocock/skills `skills/engineering/resolving-merge-conflicts` | merged | 先读 primary source 再动 hunk、可兼容则两侧都留、不发明第三种行为、提交前跑项目自带检查、`--abort` 的定位 |
| melodic-resolve | melodic-software/claude-code-plugins `plugins/source-control/skills/resolve-conflicts` | merged | 按操作类型的意图恢复表、`git show <op-head>` 静默为空的陷阱、rebase 的 ours/theirs 反转、未合并路径必须先枚举 |
| parham-worktree | 1995parham/parham-plugins `plugins/git-worktree` | merged | per-worktree vs shared 状态清单（含 `refs/stash`）、一分支一 worktree 锁、untracked 文件不跟随、何时该开 worktree 的判定表 |
| addyosmani-git | addyosmani/agent-skills `skills/git-workflow-and-versioning` | merged | trunk-based 默认与 feature flag、commit 即 save point、原子提交与关注点分离、变更尺寸阈值、分支命名前缀、pre-commit 卫生序列 |
| awesome-copilot-commit | github/awesome-copilot `skills/git-commit` + `skills/commit-message-storyteller` | merged | Conventional Commits type 表与两种 breaking 形式、先读 diff 再定 type、Git Safety Protocol、正文写 why 而非 what |
| awesome-copilot-branch | github/awesome-copilot `skills/conventional-branch` + `skills/git-flow-branch-creator` | merged | `<type>/<description>` 语法与字符级规则、trunk 名不加前缀也不重建 |
| getsentry-commit | getsentry/skills `skills/commit` + `skills/create-branch` | merged | 一段一个 `-m`、禁止字面 `\n` 与交互编辑器、主题与行长上限、不写 PII、默认分支探测与回退顺序、冲突后缀 |
| mattpocock-guardrails | mattpocock/skills `skills/misc/git-guardrails-claude-code` | reference | 校验本 skill 的危险命令清单（push/force、`reset --hard`、`clean -f`、`branch -D`、`checkout .`/`restore .`）；hook 装配属 harness 专属，未复制 |
| fvadicamo-commit | fvadicamo/dev-agent-skills `plugins/github-workflow/skills/git-commit` | reference | 印证「项目自有约定优先」与 heredoc 多行提交；含动态注入，未复制 |
| git-docs | git/git `Documentation` | reference | 仅作主题索引与旗标名核对；GPL-2.0，事实全部改由本机 man page 与 `/tmp` 实跑取证 |

## 本机实验

环境：`git version 2.55.0`（本机全局 `merge.conflictstyle=diff3`、`core.hooksPath` 已设，
因此所有实验都用 `GIT_CONFIG_NOSYSTEM=1` + `HOME=/tmp/gwlab/home` +
`GIT_CONFIG_GLOBAL=/tmp/gwlab/gitconfig` 隔离，避免本机配置污染结论）。
脚本：`/tmp/gwlab/e1-lease.sh`、`e2-conflict.sh`、`e3-zdiff3-gc.sh`、`e4-worktree.sh`、
`e5-bisect-rewrite.sh`、`e6-fix.sh`、`e7-misc.sh`、`e8-final.sh`、`fixtures.sh`。
**所有实验均在 `/tmp` 下的一次性仓库中进行，未对本仓库做任何实验。**

### E1 `--force-with-lease` 的竞态窗口（证实了本 skill 的头号规则）

```
$ git commit --amend -m "base (amended by A)"
$ git push --force-with-lease origin main
 ! [rejected]        main -> main (stale info)
$ git fetch origin                      # 只是「看一眼远端」
$ git push --force-with-lease origin main
 + e53d4da...8420192 main -> main (forced update)
$ git -C ../remote.git log --oneline main
8420192 base (amended by A)              # B 的提交消失
```

同一场景加 `--force-if-includes`：

```
$ git push --force-with-lease --force-if-includes origin main
 ! [rejected]        main -> main (remote ref updated since checkout)
$ git -C ../remote.git log --oneline main
e53d4da B: important work
06f5038 base                             # 未丢
```

补充：删掉 `refs/remotes/origin/main` 后再推 → `! [rejected] (stale info)`，即**没有
remote-tracking ref 时 lease 是 fail-safe 而非放行**。

### E2/E3a 冲突风格（推翻了「zdiff3 只是 diff3 的别名」的想法）

第一次构造的用例里 `diff3` 与 `zdiff3` 输出完全相同（共有行本就在标记外），
重新构造成「两侧的改动都以同一行开头并以同一行结尾」后差异显现：

```
merge                diff3                   zdiff3
header               header                  header
SHARED               <<<<<<< HEAD            SHARED
<<<<<<< HEAD         SHARED                  <<<<<<< HEAD
main-only            main-only               main-only
=======              SHARED-TAIL             ||||||| 848a9a9
side-only            ||||||| 848a9a9         OLD
>>>>>>> side         OLD                     =======
SHARED-TAIL          =======                 side-only
footer               SHARED                  >>>>>>> side
                     side-only               SHARED-TAIL
                     SHARED-TAIL             footer
                     >>>>>>> side
                     footer
```

`merge` 完全丢掉 base；`diff3` 把 `SHARED`/`SHARED-TAIL` 复制进两侧；`zdiff3` 保留 base 且把共有行提出去。

### E2/E3c rerere 的两种误导状态

```
$ git merge side
Resolved 'f.txt' using previous resolution.
$ git status --porcelain
UU f.txt                    # 文件里没有任何冲突标记，index 仍是未合并
```

```
$ git -c rerere.autoUpdate=true ... merge side
Staged 'f.txt' using previous resolution.
$ git status --porcelain
M  f.txt                    # 已 staged，git commit 会直接封存未审解法
```

并且记录的解法会被**回放到另一个分支的同文本冲突**上（E2 最后一节），内容原样套用、无任何提示。

`git rerere forget` 不恢复标记：

```
$ git rerere forget f
Updated preimage for 'f'
Forgot resolution for 'f'
$ cat f
a
WRONG          # 仍是缓存里的错误解法
c
$ git checkout --merge f
Recreated 1 merge conflict
```

### E3b `gc --prune=now` 何时才真的删对象

```
$ git reset --hard HEAD~1          # 1d634d8 变成孤儿
$ git gc --prune=now
$ git cat-file -t 1d634d8
commit                             # 仍在：reflog 视为可达
$ git fsck --unreachable
                                   # 空输出（reflog 算可达）
$ git reflog expire --expire=now --expire-unreachable=now --all
$ git gc --prune=now
$ git cat-file -t 1d634d8
fatal: Not a valid object name      # 这一步才真删
```

被 drop 的 stash 不在任何 reflog 里，只有 `git fsck --unreachable` 能找到，
`git stash apply <sha>` 可直接恢复（实测成功）。
默认值从本机 man page 核对：`gc.reflogExpire` 90 天、`gc.reflogExpireUnreachable` 30 天、
`core.logAllRefUpdates` 在 bare 仓库默认 false。

### E4 worktree

- `refs/stash` **共享**：在 linked worktree 里 `git stash` 后，主检出的 `git rev-parse refs/stash`
  返回同一个 SHA。
- 分支互斥：`git checkout feat` → `fatal: 'feat' is already used by worktree at ...`（exit 128）。
- 手动 `rm -rf` 目录后：`git worktree list` 标 `prunable`，`.git/worktrees/wt-feat` 仍在，
  `git branch -d feat` → `error: cannot delete branch 'feat' used by worktree at ...`；
  `git worktree prune` 后才能删。
- `git worktree remove` 在有未跟踪文件时拒绝：
  `fatal: '../wt-feat' contains modified or untracked files, use --force to delete it`。
- 先删 worktree 再删分支 → per-worktree reflog 随 admin 目录一起消失，
  `reflog expire` + `gc --prune=now` 后提交彻底不可恢复（实测 `GONE`）。

### E5/E6 rewrite 与 bisect

- rebase 后：author date 保留（`2020-01-01`），committer date 重置为当时（`2026-09-11`），全部 SHA 变化。
- ssh 签名：`G lab@example.invalid` → rebase 后 `N`（无签名）→ `-c commit.gpgsign=true` rebase 后
  重新变 `G`，但签名人是执行重写的人；`cherry-pick` 同样丢签名。
  （第一次实验因未配 `gpg.ssh.allowedSignersFile` 而全部报 `N`，补配 allowed_signers 后才拿到有效结论。）
- `git commit --amend --no-edit` 在同一秒内、内容未变时 **SHA 不变**；隔 1 秒后 SHA 变化。
  推翻了「amend 必然产生新 SHA」。
- `filter-branch` 后 `refs/original/refs/heads/main` 仍在，旧 blob 仍可读
  （`git cat-file -p <old>:secret.env` → `token=sk_live_REDACTED`）；
  删 `refs/original/*` + `reflog expire` + `gc --prune=now` 三步做完后才 `gone`。
- `git rebase --autosquash --root` 非交互可用，且能跨中间提交把 `fixup!` 折叠；
  不加 `--autosquash` 的 `git rebase --root` 保留 `fixup!` 提交 → `rebase.autosquash` 默认关闭。
- `git rebase --update-refs` 会带上栈中间的 `featA`；不加时 `featA` 留在 rebase 前的提交上。
- `bisect run` 退出码：0 good；125 → `There are only 'skip'ped commits left to test.`；
  **126 与 127 都报 `error: bogus exit code N for 'good' revision` 并继续走**（与 man page 表述不符）；
  128 → `error: bisect run failed: exit code 128 ... is < 0 or >= 128`，且 bisect 会话仍然存活、HEAD 仍分离。

### E7/E8 其它

- `git branch -D` 连带删除该分支的 reflog 文件（`git reflog show doomed` → fatal），
  只有 HEAD reflog 还记得。
- `git range-diff main topic-old topic` 在纯 rebase 后全部输出 `=`；改一条提交信息后该行变 `!` 并显示差异。
- 子模块：本地提交 + 超项目 bump 后，普通 `git push` **成功**并留下指向私有提交的 gitlink；
  `git push --recurse-submodules=check` 报
  `The following submodule paths contain changes that can not be found on any remote` 并 `fatal: Aborting.`。
- `git sparse-checkout set --cone app` 后工作树只有 `app/`，index 仍含 `docs/d`，
  `git ls-files -v` 显示 `S docs/d`（skip-worktree）。
- `rebase.autoStash=true` 且 autostash 应用冲突时：仍打印 `Successfully rebased and updated ...`，
  `git status --porcelain` 为 `UU a`，`git stash list` 里 autostash 条目还在。
- `git checkout -- f` 丢掉的未提交编辑在 `git fsck --unreachable --no-reflogs` 里查无此物；
  但先 `git add` 过就能按 blob SHA 取回（实测取回内容 `work again`）。
- `git cherry -v main squashed-branch` → `- 99ad2d7 s`（已在上游）；
  `git branch --merged main` 不含该分支。
- `git subtree` 本机可用（`/usr/lib/git-core/git-subtree` 存在，但 `git subtree --help` 因 man 缺失而失败）；
  `subtree add --prefix=vendor/lib ... --squash` 实测产生
  `Merge commit '...' as 'vendor/lib'` + `Squashed 'vendor/lib/' content from commit ...` 两个提交。
- `git filter-repo` 本机**未安装**，因此正文对它的描述标 `[official]`，只有 `filter-branch` 的善后是实测的。
- `git diff -G '(?i)...'` → `fatal: invalid regex: Invalid preceding regular expression`，
  加 `--perl-regexp` 同样失败；必须写成 `git diff -i -G '...'`。据此改写了正文与 hook 示例，
  并在 `/tmp/gwlab/hk` 里把该 hook 跑通（干净提交通过，含 `ACCESS_TOKEN=` 的提交 exit 1 被拦）。

### 未能本机验证的声明（正文标 `[official]` 或写明版本门）

- `git filter-repo` 的具体行为（本机未安装；正文只说它会自行删除原始 ref 并 expire reflog，
  并给出 `filter-branch` 的完整善后作为可实测的替代路径）。
- `--force-if-includes`（2.30+）、`zdiff3`（2.35+）、`--update-refs`（2.38+）的**引入版本**
  取自官方 man page 与旗标可用性，本机 2.55.0 只能证明「现在可用」。
- `git maintenance start` 写入用户全局配置与系统调度器这一副作用，只读了 man page，
  未在本机执行（会污染本机环境）。
- 服务端行为（bare 仓库 reflog、forge 侧对象保留）只在正文中作为「必须如实告知用户」的说明出现，
  没有远端可供实测。

## 基线缺口

无 skill（`uv run tools/run_evals.py git-workflow --baseline`，Claude Opus 5 · medium）时，
基线整体非常强——git 是模型的强项，`--force-if-includes`、`git cherry`、
`gc.reflogExpireUnreachable=30 days`、轮换凭据、squash 合并对 `--merged` 无效这些都自己答出来了。
因此下面只列**确实未达成**的行为，它们构成本 skill 必须填的缺口。

> 场景 4 第一次基线跑时，模型在 `/tmp` 下找到了我造夹具用的真实仓库
> （夹具里泄漏了 `/tmp/gwlab/fx/payments-api` 这个绝对路径）并据此作答。已把夹具路径改写为
> `/home/dev/src/payments-api` 并重跑场景 4，下表用的是重跑后的干净结果。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 force-push 事故 | `git range-diff` 作为「重写没丢东西」的验证门 | 基线用 `git log --oneline X --not <branch>` 确认丢了什么，但没有任何一步验证重写后的结果与重写前等价 |
| 1 | 重写会丢签名 / 重置 committer date | 配置里有 `commit.gpgsign = true`，基线只在另一个场景提到 ssh-agent，未指出重写会把签名换成执行者的或直接丢掉 |
| 2 冲突 | `git rerere forget` 不恢复标记，要 `git checkout --merge` | 基线给了 `git checkout -m -- <file>`，但完全没提 `rerere forget`，也没指出它清缓存却不改工作树 |
| 2 | rebase / cherry-pick 时 ours/theirs 反转 | 未出现。基线全程按 merge 语义解释两侧 |
| 2 | `rebase.autoStash` 会在打印成功的同时留下冲突 | 未出现。配置里 `rebase.autoStash = true` 摆在眼前，基线只点评了别名与 rerere |
| 2 | 从历史恢复双方意图（`git log -p <base>..MERGE_HEAD -- <path>`） | 基线直接用夹具里现成的 `--left-right` 输出推断意图，没有给出「动 hunk 前先读两侧提交」的取证命令 |
| 3 历史清理 | 重写后必须告知持有者 `fetch` + `reset --hard`（而非 `pull`/`merge`） | 未出现。基线只说了远端旧对象要提工单 |
| 3 | `rebase --autosquash` 且 `rebase.autosquash` 默认关闭 | 基线手写 todo 列表把 `fixup!` 标成 `fixup`，没用 `--autosquash`，也没说默认是关的 |
| 3 | 重写会重置 committer date / 全部 SHA；用 `range-diff` 验证 | 基线的验证是 `git log --all -- <path>` 为空，只验证了「密钥没了」，没验证「别的没丢」 |
| 3 | `git branch -D` 会删掉该分支自己的 reflog；dropped stash 不在任何 reflog 里 | 基线给了 `fsck --no-reflogs --unreachable --lost-found` 作兜底，但没说清哪些情形 reflog 根本不覆盖 |
| 4 worktree 并行 | `refs/stash` 跨 worktree 共享 | 未出现。基线说「index 各自独立」（对），但漏掉了 stash 这个真正会互相踩的共享点 |
| 4 | 新 worktree 没有 untracked/ignored 文件，必须各自 bootstrap | 未出现。三个 agent 直接开工，没有依赖安装与基线测试步骤 |
| 4 | `rm -rf` worktree 目录会留下分支锁与 admin 目录，要 `git worktree prune` | 基线用了 `git worktree remove` + `prune`（对），但没说手删目录的后果，用户真手删了就不知道怎么办 |
| 4 | worktree 的 reflog 随 admin 目录一起消失 | 未出现 |

基线全中的项（不计入缺口，但说明评测没有虚设）：场景 1 的 lease 机制与 `--force-if-includes`、
危险别名识别、先恢复后加固的顺序；场景 2 的 rerere 定位、`zdiff3`、stage 1/2/3、两侧兼容合成、
提交前跑检查；场景 3 的 `gc` 不删 reflog 可达对象、轮换凭据、`filter-repo`、merge commit 的处理；
场景 4 的一分支一 worktree、`git cherry` 判定 squash 落地、拒删未落地分支。

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 force-push 事故 | claude-opus-5 medium | 无（baseline） | false | 5/7 | 缺 `range-diff` 验证门、缺签名/committer date 影响 |
| 2 冲突 + rerere | claude-opus-5 medium | 无（baseline） | false | 4/8 | 缺 `rerere forget`、ours/theirs 反转、autoStash 陷阱、历史取证命令 |
| 3 历史清理 + 恢复 | claude-opus-5 medium | 无（baseline） | false | 4/8 | 缺协作者指令、`--autosquash` 默认、range-diff 验证、reflog 覆盖边界 |
| 4 worktree 并行 | claude-opus-5 medium | 无（baseline） | false | 3/7 | 缺 `refs/stash` 共享、bootstrap、手删目录后果、worktree reflog |
| 5 负例（PR 的 CI 失败） | claude-opus-5 medium | 无（baseline） | false | 3/3 | 基线模式下无 skill 可读，负例的意义在「有 skill」那一轮 |
| 1 force-push 事故 | claude-opus-5 medium | 有 skill | **true** | **7/7** | 补上了 `range-diff` 验证门（Plan 第 6 步）与「重写会用执行者的 key 重签、committer date 重置」 |
| 2 冲突 + rerere | claude-opus-5 medium | 有 skill | **true** | **7/8** | 补上 `rerere forget` 不还标记、`checkout --merge`、autoStash 陷阱、`log -p base..MERGE_HEAD` 取证与 `git show MERGE_HEAD` 静默为空；**仍缺** rebase 的 ours/theirs 反转（本场景是 merge，未触发该条） |
| 3 历史清理 + 恢复 | claude-opus-5 medium | 有 skill | **true** | **8/8** | 全中。额外发现一条本 skill 没写的次序约束（见下） |
| 4 worktree 并行 | claude-opus-5 medium | 有 skill | **true** | **5/7** | 补上 `refs/stash` 共享与逐 worktree bootstrap；**仍缺** 手删目录留下分支锁/admin 目录、以及 worktree reflog 随 admin 目录消失 |
| 5 负例（PR 的 CI 失败） | claude-opus-5 medium | 有 skill | **false** | 3/3 | 未读 `skills/git-workflow/SKILL.md`（`skill_read=false`），转去查 PR 的 check-run 与权限，未提冲突风格/rerere/reflog/lease |

结论：**通过**。基线未达成的 12 条行为里有 10 条在有 skill 时达成，四个正例场景每个都至少填补了两条：

| 场景 | 基线 | 有 skill | 被填补的基线缺口 |
|---|---|---|---|
| 1 | 5/7 | 7/7 | `range-diff` 验证门；重写对签名与 committer date 的影响 |
| 2 | 4/8 | 7/8 | `rerere forget` 不还标记；`rebase.autoStash` 报成功仍留冲突；从历史取证双方意图 |
| 3 | 4/8 | 8/8 | 协作者必须 `fetch` + `reset --hard` 而非 `pull`；`--autosquash` 默认关闭；`range-diff` 验证；reflog 覆盖边界（`-D` 删分支 reflog、dropped stash） |
| 4 | 3/7 | 5/7 | `refs/stash` 跨 worktree 共享；新 worktree 无 untracked/ignored 文件，必须各自 bootstrap 并建绿色基线 |

仍未达成的两条如实记录，不改判、不放宽标准：

- 场景 2 的「rebase/cherry-pick 时 ours/theirs 反转」（Core rule 13）没有出现在回答里。该场景是一次
  merge，反转规则在此不适用，模型没有主动外推——属于评测项设计得比场景宽，而不是 skill 缺内容。
- 场景 4 的「手删 worktree 目录会留下分支锁，要 `git worktree prune`」与「worktree 的 reflog 随
  admin 目录一起消失」只出现在 `references/branching-and-worktrees.md` 与
  `references/finishing-a-branch.md` 里。SKILL.md 的 Core rule 22 写了前者，但回答没引用——
  它止步于「worktree 可 `remove` + `prune` 撤掉，是可逆的」。根因是 Workflows 里原本没有任何
  收尾流程：`references/finishing-a-branch.md` 只被 Topic router 指到，模型没有理由去读它。
  **已据此补上第 8 个 workflow `finish-and-clean-up`**（SKILL.md 从 318 行增至 339 行，
  仍在 235–350 区间），其中把「先 remove worktree 再删分支」「手删目录后分支锁到 `prune` 才解」
  「remove 被拒只上报不强制」「删分支前先 `git rev-parse` 记 SHA」写进了清单与 Gate。
  补上 workflow 后**重跑了场景 4**（`run_evals.py git-workflow --only 4`，88.2s，`skill_read=true`）：
  仍是 5/7。原因清楚了——这条 query 只要求「建三个 worktree + 删已落地分支」，从头到尾没有任何
  拆除 worktree 的动作，所以「手删目录的后果」与「worktree reflog 随 admin 目录消失」在本场景里
  根本无从触发。这是评测项比场景宽，不是 skill 缺内容：两条都已写进 Core rules 22 与
  `finish-and-clean-up` 的清单与 Gate。重跑同时确认新增 workflow 没有挤掉原有行为
  （`refs/stash` 共享、逐 worktree bootstrap、`git cherry` 判定、`branch -D` 删分支 reflog 均仍在，
  且新增了「删前先 `rev-parse` 记 SHA、30 天内可 `git branch recover/... <sha>` 救回」）。
  若要真正测到这两条，下次同步应把场景 4 的 query 扩展成「任务做完了，收尾」。

**有 skill 一轮附带发现的一条真知识（本 skill 尚未收录）**：场景 3 的回答指出
`git filter-repo` 在结束时会自行 `reflog expire` + `gc --prune=now`，因此「先救回丢失的提交」
必须排在「清除密钥」之前，否则 filter-repo 的自动善后会把还能救的对象一并销毁。
本机未安装 filter-repo，无法实测该顺序约束，故 SKILL.md 未写成规则；
`references/history-rewrite-guardrails.md` 中 filter-repo 的自清理一句已标 `[official]`，
`recover-lost-work` workflow 的第一条也已要求「在锚定之前不要跑 gc / reflog expire」，
方向一致但没有显式点出这个次序。下次同步时若能装上 filter-repo，应实测并补成一条 Core rule。

## 备注

- **许可**：`git/git` 的 `COPYING` 是 GPL-2.0（实读，API 的 `spdx_id` 是 `NOASSERTION`），
  永久 reference-only。`getsentry/skills` 是 Apache-2.0，其余合入项全部 MIT（均实读 LICENSE 正文）。
  `anthropics/skills` 本主题下无候选，未涉及其逐目录专有许可问题。
- **同步时要盯的上游**：`melodic-software/claude-code-plugins` 推送极频繁（`--pin` 时已从
  `d1a9dd1` 移到 `4785e62`，但 `plugins/source-control` 路径未变），其 `plugins/source-control`
  正在重构（`reference/worktree-root-convention.md` 等）；`github/awesome-copilot` 的 `skills/`
  每周新增，下次同步要重新列一次 `git|commit|branch` 过滤结果。
- **放弃的方向**：semver / tag / changelog（→ `github`，changelog 写作本库尚无 skill）；
  `pre-commit` 框架装配（属产品用法）；`workmux`、`spine` 这类 worktree 编排 CLI 的说明书。
- **评测夹具**：`evals/files/*` 全部由 `/tmp/gwlab/fixtures.sh` 在一次性仓库里真跑 git 产出
  （`git log --graph`、三 stage 的真实冲突文件、`git ls-files -u`、`branch --merged/--no-merged`），
  不是手写的。夹具里的假凭据一律写成 `ghp_REDACTED` / `sk_live_REDACTED`，
  刻意低于推送保护的模式长度，避免重演上一波被 GitHub 推送保护拒绝的事故。
- **夹具路径泄漏**：第一版夹具里含 `/tmp/gwlab/fx/payments-api` 绝对路径，导致基线场景 4
  跑去读了本机真实仓库。已改为 `/home/dev/src/payments-api` 并重跑该场景。
  以后造夹具一律不要写本机真实路径。
