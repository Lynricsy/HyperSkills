# terraform 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`terraform agent skill SKILL.md github claude`
  - `gh api search/repositories?q=terraform+skill+claude+in:name,description&sort=stars`
    与 `q=opentofu+agent+skills`
  - `github/awesome-copilot`（`skills/*` 与 `instructions/*` 都搜过：命中
    `instructions/terraform.instructions.md`、`instructions/terraform-azure`、
    `skills/terraform-azurerm-set-diff-analyzer`、`skills/import-infrastructure-as-code`、
    `agents/terraform*.agent.md`）
  - 领域官方组织仓库：`hashicorp/`（agent-skills、terraform、web-unified-docs）、
    `opentofu/`（opentofu、opentofu.org）、`terraform-linters/`、`open-policy-agent/`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` = 已登录 `Lynricsy`，全程用登录态，未使用匿名 API）

### 版本基线（先核实再动笔）

```
$ gh api repos/hashicorp/terraform/releases --jq '.[] | "\(.tag_name) \(.published_at) prerelease=\(.prerelease)"'
v1.17.0-beta1  2026-09-09  prerelease=true
v1.16.2        2026-09-09  prerelease=false   ← 当前稳定版
v1.16.0        2026-08-26  prerelease=false

$ gh api repos/opentofu/opentofu/releases --jq '.[] | "\(.tag_name) \(.published_at) prerelease=\(.prerelease)"'
v1.13.0-beta1  2026-08-27  prerelease=true
v1.12.6        2026-08-19  prerelease=false   ← 当前稳定版
v1.11.14       2026-08-19  prerelease=false   ← 上一支持系列
```

正文写作基线：**Terraform 1.16 / OpenTofu 1.12**。所有版本门槛都从各分支的
`CHANGELOG.md`（`gh api repos/<o>/<r>/contents/CHANGELOG.md?ref=v1.N`）核过，不凭记忆：

| 特性 | Terraform | OpenTofu | 依据 |
|---|---|---|---|
| `moved` 块 | 1.1 | 1.6（继承） | TF v1.1 CHANGELOG |
| `import` 块、`check` 块 | 1.5 | 1.6（继承） | TF v1.5 CHANGELOG 第 51–54 行 |
| `terraform test`（`.tftest.hcl`） | 1.6 | 1.6 | TF v1.6 / tofu v1.6 |
| `removed` 块、provider-defined functions、`import` 里的 `for_each` | 1.7 | **1.7** | tofu v1.7.0 NEW FEATURES |
| mock providers（`mock_provider`/`mock_resource`/`mock_data`） | 1.7 | **1.8** | tofu v1.8.0 NEW FEATURES |
| `override_resource`/`override_data`/`override_module` | 1.7 | 1.8 | 同上 |
| run 块 `parallel` / `state_key` | 1.9 / 1.11 | — | TF v1.11 CHANGELOG（`state_key` 是 1.11 才加的，不是 1.9） |
| ephemeral 资源与 ephemeral 变量/输出 | **1.10** | 1.11 | TF v1.10.0、tofu v1.11.0 NEW FEATURES |
| write-only 属性（`*_wo`） | **1.11** | 1.11 | TF v1.11.0 NEW FEATURES |
| S3 后端原生锁 `use_lockfile` GA | **1.11** | **1.10** | TF v1.11.0「S3 native state locking is now generally available … deprecated the DynamoDB-related arguments」；tofu v1.10.0 |
| `import { identity = … }` | 1.12 | **1.12** | tofu v1.12 ENHANCEMENTS |
| `terraform stacks` CLI | 1.13 | 无 | TF v1.13.0 NEW FEATURES |
| list 资源 / `.tfquery.hcl` / `terraform query` / Actions 块 | **1.14** | 无 | TF v1.14.0 NEW FEATURES |
| 变量/局部值可用于 `module` 的 `source`/`version` | **1.15** | **1.8** | TF v1.15.0；tofu v1.8.0（OpenTofu 早 7 个 minor） |
| `deprecated` 标记变量/输出 | **1.15** | **1.10** | TF v1.15.0；tofu v1.10.0 |
| `convert()` 函数、`output` 显式类型约束 | 1.15 | 无 | TF v1.15.0 |
| 模块内 `import` 块、`terraform_data` 的 `store` 块、Actions `on_failure` | **1.16** | 无 | TF v1.16.0 NEW FEATURES |
| provider 配置块上的 `for_each`、`-exclude` 规划选项 | 无 | **1.9** | tofu v1.9.0 NEW FEATURES |
| 客户端 state 加密（AES-GCM + PBKDF2/AWS KMS/GCP KMS/OpenBao） | 无 | **1.7** | tofu v1.7.0 STATE ENCRYPTION |
| `.tofu` 扩展名覆盖 `.tf` | 无 | **1.8** | tofu v1.8.0 |
| OCI registry 作为模块源与 provider mirror | 无 | **1.10** | tofu v1.10.0 |
| `lifecycle { enabled = … }` 元参数 | 无 | **1.11** | tofu v1.11.0 |
| `lifecycle { destroy = false }`、`prevent_destroy` 引用变量 | 无 | **1.12** | tofu v1.12 ENHANCEMENTS |

### 许可实查（重要）

| 目标 | API 报的 license | 实读结果 | 处置 |
|---|---|---|---|
| `hashicorp/agent-skills` | MPL-2.0 | MPL-2.0（仓库根 LICENSE） | merged，**派生 reference 首行加 MPL 注释** |
| `antonbabenko/terraform-skill` | NOASSERTION | 实读 LICENSE：**Apache-2.0**（"Copyright 2026 Anton Babenko … Licensed under the Apache License, Version 2.0"），README badge 也是 Apache-2.0 | merged，`license: Apache-2.0` |
| `hashicorp/terraform`（CLI 与 CHANGELOG） | NOASSERTION | 实读 LICENSE：**BUSL-1.1**（"Licensed Work: Terraform Version 1.6.0 or later … (c) 2024 IBM Corp."） | **reference**：只读取事实与版本门槛，不复制任何文字 |
| `developer.hashicorp.com/terraform`（docs 源仓库 `hashicorp/web-unified-docs`） | NOASSERTION | 实读 LICENSE：**BUSL-1.1**（"Licensed Work: /web-unified-docs … (c) 2024 IBM Corp."） | **reference**：官方文档站不是开源许可，事实以本机实跑与 CHANGELOG 复核后自撰 |
| `opentofu/opentofu` | MPL-2.0 | MPL-2.0 | merged（仅 CHANGELOG 事实；无逐字复制，仍按 MPL 处理注明） |
| `opentofu/opentofu.org`（docs） | Apache-2.0 | Apache-2.0 | merged |
| `open-policy-agent/conftest` | NOASSERTION | 未取内容 | 仅作工具名核对，不入 SOURCES |

> 教训回写：波次 1–4 的经验是「官方文档若许可允许就该 merged」。本 skill 是**反例**——
> HashiCorp 自 Terraform 1.6 起把 CLI 与整个 `developer.hashicorp.com` 文档仓库
> 都改成了 BUSL-1.1（源码可见、非开源）。因此本 skill 的 `kind: docs` 官方上游
> **只能是 `reference`**，事实必须自己在本机跑出来或从 MPL-2.0 的 OpenTofu 侧取证。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `hashicorp/agent-skills` `plugins/terraform/skills/*`（15 个 skill） | https://github.com/hashicorp/agent-skills | 864 | 2026-09-04 | MPL-2.0 | 风格、测试、重构、导入、policy、stacks、provider 开发 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 唯一的官方厂商 skill 仓库；`terraform-test`/`refactor-module`/`terraform-search-import`/`terraform-policy`/`provider-*` 覆盖了本 skill 的骨架。抽查三条：`.tftest.hcl` 的 `run`/`assert`/`expect_failures` 语法、`moved` 块把资源移进模块、identity 形式的 `import` 块——本机 1.16.2 全部复现。MPL-2.0 → 派生 reference 首行加注释 |
| 2 | `antonbabenko/terraform-skill` `skills/terraform-skill/*` | https://github.com/antonbabenko/terraform-skill | 2336 | 2026-07-03 | Apache-2.0（API 报 NOASSERTION，实读 LICENSE） | 失败模式路由 + state/模块/测试/CI/安全六个深度 reference | 2 | 2 | 3 | 2 | 2 | 11 | INCLUDE | `terraform-best-practices.com` 作者，公认专家。`state-management.md` 1834 行、`code-patterns.md` 1064 行是全场最深。扣分点：feature-guard 表里 `use_lockfile` 标 1.10+（Terraform 实为 1.11 GA），`state_key` 标 1.9（实为 1.11）——已裁决 |
| 3 | `github/awesome-copilot` `instructions/terraform.instructions.md` | https://github.com/github/awesome-copilot | 38872 | 2026-09-10 | MIT | HCL 约定、模块化、安全、文档、测试的条目清单 | 2 | 3 | 1 | 1 | 2 | 9 | INCLUDE（仅作覆盖面枚举） | GitHub 官方仓，但这份是 113 行的泛化条目，多数是模型已知常识。取值在**覆盖面枚举**与一条冲突证据（它主张 `depends_on` 放块首，与官方风格指南相反 → 见裁决 2） |
| 4 | `LukasNiessen/terrashark` | https://github.com/LukasNiessen/terrashark | 318 | 2026-08-16 | MIT | 与 #2 同构的失败模式工作流 + good/bad/neutral 示例 | 1 | 3 | 2 | 2 | 2 | 10 | MAYBE → reference | SKILL.md 仅 86 行的路由器，深度全在 references。与 #2 高度同构（同一套「identity churn / secret exposure / blast radius / CI drift / compliance gates」五分类）；`created_at` 2026-02-23 晚于 #2 的 2026-01-15，判为后来者。只取「正/负/中性三类示例」这一形式，不取内容 |
| 5 | `nitinjain999/platform-skills` `.cursor/rules/terraform.mdc`、`commands/terraform.md`、`examples/demo/terraform-iam-risk/*` | https://github.com/nitinjain999/platform-skills | 41 | 2026-09-10 | Apache-2.0 | 平台工程视角的 Terraform 节 + IAM 风险示例 | 1 | 3 | 2 | 2 | 2 | 10 | MAYBE → reference | 内容是 Cursor rule 格式（`.mdc`），不是 SKILL.md；Terraform 部分主要是 drift 检测工作流与 checkov 门。只作安全扫描一节的第三方交叉校验，未合入 |
| 6 | `developer.hashicorp.com/terraform`（`hashicorp/web-unified-docs`） | https://developer.hashicorp.com/terraform | 84（源仓库） | 2026-09-10 | **BUSL-1.1**（实读） | 语言、CLI、后端、测试的最终事实源 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE → **reference** | 权威性满分但许可分 0：BUSL-1.1 不是开源许可，按规则表「专有/非 SPDX 开源授权 → reference」。用于核对事实，正文一字未抄 |
| 7 | `hashicorp/terraform` `CHANGELOG.md`（各 `v1.N` 分支） | https://github.com/hashicorp/terraform | 49633 | 2026-09-10 | **BUSL-1.1**（实读） | 每个特性的确切引入版本 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE → **reference** | 版本门槛的唯一可靠来源。上表 20 余条版本事实全部取自这里，只提取事实不复制文本 |
| 8 | `opentofu/opentofu` `CHANGELOG.md`（各 `v1.N` 分支） | https://github.com/opentofu/opentofu | 30152 | 2026-09-10 | MPL-2.0 | OpenTofu 独有特性与两边差异 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | state 加密、provider `for_each`、`-exclude`、`enabled` 元参数、OCI 源等「只在一边」的特性全部在此取证 |
| 9 | `opentofu/opentofu.org`（docs） | https://opentofu.org/docs/ | 47 | 2026-09-07 | Apache-2.0 | OpenTofu 语言与 CLI 文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 与 #6 同等权威但许可可合入，凡两边共有的语言语义优先在此取证 |
| 10 | `github/awesome-copilot` `skills/import-infrastructure-as-code` | https://github.com/github/awesome-copilot | 38872 | 2026-09-10 | MIT | 把现有云资源导入 IaC 的流程 | 2 | 3 | 2 | 2 | 2 | 11 | MAYBE → 未使用 | 与 #1 的 `terraform-search-import` 完全重叠且更浅（无 `.tfquery.hcl`、无 identity 导入）。留行避免下批重复评估 |
| 11 | `github/awesome-copilot` `skills/terraform-azurerm-set-diff-analyzer` | https://github.com/github/awesome-copilot | 38872 | 2026-09-10 | MIT | azurerm set 类型属性的 diff 噪声分析 | 2 | 3 | 3 | 2 | 2 | 12 | REJECT（越界） | 内容完全是 azurerm provider 的资源字段，落在本 skill 明确不覆盖的「各云资源字段」里 |
| 12 | `wshobson/agents` `plugins/cloud-infrastructure/agents/terraform-specialist.md` | https://github.com/wshobson/agents | 39558 | 2026-09-07 | MIT | Terraform 专家 agent 提示词 | 1 | 3 | 1 | 2 | 2 | 9 | MAYBE → reference | 是 agent persona（`.md` 提示词）而非 skill；无可执行规则、无版本门槛。只用来交叉核对覆盖面是否有遗漏（结论：无新增） |
| 13 | `terramate-io/agent-skills` | https://github.com/terramate-io/agent-skills | 34 | 2026-02-02 | MIT | Terramate 编排工具的用法 | 1 | 0 | 2 | 2 | 2 | 7 | REJECT | 距今 >6 个月未推送（新鲜度 0）；且内容是 Terramate 产品包装，不是 Terraform 语言本身 |
| 14 | `lgbarn/devops-skills` | https://github.com/lgbarn/devops-skills | 14 | 2026-01-23 | MIT | 泛 DevOps skill 合集 | 0 | 0 | 1 | 1 | 2 | 4 | REJECT | >6 个月未推送 + 内容泛化 |
| 15 | `anmolnagpal/devops-skills` | https://github.com/anmolnagpal/devops-skills | 8 | 2026-09-09 | MIT | 泛 DevOps skill 合集 | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | 新鲜但匿名个人仓、8 星，Terraform 部分是通用条目，无本 skill 尚缺的规则 |
| 16 | `hashi-demo-lab/claude-skill-hcp-terraform` | https://github.com/hashi-demo-lab/claude-skill-hcp-terraform | 4 | 2025-12-29 | MIT | HCP Terraform 工作区操作 | 1 | 0 | 2 | 2 | 2 | 7 | REJECT | >6 个月未推送；内容是 HCP 托管平台控制面，超出本 skill 范围 |
| 17 | `zscaler/zscaler-terraform-skills` | https://github.com/zscaler/zscaler-terraform-skills | 2 | 2026-09-07 | MIT | Zscaler provider 专用 | 1 | 3 | 2 | 1 | 2 | 9 | REJECT（越界） | 单一 provider 的资源字段说明书，属「具体资源字段」，本 skill 不覆盖 |
| 18 | `maroffo/claude-forge` | https://github.com/maroffo/claude-forge | 16 | 2026-07-29 | MIT | 通用 skill 工厂，含 terraform 模板 | 0 | 2 | 1 | 1 | 2 | 6 | REJECT | Terraform 只是它的一个模板样例，无实质规则 |
| 19 | `terraform-linters/tflint` | https://github.com/terraform-linters/tflint | 5806 | 2026-09-09 | MPL-2.0 | 静态检查规则集 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE（仅工具事实） | 不是 skill；用于确认 `tflint` 的规则分类与 `terraform validate` 的能力边界（validate 不查 provider 侧字段合法性）。未复制内容，列为 reference |
| 20 | `bridgecrewio/checkov` / `aquasecurity/trivy` | https://github.com/bridgecrewio/checkov | 8996 / 37859 | 2026-09-10 | Apache-2.0 | IaC 安全扫描 | 2 | 3 | 3 | 3 | 2 | 13 | 未入 SOURCES | 只用来核对「哪些扫描器仍在活跃维护」这一条事实（tfsec 已并入 trivy）。工具名在正文出现，但无内容派生，不构成上游 |

## 本机实跑验证（Phase A 要求）

两个运行时都装到了本机（`/usr/local/bin/{terraform,tofu}`）并在 `/tmp` 干净目录下真跑，
**正文的每个验证门都来自这里**。

> 复跑说明：本条目下的六个实验先后跑过两轮。第一轮的工作目录随系统清理 `/tmp` 一并消失，
> 因此在 Phase D 重跑评测时把六个实验**逐个原样重建并重跑了一遍**，输出与第一轮完全一致
> （`count` 删中间元素仍是 `1 to add / 2 to destroy`，`for_each` 仍是 `1 to destroy`，
> mock + `command = apply` 仍然 pass 且不落盘，`-no-cleanup` 仍然报 `flag provided but not defined`）。
> 下面引用的都是重跑后的输出。

```
$ terraform version
Terraform v1.16.2
on linux_amd64

$ tofu version
OpenTofu v1.12.6
on linux_amd64
```

### 实验 1 — `/tmp/tf-verify`：不需要云凭据的模块 + `terraform test`

模块用 `hashicorp/local` provider 与 `terraform_data`，含 `for_each`、`count`、
`validation`、typed outputs；测试文件 `tests/defaults.tftest.hcl` 三个 `run` 块
（两个断言 + 一个 `expect_failures`）。

```
$ terraform fmt -check -recursive
(exit 0)

$ terraform validate -no-color
Success! The configuration is valid.
(exit 0)

$ terraform test -no-color
tests/defaults.tftest.hcl... in progress
  run "renders_one_file_per_name"... pass
  run "summary_is_optional"... pass
  run "rejects_empty_set"... pass
tests/defaults.tftest.hcl... tearing down
tests/defaults.tftest.hcl... pass

Success! 3 passed, 0 failed.
(exit 0)
```

同一份文件在 OpenTofu 下不改一个字符也通过：

```
$ tofu init -input=false >/dev/null && tofu test -no-color
tests/defaults.tftest.hcl... pass
  run "renders_one_file_per_name"... pass
  run "summary_is_optional"... pass
  run "rejects_empty_set"... pass

Success! 3 passed, 0 failed.
(exit 0)
```

结论：`command = plan` 就能断言 `for_each`/`count` 的实例数、局部值推导出的属性，
以及用 `expect_failures = [var.x]` 断言变量 `validation` 会拒绝坏输入——**不需要任何云凭据**。
本 skill 的「给模块写测试」验证门就用这三种断言。

### 实验 2 — `/tmp/tf-moved`：`count` 的身份不稳定性（数字，不是传说）

`local_file.item` 用 `count = length(var.names)`，`names = ["a","b","c"]` 先 apply，
然后把中间元素删成 `["a","c"]`：

```
$ terraform plan
  # local_file.item[1] will be updated in-place      (内容 b → c)
  # local_file.item[2] will be destroyed  (because index [2] is out of range for count)
Plan: 1 to add, 0 to change, 2 to destroy.
```

### 实验 3 — `/tmp/tf-foreach`：同一改动换成 `for_each`

```
$ terraform plan
  # local_file.item["b"] will be destroyed
Plan: 0 to add, 0 to change, 1 to destroy.
```

再把资源标签从 `item` 改名为 `artifact` 并加 `moved { from = local_file.item, to = local_file.artifact }`：

```
$ terraform plan
  # local_file.item["a"] has moved to local_file.artifact["a"]
  # local_file.item["c"] has moved to local_file.artifact["c"]
Plan: 0 to add, 0 to change, 1 to destroy.
```

（那 1 个 destroy 是实验 2 里已删掉的 `"b"`，与改名无关；改名本身产生 0 个
add/change/destroy。）

结论：`count` 删中间元素 = **2 destroy + 1 add**；`for_each` 同一改动 = **1 destroy**；
`moved` 让重命名代价归零。这三个数字直接进 SKILL.md 的 Core rules。

### 实验 4 — `/tmp/tf-mock`：mock provider 在 `command = apply` 下能不能用

上游（hashicorp `MOCK_PROVIDERS.md`）说「Plan mode only」。实测反证：

```hcl
mock_provider "local" {
  mock_resource "local_file" { defaults = { id = "mocked-id-123" } }
}

run "apply_with_mock" {
  command = apply
  assert {
    condition     = output.id == "mocked-id-123"
    error_message = "mock default should be used in apply mode"
  }
}
```

```
$ terraform test -no-color        # Terraform 1.16.2
  run "apply_with_mock"... pass
Success! 1 passed, 0 failed.

$ tofu test -no-color             # OpenTofu 1.12.6
  run "apply_with_mock"... pass
Success! 1 passed, 0 failed.

$ ls out
ls: cannot access 'out': No such file or directory      # 真的没有创建文件
```

→ 裁决 9。正文写「两种模式都支持」，并说明 apply + mock 正是断言
`(known after apply)` 值的唯一无凭据途径。

### 实验 5 — `terraform test` 的 CLI 旗标实查

```
$ terraform test -help | grep -A2 filter
  -filter=testfile      If specified, Terraform will only execute the test files
                        specified by this flag. You can use this option multiple
                        times to execute more than one test file.

$ terraform test -no-cleanup
Error: Failed to parse command-line flags
flag provided but not defined: -no-cleanup

$ tofu test -help | grep -E 'filter|json-into|junit'
  -filter=testfile      If specified, OpenTofu will only execute the test files
  -json-into=out.json   Produce the same output as -json, but sent directly
```

→ 裁决 10（`-filter` 过滤的是文件不是 run 块名）与裁决 11（`-no-cleanup` 不存在）。
另记：`-junit-xml` 与 `-parallelism` 是 Terraform 独有，OpenTofu 提供 `-json-into` 代替。

### 实验 6 — `/tmp/tf-gate`：SKILL.md 里那条验证门在评测夹具上真跑一遍

把 `skills/terraform/evals/files/artifact_bundle.tf` 原样拷进干净目录，加一个
**指向不存在的 S3 桶**的 `backend` 块（证明 `-backend=false` 确实不碰后端），
按 SKILL.md「write-tests-for-a-module」那条门的四个命令依次跑：

```
$ terraform fmt -check -recursive                 → exit 0
$ terraform init -backend=false -input=false      → exit 0（无 AWS 凭据、桶不存在也不报错）
$ terraform validate -no-color                    → Success! The configuration is valid.  exit 0
$ terraform test -no-color
  run "keys_are_lowercased_and_payloads_trimmed"... pass   # command = plan
  run "manifest_is_optional"... pass                       # command = plan，length(...) == 0
  run "checksum_needs_apply"... pass                       # command = apply，断言 sha256 输出
Success! 3 passed, 0 failed.                      → exit 0
```

结论：SKILL.md 与 `references/testing.md` 写进正文的验证门是被验证过的，不是拟稿。
同时确认了 `terraform_data.checksum.output` 在 plan 阶段是 unknown、必须 `command = apply`
才能断言——这就是「plan 断言 apply 时值 = 永远不会通过的测试」那条规则的实证。

## 深度审查

### 1. `hashicorp/agent-skills` `plugins/terraform`（MPL-2.0，864★）

15 个独立 skill 组成的 plugin，是唯一的官方厂商上游。结构：每个 skill 一个目录，
`SKILL.md` + 可选 `references/`。frontmatter 带 `metadata.lifecycle-status`、
`metadata.copyright: Copyright IBM Corp. 2026`、`metadata.version`、`metadata.compatibility`
——都是本仓库禁止的 agent 专属 / 非规范字段，合入时全部剥离。

- `terraform-style-guide`（316 行）：文件组织表（`terraform.tf`/`providers.tf`/`main.tf`/
  `variables.tf`/`outputs.tf`/`locals.tf`）、块内顺序（元参数 → 参数 → 块 → `lifecycle`）、
  命名规范、`for_each` 优先于 `count`、版本约束运算符、`.gitignore` 清单。质量高、可执行。
- `terraform-test`（451 行 + 3 个 reference）：`run`/`assert`/`expect_failures`/`plan_options`/
  `module`/`state_key`/`parallel` 的完整语法；`MOCK_PROVIDERS.md` 讲 1.7+ 的 mock。
  本机复现无误。**唯一问题**：把 `parallel` 标为 v1.9.0、`state_key` 标为 v1.9.0，
  但 CHANGELOG 显示 `state_key` 是 1.11 才加的（见裁决 3）。
- `refactor-module`（560 行）：单体配置 → 模块的完整流程，含 `moved` 块与
  `terraform state mv` 的对照、`terraform state list` / `show -json` 取地址的取证顺序，
  以及「state 在任何格式下都是明文，不要 echo 到日志」这条硬规则。
  它用 `## Input Parameters` 表把 skill 写成了函数签名（`source_directory`、`preserve_state`…），
  这是 agent 绑定式写法，本仓库不采用——只取其分析→设计→变换→迁移→文档→测试六步骨架。
- `terraform-search-import`（395 行 + `MANUAL-IMPORT.md` + `scripts/list_resources.sh`）：
  1.14+ 的 `list` 块 / `.tfquery.hcl` / `terraform query -generate-config-out` /
  identity 形式 `import` 块。这是最新、最不为模型所知的一块，价值最高。
- `terraform-policy`（52 行 SKILL + `tfpolicy-author.md` 1781 行 + 大量 Sentinel→HCL 转换示例）：
  内容深，但 `examples/conversion/*` 全是 AWS 资源的具体策略（cloudfront/waf/dms/efs…），
  落在本 skill 明确不覆盖的云资源字段里。只取「policy 语言选型与放在流水线哪一段」的判断。
- `terraform-stacks`（481 行 + 6 个 reference）：Stacks 是 HCP Terraform 侧特性，
  `component`/`deployment` 块。本 skill 只写一句「Terraform-only，需要 HCP/TFE 才能部署」，不展开。
- `provider-resources` / `provider-test-patterns` / `provider-configuration` /
  `new-terraform-provider` / `provider-framework-migration` / `provider-ephemeral-resources` /
  `provider-actions` / `provider-docs`：Go 侧的 provider 开发，`plugin-framework` 的
  schema 设计、retries/waiters、acceptance test 的 `TF_ACC`、SDKv2→Framework 迁移映射。
  边界要求「provider 开发入门」，取其入门层（何时该写 provider、框架选型、
  acceptance test 的前提与代价），不取逐个 API 的说明。
- `azure-verified-modules`：越界（Azure 专属），不取。

### 2. `antonbabenko/terraform-skill`（Apache-2.0，2336★）

单 skill + 8 个 reference，深度冠军。SKILL.md 是「Response Contract → Workflow →
诊断路由表」的三段式，路由表按**失败模式**（identity churn / secret exposure /
blast radius / destroy cascade / CI drift / compliance gaps / testing blind spots /
state corruption / provider upgrade risk / provider lifecycle / bootstrap misuse /
navigation / cross-cloud）分派 reference。这个「按失败模式而非按 API 分章」的思路
正是本仓库标准第 3 节要的 "teach the failure, not the API"，予以采纳为 Workflows 的组织方式。

高价值且别处没有的点：
- 「`sensitive = true` 只遮显示，值仍在 state 里」——直指最常见的误解。
- targeted destroy 的级联：`locals` 引用了被 `-target` 的资源时，所有 `for_each`
  消费者都成为隐式依赖，一起被删。
- 模块层级三分（resource module → infrastructure module → composition）与
  「拆 state 的判据：不同团队 / 不同变更节奏 / >500 资源；合并的判据：紧耦合 / <100 资源」。
- `try()` 在 local 里优先取条件资源属性以强制正确的删除顺序。
- 测试选型矩阵（native test vs Terratest vs mock）与「set 类型嵌套块不能用 `[0]` 索引，
  要么 `for` 表达式要么 `command = apply`」。

扣分处：`code-intelligence-lsp.md` 整节是 terraform-ls + 另一个插件的绑定（agent 绑定，
剥离）；feature-guard 表两处版本错（见裁决 3）；`Response Contract` 要求每次回答都输出
五段固定结构，过重，本仓库改为只在 review 型 workflow 的 Output format 里约束。

### 3. `LukasNiessen/terrashark`（MIT，318★）

SKILL.md 只有 86 行，是纯路由器：捕获执行上下文 → 诊断失败模式 → 按信号条件加载
reference → 提出带风险控制的修复 → 生成工件 → 验证 → 输出契约。五类失败模式的
命名与 #2 逐字同构（identity churn / secret exposure / blast radius / CI drift /
compliance gate gaps），而仓库 `created_at` 晚一个多月。README 自述
"primarily based on HashiCorp official recommended practices"。
可取的只有一处形式：`examples-good.md` / `examples-bad.md` / `examples-neutral.md`
三分类示例（"neutral" 指两种写法都可接受、不要在评审里当缺陷提）。
本 skill 把这条吸收为 Output format 的一句约束，未取其正文。判 `reference`。

### 4. `github/awesome-copilot` `instructions/terraform.instructions.md`（MIT，38872★）

113 行、`applyTo: '**/*.tf'` 的 Copilot instruction 文件。绝大部分是模型已知常识
（"用版本控制"、"用变量而不是硬编码"）。真正有信息量的三条：
(a) 「不要为单个资源建模块；模块层级要浅」——与 #2 的模块层级论一致，作为覆盖面确认；
(b) 「避免为同一配置内创建的资源使用 data source，用 output」——一条真实的性能/循环陷阱；
(c) 与官方风格指南冲突的 `depends_on` 位置主张（见裁决 2）。

