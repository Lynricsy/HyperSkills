# security-review 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `web_search`：`security audit agent skill SKILL.md github threat model semgrep 2026`
  - 路线图波次 7 种子（`docs/roadmap.md`）
  - `gh api repos/<o>/<r>/git/trees/<ref>?recursive=1` 逐仓库列目录，按 `security|threat|vuln|secret|semgrep` 过滤
  - 领域官方组织仓库：`getsentry/`、`cloudflare/`、`github/`、`openai/`、`trailofbits/`、`semgrep/`、`OWASP/`、`anthropics/`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`，
  许可一律再用 `gh api repos/<o>/<r>/contents/<LICENSE 路径> -H "Accept: application/vnd.github.raw"` 实读正文。

### 许可实读结论（本波次最重要的一节）

`license.spdx_id` 与实际适用许可有三处不一致，全部靠实读目录内 LICENSE 才发现：

| 上游 | API 的 `spdx_id` | 实读结论 | 影响 |
|---|---|---|---|
| getsentry/skills（仓库根） | `Apache-2.0` | 仓库根确是 Apache-2.0，但 **`skills/security-review/LICENSE` 另行声明**「reference material … derived from the OWASP Cheat Sheet Series … licensed under CC BY-SA 4.0」 | 该目录按 **CC-BY-SA-4.0** 处理：只取结构与清单语义，逐句自己重写，不复制任何段落或表格 |
| openai/skills | `null`（路线图据此写「无许可 → NONE」） | `skills/.curated/security-best-practices/LICENSE.txt`、`security-threat-model/LICENSE.txt`、`security-ownership-map/LICENSE.txt` **三个都是 Apache-2.0 全文** | 按 **Apache-2.0** merged，不需要走「无许可但公开」政策；路线图种子描述需更正 |
| semgrep/skills | `NOASSERTION` | 根 `LICENSE` 正文只有一行：`Semgrep Rules License v1.0. For more details, visit https://semgrep.dev/legal/rules-license` | 自定义非 OSI 许可 → **`relation: reference`**，不复制任何规则文本或数据文件 |
| trailofbits/skills | `CC-BY-SA-4.0` | 根 `LICENSE` 实读为 CC BY-SA 4.0 全文，一致 | share-alike 与本仓库 MIT 不兼容 → 只取结构与清单语义，全部重写 |
| OWASP/ASVS | `CC-BY-SA-4.0` | `LICENSE.md` 实读为 CC BY-SA 4.0 全文，一致 | 同上；docs 类，只作事实取证与章节编号来源 |
| OWASP/Top10 | `NOASSERTION` | 根 `LICENSE` 实读为 **CC BY-SA 4.0 全文**（`Creative Commons Attribution-ShareAlike 4.0 International Public License`） | 按 CC-BY-SA-4.0 处理；类别名称与编号属事实，可引用 |

