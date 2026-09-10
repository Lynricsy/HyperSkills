# chrome-extension 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"chrome extension MV3 agent skill SKILL.md github WXT service worker"`
  - <https://www.skills.sh>（经 web_search 命中 `paulirish/dotfiles` 的
    `hot-reloading-for-chrome-extensions`）
  - GitHub 搜索：`search/repositories?q=chrome extension skill agent in:name,description`
    （按 stars 取前 40 条，逐条核 license / pushed_at）
  - `github/awesome-copilot`：`git/trees/main?recursive=1` 过滤
    `^(skills|instructions)/.*(chrome|browser-ext|manifest|webext)` —— 只命中
    `skills/chrome-devtools`（浏览器自动化，不在本 skill 范围）
  - 领域官方组织仓库：`GoogleChrome/`（modern-web-guidance、chrome-extensions-samples、
    已归档的 developer.chrome.com）、`wxt-dev/`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 通过，账号 `Lynricsy`，token scopes `repo/workflow/read:org/gist`；
  全程未使用匿名 API）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GoogleChrome/modern-web-guidance `skills/chrome-extensions` | https://github.com/GoogleChrome/modern-web-guidance | 2168 | 2026-09-07 | Apache-2.0 | MV3 全栈 + Web Store 上架 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | Chrome 团队自己维护的 skill。20 条「违反即构建不可用」硬规则 + 20 个 API reference + 4 个 webstore reference，全是失败模式而非 API 抄写（`openPanelOnActionClick` 拼错会静默中止 SW、offscreen 文档里 `chrome.downloads` 是 undefined、`chrome.windows` 没有 `.query()`）。抽查 3 条（activeTab 只认直接手势、offscreen API 白名单、CSP 不可放宽）全部与官方文档一致 |
