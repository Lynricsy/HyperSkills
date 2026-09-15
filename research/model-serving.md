# model-serving 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 立项背景

用户先问「这个项目现在有关于模型部署、性能调优的技能吗」，澄清后确认问的是
**模型部署的性能调优**（推理服务侧）。复核既有覆盖后确认这是一个真实缺口：

- `skills/ml-training/references/inference-serving.md`（147 行）是全库唯一的推理服务文档，
  覆盖 vLLM 单机单卡的 KV cache 定容、`--max-model-len`、chunked prefill 的 token 预算、
  RECOMPUTE preemption 处方、`--enforce-eager` 代价、`/metrics` 路径、LoRA merge、
  以及 `references/quantization.md` 里量化对吞吐的真实收益。
- **缺的是**：压测方法论（全库 grep `bench` 只命中训练侧的基准污染与 `cudnn.benchmark`，
  零条推理压测内容）、服务侧并行判据、prefix caching 的量化决策、P/D 分离、
  投机解码、多副本扩缩信号、K8s GPU 推理编排、多引擎选型、GPU 侧可观测。
  没有「怎么测」，`inference-serving.md` 的全部调优方向都是无法验证的建议。
- `docs/roadmap.md:250` 曾把 `performance-profiling` 判为既有 skill 的子集而不立项。
  该结论对**通用性能剖析**仍然成立（分散在 `go`/`react`/`unity`/`redis` 等各生态 skill），
  但对**推理服务性能调优**不成立：它既不属于任何单一语言生态，也不是 `ml-training`
  的子集（`ml-training` 的 Scope 是「改权重」），更不是 `containers` 的子集。
  用户在获知三个选项（扩 `ml-training` / 独立立项 / 只做调研）后明确选择**独立立项**。

## 调研日期与检索途径

- 调研日期：2026-09-15
- 复核日期：2026-09-15
- 检索途径：
  - `gh search repos`：`vllm skill`、`inference serving skill`、`sglang skill`、`kserve skill`、
    `ray serve skill`、`bentoml skill`、`triton inference skill`、`llm benchmark skill`、
    `nvidia dynamo skill`、`tensorrt-llm skill`、`gpu kubernetes skill`、`llama.cpp skill`
  - `web_search`：`"SKILL.md" vLLM OR "inference serving" OR "LLM serving" agent skill github`
  - 领域官方组织仓库直查：`vllm-project/`、`sgl-project/`、`NVIDIA/`、`ai-dynamo/`、
    `amd/`、`google/`、`huggingface/`、`microsoft/`
  - **引擎仓库内嵌 skill 目录**（本轮最重要的发现途径）：用
    `gh api repos/<r>/git/trees/main?recursive=1` 过滤 `\.claude/skills/`、`\.agents/skills/`，
    在 `sgl-project/sglang`、`NVIDIA/TensorRT-LLM`、`ai-dynamo/dynamo` 三个引擎主仓库里
    找到了搜索引擎搜不到的 skill 群。`llm-d/llm-d`、`kserve/kserve`、`ray-project/ray`、
    `bentoml/BentoML` 经同样方法确认**没有** skill 目录。
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 已确认登录，配额 4944/5000）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。
新鲜度按**该文件最后一次提交日期**计算，不按仓库整体 push 日期。

### ai-dynamo/dynamo（8082★，pushed 2026-09-15，Apache-2.0）

主体许可经实读 `LICENSE` 确认为 **Apache-2.0**；GitHub API 报 NOASSERTION 的唯一原因是
Apache 正文前插了一段 NOTICE，声明 `./lib/llm/tests/data/deepseek-v3.2` 测试数据派生自
DeepSeek-V3.2 按 MIT 授权，其后原文写 "The rest of this codebase is licensed under the
Apache License 2.0 as described below."

**结构要点**：`.agents/` 下只有 `skills/` 一个子目录；SKILL.md 多为角色编排契约，
真正的工程判据下沉在**仓库根的 `agent-docs/rules/*` 与 `agent-docs/guides/*`**。
提取以 agent-docs 为主源、SKILL.md 为索引。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `.agents/skills/dynamo-frontend-benchmark` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/dynamo-frontend-benchmark/SKILL.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口1 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 全库压测方法论密度最高：闭环/开环、Little's law、拥塞崩溃膝点、压测端反成瓶颈、median+interleave 协议 |
| 2 | `agent-docs/rules/benchmarking/comparison-uncertainty.md` | https://github.com/ai-dynamo/dynamo/blob/main/agent-docs/rules/benchmarking/comparison-uncertainty.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口1 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 噪声底 n=3 pilot / MDE / CI 分离判据 / finalist 确认重测 / 冷热缓存策略 |
| 3 | `.agents/skills/analyze-aiperf-results` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/analyze-aiperf-results/SKILL.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口1 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 结果可信度审计清单：ISL/OSL 实测对账、warmup 剥离、工具版本分级可比性、bridging run |
| 4 | `agent-docs/guides/rate-matching/matching.md` | https://github.com/ai-dynamo/dynamo/blob/main/agent-docs/guides/rate-matching/matching.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口4 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | P/D 配比的唯一定量来源：prefill/decode 代理速率公式与 `P·R_p ≈ D·R_d` |
| 5 | `agent-docs/guides/knob-tuning/tuning-hierarchy.md` | https://github.com/ai-dynamo/dynamo/blob/main/agent-docs/guides/knob-tuning/tuning-hierarchy.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口2 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 推理侧 DP vs TP 判据（DP 缩小 per-rank batch 饿死计算）+「按各自 SLO 前沿比较配置族」 |
| 6 | `agent-docs/guides/knob-tuning/dynamo.md` | https://github.com/ai-dynamo/dynamo/blob/main/agent-docs/guides/knob-tuning/dynamo.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口5 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 路由/准入/队列/扩缩的「症状→knob→预期指标→验证→陷阱」五列表；Dynamo 专有但判据可跨引擎复述 |
| 7 | `.agents/skills/configure-aiperf-benchmark` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/configure-aiperf-benchmark/SKILL.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口1 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 实验三分类与「有 SLO→goodput / 无 SLO→Pareto」的目标函数选择；其余是产物管线 |
| 8 | `.agents/skills/find-serving-recipe` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/find-serving-recipe/SKILL.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口7 | 3 | 3 | 3 | 3 | 1 | 13 | INCLUDE | 跨引擎 recipe 目录与 DURABLE/VERSION-BOUND 二分；frontmatter 与正文 SPDX 冲突扣许可分 |
| 9 | `.agents/skills/dynamo-interconnect-check` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/dynamo-interconnect-check/SKILL.md | 8082 | 2026-09-15 | Apache-2.0（正文 SPDX 写 CC-BY-4.0） | 缺口2/4 | 3 | 3 | 3 | 3 | 1 | 13 | INCLUDE | UCX/NCCL 变量与不达标表现（落 TCP、无 `nvidia_peermem` 走 host 中转）；许可自相矛盾扣分 |
| 10 | `.agents/skills/consult-perf-knowledge` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/consult-perf-knowledge/SKILL.md | 8082 | 2026-09-15 | Apache-2.0 | 方法论 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | MDE/实际显著性阈值推导、探索-利用校准、证据门；backlog 台账是产品管线 |
| 11 | `.agents/skills/run-aiperf-benchmark` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/run-aiperf-benchmark/SKILL.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口1 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 「不得为让压测跑完而降载/删 trace 行/放宽 SLO」与邻居占用记录 |
| 12 | `.agents/skills/dynamo-kv-replay-parity` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/dynamo-kv-replay-parity/SKILL.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口1 | 3 | 3 | 2 | 3 | 2 | 13 | MAYBE | 只取 Stage 7 的统计协议（60 对配对 + 阶统计量无分布界 + 禁止剔除离群点）；其余强绑自有 replay harness |
| 13 | `.agents/skills/dynamo-router-starter` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/dynamo-router-starter/SKILL.md | 8082 | 2026-09-15 | Apache-2.0（正文 SPDX 写 CC-BY-4.0） | 缺口5 | 3 | 3 | 2 | 3 | 1 | 12 | INCLUDE | KV 事件缺失→近似模式的回退判据；**模式清单漏 `power-of-two`**（见裁决 R4） |
| 14 | `.agents/skills/troubleshoot-dynamo` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/troubleshoot-dynamo/SKILL.md | 8082 | 2026-09-15 | Apache-2.0（正文 SPDX 写 CC-BY-4.0） | 缺口6 | 3 | 3 | 2 | 3 | 1 | 12 | MAYBE | 只取自顶向下排查层序与三条通用症状映射 |
| 15 | `.agents/skills/create-optimization-hypothesis` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/create-optimization-hypothesis/SKILL.md | 8082 | 2026-09-15 | Apache-2.0 | 方法论 | 3 | 3 | 1 | 3 | 2 | 12 | MAYBE | 几乎全是自有 artifact 管线；真判据在它引用的 `agent-docs/rules/optimization/one-variable.md` |
| 16 | `.agents/skills/synthesize-user-workload` | https://github.com/ai-dynamo/dynamo/blob/main/.agents/skills/synthesize-user-workload/SKILL.md | 8082 | 2026-09-15 | Apache-2.0 | 缺口1 | 3 | 3 | 1 | 3 | 2 | 12 | MAYBE | 只取「fleet 流量必须换算到 per-unit 并确认」与「参数化描述是 preset 与 trace 之间的一等公民」 |

