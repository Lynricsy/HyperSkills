# ml-training 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `gh api repos/<owner>/<repo>`（已登录账号 Lynricsy，5000 次/小时配额），逐个候选核对
    stars / `pushed_at` / `license.spdx_id`
  - `gh api repos/<o>/<r>/git/trees/<ref>?recursive=1` 列目录，`contents/<path>` 读原文
  - 领域官方组织仓库：`NVIDIA/`、`huggingface/`、`pytorch/`、`vllm-project/`、
    `deepspeedai/`、`EleutherAI/`、`axolotl-ai-cloud/`、`unslothai/`
  - 多技能仓库：`NVIDIA/skills`（339 个 skill）、`huggingface/skills`（26 个）、
    `Orchestra-Research/AI-Research-SKILLs`（22 个分类目录）、`github/awesome-copilot`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- **许可一律实读 LICENSE 正文**，不信 API 的 `spdx_id`：`pytorch/pytorch` 的 API 返回
  `NOASSERTION`，实读为 BSD 3-Clause；`NVIDIA/skills` 无单一 LICENSE，是
  `LICENSE-APACHE` + `LICENSE-CC-BY-4.0` 双许可（README.md 首行 SPDX 头
  `Apache-2.0 AND CC-BY-4.0`）；`huggingface/skills` 的 skill frontmatter 写
  `license: Complete terms in LICENSE.txt`，但仓库内**没有任何 LICENSE.txt**，
  只有根目录一份 Apache-2.0 LICENSE。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | NVIDIA/skills `skills/nemo-mbridge-perf-memory-tuning` | https://github.com/NVIDIA/skills | 3257 | 2026-09-11 | Apache-2.0 AND CC-BY-4.0 | OOM 分诊、碎片化、显存构成 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 唯一带实测数字的候选：32×H100 上 TP 4→8 吞吐 -28% 换 3 GB，PP 4→8 -6%，`expandable_segments` 零成本解决同一个 OOM；还自曝了一次把 OOM 修复误记到 VPP 上的错误归因 |