结论与波次 5/6 的教训同向：**一个仓库（甚至一个目录）的许可是它自己的**，`spdx_id` 只是索引。
`getsentry/skills` 是反向案例——仓库根宽松、子目录更严；`openai/skills` 是另一个反向案例——
仓库根无许可、子目录明确 Apache-2.0。两种情况都只能靠实读目录里的 LICENSE 文件发现。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | cloudflare/security-audit-skill `skills/security-audit` | https://github.com/cloudflare/security-audit-skill | 3270 | 2026-09-10 | MIT | 整仓审计编排、覆盖账本、独立验证、findings schema | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方厂商，唯一把「谁审、谁验、未覆盖的算什么」写成可检查契约的上游。方法论主干：invariant-first 取证、验证者不得是发现者、`rejected` 记录也要留、严重性不得超过已证实影响、干净的一轮可以是零发现 |
| 2 | getsentry/skills `skills/security-review` | https://github.com/getsentry/skills/tree/main/skills/security-review | 990 | 2026-09-07 | CC-BY-SA-4.0（目录 LICENSE，仓库根 Apache-2.0） | 置信度分级、误报清单、服务端可控 vs 攻击者可控、按代码类型路由 reference | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 主干中的「不要报什么」半边。`settings.X` / 环境变量 / 常量不是攻击者可控这张表，是本 skill 误报治理的核心语义。share-alike，逐句重写 |
| 3 | openai/skills `.curated/security-threat-model` | https://github.com/openai/skills/tree/main/skills/.curated/security-threat-model | 26870 | 2026-09-08 | Apache-2.0（目录 LICENSE.txt） | 仓库落地的威胁建模：信任边界为具体边、资产、攻击者能力与**非能力**、likelihood×impact | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 威胁建模一节主干。「显式写出攻击者的非能力以免抬高严重性」这一条是其他候选都没有的 |
| 4 | openai/skills `.curated/security-best-practices` | https://github.com/openai/skills/tree/main/skills/.curated/security-best-practices | 26870 | 2026-09-08 | Apache-2.0（目录 LICENSE.txt） | 按语言/栈分册的后端与前端安全基线 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 校验注入/认证/密钥各节的事实面；语言专属细节按边界转交对应生态 skill，本 skill 只留跨语言不变量 |
| 5 | trailofbits/skills `plugins/semgrep-rule-creator` | https://github.com/trailofbits/skills/tree/main/plugins/semgrep-rule-creator | 7035 | 2026-09-09 | CC-BY-SA-4.0 | 规则测试先行、taint 优先、一文件一规则、禁 `todoruleid` | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | semgrep 规则编写一节的骨架。只取清单语义；所有命令与断言在本机 semgrep 1.177.0 上重新实测 |
| 6 | trailofbits/skills `plugins/vulnerability-triage-brocards` | https://github.com/trailofbits/skills/tree/main/plugins/vulnerability-triage-brocards | 7035 | 2026-09-09 | CC-BY-SA-4.0 | 7 条可证伪的驳回判据（无威胁模型不成立、天降攻击者、不在实际用法中、标准行为、已文档化行为、疗法比病重、报告既非必要也非充分） | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 误报治理一节的判据来源。语义重写为本仓库的 dismissal tests |
| 7 | trailofbits/skills `plugins/insecure-defaults` | https://github.com/trailofbits/skills/tree/main/plugins/insecure-defaults | 7035 | 2026-09-09 | CC-BY-SA-4.0 | 六类不安全默认：调试特性、默认凭据、fail-open、回退密钥、过宽访问、弱加密 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 配置审计清单的分类骨架。其 `references/*.json` 数据文件**一律不复制**（share-alike + 事实数据集） |
| 8 | trailofbits/skills `plugins/supply-chain-risk-auditor` | https://github.com/trailofbits/skills/tree/main/plugins/supply-chain-risk-auditor | 7035 | 2026-09-09 | CC-BY-SA-4.0 | 依赖风险信号（维护状态、发布节奏、所有权变更）与 collect/model/render 分层 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 依赖与供应链一节：把「有没有 CVE」扩成「这个依赖本身是不是风险」。脚本不复制 |
| 9 | github/awesome-copilot `skills/threat-model-analyst` | https://github.com/github/awesome-copilot/tree/main/skills/threat-model-analyst | 38883 | 2026-09-10 | MIT | STRIDE、DFD 约定、inventory→dfd→stride→findings 的分步骨架、增量重建 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 与 openai 的威胁建模交叉校验；贡献「先清点再画边界再套 STRIDE」的次序与增量更新做法 |
| 10 | github/awesome-copilot `skills/secret-scanning` | https://github.com/github/awesome-copilot/tree/main/skills/secret-scanning | 38883 | 2026-09-10 | MIT | 告警与补救、自定义模式、push protection | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 密钥泄露一节：撤销优先于重写历史的次序。GitHub 产品面（push protection 配置、告警 API）按边界留给 `github` skill |
| 11 | github/awesome-copilot `skills/security-review` | https://github.com/github/awesome-copilot/tree/main/skills/security-review | 38883 | 2026-09-10 | MIT | 七步扫描流程、依赖与密钥前置、报告卡片模板 | 3 | 3 | 2 | 2 | 2 | 11 | INCLUDE | 流程次序（先依赖与密钥，再深挖）可用。报告模板是 emoji 框线画，本仓库不采用；正确性扣分：全篇按 `OWASP A03:2021 – Injection` 标注，2025 版编号已变 |
| 12 | trilwu/secskills `secskills-core/skills/auditing-code-for-vulnerabilities` | https://github.com/trilwu/secskills/tree/main/secskills-core/skills/auditing-code-for-vulnerabilities | 138 | 2026-09-04 | MIT | 四趟循环：context → attack surface → hunt → verify；taint 追踪、不变量、变体分析 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 个人作者但质量高。贡献「审计不是扫描」的四趟次序，以及「先证可利用再动笔」这条与 cloudflare 的验证契约同向的约束 |
| 13 | openai/skills `.curated/security-ownership-map` | https://github.com/openai/skills/tree/main/skills/.curated/security-ownership-map | 26870 | 2026-09-08 | Apache-2.0（目录 LICENSE.txt） | git 历史 → 人-文件二分图、bus factor、敏感代码归属 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 只取一个概念：审计定范围时用「敏感路径的归属与 bus factor」排优先级。脚本与 Neo4j 导出不并入（与本 skill 的任务形态无关） |
| 14 | github/awesome-copilot `instructions/security-and-owasp` | https://github.com/github/awesome-copilot/blob/main/instructions/security-and-owasp.instructions.md | 38883 | 2026-09-10 | MIT | 面向 Copilot 的 OWASP 通用指令 | 3 | 3 | 1 | 2 | 2 | 11 | MAYBE → reference | 教程式、几乎全是模型已知常识（"validate all input"），且沿用 2021 编号。只作覆盖面对照，不并入内容 |
| 15 | trailofbits/skills `plugins/differential-review` | https://github.com/trailofbits/skills/tree/main/plugins/differential-review | 7035 | 2026-09-09 | CC-BY-SA-4.0 | diff 的风险分级、对被删护栏做 blame、blast radius | 3 | 3 | 3 | 3 | 2 | 14 | reference | 内容优秀，但**已在 `code-review` skill 的 `security-review-delta` workflow 中合入**。按分界句归属，diff 层面的安全视角在 `code-review`，本 skill 不重复；仅作边界对齐 |
| 16 | semgrep/skills `skills/code-security` | https://github.com/semgrep/skills/tree/main/skills/code-security | 300 | 2026-07-28 | Semgrep Rules License v1.0（非 OSI） | 由开源 semgrep 规则生成的按类分册规则说明 | 3 | 2 | 3 | 3 | 0 | 11 | reference | 官方且内容准确，但许可为自定义非 OSI（实读 LICENSE 确认），**不得 merged**。仅用于交叉确认 semgrep 语义；本 skill 的 semgrep 事实全部本机实测取得 |
| 17 | github/awesome-copilot `skills/agent-owasp-compliance` | https://github.com/github/awesome-copilot/tree/main/skills/agent-owasp-compliance | 38883 | 2026-09-10 | MIT | OWASP Agentic Security Initiative Top 10（ASI-01…10） | 3 | 3 | 3 | 2 | 2 | 13 | reference | 质量够，但主题是 agent 系统自身的安全，按本波次边界归 `mcp-server`（MCP 特有威胁）与尚不存在的 `ai-engineering`。本 skill 不并入，避免与 `mcp-server` 重复 |
| 18 | OWASP/Top10 `2025/docs/en` | https://github.com/OWASP/Top10 | 6065 | 2026-09-10 | CC-BY-SA-4.0（实读 LICENSE） | Top 10 2025 十类风险正文与 CWE 映射 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（docs） | 类别编号的唯一权威来源。2025 版重排，且 SSRF 不再独立成类——本 skill 的版本门事实就来自这里 |
| 19 | OWASP/ASVS `5.0/en` | https://github.com/OWASP/ASVS | 3602 | 2026-09-03 | CC-BY-SA-4.0（实读 LICENSE.md） | ASVS 5.0.0 的 V1–V17 章节与验证要求 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（docs） | 审计覆盖面的清单来源。5.0 章节编号相对 4.0.3 全面重排——第二个版本门事实 |
| 20 | semgrep 官方文档（rule syntax / taint mode / testing rules） | https://semgrep.dev/docs/writing-rules/rule-syntax | — | — | 站点条款，非 OSI | 规则语法、taint 模式、`--test` 语义 | 3 | 3 | 3 | 3 | 0 | 12 | reference | 文档本身不得复制。本 skill 的 semgrep 断言全部用本机 semgrep 1.177.0 实测复核（见「semgrep 实跑记录」） |
| 21 | secureIO-GmbH/security-skills | https://github.com/secureIO-GmbH/security-skills | 2 | 2026-03-27 | MIT | security-audit / threat-model / security-scan 三件套编排 | 0 | 1 | 2 | — | 2 | 5 | REJECT | 2 星、近 6 个月未推送。编排思路已被 cloudflare 的同类内容完全覆盖且后者写得更严；无独有内容可取 |
| 22 | superagent-ai/skills `skills/skill-security` | https://github.com/superagent-ai/skills/tree/main/skills/skill-security | 76 | 2026-08-15 | MIT | 安装前审计一个 agent skill 本身（提示注入、凭据外泄、持久化） | 1 | 2 | 3 | — | 2 | — | REJECT（范围） | 审计对象是 skill 制品，不是被审的代码库。按边界属 `skill-authoring` 与 `mcp-server`，不属本 skill |
| 23 | anthropics/skills | https://github.com/anthropics/skills | 175703 | 2026-09-10 | 目录级专有 | — | — | — | — | — | — | REJECT（不存在） | `git/trees/main?recursive=1` 全树按 `security\|threat\|vuln` 过滤为空：该仓库没有安全审计类 skill，本波次无可对齐对象 |
| 24 | trailofbits/skills `plugins/static-analysis` `skills/semgrep` | https://github.com/trailofbits/skills/tree/main/plugins/static-analysis | 7035 | 2026-09-09 | CC-BY-SA-4.0 | 跑现成 semgrep ruleset、扫描模式、SARIF 合并 | 3 | 3 | 3 | 3 | 2 | 14 | MAYBE → reference | 与 `semgrep-rule-creator` 的分工是「跑规则 vs 写规则」。本 skill 只写规则并把扫描当取证手段，跑大规模 ruleset 与 SARIF 流水线不进正文（会挤掉判断类内容） |