### NVIDIA/TensorRT-LLM（14626★，pushed 2026-09-15）

许可经实读 `LICENSE` 确认为 **Apache-2.0**（"This project is licensed under the Apache 2.0
license"），GitHub API 报 NOASSERTION 仅因含衍生代码段声明。每个 SKILL.md 的 frontmatter
亦写 `license: Apache-2.0`，按「明确开源」给 2 分。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 17 | `.claude/skills/perf-optimization-casebook` | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/perf-optimization-casebook/SKILL.md | 14626 | 2026-08-17 | Apache-2.0 | 缺口2/7 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 决策先例 schema 与 lossless/lossy 精度门跨引擎成立；含 attention-DP padding、EP all-to-all、shape-aware autotune 案例 |
| 18 | `.claude/skills/perf-host-analysis`（+ `references/metrics.md`、`thresholds.md`） | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/perf-host-analysis/SKILL.md | 14626 | 2026-05-20 | Apache-2.0 | 缺口8 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 把「GPU 空转是不是 host 的锅」做成 M1–M5 可计算指标 + 分相位阈值，缺口 8 最硬的一份 |
| 19 | `.claude/skills/perf-workload-profiling` | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/perf-workload-profiling/SKILL.md | 14626 | 2026-04-08 | Apache-2.0 | 缺口1 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 压测反模式与量化阈值（循环内 sync 10–50us、`data/iter > 0.2`、必须报 median/std） |
| 20 | `.claude/skills/perf-host-optimization` | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/perf-host-optimization/SKILL.md | 14626 | 2026-05-20 | Apache-2.0 | 缺口8 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | host 热点分类法、NUMA affinity 2x、「函数提速不等于吞吐提升」的停机准则 |
| 21 | `.claude/skills/perf-torch-cuda-graphs` | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/perf-torch-cuda-graphs/SKILL.md | 14626 | 2026-04-08 | Apache-2.0 | 缺口8 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 收益判据（<80% util + 大量 <50us kernel）、三条硬约束、capture 报错码表、mempool 共享 |
| 22 | `.claude/skills/perf-torch-sync-free` | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/perf-torch-sync-free/SKILL.md | 14626 | 2026-04-08 | Apache-2.0 | 缺口8 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 三个阻塞 driver API、`set_sync_debug_mode` 盲区、false/true dependency 分类、隐蔽 sync 源清单 |
| 23 | `.claude/skills/perf-analysis` | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/perf-analysis/SKILL.md | 14626 | 2026-08-17 | Apache-2.0 | 缺口8 | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE | 实质只剩瓶颈五分类表一条可合入；其余是 agent 委派礼仪 |
| 24 | `.claude/skills/perf-optimization` | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/perf-optimization/SKILL.md | 14626 | 2026-08-17 | Apache-2.0 | 方法论 | 3 | 3 | 1 | 3 | 2 | 12 | MAYBE | 评分虚高：90% 是 TileIR/CuTe/Triton 内部路由，可合入仅「>5% 回滚 + 一次一改」 |
| 25 | `.claude/skills/trtllm-serve-config-guide`（+ `references/knob-heuristics.md`） | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/trtllm-serve-config-guide/SKILL.md | 14626 | 2026-05-18 | Apache-2.0 | 缺口2 | 3 | 1 | 2 | 3 | 2 | 11 | INCLUDE（取 references） | SKILL.md 本体是仓库内查表流程；价值在 `knob-heuristics.md` 的 KV 公式与 ADP/chunked-prefill 判据 |
| 26 | `.claude/skills/perf-nsight-systems` | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/perf-nsight-systems/SKILL.md | 14626 | 2026-04-08 | Apache-2.0 | 缺口8 | 3 | 1 | 3 | **0** | 2 | 9 | INCLUDE（只抄方法，不抄命令行） | 时间线判读方法正确，但 `--python-backtrace=lbr` 与 `--backtrace=cuda` 两处与 nsys 官方 CLI 直接矛盾（裁决 R2） |
| 27 | `.claude/skills/perf-nsight-compute-analysis/references/roofline-analysis.md` | https://github.com/NVIDIA/TensorRT-LLM/blob/main/.claude/skills/perf-nsight-compute-analysis/references/roofline-analysis.md | 14626 | 2026-09-15 | Apache-2.0 | 缺口8 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | roofline 判定（AI<1 memory-bound / >10 compute-bound、ridge point、分层 roofline）；「点远低于两条 roof = latency/occupancy 问题」是 decode 的解释入口 |
| 28 | `docs/source/features/parallel-strategy.md` + `attention.md` + `feature-combination-matrix.html` | https://github.com/NVIDIA/TensorRT-LLM/tree/main/docs/source/features | 14626 | 2026-09-15 | Apache-2.0 | 缺口2/7 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 官方核实来源：TP 切 `num_heads`、`num_heads < TP` 时 KV 全量复制、`moe_tp × moe_ep == tp`、投机解码 × PP = No |

### vllm-project/vllm-skills（99★，pushed 2026-04-03，Apache-2.0）

仓库为 Claude Code plugin marketplace 形态；根 `LICENSE` 是 Apache-2.0 全文。
全仓库同一次推送，新鲜度一律 1 分（≤6 月）。**CLI 未过时**：对照 vLLM main 的
`vllm/benchmarks/serve.py` 与 docs.vllm.ai，`vllm bench serve` 及其引用的全部参数仍存在。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 29 | `plugins/vllm-skills/skills/vllm-bench-serve` | https://github.com/vllm-project/vllm-skills/blob/main/plugins/vllm-skills/skills/vllm-bench-serve/SKILL.md | 99 | 2026-04-03 | Apache-2.0 | 缺口1 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 官方 `vllm bench serve` 全参数表；抽查 `--request-rate`/`--burstiness`/`--percentile-metrics` 三条全对 |
| 30 | `plugins/vllm-skills/skills/vllm-prefix-cache-bench` | https://github.com/vllm-project/vllm-skills/blob/main/plugins/vllm-skills/skills/vllm-prefix-cache-bench/SKILL.md | 99 | 2026-04-03 | Apache-2.0 | 缺口3 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | `prefix_repetition` 四参数与 `benchmark_prefix_caching.py` 参数表逐条核实无误 |
| 31 | `plugins/vllm-skills/skills/vllm-deploy-k8s`（+ `templates/*.yaml`） | https://github.com/vllm-project/vllm-skills/blob/main/plugins/vllm-skills/skills/vllm-deploy-k8s/SKILL.md | 99 | 2026-04-03 | Apache-2.0 | 缺口6 | 3 | 1 | 2 | 3 | 2 | 11 | INCLUDE | 带真实 YAML 的探针预算（startupProbe 30×10s=330s）、dshm 80Gi、端口四处联动 |
| 32 | `plugins/vllm-skills/skills/vllm-deploy-docker` | https://github.com/vllm-project/vllm-skills/blob/main/plugins/vllm-skills/skills/vllm-deploy-docker/SKILL.md | 99 | 2026-04-03 | Apache-2.0 | 缺口6 | 3 | 1 | 2 | 3 | 2 | 11 | MAYBE | 无错但边际价值低：绝大部分是 docs.vllm.ai/deployment/docker 的复述，仅 `--ipc=host`/`--shm-size` 值得取 |
| 33 | `plugins/vllm-skills/skills/vllm-deploy-simple` | https://github.com/vllm-project/vllm-skills/blob/main/plugins/vllm-skills/skills/vllm-deploy-simple/SKILL.md | 99 | 2026-04-03 | Apache-2.0 | — | 3 | 1 | 0 | 3 | 2 | 9 | **REJECT（分数虚高）** | 内容是自有 `quickstart.sh` 子命令手册，属产品包装；可合入仅硬件后端探测信号 1 条 |
| 34 | `plugins/vllm-skills/skills/vllm-bench-random-synthetic` | https://github.com/vllm-project/vllm-skills/blob/main/plugins/vllm-skills/skills/vllm-bench-random-synthetic/SKILL.md | 99 | 2026-04-03 | Apache-2.0 | 缺口1 | 3 | 1 | 1 | **0** | 2 | 7 | MAYBE | 参数默认值表 4 处与官方文档矛盾（裁决 R1），内容又与 bench-serve 重复；只取其输出字段块 |