| 2 | NVIDIA/skills `skills/nemo-mbridge-perf-parallelism-strategies` | https://github.com/NVIDIA/skills | 3257 | 2026-09-11 | Apache-2.0 AND CC-BY-4.0 | TP/PP/CP/EP 选型与 GPU 计数 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `min_gpus = PP * max(TP*CP, EP*ETP)` 并点名否定流行的连乘式；MoE 按 active 参数定 TP 的表 |
| 3 | NVIDIA/skills `skills/nemo-mbridge-perf-activation-recompute` | https://github.com/NVIDIA/skills | 3257 | 2026-09-11 | Apache-2.0 AND CC-BY-4.0 | 选择性重算 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 先分辨"真分配 vs 碎片"（比较 `max_memory_allocated` 与 `max_memory_reserved`），再选重算边界；`mlp` 重算 ~3 GB 换 ~16% 利用率 |
| 4 | NVIDIA/skills `skills/nemo-mbridge-resiliency` | https://github.com/NVIDIA/skills | 3257 | 2026-09-11 | Apache-2.0 AND CC-BY-4.0 | 容错、掉队检测、原地重启 | 3 | 3 | 2 | 3 | 2 | 13 | MAYBE | 内容正确但与 Megatron Bridge / NeMo Run / Slurm 强绑定，可迁移部分只剩"checkpoint 要能恢复"这一句 |
| 5 | huggingface/skills `skills/huggingface-llm-trainer` | https://github.com/huggingface/skills | 11037 | 2026-09-10 | Apache-2.0（见上文裁决） | SFT/DPO/GRPO 全流程 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 方法选型表与数据格式要求可用；但主体是 HF Jobs 平台操作（`hf_jobs()` MCP、flavor、时薪），不可迁移 |
| 6 | huggingface/skills `skills/trl-training` | https://github.com/huggingface/skills | 11037 | 2026-09-10 | Apache-2.0 | TRL CLI | 3 | 3 | 2 | 3 | 2 | 13 | MAYBE | 覆盖 SFT/DPO/GRPO/KTO/RLOO/Reward 六个 CLI，形式是命令清单；本 skill 用其方法枚举，不抄 CLI |
| 7 | huggingface/skills `skills/huggingface-community-evals` | https://github.com/huggingface/skills | 11037 | 2026-09-10 | Apache-2.0 | 评测（lighteval / inspect） | 3 | 3 | 2 | 3 | 2 | 13 | MAYBE | 有价值的是"用 vLLM 跑评测"的脚本形态；评测方法论部分很薄 |
| 8 | huggingface/skills `skills/hf-mem` | https://github.com/huggingface/skills | 11037 | 2026-09-10 | Apache-2.0 | 权重显存估算 CLI | 3 | 3 | 1 | 3 | 2 | 12 | MAYBE | 只算**推理**加载权重，不含梯度/优化器/激活；确认了"需要一个四项分账工具"这个缺口 |
| 9 | huggingface/skills `skills/huggingface-vision-trainer` | https://github.com/huggingface/skills | 11037 | 2026-09-10 | Apache-2.0 | 视觉模型训练 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT | 范围外：本 skill 聚焦语言模型权重训练，视觉专有流程（SAM2、timm、目标检测）不纳入 |
| 10 | Orchestra `08-distributed-training/pytorch-fsdp2` | https://github.com/Orchestra-Research/AI-Research-SKILLs | 12545 | 2026-06-16 | MIT | FSDP2 契约 | 1 | 2 | 3 | 3 | 2 | 11 | INCLUDE | 五条契约（bottom-up、`model(x)`、分片后建优化器、`set_requires_gradient_sync`、DCP）逐条对 pytorch.org 复核通过 |
| 11 | Orchestra `03-fine-tuning/peft` | 同上 | 12545 | 2026-06-16 | MIT | LoRA/QLoRA 选型 | 1 | 2 | 3 | 2 | 2 | 10 | INCLUDE | 选型判据可用；"6MB adapter vs 14GB 全模型"的对比正确，但它没说基座权重仍常驻——本 skill 把这点写成硬规则 |
| 12 | Orchestra `06-post-training/grpo-rl-training` | 同上 | 12545 | 2026-06-16 | MIT | GRPO 奖励设计 | 1 | 2 | 3 | 2 | 2 | 10 | INCLUDE | 奖励函数库与组内同质化失效有用；超参默认值已落后于 trl 1.x，全部以本机实测覆盖 |
| 13 | Orchestra `12-inference-serving/vllm` | 同上 | 12545 | 2026-06-16 | MIT | vLLM 部署 | 1 | 2 | 2 | 0 | 2 | 7 | REJECT | **正确性 0**：文档化了 `--enable-metrics` / `--metrics-port` 作为 `vllm serve` 参数（前者只存在于 `vllm run-batch`，后者不存在；metrics 在 API 端口的 `/metrics`），并复读无条件的 "24x throughput" |
| 14 | Orchestra `08-distributed-training/deepspeed` | 同上 | 12545 | 2026-06-16 | MIT | ZeRO | 1 | 2 | 0 | 2 | 2 | 7 | REJECT | 文档抓取生成，"Common Patterns" 一节是被压平的目录（"DeepNVMe Contents Requirements Creating…"），无可执行规则 |
| 15 | Orchestra `10-optimization/ml-training-recipes` | 同上 | 12545 | 2026-06-16 | MIT | 通用训练配方 | 1 | 2 | 2 | 2 | 2 | 9 | REJECT | 范围外：重心在视觉/扩散/生信/医学影像，与本 skill 的 LLM 权重训练边界不重合 |
| 16 | Orchestra `11-evaluation/lm-evaluation-harness` | 同上 | 12545 | 2026-06-16 | MIT | 学术基准评测 | 1 | 2 | 2 | 2 | 2 | 9 | MAYBE | 是 harness 的用法说明，不是评测方法论；污染检测定义取自上游仓库本体（#20） |
| 17 | huggingface/trl（docs） | https://github.com/huggingface/trl | 19279 | 2026-09-11 | Apache-2.0 | TRL 官方文档 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `reducing_memory_usage.md` 的省显存清单、DPO beta 语义、GRPO 的 vLLM colocate 默认 |
| 18 | pytorch/pytorch（docs） | https://github.com/pytorch/pytorch | 102922 | 2026-09-11 | BSD-3-Clause（实读） | 可复现性、AMP | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `notes/randomness.md` 是"可复现到什么程度"这一节的唯一可信来源 |
| 19 | vllm-project/vllm（docs） | https://github.com/vllm-project/vllm | 91488 | 2026-09-11 | Apache-2.0 | 推理部署 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `conserving_memory.md` / `optimization.md` / `usage/metrics.md`：KV cache 是残值、chunked prefill 默认开、抢占是容量信号 |
| 20 | deepspeedai/DeepSpeed（docs） | https://github.com/deepspeedai/DeepSpeed | 43095 | 2026-09-11 | Apache-2.0 | ZeRO 分级语义 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 只取三级分片的精确定义与 offload 的定位；V100 时代的规模示例不带 |
| 21 | EleutherAI/lm-evaluation-harness（docs） | https://github.com/EleutherAI/lm-evaluation-harness | 13948 | 2026-09-10 | MIT | 污染检测 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `docs/decontamination.md`：13-gram 任一重叠即判污染（源自 GPT-3 附录 C），以及"索引训练集、流式扫评测集"的方向 |
| 22 | huggingface/peft | https://github.com/huggingface/peft | 21654 | 2026-09-10 | Apache-2.0 | LoRA 字段语义 | 3 | 3 | 3 | 3 | 2 | 14 | MAYBE→reference | 字段语义正确，但本 skill 的所有数值以本机 peft 0.20.0 dataclass 实读为准，未复制文本 |
| 23 | NVIDIA/TensorRT-Model-Optimizer | https://github.com/NVIDIA/TensorRT-Model-Optimizer | 3789 | 2026-09-11 | Apache-2.0 | 量化/蒸馏 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT | 任务书点名的 `Model-Optimizer` 在 `NVIDIA/skills` 里不作为独立 skill 存在（只在 `nemotron-customize/references/context/modelopt-optimization.txt` 出现）；本体仓库是 TensorRT 生态专有工具链，写进框架中立的 skill 会变成单厂商教程 |
| 24 | axolotl-ai-cloud/axolotl | https://github.com/axolotl-ai-cloud/axolotl | 12460 | 2026-09-11 | Apache-2.0 | YAML 驱动微调 | 2 | 3 | 3 | 3 | 2 | 13 | REJECT | 优秀但是"某一个框架的配置手册"；本 skill 的规则要在 TRL / Axolotl / torchtune 之间中立，写进去会绑死一个 YAML schema |
| 25 | unslothai/unsloth | https://github.com/unslothai/unsloth | 76011 | 2026-09-11 | Apache-2.0 | 单卡加速微调 | 2 | 3 | 3 | 2 | 2 | 12 | REJECT | 同上，且其"省 60% 显存、快 2 倍"的宣称随版本与模型族浮动，无法在本机验证 |
| 26 | pytorch/torchtune | https://github.com/pytorch/torchtune | 5810 | 2026-09-09 | BSD-3-Clause | 官方微调配方 | 3 | 3 | 3 | 3 | 2 | 14 | REJECT | 理由同 #24：recipe/config 体系是它自己的，通用规则已由 pytorch-docs 与 trl-docs 覆盖 |
| 27 | huggingface/accelerate | https://github.com/huggingface/accelerate | 9860 | 2026-09-09 | Apache-2.0 | 分布式启动 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT | 与 FSDP2 / DeepSpeed 条目重叠，未提供这两者之外的独立判据 |
| 28 | huggingface/lighteval | https://github.com/huggingface/lighteval | 2540 | 2026-09-09 | MIT | 评测框架 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT | 与 #21 重叠；本 skill 只需要一种默认评测口径 |
| 29 | NVIDIA/Megatron-LM | https://github.com/NVIDIA/Megatron-LM | 17856 | 2026-09-11 | NOASSERTION | 大规模并行 | 3 | 3 | 3 | 3 | 1 | 13 | REJECT | 许可为 NVIDIA 自有条款（API 报 NOASSERTION），不作为 merged；其并行结论已通过 #1/#2/#3 的 Apache-2.0 skill 取得 |
| 30 | github/awesome-copilot | https://github.com/github/awesome-copilot | 38890 | 2026-09-10 | MIT | 通用 skill 集 | 3 | 3 | — | — | 2 | — | REJECT | 全仓 `skills/` 下没有任何模型训练 / 微调 / 分布式训练主题（已按 `train|fine-tun|pytorch|llm` 过滤目录树确认） |