| 2 | samber/cc-skills `skills/chrome-extension` | https://github.com/samber/cc-skills | 209 | 2026-09-07 | MIT | MV3 架构 / 上下文模型 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 唯一把「5 个执行上下文 + 通道矩阵」讲清楚的候选：`execution-contexts.md` 逐上下文列出 chrome.* 可用性、DOM、网络、生命周期、硬限制。抽查 3 条（SW 30s、storage.session 需 `setAccessLevel` 才对 content script 可见、`webRequest` 阻塞在 MV3 移除）全对 |
| 3 | developer.chrome.com/docs/extensions + /docs/webstore | https://developer.chrome.com/docs/extensions | — | 持续更新（`sw` 页 Last updated 2023-05-02，DNR/messaging 页含 Chrome 148 条目） | CC-BY-4.0（站点页脚）；旧源仓 GoogleChrome/developer.chrome.com 已归档、LICENSE 为 CC-BY-SA-4.0 | 全部事实基准 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方文档，本 skill 每条规则的取证来源。见「备注」里的许可实查结论 |
| 4 | wxt-dev/wxt（wxt.dev 文档） | https://github.com/wxt-dev/wxt | 10478 | 2026-09-07 | MIT | WXT 工程化基准 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | WXT 官方，v0.21.4。文档站直接提供 LLM 友好的 `.md`（`https://wxt.dev/guide/essentials/unit-testing.md`），可逐条取证：`WxtVitest()` + `fakeBrowser`、Playwright E2E 指向 `.output/chrome-mv3`、WXT 本身不提供 messaging（推荐 `@webext-core/messaging` 等）、0.20 起 `wxt/storage`/`wxt/client` 迁到 `#imports` 与 `wxt/utils/*` |
| 5 | pproenca/dot-skills `skills/.experimental/wxt-browser-extensions` | https://github.com/pproenca/dot-skills | 207 | 2026-08-15 | MIT | WXT 49 条规则 | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE | 每条规则一个文件，覆盖 `svc-*`/`inject-*`/`msg-*`/`store-*`/`bundle-*`。用作 WXT 侧覆盖面清单与 `store-versioned-migrations`、`inject-choose-correct-world` 的口径来源。扣分：目录在 `.experimental/`，且 `svc-keep-alive-patterns` 与官方「不要人为保活」相左 |
| 6 | ericrisco/rsc-harness `skills/chrome-extension` | https://github.com/ericrisco/rsc-harness | 81 | 2026-09-10 | MIT | MV3 陷阱 + 骨架选型 | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE | 「三个互不共享内存的上下文」这个心智模型写得最短最准；Vanilla / Vite+CRXJS 选型表可用。扣分：`tags`/`recommends`/`origin` 是 agent 专属字段（须剥离），且「MV2 phase-out 始于 2024-06 且仍在推进」已过时 |
| 7 | pproenca/dot-skills `skills/.experimental/chrome-extension` | https://github.com/pproenca/dot-skills | 207 | 2026-08-15 | MIT | MV3 67 条性能/风格规则 | 1 | 3 | 2 | 2 | 2 | 10 | INCLUDE | 覆盖面清单价值高（`mem-*`、`err-*`、`test-*`）。扣分：约一半是通用 TS 命名/风格（`style-boolean-naming` 等，与 `typescript` skill 重叠），且 `content-programmatic-injection`「优先程序化注入而非 manifest 声明」与官方相反 |
| 8 | pproenca/dot-skills `skills/.experimental/chrome-extension-ui` | https://github.com/pproenca/dot-skills | 207 | 2026-08-15 | MIT | 扩展 UI / a11y | 1 | 3 | 2 | 2 | 2 | 10 | MAYBE | 大部分（`access-*`、`brand-*`、`feedback-*`）属 `frontend-design` 边界，本 skill 只取三条扩展特有项：popup vs side panel 选择、注入 UI 用 Shadow DOM、popup 必须即时渲染（缓存数据先画） |
| 9 | tenequm/skills `skills/chrome-extension-wxt` | https://github.com/tenequm/skills | 36 | 2026-09-09 | MIT | WXT 项目骨架 | 1 | 3 | 2 | 1 | 2 | 9 | INCLUDE | 只取 entrypoints 目录约定与 `zip`/多浏览器构建命令。扣分严重：`import { storage } from 'wxt/storage'`、`import { injectScript } from 'wxt/client'` 是 0.20 之前的路径；「V2 deprecated as of 2025」属时间敏感表述；含 `openclaw` 等 agent 专属字段 |
| 10 | quangpl/browser-extension-skills `skills/extension-test`、`extension-migration`、`extension-manifest` | https://github.com/quangpl/browser-extension-skills | 49 | 2026-06-10 | MIT | 测试分层 + MV2→MV3 清单 | 1 | 1 | 3 | 1 | 2 | 8 | INCLUDE | 唯一给出完整测试分层（Jest + `jest-chrome` 单测 / Puppeteer E2E / 取扩展 ID 的 `service_worker` target 技巧）与 permission→API 映射表的候选。扣分：`extension-test` 断言「Extensions CANNOT run in headless mode」与官方 `--headless=new` 明确矛盾；推送已过 3 个月 |
| 11 | GoogleChrome/chrome-extensions-samples | https://github.com/GoogleChrome/chrome-extensions-samples | 17756 | 2026-09-08 | Apache-2.0 | 官方可运行样例 | 3 | 3 | 2 | 3 | 2 | 13 | MAYBE | 官方样例仓，是代码不是规则，无「陷阱」文本可合入。只用来核对 offscreen 生命周期、side panel 打开方式、Puppeteer 测试目标的真实写法 → `relation: reference` |
| 12 | extensiondev/skill `skills/extension-dev` | https://github.com/extensiondev/skill | 0 | 2026-08-21 | Apache-2.0 | extension.dev 平台 | 0 | 3 | 2 | 2 | 2 | 9 | REJECT | 产品包装：正文几乎全在教怎么调 `@extension.dev/mcp` 的 30 个工具和 `npx extension@latest` CLI，与 clerk/skills 同类，按立项约定排除 |
| 13 | davila7/claude-code-templates `.../browser-extension-builder` | https://github.com/davila7/claude-code-templates | 30584 | 2026-09-10 | MIT | 通用模板 | 1 | 3 | 1 | 2 | 2 | 9 | MAYBE | 星数来自模板集合本身，与该 skill 质量无关。内容是角色扮演 + 目录树 + monetization 段落，无独有事实，未采用 |
| 14 | LevyBytes/AI-SKILL-chrome-extensions | https://github.com/LevyBytes/AI-SKILL-chrome-extensions | 0 | 2026-06-22 | AGPL-3.0 | MV3 参考 | 0 | 1 | 2 | 2 | 2 | 7 | REJECT | AGPL-3.0 按许可规则只能 reference，且 0 star / 无独有主题；其主题清单已被候选 1、2 完全覆盖，连 reference 都不必挂 |
| 15 | Alcyone-Labs/chrome-extension-agent-skill | https://github.com/Alcyone-Labs/chrome-extension-agent-skill | 3 | 2026-01-21 | MIT | MV3 通用 | 0 | 0 | 2 | 2 | 2 | 6 | REJECT | 超过 6 个月未推送（新鲜 0），非官方，量表规定直接 REJECT |
| 16 | sadakenji/Native-Messaging-Skill | https://github.com/sadakenji/Native-Messaging-Skill | 0 | 2026-07-05 | MIT | 仅 native messaging | 0 | 2 | 2 | 2 | 2 | 8 | REJECT | 单一窄主题（native messaging host 清单文件），0 star 无采纳证据；本 skill 只在 reference 里点一句 native messaging 的存在，不值得挂上游 |
| 17 | amazingjoe/chrome-extension-builder-skill | https://github.com/amazingjoe/chrome-extension-builder-skill | 1 | 2026-06-28 | MIT | 「自然语言生成扩展」 | 0 | 2 | 1 | 2 | 2 | 7 | REJECT | 教程式提示词包装，无可执行规则 |
| 18 | gandli/browser-extension-skills | https://github.com/gandli/browser-extension-skills | 0 | 2026-09-05 | MIT | 扩展开发 + CDP 调试 | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | 0 star、与候选 10 同名同结构疑似衍生，且主体是 CDP 测网页（属浏览器自动化，本 skill 明确不覆盖） |
| 19 | github/awesome-copilot `skills/chrome-devtools` | https://github.com/github/awesome-copilot | 38860 | 2026-09-10 | MIT | Chrome DevTools MCP | 3 | 3 | 3 | 3 | 2 | 14 | REJECT（范围） | 质量无可指摘，但内容是用 DevTools MCP 调试**网页**，属浏览器自动化。awesome-copilot 全仓 `skills/` 与 `instructions/` 中没有任何扩展开发条目 |
| 20 | Tencent/BrowserSkill | https://github.com/Tencent/BrowserSkill | 1916 | 2026-09-10 | MIT | 让 agent 操作浏览器 | 2 | 3 | 2 | 2 | 2 | 11 | REJECT（范围） | 是「agent 通过扩展操控浏览器」的运行时产品，不是教人写扩展 |
| 21 | paulirish/dotfiles `hot-reloading-for-chrome-extensions` | https://github.com/paulirish/dotfiles | 4361 | 2026-09-07 | NONE（API `license: null`） | 扩展热重载 | 2 | 3 | 2 | 2 | 0 | 9 | MAYBE | 主题过窄（一个热重载片段），且 WXT/CRXJS 已自带 HMR；未采用，不挂上游 |
| 22 | clerk/skills | https://github.com/clerk/skills | 71 | 2026-09-09 | NONE（API `license: null`） | Clerk 产品接入 | 0 | 3 | 2 | 2 | 0 | 7 | REJECT | 任务书明确排除的产品包装仓库 |
| 23 | playwright.dev `docs/chrome-extensions`（microsoft/playwright） | https://github.com/microsoft/playwright | 95926 | 2026-09-10 | Apache-2.0 | 扩展 E2E 加载契约 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 由 WXT 的 E2E 指南转过去发现（WXT 自己不写扩展启动，直接指向这里）。给出三条别处查不到的硬约束：扩展只在持久化上下文里生效、Chrome/Edge 已移除侧载扩展的命令行开关所以必须用 Playwright 自带 Chromium（`channel: 'chromium'`，也是 headless 的前提）、MV3 worker 空闲挂起后复用同一个 `Worker` 句柄 |