### sgl-project/sglang（35979★，pushed 2026-09-15，Apache-2.0）

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 35 | `.claude/skills/sglang-prod-incident-triage`（+ `references/`） | https://github.com/sgl-project/sglang/blob/main/.claude/skills/sglang-prod-incident-triage/SKILL.md | 35979 | 2026-09-15 | Apache-2.0 | 缺口3/4/5/8 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 端点名、字段名、判据阈值全具体；`/health_generate`、`/v1/loads`、`/set_trace_level` 已在 `http_server.py` 核实存在 |
| 36 | `.claude/skills/llm-torch-profiler-analysis` | https://github.com/sgl-project/sglang/blob/main/.claude/skills/llm-torch-profiler-analysis/SKILL.md | 35979 | 2026-06-26 | Apache-2.0 | 缺口1/7 | 3 | 2 | 3 | 2 | 2 | 12 | INCLUDE | 跨引擎（SGLang/vLLM/TRT-LLM）profiler 能力矩阵 + warmup/active 与 prefill/decode 工况契约 |
| 37 | `.claude/skills/clean-startup-log` | https://github.com/sgl-project/sglang/blob/main/.claude/skills/clean-startup-log/SKILL.md | 35979 | 2026-05-24 | Apache-2.0 | 缺口7 | 3 | 1 | 2 | 2 | 2 | 10 | INCLUDE（只取 reference log） | 主体是日志降噪工程流程（无用），底部那份 clean 启动日志是「启动日志里哪些行是性能信号」的现成素材 |
| 38 | `.claude/skills/sglang-runtime-context` | https://github.com/sgl-project/sglang/blob/main/.claude/skills/sglang-runtime-context/SKILL.md | 35979 | 2026-09-15 | Apache-2.0 | — | 3 | 3 | 1 | 2 | 2 | 11 | **REJECT（越界）** | SGLang 内部 RuntimeContext / config bags / read-ratchet，面向贡献者而非服务运维 |

### google/skills（19936★，pushed 2026-09-14，Apache-2.0）

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 39 | `skills/cloud/gke-ai-troubleshooting-handle-disruption-gpu-tpu` | https://github.com/google/skills/blob/main/skills/cloud/gke-ai-troubleshooting-handle-disruption-gpu-tpu/SKILL.md | 19936 | 2026-09-14 | Apache-2.0 | 缺口6 | 3 | 3 | 3 | 2 | 2 | 13 | INCLUDE | label/taint/PromQL 指标名与 60 min grace period 全是可执行判据 |
| 40 | `skills/cloud/gke-inference` | https://github.com/google/skills/blob/main/skills/cloud/gke-inference/SKILL.md | 19936 | 2026-09-14 | Apache-2.0 | 缺口6 | 3 | 3 | 2 | **1** | 2 | 11 | INCLUDE（限编排部分） | 加速器表/ComputeClass/冷启动可用，但**自动扩缩章节与 Google 自家最佳实践直接矛盾**（裁决 R3），必须改写 |
| 41 | `skills/cloud/gke-workload-scaling` | https://github.com/google/skills/blob/main/skills/cloud/gke-workload-scaling/SKILL.md | 19936 | 2026-09-14 | Apache-2.0 | 缺口5 | 3 | 3 | 2 | **1** | 2 | 11 | MAYBE | 通用 HPA/VPA 非推理特有；stabilization window 默认值写错（裁决 R3b）；只取 External-metric 判据与 HPA/VPA 指标冲突规则 |

### amd/skills（356★，pushed 2026-09-15，MIT）

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 42 | `skills/serving-llms-on-instinct` | https://github.com/amd/skills/blob/main/skills/serving-llms-on-instinct/SKILL.md | 356 | 2026-09-15 | MIT | 缺口9 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 缺口 9 核心：gfx 判据、显存预算分档、ROCm 专有陷阱；抽查 `CUDA_VISIBLE_DEVICES`→`HIP_VISIBLE_DEVICES` 与 ROCm 官方文档一致 |
| 43 | `skills/serving-llms-on-epyc` | https://github.com/amd/skills/blob/main/skills/serving-llms-on-epyc/SKILL.md | 356 | 2026-09-15 | MIT | 缺口9 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | CPU 推理「逃生口」成立条件极具体（AVX-512 门槛、单 socket 铁律、KV 按本 socket RAM）；`--device cpu` 已移除经官方文档核实 |
| 44 | `staging/rocm-doctor` | https://github.com/amd/skills/blob/main/staging/rocm-doctor/SKILL.md | 356 | 2026-09-15 | MIT | — | 3 | 3 | 1 | 1 | 2 | 10 | **REJECT（产品包装）** | 分数达标但内容是 `rocm` CLI 的薄驱动壳（安装命令 + 路由表），零可合入技术事实 |

### huggingface/skills（Apache-2.0）

内容自述 "last checked July 2026" 与 "TEI was added in late 2026" 自相矛盾（后者相对今天是未来），
**合入时不引用其中任何日期**，只取技术判据。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 45 | `skills/hf-cloud-serving-image-selection` | https://github.com/huggingface/skills/blob/main/skills/hf-cloud-serving-image-selection/SKILL.md | — | main | Apache-2.0 | 缺口7 | 3 | 2 | 3 | 2 | 2 | 12 | INCLUDE（重剪裁） | 缺口 7 最佳来源：TGI 归档判据、reranker 架构分流、TEI 支持集；SageMaker/ECR/AMI 部分全剔 |
| 46 | `skills/hf-cloud-sagemaker-production-defaults` | https://github.com/huggingface/skills/blob/main/skills/hf-cloud-sagemaker-production-defaults/SKILL.md | — | main | Apache-2.0 | 缺口5/6 | 3 | 2 | 3 | 2 | 2 | 12 | INCLUDE（重剪裁） | 只取 scale-to-zero 实测冷启动链路（首个 200 共 +9m24s）与「InService ≠ 可服务」探针陷阱 |
| 47 | `skills/hf-cloud-sagemaker-deployment-planner` | https://github.com/huggingface/skills/blob/main/skills/hf-cloud-sagemaker-deployment-planner/SKILL.md | — | main | Apache-2.0 | 缺口7 | 3 | 2 | 2 | 2 | 2 | 11 | MAYBE | 路径选择表有价值（实时/缩零/异步/批量判据），但绑 SageMaker 术语，需抽象 |
| 48 | `skills/huggingface-local-models` | https://github.com/huggingface/skills/blob/main/skills/huggingface-local-models/SKILL.md | — | main | Apache-2.0 | 缺口7 | 3 | 2 | 2 | 2 | 2 | 11 | MAYBE | 只用于划定 llama.cpp/GGUF 适用边界与量化档位 |

### NVIDIA/skills（3294★，pushed 2026-09-15，Apache-2.0）

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 49 | `skills/jetson-speculative-decoding` | https://github.com/NVIDIA/skills/blob/main/skills/jetson-speculative-decoding/SKILL.md | 3294 | 2026-09-15 | Apache-2.0 | 缺口4 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 投机解码的并发判据（≤2 有收益 / ≥8 连续批处理已饱和）、acceptance >0.6 才加 token 数、验收门（+30% 吞吐 / −20% TPOT，<10% 则撤） |
| 50 | `skills/jetson-inference-mem-tune` | https://github.com/NVIDIA/skills/blob/main/skills/jetson-inference-mem-tune/SKILL.md | 3294 | 2026-09-15 | Apache-2.0 | 缺口7 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 四引擎选型表与各自内存旋钮对应（vLLM/SGLang/llama.cpp/TensorRT）、量化名不可混用 |
| 51 | `skills/jetson-llm-benchmark` | https://github.com/NVIDIA/skills/blob/main/skills/jetson-llm-benchmark/SKILL.md | 3294 | 2026-09-15 | Apache-2.0 | 缺口1 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | warmup 必要性、并发 1/8 双点、**带宽饱和判据**（并发 8 的 tok/s 几乎不超单流 = bandwidth-bound）、可比性前提清单 |

