# media-processing 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：2026-09-11（本文件全部 stars / `pushed_at` / license 于当日用**已登录的 `gh`**（账号 Lynricsy，5000/h 配额）实测；`gh auth status` 通过，未触发限流；未使用任何匿名 HTTP，未从仓库网页猜数字）
- 检索途径：
  - `gh search repos`：`ffmpeg skill`、`video transcode skill`、`imagemagick skill`、`image optimization skill`、`ffprobe skill`、`media processing skill`、`subtitle skill`、`video editing skill`、`claude skill video editing`、`sharp image skill`、`libvips skill`、`hls packaging skill`
  - `gh search code`：`ffmpeg filename:SKILL.md`、`image-optimization filename:SKILL.md`、`video-processing filename:SKILL.md`、`audio-processing filename:SKILL.md`、`media-toolkit filename:SKILL.md`、`sharp filename:SKILL.md`、`imagemagick filename:SKILL.md`、`libvips filename:SKILL.md`、`exiftool filename:SKILL.md`、`thumbnail filename:SKILL.md`、`HLS filename:SKILL.md`、`loudnorm filename:SKILL.md`、`sharp resize filename:SKILL.md`
  - 多技能聚合仓库按树 grep（`gh api repos/<r>/git/trees/HEAD?recursive=1`）：`github/awesome-copilot`、`VoltAgent/awesome-agent-skills`、`addyosmani/agent-skills`、`wshobson/agents`、`samber/cc-skills`、`anthropics/skills`、`obra/superpowers`、`TerminalSkills/skills`、`damionrashford/media-os`、`agentskillexchange/skills`
  - `web_search`：`"ffmpeg" agent skill SKILL.md github 2026`（命中 `dcloud/agent-skills`、`sakydev/claude`、`bryanwhl/ffmpeg-video-editor`、skills.sh / claudeskills.info 的 ffmpeg 条目）
  - 官方文档直读：`trac.ffmpeg.org/wiki/{Seeking,Encode/H.264,Encode/VP9,Encode/AV1}`、`sharp.pixelplumbing.com/api-{operation,output}`
  - 本机实测（ffmpeg N-126134-gc48230eb86-20260814、vips 8.18.6、Pillow 12.3.0）：见「本机实验」节
  - 同批兄弟 agent `GenMediaResearch` 提供的跨边界线索：`GoogleCloudPlatform/vertex-ai-creative-studio` 的 `genmedia-*` 三个 skill
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`；读原文用
  `gh api repos/<owner>/<repo>/contents/<path> --jq '.content' | base64 -d`，先用
  `gh api repos/<owner>/<repo>/git/trees/HEAD?recursive=1 --jq '.tree[].path'` 列树定位路径。

**聚合器结论（重要，避免下轮重复搜）**：`github/awesome-copilot`（38842★）、`VoltAgent/awesome-agent-skills`、
`addyosmani/agent-skills`、`wshobson/agents`、`samber/cc-skills`、`anthropics/skills`、`obra/superpowers`
**全部没有多媒体工程 skill**。awesome-copilot 树里唯一沾边的是 `skills/generate-image` 与
`plugins/skill-image-gen`（属 `generative-media`）。本主题的上游全部来自独立仓库与少数领域聚合仓
（`TerminalSkills/skills`、`damionrashford/media-os`）。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。
「正确」列为抽查 3 条规则对官方文档/本机复现的结果；得 0 直接 REJECT。新鲜度以 2026-09-11 为基准。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kajisho5/ffmpeg-skill | https://github.com/kajisho5/ffmpeg-skill | 950 | 2026-09-11 | MIT | 42 个 Python 脚本包住 ffmpeg：probe/cut/fit/caption/color/loudness/check/look/render | 2 | 3 | 3 | 3 | 2 | **13** | **INCLUDE（主干）** | 本主题事实上的标杆。工作流（probe→plan→execute→check→look）、「机械 vs 判断」分界、VFR/HDR/关键帧/CJK 字体五类陷阱，都是可执行规则而非教程。抽查三条全对（见深度审查） |
| 2 | GoogleCloudPlatform/vertex-ai-creative-studio `experiments/mcp-genmedia/skills/{genmedia-video-editor,genmedia-audio-engineer,genmedia-producer}` | https://github.com/GoogleCloudPlatform/vertex-ai-creative-studio | 1205 | 2026-09-11 | Apache-2.0 | 一半 Veo/Lyria/TTS 生成，一半 ffmpeg 合成 | 3 | 3 | 2 | 3 | 2 | **13** | **INCLUDE（按边界只取 ffmpeg 操作部分）** | 唯一的官方厂商上游。取：overlay 前必须先 `get_media_info` 再算坐标、GIF 两遍法默认 `fps=15`+0.33 缩放、concat 前要求同尺寸同帧率、layer 前要求同采样率（否则变调）、人声/配乐相对增益与 `afade` 收尾。生成侧（Veo/Lyria/Chirp/Gemini TTS）归 `generative-media`，已与 `GenMediaResearch` 约定 |
| 3 | TerminalSkills/skills `skills/ffmpeg` | https://github.com/TerminalSkills/skills | 149 | 2026-09-04 | Apache-2.0 | 转码/剪辑/拼接/字幕/缩略图/GIF/水印/响度 + yt-dlp 管线 | 1 | 3 | 2 | 3 | 2 | **11** | **INCLUDE** | 许可最干净的「通用 ffmpeg 手册」型上游。`-c copy` 仅在编解码已匹配时可用、`+faststart`、拼接前统一 `scale+pad+ar` 的做法都对；但 loudnorm 只给单遍式（见 C7） |
| 4 | damionrashford/media-os `skills/ffmpeg-*`（110 个 skill 目录） | https://github.com/damionrashford/media-os | 19 | 2026-05-31 | MIT | 按 ffmpeg 子领域切成 40+ 个独立 skill：cut-concat、streaming(HLS/DASH/RTMP/SRT)、hdr-color、lut-grade、hwaccel、bitstream、probe、quality、subtitles、audio-filter… | 1 | 1 | 3 | 3 | 2 | **10** | **INCLUDE** | star 少但内容最硬。是**唯一**正确写出「现代 ffmpeg 的输入侧 `-ss` 在重编码时已经是精确的」的候选（C1），也是唯一系统覆盖 HLS/DASH 打包（`-g = fps × segment_time`、`-sc_threshold 0`、`hls_flags delete_segments`、fMP4/CMAF）的候选 |
| 5 | n0an/ffmpeg-skill | https://github.com/n0an/ffmpeg-skill | 8 | 2026-09-08 | MIT | 6 个 references：glossary / simple-editing / audio / advanced / asset-generation / encoding-tuning | 1 | 3 | 3 | 1 | 2 | **10** | **INCLUDE（部分）** | 规则密度极高（`setpts=PTS-STARTPTS`、`-vtag hvc1`、`setsar` 与 pad、`-shortest`+`duration=shortest`、CRF ±6 ≈ 倍半码率、CRF 无法限大小要两遍 ABR）。**但抽查命中一处硬错**：主张「帧精确裁剪要用输出侧 `-ss`」，与官方 Seeking wiki 冲突（C1）；`-preset veryslow` 作默认也被否（C4） |
| 6 | maxazure/video-editing-skill | https://github.com/maxazure/video-editing-skill | 189 | 2026-09-10 | **无（API `license: null`）** | 小红书/抖音/视频号短视频端到端流水线（180 KB SKILL.md + 120 个 prompt 文档） | 1 | 3 | 3 | 3 | 0 | **10** | **INCLUDE（部分）** | 创作流程部分不要；只取三块确定性内容：① HDR→SDR 必须 `zscale`+`tonemap` 在 linear-light 做、色彩标签不明确就 fail closed；② 交付前 review proxy（720p/24fps/`+faststart`/烧时间码）；③ 每次 apply 前校验 H.264/AAC + `yuv420p` + 尺寸/fps/时长/声道 + 完整解码才原子提升。许可为空，按 roadmap「无许可但公开」→ merged + `license: NONE` |
| 7 | TerminalSkills/skills `skills/imagemagick` | 同 #3 | 149 | 2026-09-04 | Apache-2.0 | `magick`/`mogrify`/`identify`/`montage`，批量改尺寸、缩略图、水印、PDF 首页 | 1 | 3 | 2 | 1 | 2 | **9** | **INCLUDE（部分）** | 图像侧唯一许可干净且活跃的 CLI 上游。`-auto-orient`、`-strip`、`-density` 转 SVG/PDF、`mogrify` 批量都对；**一处错**：注释把 `-resize 800x600^` 说成「Fill（crop overflow）」，`^` 只保证最小边覆盖，不裁剪，必须再加 `-gravity center -extent 800x600`（它后面的缩略图配方其实写对了，是注释错） |
| 8 | TerminalSkills/skills `skills/sharp` | 同 #3 | 149 | 2026-09-04 | Apache-2.0 | Node 端 sharp：resize/fit、WebP/AVIF、responsive 变体、composite 水印、metadata/stats | 1 | 3 | 2 | 1 | 2 | **9** | **INCLUDE（部分）** | 唯一覆盖 sharp（libvips 绑定）的活跃候选。`fit:'inside'+withoutEnlargement`、`fit:'cover'`、SVG 转文字水印、`.stats()` 都对；**一处错**：把 `.withMetadata({orientation:undefined})` 当作「剥离 EXIF/ICC」，实际语义相反（C6，官方文档：sharp 默认就剥离全部 metadata，`withMetadata`/`keepMetadata` 是**保留**） |
| 9 | DabRlin/ffmpeg-skills | https://github.com/DabRlin/ffmpeg-skills | 0 | 2026-08-06 | Apache-2.0 | ffmpeg/ffprobe/ffplay 命令构造，强调环境能力探测 | 0 | 2 | 2 | 3 | 2 | **9** | **INCLUDE（部分）** | 零 star，但有一条别家都没有的立场：**编码器/硬件加速能力必须每台机器实测**（`-encoders \| grep`、`-hwaccels`），不得凭上一台机器的经验选 `*_nvenc`/`*_qsv`/`*_vaapi`。只取这一条与其回退顺序 |
| 10 | chang416/cutcraft `skills/cutcraft` | https://github.com/chang416/cutcraft | 51 | 2026-08-14 | MIT | 对话式成片工作流（工作区、逐字稿、字幕、素材授权） | 0 | 3 | 2 | 3 | 2 | **10** | **INCLUDE（部分）** | 主体是创作流程，不取。只取一条：**烧录字幕前先渲染三张字幕预览图让人选**——把「字幕样式是否可读」从事后返工提前成一道可看的门，正好补 kajisho `look.py`（事后）的前置缺口 |
| 11 | einverne/dotfiles `claude/skills/imagemagick` | https://github.com/einverne/dotfiles | 121 | 2026-09-09 | **GPL-3.0**（仓库）/ frontmatter 自称 MIT | ImageMagick 命令指南 | 1 | 3 | 2 | 3 | 0 | **9** | **REFERENCE ONLY** | 内容无误（v7 `magick` 统一入口、`convert` 为遗留命令、`mogrify` 原地改写的危险），但仓库许可是 GPL-3.0，frontmatter 的 `license: MIT` 不可信。按 roadmap「GPL → reference」：只用它的主题清单核对覆盖面，**不复制任何文字** |
| 12 | muhammaddadu/ffmpeg-skill | https://github.com/muhammaddadu/ffmpeg-skill | 1 | 2026-06-01 | MIT | 配方库 + 成片流水线（`ffmpeg-usage` v2.0.0） | 0 | 1 | 2 | 3 | 2 | **8** | **MAYBE→不采用** | 配方本身没错，但全部被 #1/#5 覆盖；「把 ffmpeg 当最终合成器与编码器，资产设计交给别的工具」这条立场已由 #1 的「本 skill 只执行参数，不做判断」以更严格的形式表达 |
| 13 | ychoi-kr/claude-ffmpeg-skill | https://github.com/ychoi-kr/claude-ffmpeg-skill | 46 | **2025-10-19** | MIT | 通用 ffmpeg skill | 1 | **0** | 2 | 3 | 2 | 8 | **REJECT（新鲜度硬性）** | 近 11 个月无推送，破 6 个月线，且非官方，不适用例外。分数看着够但按量表新鲜 0 直接出局；内容已被 #1/#3 完全覆盖 |
| 14 | Jaycheng1103/chatgpt-video-editing-skills | https://github.com/Jaycheng1103/chatgpt-video-editing-skills | 529 | 2026-07-26 | MIT | 「ChatGPT 剪短影音八大步驟」提示词工作流 + 环境 setup runbook | 0 | 2 | 1 | 3 | 2 | 8 | **REJECT（范围外）** | star 高，但 `references/{eight-step-workflow,production-rules,output-contract}.md` 全是内容创作方法论与 ChatGPT 环境配置，没有一条确定性媒体工程规则。属内容生产，不属本 skill |
| 15 | thedaviddias/Front-End-Checklist `skills/image-optimization`、`skills/video` | https://github.com/thedaviddias/Front-End-Checklist | 74101 | 2026-08-14 | 无（`license: null`） | 前端图片交付审计、VideoObject 结构化数据 | 1 | 3 | 1 | 3 | 0 | 8 | **REJECT（否定边界）** | 内容正确但整条落在 `frontend-design`（LCP/CLS、`srcset`/`sizes`、`loading=lazy`、`fetchpriority`）与 SEO（VideoObject JSON-LD）上，正是本 skill 明文划走的部分 |
| 16 | MastroMimmo/ffmpeg-skill | https://github.com/MastroMimmo/ffmpeg-skill | 16 | 2026-03-16 | MIT | 单文件 `ffmpeg.md` + `scripts/fftools.py`（22 KB）包住 info/cut/merge/gif/thumbnail/compress/speed/watermark | 0 | 1 | 1 | 3 | 2 | **7** | **MAYBE→不采用** | 命令本身没错（GIF 两遍法、`merge --reencode` 处理异构源），但 SKILL.md 基本是自家脚本的参数表，不含 ffmpeg 层面的陷阱；与 #1 同形状而弱一个量级 |
| 17 | sakydev/claude `skills/ffmpeg` | https://github.com/sakydev/claude | 0 | 2026-08-04 | 无（`license: null`） | 精简 ffmpeg 规则页 | 0 | 2 | 2 | 3 | 0 | **7** | **MAYBE→部分采纳** | 三条「硬规则」值得借鉴形状：① 绝不覆盖原文件，输出名从输入派生；② **质量下限表**（x264 crf ≤28、x265 ≤32、vp9 ≤40、AAC ≥128k），目标体积要求突破下限时明说做不到；③ 输入 >1 GB 先停下来确认。#1 已有 ①，②③ 可吸收 |
| 18 | IgorVaryvoda/image-optimization-skill | https://github.com/IgorVaryvoda/image-optimization-skill | 0 | 2026-07-03 | 无（`license: null`） | Sirv CDN 系列 skill + image/video optimization | 0 | 2 | 2 | 3 | 0 | **7** | **REJECT（范围外 + 产品包装）** | `skills/sirv-*` 七个是某 SaaS 的 API 说明书（roadmap 已排除此类）；`image-optimization` 主体是 LCP/CLS/srcset/CDN 交付 → `frontend-design`。仅 `references/tools.md` 有少量 squoosh/sharp CLI 内容，不足以支撑一行合入 |
| 19 | hufang360/ffmpeg-skill | https://github.com/hufang360/ffmpeg-skill | 0 | 2026-08-02 | 无（`license: null`） | 中文速查手册（19 章：安装/转换/提音频/裁剪/CRF/delogo/WebP转PNG/拼接/水印/GIF/字幕/硬件加速…） | 0 | 2 | 2 | 1 | 0 | **5** | **MAYBE→不采用** | frontmatter 的 TRIGGER / DO NOT TRIGGER / REQUIREMENT 三段式写法值得借鉴（否定边界写在 description 里）。但「WebP 转 PNG」「图片格式转换」用 ffmpeg 做是错路线：本机实测 ffmpeg 走一遍 JPEG 会**静默丢掉全部 EXIF**（C10） |
| 20 | agentskillexchange/skills `skills/libvips-…`、`skills/ffmpeg-video-processing-pipeline` | https://github.com/agentskillexchange/skills | 38 | 2026-09-11 | MIT | 上千个 1–2 KB 的 skill 条目 | 0 | 3 | **0** | — | 2 | **5** | **REJECT** | 内容是脚本抓取上游 README 后拼接（正文里直接写着 "Extracted from upstream docs: https://raw.githubusercontent.com/libvips/libvips/HEAD/README.md"），只有安装说明和一句简介，零可执行规则 |
| 21 | keiloktql/media-toolkit | https://github.com/keiloktql/media-toolkit | 0 | 2026-05-21 | MIT | 单一脚本 `lrf_to_proxy.sh`（DJI LRF → 剪辑代理） | 0 | 1 | 1 | 3 | 2 | **7** | **MAYBE→不采用** | SKILL.md 仅 1823 B，围绕一个厂商特定工作流；「先生成低码率代理再剪」这条已由 #1 的 `proxy.py` 与 #6 的 review proxy 覆盖 |
| 22 | chunpu/ffmpeg-skills `skills/ffmpeg-{video,audio,image}-processing` | https://github.com/chunpu/ffmpeg-skills | 7 | 2026-03-12 | 无（`license: null`） | 三个中文命令速查 skill | 0 | 1 | 1 | 1 | 0 | **3** | **REJECT** | 纯 cheatsheet。`ffmpeg -i input.png -q:v 2 output.jpg` 注释成「质量 85」不成立（mjpeg `-q:v` 是 2–31 的量化尺度，2 约等于 q≈90+，且与 JPEG「quality」不是一个刻度）；转码示例普遍缺 `-pix_fmt yuv420p` 与 `+faststart`；用 ffmpeg 做静图批处理会丢 EXIF |
| 23 | dcloud/agent-skills `skills/ffmpeg` | https://github.com/dcloud/agent-skills | 0 | 2026-08-22 | 无（`license: null`） | SKILL.md + 7 个 references（filters 20 KB、color-grading 9 KB、encoding-formats 7 KB…） | 0 | 3 | 3 | **0** | 0 | 6 | **REJECT（正确性 0 强制出局）** | 结构与密度都很好（`-h filter=<name>` 的 live help、`haldclut` 色彩流程、`ffv1`/png 序列做无损中间件），**但 AV1 一节两处硬错**：① 称 libsvtav1「CRF 默认 0」，实际生效默认是 35（官方 AV1 wiki + 本机 SVT 日志 `BRC mode / rate factor : CRF / 35.00`）；② 称 `-b:v 0` 用来「启用 CRF 模式」，那是 libaom-av1 在 FFmpeg 4.3 之前的要求，对 libsvtav1 不成立（CRF 本来就是默认 BRC 模式）。另「preset 默认 -2 约等于 10」本机实测解析为 preset 8。量表规定正确 0 直接 REJECT；其章节标题仍可作主题清单参照 |
| 24 | bryanwhl/ffmpeg-video-editor | https://github.com/bryanwhl/ffmpeg-video-editor | 7 | **2026-03-03** | MIT | 滤镜/编解码/转场/硬件加速 references + probe/concat/normalize 脚本 | 0 | **0** | 2 | 3 | 2 | 7 | **REJECT（新鲜度硬性）** | 6 个月零 8 天无推送，破线；内容（两遍 loudnorm 脚本、硬件加速矩阵）已分别由 #4、#9 覆盖 |
| 25 | m4dc4p/claude-hls `skills/hls-troubleshooting` | https://github.com/m4dc4p/claude-hls | 31 | 2026-01-07 | MIT | — | 0 | 0 | 0 | — | 2 | **2** | **REJECT（名称撞车）** | 搜索 `HLS filename:SKILL.md` 的头部命中，但这里的 HLS 是 **Haskell Language Server**，与 HTTP Live Streaming 无关。留行以免下轮再点进去 |
| 26 | 官方文档 — FFmpeg Filters（`ffmpeg.org/ffmpeg-filters.html`） | https://ffmpeg.org/ffmpeg-filters.html | — | 持续维护 | GPL/LGPL（随 FFmpeg 发布） | 全部滤镜的参数语义：`scale`/`pad`/`crop`/`setsar`/`overlay`/`subtitles`/`drawtext`/`loudnorm`/`amix`/`concat`/`zscale`/`tonemap` | 3 | 3 | 3 | 3 | 1 | **13** | **INCLUDE（docs）** | 所有滤镜事实的第一来源。**只取参数语义，不复制文字，示例全部自写**（许可分给 1 并在 `notes` 记录） |
| 27 | 官方文档 — Encode/H.264 wiki | https://trac.ffmpeg.org/wiki/Encode/H.264 | — | 官方 wiki | 无明示许可（trac wiki） | CRF 尺度、preset 取舍、两遍 ABR、`+faststart`、lossless | 3 | 3 | 3 | 3 | 1 | **13** | **INCLUDE（docs）** | 裁决 C4/C8 的依据：「0–51，默认 23，合理区间 17–28，17/18 视觉无损」「用你能忍的最慢 preset」「`veryslow` 比 `slower` 只有极小提升却要 280% 时间」「浏览器播放加 `-movflags +faststart`」 |
| 28 | 官方文档 — Encode/VP9 wiki | https://trac.ffmpeg.org/wiki/Encode/VP9 | — | 官方 wiki（最后修改 2024-01-08） | 无明示许可 | VP9 的五种码率控制模式 | 3 | 2 | 3 | 3 | 1 | **12** | **INCLUDE（docs）** | 裁决 C3 的依据：恒定质量「必须 `-crf` 配 `-b:v 0`，`-b:v` **MUST** be 0；设成别的值或省略都会落进 Constrained Quality」。页面 >6 个月未改，但属官方且内容仍准确，按量表例外保留 |
| 29 | 官方文档 — Encode/AV1 wiki | https://trac.ffmpeg.org/wiki/Encode/AV1 | — | 官方 wiki | 无明示许可 | libaom / SVT-AV1 / rav1e / AMF 的 CRF、preset、keyint、film-grain | 3 | 3 | 3 | 3 | 1 | **13** | **INCLUDE（docs）** | 裁决 C2 的依据：「libsvtav1 CRF 范围 0–63，**默认 35**」「CRF 是默认的码率控制方式」「`-b:v 0` 的要求是 libaom 在 4.3 之前的事」「SVT-AV1 默认关键帧间隔只有 2–3 秒，要用 `-g` 调大」 |
| 30 | 官方文档 — Seeking wiki | https://trac.ffmpeg.org/wiki/Seeking | — | 官方 wiki（最后修改 2025-05-01） | 无明示许可 | 输入侧/输出侧/组合 seek 的语义 | 3 | 1 | 3 | 3 | 1 | **11** | **INCLUDE（docs）** | 裁决 C1 的依据：「自 FFmpeg 2.1 起，转码（非流复制）时 `-ss` 作为输入选项**也是帧精确的**」「`-c copy` 时只能切在关键帧」「配 `concat` demuxer 要加 `-avoid_negative_ts`」 |
| 31 | 官方文档 — FFmpeg Formats（hls / dash / segment muxer） | https://ffmpeg.org/ffmpeg-formats.html | — | 持续维护 | GPL/LGPL | `hls_time`/`hls_list_size`/`hls_flags`/`hls_segment_type fmp4`/`hls_playlist_type`、dash muxer、`segment` muxer、`-movflags` | 3 | 3 | 3 | 3 | 1 | **13** | **INCLUDE（docs）** | HLS/DASH 打包全部参数语义的来源；#4 给覆盖面，参数取值以此为准 |
| 32 | 官方文档 — sharp | https://sharp.pixelplumbing.com/ | — | 持续维护 | Apache-2.0（sharp 本体） | `resize`/`fit`、`rotate`/`autoOrient`、`keepMetadata`/`withMetadata`、`toFormat`、`composite` | 3 | 3 | 3 | 3 | 2 | **14** | **INCLUDE（docs）** | 裁决 C6 的依据：「默认移除全部 metadata，包括基于 EXIF 的朝向」「`keepMetadata()` 保留 EXIF/ICC/XMP/IPTC；不用它时会转到 sRGB 并剥掉 ICC」「无参 `rotate()` 出于向后兼容等于 `autoOrient()`」 |
| 33 | 官方文档 — ImageMagick command-line options | https://imagemagick.org/script/command-line-options.php | — | 持续维护 | ImageMagick License(ASL-2.0 兼容) | `-resize` 几何后缀（`^` `!` `>` `<` `%`）、`-extent`/`-gravity`、`-auto-orient`、`-strip`、`-density`、`-colorspace` | 3 | 3 | 3 | 3 | 2 | **14** | **INCLUDE（docs）** | 裁决 C9（几何后缀语义）的依据；也是 v7 `magick` vs 遗留 `convert` 的权威说法来源 |
| 34 | 官方文档 — libvips | https://www.libvips.org/API/current/ | — | 持续维护 | LGPL-2.1（库）/ 文档同源 | `thumbnail`（含 shrink-on-load）、`smartcrop`、ICC 转换、序列化访问模式 | 3 | 3 | 3 | 3 | 1 | **13** | **INCLUDE（docs）** | 大批量缩略图的正解（`vips thumbnail` 的 shrink-on-load 比「先解码全图再 resize」快一个量级）；LGPL 只影响链接本体，文档事实照常取用但不复制文字 |
| 35 | 官方文档 — Pillow | https://pillow.readthedocs.io/en/stable/ | — | 持续维护 | MIT-CMU | `Image.open`/`draft`、`ImageOps.exif_transpose`、`save(quality=, progressive=, subsampling=, icc_profile=)` | 3 | 3 | 3 | 3 | 2 | **14** | **INCLUDE（docs）** | Python 侧图像处理的事实来源；`exif_transpose` 是「EXIF 朝向必须显式处理」这条规则在 Pillow 上的落点 |
| 36 | 官方标准 — EBU R 128 / ITU-R BS.1770-5 | https://tech.ebu.ch/publications/r128 | — | 标准文本 | EBU/ITU 版权，仅引用 | 整合响度 (LUFS)、LRA、真峰值 (dBTP)、门限 | 3 | 3 | 3 | 3 | 0 | **12** | **INCLUDE（docs, 仅引用）** | 响度目标与真峰值的定义来源；`loudnorm` 的 `I`/`LRA`/`TP` 三参语义与默认值（本机 `-h filter=loudnorm`：I=-24、LRA=7、TP=-2）对照于此。**不复制标准文本**，只引用其定义与本 skill 自写的平台目标表 |

## 深度审查

### #1 kajisho5/ffmpeg-skill（950★，MIT，2026-09-11，总分 13，主干）

**结构**：仓库根 `SKILL.md`（33 KB / 340 行）+ `scripts/`（42 个 Python 脚本）+ `docs/contract.md`（23 KB）+
`evals/`（真跑过的多轮评测结果 JSON）+ `.claude/skills/`（另 13 个与本主题无关的工程类 skill）。
**frontmatter** 只有 `name: ffmpeg-skill` 与一段极长的 `description`——把触发词直接铺开写
（"mp4, mov, mkv, wav, m4a、footage、clip、captions、reel、YouTube/Instagram/TikTok delivery、LUFS、sync、transcoding"），
这是本仓库标准第 1.1 节要的形状，只是它没有写否定边界（否定边界被放进正文的
"What this skill does and does not decide" 一节）。

**质量**：这是候选里唯一把「工作流」写成可失败的门的：

0. 不熟悉的机器先跑一次 `doctor --json`，检查 `usable`——缺 `libass`/`zscale`/编码器要**报告能力缺失**，
   而不是等运行时报错；且明说 `doctor` 查的是 `ffmpeg -filters`/`-encoders`，不便宜，每会话一次就够。
1. 任何输入先 `probe.py`，读时长/fps/分辨率/编解码/声道与 `variable_frame_rate_suspected`。
2. 能不重编码就不重编码（关键帧对齐的切、remux、纯音频改动）。
3. `--dry-run --json` 先出计划再执行；并特别指出**只能信 `--json`，不能信 dry-run 那行人话摘要**
   （里面的尺寸可能是占位符而非计算结果）。
4. 固定链路顺序：颜色（HDR→SDR / LUT）→ 切 → 拼 → 去静音 → 改画幅 → 字幕/叠加 → 同步 → 音频 → 响度 → 导出；
   并给出理由：**画幅变化必须在字幕/叠加之前**，否则文字尺寸按错误的画面算。
5. `check.py --platform X`，且把检查结果分成 `format`（编解码、像素格式、尺寸、真峰值、色彩标签、VFR——可机械修）
   与 `judgement`（时长、画幅、fps、响度——改了就改变内容，必须让人决定）两类。这个二分是整份文档最有价值的结构。
6. `probe.py` 复核输出；**「写出命令不等于做完事情」**，非零退出/空文件/与请求矛盾的 probe 都算失败。
7. 绝不覆盖原文件。
8. 画面变了就 `look.py` 出 contact sheet 并**真的去看**；没有视觉能力时必须写
   `Look: PATH (pixels not inspected; agent has no image view)`，**不许谎称看过**。

**具体规则抽查（3 条，全对）**：
- 「`yuv420p` 需要偶数宽高，`fit.py`/`export.py` 自动取偶」——本机复现：`-vf scale=321:241 -c:v libx264` 直接报
  `width not divisible by 2 (321x241)` 并使输出文件不可用（moov atom not found）。
- 「`-c copy` 的切可能比请求早最多一个 GOP（常见 1–10 s），偏差超 0.5 s 就自动改重编码」——与官方 Seeking wiki
  「`-c copy` 时只能切在 I 帧」一致，且给出了比官方更可操作的阈值化处理。
- 「VFR 时每个重编码脚本都加 `-fps_mode cfr` 按平均帧率归一，`cut.py` 自动切到 `--accurate`」——`-fps_mode`
  是 `-vsync` 的现代写法，语义正确。

其余高价值论断（未计入抽查但已核对方向无误）：HDR 源默认保持 HDR（HEVC Main10 + 源色彩标签）而不是静默压成
SDR；Log 素材（S-Log/V-Log/C-Log）标签是 SDR 但画面灰平，要先 `probe --analyze` 看 `looks_like_log` 再上 `.cube`；
libass/drawtext 缺字形只会出豆腐块**不会报错**，所以 CJK 必须先 `fc-list :lang=ja file` 验字体；
某些 Windows ffmpeg 构建（winget 的 gyan.dev）在 `drawtext` 按族名走 fontconfig 时会访问违例崩溃，所以默认解析出
具体 `--font-file`；`sync.py`/`multicam.py` 对齐的是**音轨**，confidence 高不代表口型对得上，本 skill 里没有任何
人脸/嘴部检测。

**agent 绑定**：几乎为零——`SKILL.md` 不引用任何 agent 专有机制，只要求 `python3 <skill-dir>/scripts/<name>.py`
和「能看 PNG」。报告格式固定五行（`Done:` / `Steps:` / `Check:` / `Look:` / `Notes:`），字段名保持英文、
句子跟随用户语言。这个「产出一个可核查的交付报告」的形状可直接借鉴。

**与其他候选的重叠**：覆盖面上它是 #3/#5/#12/#16/#17 的超集。与 #4 互补——#4 有 HLS/DASH 打包与
bitstream/IVTC/MXF 这类 #1 没有的专业条目，#1 有 #4 没有的「交付门 + 报告格式 + 判断/机械二分」。
唯一不重叠的短板：**图像批处理（sharp/ImageMagick/libvips/Pillow）、EXIF/ICC、雪碧图它一条都没有**——
那部分要靠 #7/#8 与官方文档 #32–#35 自写。

### #2 GoogleCloudPlatform/vertex-ai-creative-studio `genmedia-*`（1205★，Apache-2.0，2026-09-11，总分 13）

**结构**：`experiments/mcp-genmedia/skills/` 下三个目录，每个只有一个 SKILL.md（video-editor 3619 B、
audio-engineer 约 3.4 KB、producer 若干）。**frontmatter 有 `allowed-tools` 白名单**，逐个列出
`mcp_avtool_ffmpeg_*` 与 `mcp_veo_*`/`mcp_lyria_*`/`mcp_chirp3-hd_*` 工具名，以及 `metadata.veo_prompting_guide`
这样的外链。这是强 agent 绑定：**离开它那套 mcp-genmedia Go 服务器，工具名全部失效**。

**质量（只看归本 skill 的 ffmpeg 那一半）**：规则少但都是「顺序型」约束，且恰好是 agent 最常跳过的：
- 叠加图片前**先 `ffmpeg_get_media_info` 取源视频尺寸再算 (x,y)**，并明确左上是 `0:0`、右下是
  `width-overlay_width : height-overlay_height`。别家都直接给 `overlay=W-w-10:H-h-10`，没说「先量再算」。
- GIF 走**两遍法**，默认 `fps=15` + `scale_width_factor=0.33`，除非用户明确要更高。
- **拼接前必须尺寸与帧率一致**；不一致时要**告诉用户工具会先做一次标准化重编码**（而不是悄悄重编码）。
- 音视频合流前先量音频时长，再让视频对齐；已有音轨时会自动混音，用
  `input_video_volume_db_change` / `input_audio_volume_db_change` 调相对电平。
- audio-engineer 侧（归本 skill 的部分）：**多轨叠加前采样率必须一致，否则会变调**；长稿分段合成后用
  `ffmpeg_concatenate_media_files` 拼接；WAV→MP3 用专门的转换工具而不是随手改扩展名。

**正确性抽查（3 条，全对）**：叠加坐标公式正确；GIF 两遍法（palettegen/paletteuse）是官方 GIF 路线；
「采样率不一致导致变调」是 `concat`/`amix` 在未 `aresample` 时的真实行为。

**与其他候选的重叠**：技术深度远不如 #1/#4，价值在**权威性**——它是本主题唯一的官方厂商上游，
`docs/roadmap.md` 第 4 条特例的锚点。与 `generative-media` 的切分已与 `GenMediaResearch` 谈定：
Veo/Lyria/Chirp/Gemini TTS 的提示与参数归对面，ffmpeg 合成、容器封装、重采样归这边。
`GenMediaResearch` 另外指出「Gemini TTS 输出是裸 PCM 24 kHz/16-bit/mono，必须自己套 WAV 容器」——
**生成参数归对面，「裸 PCM 怎么正确封进 WAV / 怎么重采样到 48 kHz」归本 skill**
（`ffmpeg -f s16le -ar 24000 -ac 1 -i raw.pcm out.wav`，再 `aresample=48000:resampler=soxr`）。

### #3 / #7 / #8 TerminalSkills/skills 的 ffmpeg + imagemagick + sharp 三件套（149★，Apache-2.0，2026-09-04）

**结构**：同一仓库下 30+ 个扁平 skill 目录，每个 `SKILL.md` 5–10 KB，另有 `_scores.json`（自评分）。
frontmatter 规整统一：`name` / 折叠式长 `description` / `license: Apache-2.0` / `compatibility` /
`metadata.{author,version,category,tags}`。**零 agent 绑定**，正文是「Instructions → Step 1 安装 → Step 2… 」
的教学式骨架，代码块可直接粘。

**为什么这三条一起进**：它们是本次调研里**唯一一组许可干净（Apache-2.0）、当月仍在推送、且同时覆盖
视频 + CLI 图像 + Node 图像三条链路**的上游。图像侧（#7/#8）没有第二个合格候选：
`einverne`（#11）被 GPL 挡住，`agentskillexchange`（#20）是抓取拼接，`IgorVaryvoda`（#18）与
`Front-End-Checklist`（#15）落在 `frontend-design`。

**ffmpeg（#3）读到的具体内容**：WebM→MP4 分两种写法并说清何时用哪种（已是 H.264/AAC 就 `-c copy`，否则
`-c:v libx264 -c:a aac -movflags +faststart`）；拼接异构素材时先统一
`scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1` 再 `-ar 44100`；
`loudnorm=I=-16:LRA=11:TP=-1.5` 单遍式（缺两遍测量，见 C7）；与 yt-dlp/gallery-dl 的管线衔接。

**imagemagick（#7）读到的具体内容**：几何后缀四态（`800x600` 内接 / `^` 覆盖 / `50%` / `!` 强制拉伸）、
`magick input.pdf[0] output.jpg` 取 PDF 首页、`-density 300` 提高 SVG 栅格化分辨率、
`-strip` 去元数据、`-auto-orient` 修 EXIF 朝向、`mogrify` 原地批量、
「先 `-resize 200x200^` 再 `-gravity center -extent 200x200`」的方形缩略图配方。
**它的错在注释不在配方**：`-resize 800x600^` 那行注释写「Fill 800x600 (crop overflow)」，
而 `^` 本身不裁剪，必须配 `-extent`——本 skill 正文只写「`^` 保证最小覆盖，裁剪要 `-extent`」这一种说法。

**sharp（#8）读到的具体内容**：`fit:'inside'` + `withoutEnlargement:true`（不放大）、
`fit:'cover'` + `position:'centre'` 做头像、`.avif({quality:50})` 并注明
「AVIF 的质量刻度与 JPEG 不同，50 ≈ JPEG 80」、`.png({compressionLevel:9, palette:true})`、
把 SVG 文本当 `composite` 输入做文字水印、`.metadata()` 返回 `orientation`/`exif`/`icc`、`.stats()` 取通道统计。
**它的错是语义反了**：`// Strip metadata (EXIF, ICC) for privacy` 后面写
`.withMetadata({ orientation: undefined })`——sharp 官方文档明写「默认就会移除全部 metadata，包括
EXIF 朝向」，`withMetadata()`/`keepMetadata()` 是**保留**。见 C6。