## 深度审查

### 1. GoogleChrome/modern-web-guidance `skills/chrome-extensions`（主干）

- 结构：单个 530 行 SKILL.md + `references/extensions/*`（20 个 API 主题）+
  `references/webstore/*`（4 个上架主题）。frontmatter 只有 `name` + 一段极长的
  `description`（把触发关键词全塞进去），没有 agent 专属字段，也没有 `license` 字段——
  许可由仓库根 Apache-2.0 覆盖（已确认 `skills/chrome-extensions/` 下无独立 LICENSE）。
- 质量：正文组织成「Mandatory Rules（20 条）→ Always Manifest V3 → Part 2 上架 →
  Reference Files 表 → Output Checklist（30 项）」。每条规则都是 ❌/✅ 对照的真实故障，
  例如：`sidePanel.setPanelBehavior({ openPanelOnActionIconClick })` 这个拼写错误会抛同步
  TypeError 并静默中止 service worker；offscreen 文档里 `chrome.downloads`/`chrome.action`
  是 `undefined`；`chrome.windows` 根本没有 `.query()`；`chrome.permissions.request()` 在
  `onMessage` 里只要先 `await` 过一次手势就失效。这些是官方文档里不会以「陷阱」形式出现、
  只有踩过才知道的东西，正是标准第 3 节要的「teach the failure, not the API」。
- 弱点：Part 2 把上架流程绑在一个自创产物 `CHROMEWEBSTORE.md` 上（要求 agent 在用户项目
  根目录维护这个文件）。这是工作流约定而非平台事实，不合入；只取其中「每条 permission
  一句面向审核的白话理由」「描述必须写功能不写感受」「zip 排除 .git/node_modules/.env」
  这些可验证的审核规则。另外 Prompt API 一节交叉引用了同仓的 `modern-web-guidance` skill，
  按标准第 1.3 节属上游交叉引用残留，必须删除（本仓库不收 Prompt API 这条）。
- 重叠：与候选 2 在 SW 生命周期 / 消息 / 权限上大面积重叠，但侧重不同——它给症状，
  候选 2 给上下文模型。

### 2. samber/cc-skills `skills/chrome-extension`

- 结构：340 行路由式 SKILL.md + 13 个自包含 reference。frontmatter 含
  `user-invocable: true`、`allowed-tools`、`metadata.openclaw`、`metadata.author`，
  全部是 agent 专属字段，合入时按标准第 1.2 节剥离。`description` 末尾写
  `Do NOT use for CRXJS/Vite-based builds — use samber/cc-skills@crxjs instead`，
  是跨仓 skill 引用，必须去掉（本 skill 自己覆盖构建选型）。
- 质量：最值得取的是 `execution-contexts.md` 的上下文能力矩阵，以及 SKILL.md 里的
  「决策树」写法（"我要给页面注入代码" → 走哪个上下文）。三条抽查全对。
  ASCII 架构图两张，符合标准第 3 节（只允许 ASCII/mermaid），但两张图内容重复，
  合入时压成一张。
- 弱点：`typescript-build.md` 是构建工具横向对比（罗列多个可选库），与标准
  「只给一个默认方案 + 一个逃生口」冲突，只取结论。
- 重叠：与候选 6 的三上下文模型同构，候选 6 更简洁，正文采用候选 6 的表述。

### 3. developer.chrome.com（事实基准）

- `docs/extensions/develop/concepts/service-workers/lifecycle`：终止三条件（30s 空闲、
  单次请求 >5min、`fetch()` 响应 >30s）与「事件和扩展 API 调用会重置计时器」；
  以及 Chrome 110/114/116/118/120 的生命周期改进清单。
- `docs/extensions/develop/migrate/mv2-deprecation-timeline`：MV2 已在 Chrome 139 彻底
  移除支持，2026-08-31 起 Web Store 下架所有剩余 MV2 扩展。**结论：MV3 是唯一形态**，
  MV2→MV3 只作为「接手遗留代码库」的迁移动作存在，不进 Core rules。
- `reference/api/alarms`：Chrome 限制闹钟最快 30 秒一次，`periodInMinutes` / `delayInMinutes`
  < 0.5 不被采纳并告警（unpacked 加载时无此限制，所以开发期看不出问题）。
- `reference/api/storage`：local 10 MB（可用 `unlimitedStorage` 放开）、session 10 MB、
  sync ≈100 KB 且单项 8 KB；session 默认**不**暴露给 content script，需
  `setAccessLevel()`；local/managed/sync 默认暴露。
