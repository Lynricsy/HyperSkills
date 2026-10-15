---
description: 合并上游更新、评估追踪仓库新增内容与新候选、复核文档上游并完成 D2 回归与集成
argument-hint: "[skill ...]"
---

处理范围取自 `$ARGUMENTS`：为空时处理 `skills/` 下全部 skill；非空时只处理 `$ARGUMENTS` 列出的 skill。

各阶段通用细则与字段规范以 `AGENTS.md`、`docs/workflow.md`、`docs/skill-standard.md` 为唯一准绳；
本命令只规定执行顺序、硬性约束，以及 2026-10-15 全量同步中踩过的坑。

## 0. 开工前

1. **对齐规范与历史遗留**：先读 `AGENTS.md`、`docs/workflow.md`（五阶段流水线 +「更新流程」
   状态表）、`docs/skill-standard.md`；用 MCP `search-logs` 搜「上游同步」查看上次留下的
   遗留项（如 `parham-worktree` `MISSING`、待定 `## Scope` 的条目），避免重复踩坑或漏掉待办。
2. **锁定 GitHub API 认证配额**：运行 `gh auth status` 确认通过。查 GitHub 一律用已登录 `gh`
   （5000 次/小时），禁止匿名 HTTP（60 次/小时会迅速打满）、禁止读 GitHub 网页猜数据。
   `gh` 不可用或触发限流时立即停止并上报，不得降级。
3. **验证评测前置条件**：确认 `vm/local.env` 含 `OPENAI_API_KEY`（主人填写，勿打印内容），
   并执行冒烟测试确认隔离 VM 与模型通路正常：
   ```bash
   uv run tools/vm.py run --thinking minimal "Reply with exactly: pong"
   ```
   没有密钥或冒烟失败就直接问主人，不要换模型口径。
4. **先快照旧 pin（必须在任何 `--pin` 之前）**：运行以下命令并保存一份 `skill/id → pinned, head`
   映射表：
   ```bash
   uv run tools/check_upstream.py --json > /tmp/hs-upstream-<日期>.json
   ```
   理由：阶段 2 要用「旧 pin..新 HEAD」区间找仓库新增文件，一旦先执行 `--pin` 覆盖了
   `SOURCES.yaml`，旧 pin 就丢了。

## 1. 已追踪路径的更新（tracked paths）

1. **按状态表分流**：运行 `uv run tools/check_upstream.py [<skill>...]`，各状态含义与动作
   见 `docs/workflow.md`「更新流程」状态表（含 `EMPTY`、`MISSING`、`diverged`、
   `pinned commit is unreachable` 等需按 Phase B 重新裁决的情形）。
2. **大跨度区间完整归因**：遇到 `diff too large to attribute to paths` 的条目，必须自己做完整
   区间归因——按仓库分组拉取裸仓库缓存，再按路径查日志：
   ```bash
   git clone --bare --filter=blob:none --single-branch --branch <ref> --shallow-since=<该仓库最早 pin 的提交日期 - 3 天> https://github.com/<repo>.git /tmp/hs-attr/<owner>__<repo>
   git log <pinned>..<head> -- <paths>
   ```
   在裸仓库目录下执行 `git log <pinned>..<head> -- <paths>` 输出为空即为噪声，只需 re-pin。
   **不要用 `commits?path=&since=` 日期过滤**——该接口会漏掉早创建、晚合入的提交，且默认不分页。
3. **读真实 diff 再裁决**：必须读取 tracked paths 的**真实 diff** 再判断，不凭提交标题猜测：
   - **无影响** → 正文不动，只 re-pin；
   - **事实更正** → 用官方文档、源码或本机实跑核实后直接修改正文；
   - **新增规则** → 先在 `evals/evals.json` 中跑基线证明存在能力缺口，基线已会就不合入。
4. **核对 `--pin` 越界差额**：`uv run tools/check_upstream.py --pin <skill>` 写的是**执行当时**的
   远端 HEAD，可能越过刚刚审阅过的 HEAD。每次 `--pin` 后逐条比较写入的 `commit` 与审阅 HEAD；
   若不等，立即对差额区间按 `paths` 再归因并记录，防止漏审期间新推入的提交：
   ```bash
   gh api repos/<o>/<r>/compare/<审阅>...<写入>
   ```
5. **更新版本号与同步记录**：即使无实质变更也要 re-pin；把 `SKILL.md` 的 `metadata.version`
   与 `SOURCES.yaml` 的 `version` 改为当天日期（`YYYY.MM.DD`）；在 `research/<s>.md` 追加
   `## <日期> 上游同步`，使用如下表头记录：
   ```markdown
   | 上游 | 区间 | 命中 paths | 判定 |
   ```

