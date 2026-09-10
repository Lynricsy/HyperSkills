# java-spring 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `web_search`：`"Spring Boot agent skill SKILL.md github claude 2026"`
  - GitHub 搜索：`search/repositories?q=spring boot agent skills SKILL.md`、
    `q=spring-boot claude skills`；`search/code?q="spring-boot" filename:SKILL.md path:skills`
  - <https://www.skills.sh>（经 `web_search` 的 `site:` 检索间接覆盖）
  - VoltAgent/awesome-claude-code-subagents、wshobson/agents（均无 Java/Spring 目录，已核）
  - `github/awesome-copilot`：`skills/` 与 `instructions/` 两侧都搜过
  - 领域官方组织：`spring-projects/`、`spring-io/`、`spring-ai-community/`
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
- `gh auth status`：已登录（账号 Lynricsy，scopes `gist, read:org, repo, workflow`），全程无限流。

**路线图更正**：旧 `docs/roadmap.md` 记「java-spring 尚未找到合格上游」，已过时。本次核到 4 个
总分 ≥11 的可合入上游（rrezartprebreza、github/awesome-copilot、a-pavithraa、spring-ai-community）
外加官方文档，远超立项判据。

**官方上游确认不存在**：`spring-projects/spring-boot#50893`（"Dedicated Spring Boot Claude Skills"，
2026-06-30 开）已被 **Closed as not planned**，Spring 官方目前不维护 agent skill 仓库。因此本 skill
不适用「官方厂商特例」，走常规判据（≥3 个活跃、总分 ≥8 的上游），并以 `docs.spring.io` +
spring-boot wiki 作为事实裁决基准。

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | rrezartprebreza/spring-boot-skills `skills/spring-boot-4/*`（33 个目录） | https://github.com/rrezartprebreza/spring-boot-skills | 261 | 2026-09-07 | MIT | Boot 4 全栈：JPA、事务、安全、测试、Modulith、可观测、迁移、打包 | 2 | 3 | 3 | 3 | 2 | 13 | INCLUDE | 主干。每个 skill 都以「Agent 会犯的错」收尾，正是标准要的 teach-the-failure；抽查 `@ImportHttpServices`、`org.springframework.resilience` 重试、Boot 4 起步依赖改名三条，全部对得上官方 wiki |
| 2 | rrezartprebreza/spring-boot-skills `skills/spring-boot-3/*`（同名 33 个目录） | 同上 | 261 | 2026-09-07 | MIT | Boot 3.5 版本的同一批主题 | 2 | 3 | 3 | 2 | 2 | 12 | MAYBE（不作正文来源） | 与 spring-boot-4 目录逐篇对照，只用来确认「哪些差异属于 3→4 破坏性变更」。本 skill 不按大版本分叉，正文取 GA（4.1），3.x 差异进 `references/boot-4-migration.md` |
| 3 | github/awesome-copilot `skills/spring-boot-testing` | https://github.com/github/awesome-copilot | 38860 | 2026-09-10 | MIT | 测试切片选型、MockMvcTester、RestTestClient、Testcontainers、上下文缓存 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | GitHub 官方仓；切片决策树 + 上下文缓存成本分析是本 skill 测试章的骨架 |
| 4 | github/awesome-copilot `instructions/springboot-4-migration` | 同上 | 38860 | 2026-09-10 | MIT | 3.x→4.0 迁移（48 KB，含起步依赖改名表、Jackson 3、包搬迁、属性改名） | 3 | 3 | 3 | 2 | 2 | 13 | INCLUDE | 覆盖面最全的迁移清单。扣 1 分：称「Spock 已移除」，而官方 4.1 Release Notes 有 "Restoration of Spock Support"，属版本滞后（见裁决 3） |
| 5 | github/awesome-copilot `instructions/java-17-to-java-21-upgrade` + `instructions/java-21-to-java-25-upgrade` | 同上 | 38860 | 2026-09-10 | MIT | JDK 18–25 语言特性、弃用、GC、preview 开关 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | 语言升级章的来源。具体性扣 1：偏 JEP 目录式罗列，落到 Spring 应用的取舍需自己补 |
| 6 | github/awesome-copilot `skills/java-add-graalvm-native-image-support` | 同上 | 38860 | 2026-09-10 | MIT | native image 接入、reachability metadata、构建错误迭代 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 打包章 native 部分的来源；Step 4「按构建错误反推 hints」这条流程别处没有 |
| 7 | github/awesome-copilot `instructions/springboot` | 同上 | 38860 | 2026-09-10 | MIT | 通用 Spring Boot 编码约定 | 3 | 3 | 1 | 1 | 2 | 10 | MAYBE（未进 `paths`） | 全是模型已知常识（构造器注入、SLF4J 参数化日志）；且把错误契约写成 RFC 7807，而 RFC 9457 已废止它。只用来交叉校验，未取内容 |
| 8 | github/awesome-copilot `skills/java-springboot` | 同上 | 38860 | 2026-09-10 | MIT | 同上，skill 形态 | 3 | 3 | 1 | 2 | 2 | 11 | MAYBE（未进 `paths`） | 与 #7 高度重复，无版本敏感信息，无 Boot 4 内容 |
| 9 | github/awesome-copilot `skills/java-junit`、`skills/create-spring-boot-{java,kotlin}-project` | 同上 | 38860 | 2026-09-10 | MIT | JUnit 5 通用写法 / start.spring.io 脚手架 | 3 | 3 | 1 | 3 | 2 | 12 | MAYBE（未进 `paths`） | JUnit 通用方法论属 `test-driven-development` 边界；脚手架步骤是一次性动作，不值 token |
| 10 | a-pavithraa/springboot-skills-marketplace `plugins/springboot-architecture/skills/*` | https://github.com/a-pavithraa/springboot-skills-marketplace | 75 | 2026-08-25 | MIT | JPA/CQRS、代码评审清单、Boot 4 迁移、Java 25 特性、JSpecify | 1 | 3 | 3 | 2 | 2 | 11 | INCLUDE | 「只给聚合根建 repository」「查询模式选型表」这两条别处没有；`references/java-25-features.md` 是语言章的第二来源。正确性扣 1：把 `Testcontainers 2` 的迁移写得比官方更激进 |
| 11 | spring-ai-community/spring-testing-skills `skills/*` | https://github.com/spring-ai-community/spring-testing-skills | 52 | 2026-04-24 | NOASSERTION → 实读为 Apache-2.0 | `@DataJpaTest`/`@WebMvcTest`/security/WebFlux 测试 | 2 | 1 | 3 | 3 | 2 | 11 | INCLUDE | `flush()`+`clear()` 否则读 L1 缓存假通过——这是本批评测里区分度最高的一条。API 报 NOASSERTION，实读 `LICENSE` 为完整 Apache License 2.0 正文 |
| 12 | adityamparikh/spring-boot-4-migration-skill | https://github.com/adityamparikh/spring-boot-4-migration-skill | 41 | 2026-07-31 | Apache-2.0 | 2.7→3.5→4 迁移，18 个 reference（Security 7、Framework 7、Kafka 4、AOT） | 1 | 2 | 3 | 3 | 2 | 11 | INCLUDE | Security 7 破坏性变更清单（`AuthorizationManager#check` 移除、`PathPatternRequestMatcher`、`SecurityJacksonModules`）比 #4 细，逐条对上 spring-security 源码 |
| 13 | Amplicode/spring-skills | https://github.com/Amplicode/spring-skills | 112 | 2026-09-06 | null → NONE | CRUD 控制器、DTO、格式化、覆盖率 | 2 | 3 | 2 | 2 | 0 | 9 | REJECT | 每个 skill 开头是 "Preflight: Spring MCP"，强制依赖 Amplicode IntelliJ 插件提供的专有 MCP server，且要求「只能照抄 examples/ 里的代码」。属产品包装 + agent 工具绑定，本仓库禁止 |
| 14 | piomin/claude-ai-spring-boot `.claude/skills/spring-boot` | https://github.com/piomin/claude-ai-spring-boot | 1289 | 2026-04-29 | Apache-2.0 | Boot 3.x 模板集（entity/service/controller/test） | 2 | 1 | 1 | 1 | 2 | 7 | MAYBE（未采用） | 星数最高但内容是模型已知的样板代码；且 `@MockBean`（Boot 4 已移除）、控制器直接返回实体、`GenerationType.IDENTITY` 无说明。以 Boot 4 为基线时会主动教错 |
| 15 | giuseppe-trisciuoglio/developer-kit `plugins/developer-kit-java/skills/spring-boot-*` | https://github.com/giuseppe-trisciuoglio/developer-kit | 343 | 2026-09-10 | MIT | Boot 3.5 CRUD/DI/缓存/actuator/resilience4j | 1 | 3 | 2 | 1 | 2 | 9 | MAYBE（未采用） | 基线是 Boot 3.5，与主干重叠且更弱；frontmatter 带 `allowed-tools`（本仓库禁止的 agent 专属字段）。其 AWS/LangChain4j 目录不在本 skill 边界内 |
| 16 | HoangNguyen0403/agent-skills-standard `skills/spring-boot/*` | https://github.com/HoangNguyen0403/agent-skills-standard | 565 | 2026-09-09 | MIT | Boot 3 最佳实践、架构、API 设计、数据访问、安全 | 1 | 3 | 2 | 1 | 2 | 9 | MAYBE（未采用） | 满篇 ALL-CAPS MUST/NEVER，标准第 3 节明令禁止；把 ProblemDetails 写成 RFC 7807；`metadata.triggers` 是 agent 专属字段 |
| 17 | majiayu000/claude-skill-registry `skills/**/spring-boot*`（约 25 个目录） | https://github.com/majiayu000/claude-skill-registry | 601 | 2026-09-10 | MIT | 聚合镜像 | 0 | 3 | 1 | 0 | 2 | 6 | REJECT | 同一个 `spring-boot` skill 在 `data/`、`design/`、`development/`、`testing/` 下重复出现多份且内容互相矛盾；无原创性，无法定位事实来源 |
| 18 | full-stack-skills/spring-skills | https://github.com/full-stack-skills/spring-skills | 2 | 2026-07-29 | NOASSERTION → 实读非许可 | Spring 通用 | 0 | 2 | 1 | 1 | 0 | 4 | REJECT | 仓库根 `LICENSE` 实读后是一份 "Third-Party Notices" 声明（BSD/imageio 等），并非本仓库自身许可 → 视同无许可；2 星，内容单薄 |
| 19 | ItQianChen/java-springboot-standards-skill | https://github.com/ItQianChen/java-springboot-standards-skill | 2 | 2026-09-02 | MIT | 单人 Java 规约 | 0 | 3 | 1 | 1 | 2 | 7 | REJECT | 个人代码规约，无版本敏感内容，被 #1 完全覆盖 |
| 20 | ayrtonaldayr/agent-skill-java-spring-framework | https://github.com/ayrtonaldayr/agent-skill-java-spring-framework | 11 | 2026-02-22 | null | Spring Framework 通用 | 0 | 0 | 1 | 1 | 0 | 2 | REJECT | >6 个月未推送，无许可，非官方 |
| 21 | Ashfaqbs/software-dev-ai-claude-toolkit | https://github.com/Ashfaqbs/software-dev-ai-claude-toolkit | 24 | 2026-02-07 | MIT | 综合工具箱含 Java | 0 | 0 | 1 | 1 | 2 | 4 | REJECT | >6 个月未推送 |
| 22 | ducpm2303/claude-java-plugins | https://github.com/ducpm2303/claude-java-plugins | 17 | 2026-04-06 | null | Java 插件集 | 0 | 1 | 1 | 1 | 0 | 3 | REJECT | 无许可，5 个月未动，内容为 IDE 操作说明 |
| 23 | docs.spring.io（Boot 4.1 / Framework 7 / Security 7 / Data JPA / Modulith 参考文档） | https://docs.spring.io/spring-boot/reference/ | — | 持续 | Apache-2.0（源在 `spring-projects/spring-boot` 等仓的 `*/src/docs/` 与 `framework-docs/`，仓库许可即 Apache-2.0） | 全部主题的权威事实 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | 所有版本敏感断言的裁决基准。许可已实查：`spring-projects/spring-boot` = Apache-2.0，`spring-projects/spring-framework` = Apache-2.0，`spring-projects/spring-security` = Apache-2.0 |
| 24 | spring-projects/spring-boot wiki：`Spring-Boot-4.0-Migration-Guide`、`Spring-Boot-4.0/4.1-Release-Notes` | https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide | 81415（宿主仓） | 2026-09-10（wiki 末次编辑 2026-06-28） | Apache-2.0（宿主仓许可） | 3→4 破坏性变更的官方原文 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE（merged） | 迁移章的最终依据；起步依赖对照表、`@MockBean` 移除、Jackson 3 群组 ID、Undertow 移除均出自此处 |
| 25 | openjdk.org JEP 页面（444 虚拟线程、440 record patterns、441 switch 模式匹配、485 stream gatherers 等） | https://openjdk.org/jeps/444 | — | 持续 | GPL-2.0（openjdk.org 站点内容） | Java 17→25 语言事实 | 3 | 3 | 3 | 3 | — | — | **reference** | 站点内容 GPL-2.0，按许可规则不得 merged。只用于核实 JEP 编号与「哪个版本转正」，正文语言事实由 #5 与 #10（均 MIT）重写而来 |