- `reference/api/declarativeNetRequest`：静态 ruleset 最多 100 个、同时启用 50 个、
  保底 30000 条静态规则；session 规则 5000；动态规则 unsafe 5000 / safe 30000；
  每类正则规则 1000 条上限、单条编译后 <2 KB。
- `reference/manifest/content-security-policy`：`extension_pages` 的最低策略是
  `script-src 'self' 'wasm-unsafe-eval'; object-src 'self'`，**不可放宽**，加了
  `'unsafe-eval'` 或远端源，Chrome 在安装时报 `Insecure CSP value`。
- `develop/migrate/remote-hosted-code`：RHC 禁令；审核拒绝代号 **Blue Argon**；
  第三方依赖里的 RHC 同样算违规（Firebase Auth 曾是典型）。
- `develop/concepts/messaging`：异步回复要 `return true`（字面量），Chrome 148 起
  允许直接 `return` promise，但该能力灰度中且 devtools page 场景不启用——所以正文继续以
  `return true` 为默认做法。
- `reference/api/offscreen`：一个扩展同时只能有一个 offscreen 文档；`createDocument()`
  需要 `reasons` + `justification`；`AUDIO_PLAYBACK` 会在无音频 30 秒后自动关闭，
  其余 reason 无生命周期上限。
- `develop/concepts/content-scripts`：`world` 默认 `ISOLATED`；静态声明的 content script
  在同一文档阶段最先注入。
- `reference/api/userScripts`：Chrome ≥138 需要用户打开扩展详情页的「Allow User Scripts」，
  <138 需要开发者模式；`configureWorld({ messaging: true })` 之后走
  `runtime.onUserScriptMessage`（不是 `onMessage`）。
- `docs/webstore/review-process`：多数扩展几天、可能几周；广泛 host 权限、敏感执行权限、
  代码量大或难读会延长审核；**混淆被禁止、压缩允许**；超过三周可联系开发者支持。
- `docs/extensions/how-to/test/end-to-end-testing`：`--headless=new` 支持加载扩展
  （旧 headless 不支持）；固定扩展 ID 的做法；扩展页可直接用
  `chrome-extension://<id>/x.html` 访问；popup 可用 `action.openPopup()`。

### 4. wxt-dev/wxt（wxt.dev，WXT 工程化基准）

- 文档站对每个页面提供 `.md` 版本，取证成本极低。
- 关键事实：WXT **不提供** messaging 抽象，官方推荐 `@webext-core/messaging` /
  `webext-bridge` / `trpc-chrome`；单测用 `WxtVitest()` 插件 + `wxt/testing/fake-browser`
  的 `fakeBrowser`（`browser.storage` 有内存实现，不需要手写 mock）；E2E 官方只推荐
  Playwright，扩展路径传 `.output/chrome-mv3`；storage 用 `storage.defineItem` 并支持
  `version` + `migrations`；0.20 起 `wxt/sandbox`、`wxt/client`、`wxt/storage` 的导出迁到
  `wxt/utils/*`，推荐从 `#imports` 导入。
- 三种 content script UI（integrated / shadow root / iframe）的隔离性对照表，
  是「注入 UI 该用哪种」的权威答案。

### 5. pproenca/dot-skills 三个目录

- 结构：`SKILL.md` 是一张规则索引表，每条规则一个独立 reference 文件（67 / 49 / 52 条），
  外加 `metadata.json`、`AGENTS.md`、`assets/templates/_template.md`。
- 价值在**覆盖面清单**，不在文本：逐条对照可以查出遗漏。据此补进了本 skill 的
  `store-versioned-migrations`（storage schema 版本迁移）、`inject-spa-navigation`
  （SPA 路由变化后重新注入）、`mem-cleanup-event-listeners`（content script 卸载清理）、
  `ui-sidepanel-persistence`。
- 弱点：目录在 `.experimental/` 下（作者自己标为实验性）；多条规则与官方相反或过度概括
  （见「冲突与裁决」1、2）；`style-*`/`comp-*`/`ts-*` 属通用 TS 话题，交给 `typescript` skill。

### 6. quangpl/browser-extension-skills

- 结构：9 个 skill 目录（analyze / assets / backend / create / dev / manifest / migration /
  payment / test），每个 SKILL.md 100–130 行 + 3–5 个 reference。
- 只有三个目录在本 skill 范围内：`extension-test`（测试分层、`jest-chrome`、从
  `browser.targets()` 里挑 `type() === 'service_worker'` 拿扩展 ID）、`extension-migration`
  （MV2→MV3 变更清单）、`extension-manifest`（permission → API 映射与权限警告文案）。
  `extension-backend`（NestJS + Mongoose）、`extension-payment` 明显越界，弃用。
- 弱点：`extension-test` 的 headless 断言是硬错误（见裁决 3）；reference 之间互相
  markdown 链接，本仓库禁止（标准第 4 节）。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | content script 该静态声明还是程序化注入 | dot-skills `content-programmatic-injection`：优先 `chrome.scripting` 程序化注入以省开销；官方：匹配模式已知的页面用 manifest 静态声明，未知或条件注入才用动态/程序化 | 采官方。正文写「已知 URL 模式用 manifest 静态声明；模式不确定或需用户触发才用 `chrome.scripting`」 | `develop/concepts/content-scripts`「Use static content script declarations in manifest.json for scripts that should be automatically run on a well known set of pages」；官方厂商 > 社区 |