### 5. `nitinjain999/platform-skills`（Apache-2.0，41★）

不是 SKILL.md 体系，主体是 `.cursor/rules/*.mdc` + `commands/` + `examples/`。
Terraform 相关的是一个 drift 检测 workflow（GitHub Actions 定时 `plan -detailed-exitcode`）
与 `examples/demo/terraform-iam-risk/{bad,fixed}.tf` 的 IAM 通配符对照。
`commands/terraform.md` 是斜杠命令定义（agent 绑定）。只作安全一节的第三方交叉校验。

### 6. `wshobson/agents` `terraform-specialist.md`（MIT，39558★）

agent persona 提示词，不含版本门槛与可执行验证门。通读后确认本 skill 的覆盖面
没有遗漏项（它提到的 state 迁移、模块版本固定、drift、policy 都已覆盖）。判 `reference`。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 资源标签该用 `main`/`this` 还是描述性名字 | hashicorp `terraform-style-guide`：「只有一个实例且描述性名字冗余时默认用 `main`」；antonbabenko：「用描述性名字 `aws_instance.web_server`，`this` 只留给真正的单例」 | **两条不冲突，合并成一条规则**：名字描述资源的**角色**且不重复资源类型；模块内只有一个该类型资源、角色无可描述时才用 `main`（HashiCorp 风格指南的原意），`this` 不作为本仓库推荐拼写 | 官方厂商 > 公认专家；但 antonbabenko 反对的其实是「一切都叫 main」，两者的交集是「名字必须承载角色信息」 |
| 2 | `depends_on` 在资源块里的位置 | awesome-copilot instruction：「`depends_on` 放在资源定义的**最前面**，`for_each`/`count` 放在它后面」；hashicorp 风格指南：元参数（`count`/`for_each`）在最前，`lifecycle` 在最后，`depends_on` 与 `lifecycle` 同属尾部元参数；antonbabenko：`count`/`for_each` → 参数 → `tags` → `depends_on` → `lifecycle` | **采用 HashiCorp 顺序**：`count`/`for_each` 最前，然后参数，然后嵌套块，最后 `depends_on` 与 `lifecycle` | 官方厂商 > 社区。awesome-copilot 是 GitHub 官方仓但内容非 Terraform 官方；且它自己也说「Follow the Terraform Style Guide」，自相矛盾 |
| 3 | 版本门槛写错 | antonbabenko feature-guard 表：`use_lockfile` = 1.10+、`state_key` = 1.9；hashicorp `terraform-test`：`parallel` 与 `state_key` 都是 v1.9.0 | **以 CHANGELOG 为准**：Terraform 的 `use_lockfile` 在 **1.11.0 GA**（1.10 为实验），`run` 块 `state_key` 在 **1.11.0**，`parallel` 在 **1.9.0**；OpenTofu 的 S3 原生锁在 **1.10.0** | 一手 CHANGELOG > 任何 skill。TF v1.11.0：「S3 native state locking is now generally available…」「Add new `state_key` attribute for `run` blocks」 |
| 4 | mock provider 的可用版本 | 所有社区上游都写「mock providers 1.7+」，不区分运行时 | **拆成两行**：Terraform **1.7+**，OpenTofu **1.8+** | tofu v1.8.0 NEW FEATURES 才加入 `mock_provider`/`mock_resource`/`mock_data`；OpenTofu 1.6/1.7 没有 |
| 5 | 「OpenTofu 是 Terraform 的 drop-in 替代」 | antonbabenko / terrashark 都写「both supported」，只在 quick-reference 里提差异 | **单开一节讲差异**，并明确两个方向的独有特性：OpenTofu 独有 state 加密、provider `for_each`、`-exclude`、`enabled` 元参数、OCI 模块源、`.tofu` 覆盖；Terraform 独有 Stacks、list 资源/`terraform query`、Actions、模块内 `import`、`terraform_data` 的 `store` | 两边 CHANGELOG 实查。「drop-in」在 1.6 时代成立，到 1.12/1.16 已不成立，写成 drop-in 会让模型给出在另一边跑不了的配置 |
| 6 | 官方文档能否 merged | 前四波的经验是「官方文档许可允许就 merged」 | **本 skill 例外：`developer.hashicorp.com/terraform` 与 `hashicorp/terraform` 都是 BUSL-1.1 → `reference`** | 实读两个 LICENSE 文件，均为 Business Source License 1.1（Licensor: IBM）。非开源许可，按规则表走 reference |
| 7 | 是否推荐 Terragrunt / Terramate 这类编排器 | terramate-io 上游主推自家编排器；antonbabenko 只字未提 | **不推荐任何第三方编排器**，只写原生的 state 拆分 + 目录分层 + `-var-file`；第三方编排器作为一句逃生口提及而不展开 | 标准第 3 节「只给一个默认方案 + 一个逃生口，不罗列多个可选库」 |
| 8 | `-target` 的地位 | hashicorp 的 `terraform-test` 在 `plan_options` 里演示 `target`；antonbabenko 把 targeted destroy 列为独立失败模式 | 正文写：`-target` 是**恢复手段不是工作流**；它会跳过依赖图的一部分，产生不完整的 plan；OpenTofu 的 `-exclude`（1.9+）是它的对偶而非替代 | 官方文档对 `-target` 的定位一贯是 "exceptional circumstances"；antonbabenko 的级联证据支持这一判断 |
| 9 | mock provider 能否用在 `command = apply` | hashicorp `terraform-test/references/MOCK_PROVIDERS.md` 明写「**Plan mode only** — mocks don't work with `command = apply`」；antonbabenko 未表态 | **上游错了，正文写「两种模式都支持」**。`/tmp/tf-mock` 实测：`mock_provider "local"` + `mock_resource` 的 `defaults`，`run { command = apply }` 断言 `output.id == "mocked-id-123"`，Terraform 1.16.2 与 OpenTofu 1.12.6 **都 pass，且磁盘上没有生成任何文件**（`ls out` → No such file or directory） | 本机实跑 > 官方 skill 的文字。这条很要紧：apply 模式加 mock 才能断言 `(known after apply)` 的值，照抄上游会让模型放弃这条路径 |
| 10 | `terraform test -filter` 过滤的是什么 | hashicorp `terraform-test`：`terraform test -filter=test_vpc_configuration   # by run block name`；antonbabenko：`-filter=<path>` 按文件 | **按文件**。`terraform test -help`（1.16.2）原文：`-filter=testfile   If specified, Terraform will only execute the test files specified by this flag.` OpenTofu 1.12.6 的 help 同义。正文写「要单独跑一个场景就把它放进自己的文件」 | 本机 `-help` > 上游文字 |
| 11 | `terraform test -no-cleanup` 是否存在 | hashicorp `terraform-test` 在「Running Tests」与「Best Practices」两处都写 `terraform test -no-cleanup` | **不存在**。`cd /tmp/tf-verify && terraform test -no-cleanup` → `Error: Failed to parse command-line flags / flag provided but not defined: -no-cleanup`；OpenTofu 1.12.6 同样没有。留住测试资源在 Terraform 1.18 的 unreleased CHANGELOG 里还是 experiment（`skip_cleanup` 属性 + `terraform test cleanup` 子命令）。正文改为用 `-verbose` 调试 | 本机实跑 + 1.18 CHANGELOG 的 EXPERIMENTS 节 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `hashicorp-agent-skills` | hashicorp/agent-skills `plugins/terraform/skills/*` | merged（MPL-2.0，派生 reference 首行加注释） | 风格与文件组织、`terraform test` 语法全集、单体→模块重构六步、`moved`/`state mv` 对照、1.14+ 的 list 资源与 `terraform query`、identity `import`、policy 的选型层、provider 开发入门 |
| `antonbabenko-terraform` | antonbabenko/terraform-skill | merged（Apache-2.0） | 按失败模式组织 workflow 的思路、state 组织与拆分判据、模块层级三分、`sensitive` 只遮显示、targeted destroy 级联、测试选型矩阵与 set 类型断言陷阱、CI 里 plan artifact 的复用 |
| `opentofu` | opentofu/opentofu（CHANGELOG） | merged（MPL-2.0） | OpenTofu 独有特性清单与其确切版本门槛 |
| `opentofu-docs` | opentofu.org/docs | merged（Apache-2.0） | 两边共有语言语义的可合入取证源；state 加密与 `enabled` 元参数的语义 |
| `awesome-copilot-terraform` | github/awesome-copilot `instructions/terraform.instructions.md` | merged（MIT） | 覆盖面枚举：模块粒度下限、同配置内不要用 data source 回读自己创建的资源、`terraform-docs` 生成文档 |
| `terraform-docs-site` | developer.hashicorp.com/terraform | **reference**（BUSL-1.1） | 事实核对，未复制任何文本 |
| `hashicorp-terraform` | hashicorp/terraform（CHANGELOG） | **reference**（BUSL-1.1） | 每条版本门槛的核对 |
| `terrashark` | LukasNiessen/terrashark | reference（MIT） | 只读取「good/bad/neutral 三类示例，neutral 不当缺陷报」的评审形式 |
| `nitinjain-platform-skills` | nitinjain999/platform-skills | reference（Apache-2.0） | 安全扫描与 drift 检测一节的第三方交叉校验 |
| `wshobson-terraform-specialist` | wshobson/agents | reference（MIT） | 覆盖面查漏，结论无新增 |
| `tflint` | terraform-linters/tflint | reference（MPL-2.0） | 确认 `validate` 与 `tflint` 的能力边界划分 |