### 已核查但不采用

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 52 | `av/skills` · `run-llms` | https://github.com/av/skills/blob/master/run-llms/SKILL.md | 15 | 2026-09-05 | MIT | — | 1 | 3 | 2 | 2 | 2 | 10 | **REJECT（产品包装）** | Harbor CLI 说明书；可迁移事实仅「Apple Silicon 用 Metal 后端、HF safetensors 生产服务用 vLLM」一句 |
| 53 | `cohere-ai/vllm-skills` | https://github.com/cohere-ai/vllm-skills | 6 | 2026-06-24 | Apache-2.0 | — | 1 | 2 | 2 | — | 2 | — | **REJECT（范围不符）** | 是 vLLM fork 的开发与 rebase 维护（editable CUDA 安装、本地测试、上游基线探测），不是生产服务 |
| 54 | `shen-shanshan/vllm-dev-skills` | https://github.com/shen-shanshan/vllm-dev-skills | 17 | 2026-09-14 | Apache-2.0 | — | 1 | 3 | 1 | — | 2 | — | **REJECT（范围不符）** | vLLM 贡献者开发流程与技术博客写作，非服务部署 |
| 55 | `open-infra-skills/infra-skills` | https://github.com/open-infra-skills/infra-skills | 140 | 2026-07-10 | Apache-2.0 | — | 1 | 2 | — | — | 2 | — | **REJECT（无相关内容）** | 全仓库唯一 skill 是 `optimize-musa-training`（摩尔线程训练优化），与推理服务无关 |
| 56 | `BarrenWardo/kserve-skills` | https://github.com/BarrenWardo/kserve-skills | 0 | 2026-05-29 | — | — | 0 | 1 | — | — | 0 | — | **REJECT（无权威）** | 0★、无许可、无内容量 |
| 57 | `microsoft/skills` · `microsoft-foundry/models/deploy-model{,/capacity}` | https://github.com/microsoft/skills | — | main | MIT | — | 3 | 3 | 2 | — | 2 | — | **REJECT（产品包装）** | Azure AI Foundry 的 PTU/TPM 容量与部署流程，属托管产品控制面 → 已由 `azure` skill 覆盖 |
| 58 | `Orchestra-Research/AI-Research-SKILLs` · `12-inference-serving/vllm` | https://github.com/Orchestra-Research/AI-Research-SKILLs | — | — | MIT | — | 1 | — | 2 | **0** | 2 | — | **REJECT（正确性 0，沿用既有裁决）** | `ml-training` 建设期已裁决：把 `--enable-metrics`/`--metrics-port` 当作 `vllm serve` 参数（实际只存在于 `vllm run-batch`），并复述无条件的「24x 吞吐」 |
| 59 | `llm-d/llm-d`、`kserve/kserve`、`ray-project/ray`、`bentoml/BentoML` | — | 4540 / 5908 / 43805 / 8841 | 2026-09 | Apache-2.0 | — | — | — | — | — | — | — | **无 skill 可取** | 用 git trees API 确认四个仓库均无 `.claude/skills` 或 `.agents/skills` 目录。`llm-d` 的 `guides/` 仍是 P/D 分离拓扑的重要文档来源（经 Dynamo 的 `find-serving-recipe` 转述），但不构成 skill 候选 |

**候选总数 59 行**（远超 Phase A 的 12 条下限），其中 INCLUDE 32、MAYBE 9、REJECT 8、
无 skill/仅作文档来源 10。

## 深度审查

### 1. `ai-dynamo/dynamo`（14 分 ×6）— 本主题的方法论主干

双层结构是这批候选里最容易踩空的地方：`.agents/skills/*/SKILL.md` 大多是角色编排契约
（inputs / workflow / artifacts / next_action 状态机），真正的工程判据在**仓库根的
`agent-docs/`**。全部 12 个 SKILL.md 都写 `Read agent-docs/rules/...` 这样的相对路径，
容易被误读成 `.agents/agent-docs/`；已用 contents API 确认 `.agents/` 下只有 `skills/`。

frontmatter 无 HyperSkills 禁用字段问题，但有三个文件（`dynamo-router-starter`、
`dynamo-interconnect-check`、`troubleshoot-dynamo`）的 frontmatter 写 `license: Apache-2.0`
而正文 SPDX 头写 `CC-BY-4.0`，与仓库 LICENSE 冲突。处理见裁决 R5。

与其他候选的重叠：`agent-docs/guides/knob-tuning/{vllm,sglang,tensorrt-llm}.md` 是引擎原生
knob 目录，与 `skills/ml-training/references/inference-serving.md` 大幅重叠，**未提取**；
只取 `tuning-hierarchy.md` 的「提升/降级判据」这一层（服务侧决策逻辑，现有 reference 没有）。

### 2. `NVIDIA/TensorRT-LLM`（14 分 ×3）— 缺口 8 的唯一硬来源

`perf-host-analysis` 把「GPU 空转到底是不是 host 的锅」做成了 M1–M5 可计算指标，并且
**诚实标注阈值是标定值而非常数**（来自 Llama 3.2 1B、TP=2、B200），与目视矛盾时以目视为准。
这种自我限定是高质量上游的标志，值得连同阈值一起合入。

`perf-nsight-systems` 是本批唯一正确性得 0 的官方文件：`--python-backtrace=lbr` 与
`--backtrace=cuda` 两处把 nsys 的两个不同开关的取值张冠李戴。**时间线判读方法可用，
命令行一律不抄**（裁决 R2）。

越界部分明确：`perf-torch-cuda-graphs` 的 Workflow 3–6（`make_graphed_callables`、
TE FP8 `_order` 流水线、MCore `CudaGraphManager`、optimizer 入图）是训练语境，
与 `ml-training` 重叠或越界，只取推理侧的 capture/replay 判据。

### 3. `vllm-project/vllm-skills`（12 分 ×2）— 缺口 1/3 的一级 CLI 来源

官方组织出品，`vllm bench serve` 的参数语义是压测方法论落地为命令的唯一权威。
值得注意的是它**自己内部就不一致**：`vllm-bench-serve` 的参数表全对，
而教程化的 `vllm-bench-random-synthetic` 有 4 处默认值错误（裁决 R1）。
同一仓库内的两份文档质量差这么多，说明不能因为「同属官方仓库」就整仓信任。

`vllm-deploy-simple` 是「分数虚高」的典型：权威 3 + 新鲜 1 + 正确 3 + 许可 2 = 9 分达到
INCLUDE 线，但具体性得 0——内容是自有 `quickstart.sh` 的子命令手册。**按产品包装剔除规则
覆盖评分结论判 REJECT**，并在此留档说明分数与可提取量不是一回事。

### 4. `sgl-project/sglang` · `sglang-prod-incident-triage`（14 分）— 第二引擎视角

这是唯一一份从**生产事故**视角写的候选，端点名、字段名、阈值全部具体且可在
`python/sglang/srt/entrypoints/http_server.py` 核实（`/health_generate` 647 行、
`/v1/loads` 826-834 行、`/set_trace_level` 1157 行）。它提供了 `cache_hit_rate` 作为一等指标
和「`/health` 绿但请求超时必须用 `/health_generate`」这两条 vLLM 侧没有的判据。

`sglang-runtime-context` 同仓但**越界**（内部配置架构，面向贡献者），REJECT。
同一仓库内 skill 的适用对象差异极大，必须逐个判而不是按仓库判。

### 5. `google/skills` · `gke-inference`（11 分）— 必须改写才能用

这是本轮最重要的**裁决对象**：它把 GPU duty cycle 作为 LLM 推理 HPA 的首选示范配置，
而 Google 自家的 GKE 推理最佳实践文档明确反对这件事。详见裁决 R3。
编排部分（ComputeClass、local SSD 模型缓存 + 预拉镜像）可用，扩缩章节按官方文档重写。

### 6. `amd/skills` 两个 serving skill（14 分 ×2）— 缺口 9 的唯一高质量来源

全部是可执行参数与失败模式，且把「什么时候 CPU 推理是合理选择」写成了硬门槛
（AVX-512/Zen4+、zentorch 仅 EPYC 9000 系）而不是含糊的「也可以考虑」。
`serving-llms-on-epyc` 的「一个实例只绑一个 socket」是跨厂商可复用的拓扑铁律。
同仓 `staging/rocm-doctor` 10 分但内容是 CLI 壳，REJECT。

### 7. `NVIDIA/skills` 三个 jetson skill（13–14 分）— 剔除 SKU 后判据通用

