# python 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`"python agent skill SKILL.md github uv ruff pytest typing 2026"`、
    `site:github.com "SKILL.md" python "modern python" skill uv mypy asyncio`
  - <https://www.skills.sh> 检索结果（经上述搜索命中的仓库：`gvre/skills`、
    `SpillwaveSolutions/mastering-python-skill-plugin`、`s2005/uv-skill`、`cast42/python-minimal-boilerplate`）
  - VoltAgent/awesome-agent-skills、addyosmani/agent-skills（无 Python 专项 skill）
  - `github/awesome-copilot`：`skills/` 与 `instructions/` 全树 grep（`python|pytest|pypi|ruff|mypy|typing`）
  - 领域官方组织仓库：`astral-sh/uv`、`astral-sh/ruff`、`astral-sh/ty`、`pytest-dev/pytest`、
    `python/cpython`、`python/typing`；另核查 `anthropics/skills`、`openai/skills`、
    `microsoft/skills`、`mattpocock/skills`（均无 Python 生态 skill）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- `gh auth status`：已登录（账号 Lynricsy，scopes `gist, read:org, repo, workflow`），全程未触发限流。

### 种子更正记录

- 路线图旧种子 `getsentry/skills` 的 `languages/python.md` **已不在仓库树中**。
  用 `gh api repos/getsentry/skills/git/trees/main?recursive=1` 核实，当前树内与 Python 相关的
  只有 `skills/typing-exclusion-worker/`、`skills/find-bugs/` 与
  `skills/security-review/languages/python.md`。最后一项是 `security-review` skill 的语言分册，
  属安全审计范围，不属本 skill。
- 种子 `existential-birds/beagle` 的「Python 评审部分」实际路径是
  `plugins/beagle-python/skills/{python-code-review,pytest-code-review,review-python}`
  （`plugins/beagle-ai/` 下全是 LangGraph / pydantic-ai，与本 skill 无关）。
- 种子 `giuseppe-trisciuoglio/developer-kit` 的 Python 部分主体是
  `plugins/developer-kit-python/rules/*.md`；该插件下的两个 skill 是 AWS Lambda 与
  Clean Architecture，超出本 skill 边界。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | trailofbits/skills `plugins/modern-python/skills/modern-python`（+9 个 references） | https://github.com/trailofbits/skills/tree/main/plugins/modern-python | 7031 | 2026-09-09 | CC-BY-SA-4.0 | uv/ruff/ty/pytest/PEP 723/迁移 | 2 | 3 | 3 | 2 | 2 | 12 | INCLUDE（merged，仅结构与清单语义） | 覆盖面与本 skill 最贴合的一份：项目 vs 单文件脚本的分流、`[dependency-groups]` 取代 extras、四条迁移路径、迁移后清理清单。正确性扣分见「冲突与裁决」1/2/3 条。CC-BY-SA-4.0 与本仓 MIT 不相容，只取结构，不复制任何句子 |