| 2 | 长任务要不要保活 service worker | dot-skills（chrome-extension 与 wxt 两份自相矛盾）：一边 `sw-avoid-keepalive`，一边 `svc-keep-alive-patterns` 给保活写法；官方：不要无限保活，改设计成对意外终止有韧性 | 采官方。正文只给「拆成 `chrome.alarms` 驱动的小步 + 把进度写进 `chrome.storage`」，并明确「人为 ping 保活是错的修法」 | `service-workers/lifecycle`「avoid keeping your service worker alive indefinitely」；同一上游内部矛盾时以官方为准 |
| 3 | 扩展能否在 headless Chrome 里跑 E2E | quangpl `extension-test`：**不能**，必须 `headless: false`；官方：新 headless 支持加载扩展，用 `--headless=new`（默认的旧 headless 不支持） | 采官方。正文写「CI 里用 `--headless=new`；旧 headless 加载不了扩展，这是很多人以为『扩展不能 headless』的由来」 | `how-to/test/end-to-end-testing`「Chrome's new headless mode allows Chrome to be run in an unattended environment… Start Chrome using the `--headless=new` flag」 |
| 4 | E2E 用 Puppeteer 还是 Playwright | 官方 Chrome 文档有 Puppeteer 教程且并列列出 Playwright/Selenium/WebDriverIO；quangpl 用 Puppeteer；WXT 官方：「Playwright is the only good option」 | 默认 Playwright（持久化上下文 + `.output/chrome-mv3`），逃生口写「已有 Puppeteer 套件就沿用，官方教程在 Chrome 文档」。只给一个默认 + 一个逃生口 | `docs/skill-standard.md` 第 3 节；WXT 是扩展框架侧最新的一手意见，Chrome 文档并未偏好 Puppeteer |
| 5 | WXT 的 storage / 注入工具从哪里导入 | tenequm：`from 'wxt/storage'`、`from 'wxt/client'`；WXT 官方 v0.21：这些导出已迁到 `wxt/utils/*`，推荐 `#imports` | 采官方，正文只写 `#imports`。tenequm 只保留 entrypoints 目录约定与 `zip` 命令 | wxt.dev Upgrading 指南「The APIs exported by `wxt/sandbox`, `wxt/client`, or `wxt/storage` have moved to individual exports under the `wxt/utils/*` path」；更新 > 更旧 |
| 6 | 异步 `onMessage` 回复的写法 | 三个社区上游一致要求 `return true`；官方文档新增「Chrome 148 起可直接返回 promise」但注明灰度中、devtools page 场景不启用 | 正文默认 `return true`（字面量），promise 写法只作为一句可用性说明，不作为默认。不写「2026 年后可以…」这类时间敏感表述 | `develop/concepts/messaging`「Using `return true;` will continue to work… whether this capability is enabled or not」 |
| 7 | MV2→MV3 迁移在本 skill 里的位置 | tenequm / rsc-harness / quangpl 都把 MV2 迁移当主线之一（措辞停留在「phase-out 仍在推进」）；官方：Chrome 139 起 MV2 完全不再受支持，2026-08-31 Web Store 清空剩余 MV2 | MV3 是唯一形态，Core rules 不提 MV2；迁移动作压进 `references/wxt-and-tooling.md` 的「Inheriting a Manifest V2 codebase」一节，服务于「接手一个 MV2 老库」 | `migrate/mv2-deprecation-timeline`；标准第 3 节禁止时间敏感表述，弃用内容不进主线 |
| 8 | 扩展 UI 的视觉/可访问性规则归谁 | dot-skills `chrome-extension-ui` 有 52 条（对比度、focus trap、aria、图标风格） | 只保留扩展平台特有的三条（popup vs side panel、Shadow DOM 隔离注入 UI、popup 先用缓存数据即时渲染）；通用视觉与 a11y 明确不覆盖，转交 `frontend-design` | 本波边界约定：页面视觉设计不属本 skill |
| 9 | popup 里的按钮点击算不算 `activeTab` 手势 | GoogleChrome/modern-web-guidance 第 12 条：`activeTab` 「NOT from a button click inside a side panel or popup」，两者一并否掉；官方 activeTab 页只列四种手势（executing an action / context menu item / commands 快捷键 / omnibox 建议），而**点工具栏图标打开 popup 本身就是 executing an action**，授权落在当次活动标签页上并在同源导航后保留 | 拆开裁决：popup 由工具栏点击打开，授权已经存在，popup 内按钮可以用；side panel 打开不属四种手势，且面板会跟着用户切标签页而授权留在原标签页，所以面板要 `tabs` + host 权限。正文（Core rule 20、`manifest-and-permissions.md`、`ui-surfaces.md`）按这个拆法写 | `develop/concepts/activeTab`「The following user gestures enable the "activeTab" permission: Executing an action / Executing a context menu item / Executing a keyboard shortcut from the commands API / Accepting a suggestion from the omnibox API」；官方文档 > 官方仓库里的 skill 概括。**本条是初稿写错后回改的**：初稿照抄了上游的合并说法，并据此写进了评测的 `expected_behavior`，核对官方文档后同时修正了正文与评测项 |
| 10 | Playwright 加载扩展要用哪个 Chromium | quangpl 与多数教程：`puppeteer.launch({ headless: false, --load-extension })`；Playwright 官方：扩展只在**持久化上下文**里生效，且 Chrome / Edge 已移除侧载扩展所需的命令行开关，必须用 Playwright 自带的 `channel: 'chromium'`，这也是能跑 headless 的前提 | 正文的 fixture 写 `channel: 'chromium'` 并注明原因，同时保留官方 Chrome 文档的 `--headless=new` 说明（两者说的是同一件事的不同层次） | playwright.dev/docs/chrome-extensions「Google Chrome and Microsoft Edge removed the command-line flags needed to side-load extensions, so use Chromium that comes bundled with Playwright」「Note the use of the chromium channel that allows to run extensions in headless mode」 |
| 11 | `minimum_chrome_version` 的代价 | 社区上游把它当「声明式兼容开关」，随手加；官方 browser-namespace 页：设了它，**低于该版本的用户拿不到任何后续更新**，会被冻结在当前版本（收不到修复与安全补丁） | 正文写成「这是一个刻意的决定，要配灰度发布；只有一个特性需要新版本时优先做运行时能力探测」 | `develop/concepts/browser-namespace`「Setting minimum_chrome_version stops all updates for users on older Chrome… treat it as a deliberate decision, not a routine compatibility setting」 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `chrome-modern-web-guidance` | GoogleChrome/modern-web-guidance `skills/chrome-extensions` | merged | 20 条「违反即不可用」的硬故障（side panel 无触发器、`chrome.action` 需 manifest `action` 键、offscreen 的 chrome.* 白名单、`chrome.windows` 无 `.query()`、`activeTab` 只认直接手势、`tab.url` 静默 undefined、DevTools 面板路径、用户脚本四个陷阱、手势跨消息只存活一个同步回合）；沙箱/blob/srcdoc 三种执行逃生口；上架前置清单与 permission 逐条白话理由 |
| `samber-cc-skills` | samber/cc-skills `skills/chrome-extension` | merged | 五上下文能力矩阵与通道选择表；决策树式路由（"我要做 X" → 哪个上下文 + 哪个 API）；content script → SW 的 CSP/CORS 中继模式；孤儿 content script 检测；async handler 包装器 |
| `chrome-docs` | developer.chrome.com（extensions + webstore） | merged | 所有数值与语义基准：SW 终止三条件、alarms 30 秒下限、storage 三区配额与 `setAccessLevel`、DNR 规则上限、CSP 最低策略不可放宽、RHC 与 Blue Argon、offscreen 单例与 reason 生命周期、`world` 默认 ISOLATED、userScripts 的开关门、审核时长与混淆/压缩规则、`--headless=new` |
| `playwright-docs` | playwright.dev（microsoft/playwright，Apache-2.0） | merged | E2E 加载契约：扩展只在持久化上下文生效、Chrome/Edge 已移除侧载开关故须 `channel: 'chromium'`（也是能 headless 的前提）、从 service-worker target 取扩展 ID、MV3 worker 空闲挂起后 Playwright 复用同一个 `Worker` 句柄 |
| `wxt-docs` | wxt.dev（wxt-dev/wxt） | merged | WXT 工程化：entrypoints 约定、`#imports`、`storage.defineItem` + `version`/`migrations`、三种 content script UI 的隔离性对照、`WxtVitest()` + `fakeBrowser` 单测、Playwright E2E 指向 `.output/chrome-mv3`、WXT 无内建 messaging 的事实与推荐库 |
| `dot-skills` | pproenca/dot-skills 三个 `.experimental` 目录 | merged | 覆盖面清单（据此补入 storage schema 版本迁移、SPA 路由后重注入、content script 卸载清理、side panel 状态保持、消息合并/去抖）；WXT 侧规则分类骨架 |
| `rsc-harness` | ericrisco/rsc-harness `skills/chrome-extension` | merged | 「三个互不共享内存、只靠消息通信的上下文」这一心智模型的表述；Vanilla vs Vite+CRXJS vs WXT 的选型口径 |
| `quangpl-ext` | quangpl/browser-extension-skills（`extension-test`/`extension-migration`/`extension-manifest`） | merged | 测试三层划分与 `jest-chrome` / `@webext-core/fake-browser` 的用法定位；从 `browser.targets()` 取 `service_worker` 拿扩展 ID；MV2→MV3 变更清单；permission → 权限警告映射 |
| `tenequm-wxt` | tenequm/skills `skills/chrome-extension-wxt` | merged | WXT `entrypoints/` 目录约定与 `dev`/`build`/`zip --browser` 命令；多浏览器产物命名 |
| `chrome-samples` | GoogleChrome/chrome-extensions-samples | reference | 只读校验：offscreen 单例的 `runtime.getContexts()` 写法、side panel 打开方式、Puppeteer 测试目标，用来确认上面的规则在真实官方样例里成立。未复制任何代码 |