## 深度审查

### NVIDIA/skills 的 `nemo-mbridge-perf-*`（#1、#2、#3）

结构统一：frontmatter（`name` / `description` / `license` / `when_to_use`）+ What It Is +
Quick Decision + Enablement + Compatibility + **Measured Results** + Code Anchors +
Failure Diagnosis + Known Limitations。`when_to_use` 是非规范字段，合入时剥离。

这三个是本波次质量最高的候选，理由是它们**给数字并给条件**：`Llama3 70B SFT / 32×H100 80GB /
FP8 / TP4 PP4 VPP5 DP2 / MBS1 GBS32 / seq 4096`，baseline 709.93 TFLOP/s/GPU，然后逐个实验
列 TFLOP/s、峰值显存、结论。`nemo-mbridge-perf-memory-tuning` 甚至主动记录了一次错误归因
（把 OOM 修复算在 VPP 5→10 上，实际是 `expandable_segments`，且 VPP=10 峰值更高：60.2 vs
58.8 GB）——这类自我更正在候选里极罕见，是可信度的强信号。

不可迁移的部分：`megatron.bridge.*` 的配置对象、`LoRA(sequence_parallel_input_regather=True)`、
`estimate_training_memory(cfg, ...)`、`@docs/...` 与 `@skills/...` 交叉引用语法、Slurm 脚本。
本 skill 是框架中立的，只合入结论与顺序，不合入符号。

