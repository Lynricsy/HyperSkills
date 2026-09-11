# generative-media 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11
- 检索途径：
  - `gh api repos/<owner>/<repo>`（已登录账号 Lynricsy，5000 次/小时配额），逐个候选核对
    stars / `pushed_at` / `license.spdx_id`；未使用任何匿名 HTTP
  - `gh api repos/<o>/<r>/git/trees/<ref>?recursive=1` 列目录树，
    `gh api repos/<o>/<r>/contents/<path> --jq '.content' | base64 -d` 读原始 `SKILL.md`
  - 官方组织仓库逐个探测：`openai/skills`、`google/skills`、`huggingface/skills`、
    `anthropics/skills`、`microsoft/skills`、`replicate/skills`、
    `GoogleCloudPlatform/vertex-ai-creative-studio`、`fal-ai-community/skills`、
    `veniceai/skills`（`fal-ai/skills` 不存在，404）
  - 多技能聚合仓库：`github/awesome-copilot`（`plugins/skill-image-gen` →
    `skills/generate-image`）、`VoltAgent/awesome-agent-skills`（纯 README 索引，用作检索入口）、
    `addyosmani/agent-skills`（25 个 skill，无任何媒体主题）、`wshobson/agents`（同，无）
  - `gh search repos`：`nano banana skill`、`comfyui skill SKILL.md`、
    `text-to-speech agent skill`、`whisper transcription skill`、`video generation skill agent`
  - `web_search`：`"image generation" agent skill SKILL.md github 2026`
  - 领域本体仓库：`huggingface/diffusers`、`openai/whisper`、`ggml-org/whisper.cpp`、
    `SYSTRAN/faster-whisper`、`comfyanonymous/ComfyUI`、`Comfy-Org/docs`、
    `c2pa-org/specifications`、`remotion-dev/remotion`
  - 官方文档站（`kind: docs`）：`ai.google.dev/gemini-api/docs/{image-generation,video,veo,speech-generation}`、
    `developers.openai.com/api/docs/guides/{image-generation,text-to-speech,speech-to-text}`（`.md` 后缀版）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- **许可一律实读**，不信 API 的 `spdx_id`：`openai/skills` 仓库**没有顶层 LICENSE**（API 报
  `null`），但 `skills/.system/imagegen/LICENSE.txt`、`skills/.curated/speech/LICENSE.txt`、
  `skills/.curated/transcribe/LICENSE.txt` 三份逐个实读均为 Apache-2.0；
  `fal-ai-community/skills` 根树只有 `.gitignore` / `README.md` / `scripts` / `skills`，
  确无 LICENSE 文件 → `license: NONE`；`ai.google.dev` 页脚实读为
  「content licensed under CC BY 4.0, code samples under Apache 2.0」。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | openai/skills `skills/.curated/transcribe` | https://github.com/openai/skills | 26899 | 2026-09-08 | Apache-2.0（**逐目录**实读 `LICENSE.txt`；仓库无顶层 LICENSE，API 报 `null`） | ASR / 说话人分离 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 短，但每条都是会出事的阈值：25 MB 单请求上限、输入格式白名单、**音频超过 ~30 秒必须传 `chunking_strategy`**、`gpt-4o-transcribe-diarize` **不支持 prompt**、已知说话人最多 4 个。三条抽查全部对上官方 `speech-to-text` 文档 |