## 基线缺口

无 skill（`uv run tools/run_evals.py chrome-extension --baseline`，Claude Opus 5 · medium）
跑完后逐条读 `answer.md` 判定。基线整体很强（四个场景都真的动手验证过），未达成项如下：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1（service worker） | ①「事件/扩展 API 调用会重置空闲计时器」②`buildReport()` 的 `fetch` 撞 30 秒响应上限 | 基线给了「~30 秒空闲即被终止」，但写下「Chrome 不因扩展 API 调用而免死」，与官方 `service-workers/lifecycle`「Receiving an event or calling an extension API resets this timer」直接相反——它删掉保活心跳的理由本身是错的；`buildReport()` 那个无超时的 `fetch` 也完全没提。另外状态外移只用了 `chrome.storage.local`，没有区分 `session`（热态）与 `local`（累计值），记为部分达成 |
| 2（manifest 与上架） | `side_panel` 的触发器契约；`panel.html` 不能靠 `activeTab` | 基线只查到缺 `sidePanel` 权限、`open()` 需要手势与 `windowId`，没提「声明 `side_panel` 不等于可打开」以及 `setPanelBehavior({ openPanelOnActionClick })` 这条路（及其与 `default_popup` 互斥）；也没讨论面板自己的标签页访问权——它把 `activeTab` 写进建议权限集就收工，而面板会跟着用户切标签页、旧授权留在原标签页 |
| 3（content script） | 扩展重载后 content script 被孤立、`chrome.runtime` 全线抛 `Extension context invalidated`，需先查 `chrome.runtime?.id` 再消息并做卸载 | 基线抓到了 MutationObserver 自触发风暴，但完全没提孤儿 content script 与卸载路径 |
| 4（负例） | —（3/3 全达成，`skill_read=false`） | 用于确认有 skill 时也不误触发 |

