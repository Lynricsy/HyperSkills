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

## 2026-09-30 上游同步

依据：`/tmp/upstream-report-0930.txt`（2026-09-30 `check_upstream.py`）中本 skill 有 2 条 `behind`，其中
awesome-copilot 为 `diff too large`。全部按完整区间归因：blobless 克隆到 `/tmp/hs-up/<owner>__<repo>`，对
`<旧 pin>..<HEAD>` 跑 `git log --oneline -- <paths>`、`git diff --stat` 与 `git diff`，并用
`git cat-file -e <HEAD>:<path>` 确认 tracked path 均仍存在。`--pin` 后逐条核对：写入的 commit 与审阅 HEAD 一致
（f0c06a0、15ed97c）。三条 docs 为 manual check，本次只为核实下文的事实更正读了 spring-framework 源码。

### 归因表

| 上游 | 区间 | 命中提交/文件 | 判定 | 理由 |
|---|---|---|---|---|
| rrezart-spring-boot | c43b0b6 → f0c06a0（2 提交） | 09d9b78「Correct transaction and domain event skill guidance」：`spring-boot-4/transactional-patterns` 的 SKILL.md、good/bad 示例与模板。要点：① `readOnly` 只是优化提示，不是写保护也不自动路由到副本；② 成功审计不该用 `REQUIRES_NEW`（外层回滚后留下声称成功的孤儿行），改 `MANDATORY` 同事务，`REQUIRES_NEW` 只留给必须在失败后存活的「尝试」记录，且独立事务不可引用未提交父行；③ 删除错误的 `noRollbackFor = OptimisticLockException` 示例；④ 没有活动事务时 `@TransactionalEventListener` 默认被跳过；⑤ AFTER_COMMIT 非持久投递，必达要 outbox；⑥ saga 改为「本地事务 + 幂等命令 + 补偿」步骤描述；⑦ 修复建议去掉「注入自身」；⑧ 仓库层事务注解不该被删 | ① 需更正（事实更正）；②④ 候选 → 评测后不合入；③⑤⑦⑧ 已覆盖；⑥ 噪声 | ① `references/data-jpa.md` 原文「`readOnly` … lets the driver route to a replica」暗示标志本身可路由，见下「事实更正」。②④ 写成场景 5，无 skill 基线全部答出。③ 正文从未写 `noRollbackFor` 恢复乐观锁，重试节已是「调用方 bean + 新事务」；⑤ data-jpa「Side effects after commit」与 modulith 已写进程内投递会丢、用持久发布登记或 outbox；⑦ 正文首选抽 bean，`exposeProxy` 仅作最后手段；⑧ 正文只说业务事务放在服务层，没有让删仓库注解。⑥ 是通用架构常识，本 skill 不覆盖分布式事务 |
| awesome-copilot | 7568a48 → 15ed97c（64 提交） | 5 个 tracked 路径 0 提交 | 噪声 | 区间改动全在其他 skill/instructions；too-large 只是 compare 上限 |

### 事实更正：`readOnly` 与副本路由

证据（`gh api` 读 spring-projects/spring-framework `main`）：`Transactional#readOnly` 的 javadoc 写明它
「just serves as a hint for the actual transaction subsystem; it will not necessarily cause failure of write access
attempts」，不能解释该提示的事务管理器会静默忽略它；`HibernateJpaDialect#beginTransaction` 在 `readOnly` 时只通过
`DataSourceUtils.prepareConnectionForTransaction` 给物理连接设只读，不选数据源；真正按只读事务换数据源的是
`LazyConnectionDataSourceProxy#setReadOnlyDataSource`（`@since 6.1.2`）或以
`TransactionSynchronizationManager#isCurrentTransactionReadOnly()` 取键的 `AbstractRoutingDataSource`。据此把
`references/data-jpa.md`「Transaction boundaries」一条改为：标志只是提示，既不保证写失败也不自行路由，副本读需要
路由 `DataSource`，并点名上述两种做法。

### 评测