**重叠**：#3 与 #1/#4 大面积重叠且更浅，取它主要是为了一份许可干净、结构规整的「通用手册」骨架；
#7/#8 与任何其他候选都不重叠，是图像侧的唯一入口。

### #4 damionrashford/media-os（19★，MIT，2026-05-31，总分 10）

**结构**：`skills/` 下 **110 个** SKILL.md，其中 ffmpeg 相关约 40 个，按子领域切得极细：
`ffmpeg-cut-concat`、`ffmpeg-streaming`、`ffmpeg-hdr-color`、`ffmpeg-lut-grade`、`ffmpeg-ocio-colorpro`、
`ffmpeg-hwaccel`、`ffmpeg-bitstream`、`ffmpeg-ivtc`、`ffmpeg-mxf-imf`、`ffmpeg-probe`、`ffmpeg-quality`、
`ffmpeg-subtitles`、`ffmpeg-audio-{filter,fx,spatial}`、`ffmpeg-vapoursynth`、`ffmpeg-whip` 等，
另有 `audio-{coreaudio,jack,pipewire,wasapi}`、`cv-{opencv,mediapipe}`、`gstreamer-pipeline`、
`decklink-tools`、`hdr-dovi-tool`。每个 8–17 KB，统一写成「Quick start → When to use → Step 1 选策略
→ Step 2 决策 → Step 3 命令」。frontmatter 用 `argument-hint: "[action] [input]"` 与正文的
`**Context:** $ARGUMENTS`——**这是 Claude Code slash-command 绑定**，改写时必须去掉。

