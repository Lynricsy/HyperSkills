# solidity-web3 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11（同日，所有 stars / `pushed_at` / license 均以 `gh api` 当日返回为准）
- 检索途径：
  - `gh api /search/repositories`：`solidity skill in:name,description SKILL.md`、`foundry agent skills solidity`
  - `web_search`：`solidity smart contract audit agent skill SKILL.md github claude skills foundry`
  - `github/awesome-copilot` 全树检索 `solidity|blockchain|web3|smart-contract` → **零命中**（GitHub 官方 skill 集合里没有 EVM 主题，这条路对本 skill 不可用）
  - 领域官方组织：`OpenZeppelin/`、`foundry-rs/`、`crytic/`、`trailofbits/`、`Cyfrin/`、`ethereum/`、`argotorg/`
  - 路线图种子（`docs/roadmap.md` 波次 8）逐个复核，其中 `ethereum/solidity` 已重定向为 `argotorg/solidity`（Argot Collective 接管），见「备注」
  - 二跳发现：`gonzaloetjo/awesome-solidity-skills` 索引出 `tenequm/skills`，后者是 `mrheyday/agentic-solidity-foundry-skill` 的上游
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`，
  许可一律再用 `gh api repos/<o>/<r>/contents/LICENSE --jq .content | base64 -d` 实读正文；按目录授权的仓库逐目录读。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。
「正确」列按量表抽查 3 条规则对照 Solidity 0.8.37 / OpenZeppelin Contracts 5.7.0 / Foundry 1.8.1 复核。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | pashov/skills `solidity-auditor` | <https://github.com/pashov/skills/tree/main/solidity-auditor> | 1144 | 2026-07-09 | MIT（实读 MIT License 正文） | 12 个专项漏洞猎手 + 判定门 + 报告模板 | 2 | 2 | 3 | 2 | 2 | 11 | INCLUDE | 漏洞分类学最全、证据纪律最严；`judging.md` 把「0.8 显式窄化转换会 revert」列为安全模式，实测 `uint128(2**128+7)==7`，该条已裁决为错并取反 |
| 2 | pashov/skills `fizz` | <https://github.com/pashov/skills/tree/main/fizz> | 1144 | 2026-07-09 | MIT | Echidna/Medusa 模糊测试套件生成 | 2 | 2 | 3 | 2 | 2 | 11 | INCLUDE | handler 分层、clamp 而非 reject、donation handler、ghost/snapshot 分离是本 skill invariant 章的骨架；硬依赖 Medusa 与 25 个脚本不合入，模板 pragma `>=0.6.2 <0.9.0` 与本仓库版本门相悖 |
| 3 | pashov/skills `x-ray` | <https://github.com/pashov/skills/tree/main/x-ray> | 1144 | 2026-07-09 | MIT | 审计前侦察报告生成 | 2 | 2 | 3 | 3 | 2 | 12 | INCLUDE | 「按协议类型选威胁模型」的不变量目录 + 「guard 不是 invariant，被抬升后别处没执行的那条既是 invariant 又是候选 bug」；~95 KB reference 与三个脚本不合入 |
| 4 | trailofbits/skills `plugins/property-based-testing` | <https://github.com/trailofbits/skills/tree/main/plugins/property-based-testing> | 7040 | 2026-09-09 | CC-BY-SA-4.0（实读 Attribution-ShareAlike 4.0 正文） | 属性测试的写/审/读失败 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 本批次可信度最高；tautology/vacuity 两种失效、属性强度排序、Echidna 属性函数必须 view/pure 无参。share-alike → 只取清单语义重写 |
| 5 | trailofbits/skills `plugins/building-secure-contracts` | <https://github.com/trailofbits/skills/tree/main/plugins/building-secure-contracts> | 7040 | 2026-09-09 | CC-BY-SA-4.0 | 多链漏洞扫描 + 代币集成 + 成熟度评估 | 3 | 3 | 2 | 1 | 2 | 11 | INCLUDE | 怪异 ERC-20 目录与成熟度九轴可用；**该 plugin 内没有 Solidity/EVM 扫描 skill**（只有 Algorand/Cairo/Cosmos/Solana/Substrate/TON），且 `increaseAllowance` 防抢跑、Manticore、Truffle 门控的 `slither-prop`、「70+ detectors」（实测 102）四条已过期 |
| 6 | trailofbits/skills `plugins/audit-context-building` | <https://github.com/trailofbits/skills/tree/main/plugins/audit-context-building> | 7040 | 2026-09-09 | CC-BY-SA-4.0 | 审计前的逐函数理解，禁止命名漏洞 | 3 | 3 | 2 | 3 | 2 | 13 | 不合入（内容裁决） | 质量高但方法论与本 skill 冲突：它要求理解阶段不得命名漏洞/不得评级，本 skill 是一次过的评审；通用审计方法论按分界归 `security-review` |
| 7 | trailofbits/skills `plugins/testing-handbook-skills` | <https://github.com/trailofbits/skills/tree/main/plugins/testing-handbook-skills> | 7040 | 2026-09-09 | CC-BY-SA-4.0 | 14 个生成的 fuzzing/加密测试 skill | 3 | 3 | 0 | 0 | 2 | 8 | REJECT（范围） | 14 个 skill 全是 libFuzzer/AFL++/cargo-fuzz/atheris 一类原生代码与 Python/Ruby/Rust 方向，**零 EVM 内容**；8 分全由母仓库权威度与新鲜度撑起，按内容判为零贡献 |
| 8 | OpenZeppelin/openzeppelin-skills | <https://github.com/OpenZeppelin/openzeppelin-skills> | 209 | 2026-09-01 | AGPL-3.0（实读 AGPL 正文 + NOTICE） | setup / develop / upgrade × 6 生态 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE → **reference** | 升级章覆盖面最权威（模式取舍、ERC-7201、初始化生命周期、v4→v5 禁止升级）；AGPL 与本仓库 MIT 不兼容，按许可规则表只作 reference，事实全部改从 OZ 源码 / ERC-7201 / 本机实验取证 |
| 9 | Cyfrin/solskill `skills/solidity` | <https://github.com/Cyfrin/solskill/tree/main/skills/solidity> | 144 | 2026-06-18 | AGPL-3.0（实读） | 32 条 Solidity 风格与安全规则 + CI | 3 | 2 | 3 | 3 | 2 | 13 | INCLUDE → **reference** | 唯一提到 0.8.28–0.8.33 transient storage 高危 bug 的候选，该说法已对 `argotorg/solidity` 的 `docs/bugs.json` 独立验证后才写入；AGPL → reference |
| 10 | OpenZeppelin/openzeppelin-contracts | <https://github.com/OpenZeppelin/openzeppelin-contracts> | 27238 | 2026-09-11 | MIT | 合约库本体（v5.7.0） | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 所有 5.x API 形状的事实来源：实读安装后的源码 + 本机测试断言自定义错误选择子 |
| 11 | foundry-rs/book | <https://github.com/foundry-rs/book> | 961 | 2026-09-10 | Apache-2.0（实读 LICENSE-APACHE 正文） | Foundry 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `[fuzz]`/`[invariant]` 配置语义（含 `fail_on_revert` 两侧默认值相反）与 `bound` vs `assume`；其余 Foundry 事实全部本机实测 |
| 12 | argotorg/solidity `docs/bugs.json` | <https://github.com/argotorg/solidity/blob/develop/docs/bugs.json> | 25735 | 2026-09-11 | GPL-3.0（实读 LICENSE.txt；`docs/` 下无独立许可文件） | 编译器已知 bug 机读数据 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE → **reference** | 版本门的唯一权威依据；GPL-3.0 → reference，只引用版本号、bug 名、严重级与修复版本，不抄文档正文 |
| 13 | crytic/slither | <https://github.com/crytic/slither> | 6361 | 2026-09-09 | AGPL-3.0（实读） | 静态分析器（102 detectors） | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE → **reference** | detector 名与语义参考；本 skill 里每条 Slither 断言都由 0.11.6 在本 skill 自己的夹具上跑出来 |
| 14 | ethereum/ERCs `ERCS/erc-7201.md` | <https://github.com/ethereum/ERCs/blob/master/ERCS/erc-7201.md> | 754 | 2026-09-09 | CC0-1.0（实读 CC0 正文） | 命名空间存储规范 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `erc7201` 公式、`- 1` 与二次哈希的理由、`@custom:storage-location` 自 0.8.20 进 AST、编译器不做强制 |
| 15 | crytic/properties | <https://github.com/crytic/properties> | 371 | 2026-03-09 | AGPL-3.0（实读） | 168 条现成属性（ERC20 25 / ERC721 19 / ERC4626 37 / ABDK 106） | 3 | 0 | 3 | 3 | 2 | 11 | INCLUDE → **reference** | 不变量词汇的对照表；AGPL copyleft 触及网络分发，本 skill 明确告诉读者只学属性名与 harness 形状、不要 vendor 其 `.sol` |
| 16 | Cyfrin/aderyn | <https://github.com/Cyfrin/aderyn> | 796 | 2026-09-06 | GPL-3.0 | Rust 静态分析器 | 2 | 3 | 2 | 2 | 2 | 11 | INCLUDE → **reference** | 只值一行「第二套 detector 的分歧本身是信号」；GPL → reference |
| 17 | tenequm/skills `skills/foundry-solidity` | <https://github.com/tenequm/skills/tree/main/skills/foundry-solidity> | 36 | 2026-09-10 | **目录级 Apache-2.0**（仓库根是 MIT，`skills/foundry-solidity/LICENSE.txt` 是 Apache-2.0 全文） | Foundry 全流程 + 15 个 reference | 1 | 3 | 3 | 1 | 2 | 10 | INCLUDE | 测试命名约定与「一条命令即完成定义」的 CI 门可用；正文钉在 Foundry 1.5.0 / Solidity 0.8.30，示例断言 OZ 4.x 的 `ReentrancyGuard` 字符串 revert，`PRIVATE_KEY` 作 primaryEnv 与本 skill 的密钥规则相反 |
| 18 | mrheyday/agentic-solidity-foundry-skill | <https://github.com/mrheyday/agentic-solidity-foundry-skill> | 0 | 2026-07-28 | Apache-2.0（实读，**无版权人行**） | 同 #17 的内容 | 0 | 2 | 3 | 2 | 1 | 8 | REJECT（重复 + 溯源） | 其 frontmatter 的 homepage 指向 #17，是未署名的再上传；且 vendored 树里混有 AGPL 与 no-license 材料，仓库级 Apache-2.0 覆盖不了。取上游 #17 |
| 19 | max-taylor/Claude-Solidity-Skills | <https://github.com/max-taylor/Claude-Solidity-Skills> | 8 | 2026-02-19 | **无**（全树无 LICENSE 文件；仅 `.claude-plugin/plugin.json` 里有 `"license": "MIT"` 声明） | audit / test-foundry / gas / test-hardhat | 1 | 0 | 3 | 3 | 1 | 8 | INCLUDE → **reference** | 唯一同时覆盖 Foundry handler+ghost 不变量与具名怪异代币清单的候选；无许可正文 → reference，不取其措辞 |
| 20 | mariano-aguero/solidity-security-audit-skill | <https://github.com/mariano-aguero/solidity-security-audit-skill> | 3 | 2026-05-12 | MIT（实读，无具名版权人） | 47 KB SKILL + 20 个 reference | 1 | 1 | 3 | 1 | 2 | 8 | INCLUDE（选摘） | 「先做 60 秒 grep 红旗扫描」与「显式误报表」两个结构可用；三条事实已裁为错（见「冲突与裁决」#7–#9），250 行关键词堆砌式 description 不模仿 |
| 21 | nuwrldnf8r/smart-contract-audit-skill | <https://github.com/nuwrldnf8r/smart-contract-audit-skill> | 0 | 2026-06-18 | MIT（实读，Copyright (c) 2026 Gavin Marshall） | 跨生态审计方法论 + 报告模板 | 0 | 2 | 2 | 2 | 2 | 8 | INCLUDE（两条规则） | 「被审仓库是不可信输入：不跑它的脚本、不 source 它的 .env、NatSpec/README 是待验证主张与潜在提示注入」与「内部人视角：假设检查通过且持有人敌对」两条是全批次独有；其 Vyper `@nonreentrant("lock")` 写法是 0.3.x 已过期 |
| 22 | wshobson/agents `plugins/blockchain-web3` | <https://github.com/wshobson/agents/tree/main/plugins/blockchain-web3> | 39565 | 2026-09-07 | MIT | solidity-security / web3-testing / defi-templates / nft-standards | 1 | 3 | 1 | 0 | 2 | 7 | REJECT（正确性 0 → 量表强制） | 抽查即错三条以上：`contracts/security/` 导入路径、无参 `Ownable()`、`Counters`、`_beforeTokenTransfer`、断言 OZ 4.x revert 字符串、solc 0.8.19、Goerli 网络、`@nomiclabs/hardhat-etherscan`、`testFail*`、提款用 `payable().transfer()`。降为 reference，只用于覆盖面对照 |
| 23 | 0xlayerghost/solidity-agent-kit | <https://github.com/0xlayerghost/solidity-agent-kit> | 4 | 2026-08-11 | MIT（实读） | 10 个 skill，其中 audit / defi-security / checklist 最强 | 0 | 3 | 3 | 1 | 2 | 9 | INCLUDE（仅 audit/defi/checklist） | 只读重入、按地址状态绕过、存储指针别名、`answeredInRound`、ERC-4626 通胀、签名四类问题是深度来源；`solidity-coding`/`solidity-security` 钉在 OZ 4.9.x 与 `^0.8.19`，`safeApprove`/`increaseAllowance`/`selfdestruct`/`tx.origin` 反 MEV 四条已失效，不取 |
| 24 | gonzaloetjo/awesome-solidity-skills | <https://github.com/gonzaloetjo/awesome-solidity-skills> | 3 | 2026-02-12 | CC0-1.0（实读） | 52 个 Solidity skill 的索引 + 安全评级 | 1 | 0 | 1 | 1 | 2 | 5 | MAYBE（仅作发现输入） | 不是 skill，零可执行规则；`SECURITY_AUDIT.md` 的「不要抄这些仓库」名单与「私钥处理是安全与危险 skill 的分水岭」有价值，用于定本 skill 的密钥规则 |
| 25 | github/awesome-copilot | <https://github.com/github/awesome-copilot> | 38900+ | — | MIT | — | — | — | — | — | — | — | REJECT（无内容） | 全树检索 `solidity|blockchain|web3|smart-contract` 零命中；GitHub 官方 skill 集合不含 EVM 主题，本 skill 无法从这条路取材 |

## 深度审查

### pashov/skills（`solidity-auditor` / `fizz` / `x-ray`，MIT）

三个 skill 是同一支审计团队的三段流水线：x-ray 做审计前侦察并产出不变量目录，fizz 把它变成模糊测试套件，solidity-auditor 派 12 个专项 agent 去猎 bug。frontmatter 干净（只有 `name` + `description`），但强绑 Claude Code（后台 Agent、AskUserQuestion、TodoWrite、运行时 `git clone` 自己进 `~/.claude/skills`），并带 ASCII 横幅与 pashov.com 页脚——这些全部剥离。真正值钱的是三样东西：**漏洞分类学**（舍入方向按数量分类、先除后乘、精度不匹配、窄化转换、首存款人份额通胀、初始化抢跑、角色提权、`renounceRole` 砖化、代理存储与 admin 槽冲突、单块预言机读、ERC-4626 与 permit 边界、`IERC20` 操作里的哨兵地址）、**证据纪律**（没有攻击路径的主张只能是 lead）、**handler 形状**（clamp 而非 reject、acting-actor 修饰符、donation handler、ghost 与 snapshot 放在合约之外）。`x-ray` 的 epistemics 最严：「无法验证就删行，『无法确认』不是合法行」——本 skill 的 gate 写法沿用这条。

### trailofbits/skills（CC-BY-SA-4.0）

母仓库 7040★、两天前推送，权威度与新鲜度都满分，但**内容分布与仓库名不符**：`building-secure-contracts` 的 11 个 skill 里没有任何 Solidity/EVM 漏洞扫描器，只有 Algorand、Cairo、Cosmos、Solana、Substrate、TON 六条链的扫描器，加上 `audit-prep-assistant`、`code-maturity-assessor`、`guidelines-advisor`、`secure-workflow-guide`、`token-integration-analyzer`。EVM 专属材料只存在于 `cosmos-vulnerability-scanner/resources/EVM_VULNERABILITY_PATTERNS.md`，而那是 Cosmos-EVM precompile 的问题，不是普通 Solidity。所以这家最权威的上游对本 skill 的贡献集中在两处：**怪异 ERC-20 目录**（24 项，带具名代币）与 **`Rationalizations (Do Not Skip)` 表**（预先堵住偷懒借口的可执行规则）。`property-based-testing` 是本批次单份质量最高的文件，且 Echidna/Medusa 就是这家出的；但它 frontmatter 明确把 Foundry 的 invariant 引擎排除在外，所以本 skill 的 invariant 章只能自己实测补齐。share-alike 与本仓库 MIT 不兼容 → 只取清单语义、全部重写。

### OpenZeppelin/openzeppelin-skills（AGPL-3.0 → reference）

`upgrade-solidity-contracts` 是全批次最精确的升级文档：UUPS/Transparent/Beacon 取舍表、v4→v5 代理升级禁止、`_disableInitializers`/`reinitializer`/`onlyInitializing` 生命周期、ERC-7201 与槽计算命令、Hardhat 与 Foundry 两套 upgrades 插件、校验问题的升级式抑制层级（改根因 → 注解 → 窄标志 → 宽绕过）。它刻意不写死版本号，并反复强调「不要凭记忆假设 override 点，去读安装后的源码」——这条被本 skill 直接采纳为规则 22。AGPL 决定它只能 reference：覆盖面照它对，事实全部改从 OZ 源码、ERC-7201 与本机实验重新取证。`dev/TESTING.md` 是一套 LLM 行为评测（653 行、约 30 个 prompt+Expected），与本仓库 `evals/` 思路一致，但不是合约测试材料。

### Cyfrin/solskill（AGPL-3.0 → reference）

302 行、32 条编号规则，是唯一带当前版本门的社区候选：`0.8.34+` 作为下限、`ReentrancyGuardTransient` 要求 `^0.8.34`、`forge build --sizes` 卡 24 KB、`forge install` 不再需要 `--no-commit`、`Ownable2Step` 优先、私钥走 `--account`/keystore 而非 `vm.envUint`、admin 第一天就上多签、BTT `.tree` 文件、Chimera 多 fuzzer。它的 0.8.28–0.8.33 transient storage 说法是本次最值钱的线索，但**没有直接采信**：改去读 `argotorg/solidity` 的 `docs/bugs.json`，确认为 `TransientStorageClearingHelperCollision`（high，introduced 0.8.28，fixed 0.8.34）之后才写进正文。

### 0xlayerghost/solidity-agent-kit（MIT，4★）

星标数与内容质量严重不匹配。`solidity-audit`（397 行、19 类漏洞）、`defi-security`、`solidity-checklist` 三个 skill 是表格驱动的陷阱清单，引 EVMbench 论文、Code4rena 报告与事故复盘，并且提供了别处都没有的深度：**只读重入单列一类**、按地址状态绕过（含 `max()` 传播修法与 `block.timestamp` 阻塞陷阱）、存储指针别名与嵌套 `delete`、`answeredInRound` 与陈旧性、ERC-4626 通胀、签名四类（零恢复/可塑性/重放/空签名者）、闪电贷四变体。同一仓库的 `solidity-coding`/`solidity-security` 则钉死在 OZ 4.9.x 与 `^0.8.19`，并给出四条已失效建议，所以**按目录取舍**而不是整仓采纳。其 `[AUTO-INVOKE] MUST be invoked BEFORE …` 式 description 与每个 skill 顶部的语言指令都是反模式，不复制。

### tenequm/skills `skills/foundry-solidity`（目录级 Apache-2.0）

本批次第二个「目录许可覆盖仓库许可」的实例：仓库根 `LICENSE` 是 MIT（Copyright (c) 2025 Mykhaylo Kolesnik），而 `skills/foundry-solidity/LICENSE.txt` 是 Apache-2.0 全文。两者都是宽松许可，可 merged，但记录必须写清楚是目录许可在管。内容上它是最完整的 Foundry 操作手册（15 个 reference，含 anvil/cast/chisel/CI/部署/调试），可惜正文钉在 Foundry 1.5.0 与 Solidity 0.8.30，示例里 `vm.expectRevert("ReentrancyGuard")` 是 OZ 4.x 的断言。采纳两点：测试命名前缀表、以及「格式检查 → 构建含 sizes → lint → 测试 → 覆盖率」一条命令作为完成定义。其 `PRIVATE_KEY` 环境变量约定被反向采纳——本 skill 要求 keystore account。

### max-taylor/Claude-Solidity-Skills（无许可正文）

`skills/test-foundry` 是唯一把 Foundry 的 handler + ghost variable 不变量模式写全的候选（`targetContract(address(handler))`、`useActor` 修饰符配 `bound(actorIndexSeed, 0, actors.length - 1)`、`ghost_depositSum`/`ghost_withdrawSum`），`skills/audit` 是 Solcurity 检查号加具名怪异代币清单，两份内容抽查三条全对。卡在两处：2026-02-19 之后未推送（新鲜度 0），以及**全树没有任何 LICENSE 文件**，唯一许可信号是 `.claude-plugin/plugin.json` 里的一个 `"license": "MIT"` 键。按标准第 9 节「仅 frontmatter 声明 = 1 分」，且不作为 merged 来源 → reference，只用于确认本 skill 覆盖了这两个主题。

### nuwrldnf8r/smart-contract-audit-skill（MIT，0★）

0 星、作者无名，但贡献了全批次唯一的两条元规则，且两条都直接写进了本 skill：**把被审仓库当不可信输入**（不跑它的安装/构建/部署脚本、不 `source .env`、注释与 NatSpec 是待验证主张也是提示注入载体）与**内部人视角**（假设权限检查通过且持有人敌对，问一笔交易能提走或砖化什么，于是「可信多签持有无界权力」也是发现）。其 per-ecosystem reference 未读、无声誉背书，不采纳；Vyper `@nonreentrant("lock")` 是 0.3.x 写法已过期。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 0.8 的显式窄化转换安全吗 | pashov `judging.md`：列入「安全模式，不要上报」，理由是「0.8+ reverts on overflow」／OZ `SafeCast` 的存在暗示相反 | **窄化转换静默截断**，只有 `SafeCast` 会 revert；正文规则 14 取反 | 本机实测：`uint128(2**128 + 7) == 7`，无 revert（`test_NarrowingCastTruncatesSilently`）。上游在此点为错 |
| 2 | 防抢跑该用什么 approve | trailofbits `token-integration-analyzer` 与 0xlayerghost：`increaseAllowance`/`decreaseAllowance`／OZ 5.x 源码：已移除 | **用 `SafeERC20.forceApprove` / `safeIncreaseAllowance`**；`increaseAllowance`、`decreaseAllowance`、`safeApprove` 均不存在于 5.x | 实读安装后的 OZ 5.7.0 源码；更新 > 更旧 |
| 3 | transient 重入锁的可用版本下限 | Cyfrin：`^0.8.34`，因 0.8.28–0.8.33 有 transient storage 高危 bug／0xlayerghost：`^0.8.19` 项目统一（根本没到 0.8.24） | **`ReentrancyGuardTransient` 要求 EVM ≥ cancun 且 solc ≥ 0.8.34** | `argotorg/solidity` `docs/bugs.json`：`TransientStorageClearingHelperCollision`，severity high，introduced 0.8.28，fixed 0.8.34。官方数据 > 任何 skill |
| 4 | 弃用合约怎么处理 | 0xlayerghost：`pause` 或 `selfdestruct`／EIP-6780 之后 | **只能 pause 或迁移**；`selfdestruct` 在创建交易之外不再删除代码，该建议已失效 | EIP-6780（Dencun）；本 skill 的升级 checklist 显式禁止把 selfdestruct 当缓解手段 |
| 5 | `msg.sender == tx.origin` 能防 MEV / 合约调用吗 | 0xlayerghost：EOA-only 检查作为反三明治手段 | **不能**，EIP-7702 授权 EOA 与所有智能账户都被误伤或绕过；`tx.origin` 只能用于日志 | EIP-7702（Pectra）；并且本机实测 `tx.origin` 授权可被中继合约满足（`test_TxOriginGuardPassesForRelayedCall`） |
| 6 | Slither 有多少 detector | trailofbits：「70+ built-in detectors」、`slither-check-upgradeability`「17 ways」 | **102 个 detector；`slither-check-upgradeability` 22 个** | 本机 Slither 0.11.6 输出：`. analyzed (21 contracts with 102 detectors), 32 result(s) found`；`7 findings, 22 detectors run` |
| 7 | `payable().transfer()` 会在哪个版本编译失败 | mariano：「Solidity 0.9.0 起不再编译」 | **不存在 0.9.0**，当前稳定版是 0.8.37；该条作为迁移门是伪事实，改写为「2300 gas 会让合约收款人失败」这一可验证后果 | `gh api repos/argotorg/solidity/releases/latest` → `v0.8.37`（2026-09-10） |
| 8 | TSTORE 是否让 2300 gas 补贴不再阻止重入 | mariano：「若 callee 用 TSTORE，2300 gas 补贴不再阻止重入」 | **错**：2300 gas 连一次再入 `CALL` 都付不起 | 实测 trace：`[2300] HungryRecipient::receive{value: 1e18}() → [OutOfGas]` |
| 9 | transient storage bug 的版本区间 | mariano：「0.8.28–0.8.33 + `--via-ir` 会污染槽」，自标 UNVERIFIED | 区间碰巧与官方一致，但**改用官方 bug 名与严重级表述**，并补齐 0.8.36/0.8.37 修掉的另外四条 | `docs/bugs.json` / `docs/bugs_by_version.json`；0.8.37 是第一个已知 bug 列表为空的版本 |
| 10 | 理解阶段能不能命名漏洞 | trailofbits `audit-context-building`：禁止命名漏洞、禁止评级、禁止写 PoC／pashov `solidity-auditor`：同一遍里就要出 FINDING + 修复 diff + 置信度／x-ray：不写利用叙事但给威胁模型与结论 | **本 skill 走 pashov/x-ray 的一次过路线**，但保留 lead/finding 两态：没有可复现 PoC 的候选只能是 lead。评级方法论不进本 skill，归 `security-review` | 「一个 agent 做一次评审」的现实约束；分界见 `docs/roadmap.md` 与本 skill `## Scope` |
| 11 | `nonReentrant` 该不该上报 | pashov `judging.md`：列为安全模式，「只上报跨合约攻击」／x-ray：逐入口记录 guard 状态，且 AMM 档仍要求追 ERC-777/1155 回调重入／`boundary-agent`：必须追 `onERC721Received` 再入 | **规则写一次**：有 guard 时只有跨函数、跨合约、回调与只读重入可上报；并强调 guard 必须覆盖 hook 路径与 view 路径 | 上游自相矛盾 → 取两者的交集并写成可证伪形式；本机实测 hook 路径先于任何状态写入被触达 |
| 12 | 覆盖率数字能不能当结论 | `audit-prep-assistant`：94% statements 是「EXCELLENT」／x-ray：不得从覆盖率工具失败推断任何事／fizz：`via_ir` 下覆盖率虚低 10–20%，必须先校正 | **读分支列而不是行列；工具报错只说明工具报错** | 本机实测：夹具套件 63.83% 行 / 35.00% 分支，未覆盖的分支正好是有漏洞的那几条 |
| 13 | 哪个 fuzzer 是主力 | fizz：硬依赖 Medusa，Echidna 可选，禁止同时跑／trailofbits `secure-workflow-guide`：只提 Echidna（和已停维护的 Manticore）／两家都不提 `forge` 的 invariant 引擎 | **Foundry invariant 作为仓内 CI 默认，Echidna/Medusa 作为深度战役的逃生口**，两者的反例都转成 Foundry 单测 | 无外部工具链即可在 CI 跑通是本仓库的一贯取舍；`forge` 的 invariant 语义由本机实测补齐 |
| 14 | Manticore / `slither-prop` | trailofbits 推荐 Manticore 做形式化验证、`slither-prop` 以 Truffle 为前提 | **不写 Manticore**（已停维护）；符号执行只提 Halmos/hevm，且限定为「某个函数要对所有输入成立」的场合 | 上游自身停止维护该项目；Truffle 门控与当前 Foundry 主流不符 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `pashov-auditor` | pashov/skills `solidity-auditor` (MIT) | merged | 漏洞分类学与证据纪律（lead vs finding） |
| `pashov-fizz` | pashov/skills `fizz` (MIT) | merged | handler 形状、clamp 而非 reject、donation handler、ghost/snapshot |
| `pashov-xray` | pashov/skills `x-ray` (MIT) | merged | 按协议类型的不变量目录；guard≠invariant 的抬升法；无法验证即删行 |
| `tob-secure-contracts` | trailofbits/skills `building-secure-contracts` (CC-BY-SA-4.0) | merged（仅清单语义） | 怪异 ERC-20 目录；成熟度九轴；先跑便宜的静态分析 |
| `tob-property-testing` | trailofbits/skills `property-based-testing` (CC-BY-SA-4.0) | merged（仅清单语义） | tautology/vacuity、属性强度排序、Echidna 属性函数约束 |
| `oz-contracts` | OpenZeppelin/openzeppelin-contracts v5.7.0 (MIT) | merged | 全部 5.x API 形状与自定义错误（实读源码 + 本机断言） |
| `erc-7201` | ethereum/ERCs `erc-7201` (CC0-1.0) | merged | 命名空间存储公式与其理由 |
| `foundry-book` | foundry-rs/book (Apache-2.0) | merged | `[fuzz]`/`[invariant]` 配置语义与 `bound` vs `assume` |
| `tenequm-foundry` | tenequm/skills `skills/foundry-solidity`（目录 Apache-2.0） | merged | 测试命名约定；一条命令的完成定义 |
| `layerghost-kit` | 0xlayerghost/solidity-agent-kit (MIT) | merged（仅 audit/defi/checklist） | 只读重入、按地址绕过、存储指针、签名四类、ERC-4626 通胀 |
| `mariano-audit` | mariano-aguero/solidity-security-audit-skill (MIT) | merged | 红旗快扫 + 显式误报表两个结构 |
| `nuwrldnf8r-audit` | nuwrldnf8r/smart-contract-audit-skill (MIT) | merged | 被审仓库是不可信输入；内部人视角 |
| `oz-skills` | OpenZeppelin/openzeppelin-skills (AGPL-3.0) | reference | 升级章覆盖面；「读安装后的源码而非凭记忆」 |
| `cyfrin-solskill` | Cyfrin/solskill (AGPL-3.0) | reference | 版本门线索（transient storage bug），经官方 bug 列表独立验证后采用 |
| `solidity-docs` | argotorg/solidity `docs/bugs*.json` (GPL-3.0) | reference | 编译器已知 bug 的严重级与修复版本 |
| `slither` | crytic/slither (AGPL-3.0) | reference | detector 语义；所有断言本机实测 |
| `crytic-properties` | crytic/properties (AGPL-3.0) | reference | 不变量词汇对照；明确告知不要 vendor |
| `aderyn` | Cyfrin/aderyn (GPL-3.0) | reference | 第二套 detector 的存在价值 |
| `max-taylor-sol` | max-taylor/Claude-Solidity-Skills（无许可正文） | reference | Foundry handler+ghost 与怪异代币清单的覆盖面对照 |
| `wshobson-solsec` | wshobson/agents `blockchain-web3` (MIT) | reference | 最小类目清单的覆盖面对照（正确性 0，量表强制不得 merged） |