## 深度审查

### rrezartprebreza/spring-boot-skills（主干）

- **结构**：`skills/spring-boot-3/<topic>/` 与 `skills/spring-boot-4/<topic>/` 两套完全同名的 33 个目录，
  每个含 `SKILL.md` + `examples/{good,bad}-*.java` + 部分 `templates/*.java`，另有
  `plugins/spring-boot-{3,4}-skills/` 的 marketplace 包装和 `evaluations/cases.json`。
- **frontmatter**：只有 `name` + `description`（块标量），无 agent 专属字段，无需剥离。
  `description` 已经是「何时用 + 边界」的写法，与本仓库标准同源。
- **质量**：每篇末尾的 `## Gotchas` 一律写成 `Agent <做了什么> - <正确做法>`，即「模型会犯的错」，
  与 `docs/skill-standard.md` 第 3 节「teach the failure, not the API」完全一致，是本次唯一
  达到这个密度的上游。`transactional-patterns` 里「`@Retryable` 与 `@Transactional` 叠在同一方法上，
  重试跑在已标记 rollback-only 的事务里」这类断言，别的候选一条都没有。
- **agent 绑定**：无。`examples/` 里的 `bad-*.java` 不是可编译工程，只作阅读材料。
- **重叠**：与 #10 在 JPA/迁移上重叠，与 #3 在测试上重叠；裁决见下节。
- **不采用的目录**：`spring-ai-integration`、`ai-observability`、`mcp-server`（属 `ai-engineering` /
  `mcp-server` 边界）、`spring-cloud-gateway`、`spring-data-redis`、`spring-batch`、
  `multi-tenancy`、`hateoas`、`openapi-first`、`rest-api-conventions`、`api-versioning`
  （REST 契约设计按边界不覆盖）。