### huggingface/skills 的 `huggingface-llm-trainer`（#5）

738 行 SKILL.md + 10 个 references + 8 个脚本，规模最大。但重心是 **Hugging Face Jobs
平台**：`hf_jobs("uv", {...})` MCP 调用、`t4-small`/`a10g-large` flavor 名、时薪表、
`secrets={"HF_TOKEN": "$HF_TOKEN"}`、job timeout。这些都不是"训练"知识。

可迁移且正确的部分：方法选型表（SFT/DPO/GRPO/Reward × 数据形状 × 用途）、
SFT→DPO 的流水线顺序、`SFTConfig(max_length=)` 而非 `max_seq_length` 的明确纠正、
省显存的升级顺序。

`references/hardware_guide.md` 的 `Memory (GB) ≈ params_in_billions × 20`（全参）/ `× 4`
（LoRA）这个经验式被**裁决为不采用**：它给一个总数而不给构成，正是本 skill 认定会让人
"降 batch 来救优化器态"的那类建议。改用四项分账（`scripts/vram_ledger.py`）。

其 frontmatter 的 `license: Complete terms in LICENSE.txt` 是 Anthropic 模板残留，仓库内
不存在该文件（`git/trees?recursive=1` 全量过滤 `licen` 只有根 `LICENSE`），故以根
Apache-2.0 为准。

### Orchestra-Research/AI-Research-SKILLs（#10–#16）

22 个分类目录、778 个路径条目，覆盖面最广但质量分布极不均匀，**必须逐 skill 判定，不能整仓收**：

- `pytorch-fsdp2`：最好的一个。五条契约全部对 PyTorch 官方文档核实通过，且解释了 why
  （`fully_shard` 按参数分组、只 shard 根模块会更差却看起来正常）。
- `peft`：判据清晰，数量级正确。
- `grpo-rl-training`：奖励函数库有价值；超参默认值停留在旧版 TRL。
- `deepspeed`：文档抓取的产物，"Common Patterns" 是被压平的目录字符串。**REJECT**。
- `vllm`：**REJECT on correctness**，见冲突与裁决 #1。
- `ml-training-recipes`：作者是 `dailycafi`（非 Orchestra 本体），质量不差但范围是全域
  ML（视觉/扩散/生信），越过本 skill 的边界。

仓库整体 `pushed_at` 为 2026-06-16，将近 3 个月未动，新鲜度 2 分；作者是社区而非厂商，
权威 1 分。因此其贡献的每一条都在官方文档上复核过才写入。

### 官方文档类（#17–#21）