## 实测记录（Phase C 取证）

工具版本，全部本机安装：

```
$ forge --version
forge Version: 1.8.1
Commit SHA: 982849d3140c01fd3b72905759581a132df7aa98
Build Timestamp: 2026-08-28T17:46:00.964391484Z (1787939160)
Build Profile: dist

$ cast --version   → cast 1.8.1 (同 commit)
$ anvil --version  → anvil 1.8.1 (同 commit)
$ slither --version → 0.11.6
solc: 0.8.36（forge 自动下载）与 0.8.37（`--use 0.8.37` 拉取后成为默认）
OpenZeppelin: contracts v5.7.0 @ cab19933c33c2ad1d4c7a84864a3601dddfd16f3
             contracts-upgradeable v5.7.0 @ 14f52c54d3a1eefbda3d4071efba24d3c1e07e8a
实验工程：/tmp/sw3-lab（forge init + 本 skill 的三个夹具合约）
```

### E1 编译器选择不是仓库属性

```
$ forge build          # pragma ^0.8.24，全新机器
Compiling 38 files with Solc 0.8.36
installing solc version "0.8.36"
Successfully installed solc 0.8.36
$ forge build --use 0.8.37
Compiling 50 files with Solc 0.8.37
$ forge clean && forge build --force
Compiling 52 files with Solc 0.8.37
```