新增场景 5（夹具 `PaymentService.java`、`PaymentExpiryJob.java`、`V7__audit_entry.sql`、
`payments-application.yml`）：成功审计走 `REQUIRES_NEW` 留孤儿行、无事务发布事件致 AFTER_COMMIT 监听器被跳过、
以为 `readOnly` 已把读流量送到副本。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 5 | workbuddy/deepseek-v4.1-flash（thinking max） | 无 | False | 1、2、3、4、5（5/5） | 自行核对了 `fallbackExecution` 默认值；给出 `MANDATORY` 同事务、失败尝试另表；`@Transactional` 包住作业并提到 AFTER_COMMIT 需 outbox 才必达；路由用 `AbstractRoutingDataSource` + `LazyConnectionDataSourceProxy` |
| 5 | workbuddy/deepseek-v4.1-flash（thinking max） | 有 | True | 1、2、3、5；4 前半（4.5/5） | 正文改后跑；1、2、3、5 与基线同；4 只给了 `@Transactional` 修复和可选 `@Async`，没提 AFTER_COMMIT 仍是尽力而为（该句在 `data-jpa.md` 已有，本次未改动相关段落）；5 与更正后的 data-jpa 表述一致 |

结论：②④ 两个候选基线已会，按规则不合入，场景 5 保留作哨兵；正文只做 ① 的事实更正。D1 静态门通过；安装冒烟
（`npx skills@latest add <worktree> --skill java-spring --agent universal --copy --yes`）后
`.agents/skills/java-spring/` 的 SKILL.md、SOURCES.yaml、NOTICE.md 与 10 个 references 齐全，与源目录 `diff -r` 一致。

## 2026-10-15 上游同步

依据 2026-10-15 `tools/check_upstream.py` 报告：`awesome-copilot`（138 commits）一条 `behind`，为 diff too large to attribute to paths。主代理已在 shallow blobless 裸仓库缓存（`/tmp/hs-attr/github__awesome-copilot`）上按完整 `<旧pin>..<审阅HEAD>` 区间、限该条目 `paths` 归因为空；本次复跑 `git log --oneline <pinned>..<head> -- <paths>` 仍为空，并用不依赖提交历史完整性的树对比 `git diff --stat <pinned> <head> -- <paths>` 与两端 `git ls-tree` 复核（结果为空、所有追踪路径在两端均存在），未用日期过滤。

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| awesome-copilot | 15ed97c → 3cf7c7e（138 commits，全仓 827 个文件变更） | 无：`skills/spring-boot-testing`、`skills/java-add-graalvm-native-image-support`、`instructions/springboot-4-migration.instructions.md`、`instructions/java-17-to-java-21-upgrade.instructions.md`、`instructions/java-21-to-java-25-upgrade.instructions.md` 区间内无提交、树对比为空 | 未变更，仅 re-pin |

其余仓库上游（`rrezart-spring-boot`、`pavithraa-springboot`、`spring-testing-skills`、`adityamparikh-boot4` 为 up to date）随 `--pin` 一并对齐；pin 写入的 commit 与审阅 HEAD 逐条一致（f0c06a0、3cf7c7e、6277c14、7e7b331、9ba6aab），`pin_check.py` 结果 PIN CHECK CLEAN。3 条 `kind: docs` 条目为 manual check，本次未改。

结论：behind 条目在追踪 paths 下均无上游提交，正文未变，未新增评测场景、未跑评测；仅 re-pin 并把版本号改为 2026.10.15。

## 2026-10-15 文档上游复核

范围：3 条 `kind: docs` 条目的 `contributes` 声明事实 + SKILL.md 与 references 中引用的属性名、移除/弃用项、版本下限与 JEP 编号。当前版本（`gh api` 与 Maven Central）：Spring Boot GA 仍为 4.1.1（4.2.0-M2 为里程碑），Spring Framework 7.0.9、Spring Security 7.1.1、Spring Data JPA 4.1.1、Spring Modulith 2.1.1。wiki 用 `gh repo clone spring-projects/spring-boot.wiki` 读取（页面已移入 `releasenotes/` 目录，原 URL 仍 200）。本机实跑：Maven + Boot 4.1.1 最小应用（`spring-boot-starter-security`），Temurin 25.0.4.1、26.0.2.1 与系统 OpenJDK 27。