这五个是本 skill 的事实底座。取用方式一律"读仓库内的 markdown 源文件"，而不是读渲染后的
文档站，原因是许可要看**仓库自己的** LICENSE：`pytorch/pytorch` 的 API `spdx_id` 是
`NOASSERTION`，实读 LICENSE 是 BSD 3-Clause，可以 merged。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | vLLM 的 metrics 怎么开 | Orchestra vllm skill：`--enable-metrics --metrics-port 9090`；vLLM 官方：`vllm serve` 恒在 API 端口的 `/metrics` 暴露 | 采官方。`--enable-metrics` 只存在于 `vllm run-batch`（读 `vllm/entrypoints/openai/run_batch.py`：`if args.enable_metrics: start_http_server(port=args.port, ...)`），`--metrics-port` 不存在 | 官方厂商 > 社区；且直接读上游源码 |
| 2 | OOM 先动哪个旋钮 | HF skill：LoRA → 降 batch → 累积 → 检查点 → 混合精度 → 换更大卡；NVIDIA：先 `expandable_segments`，TP 最后 | 采 NVIDIA 的顺序，并在前面插入"先算分账"。HF 的清单没有分辨"碎片 vs 容量"，也没有成本排序 | 有实测数字 > 无数字；NVIDIA 给了 -28%/-6%/-16% 的代价 |
| 3 | 显存怎么估 | HF：`params_B × 20`（全参）；NVIDIA：四项 + 估算器且声明不含碎片/workspace | 采四项分账，并写明是下界、需留 10–20% 余量 | 单一乘数无法指出该动哪一项；本机实测 AdamW = 8.000005 B/param 支持分账式 |
| 4 | DPO/GRPO 的学习率 | Orchestra GRPO skill 与多数社区配方：1e-5～5e-5；trl 1.13 默认：两者均 1e-6 | 采库默认，并在正文写出 SFT 2e-5 与之相差二十倍的后果 | 更新 > 更旧；且本机读 dataclass 实证 |
| 5 | GRPO 是否带 KL | GRPO 原论文与旧配方：`beta` 取 0.04；trl 1.13：`beta=0.0`（默认关闭） | 正文写"库默认已关闭"，并把"奖励可被字符串满足时必须重新加 KL 锚"写成规则，不写某个具体数 | 版本事实以安装版为准，判断以后果为准 |
| 6 | 梯度检查点要不要传 `use_reentrant=False` | 大量教程：必须显式传；transformers 5.17：未传时默认即 `{"use_reentrant": False}` | 写成"这已是默认；看到要求显式传的建议，说明它描述的是旧版本" | 读安装版 `modeling_utils.py` 源码 |
| 7 | MoE 组合并行的最小 GPU 数 | 很多 README / sizing 表：`PP*TP*CP*EP*ETP`；NVIDIA：`PP*max(TP*CP, EP*ETP)` | 采 NVIDIA，并在规则里点名否定连乘式 | 官方厂商，且给出了机制解释（dense mesh 与 expert mesh 在同一 PP stage 共用 GPU） |
| 8 | 训评隔离的判定口径 | 各家含糊的"去重一下"；lm-evaluation-harness：13-gram 任一重叠即污染 | 采 13-gram 口径并落进 `scripts/dataset_overlap.py`，同时要求报告污染比例 | 有可执行定义 > 无定义；源自 GPT-3 附录 C |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| nvidia-skills | NVIDIA/skills（4 个 `nemo-mbridge-perf-*` / `-resiliency`） | merged | OOM 分诊顺序与实测代价、碎片 vs 容量、`min_gpus` 公式、并行选型表、CPU offload 与 PP>1 不兼容 |
| hf-skills | huggingface/skills（4 个 skill） | merged | 方法选型表与数据形状、SFT→DPO 顺序、`max_length` 而非 `max_seq_length`、省显存升级顺序 |
| orchestra-ai-research | Orchestra（fsdp2 / peft / grpo） | merged | FSDP2 五条契约、PEFT/QLoRA/全参的选型分界、GRPO 奖励设计与组内同质化 |
| pytorch-docs | pytorch/pytorch `notes/randomness.md`、`notes/amp_examples.md` | merged | 可复现性的真实边界、确定性算法与 cudnn.benchmark、seed 覆盖不到的地方 |
| trl-docs | huggingface/trl `docs/source/*` | merged | 省显存清单、DPO beta 语义、GRPO 的 vLLM colocate |
| vllm-docs | vllm-project/vllm `docs/configuration/*`、`docs/usage/metrics.md` | merged | KV cache 是残值、chunked prefill 默认与其约束、抢占、CUDA graph、metrics 端点 |
| deepspeed-docs | deepspeedai/DeepSpeed `docs/_tutorials/zero.md` | merged | ZeRO 三级各分片什么、offload 的定位 |
| lm-eval-harness | EleutherAI/lm-evaluation-harness `docs/decontamination.md` | merged | 13-gram 污染定义与扫描方向 |
| peft-docs | huggingface/peft | reference | LoraConfig 字段语义交叉验证（数值以本机实读为准，未复制文本） |

## 基线缺口