0.8.37 在 2026-09-10 已发布，forge 1.8.1（2026-08-28 构建）默认仍选 0.8.36；本地装了 0.8.37 之后默认改变。→ 规则 1。

### E2 OZ 4.x 代码在 5.7.0 上的真实报错

```
$ # import "@openzeppelin/contracts/security/ReentrancyGuard.sol"
ERROR foundry_compilers_artifacts_solc::sources: error=".../contracts/security/ReentrancyGuard.sol": No such file or directory
Unable to resolve imports: "@openzeppelin/contracts/security/ReentrancyGuard.sol"

$ # contract Legacy is Ownable, ReentrancyGuard { constructor() {} }
Error (3415): No arguments passed to the base constructor. Specify the arguments or mark "Legacy" as abstract.
Note: Base constructor parameters:
  --> lib/openzeppelin-contracts/contracts/access/Ownable.sol:38:16:
38 |     constructor(address initialOwner) {

$ # initialize() { __UUPSUpgradeable_init(); }
Error (7576): Undeclared identifier.
18 |         __UUPSUpgradeable_init();
```

另：`contracts-upgradeable/proxy/utils/{Initializable,UUPSUpgradeable}.sol` 在 5.7.0 里只有两行，是 re-export shim，必须同时 remap 两个包。→ 规则 22 与 `## Environment`。