| 2 | github/awesome-copilot `skills/python-pypi-package-builder`（含 9 个 references + `scripts/scaffold.py`） | https://github.com/github/awesome-copilot/tree/main/skills/python-pypi-package-builder | 38858 | 2026-09-10 | MIT | 打包发布 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | GitHub 官方仓库中最完整的打包篇：src vs flat 决策、四种 build backend 的取舍、`py.typed`/PEP 561、Trusted Publishing（OIDC）、TestPyPI 演练。抽查 `py.typed`、PEP 440、`[project.scripts]` 三条与 packaging.python.org 一致 |
| 3 | github/awesome-copilot `skills/ruff-recursive-fix` | https://github.com/github/awesome-copilot/tree/main/skills/ruff-recursive-fix | 38858 | 2026-09-10 | MIT | ruff 修复循环 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | 唯一把「先 safe fix、再 `--unsafe-fixes` 且逐轮看 diff、`# noqa` 需理由」写成可执行循环的候选。runner 解析顺序（`uv run ruff` → `ruff` → `python -m ruff`）也直接可用 |
| 4 | github/awesome-copilot `skills/pytest-coverage` | https://github.com/github/awesome-copilot/tree/main/skills/pytest-coverage | 38858 | 2026-09-10 | MIT | 覆盖率门 | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE（merged，仅补充） | 只有 28 行，内容是覆盖率阈值门本身；作为「验证门」一句话的交叉校验用，不构成独立章节 |
| 5 | github/awesome-copilot `instructions/python-mcp-server.instructions.md` | https://github.com/github/awesome-copilot/blob/main/instructions/python-mcp-server.instructions.md | 38858 | 2026-09-10 | MIT | MCP server | 3 | 3 | 2 | 3 | 2 | 13 | MAYBE → reference | 主体是 MCP 协议与 FastMCP 用法，属未来 `mcp-server` skill；只用它的 lifespan / async 生命周期段落交叉校验 asyncio 一节，不合入正文 |
| 6 | getsentry/skills `skills/typing-exclusion-worker` | https://github.com/getsentry/skills/tree/main/skills/typing-exclusion-worker | 989 | 2026-09-07 | Apache-2.0 | 渐进式收严 typing | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE（merged） | 唯一一份把「大仓 typing 债怎么分批还」写成硬约束的候选：一次只摘掉分配到的排除项、先跑目标路径、禁止 blanket `# type: ignore`、必须窄化到 `ignore[code]` 并写原因 |
| 7 | getsentry/skills `skills/find-bugs` | https://github.com/getsentry/skills/tree/main/skills/find-bugs | 989 | 2026-09-07 | Apache-2.0 | 分支 diff 安全审查 | 2 | 3 | 2 | 3 | 2 | 12 | reference | 内容与语言无关（注入 / IDOR / TOCTOU / 会话），是 `code-review` 的范围。读它确认了「整仓找 bug」不属本 skill，正文不取任何内容 |
| 8 | getsentry/skills `languages/python.md`（路线图旧种子路径） | https://github.com/getsentry/skills | 989 | 2026-09-07 | Apache-2.0 | — | — | — | — | — | — | — | REJECT（路径已不存在） | 全树核实后该文件不在仓库中；当前等价物 `skills/security-review/languages/python.md` 属安全审计范围 |
| 9 | existential-birds/beagle `plugins/beagle-python/skills/python-code-review` | https://github.com/existential-birds/beagle/tree/main/plugins/beagle-python/skills/python-code-review | 80 | 2026-08-10 | Apache-2.0 | Python 评审 | 1 | 2 | 3 | 2 | 2 | 10 | INCLUDE（merged） | 价值在「不要报的东西」：Valid Patterns（`cast()` 在运行时检查之后是对的、空 `__init__.py` 合法、对接无 stub 的库时 `Any` 合理）与 Context-Sensitive Rules。正确性扣分见「冲突与裁决」第 4 条（PEP 8 79 列） |
| 10 | existential-birds/beagle `plugins/beagle-python/skills/pytest-code-review` | https://github.com/existential-birds/beagle/tree/main/plugins/beagle-python/skills/pytest-code-review | 80 | 2026-08-10 | Apache-2.0 | pytest 评审 | 1 | 2 | 3 | 3 | 2 | 11 | INCLUDE（merged） | `patch()` 要打在「被使用处」而非「定义处」、异步依赖用 `AsyncMock` 而非 `Mock`、fixture 作用域与测试隔离——三条都是真会咬人的点，且与官方文档一致 |
| 11 | giuseppe-trisciuoglio/developer-kit `plugins/developer-kit-python/rules/{language-best-practices,error-handling,project-structure,naming-conventions}.md` | https://github.com/giuseppe-trisciuoglio/developer-kit/tree/main/plugins/developer-kit-python | 343 | 2026-09-10 | MIT | 语言层规则 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE（merged） | 数据建模选型（Pydantic / dataclass / NamedTuple 各自的场合）、3 个以上参数用 keyword-only、`pathlib` 取代 `os.path`、内建泛型取代 `typing.List`。`paths` 专属字段需剥离 |
| 12 | wshobson/agents `plugins/python-development/skills/*`（16 个 skill） | https://github.com/wshobson/agents/tree/main/plugins/python-development | 39554 | 2026-09-07 | MIT | 语言/异步/类型/测试 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE（merged，选 6 个目录） | 教程成分偏重（大量「Pattern 1: Basic Async/Await」这类模型已知内容），但 `async-python-patterns` 的 sync/async 选型表与 `python-anti-patterns` 的清单（双层重试、暴露 ORM 模型、批处理吞掉部分失败、异步里阻塞）可用。只取 6 个目录 |
| 13 | laurigates/claude-plugins `python-plugin/skills/{pytest-advanced,ruff-linting,uv-project-management,basedpyright-type-checking}` | https://github.com/laurigates/claude-plugins/tree/main/python-plugin | 58 | 2026-09-10 | MIT | pytest/ruff/uv | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE（merged） | 配置形态最准确的一份（`[tool.pytest.ini_options]`、`asyncio_mode`、`[tool.coverage.*]`），插件表（cov / xdist / asyncio / mock / timeout）与面向 agent 的快速调用组合（`-x --tb=short -q`、`--lf`、`-n auto`）直接可用。`user-invocable`、`allowed-tools`、`created/modified/reviewed` 专属字段需剥离 |
| 14 | probabl-ai/skills `skills/python-code-style` | https://github.com/probabl-ai/skills/tree/main/skills/python-code-style | 122 | 2026-09-10 | BSD-3-Clause | lint 作业范围 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE（merged） | 唯一写清 lint 的**作业边界**的候选：只修本次改动触及的行，仓里既有的违规只报告不顺手修；一次修复尝试后仍失败就上报而不是反复自动改 |
| 15 | probabl-ai/skills `skills/data-science-python-stack`、`skills/python-env-manager`、`skills/python-api` | https://github.com/probabl-ai/skills | 122 | 2026-09-10 | BSD-3-Clause | numpy/pandas/sklearn；conda/pixi/poetry 多管理器 | 1 | 3 | 2 | 2 | 2 | 10 | REJECT（超出边界） | 数据分析栈被本 skill 的 `Do not use for` 明确排除；`python-env-manager` 并列 6 种环境管理器，与本 skill「uv 是唯一默认」的裁决相反 |
| 16 | gvre/skills `python-developer` | https://github.com/gvre/skills/blob/main/python-developer/SKILL.md | 5 | 2026-06-17 | MIT | 语言/工具/版本矩阵 | 1 | 2 | 2 | 2 | 2 | 9 | INCLUDE（merged，仅一条规则 + 版本矩阵） | 价值在一条元规则：评审既有代码时 `pyproject.toml` 是唯一事实源，不要用「默认值」覆盖项目已声明的 line-length / 类型检查器 / 布局。扣分点：正文写死「ty beta 0.0.22, Mar 2026」这种时间敏感表述，且 3.12–3.14 特性矩阵需按官方文档复核；带 `disable-model-invocation` 专属字段 |
| 17 | databricks-solutions/ai-dev-kit `.claude/skills/python-dev` | https://github.com/databricks-solutions/ai-dev-kit/blob/main/.claude/skills/python-dev/SKILL.md | 1894 | 2026-08-13 | NOASSERTION → 实读为专有 | uv/ruff/pytest/pyright | 1 | 2 | 2 | 2 | 0 | 7 | REJECT | 实读 `LICENSE.md`：Databricks 自有许可，「You may not use the Licensed Materials except in connection with your use of the Databricks Services」——不得作为 merged。内容上强制 pyright 且明确拒绝 mypy，是单厂商口径，与官方文档的中立立场不符 |
| 18 | rmyndharis/antigravity-skills `skills/python-pro` | https://github.com/rmyndharis/antigravity-skills/blob/main/skills/python-pro/SKILL.md | 1521 | 2026-08-02 | MIT | 泛 Python | 0 | 2 | 0 | 2 | 2 | 6 | REJECT | persona 式提示词（"You are a Python expert…"、"Use PROACTIVELY"），全篇是能力清单而非可执行规则；带 `metadata.model` 专属字段 |
| 19 | SpillwaveSolutions/mastering-python-skill-plugin | https://github.com/SpillwaveSolutions/mastering-python-skill-plugin | 6 | 2026-08-22 | 无许可（API `null`） | 泛 Python 教学 | 0 | 2 | 1 | 2 | 0 | 5 | REJECT | 定位是「从基础到生产的教学」，与「默认模型已经很聪明」冲突；无许可文件且无第二方交叉校验，不值得为它承担溯源成本 |
| 20 | s2005/uv-skill | https://github.com/s2005/uv-skill | 9 | 2025-11-01 | MIT | 仅 uv | 0 | 0 | 2 | 1 | 2 | 5 | REJECT | 最近推送距今 10 个月，>6 月直接 REJECT；uv 在此期间发布了多个版本（当前 0.12.12），内容已不可信 |
| 21 | cast42/python-minimal-boilerplate | https://github.com/cast42/python-minimal-boilerplate | 6 | 2026-07-17 | MIT | 项目模板 | 0 | 2 | 1 | 2 | 2 | 7 | REJECT | 是仓库模板而非 skill（`.agents/skills/` 里只有一条「照本仓结构初始化」的说明），可迁移的知识为零 |
| 22 | anthropics/skills | https://github.com/anthropics/skills | 175594 | 2026-09-03 | 无 LICENSE（API `null`） | — | — | — | — | — | — | — | REJECT（无对应 skill） | 全树只有 `skills/claude-api/python/*`，是 Claude API 的 Python SDK 用法，属 `ai-engineering` 范围 |
| 23 | openai/skills | https://github.com/openai/skills | 26833 | 2026-09-08 | 无 LICENSE（API `null`） | — | — | — | — | — | — | — | REJECT（无对应 skill） | Python 相关文件只有 `security-best-practices/references/python-{django,fastapi,flask}-web-server-security.md`，全部落在本 skill 排除的框架上 |
| 24 | mattpocock/skills | https://github.com/mattpocock/skills | 258595 | 2026-09-04 | MIT | — | — | — | — | — | — | — | REJECT（无对应内容） | 全仓 TypeScript 向；已是本仓 `code-review` / `typescript` 的上游，不含 Python 素材 |
| 25 | docs.astral.sh/uv（`astral-sh/uv` 0.12.12） | https://docs.astral.sh/uv/ | 89685 | 2026-09-10 | Apache-2.0 | uv 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（docs, merged） | 依赖字段四分（`project.dependencies` / extras / `dependency-groups` / `tool.uv.sources`）、`uv add --script`、`uv init --script`、inline metadata 下项目依赖被忽略、shebang `#!/usr/bin/env -S uv run --script`——全部据此逐条取证 |
| 26 | docs.astral.sh/ruff（`astral-sh/ruff` 0.16.6） | https://docs.astral.sh/ruff/ | 49575 | 2026-09-03 | MIT | ruff 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（docs, merged） | 默认 line-length 88、`target-version` 从 `requires-python` 反推、`select` 覆盖默认而 `extend-select` 追加、官方明确「Use ALL with discretion」并给出 E/F/UP/B/SIM/I 的推荐起点 |
| 27 | docs.pytest.org（`pytest-dev/pytest` 9.1.1） | https://docs.pytest.org/en/stable/ | 14495 | 2026-09-08 | MIT | pytest 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（docs, merged） | 决定性事实：`[tool.pytest]` 原生 TOML 表自 **pytest 9.0** 起支持，`[tool.pytest.ini_options]` 自 6.0 起支持；配置文件优先级 `pytest.toml` > `pytest.ini` > `pyproject.toml` > `tox.ini` > `setup.cfg`，且多个候选之间**不合并**，第一个命中的胜出 |
| 28 | typing.python.org（`python/typing`） | https://typing.python.org/en/latest/spec/ | 1783 | 2026-09-04 | NOASSERTION（PSF 文档仓） | 类型系统规范 | 3 | 3 | 3 | 3 | 1 | 13 | INCLUDE（docs, merged） | PEP 695 语法下型变由检查器**推断**（不再写 `covariant=True`）；`@runtime_checkable` 只检查属性/方法**存在**，不检查签名 |
| 29 | docs.python.org `library/asyncio-task.html`（3.14） | https://docs.python.org/3/library/asyncio-task.html | — | — | PSF-2.0 | asyncio 官方文档 | 3 | 3 | 3 | 3 | 1 | 13 | INCLUDE（docs, merged） | 事件循环只持有 task 的**弱引用**（必须自留强引用）；`gather(return_exceptions=False)` 首个异常传播但**不取消**其余 awaitable，而 `TaskGroup` 会取消；捕获 `CancelledError` 后须重新抛出，否则 `TaskGroup`/`timeout` 会误动作；`asyncio.timeout` 把 `CancelledError` 转成 `TimeoutError` |
| 30 | packaging.python.org（PyPA） | https://packaging.python.org/en/latest/ | — | — | 混合（CC-BY / MIT） | 打包规范 | 3 | 3 | 3 | 3 | 1 | 13 | INCLUDE（docs, merged） | `pyproject.toml` `[project]` 字段、inline script metadata 规范、`py.typed` / PEP 561、src 布局的理由，用于校正候选 2 与候选 1 的打包段落 |