## 深度审查

### cloudflare/security-audit-skill（主干：方法与验证契约）

15 个大写命名的 Markdown 文件加 `report-schema.json` 与两个 `.cjs` 校验器，整体是一套多代理编排：
父代理维护 `coverage-ledger.json`，把攻击面切成 coverage unit 派给 hunter，再把每个候选交给
**没有发现过它的**另一个代理去反驳，最后按 `findings.json` 的 `confirmed` /
`needs_validation` / `rejected` 三支 schema 落盘。frontmatter 干净（只有 name/description）。

值得拿的是判断规则而不是编排：

- **invariant-first**：先命名低信任主体与其起始能力，再命名被接受的值/动作/资源选择符，
  再定位本该拒绝它的控制点，最后只追到「最小可观察影响」就停。
- **验证者不得是发现者**，且必须重读被引用的每一个源位置。
- **`rejected` 也要留档**，附驳回理由，这样下一轮不会重复同一个无据主张。
- **整体严重性不得超过已证实的影响**；likelihood 与 impact 分开写。
- **一轮干净的审计可以零发现**；不得为了交差编造 LOW。
- **未覆盖的部分必须点名**，`quick` / 预算受限的一轮要写明这是部分审计。

不拿的：全套 agent 派发与 artifact promotion 协议（几十行 `fstat`/no-follow 的文件提升流程），
那是给带沙箱的编排器写的；本仓库的 skill 面向一个 agent 在一次任务里干活，照抄会淹没判断内容。

### getsentry/skills `skills/security-review`（主干：不要报什么）

312 行 SKILL.md + 17 个 `references/` + 5 个语言册 + infra 册。它的独有价值集中在三张表：
攻击者可控 vs 服务端可控的输入来源、框架已缓解的模式（Django `{{ }}`、React `{}`、ORM 参数化）
与「只在什么情况下才算漏洞」（`mark_safe`、`dangerouslySetInnerHTML`、`.raw()`）、以及
「检查上下文再报」的四类（SSRF / 路径穿越 / 开放重定向 / 弱哈希，各自只在输入来自请求时才算）。
置信度三级（HIGH 报、MEDIUM 记为待验证、LOW 不报）比一般的严重性分级更能压住噪声。

目录内 LICENSE 指向 OWASP Cheat Sheet Series（CC-BY-SA-4.0），因此一个字都不能抄；
取的是语义：**服务端可控的值不是攻击者可控的输入**，以及「不要基于模式匹配报告」。

### openai/skills `.curated/security-threat-model`

81 行，八步工作流。与其他威胁建模候选的差别有两点：一是要求把信任边界写成**具体的边**并
标注协议/认证/加密/校验/限流；二是要求显式写出攻击者的**非能力**，用来防止严重性被未言明的
最坏情况抬高。另有「先跟用户确认影响排序的关键假设再出最终报告」一步——本仓库改写为
「把假设写出来并标明结论对它的依赖」，因为评测与实际使用多是单轮，强制暂停会变成不产出。

