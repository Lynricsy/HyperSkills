# HyperSkills 仓库约定

本仓库维护一套整合型 Agent Skill 集合：每个技术生态 / 每类常见任务 = 一个独立 skill，
由多个上游高质量 skill 精编重写而成，全部扁平存放在 `skills/` 下。

## 硬性约定

1. **新增或更新 skill 必须按 `docs/workflow.md` 的五个阶段执行**（调研 → 审查与评测先行 →
   重写 → 校验 → 记录与提交）。跳过阶段的产物不接受。
2. **结构与写作规范以 `docs/skill-standard.md` 为唯一来源**。`tools/validate_skills.py`
   的每条检查都对应其中一条条款；两者冲突时以 `docs/skill-standard.md` 为准并同步修改校验器。
3. **提交前必须通过**：
   ```bash
   uv run tools/validate_skills.py && uv run tools/build_catalog.py --check
   ```
4. **语言**：skill 正文（`SKILL.md`、`references/`、`scripts/` 注释）一律英文；
   README、`docs/`、`research/` 与提交信息一律中文。
5. **每完成一个 skill 提交一次**，提交信息格式 `<type>(<scope>): <gitmoji> <subject>`，
   并附 `Co-authored-by: Wine Fox <fox@ling.plus>`。
6. **禁止设置 local git config**；身份信息一律走全局配置。
7. `skills/` 必须保持**扁平**（`skills/<name>/SKILL.md`）。分类只通过 frontmatter 的
   `metadata.category` 与 README 目录表表达，禁止建立嵌套分类目录——所有主流 agent 的
   skill 发现都是一级扁平扫描。
8. `NOTICE.md`、`THIRD_PARTY_NOTICES.md`、`.claude-plugin/marketplace.json` 与 README 的
   目录表区块**由 `tools/build_catalog.py` 生成，禁止手工编辑**。

## 许可策略

- 自有内容 MIT。
- 上游宽松许可（MIT / Apache-2.0 / BSD / MPL 等）：重写后合入，在 `SOURCES.yaml` 记录。
- 上游无许可但公开：按宽松策略可合入，`notes` 中注明无授权、以署名方式使用。
- **上游为专有许可（如 Anthropic 的 docx/pptx/xlsx/pdf）：只能作为参考基准，
  `relation: reference`，禁止复制任何文字、脚本或数据文件。**
- CC-BY-SA 上游：只取结构与清单语义，全部用自己的话重写，并在 `SOURCES.yaml` 记录许可。

## 目录导航

| 路径 | 用途 |
|---|---|
| `docs/skill-standard.md` | skill 结构、写作、溯源规范 |
| `docs/workflow.md` | 新增/更新 skill 的五阶段流水线 |
| `docs/roadmap.md` | 后续批次主题路线图 |
| `research/<skill>.md` | 该 skill 的候选调研、冲突裁决、评测结果 |
| `templates/` | 新 skill 与 research 文档的脚手架 |
| `tools/` | 校验、上游检查、目录生成、评测运行 |