## 深度审查

### 1. trailofbits/skills `modern-python`（主干，CC-BY-SA-4.0）

结构：`SKILL.md`（333 行）+ 9 个 references + 2 个 templates + 一套 `hooks/shims`（把 `pip`/`python`/`pipx`
命令劫持到 uv）。frontmatter 只有 `name` + `description`，干净。质量上这是候选中唯一一份把
「决策树 → 快速开始 → 完整设置 → 迁移 → 速查」串成闭环的，`migration-checklist.md` 里
「找残留的旧 linter pragma」「找缺失的 `__init__.py`」这类清理动作是真实迁移里会漏的。

不能直接用的部分：
- `hooks/` 与 `templates/` 是 Claude 插件机制的产物（`hooks.json` + bash shims），本仓库
  skill 不携带 hook，`agents/openai.yaml` 也是 agent 专属，全部丢弃。
- 强推 `ty` 取代 mypy/pyright（见裁决 1）、`select = ["ALL"]`（裁决 2）、`prek` 取代
  pre-commit（裁决 5）三处是本仓不能照抄的口径。
- 许可是 CC-BY-SA-4.0：share-alike，与本仓 MIT 不相容。处理方式与 Batch 1 的 `code-review`
  合入 `trailofbits/skills` `differential-review` 时一致——**只取清单语义与阶段结构，每句话
  重写**，不复制任何表格、模板或句子。

