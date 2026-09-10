# HyperSkills skill 编写标准

本文件是全仓库唯一的结构 / 写作 / 溯源规范。`tools/validate_skills.py` 的每条检查都对应
本文的一条条款。执行者按此原样落地，**不得另立约定**。

规范依据（均已核实）：

- Agent Skills 规范 <https://agentskills.io/specification>
- Anthropic《Skill authoring best practices》
  <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
- anthropics/skills `skill-creator`、obra/superpowers `writing-skills`

---

## 1. frontmatter（精确形式）

```yaml
---
name: <目录名>
description: "<英文；what + when + 触发关键词 + 一句否定边界 'Do not use for ...'；80–1024 字符>"
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "YYYY.MM.DD"
  category: platform | framework | task | meta
---
```

### 1.1 字段约束

| 字段 | 约束 |
|---|---|
| `name` | 必填；`^[a-z0-9]+(-[a-z0-9]+)*$`；≤64 字符；**必须等于所在目录名**；不得含保留字 `anthropic` / `claude`；不得含 XML 标签 |
| `description` | 必填；本仓库要求 80–1024 字符；第三人称（`Guides…` / `Reviews…`），禁止 `I can…` / `You can…`；必须含否定边界 `Do not use for …`；最核心用途放最前（Codex 会截断） |
| `license` | 必填；本仓库统一 `MIT (upstream attributions in NOTICE.md)` |
| `metadata.author` | 必须为 `HyperSkills` |
| `metadata.version` | `^\d{4}\.\d{2}\.\d{2}$`，日期版本；每次合入 / 同步后改为当天 |
| `metadata.category` | `platform` \| `framework` \| `task` \| `meta` |

### 1.2 顶层键白名单

只允许规范字段：`name`、`description`、`license`、`compatibility`、`metadata`、`allowed-tools`。

**禁止**任何 agent 专属字段：`user-invocable`、`paths`、`globs`、`argument-hint`、`model`、
`disable-model-invocation`、`metadata.pathPatterns`、`metadata.promptSignals`、`metadata.priority` 等。
合入上游内容时必须剥离这些字段。

### 1.3 正文禁用项

- `${CLAUDE_PLUGIN_ROOT}`、`${CLAUDE_SKILL_DIR}` 等 harness 变量
- `WebFetch` 等特定 agent 的工具名（引用 MCP 工具时用全限定名 `Server:tool`）
- `` !`cmd` `` 动态注入、`@file` 强制加载
- 上游交叉引用残留（如 `superpowers:`）
- 反斜杠路径分隔符；路径一律正斜杠

脚本调用一律用相对 skill 根目录的路径（`scripts/x.py`），并在 SKILL.md 中该类路径首次出现
之前写一句：`Paths below are relative to this skill's directory.`

---

## 2. SKILL.md 正文固定章节顺序

缺省章节可省略，**顺序不可变**：

1. `## Scope` — 覆盖范围 + 明确不覆盖什么（否定范围，防止编造）
2. `## Read first` — 每次任务前必读的 reference（仅在存在"过期 API 索引"这类文件时）
3. `## Core rules` — 硬性不变量清单（违反即 bug），每条一行附一句 why；≤25 条
4. `## Workflows` — 按任务形态（implement / review / debug / migrate …）给 `- [ ]` 清单，
   每个 workflow 以一个**具名验证门**结尾（必须通过的命令或检查）
5. `## Topic router` — 表格 `| Topic | Read when | File |`，指向 `references/`
6. `## Output format` — review 型 workflow 的输出契约（按文件分组、`path:line - finding`、before/after）
7. `## Environment` — 依赖与安装命令（仅有依赖时）

### 2.1 篇幅

| 文件 | 建议 | 硬上限 |
|---|---|---|
| `SKILL.md` | 150–400 行 | 500 行 |
| `references/*.md` | ≤400 行 | 600 行 |

>100 行的 reference 顶部必须加 `## Contents` 目录（模型可能只预读文件头部）。