### trailofbits `semgrep-rule-creator` + `vulnerability-triage-brocards`

前者 165 行，核心是「测试先行 + taint 优先 + 一文件一规则 + 禁止 `todoruleid`/`todook`」，
并要求写规则前先读 7 篇 semgrep 文档。它的 Quick Start 里写 `severity: HIGH`——这一点我在本机
semgrep 1.177.0 上实测确认合法（schema 允许 9 个取值），但同一次校验里 rule parser 又打印
`expected ERROR, WARNING or INFO`，说明两套取值并存；正文因此只写「用 semgrep 实际接受的取值」
并列出两组，不复述某一组为唯一正确。

后者 208 行，7 条 brocard 每条都是一个可证伪的驳回测试。这正是本 skill「误报治理」需要的形状：
不是「小心别误报」，而是七个能当场判定的驳回条件。语义全部重写，并补上 cloudflare 的
「驳回记录要留档」。

### github/awesome-copilot `skills/threat-model-analyst` 与 `skills/secret-scanning`

threat-model-analyst 的 `references/skeletons/` 把产物拆成 inventory / dfd / stride-analysis /
findings / assessment 五份骨架，次序（先清点资产与入口，再画边界，再套 STRIDE）比直接套
STRIDE 清单更不容易产出空话。secret-scanning 的 `alerts-and-remediation.md` 给出了
「撤销 → 轮换 → 再处理历史」的次序与「历史重写不等于撤销」这一条，是密钥一节的关键；
它的 push protection / 自定义模式配置属 GitHub 产品面，按边界留给 `github`。

### 与 `code-review` 的重叠核查

`code-review` 已有 `security-review-delta` workflow（风险分级、对被删护栏 blame、blast radius、
每个 HIGH 写一个攻击场景），其上游正是 trailofbits `differential-review`。本 skill 因此
**不写 diff 层面的安全评审**，改为整仓/功能/威胁面审计：定范围与覆盖账本、威胁建模、
按攻击面分类深挖、semgrep 规则化、报告与分级、误报治理。分界句两边字面一致。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | OWASP Top 10 编号 | awesome-copilot 的 `security-review` 与 `instructions/security-and-owasp` 通篇按 2021 编号（`A03:2021 – Injection`）；OWASP/Top10 仓库 `2025/docs/en/` 已发布 2025 版 | 一律按 **2025** 编号；引用 2021 编号时必须写出年份后缀 | 「更新 > 更旧」+ 官方仓库实读。2025：A01 Broken Access Control、A02 Security Misconfiguration、A03 Software Supply Chain Failures、A04 Cryptographic Failures、A05 Injection、A06 Insecure Design、A07 Authentication Failures、A08 Software or Data Integrity Failures、A09 Security Logging and Alerting Failures、A10 Mishandling of Exceptional Conditions |
| 2 | SSRF 是否独立类别 | 2021 版 A10 是 SSRF，多数候选据此把 SSRF 当独立 Top 10 类别 | 2025 版**没有** SSRF 类别；CWE-918 被并入 A01:2025 Broken Access Control | 实读 `2025/docs/en/A01_2025-Broken_Access_Control.md`：正文与 CWE 列表都含 `CWE-918 Server-Side Request Forgery (SSRF)` |
| 3 | ASVS 章节编号 | 沿用 4.0.x 的读者会按 V1 架构 / V2 认证 / V4 访问控制引用 | 按 **ASVS 5.0.0**：V1 Encoding and Sanitization、V6 Authentication、V7 Session Management、V8 Authorization、V9 Self-contained Tokens、V10 OAuth and OIDC、V11 Cryptography | 实读 `5.0/en/` 文件名清单；`v5.0.0_release` 发布于 2025-05-30，仓库另有 `0x05-For-Users-Of-4.0.md` 迁移说明 |
| 4 | semgrep `severity` 合法取值 | trailofbits 用 `severity: HIGH`；semgrep 早期文档只承认 ERROR/WARNING/INFO | 两组都被 1.177.0 接受，正文写出完整集合并要求「用 semgrep 实际接受的取值」 | 本机实测：`severity: BANANA` 报 `'BANANA' is not one of ['ERROR','WARNING','INFO','INVENTORY','EXPERIMENT','CRITICAL','HIGH','MEDIUM','LOW']`，而 HIGH 与 MEDIUM 都 `Configuration is valid` |
| 5 | 报告格式 | awesome-copilot 用 emoji + 框线字符卡片；cloudflare 用三份 Markdown + JSON schema；getsentry 用扁平 Markdown | 采用「一份 Markdown 报告 + 每条发现固定字段」：位置、低信任主体、路径、已证实影响、likelihood/impact 分列、最小修复、回归用例；不用框线画 | 「官方厂商 > 社区」中 cloudflare 更严；框线字符在终端与 diff 里都会错位，且挤占 token |
| 6 | 置信度 vs 严重性 | getsentry 用置信度三级决定报不报；cloudflare 用 `confirmed`/`needs_validation`/`rejected` 三态 | 合并：三态决定**放在报告的哪一节**，严重性只给 `confirmed`；`needs_validation` 不给严重性 | cloudflare 明确「不要给 needs_validation 打严重性」，这条更能防止把猜测写成发现；getsentry 的 LOW 不报则保留为噪声闸 |
| 7 | 是否覆盖 agentic / MCP 威胁 | awesome-copilot `agent-owasp-compliance` 给了 OWASP ASI Top 10 | 不进本 skill；MCP 特有威胁（工具投毒、经工具返回值的提示注入、过宽 scope、confused deputy）归 `mcp-server`，由它指回本 skill 做整体审计 | 本波次跨 skill 边界契约；避免两个 skill 写同一份清单 |
| 8 | 语言专属漏洞细节 | getsentry 与 openai 都带按语言分册的 references | 本 skill 只留跨语言不变量与判断方法；语言/框架专属正确性转交 `python`、`typescript`、`go`、`java-spring`、`csharp-dotnet`、`laravel`、`nodejs-backend`、`fastapi` 等生态 skill | `code-review` 与既有生态 skill 的既定边界；重复一遍会立刻过期 |
| 9 | 是否收录跑大规模 ruleset 的内容 | trailofbits `static-analysis` 提供 ruleset 目录与 SARIF 流水线 | 不收；semgrep 在本 skill 里是取证与规则化手段，不是扫描器操作手册 | 「每段都要能回答这段值它的 token 吗」；扫描器 CLI 细节腐化快且属工具文档 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `cloudflare-audit` | cloudflare/security-audit-skill `skills/security-audit` | merged | 审计的方法骨架：覆盖账本与「未覆盖必须点名」、invariant-first 取证六步、验证者不得是发现者、confirmed/needs_validation/rejected 三态、严重性不得超过已证实影响、零发现是合法结论 |
| `sentry-secreview` | getsentry/skills `skills/security-review` | merged | 误报治理的另一半：攻击者可控 vs 服务端可控的输入来源判定、框架已缓解模式、四类「先查上下文再报」、置信度闸门 |
| `openai-threatmodel` | openai/skills `.curated/security-threat-model` | merged | 威胁建模：信任边界写成带协议与认证的具体边、资产清点、攻击者能力与非能力、likelihood×impact 与「哪个假设最影响排序」 |
| `openai-secbase` | openai/skills `.curated/security-best-practices` | merged | 注入、认证、密钥各节的跨语言不变量与事实校验 |
| `openai-ownership` | openai/skills `.curated/security-ownership-map` | merged | 定范围阶段用敏感路径的归属与 bus factor 排优先级 |
| `tob-semgrep-rules` | trailofbits/skills `plugins/semgrep-rule-creator` | merged | semgrep 规则一节的骨架：测试先行、taint 优先、一文件一规则、禁 `todoruleid`/`todook` |
| `tob-brocards` | trailofbits/skills `plugins/vulnerability-triage-brocards` | merged | 误报治理的七条可证伪驳回判据 |
| `tob-insecure-defaults` | trailofbits/skills `plugins/insecure-defaults` | merged | 配置审计的六类不安全默认分类 |
| `tob-supplychain` | trailofbits/skills `plugins/supply-chain-risk-auditor` | merged | 依赖风险信号：从「有无 CVE」扩到「这个依赖本身是不是风险」 |
| `copilot-threatmodel` | github/awesome-copilot `skills/threat-model-analyst` | merged | 先清点再画边界再套 STRIDE 的次序，与威胁模型的增量重建 |
| `copilot-secrets` | github/awesome-copilot `skills/secret-scanning` | merged | 密钥泄露处置次序：撤销优先于重写历史，历史重写不等于撤销 |
| `copilot-secreview` | github/awesome-copilot `skills/security-review` | merged | 流程次序：依赖清单与密钥扫描前置于源码深挖 |
| `trilwu-audit` | trilwu/secskills `secskills-core/skills/auditing-code-for-vulnerabilities` | merged | 「审计不是扫描」的四趟循环 context → attack surface → hunt → verify，以及先证可利用再动笔 |
| `owasp-top10` | OWASP/Top10 `2025/docs/en` | merged（docs） | Top 10 2025 的类别名称与编号、CWE 映射、SSRF 的归属变更 |
| `owasp-asvs` | OWASP/ASVS `5.0/en` | merged（docs） | ASVS 5.0.0 的 V1–V17 章节编号，用作审计覆盖面清单 |
| `semgrep-skills` | semgrep/skills | reference | 官方 semgrep 语义交叉确认。自定义非 OSI 许可，不复制任何内容 |
| `tob-diffreview` | trailofbits/skills `plugins/differential-review` | reference | 与 `code-review` 的分界对齐：diff 层面的安全评审不在本 skill |