| 2 | openai/skills `skills/.curated/speech` | 同上 | 26899 | 2026-09-08 | Apache-2.0（逐目录实读） | TTS | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 4096 字符/请求上限、50 RPM、`instructions` 只对 GPT-4o mini TTS 系有效而 `tts-1`/`tts-1-hd` 无效、**必须向终端用户披露这是 AI 生成的声音**、指令模板（affect→tone→pacing→emotion→pronunciation→emphasis）。披露那条在官方 TTS 文档里是 usage policy 的硬要求，不是建议 |
| 3 | GoogleCloudPlatform/vertex-ai-creative-studio `experiments/mcp-genmedia/skills/*`（7 个 skill） | https://github.com/GoogleCloudPlatform/vertex-ai-creative-studio | 1205 | 2026-09-11 | Apache-2.0 | TTS 指挥 / 生图 / 生视频 / 多步编排 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（部分） | 官方 Google 仓库里唯一把「生成媒体当制作流程」写清楚的一组。`genmedia-voice-director` 的四段式提示框架与**带毫秒量级的停顿标签**（`[short pause]`≈250ms / `[medium]`≈500ms / `[long]`≈1000ms+）、`genmedia-image-artist` 的「安全过滤器拦截后做临床式改写」、`genmedia-producer` 的「>8 秒视频必须先分镜成 5–8 秒片段」。**按边界只取生成部分**；`genmedia-video-editor` / `genmedia-audio-engineer` 里的 ffmpeg 半边（overlay 坐标、两遍法 GIF、concat 前对齐、混音 dB）归 `media-processing` |
| 4 | ai.google.dev `gemini-api/docs/{image-generation,video,veo,speech-generation}` | https://ai.google.dev/gemini-api/docs/veo | — | 页面注明 2026-09-04 / 2026-06-30 更新 | **CC-BY-4.0**（页脚实读；代码示例 Apache-2.0） | 官方事实源 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged，需署名） | 本主题唯一**许可允许合入**的一线厂商文档。给出的是别处拿不到的硬数字：Veo 3.1 固定 24 fps、`durationSeconds` 只能 4/6/8 且 1080p/4k/参考图场景必须为 8、**生成视频服务端只保留 2 天**、请求延迟 11 秒–6 分钟、`personGeneration` 在 EU/UK/CH/MENA 只允许 `allow_adult`、音频被安全过滤拦截时不计费；以及「**`seed` 不保证确定性，只是略微提高**」这句原文 |
| 5 | openai/whisper（README + model-card） | https://github.com/openai/whisper | 108898 | 2026-08-31 | MIT | 本地 ASR 的机制与失效模式 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | `transcribe()` 内部是**滑动 30 秒窗口**逐窗自回归解码，低层 API 要先 `pad_or_trim` 到 30 秒——这解释了为什么时间戳会在长音频上漂移、为什么分段边界会切断词。model-card 自述两类失效：弱监督训练导致**幻听出未被说出的文本**，seq2seq 架构导致**重复输出**，且低资源语言更糟 |
| 6 | huggingface/diffusers `docs/source/en/using-diffusers/reusing_seeds.md`（+ `schedulers.md` / `image_quality.md`） | https://github.com/huggingface/diffusers | 34497 | 2026-09-11 | Apache-2.0 | 本地 diffusion 的可复现边界 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 唯一把「seed 到底保证什么」讲到位的上游：`Generator` 带**会被消费并改变的随机状态**，循环里复用同一个对象每次结果都不同（必须每次新建）；CPU 与 GPU 是不同的随机数发生器，diffusers 靠 `randn_tensor` 在 CPU 上造张量再搬到 GPU；`enable_full_determinism` 具体做三件事（`CUBLAS_WORKSPACE_CONFIG=:16:8`、关 cudnn.benchmark、关 TF32）；结论句是「即使 seed 相同也**不保证**」 |
| 7 | c2pa-org/specifications | https://github.com/c2pa-org/specifications | 206 | 2026-08-20 | CC-BY-4.0（实读 LICENSE：Attribution 4.0 International） | 内容凭证 / 产物溯源 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 标准组织本体，许可可合入。提供「生成物治理」这一节的规范侧骨架（manifest / assertion / 签名与信任列表），与 Google 侧的 SynthID + C2PA 元数据、以及 TTS 的 AI 披露义务串成一条完整的产物责任链 |
| 8 | ggml-org/whisper.cpp | https://github.com/ggml-org/whisper.cpp | 53603 | 2026-09-11 | MIT | 本地 ASR 的落地约束 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（部分） | 取两条：`whisper-cli` **只吃 16-bit WAV**，必须先 `ffmpeg -i input.mp3 -ar 16000 -ac 1 -c:a pcm_s16le output.wav`（这条正好是与 `media-processing` 的交接点）；以及自带 VAD 这一层——长音频先做语音活动检测再送模型，是抑制 30 秒窗口空白段幻听的标准做法。其余是构建与后端选择，不合入 |
| 9 | openai/skills `skills/.system/imagegen` | 同上 | 26899 | 2026-09-08 | Apache-2.0（逐目录实读） | 文生图 / 图像编辑 | 3 | 3 | 3 | 1 | 2 | 12 | INCLUDE（部分） | 279 行，本波次结构最完整的生图 skill：**generate 与 edit 的判定规则**（用户给图只作风格参考 = generate，要保留原图部分 = edit）、编辑必须每轮重申 invariants、16 张输入图上限、`input_fidelity` 高会显著抬输入 token、**「掩膜是提示引导的，不保证精确形状」**、不覆盖原资产而写 `-v2` 兄弟文件。正确性扣 2：`references/image-api.md` 的适用模型清单写的是 `gpt-image-1.5 / gpt-image-1 / gpt-image-1-mini`，而官方 `image-generation` 指南当前为 `gpt-image-2.5-sunburst` / `gpt-image-2.5-flare`（抽查三条中一条错）。另有 harness 绑定问题，见深度审查 |
| 10 | replicate/skills `skills/run-models` | https://github.com/replicate/skills | 58 | 2026-06-04 | Apache-2.0 | 长任务 / 产物治理 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 本主题「长任务怎么等」的最佳来源：三种取结果的方式（轮询 / `Prefer: wait` 同步阻塞**上限 60 秒**且只推荐给极快模型 / HTTPS webhook + `Webhook-ID`·`Webhook-Timestamp`·`Webhook-Signature` 验签），`starting→processing→succeeded/failed/canceled` 状态机，`lifetime` 自动取消跑飞的任务，以及**输出文件 URL 1 小时后过期，必须立刻下载另存** |
| 11 | replicate/skills `skills/prompt-images`（+ `find-models` / `compare-models`） | 同上 | 58 | 2026-06-04 | Apache-2.0 | 图像提示与参数控制 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 跨厂商成立的提示工程，且带**反模式清单**：对未用负向提示训练的模型使用 negative prompt 是加噪不是去噪；CFG 过高会「烧」出过曝高对比；多数模型在 ~1 百万像素附近最好，超了出边缘伪影；`transform` 这类动词会把整个身份换掉。`find-models` 的「永远查 API 而不是凭记忆报模型名」是本 skill 一条核心规则的第二来源 |
| 12 | replicate/skills `skills/prompt-videos` | 同上 | 58 | 2026-06-04 | Apache-2.0 | 视频提示与参数控制 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 七要素分层（主体/环境/动作/风格/运镜/构图/氛围）、镜头与运镜词表、8–15 秒的 wide→medium→close 递进；两条非直觉事实：**部分视频模型即使换 seed 也给出高度相似的输出**（要变化得改提示词，不是重跑）；**字幕污染**——训练数据里有烧录字幕，对白要用冒号而不是引号并显式写 `(no subtitles)` |
| 13 | google/skills `skills/cloud/gemini-api`（`references/media_generation.md`） | https://github.com/google/skills | 19780 | 2026-09-11 | Apache-2.0 | Gemini 侧媒体生成 | 3 | 3 | 2 | 1 | 2 | 11 | MAYBE | 覆盖面对（Nano Banana 生图、chat 模式迭代编辑、Omni 的四种 task、Veo 轮询、`background=True` 异步），但**调用形状已与官方文档分叉**：它写 `client.models.generate_content(...)` + `response.parts`，官方 `image-generation` 页已改为 `client.interactions.create(...)` + `interaction.output_image`（裁决 1）。只用作覆盖面对照与 Omni/Veo 分工的佐证，不抄代码 |
| 14 | developers.openai.com `api/docs/guides/{image-generation,text-to-speech,speech-to-text}` | https://developers.openai.com/api/docs/guides/image-generation | — | 持续 | Proprietary（全站未见任何内容许可授予，沿用 `ai-engineering` 的同一裁决） | 官方事实源 | 3 | 3 | 3 | 3 | 0 | 12 | reference（许可裁决） | 内容质量足以 INCLUDE，但无内容许可，只作事实复核：本次用它核对了 imagegen / speech / transcribe 三个 skill 的抽查项（25 MB、格式白名单、>30 秒 `chunking_strategy`、AI 语音披露义务、`instructions` 的模型适用范围），并发现了模型 id 已整代更替。同样的工程事实改从 Apache-2.0 的 `openai/skills` 合入 |
| 15 | google-gemini/cookbook | https://github.com/google-gemini/cookbook | 17765 | 2026-09-10 | Apache-2.0 | notebook 示例集 | 3 | 3 | 1 | 3 | 2 | 12 | REJECT（内容裁决） | 可运行示例集，不是可证伪的工程判据；沿用 `ai-engineering` 对 cookbook 类上游的同一裁决。它覆盖的事实已由 #4 的官方文档以更可引用的形式取得 |
| 16 | microsoft/skills `.github/skills/podcast-generation` | https://github.com/microsoft/skills | 3008 | 2026-09-11 | MIT | Azure Realtime 播客生成 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT（选题裁决） | 按 `docs/roadmap.md`「已排除主题·SaaS 产品包装类」：主体是 Azure OpenAI Realtime 端点配置 + React/FastAPI 全栈教程，连 `AZURE_OPENAI_AUDIO_ENDPOINT` 不能带 `/openai/v1/` 这种部署细节都写进去了。**只留一条二次佐证**：Realtime 回来的是裸 PCM（24 kHz），必须自己封成 WAV（`scripts/pcm_to_wav.py`）——与 Gemini TTS 一致，说明这是通用陷阱而非单厂商怪癖 |
| 17 | veniceai/skills `venice-image-generate` / `venice-image-edit` / `venice-audio-{speech,music,transcription}` / `venice-video` | https://github.com/veniceai/skills | 141 | 2026-09-07 | MIT | Venice API 说明书 | 1 | 3 | 3 | 3 | 2 | 12 | REJECT（选题裁决） | 分数够，但它就是「某个产品的 API 说明书」的教科书样本：逐字段列 `POST /api/v1/image/generate` 的 `cfg_scale` / `variants` / `style_preset` / `safe_mode` / `watermark` 及其默认值。按已排除主题表 REJECT。**注意区分**：跨厂商的生成媒体工程规则（提示控制、种子可复现、成本与速率、产物治理）不属于产品包装，那部分已由 #10–#12 覆盖 |
| 18 | huggingface/skills `skills/huggingface-lora-space-builder` | https://github.com/huggingface/skills | 11038 | 2026-09-10 | Apache-2.0 | 图像模型 LoRA 训练 | 3 | 3 | 2 | 3 | 2 | 13 | REJECT（边界裁决） | 许可与质量都没问题，但它改的是权重（LoRA 训练、基座模型选择），按波次契约归 `ml-training`。本 skill 只覆盖「**用**已有 LoRA 时要带触发词、多 LoRA 用 0.9–1.1 的权重调和」这一层，取自 #11 |
| 19 | fal-ai-community/skills `skills/{genmedia,fal-prompting,model-routing,fal-models-catalog,…}` | https://github.com/fal-ai-community/skills | 237 | 2026-05-13 | **NONE**（根树实查确无 LICENSE 文件） | fal.ai CLI 与端点路由 | 1 | 1 | 2 | 2 | 0 | 6 | MAYBE | 有两条可迁移：`fal-prompting` 的「视觉事实压过体面形容词」（把 stunning/cinematic/masterpiece 换成 overcast daylight / brushed aluminum / 50mm feel）、「每次迭代只动一个变量」；以及「图像通常内联完成，视频/音频/3D 需要队列 + 轮询」这条模态与时延的经验分档。其余（`genmedia` CLI 全部命令、`model-routing` 的硬编码端点清单）是单厂商产品包装且腐化极快，不合入。许可 0 分是因为无 LICENSE；按许可规则可 merged（`license: NONE`），但内容不值得 |
| 20 | comfyanonymous/ComfyUI | https://github.com/comfyanonymous/ComfyUI | 132549 | 2026-09-11 | **GPL-3.0** | 本地节点式工作流 | 3 | 3 | 2 | 3 | 0 | 11 | reference（许可裁决） | 按许可处理规则，GPL-3.0 一律 `relation: reference`：只用它的**主题清单**判断本 skill 的覆盖面（采样器/调度器、CFG、latent、LoRA 加载、mask/inpaint、API 节点），每条事实改从 Apache-2.0 的 diffusers 文档取证，不复制任何文字 |
| 21 | Comfy-Org/docs | https://github.com/Comfy-Org/docs | 288 | 2026-09-11 | **GPL-3.0** | ComfyUI 官方文档 | 3 | 3 | 2 | 3 | 0 | 11 | reference（许可裁决） | 同上。`built-in-nodes/` 下的节点清单证实了「ComfyUI 已经把第三方生图 API 包成内置节点」这一形态变化，可用于判断覆盖面，但一字不取 |
| 22 | github/awesome-copilot `skills/generate-image`（插件 `plugins/skill-image-gen`） | https://github.com/github/awesome-copilot | 38899 | 2026-09-10 | MIT | 双厂商生图 | 3 | 3 | 1 | **0** | 2 | 9 | REJECT（正确性 0） | 抽查三条**两条以上错**：① 默认 Gemini 模型写 `gemini-2.0-flash-exp`，官方生图入口现为 `gemini-3.1-flash-lite-image` / `gemini-3.1-flash-image` / `gemini-3-pro-image` 系；② 请求体用 `generationConfig.responseModalities: ["TEXT","IMAGE"]` 打 `:generateContent`，官方已改为 `/v1beta/interactions`；③ OpenAI 侧写 `gpt-image-2`，官方当前为 `gpt-image-2.5-sunburst` / `gpt-image-2.5-flare`。量表规定正确性 0 直接 REJECT。它恰好是「把模型 id 写死在 skill 里」这个反模式的实证 |
| 23 | adamd9/skill-image-gen（#22 的上游仓库） | https://github.com/adamd9/skill-image-gen | 1 | 2026-05-13 | MIT | 同上 | 0 | 1 | 1 | 0 | 2 | 4 | REJECT | 1 星个人仓库，内容即 #22 的同一份，同样的过期 API 形状。留行是为了避免下轮把它当成独立候选再讨论一次 |
| 24 | SYSTRAN/faster-whisper | https://github.com/SYSTRAN/faster-whisper | 25342 | 2025-11-19 | MIT | CTranslate2 加速推理 | 2 | **0** | 2 | 3 | 2 | 9 | REJECT（新鲜度） | 最近推送 2025-11-19，距今近 10 个月，按量表新鲜度 0 且非官方厂商。它提供的 VAD 与批处理加速结论已由 #8 覆盖 |
| 25 | ShinChven/nano-banana-skills | https://github.com/ShinChven/nano-banana-skills | 66 | 2026-02-26 | MIT | Gemini 生图 | 1 | **0** | 2 | 2 | 2 | 7 | REJECT（新鲜度） | 社区 nano-banana skill 里 star 最高的一个，仍只有 66 星且已 6 个多月未推送；`gh search repos "nano banana skill"` 返回的其余 11 个全是 ≤6 星的个人仓库，整条线放弃 |
| 26 | remotion-dev/remotion | https://github.com/remotion-dev/remotion | 58917 | 2026-09-11 | NOASSERTION（Remotion License，公司使用需付费）→ 视同专有 | React 程序化视频 | 3 | 3 | 3 | 3 | 0 | 12 | REJECT（边界 + 许可） | **不属于本 skill**：同样的输入渲染出同样的帧，是确定性视频合成，不是概率生成；它的取舍（帧率、编码、合成时长）属于 `media-processing` 与 `react`。许可也不允许 merged。留行是因为它在两个索引里都被挂在「视频生成」标签下，容易被误收 |
| 27 | fal.ai/docs、replicate.com/docs | https://fal.ai/docs · https://replicate.com/docs | — | 持续 | 专有（未见内容许可授予） | 厂商文档 | 3 | 3 | 3 | 3 | 0 | 12 | reference（许可裁决） | 仅作事实复核。Replicate 侧同样的工程事实改从 Apache-2.0 的 `replicate/skills`（#10–#12）合入；fal 侧无可合入的等价开源来源，因此本 skill 不写任何 fal 专属内容 |