### github/awesome-copilot

- **结构**：`skills/<name>/SKILL.md`（+ `references/`）与 `instructions/<name>.instructions.md` 两类。
  后者的 frontmatter 是 `description` + `applyTo` glob，`applyTo` 属 agent 专属字段，合入时剥离。
- **`skills/spring-boot-testing`**：唯一给出「切片决策树 + 上下文缓存为什么慢」的上游，并且已经是
  Boot 4 + JUnit 6 基线（`MockMvcTester`、`RestTestClient`、`@MockitoBean`）。
- **`instructions/springboot-4-migration`**：48 KB，是本次覆盖面最全的迁移清单，但它以 Gradle Kotlin DSL +
  version catalog 为叙述主线，Maven 用户要自己翻译；本 skill 改写成构建工具中立的对照表。
- **`instructions/java-*-upgrade`**：JEP 编号、转正版本、preview 开关都准确，但缺「这个特性在 Spring 应用里
  什么时候真的该用」。虚拟线程与 `@Transactional`/`synchronized`/连接池的关系是本 skill 自己补的，
  依据 Boot 参考文档的 `spring.threads.virtual.enabled` 一节。

### a-pavithraa/springboot-skills-marketplace

- **结构**：`plugins/springboot-architecture/skills/{code-reviewer,creating-springboot-projects,spring-data-jpa,springboot-migration}/`，
  每个带 5–8 个 `references/*.md`。仓库还带 `tests/baseline-scenarios.md` 与 `tests/rationalizations.md`，
  说明作者也做过基线评测——这在社区上游里少见。