与其他候选的重叠：uv 命令表与候选 13 大面积重叠，但候选 13 的 pytest / coverage 配置更准确；
打包段落与候选 2 重叠，候选 2 更完整（四种 backend、Trusted Publishing）。

### 2. github/awesome-copilot（GitHub 官方，MIT）

三个目录各司其职、彼此不重叠：`python-pypi-package-builder` 是打包与发布，
`ruff-recursive-fix` 是 lint 修复循环，`pytest-coverage` 是覆盖率门。前者体量最大（444 行 +
9 个 references），带 `scripts/scaffold.py`；它的「AI Agent Instruction: Read this entire file
before writing a single line of code」是典型的 agent 绑定指令，本仓不采用（我们靠
`description` 触发 + Topic router 按需读）。`ruff-recursive-fix` 的输入参数化（`target_path`、
`ruff_runner`、`rules_select`…）在本仓写成一个 workflow 清单即可，不需要保留「Inputs」表。

抽查正确性：`py.typed` 需在包内且在 `[tool.setuptools.package-data]`/等价字段中声明、
PEP 440 的 pre-release 记法、`[project.scripts]` 生成 console script——三条与
packaging.python.org 一致。

### 3. getsentry/skills `typing-exclusion-worker`（Apache-2.0）

frontmatter 干净（`name` + `description`）。它不是「怎么写类型」而是「怎么在一个几十万行的
仓库里把类型债还掉而不引爆 CI」：一个批次只摘掉分配到的模块、先跑目标路径拿快反馈、
改动不外溢到别的域、必须窄化 `ignore[code]` 并写理由、批次太大就上报拆分。这套东西在其它
候选里完全没有，是本 skill「渐进式收严」一节的骨架。

它的「Required Output Template」（Batch Summary / Modules Removed / Validation…）是给
orchestrator 消费的，本仓不需要那层协议，只保留其中「验证要分别报 mypy / 测试 / pre-commit
三项结果」的要求。

### 4. existential-birds/beagle `beagle-python`（Apache-2.0）

两个 review skill 的 frontmatter 干净，但正文里 `[review-verification-protocol](../review-verification-protocol/SKILL.md)`
是跨 skill 相对链接（上游交叉引用残留），本仓禁止，剥离。
`python-code-review` 的最大价值是**反向清单**：哪些看起来像问题的东西不要报
（运行时检查之后的 `cast()`、空 `__init__.py`、对接无 stub 库时的 `Any`、有理由的 `noqa`），
以及「只在有更具体异常类型可用时才报泛化 except」这类条件化规则。它把假阳性成本当成一等
问题，这和本仓 `code-review` 的第 7 条同源。
`pytest-code-review` 的三条（`patch` 打在使用处、异步依赖用 `AsyncMock`、yield fixture 的清理）
经官方文档复核无误。

### 5. laurigates/claude-plugins `python-plugin`（MIT）

17 个细粒度 skill（`uv-run`、`uv-workspaces`、`ruff-linting`、`ty-type-checking`…），
拆得过细，但配置片段是候选中最准的：`[tool.pytest.ini_options]`、`asyncio_mode = "auto"`、
`[tool.coverage.run] branch = true`、`exclude_lines` 含 `if TYPE_CHECKING:`。
frontmatter 带 `user-invocable`、`allowed-tools`、`created`/`modified`/`reviewed` 四类专属字段，
全部剥离。它的「Agentic Optimizations」表（不同场景该用哪串 pytest 参数）对 agent 实用，
本仓收进 pytest reference。

### 6. wshobson/agents `python-development`（MIT）

体量最大（16 个 skill，多数带 `references/details.md`），但写法是教程：`async-python-patterns`
前 160 行在教 `async def`/`gather`/`create_task` 的基本用法，这些模型已知，按标准第 3 节
「不重复模型已知的常识」应当整段丢弃。真正有价值的是两处：
`async-python-patterns` 开头的 sync/async 选型表（CPU 密集 → 进程池；混合 → `to_thread`；
少量连接的脚本 → 保持同步）与「一条调用链要么全同步要么全异步」；
`python-anti-patterns` 的清单里有几条不是常识：应用层与客户端库**双层重试**、
批处理静默吞掉部分失败、把 ORM 模型直接当响应模型。`python-type-safety` 的 `Result[T, E]`
示例里自带两个 `# type: ignore[return-value]`，恰好是本 skill 要禁止的写法，不取。