27 行，其中 INCLUDE 12、MAYBE 2、REJECT 9、许可降级 4。

## 深度审查

### openai/skills `skills/.curated/transcribe`（14 分）

结构极简：frontmatter（只有 `name` / `description`）+ Workflow 5 步 + Decision rules + Output
conventions + Dependencies + Environment + Skill path + CLI quick start + Reference map。
`references/api.md` 只有 7 行，但那 7 行全是阈值。

它的价值在于把 ASR 的三个「会改变结果而不是报错」的点写死了：

- **25 MB 单请求上限**与格式白名单（mp3/mp4/mpeg/mpga/m4a/wav/webm）——超了是请求失败，好办；
- **音频超过 ~30 秒必须传 `chunking_strategy`**——不传不会报错，只会得到被截断的转写。我对着
  官方 `speech-to-text` 文档逐字核过这条：「For audio longer than 30 seconds, set
  `chunking_strategy` to `"auto"` or a voice activity detection configuration」，一致；
- **`gpt-4o-transcribe-diarize` 不支持 prompt**——也就是说，你想用 prompt 注入专有名词来救
  识别率的那套办法，在开了说话人分离之后直接失效。已知说话人参考最多 4 个。

一处**已被官方超越但不算错**的地方：它默认 `gpt-4o-mini-transcribe`，而官方文档当前的推荐
起点是 `gpt-transcribe`，并且新增了 `keywords`（字面词表）与 `languages`（多语提示）两个参数，
以及「语言判不准时返回 `languages: []`」这个可检测信号。这不是规则错误，是模型代际更替——
恰好印证裁决 2：**skill 里不该写模型 id 清单**。

绑定：`export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"` 与
`$CODEX_HOME/skills/transcribe/scripts/transcribe_diarize.py`——Codex harness 专属路径，
合入时全部剥离。
重叠：与 #5（whisper 的 30 秒窗口）互相印证——托管 API 的 30 秒阈值不是随便定的，它就是
Whisper 系模型的原生窗口长度。

### openai/skills `skills/.curated/speech`（14 分）

结构与 transcribe 同构。frontmatter 的 `description` 里直接写了否定边界
（「Custom voice creation is out of scope」），这是本仓库要求的写法。

值得取的四条：

1. **4096 字符/请求**——超了要自己切分，而切分点决定了句子的语调断裂位置；
2. **50 RPM，且 CLI 把 `--rpm` 上限钉死在 50**——把速率限制做成工具的硬约束而不是注释；
3. **`instructions` 只对 GPT-4o mini TTS 系有效，`tts-1` / `tts-1-hd` 不支持**——我对着官方
   TTS 指南核过：该页所有 `instructions` 示例都用 `gpt-4o-mini-tts`，并明确把 `tts-1`/`tts-1-hd`
   列为「our other text-to-speech models」，一致；
4. **「Provide a clear disclosure to end users that the voice is AI-generated」**——这条在官方
   文档里是 usage policy 的硬要求原文（"Our usage policies **require** you to provide a clear
   disclosure…"），不是礼貌建议。这是本 skill 产物治理一节里唯一一条**法务性质**的规则，
   与 C2PA / SynthID 属于同一条责任链的不同层。

它的指令模板（Voice Affect / Tone / Pacing / Emotion / Pronunciation / Pauses / Emphasis /
Delivery）与 #3 的 Google 版四段式框架不冲突，是同一件事的两种粒度：OpenAI 版是逐维度标签，
Google 版是「角色→场景→导演笔记→带标签的台词」的叙事式。合入时以 Google 版为骨架、
OpenAI 版为字段表。

### GoogleCloudPlatform/vertex-ai-creative-studio `experiments/mcp-genmedia/skills/*`（14 分）

七个 skill：`genmedia-producer`、`genmedia-image-artist`、`genmedia-video-editor`、
`genmedia-audio-engineer`、`genmedia-voice-director`、`story-generator`、`agent-aware-cli`。
frontmatter 有 `name` / `description` / `allowed-tools` / `metadata`，其中 `allowed-tools`
列的全是 MCP 工具名（`mcp_veo_veo_t2v`、`mcp_nanobanana_nanobanana_image_generation`、
`mcp_avtool_ffmpeg_*`），**这是本组候选最重的 agent 绑定**：离开那套 MCP server，工具名一个都
不存在。合入时只能取规则，不能取工具调用。

`genmedia-voice-director` 是我读到的最好的一份 TTS 上游，因为它把「怎么说」变成了可执行结构：

- 四段式：AUDIO PROFILE（角色档案）→ THE SCENE（环境与情绪）→ DIRECTOR'S NOTES
  （Style / Accent / Pacing，且要求口音尽量具体到城区，例如 "Brixton, London"）→
  TRANSCRIPT（带内联音频标签的台词）；