### E3 重入实测（`evals/files/Vault.sol`）

```
$ forge test --match-path test/Poc.t.sol -vv
[PASS] test_ReentrancyDrainsVault() (gas: 535550)
Logs:
  vault balance before 10000000000000000000
  vault balance after  0
  drainer balance      12000000000000000000
  reentrant hits       10

[PASS] test_PartialWithdrawReentrancyRevertsOnUnderflow() (gas: 490571)
[PASS] test_ReadOnlyReentrancyObservesStaleShare() (gas: 636455)
Logs:
  share quoted outside callback 333333333333333333
  share quoted inside callback  333333333333333333
  totalDeposits inside callback 15000000000000000000
  vault ETH inside callback     10000000000000000000

[PASS] test_TxOriginGuardPassesForRelayedCall() (gas: 280842)
[PASS] test_AnyoneCanSetFeeRecipient() (gas: 38679)
```

三条独立事实：`withdrawAll` 可被 1 ETH 本金掏空 10 ETH（10 次再入）；`withdraw(amount)` 的同型错误因 0.8 下溢检查而整笔 revert（`transfer failed`），是拒绝服务不是盗取；回调中 `totalDeposits` 报 15 ETH 而合约只剩 10 ETH——只读重入的受害者是集成方。→ 规则 3、4、6、8、9。