## 基线缺口

无 skill（`uv run tools/run_evals.py security-review --baseline`，claude-opus-5 · medium）时的
逐条判定。五场景 `skill_read` 全为 `False`，答案在
`/tmp/hs-evals/security-review/anthropic-claude-opus-5-medium/baseline/<N>/answer.md`。

**先说第一轮的两处评测自身缺陷**（按 Phase B「不要靠降低标准制造缺口」处理，改的是评测而非判定）：

1. 场景 1 原第 3 条要求把 callback SSRF 与 IMDSv1 串成凭据窃取链。基线**明确反驳了这条链**：
   callback 只发 POST，而 IMDSv1 只应答 GET，所以没有 GET 原语时这条链不成立。基线是对的，
   我的原期望是外行的那一版。改写为「两个方向都要对」：既要报出一次请求即可导出整个 warehouse
   （`spec.query` 与 `callback_url` 都由调用方控制、warehouse 无认证），又**不得**在没有 GET
   或跟随重定向路径的前提下断言凭据窃取。
2. 场景 1 原第 10 条（「若引用 OWASP 则用 2025 编号」）是空条件——基线一次都没引用 OWASP，
   于是无条件达成，零区分度。把版本门事实移到场景 4，并把场景 4 的 query 改成明确要求
   「map each threat to its OWASP Top 10 category so I can paste it into our compliance doc」，
   强制产生引用；场景 1 第 10 条换成防御性取证边界（下表 S1-c）。场景 4 因 query 变更重跑了基线。