### 7. probabl-ai/skills `python-code-style`（BSD-3-Clause）

`description` 长达 30 行、混入 `organize-ml-workspace` / `python-env-manager` / `update-config`
等同仓 skill 名，还带 PostToolUse hook 的讨论——这些都是上游自身栈的绑定，剥离。
留下的两条是真正可迁移的：**只修本次触及的行**（仓里既有的 D 规则违规只报告不顺手修，
避免 PR 范围扩散）与**一个文件只尝试修一次，仍失败就上报**（避免 agent 在自动修复里打转）。

### 8. gvre/skills `python-developer`（MIT）

714 行单文件 + 7 个 references，星数只有 5、最近推送 2026-06-17（近 3 个月），
按量表刚过 INCLUDE 线。它唯一不可替代的贡献是「Project Overrides」一节的元规则：
**评审既有代码时 `pyproject.toml` 是唯一事实源**，不要用 skill 的默认值去覆盖项目已声明的
line-length / 类型检查器 / 测试布局；只有新建项目时才用默认值。这条正好治住候选 1 和
候选 17 那种「一律换成我推荐的工具」的倾向。其余内容（版本特性矩阵）改按 docs.python.org
复核后使用；正文里「ty beta 0.0.22（Mar 2026）」是时间敏感表述，本仓标准禁止，不取写法。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 默认类型检查器：ty 还是 mypy/pyright | 候选 1（trailofbits）：`mypy / pyright` → `ty`，理由是快，并给出「删掉 mypy.ini、装 ty」的迁移步骤；候选 16（gvre）：ty 是「新项目默认」但标注 beta；候选 17（databricks）：只许 pyright、明确拒绝 mypy；候选 6（getsentry）实际用 mypy | **既有项目沿用项目已配置的检查器；新项目默认 mypy 或 pyright，ty 作为逃生口（明确标注 beta）。** 正文只给这一种做法 | `astral-sh/ty` README 自述 "ty is currently in beta"，最新 release 0.0.80（2026-09-09），版本号仍在 0.0.x。按「更新 > 更旧」不能压过「官方自述尚未稳定」；按「官方厂商 > 社区」，Astral 自己的状态声明优先于第三方 skill 的推荐 |
| 2 | ruff 规则集起点：`select = ["ALL"]` 还是显式集合 | 候选 1：`select = ["ALL"]` + 少量 ignore，并写进「最佳实践清单」；候选 13：`select` 给具体前缀 | **显式列出规则前缀（E, F, UP, B, SIM, I 起步），逐组扩；`ALL` 只在 ruff 版本被锁定时使用。** | ruff 官方 linter 文档的 recommended guidelines 原文：「Prefer `lint.select` over `lint.extend-select`」「**Use `ALL` with discretion. Enabling `ALL` will implicitly enable new rules whenever you upgrade.**」「Start with a small set of rules (`select = ["E", "F"]`)」。这是官方厂商对社区的直接否定 |
| 3 | pytest 在 `pyproject.toml` 里的配置表名 | 候选 1：`[tool.pytest]`；候选 13、候选 2：`[tool.pytest.ini_options]` | **两者都合法但有版本门槛：`[tool.pytest]`（原生 TOML 类型）需 pytest ≥ 9.0，`[tool.pytest.ini_options]` 自 6.0 起可用。项目 pin 的 pytest < 9 时用 `[tool.pytest]` 会被静默忽略，整表失效。** 正文按此写成一条版本敏感规则，而不是二选一 | docs.pytest.org「Configuration file formats → pyproject.toml」：`[tool.pytest]` 标注 "supported since pytest 9.0"，`[tool.pytest.ini_options]` 标注 "supported since pytest 6.0"。候选 1 用了前者却把 `requires-python`/依赖写成不限 pytest 版本，属漏标 |
| 4 | 行宽 | 候选 9（beagle）：PEP 8，≤79 列（docstring ≤72）；候选 1：100；候选 16：120；ruff 默认 88 | **不写数字：读项目 `pyproject.toml`；项目没声明时用 ruff 默认 88。** | ruff 配置文档给出的默认值 `line-length = 88`（注释 "Same as Black"）。候选 9 的 79 列是 PEP 8 原文，但在装了 ruff 的仓库里由配置决定，硬写 79 会与 formatter 打架。候选 16 的「项目配置是唯一事实源」这条元规则在此适用 |
| 5 | pre-commit 还是 prek | 候选 1：`prek` 取代 pre-commit，理由是快、无需 Python 运行时 | **本 skill 不指定 hook 运行器**，只要求「lint / 类型 / 测试三道门在提交前都跑过」；hook 工具属项目基础设施选择 | 单一社区上游主张、无第二方交叉校验，且 prek 与本 skill 的核心（uv/ruff/pytest/typing）无耦合。按标准第 3 节「只给一个默认方案 + 一个逃生口，不罗列多个可选库」，宁可不写 |
| 6 | `asyncio.gather` 还是 `TaskGroup` | 候选 12：以 `gather` 为主线介绍，`TaskGroup` 只在末尾提及；候选 11：明确「优先 `TaskGroup`」 | **默认 `TaskGroup`；只有确实需要「保留每个位置的结果 / 用 `return_exceptions=True` 收集异常」时才用 `gather`。** | docs.python.org asyncio 文档在 `gather` 条目下的 Note 原文说明：子任务抛异常时 `TaskGroup` 会取消其余任务，`gather` **不会**（"Other awaitables in the aws sequence won't be cancelled and will continue to run"）。官方文档直接给出取舍 |
| 7 | 环境管理器 | 候选 15（probabl）并列 conda / pixi / poetry / hatch / pip-venv / uv 六种；候选 1、13、16、17 一致选 uv | **uv 是唯一默认**；遇到既有的 poetry/conda 项目时按候选 16 的元规则沿用项目现状，不主动迁移，除非用户要求 | 「更新 > 更旧」+ 五家上游中的四家一致；且并列六种管理器与标准第 3 节的「不罗列多个可选库」直接冲突 |
| 8 | 「整仓找 bug / 安全审查」归谁 | 候选 7（getsentry find-bugs）把注入、IDOR、TOCTOU 做成 Python 无关的整仓清单 | **不进本 skill。** 本 skill 只保留会咬人的**语言级**运行期陷阱（可变默认参数、事件循环弱引用、`except` 吞掉 `CancelledError`），diff 评审归 `code-review` | 本仓已有 `code-review` skill，其 Scope 明确覆盖「对一个 diff 的评审 + 安全视角」；重复即两处事实源 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `trailofbits-modern-python` | trailofbits/skills `plugins/modern-python/skills/modern-python` | merged（仅结构与清单语义） | 项目 / 单文件脚本的分流结构、`[dependency-groups]` 取代 `[project.optional-dependencies]` 的理由、四条迁移路径（requirements.txt+pip、setup.py、flake8+black+isort、旧类型检查器）的阶段划分、迁移后清理清单的条目语义。CC-BY-SA-4.0：不复制任何句子 / 表格 / 模板 |
| `awesome-copilot-python` | github/awesome-copilot `skills/python-pypi-package-builder`、`skills/ruff-recursive-fix`、`skills/pytest-coverage` | merged | 打包发布全链（src vs flat 判据、build backend 取舍、`py.typed`/PEP 561、Trusted Publishing、TestPyPI 演练、PyPI 名与 import 名的分离）；ruff 的 safe→unsafe 分级修复循环与 `# noqa` 需理由；覆盖率阈值作为验证门 |
| `getsentry-typing` | getsentry/skills `skills/typing-exclusion-worker` | merged | 渐进式收严 typing 的整套硬约束：按模块分批摘排除项、先跑目标路径、改动不外溢、禁止 blanket ignore 且必须窄化到 `ignore[code]` 并写理由、批次过大即拆 |
| `beagle-python` | existential-birds/beagle `plugins/beagle-python/skills/{python-code-review,pytest-code-review}` | merged | 假阳性反向清单（不该报的合法写法）与条件化规则；`patch` 打在名字被查找处、异步依赖用 `AsyncMock`、fixture 作用域与测试隔离的评审要点 |
| `laurigates-python` | laurigates/claude-plugins `python-plugin/skills/{pytest-advanced,ruff-linting,uv-project-management,basedpyright-type-checking}` | merged | pytest / coverage 的准确配置形态、插件矩阵（cov/xdist/asyncio/mock/timeout）、面向 agent 的 pytest 调用组合；ruff lint 与 format 是两个命令 |
| `wshobson-python` | wshobson/agents `plugins/python-development/skills/{async-python-patterns,python-anti-patterns,python-type-safety,python-testing-patterns,python-resource-management,uv-package-manager}` | merged | sync/async 选型表与「一条调用链不混用」；双层重试、批处理吞掉部分失败、暴露 ORM 模型等非常识性反模式；Protocol / 泛型 / 收窄的条目盘点 |
| `developer-kit-python` | giuseppe-trisciuoglio/developer-kit `plugins/developer-kit-python/rules/*` | merged | 数据建模选型（Pydantic 用于边界校验 / dataclass 用于内部结构 / NamedTuple 用于轻量不可变记录）、3 个以上参数用 keyword-only、`pathlib` 取代 `os.path`、内建泛型取代 `typing.List` |
| `probabl-python-style` | probabl-ai/skills `skills/python-code-style` | merged | lint 的作业边界：只修本次触及的行、既有违规只报告；一个文件一次修复尝试后仍失败就上报 |
| `gvre-python` | gvre/skills `python-developer` | merged | 元规则：评审既有代码时 `pyproject.toml` 是唯一事实源，默认值只用于新建项目 |
| `awesome-copilot-mcp-python` | github/awesome-copilot `instructions/python-mcp-server.instructions.md` | reference | 交叉校验 asyncio 生命周期（lifespan / 启动关闭钩子）的写法，确认本 skill 的 TaskGroup 与取消规则不与 MCP 场景冲突。MCP server 本身不属本 skill |
| `getsentry-findbugs` | getsentry/skills `skills/find-bugs` | reference | 读它确认整仓 / diff 级 bug 与安全审查属 `code-review` 范围，本 skill 只留语言级运行期陷阱。未复制内容 |
| `uv-docs` | docs.astral.sh/uv | merged（docs） | 依赖字段四分、`uv add/remove/sync/run/lock/build/publish` 语义、PEP 723（`uv init --script`、`uv add --script`、`dependencies` 必填、inline metadata 忽略项目依赖）、shebang 形式 |
| `ruff-docs` | docs.astral.sh/ruff | merged（docs） | 默认 line-length 88、`target-version` 从 `requires-python` 反推、`select` vs `extend-select` 语义、官方推荐规则起点与「谨慎用 ALL」、`per-file-ignores` |
| `pytest-docs` | docs.pytest.org | merged（docs） | 配置表名的版本门槛（`[tool.pytest]` ≥9.0 / `ini_options` ≥6.0）、配置文件优先级且不合并、fixture 作用域与 `--strict-markers`/`filterwarnings` 的作用 |
| `typing-docs` | typing.python.org | merged（docs） | PEP 695 型变推断、`Protocol` 与 `@runtime_checkable` 的边界（只查存在性）、`TypedDict` 的必填/选填限定 |
| `python-docs` | docs.python.org（asyncio / typing 标准库） | merged（docs） | 事件循环只持弱引用、`gather` 不取消兄弟任务而 `TaskGroup` 会、`CancelledError` 必须重新抛出、`asyncio.timeout` 转 `TimeoutError`、`to_thread` 的定位 |
| `pypa-docs` | packaging.python.org | merged（docs） | `[project]` 字段规范、inline script metadata 规范、`py.typed`/PEP 561、src 布局的理由 |