### E4 2300 gas 补贴（`-vvvv` trace）

```
├─ [37759] Vault::payFees(1000000000000000000 [1e18])
│   ├─ [2300] HungryRecipient::receive{value: 1000000000000000000}()
│   │   └─ ← [OutOfGas] EvmError: OutOfGas
│   └─ ← [Revert] EvmError: Revert
```

→ 规则 10、11。

### E5 代理升级：存储冲突与越权升级

```
$ forge inspect src/StakingUpgradeable.sol:StakingV1 storage-layout
| stakingToken | contract IERC20 | 0 |   | totalStaked | uint256 | 1 |
| stakedOf | mapping(address => uint256) | 2 |   | cooldown | uint256 | 3 |
$ forge inspect src/StakingUpgradeable.sol:StakingV2 storage-layout
| rewardRate | uint256 | 0 |   | treasury | address | 1 |   | stakingToken | IERC20 | 2 |
| totalStaked | uint256 | 3 |  | stakedOf | mapping | 4 |    | cooldown | uint256 | 5 |

$ forge test --match-path test/Proxy.t.sol -vv
[PASS] test_Erc1967SlotMatchesConstant()
[PASS] test_AttackerUpgradesProxyBecauseAuthorizeIsEmpty()
Logs:
  implementation after attacker upgrade
  0xF62849F9A0B5Bf2913b396098F7c7019b51A820a
[PASS] test_ImplementationIsInitializableByAnyone()
[PASS] test_StorageCollisionAfterUpgrade()
Logs:
  V1 totalStaked  (slot 1) 7000000000000000000
  V2 treasury     (slot 1) 0x0000000000000000000000006124feE993BC0000
  V2 totalStaked  (slot 3) 604800
[PASS] test_V2ConstructorValueIsInvisibleThroughProxy()
Logs:
  rewardRate seen through proxy 57005
[PASS] test_InitializeV2RevertsAfterUpgrade()
[PASS] test_UpgradeToWasRemovedInV5()
```