`jetson-speculative-decoding` 是**全库唯一**把投机解码的并发适用区间写成硬判据的来源
（≤2 并发有收益、≥8 并发连续批处理已饱和、acceptance >0.6 才值得加 token 数），
并给了可执行的验收门。Jetson 专有部分（Thor/Orin SKU、JetPack 版本、NVIDIA-AI-IOT 镜像、
`tegrastats`/`nvpmodel`）全部剔除，剩下的判据与数据中心 GPU 同样成立。
`jetson-llm-benchmark` 的「并发 8 的 tok/s 几乎不超过单流 = 内存带宽饱和」是一条
极高价值的粗判据，与 TRT-LLM 的 roofline 判定互为印证。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| R1 | `vllm bench serve` 的参数默认值 | `vllm-bench-random-synthetic` 写 `--backend` 默认 `vllm`、`--num-prompts` 默认 `10`、`--max-concurrency` 默认 `Auto`、`--endpoint` 默认「`/v1/completions` 或 `/v1/chat/completions`」；`vllm-bench-serve` 与官方文档写 `openai` / `1000` / 无默认值（不限并发）/ `/v1/completions` | **采用官方文档与 `vllm-bench-serve`**。四处全部按官方写。特别是「`--max-concurrency` 无 `Auto` 档」与「`--endpoint` 唯一默认是 `/v1/completions`」——后者正是 `URL must end with chat/completions` 高频报错的成因 | docs.vllm.ai `/cli/bench/serve/`；`vllm/benchmarks/serve.py` |
| R2 | nsys 的 backtrace 开关取值 | `perf-nsight-systems` 给 `--python-backtrace=lbr` 与 `--backtrace=cuda` | **两处都不采用**。`--python-backtrace` 合法取值只有 `cuda`/`none`；`--backtrace` 合法取值是 `auto`/`fp`/`lbr`/`dwarf`/`none`；捕获 CUDA API 调用栈的开关是 `--cudabacktrace`。本仓库 reference **只写时间线判读方法，不写 nsys 命令行** | Nsight Systems User Guide，CLI Profile Command Switch Options 表 |
| R3 | 推理服务该按什么指标自动扩缩 | `gke-inference` 把 GPU duty cycle（`gpu_duty_cycle`，target 80）作为首选示范，并把 "Use DCGM metrics for GPU utilization" 列为 best practice 第 1 条，队列深度仅列第 4 条 "consider"；GKE 官方推理扩缩最佳实践把 **server metrics（queue size / batch size）** 列为推荐信号 | **采用 GKE 官方文档，判 `gke-inference` 该章节为错误**。正文只写 server metric：queue size（`vllm:num_requests_waiting`，阈值起步 3–5）用于「在延迟阈值内最大化吞吐」，batch size（`vllm:num_requests_running`）用于「queue 反应不够快的更紧延迟目标」。同时写明 GPU utilization 为何不行：它只测 duty cycle，不测活跃期间做了多少工作，因此无法把延迟/吞吐映射到某个利用率阈值 | https://docs.cloud.google.com/kubernetes-engine/docs/best-practices/machine-learning/inference/autoscaling ；Google Cloud 官方博客原文 "we do not recommend using GPU utilization for autoscaling inference workloads" |
| R3b | HPA stabilization window 默认值 | `gke-workload-scaling` 写「默认 5 分钟」 | **采用官方值**：scale-down 300s、**scale-up 0s**。对推理服务这个区别是决定性的——scale-up 默认没有稳定窗口，而 LLM 权重加载是分钟级，必须显式加长 scale-up 窗口否则必然抖动 | 同 R3 来源 |
| R3c | 按平台监控指标扩缩用哪种 metric 类型 | 同仓 `gke-inference` 用 `type: Pods` 自定义指标示例；`gke-workload-scaling` 说 GKE 推荐 **External** metric（控制面原生支持，不需 Custom Metrics Adapter） | **采用 `gke-workload-scaling` 的说法**（同仓两份自相矛盾，取与官方 how-to 一致的一方），并按官方路径写：server metrics → Managed Service for Prometheus → Adapter → HPA，per-pod 指标配 `AverageValue` target | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/machine-learning/inference/autoscaling |
| R4 | 路由模式全集 | `dynamo-router-starter` 列 6 个模式，漏 `power-of-two`；同仓 `agent-docs/guides/knob-tuning/dynamo.md` 列全 7 个 | **采用 7 个的版本**（已对源码 `ROUTER_MODE_MAP` 核实）。power-of-two-choices 恰是负载均衡最常推荐的默认策略，漏掉它会让读者以为只能在 round-robin 与 KV 之间二选一 | `components/src/dynamo/common/configuration/groups/router_args.py` `ROUTER_MODE_MAP`；`lib/llm/src/entrypoint/input/common.rs` |
| R5 | Dynamo 三个文件的许可 | frontmatter `license: Apache-2.0`，正文 SPDX 头 `CC-BY-4.0`，仓库 LICENSE 为 Apache-2.0 且未给这三个文件设例外 | **按更严格的一方处理**：这三个文件按 CC-BY-4.0 对待（需署名），在 `SOURCES.yaml` 的 `notes` 中记录该冲突。它们贡献的事实本就全部重写，无逐字复制 | 仓库 `LICENSE`；三个文件的 SPDX 头 |
| R6 | 并发扫描每点的请求数上界 | `agent-docs/rules/benchmarking/concurrency-grid.md` 同时要求「每点请求数至多为并发的 4 倍」与「请求数过少无法支撑噪声底与比较规则」——在 c=1..8 段落，4× 上界只给出 4–32 个请求，既算不出稳定 p99 也填不满同文档要求的 30 分钟窗口 | **只采纳下界与理由记录，不采纳 4× 上界**。本仓库表述为：下界是并发数本身（槽位填不满连一个完整 batch 都组不出），上界由测量窗口决定；另采用 vLLM 侧「生产型压测 `--num-prompts >= 100`」作为实际下限 | 同一份 `concurrency-grid.md` 内两条约束打架，对照 `comparison-uncertainty.md` |
| R7 | 投机解码的适用区间 | `jetson-speculative-decoding` 给并发硬判据（≤2 有收益、≥8 通常净损失）；Dynamo `tuning-hierarchy.md` 说「低到中等并发 decode 受限时提升，高并发吞吐优先时降级」；TRT-LLM casebook 从瓶颈信号角度说「接受率低或 draft forward 暴露在关键路径」 | **三方一致，合并为一条**：按「并发区间 + 瓶颈方向 + 实测接受率」三重判据写，并采用 Jetson 的可执行验收门（并发 1 与生产并发两点都测，<10% 则撤）。Jetson 的 Thor/Orin SKU 与 `num_speculative_tokens` 起步值（Thor 5 / Orin 3）作为硬件相关值剔除，只留「acceptance >0.6 才值得加 token 数」 | 三个官方上游互不矛盾，取交集并保留最可执行的表述 |
| R8 | 阈值该不该写成固定数字 | TRT-LLM `thresholds.md` 明确标注阈值标定自 Llama 3.2 1B/TP=2/B200，与目视矛盾时以目视为准；多数其他上游直接给数字 | **采用 TRT-LLM 的自限定做法**：本仓库 reference 写阈值时一并写明它是标定值、标定条件、以及重标条件。这与 `docs/skill-standard.md` 的置信度标注要求一致 | TRT-LLM `perf-host-analysis/references/thresholds.md` |
| R9 | `enable_prefix_caching` 的默认值 | `vllm-prefix-cache-bench` 以「对比有无 `--enable-prefix-caching`」为 A/B 方法，未说明默认值 | **补上默认值**：vLLM 当前 `CacheConfig.enable_prefix_caching` 默认 `True`，所以加该 flag 等于 no-op，真正改变行为的是 `--no-enable-prefix-caching`。基线必须显式关闭 | `vllm/config/cache.py:126` |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `dynamo` | `ai-dynamo/dynamo`（`.agents/skills/` + `agent-docs/rules/` + `agent-docs/guides/`） | merged | 闭环压测的 Little's law 解释、拥塞崩溃、压测端反成瓶颈判据、噪声底 n=3 pilot 与 MDE、CI 分离判据、finalist 确认重测、缓存状态与邻居占用策略、工具版本可比性分级、SLO 前沿比较、P/D 配比方程、推理侧 DP vs TP 判据、interconnect 验证清单、KV-aware 路由与队列准入、按角色分开的扩缩信号、单变量与证据门方法论 |
| `trtllm` | `NVIDIA/TensorRT-LLM`（`.claude/skills/perf-*` + `docs/source/features/`） | merged | GPU 空转的 host 归因（M1–M5 指标与分相位阈值）、瓶颈五分类签名、roofline 判定与「远低于两条 roof = latency/occupancy」、CUDA graph 收益判据与三条硬约束与 capture 报错码、CPU-GPU 同步点清单、TP 切 `num_heads` 与 `num_heads < TP` 时 KV 全量复制、每 token KV 公式、`moe_tp × moe_ep == tp`、投机解码 × PP 不兼容、NUMA affinity 2x |
| `vllm-skills` | `vllm-project/vllm-skills` | merged | `vllm bench serve` 的参数语义与默认值（`--request-rate inf`、`--num-warmups 0`、`--percentile-metrics` 不含 e2el）、TPOT/ITL/E2EL 口径、`--goodput` 从 SLO 反推、`--ramp-up-strategy`、`prefix_repetition` 四参数与命中率解析式、`--disable-shuffle`/`--no-oversample` 的必要性、权重加载期探针预算与 dshm |
| `sglang` | `sgl-project/sglang`（`.claude/skills/`） | merged | 第二引擎视角的生产信号：`cache_hit_rate` 作为一等指标、`/health` 绿而 `/health_generate` 才能抓住卡死 scheduler、`token_usage` 接近 1.0 = KV 饱和、启动日志里的性能信号行、跨引擎 profiler 能力矩阵与 warmup/active 契约 |
| `amd-skills` | `amd/skills` | merged | ROCm/Instinct 差异（`HIP_VISIBLE_DEVICES` 映射与空串隐藏全部 GPU、gfx 精度原生性、MLA 需 `--block-size 1` 否则静默回落）、显存预算分档公式、首请求 HIP kernel 编译 40–45s、CPU 推理成立条件与单 socket 铁律 |
| `google-skills` | `google/skills`（`skills/cloud/`） | merged | GPU/TPU 节点中断的预告信号三连与防护三件套（`terminationGracePeriodSeconds` 最长 60 min）、ComputeClass 声明加速器、local SSD 模型缓存 + 预拉镜像。**扩缩章节按 GKE 官方文档重写，不采用其 GPU duty cycle 主张** |
| `hf-skills` | `huggingface/skills` | merged | TGI 已归档的选型判据、reranker 两类架构分流与 `config.json` 预检、TEI 支持集是编进镜像的固定集合、scale-to-zero 的实测冷启动代价链路、「InService/ping 通 ≠ 可服务」 |
| `nvidia-skills` | `NVIDIA/skills`（`skills/jetson-*`） | merged | 投机解码的并发适用区间与验收门、四引擎选型表与内存旋钮对应、量化名不可混用、warmup 必要性、「并发 8 的 tok/s 不超单流 = 内存带宽饱和」 |
| `gke-docs` | GKE 推理最佳实践与 how-to 文档 | merged | 推理扩缩的 server metric 优先级与阈值标定法、queue size 只跟踪 pending 的硬限制、HPA tolerance 默认 0.1、stabilization window 默认值、`DCGM_FI_DEV_GPU_UTIL` 只测 duty cycle、`DCGM_FI_DEV_FB_USED` 不回落故不能用于缩容 |
| `vllm-docs` | vLLM 官方文档与 `vllm/benchmarks/serve.py` | merged | 裁决 R1/R9 的权威依据；`client_queue_time` 与 `e2el_including_client_queue` 只在设了 `--max-concurrency` 时计算、`--probe-request-rate` 的队头阻塞证据、prefix cache 命中率计数器单位是 token 而非请求 |
| `nsys-docs` | Nsight Systems User Guide | reference | 裁决 R2 的依据；本仓库只写时间线判读方法，不写 nsys 命令行 |
| `rocm-docs` | ROCm 官方文档（GPU isolation） | reference | 核实 `CUDA_VISIBLE_DEVICES` 在 AMD 平台等效于 `HIP_VISIBLE_DEVICES` |