| 上游 id | 核对的事实 | 当前官方页面 | 结论 |
|---|---|---|---|
| spring-docs | 正文引用的 26 个配置键在 4.1.1 属性附录中存在（`spring.http.clients.connect-timeout`/`read-timeout`、`spring.http.serviceclient.*`、`spring.http.clients.cookie-handling`、`spring.mvc/webflux.apiversion.*`、`spring.jackson.use-jackson2-defaults`/`find-and-add-modules`/`json.read.*`、`spring.datasource.connection-fetch`、`management.opentelemetry.tracing.export.otlp.*` 等），单数 `spring.http.client.*` 确实不存在；`@ImportHttpServices(group=…)` 与 `spring.http.serviceclient.<group>`，`HttpServiceGroup.ClientType.WEB_CLIENT`；Framework 7 `@Retryable`/`@ConcurrencyLimit`/`@EnableResilientMethods` 及 `includes`/`maxRetries`/`delay`/`jitter`；Security 7.0 移除项；`-Djarmode=tools … extract --layers` 的四个层目录 | https://docs.spring.io/spring-boot/reference/ （appendix/application-properties、io/rest-client）、https://docs.spring.io/spring-framework/reference/core/resilience.html 、https://docs.spring.io/spring-security/reference/7.0/whats-new.html | 属性、HTTP 服务客户端、重试注解、Dockerfile 解包一致（本机打包 4.1.1 jar 实跑 `extract --layers` 得 application/dependencies/snapshot-dependencies/spring-boot-loader）。**更正 1**：web-and-clients.md 写「重试、并发限制与熔断来自核心 Spring Framework」，Framework 7 resilience 页只有 `@Retryable` 与 `@ConcurrencyLimit`，核心无熔断器；改为核心无熔断、沿用项目已有熔断库。**更正 2**：security.md 把 `@EnableGlobalMethodSecurity` 与 `SecurityJackson2Modules` 列为「编译错误、非弃用」的已移除项；7.0 What's New 未列其移除，7.1.1 jar 中两者仍在（javap：`@Deprecated`，后者 `forRemoval=true`），本机 Boot 4.1.1 实跑带 `@EnableGlobalMethodSecurity` 的应用可编译，启动时报 `IllegalStateException: @EnableGlobalMethodSecurity requires the spring-security-access dependency`，加 `spring-security-access` 后正常启动；已移出移除表并写明弃用 + 启动依赖。**更正 3**：`AccessDecisionManager`/`AccessDecisionVoter`「自 5.5 弃用」改为 5.8（5.5/5.7 javadoc 无弃用标记，5.8 起 `@Deprecated`） |
| spring-boot-wiki | 4.0 迁移指南：模块化 starter 与改名表、per-technology test starter、Undertow/Spock 移除、Jackson 3（`tools.jackson`、注解包例外、改名类型、`use-jackson2-defaults`、`spring-boot-jackson2`、Jersey）、properties-migrator、`@MockBean`→`@MockitoBean`（不能用于 `@Configuration` 字段）、`@SpringBootTest` 不再提供 MockMvc、`RestTestClient`、`BootstrapRegistry`/`EnvironmentPostProcessor` 包迁移、Kotlin 2.2+、GraalVM 25+；4.1 发布说明：Spock 恢复、cookie-handling、`InetAddressFilter`、gRPC、懒取 JDBC 连接、Derby 弃用、jOOQ 3.20 需 Java 21 | https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide （及 Spring-Boot-4.1-Release-Notes） | 迁移指南自上次同步无提交，逐项一致；4.1 发布说明自 09-11 起仅新增 Hibernate 7.4 升级与 Tomcat 临时目录清理两条，与正文规则无关。**更正 4**：boot-4-migration.md 写「4.1 弃用 Derby 与 layertools」，发布说明为「已弃用的 layertools jar mode 在本版本移除，改用 `tools`」；本机 4.1.1 jar 实跑 `-Djarmode=layertools` 报 `Unsupported jarmode 'layertools'`，`-Djarmode=tools list-layers` 正常；已改为移除 |
| openjdk-jeps | 21：JEP 441/440/431/451；22：456；23：467/474/471；24：485/484/491/472/486/490/479；25：511/512/506/510/514/515/503，470 与 505 为预览；421 自 18 | https://openjdk.org/projects/jdk/25/ 及各 JEP 页（Release 字段逐个核对） | 其余一致。**更正 5**：Flexible Constructor Bodies 标为 25 正式却给出预览 JEP 447/482/492，25 的正式 JEP 为 513；改为「JEP 513（预览 447/482/492）」。**更正 6**：GC 段写「24 移除非分代模式，`-XX:-ZGenerational` 现在无法启动」；JEP 490 规定该选项 obsolete（打印警告、仍用分代 ZGC），本机 Temurin 25.0.4.1 实跑为「Ignoring option ZGenerational; support was removed in 24.0」且正常启动，26.0.2.1 与 27 报「Unrecognized VM option」拒绝启动；已改为 24/25 忽略并警告、26 起拒绝启动 |