无 skill（`uv run tools/run_evals.py ml-training --baseline`，claude-opus-5 / medium，
五个场景 status=ok，`skill_read=False`）时未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 单卡 SFT 崩溃 | 「逐条点名 trl 1.13 / transformers 5.x 的已移除参数」 | 只改了 4 处（`max_seq_length`→`max_length`、`evaluation_strategy`→`eval_strategy`、`tokenizer`→`processing_class`、`torch_dtype`→`dtype`），**把 `warmup_ratio=0.03` 原样留在了新脚本里**（`train_sft.py:110`）。transformers 5.17 已移除 `warmup_ratio`，所以它交付的"修好的"脚本仍然在同一行抛 `TypeError` |
| 1 单卡 SFT 崩溃 | 「给出 8B 全参 + AdamW 的显存算术，说明 100–130 GB 量级」 | 写成「bf16 权重 16 + bf16 梯度 16 + 两个 AdamW moment 32 = 64 GB，剩不到 16 GB 给激活」。漏了 fp32 master（32 GB），且把两个 fp32 moment 算成 32 GB（实为 64 GB）。少算约一半，结论从"算术上不可能"被削弱成"差一点就够" |
| 1 单卡 SFT 崩溃 | 「按数据定 `max_length` 并说明截断代价」 | 部分达成：取了 8192 覆盖 p99=9.6k，但没说被截断那部分会变成"答案被切掉的 prompt 样本" |
| 3 DPO/GRPO 复核 | 「`DPOConfig(max_prompt_length=...)` 在 trl 1.13 已不存在」 | 完全未达成，且**方向相反**：答案里把 `max_prompt_length=512` 当作合法参数讨论（"先看工单长度分布…若 chosen 回复被右截断"）。实际它会先抛 `TypeError` |
| 3 DPO/GRPO 复核 | 「指出库默认 LR 为 1e-6」 | 部分达成：说了"DPO 全参常用 5e-7~5e-6、GRPO 常用 ~1e-6"，是社区经验值而非可核对的库默认 |
| 2 数据污染 | — | **全部达成**。基线甚至复现了 `SEED=0` 的切分，算出 1167/1200 条基准题落入 train。此场景零区分度 |
| 4 vLLM 部署 | — | 全部达成（chunked prefill 约束、KV cache 算术、抢占、0.98、enforce-eager、TTFT 物理下界都对） |
| 5 负例 | — | 达成：按 API 客户端问题回答（重试、结构化输出、缓存、并发、密钥），未提微调 |

结论：区分度集中在**版本分界事实**（场景 1、3）与**显存分账的算术**（场景 1）。这正是
`references/api-versions.md` 与 `references/memory-ledger.md` 要填的洞。场景 2、4 在
opus-5 基线下已饱和，保留它们是为了防止 skill 引入回归。

## 评测结果

模型固定 `anthropic/claude-opus-5`、thinking=medium（`tools/run_evals.py` 默认），
基线与有 skill 两轮同模型。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 单卡 SFT 崩溃 | claude-opus-5 medium | 无（baseline） | False | 4/7 | 漏 `warmup_ratio`；显存算术少算约一半；`max_length` 只做了一半 |
| 2 数据污染 | claude-opus-5 medium | 无（baseline） | False | 7/7 | 零区分度 |
| 3 DPO/GRPO 复核 | claude-opus-5 medium | 无（baseline） | False | 5/7 | 漏 `max_prompt_length`；LR 只给社区经验值 |
| 4 vLLM 部署 | claude-opus-5 medium | 无（baseline） | False | 7/7 | 零区分度 |
| 5 负例（API 客户端） | claude-opus-5 medium | 无（baseline） | False | 3/3 | 正确按 API 问题作答 |
| 1 单卡 SFT 崩溃 | claude-opus-5 medium | 有 | True | 7/7 | 六处改名全中（含基线漏掉的 `warmup_ratio`，还额外实测出 `group_by_length` 也被删了）；显存写成 16–18 B/param ≈ 122 GiB + 激活 272 GiB = 391 GiB 台账，明确"与 batch 无关地放不下"；用 `scripts/vram_ledger.py` 的输出做 LoRA 方案；点出 eval 边界的独立峰值 |
| 2 数据污染 | claude-opus-5 medium | 有 | True | 7/7 | 与基线同为满分，另外补上了 13-gram/MinHash 阈值、按家族+时间切分、以及"不允许调阈值到数字好看为止" |
| 3 DPO/GRPO 复核 | claude-opus-5 medium | 有 | True | 7/7 | `max_prompt_length` 的 `TypeError` 点名（基线把它当合法参数）；LR 写成"比 trl 1.13 的 1e-6 默认高 20 倍"；按 blocks/wastes/degrades 三档输出，并附显存台账 |
| 4 vLLM 部署 | claude-opus-5 medium | 有 | True | 7/7 | 与基线同为满分，metrics 一条更精确（`--enable-metrics` 只属于 `vllm run-batch`）；补了 `cudagraph_capture_sizes` 与上线前三项一致性检查 |
| 5 负例（API 客户端） | claude-opus-5 medium | 有 | **False** | 3/3 | 明确声明"没有我们自己的权重，`ml-training` 不适用，未加载"；全程按 API 客户端问题作答，未提微调/LoRA/显存/GPU |

结论：**通过**。基线未达成的行为在有 skill 时达成，且都落在设计时预期的两类缺口上：