- **内联音频标签带毫秒量级**：`[short pause]` ≈250ms、`[medium pause]` ≈500ms、
  `[long pause]` ≈1000ms+，情绪标签与动作标签分两类；
- 一条容易漏的约束：**标签必须是英文**，但可以和非英文台词混用（`[anger] Je ne sais pas!`）；
- 「take 3 on the bounce」：在**一次**请求里让模型把同一句连演三遍产生差异，而不是发三次请求
  ——这是成本与一致性的真实取舍。

`genmedia-image-artist` 贡献一条别处没有的操作：**生成被安全过滤器拦截时，做「临床式改写」
（clinical rewrite）——剥掉带情绪色彩的措辞，只保留物理描述**，而不是换模型或反复重试。
`genmedia-producer` 贡献「>8 秒的视频必须先写分镜、切成 5–8 秒的片段生成」，这正好对上 #4 里
Veo 单次最长 8 秒的硬限制——两份官方材料一个说约束一个说对策。

重叠与切分：`genmedia-video-editor` / `genmedia-audio-engineer` 各有一半是 ffmpeg 具体操作
（overlay 前先 `get_media_info` 拿尺寸再算坐标、GIF 两遍法默认 `fps=15` / `scale 0.33`、
concat 前必须同分辨率同帧率、layer 前必须同采样率否则变调、人声 +6~+10 dB 配乐 −10~−15 dB、
收尾用 `afade`）。**按边界这半边归 `media-processing`**，已同步给该 skill 的调研者。

### ai.google.dev Gemini API 文档（14 分，唯一可合入的一线厂商文档）

许可是这条的关键：页脚实读为「content licensed under the **Creative Commons Attribution 4.0
License**, code samples under the Apache 2.0 License」。按许可处理规则，CC-BY-4.0 可 merged，
在 `notes` 写署名即可。这与 `ai-engineering` 得出的「厂商文档站只能 reference」的结论**不冲突**
——那条结论是对 Anthropic 与 OpenAI 说的，Google 开发者站有明确的开放许可授予。

内容上，它提供了本主题最硬的一批数字（`/gemini-api/docs/veo` 的参数表与 Limitations 节）：

- Veo 3.1 固定 **24 fps**；`durationSeconds` 只能是 4/6/8，且用扩展、参考图、1080p 或 4k 时
  **必须为 8**；每次请求只出 1 个视频；
- **请求延迟 Min 11 秒 / Max 6 分钟（高峰）**——这一个数字就足以否掉「同步等生成视频」的设计；
- **生成视频在服务端只存 2 天**，过期删除；扩展出来的视频算新生成的；
- `personGeneration` 在 EU / UK / CH / MENA 只允许 `allow_adult`——一条会让同一份代码在不同
  区域直接失败的规则；
- **音频被安全过滤拦截导致视频未生成时不计费**；
- 以及那句必须原样引用的：「Note that the `seed` parameter is also available for Veo 3 models.
  **It doesn't guarantee determinism, but slightly improves it.**」

`/gemini-api/docs/image-generation` 侧给出 aspect ratio → 分辨率 → **token 数**的完整表
（例如 3.1 Flash Image 的 1K 一律 1120 tokens、4K 2520 tokens），这是做成本预算的唯一可靠依据；
并写明「All generated images include a SynthID watermark」。
`/gemini-api/docs/speech-generation` 侧给出的关键事实是：**TTS 返回的是裸 PCM（24 kHz / 16-bit /
单声道），示例代码自己用 `wave` 模块封 WAV**——生成侧不给你容器，容器是你的事。

### huggingface/diffusers 的 `reusing_seeds.md`（14 分）

不是 skill 而是官方文档，但它是本主题里唯一把「可复现」讲到可操作精度的上游，四条都写进了正文：

1. **`Generator` 是有状态的，状态会被消费**。文档用一个 diff 直接演示：在 `for` 循环里复用
   同一个 `generator` 对象，五次结果各不相同；正确写法是每次传 `torch.manual_seed(0)` 新建。
   这条是「我明明固定了 seed 为什么还是不一样」的最常见真实答案。
2. **CPU 与 GPU 是不同的随机数发生器**。diffusers 内部用 `randn_tensor` 在 CPU 上造噪声再搬到
   GPU；文档明确建议「如果可复现重要，一律用 CPU `Generator`，性能损失通常可忽略」。
3. `enable_full_determinism()` 具体做三件事：`CUBLAS_WORKSPACE_CONFIG=:16:8`、
   `torch.backends.cudnn.benchmark=False`、关闭 TF32。每一件都有性能代价，所以它是测试开关
   不是生产默认。
4. 开篇与结尾两次强调的边界：可复现只在「**across releases and platforms within a certain
   tolerance range**」的意义上成立，并且「you can try to limit randomness, but it is **not
   guaranteed** even with an identical seed」。

绑定：纯 Python/PyTorch，无 harness 假设。
重叠：与 #4 的 Veo seed 声明形成本 skill 最重要的一组对照——**本地开源栈上 seed 能给到「同权重
同实现同设备下可复现」，托管 API 上 seed 只是一个提高相似度的提示**。裁决 3 就建在这上面。

### openai/whisper README + model-card（14 分）

选它而不是选各种 whisper 封装，是因为只有本体仓库说清了机制：`transcribe()` **读整个文件，
用滑动 30 秒窗口逐窗做自回归 seq2seq 预测**；低层 API 必须先 `whisper.pad_or_trim(audio)` 把音频
补/截到 30 秒再算 log-Mel。知道这一点，三个常见现象就不再神秘：长音频的段级时间戳会随窗口累积
漂移、词会在窗口边界被切断、静音段容易凭空冒词。

model-card 的 Performance and Limitations 一节自述两类失效，措辞可直接引用：弱监督 + 大规模含噪
数据导致预测里出现**音频中根本没说过的文本（hallucination）**，作者的假设是模型把「预测下一个词」
和「转写音频」两件事混在了一起；seq2seq 架构使其**倾向产生重复文本**，beam search 与温度调度只能
部分缓解；且低资源语言更严重。

这正是本 skill 与 `media-processing` 分界的教科书例子：把 m4a 转成 16 kHz 单声道 WAV 是确定性工程
（那边），而「同一段音频这次转出来多了一句没人说过的话」是概率性识别的固有失效（这边），
对策也完全不同——前者是参数正确性，后者是 VAD 前置、温度回退与人工复核采样率。

### replicate/skills `run-models` + `find-models` + `compare-models`（各 12 分）

三个小 skill 合起来构成本 skill「长任务与成本」一章的骨架。frontmatter 只有 `name` /
`description`，正文是裸清单，没有任何 harness 绑定（引用的都是公开 HTTP 端点），是本波次
**最容易合入**的一组。

`run-models` 把「同步 vs 轮询 vs webhook」这件事讲全了，而且给了边界条件：

- `Prefer: wait` 同步阻塞**最长 60 秒**，且明说「只推荐给非常快的模型」；
- 轮询走 `starting → processing → succeeded / failed / canceled` 状态机；
- webhook 要用 `Webhook-ID` / `Webhook-Timestamp` / `Webhook-Signature` 三个头验签，签名密钥从
  `GET /v1/webhooks/default/secret` 取——**把 webhook 的安全要求写进了「怎么等」这一节**，
  而不是丢给读者自己想；
- `lifetime`（`30s` / `5m` / `1h`）自动取消跑飞的任务；
- **输出 URL 1 小时过期**，必须立刻下载另存；官方模型 `owner/name`、社区模型必须
  `owner/name:version_id` 且会冷启动。

`find-models` 的开篇就是本 skill 的一条核心规则：「**Always search the API for current models…
Don't rely on model names you've seen before, including names from past conversations or training
data**」，并给出 schema 路径
`model.latest_version.openapi_schema.components.schemas.Input.properties`。
`compare-models` 提供成本口径：官方模型按次计价、社区模型按 GPU 秒计价，实际耗时看
`metrics.predict_time`。

新鲜度只有 1 分（2026-06-04，3 个月零 7 天）是它唯一的短板；但它讲的是 HTTP 协议层与任务生命周期，
不是模型清单，腐化速度远低于分数所暗示的。下次同步优先复核这三份。

### replicate/skills `prompt-images` / `prompt-videos`（各 12 分）