结论：3 条复核完毕，6 处既有正文事实更正已合入（均为纠错、非新增内容，未新增评测场景、未跑评测）；3 个条目 `synced_at` 改为 2026-10-15，`spring-boot-wiki` notes 记录 GA 复核。

## 2026-10-15 D2 回归

覆盖提交：a187d7d 上游同步、d8d1edf Security 7 弃用项、layertools 移除、熔断、JEP 513 / ZGC。口径 omp + `openai/gpt-6.1-sol` medium，隔离 VM，输出 `/tmp/hs-d2/D2G1/java-spring/omp-openai-gpt-6.1-sol-medium/`（14:17–14:55 provider 503 期间的失败运行已自动重跑，不计）。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 2 Boot 3.5 → 4 迁移（SecurityConfig 含 `@EnableGlobalMethodSecurity`，pom 含 spring-retry） | gpt-6.1-sol medium | 有 | true | ✔1–4 ◐5 ✔6–11 ◐12（10✔2◐） | 123 s。`@EnableGlobalMethodSecurity` → `@EnableMethodSecurity`、`DaoAuthenticationProvider` 构造器注入，未把弃用项说成编译错误；spring-retry 写「Boot 4 不再管理版本，迁到 Framework 7 resilience API 或自行定版本」，未点名 `@Retryable`/`@EnableResilientMethods`；properties-migrator 与 `spring.jackson.json.read` 改名均给出；基线要求缺 Framework 7 / Jakarta EE 11 明示 |
| 2 | gpt-6.1-sol medium | 无 | false | ✔1–4 ◐5 ✔6–10 ◐11 ✔12（10✔2◐） | 234 s。与有 skill 同级：同样未点名核心 `@Retryable`；改了 Jackson 属性但未建议 properties-migrator |
| 4 负例（Android 协程） | gpt-6.1-sol medium | 有 | false | 3/3 | 36 s。改用 `viewModelScope`，无 Spring 建议 |
| 6 Boot 4.1 / Java 25→26 升级评审（新增） | gpt-6.1-sol medium | 有 | true | 4/4 | 133 s。`layertools` 在 4.1 移除 → `-Djarmode=tools … extract --layers`，入口改 `java -jar`；非分代 ZGC 自 JDK 24 移除，25 上 `-XX:-ZGenerational` 被忽略并告警、26 上拒绝启动，现在就删；核心 Spring 只有 `@Retryable`/`@ConcurrencyLimit`/`@EnableResilientMethods`，无断路器，保留 Resilience4j；JEP 513 在 25 已定稿，无需 `--enable-preview`。另提 4.1 `-DskipTests` 不再跳过测试 AOT |
| 6 | gpt-6.1-sol medium | 无 | false | 4/4 | 197 s。四项结论与有 skill 一致（含 25 忽略 / 26 拒绝启动、`resilience4j-spring-boot4`、JEP 513 final） |

选择理由：2 的夹具含 `@EnableGlobalMethodSecurity` 与 spring-retry（Security 7 弃用项、熔断更正）；layertools 移除、`-XX:-ZGenerational`、核心无熔断、JEP 513 没有场景覆盖，新增 6（`Dockerfile` + `upgrade-plan.md`）；4 为负例。

结论：场景 2 两侧 10✔2◐ 持平，有 skill 未把弃用项说成编译错误；新增 6 两侧 4/4（基线已会，作哨兵保留）；负例 `skill_read=false`。未改正文。

遗留：场景 2 两侧都没有点名核心 `@Retryable` 的迁移目标，与基线持平。

## 2026-11-01 上游同步

依据主代理 2026-11-01 快照（`/tmp/hs-upstream-2026-11-01.json`）与工作单。`--pin` 写入的 commit 与审阅 HEAD 逐条一致（rrezart `c2c23fe`、awesome-copilot `5269f7e`、pavithraa `208a943`），无越界差额。awesome-copilot 用裸仓库缓存 `/tmp/hs-attr/github__awesome-copilot` 做树对比；另两个仓库用 `gh api compare` 的 patch，逐文件读真实 diff。本机核实环境：Maven + Spring Boot 4.1.1 父 POM（Framework 7.0.9、Security 7.1.x、Testcontainers 2.0.5），一次性工程 `/tmp/g05b-verify`，用后不入库。