- 场景 1：基线把 `warmup_ratio=0.03` 留在"修好的"脚本里（仍会 `TypeError`），并把 8B 全参
  模型状态算成 64 GB（漏 fp32 master、moment 少算一半）；有 skill 时六处改名全中，台账
  122 GiB / 391 GiB 与本机 `scripts/vram_ledger.py` 一致。
- 场景 3：基线把 `DPOConfig(max_prompt_length=512)` 当合法参数继续讨论；有 skill 时点名
  它在 trl 1.13 已移除并给出确切 `TypeError`，同时把 LR 从社区经验值换成可核对的库默认。

场景 2、4 两轮都是满分，没有制造出区分度——保留它们的作用是回归防护而非度量。
负例 `skill_read=False`，未被误触发。

## 备注

### 本机验证环境

- **本机没有 GPU**：`nvidia-smi` 不存在（`command not found`），
  `torch.cuda.is_available()` 为 `False`。
- 为做 API 与算术验证，在 `/tmp/mlwork/.venv`（Python 3.12，`UV_TORCH_BACKEND=cpu`）
  安装了 `torch 2.14.0+cpu` / `transformers 5.17.0` / `trl 1.13.0` / `peft 0.20.0` /
  `datasets` / `accelerate`。该环境是一次性的，不在仓库内。

### `[verified]`——本机实测的事实

1. `torch.optim.AdamW` 状态 = **8.000005 字节/参数**（58,073,600 参数的 Llama，
   `exp_avg` + `exp_avg_sq` 均 fp32，外加每个参数张量一个标量 `step`）。
2. LoRA `r=16` 打 `q_proj`/`v_proj` → 262,144 可训练参数 = 0.4514%，优化器态
   464 MB → 2.1 MB。
3. 七处已移除参数全部复现 `TypeError`：`SFTConfig(max_seq_length=)`、
   `DPOConfig(max_prompt_length=)`、`TrainingArguments(evaluation_strategy=)`、
   `TrainingArguments(warmup_ratio=)`、`TrainingArguments(save_safetensors=)`、
   `TrainingArguments(group_by_length=)`、
   `Trainer(tokenizer=)`；`from_pretrained(torch_dtype=)` 仅告警
   （`modeling_utils.py:1409`）。
4. GRPO 批次整除：`bs=2, accum=1, G=8` 抛
   `ValueError: generation_batch_size (2) must be divisible by num_generations (8)`；
   `bs=4, accum=2, G=8` 与 `bs=3, accum=1, G=3` 通过。
5. 各配置默认值（读安装版 dataclass）：`SFTConfig.learning_rate=2e-5`、
   `DPOConfig/GRPOConfig.learning_rate=1e-6`、`SFTConfig.max_length=1024`、
   `truncation_mode='keep_start'`、`packing=False`、`packing_strategy='bfd'`、
   `completion_only_loss=None`、`GRPOConfig.beta=0.0`、`loss_type='dapo'`、
   `num_generations=8`、`scale_rewards='group'`、`epsilon=0.2`、
   `vllm_mode='colocate'`、`vllm_gpu_memory_utilization=0.3`、
   `LoraConfig(r=8, lora_alpha=8, target_modules=None)`、
   `TrainingArguments.optim='adamw_torch_fused'`、
   `average_tokens_across_devices=True`、`seed=42`、`data_seed=None`。
   `TrainingArguments` 共 112 个字段，其中**没有** `warmup_ratio` / `save_safetensors` /
   `evaluation_strategy` / `processing_class`。
6. `gradient_checkpointing_enable()` 在 transformers 5.17 的签名是
   `(gradient_checkpointing_kwargs=None, every_n_layers=1, offload=False)`，未传时
   默认 `{"use_reentrant": False}`；启用后 `config.use_cache` **仍为 `True`**，首次
   forward 时由 logger 打印 `use_cache=True is incompatible with gradient
   checkpointing. Setting use_cache=False.`（是日志不是 `warnings`）。
7. 两个脚本都在本机跑通：`scripts/vram_ledger.py`（8B 全参 micro-batch 8 / seq 8192 →
   权重 14.90 + 梯度 14.90 + 优化器 89.41 + 激活 272.00 GiB；LoRA+检查点 → 18.49 GiB）、
   `scripts/dataset_overlap.py`（62 行合成语料：1 条精确重复、2 条近似重复、
   4 条评测里 3 条泄漏，退出码 1）。
8. `vllm run-batch` 确有 `--enable-metrics`（读上游
   `vllm/entrypoints/openai/run_batch.py`，`start_http_server(port=args.port, ...)`），
   `vllm serve` 没有。