**质量**：技术判断是全部候选里最准的。`ffmpeg-cut-concat` 里：
- 明写「**不要**把 concat demuxer 用在编解码/分辨率/SAR/fps/采样率不同的文件上——它会照样封装，但播放会**静默**出问题」，
  异构要走 concat 滤镜。
- 给出 `-ss T1 -i in -to T2 -c copy -avoid_negative_ts make_zero` 并解释 `-to` 是**输入绝对时间**、
  `-t` 与 `-to` 同时给时 `-t` 赢（与官方 Seeking wiki 一致）。
- **唯一写对输入侧 seek 的候选**：「输出侧 seek 慢但准。**现代 ffmpeg 打开解码后输入侧 seek 默认就已经是准确的
  （`-accurate_seek`），所以很少需要输出侧 seek**；要精确切又要重编码时，用输入侧 seek——又快又准。」
- `-f segment -segment_time 60 -reset_timestamps 1` 并指出分段仍然落在关键帧上，要精确 60.000 s
  必须 `-force_key_frames "expr:gte(t,n_forced*60)"`。
- `-safe 0` 的真实作用（允许绝对路径与 `..`）。

`ffmpeg-streaming` 是本主题 HLS/DASH 唯一的系统覆盖：延迟表（HLS/DASH 标准 6–20 s、低延迟 3–7 s）、
直播强制三件套 `-g 60 -keyint_min 60 -sc_threshold 0` 并解释 **GOP = fps × segment_time**、
`-sc_threshold 0` 关掉场景切换关键帧以保证段边界干净、YouTube/Twitch/Facebook 要 2 秒关键帧 + AAC LC + 44.1/48 kHz、
HLS VOD（`-hls_playlist_type vod`）与直播滑窗（`-hls_list_size 6 -hls_flags delete_segments+append_list`，
并指出 `vod`/`event` 与 `delete_segments` 互斥）、fMP4/CMAF（`-hls_segment_type fmp4`）、ABR 多码率 ladder、
tee muxer 一次推多目的地。