- **质量**：`spring-data-jpa/SKILL.md` 的「Critical rules」里「只给聚合根建 repository」「`save()` 在状态
  转换时的 persist/merge 语义」两条，是 #1 没有的架构层判断。`code-reviewer/references/java-25-features.md`
  （23 KB）覆盖虚拟线程、模式匹配、sealed、record patterns，是语言章的第二来源。
- **agent 绑定**：无，但目录深度依赖 plugin 布局；`paths` 精确到 4 个 skill 目录。

### spring-ai-community/spring-testing-skills

- **结构**：5 个测试 skill（fundamentals / jpa / mvc / security / webflux），每个带 `references/`。
  frontmatter 含非标准的 `version` 与 `license` 字段，合入时剥离。
- **许可**：GitHub API 报 `NOASSERTION`。实读仓库根 `LICENSE`，是完整的 Apache License 2.0 正文，
  按规则以真实 SPDX id `Apache-2.0` 记为 merged。
- **新鲜度**：2026-04-24，4.5 个月，仍在 6 个月窗口内（新鲜 1 分）。抽查 `@MockitoBean`、
  `@ServiceConnection`、Hibernate 7 三条，与官方文档一致，没有因为半年未动而失准。
- **不可替代的一条**：`@DataJpaTest` 里不 `flush()`+`clear()` 就从 Hibernate 一级缓存读回，
  测试假通过、SQL 根本没执行。#1 和 #3 都没写。

### adityamparikh/spring-boot-4-migration-skill

- **结构**：根 `SKILL.md` + 18 个 `references/*.md`，按「Framework 7 / Security 7 / Jackson 3 /
  Kafka 4 / AOT / 属性改名 / 渐进升级策略」切分。
- **质量**：Security 7 一章逐条给出移除的 API 与替代（`AuthorizationManager#check` → `#authorize`、
  `AntPathRequestMatcher`/`MvcRequestMatcher` → `PathPatternRequestMatcher`、
  `SecurityJackson2Modules` → `SecurityJacksonModules`、授权服务器起步依赖改名）。
  逐条对照 `spring-projects/spring-security` 源码核实：`PathPatternRequestMatcher.java` 存在于
  `web/src/main/java/.../servlet/util/matcher/`，`DaoAuthenticationProvider` 只剩
  `public DaoAuthenticationProvider(UserDetailsService)` 构造器、`setUserDetailsService` 已不存在。