两份的自述都是「distilled from Replicate's blog posts，techniques are model-agnostic」，并在文末
列出了被蒸馏的博文与日期——**来源可追溯**，这在提示工程类上游里很少见。

`prompt-images` 真正有价值的是它的 10 条 Common pitfalls，其中四条是可证伪的机制性事实：
**对未用负向提示训练的模型使用 negative prompt 是引入噪声而不是去除元素**；CFG 过高会产生
「烧过」的过曝高对比；多数模型在 ~1 megapixel 附近最好，超了出边缘伪影、小了出硬裁切；
`transform` 这类整体性动词会把身份整个换掉，想做小改动必须用「change X, keeping Y unchanged」。
编辑一节还给了 inpaint 的一个非直觉点：**模型若带 magic prompt / 自动改写，只描述被遮罩区域即可；
关掉时必须描述整幅场景**——同一个掩膜、同一句提示，在两种设置下语义不同。

`prompt-videos` 的两条是本 skill 里「概率性」体感最强的：**部分视频模型即使换 seed 也产出高度
相似的结果，要变化必须改提示词**（这与图像模型的直觉相反）；以及**字幕污染**——训练集里大量视频
带烧录字幕，所以对白要用冒号引导而非引号，并显式写 `(no subtitles)`，必要时重复。

重叠：与 #3 的 Veo 五段式公式（Cinematography / Subject / Action / Context / Style）是同一件事的
两种切法，合入时取 Replicate 的七要素做骨架、Google 的五段式做速记，并注明二者等价。

### openai/skills `skills/.system/imagegen`（12 分，结构最好但绑定最重）

279 行，两级模式（内建 `image_gen` 工具优先 / 显式 CLI 回退），有 use-case taxonomy（16 个固定
slug）、共享提示 schema、augmentation 的允许项与禁止项清单。**写作水位是本波次最高的**，
`Not allowed augmentations`（不得添加未被暗示的角色、物体、品牌名、口号、色板、叙事）这一节
直接可以抄进本仓库的写作规则。

但它有两处必须处理：

1. **harness 绑定极重**。内建 `image_gen` 工具、`view_image` 工具、`$CODEX_HOME/generated_images/`
   默认落盘路径、「永远不要修改 `scripts/image_gen.py`」——这些只在 Codex 里成立。合入时保留的是
   它背后的**判据**：产物是给项目用的就必须搬进工作区并更新引用方；只是预览就可以留在临时目录；
   不覆盖已有资产而写 `hero-v2.png` 这样的兄弟文件名；最后必须报告最终落盘路径与最终提示词。
2. **模型清单过期**。`references/image-api.md` 写「intended for GPT Image models
   (`gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini`)」，官方指南当前是
   `gpt-image-2.5-sunburst` / `gpt-image-2.5-flare`（前者编辑精度优先，后者日常快速生成）。
   正确性因此扣到 1。