`ffmpeg-audio-filter` 里明确「感知响度母带**必须**两遍 loudnorm，单遍是动态压缩」，并给了
`print_format=json` → 回填 `measured_*` 的完整两遍写法。

**agent 绑定与脚本**：正文大量引用 `${CLAUDE_SKILL_DIR}/scripts/afilter.py --two-pass` 这类自带脚本，
改写时这些要么自写要么改成裸 ffmpeg 命令。

**重叠**：与 #1 的重叠集中在 cut/concat/probe/audio；**不重叠且不可替代的是 streaming（HLS/DASH/RTMP/SRT）
与 bitstream/IVTC/MXF-IMF/OCIO 这一层**。粒度上它是反面教材：110 个 skill 意味着 agent 每次要在 110 个
description 里路由，正是本仓库标准第 2.1 节「一个 SKILL.md + `references/` 进阶披露」要避免的形状。

### #5 n0an/ffmpeg-skill（8★，MIT，2026-09-08，总分 10）

**结构**：`ffmpeg/SKILL.md`（6957 B）+ 6 个 references（glossary 6 KB、simple-editing 3.7 KB、
audio-processing 4 KB、advanced-editing 10.3 KB、asset-generation 7.6 KB、encoding-and-tuning 7.5 KB）+
`ffmpeg/agents/openai.yaml`（多 agent 适配）。frontmatter 有 `license: MIT` 与
`metadata.{author,version}`，`description` 把触发词与参数名（CRF、preset、faststart、硬件加速）都铺开。
正文末尾**诚实标注来源**：「Recipes adapted from the Rendi FFmpeg cheatsheet」。

**质量**：「Core Instructions」是全部候选里规则密度最高的一段，逐条列举（下列均已核对）：
- 何时**不能**用 `-c copy`：任何视频滤镜（`scale`/`overlay`/`subtitles`/`trim`/`fade`）、任何音频改动
  （`amix`/`atempo`/`volume`）、烧字幕、转码、压缩。
- H.264 默认串 `-c:v libx264 -crf 18 -preset veryslow -movflags +faststart -pix_fmt yuv420p`，
  并说明 `yuv420p` 是 QuickTime 与多数消费级播放器的硬要求。
- HEVC 发给苹果设备要 `-vtag hvc1`，否则 AirDrop/QuickTime 不认。
- CRF **+6 大约减半码率**；x264 合理区间 17–28，18 视觉无损；libvpx-vp9 用 15–35 且必须配 `-b:v 0`。
- `trim`/`atrim` 之后**必须** `setpts=PTS-STARTPTS` / `asetpts=PTS-STARTPTS`，否则 concat 与下游滤镜坏掉。
- `pad` 之后跟 `setsar=1:1` 锁方形像素，否则尺寸看着对、画面却是拉伸的。
- 已知目标体积就切两遍 ABR，**CRF 无法约束文件大小**。
- 播放异常（黑帧、音画漂移、"file not supported"）先查四件事：缺 `-pix_fmt yuv420p`、缺 `+faststart`、
  `-c copy` 配了输入侧 seek、苹果 HEVC 缺 `-vtag`。
- 输出格式约定：给命令 + 逐个非平凡参数的一行解释 + caveats；评审既有命令时按
  Correctness / Quality / Performance / Portability 四栏组织。

**抽查命中的错**：「For frame-accurate trimming, use **output seeking** (`-ss` after `-i`) without `-c:v copy`.
Input seeking … only seeks to the nearest keyframe and can produce black frames」——这是 FFmpeg 2.1 之前的
行为，官方 Seeking wiki 已明确改口（见 C1）。另 `-preset veryslow` 作为默认与官方「veryslow 相对 slower
只有极小提升却要 280% 时间」的判断相悖（C4）。因此「正确」给 1 分。

**agent 绑定**：`ffmpeg/agents/openai.yaml` 是适配层，正文本身无绑定。

**重叠**：规则清单与 #1 的「Gotchas」高度互补——#1 强在流程与交付门，#5 强在**单条命令级的参数纪律**。
本 skill 的「Core rules」将以 #5 的清单为骨架、按 C1/C4 改正后写入。

### #6 maxazure/video-editing-skill（189★，无许可，2026-09-10，总分 10）

**结构**：根 `SKILL.md` **180 KB**（远超任何合理上限）+ `docs/prompts/` 下 120 个独立 prompt 文档
+ `README.md` 576 KB。frontmatter 里塞了 `metadata.openclaw`（emoji、os 白名单、`requires.bins`、
brew 安装描述符）——**强绑定 openclaw 运行时**。

**质量**：内容两极。创作侧（小红书/抖音/视频号选题、口播、标题文案、平台守门）**完全不取**。
工程侧有三块是别家都没有到位的：
- **HDR→SDR fail closed**：`hdr_sdr.py` 只接受 metadata 明确的 `smpte2084`(PQ) 或 `arib-std-b67`(HLG) 且要求
  BT.2020 primaries/matrix；色彩标签未知或互相矛盾就**拒绝处理**。转换必须 `zscale` + `tonemap`
  在 linear-light float 下做（Hable），**不允许裸 `tonemap`，也不允许「只降到 `yuv420p`」的退化回退**；
  产物要显式验证四项 color tag。并诚实写明 Dolby Vision / HDR10+ 的动态 metadata 不会保留，
  必须在可信 SDR 屏上完整复核肤色/高光/阴影/渐变/饱和色。
- **审片代理**：`review_proxy.py` 不改 master，输出 ≤720p / 24 fps / H.264+AAC / `+faststart` 并在左上角
  烧入 `REVIEW PROXY` 和 elapsed timecode，要求审片意见引用可见时间码。
- **原子提升 + 契约校验**：任何 apply 只有在 H.264/AAC、`yuv420p`、尺寸/fps/时长/采样率/声道全部匹配
  且**完整解码通过**之后才原子替换输出；源 SHA-256 绑定，漂移就 fail closed。
  音频链路顺序固定 `highpass → afftdn → atempo → dynaudnorm → acompressor → loudnorm → cover delay → BGM ducking/mix`。

**抽查 3 条全对**：zscale+tonemap 的 linear-light 要求与 ffmpeg `zscale`/`tonemap` 文档一致；
`+faststart` 代理片正确；响度链顺序（先降噪再变速再动态再响度）在信号处理上成立。

**许可**：GitHub API `license: null`。按 `docs/roadmap.md`「无许可但公开 → merged，`license: NONE`，
`notes` 写明未逐字复制」处理。