| 上游 | 区间 | 命中 paths | 判定 |
|---|---|---|---|
| rrezart-spring-boot | f0c06a0 → c2c23fe（a317397、b22f8c0 命中） | `oauth2-resource-server`：示例删掉 `setAuthoritiesClaimName("scope")`，改为保留默认 `scope`/`scp` 转换再追加 Keycloak `realm_access.roles`；gotcha「`setAuthoritiesClaimName(...)` 替换默认查找，`SCOPE_*` 消失」；`sub` 不是 UUID；补 `audiences`。`problem-details-rfc9457`：`@PreAuthorize` 拒绝在 dispatcher 内抛 `AccessDeniedException`，advice 不映射就被 `Exception` 兜底成 500。`testing-pyramid`：`@WebMvcTest` 写请求需 `.with(csrf())`，否则 `@WithMockUser` 下也是 403；Testcontainers 2 构件 `testcontainers-postgresql`、类 `org.testcontainers.postgresql.PostgreSQLContainer`（非泛型）。`flyway-migrations`：`CREATE INDEX CONCURRENTLY` 必须独占一个迁移且要 `spring.flyway.postgresql.transactional-lock=false`、`baseline-on-migrate: false`、`NOT VALID` + `VALIDATE` 加约束。`spring-security-jwt`：`/error` 放行。`multi-module-maven`：`lombok-mapstruct-binding`。`spring-data-jpa`：示例 `@EntityGraph` 路径修正 | **事实更正 4 处**（见下），均本机实跑或读源码核实；`CONCURRENTLY`/`transactional-lock`、`baseline-on-migrate`、`/error` 放行、`lombok-mapstruct-binding`、`sub` 非 UUID 属新增规则，本 skill 正文无对应错误断言，未跑基线证明缺口，本轮不合入 |
| awesome-copilot | 3cf7c7e → 5269f7e | `instructions/java-17-to-java-21-upgrade.instructions.md`、`instructions/java-21-to-java-25-upgrade.instructions.md` **在 HEAD 已不存在**：9de77d27 把两份指南并入新的 `skills/java-upgrade`（`references/java-17-to-21.md`、`java-21-to-25.md`），并修正示例（Class-File API 与 Stream Gatherers 定稿于 24 而非 25、JEP 468 派生记录未交付、ML-KEM 到 24 才有、`STR` 外无内置模板处理器、`Gatherers.fold` 签名、ZGC 非分代模式 24 移除）。`skills/java-add-graalvm-native-image-support` 重构为 SKILL.md + 6 个 references（构建工具、reachability metadata、排错表、Spring Boot 4.1.1 + GraalVM 25 实测） | Phase B：`paths` 改指 `skills/java-upgrade/references/java-17-to-21.md` 与 `java-21-to-25.md`，notes 记录迁移。上游的更正与本 skill `references/java-language.md` 现有写法一致（24 定稿的两项、ZGC、JEP 513 早已按 2026-10-15 复核写对），无影响。GraalVM 重构与 `build-and-packaging.md` 的 native 工作流一致，新增的「先在 JVM 上 `spring.aot.enabled=true`」「native 测试改 subclass mock maker」属新增规则，不合入 |
| pavithraa-springboot | 6277c14 → 208a943（67 提交） | `spring-data-jpa` **整目录被删除**（23a35a4 retire，2.0.0），JPA 内容并入 `code-reviewer/references/jpa-performance.md`；`code-reviewer` 大幅压缩并新增 `test-review.md`、`testing/traps.md`、`testing/boot4-test-toolkit.md`；`springboot-migration` 压缩并核对 Boot 4.1.1（Jackson 属性族在 4.1 的回归、`maxAttempts`→`maxRetries` 差一、`TestRestTemplate` 未弃用）、新增 Testcontainers 2 迁移细节（Kafka `ConfluentKafkaContainer`、LocalStack 新类、JUnit 4 规则失效）、JEP 491 / Java 26–27 预览 API 更正 | Phase B：删去已不存在的 `spring-data-jpa` path（内容已在 `code-reviewer` path 下）。Testcontainers 2 构件与包名与 rrezart 一致，经 Boot 4.1.1 BOM 核实后作为更正 4 合入；上次 notes 里「TC2 迁移建议超出官方文档、未采用」随之改写。其余均为新增规则，本轮不合入；它们与本 skill 现有断言不冲突（JEP 491、ZGC、Jackson `json.read` 已一致） |