## 基线缺口

### 第一轮（Claude Opus 5 / medium）——**已作废，仅作背景**

2026-09-15 先用 `anthropic/claude-opus-5 --thinking medium` 跑了一轮 `--baseline`，
4 场景全部 `status=ok`、`skill_read=false`。这一轮的**逐条评分作废**，原因是三处出在
我这边、而不是出在被测模型那边的问题。如实记录，因为它们正是本 skill 要教的东西：

| # | 我的判定 | 实际 | 为什么我判错 |
|---|---|---|---|
| 1 | 判基线「`ready_check_timeout_sec` 默认 600」为错误陈述 | **在夹具当时声明的 vLLM 0.11.0 上，基线是对的**：`--ready-check-timeout-sec` 的 argparse `default=600`，help 原文「(default: 600 seconds / 10 minutes). If set to 0, the ready check will be skipped.」 | 我拿 `main` 分支的 `default=0` 去判一个声明了 0.11.0 的夹具。**这个默认值在版本之间反转了**——0.29.0 与 main 都是 `0`（跳过）。该反转本身已写进 `references/benchmarking.md`，并给正文加了版本锚点 |
| 2 | 判基线的 `vllm:prefix_cache_hits_total` / `..._queries_total` 为「多了 `_total` 后缀」 | **基线是对的**：这两个指标在 vLLM 里用 `self._counter_cls` 声明，而 `prometheus_client` 渲染 `/metrics` 时给每个 Counter 追加 `_total`，Gauge 原样暴露 | 我拿**构造器里的 name** 当成了 PromQL 里的时间序列名。本机复现：`Counter('vllm:prefix_cache_hits')` → `vllm:prefix_cache_hits_total`；`Gauge('vllm:gpu_cache_usage_perc')` → 原名。这条规律（以及它为何解释 `num_preemptions_total` 带后缀而 `num_requests_waiting` 不带）已写进 `references/kv-reuse-and-routing.md` |
| 3 | 把「基线完全没回应 `nvidia-smi` 95-99% 那句」记成真实缺口 | **夹具当时根本没有那句话**——我在前一次用 `edit` 重写结果表时，把紧跟结果表的那两行一并覆盖掉了 | 基线不可能反驳一句不存在的话。该句已补回夹具 |

另外，`--num-warmups` 在 0.11.0 **不存在**（0.29.0 才有，`default=0`），所以当时那条
关于 warmup 默认值的 `expected_behavior` 在夹具声明的版本上根本不成立。

### 夹具与版本对齐（第二轮之前做的修正）

根因是**夹具声明 vLLM 0.11.0，而我的 `expected_behavior` 与 reference 都按当前版本写**。
两者必须一致。决定把夹具对齐到当前稳定版 **v0.29.0**（`gh api repos/vllm-project/vllm/releases/latest`
→ `v0.29.0`，2026-09-09），而不是把正文降级到一个一年前的版本——skill 要教的是当前的正确做法。

随后对 `references/benchmarking.md` 引用的**每一个** flag 逐一核实 v0.29.0：

| 事实 | v0.29.0 | v0.11.0（对照） |
|---|---|---|
| `--ready-check-timeout-sec` | `default=0`（跳过） | `default=600` |
| `--num-warmups` | `default=0` | **不存在** |
| `--request-rate` | `default=inf`，help「all the requests are sent at time 0」 | 同 |
| `--burstiness` | `default=1.0` | 同 |
| `--percentile-metrics` | `default=None`，未指定时生成式模型解析为 `ttft,tpot,itl`、pooling 为 `e2el`；合法名仅四个 | `default="ttft,tpot,itl"` |
| `--metric-percentiles` | `default="99"` | 同 |
| `--goodput` | `nargs="+"`，help「separated by spaces」，合法 key 仅 `ttft`/`tpot`/`e2el` | 同 |
| `--probe-request-rate` | `default=0.0`，存在 | **不存在** |
| `--backend` / `--endpoint` | `"openai"` / `"/v1/completions"` | 同 |
| `--num-prompts` / `--seed` | `DEFAULT_NUM_PROMPTS`（模块 docstring 写 1000）/ `0` | 同 |
| `--dataset-name` | `default="random"`，14 个 choices（含 `prefix_repetition`、`timed_trace`） | 集合更小 |
| `--random-range-ratio` / `--random-prefix-len` | `"0.0"` / `0`，均在 `vllm/benchmarks/datasets/datasets.py` | **均不存在** |
| `--no-oversample` / `--disable-shuffle` | `store_true`，均存在 | **均不存在** |
| `client_queue_time` / `e2el_including_client_queue` | **不存在**（仅 `main` 有） | 不存在 |
| `benchmarks/benchmark_prefix_caching.py` | 存在 | 存在 |

据此修正了 reference 三处：ready-check 改为版本敏感表述并保留「函数签名 600 vs argparse 0」
这个二阶陷阱；删掉 `client_queue_time` 那段（`main`-only），改写为「`--max-concurrency`
压住的客户端排队时间落在 E2EL 之外」这个与版本无关的判据；补上 `--random-prefix-len`
（这是 Phase A 调研报告漏掉的事实，反而是第一轮基线用对了的）。

### 第一轮仍然有效的观察（**必须保留**，避免正文重复写模型已会的内容）

评分作废，但这些观察与版本无关，直接决定正文不该写什么：

- **场景 1**：从 `duration ≥ max(e2e)` 反推出结果表**内部不自洽**——
  `8.104 + 511 × 0.03102 = 23.96 s > 17.54 s`，据此判定三个量不可能来自同一次运行、
  吞吐被高估约 37%。这比我设计的任何一条 `expected_behavior` 都强，是我没想到的攻击角度。
- **场景 1**：注意到 `Total generated tokens = 102400` 恰好等于 200 × 512，
  在没有 `--ignore-eos` 时不可能，判断是按配置回填的。
- **场景 3**：指出 `maxReplicas: 16` 在 4 节点 × 1 卡的拓扑上**物理不存在**，
  现有 `maxReplicas: 8` 就已经有 4 个 Pod 永久 Pending。
- **场景 3**：指出把 target 从 80 降到 60 会让该指标**永久**高于目标，
  于是 HPA 永久顶上限、抖动「消失」成 `minReplicas == maxReplicas` 的假象。
- **场景 4（负例）**：从 `3.52 GiB ÷ 4 bytes ÷ 128256 vocab = 7367 tokens` 反推出
  失败分配正是长尾样本在交叉熵前 `logits.float()` 的 fp32 上采样，并给出
  `use_liger_kernel` 融合 linear+CE 直接消掉这块；全程未越界到推理服务侧。

一条经核实成立的基线错误（与版本无关，正文应避免）：`--goodput ttft:2000,tpot:60`
用逗号分隔。该参数是 `nargs="+"`，逗号会让整串作为一个 token 传入并解析失败。

### 第二轮（被测 `openai/gpt-5.6-sol` / medium）