V1 自己的变量从槽 0 开始（5.x 的可升级基类走 ERC-7201 命名空间，不占顺序槽，也不需要 `__gap`）；升级后 `treasury` 变成由金额推出来的地址、`totalStaked` 变成 604800 秒、`rewardRate` 变成旧的 `stakingToken` 地址 `0xdead`(=57005)；空 `_authorizeUpgrade` 让任意地址完成了升级；`initializer` 在已初始化代理上 revert `InvalidInitialization()`；`upgradeTo(address)` 在 5.x 已不存在。→ 规则 17–21。

### E6 精度与预言机（`evals/files/LendingDesk.sol`）

```
$ forge test --match-path test/Precision.t.sol -vv
[PASS] test_SpotPriceMovesWithASingleSwap()
Logs:
  price before swap 2000000000000000000000
  price after  swap 80000000000000000000
[PASS] test_BorrowUsesManipulatedPrice()
Logs:
  manipulated price 50000000000000000000000
  debt after borrow 300000000000000000000000
[PASS] test_AccruedInterestLosesPrecision()
Logs:
  debt               1000000000
  interest charged   31536000
  interest owed      50000000
  under-charged by % 37
```

→ 规则 13、15。

### E7 主网 fork：Chainlink 陈旧性

`[rpc_endpoints] mainnet = "https://ethereum-rpc.publicnode.com"`，fork 区块 25953358，ETH/USD 聚合器 `0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419`：

```
$ forge test --match-path test/Fork.t.sol -vv
[PASS] test_FeedRoundShape()
Logs:
  description   ETH / USD
  decimals      8
  roundId       129127208515966894815
  answer        247209000000
  updatedAt     1789119107
  block.ts      1789120055
  age (s)       948
[PASS] test_LatestAnswerStillExists()
Logs:
  latestAnswer 247209000000
[PASS] test_StaleFeedIsAcceptedWithoutACheck()
Logs:
  answer 30 days later 247209000000
  updatedAt unchanged  1789119107
  age (s)              2592000
```

`vm.warp(updatedAt + 30 days)` 之后读数与 `updatedAt` 都不变——调用本身不会告诉你数据已经一个月前；`latestAnswer()` 仍然存在，所以它还会继续出现在新代码里。→ 规则 16。

### E8 不变量测试：假绿与真失败

同一个套件，只改 handler 里的 `feeRecipient`：

```
# handler 的 payFees 全部 revert（收款人不能收 ETH）
[PASS] invariant_SolvencyBacksAccounting
 VaultInvariantTest invariants (runs: 256, calls: 128000, reverts: 42678)
| VaultHandler | deposit  | 42732 | 0     |
| VaultHandler | payFees  | 42678 | 42678 |   ← 一次都没真正执行
| VaultHandler | withdraw | 42590 | 0     |
Suite result: ok. 1 passed
```

```
# 修好 handler 之后
[FAIL: assertion failed: 844264577245486604 < 844264577245486654] invariant_SolvencyBacksAccounting
        [Sequence] (original: 7, shrunk: 2)
                sender=0x…A1 calldata=deposit(uint256,uint256) args=[0, 6.654e38]
                sender=0x…4d9 calldata=payFees(uint256) args=[50]
 VaultInvariantTest invariants (runs: 256, calls: 128000, reverts: 9563)
Fuzz seed: 0x42437f2d7955fabe48f6caf606e2d48a6713eb38518530ecfcc2f247410ceef3
```

`runs 256 × depth 500 = 128000` 与 foundry book 的 `[invariant]` 默认值一致；`fail_on_revert` 在 `[invariant]` 侧默认 `false`、在 `[fuzz]` 侧默认 `true`，这就是「全 revert 也报 PASS」的机制。→ 规则 23。

### E9 OZ 5.x revert 形状与 `expectRevert` 陷阱

```
$ forge test --match-path test/OzShapes.t.sol -vv
[PASS] test_OwnableRevertShape()                  # OwnableUnauthorizedAccount(address)
[PASS] test_Erc20InsufficientBalanceShape()       # ERC20InsufficientBalance(address,uint256,uint256)
[PASS] test_ReentrancyGuardRevertShape()          # ReentrancyGuardReentrantCall()
[PASS] test_BareExpectRevertAcceptsWrongReason()  # 裸 expectRevert 吃下了访问控制错误
[PASS] test_NarrowingCastTruncatesSilently()
Logs:
  uint128(2**128 + 7) = 7
[PASS] test_CheckedArithmeticPanics()             # stdError.arithmeticError
```

`stdError` 必须显式 `import {Test, stdError} from "forge-std/Test.sol"`，否则报 `Error (7576): Undeclared identifier`。→ 规则 14、22、24。

### E10 覆盖率、格式、lint

```
$ forge coverage --match-path "test/Vault.t.sol" --no-match-coverage "(test|script|lib)"
| src/Vault.sol | 63.83% (30/47) | 64.29% (27/42) | 35.00% (7/20) | 54.55% (6/11) |
[FAIL: not owner] test_SetFeeBps()      ← 夹具里的 happy-path 测试因 tx.origin 而失败
$ forge fmt --check src/   → exit 0
$ forge build            → note[custom-errors] / note[literal-instead-of-constant]
                           warning[erc20-unchecked-transfer] / help: .../linting/calls-loop
```