### `[official]`——未在本机验证，仅对官方文档/官方 skill 核对

**本机无 GPU，以下全部无法实测，正文一律标 `[official]`：**

1. NVIDIA 的全部实测数字：TP 4→8 的 -28.4%、PP 4→8 的 -5.9%、`mlp` 重算的 ~16%、
   LoRA+SP re-gather 的 4.731 GB / -6.74%、峰值 58.8 vs 60.2 GB。
2. `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` 消除碎片化 OOM 的效果，及其与
   `--use-nccl-ub`、CUDA graph（`NCCL_GRAPH_REGISTER=0`）的不兼容。
3. CPU offload 与 PP>1 的 `ValueError`（读的是上游源码片段，未运行）。
4. 并行选型表（按模型规模/拓扑/序列长度）、`min_gpus = PP * max(TP*CP, EP*ETP)`、
   MoE 按 active 参数定 TP。
5. ZeRO 各级分片语义与 offload 的性能定位。
6. FSDP2 的五条契约（bottom-up、`model(x)`、分片后建优化器、
   `set_requires_gradient_sync`、DCP）——需要多进程 NCCL，单机 CPU 跑不出有意义的结论。
7. 激活显存公式（每 token 每层约 34×hidden 字节，源自 Megatron 的激活重算论文）；
   `scripts/vram_ledger.py` 的激活项是**模型形状估算**，不是 profile 结果。
8. 混合精度省 25–30% 而非 50%、bf16 相对 fp16 免 loss scaling。
9. vLLM 侧全部：KV cache 作为残值、chunked prefill 默认开、关闭时
   `max_num_batched_tokens > max_model_len` 的约束、RECOMPUTE 抢占、
   `cudagraph_capture_sizes`、`/metrics` 端点、各调参方向。
10. 量化侧全部：FP8/AWQ/GPTQ/NF4 的精度与吞吐取舍、校准集要贴近生产流量、
    QLoRA 相对 LoRA 的质量差、合并顺序。
11. 13-gram 污染判据的具体阈值选择（8–13）来自 GPT-3 附录 C 与 harness 文档；
    `scripts/dataset_overlap.py` 实现并在合成语料上跑通，但**没有在真实大语料上**
    验证过规模表现。
12. PyTorch 可复现性的各条（跨版本/跨平台不保证、`use_deterministic_algorithms` 的
    报错行为、cudnn.benchmark 的抖动）——`use_deterministic_algorithms` 的报错示例是
    CUDA 算子，本机无 GPU 无法触发。

### 未达成项 / 已知取舍

- **场景 2 与场景 4 在 opus-5 基线下零区分度**。没有改题也没有降低标准（两处 expected
  只做了一次事实性修正：把 vLLM metrics 那条从"不是 vLLM 参数"改成更精确的"不是
  `vllm serve` 参数"，因为 `--enable-metrics` 确实存在于 `vllm run-batch`）。区分度
  由场景 1、3 承担。
- **`NVIDIA/skills` 里没有任务书所说的 `skills/Megatron-Bridge/*` 与 `Model-Optimizer/*`
  目录**。实际存在的是 24 个 `nemo-mbridge-*` skill（Megatron Bridge 的性能与韧性主题），
  Model Optimizer 只以 `nemotron-customize/references/context/modelopt-optimization.txt`
  的形式出现，不是独立 skill。已改取前者，并在候选表 #23 记录后者的裁决。
- **`huggingface/skills` 里没有 `hugging-face-model-trainer` / `hugging-face-evaluation`**，
  对应的实际目录是 `huggingface-llm-trainer` 与 `huggingface-community-evals`。
- 量化一节没有本机实证。要验证 NF4/AWQ 的精度损失需要 GPU 与真实模型，本机不具备。
- 所有 references 均未写"仅 macOS"类平台限制——两个脚本是纯标准库，已在本机 Linux 跑通。

### 未来同步时要盯的上游

- `huggingface/trl`：GRPO 的默认值（`beta`、`loss_type`、`scale_rewards`）在 1.x 内仍在变，
  `references/api-versions.md` 的默认值表要跟着安装版重读，不能只跟文档。
- `huggingface/transformers`：5.x 仍在移除 4.x 遗留参数，「已移除参数」表需要每次同步复跑
  一遍构造式验证。
- `vllm-project/vllm`：V1 的默认值（chunked prefill、优化级别 `-O0..-O3`）变动频繁。
- `NVIDIA/skills`：该仓库每日从各产品仓库同步，`pushed_at` 天天在动；盯 `paths` 下的
  `nemo-mbridge-perf-*` 即可。