- **重叠**：与 #4 大面积重叠但更细，且是 Maven 视角，正好补 #4 的 Gradle 偏向。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| 1 | 本 skill 是否按 Spring Boot 大版本分叉 | 主干上游 #1 分成 `spring-boot-3/*` 与 `spring-boot-4/*` 两套；#10、#12 只写迁移 | **不分叉**。正文一律以当前 GA 为准，3.x 差异集中在 `references/boot-4-migration.md` 的 `Spring Boot 4 differences` 小节 + 3→4 步骤 | 本仓库「一个生态 = 一个 skill」；且两套目录逐篇 diff 后，主题结构完全相同，差异集中在起步依赖名、Jackson 命名空间、测试注解、重试 API 这几处，够一个 reference 装下 |
| 2 | 「当前 GA」到底是 3.5 还是 4.x | 旧路线图与 #14、#15、#16 假设 3.x；#1、#3、#4 假设 4.x | **4.1**。`gh api repos/spring-projects/spring-boot/releases` 显示最新非预发布为 `v4.1.1`（2026-08-20），同日还有维护版 `v4.0.8` 与 `v3.5.16`，预发布为 `v4.2.0-M1` | 官方 releases 端点实测，未凭记忆 |
| 3 | Spock 在 Boot 4 是否可用 | #4 写「Spock 已移除，因为不支持 Groovy 5」 | **4.0 移除、4.1 恢复**。正文不写 Spock（属边缘），迁移 reference 里注明「4.0 曾移除、4.1 已恢复」 | `spring-boot` wiki `Spring-Boot-4.0-Migration-Guide` 有 "Spock Integration ... has been removed"；`Spring-Boot-4.1-Release-Notes` 有 "Restoration of Spock Support" |
| 4 | 重试用什么 | #14、#15 用 `spring-retry` + `@EnableRetry`；#1 用核心框架 `org.springframework.resilience.annotation` | **核心框架**。`@Retryable`/`@ConcurrencyLimit` + `@EnableResilientMethods`，属性名是 `includes`/`maxRetries`/`delay`/`jitter`，不是 spring-retry 的 `retryFor`/`maxAttempts` | `spring-projects/spring-framework` 中 `spring-context/src/main/java/org/springframework/resilience/annotation/{Retryable,EnableResilientMethods,ConcurrencyLimit}.java` 实测存在；`framework-docs/modules/ROOT/pages/core/resilience.adoc` 为其官方文档 |
| 5 | 声明式 HTTP 客户端怎么注册 | #14、#15 手写 `HttpServiceProxyFactory` bean；#1 用 `@ImportHttpServices` + 分组配置 | **`@ImportHttpServices`**，手写工厂降级为「一次性客户端」的逃生口 | `spring-projects/spring-framework` 中 `spring-web/src/main/java/org/springframework/web/service/registry/ImportHttpServices.java` 存在；Boot 4.0 Release Notes 的 "HTTP Service Clients" 一节确认自动配置与配置属性 |
| 6 | 错误契约叫 RFC 7807 还是 RFC 9457 | #7、#16 写 RFC 7807；#1 写 RFC 9457 | **RFC 9457**（它废止了 7807）。正文只写 9457 | RFC 9457 的 Obsoletes 头；Spring MVC 错误响应文档 |
| 7 | `@DataJpaTest` 用什么数据库 | #14、#8 默认嵌入式 H2；#1、#3、#11 要求 Testcontainers | **Testcontainers + `@ServiceConnection`**，并 `@AutoConfigureTestDatabase(replace = NONE)`。H2 只在「没有 Docker 的 CI」这个逃生口出现 | 方言与约束行为差异会让 H2 上的绿灯在 PostgreSQL 上变红；Boot 参考文档的 Testcontainers/service connection 一节 |
| 8 | `@DataJpaTest` 断言前要不要 `flush()`+`clear()` | 只有 #11 要求；#1、#3 未提 | **要求**。写进 Core rules | #11 的论证（不 clear 就命中 Hibernate 一级缓存，查询根本没下发）与 JPA `EntityManager` 语义一致，属真会咬人的静默失败 |
| 9 | 实体相等性 | #14 用 Lombok `@Data`；#1 要求自然键或默认对象同一性，禁止把集合/可变字段放进 `equals` | **#1**。`@Data` 生成的 `equals/hashCode/toString` 会遍历关联，触发懒加载与递归 | Hibernate 代理语义；#1、#10 一致 |
| 10 | 事务里发外部副作用 | #14、#15 直接在 `@Transactional` 方法里发邮件/发消息；#1 要求 `@TransactionalEventListener(AFTER_COMMIT)` | **#1** | 回滚撤不回已发出的邮件；Spring Framework 事务事件文档 |
| 11 | 空安全注解 | #12、#15 用 `org.springframework.lang.Nullable`；#1、#10 用 JSpecify | **JSpecify**（包级 `@NullMarked` + 例外处标注） | Spring Framework 7 全量采用 JSpecify，Boot 4 迁移指南「Nullability Annotations」一节 |
| 12 | 测试里的 mock 注解 | #14 用 `@MockBean`；#1、#3、#11 用 `@MockitoBean` | **`@MockitoBean`/`@MockitoSpyBean`**，并注明它们不能放在 `@Configuration` 类字段上（要用类级 `@MockitoBean(types = ...)`） | Boot 4.0 迁移指南 "`@MockBean` and `@SpyBean` Removal" 原文 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `rrezart-spring-boot` | rrezartprebreza/spring-boot-skills（`skills/spring-boot-4/` 下 11 个目录） | merged | 主干：事务传播与自调失效、AFTER_COMMIT 副作用、JPA 映射与 N+1/投影/keyset 分页/批量写、新实体判定、Security 7 lambda DSL 与方法安全、Problem Details、声明式 HTTP 客户端与分组配置、Modulith 模块校验与持久化事件、Actuator/Micrometer 约定、容器与 native 打包、JSpecify、3→4 迁移骨架、每章的 Gotchas |
| `awesome-copilot` | github/awesome-copilot（2 个 `skills/` + 3 个 `instructions/`） | merged | 测试切片决策树与上下文缓存成本、`MockMvcTester`/`RestTestClient`、GraalVM native image 接入与按构建错误反推 hints、Boot 4 起步依赖改名与包搬迁全表、Java 18–25 语言特性与 preview 开关 |
| `pavithraa-springboot` | a-pavithraa/springboot-skills-marketplace | merged | 只给聚合根建 repository、查询模式选型表（派生/`@Query`/投影/自定义/CQRS）、`save()` 的 persist-vs-merge 语义、Java 25 特性在 Spring 代码里的落法、评审输出结构 |
| `spring-testing-skills` | spring-ai-community/spring-testing-skills | merged | `@DataJpaTest` 的 `flush()`+`clear()` 规则、`@Transactional` 测试的回滚陷阱、懒加载在测试里通过而生产失败、Hibernate 6→7 迁移症状、切片之间的分工 |
| `adityamparikh-boot4` | adityamparikh/spring-boot-4-migration-skill | merged | Spring Security 7 破坏性变更清单、Framework 7 变更、渐进升级策略（先 6.5 准备再 7.0）、Kafka 4 与 AOT 迁移要点 |
| `spring-docs` | docs.spring.io（Boot / Framework / Security / Data JPA / Modulith 参考文档） | merged | 所有版本敏感断言的裁决基准与事实来源 |
| `spring-boot-wiki` | spring-projects/spring-boot wiki（4.0 迁移指南 + 4.0/4.1 Release Notes） | merged | 3→4 破坏性变更原文、起步依赖对照表、`@MockBean` 移除、Jackson 3 群组 ID、Undertow 移除、Spock 4.1 恢复、当前 GA 版本 |
| `openjdk-jeps` | openjdk.org JEP 页面 | reference | 仅用于核实 JEP 编号与转正版本；站点内容 GPL-2.0，不得 merged，未复制任何文字 |