用户在本轮中途指定被测模型改为 `gpt-5.6-sol:medium`。按 `docs/workflow.md`
「基线与『有 skill』都用它，两次运行才可比」，两侧统一用
`--model openai/gpt-5.6-sol --thinking medium` 重跑；波次 11 已有同样的临时覆盖先例。
第一轮的 Opus 5 结果只作背景，不参与增益判定。

#### 第一次跑（`/tmp/hs-ms-sol`）--**夹具与判据都被这一轮否证，已修，需重跑**

4 场景全部 `status=ok`、`skill_read=false`。逐条判定 32 条：**14 达成 / 15 部分 / 3 未达成**。
但这一轮最有价值的产出不是分数,而是它暴露的**我自己的四处缺陷**--两处在夹具,两处在判据:

| # | 缺陷 | 证据 | 修法 |
|---|---|---|---|
| 1 | `bench/bench-report.md` 的数字**自相矛盾** | duration 17.54 s,但 mean TTFT 8.104 s + 511 × mean TPOT 31.02 ms = **23.96 s** 的隐含平均端到端延迟已超过整场时长。两个不同模型(Opus 5 与 gpt-5.6-sol)都**优先**攻击这一点并花掉大量篇幅 | duration 改 42.13 s,派生量同改(req/s 4.75、output 2430.62、total 4861.24 tok/s),P99 TPOT 降 47.02 ms 使最慢请求 41.33 s ≤ duration。容量结论随之从「3 卡」改「7 卡」,query 与 EB10 同步 |
| 2 | 场景 3 EB4 要求 `scaleUp.stabilizationWindowSeconds` **长于**冷启动 | 基线给的是 `scaleUp: 0` + `scaleDown: 900`,并说明扩容要快、缩容要慢。这在突发到达下是**更正确**的工程判断,我的判据把它判成不达标 | 改为「显式 `behavior:` 块 + 缩容窗口越过冷启动(300 s 默认 < 281 s 启动正是副本刚可用就被摘掉的原因),扩容侧不得被限流到失效」 |
| 3 | 场景 4 EB2 把 `packing` 与 8-bit optimizer 列为本例补救 | 基线明确**反对** `packing`,理由是 `per_device_train_batch_size=1` 时本就没有批内 padding 可省,把短样本拼到 8192 只会让高显存步骤变多。这个推理是对的 | EB2 删去 `packing`/8-bit 推荐,改为要求答案**识别** packing 在 batch=1 下不降峰值;补入 length-grouped batching |
| 4 | 场景 4 EB3 把 `expandable_segments` 说成「换硬件前最便宜的第一步」 | 进程已占 77.26 / 79.15 GiB,碎片不是主因;基线把它降级为「只能作为辅助」 | EB3 改为「提及但保持次要:真实激活峰值必须先降下来,分配器参数单独做不到」 |

**评测设计教训(第二条,与 containers 侧那条并列)**:夹具里的数字必须**先自洽**。
一处算术矛盾会变成注意力陷阱--被测模型会把主要篇幅投向「数据不可信」,
而没有任何一条 `expected_behavior` 要求它这么做,于是其余判据的达成率被系统性压低。
写夹具时必须像跑真实工具一样验算派生量(req/s、tok/s、隐含 e2e ≤ duration)。

这一轮仍然有效的缺口信号(修夹具不影响这些,它们与那处矛盾无关):

| 场景 | 未达成 / 缺失机制 | 基线原文与缺口 |
|---|---|---|
| 1 | EB5 `--ignore-eos` | 完全未提;输出长度只是上限、跨配置不可比这一点没有进入视野 |
| 1 | EB2/6/7/8/9 全部只到「部分」 | warmup 只说「热身完成后再测」,无 `--num-warmups` 默认 0 与 ready check 默认跳过;`nvidia-smi` 只说「GPU 很忙」,无 memory-bound 机制、无三个 vLLM 指标;测法只说「跑有限速率」,无 `--goodput` / ramp-up / `--burstiness`;prefix caching 只说「要对齐」,没认定它是一阶杠杆、也没说 `random` 数据集测不出;噪声底只说「多跑几次」,无 `--save-result`/`--metadata` |
| 2 | EB6 推测解码只缩 decode、**不可能**改善 TTFT | 答案列了 TTFT 恶化 104% 却没指出干预瞄错指标--这正是该场景的核心机制 |
| 2 | EB7 700-token 固定系统提示 -> prefix caching 才是杠杆 | **完全未提 prefix caching**;与场景 1 EB8 同向缺失,说明这是稳定缺口而非偶然 |
| 2 | EB2/4/8 部分 | 有全部数字与「KV 抢占是瓶颈」的结论,但没有「draft 权重占的显存来自 KV cache -> preemption 重算 -> TTFT 翻倍」这条机制链;acceptance 要测但无 ~0.6 阈值;无量化撤回门 |
| 3 | EB1/3/5/7 部分 | utilization 恒高的**原因**(decode 受显存带宽约束)缺失;冷启动只给 4m41s 总量,未拆 checkpoint load 与 KV profiling + graph capture;探针只说「缺 startupProbe」,未算 25 s 预算 vs 281 s;140 GB 权重只提 I/O 争用,无 NVMe / node-local cache / 烤进镜像 |
| 4（负例） | **5/5 达成** | 全程在训练侧(activation checkpointing、FlashAttention、`max_length`、activation offloading),未越界到 KV cache / `--max-model-len` / prefix caching / 压测。负例边界正确 |

缺口集中在四处,恰好是三份 reference 的主体:压测参数层与到达模型(`benchmarking.md`)、
prefix caching 作为一阶杠杆与命中率读法(`kv-reuse-and-routing.md`)、
「推测解码只作用于 decode」与并发适用域(`benchmarking.md` + `parallelism-and-topology.md`)、
以及 utilization 为何不是饱和信号(三份都涉及)。

#### 第二次跑(修正后的最终基线)

夹具与判据修正后重跑:场景 1/2/4 用 `/tmp/hs-ms-sol2`;场景 3 的夹具在第二次跑里又被
否证一次(见下),单独第三次跑 `/tmp/hs-ms-sol3`。全部 `status=ok`、`skill_read=false`。

| 场景 | 达成 | 部分 | 未达成 | 修正前 |
|---|---|---|---|---|
| 1 压测报告签核(10 条) | 3 | 6 | 1 | 2 / 7 / 1 |
| 2 推测解码回归(9 条) | 5 | 2 | 2 | 4 / 3 / 2 |
| 3 HPA 与冷启动(8 条) | 6 | 2 | 0 | 3 / 5 / 0 |
| 4 训练 OOM(负例,5 条) | 5 | 0 | 0 | 5 / 0 / 0 |
| **合计 32 条** | **19** | **10** | **3** | 14 / 15 / 3 |

**场景 3 夹具的第二处缺陷(第二次跑暴露,已修)**:原夹具写「HPA 在 2 和 8 之间双向
`SuccessfulRescale`」,同时写「`DCGM_FI_DEV_GPU_UTIL` 恒为 88-96%」而 target 是 80。
这两句不可能同时成立--指标恒高于 target 时 HPA 只会扩容,不会缩到 2。基线把它列为
「一个必须调查的不一致」并花掉一整节,说明夹具缺的是**因果链**而不是数字。
修法保留了「utilization 恒高」这个教学点(它是真实的:vLLM decode 下低并发也接近满),
改为真实机制:`SuccessfulRescale` 全为扩容方向,副本回落到 2 是 liveness 在权重加载期
杀容器导致 available 塌陷(补入 `4 Running + 4 Pending` 与 `RESTARTS 3-7` 证据),
`maxReplicas: 8` 对 4 节点池本就留 4 个永久 Pending。EB4 随之从「显式 `behavior:` 块」
改成「纠正前提:HPA 没有在缩容」--这才是该场景未被陈述的核心问题。
修正后基线第 35-37 行完整推出了这条链,EB4 达成。

**两次修正的共同教训**:夹具的**算术**与**因果**都必须先自洽。不自洽处会成为注意力陷阱,
被测模型合理地把篇幅投向「这份材料本身不可信」,而没有任何 `expected_behavior` 要求它
这么做,于是其余判据被系统性压低。场景 3 修正前后同一模型同一判据集从 3/5/0 变 6/2/0,
差值全部来自夹具可推理性,与 skill 无关。

### 稳定缺口(两轮一致,reference 必须承载)