**重叠**：与 #1 在 VFR/响度/交付检查上重叠；**HDR→SDR 的 fail-closed 立场与 review proxy 是它独有的**。
它同时是「SKILL.md 不能这么写」的反面样本：180 KB 正文 + 120 个 prompt 文件，路由全靠人肉。

### #9 DabRlin/ffmpeg-skills（0★，Apache-2.0，2026-08-06，总分 9）

零 star、内容也不厚，但开篇那一节值得单独拿出来：**"Environment check (do this first) — Never assume
what's installed；capabilities vary a lot by OS, build, and distro packaging. Check every time you're on an
unfamiliar machine"**，随后给出 `ffmpeg -version`、`-encoders | grep -i <codec>`、`-decoders`、`-hwaccels`
四条探测命令，并明确「**按这次探测实际报告的名字选编码器，不要按上一台机器上能用的名字**」，
以及硬件族谱与回退顺序（`*_videotoolbox` / `*_nvenc`+`*_cuvid` / `*_qsv` / `*_vaapi` → 软件
`libx264`/`libx265`/`libsvtav1`/`libvpx-vp9`）。

这条与 #1 的 `doctor --json`、#5 的「macOS/Linux 无 GPU 时不要建议 `*_nvenc`/`*_qsv`/VAAPI」是同一件事的
三种强度，本 skill 取最强的那种：**能力探测是第一步，不是可选项**。除此之外它没有别的独有内容。

### #10 chang416/cutcraft（51★，MIT，2026-08-14，总分 10，只取一条）

`skills/cutcraft/SKILL.md` 12 KB，主体是对话式成片的「Non-negotiable contract」五条：先跑
`helpers/check_environment.py` 就绪门、密钥只放 `~/.config/cutcraft/.env`（mode 600）且绝不出现在命令行/日志/
仓库里、先建命名工作区、先盘点转写再一次性问完所有创作问题、**「Show choices visually」——生成三张
material-aware 的字幕预览图（recommended / clean / …）让用户挑**。

前四条属创作流程或通用工程卫生，不取。第五条取：它把「字幕在这段素材上到底看不看得清」从
**烧录之后再返工**提前成**烧录之前的一张图**。#1 的 `look.py` 是事后 contact sheet，两者合起来
才是完整的「渲染前选样式 / 渲染后核查」双门。

### 粒度决定：为什么是一个 `media-processing` 而不是 `ffmpeg` + `image-processing` 两个

- 三条链路（视频/音频/图像）共用同一套**交付门**：probe/identify 量事实 → 执行 → 回读产物 → 目视核查。
  拆成两个 skill 会让这套门写两遍，`references/` 里的「偶数尺寸」「色彩标签」「元数据存亡」也要各存一份。
- `docs/roadmap.md` 的粒度是「一类事情 = 一个 skill」。这类事情是「**用确定性工具把一个媒体文件变成
  另一个符合规格的媒体文件**」——ffprobe 与 `identify`、`-crf` 与 `-quality`、`scale` 与 `resize`、
  loudnorm 与 ICC 转换，是同一件事在不同容器上的投影。