未采用（已在候选表留行）：Amplicode/spring-skills（专有 MCP 绑定）、piomin/claude-ai-spring-boot、
giuseppe-trisciuoglio/developer-kit、HoangNguyen0403/agent-skills-standard、
majiayu000/claude-skill-registry、full-stack-skills/spring-skills、ItQianChen、ayrtonaldayr、
Ashfaqbs、ducpm2303。

## 基线缺口

无 skill（`uv run tools/run_evals.py java-spring --baseline`，Claude Opus 5 · medium，2026-09-11）时，
各场景未达成的 `expected_behavior`。四个场景 `skill_read` 均为 `False`，耗时依次
456.7 / 297.1 / 296.1 / 68.5 秒。总体基线很强（模型自行联网查了官方迁移指南，甚至自建
Spring Boot 工程做了对照实验），缺口集中在「不查文档就想不起来」的静默失败上：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 JPA/事务评审 | 「primitive `long version` 必须换成包装类 `Long`」 | 8 条里唯一完全漏掉的一条。基线逐条点评了 `@Data`、`ORDINAL`、EAGER、自调用、事务内发信、N+1、private `@Transactional`，却没看 `@Version` 的类型。这是典型的静默失败：Spring Data 用 null version 判定新实体，primitive 恒为 0 → 每次 `save()` 都走 merge 并多发一条 SELECT |
| 1 JPA/事务评审 | 「自调用的修法是把 `submitOne` 挪到独立 bean（或注入自身代理）」 | 诊断完全正确，但修法是把它降级成私有助手、明确放弃 `REQUIRES_NEW`。这是一个可辩护的设计选择，只是不等于期望里的修法，记为部分达成 |
| 2 Boot 3.5→4 迁移 | 「重试搬进核心框架：`org.springframework.resilience.annotation` 的 `@Retryable` + `@EnableResilientMethods`」 | 基线只说「Boot 4 移除了 spring-retry 的依赖管理，要么钉死版本，要么迁到 Spring Framework 7 的 `org.springframework.core.retry`」。`core.retry` 是编程式 `RetryTemplate`/`RetryPolicy` API，声明式注解在 `resilience.annotation`，基线没给出可直接照抄的注解名 |
| 3 测试重构 | 「`@DataJpaTest` 里 `TestEntityManager` + `flush()` 然后 `clear()` 再断言」 | 完全没提。基线把 `@DataJpaTest` 的价值说成「自带事务回滚，顺序依赖消失」，恰恰漏掉了「不 `clear()` 就命中 Hibernate 一级缓存、查询根本没下发、测试假通过」这条 |
| 3 测试重构 | 「用 `RestTestClient` + `@AutoConfigureRestTestClient` 取代 `TestRestTemplate`」 | 基线在冒烟切片里继续用 `TestRestTemplate`，尽管它在同一份答复里正确指出 `@MockBean` 已被 Boot 4 移除 |
| 3 测试重构 | 「`spring.jpa.open-in-view=true` 也是要报的问题之一」 | `ddl-auto: update`、actuator 全暴露、`spring.test.database.replace` 位置错误都点到了，`open-in-view` 漏掉 |