## 基线缺口

无 skill（`uv run tools/run_evals.py python --baseline`，Claude Opus 5 · medium）时，
各场景未达成的 `expected_behavior`。基线整体很强——三个正例的诊断主线（可变默认参数、
session fixture 污染、`create_task` 弱引用、异步里阻塞、`Protocol`、per-module 收严）
全部自力达成，所以缺口集中在**版本门槛与收尾纪律**这两类「知道才知道」的点上。

第一轮基线跑完后修了两条评测标准（S1 加「收尾清理」一条；S3 第 5 条原文把
`patch` 的查找语义写错了，改成正确表述），并对场景 1、3 重跑了基线，下表是重跑后的判定。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 | #6 用 ruff 取代 black + isort + flake8 | 基线把三件套原样搬进 `[dependency-groups] lint`，还新增了 `[tool.isort] profile = "black"`，并在正文写「后续建议用 ruff 替换」——把该做的迁移推给了下一次 |
| 1 | #7 审计被迁移作废的残留 | 完全没做：没查 README / CI / Makefile / pre-commit 里的旧命令，也没查旧 linter 的 pragma 与配置节。它反而给要被删掉的工具加了新配置 |
| 1 | #1 依赖变更走 `uv add`（部分达成） | 迁移本身是手写 `pyproject.toml`，没用 `uv add -r requirements.txt`；只在 README 的「常用命令」里写了以后加依赖用 `uv add`。未建议 `uv pip install`，故判部分达成 |
| 2 | #2 载荷用 TypedDict 并把 `region` 标为非必填 | 基线主动拒绝了 TypedDict，输入侧用 `Mapping[str, Any]`；输出 TypedDict 里 `region: str`，没有用 `NotRequired`，键的「可缺失」与值的「可为 None」被混为一谈 |
| 2 | #5 不留放宽用的 `Any` | 基线明确保留了两处 `Any`（`user_id`、`load_events` 返回），理由是「`json.loads` 本来就是 Any」。它没有走「先窄化再用 / 用 `object` 逼迫收窄」这条路 |
| 3 | #4 `[tool.pytest]` 的版本门槛 | 判成了「pytest 只读 `[tool.pytest.ini_options]`，`[tool.pytest]` 不是识别的表名」。这是错的：pytest 9.0+ 支持原生 TOML 表，而它自己跑的正是 pytest 9.1.1。修法（搬到 `ini_options`）碰巧可用，理由与版本门槛都错 |
| 3 | #5 `patch` 目标的两半理由 | 只讲了「patch 上下文在后台任务执行前就退出了」这一半；没讲另一半——这里 `patch("httpx.get")` 之所以有效是因为 `orders_service` 用的是 `import httpx`（调用时才取属性），若换成 `from httpx import get` 就必须打在 `orders_service.get` |
| 4 | — | 负例只验 `skill_read == false` |