---

## 3. 写作规则

- **默认假设模型已经很聪明**：不重复模型已知的常识；只写边缘情况、软弃用、静默失败、
  版本差异、易错点——teach the failure, not the API。每段都要能回答"这段值它的 token 吗"。
- **自由度与脆弱性匹配**：多种做法皆可 → 启发式（高自由度）；有首选模式 → 带参数的模板 /
  伪代码（中）；脆弱且必须按序 → 精确命令并注明"不要改动参数"（低）。
- **祈使语气，解释 why**；禁止满篇 ALL-CAPS MUST/NEVER。
- **触发条件全部写进 `description`**，正文不重复"何时使用"。
- **只给一个默认方案 + 一个逃生口**：`Use X. For <特殊情况> use Y instead.` 不罗列多个可选库。
- **术语全篇一致**：一个概念只用一个词。
- **不写时间敏感表述**（"2025 年 8 月前用旧 API"）。弃用内容放在 `## Old patterns` 节的
  `<details><summary>…</summary>` 折叠块里，主线只写当前做法。
- **版本敏感规则标注可用性底线**，如 `(iOS 26+)`、`(Next.js 16.3+)`。版本敏感的 reference
  顶部写 `Verified against: <tool/OS version>`（写版本，不写日期条件）。
- **不确定的规则标注置信度**：`[verified]`（本仓库验证过）、`[official]`（官方文档/官方 skill）、
  `[community]`。
- **必须取最新文档而非猜 API 的场景**，显式写出取文档的命令，如 `npx shadcn@latest docs <component>`。
- **输出格式用模板模式**：严格场景写 `Use exactly this template`，灵活场景写
  `sensible default, adapt`；风格依赖示例的场景给 2–3 组 input→output 对。
- **上游冲突裁决**：按「官方厂商 > 公认专家 > 社区」和「更新 > 更旧」，并对照官方文档核实。
  裁决结果写进 `research/<skill>.md` 的「冲突与裁决」节，**正文只写裁决后的一种做法**。
- **图示只用 ASCII 或 mermaid**；上游的 Graphviz `dot` 块一律删除或转 ASCII。

---

## 4. `references/` 命名与来源标注

- 文件名 kebab-case 主题名。单 skill 超过 10 个文件时用前缀分组
  （如 `swiftui-*.md`、`swift-*.md`、`nextjs-*.md`）。
- 每个 reference 的**最后一行**必须是来源注释：

  ```
  <!-- sources: <id1>, <id2> -->
  ```

  其中每个 id 必须在该 skill 的 `SOURCES.yaml` 中存在。
- **reference 之间不得互相链接**（只允许 SKILL.md → reference 一层）。
- `references/` 下每个文件都必须被 SKILL.md 引用；未被引用 = 死重量。

---

## 5. `scripts/` 规则

- **自包含**。Python 脚本顶部写 PEP 723 内联依赖块，可用 `uv run scripts/x.py` 直接运行：

  ```python
  # /// script
  # requires-python = ">=3.11"
  # dependencies = ["..."]
  # ///
  ```

  Node 脚本配 `scripts/package.json`。
- **解决而非推诿**：常见错误（文件不存在、权限不足、缺依赖）在脚本内处理并给出可操作的
  错误信息，如 `Field 'x' not found. Available: a, b, c`。
- **无魔法数**：所有常量带一行注释说明取值理由。
- 不引用任何 harness 变量。
- SKILL.md 中必须明确该脚本是 **Run**（执行）还是 **See**（作为参考阅读）。
- 每个脚本在 SKILL.md 中至少被引用一次。
- 批量 / 破坏性操作采用 **plan → validate → execute** 模式：先产出结构化计划文件，
  用脚本校验后再执行。

---

## 6. `evals/evals.json`（每个 skill 必备，评测先行）

Phase B 结束、Phase C 动笔之前先写 ≥3 个评测场景：