### 事实更正（均为既有正文断言错误，非新增内容）

1. **`setAuthoritiesClaimName` 会丢掉 scope 权限**（`references/security.md`）。原文先说 scope 检查用 `hasAuthority("SCOPE_…")`，紧接着的示例却 `setAuthoritiesClaimName("roles")`——spring-security 7.1.2 `JwtGrantedAuthoritiesConverter` 源码里默认 `WELL_KNOWN_AUTHORITIES_CLAIM_NAMES = ["scope","scp"]`，`setAuthoritiesClaimName` 用 `singletonList` 整体替换。本机实跑：默认转换 `scope`/`scp` 都得 `[SCOPE_orders:read]`；设成 `roles` 后只剩 `[ROLE_admin]`。改为保留默认转换再叠加角色的写法（已编译实跑，得 `ROLE_admin`、`SCOPE_orders:read`）。
2. **`@PreAuthorize` 拒绝会进 advice**（`references/security.md`「Errors from the filter chain」、`references/web-and-clients.md`）。原文「所有认证与授权失败都发生在 dispatcher 之前 / 永远到不了 advice」。本机 `@WebMvcTest` + `@EnableMethodSecurity` + `@ExceptionHandler(Exception.class)`：USER 调 `@PreAuthorize("hasRole('ADMIN')")` 返回 `500 {"detail":"AuthorizationDeniedException"}`。改为 URL 级失败走过滤器链，方法级拒绝会进 advice，须映射为 403 或放行传播。
3. **`@WebMvcTest` 写请求需要 CSRF token**（`references/testing.md`）。原示例 `mvc.post()` 未带 `.with(csrf())` 却断言 400。本机：`@WithMockUser` 下不带 csrf 为 403，带上才进入控制器。示例补 `.with(csrf())`，说明段补「默认链开 CSRF；要测真实规则就 `@Import` 安全配置」。
4. **Testcontainers 2**（`references/testing.md`）。原示例 `PostgreSQLContainer<?>`（1.x 的 `org.testcontainers.containers` 类）。Boot 4.1.1 BOM 管理 `testcontainers.version` 2.0.5，`testcontainers-bom` 2.0.5 只有 `testcontainers-postgresql`；本机加载到 `org.testcontainers.postgresql.PostgreSQLContainer`（类型参数 0 个），旧类仍在且带 `@Deprecated`。Boot 自己的文档示例（v4.1.2 `MyIntegrationTests` 用 `org.testcontainers.neo4j.Neo4jContainer`）同样已是 2.x 写法。示例改为新类，并补构件改名与旧 id 无托管版本的说明。

另核实但**不采纳**的一条：pavithraa `testing/traps.md` 称「实现了接口的类上 `@Retryable` 永不重试（Framework 7.0.9），须 `@EnableResilientMethods(proxyTargetClass = true)`」。本机纯 `AnnotationConfigApplicationContext` 下确实如此（JDK 代理，调用 1 次即抛出；`proxyTargetClass = true` 时 CGLIB，重试到第 3 次成功）；但在 `@SpringBootTest` 的 Boot 默认配置下得到 CGLIB 代理、重试生效（3 次调用返回 ok）。对 Boot 应用不成立，不写入正文。

## 2026-11-01 上游新增内容评估

