# {{name}} 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：{{today}}
- 复核日期：
- 检索途径：
  - `web_search`：`"{{name}} skill SKILL.md github"`、`site:skills.sh {{name}}`
  - <https://www.skills.sh>
  - VoltAgent/awesome-agent-skills、addyosmani/agent-skills
  - 领域官方组织仓库：
- GitHub API 核对方式：`curl -s https://api.github.com/repos/<owner>/<repo>`（`stargazers_count` / `pushed_at` / `license.spdx_id`）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

## 深度审查

<!-- 对总分前 5–8 名逐个：结构、frontmatter、质量、agent 绑定、与其他候选的重叠。 -->

## 冲突与裁决

<!-- 每条：冲突点 → 各方主张 → 裁决与依据（官方厂商 > 公认专家 > 社区；更新 > 更旧）。
     正文只写裁决后的一种做法。 -->

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|

## 基线缺口

无 skill（`uv run tools/run_evals.py {{name}} --baseline`）时，各场景未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|

结论：<!-- 至少一条基线未达成的行为在有 skill 时达成？两种模型分别如何？ -->

## 备注

<!-- 许可注意事项、未来同步时要盯的上游、放弃的方向。 -->