```json
[
  {
    "skills": ["<name>"],
    "query": "<用户会怎么说>",
    "files": ["evals/files/<fixture>"],
    "expected_behavior": ["<可观察行为 1>", "<可观察行为 2>", "<可观察行为 3>"]
  }
]
```

- 至少 1 个场景是「近似但不应触发本 skill」的**负例**（`skills: []`，
  `expected_behavior` 写明不应读取本 skill）。
- 夹具文件放 `evals/files/`，小文件，≤50 KB。
- **skill 目录下只有根目录可以有 `SKILL.md`。** 夹具即使内容是一个 skill，也必须换名
  （如 `widget-builder-SKILL.md`）——Cursor 等递归发现器把「含 SKILL.md 的目录」直接
  当作一个 skill，`evals/files/SKILL.md` 会注册出第二个坏 skill。
- Phase D 用 Claude Opus 5（medium 思考，`tools/run_evals.py` 默认）各跑一遍「有 skill」
  与「无 skill（基线）」，结果记入 `research/<skill>.md`。

---

## 7. `SOURCES.yaml` 精确 schema

```yaml
skill: <name>
version: "YYYY.MM.DD"            # 必须等于 SKILL.md metadata.version
upstreams:
  - id: twostraws-swiftui        # ^[a-z0-9]+(-[a-z0-9]+)*$，skill 内唯一
    kind: repo                   # repo | docs
    repo: twostraws/SwiftUI-Agent-Skill     # kind=repo 必填
    url: https://github.com/twostraws/SwiftUI-Agent-Skill   # 必填（docs 类填文档 URL）
    paths: [swiftui-pro]         # kind=repo：实际参考的仓库内路径；docs 可省略
    ref: main                    # kind=repo 必填：跟踪的分支
    commit: <40 位 hex>          # kind=repo 必填：合入/同步时 ref 的 HEAD
    license: MIT                 # SPDX id；无许可写 NONE；专有写 Proprietary
    relation: merged             # merged = 内容经重写合入；reference = 仅阅读对齐，未复制内容
    synced_at: "YYYY-MM-DD"
    contributes: "<英文一句：贡献了什么>"
    notes: "<可选，英文：许可注意 / 冲突裁决>"
```

约束：`skill` == 目录名；`version` == frontmatter `metadata.version`；`upstreams` 非空；
`id` 唯一；`kind=repo` 时 `commit` 为 40 位 hex；`relation ∈ {merged, reference}`；
`synced_at` 为 ISO 日期；**至少一个 `relation: merged`**。

---

## 8. `NOTICE.md`（生成，勿手改）

由 `tools/build_catalog.py` 生成，格式：

```
# NOTICE — <name>

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- <repo> (<license>) — <url> @ <commit> — paths: <paths> — <contributes>
...

Reference-only sources (no content copied):
- <repo> (<license>) — <url>
```

---

## 9. 候选评审量表（Phase B 用）

写进 `research/<skill>.md` 的评分列。

| 维度 | 分值 | 判定 |
|---|---|---|
| 权威性 | 0–3 | 官方厂商 3 / 公认专家 2 / 活跃社区 1 / 匿名 0 |
| 新鲜度 | 0–3 | ≤1 月 3 / ≤3 月 2 / ≤6 月 1 / >6 月 0；>6 月直接 REJECT，除非官方且内容仍准确 |
| 具体性 | 0–3 | 全是可执行规则与陷阱 3 / 半通用 2 / 教程式 1 / 空话 0 |
| 正确性 | 0–3 | 抽查 3 条规则对照官方文档：全对 3 / 一错 1 / 两错以上 0；得 0 直接 REJECT |
| 许可 | 0–2 | 明确开源 2 / 仅 frontmatter 声明 1 / 无 0；专有 = 不得作为 merged |

结论：总分 **≥8 INCLUDE**，**5–7 MAYBE**（仅作补充或校验），**≤4 REJECT**。
REJECT 也必须在候选表中留行并写理由。