## 基线缺口

`uv run tools/run_evals.py terraform --baseline`（`anthropic/claude-opus-5`，thinking=medium，
四个场景全部 `status: ok`、`skill_read: false`）。

> 这一节跑过两轮。第一轮的 `/tmp/hs-evals` 随系统清理消失，Phase D 时**原样重跑了一遍**；
> 下表**只写重跑那一轮的证据**（可复现的那一轮），并在有差异处注明第一轮的结论。
> 两轮的三条主要缺口完全一致。

基线本身很强——四个答案都实跑了命令、都给了可执行工件、都主动列了「不能证明什么」——
所以缺口不在「答不出」，而在**几个具体的裁决点上答反了或漏了**。

| 场景 | 未达成的行为 | 说明（重跑轮的原话） |
|---|---|---|
| 1 重构成模块 | ① 把索引式 `count` 换成 `for_each` | **答反了**：「**2. 保留 `count`，没换 `for_each`。** `for_each` 会把地址从 `[0]` 变成 `["eu-west-1a"]`。虽然也能 moved，但会让变更从"机械 1:1 搬移"变成"逐条核对映射"。索引原样保留，diff 面积最小。」——把身份稳定性让位给了一次性 diff 面积。第一轮更极端：直接跑了个负面对照得出「换 `for_each` = 9 add / 9 destroy」，却没意识到那正是缺 `[i]→["key"]` 的 `moved` |
| 1 重构成模块 | ② 为 `count` 索引到 `for_each` 键各写一条 `moved` | 因①未做而缺失。交付的 `moved.tf` 只有 root→module 的整体地址平移；索引到键的映射被降级成「可选后续」的一行 |
| 1 重构成模块 | ③ 模块接口设计（CIDR 的 `validation`） | 变量都有 `type` 与 `description`、输出都有 `description`（这两半达成），但**一个 `validation` 块都没有**。第一轮反而写了 `cidrnetmask` 与 env 命名两个 validation——不稳定 |
| 1 重构成模块 | ⑤ 版本约束不能让 provider 大版本静默到来 | 写了 `required_version = ">= 1.1"` 与 `version = ">= 4.0"`——`>= 4.0` 恰恰是允许大版本静默跳变的写法；并且**主动删掉了自己生成的 `.terraform.lock.hcl`**（「这个决定应该由你们做」）。第一轮同样删了 lock 文件，且连约束都只列进后续项 |
| 1 重构成模块 | ⑥ 拆分 state | 提到了 blast radius（这半条达成），但决定「保持单 root、单 state，不拆」，拆分列为「可选后续……那是真正的大工程」 |
| 1 重构成模块 | ⑧ 把 `.*.id` splat 现代化 | 模块 `outputs.tf` 仍是 `value = aws_subnet.public[*].id` |
| 2 state 事故 | ④ 明确反对用 `-target` 做局部 apply | 两轮都全文未出现 `-target`，既没用也没警告 |
| 2 state 事故 | ⑥ `use_lockfile` 的版本门槛 | **两轮都答错同一个版本**：重跑轮写 `use_lockfile = true   # TF 1.10+ 原生 S3 条件写锁`；第一轮写 `required_version = ">= 1.10"   # use_lockfile 需要 1.10+`。Terraform 的 `use_lockfile` 是 **1.11.0 GA**（TF v1.11.0 CHANGELOG：「S3 native state locking is now generally available」），1.10 是 **OpenTofu** 的版本号。这正是「一个数字不能同时代表两个运行时」的实例 |
| 2 state 事故 | ③ 用 `plan -generate-config-out` 起草导入配置 | 用了 `import` 块（这半条达成），但让用户「规则按控制台现状逐条补全」，两轮都没提生成器 |
| 2 state 事故 | ⑧ state 明文与后端加密 | 提了 bucket versioning 与离线备份，**没提加密**；且没说 state 里每个属性都是明文 |
| 3 写测试 | ⑤ 分别标注两个运行时的 mock 版本门槛 | 两轮都未提及。它们把 CI 矩阵压到 TF 1.6.6 / Tofu 1.6.3，却没有触及「mock 是 Terraform 1.7、OpenTofu 1.8」这个不对称门槛——一个用了 mock 的模块在 OpenTofu 1.6/1.7 上会直接加载失败，而它给出的下界会让人以为 1.6 够用 |
| 4 负例（Dockerfile） | — | 基线正确地当成容器题回答（多阶段、slim、`npm ci --omit=dev`、`.dockerignore`、`.git` 进上下文），`grep -c -i terraform answer.md` = **0**。负例在基线侧没有缺口；它的作用是回归 `description` 的否定边界 |