- 真正被加载的 token 由 `SKILL.md` 的路由表决定，不由 skill 个数决定（同 `office` 的结论）。
- 消歧靠 description 的否定边界（框架内置图片管线 / 文档格式 / 生成式），不靠 skill 个数。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| C1 | 帧精确裁剪该用输入侧还是输出侧 `-ss` | **n0an(#5)**：「帧精确裁剪用**输出侧** `-ss`（`-i` 之后）；输入侧只能 seek 到最近关键帧，会产生黑帧或差几秒」。**sakydev(#17)/bryanwhl(#24)**：「`-ss` 放 `-i` 前是快速 seek」（只说快，未说准不准）。**media-os(#4)**：「输出侧慢但准；**但现代 ffmpeg 打开解码后输入侧 seek 默认就已精确（`-accurate_seek`），所以很少需要输出侧**；要精确又要重编码时用输入侧——又快又准」 | **采用 media-os。** 正文只写一种做法：**重编码时一律 `-ss` 放 `-i` 之前**（快且帧精确）；只有 `-c copy` 时 `-ss` 才退化为「切到不晚于该时刻的关键帧」，此时要么接受 GOP 级偏差（并告诉用户实际落点），要么改成重编码。`n0an` 的说法作为「FFmpeg 2.1 之前的历史行为」在 `references/` 里记一句，避免 agent 从旧博客里学回去 | 官方 <https://trac.ffmpeg.org/wiki/Seeking>：「As of FFmpeg 2.1, when transcoding with ffmpeg (i.e. not stream copying): `-ss` is also "frame-accurate" even as input option. Previous behavior … can be restored with `-noaccurate_seek`.」同页 Combined seeking 一节直言组合 seek 现在「mostly useless」。裁决口径：官方 > 社区，更新 > 更旧 |
| C2 | libsvtav1 的 CRF 默认值，以及要不要写 `-b:v 0` | **dcloud(#23)**：「CRF：0–63（**默认 0**）」「`-b:v 0`：启用 CRF 模式，绕过码率控制」「preset 默认 -2，大致相当于 preset 10」 | **三条全部不采用。** 正文写：**libsvtav1 的 CRF 就是默认码率控制方式，不需要 `-b:v 0`；不写 `-crf` 时实际生效的是 35**；`ffmpeg -h` 显示的 `default 0` 是**包装层哨兵值**，不是生效值，不能当文档读；preset 不写时本机解析为 **8**。`-b:v 0` 的要求只对 **libaom-av1 且 FFmpeg < 4.3** 成立，正文在 libaom 段落单独写 | 官方 <https://trac.ffmpeg.org/wiki/Encode/AV1>：「CRF is the default rate control method」「The valid CRF value range is 0-63, **with the default being 35**」；libaom 段落：「in FFmpeg versions prior to 4.3, triggering the CRF mode also requires setting the bitrate to 0 with `-b:v 0`」。本机复现（ffmpeg N-126134）：`ffmpeg -i t.mp4 -c:v libsvtav1 -an a1.mkv` 输出 `Svt[info]: SVT [config]: preset / tune / pred struct : 8 / PSNR / random access` 与 `Svt[info]: SVT [config]: BRC mode / rate factor : CRF / 35.00` |
| C3 | libvpx-vp9 的 `-crf` 要不要配 `-b:v 0` | **n0an(#5)**：「libvpx-vp9 用 15–35 并配 `-b:v 0`」。**sakydev(#17)** 的下限表只写 `-crf 40 max`，没提 `-b:v`。**多数候选**在 VP9 示例里直接 `-crf N` 了事 | **采用 n0an：`-b:v 0` 必须显式写。** 理由不是「不写就一定不同」，而是**不写就把模式交给上下文**：一旦命令是从某个带 `-b:v` 的模板改来的，CRF 会静默退化成 Constrained Quality，体积与画质全变，而命令看上去没错。正文写死「VP9 恒定质量 = `-crf N -b:v 0`；要限码率才写非零 `-b:v`，并明说这是 Constrained Quality」 | 官方 <https://trac.ffmpeg.org/wiki/Encode/VP9>：「you must use a combination of `-crf` and `-b:v` 0. Note that `-b:v` **MUST** be 0. Setting it to anything higher or omitting it entirely will instead invoke the Constrained Quality mode.」本机复现印证「易编码素材上两者一致、约束一旦生效就天差地别」：`-crf 30` 与 `-crf 30 -b:v 0` 产出**字节数完全相同**（1 221 946 B），而 `-crf 30 -b:v 256k` 只有 239 192 B——恰好是官方所说「for videos that are easy to encode this mode behaves exactly like the Constant Quality mode」 |
| C4 | 默认 `-preset` 取什么 | **n0an(#5)**：默认串里写死 `-preset veryslow`，并称「比 medium 小 20–30%」。**kajisho5(#1)**：重编码用 x264 `medium`，长文件的**中间件**才降到 `veryfast`，最终导出保持默认。**dcloud(#23)/TerminalSkills(#3)**：示例多用 `slow`。**media-os(#4)**：重编码切片示例用 `veryfast` | **采用 kajisho5 + 官方：默认 `medium`，质量档 `slow`，中间件 `veryfast`，不把 `veryslow` 设成默认。** 正文给一张三行表（中间件 / 交付 / 归档）而不是一个魔法默认值 | 官方 <https://trac.ffmpeg.org/wiki/Encode/H.264>：「`medium` – default preset」「Use the slowest preset that you have patience for」；FAQ 的量化数据：`slow` 比 `medium` 好 5–10%，`slower` 再好 5%，`veryslow` 再好 3%，而编码时间 `veryslow` 是 `medium` 的 **280%**。把 280% 的时间当默认，对 agent 这种会被要求「处理整个文件夹」的调用方是错误默认 |
| C5 | `scale` 之后是不是必须 `setsar` | 常见社区说法（也是本次调研前的假设）：「`-vf scale=…` 之后必须补 `setsar=1`，否则画面会拉伸」。**n0an(#5)** 的说法更窄且更准：「**对 `pad`**，`setsar=1:1` 应跟在 resize/pad 链之后」 | **采用 n0an 的窄版，并把「scale 之后一律 setsar」明确写成错误做法。** 正文：`scale` **保留**源 SAR，不会改变显示宽高比；只有在 ① 源是非方形像素而你要输出方形像素，② `pad`/`crop` 之后需要重新锁定 SAR，③ 后续 `concat`/`hstack` 要求各路 SAR 一致 这三种情况下才写 `setsar=1`。**无脑加 `setsar=1` 反而会把一个正确的非方形像素源改成错误的显示比例** | 本机复现（源：640×480，SAR 4:3，DAR 16:9）：`-vf scale=320:240` → `320,240,SAR 4:3,DAR 16:9`（DAR 保持正确）；`-vf scale=320:240,setsar=1` → `320,240,SAR 1:1,**DAR 4:3**`（显示比例被改坏）；`-s 320x240` → 与不加 setsar 的 scale 完全相同（`SAR 4:3, DAR 16:9`）。即：`setsar` 在此处是**制造**问题而非解决问题 |
| C6 | sharp 怎么剥离 / 保留 EXIF 与 ICC | **TerminalSkills sharp(#8)**：注释 `// Strip metadata (EXIF, ICC) for privacy`，代码 `.rotate().withMetadata({ orientation: undefined })` | **不采用。** 正文写死三条：① **sharp 默认就剥离全部 metadata（EXIF/ICC/XMP/IPTC），并转到 sRGB**——所以「隐私剥离」不需要任何调用，**需要显式处理的反而是保留**；② 要保留用 `.keepMetadata()`（全保）或 `.withMetadata()`（保 EXIF/XMP/IPTC）；③ 因为默认丢 ICC，**Display-P3 / Adobe RGB 的输入会被当成 sRGB 解释而偏色**，广色域素材必须显式 `.keepMetadata()` 或先做 ICC 转换；朝向用 `.autoOrient()`（无参 `.rotate()` 只是向后兼容的等价写法） | 官方 <https://sharp.pixelplumbing.com/api-output/>：`toFile`/`toBuffer` 条目「By default all metadata will be removed, which includes EXIF-based orientation.」；`keepMetadata` 条目「Keep all metadata (EXIF, ICC, XMP, IPTC) … The default behaviour, when `keepMetadata` is not used, is to convert to the device-independent sRGB colour space and **strip all metadata, including the removal of any ICC profile**.」；<https://sharp.pixelplumbing.com/api-operation/> `rotate`：「For backwards compatibility, if no angle is provided, `.autoOrient()` will be called.」 |
| C7 | `loudnorm` 单遍够不够，以及它对采样率做了什么 | **TerminalSkills(#3)**：`-af loudnorm=I=-16:LRA=11:TP=-1.5` 单遍。**dcloud(#23) / media-os(#4) / bryanwhl(#24)**：两遍（先 `print_format=json` 测量，再回填 `measured_*`）。**所有候选都没有提采样率** | **采用两遍派，并补一条谁都没写的规则：`loudnorm` 会静默重采样到 192 kHz，必须自己收尾。** 正文：① 母带/交付级响度一律两遍（单遍是动态处理，LRA 会被改，`linear` 模式在没有 `measured_*` 时根本用不上）；② **`loudnorm` 之后必须接 `aresample=<目标采样率>`（或显式 `-ar`）**，否则输出采样率会被改掉；③ 目标值不写默认，默认 `I=-24 / LRA=7 / TP=-2` 是 EBU 广播档，不是流媒体档 | 本机 `-h filter=loudnorm`：`linear`（默认 true）「normalize linearly **if possible**」——而 linear 只有在 `measured_*` 齐备时才可能，故单遍必然走动态路径；默认 `I=-24 / LRA=7 / TP=-2`。本机复现采样率问题：源 44 100 Hz → `-af loudnorm=I=-16 -vn out.wav` 得 **pcm_s16le / 192000 Hz**；同源 `-af loudnorm=I=-16:TP=-1.5 -c:v copy out.mp4` 得 **aac / 96000 Hz**（被 AAC 上限截住）。两次都没有任何告警 |
| C8 | `-movflags +faststart` 是不是必须 | **n0an(#5)/TerminalSkills(#3)/maxazure(#6)**：MP4 交付默认带。**dcloud(#23) 的 Quick Reference** 与 **chunpu(#22)** 的全部转码示例都不带；**MastroMimmo(#16)** 的 compress 也不带 | **采用「带」，但把理由写准：它是容器层的 moov 位置问题，不是编码参数。** 正文：所有**面向渐进式下载/浏览器播放**的 MP4/MOV 输出都加 `-movflags +faststart`；纯本地文件、要走 HLS/DASH 分段、或后续还要再处理的中间件不必加（分段交付由 muxer 负责）。同时写明它是**一次额外的整文件重写**，对超大文件有 I/O 成本 | 官方 <https://trac.ffmpeg.org/wiki/Encode/H.264>「faststart for web video」：「add `-movflags +faststart` … This will move some information to the beginning of your file and allow the video to begin playing before it is completely downloaded … It is not required if you are going to use a video service such as YouTube（但 YouTube 自己也推荐加，以便在上传完成前开始转码）」。本机复现 box 顺序：不加 → `['ftyp','free','mdat','moov']`；加 → `['ftyp','moov','free','mdat']` |
| C9 | 缩放写法：`-s` / `scale=W:-1` / `scale=W:-2` / `-resize WxH^` | **chunpu(#22)/hufang360(#19)** 用 `-vf "scale=1280:720"` 硬写。**MastroMimmo(#16)** 用 `--width 1920 --height -1`（`-1` 自动）。**sakydev(#17)** 用 `scale=1280:-2`。**TerminalSkills imagemagick(#7)** 把 `-resize 800x600^` 注释成「Fill（crop overflow）」 | **统一为：视频侧一律 `scale=W:-2` / `scale=-2:H`（不用 `-1`，不用 `-s`）；图像侧 `^` 与 `-extent` 必须成对出现。** 理由：`-1` 会算出奇数高度，而 `yuv420p` 要求偶数宽高，结果是**编码器直接报错、输出文件不可用**——这是一个会在批处理里随机炸掉的地雷，`-2` 自动取偶正好消掉它。`-s` 是遗留写法，不支持 `-1`/`-2`，也不能参与滤镜链 | 本机复现：`-vf scale=321:241 -c:v libx264` → `[libx264] width not divisible by 2 (321x241)` + `Error while opening encoder`，产物 `moov atom not found`（文件废掉）。ImageMagick 几何后缀语义见官方 <https://imagemagick.org/script/command-line-options.php>（`^` = 最小值填充，不裁剪；裁剪要 `-extent`） |
| C10 | 静态图片批处理该用 ffmpeg 还是 magick / sharp / vips | **chunpu `ffmpeg-image-processing`(#22) / hufang360(#19)**：用 `ffmpeg -i in.jpg -q:v 2 out.jpg`、`ffmpeg -i in.webp out.png` 做格式转换与压缩。**TerminalSkills(#7/#8)**：用 `magick` / `sharp` | **采用 magick/sharp/vips，并把「用 ffmpeg 处理静图」写成明确的失败模式。** 正文：ffmpeg 只负责「从视频里抽帧 / 把序列帧合成视频」；**任何以图片为输入、图片为输出的批处理都不走 ffmpeg**，因为它会静默丢掉 EXIF（包括 Orientation；朝向是否已被应用取决于构建的隐式默认，而标签丢失后下游再也无法纠正），且 `-q:v` 是 mjpeg 的 2–31 量化尺度，与 `magick -quality 85` / `sharp.jpeg({quality:85})` 不是一个刻度，没法照抄。大批量缩略图用 `vips thumbnail`（shrink-on-load） | 本机复现（Pillow 12.3.0 造源：ICC 588 B + EXIF Orientation=6 + Make=ACME）：源 `icc=588 orientation=6 make=ACME`；`ffmpeg -i src2.jpg -q:v 2 ff2.jpg` → `icc=588 **orientation=None make=None**`（ICC 留下了，**EXIF 全丢**）。**Phase D 更正**：原判「未应用朝向」不成立——见下方本机实验表；`vips copy src2.jpg vips2.jpg[Q=90]` → `icc=588 orientation=6 make=ACME`（全保）。chunpu 把 `-q:v 2` 注释成「质量 85」也不成立 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| kajisho-ffmpeg | kajisho5/ffmpeg-skill (MIT) | **merged** | 主干：probe→plan→execute→check→look 工作流；`format` / `judgement` 两类检查的二分；五行交付报告形状；VFR / HDR / Log / 关键帧切 / CJK 字体 / 偶数尺寸 / 旋转 metadata 七类陷阱；「本 skill 只执行给定参数，不推断审美」的范围声明 |
| vertex-genmedia-av | GoogleCloudPlatform/vertex-ai-creative-studio `experiments/mcp-genmedia/skills/{genmedia-video-editor,genmedia-audio-engineer}` (Apache-2.0) | **merged** | **按边界只取 ffmpeg 操作部分**：叠加前先 `get_media_info` 再算坐标；GIF 两遍法默认 `fps=15` + 0.33 缩放；concat 前同尺寸同帧率、异构时明告用户会先标准化；多轨叠加前同采样率否则变调；人声/配乐相对增益与 `afade` 收尾；裸 PCM（如 24 kHz/16-bit/mono）封 WAV 与重采样。生成侧归 `generative-media` |
| media-os-ffmpeg | damionrashford/media-os `skills/{ffmpeg-cut-concat,ffmpeg-streaming,ffmpeg-hdr-color,ffmpeg-hwaccel,ffmpeg-probe,ffmpeg-audio-filter,ffmpeg-subtitles}` (MIT) | **merged** | HLS / DASH / RTMP / SRT 打包全套（`-g = fps × segment_time`、`-keyint_min`、`-sc_threshold 0`、`hls_playlist_type` 与 `delete_segments` 的互斥、fMP4/CMAF、ABR ladder、tee 多出口）；concat demuxer 的同参要求与「不匹配时静默坏播放」；`-force_key_frames` 做精确分段；两遍 loudnorm 的 measure→apply 形；C1 的正确裁决 |
| n0an-ffmpeg | n0an/ffmpeg-skill (MIT) | **merged** | 单条命令级的参数纪律清单：何时不能 `-c copy`；`yuv420p` 的播放器要求；HEVC `-vtag hvc1`；CRF ±6 ≈ 倍半码率与 CRF 无法限体积→两遍 ABR；`trim`/`atrim` 后必须 `setpts/asetpts`；`pad` 后 `setsar`；`-shortest` 与 `amix duration=shortest`；播放异常四查表；命令评审的 Correctness/Quality/Performance/Portability 四栏。**按 C1 改正输入侧 seek、按 C4 改正默认 preset 后合入** |
| terminalskills-ffmpeg | TerminalSkills/skills `skills/ffmpeg` (Apache-2.0) | **merged** | 容器/编解码选型表与 remux-vs-transcode 判据；异构素材拼接前的统一化滤镜串；与下载工具链的衔接 |
| terminalskills-imagemagick | TerminalSkills/skills `skills/imagemagick` (Apache-2.0) | **merged** | ImageMagick 几何后缀四态、`-gravity`+`-extent` 方形缩略图、`-auto-orient`、`-strip`、`-density` 栅格化、`mogrify` 批量与其原地改写风险。**注释错误按 C9 改正** |
| terminalskills-sharp | TerminalSkills/skills `skills/sharp` (Apache-2.0) | **merged** | sharp 的 `fit` 语义与 `withoutEnlargement`、AVIF/WebP 质量刻度差异、responsive 变体批量、SVG 文字水印、`metadata()`/`stats()`。**metadata 语义按 C6 反向改正** |
| maxazure-video | maxazure/video-editing-skill (**无许可 → `license: NONE`**) | **merged** | HDR→SDR 的 fail-closed 规则（只认明确的 PQ/HLG + BT.2020，`zscale`+`tonemap` 在 linear-light，禁裸 tonemap 与「只降 `yuv420p`」的退化回退，产物验四项 color tag）；review proxy（≤720p/24fps/`+faststart`/烧时间码）；apply 前的媒体契约校验 + 完整解码 + 原子提升 |
| dabrlin-ffmpeg | DabRlin/ffmpeg-skills (Apache-2.0) | **merged** | 「编码器与硬件加速能力每台机器实测、按实测结果选名字」这一条及其回退顺序 |
| sakydev-ffmpeg | sakydev/claude `skills/ffmpeg` (**无许可 → `license: NONE`**) | **merged** | 质量下限表（x264 ≤28 / x265 ≤32 / vp9 ≤40 / AAC ≥128k）与「目标体积要求突破下限时明说做不到、给出下限处的最佳体积」；超大输入先确认 |
| cutcraft | chang416/cutcraft `skills/cutcraft` (MIT) | **merged** | 「烧录字幕前先渲染样式预览图让人选」这一条前置门 |
| einverne-imagemagick | einverne/dotfiles `claude/skills/imagemagick` (**GPL-3.0**) | **reference** | 仅用其章节清单核对 ImageMagick 覆盖面（v7 `magick` 统一入口、`convert` 遗留、`mogrify` 原地风险）。**不复制任何文字** |
| dcloud-ffmpeg | dcloud/agent-skills `skills/ffmpeg` (无许可) | **reference** | 正确性 0 已 REJECT 为 merged 源；仅保留条目记录「其 AV1 一节的两处错误」，避免下轮重新评估。另借鉴一条**惯例**（非文字）：把 `ffmpeg -h filter=<name>` / `-encoders` / `-pix_fmts` 作为「文档没写就现场查」的一等手段 |
| ffmpeg-filters-docs | <https://ffmpeg.org/ffmpeg-filters.html> | **merged (docs)** | 全部滤镜参数语义（`scale`/`pad`/`crop`/`setsar`/`overlay`/`subtitles`/`drawtext`/`loudnorm`/`amix`/`concat`/`zscale`/`tonemap`）。只取语义，示例自写 |
| ffmpeg-formats-docs | <https://ffmpeg.org/ffmpeg-formats.html> | **merged (docs)** | hls / dash / segment muxer 与 `-movflags` 的参数语义 |
| ffmpeg-h264-docs | <https://trac.ffmpeg.org/wiki/Encode/H.264> | **merged (docs)** | CRF 尺度与合理区间、preset 的量化代价（C4）、两遍 ABR、`+faststart`（C8）、lossless 的 `-qp 0` 与 profile 限制 |
| ffmpeg-av1-docs | <https://trac.ffmpeg.org/wiki/Encode/AV1> | **merged (docs)** | libsvtav1 CRF 默认 35 与 `-b:v 0` 的适用边界（C2）、SVT-AV1 默认 keyint 太短要 `-g`、film-grain 合成 |
| ffmpeg-vp9-docs | <https://trac.ffmpeg.org/wiki/Encode/VP9> | **merged (docs)** | 恒定质量必须 `-b:v 0`（C3）、Constrained Quality 与 CBR 的写法、`-row-mt 1` |
| ffmpeg-seeking-docs | <https://trac.ffmpeg.org/wiki/Seeking> | **merged (docs)** | 输入侧 seek 自 2.1 起帧精确（C1）、`-c copy` 只能切关键帧、`-avoid_negative_ts` 与 concat 的关系、`-t`/`-to` 优先级 |
| sharp-docs | <https://sharp.pixelplumbing.com/> | **merged (docs)** | 默认剥离 metadata 并转 sRGB、`keepMetadata`/`withMetadata`/`autoOrient` 的准确语义（C6）、`fit`/`position` 全集、`composite` |
| imagemagick-docs | <https://imagemagick.org/script/command-line-options.php> | **merged (docs)** | 几何后缀语义（C9）、`-extent`/`-gravity`/`-auto-orient`/`-strip`/`-density`/`-colorspace` |
| libvips-docs | <https://www.libvips.org/API/current/> | **merged (docs)** | `vips thumbnail` 的 shrink-on-load、`smartcrop`、ICC 转换、序列化访问 —— 大批量缩略图与雪碧图的正解 |
| pillow-docs | <https://pillow.readthedocs.io/en/stable/> | **merged (docs)** | `ImageOps.exif_transpose`、`Image.draft`、`save(quality/progressive/subsampling/icc_profile)` |
| ebu-r128 | EBU R 128 / ITU-R BS.1770-5 | **merged (docs, 仅引用)** | 整合响度 / LRA / 真峰值的定义；平台目标表由本 skill 自写。不复制标准文本 |

## 基线缺口

无 skill（`uv run tools/run_evals.py media-processing --baseline`，Claude Opus 5 / medium）时，
各场景未达成的 `expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 转码审查 | 「把 `-preset veryslow` 作为成本决策显式交还给用户」 | 基线把它归为「交付规格而非缺陷，改它属于越界」，既没改也没给出编码时间代价，用户无从判断 |
| 2 HLS 打包 | 无 | 7/7 全达成，含 GOP 对齐、`hls_time` 是下界、VFR 先转 CFR、BANDWIDTH 实测重算 |
| 3 静图缩略图 | 「迁出 ffmpeg 到成像库」「以成本论证工具切换」「`-q:v` 与 `quality` 不同刻度」「EXIF 未被 carry through」 | **最大缺口**。基线选择留在 ffmpeg，手工解析 ICC 的 colorant 与 TRC、烘出 65 格 `.cube`、再用 `lut3d` 应用——为保住工具而重新实现一遍色彩管理，复杂度高一个数量级 |
| 4 负例 | — | `skill_read=false`，按 Next.js 图片配置作答，未打开 ffmpeg 工作流 |

第一轮评测的场景 2 是两遍 `loudnorm`（基线 6/6 全达成，零区分度），按 `docs/workflow.md`
Phase B「基线全部达成 = 评测没有区分度」改写为 HLS 打包；改写后基线仍 7/7。这一条如实记录：
**Opus 5 在常规 ffmpeg 工程上已无缺口，本 skill 的增量集中在工具选型的经济性判断与交付决策的交还。**

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 转码审查 | Claude Opus 5 / medium | 无 | false | 6/7 | preset 未作为成本决策交还 |
| 1 转码审查 | Claude Opus 5 / medium | 有 | true | 7/7 | Notes 里写明 veryslow 约为默认档 2.8 倍耗时换几个百分点，列为旋钮交还所有者 |
| 2 HLS 打包 | Claude Opus 5 / medium | 无 | false | 7/7 | — |
| 2 HLS 打包 | Claude Opus 5 / medium | 有 | true | 7/7 | 无增量；保留该场景作为回归面 |
| 3 静图缩略图 | Claude Opus 5 / medium | 无 | false | 3/7 | 留在 ffmpeg 手写 ICC→LUT |
| 3 静图缩略图 | Claude Opus 5 / medium | 有（第一轮） | true | 7/7 | 改用 Pillow；显式择一「转 sRGB 而非保留 profile」；元数据丢弃写成明确决策；改正 `-q:v` 刻度。**但它实测到本机该 ffmpeg 构建默认 autorotate，与 `images.md` 当时的断言冲突并明确指出**——该反馈触发了下方的事实更正 |
| 3 静图缩略图 | Claude Opus 5 / medium | 有（更正后重跑） | true | 7/7 | 复述的已是更正后的事实：「ffmpeg 丢弃整个 EXIF 块，而有没有先应用 Orientation 是构建级默认值（本机会旋转，`-noautorotate` 就不转）→ 输出既无标签也无从修复」。结论不变，依据变正确 |
| 4 负例 | Claude Opus 5 / medium | 无 | false | 3/3 | — |
| 4 负例 | Claude Opus 5 / medium | 有 | **false** | 3/3 | 负例确认不触发 |

结论：**通过**。场景 3 有四条基线未达成的行为在有 skill 时全部达成，场景 1 补上一条。
两次有 skill 运行都采用了 SKILL.md 规定的五行交付报告格式，这是可观察的输出契约差异。

### Phase D 事实更正：C10 的「朝向未应用」不成立

第一轮有 skill 运行的场景 3 报告：本机 ffmpeg **同一构建号** N-126134 上，8 个 Orientation 值全部被正确
自动旋转，与 `references/images.md` 当时写的「未应用朝向，成品未旋转」直接冲突。主会话复测确认
**该 agent 是对的**：

| 命令 | 输出尺寸 | EXIF Orientation | EXIF Make |
|---|---|---|---|
| 源（Pillow 构造，Orientation=6） | 640x480 | 6 | ACME |
| `ffmpeg -i src.jpg -q:v 2 out.jpg` | **480x640**（已旋转） | 剥离 | 剥离 |
| `ffmpeg -noautorotate -i src.jpg -q:v 2 out.jpg` | 640x480 | 剥离 | 剥离 |
| `vips copy src.jpg out.jpg[Q=90]` | 640x480 | 6 | ACME |

原判的错误在于**把「元数据被剥离」当成了「像素没被旋转」的证据**——这两件事互相独立，调研时只观测了前者
就推断了后者。正确的事实是：EXIF 一定被剥离；朝向是否被应用取决于构建的隐式默认值。

更正后的论证反而更强：真正的失败模式不是「一定躺倒」，而是**「转不转由构建默认决定，而唯一能纠正它的
标签已经被丢掉了」**——同一份脚本在写它的机器上产出正立缩略图，换一台默认不同的构建就产出躺倒的，
且下游无从修复。`SKILL.md` 规则 16 与 `references/images.md` 已按此改写，重跑后场景 3 仍为 7/7，
复述的依据已是更正后的事实。

教训：本机复现实验必须直接观测**被断言的那个量**（此处是输出像素几何），不能用相邻观测量推断。

## 备注

### 许可注意事项

- **GPL 红线**：`einverne/dotfiles` 仓库许可是 **GPL-3.0**，而其 `claude/skills/imagemagick/SKILL.md` 的
  frontmatter 自称 `license: MIT`。**以仓库 LICENSE 为准**，按 `docs/roadmap.md`「GPL/LGPL/AGPL → reference」
  处理：只取主题清单判断覆盖面，每条事实改从 ImageMagick 官方文档取证，**不复制任何文字**。
  `SOURCES.yaml` 的 `notes` 要写明这处 frontmatter 与仓库许可的矛盾。
- **无许可但公开（API `license: null`）→ merged**，`license: NONE`，
  `notes: "No licence file; used under the repository's permissive-attribution policy, no text copied verbatim"`：
  `maxazure/video-editing-skill`、`sakydev/claude`。两者都只取规则不取文字。
- **`dcloud/agent-skills`** 同为无许可，但因正确性 0 被 REJECT 为 merged 源，降为 `reference`，
  `contributes` 写「审查后确认不可作为事实来源；条目保留以记录其 AV1 两处错误」。
- **FFmpeg 官方文档**（`ffmpeg.org/ffmpeg-{filters,formats}.html`）随 FFmpeg 以 GPL/LGPL 发布，
  trac wiki 无明示许可。按 `office` 的 `ecma-376` 先例处理：**只取参数与行为语义，全部示例自写，
  不复制任何句子**，`notes` 记录该处理方式，许可分记 1。
- **EBU R 128 / ITU-R BS.1770-5** 是有版权的标准文本，**只引用定义**（LUFS / LRA / dBTP / 门限），
  平台目标表（YouTube −14、Apple Podcasts −16、EBU 广播 −23 等）由本 skill 自行整理并注明出处，
  不摘抄标准正文，许可分记 0。
- **libvips** 本体是 LGPL-2.1，但这只影响链接其代码；本 skill 只调用其 CLI（`vips`/`vipsthumbnail`）
  并引用文档事实，不构成衍生作品。
- **Apache-2.0 上游**（`TerminalSkills/skills`、`GoogleCloudPlatform/vertex-ai-creative-studio`、
  `DabRlin/ffmpeg-skills`）与 **MIT 上游**（`kajisho5`、`damionrashford`、`n0an`、`chang416`）
  可直接 merged，按标准重写并在 `NOTICE.md` 署名。

### 未来同步要盯的上游

| 上游 | 为什么要盯 | `paths` 建议 |
|---|---|---|
| `kajisho5/ffmpeg-skill` | 主干，且**当天仍在推送**（CHANGELOG 已 111 KB），迭代极快；其 `SKILL.md` 与 `docs/contract.md` 的语义变化会直接影响本 skill 的工作流与陷阱清单 | `SKILL.md`、`docs/contract.md` |
| `GoogleCloudPlatform/vertex-ai-creative-studio` | 唯一官方上游，且 `experiments/` 目录随 Veo/Lyria 版本迭代改名或移动的风险高；仓库本体是大 monorepo，**必须声明 paths** 否则每天都报 `behind` | `experiments/mcp-genmedia/skills/**` |
| `damionrashford/media-os` | HLS/DASH 这一层的唯一来源；上次推送 2026-05-31，已接近 6 个月线，**下次同步要先确认它是否仍活跃**，不活跃则把 streaming 段完全改挂官方 formats 文档 | `skills/ffmpeg-streaming/**`、`skills/ffmpeg-cut-concat/**`、`skills/ffmpeg-hdr-color/**` |
| `TerminalSkills/skills` | 图像侧（imagemagick / sharp）唯一活跃且许可干净的上游；仓库会新增 skill，值得留意是否出现 `vips` / `exiftool` 条目 | `skills/ffmpeg/**`、`skills/imagemagick/**`、`skills/sharp/**` |
| FFmpeg 官方 wiki 的 Encode 系列 | `kind: docs`，人工比对。**特别盯 AV1 页**：SVT-AV1 的默认 preset 与 CRF 随版本变过不止一次（本次实测 preset 解析为 8、CRF 35），下次同步要重跑一次本机探测再对照 | 手动 |
| sharp | 主版本升级常动 metadata / 色彩管理默认值（`keepMetadata` 是 0.33.0 才引入的），C6 的裁决依赖这些默认值 | 手动 |

### 本主题与相邻 skill 的边界（`SKILL.md` 的 description 要写成否定边界）

**本 skill 是什么（`media-processing` = 确定性多媒体工程）**：ffmpeg 命令与滤镜图；容器 / 编解码器选型；
转码、裁剪、拼接；字幕（烧录与软封）；HLS / DASH 打包；图像批处理（sharp / ImageMagick / Pillow / libvips）；
色彩空间与元数据（EXIF / ICC）；缩略图与雪碧图；音频响度规范化与格式转换；ffprobe 探测。
判据是**同样的输入与同样的显式参数，永远产出同一个可验证的输出**。

**本 skill 不是什么（逐条划走，写进 description 的否定边界）**：

| 不覆盖 | 归谁 | 分界理由 |
|---|---|---|
| 概率性的生成与识别：文生图 / 图生图 / 图像编辑 API（Gemini image、OpenAI images、Replicate、fal）、本地 diffusion（ComfyUI / diffusers）、视频生成、TTS、ASR（Whisper 系）、提示与参数控制、种子与可复现、生成成本与配额、C2PA / 水印 | **`generative-media`** | 「对同样输入给同样输出」与「对同样输入给一个采样」是两类不同的工程问题：前者的验证是断言，后者的验证是评测与成本。本 skill 只在生成**之后**接手——把产物封成正确的容器、对齐采样率、做响度与色彩规范化 |
| 框架内置的图片管线：Astro 的 image service / `<Image>` | **`astro`** | 那是框架的构建期 API 与配置问题，不是 ffmpeg/sharp 的参数问题 |
| Next.js 的 `next/image`、OG image 生成、React 侧图片组件 | **`react`** | 同上，属框架 API |
| 图片格式与 LCP 的前端取舍、`srcset`/`sizes`、`loading=lazy`、`fetchpriority`、CLS、Core Web Vitals | **`frontend-design`** | 「该给浏览器发哪一张」是交付与性能预算问题；「怎么把这张图做出来」才是本 skill。候选 #15 #18 整条落在这一侧，因此 REJECT |
| docx / pptx / xlsx / PDF 的生成、编辑、抽取、渲染质检 | **`office`** | 文档格式有自己的对象模型与交付门。**边界上的一条具体例子**：把 PDF 页渲染成 PNG 属 `office`（`pdftoppm`），把一堆 PNG 批量压成 WebP 属本 skill |
| 通用 LLM 应用、RAG、评测、agent 循环、结构化输出 | **`ai-engineering`** | — |
| 训练与微调权重、GPU 显存账本、分布式训练 | **`ml-training`** | — |

**与 `generative-media` 共同持有的两个候选**（两份 research 都留行）：
`GoogleCloudPlatform/vertex-ai-creative-studio` 的 `genmedia-{video-editor,audio-engineer,producer}`——
按边界本 skill 只取 ffmpeg 操作部分（叠加坐标、GIF 两遍法、concat/layer 前置条件、相对增益、`afade`、
裸 PCM→WAV 与重采样），生成参数（Veo 五段式提示、Lyria 提示、Chirp/Gemini 声音选择）归对面；
`maxazure/video-editing-skill` 的 `docs/prompts/19-imagegen.md` 等生成相关章节同理不取。

### 放弃的方向

- **拆成 `ffmpeg` + `image-processing` 两个 skill**：见「粒度决定」。三条链路共用一套交付门，拆了要写两遍。
- **把 `damionrashford/media-os` 的 110 个 skill 形状照搬**：agent 每次要在 110 个 description 里路由，
  与本仓库标准第 2.1 节冲突。只取其内容，不取其粒度。
- **自写 ffmpeg 命令包装脚本库**（像 #1 的 42 个脚本、#16 的 `fftools.py`）：那是另一个产品，不是 skill。
  本 skill 走「教 agent 写对裸命令 + 给几个必要的校验脚本（probe 断言、响度两遍、产物契约检查）」的路线。
- **直播推流运维**（SRS、mediamtx、OBS、NDI、DeckLink、PTZ）：`media-os` 里有这一整层，但那是**运行一个
  流媒体服务器**，与「把文件处理成规格」是两类事，且更靠近 `observability` / 运维。HLS/DASH **打包**留下，
  **服务器运维**不取。
- **ossrs/srs `skills/srs-support`**（29233★，MIT，2026-09-05）：按上一条同理排除——它是 SRS 服务器的支持手册，
  不是 ffmpeg 打包指南。留此一行以免下轮重新评估。

### 本机实验：每条裁决的复现证据

环境：ffmpeg / ffprobe **N-126134-gc48230eb86-20260814**（自建，含 libx264 / libx265 / libsvtav1 / libvpx-vp9）、
vips **8.18.6**、Python 3.14 + Pillow **12.3.0**。测试源由
`ffmpeg -f lavfi -i testsrc2=size=640x480:rate=30:duration=3 -f lavfi -i sine=frequency=440:duration=3 -aspect 16:9`
生成（故意造成 SAR 4:3 / DAR 16:9 的非方形像素源）。

| 裁决 | 复现方式 | 观测结果 |
|---|---|---|
| C2 libsvtav1 默认 | `ffmpeg -i t.mp4 -c:v libsvtav1 -an a1.mkv`（不给 `-crf`/`-preset`） | `SVT [config]: preset / tune / pred struct : **8** / PSNR / random access`；`SVT [config]: BRC mode / rate factor : **CRF / 35.00**`。而 `ffmpeg -h encoder=libsvtav1` 显示 `-crf … (default 0)`、`-preset … (default -2)` —— **`-h` 的默认值是哨兵，不是生效值** |
| C3 VP9 `-b:v 0` | 同源三次编码后比字节数 | `-crf 30` → 1 221 946 B；`-crf 30 -b:v 0` → **1 221 946 B（完全相同）**；`-crf 30 -b:v 256k` → 239 192 B。印证官方「easy content 下 CQ 与 CRF 表现一致」，也印证一旦模板里带了 `-b:v` 就会静默变模式 |
| C5 `scale` 与 `setsar` | 三种写法后 `ffprobe -show_entries stream=width,height,sample_aspect_ratio,display_aspect_ratio` | 源 `640,480,SAR 4:3,DAR 16:9`；`scale=320:240` → `320,240,**4:3**,**16:9**`（DAR 正确保持）；`scale=320:240,setsar=1` → `320,240,1:1,**4:3**`（**DAR 被改坏**）；`-s 320x240` → `320,240,4:3,16:9`（与裸 scale 相同） |
| C7 loudnorm 采样率 | 源音频 44 100 Hz，两种输出 | `-af loudnorm=I=-16 -vn out.wav` → `pcm_s16le,**192000**`；`-af loudnorm=I=-16:TP=-1.5 -c:v copy out.mp4` → `aac,**96000**`（被 AAC 上限截断）。两次都**无任何告警** |
| C7 loudnorm 默认值 | `ffmpeg -h filter=loudnorm` | `I` 默认 **-24**、`LRA` 默认 **7**、`TP` 默认 **-2**、`linear` 默认 true 但描述为 "normalize linearly **if possible**"（需要 `measured_*` 才可能） |
| C8 faststart | `-c copy` 两次，逐个读顶层 box 类型 | 不加 → `['ftyp','free','mdat','moov']`；`-movflags +faststart` → `['ftyp','**moov**','free','mdat']` |
| C9 奇数尺寸 | `-vf scale=321:241 -c:v libx264` | `[libx264] width not divisible by 2 (321x241)` → `Error while opening encoder` → 产物 `moov atom not found`（文件不可用）。`scale=W:-2` 自动取偶可消除 |
| C10 静图元数据 | Pillow 造 `src2.jpg`（ICC 588 B + EXIF `Orientation=6` + `Make=ACME`），分别过 ffmpeg 与 vips | 源：`icc=588 orientation=6 make=ACME`；`ffmpeg -i src2.jpg -q:v 2 ff2.jpg` → `icc=588 **orientation=None make=None**`（EXIF 全丢；**该构建默认已应用朝向**，输出 480×640，`-noautorotate` 时输出 640×480）；`vips copy src2.jpg vips2.jpg[Q=90]` → `icc=588 orientation=6 make=ACME`（全保）。**Phase D 复测更正**：同一构建上 640×480 / Orientation=6 的源经 `ffmpeg -i src.jpg -q:v 2 out.jpg` 输出 **480×640**，即**朝向被应用了**；加 `-noautorotate` 则输出 640×480。两种情况 EXIF 均被剥离。真正的失败模式不是「一定不转」，而是「转不转由构建默认决定，且标签已丢、无从纠正」 |

## 立项判据核对

逐条对照 `docs/roadmap.md`「新增主题的判据」：

**判据 1 — 它对应一次真实任务的完整上下文，不需要同时加载另一个同级 skill 才能干活：满足。**
典型任务「把这段 4K HDR 手机素材做成 9:16、带烧录字幕、−14 LUFS 的 Reels，并给我一份 HLS」在本 skill 内
闭环：ffprobe 探测 → HDR 判定与 `zscale`/`tonemap` → `scale`/`crop` 与偶数尺寸 → libass 字体检查与烧录 →
两遍 loudnorm 与采样率收尾 → `+faststart` 导出 → HLS 分段与 GOP 对齐 → 产物回读与目视核查。
图像侧的「把这批 RAW 导出的 JPEG 批量压成 WebP，保留 ICC、修正 EXIF 朝向、再出一张雪碧图」同样闭环。
两条链路共用同一套「量事实 → 执行 → 回读 → 目视」的交付门，不需要借另一个同级 skill。

**判据 2 — 至少存在 3 个活跃（6 个月内有推送）、评审量表总分 ≥8 的上游：满足，且远超下限。**
符合条件的上游共 **10 个**（全部 `pushed_at` 经 `gh api` 实测，全部在 6 个月内）：

| 上游 | 最近推送 | 总分 |
|---|---|---|
| kajisho5/ffmpeg-skill | 2026-09-11 | 13 |
| GoogleCloudPlatform/vertex-ai-creative-studio `genmedia-*` | 2026-09-11 | 13 |
| TerminalSkills/skills `skills/ffmpeg` | 2026-09-04 | 11 |
| damionrashford/media-os `skills/ffmpeg-*` | 2026-05-31 | 10 |
| n0an/ffmpeg-skill | 2026-09-08 | 10 |
| maxazure/video-editing-skill | 2026-09-10 | 10 |
| chang416/cutcraft | 2026-08-14 | 10 |
| TerminalSkills/skills `skills/imagemagick` | 2026-09-04 | 9 |
| TerminalSkills/skills `skills/sharp` | 2026-09-04 | 9 |
| DabRlin/ffmpeg-skills | 2026-08-06 | 9 |

另有 11 个官方文档类上游（`kind: docs`，总分 11–14）作为全部事实的取证来源。
**结论：判据 2 通过，不需要动用第 4 条官方厂商特例**（虽然 Google 的 `genmedia-*` 恰好也能满足它）。

需要诚实标注的一点：这 10 个里**图像侧只有 3 个**，且全部来自同一个仓库（`TerminalSkills/skills`）。
也就是说，**视频/音频侧有多源交叉验证，图像侧只有单源**。处理方式：图像侧的每一条规则都必须由
官方文档（sharp / ImageMagick / libvips / Pillow）独立取证，`TerminalSkills` 只提供覆盖面与结构——
本次调研已经因此抓出它两处错误（C6、C9），证明这个处理方式是必要的而非形式化的。

**判据 3 — 它不是既有 skill 的子集：满足。**
逐个对照可能的父集：`frontend-design` 管的是「该给浏览器发哪一张图、怎么不拖垮 LCP/CLS」，不管
`-crf`、色彩空间、EXIF 存亡或 HLS 分段；`office` 管文档格式的对象模型；`astro`/`react` 管框架构建期的
image API；`ai-engineering` 管模型调用；`generative-media` 管概率性产出。本 skill 的核心资产——
编解码器与容器选型、滤镜图组装、关键帧与 GOP、色彩标签与元数据、响度标准、批量图像管线——
**在现有任何 skill 里都没有落点**。反过来说，本次 REJECT 的 #15 #18 恰恰证明边界是清晰可判的：
它们「看起来像图像处理」，但一读正文就全是 `srcset` 与 CDN，干净利落地归了 `frontend-design`。

**判据 4 — 官方厂商特例：不需要动用。** 判据 2 已独立满足。
（`GoogleCloudPlatform/vertex-ai-creative-studio` 虽是官方组织维护的活跃 skill 仓库，但它只覆盖本主题的
一小片，不构成「单一权威上游改写」，因此**标题下不写那一行**。）

**总结论：`media-processing` 够格立项。** 主干 `kajisho5/ffmpeg-skill`（工作流与交付门）+
`damionrashford/media-os`（HLS/DASH 与专业条目）+ `n0an/ffmpeg-skill`（参数纪律）+
`TerminalSkills/skills`（图像三件套）+ `GoogleCloudPlatform`（官方权威锚点），
全部事实以 FFmpeg / sharp / ImageMagick / libvips / Pillow / EBU 官方文档复核。
唯一需要在 Phase C 特别用力的是**图像侧的单源风险**，办法是逐条回官方文档取证。