## 2. 已追踪仓库里的新增内容

1. **枚举区间新增文件**：对每个移动过的已追踪仓库，在阶段 0 保存的「旧 pin..新 HEAD」区间上执行
   `git diff --name-status --diff-filter=A`（大仓库直接用阶段 1 的 `/tmp/hs-attr/<owner>__<repo>`
   裸仓库缓存；其余仓库用 `gh api repos/<o>/<r>/compare/<pinned>...<head>` 的
   `files[].status=="added"`，文件数 ≥300 时改用 clone），筛出 `SKILL.md`、`*.instructions.md`、
   `*.agent.md`、`AGENTS.md`、`CLAUDE.md` 等 skill 类新文件。
2. **只读评估每个新文件**：动手前从五个维度评估：
   - **Scope 归属**：是否落在我们某个 skill 的 `## Scope`（同时检查本 skill 与其他 skill）；
   - **历史去重**：`research/<s>.md` 是否已 REJECT 过同类候选，避免重复讨论；
   - **增量价值**：是否含我们**尚未覆盖**的具体可验证内容；
   - **权威度**：按「官方 > 公认专家 > 社区」排序；
   - **许可**：查清 SPDX 标识，专有许可只能作 `relation: reference`，禁止复制文字或脚本：
     ```bash
     gh api repos/<o>/<r> --jq .license.spdx_id
     ```
   上游自用流程、行业/营销内容、单一商业产品手册、alpha/未发布功能 → 判 `REJECT` 或记待定。
3. **严守合入门槛与规则位置**：事实更正可直接核实后改；新增内容必须先跑基线证明缺口（基线已会就
   不合入，场景留作哨兵）。规则只放 `references/` 时模型常不主动读，必要时提炼到 `SKILL.md` 的
   `## Core rules`（注意 `SKILL.md` 行数与 `Core rules` ≤25 条的篇幅上限）。
4. **扩 Scope 条目交由主人拍板**：需要扩 `## Scope` 的条目（例：车机/Wear、持续 profiling、
   固件审计）不要自作主张，单独列出交主人决定。
5. **溯源与落盘记录**：同仓库已被该 skill 追踪就把新路径加进 `paths`，否则新增 upstream 条目，
   再执行 `--pin`。在 `research/<s>.md` 追加 `## <日期> 上游新增内容评估`，每个候选写一行结论。

## 3. 新的值得追踪的仓库

1. **多途径检索与指标核验**：按 `docs/workflow.md` Phase A 的检索途径找候选（`skills.sh`、
   `VoltAgent/awesome-agent-skills`、`addyosmani/agent-skills`、`github/awesome-copilot`、
   领域官方组织列表），也看已追踪仓库新近引用的上游；用 `gh search repos` / `gh api` 核实
   stars、`pushed_at`、license：
   ```bash
   gh api repos/<owner>/<repo> --jq '{stars: .stargazers_count, pushed: .pushed_at, license: .license.spdx_id}'
   ```
2. **候选表去重与量表评分**：先读 `research/<s>.md` 候选表，已 REJECT 的不重复讨论；新候选按
   `docs/skill-standard.md` 第 9 节量表打分，**REJECT 也要留行写理由**，防止后续批次重审。
3. **合入或记入路线图**：`INCLUDE` 的仓库按 Phase B/C 合入（评测先行、证明基线缺口），在
   `SOURCES.yaml` 新增条目并 `--pin`；只作校验的用 `relation: reference`。值得追踪但不属于
   任何现有 skill 的仓库 → 记入 `docs/roadmap.md` 供主人决定，不擅自新建 skill。

## 4. `kind: docs` 上游

1. **人工比对具体事实**：`docs/workflow.md` 对 `kind: docs` 要求 `manual check`（人工打开链接
   比对），零 `behind` 不能替代。核对范围 = 该条目 `contributes` + 正文实际引用该来源的具体事实
   （版本、默认值、弃用/移除、命令参数、限制数字、日期），不遍历整站。
2. **写入复核表并更新 `synced_at`**：逐条结论写进 `research/<s>.md` 的 `## <日期> 文档上游复核` 表：
   ```markdown
   | 上游 id | 核对的事实 | 当前官方页面 | 结论 |
   ```
   核完把 `SOURCES.yaml` 中该条目的 `synced_at` 改为当天（`--pin` 不改 `docs` 条目）。
3. **当场修复已知过时项**：发现的已知过时项（例：版本对照表缺最新大版本）当场修，不留给下次。

## 5. Phase D2 回归（不能省）