归纳成三类，这也是 SKILL.md 要填的洞：

1. **身份稳定性的因果链断了。** 基线知道 `count` 会 churn、也知道 `moved` 存在，但没有把两者接起来：
   「换 `for_each` 会重建」的正确结论是「补 `[i]→["key"]` 的 `moved`」，不是「别换」。
2. **版本门槛按单一运行时记忆。** `use_lockfile` 记成 1.10（那是 OpenTofu），mock 的
   OpenTofu 1.8 门槛完全不知道。
3. **危险操作的否定规则不会主动出现。** `-target` 在没被问到时不会被主动警告；
   `>= 4.0` 这种反向 pin 与「删掉 lock 文件」也不会自我纠正。

## 评测结果

模型：`anthropic/claude-opus-5`，thinking `medium`（`tools/run_evals.py` 默认，未传 `--model` / `--thinking`）。
两组各一次运行，同一天、同一份 `evals.json`、同一批夹具。判定方式：逐条读
`/tmp/hs-evals/terraform/anthropic-claude-opus-5-medium/{baseline,skill}/<n>/answer.md`
以及该目录下模型实际写出的 `.tf` / `.tftest.hcl` 工件（只看答复文字会漏判接口设计与
splat 这类只体现在文件里的行为）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 重构复制粘贴的网络层为模块 | claude-opus-5:medium | 无（baseline） | false | **4 / 8**：④ 明文 `db_password`（并要求轮换）、⑦ 三环境三个 module 调用方且不引入第三方编排器；③⑥ 各达成一半（有 type/description、无 `validation`；提了 blast radius、拒绝拆） | 明确选择「保留 `count`，不换 `for_each`」；`moved.tf` 只有 root→module；`version = ">= 4.0"` 是反向 pin，且主动删除了 `.terraform.lock.hcl`；输出仍是 `aws_subnet.public[*].id` |
| 1 重构复制粘贴的网络层为模块 | claude-opus-5:medium | 有 | **true** | **8 / 8** | `for_each` 键取 AZ 名、`netnum` 用 `{ for index, az in var.azs : az => index }` 保住原 CIDR；每个 env root 都有 root→module **与 `[0]→["eu-west-1a"]`** 的 `moved`；闸门写成「必须 `Plan: 0 to add, 0 to change, 0 to destroy`，出现任何 add/destroy 就不要 apply」；`validation` 拒绝 `/24` 与重复 AZ；拆成 `environments/{dev,staging,prod}` 三个 backend key；`required_version >= 1.6.0` + `aws ~> 6.0` + 显式保留 lock 文件；输出改为 `[for az in var.azs : aws_subnet.public[az].id]` |
| 2 生产被手改后的 state 对账 | claude-opus-5:medium | 无（baseline） | false | **5 / 8**：①先冻结不 apply、②三处漂移三种补救、⑤缺 lock 文件让 plan 不可信、⑦`-refresh-only` → 改配置 → 空 plan 的顺序、③一半（用了 `import`/`removed` 块，没提 `-generate-config-out`） | `use_lockfile` 标成「TF 1.10+」（错，Terraform 是 1.11 GA）；全文没有 `-target` 警告；只说 bucket versioning，没提 state 明文与加密 |
| 2 生产被手改后的 state 对账 | claude-opus-5:medium | 有 | **true** | **8 / 8** | 版本改对了：「`use_lockfile` 在 Terraform 1.11 / OpenTofu 1.10 才 GA」；主动写「不要用 `-target` 分步做。它跑的是故意残缺的图，而且 `locals` 一旦引用被 target 的资源会把消费者全拖进来」；`import` 骨架用 `plan -generate-config-out=` 起草再删 computed 属性；`removed { lifecycle { destroy = false } }`；反对 `ignore_changes = all`；backend 同时加锁与加密；并抓到夹具里的真陷阱——`aws_ecs_service.api` 没有 `network_configuration`，补一个不完整的会把 hotfix SG 摘掉 |
| 3 给模块写 `terraform test` | claude-opus-5:medium | 无（baseline） | false | **7 / 8** | 交付质量很高（plan/apply 分文件、回读磁盘、幂等性、双 CLI 矩阵、「不能证明什么」清单）。唯一缺口是⑤：没有分运行时标注 mock 的版本门槛，CI 矩阵下界压到 TF 1.6.6 / Tofu 1.6.3 |
| 3 给模块写 `terraform test` | claude-opus-5:medium | 有 | **true** | **7 / 8** | 同样缺⑤（模块无需 mock，答复未触及该门槛）。其余更强：明确「`assert` 的 `condition` 必须引用配置中的对象，`fileexists("字面量路径")` 会被拒为 `Invalid assert expression`」，并把 `checksum_algorithm` 静默降级 md5 固化成一条命名清楚的回归用例 |
| 4 负例：Dockerfile 1.8 GB 瘦身 | claude-opus-5:medium | 无（baseline） | false | 3 / 3 | 纯容器答案，`grep -c -i terraform` = 0 |
| 4 负例：Dockerfile 1.8 GB 瘦身 | claude-opus-5:medium | 有 | **false** ✅ | 3 / 3 | **未加载 terraform skill**——`description` 的否定边界成立。答案是多阶段 + `node:22-slim` + `npm ci --omit=dev` + `.dockerignore` + `USER node`，同样零 Terraform 内容 |