| 候选 | 许可 | 结论 | 理由 |
|---|---|---|---|
| a-pavithraa/springboot-skills-marketplace `writing-springboot-tests/SKILL.md`（+ `assets/*`） | MIT | MERGE（加入 `paths` 追踪；正文本轮只取已核实的 TC2 事实） | 在 Scope 内（各层测试），作者用 Boot 4.1.1 + Postgres 18 + Kafka 4.1 + WireMock 3.13 实跑模板，增量明确：测试登录（`jwt()`/`oidcLogin()`/`user()`）绕过应用自己的角色映射、`@RestClientTest` 不导入 `spring.http.clients.*`、WireMock 引入 Apache HttpClient 5 后 503 POST 自动重试一次掩盖 `@Retryable`、Kafka 4 DLT 名改 `-dlt`。这些是新增规则，按流程需先证明基线缺口，留待下轮；其 `@Retryable` 接口代理一条在 Boot 下不成立（见上） |
| 同仓库 `spring-boot-team-harness/SKILL.md`、`assets/project-skills/{add-module,db-migration}/SKILL.md`、`assets/project/{AGENTS.md,CLAUDE.md}` | MIT | REJECT | 给团队仓库装 Claude Code hooks、NullAway/ArchUnit/Spotless 门禁与 CI 的安装脚本，属上游自用 agent 编排；其中「Boot 4 只有 `flyway-core` 不跑迁移」已在本 skill Core rule 18 |
| github/awesome-copilot `skills/java-upgrade/SKILL.md` | MIT | REJECT（references 已改入 `paths`） | SKILL.md 是通用升级流程 + 外部 `modernize-java` 插件推广；`java-11-to-17.md` 低于本 skill 的 Java 17 下限 |
| github/awesome-copilot `instructions/java-upgrade.instructions.md` | MIT | REJECT | 13 行指针，只叫模型去用 java-upgrade skill |
| github/awesome-copilot `skills/java-hibernate-jpa/SKILL.md` | MIT | 待定 | 框架中立的 Hibernate/JPA 问题库，与 `references/data-jpa.md` 大面积重叠；增量如 `hibernate.query.fail_on_pagination_over_collection_fetch`、Hibernate 7 版本差异属新增规则，需基线证明缺口后再议 |
| github/awesome-copilot `skills/java-development/SKILL.md` | MIT | REJECT（范围） | 无框架的纯 Java 日常开发（构建、格式化、jlink/jpackage），不在本 skill「Spring Boot 应用」范围；作为「纯 Java」skill 候选写进汇报 |
| github/awesome-copilot `skills/create-quarkus-project`、`quarkus-application-development`、`quarkus-dev-services-and-testing` | MIT | REJECT（范围） | Quarkus 是另一套框架，本 skill 只写 Spring；作为 Quarkus skill 候选写进汇报（awesome-copilot 另有 `quarkus-native-and-container`） |
| Redocly/redocly-cli `packages/client-generator/eject-assets/skills/java-generator/SKILL.md` | MIT | REJECT | Redocly CLI 客户端代码生成器 eject 出来的产品附带 skill，单一产品手册 |

## 2026-11-01 新候选检索

途径：`gh search repos`（`spring boot skills` 限 2026-09-15 后创建、`spring boot 4 agent skill`）、`spring-projects`/`spring-ai-community`/`spring-io` 组织最近新建仓库（无新 skill 仓库）、awesome-copilot 本区间新增 Java 类 skill（见上表）。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 26 | Dancan254/spring-boot-skills | https://github.com/Dancan254/spring-boot-skills | 4 | 2026-09-30 | MIT | 17 个 skill：api-design、devops-scaffold、kafka-setup、otel-setup、pentest-audit 等 | 0 | 3 | 1 | — | 2 | 6 | REJECT | 一人维护的脚手架/流程合集，主题多在本 skill 范围外（DevOps、渗透、MCP），Spring 部分无版本敏感事实 |
| 27 | gianmdp03/modern-spring-boot-skills | https://github.com/gianmdp03/modern-spring-boot-skills | 1 | 2026-09-17 | NONE | 单个 SKILL.md | 0 | 3 | 1 | — | 0 | 4 | REJECT | 无许可、1 star、单文件 |

## 2026-11-01 文档上游复核

| 上游 id | 核对的事实 | 当前官方页面 | 结论 |
|---|---|---|---|
| spring-docs | 本轮更正涉及的四处：`JwtGrantedAuthoritiesConverter` 默认 `scope`/`scp`、方法安全拒绝在 dispatcher 内抛出、`@WebMvcTest` 默认链开 CSRF、Boot 4.1 托管 Testcontainers 2 | spring-security 7.1.2 源码；spring-boot v4.1.2 `documentation/spring-boot-docs` 的 Testcontainers 示例；本机 Boot 4.1.1 实跑 | 四处原正文过时或错误，**已修**（见上「事实更正」）。当前版本：Boot 4.1.2 GA（2026-10-22）、4.2.0-RC1；Framework 7.0.10；Security 7.1.2；Data JPA 4.1.2；Modulith 2.1.2；正文「Spring Boot 4.1」基线不变 |
| spring-boot-wiki | 4.0 迁移指南与 4.1 发布说明 | `gh repo clone spring-projects/spring-boot.wiki`，`git log --since=2026-10-14` | 一致。此后只有 `releasenotes/preview/4.2/*`（RC1/RC2）与 4.2 发布说明草稿变化，4.0 迁移指南、4.1 发布说明未改；notes 更新 GA 为 4.1.2 |
| openjdk-jeps | 25 的 JEP 列表（506/510/511/512/513/514/515 正式，470/502/505/507 预览，508 孵化） | https://openjdk.org/projects/jdk/25/（Last update 2025/9/23） | 一致，无需改动 |