| 缺口 | 证据 | 落点 |
|---|---|---|
| `--ignore-eos` 与跨配置可比性 | 场景 1 EB5 两轮均未达成,完全未进入视野 | `benchmarking.md`「Output length is uncontrolled unless…」 |
| 推测解码只作用于 decode,**不可能**改善 TTFT | 场景 2 EB6 两轮均未达成:两次都列出 TTFT 恶化 104% 却没指出干预瞄错指标 | `benchmarking.md` 推测解码段 + SKILL.md Core rule 18 |
| prefix caching 是共享前缀负载的一阶杠杆 | 场景 2 EB7 两轮均未达成(700-token 固定系统提示完全未被识别);场景 1 EB8 两轮均只到「部分」 | `kv-reuse-and-routing.md` 全文 + Core rules 15-17 |
| 压测参数层 | 场景 1 EB2/3/6/7/9 全部「部分」:warmup 只说「热身后再测」无 `--num-warmups` 默认 0 与 ready check 默认跳过;E2EL 会自己补算但不知道 `--percentile-metrics` 默认不含它;测法有 sweep 与 goodput 概念但无 `--goodput` 语法/ramp-up/`--burstiness` 仅在有限速率生效;零方差只说「固定」不知 `--random-range-ratio` 默认 0 | `benchmarking.md` |
| decode 受显存带宽约束 -> utilization 恒高的**原因** | 场景 1 EB6、场景 3 EB1 两轮四次全部「部分」:结论都对,机制从未出现 | 三份 reference + Core rule 10 |
| 冷启动分项与 acceptance 阈值 | 场景 3 EB3「部分」(只给 4m41s 总量,未拆 checkpoint load 与 KV profiling + graph capture);场景 2 EB4「部分」(要测 acceptance 但无 ~0.6 阈值) | `benchmarking.md` + Core rule 19 |

基线已经很强的部分(**正文不得重复**):`--request-rate inf` 的语义与「SLO 不能从结果倒推」、
`--max-model-len` 与 p99 prompt 的不兼容、KV 抢占的完整因果链、`--gpu-memory-utilization`
0.97 的余量风险、单流观测不能代表队列行为、探针语义拆分与 readiness 假阳性、
权重存储是冷启动主项、以及负例边界(训练 OOM 不越界到推理服务,两轮 5/5)。

## 评测工具缺陷：夹具存在但未在提示中指明（2026-09-15，已修）

`tools/run_evals.py` 原实现把 `scenario.files` 里的夹具 `shutil.copy2` 到工作目录，
但 `omp -p` 的提示只有 `scenario["query"]`--**文件名与内容都不在提示里**。
于是「模型有没有自己去翻工作目录」成了一个隐藏随机变量，而它单独决定了答案形态：
读到夹具的轮次能引用真实数值，没读到的只能给条件分支式回答，
两者却被当成同一个输入下的对照来比较。

逐轮审计（`events.jsonl` 里对夹具文件名的引用次数）：

| 运行 | 模式 | 场景 | fixture-refs | 判定可用性 |
|---|---|---|---|---|
| `hs-ms-sol2` | 基线 | 1 / 2 / 3 / 4 | 23 / 27 / 19 / 29 | 全部有效 |
| `hs-ms-sol3` | 基线 | 3 | 20 | 有效 |
| `hs-ms-skill` | 有 skill | 1 / 2 / 3 / 4 | 38 / **0** / **0** / **0** | 只有场景 1 有效 |
| `hs-ms-skill2` | 有 skill | 1 / 2 / 3 / 4 | 23 / 19 / **0** / **0** | 场景 1、2 有效 |
| `hs-ms-skill3` | 有 skill | 3 | **0** | 无效 |
| `hs-ms-skill5` | 有 skill | 3 | 2 | 基本无效 |
| `hs-gpu-sol` | 基线 | 4 | 75 | 有效 |
| `hs-gpu-skill` | 有 skill | 4 | 113 | 有效 |

**所有基线轮次都读了夹具**（19-75 次）；**有 skill 的轮次里，场景 3 一次都没读到过**。

因此我先前写下的两处因果结论都被推翻，此处如实作废：

| 我的结论 | 为什么错 |
|---|---|
| 「场景 2 从 4/4/1 变 9/0/0 是 `## Output format` 硬化生效」 | 第一轮 fixture-refs=**0**、第二轮=**19**。真实变量是第二轮读到了夹具，因此能引用 0.61→0.94、0→14200、4120→2980。Output format 的改动可能有贡献，但这两轮不构成能分离它的对照 |
| 「场景 3 三轮回归是 workflow 清单化诱导『待办清单』，且任务形态与 skill 形态不匹配」 | 场景 3 的三轮有 skill 全部 fixture-refs=0/0/2。答案之所以只能给「如果是振荡…如果是容量消失…」的条件分支，是因为模型**手里没有那份材料**。与 workflow 措辞、任务形态都无关 |

一并作废的还有由此推出的建议（「后续应改 query 措辞而非 skill」）与
第三轮那次 workflow 回滚的依据。回滚本身保留：回滚后的措辞
（冷启动逐项给数字、autoscaler 那条要求说出本部署属于哪种情况）
独立判断更好，不依赖那次被污染的对照。

`containers` 场景 4 的增益判定**不受影响**：基线 75、有 skill 113，双方都实读了两份夹具。

修法（`tools/run_evals.py`）：把复制进工作目录的文件名追加到提示尾部
（`Files in the working directory: \`a\`, \`b\``）。只加文件名、不加内容，
这样「会不会读」不再是随机变量，而「读了之后怎么用」仍然是被测能力。

一个附带观察，需在新对照里重新检验而不是现在下结论：
四次 fixture-refs=0 全部发生在**有 skill** 的轮次，基线一次都没有。
`skill://model-serving` 是有 skill 轮次唯一的额外读取动作，
**读 skill 可能替代了「去看看工作目录里有什么」这个动作**。如果新对照下仍然出现
有 skill 不读工件的情况，那是 skill 的真实风险（`## Core rules` 第 1 条正是为此写的），
需要在 skill 侧解决;如果不再出现，则纯粹是旧提示缺文件名所致。

## 评测结果（夹具命名修复后的对照）

| 场景 | 模型 | 有/无 skill | skill_read | fixture-refs | 达成的 expected_behavior |
|---|---|---|---|---|---|
| 待填 | openai/gpt-5.6-sol medium | 无（基线） | | | `/tmp/hs-ms-base-fix` |
| 待填 | openai/gpt-5.6-sol medium | 有 skill | | | `/tmp/hs-ms-skill-fix` |

结论：<!-- 新对照判定后填 -->

### 仍然成立的记录

以下不依赖被污染的对照，保留：

- **基线缺口**（上文「第二次跑」，4 场景 fixture-refs 19-29 全部实读）：
  32 条里 19 达成 / 10 部分 / 3 未达成，以及稳定缺口清单。
- **三处夹具/判据缺陷**：`bench-report.md` 的 duration 与延迟自相矛盾、
  `hpa-and-startup.md` 的「HPA 双向 rescale」与「指标恒高于 target」不可能同时成立、
  四条我自己写错的 `expected_behavior`。这些是文件与判据本身的问题，
  与模型是否读取无关，修正全部有效。
- **场景 1 的增益**：两轮有 skill 都实读夹具（38、23），两轮都得 6/3/1，基线 3/6/1。
  填补的四项可核验：`--goodput` 空格分隔语法、readiness gate + 数百请求 warmup、
  decode 受显存带宽约束 + 三个 vLLM 指标点名、`n=3` pilot 与 finalist 独立确认。
- **场景 4 的负例边界**：两轮有 skill 虽然都没读夹具，但都没有越界到 KV cache /
  `--max-model-len` / prefix caching / 压测，全程留在训练侧。这条不依赖夹具内容，
  测的是 `## Scope` 否定范围，结论有效。`skill_read` 三轮为 false / true / true，
  `n=1` 的采样无法支持任何结论。

## 备注

- **许可注意**：Dynamo 的 `dynamo-router-starter`、`dynamo-interconnect-check`、
  `troubleshoot-dynamo` 三个文件 frontmatter 与正文 SPDX 冲突，按 CC-BY-4.0 处理（裁决 R5）。
  `NVIDIA/TensorRT-LLM` 与 `ai-dynamo/dynamo` 的 GitHub API 许可字段都是 NOASSERTION，
  均已实读 LICENSE 确认为 Apache-2.0，`SOURCES.yaml` 的 `notes` 记录该实读结论。
- **未来同步时要盯的上游**：`vllm-project/vllm-skills` 自 2026-04-03 未再推送，
  而 vLLM 本体迭代很快——`check_upstream.py` 报 behind 时优先核 `vllm bench serve` 的
  参数是否改名。`huggingface/skills` 的日期表述内部不一致，同步时只核技术判据。
- **放弃的方向**：`llm-d`/`kserve`/`Ray Serve`/`BentoML` 四个主流服务框架都没有 skill 仓库，
  本轮不以它们为上游；`llm-d` 的 `guides/` 是 sized P/D 分离拓扑的重要文档来源，
  若后续要深化缺口 4，它是第一顺位的新增上游候选。
- **与 `containers` skill 的并行工作**：用户在本轮中途追加要求「`containers` skill 也需要
  有 GPU 相关内容」。两边的分界与字面一致的分界句见 `docs/roadmap.md` 的跨 skill 分界句表；
  `containers` 侧的调研记录在该 skill 的 `SOURCES.yaml` 与 `docs/roadmap.md`，
  不在本文件内（本文件只记 `model-serving` 的立项与裁决）。