结论：**通过**。

- 场景 1：基线 4/8 → 有 skill 8/8，四条基线未达成的行为全部被填补（`for_each` 转换、
  `[i]→["key"]` 的 `moved`、CIDR `validation`、拆 state、真正的版本 pin、splat 现代化）。
- 场景 2：基线 5/8 → 有 skill 8/8，其中**两条是基线答错而不是漏答**——
  `use_lockfile` 的版本从「TF 1.10+」纠正为「Terraform 1.11 / OpenTofu 1.10」，
  以及 `-target` 从只字不提变成带级联理由的主动警告。
- 场景 3：7/8 → 7/8，同一条缺口（mock 的分运行时门槛）。该场景不构成通过依据，
  但它证明 skill 没有让一个本来就强的答案变差。
- 场景 4（负例）：`skill_read == false`，无需修改 `description`。

## 备注

### 许可（最需要下游注意的一条）

本 skill 是本仓库第一个**官方文档不能 merged** 的 skill。`developer.hashicorp.com/terraform`
的源仓库 `hashicorp/web-unified-docs` 与 `hashicorp/terraform` 本身，GitHub API 都报
NOASSERTION，实读 LICENSE 都是 **BUSL-1.1**（Licensor: IBM，Licensed Work 自 Terraform 1.6.0 起）。
BUSL 是 source-available 而非开源许可，按许可规则表走 `relation: reference`：只核对事实，
一字未抄。可 merged 的官方取证源因此只剩 Apache-2.0 的 `opentofu.org/docs` 与 MPL-2.0 的
`opentofu/opentofu` CHANGELOG，两边共有的语言语义优先在那边取证，Terraform 独有的事实
则靠本机实跑 + `hashicorp/terraform` 各 `v1.N` 分支的 CHANGELOG 交叉确认。