仍然值得 INCLUDE 的是三条与型号无关的 API 形状事实，且都在官方文档核对通过：编辑走
`POST /v1/images/edits`、`mask` 可选；GPT Image 编辑最多 16 张输入图；`background`
（`transparent`/`opaque`/`auto`）控制输出透明度，**与提示词里的 "scene/backdrop" 不是一回事**
——这条歧义它专门写了一段来消除。最关键的一句是掩膜语义：
**「Masking is prompt-guided; exact shapes are not guaranteed.」** 掩膜是提示不是裁剪，
这是把「概率性编辑」和「确定性合成」分开的那条线，也是本 skill 与 `media-processing` 在
「抠图/合成」这个词上会被混淆时的判据来源。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | Gemini 生图/生视频的调用形状 | `google/skills` 的 `references/media_generation.md`（2026-09-11 仍在推送）写 `client.models.generate_content(model="gemini-3.1-flash-image")` 然后遍历 `response.parts` 取 `inline_data`；官方 `ai.google.dev/gemini-api/docs/image-generation`（页面注明 2026-09-04 更新）已改为 `client.interactions.create(...)` 并用 `interaction.output_image` 取结果，REST 端点从 `:generateContent` 变成 `/v1beta/interactions` | 以官方文档为准，且**正文不写任何 SDK 调用形状**，只写「Gemini 侧的生图、生视频、TTS 已统一到 Interactions API；具体签名读随 SDK 版本发布的文档」 | 官方文档 > 官方组织维护的 skill 快照；两者同为 Google 但文档是一手。同一仓库的 `gemini-live-api` 也仍在用旧形状，说明这是同步滞后而非有意分叉 |
| 2 | 模型 id 要不要写进 skill | `openai/skills` imagegen 写 `gpt-image-1.5` / `gpt-image-1` / `gpt-image-1-mini`；`github/awesome-copilot` 写 `gpt-image-2` 与 `gemini-2.0-flash-exp`；`fal-ai-community/model-routing` 给了一整页硬编码端点（`openai/gpt-image-2`、`fal-ai/nano-banana-pro`、`fal-ai/flux-2/klein/9b`…）；`replicate/skills` 的 `find-models` 反过来主张「永远查 API，不要相信记忆里的模型名」 | 采纳 Replicate 的立场：**本 skill 不含任何模型 id 清单**，只写「先查 models 列表或模型页、再读 schema、再调用」的流程，以及能力维度（文生图 / 图生图 / 掩膜编辑 / 参考图 / 多图合成 / 原生音频）的对照表 | 实证：同一时点三家上游给出三套互相矛盾的型号，而官方当前是第四套（`gpt-image-2.5-sunburst` / `gpt-image-2.5-flare`、`gemini-3.1-flash-image` 系）。型号清单的半衰期以月计，写进去等于内置一个必然过期的错误 |
| 3 | `seed` 到底保证什么 | `veniceai` 等产品文档把 `seed` 当确定性开关列在参数表里；`fal-prompting` 要求「每次迭代只改一个变量」（隐含 seed 固定即可比）；`huggingface/diffusers` 官方说「即使 seed 相同也**不保证**」，且 `Generator` 状态会被消费、CPU 与 GPU 是不同的 RNG；Google 官方对 Veo 写「`seed` **doesn't guarantee determinism, but slightly improves it**」 | 分两层写死：**本地开源栈**上，seed 在「同权重 + 同实现 + 同设备 + 同 pipeline 版本 + 每次新建 `Generator`」五个条件同时成立时可复现，任一条件变动即失效；**托管 API** 上，seed 只是提高相似度的提示，不是复现手段。要复现必须把 prompt、全部参数、模型版本串、seed 与输出文件 hash 一起落盘 | 两家官方各自对自己的栈给出的否定性表述（diffusers「not guaranteed even with an identical seed」、Veo「doesn't guarantee determinism」）；产品文档的参数表只描述字段存在，不构成语义承诺 |
| 4 | 长任务用同步还是异步 | `replicate/run-models` 提供 `Prefer: wait` 同步阻塞并标注上限 60 秒、只推荐给极快模型；`fal-ai-community/genmedia` 按模态分档「图像通常内联完成，视频/音频/3D 用 `--async` + 轮询」；Google Veo 只有 LRO：`generate_videos` 返回 operation，示例 `time.sleep(10)` 轮询，官方 Limitations 写延迟 11 秒–6 分钟 | 统一按模态定：**视频、音乐、长音频一律按异步任务设计**（轮询或 webhook + 持久化 request id），同步阻塞只对「已实测 p99 < 60 秒」的图像/短 TTS 调用开放；任何同步路径都要有超时后转轮询的退路 | Veo 官方给出的 6 分钟上界直接否掉同步；Replicate 自己把同步路径限定在 60 秒并加了「only recommended for very fast models」的限定语 |
| 5 | 生成物由谁负责保存 | `replicate/run-models`：输出 URL **1 小时**后过期，必须立刻下载另存；Google Veo：服务端保存 **2 天**，过期删除，扩展视频按新生成计算；OpenAI Image API：直接返回 `b64_json`，不托管 | 把「下载并写入自有存储 + 记录产物与生成参数的对应关系」写成生成流程的**必做步骤**，不是可选优化；三家的保留期各不相同且都不适合当存储层 | 三家官方各自的保留策略互不兼容，唯一可移植的做法就是自己存。这条同时是 `run-models` 与 Veo Limitations 的交集 |
| 6 | ASR 的输入预处理算谁的活 | `ggml-org/whisper.cpp`：`whisper-cli` 只接受 16-bit WAV，README 直接给 `ffmpeg -i input.mp3 -ar 16000 -ac 1 -c:a pcm_s16le output.wav`；`openai/skills` transcribe：托管 API 接受 mp3/mp4/m4a/webm 等，但 25 MB 上限、>30 秒要分段 | 转码与容器封装本身归 `media-processing`；本 skill 只规定两类**会改变识别结果**的阈值与前置：25 MB / 30 秒分段、以及长音频先做 VAD 再送模型。反向同理：Gemini TTS 与 Azure Realtime 都返回裸 PCM（24 kHz / 16-bit / 单声道），**封 WAV 容器与重采样归 `media-processing`** | 分界句（见备注）：同样输入必得同样字节的是确定性工程；结果随模型与采样变化的是概率性生成。`ffmpeg -ar 16000` 属前者，「这次多转出一句没人说过的话」属后者 |
| 7 | 「图像编辑」里的掩膜是不是裁剪 | 产品文档（Venice 等）与部分社区 skill 把 `mask` 当作精确区域约束；`openai/skills` imagegen 的 `references/image-api.md` 明写「**Masking is prompt-guided; exact shapes are not guaranteed**」；`replicate/prompt-images` 补充：模型若开了自动改写，只描述遮罩区即可，关掉则须描述整幅场景 | 正文写成：掩膜是**提示**不是**裁剪**；需要像素级精确的区域操作（抠图、合成、羽化、alpha 通道）走确定性工具链（`media-processing`），生成式编辑只承诺「大致在这块区域内按提示改」，且必须逐轮重申 invariants | 官方参数文档的否定性表述最强；Replicate 的 magic-prompt 差异进一步说明同一掩膜在不同设置下语义都不同，更不可能是精确裁剪 |
| 8 | TTS 产物要不要标注来源 | 多数社区与产品 skill 只讲音色与参数；`openai/skills` speech 把「向终端用户明确披露这是 AI 生成的声音」列为规则；Google 侧把 SynthID 水印与 C2PA 元数据做成**不可关闭**的默认（Omni 生成的每个视频都带） | 产物治理写成三层且都为必做：① 平台强制层（SynthID / C2PA，不可关，只能读取与校验）；② 合规层（AI 生成语音/影像的显式披露）；③ 工程层（把 prompt、模型版本、seed、请求 id 与输出 hash 一起落盘，便于事后追溯） | OpenAI usage policy 的「require」措辞 + Google 文档的「All generated images include a SynthID watermark」；C2PA 规范（CC-BY-4.0）提供 manifest/assertion 的规范词汇 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `openai-skills-transcribe` | openai/skills `skills/.curated/transcribe`（Apache-2.0，逐目录 LICENSE.txt） | merged | ASR 的四个硬阈值：25 MB / 格式白名单 / >30 秒必须分段 / diarize 模型不支持 prompt；已知说话人上限 4 |
| `openai-skills-speech` | openai/skills `skills/.curated/speech` | merged | TTS 的 4096 字符与 50 RPM 上限、`instructions` 的模型适用范围、指令维度模板、**AI 语音必须向终端用户披露** |
| `openai-skills-imagegen` | openai/skills `skills/.system/imagegen` | merged | generate/edit 判定规则、编辑逐轮重申 invariants、16 图上限、`background` 与场景描述的歧义消除、**掩膜是提示引导不保证形状**、产物落盘与版本化命名、prompt augmentation 的允许/禁止清单。Codex harness 绑定（`image_gen`/`view_image`/`$CODEX_HOME`）全部剥离 |
| `replicate-skills` | replicate/skills `run-models` + `find-models` + `compare-models` + `prompt-images` + `prompt-videos`（Apache-2.0） | merged | 同步(≤60s)/轮询/webhook 三路与验签、任务状态机与 `lifetime`、**输出 URL 1 小时过期**、按 API 查模型而非凭记忆、官方 vs 社区模型的冷启动与计价差异；图像与视频的提示要素与反模式清单（负向提示、CFG、分辨率、字幕污染、seed 对视频无效） |
| `google-genmedia-skills` | GoogleCloudPlatform/vertex-ai-creative-studio `experiments/mcp-genmedia/skills/*`（Apache-2.0） | merged | TTS 四段式导演框架与带时长的停顿标签、安全过滤器拦截后的临床式改写、>8 秒视频先分镜成 5–8 秒片段。**按边界只取生成部分**，ffmpeg 半边交给 `media-processing` |
| `google-gemini-docs` | ai.google.dev `gemini-api/docs/{image-generation,video,veo,speech-generation}`（**CC-BY-4.0**，`notes` 写署名） | merged | Veo 的 24 fps / 4-6-8 秒 / 单次 1 个视频 / 11 秒–6 分钟延迟 / **2 天保留期** / 区域 personGeneration 限制 / 拦截不计费；生图的 aspect-ratio→分辨率→token 成本表与 SynthID；TTS 返回裸 PCM 24 kHz 需自行封装；**「seed 不保证确定性」原文** |
| `diffusers-docs` | huggingface/diffusers `docs/source/en/using-diffusers/reusing_seeds.md` 等（Apache-2.0） | merged | 本地 diffusion 的可复现四条：`Generator` 状态被消费、CPU/GPU 不同 RNG、`enable_full_determinism` 的三件事及其代价、「即使同 seed 也不保证」 |
| `openai-whisper` | openai/whisper README + model-card（MIT） | merged | 30 秒滑动窗口机制及其三个后果（时间戳漂移、边界切词、静音幻听）；model-card 自述的幻听与重复两类失效及其成因 |
| `whisper-cpp` | ggml-org/whisper.cpp（MIT） | merged | 本地 ASR 的输入约束（16 kHz 单声道 16-bit WAV）与 VAD 前置；同时作为与 `media-processing` 的交接点样例 |
| `c2pa-spec` | c2pa-org/specifications（CC-BY-4.0，`notes` 写署名） | merged | 产物治理的规范词汇：manifest / assertion / 签名与信任列表，与 SynthID、AI 披露义务合成一条责任链 |
| `google-skills-gemini-api` | google/skills `skills/cloud/gemini-api`（Apache-2.0） | reference | **内容裁决**：覆盖面可用（Omni 四种 task 与 Veo 的分工），但调用形状已与官方文档分叉（裁决 1），只作覆盖面对照，不取代码 |
| `comfyui` | comfyanonymous/ComfyUI + Comfy-Org/docs（**GPL-3.0**） | reference | **许可裁决**：只用其主题清单判断本 skill 对本地工作流的覆盖面（采样器/调度器、CFG、latent、LoRA 加载、mask/inpaint、API 节点），每条事实改从 diffusers 官方文档取证，不复制任何文字 |
| `openai-docs` | developers.openai.com `api/docs/guides/{image-generation,text-to-speech,speech-to-text}` | reference | **许可裁决**：无内容许可授予，仅用于事实复核（本次核对了三个 skill 的抽查项并发现模型代际更替）。同义指引改从 Apache-2.0 的 `openai/skills` 合入 |
| `fal-community-skills` | fal-ai-community/skills（无 LICENSE → `license: NONE`） | reference | **内容裁决**：只留两条通用判据的二次佐证（视觉事实压过体面形容词、每次迭代只动一个变量、按模态分档同步/异步），CLI 与端点清单不合入 |

## 基线缺口

无 skill（`uv run tools/run_evals.py generative-media --baseline`，Claude Opus 5 / medium）时，
各场景未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 本地 diffusion 复现 | 「顶部的 `torch.manual_seed` 并不是 pipeline 的种子来源，只给假信心」 | 生成器状态消费、CPU/GPU RNG、非确定性 kernel、拒绝承诺跨后端一致这四条都自己答出来了，唯独没点破这行死代码 |
| 2 掩膜编辑与合规 | 「生成记录里要有 request id」 | 写了 sidecar 与双哈希，但没有任何字段能回答「哪一次调用产生了这张图」 |
| 3 长文本 TTS | 「朗读前把 markdown 转成纯文本」「向学习者披露这是合成语音」 | **最大缺口**。markdown 清洗被明确列为「刻意没做」；披露一次都没出现——注意场景 2 的披露之所以做了，是因为用户在提问里直接问了「购物者怎么知道」，没被问到时它不会主动做 |
| 4 负例 | — | `skill_read=false`，按提示结构与结构化输出作答 |