其余 `expected_behavior` 基线均已达成，场景 4（负例）基线表现正确：只给 Android/Kotlin
建议（`viewModelScope`、`SupervisorJob`、`asStateFlow`），完全没有 Spring 内容。

## 评测结果

两组均为 `anthropic/claude-opus-5` · `thinking=medium`（`tools/run_evals.py` 默认值，未传
`--model` / `--thinking`）。输出目录 `/tmp/hs-evals/java-spring/anthropic-claude-opus-5-medium/`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 JPA 与事务评审 | claude-opus-5:medium | 无（baseline） | false | 8 条中 6.5 条：自调用诊断、事务内发信、N+1、private `@Transactional`、`ORDINAL`、`@Data`、EAGER+`readOnly`；自调用**修法**不同（降级为私有助手而非独立 bean），记 0.5 | 漏 primitive `long version`。456.7 s；自建 Boot 3.5 + H2 工程做了对照实验 |
| 1 JPA 与事务评审 | claude-opus-5:medium | 有 skill | true | 8 条中 7.5 条：新增达成 **primitive `long version` → `Long`**（基线缺口，已填补）；自调用修法仍选择去掉 `REQUIRES_NEW`，记 0.5 | 142.4 s（基线的 31%）。直接套用了 SKILL.md 的 Output format（按文件分组、`Lnn severity - …`、before/after），并额外提示 `open-in-view=false` 与 `status` 索引 |
| 2 Boot 3.5→4 迁移 | claude-opus-5:medium | 无（baseline） | false | 12 条中 11 条 | 漏「核心框架重试 API」的具体注解名（只说迁到 `org.springframework.core.retry`，那是编程式 `RetryTemplate`，不是声明式注解）。297.1 s，大量联网检索官方指南 |
| 2 Boot 3.5→4 迁移 | claude-opus-5:medium | 有 skill | true | 12 条全部达成，含 **`@Retryable` + `@EnableResilientMethods`（`org.springframework.resilience.annotation`）及其 `includes`/`maxRetries`/`delay`/`jitter` 属性名**（基线缺口，已填补） | 108.4 s。额外产出：`hasRole` 对 JWT scope 无效、401/403 需要 `AuthenticationEntryPoint`/`AccessDeniedHandler`、缺 `issuer-uri` 校验、明文口令、`open-in-view`。Spring Framework 7 只以「Servlet 6.1 / Jakarta EE 11 基线」表述，未逐字点名，仍判达成 |
| 3 测试重构 | claude-opus-5:medium | 无（baseline） | false | 8 条中 5 条 | 漏 `flush()`+`clear()`、`RestTestClient`、`open-in-view`。296.1 s |
| 3 测试重构 | claude-opus-5:medium | 有 skill | true | 8 条全部达成，新增 **`TestEntityManager` + `flush()`/`clear()`（并写明「不 clear 就命中一级缓存、查询根本没执行」）**、**`@AutoConfigureRestTestClient`**、**`open-in-view: false`**（三条基线缺口全部填补） | 155.2 s。另外指出旧 `findByStatus(null)` 生成 `status is null`、`pricingIsStubbed` 是重言式断言、`@WithMockUser` 需要 `spring-boot-starter-security-test` |
| 4 Android 协程负例 | claude-opus-5:medium | 无（baseline） | false | 3 条全部达成 | 68.5 s。只给 `viewModelScope`/`SupervisorJob`/`asStateFlow` 等 Android 建议 |
| 4 Android 协程负例 | claude-opus-5:medium | 有 skill（可见但不应加载） | **false** | 3 条全部达成 | 58.9 s。答复里明确写「`java-spring` skill 明确排除 Android/Kotlin mobile，所以没有套用它」——`description` 的否定边界起了作用，SKILL.md 未被读取。全文无任何 Spring/JPA/servlet 建议 |