### MPL-2.0 的注释头

`hashicorp/agent-skills` 是 MPL-2.0。实质派生自它的 **5 个** reference 首行都加了
`<!-- Adapted from hashicorp/agent-skills (MPL-2.0); see NOTICE.md -->`：

| reference | 有 MPL 注释 | 派生自 |
|---|---|---|
| `hcl-style.md` | ✅ | `terraform-style-guide` |
| `modules.md` | ✅ | `refactor-module` + `terraform-style-guide` |
| `refactoring.md` | ✅ | `refactor-module` + `terraform-search-import` |
| `testing.md` | ✅ | `terraform-test` 及其三个 reference |
| `provider-development.md` | ✅ | `provider-*` / `new-terraform-provider` 五个 skill |
| `state.md` | ❌（正确） | antonbabenko(Apache-2.0) + OpenTofu 文档 |
| `policy-and-security.md` | ❌（正确） | antonbabenko + nitinjain + awesome-copilot |
| `opentofu-differences.md` | ❌（正确） | 两边 CHANGELOG 的事实提取 |

`SOURCES.yaml` 的 `hashicorp-agent-skills.notes` 里逐条写明了这个做法与哪些文件不带头。

### 本机实跑（六个实验，两轮结果一致）

`terraform` 1.16.2 与 `tofu` 1.12.6 都装在 `/usr/local/bin`。SKILL.md 与
`references/testing.md` 写进正文的验证门**全部是跑出来的，不是拟稿**：
`fmt -check -recursive` / `init -backend=false` / `validate` / `test` 四条命令在
`/tmp/tf-gate`（内容就是评测夹具 `artifact_bundle.tf`，外加一个指向不存在 S3 桶的 backend）
上依次 exit 0，`terraform test` 报 `Success! 3 passed, 0 failed.`。
`count` 与 `for_each` 的两个数字（`1 to add / 2 to destroy` 对 `1 to destroy`）
与 `moved` 的 0/0/0 都来自 `/tmp/tf-moved`、`/tmp/tf-foreach`。详见「本机实跑验证」节。