另修正了一个夹具缺陷：`pagination.diff` 原为手写，hunk 头行数与正文不符，基线直接报
`corrupt patch at pagination.diff:42`。已改为真 git 仓库里 `git diff` 生成，`git apply --check`
返回 0。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| S1-a | 「引用本仓库自己的正确写法作为差异证据」 | 基线在 SQL 一节用了「同文件其他路由都用 `$1`」这个差异论证，但在授权一节没有拿 `GET /`（确实按 `req.session.customerId` 收敛）去对照 `GET /:id` 的缺失，只是列了一张缺检查的表。缺了这一步，结论从「三条路由漏了」退化成「你们应该校验归属」 |
| S1-b | 「likelihood 与 impact 分开给，各带理由」 | 基线只给了 P0/P1/P2 单一优先级标签。整份报告里没有一处把可能性与影响拆开写，也没有「整体严重性不得超过已证实影响」这条约束的痕迹 |
| S1-c | 「取证边界保持防御性，不提议对已部署/预发环境打 payload」 | 基线最后一节是「动态验证（需在预发环境、书面授权范围内）」，列了五条对运行中系统发请求的动作：两租户 session 打同一 order_id、`?sort=1--`、构造 `alg:none` 令牌、callback 指向自建 collector、跑 format payload。方向上正确地加了授权前提，但这已越过「源码审计 + 本地有界复现」的边界，是本 skill 要收紧的地方 |
| S2-a | 「警告过宽的 sanitizer 会吃掉 source，把规则静默变成空规则」 | 基线确实警告了一个 sanitizer 陷阱，但是另一个：守卫分支只打日志、没重新赋值。它没有提到 `$D.get(...)` 会匹配到 `request.args.get(...)` 从而净化 source、使命中数从 3 变 0 这个「看起来像扫干净了」的失败 |
| S2-b | 「目录模式基名不匹配时一个测试都不跑，退出码仍为 0」 | 基线用的正是目录模式（`semgrep --test --config semgrep/ semgrep/`）并报了 `1/1`，但全篇没有提到「绿色退出码本身不是规则被测过的证据」 |
| S2-c | 「severity 用 semgrep 实际接受的取值、一文件一规则、禁 `todoruleid`/`todook`」 | 答案里没有出现 severity 取值、一文件一规则或 todo 注解的任何说明；产物 YAML 未随答案给出，无法判定，按未达成记 |
| S2-d | 「message 告诉开发者该怎么做」 | 同上，未在答案中体现 |
| S3-a | 「干净的审计日志是弱证据而非未被使用的证明」 | 基线要求拉四家 provider 的日志（这部分达成），但没有说明 read 类操作常常不落日志、保留期可能短于暴露窗口，因此「查不到」不等于「没用过」 |
| S3-b | 「先吊销会打断生产时，先签发替代再立即吊销，而不是推到维护窗口」 | 基线把吊销放在第一阶段（达成大方向），但没有处理「吊销会直接打断部署」这一现实分支 |
| S3-c | 「`.gitignore` 对已被跟踪的文件毫无作用」 | 基线在阶段 3 加了 `.gitignore` 条目，却没有指出这对已提交文件无效、需要 `git rm --cached`。这是这个问题最常见的错误答案 |
| S4-a | 「用 OWASP Top 10 **2025** 编号，且 SSRF 不再是独立类别」 | 基线整张映射表标题就是「OWASP Top 10:2021 映射（可直接粘贴）」，14 条威胁全按 2021：T3 标 **A10 服务端请求伪造**、T11 标 A02 加密机制失效、T4/T5/T14 标 A05 安全配置错误、并在注记里讨论要不要「加挂 A03（注入）」。在 2025 版里这些分别应是 A01（CWE-918 已并入）、A04、A02、A05。用户明说要粘进合规文档，编号错了就是错误的合规记录 |
| S4-b | 「写出各主体的能力**与非能力**」 | 基线对 IMDS 那一条做了诚实的原语限制说明（POST vs GET），但没有为任何主体系统地列出非能力，因此没有防住严重性被未言明的最坏情况抬高这一机制 |
| S4-c | 「likelihood 与 impact 分开排序」 | 基线明说「我没有用传统的严重度打分」，表里只有一列「严重度」。可达性×爆炸半径的叙述是好的，但没有两列可分别被反驳的判断 |

已达成（因此不属缺口）：S1 的可达性优先、pickle 排第一、`x-internal-role`、`/export` 无校验、
两处 SQL 拼接、不误报 `settings.*`、依赖按可达性挑出 `node-serialize` 与 `jsonwebtoken`+`alg:none`、
明确列出无法验证的事实；S2 的测试先行与注解、taint 优先及其理由、预测并解决 `list_orders_ok`
误报、跑 `--test` 要求全过；S3 的吊销优先于重写历史、按凭据分别定爆炸半径、从提交日期算暴露窗口、
「新提交删掉几行没用」「fork 清不掉」「要找 GitHub Support 清缓存」、`echo` 进 CI 日志；
S4 的边界成边、指出文档自相矛盾、跨租户三处、90 天 cookie 与仅登录审计、结论条件化。

负例 S5：`skill_read=False`，产出的是分页正确性与风格评审（游标非唯一丢行、微秒 vs 毫秒精度、
`Intl.NumberFormat` 行为变化、调用方未迁移、缺索引迁移），没有威胁建模、没有严重性分级、
没有写报告文件。三条期望全部达成。

## 评测结果