### 就着基线争议点做的实测（写进 skill 正文的依据）

同一份夹具 `pyproject.toml`（`markers = ["slow: ..."]` 写在 `[tool.pytest]` 下）：

```
pytest 9.1.1 → pytest --markers 列出 `@pytest.mark.slow: takes more than a second`
pytest 8.3.5 → PytestUnknownMarkWarning: Unknown pytest.mark.slow（整表未生效）
```

这条实测同时确认了两件事：基线的结论错了，而夹具本身的坑是真的——`pytest>=8.3`
这个约束让「配置生效与否」取决于锁文件解到哪个版本。正文与 `references/pytest.md`
按此写成版本敏感规则并标 `[verified]`。

另一条实测：pytest 9.1.1 下未被插件接管的 `async def test_*` 会**失败**并给出
"async def functions are not natively supported"，而不是旧版本那种「告警后跳过」。
`references/pytest.md` 初稿按旧行为写错了，已按实测改正。

## 评测结果

两组都用 `anthropic/claude-opus-5` + `medium` 思考（`tools/run_evals.py` 默认，未传
`--model` / `--thinking`）。逐条读 `answer.md` 与 `events.jsonl` 人工判定，`✓` = 达成、
`~` = 部分达成、`✗` = 未达成。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 setup.py+requirements → uv | claude-opus-5:medium | 无（baseline） | false | #1 `~` / #2 ✓ / #3 ✓ / #4 ✓ / #5 ✓ / **#6 ✗** / **#7 ✗** | 把 black+isort+flake8 原样搬进 `lint` 组并新增 `[tool.isort]`，ruff 推给「后续」；无任何残留审计 |
| 1 | claude-opus-5:medium | 有 | true | #1 ✓ / #2 ✓ / #3 ✓ / #4 ✓ / #5 ✓ / **#6 ✓** / #7 `~` | ruff 取代三件套并写明「extra 会随 wheel 发布 = 把 linter 变成公开 API」；用 `uv add --script` 加 PEP 723 块；`uv sync --all-groups --locked` 做 CI 门。#7 只做到全树盘点（`glob **/*` 含 gitignored）+ 删三个遗留文件，没有报告 pragma / 配置节的扫描结果——夹具里本来也没有可清理的残留 |
| 2 pipeline.py 加类型 | claude-opus-5:medium | 无（baseline） | false | #1 ✓ / **#2 ✗** / #3 ✓ / #4 ✓ / **#5 ✗** / #6 ✓ | 主动拒绝 TypedDict，输入侧用 `Mapping[str, Any]`，输出 TypedDict 里 `region: str` 无 `NotRequired`；保留两处 `Any` |
| 2 | claude-opus-5:medium | 有 | true | #1 ✓ / **#2 ✓** / #3 ✓ / #4 ✓ / **#5 ✓** / #6 ✓ | `RawEvent`/`Profile`/`EnrichedRow` 三个 TypedDict，`region: NotRequired[str]` 并说明「原码 `.get("region", "unknown")` 就是在说这个键可缺失」；全模块零 `# type: ignore`，`Any` 收敛到 `load_events` 里一处带理由的 `cast`；per-module `[[tool.mypy.overrides]] strict = true` 并指出 `exclude` 是正则、优先级高于命令行显式路径 |
| 3 pytest 隔离 + asyncio + 配置表名 | claude-opus-5:medium | 无（baseline） | false | #1 ✓ / #2 ✓ / #3 ✓ / **#4 ✗** / **#5 `~`** / #6 ✓ | #4 判成「`[tool.pytest]` 不是 pytest 识别的表名」，与它自己运行的 pytest 9.1.1 事实相反；#5 只讲了 patch 上下文提前退出这一半 |
| 3 | claude-opus-5:medium | 有 | true | #1 ✓ / #2 ✓ / #3 ✓ / **#4 ✓** / #5 `~` / #6 ✓ | #4 完全正确：「该表名只有 pytest 9.0+ 才读，而 test 组下限是 `pytest>=8.3`，任何 8.x 环境里整张表被静默丢弃」，并用 `pytest==8.3.5` 复跑 `pytest --markers` 取证；额外把 `gather` 换成 `TaskGroup` 并给出理由（gather 不取消兄弟任务），这是 Core rule 20 |
| 4 TypeScript 负例 | claude-opus-5:medium | 有 | **false** | 三条全部达成 | 纯 TypeScript 判别式联合答案；`grep -ciE 'TypedDict\|Protocol\|mypy\|python'` 命中 0，未加载本 skill |