**三条上游错误是靠实跑抓出来的**（裁决 9/10/11），都写进了正文的相反面：
mock 可以用在 `command = apply`、`-filter` 过滤的是文件不是 run 块名、
`-no-cleanup` 这个旗标根本不存在。

### 未来同步时要盯的

- Terraform 1.17 已进 beta、1.18 的 unreleased CHANGELOG 里有 `terraform test cleanup`
  与 run 块内 `backend` 的实验特性；一旦 GA，`references/testing.md` 关于
  「没有 `-no-cleanup`」的段落要改。
- OpenTofu 1.13 已进 beta（symbol libraries 实验），`references/opentofu-differences.md`
  的独有特性表要跟。
- `hashicorp/agent-skills` 的 `terraform-stacks` 与 `provider-actions` 更新较快；本 skill
  只取入门层，`paths` 已限定到实际使用的十个目录。

### 放弃的方向

- 不写 `scripts/`。这个主题的所有可自动化动作都是 `terraform` 自己的子命令，
  外面再包一层脚本只会多一个要维护的间接层，没有可运行价值。
- 不覆盖 HCP Terraform / TFE 的平台面（Stacks 只留一句「Terraform 独有、需要该平台」）、
  不覆盖任何 provider 的资源字段、不推荐 Terragrunt/Terramate 这类第三方编排器。