1. **正文改动必跑回归**：任何正文（`SKILL.md` / `references/` / `scripts/`）有改动的 skill，
   包括「只是事实更正」的，都要在隔离 VM 用 `omp` + `openai/gpt-6.1-sol` `medium` 跑受影响场景的
   「有 skill」与「基线」，外加 1 个负例查 `skill_read == false`；本轮改过 `expected_behavior`
   的场景两侧都必须重跑。没有场景覆盖某处更正时新增一个回归场景（不要求制造知识缺口）。
2. **严守结果复用规则**：「有 skill」结果必须晚于该 skill 最后一次正文提交；基线在场景/夹具未变时
   可复用当天结果；`2026-10-10` 之前的旧口径结果一律不复用。
3. **独立输出目录与单场景串行**：每个 agent 指定 `--out /tmp/hs-d2/<agent>`，同一时刻只跑一个
   场景，避免锁冲突。结果记入 `research/<s>.md` 的 `## <日期> D2 回归`。
4. **负例误读处理**：若负例误读 skill（`skill_read == true`），先查 `description` 当天是否改过；
   没改 = 既有路由问题，如实记录，**本轮不改 `description`**（`description` 维护须走
   `docs/workflow.md`「本地 description 维护的阶段映射」的专门流程）。

## 6. 编排与集成（大批量时）

1. **并发上限与禁止嵌套派生**：遵守用户规则——同时工作的 subagent ≤5 个，**嵌套派生也计数**，
   所以子代理一律禁止再派生；writer agent 用其他提供商模型，不占这 5 个名额。按领域分组，
   滚动补位；完成的代理不要广播唤醒。
2. **独立 worktree 与绝对路径铁律**：每个代理分配一个独立 worktree，并复制 `vm/local.env`（勿提交）：
   ```bash
   git worktree add /tmp/hs-wt/<名> -b <前缀>/<名> main
   cp vm/local.env /tmp/hs-wt/<名>/vm/local.env
   ```
   **所有路径一律用 worktree 绝对路径**——相对路径会落到主工作区（2026-10-15 同步中发生过 3 次）。
   **禁止 `git stash`**——stash 跨 worktree 共享，曾有两个代理互相 pop 了对方的 stash。
3. **单 skill 单提交规范**：每个 skill 一个提交，格式 `<type>(<scope>): <gitmoji> <subject>`
   并附 `Co-authored-by: Wine Fox <fox@ling.plus>`：
   - 同步：`chore(skills): ⬆️ 同步 <s> 上游 <ids>`
   - 更正：`fix(skills): 🐛 …`
   - 新增：`feat(skills): ✨ …`
   - 仅记录：`docs(research): 📝 …`
   - 仅评测：`test(evals): ✅ …`
4. **主代理逐提交集成到 `main`**：
   - 先确认主工作区 `git status` 干净（否则 `git add -A` 会把别人误写的改动混进集成提交）；
   - 执行 `git cherry-pick -n <c>`，只允许生成文件冲突（`README.md`、`THIRD_PARTY_NOTICES.md`、
     `skills/*/NOTICE.md`、`.claude-plugin/marketplace.json`、`docs/assets/badge-*.svg`，
     用 ours 后重建），其他冲突立即停下人工处理；
   - 依次执行目录重建与提交：
     ```bash
     uv run tools/build_catalog.py
     git add -A
     git commit -C <c>
     ```
   - 去重键必须用**「作者时间|标题」**，不能只比标题（同一 skill 历次同步标题相同，会被误跳过）。
     集成后核对每个分支提交都在 `main`。
5. **503 与额度中断恢复**：代理因提供商 503 或额度用尽中断时，先集成已提交部分，再给原代理发消息
   让其续做，或开接班代理并把前任汇报（`agent://<id>`）、未提交改动、后台队列交代清楚。
   评测接口 503 时让队列自动重试，不要换模型。
6. **收尾与清理**：
   - 跑全仓静态校验并确保全过：
     ```bash
     uv run --locked tools/check_repository.py
     ```
   - 再跑一次 `uv run tools/check_upstream.py`，对同一天又前进的上游重复阶段 1 的归因
     （`hyperskills-self` 指向本仓库，自身提交只需按 tracked paths 判断）；
   - `git push` 推送远端；调用 MCP `record-agent-log` 记录做了什么和为什么；删除临时 worktree
     与分支。

## 汇报格式

用中文向主人汇报：每类结果一张表（已追踪路径同步 / 已追踪仓库新增内容 / 新仓库 / `docs` 复核 / D2 回归），
并在末尾列出需要主人决定的 `## Scope` 问题与遗留项。