基线达成情况汇总：场景 1 = 5/8（另 1 项部分）、场景 2 = 8/10、场景 3 = 7/8、场景 4 = 3/3。
评测有区分度，无需改写场景的 `query` 或夹具。

## 评测结果

两组都是 `anthropic/claude-opus-5` · thinking `medium`（`tools/run_evals.py` 默认，未传
`--model` / `--thinking`）。逐条判定依据是 `/tmp/hs-evals/chrome-extension/anthropic-claude-opus-5-medium/{baseline,skill}/<n>/answer.md`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 service worker 生命周期 | claude-opus-5:medium | 无（baseline） | false | 5/8 + 1 部分：`localStorage` 不存在 ✓、监听器在 `await` 之后注册 ✓、`alarms` 0.5 分钟下限 ✓、删保活心跳 ✓、`return true` 字面量 ✓；状态外移**部分**（只用 `local`，未区分 `session`）。未达成：30 秒空闲 + 「事件/API 调用重置计时器」✗（写成相反的「Chrome 不因扩展 API 调用而免死」）、`buildReport()` 的 30 秒 `fetch` 上限 ✗ | 基线自己写了 Node + `vm` 打桩脚本做冒烟，定位很细（连 `hostOf` 拿 tabId 当 host 都抓到了），失分全在平台数值与语义 |
| 1 service worker 生命周期 | claude-opus-5:medium | 有 | true | 7/8：新增达成 `buildReport()` 撞 30 秒响应上限并给 `AbortSignal.timeout(10_000)` ✓；状态外移改为「热态放 `chrome.storage.session`、累计值放 `local`」✓，其余 5 项保持 ✓。仍未达成：没有明说「事件与扩展 API 调用会重置空闲计时器」✗ | **填补的缺口**：30 秒 `fetch` 上限、`session`/`local` 分区。删保活心跳的理由也改对了（「MV3 不允许人为保活，它只是掩盖状态设计缺陷」），不再是基线那条错误依据。另外主动指出缺 `"action": {}` 会让 `chrome.action` 为 undefined |
| 2 manifest 与上架审查 | claude-opus-5:medium | 无（baseline） | false | 8/10：`webRequestBlocking`→DNR ✓、CSP 最低策略与安装期 `Insecure CSP value` ✓、CDN 脚本=RHC ✓、内联 onclick/script 被 CSP 拦 ✓、`eval` ✓、收窄 `<all_urls>` 与逐权限理由 ✓、WAR `["*"]` 指纹化 ✓、描述空泛+缺 icons ✓。未达成：`side_panel` 触发器契约 ✗、`panel.html` 的标签页访问权 ✗ | 基线真的用本机 `/usr/bin/chromium` 装了一遍并二分定位，CSP 两条拒绝信息是实测输出——这一场基线极强 |
| 2 manifest 与上架审查 | claude-opus-5:medium | 有 | true | 8/10：同上八项 ✓；`side_panel` 触发器契约 ✗、`panel.html` 的标签页访问权 ✗ | **本场未净填补缺口**，如实记录。差异在别处：有 skill 时补出了「`document_start` 时 `document.body` 为 null，content.js 的 DOM 查询全失效」，并把 popup 的 `activeTab` 说对（「popup 已经天然持有 activeTab」，与裁决 9 一致）；输出严格走了 `## Output format` 的 `path:line` + before/after 形态 |
| 3 content script 世界与消息 | claude-opus-5:medium | 无（baseline） | false | 7/8：隔离世界 ✓、MAIN world 或桥接（并说明 MAIN 无 `chrome.*`）✓、`document_start` 无 body ✓、`storage.session` 需 `setAccessLevel` ✓、`bridge.js` 需 WAR + `getURL` ✓、顶层 `await` 是解析期错误 ✓、`message` 未校验 `source`/`origin` ✓。未达成：孤儿 content script 与卸载路径 ✗ | 基线只抓到 MutationObserver 自触发风暴，没有把「扩展重载 → `Extension context invalidated`」这一层接上 |
| 3 content script 世界与消息 | claude-opus-5:medium | 有 | true | 8/8：新增达成 `alive()` / `teardown()`——「扩展重载后脚本仍在页面里跑，`chrome.runtime` 每次调用都抛 `Extension context invalidated`」✓ | **填补的缺口**：孤儿检测与卸载。并且把 shadow root + 稳定容器 id、`writingBadge` 自写忽略、`session` 区开放后的敏感值告警都写进了方案 |
| 4 负例（营销页 Playwright 登录测试） | claude-opus-5:medium | 无（baseline） | **false** | 3/3：未读本 skill ✓、产出普通网页的 Playwright 用例（`page.route` 打桩 401/500、`role=alert` 断言）✓、未引入扩展概念 ✓ | — |
| 4 负例（营销页 Playwright 登录测试） | claude-opus-5:medium | 有 | **false** | 3/3：`skill_read == false` ✓、同样只产出网页 E2E（真的装了 `@playwright/test` 跑出 2 passed / 1 failed 并定位到缺失的 `assets/login.js`）✓、未提 unpacked 加载、`--disable-extensions-except`、manifest、service worker 或 `chrome.*` 打桩 ✓ | 负例边界成立：即使会话里挂着 chrome-extension skill，也没有被误触发 |