### E11 Slither 0.11.6 在本 skill 夹具上的命中与盲区

```
$ slither . --exclude-dependencies --filter-paths "lib|test"
Detector: reentrancy-eth        ← withdraw 与 withdrawAll，附跨函数变量清单
Detector: unchecked-transfer    ← 8 处
Detector: uninitialized-state   ← StakingV2.stakingToken
Detector: divide-before-multiply← 3 处（只有 accrued 那条是真问题）
Detector: tx-origin             ← setFeeBps / setRewardHook
Detector: unused-return / missing-zero-check / calls-loop
Detector: reentrancy-benign / reentrancy-events / low-level-calls
Detector: constable-states      ← 误报：建议把 StakingV2.stakingToken/cooldown 改成 constant
Detector: immutable-states
INFO:Slither:. analyzed (21 contracts with 102 detectors), 32 result(s) found

$ slither-check-upgradeability . StakingV1 --new-contract-name StakingV2
Detector: initialize-target / order-vars-contracts / extra-vars-v2
  StakingV1.totalStaked ↔ StakingV2.treasury（以及另外三对）
INFO:Slither:7 findings, 22 detectors run
```

未命中：`setFeeRecipient` 的缺失鉴权（只报了零地址检查）、`shareOf` 的只读重入、空 `_authorizeUpgrade`、缺失 `_disableInitializers()`、现货预言机与陈旧性、2300 gas 补贴。→ 规则 25 与 `references/static-analysis-and-audit-checklist.md`。

### 未验证项（标 `[official]` 而非 `[verified]`）

- `TransientStorageClearingHelperCollision` 的实际触发条件（只读了官方 `docs/bugs.json` 的元数据，没有构造 miscompilation 复现）。
- Transparent 代理在 5.x 的构造函数第二参数是 `ProxyAdmin` 的 owner：读自 OZ 文档与源码注释，未部署验证。
- v4→v5 代理升级不被支持：OZ 官方说法，未构造 4.x 实现来实测。
- Echidna / Medusa 的具体行为：本机未安装这两个 fuzzer，相关段落全部标 `[official]`，仅引 trailofbits 与 crytic 的文档说法。
- EIP-6780 之后 `selfdestruct` 的语义、EIP-7702 对 `tx.origin` 的影响：引规范，未在 fork 上构造实例。
- 24 KB 部署上限（EIP-170）：只用 `forge build --sizes` 读到尺寸，未真正部署超限合约。

## 基线缺口

无 skill（`uv run tools/run_evals.py solidity-web3 --baseline`，Claude Opus 5 / medium）。
**判定说明**：`tools/run_evals.py` 只把 `query` 传给被测 agent（`-p scenario["query"]`），`expected_behavior` 是人工评判用的量规、不进 prompt。
基线跑完后发现场景 4 零区分度、场景 2/3 只剩薄缺口，于是按 Phase B 把 `expected_behavior` 改写为**版本分界事实**与**会造成资金损失的判断**（题目与夹具一字未改），并用改写后的量规重新评判**同一批已捕获的转录**——prompt 未变，重跑只会引入噪声而不产生新测量。场景 1 因被服务端拒答，单独重跑过一次。

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 Vault 评审 | 全部 8 条（无产出） | 两次运行都在 agent 决定「写一个 PoC exploit 脚本」时被服务端 `Refusal (cyber)` 掐断：`events_bytes` 467123 与 169422，最后一条消息只有 thinking「Now I'm putting together a proof-of-concept exploit script」，没有任何 assistant 文本。不是超时也不是 stdin 问题。这条缺口是**框架性**的：同样的防御性任务，措辞成「攻击脚本」会被拒答，措辞成「带攻击者合约的 Foundry 回归测试」才能落地——正是本 skill 的 `## Scope` 与 workflow 规定的做法 |
| 2 代理升级 | ①未给出升级前的具体校验手段（没提 `forge inspect … storage-layout` 对比，也没提 `slither-check-upgradeability`）；②未说明这些工具查不到空 `_authorizeUpgrade` 与缺失 `_disableInitializers()`，所以不能只靠工具；③未提 5.x 可升级基类走 ERC-7201、V1 变量从槽 0 起（它的槽位表推对了，但没说明为什么没有 `__gap`） | 其余 4 条全部达成，而且质量很高：槽位逐条误读、`InvalidInitialization()`、构造函数死写入、`_authorizeUpgrade` 是「正在发生的活跃漏洞」并据此把时间压力反转。它自己声明「环境无 forge/solc/anvil，代码未经编译」，数值是用 Python 重算槽位得到的 |
| 3 强化测试 | ①未提 `[invariant] fail_on_revert` 默认 `false`，也未引用 per-selector calls/reverts 表作为「handler 真的执行了」的证据（它靠推理发现了 handler owner 不匹配会导致 `payFees` 空转，但没给出读表这个可复用手段）；②未把 `test_WithdrawRevertsWhenEmpty` 的裸 `vm.expectRevert()` 换成具体 selector，也未点出「裸断言会因错误原因假通过」这条通用规则（它只在自己新写的一条测试上发现了假通过）；③没有任何覆盖率测量，未覆盖函数靠叙述而非 `forge coverage` 数字 | 基线在这个场景异常强：自己补了工程脚手架、写了 30 个测试（19 通过 / 11 失败）、写了带 handler 的 invariant 并独立发现「handler 必须自己部署 Vault，否则 payFees 空转」、点出 `withdraw(uint256)` 因 0.8 下溢无法获利、点出 `transfer` 只给 2300 gas |
| 4 借贷定价审计 | 无（改写量规后仍为 0 缺口） | 8 条全达成，且超出题目：额外发现精度维度不匹配导致 1e12 倍超额借出、清算无还款可自清算、无 `repay` 函数、清算阈值等于 LTV 无缓冲、Base 的 sequencer uptime feed。改写量规后新增的「陈旧性上限要以该 feed 的 heartbeat 为依据 + 固定区块 fork 测试取证」一条，它说到了 heartbeat 但没要求 fork 取证——判为**部分达成**，不计入缺口 |
| 5 负例（React 组件） | 无（本就应当零缺口） | `skill_read=false`；按 React 问题修好了无依赖数组的 `useEffect`、函数式更新、稳定 `key`、`enabled` 门控，并自建 bun + happy-dom 冒烟验证；全程未涉及 Solidity |

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Vault 评审 | claude-opus-5 / medium | 无（基线，两次） | false | 0 / 8 | 服务端 `Refusal (cyber)`，无 assistant 文本；`events_bytes` 467123 与 169422 |
| 2 代理升级 | claude-opus-5 / medium | 无（基线） | false | 4 / 7 | 缺升级前校验手段、工具盲区、ERC-7201 槽位解释 |
| 3 强化测试 | claude-opus-5 / medium | 无（基线） | false | 3 / 6 | 缺 `fail_on_revert` 语义与读表、裸 `expectRevert` 通用规则、覆盖率测量 |
| 4 借贷定价审计 | claude-opus-5 / medium | 无（基线） | false | 8 / 8 | 零区分度，量规已按版本分界事实改写后重判，仍为 8/8 |
| 5 负例（React） | claude-opus-5 / medium | 无（基线） | false | 4 / 4 | 正确未触发本 skill |
| 1 Vault 评审 | claude-opus-5 / medium | 有 | true | **8 / 8** | 自行装 Foundry 并真跑 `forge test`：11 个 PoC 对未修代码全成立 + 9 个修复形态用例全被挡（20 passed）。只读重入实测 `shareOf` 从 `1e18` 涨到 `10e18`；点明 Slither 只报 `missing-zero-check` 掩盖了缺失鉴权；修复建议用 `Ownable2Step` / `OwnableUnauthorizedAccount` / `_reentrancyGuardEntered()`，并把 `ReentrancyGuardTransient` 门在 0.8.34；未改 `Vault.sol`，未提出攻击任何已部署合约 |
| 2 代理升级 | claude-opus-5 / medium | 有 | true | **7 / 7** | 槽位逐条误读（`treasury = 0x…03A352944000`、`totalStaked = 604800`）+ PoC 断言攻击者拿到 4M USDC；给出 `forge inspect storage-layout` 对比与 `slither-check-upgradeability`，并明说「Slither 对 F-1/F-2 一条都没报，工具命中只是线索」；`UPGRADE-REVIEW.md` 写明 OZ 5.7 可升级基类走 ERC-7201 不占顺序槽；要求主网 fork 演练并要求实读 ERC-1967 两个槽确认代理类型；额外提出修复升级交易本身会被抢跑，建议走私有通道 |
| 3 强化测试 | claude-opus-5 / medium | 有 | true | **6 / 6** | 22 个契约用例 + 9 个对抗用例（全红=9 个真实漏洞）+ handler 不变量；`foundry.toml` 写 `solc = "0.8.37"` 与 `[invariant] fail_on_revert = true`，并报「16384 次调用 / 0 revert，逐 selector 表已核对」；每条 revert 断言到具体原因；报 `src/Vault.sol` 分支覆盖率 100% (20/20)；在 `/tmp` 副本上验证 fail-before / pass-after 双向（32/32 绿）后删除 |
| 4 借贷定价审计 | claude-opus-5 / medium | 有 | true | **8 / 8** | 12 个 PoC 对未修代码全成立；把问题归成「定价层与记账层各有一个根本错误」而不是罗列 bug；额外联网核实了 Base sequencer uptime feed 地址；明确列出未覆盖项（无 RPC，池深度与 heartbeat 未在 fork 上核实）；指出 Slither 漏了 5 个 Critical 中的 3 个 |
| 5 负例（React） | claude-opus-5 / medium | 有 | **false** | 4 / 4 | `description` 末尾的 `Do not use for …` 生效，未读本 skill；纯 React 修复，并用 react-test-renderer 做了对照实验（修复前 15s 超时复现无限渲染，修复后 6 次渲染 / 0 key 警告） |

