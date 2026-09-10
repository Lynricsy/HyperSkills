# laravel 调研记录

**单一权威上游改写**（官方厂商特例判据：`laravel/boost` 官方 skill 仓库 merged + `laravel.com/docs`
官方文档 merged + 多个社区上游）。

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"Laravel Claude agent skill SKILL.md github 2026"`
  - `gh search repos "laravel skill"` / `"laravel agent skills"`（各 40 条，见候选表）
  - `gh search code "laravel-best-practices" --filename SKILL.md`（30 条，用于分辨
    「独立作品」与「被 `boost:install` 复制进业务仓库的官方副本」）
  - `github/awesome-copilot`：`gh api .../git/trees/main?recursive=1 | grep -iE 'php|laravel'`
  - 领域官方组织：`laravel/`（boost、agent-skills、docs、framework、pennant）、
    `livewire/`、`pestphp/`、`php/`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 正常，账号 Lynricsy，全程登录态）

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | laravel/boost `.ai/laravel/skill/laravel-best-practices`（SKILL.md + 20 个 rules/） | https://github.com/laravel/boost | 3611 | 2026-09-10 | MIT | Eloquent / 查询性能 / 迁移 / 校验 / 路由 / 队列 / 缓存 / HTTP client / 错误 / 事件 / 邮件 / 调度 / 集合 / Blade / 配置 / 风格 / 架构 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 官方维护，20 个 rules 全是「做什么 + 为什么」的可执行规则，抽查 `retry_after`、`Cache::remember` falsy、`chunkById` 三条与官方文档一致。本 skill 主干 |
| 2 | laravel/boost `.ai/laravel/skill/testing-best-practices`（SKILL + 9 个 rules/） | https://github.com/laravel/boost | 3611 | 2026-09-10 | MIT | 测试价值判定 / 命名 / 断言 / 端点覆盖 / 工厂数据 / 隔离与确定性 / 安全 / 套件性能 / 评审清单 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 目前见过最完整的 Laravel 测试设计规范；`Event::fake()` 与工厂模型事件的顺序陷阱、`BCRYPT_ROUNDS=4`、并行三条件都是别处没有的 |
| 3 | laravel/boost `.ai/pennant/skill/pennant-development` | https://github.com/laravel/boost | 3611 | 2026-09-10 | MIT | Pennant 定义 / 检查 / Blade / 作用域 | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE（薄） | 官方但只是 API 示例，「常见陷阱」仅两条。作为骨架采纳，真正的失败模式（首次解析即落盘、purge、null 作用域）全部来自官方文档 |
| 4 | laravel/boost `.ai/livewire/4/skill/livewire-development` | https://github.com/laravel/boost | 3611 | 2026-09-10 | MIT | Livewire 4 组件形态 / v3→v4 变更 / 指令 / 测试 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | v4 的 SFC/MFC/class 三形态、⚡ 前缀可配置、`wire:model` 不再冒泡子事件等，全是版本迁移期的高价值差异 |
| 5 | laravel/boost `.ai/php/*`、`.ai/pest`、`.ai/phpunit`、`.ai/pint`、`.ai/laravel/core.blade.php`、`.ai/laravel/12/core.blade.php`、`.ai/foundation.blade.php`、`.ai/enforce-tests.blade.php` | https://github.com/laravel/boost | 3611 | 2026-09-10 | MIT | 现代 PHP 约定 / 8.4 与 8.5 语法 / Pest 与 PHPUnit 运行方式 / Pint / Artisan `make:` / 骨架差异 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | `.blade.php` 是模板不是成品，需剥离 `$assist->` helper 与 `@scoped`；剥离后是官方口径的 PHP/工具链约定 |
| 6 | laravel/boost `.ai/volt/skill/volt-development`、`.ai/folio/skill/folio-routing` | https://github.com/laravel/boost | 3611 | 2026-09-10 | MIT | Volt 单文件组件 / Folio 文件路由 | 3 | 3 | 2 | 3 | 2 | 13 | 部分 INCLUDE | Volt 的「先看项目用函数式还是类式」并入 `blade-and-livewire.md`；Folio 是可选包且与本 skill 的路由章节重复，本轮不写入正文，留待后续同步重估 |
| 7 | laravel/boost `.ai/deployments/skill/deploying-to-cloud` | https://github.com/laravel/boost | 3611 | 2026-09-10 | MIT | Laravel Cloud 部署清单 | 3 | 3 | 2 | 3 | 2 | 13 | **排除（越界）** | 内容质量没问题，但属于托管控制面。用户拍板的边界把 Laravel Cloud/Forge 明确排除在本 skill 之外，正文只写「Not covered」 |
| 8 | laravel/boost `.ai/fluxui-free`、`.ai/fluxui-pro`、`.ai/tailwindcss/*` | https://github.com/laravel/boost | 3611 | 2026-09-10 | MIT | 商业 UI 套件 / Tailwind | 3 | 3 | 2 | 3 | 2 | 13 | **排除（越界）** | Flux 是商业组件库说明书；Tailwind 与视觉样式归 `frontend-design`，不进框架 skill |
| 9 | laravel/agent-skills `laravel/skills/starter-kit-upgrade`（+ 8 个 bash 脚本） | https://github.com/laravel/agent-skills | 716 | 2026-09-09 | NONE（API `license: null`） | starter kit 特性回合并的安全流程 | 3 | 3 | 3 | 3 | 0 | 12 | INCLUDE（窄） | 只取其「安全契约」：工作树必须干净且不代为 stash、专用分支、每特性一次提交、不自动合并被定制的文件与 lockfile、以「改动前通过的检查改动后仍通过」为验收。脚本本身绑定 starter kit，不搬 |
| 10 | laravel/agent-skills `laravel-cloud/skills/deploying-to-cloud`、`laravel-nightwatch/skills/configure-nightwatch` | https://github.com/laravel/agent-skills | 716 | 2026-09-09 | NONE | Laravel Cloud 部署 / Nightwatch 监控接入 | 3 | 3 | 2 | 3 | 0 | 11 | **排除（产品包装）** | 两者都是「教 agent 怎么配置我们家的付费 SaaS」——Cloud 是托管平台、Nightwatch 是监控产品，其内容随产品面板变化而非随框架变化，且与本 skill 的边界（不覆盖托管）直接冲突。同理排除 `laravel-lsp`（只有 plugin.json，无 skill） |
| 11 | laravel.com/docs（源仓库 laravel/docs，13.x 分支） | https://laravel.com/docs/13.x | 3485 | 2026-09-08 | MIT | 全框架 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE | 许可实查：`laravel/docs` 的 `license.md` 与仓库 LICENSE 均为 MIT（Taylor Otwell），API `spdx_id` 也是 MIT → 可 `merged` 而非 `reference`。版本敏感事实的唯一权威 |
| 12 | laravel/framework 源码（13.x） | https://github.com/laravel/framework | 34904 | 2026-09-10 | MIT | 队列属性解析实现 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE（窄） | 只读三处：`Queue::createPayloadArray`/`getJobBackoff`、`Queue/Attributes/*`、`Support/Traits/ReadsClassAttributes`。用来定「属性 vs 属性字段」的优先级，见裁决 1 |
| 13 | laravel/pennant `resources/boost/skills/pennant-development` | https://github.com/laravel/pennant | 593 | 2026-08-13 | MIT | Pennant | 3 | 3 | 1 | 3 | 2 | 12 | 合并同源 | 与候选 3 是同一份内容的两个发布位置（boost 从各包收集 skill）。按一个上游计，`SOURCES.yaml` 只登记 boost 侧路径，避免重复署名 |
| 14 | leeovery/agentic-skills `laravel/skills/*`（12 个 skill：actions、architecture、controllers、dtos、enums、exceptions、jobs、models、multi-tenancy、packages、query-builders、…） | https://github.com/leeovery/agentic-skills | 14 | 2026-06-11 | MIT | 分层架构：action / DTO / 自定义 query builder / 多租户 | 1 | 2 | 3 | 2 | 2 | 10 | INCLUDE（窄） | 唯一一份成体系的社区「Laravel 架构观」。取 `#[UseEloquentBuilder]` 自定义 builder 与「job 只是 action 的薄委托」；其「不要用 local scope」与「模型不得有任何行为」的强主张被官方否决（裁决 2） |
| 15 | leeovery/claude-laravel | https://github.com/leeovery/claude-laravel | 43 | 2026-03-26 | MIT | — | 1 | 1 | 0 | – | 2 | 4 | REJECT | 仓库只剩 `LICENSE` + `README`，README 写明「已迁移到 leeovery/agentic-skills」。星数最高但已是空壳，按候选 14 处理 |
| 16 | johnlui/laravel-skills `.agents/skills/laravel-ai-coding-safety` | https://github.com/johnlui/laravel-skills | 4 | 2026-04-13 | MIT | 破坏性 Artisan 命令护栏 | 1 | 1 | 3 | 3 | 2 | 10 | INCLUDE（窄） | 仓库整体是小众任务集（飞书告警、schema 同步），但这一条抓住了 agent 在 Laravel 项目里最贵的事故：`migrate:fresh` / `db:seed` 打到真库。取规则，不取其 `ALLOW_DB_DESTRUCTIVE_COMMANDS` 包装方案 |
| 17 | johnlui/laravel-skills 其余 5 个 skill（exception-feishu-notify、new-project-init、scheduler-timing-metrics、sync-database-schema、unified-api-response） | https://github.com/johnlui/laravel-skills | 4 | 2026-04-13 | MIT | 特定实现蓝图 | 1 | 1 | 2 | 2 | 2 | 8 | 排除（越界） | 都是「把某个具体方案抄进项目」的蓝图（飞书 webhook、统一响应基类），属于团队约定而非框架事实 |
| 18 | AsyrafHussin/agent-skills `skills/laravel-best-practices` | https://github.com/AsyrafHussin/agent-skills | 75 | 2026-08-27 | MIT | Laravel 13 规则索引（7 类 31 条） | 1 | 3 | 1 | 2 | 2 | 9 | MAYBE → reference | 索引里 Performance 与 API Design 两类写着「No rule files exist yet」，实际规则不足；覆盖到的部分官方讲得更准。仅用于交叉核对 13 的话题面（queue routing、vector search） |
| 19 | github/awesome-copilot `agents/laravel-expert-agent.agent.md` | https://github.com/github/awesome-copilot | 38871 | 2026-09-10 | MIT | Laravel 12+ 全面「人设」 | 2 | 3 | 0 | 2 | 2 | 9 | MAYBE → reference | 是 persona 文件（"You are a world-class Laravel expert…" + 能力清单），没有一条可验证规则，且带 `model` / `tools` 等 agent 专属 frontmatter。只用来对话题面 |
| 20 | github/awesome-copilot `instructions/php-symfony.instructions.md` | https://github.com/github/awesome-copilot | 38871 | 2026-09-10 | MIT | Symfony 约定 | 2 | 3 | 2 | 3 | 2 | 12 | REJECT（不相关） | 计划里指定它做「PHP 语言层交叉校验」，实读后 95% 是 Symfony 专属（bundle、Twig、services.yaml），PHP 层只有「构造器注入、避免容器 get()」这类与 boost 重复的通用条目。不采纳任何内容 |
| 21 | PauloFelipeM/agent-laravel-skills（SKILL.md + 40 条 rules） | https://github.com/PauloFelipeM/agent-laravel-skills | 12 | 2026-04-04 | NONE（frontmatter 自称 MIT） | 「Laravel 最佳实践」40 条 | 1 | 1 | 2 | 1 | 0 | 5 | REJECT | 规则命名暴露来源不对：`api-use-interceptors`、`api-use-pipes`、`arch-feature-modules`、`micro-use-health-checks`、`devops-use-config-module` 是 NestJS 词汇被套到 Laravel 上；N+1 那条本身写得不错但不值得为它承担整包的错配风险 |
| 22 | clawvpsai/laravel-skill | https://github.com/clawvpsai/laravel-skill | 2 | 2026-07-18 | NONE | 未知 | 0 | 2 | – | – | 0 | ≤4 | REJECT | 2 星、无许可、无社区采纳信号；与官方 skill 完全重叠，没有引入价值 |
| 23 | CarianLabs/LaravelAgentSkills / mikeu-dev/laravel-skill / jasim-k、shshohagh、abdallhMoukdad 等 `laravel-agent-skills` 同名仓 | 见 `gh search repos "laravel agent skills"` | 0–2 | 2026-03~05 | NONE | 个人试验 | 0 | 1 | – | – | 0 | ≤4 | REJECT | 均为 0–2 星、无许可的个人仓库，多数是 boost 的复制或空壳 |
| 24 | 业务仓库里的 `*/skills/laravel-best-practices/SKILL.md`（cachethq/core、CodeWithDennis/larament、nunomaduro/laravel-starter-kit-inertia-vue、thinktomorrow/chief 等 20+ 个命中） | `gh search code` 结果 | – | – | – | — | – | – | – | – | – | – | 非候选 | 逐个比对确认是 `php artisan boost:install` 把候选 1 复制进各自仓库的产物，不是独立作品。它们的存在反而佐证候选 1 是事实标准 |
| 25 | livewire/livewire `.claude/skills/*`、pestphp/pest `.hod/skills/*` | https://github.com/livewire/livewire · https://github.com/pestphp/pest | 23575 · 11714 | 2026-09-10 · 2026-09-09 | MIT | review-pr / summarize-activity / test / snapshots-update | 3 | 3 | 2 | 3 | 2 | 13 | 排除（对象不对） | 官方且活跃，但服务的是「维护 Livewire/Pest 这个库本身」的贡献者流程（跑仓库测试、总结活动），不是「用 Livewire/Pest 写业务代码」 |
| 26 | wshobson/agents `plugins/web-scripting/agents/php-pro.md` | https://github.com/wshobson/agents | 39558 | 2026-09-07 | MIT | PHP 通用 agent | 2 | 3 | 1 | 2 | 2 | 10 | 排除（无 Laravel 内容） | 该仓库无任何 Laravel skill，仅有一个 PHP persona agent；与候选 19 同类问题 |
| 27 | php/php-src `UPGRADING`（8.4 / 8.5 tag） | https://github.com/php/php-src | 40369 | 2026-09-10 | BSD-3-Clause | PHP 版本特性归属 | 3 | 3 | 3 | 3 | 2 | **14** | INCLUDE（校验用） | 用来确认 `modern-php.md` 里每条语法写对了版本（8.5 才有管道运算符、`array_first/last`、clone-with；8.4 才有 `array_find` 家族）。许可实读：LICENSE 已是三条款 BSD，与 API 的 `spdx_id` 一致 |

## 深度审查

**1. laravel/boost `laravel-best-practices`（候选 1）** — `SKILL.md` 本体只有 82 行，是一张
「关注点 → 规则文件」的索引表，真正的内容在 20 个 `rules/*.md` 里，每个 3–6 KB。frontmatter 干净
（`name` / `description` / `license` / `metadata.author`），没有 agent 专属字段。写法是「反例代码 →
正例代码 → 为什么」，几乎每条都带一句限定（"Use `chunkById()` when updates can change which rows
match the query"），这正是标准第 3 节要的「teach the failure」。开篇的 **Consistency First**
（先看项目已有做法，不一致比不最优更糟）值得整条继承——它是所有框架 skill 最容易漏的第一原则。
弱点：完全不谈版本差异，因为 boost 运行时会按 `composer.lock` 拼装上下文，而独立 skill 没有这个
能力，所以 Laravel 13 的属性化 API 必须由官方文档补上。

**2. laravel/boost `testing-best-practices`（候选 2）** — 9 个 rules 是 `.blade.php` 模板，用
`$pest = $assist->hasPackage('pestphp/pest')` 在 Pest / PHPUnit 两套写法间分支。合入时按「骨架
安装 Pest」定为 Pest 主线并注明每条都有 PHPUnit 对应写法。内容强度高于候选 1：
`rules/isolation.blade.php` 的「先建工厂记录再 `Event::fake()`，否则 `creating` 钩子被吞掉、模型
非法」是真实事故；`rules/review.blade.php` 是可直接照抄的评审清单；`rules/performance.blade.php`
的 `BCRYPT_ROUNDS=4`、并行三条件、`--tia` 都能立刻省时间。与 `test-driven-development` skill 的
分界很清楚：那边管「该不该写这个测试」，这边管「Laravel 里这个测试怎么写才不假绿」。

**3. laravel.com/docs 13.x（候选 11）** — 决定本 skill 版本正确性的上游。`releases.md` 给出
支持矩阵（13 于 2026-03-17 发布，PHP 8.3–8.5；12 的 bug fix 到 2026-08-13、安全到
2027-02-24），`upgrade.md` 给出完整破坏性变更表，`queues.md` / `eloquent.md` / `pennant.md` /
`container.md` / `controllers.md` / `octane.md` 给出所有属性化 API 与陷阱。许可实查后可 merged，
这一步很关键——若按印象当成 `reference`，版本表和破坏性变更表就都不能写进正文。

**4. laravel/agent-skills `starter-kit-upgrade`（候选 9）** — 质量与官方 skill 同级，但主题很窄
（把 starter kit 的某个特性回合并到已定制的项目）。真正可迁移的是它开头的 **Safety contract**：
七条不可协商的前置条件。这套契约对「升级 Laravel 大版本」同样成立，因此抽象后写进
`upgrade-a-laravel-application` workflow 与 `runtime-config-and-upgrades.md` 末节。仓库无 LICENSE
文件（API `license: null`），按无许可规则处理：`license: NONE` + notes，不逐字复制。

**5. leeovery/agentic-skills（候选 14）** — 12 个 skill，观点鲜明：一切业务逻辑进 action，模型只留
关系/cast/简单判定，用自定义 query builder 替代 local scope，DTO 用 spatie/laravel-data。前两条
与 boost 的「不要投机抽象」和官方的 `#[Scope]` 直接冲突（见裁决 2）。有价值的是它对
Laravel 13 属性化的敏感度（`#[UseEloquentBuilder]`、`#[Table]`、`#[ObservedBy]`、`#[UsePolicy]`）
和「job 是 action 的薄委托」——后者恰好解释了为什么 `failed()` 里不该有业务状态。

**6. AsyrafHussin/agent-skills（候选 18）与 awesome-copilot 的两个文件（候选 19、20）** —
三者都是「看起来该收、实读后不该收」。18 的索引承诺 7 类规则、实际两类空文件；19 是人设不是规则；
20 是 Symfony。这三行留在表里，避免下一批再花时间重新评估。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 队列的 tries / backoff / timeout / uniqueFor 怎么声明 | boost `rules/queue-jobs.md`：`public $tries = 4; public $backoff = [1,5,10]; public $uniqueFor = 3600;` ／ laravel/docs 13.x `queues.md`：只给 `#[Tries(5)]`、`#[Backoff(3)]`、`#[Timeout(120)]`、`#[UniqueFor(3600)]`、`#[FailOnTimeout]`、`#[DeleteWhenMissingModels]`，属性写法已从文档中消失 | Laravel 13 上写属性；同时明确旧属性字段仍然有效，**且当两者都存在时属性字段胜出**，所以一个设置只能选一种写法 | 官方文档 > 官方 skill（更新 > 更旧）；「两者都有效、属性字段优先」不是文档写的，而是实读 `laravel/framework` 13.x 的 `Queue::getJobBackoff()` → `getAttributeValue()` → `Support/Traits/ReadsClassAttributes` 得到：先看运行时属性值是否偏离声明默认值，是则用属性字段，否则读 attribute |
| 2 | local scope 还是自定义 query builder | boost `rules/eloquent.md`：用 `#[Scope]` local scope 复用查询约束，global scope 谨慎 ／ leeovery `laravel-models`：「用自定义 query builder，**不要** local scope」，且「模型不得含业务逻辑」 | 默认 local scope（`#[Scope]`）；自定义 builder（`#[UseEloquentBuilder]`）作为「模型查询方法过多」时的逃生口。模型「不得含任何行为」不采纳，简单判定方法留在模型上是官方与 boost 的共同写法 | 官方厂商 > 社区。`eloquent.md` 与官方 `eloquent.md` 文档都把 `#[Scope]` 作为一等做法；leeovery 是个人架构偏好（14 星），正文只写裁决后的一种默认 |
| 3 | 子模型访问父模型造成的 N+1 怎么修 | boost `rules/advanced-queries.md`：`$feature->comments->each->setRelation('feature', $feature)` ／ laravel/docs `eloquent-relationships.md`：在关系定义上加 `chaperone()`，Eloquent 自动把父模型挂到子模型 | 默认 `chaperone()`（定义处一次性解决，新调用点自动受益）；`setRelation()` 作为「模型已经加载好、不便改定义」时的现场手段 | 官方文档给的是框架内建能力，boost 给的是手工等价物；更新 > 更旧 |
| 4 | 防 N+1 用「禁止懒加载」还是「自动贪婪加载」 | boost `rules/db-performance.md`：`Model::preventLazyLoading(! app()->isProduction())` ／ laravel/docs `eloquent-relationships.md`：`Model::automaticallyEagerLoadRelationships()` 自动为整个集合补加载 | 默认 `preventLazyLoading`（让问题在开发期炸出来）；自动贪婪加载作为「访问模式确实动态」时的替代**策略**，二者互斥，不得同时开——违规异常会先于自动加载触发 | 两者都是官方，属于策略选择而非新旧之分。按标准「只给一个默认方案 + 一个逃生口」裁决，并在正文写明互斥理由 |
| 5 | Laravel 12 还是 13 作为写作基准 | 计划表写「覆盖 Laravel 12+」 ／ `gh api repos/laravel/framework/releases` 显示当前是 v13.31.0，`laravel/laravel` 骨架 `require` 为 `laravel/framework: ^13.17` + `php: ^8.3` | 以 **13** 为基准写，凡在 12 上同样成立的规则不加版本标注，13 专属 API 显式标注；`## Scope` 写明两者与 PHP 区间，并要求先 `composer show --direct` 再套用版本敏感规则 | 「更新 > 更旧」，且 12 仍在 bug fix 支持期（至 2026-08-13 已结束，安全支持到 2027-02-24），大量存量项目仍在 12，不能只写 13 |
| 6 | Livewire 版本 | boost 同时提供 `.ai/livewire/2`、`/3`、`/4` 三份 | 只写 4，并单列一节「v3 → v4 的实际变更」供读存量代码用 | boost 按 `composer.lock` 选版本，独立 skill 无此能力；写当前版本 + 迁移差异是标准第 3 节「弃用内容不进主线」的做法 |
| 7 | 测试框架 | boost 按 `pestphp/pest` 是否安装在 Pest 与 PHPUnit 间分支 | 正文用 Pest（Laravel 13 骨架的默认，`pestphp/pest ^4.0`），并在 reference 顶部声明每条规则都有 PHPUnit 对应写法 | 官方骨架默认 > 二选一并列；标准第 3 节禁止罗列多个可选方案 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `laravel-boost` | laravel/boost（`.ai/laravel/skill/*`、`.ai/pennant`、`.ai/livewire/4`、`.ai/volt`、`.ai/php`、`.ai/pest`、`.ai/phpunit`、`.ai/pint`、`.ai/laravel/core*`、`.ai/foundation`、`.ai/enforce-tests`） | merged | 八个 reference 的骨架：一致性优先、Eloquent 加载与严格模式、子查询与条件聚合、chunk/cursor/lazy 选型、迁移分阶段与索引纪律、批量赋值与 `validated()`、表单请求 `after()`、资源控制器组织、`retry_after` 与 timeout、backoff、唯一任务、批次、`failed()` 是新实例、事件/通知/邮件的 after-commit、调度锁语义、缓存原语选型、异常 report/render 优先级、整套 Pest 测试设计与评审清单、Livewire 4 形态与指令、Volt、Pennant 基础、PHP 风格与 Pint |
| `laravel-docs` | laravel.com/docs 13.x（源 laravel/docs，MIT 实查） | merged | 所有版本敏感事实与官方 skill 缺失项：13 的支持矩阵与 PHP 区间、完整 12→13 破坏性变更表、队列属性与 `Queue::route`、`ShouldBeUniqueUntilProcessing`、`DeleteWhenMissingModels`、`#[Scope]`/`#[Table]`/`#[ObservedBy]`、`chaperone()` 与 `automaticallyEagerLoadRelationships`、控制器 `#[Middleware]`/`#[Authorize]`、容器上下文属性、`PreventRequestForgery` 与 `Sec-Fetch-Site`、`denyAsNotFound`、Pennant 存储语义/purge/null 作用域/富值/eager load、`Cache::touch` 与 failover、`Concurrency::run`、Octane 的容器与请求注入陷阱 |
| `laravel-framework` | laravel/framework 13.x（`Queue/Queue.php`、`Queue/Attributes`、`Support/Traits/ReadsClassAttributes.php`） | merged | 裁决 1 的实现事实：属性与旧属性字段的优先级，文档未述 |
| `laravel-agent-skills` | laravel/agent-skills `laravel/skills/starter-kit-upgrade`（NONE） | merged | 升级安全契约（干净工作树 / 专用分支 / 每步可回滚 / 不自动合并定制文件与 lockfile / 以既有检查为验收） |
| `johnlui-laravel-skills` | johnlui/laravel-skills `.agents/skills/laravel-ai-coding-safety`（MIT） | merged | 破坏性 Artisan 命令护栏（core rule 4） |
| `leeovery-agentic-skills` | leeovery/agentic-skills `laravel/skills`（MIT） | merged | `#[UseEloquentBuilder]` 自定义 builder 作为 scope 的逃生口；job 作为 action 的薄委托 |
| `asyrafhussin-agent-skills` | AsyrafHussin/agent-skills `skills/laravel-best-practices`（MIT） | reference | 仅交叉核对 Laravel 13 话题面 |
| `awesome-copilot-laravel` | github/awesome-copilot（`agents/laravel-expert-agent.agent.md`、`instructions/php-symfony.instructions.md`，MIT） | reference | 仅核对话题广度与 PHP 层约定，未合入内容 |
| `php-src` | php/php-src `UPGRADING`（BSD-3-Clause 实读） | reference | 仅核验 PHP 8.4/8.5 语法的版本归属与当前稳定线 |

## 基线缺口

无 skill（`uv run tools/run_evals.py laravel --baseline`，claude-opus-5 · medium）时，各场景未达成的
`expected_behavior`：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 Eloquent / 安全 | 未点名自动贪婪加载（`Model::automaticallyEagerLoadRelationships()` / `withRelationshipAutoloading()`）是另一条互斥策略 | 基线答出了 `preventLazyLoading`，但没有把两条策略摆在一起并说明不可混用 |
| 1 Eloquent / 安全 | 未把 casts 迁到 `casts()` 方法 | 基线只在既有 `$casts` 属性里补了 `published_at`；Laravel 12+ 的做法是 `casts()` 方法 |
| 2 队列 | 未解释 `failed()` 为什么读不到 `$attemptLog` | 基线把 `count($this->attemptLog)` 换成了 `$this->attempts()`（结果对），但没说原因是 `failed()` 运行在反序列化出来的新实例上——不解释就无法迁移到下一个类似 bug |
| 2 队列 | 完全没有提到 `ShouldBeUnique` / `uniqueId()` 的派发去重 | 只讲了幂等键；派发层去重与执行幂等是两件事 |
| 2 队列 | 没有提到 Laravel 13 的 `#[Tries]` / `#[Backoff]` / `#[Timeout]` 属性写法 | 基线沿用 `public $tries`，也没有指出「属性与属性字段不要同时声明」 |
| 2 队列 | HTTP 调用只补了 `->throw()`，未提 `connectTimeout` / `timeout` | 30 秒默认响应超时叠加重试会把 job 拖到 timeout |
| 2 队列 | 未逐项点出事件与队列通知同样受事务时序影响 | 基线在连接上开了 `after_commit`（间接覆盖），但没说明 `event()` 与 `notify()` 也在这条路径上 |
| 3 测试 / Pennant | 未指出「改了 odds 也不影响已解析的用户，灰度变更必须 `pennant:purge`」 | 基线明确写了「`AppServiceProvider.php` 未动」，把 sticky 行为当作正常灰度语义就收尾了——这正是线上「改了没生效」的成因 |
| 3 测试 / Pennant | 未把工厂记录移出 `beforeEach()` | 基线保留了 `beforeEach` 里建记录 |
| 3 测试 / Pennant | 删掉了 `Carbon::setTestNow()` 但未给出 `freezeTime()` / `travelTo()` 替代 | 只做减法，没给正确做法 |
| 3 测试 / Pennant | 未提 `Http::preventStrayRequests()`，仍保留裸 `Http::fake()` | 基线明确写「保留 `Http::fake()` 作出网阻断」，而裸 fake 会静默接受任何未预期请求 |
| 3 测试 / Pennant | 未提 `Event::fake()` 需传类名、以及工厂记录要先于 fake 创建 | 基线选择直接删掉 `Event::fake()` |
| 3 测试 / Pennant | 未用具名响应断言，也未指出跨租户宜用 404 而非 403 | 第三个测试的 `assertStatus(403)` 原样保留 |
| 3 测试 / Pennant | 未提 `LazilyRefreshDatabase` 与 `BCRYPT_ROUNDS` 等套件卫生 | 套件级设置完全未涉及 |
| 4 负例（Spring） | —（负例无需缺口） | 基线给出正确的 Spring 自调用/代理解释，`skill_read == false`，符合预期 |

基线在场景 1 表现很强（N+1、`withCount`、SQL 注入与标识符白名单、`$guarded = []`、`chunkById`、
scope 里读 `auth()` 的空指针都答出来了），场景 2 中等，场景 3 差距最大——这与预期一致：
越是「框架特定的沉默失败」（Pennant 落盘语义、fake 的默认宽松、`failed()` 的新实例）基线越容易漏。

## 评测结果

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Eloquent/安全 | claude-opus-5:medium | 无（baseline） | false | 5/7：贪婪加载 + `withCount`、`$guarded=[]` 与 `validated()`、`search()` 两处注入与标识符白名单、scope 里 `auth()` 的空指针、`export()` 的 1+N | 未达成：未点名 `automaticallyEagerLoadRelationships()` 是互斥的另一策略；casts 仍写在 `$casts` 属性里而非 `casts()` 方法 |
| 2 队列 | claude-opus-5:medium | 无（baseline） | false | 2/7：`retry_after` > timeout；幂等键/短路 | 未达成：`failed()` 为何读不到 `$attemptLog`（只改对了写法未解释）、`ShouldBeUnique` 派发去重、Laravel 13 属性写法；`->throw()` 提到但未提两个超时；`after_commit` 开在连接上但未点名 `event()`/`notify()` 同受影响 |
| 3 测试/Pennant | claude-opus-5:medium | 无（baseline） | false | 2/8：lottery 是 flaky 根因并改为显式置位；把 `it('works')` 改成真实断言 | 未达成：purge（明确写「provider 未动」把 sticky 当正常语义）、工厂记录移出 `beforeEach`、`freezeTime()` 替代、`Http::preventStrayRequests()`（明确保留裸 `Http::fake()`）、具名断言与跨租户 404、`LazilyRefreshDatabase`/`BCRYPT_ROUNDS` |
| 4（负例） | claude-opus-5:medium | 无（baseline） | false | 3/3：Spring 代理自调用解释 + 拆 bean/自注入/AspectJ 方案；无 Laravel 内容 | 符合预期 |
| 1 Eloquent/安全 | claude-opus-5:medium | 有 | **true** | **7/7**：基线那 5 条全部保留，另外补上「别同时开 `automaticallyEagerLoadRelationships()`，那是相反策略」与 `casts()` 方法形式；额外自发给出 `chaperone()` 与 Policy 拒绝宜 404 | 两条基线缺口被填补 |
| 2 队列 | claude-opus-5:medium | 有 | **true** | 5/7：`retry_after`、幂等（短路 + `Idempotency-Key`）、`afterCommit()` 且点名 `event()` 与 `ShouldDispatchAfterCommit`（队列通知未单独点名）、**`failed()` 运行在重新反序列化的新实例上**、**`connectTimeout()`/`timeout()`/`->throw()` 与「4xx/5xx 是普通响应」** | 三条基线缺口被填补。仍未达成：`ShouldBeUnique` 派发去重、Laravel 13 属性写法（两者都在 `queues-events-and-scheduling.md` 里，模型未读到那两段）。首轮跑时 `->throw()`/超时也未答出，因此在 core rules 补了第 24 条后重跑本场景，该条随即达成 |
| 3 测试/Pennant | claude-opus-5:medium | 有 | **true** | 6.5/8：lottery 根因 + 测试内重定义 flag、**「改 odds 不影响已解析用户，扩量必须 `pennant:purge`」**、真实断言取代恒真式、**工厂记录移出 `beforeEach`**、**`freezeTime()`**、**`Http::preventStrayRequests()`**、**`assertOk()`/`assertForbidden()` 与跨租户宜 404**；另外自发指出 `fn (User $user)` 不可空导致队列/命令里静默为 off | 五条基线缺口被填补。裸 `Event::fake()` 只答到「吞掉真实监听器」一半，未提工厂模型事件顺序（计 0.5）；`LazilyRefreshDatabase`/`BCRYPT_ROUNDS` 未达成 |
| 4（负例） | claude-opus-5:medium | 有 | **false** | 3/3：仍是 Spring 答案（拆 `InvoiceSettlementService` + `REQUIRES_NEW` + 逐张 try/catch），未加载 `laravel` skill，未出现任何 Laravel/Eloquent 内容 | 负例通过 |

结论：**通过**。基线未达成而有 skill 时达成的行为共 10 条，分布在三个正例场景：
场景 1 的「两条防 N+1 策略互斥」与 `casts()` 方法；场景 2 的 `failed()` 新实例语义、
事件同受事务时序影响、HTTP 客户端超时与 `->throw()`；场景 3 的 `pennant:purge`、
`beforeEach` 只放配置、`freezeTime()`、`preventStrayRequests()`、具名断言与跨租户 404。
负例 `skill_read == false` 且答案里没有任何 Laravel 内容，符合要求。

## 备注

### 版本核实（不凭记忆）

- `gh api repos/laravel/framework/releases` → 最新 `v13.31.0`（2026-09-08），13.x 与 12.x 并行发版
  （`v12.69.2` 同日）。**当前主版本是 13，不是计划表写的 12**，正文据此以 13 为基准。
- `gh api repos/laravel/laravel/contents/composer.json` → 骨架 `require`：`php: ^8.3`、
  `laravel/framework: ^13.17`、`laravel/tinker: ^3.0`；`require-dev` 含 `phpunit/phpunit: ^12.5.12`、
  `laravel/pint: ^1.27`。
- `laravel/docs` 13.x `releases.md` 支持矩阵：13 于 2026-03-17 发布，PHP 8.3–8.5，bug fix 至 2027 Q3、
  安全至 2028-03-17；12 于 2025-02-24 发布，PHP 8.2–8.5，bug fix 至 2026-08-13、安全至 2027-02-24。
- `gh api repos/php/php-src/releases` → 当前稳定 `php-8.5.10`（2026-08-28），8.4 线为 `php-8.4.25`。
  `modern-php.md` 的版本门限据此标注。

### 许可注意

- `laravel/docs` 实查为 MIT（仓库 LICENSE 与 `license.md` 都是 Taylor Otwell 的 MIT 全文），因此
  `kind: docs` 也能 `merged`。这是本 skill 能写出完整 12→13 破坏性变更表的前提。
- `laravel/agent-skills` API `license: null`，仓库内无 LICENSE 文件 → `license: NONE` +
  `notes: "No licence file; used under the repository's permissive-attribution policy, no text copied verbatim"`。
- `php/php-src` API 报 `BSD-3-Clause`；实读 LICENSE 确认确实已是三条款 BSD（不再是 PHP-3.01 措辞），
  与 API 一致，按 reference 登记。
- 无 GPL / LGPL / AGPL / 专有上游，因此没有 `reference` 是被许可强制的；三个 `reference`
  （AsyrafHussin、awesome-copilot、php-src）都是「读过但未合入内容」。

### 产品包装目录被排除的理由

`laravel/agent-skills` 的 `laravel-cloud/*` 与 `laravel-nightwatch/*`、以及 `laravel/boost` 的
`.ai/deployments`（Laravel Cloud 部署）、`.ai/fluxui-free`、`.ai/fluxui-pro` 全部排除。它们由官方维护、
质量也够，但教的是「怎么配置我们家的托管平台 / 监控 SaaS / 商业 UI 套件」：内容随产品面板演进而非随
框架演进，同步周期与框架不同；并且用户拍板的边界已把 Laravel Cloud/Forge 托管排除在本 skill 之外。
`.ai/tailwindcss/*` 属于视觉样式，归 `frontend-design`。

### Phase D 的一次回改

首轮「有 skill」评测里场景 2 反而没答出 HTTP 客户端的两个超时与 `->throw()`（基线答出了
`->throw()`）。原因是这条事实只写在 `references/http-and-validation.md` 的末节，而模型在队列诊断
任务里只读了 `queues-events-and-scheduling.md`。据此在 `SKILL.md` 的 core rules 补了第 24 条
（出站 `Http::` 必须设 `connectTimeout()`/`timeout()` 且 `->throw()` 或查状态码，因为客户端默认
30 秒响应超时、4xx/5xx 是普通响应），随后 `uv run tools/run_evals.py laravel --only 2` 重跑，
该条即达成。评测结果表里场景 2 的一行是重跑后的结果。

### 未来同步时要盯的

- `laravel/boost` 的 `.ai/laravel/13/core.blade.php`：目前只有 `11/` 与 `12/`，13 专属 core 文件一旦
  出现，说明官方对 13 的骨架差异有了正式口径，应立即并入。
- `.ai/folio/skill/folio-routing`（候选 6）本轮未写进正文；若后续 Laravel 骨架把 Folio 变成默认，
  应在 `http-and-validation.md` 加一节。
- Livewire 4 仍在快速迭代，`.ai/livewire/4/skill/livewire-development` 与
  `reference/javascript-hooks.md` 值得每次同步都读一遍 diff。
- `AsyrafHussin/agent-skills` 的 Performance / API Design 两类规则文件若补齐，可从 reference 升为
  merged 候选重估。