结论：**通过**。两条基线未达成的行为在有 skill 时达成——场景 1 的
「`fetch` 响应 30 秒上限会终止 worker」与场景 3 的「孤儿 content script 检测与卸载」；
场景 1 另有一项由部分达成转为达成（`session` / `local` 分区）。负例两组 `skill_read`
均为 `false`。场景 2 未净填补缺口，已如实记录，不作为通过依据。

### Phase D 期间对 skill 与评测的修改（可追溯）

1. 读官方 activeTab 文档后发现初稿的 Core rule 20 抄错了上游（见裁决 9），修正了
   `SKILL.md`、`manifest-and-permissions.md`、`ui-surfaces.md`，同时把当初据错误规则写下的
   场景 2 `expected_behavior` 换成正确的那条（`panel.html` 不能靠 `activeTab`）。
   随后**整组重跑**「有 skill」四个场景，基线未重跑（`query` 与夹具未变，
   `expected_behavior` 不进入模型输入，可比性成立）。
2. 场景 1 原本有一条把四个事实捆在一起的 `expected_behavior`，按标准第 6 节「一条一个可观察
   行为」拆成两条，并去掉与夹具无关的「单次请求 >5 分钟」要求。两组用同一份拆分后的量表重判。
3. 复核发现 `review` workflow 缺「逐 surface 核对它真正需要的访问权」这一步（这是本 skill
   自己 Core rules 里最高频的静默失效来源），补上后只重跑了场景 2（`--only 2`）。
   结果仍是 8/10，如实记录。

## 备注

### `kind: docs` 的许可实查

- **developer.chrome.com**：站点页脚写
  「Except as otherwise noted, the content of this page is licensed under the
  Creative Commons **Attribution 4.0** License, and code samples are licensed under the
  Apache 2.0 License」，据此 `license: CC-BY-4.0`，`notes` 里写署名。
  需要注意的是旧内容源仓 `GoogleChrome/developer.chrome.com` 已于 2024-03 归档，
  其 `LICENSE` 文件是 **CC-BY-SA-4.0**（API 报 `NOASSERTION`）。两者不一致时以现行站点
  页脚为准，但为稳妥起见**未从任何页面复制成句文本**，只取技术事实与数值。
- **wxt.dev**：源仓 `wxt-dev/wxt` 为 MIT（GitHub API 明确返回 `MIT`），文档目录在同一仓库内，
  故 `license: MIT`、`relation: merged`。
- **playwright.dev**：源仓 `microsoft/playwright` 为 Apache-2.0（GitHub API 返回
  `Apache-2.0`），`docs/` 在同一仓库内，故 `license: Apache-2.0`、`relation: merged`。

### 许可分类

- 全部 merged 上游为 MIT / Apache-2.0 / CC-BY-4.0，无 GPL 家族、无 MPL、无 CC-BY-SA 派生内容。
- `chrome-samples` 是 Apache-2.0（可 merged），但本 skill 只读它做交叉校验、未复制内容，
  按 schema 语义标 `relation: reference`。
- 无许可仓库（`paulirish/dotfiles`、`clerk/skills`）均未采用，不出现在 SOURCES.yaml。

### 临界上游复核结论

- `quangpl/browser-extension-skills` 推送 2026-06-10，距调研日 3 个月，仍在 6 个月窗口内 →
  可 merged。其 headless 错误断言按裁决 3 处理。
- `Alcyone-Labs/chrome-extension-agent-skill` 推送 2026-01-21，已超 6 个月且非官方 → REJECT。

### 未来同步时要盯的上游

- `developer.chrome.com`：`return`-promise 的 `onMessage`（Chrome 148 灰度）一旦全量，
  `references/messaging-and-contexts.md` 的默认写法要重新裁决。
- `wxt-dev/wxt`：v0.21 → v1.0 期间导入路径与 `@wxt-dev/*` 子包版本仍在动。
- `GoogleChrome/modern-web-guidance`：Chrome 团队在持续加新 API 主题（Prompt API、
  `chrome.contextMenus` 的 `"tab"` context 需 M150+），下次同步时检查是否有新的硬故障条目。
- `developer.chrome.com` 的 `develop/concepts/browser-namespace`：Chrome 148 起 `browser.*`
  原生可用、152 起 `devtools_page` 扩展也可用。等 148 成为绝对多数后，
  `references/wxt-and-tooling.md` 里「polyfill 是兼容层」这段与 `chrome.*` 的默认写法要重新裁决。
- `playwright.dev/docs/chrome-extensions`：`channel: 'chromium'` 这条约束来自 Chrome/Edge
  的开关移除，属浏览器侧变动，Playwright 侧写法可能随之调整。

### 放弃的方向

- 未做 native messaging 的独立章节：`references/service-worker.md` 只在「什么会延长 worker
  寿命」里列出 `runtime.connectNative()` 的端口，`## Scope` 明确把 native messaging host
  的部署排除——它把问题变成桌面应用分发，不是扩展代码问题。
- 未做 Prompt API / 内置 AI：属 Chrome 平台 AI 能力而非扩展形态，且上游只有一处覆盖。
- 未做 Firefox / Safari 的 WebExtensions 差异章节：`manifest_version` 与 API 差异由 WXT 的
  跨浏览器构建承担，正文只在 WXT 一节点出「用 `#imports` 的 `browser`，不要直接写
  `chrome.*`」，并补上 Chrome 148 起 `browser.*` 已原生可用这一事实。