结论：**通过**。三个场景的基线缺口全部被填补，且都是可验证的填补，不是措辞变化：

- 场景 2 的三条缺口全中——升级前的存储布局对比命令与 `slither-check-upgradeability` 都给了出来，并且明确写出这两样查不到空 `_authorizeUpgrade`（「Slither 对 F-1/F-2 一条都没报」），ERC-7201 为什么让 V1 变量从槽 0 起也写清了。
- 场景 3 的三条缺口全中——`[invariant] fail_on_revert` 被显式设为 `true`、逐 selector 表被核对并报出「16384 次调用 / 0 revert」、每条 revert 断言到具体原因、覆盖率以分支数 20/20 给出而不是叙述。
- 场景 1 的缺口是最重的一条：基线两次都在「写 exploit 脚本」这一步被服务端 `Refusal (cyber)` 掐断、零产出；有 skill 时同一道题跑完 555 秒、0 次拒答，产出 `REVIEW.md` + 11 个 PoC + 9 个修复验证用例（`forge test` 20 passed）。差别正是本 skill 强制的框架——防御性评审的产物是**带攻击者合约的 Foundry 回归测试**，不是攻击脚本；不广播任何交易。
- 场景 4 基线本就 8/8，有 skill 后仍 8/8，但产出形态变了：从「一份缺陷清单」变成「12 个对未修代码成立的 PoC + 明确的未覆盖声明」。这条不计入缺口填补。
- 负例在两侧都 `skill_read=false`，`description` 的否定边界有效，无需收紧。

## 备注

- **许可教训（本波次新增两条）**：`tenequm/skills` 仓库根是 MIT，但 `skills/foundry-solidity/LICENSE.txt` 是 Apache-2.0——又一个「目录许可覆盖仓库许可」的实例，两者都宽松但记录必须写清是哪一份在管。`max-taylor/Claude-Solidity-Skills` 的 `license: MIT` 只存在于 `.claude-plugin/plugin.json` 里，全树没有任何许可正文，按量表只给 1 分且不作 merged。`mrheyday/agentic-solidity-foundry-skill` 的 Apache-2.0 正文没有版权人行，且 vendored 树里混有 AGPL 材料——仓库级许可覆盖不了被 vendored 的第三方内容。
- **`ethereum/solidity` 已重定向为 `argotorg/solidity`**（`gh api repos/ethereum/solidity` 返回 `full_name: argotorg/solidity`）。路线图里的种子名仍可用，但 `SOURCES.yaml` 记的是新名字。下次同步注意分支是 `develop` 而非 `main`。
- **Solidity 版本腐化速度**：0.8.37 在本次调研前一天（2026-09-10）发布，foundry 1.8.1 默认还选 0.8.36。本 skill 的版本门写的是「读 `docs/bugs_by_version.json` 决定下限」而不是写死某个号，正是为了抗这种腐化；下次同步时该表要重新读一遍。
- **要盯的上游**：`OpenZeppelin/openzeppelin-contracts`（5.x 的 `Initializable`/`UUPSUpgradeable` alias 官方说下个大版本移除，届时导入路径规则要改）、`foundry-rs/book`（`[invariant]` 默认值一变，规则 23 就要改）、`argotorg/solidity` 的 `docs/bugs.json`、`trailofbits/skills`（两天一推，`building-secure-contracts` 若补上 Solidity 扫描器要重新审）。
- **放弃的方向**：Echidna / Medusa 的实操细节（本机未装两个 fuzzer，相关内容一律 `[official]` 且只占一小节，避免写成没实测的操作手册）；Vyper 与非 EVM 链（Solana/Cairo/Move/CosmWasm）按 `## Scope` 明确交回「本库暂无对应 skill」；MEV 与链上套利按定性完全排除。
- **与 `security-review` 的边界需要主代理补一刀**：`skills/security-review/SKILL.md:43` 目前写着「Smart-contract auditing has no skill in this library yet; say so rather than improvising one.」，本 skill 落地后这句已过期，应改为把合约特有漏洞类与 Foundry/Slither 工具链转交 `solidity-web3`。本任务不允许改其他 skill，故在此登记。
- **评测夹具的密钥约定**：五个夹具里没有任何私钥字面量；正文与 reference 提到假密钥时统一用 `0xREDACTED` 形式，`references/foundry-testing.md` 明确要求用 keystore `--account` 而非 `PRIVATE_KEY` 环境变量。