第一轮评测的三个正例是生图复现、Veo 视频长任务、ASR 长通话，基线分别 5/5、5/6、6/6，
几乎零区分度（场景 1 甚至自行指出该生图端点根本没有 `seed` 参数）。按 `docs/workflow.md`
Phase B「基线全部达成 = 评测没有区分度」全部改写为上表三个场景。如实记录：
**Opus 5 对主流生成 API 的常规工程已经很强，本 skill 的增量集中在没被问到时仍要履行的
合规与溯源义务，以及本地 diffusion 的复现因果链。**

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 本地 diffusion | Claude Opus 5 / medium | 无 | false | 5/6 | 漏 `torch.manual_seed` 假信心 |
| 1 本地 diffusion | Claude Opus 5 / medium | 有 | true | 6/6 | 明写「`torch.manual_seed(SEED)` 对图像零影响……只提供假安全感」；五条件落盘；`--check` 跨进程比像素 sha256 |
| 2 掩膜与合规 | Claude Opus 5 / medium | 无 | false | 6/7 | 生成记录无 request id |
| 2 掩膜与合规 | Claude Opus 5 / medium | 有 | true | 7/7 | 记录含实发 prompt、运行时解析的模型 id、request id、双哈希；manifest 断链登记为 `broken_by_postprocessing` 而非伪造或剥离；策略拒绝列为一等结果且不重试 |
| 3 长文本 TTS | Claude Opus 5 / medium | 无 | false | 5/7 | 漏 markdown 清洗与合成语音披露 |
| 3 长文本 TTS | Claude Opus 5 / medium | 有（第一轮） | true | 7/7 但**结果作废** | markdown 与披露都补上了，但把 `speech.md` 里被错误泛化的「4096 字符 / 50 RPM」硬编码进了实现并用它解释根因——见下方事实更正 |
| 3 长文本 TTS | Claude Opus 5 / medium | 有（更正后重跑） | true | 7/7 | 分段预算改为运行时从 `client.models.list()` 读该模型自己声明的 `input_token_limit`，速率改为配置项而非硬编码；检查 `finish_reason=MAX_TOKENS` 并按句边界二分重切而非盲重试；markdown 展平（代码块/表格/脚注丢弃而非朗读）；披露为首段固定口播 + manifest 字段 |
| 4 负例 | Claude Opus 5 / medium | 无 | false | 3/3 | — |
| 4 负例 | Claude Opus 5 / medium | 有 | **false** | 3/3 | 负例确认不触发 |

结论：**通过**。三个正例场景各自把基线未达成的行为补齐，场景 3 的两条是本 skill 最实质的增量。
三次有 skill 运行都采用了 SKILL.md 规定的 `Generated/Record/Cost/Exposure/Notes` 输出契约。

### Phase D 事实更正：`speech.md` 的通用硬数字被证伪

第一次有 skill 运行后复核发现，`references/speech.md` 把「约 4096 字符 / 约 50 RPM」写成了**所有**
托管 TTS 端点的上限并标 `[official]`。这两个数字来自 OpenAI 的 speech 端点，被错误泛化。
实读官方 <https://ai.google.dev/gemini-api/docs/speech-generation> 的 Limitations 节：
Gemini TTS 的约束是 **「A TTS session has a context window limit of 32k tokens」**——单位是 token 不是字符，
量级也完全不同，且该页没有任何 50 RPM 的说法。

这条错误**污染了评测**：场景 3 是 Gemini TTS，有 skill 的那一轮据此把 3500 字符预算与「50 RPM 硬约束」
写进了实现并用它解释根因；基线反而自己算出了更接近事实的输出 token 上限。**增加披露这一项达标，
不能抵消注入了错误端点约束这一回归。**

更正同时违反了本 skill 自己的裁决 2（不写会过期的具体数字），说明该裁决需要在写作时逐条执行而不只是
记在 research 里。已把该节改写为：上限按供应商与模型查（并指出各家单位不同）、超限的两种失败形态
（拒绝 / 静默截断且只在 finish 或 stop reason 里体现）、速率配额对长稿墙钟时间的影响。改写后重跑场景 3。

## 备注

### 许可注意事项

- **`openai/skills` 必须逐目录读许可。** 该仓库没有顶层 LICENSE（`gh api repos/openai/skills`
  返回 `license: null`，根树只有 `.gitignore` / `README.md` / `contributing.md` / `skills`），
  但 `skills/.system/imagegen/LICENSE.txt`、`skills/.curated/speech/LICENSE.txt`、
  `skills/.curated/transcribe/LICENSE.txt` 三份逐个实读都是 Apache-2.0，可 merged。沿用
  `ai-engineering` 在 `anthropics/skills` 上得到的同一教训。
- **`ai.google.dev` 是本主题唯一可 merged 的一线厂商文档。** 页脚实读为「content licensed under
  the Creative Commons Attribution 4.0 License, code samples under the Apache 2.0 License」。
  按许可处理规则，CC-BY-4.0 → merged，**在 `SOURCES.yaml` 的 `notes` 写署名**。这与
  `ai-engineering` 得出的「Anthropic / OpenAI 文档站只能 reference」并不矛盾——那两家确实没有
  任何 licence grant，Google 开发者站有。
- **GPL 一律 reference。** `comfyanonymous/ComfyUI` 与 `Comfy-Org/docs` 都是 GPL-3.0，只取主题
  清单判断覆盖面，不 copy 任何文字，事实改从 Apache-2.0 的 diffusers 文档取证。
- **`fal-ai-community/skills` 无 LICENSE 文件**（根树实查），按规则属「无许可但公开」→ 可以
  `license: NONE` merged。**但它被降为 reference 的理由是内容裁决而不是许可**：主体是单厂商
  CLI 与会迅速腐化的端点清单。
- **`remotion-dev/remotion` 的 API `spdx_id` 是 NOASSERTION，实为 Remotion 自有许可（公司使用
  需付费）**，视同专有，不得 merged；不过它被拒的首要原因是边界（确定性渲染，不是生成）。
- **许可通过 ≠ 值得合入。** `veniceai/skills`（MIT）、`microsoft/skills` podcast-generation
  （MIT）、`google-gemini/cookbook`（Apache-2.0）、`huggingface/skills` lora-space-builder
  （Apache-2.0）四个都许可干净，分别因产品包装、产品包装、示例集、边界（改权重）被拒。

### 未来同步要盯的上游

- **`ai.google.dev/gemini-api/docs/veo` 的参数表与 Limitations 节**：24 fps、4/6/8 秒、2 天保留、
  11 秒–6 分钟延迟、区域 personGeneration 限制——本 skill 引用的硬数字几乎都在这一页，它一变
  正文就要跟着改。`kind: docs`，只能人工比对。
- **`ai.google.dev/gemini-api/docs/image-generation` 的 token 成本表**：aspect ratio → 分辨率 →
  token 数是成本一节的唯一依据，模型代际更替时整表会换。
- **`developers.openai.com` 的 audio 与 image 指南**：本次同步已见模型整代更替
  （`gpt-image-2.5-*`、`gpt-transcribe`）与新参数（`keywords`、`languages`、`languages: []` 的
  低置信信号）。本 skill 不写型号，但 `chunking_strategy`、25 MB、4096 字符这三个阈值变了要改。
- **`openai/skills` 的三个媒体 skill**：`.system/imagegen` 的 `references/image-api.md` 已经
  落后于官方型号，下次同步要重新抽查；若上游长期不更新，考虑把该 reference 的贡献降级。
- **`replicate/skills`**：`pushed_at` 停在 2026-06-04，是全部 INCLUDE 里唯一新鲜度只有 1 分的。
  若下次同步时超过 6 个月未推送，按量表要重新裁决——但它讲的是 HTTP 协议层与任务生命周期，
  真变化的概率低于分数所示，届时以「内容是否仍与 `replicate.com/docs` 一致」为准，而不是只看日期。
- **`GoogleCloudPlatform/vertex-ai-creative-studio`**：路径在 `experiments/` 下，上游有权随时
  重组；`paths` 要精确到 `experiments/mcp-genmedia/skills/`，并注意它与
  `experiments/agent_tools/plugins/genmedia/skills/` 是两套。
- **`c2pa-org/specifications`**：规范发新版本时要重读 manifest / assertion 的术语定义。

### 与相邻 skill 的边界