三个 docs 条目 `synced_at` 改为 2026-11-01。下次同步要盯：Spring Boot 4.2 GA（RC1 已出，转正后复核 `references/boot-4-migration.md` 的版本标注）；pavithraa `writing-springboot-tests` 的测试陷阱若在评测里暴露缺口再按新增规则合入。

## 2026-11-01 D2 回归

覆盖提交 `144f0ef`（四处事实更正：JWT 权限转换、方法安全拒绝进 advice、`@WebMvcTest` CSRF、Testcontainers 2）。现有场景都不考察这四处，新增场景 7（夹具 `AccountsSecurityConfig.java`、`AccountService.java`、`AccountControllerTest.java`：四张工单一一对应四处更正）。负例用场景 4（Android 协程）。模型 `openai/gpt-6.1-sol` medium（VM 内 omp），产物 `/tmp/hs-d2/G05b-backend2/java-spring/omp-openai-gpt-6.1-sol-medium/`，逐条读 `answer.md` 人工判定。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 7（新增） | gpt-6.1-sol medium | 有 | True | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ | 87 s。默认 scope 转换 + roles 转换合并；`AccessDeniedException` → 403 handler，并指出过滤器链的 `AccessDeniedHandler` 救不回已被 advice 吞掉的异常；`.with(csrf())` 或 `@Import` 真实配置；`testcontainers-postgresql` + `org.testcontainers.postgresql.PostgreSQLContainer`。另指出兜底 handler 会把 `MethodArgumentNotValidException` 也变 500 |
| 7（新增） | gpt-6.1-sol medium | 无 | False | EB1 ✔ EB2 ✔ EB3 ✔ EB4 ✔ | 103 s。联网查文档，结论与有 skill 一致（用 `DelegatingJwtGrantedAuthoritiesConverter`；建议删掉兜底或对安全异常 rethrow）|
| 4（负例） | gpt-6.1-sol medium | 有 | **False** | 3/3 | 26 s。改用 `viewModelScope`，无 Spring 建议 |

结论：四处更正在有 skill 时全部按更正后的内容作答，无回退；基线同样 4/4，不构成新增正文的缺口，场景 7 留作哨兵（主要防止正文旧断言「授权失败到不了 advice」「`PostgreSQLContainer<?>`」再次误导）。负例 `skill_read == false`。正文无需再改。

## 2026-11-01 跨组命中评估

其他组（`debugging` 2026-11-01 评估，列为跨组命中）转来的上游新增文件，`gh api` 读原文后裁决。github/awesome-copilot 已由本 skill 以 `awesome-copilot` 追踪。

| 候选 | 结论 | 理由 |
|---|---|---|
| github/awesome-copilot `skills/java-debugging`（`SKILL.md` + `references/stack-traces.md`；最近提交 aeb5a5af 2026-10-21） | REJECT（不扩 paths）；Scope 问题上交 | 主体是 JDWP 挂调试器（只绑 `127.0.0.1`、`suspend=n`、JDK 9 前裸 `address=5005` 绑全部网卡、Gradle `--debug-jvm`/`debugOptions.host` 7.6+、Surefire/Failsafe debug、容器内 `*:5005` 的暴露面）与 JEP 358 版本差异。本 skill Scope 是 Spring Boot 应用本身，「把可复现故障追到根因」明确归 `debugging`，而 `debugging` 又以「Java 生态内容」拒收——JVM 调试器操作目前无 skill 覆盖，属扩 Scope，写入汇报。Spring 相关的一行（`spring-boot:run -Dspring-boot.run.jvmArguments=...`）单独不足以成条 |
| github/awesome-copilot `skills/java-diagnostics`（`SKILL.md` + 8 个 references） | REJECT（不扩 paths）；Scope 问题上交 | JVM 运行时诊断（jcmd/jstack/jmap 分级、JFR、async-profiler、NMT、GC 日志、MAT、堆转储含密钥）。与本 skill 的交集只有 Actuator `heapdump`/`threaddump` 不得公开暴露，已在 SKILL.md 规则与 `references/observability.md` 覆盖；其余是 JVM 层而非 Spring 层，同上属扩 Scope |

正文无改动，无需 D2。