结论：**通过**。基线未达成而有 skill 时达成的行为共四条——场景 1 的 #6（ruff 取代
black+isort+flake8）、场景 2 的 #2（TypedDict + `NotRequired`）与 #5（不留放宽用的 `Any`）、
场景 3 的 #4（`[tool.pytest]` 的 pytest 9.0 门槛）。其中场景 3 的 #4 是最强证据：基线不是
漏了，而是给出了**与事实相反**的解释，而有 skill 时给出了正确的版本门槛并自行取证。
负例 `skill_read == false`，无误触发。

仍未完全达成的两条：场景 1 的 #7（残留审计只做到盘点层）与场景 3 的 #5（`patch` 目标只讲了
一半理由）。两者都不是 skill 缺内容——`references/uv-projects.md` 的「Cleanup after a
migration」与 `references/pytest.md` 的 Mocking 节都写了，属于 Topic router 未被展开读取；
SKILL.md 的 workflow 清单里已各留一条指向。不构成阻塞，记为下次同步时观察项。

## 备注

### CC-BY-SA-4.0 的处理（trailofbits/skills）

`trailofbits/skills` 全仓 CC-BY-SA-4.0。share-alike 条款要求派生作品同样以 CC-BY-SA 发布，
与本仓统一的 MIT 不相容，因此按 Batch 1 `code-review` 合入同一上游 `differential-review` 时
建立的先例处理：

1. `relation: merged`，但 `notes` 明确写「只取清单语义与阶段结构，未复制任何散文、表格或模板」。
2. 实际操作：读完 `SKILL.md` 与 9 个 references 后**关掉文件**，按本仓自己的章节顺序重新组织，
   每条规则重新论证并重新落笔；凡与官方文档不一致处（裁决 1/2/3/5）直接改写为官方口径，
   这本身也降低了措辞雷同的风险。
3. 未取用其 `templates/`（`pre-commit-config.yaml`、`dependabot.yml`）与 `hooks/`（bash shims），
   这两类是可直接复制的成品文件，风险最高。

### 其它许可注意

- `probabl-ai/skills` 是 BSD-3-Clause（三条款 BSD 属规则表的 BSD 一档，可 merged）。
- `databricks-solutions/ai-dev-kit` 的 GitHub API 报 `NOASSERTION`，实读 `LICENSE.md` 为
  Databricks 自有许可（使用范围限定于 Databricks Services），按规则表属 Proprietary，
  已 REJECT，不进 `SOURCES.yaml`。
- `python/typing` 的 API 许可也是 `NOASSERTION`（PSF 文档许可 + 各 PEP 自身条款），
  本 skill 只把它当 `kind: docs` 的事实来源，不复制条文，`license` 写 `NOASSERTION`。
- `anthropics/skills`、`openai/skills`、`SpillwaveSolutions/*` 的 API 许可为 `null`，
  但三者都已 REJECT，无需按「无许可但公开」规则处理。

### 未来同步时要盯的上游

- `astral-sh/ty`：一旦发布 1.0（脱离 beta），裁决 1 需要重新审：新项目默认检查器可能要换成 ty。
- `pytest-dev/pytest`：9.x 的 `[tool.pytest]` 原生表若成为主流，裁决 3 的版本门槛表述要收紧
  （届时 `ini_options` 变成兼容路径）。
- `github/awesome-copilot`：每天都在推送，`paths` 只列本 skill 实际用到的三个目录 + 一个
  instruction 文件，靠 `check_upstream.py` 的路径过滤压掉噪声。
- `probabl-ai/skills`：若 `python-code-style` 的内容进一步绑定其数据科学栈，可能降为 reference。