本 skill 覆盖：文生图 / 图生图 / 掩膜与指令式图像编辑、视频生成与视频编辑、TTS、ASR 与说话人
分离、音乐生成；提示与参数控制、种子与可复现、长任务的同步/轮询/webhook、成本与速率与配额、
产物存储与溯源（C2PA / SynthID / AI 披露）；托管 API 与本地 diffusion（ComfyUI / diffusers）
两条路径。

不覆盖（划给既有 skill）：

- 框架内置图像管线：Astro image service → `astro`；Next.js OG image 与 `next/image` → `react`；
  图片格式与 LCP 的前端取舍 → `frontend-design`。
- docx / pptx / xlsx / PDF 文档处理 → `office`。
- 通用 LLM 应用、RAG、评测与 agent 循环 → `ai-engineering`。
- 训练与微调权重（含图像模型的 LoRA / DreamBooth / 蒸馏）→ `ml-training`。
- 确定性多媒体工程：ffmpeg 命令与滤镜图、容器与编解码器选型、转码/裁剪/拼接、字幕、
  HLS/DASH 打包、图像批处理（sharp / ImageMagick / Pillow / libvips）、色彩空间与元数据、
  缩略图与雪碧图、音频规范化、ffprobe 探测 → `media-processing`。

**跨 skill 分界句（两边 SKILL.md 原文照抄，字面一致）：**

| 一对 | 分界句 |
|---|---|
| `media-processing` / `generative-media` | 同样的输入必然得到同样的字节，归 `media-processing`；输出随模型、种子或服务端版本而变，归 `generative-media` |
| `ai-engineering` / `generative-media` | 模型输出是文本或结构化数据、要接进 agent 循环或检索管道，归 `ai-engineering`；模型输出是像素、视频帧或音频采样，归 `generative-media` |
| `ml-training` / `generative-media` | 改动权重（微调、LoRA、蒸馏）归 `ml-training`；调用别人训好的权重生成或识别媒体归 `generative-media` |

三条都已按 `docs/roadmap.md`「跨 skill 分界句」表的格式写成单句、无从属子句、可直接粘贴。
第一条已同步给 `media-processing` 的调研者，两份 research 用的是同一字面。

### 这个题材特有的三个坑

1. **上游绝大多数是某家生图 SaaS 的 API 说明书。** 27 个候选里有 5 个（Venice 全家桶、fal
   genmedia、awesome-copilot generate-image、微软 podcast-generation、adamd9）本质是产品手册，
   已按「已排除主题」拒掉。过滤方法是问一句：「换一家厂商这句话还成立吗」——`cfg_scale` 的取值
   范围不成立，「CFG 过高会烧出过曝高对比」成立。
2. **模型 id 会在一次同步周期内整代更替。** 三家上游同一时点给出三套互相矛盾的型号，而官方是
   第四套。任何把型号写进正文的做法都会在三个月内变成错误答案，所以本 skill 一个模型 id 都不写
   （裁决 2）。
3. **「概率性」这件事很容易被写成免责声明。** 定稿时对每条规则问「违反它会发生什么具体的事」：
   seed 那条的后果是「你以为复现了，其实换了张卡就不一样」；2 天保留那条的后果是「第三天客户
   要原片，链接已 404」；30 秒分段那条的后果是「转写没报错，只是后面全丢了」。写不出具体后果的
   条目（「注意生成内容可能不准确」「提示词要清晰」）一律删。

## 立项判据核对

逐条对照 `docs/roadmap.md`「新增主题的判据」：

**判据 1 —— 对应一次真实任务的完整上下文，不需要同时加载另一个同级 skill 才能干活。满足。**
一次典型任务「给这段脚本配音、配一张封面、出一条 8 秒宣传片，并把产物存下来」在本 skill 内闭环：
选能力而不是选型号 → 写提示与参数 → 按模态决定同步还是轮询 → 处理安全过滤与重试 → 落盘与溯源。
唯一会外溢的是最后的转码与封装（封 WAV 容器、合流、压制），那本来就是 `media-processing` 的活，
且分界句已写死，不构成「必须同时加载」。

**判据 2 —— 至少 3 个活跃（6 个月内有推送）、总分 ≥8 的上游。远超，满足。**
达标且活跃的有 12 个：`openai/skills` 的 transcribe(14) / speech(14) / imagegen(12)，
`ai.google.dev` 官方文档(14，CC-BY-4.0)，`GoogleCloudPlatform/vertex-ai-creative-studio`(14)，
`huggingface/diffusers`(14)，`openai/whisper`(14)，`c2pa-org/specifications`(14)，
`ggml-org/whisper.cpp`(13)，`replicate/skills` 的 run-models / prompt-images / prompt-videos
(各 12，2026-06-04 推送，在 6 个月内)。其中**可 merged 的许可**（Apache-2.0 / MIT / CC-BY-4.0）
占全部 12 个，不存在「分数够但全是 GPL/专有」的问题。

**判据 3 —— 不是既有 skill 的子集。满足。正面回答「为什么不是 `ai-engineering` 的子集」：**

`ai-engineering` 的主题是「让一个语言模型在应用里可靠地产出**文本或结构化数据**」，它的全部核心
机制都建立在这个输出类型上——provider 强制的结构化输出与 schema 方言、RAG 的切块与重排与相关性
下限、agent 循环的终止条件与工具授权、evals 的逐例判定与 judge、以及从工具结果进来的提示注入。
把这五样搬到生成媒体上，没有一样能直接用：

- **没有 schema。** 输出是一张 PNG 或一段 24 fps 的 mp4，没有 `response_format` 能约束「这只手
  有五根手指」。`ai-engineering` 里「校验 ≠ 授权」的那套对账机制在这里连第一步（校验）都无从落地，
  取而代之的是完全不同的一组控制手段：invariants 逐轮重申、掩膜的提示语义、参考图与角色一致性、
  安全过滤器的临床式改写。
- **没有 token 预算，有 GPU 秒与保留期。** 成本模型不是上下文窗口，而是 aspect ratio → 分辨率 →
  token 的换算表、官方模型按次计价 vs 社区模型按 GPU 秒计价、以及「11 秒到 6 分钟」的延迟分布。
  与之配套的是 `ai-engineering` 完全不涉及的一层：**产物生命周期**——输出 URL 1 小时过期、
  服务端 2 天删除，因此「下载并另存」是流程步骤而不是优化。
- **没有「一次请求一次响应」。** 视频与音乐是长任务，本 skill 一半的工程内容是同步/轮询/webhook
  的选择与验签、request id 的持久化、跑飞任务的 `lifetime` 取消。`ai-engineering` 的循环讲的是
  模型与工具的多轮交互，不是一个作业跑六分钟。
- **可复现的定义不同。** `ai-engineering` 靠 `temperature=0` 与 pin 带日期的模型快照；本 skill
  面对的是 `Generator` 状态被消费、CPU 与 GPU 是不同 RNG、`enable_full_determinism` 要付性能
  代价、以及托管 API 上「seed 不保证确定性」。这是两套不同的因果链。
- **治理义务不同。** 本 skill 有一层 `ai-engineering` 完全没有的强制项：SynthID / C2PA 内容凭证
  不可关闭，AI 生成语音必须向终端用户披露。这不是「安全建议」，是平台条款与规范。

反过来说，本 skill **也不是 `media-processing` 的子集**：`media-processing` 的每条规则都建立在
「同样的输入得到同样的字节」之上，而本 skill 的每条规则都在处理这个前提不成立之后的后果。
两者的交界（PCM 封 WAV、16 kHz 重采样、生成片段的合流与压制）已由分界句切开。

**判据 4 —— 官方厂商特例。不适用。** 本主题不是单一官方上游改写：合入清单里有 OpenAI、Google
（skills 与文档两处）、Hugging Face、Replicate、C2PA 五方，跨厂商正是它的立项理由之一。
因此 `research/generative-media.md` 标题下**不写**「单一权威上游改写」。

**结论：够格立项。** 判据 1、2、3 全部满足，判据 4 不适用且无需适用。主干上游为
`openai/skills` 的三个媒体 skill + `ai.google.dev`（CC-BY-4.0 官方文档）+ `replicate/skills`
+ `GoogleCloudPlatform/vertex-ai-creative-studio`，辅以 `diffusers` / `whisper` / `c2pa` 三个
本体仓库；ComfyUI（GPL）与两家厂商文档站（专有）作 reference。