两组都用 `tools/run_evals.py` 的默认模型与思考档（未传 `--model` / `--thinking`）。
基线：`uv run tools/run_evals.py security-review --baseline`（场景 4 因 query 改写单独
`--only 4` 重跑）。有 skill：`uv run tools/run_evals.py security-review`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 功能级审计（5 个夹具） | claude-opus-5 · medium | 无 | false | 8 / 11 | 缺 S1-a 差异证据、S1-b likelihood/impact 分列、S1-c 取证边界（提议对预发环境打 payload） |
| 1 | claude-opus-5 · medium | 有 | true | **11 / 11** | 三条缺口全部填补：`:80` 引用同文件 `:40` 的 `req.session.customerId` 作差异证据；每条发现都有「可能性」「影响」两行独立判断；开头与「未覆盖」两处写明「未对任何已部署系统发请求」，无动态 payload 一节。另按报告模板输出「确认 / 待验证 / 驳回 / 加固 / 覆盖」五节，并正确沿用基线对 IMDS 链的反驳 |
| 2 semgrep 规则 | claude-opus-5 · medium | 无 | false | 3 / 8 | 达成测试先行、taint 优先、预测 `list_orders_ok` 误报；缺 S2-a 过宽 sanitizer 吃掉 source、S2-b 目录模式静默零测试、severity/一文件一规则/禁 todo、message 可操作性 |
| 2 | claude-opus-5 · medium | 有 | true | 6 / 8 | 填补 S2-a（显式写出「不加 `metavariable-regex` 会匹配 `request.args.get(...)` 自身，在 source 原点清掉污点，规则静默零命中」）与 S2-b（「basename 与规则同名，否则目录模式会 `No unit tests found` 并 exit 0」），并报出 `missed lines` / `incorrect lines` 两个方向。**未达成**：答案没有粘出 YAML，severity 取值、一文件一规则、禁 `todoruleid`/`todook` 与 message 文本均无法从答案判定，按未达成记 |
| 3 泄露凭据处置 | claude-opus-5 · medium | 无 | false | 4 / 8 | 达成吊销优先、按提交日算窗口、逐凭据定半径、CI 日志；缺 S3-a「干净日志是弱证据」、S3-b「吊销打断生产怎么办」、S3-c「`.gitignore` 对已跟踪文件无效」、陈旧克隆会把 blob 推回 |
| 3 | claude-opus-5 · medium | 有 | true | **8 / 8** | 三条缺口全部填补（第 28、26、29 行），并补上陈旧克隆推回 blob；额外重写了 `ci-deploy.sh`（无 fallback 默认值、token 走 stdin 不进 argv）并实测 `rc=78` 与钩子双向验证，同时诚实写明本机 `core.hooksPath` 会屏蔽仓库钩子、所以服务端 push protection 才是权威控制 |
| 4 威胁建模（要求 OWASP 映射） | claude-opus-5 · medium | 无 | false | 5 / 8 | 缺 S4-a（整表标题即「OWASP Top 10:2021 映射」，SSRF 标成 A10、加密标成 A02、配置错误标成 A05）、S4-b 非能力、S4-c 可能性与影响分列 |
| 4 | claude-opus-5 · medium | 有 | true | **8 / 8** | 三条缺口全部填补：开头声明「OWASP 编号统一使用 2025 版（A01 含 SSRF/CWE-918；A03 已改为 Software Supply Chain Failures）」且 12 条威胁的映射全部为 2025 编号并附 ASVS 5.0 章节；主体表有独立的「非能力」列；威胁表有「可能性」「影响」两列。另按 9 条边逐列填信任边界表，并在结尾限定「影响列为推断、无已确认发现」 |
| 5 负例：diff 正确性评审 | claude-opus-5 · medium | 无 | **false** | 3 / 3 | 产出分页正确性与风格评审，无威胁建模、无严重性分级 |
| 5 负例 | claude-opus-5 · medium | 有 | **false** | 3 / 3 | 未读本 skill。仍是正确性/风格评审（调用方迁移、`Order` 类型、索引 migration），并顺手核对了 diff 的 hunk 计数一致、可 apply。`description` 末尾的 `Do not use for reviewing a diff for general correctness and style` 生效，无需收紧 |

结论：**通过**。四个正例每一个都至少填补一条基线未达成的行为，合计 12 条缺口中填补 10 条：
S1 三条全补（8/11 → 11/11）、S2 两条（3/8 → 6/8）、S3 三条全补（4/8 → 8/8）、
S4 三条全补（5/8 → 8/8）。负例两组 `skill_read` 均为 `false`。

**如实记录的未达成项**：场景 2 的 `severity` 合法取值、一文件一规则、禁 `todoruleid`/`todook`、
message 可操作性四条，在有 skill 一轮里既没有被违反、也没有在答案文本中被陈述——模型把
YAML 写进了文件但没有粘进回答，因此无法判定。这四条是 `references/semgrep-rules.md`
「Rule hygiene」与「Messages」两节覆盖的内容，评测手段（只读最终回答文本）看不到产物文件，
属评测方法的局限而非内容缺失；不改判为达成。

## semgrep 实跑记录

本机 semgrep 由 `uv tool install semgrep` 安装，版本 **1.177.0**。所有断言都在
`skills/security-review/evals/files/raw_query_usages.py` 与等价的最小夹具上实跑取得。

### 1. taint 模式对「已做允许清单校验」的调用点仍然命中（真误报）

```
$ semgrep --config no-tainted-raw-query.yaml --metrics=off --quiet no-tainted-raw-query.py
┌─────────────────┐
│ 3 Code Findings │
└─────────────────┘
   14┆ return db.raw_query("SELECT * FROM orders ORDER BY " + sort)
   19┆ return db.raw_query(f"SELECT * FROM orders WHERE note ILIKE '%{term}%'")
   26┆ return db.raw_query("SELECT * FROM orders ORDER BY " + sort)
```

第 26 行是 `list_orders_ok`：`if sort not in ALLOWED_SORTS: sort = "created_at"`。
taint 不认这个重新赋值为净化，因此命中。规则不加 sanitizer 就带着这个误报上 CI。

### 2. 过宽的 sanitizer 会把 source 一起吃掉，规则静默变成空规则

最小夹具 `t.py` 三个函数：`a()` 直接拼接（真漏洞）、`b()` 用字面量字典 `ALLOWED.get(sort, ...)`、
`c()` 用校验助手 `safe_column(sort)`。

| sanitizer | 命中行 |
|---|---|
| 无 | 9, 15, 21（三个全中，`b` 与 `c` 是误报） |
| `pattern: $D.get(...)` | **空**（连真漏洞 `a()` 都没了） |
| `pattern: safe_column(...)` | 9, 15 |
| 两条都写 | 空 |