结论：**通过**。基线未达成的 5 条行为在有 skill 时全部达成——
场景 1 的 primitive `@Version` 类型、场景 2 的核心框架重试注解、场景 3 的 `flush()`/`clear()`、
`RestTestClient`、`open-in-view`。负例场景 `skill_read == false`，边界生效。
附带观察：三个正例的耗时都降到基线的 31%–52%，因为基线要靠联网检索才能确认 Boot 4 的事实，
有 skill 时直接从 reference 取。

唯一仍未按期望达成的一项：场景 1 的「自调用修法应为挪到独立 bean」。两组都选择删掉
`REQUIRES_NEW` 让整批成为一个原子事务。考虑到夹具的用户描述正是「整批失败时不该发信」，
这个修法在语义上更贴题，不视为 skill 缺陷；SKILL.md 规则 11 与 `references/data-jpa.md`
都已写明「独立 bean」是标准修法，模型是在读到之后做了取舍。

## 备注

- **不按大版本分叉的理由**（裁决 1 的展开）：主干上游把 `spring-boot-3` 与 `spring-boot-4` 做成两套
  平行目录，是因为它按「插件」分发，用户按自己项目的大版本二选一。本仓库是单一 skill 库，
  `description` 决定加载时机，分叉会让两个 skill 的触发词几乎相同、互相抢加载，而且 90% 内容重复。
  逐篇 diff 两套目录后确认，真正的差异只有五类：起步依赖名、Jackson 命名空间、测试注解与测试起步依赖、
  重试 API 归属、空安全注解体系——全部装进 `references/boot-4-migration.md` 一个文件即可。
- **当前 GA 版本核实结果**：`gh api repos/spring-projects/spring-boot/releases` 于 2026-09-11 返回的
  最新非预发布版本为 **`v4.1.1`（2026-08-20）**；同期维护分支为 `v4.0.8`（2026-08-21）与
  `v3.5.16`（2026-06-25）；最新预发布为 `v4.2.0-M1`（2026-08-20）。因此正文基线写作
  「Spring Boot 4.1」，需要区分 4.0/4.1 的地方（如 Spock、`spring.http.clients.cookie-handling`）
  显式标版本。
- **许可注意**：
  - `spring-ai-community/spring-testing-skills` 的 GitHub API 值是 `NOASSERTION`，实读 `LICENSE`
    为完整 Apache License 2.0 → 按 `Apache-2.0` 记 merged。
  - `full-stack-skills/spring-skills` 的 `LICENSE` 实读后是第三方声明汇总，不构成本仓库许可 →
    视同无许可；因内容质量本就不达标，直接 REJECT，不进 SOURCES。
  - `Amplicode/spring-skills` API 返回 `license: null`，本可按 NONE 合入，但它强制依赖专有 MCP
    server 且要求逐字照抄其 `examples/`，属产品包装 + agent 绑定 → REJECT。
  - `docs.spring.io` 的源在 `spring-projects/*` 各仓（`spring-boot`、`spring-framework`、
    `spring-security` 实查均为 Apache-2.0），按波次 1 的教训以 `merged` 记，不记 reference。
  - openjdk.org 站点内容为 GPL-2.0 → `reference`，只用于核对 JEP 编号与转正版本。
- **未来同步要盯**：`rrezartprebreza/spring-boot-skills`（活跃，主干）、
  `github/awesome-copilot` 的 `instructions/springboot-4-migration`（随 Boot 小版本变动）、
  Spring Boot 4.2 GA（当前 `4.2.0-M1`，转正后需复核 `references/boot-4-migration.md` 的版本标注）。
- **放弃的方向**：REST 契约/OpenAPI 设计（`rest-api-conventions`、`api-versioning`、`openapi-first`、
  `hateoas`）、Spring Cloud Gateway、Spring Batch、Spring AI、Spring Data Redis、多租户——
  按本波边界不覆盖，主干上游中对应的目录未进 `paths`。