原因：source 是 `request.$A`，而 `request.args.get("sort")` 本身就匹配 `$D.get(...)`，
sanitizer 把 source 净化掉了。**规则从「3 个发现」变成「0 个发现」，看起来像扫干净了。**

### 3. `semgrep --test` 能同时抓住误报与漏报

测试文件用 `# ruleid: <id>` 标注应命中的下一行、`# ok: <id>` 标注不应命中的下一行。

```
# 过宽 sanitizer（漏报）
$ semgrep --test --config no-tainted-raw-query.yaml no-tainted-raw-query.py ; echo rc=$?
0/1: 1 unit tests did not pass:
	✖ no-tainted-raw-query
	missed lines: [10], incorrect lines: []
rc=1

# 不加 sanitizer（误报）
0/1: 1 unit tests did not pass:
	✖ no-tainted-raw-query
	missed lines: [], incorrect lines: [17]
rc=1

# sanitizer 收窄到 ALLOWED.get(...)
1/1: ✓ All tests passed
rc=0
```

`missed lines` = 漏报，`incorrect lines` = 误报，失败时退出码 1。

### 4. 目录模式下基名不匹配 = 一个测试都没跑，但退出码仍是 0

```
$ ls            # cases.py 与 no-tainted-raw-query.yaml
$ semgrep --test --metrics=off . ; echo rc=$?
No unit tests found. See https://semgrep.dev/docs/writing-rules/testing-rules
rc=0

$ mv cases.py no-tainted-raw-query.py
$ semgrep --test --metrics=off . ; echo rc=$?
1/1: ✓ All tests passed
rc=0
```

目录模式按基名把 `<rule-id>.yaml` 与 `<rule-id>.<ext>` 配对；名字不对就一个测试都不跑，
而退出码还是 0。**绿色退出码本身不是「规则被测过」的证据。**
显式给 `--config <rule>.yaml <testfile>` 时基名不必一致（实测两种命名都跑了测试）。

### 5. `severity` 的合法取值

```
$ semgrep --validate --config sev-banana.yaml
Configuration is invalid - found 2 configuration error(s), and 0 rule(s).
semgrep error: Invalid rule schema
'BANANA' is not one of ['ERROR', 'WARNING', 'INFO', 'INVENTORY', 'EXPERIMENT',
                        'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
[ERROR] Rule parse error in rule sev-banana:
 Bad severity: BANANA (expected ERROR, WARNING or INFO)
```

`HIGH` 与 `MEDIUM` 单独校验都返回 `Configuration is valid`。注意同一次输出里 schema 列了 9 个
取值、parser 又只提 3 个——两套并存，正文因此不把任何一组说成唯一正确。

## 备注

### 未验证项

- OWASP Top 10 2025 / 2021 的类别名称与编号、SSRF 的 CWE 归属、ASVS 5.0.0 的 V1–V17 章节：
  全部来自 `OWASP/Top10` 与 `OWASP/ASVS` 仓库文件的实读，标 `[official]`（官方文档），
  非本机可执行验证。
- semgrep 的全部断言标 `[verified]`：本机 1.177.0 实跑，命令与原始输出见上一节。
- CVE 编号（`node-serialize` CVE-2017-5941、`lodash` CVE-2021-23337、`semver` CVE-2022-25883 等）
  出现在评测夹具与 reference 中，来源为公开公告，标 `[official]`；本机未跑 `npm audit`
  （夹具不是真实可安装的工程，跑不出有意义的结果）。
- 「攻击者可控 vs 服务端可控」「框架已缓解模式」两张表的框架行为（Django 自动转义、React
  自动转义、ORM 参数化）标 `[official]`，未逐个框架实跑。

### 评测夹具的凭据写法

夹具里所有假凭据都用 `REDACTED` 字样（`wh_REDACTED`、`sk_live_REDACTED`、`ghp_REDACTED`、
`REDACTED_DB_PASSWORD_PLACEHOLDER`）。波次 6 的教训是 `sk_live_` 加 24 位占位符会命中
GitHub 推送保护的 Stripe 规则，导致整批推送被拒。`REDACTED` 只有 8 个字符，低于所有
相关扫描器的长度门，同时语义上仍一眼看得出是硬编码凭据。

### 未来同步时要盯的上游

- `cloudflare/security-audit-skill`：推送频繁，`report-schema.json` 与 `ATTACK-CLASSES.md` 的
  分类若变动要重读；其 `.cjs` 校验器不并入，不必跟。
- `OWASP/Top10`：2025 版仍在加译本与修订，`2025/docs/en/` 下的类别名称是本 skill 版本门的来源。
- `OWASP/ASVS`：`latest` tag 会随 5.x 小版本移动，章节编号变动要同步 reference。
- `getsentry/skills`：注意**目录级** LICENSE，同步时重读 `skills/security-review/LICENSE`。
- `semgrep`：`severity` 取值集合与 `--test` 输出格式随版本变化，reference 顶部已写
  `Verified against: semgrep 1.177.0`。

### 放弃的方向

- 语言分册（Python/JS/Go/Java/Rust 各一份漏洞册）：`getsentry` 与 `openai` 都这么做，但本仓库
  已有对应生态 skill，重复会立刻过期，且会把本 skill 撑到无法阅读。
- 多代理审计编排（cloudflare 的 hunter/critic/verifier 派发 + artifact promotion 协议）：
  面向带 OS 沙箱的编排器，与本仓库「一个 agent 一次任务」的形态不符。只取其判断规则。
- 跑现成 ruleset 与 SARIF 流水线（trailofbits `static-analysis`）：属工具操作手册。
- 渗透测试、对运行中系统发起请求、规避检测：明确排除，`description` 与 `## Scope` 都写明
  本 skill 是防御性审计，取证边界是源码阅读与本地沙箱内的有界执行。
