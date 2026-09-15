# containers 调研记录

> 模板：`templates/research.md`。流程见 `docs/workflow.md`，评分量表见 `docs/skill-standard.md` 第 9 节。

## 调研日期与检索途径

- 调研日期：2026-09-11
- 复核日期：
- 检索途径：
  - `gh api search/repositories`：`kubernetes skill agent in:name,description`、
    `docker claude skill in:name,description`、`helm OR kustomize agent skill`
  - `gh api search/code`：`filename:SKILL.md dockerfile multi-stage`
  - `github/awesome-copilot`（`skills/` 与 `instructions/` 两个目录都搜过 `docker|kube|container|helm|devcontainer|compose|k8s`）
  - 领域官方组织仓库：`docker/`（全量 repo 列表已扫，**没有**官方 agent-skills 仓）、
    `google/skills`、`Azure/AKS-Skills`、`kubernetes/website`、`helm/helm-www`、
    `kubernetes-sigs/kustomize`、`devcontainers/spec`、`compose-spec/compose-spec`
  - 路线图种子更正：`getsentry/skills` 的 `infrastructure/` **不存在**（见候选表第 17 行）
- GitHub API 核对方式：`gh api repos/<owner>/<repo> --jq '{stars:.stargazers_count, pushed:.pushed_at, license:.license.spdx_id}'`
  （`gh auth status` 通过：账号 Lynricsy）

## 版本事实核对（写正文前先定的基线）

全部用 `gh api` 从上游仓库原文取证，不凭记忆：

| 事实 | 取值 | 取证方式 |
|---|---|---|
| Kubernetes 当前稳定版 | **v1.37.0**（2026-08-26 发布；1.36.4 / 1.35.8 / 1.34.11 仍在维护） | `gh api repos/kubernetes/kubernetes/releases` |
| 最近一次 API **移除** | **v1.32** 移除 `flowcontrol.apiserver.k8s.io/v1beta3`；1.33–1.37 无新移除 | `kubernetes/website` `content/en/docs/reference/using-api/deprecation-guide.md`（`## Removed APIs by release` 最新一节是 v1.32） |
| 历史高频踩坑移除 | Ingress `extensions/v1beta1`+`networking.k8s.io/v1beta1` → 1.22；CronJob `batch/v1beta1`、PDB `policy/v1beta1`、HPA `autoscaling/v2beta1`、EndpointSlice `discovery.k8s.io/v1beta1` → 1.25；HPA `autoscaling/v2beta2` → 1.26 | 同上 |
| 边车容器（`initContainers[].restartPolicy: Always`） | `SidecarContainers` **stable since 1.33**（1.29–1.32 beta 默认开） | `feature-gates/SidecarContainers.md` 的 `stages` |
| 原地改资源（`pods/resize` 子资源、`resizePolicy`） | `InPlacePodVerticalScaling` **beta 1.33–1.34，stable+locked since 1.35** | `feature-gates/InPlacePodVerticalScaling.md` |
| Pod 级 resources（`spec.resources`） | `PodLevelResources` **beta since 1.34**（1.32–1.33 alpha） | `feature-gates/PodLevelResources.md` |
| 用户命名空间（`spec.hostUsers: false`） | `UserNamespacesSupport` **stable+locked since 1.36**（1.33–1.35 beta 默认开） | `feature-gates/UserNamespacesSupport.md` |
| Compose 顶层 `version:` | **obsolete**：只作向后兼容，用了会告警；Compose 永远用最新 schema 校验 | `docker/docs` `content/reference/compose-file/version-and-name.md`，小节标题原文 `## Version top-level element (obsolete)` |
| Compose 当前版本 | v5.5.1（2026-09-03） | `gh api repos/docker/compose/releases` |
| Docker Engine（本机） | 29.7.2 | `docker version --format '{{.Server.Version}}'` |
| 构建缓存失效规则 | `ADD`/`COPY`/`RUN --mount=type=bind` 按文件元数据算 checksum（**不含 mtime**）；其余指令只比较命令字符串；一旦失效后续全部失效 | `docker/docs` `content/manuals/build/cache/invalidation.md` |

## 候选表

评分：权威 0–3 / 新鲜 0–3 / 具体 0–3 / 正确 0–3 / 许可 0–2。总分 ≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | LukasNiessen/kubernetes-skill（根 `SKILL.md` + `references/*`，不含 `references/conditional/*`） | https://github.com/LukasNiessen/kubernetes-skill | 399 | 2026-08-16 | MIT | K8s 六大失效模式：不安全默认、资源饥饿、网络暴露、权限蔓延、脆弱滚动、API 漂移 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | 唯一按「失效模式」而非「资源类型」组织的 K8s skill，正是本仓库要的写法。抽查三条：Ingress 1.22 移除、PDB `policy/v1beta1` 1.25 移除、HPA v2beta1 1.25 / v2beta2 1.26 移除，对照官方 deprecation-guide **全对** |
| 2 | github/awesome-copilot `instructions/devcontainers.instructions.md` | https://github.com/github/awesome-copilot | 38872 | 2026-09-10 | MIT | devcontainer.json / Feature / Codespaces 生命周期的 12 条可核查规则 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 全仓最高质量的一份：每条规则给出「读什么文件、报什么、不要报什么」，并区分「文件里写了」与「镜像 label 可能补上」。devcontainer 一节直接以它为骨架 |
| 3 | github/awesome-copilot `instructions/kubernetes-manifests.instructions.md` | 同上 | 38872 | 2026-09-10 | MIT | 标签约定、securityContext 默认、资源、探针、校验命令 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | `app.kubernetes.io/*` 推荐标签集与 securityContext 默认值清单可直接作为清单基线；组织方式偏「要点罗列」，需重写 |
| 4 | github/awesome-copilot `instructions/kubernetes-deployment-best-practices.instructions.md` | 同上 | 38872 | 2026-09-10 | MIT | Pod/Deployment/Service/Ingress/ConfigMap/Secret/HPA 全资源覆盖（307 行） | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE（仅覆盖面） | "Your Mission / As GitHub Copilot" 人设 + 教程式讲解，具体性低；只用来核对「本 skill 少写了哪类资源」 |
| 5 | github/awesome-copilot `instructions/containerization-docker-best-practices.instructions.md` | 同上 | 38872 | 2026-09-10 | MIT | 不可变性、可移植性、多阶段、层优化、扫描、运行时（681 行） | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE（仅覆盖面） | 每条都是 "Principle / Deeper Dive / Guidance for Copilot / Pro Tip" 四段展开，token 密度极低；取覆盖面不取文字 |
| 6 | github/awesome-copilot `skills/multi-stage-dockerfile/SKILL.md` | 同上 | 38872 | 2026-09-10 | MIT | 多阶段结构、基础镜像、层缓存、安全、性能 | 3 | 3 | 2 | 2 | 2 | 12 | INCLUDE（仅覆盖面） | 40 行泛化建议（"consider distroless where appropriate"），且示例仍写 `node:18`。正确性扣分：只讲 "use multi-stage to avoid build secrets"，而多阶段**不能**阻止 provenance attestation 泄密（见冲突 C2） |
| 7 | netresearch/docker-development-skill `skills/docker-development/**` | https://github.com/netresearch/docker-development-skill | 20 | 2026-09-10 | **MIT（代码）+ CC-BY-SA-4.0（内容）**，API 报 NOASSERTION | 多阶段缓存、构建密钥泄漏、CI 中测镜像、bind mount 属主、registry pin rot、GPG 验证 | 1 | 3 | 3 | 3 | 2 | 12 | INCLUDE | API 的 NOASSERTION 是双许可文件（`LICENSE-MIT` + `LICENSE-CC-BY-SA-4.0`）导致，README「License」节明写：代码 MIT，**内容（skill 定义、文档、references）CC-BY-SA-4.0** → 按规则只取结构与清单语义、全部重写。`build-secret-leaks.md` 给出可执行的 provenance 取证命令与实测案例，是本 skill 最有价值的单点 |
| 8 | google/skills `skills/cloud/gke-app-onboarding`（含 `assets/Dockerfile`、`assets/deployment.yaml`） | https://github.com/google/skills | 19743 | 2026-09-10 | Apache-2.0 | 容器化评估→多阶段构建→加固 Deployment+Service 清单 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE（剥离 GKE） | `assets/deployment.yaml` 是一份少见的**同时**写全 `automountServiceAccountToken: false`、`runAsNonRoot`、`seccompProfile: RuntimeDefault`、`readOnlyRootFilesystem`、`capabilities.drop: [ALL]`、镜像按 digest 引用、`/healthz` 与 `/readyz` 分离的参考清单。GKE 专属部分（Artifact Registry 路径、`gcloud`/`pack`、MCP 工具名、Cloud Logging）全部剥离 |
| 9 | Azure/AKS-Skills `skills/aks-troubleshooting`（`references/symptom-map.md` 等） | https://github.com/Azure/AKS-Skills | 4 | 2026-09-10 | MIT | Day-2 症状路由：CrashLoopBackOff / OOMKilled / ImagePullBackOff / Pending / NotReady / 502 | 3 | 3 | 3 | 2 | 2 | 13 | INCLUDE（剥离 AKS） | 微软官方，「症状→证据→根因」的只读排障契约质量高。正确性扣分：大量结论依赖 `az aks` 与 AppLens，脱离 Azure 不成立 → 只取与 `kubectl` 相关的症状/证据顺序，`az`、AGIC、SNAT、Entra Workload ID 一律剥离 |
| 10 | Impertio-Studio/Docker-Claude-Skill-Package `skills/source/docker-agents/docker-agents-review` | https://github.com/Impertio-Studio/Docker-Claude-Skill-Package | 10 | 2026-07-08 | MIT | Dockerfile / Compose 评审清单，PASS/FAIL 对照 | 1 | 2 | 2 | 2 | 2 | 9 | INCLUDE（仅评审清单结构） | `FAIL: … PASS: …` 的对照式清单格式适合 review workflow。内容偏基础（latest 标签、HEALTHCHECK、非 root），且 `compatibility` 写 "Designed for Claude Code" 属 agent 绑定，必须剥离 |
| 11 | BagelHole/DevOps-Security-Agent-Skills `devops/containers/*`、`devops/orchestration/helm-charts` | https://github.com/BagelHole/DevOps-Security-Agent-Skills | 1081 | 2026-05-22 | MIT | Docker 管理、Compose、registry、Podman、Helm chart | 1 | 2 | 1 | 2 | 2 | 8 | MAYBE（覆盖面校验） | 星数高但内容是「命令速查 + 教程」（`references/docker-commands.md`、`helm-commands.md`），模型早就会；`Prerequisites: Docker Engine 20.10+` 这类段落是纯 token 浪费。只用于确认没漏主题 |
| 12 | docs.docker.com（源仓库 docker/docs） | https://docs.docker.com/ | 4648 | 2026-09-10 | **Apache-2.0**（已实读 `LICENSE` 首行确认） | Dockerfile 参考、BuildKit 缓存与失效、`--mount=type=secret`、Compose 规范、`compose watch` | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 官方文档且许可可合入 → `relation: merged` 而非 reference。缓存失效规则、`version:` obsolete、secret mount 三处事实以它为准 |
| 13 | kubernetes.io/docs（源仓库 kubernetes/website） | https://kubernetes.io/docs/ | 5381 | 2026-09-10 | **CC-BY-4.0** | API 弃用/移除表、PSS 三档、QoS、探针、feature gate 阶段表 | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 所有版本门（1.33 sidecar / 1.35 resize / 1.36 hostUsers / 1.34 pod-level resources）都从这里的 `feature-gates/*.md` `stages` 字段取，不凭记忆。CC-BY-4.0 → `notes` 写署名 |
| 14 | helm.sh/docs（源仓库 helm/helm-www） | https://helm.sh/docs/ | 229 | 2026-09-10 | MIT | chart 结构、values 约定、`helm template`/`--dry-run=server`、chart 测试与钩子 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | Helm 侧事实来源；`helm/helm` 本体（Apache-2.0，30232★）只用来确认版本 |
| 15 | kubernetes-sigs/kustomize（`site/content/en/**` 文档） | https://github.com/kubernetes-sigs/kustomize | 12161 | 2026-09-09 | Apache-2.0 | overlay/patch/generator、`kubectl kustomize` 与独立 CLI 的差异 | 3 | 3 | 2 | 3 | 2 | 13 | INCLUDE | Kustomize 侧事实来源；「什么时候用 Kustomize 而不是 Helm」的裁决依据之一 |
| 16 | containers.dev 规范（源仓库 devcontainers/spec） | https://containers.dev/implementors/json_reference/ | 5709 | 2026-03-20 | CC-BY-4.0 | devcontainer.json 属性表、image-metadata label 合并语义、生命周期命令顺序 | 3 | 1 | 3 | 3 | 2 | 12 | INCLUDE | 规范仓推送 >5 月但属官方规范且内容仍准确（新鲜度给 1 而非 REJECT）。第 2 行候选的每条规则都指向这里，交叉校验用 |
| 17 | getsentry/skills `infrastructure/` | https://github.com/getsentry/skills | — | — | — | 路线图种子 | — | — | — | — | — | — | **REJECT（不存在）** | `gh api repos/getsentry/skills/git/trees/main?recursive=1` 顶层只有 `.agents/ .claude-plugin/ .claude/ agents/ skills/` 等；全树按 `infra\|docker\|kube\|container` 过滤只命中 `skills/gha-security-review/references/runner-infrastructure.md` 与 `skills/security-review/infrastructure/docker.md`（属安全审计 skill 的子文件，非容器 skill）。路线图种子作废，后续批次不要再找 |
| 18 | compose-spec/compose-spec | https://github.com/compose-spec/compose-spec | 2726 | 2026-09-01 | Apache-2.0 | Compose 规范本体（`profiles`、`develop.watch`、`healthcheck`、`depends_on.condition`） | 3 | 3 | 3 | 3 | 2 | 14 | INCLUDE | 与 docs.docker.com 同源事实的规范级出处；`version:` obsolete 的规范依据 |
| 19 | initializ/forge | https://github.com/initializ/forge | 227 | 2026-09-10 | Apache-2.0 | Go 写的构建/打包 CLI | 0 | 3 | 0 | 0 | 2 | 5 | REJECT | 搜索命中是因为仓里有 `Dockerfile` 与 `forge-cli/container/*.go`。这是产品源码，不是 skill 仓 |
| 20 | iflytek/skillhub | https://github.com/iflytek/skillhub | 5080 | 2026-09-10 | Apache-2.0 | skill 市场平台本体 | 0 | 3 | 0 | 0 | 2 | 5 | REJECT | 命中的全是它自己的 `Dockerfile`/`docker-compose.yml`/部署文档，仓内没有容器主题 skill |
| 21 | wrsmith108/docker-claude-skill | https://github.com/wrsmith108/docker-claude-skill | 8 | 2026-03-04 | MIT | 单人 Docker skill | 0 | 0 | 1 | 1 | 2 | 4 | REJECT | >6 个月未推送（量表规定直接 REJECT），且非官方 |
| 22 | vstorm-co/production-stack-skills | https://github.com/vstorm-co/production-stack-skills | 25 | 2026-04-16 | MIT | 「生产技术栈」拼装（含 Docker 部署片段） | 0 | 1 | 1 | 1 | 2 | 5 | REJECT | 近 5 个月未推送；内容是把若干产品拼在一起的部署脚本，不是容器主题的规则集 |
| 23 | alphaparkinc/genpark-kubernetes-gitops-manifest-drift-reconciliation-skill | https://github.com/alphaparkinc/genpark-kubernetes-gitops-manifest-drift-reconciliation-skill | 8 | 2026-08-30 | 无（API `null`） | GitOps 清单漂移对账 | 0 | 3 | 2 | 1 | 0 | 6 | REJECT（越界） | 主题是 GitOps 控制器对账，属未来 `observability`/CD 范畴，不在本 skill 边界内；且无许可文件 |
| 24 | Docker 官方组织有无 agent-skills 仓 | https://github.com/orgs/docker/repos | — | — | — | — | — | — | — | — | — | — | **结论：没有** | `gh api orgs/docker/repos?per_page=100` 全量列过（`docs`、`cli`、`buildx`、`compose`、`awesome-compose`、`build-push-action`…），**不存在**官方 agent skills 仓。所以 `containers` 不适用「官方厂商特例」，走常规判据：merged 上游远超 3 个且均活跃 |

**立项判据**：常规判据满足——活跃（6 个月内推送）且总分 ≥8 的上游有 14 个（第 1–16 行去掉 REJECT），
其中 merged 上游 9 个。不是官方厂商特例。

## 深度审查

### 1. LukasNiessen/kubernetes-skill（MIT，399★）

- **结构**：根 `SKILL.md` 100 行，7 步流水线（捕获上下文→判定失效模式→按需加载 reference→给修复路径→产出清单→校验→输出契约），
  25 个 `references/*.md` + 6 个 `references/conditional/*.md`。`docs/` 是同内容的 GitBook 副本，重复。
- **frontmatter**：只有 `name` + `description`，无 agent 专属字段，干净。`description` 里点名 EKS/GKE/AKS/OpenShift/GitOps/observability——
  这正是本 skill 要划掉的边界，合入时**不能**照抄。
- **质量**：`fragile-rollouts.md` 把「liveness 探针里查外部依赖 → 数据库一挂全体级联重启」这条讲透了因果链，是本主题里最值得占 token 的一条；
  `resource-starvation.md` 的 QoS 表与「CPU limit 引发 CFS 节流」立场明确；`api-drift.md` 的移除版本全部核对无误。
- **重叠**：与候选 3/4（awesome-copilot K8s instructions）在 securityContext、probes、resources 上重叠，但它给的是**症状→根因**，
  后者给的是**字段清单**，可互补。
- **不取的部分**：`references/conditional/{eks,gke,aks,openshift}-patterns.md`（托管控制面，明确不覆盖）、
  `observability-stacks.md`（Prometheus Operator/OTel，未来 `observability` 的地盘）、`gitops-controllers.md`（Argo/Flux，越界）。
  `SOURCES.yaml` 的 `paths` 只列实际用到的目录。
- **写法上不采纳的**：满篇 `ALWAYS`/`NEVER` 全大写（标准第 3 节禁止）；「Directive:」开头的祈使段；`docs/` 副本。

### 2. github/awesome-copilot `instructions/devcontainers.instructions.md`（MIT，38872★）

- **结构**：无章节模板，但每条规则形如「断言 → 看什么 → 改什么 → 出处链接」，并单列「Do not report」段落防过度报告。
- **质量**：最关键的一条是「`devcontainer.json` 与镜像的 `devcontainer.metadata` label 合并，文件里**写了**的赢，
  文件里**没写**的不能推断为不存在」——这是 review 场景下唯一能保证零假阳性的读法，直接决定本 skill 的 devcontainer 一节怎么写。
  「可缓存的安装工作属于 `onCreateCommand`/`updateContentCommand`，不属于 `postCreateCommand`，因为 prebuild 只跑到 `updateContentCommand`」
  这条对照 devcontainers/spec 与 Codespaces 文档核实无误。
- **agent 绑定**：`applyTo:` 是 Copilot instruction 专属字段，合入时剥离。
- **重叠**：与其他候选零重叠，是唯一覆盖 devcontainer 的高质量上游。

### 3. netresearch/docker-development-skill（MIT + CC-BY-SA-4.0，20★）

- **结构**：`SKILL.md` + 8 个窄主题 reference + `checkpoints.yaml`。
- **frontmatter**：`allowed-tools`（在本仓库白名单内但语义是 Claude Code 绑定）、`metadata.repository`——合入时按 1.2 节剥离到只剩规范字段。
- **质量**：`build-secret-leaks.md` 指出「`docker history` 干净 ≠ 没泄密」，因为 buildx 把 `--build-arg` **原样**写进 SLSA provenance attestation，
  并给出 `docker buildx imagetools inspect --format '{{json .Provenance}}'` 的取证命令和一个实测案例（1461 个已发布版本携带可用 token）。
  这一条其他所有候选都没有，且直接推翻候选 6 的「用多阶段就能避免构建密钥进镜像」。
- **许可**：API 报 NOASSERTION 是因为仓根有两个许可文件。README 明确分割：代码 MIT、**内容 CC-BY-SA-4.0**。
  按仓库规则，CC-BY-SA 只取结构与清单语义，正文全部用自己的话重写，不复制任何句子。
- **重叠**：与候选 10（Impertio）在「Dockerfile 评审项」上重叠，但深度差一个量级。

### 4. google/skills `skills/cloud/gke-app-onboarding`（Apache-2.0，19743★）

- **结构**：评估→容器化→清单→部署→迁移，配 `assets/`（Dockerfile、index.js、package.json、deployment.yaml）。
- **frontmatter**：`metadata.category: Containers`（非白名单形态，剥离）；正文顶部有 `> **MCP Tools:** apply_k8s_manifest, …` 的工具绑定块，剥离。
- **质量**：`assets/deployment.yaml` 是最完整的一份「默认就该长这样」的加固清单，且 `/healthz` 与 `/readyz` 分离——
  与候选 1 的探针语义论证正好互为示例与原理。
- **GKE 剥离方式**（记录在案）：删除 `us-docker.pkg.dev/<PROJECT>/<REPO>/...` 形式的 Artifact Registry 路径（改为占位 registry），
  删除 `gcloud`/`pack build --builder gcr.io/buildpacks/builder`、Cloud Logging 采集、Workload Identity、Autopilot 约束、
  `apply_k8s_manifest` 等 MCP 工具名；保留的只有 securityContext 字段集、探针分离、digest 引用、资源设置这些在任何集群都成立的部分。

### 5. Azure/AKS-Skills `skills/aks-troubleshooting`（MIT，4★，微软官方）

- **结构**：操作规则（只读、证据先于结论、证据顺序）→ 症状路由表 → `references/symptom-map.md`（16 个症状块）→ 两个只读脚本。
- **质量**：「只读默认」与「不许在没有证据的情况下下根因结论」两条契约值得吸收进本 skill 的排障 workflow。
  症状清单（Pending、CrashLoopBackOff、OOMKilled、ImagePullBackOff、NotReady、502/503、DNS）与本 skill 边界重合度高。
- **AKS 剥离方式**（记录在案）：`az aks` 全部命令、AppLens/Resource Health 检测器、Azure MCP 能力发现段、
  Azure CNI / SNAT 端口耗尽 / AGIC / Entra Workload ID / spot 驱逐与可用区再平衡等 Azure 侧原因全部删除；
  保留「先看平台侧状态再进集群」的**顺序**思想，重写为「先看 Node 与 Event，再看 Pod 与容器」。
- **重叠**：与候选 1 的失效模式框架重叠，但候选 1 面向「写清单时避免」，它面向「已经炸了怎么查」，正好构成两个不同 workflow。

### 6. github/awesome-copilot 的三份泛化资产（候选 3/4/5/6）

结构上都是 Copilot instruction/skill 的「人设 + 要点罗列」，`## Your Mission` / `As GitHub Copilot, you are an expert…` 是硬伤，
且候选 5 每条要点展开成四段，681 行里真正的可执行规则不足 30 条。裁决：**只用作覆盖面清单**，
逐条对照「本 skill 是否漏了这个主题」，文字一律不取。唯一例外是候选 3 的 `app.kubernetes.io/*` 推荐标签集（本身来自 Kubernetes 官方约定）。

## 冲突与裁决

| # | 冲突点 | 各方主张 | 裁决 | 依据 |
|---|---|---|---|---|
| C1 | 要不要设 CPU limit | LukasNiessen `resource-starvation.md`：多数工作负载**不要**设 CPU limit，CFS 节流带来不可预测的延迟；只在多租户/批处理/需要 Guaranteed QoS 时设。awesome-copilot `kubernetes-deployment-best-practices`：requests 和 limits 都要设 | 采纳「memory limit 必设、CPU limit 默认不设，除非需要 Guaranteed QoS 或多租户公平性」，并写明代价：不设 CPU limit 的 Pod 只能是 Burstable，节点压力下的驱逐序位在 Guaranteed 之后 | 官方文档两边都不表态（kubernetes.io 只描述 QoS 与节流机制，不给偏好），社区里 LukasNiessen 的论证给出了机制层面的因果（CFS 配额窗口内耗尽即节流），awesome-copilot 那句是无论证的清单项。「更具体 > 更泛化」，并补上官方 QoS 语义作为代价说明 |
| C2 | 多阶段构建能否防止构建密钥泄漏 | awesome-copilot `multi-stage-dockerfile`：「Use multi-stage builds to avoid including build secrets in the final image」。netresearch `build-secret-leaks.md`：多阶段**不能**防——buildx 把 `--build-arg` 原样写进 SLSA provenance attestation，`docker history` 看不到但 `imagetools inspect --format '{{json .Provenance}}'` 里是明文 | 采纳 netresearch：正文写「`ARG` 传密钥即泄漏，与是否多阶段无关；唯一正确做法是 `RUN --mount=type=secret`」，并给 provenance 取证命令作为验证门 | 官方文档站在 netresearch 一边：docs.docker.com 的 build secrets 页面明确 build args 不适合密钥。且 netresearch 给了可复现的取证命令与实测案例，awesome-copilot 只有一句断言。「更具体且可验证 > 断言」 |
| C3 | Compose 文件要不要写 `version:` | 大量社区素材（含候选 11 的 compose 示例）仍写 `version: "3.8"` | 正文一律不写 `version:`，并说明写了会收到 obsolete 告警 | docker/docs `content/reference/compose-file/version-and-name.md` 小节标题原文即 `## Version top-level element (obsolete)`：「only informative and you'll receive a warning message that it is obsolete if used」。官方 > 社区 |
| C4 | Alpine 还是 distroless 作为运行时基础镜像 | netresearch 默认 Alpine（`node:24-alpine` + `addgroup/adduser`）；google/skills 与 awesome-copilot 都推 distroless；候选 10 列出 alpine/slim/distroless/scratch 四选 | 给**一个默认 + 一个逃生口**（标准第 3 节）：默认 distroless 或 `scratch`（静态链接语言）/`-slim`（需要 libc 与包管理的语言）；需要在容器里 exec 排障时才退回 Alpine，并说明 Alpine 的 musl 会改变 DNS 解析与 glibc 编译产物的行为 | 「不罗列多个可选库」是本仓库写作规则；distroless 是三方中两方（含官方厂商 Google）的选择；musl/DNS 差异是 Alpine 的真实代价，必须写出来而不是简单否定 |
| C5 | 排障时先查什么 | Azure/AKS-Skills：先查平台侧（云 API、检测器）再进集群；LukasNiessen：直接按失效模式定位 | 本 skill 不覆盖托管控制面，采纳「先 `kubectl get events --sort-by=.lastTimestamp` 与 Node 状态，再 Pod/容器」的集群内顺序，并保留 AKS 的「证据先于结论」契约 | 边界决定：平台侧那一层没有对应 skill，直述不覆盖比给半个 `az`/`gcloud` 流程更诚实 |
| C6 | 用 Helm 还是 Kustomize | 候选 1 两个 reference 平行给出；候选 11 只讲 Helm | 按「谁分发、谁消费」裁决：**要把配置分发给别人**（跨团队、公开 chart、需要版本化与依赖）用 Helm；**只在自己的环境之间改差异**用 Kustomize；同一个仓库里两个都用属反模式，除非是「用 Kustomize 后处理别人的 Helm 渲染输出」 | helm.sh/docs 定位 Helm 为 package manager，kustomize 文档定位为 template-free overlay。两边官方定位不冲突，冲突的是社区的「二选一」讨论；按用途而非偏好切分 |
| C7 | `latest` 标签 vs 语义化标签 vs digest | 候选 6/10/11：禁用 `latest`，用语义化版本标签。google/skills `assets/deployment.yaml`：直接用 `@sha256:` digest | 生产清单里引用 **digest**；语义化标签只作为人读的别名。理由：标签可变，同一个 `v1.2.3` 可以被重新推送，`imagePullPolicy: IfNotPresent` 下不同节点会跑到不同镜像 | 官方厂商（Google）的做法 > 社区的「不要 latest」；且 digest 是唯一能让 `kubectl rollout undo` 真正回到旧代码的引用方式 |

## 最终合入清单

| id | 上游 | relation | 贡献 |
|---|---|---|---|
| `lukasniessen-k8s` | LukasNiessen/kubernetes-skill | merged | 失效模式框架（不安全默认 / 资源饥饿 / 网络暴露 / 权限蔓延 / 脆弱滚动 / API 漂移）、探针语义的因果论证、QoS 与 CFS 节流立场、Helm/Kustomize 反模式清单 |
| `awesome-copilot` | github/awesome-copilot | merged | `instructions/devcontainers` 的 12 条 devcontainer 规则与 label 合并读法（骨架）；`instructions/kubernetes-manifests` 的 `app.kubernetes.io/*` 标签集与 securityContext 默认；另外三份作覆盖面清单 |
| `netresearch-docker` | netresearch/docker-development-skill | merged | 构建密钥泄漏的真实路径（provenance attestation）与取证命令、多阶段缓存顺序、bind mount 属主、镜像 pin 腐化。**内容为 CC-BY-SA-4.0：只取结构与清单语义，全部重写** |
| `google-skills` | google/skills | merged | 加固 Deployment 的完整字段集（`automountServiceAccountToken: false`、`seccompProfile: RuntimeDefault`、`readOnlyRootFilesystem`、`capabilities.drop: [ALL]`、digest 引用）与 `/healthz` `/readyz` 分离示例。GKE 专属部分已剥离 |
| `azure-aks-skills` | Azure/AKS-Skills | merged | 排障 workflow 的「只读默认 + 证据先于结论」契约与症状清单顺序。AKS/`az`/Azure 专属部分已剥离 |
| `impertio-docker` | Impertio-Studio/Docker-Claude-Skill-Package | merged | Dockerfile/Compose 评审的 PASS/FAIL 对照式清单结构 |
| `docker-docs` | docs.docker.com（docker/docs，Apache-2.0） | merged | 构建缓存失效规则、`RUN --mount=type=secret`、Compose `version:` obsolete、`compose watch`、多架构构建 |
| `kubernetes-docs` | kubernetes.io/docs（kubernetes/website，CC-BY-4.0） | merged | API 移除表、PSS 三档、QoS 与驱逐、探针字段语义、所有版本门的 feature-gate `stages` |
| `helm-docs` | helm.sh/docs（helm/helm-www，MIT） | merged | chart 结构与 values 约定、`helm template` / `--dry-run=server` 的差别 |
| `kustomize` | kubernetes-sigs/kustomize | merged | overlay/patch 语义、`kubectl kustomize` 与独立 CLI 的版本差 |
| `devcontainers-spec` | containers.dev（devcontainers/spec，CC-BY-4.0） | merged | devcontainer.json 属性表与 image-metadata label 合并语义（交叉校验 `awesome-copilot` 的规则） |
| `compose-spec` | compose-spec/compose-spec | merged | Compose 规范级事实：`profiles`、`develop.watch`、`healthcheck`、`depends_on.condition` |
| `bagelhole-devops` | BagelHole/DevOps-Security-Agent-Skills | reference | 仅用于覆盖面校验（Podman、registry、Helm 命令），未取任何内容 |

## 基线缺口

`uv run tools/run_evals.py containers --baseline`（`anthropic/claude-opus-5`，thinking=medium，
4 个场景全部 `skill_read=False`，`status=ok`）。

> 这一节跑过两轮：第一轮的 `answer.md` 随 `/tmp` 被系统清理而丢失，于是完整重跑了一遍。
> 下面记录的是**重跑那一轮**，判定依据是归档在 `/root/hs-evals-archive/baseline/<n>/answer.md`
> 的原文。两轮结论在场景 1 上逐条一致；场景 2、3 有出入，已按重跑结果修正（见每行的说明）。

**基线整体很强**——评测里模型有工具，场景 1 它自己造了等价夹具真跑了 `docker build` 并给出前后尺寸，
场景 2 把两次事故的因果链都指对了。所以缺口不是「大面积不会」，而是**八条具体的、错了会付代价的点**：

| 场景 | 未达成的行为 | 说明 |
|---|---|---|
| 1 Dockerfile | EB1：构建密钥的真实泄漏路径与正确检查 | 基线**认出了**泄漏并要求轮换，但把原因归给「`ENV` 固化进 build stage 镜像的 `Config.Env` 与 `docker history`」「BuildKit 缓存被 `--cache-to` 推出去」。这对本夹具（确实有 `ENV NPM_TOKEN=$NPM_TOKEN`）成立，却**漏掉了真正普遍的那条**：只写 `ARG`、不写 `ENV`、并当场 `rm` 掉产物时，`docker history` 与 `docker inspect .Config.Env` 都是干净的，密钥仍在 SLSA provenance attestation 里明文（本机实验 3 实测：history 命中 0、attestation 命中 1 个 blob、其中三处明文）。两轮基线都没提 provenance，也就都给不出 `docker buildx imagetools inspect --format '{{json .Provenance}}'` 这个能真正判定的检查 |
| 1 Dockerfile | EB8：基础镜像钉版本/摘要 | 两轮都只把 `node:20` 换成 `node:20-slim`，没有说 `node:20` 本身是浮动标签、需要钉到完整补丁版本或 digest。可复现性缺口 |
| 2 Deployment | EB8：securityContext 完整字段集与 restricted PSS | 重跑这一轮补上了 `seccompProfile: RuntimeDefault`（第一轮缺），但两轮都**没有 `automountServiceAccountToken: false`**，也都没有把这套字段与 restricted Pod Security Standard 对应起来——而「在 `enforce: restricted` 命名空间里会不会被拒」正是这份清单上线前唯一要回答的问题 |
| 2 Deployment | EB11：`requests == limits` 与 QoS 的取舍 | 基线直接删掉了 CPU limit，理由只有「预热期硬限流会拖长启动」。没有指出原配置 `cpu: 2` 请求等于上限使 Pod 落在 **Guaranteed** QoS，也没有说删掉之后 Pod 变成 Burstable、节点压力下的驱逐序位随之后移。它做对了动作，但没给出代价，读者无法判断该不该采纳 |
| 3 Compose | EB3：一次性任务的顺序 | 两轮都只把 migrate 放进 profile 让它不再默认启动，都**没有**用 `depends_on: migrate: condition: service_completed_successfully` 让 api 等待迁移完成。结果是把「每次都跑」改成了「永远不跑」，第一次 `up` 依然撞上未迁移的 schema |
| 3 Compose | EB6：`develop.watch` | 第一轮明确拒绝了 `action: sync`（理由「与 bind mount 重复」）且只对 `package.json` 写了 `rebuild`；重跑这一轮**连 `develop:` 段都没有**，完全停留在整目录 bind mount。两轮都没有意识到 sync 的意义正是**替掉**整目录 bind mount——bind mount 在 macOS/Windows 上是开发环境最大的 I/O 开销来源 |
| 3 Compose | EB8：发布到宿主机的 `5432` | 重跑这一轮完全没提（第一轮还改成了 `127.0.0.1:5432`）。容器之间靠服务名通信根本不需要 `ports:`，把开发库暴露到局域网是白送的风险 |
| 3 Compose | EB9：`POSTGRES_PASSWORD` 明文 | 两轮都一字未提。本地库无所谓，但评审时对明文凭据只字不提是坏习惯 |

达成的部分（skill 不需要重复教的）：多阶段结构、`COPY` 顺序与缓存链、`.dockerignore`、非 root、
exec 形式 CMD 与 SIGTERM、三种探针的语义与启动预算、PDB 预算为零导致 drain 挂死、
已移除的 API 版本与 v1 Ingress 的结构变化、缺失的 Service、明文 Secret、`latest` 标签、
滚动更新参数、`depends_on` 短语法只等容器创建、匿名卷遮蔽 node_modules、profiles、
以及负例里 `count` 对 `for_each` 的完整裁决与 `moved` 块。

## 评测结果

两次运行都用 `tools/run_evals.py` 的默认模型与思考档（未传 `--model` / `--thinking`）。
`status` 全部 `ok`。答复原文归档在 `/root/hs-evals-archive/{baseline,skill}/<n>/answer.md`。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 1 Dockerfile 瘦身与构建密钥 | claude-opus-5:medium | 无（baseline） | false | 8 条中 **6 条**：EB2 secret mount、EB3 缓存层序、EB4 `.dockerignore`、EB5 运行时基础镜像与只拷产物、EB6 非 root、EB7 exec 形式 CMD 与 SIGTERM | 未达成 EB1（把泄漏归因为 `ENV`→`Config.Env`/`docker history`/BuildKit 缓存，没提 provenance attestation，因此给不出能判定的取证命令）与 EB8（只换 slim，未钉补丁版本或 digest） |
| 1 Dockerfile 瘦身与构建密钥 | claude-opus-5:medium | 有 skill | true | **8/8** | EB1 填补：直接写「多阶段 + `rm -f .npmrc` 都救不了：BuildKit 把 `--build-arg` 原样写进 provenance attestation」，并跑了 `docker buildx imagetools inspect … --format '{{json .Provenance}}' \| grep -oE 'npm_…'`，old=1 / new=0，同时点明 `docker history` 与 `inspect .Config.Env` **都是干净的**。EB8 填补：base 钉成 `node:20.20.2-bookworm-slim@sha256:…`。额外收获：自己发现 `RUN echo "…${NPM_TOKEN}…"` 把 token 打进了构建日志，并把 `docker buildx build --check` 设为 CI gate |
| 2 Deployment 评审 | claude-opus-5:medium | 无（baseline） | false | 11 条中 **9 条**：EB1 liveness 依赖、EB2 startupProbe、EB3 探针计时、EB4 PDB 零预算、EB5 已移除 API 与 v1 结构变化、EB6 缺失 Service、EB7 Secret、EB9 digest、EB10 滚动参数 | 未达成 EB8（补了 `seccompProfile` 但**缺 `automountServiceAccountToken: false`**，也没与 restricted PSS 对应）与 EB11（删了 CPU limit 却没说原配置是 Guaranteed QoS、也没说删掉后变 Burstable 的代价）。另有一处事实错误：称 `preStop.sleep`「1.33 起 GA」，实际 1.30 默认开启、1.34 stable |
| 2 Deployment 评审 | claude-opus-5:medium | 有 skill | true | **11/11** | EB8 填补：「已按 restricted PSS 补齐（`runAsNonRoot`、`allowPrivilegeEscalation: false`、`drop: [ALL]`、`RuntimeDefault`），另加 `readOnlyRootFilesystem` + `/tmp` emptyDir 和 `automountServiceAccountToken: false`」。EB11 填补：「资源没动（requests == limits → Guaranteed）。没有实测数据就不该改 QoS 档位。代价要知道：CPU 限额是 CFS 配额，节点空闲时也会在每个调度窗口被节流」。额外：跑了 kubeconform 1.34.0 `-strict`，修改前 `Valid: 1, Errors: 2`、修改后 `Valid: 4, Errors: 0`；补了 `unhealthyPodEvictionPolicy: AlwaysAllow`；并指出该命名空间没有 NetworkPolicy 属「未分段」。EB9 按「不编造 digest、保留原行 + 阻断性注释」处理，判为达成 |
| 3 Compose 开发环境 | claude-opus-5:medium | 无（baseline） | false | 9 条中 **5 条**：EB1 删 `version:`、EB2 长式 `depends_on` + `pg_isready -U -d`、EB4 profiles、EB5 匿名卷遮蔽、EB7 钉 redis 标签 | 未达成 EB3（只加 profile，没有 `service_completed_successfully`，把「每次都跑」改成了「永远不跑」）、EB6（连 `develop:` 段都没有）、EB8（未提发布到宿主机的 5432）、EB9（未提明文口令） |
| 3 Compose 开发环境 | claude-opus-5:medium | 有 skill | true | **9/9**（EB5 以文档化的逃生口形式达成，见备注） | EB3 填补：`condition: service_completed_successfully` + `required: false`，并明说「只加 profiles 会把『每次都跑』变成『永远不跑』——那是另一个 bug」。EB6 填补：整段 `develop.watch`，源码 `sync`、lockfile `rebuild`，日常命令改 `docker compose watch`。EB8 填补：`127.0.0.1:5432:5432` 并说明服务间通信走服务名。EB9 填补：「明文口令 `app` 保留——一次性本地库，可接受；但这份文件不得复用于任何共享环境」。EB5 它没有用匿名卷，而是**删掉整目录 bind mount 改用 watch + `ignore: node_modules/`**，并逐条比较了匿名卷方案的代价（首次填充后持久化、换依赖要 `down -v`）——这正是 SKILL.md Core rule 14 给的首选方案，问题本身已解决，判为达成 |
| 4 负例：Terraform `count` vs `for_each` | claude-opus-5:medium | 无（baseline） | **false** | 5/5 | 纯 IaC 作答：`for_each` + map、地址稳定性、模块抽取、`moved` 块，无任何容器内容 |
| 4 负例：Terraform `count` vs `for_each` | claude-opus-5:medium | 有 skill | **false** | 5/5 | **负例通过**：`containers` skill 未被加载。作答仍是纯 IaC，且额外指出 module 的 `for_each` 实例无法各自绑定 provider alias。description 的否定边界（`Do not use for Terraform, OpenTofu or other infrastructure-as-code syntax…`）未被误触发，无需调整 |

结论：**通过**。四个场景 26 条 `expected_behavior`（正例 8+11+9）中，基线未达成 8 条，
有 skill 时这 8 条**全部达成**，正例三场 `skill_read=true`、负例 `skill_read=false`。
填补的缺口集中在三处，都是「不知道就会错」而不是「知道但写漏」：
构建密钥的真实泄漏路径与取证命令（provenance attestation）、
restricted PSS 的完整字段集与 QoS 取舍的代价、
Compose 一次性任务的「profiles + `service_completed_successfully` 两手都要」与 `develop.watch`。
另外有 skill 的三场都自发跑了本 skill 写的验证门
（`buildx imagetools inspect .Provenance`、`kubeconform -strict` 前后对比、`compose config` + `--dry-run`），
基线三场只有场景 1 自发做了测量。

## 本机实验（写正文前做的验证）

全部在本机真实执行，并在会话被额度中断、`/tmp` 被系统清理之后**从零重跑了一遍**（`docker builder
prune -af` 清空构建缓存后重建），两次结果逐字一致；下面记录的是重跑那一轮。
工作目录 `/root/hs-containers-build`（Node 22 + express 的最小应用，
仓库里额外放了 `node_modules/junk/big.bin` 40 MB 与 `.git/pack.bin` 30 MB 模拟真实上下文）。
环境：Docker Engine **29.7.2**、Helm **v4.2.2**、kubectl **v1.34.0**（本机原本没有 kubectl，
从 `dl.k8s.io/release/v1.34.0` 下载到 `/root/bin`）、kubeconform 走容器
`ghcr.io/yannh/kubeconform:latest`。
**本机没有 Kubernetes 集群**，所有 K8s 验证都是离线的（见实验 4）。

### 实验 1 — 多阶段瘦身，前后尺寸对比（真的构建了）

```bash
docker build -f Dockerfile.before -t hs-demo:before .   # 单阶段 node:22，COPY . . → npm install，无 .dockerignore
docker build -f Dockerfile.after  -t hs-demo:after  .   # 三阶段 node:22-bookworm-slim，lockfile 先行，USER node
docker images hs-demo --format '{{.Tag}}\t{{.Size}}'
```

```
after   230MB
before  1.3GB
```

**1.3 GB → 230 MB（−82%）**。`docker history hs-demo:before` 指出了钱花在哪：

```
61.7MB  RUN apt-get update && apt-get install -y curl vim procps
32MB    RUN npm install
73.5MB  COPY . .            <- 正好是 node_modules/junk 的 40MB + .git 的 30MB，缺 .dockerignore 的代价
```

构建器还自动报了一条：`JSONArgsRecommended: JSON arguments recommended for CMD to prevent
unintended behavior related to OS signals (line 9)`——即 `CMD npm start` 的 shell 形式不转发 SIGTERM。
这条进了正文 Core rules。

### 实验 2 — 层顺序对缓存的影响（改一行源码后重建）

```bash
echo "// touch" >> src/index.js
docker build -f Dockerfile.before ...   # COPY . . 未命中 → npm install、npm run build、apt-get 全部重跑
docker build -f Dockerfile.after  ...   # deps/build 两个阶段的 npm ci 均 CACHED，只重跑 COPY src + npm run build
```

`before` 的输出里 `#7 [4/6] RUN npm install`、`#9 [6/6] RUN apt-get …` 都没有 `CACHED` 标记；
`after` 的 `#9 [build 4/6] RUN --mount=type=cache … npm ci` 与 `#12 [deps 4/4] … npm ci --omit=dev` 都是 `CACHED`。

### 实验 3 — `--build-arg` 传密钥确实会泄漏（推翻候选 6 的说法，坐实冲突 C2）

构造一个「密钥只出现在 builder 阶段、且当场 `rm -f .npmrc`」的最有利情况：

```bash
docker buildx build --builder hsprov -f Dockerfile.leak \
  --build-arg NPM_TOKEN=glpat-SECRETVALUE1234567890 \
  --provenance=mode=max --output type=oci,dest=leak.tar .
tar -xf leak.tar -C leakx && grep -rl "glpat-SECRETVALUE1234567890" leakx
# leakx/blobs/sha256/3aa761ff2e5d…
```

命中的 blob 就是 provenance attestation，明文片段：

```
{"frontend":"dockerfile.v0","args":{"build-arg:NPM_TOKEN":"glpat-SECRETVALUE1234567890"},…
…"request":{"args":{"build-arg:NPM_TOKEN":"glpat-SECRETVALUE1234567890"}}}…
…"NODE_VERSION=22.23.2","YARN_VERSION=1.22.22","NPM_TOKEN=glpat-SECRETVALUE1234567890"…
```

同一个镜像用大家惯用的检查看：

```bash
docker history --no-trunc hs-demo:leak | grep -c glpat          # 0
docker inspect hs-demo:leak --format '{{json .Config.Env}}' | grep -c glpat   # 0
```

**`docker history` 与 `docker inspect` 都是 0，attestation 里是明文。** 这就是「多阶段能防构建密钥」错在哪。
改用 secret mount 后同样的检查：

```bash
NPM_TOKEN=glpat-… docker buildx build -f Dockerfile.nosecret --secret id=npmtoken,env=NPM_TOKEN \
  --provenance=mode=max --output type=oci,dest=nosecret.tar .
grep -rl "glpat-SECRETVALUE1234567890" /tmp/nosecx | wc -l    # 0
```

另外 BuildKit 自己会警告 `SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for
sensitive data (ARG "NPM_TOKEN")`——这条 lint 值得写进正文的验证门。

### 实验 4 — 离线校验 K8s 清单：`--dry-run=client` 不是离线校验（重要发现）

```bash
kubectl apply --dry-run=client -f evals/files/deployment.yaml
# error: failed to download openapi: the server could not find the requested resource
kubectl apply --dry-run=client --validate=false -f fixed.yaml
# couldn't get current server API group list … unable to recognize "fixed.yaml"
```

`--dry-run=client` **仍然要连 API server**（先取 OpenAPI 做校验，加了 `--validate=false` 还要做 RESTMapper 发现），
没有集群时两条都失败。真正能离线跑的是：

```bash
kubectl create deployment demo --image=nginx:1.29 --dry-run=client -o yaml   # OK，纯本地生成
kubectl kustomize ./overlay                                                   # OK，纯本地渲染
helm template rel ./chart                                                     # OK，纯本地渲染
helm lint ./chart                                                             # OK
```

这条修正了候选 1 与候选 3 都推荐的 `kubectl apply --dry-run=client` 作为「校验门」的说法，写进正文。

### 实验 5 — 用 kubeconform 证明夹具里的两个 API 版本确实已被移除

```bash
docker run --rm -i ghcr.io/yannh/kubeconform:latest -kubernetes-version 1.34.0 -summary -verbose - \
  < skills/containers/evals/files/deployment.yaml
```

```
stdin - PodDisruptionBudget checkout-pdb failed validation: could not find schema for PodDisruptionBudget
stdin - Ingress checkout failed validation: could not find schema for Ingress
stdin - Deployment checkout is valid
Summary: 3 resources found parsing stdin - Valid: 1, Invalid: 0, Errors: 2, Skipped: 0
```

换成 `policy/v1` + `networking.k8s.io/v1`（补 `pathType`、`service.name`/`service.port.number`、
`ingressClassName`）后：`Valid: 2, Invalid: 0, Errors: 0`。

Helm 侧的完整门也跑通了：`helm template rel ./hchart | kubeconform -kubernetes-version 1.34.0 -strict -` → `Valid: 4`。

### 实验 6 — Helm 版本现状

`helm version --short` → `v4.2.2+gb05881c`；`gh api repos/helm/helm/releases` 最新为 **v4.3.0**（v3 线仍在发 v3.22.0）。
helm-www 的发布博客写明 Helm 4 于 2025-11-12 发布，Helm 3 的**缺陷修复已于 2026-07-08 结束**、
安全修复到 2026-11-11 为止；Helm 4 新增服务端 apply、基于 kstatus 的等待、post-renderer 改为插件。
正文因此按 Helm 4 写，并给 Helm 3 的差异一句话。

## 备注

### 许可注意

- **netresearch/docker-development-skill**：GitHub API 报 `NOASSERTION`，原因是仓根同时有
  `LICENSE-MIT` 与 `LICENSE-CC-BY-SA-4.0`。实读 README 的 License 节：**代码 MIT，内容
  （skill 定义、文档、references）CC-BY-SA-4.0**。按仓库规则按 CC-BY-SA 处理：只取结构与清单语义，
  全部用自己的话重写；其最核心的 provenance 泄漏结论在写进正文之前**本机独立复现了一遍**（实验 3），
  因此正文里的那段是自己的实验记录而不是转述。`SOURCES.yaml` 的 `license` 填 `CC-BY-SA-4.0`。
- **kubernetes.io/docs**（kubernetes/website）：CC-BY-4.0 → merged，`notes` 里写了署名
  （"portions derived from the Kubernetes documentation by the Kubernetes Authors, used under CC-BY-4.0"）。
- **containers.dev**（devcontainers/spec）：CC-BY-4.0 → merged + 署名。该仓 2026-03-20 最后推送，
  超出社区上游的 6 个月新鲜度窗口，但它是规范本体、所用条目内容未变，故新鲜度给 1 分而不是 REJECT，
  并在 `notes` 写明复核结论。
- **docs.docker.com**（docker/docs）：实读 `LICENSE` 首行确认是 **Apache-2.0**，所以是 merged 不是 reference。
  顺带确认了 **Docker 官方组织没有 agent-skills 仓**（`gh api orgs/docker/repos?per_page=100` 全量列过），
  因此 `containers` 不适用「官方厂商特例」，走的是常规判据。
- **helm.sh/docs**：源仓库 `helm/helm-www` 是 MIT（不是 `helm/helm` 的 Apache-2.0），已分别核对。
- GPL/AGPL/LGPL/专有上游：本 skill 一个都没有采用，`SOURCES.yaml` 里也就没有这类条目。
  唯一的 `relation: reference` 是 `bagelhole-devops`，因为它确实只用来做覆盖面校验，未取任何内容。

### GKE / AKS 专属内容是怎么剥离的

**google/skills `gke-app-onboarding`**：删掉 `us-docker.pkg.dev/<PROJECT>/<REPO>/…` 形式的
Artifact Registry 镜像路径（正文改为占位 registry + digest）、`gcloud` 与
`pack build --builder gcr.io/buildpacks/builder` 的 Buildpacks 路线、Cloud Logging 采集约定、
Workload Identity、Autopilot 的资源约束，以及 SKILL.md 顶部
`> **MCP Tools:** apply_k8s_manifest, get_k8s_resource, …` 的工具绑定块与
`metadata.category: Containers` 这个非白名单 frontmatter 键。
**保留的只有在任何合规集群上都成立的部分**：`assets/deployment.yaml` 的加固字段集
（`automountServiceAccountToken: false`、`runAsNonRoot` + 数值 uid、`seccompProfile: RuntimeDefault`、
`readOnlyRootFilesystem`、`capabilities.drop: [ALL]`、按 digest 引用镜像）与 `/healthz` `/readyz` 分离。

**Azure/AKS-Skills `aks-troubleshooting`**：删掉全部 `az aks` 命令、AppLens 与 Resource Health 检测器、
「先发现 Azure MCP 能力再决定用哪个」的整段工具协商、Azure CNI、SNAT 端口耗尽、AGIC、
Entra Workload ID、spot 驱逐与可用区再平衡。它的「先取平台侧状态、再取集群内状态」的顺序思想被
**改写**为纯集群内的顺序（先 events 与 Node，再 Pod 与容器），因为平台层被本 skill 明确划出边界。
保留下来的是两条契约——「未被要求前只读」「先引证据再下根因」——与症状清单本身。

### 是否真的构建了镜像

是。`docker build` / `docker buildx build` 共跑了 7 次（before、after、两次源码改动后的增量重建、
leak 的 OCI 导出、nosecret 的 OCI 导出、leak 再用普通 `docker build` 出一份好查 `docker history`），
镜像尺寸 **1.3 GB → 230 MB（−82%）**，`docker history` 逐层归因见实验 1。
另外真跑了 buildx provenance 导出与解包 grep（实验 3）、kubeconform 校验（实验 5）、
`helm template | kubeconform`（实验 5）、kubectl 的离线能力边界测试（实验 4）。
**没有** Kubernetes 集群，所以 `--dry-run=server`、实际滚动更新、PDB 阻塞 drain 这三类行为属未实验验证，
正文中相关结论标的是 `[official]` 而非 `[verified]`。

### 未来同步时要盯的上游

- `LukasNiessen/kubernetes-skill`：更新频繁且会新增 `references/conditional/*`。同步时注意**不要**把
  新增的 EKS/GKE/AKS/OpenShift/GitOps/observability 条件文件拉进来，它们在边界之外。
- `github/awesome-copilot`：`instructions/devcontainers.instructions.md` 是本 skill devcontainer 章的骨架，
  它改动就要跟。另外三份泛化 instruction 只作覆盖面清单，改了不必跟。
- `kubernetes/website`：每个 Kubernetes 小版本都要复核两处——`deprecation-guide.md` 的移除表，
  和本 skill 引用的每个 feature gate 的 `stages`（目前：SidecarContainers、InPlacePodVerticalScaling、
  UserNamespacesSupport、PodLevelResources、PodLifecycleSleepAction、PDBUnhealthyPodEvictionPolicy）。
- `helm/helm`：Helm 3 的安全修复 2026-11-11 到期，到期后正文里「Helm 3 仍在维护」的措辞要改。

### 放弃的方向

- **不写 `scripts/`**。想过写一个「渲染 + kubeconform + 报告」的包装脚本，但那只是
  `helm template | kubeconform` 与 `kubectl kustomize | kubeconform` 的三行封装，
  按标准第 5 节属于没有可运行价值的脚手架，不如把命令直接写进 workflow 的验证门。
- **不写 Podman/Buildah 专章**。命令面与 Docker 高度重合，真正的差异（rootless 默认、
  没有守护进程、`podman generate kube`）不足以支撑一章，需要时在 Dockerfile 章里一句话即可。
- **不覆盖 Gateway API 细节**。只在 Ingress 一节写了「它是标准化的后继方向」，
  展开需要控制器实现层的知识，且与未来可能的网络类 skill 边界未定。

---

## GPU 扩展（2026-09-15）

用户在 `model-serving` 立项过程中追加要求：「container skill 也需要有与 GPU 相关的内容」。
本节记录这次扩展的调研、分界与基线，正文落点是新增 `references/kubernetes-gpu.md`
+ 一个 workflow + 一行 topic router。

### 为什么不新增 core rule

`## Core rules` 已有 25 条，正好是 `docs/skill-standard.md` 第 3 节规定的上限。
逐条核对 25 条后确认：**没有任何一条与 GPU 事实矛盾，也没有任何一条弱到该被 GPU 规则替换**。

- Rule 1（先确定版本再套版本门）对 GPU 尤其成立，且 GPU 还多两个版本轴（驱动、插件），
  这属于 reference 内容而非新 rule。
- Rule 8（按 digest 固定镜像）与 CUDA 镜像的强耦合同向，不需要 GPU 变体。
- Rule 17（总设内存 limit / CPU 尽量不限）与 GPU 工作负载不冲突。
- Rule 18（PDB 与 drain 卡死）与驱动升级的 `maxUnavailable` 把 cordon 计入是不同机制，
  但结论同向，reference 引用即可。
- Rule 25（从对象诊断而非症状名）正是 GPU 诊断章的组织原则。

结论：core rules 保持 25 条不变。

### 与 `model-serving` 的分界

两边 SKILL.md 写入字面一致的分界句（英文原文照抄，见两边 `## Scope`）：

> Getting a GPU into a container — device plugin resource names, MIG and time-slicing,
> driver and CUDA compatibility, topology-aware scheduling — belongs to the `containers`
> skill; what a serving process does with the GPU once it has one — KV cache sizing,
> batching, parallelism, benchmarking and scaling signals — belongs to the `model-serving`
> skill.

`containers` 侧只写到「Pod 拿到了正确数量与正确形态的设备」为止，验证门是
`nvidia-smi -L` 输出正确。刻意**不**提取而移交对面的内容：`ComputeDomain` 之上的并行策略、
NCCL 调优参数取值、按 GPU 利用率扩缩的对错、`gpu_count × num_nodes` 的容量规划方法论。

### 版本事实纠偏（写正文前必须定的）

调研时的先验判断有两处错，已按官方文档更正：

| 先验 | 实际 | 依据 |
|---|---|---|
| DRA 在 1.37 仍是 alpha/beta | **Stable since v1.35**，gate `DynamicResourceAllocation` 已锁定（显式设置被忽略且不报错）；API 组是 `resource.k8s.io/v1`，不是 `v1alpha3`/`v1beta1` | kubernetes.io DRA 概念页 |
| DRA 文档在 `/concepts/scheduling-eviction/` | 已迁至 `/concepts/resource-management/dynamic-resource-allocation/` | 同上（旧链接重定向） |
| `nvidia.com/gpu` 写进 `requests` 会被静默同值化 | 静默同值化只发生在**只写 limits** 的方向（Kubernetes 把 limit 复制为 request）；**只写 requests 不写 limits 是非法的**；两边都写则必须相等 | kubernetes.io `scheduling-gpus` |

其余需要写进正文的版本门：Device taints/`DeviceTaintRule` **Stable since 1.37**；
prioritized list **Stable since 1.36**；`DRAPartitionableDevices` 与 consumable capacity
**1.36 beta 默认开**；`DRADeviceCompatibilityGroups` **1.37 alpha 默认关**；
`DRAWorkloadResourceClaims` **1.37 beta 默认关**；`allocatedResourcesStatus` **1.36 beta**；
CDI 设备名处理 **1.31 GA**。

NVIDIA 的 DRA 驱动仓库**已迁到 `kubernetes-sigs/dra-driver-nvidia-gpu`**，其中
`compute-domain-kubelet-plugin`（多节点 NVLink 的 ComputeDomain）是官方支持的，而
`gpu-kubelet-plugin`（用 DRA 分配 GPU）**Helm chart 默认禁用、尚未正式支持**——
写「用 DRA 分配 GPU」的建议时必须带这个 caveat。

### 上游来源

全部为 `relation: reference`（只阅读对齐，未复制内容）。Kubernetes 官方文档、
NVIDIA k8s-device-plugin、GPU Operator 文档、Container Toolkit 文档、
CUDA Compatibility 文档、ROCm k8s-device-plugin、`kubernetes-sigs/dra-driver-nvidia-gpu`。
repo 型来源的 HEAD commit 已核实并写入 `SOURCES.yaml`。

两个 skill 型候选经实读后判为**不可合入**，留档以免后续批次重复讨论：

| 候选 | 判定 | 理由 |
|---|---|---|
| `NVIDIA/skills` `tao-run-on-kubernetes` | reference，不 merge | 95% 是 TAO SDK 的 Python API 契约与 NGC 凭据；可提取的只有 Pending 事件原文、allocatable 探针命令、Indexed Job + headless Service 的 rendezvous 构造 |
| `NVIDIA/skills` `tao-setup-nvidia-gpu-host` | reference，不 merge | 主体是宿主机发行版包管理安装流程，属节点准备而非本 skill Scope。它给的最小栈（driver ≥580 / CUDA ≥13.0 / Toolkit ≥1.19.0）是 **TAO 自己的要求**，**不得**写成普适下限 |
| `google/skills` `gke-compute-classes` | reference，不 merge | 整份是 GKE ComputeClass/CapacityQuota 的 CRD 语义与 GKE 版本门，正落在本 skill 明确排除的「托管集群控制面」，应归 `gcp`。其中「GKE 自动给 GPU 节点打 `nvidia.com/gpu:NoSchedule`」是 GKE 特有行为，**不得**写成通用事实。只取「加速器启动延迟严重」一条 |

### 与既有 reference 的重叠处理

| 既有内容 | 处理 |
|---|---|
| `kubernetes-resources.md` 的 requests/limits 与 QoS | **引用不重写**。但要补一条它没覆盖的：GPU Pod 即使 `nvidia.com/gpu` 两边相等，**QoS 类仍由 CPU/内存决定**，只写了 GPU limit 的 Pod 仍可能是 Burstable 甚至 BestEffort，节点压力下先被驱逐 |
| `kubernetes-resources.md:223-225`「容忍不等于吸引…GPU 工作负载落到 CPU 节点」 | **不复述**。GPU 侧的增量是「用什么标签做那个 affinity」：NFD/GFD 标签目录、`Gt` 数值比较，以及 **MIG single 策略会把 `gpu.product` 改写成 `…-MIG-1g.10gb` 从而让按型号写死的 affinity 失配** |
| `troubleshooting.md` 的 Pending 原因表 | 该表已含 `Insufficient cpu/memory` 与 untolerated taint（且已点名 GPU 池），**无需改动**；GPU reference 补三条它覆盖不到的：allocatable 里根本没有该资源 key、`Capacity` 8 / `Allocatable` 5 的差值、`UnexpectedAdmissionError`（既非 Pending 也非 CrashLoopBackOff 且不自愈）。另在该表加一行交叉引用 |
| `kubernetes-workloads.md` 的 Probes | **只补预算**，不重讲三探针语义 |

### 基线缺口

新增第 4 个场景（GPU 推理 Deployment + Dockerfile 双文件评审）。
基线：`uv run tools/run_evals.py containers --baseline --only 4`，
Claude Opus 5 / thinking=medium，`status=ok`、`skill_read=false`。

**夹具修正记录**：第一版夹具把 GPU 只写在 `requests`，同时让 query 声称出现了
`UnexpectedAdmissionError`。这是因果矛盾——只写 requests 的 Pod 会被 API server 直接拒绝，
根本到不了 kubelet 调用 device plugin `Allocate` 的阶段；而合法的 GPU 请求本身就是调度约束，
也不会「因为缺 affinity 而落到没有 GPU 的节点」。已把 query 改写为显式的三步时间线
（apply 被拒 → 补上 limits 后 admission 失败 → 改成 1 后 Running 但容器内无设备），
并把「落到 CPU 节点」改为异构池下的型号/显存选择。第一版基线已作废重跑。

基线 13 条 `expected_behavior`：**达成 6、部分 6、未达成 1**。

| 未达成/部分的行为 | 说明 |
|---|---|
| **`renameByDefault` / `.shared` 资源名（未达成）** | 完全未提。基线改用 `nvidia.com/gpu.sharing-strategy` 标签排除共享池（也是正确做法），但没意识到共享池可以把资源名改成 `nvidia.com/gpu.shared`，也没提 mixed MIG 策略下的 `nvidia.com/mig-<n>g.<m>gb` |
| time-slicing 的故障域共享（部分） | 多处正确说了「不做显存隔离」，但没说**故障域也共享**（同卡一个容器崩会带走全部），也没提 MIG（Ampere+ 硬件分区）与 MPS 作为替代 |
| `UnexpectedAdmissionError` 的机制（部分） | 基线给了一条很深刻的反向洞察——「把 `failRequestsGreaterThanOne` 关掉会让 Pod 顺利启动但只拿到同一张卡的两个引用，故障从明确的 admission 错误变成隐蔽的显存 OOM」——但没解释报错本身的机制，也没说 **Pod 不自愈必须手工删除**、没说该开关默认 `false` |
| 扩展资源的其余约束（部分） | 正确写出「只写 limits，kubelet 自动令 requests == limits；显式写 requests 且与 limits 不等会被 API server 拒绝」；但没提整数、不可超卖、不可跨同 Pod 的两个容器共享 |
| `NVIDIA_DRIVER_CAPABILITIES` 缺 `compute` 的诊断症状（部分） | 显式设了 `compute,utility`（正确），但没描述「`nvidia-smi` 能跑而框架看不到卡」这个诊断入口 |
| CUDA/驱动不匹配的报错与逃生阀（部分） | 给出驱动下限 **580.65.06**（比调研记录的 580 更精确）并选择降到 CUDA 12.4；但没提 `cudaGetDeviceCount returned 3 -> initialization error` 这个实际报错文本，也没提 forward-compatibility 包这条路 |
| RuntimeClass handler 不存在的后果（部分） | 正确加了 `runtimeClassName: nvidia` 并把「缺它」与「slim 基础镜像丢 ENV」并列为两个独立根因（正是期望的）；但没提 handler 不存在会让 Pod 直接进 `Failed` 终态 |

**基线超出预期之处**（如实记录，避免正文重复写模型已会的）：

- 抓到了夹具里我自己没注意到的真实缺陷：`models-pvc` 若是 `ReadWriteOnce`，
  4 个副本落在不同节点时无法同时挂载，必须 `ReadOnlyMany`/`ReadWriteMany`。
- 指出「40GB/副本」这个约束**无法在 Kubernetes 资源模型里表达**，只能靠 nodeAffinity
  翻译成「整张 H100」——这是对扩展资源表达力边界的准确认识。
- Dockerfile 的修法完整且理由正确：build/runtime 两段都用 CUDA 镜像、注释写明
  「不安装任何 nvidia 驱动包，内核驱动与 libcuda 由宿主经 nvidia-container-runtime 注入」、
  runtime stage 必须是 CUDA runtime 镜像否则 toolkit 不注入 compute 能力所需的库。

**评测设计的一处教训**：query 结尾写「What is wrong and what do we change?」导致基线
直接改文件 + 只在 `answer.md` 里写「还要改的两处」，主体诊断落在 workspace 的文件注释里。
判定时必须连 workspace 产物一起读（`result.json` 的 `workspace` 字段），
否则会把已达成误判为未达成。现有场景 2 的措辞「Review deployment.yaml before we roll it out」
更能稳定引出评审文本，后续新增 review 型场景应沿用该措辞。

### 评测结果

被测模型在本轮中途统一改为 `openai/gpt-5.6-sol --thinking medium`（见
`research/model-serving.md` 第二轮说明），两侧基线用同一模型重跑；Opus 5 那行只作背景。

| 场景 | 模型 | 有/无 skill | skill_read | 达成的 expected_behavior | 备注 |
|---|---|---|---|---|---|
| 4（GPU） | anthropic/claude-opus-5 medium | 无（基线） | false | 6/13 达成、6 部分、1 未达成 | 背景，不参与增益判定；判定需连 workspace 产物一起读 |
| 4（GPU） | openai/gpt-5.6-sol medium | 无（基线） | false | **3/13 达成、6 部分、4 未达成** | 见下表 |
| 4（GPU） | openai/gpt-5.6-sol medium | 有 skill | **true** | **6/13 达成、5 部分、2 未达成** | 见「有 skill 对照」 |

`gpt-5.6-sol` 基线逐条（`/tmp/hs-gpu-sol/.../baseline/4/answer.md`）：

| EB | 判定 | 依据 |
|---|---|---|
| 1 Capacity 80 = 副本乘数 | 达成 | 「不代表突然拥有 80 张 GPU，而是设备插件将共享副本计入扩展资源容量」+「调度器只看见整数资源，没有看见背后的物理显存」 |
| 2 时间切片无隔离 + MIG/MPS | 部分 | 有「不提供显存隔离或预留」与 MIG 方案；**缺故障域**（一个容器崩则同卡全崩）与 **MPS 完全未提** |
| 3 共享请求上限 | 部分 | 说了「单次请求最大只能是 1」「Allocate 阶段拒绝」；**缺 Pod 不自愈须手删**、**缺 `failRequestsGreaterThanOne` 默认 false** |
| 4 GPU 必须在 limits | 部分 | 只说「两者必须相等」；**没说只写 `limits` 会自动复制而只写 `requests` 非法**，也缺整数/不可超卖/不可跨容器共享 |
| 5 `renameByDefault` 改名 | **未达成** | 完全未提 `nvidia.com/gpu.shared`，也未提错名 = 永久 Pending 无错误 |
| 6 删镜像内驱动 | 达成 | 「驱动属于宿主机，并且该构建阶段随后被丢弃」 |
| 7 runtime stage 丢 NVIDIA 变量 | 部分 | 归因为「没有 CUDA 用户态运行库」，**未点明丢失 `NVIDIA_VISIBLE_DEVICES`**，也未说 unset 时 runtime 退化为 runc |
| 8 只有 `utility` 的症状 | **未达成** | 未提 `nvidia-smi` 可用而框架看不到设备这一诊断 |
| 9 CUDA/驱动版本失配 | 部分 | 指出 CUDA 13 与 550 代际不匹配并换 12.4.1；**缺 580/525 地板值**、**缺 `cudaGetDeviceCount returned 3` 症状**、缺另两条修法 |
| 10 两个独立原因 | 部分 | 两个原因都给了且都修；**缺** RuntimeClass 不存在会直接 `Failed` 的反面辨析 |
| 11 异构池节点选择 | 达成 | 正是 `nvidia.com/gpu.memory` + `Gt` + `40959`，未重复泛化 taint 建议 |
| 12 startup probe | **未达成** | 探针完全未提；readiness 约 25 s 的预算问题未触及 |
| 13 `:latest` 换 digest | **未达成** | 只钉了基础镜像 `12.4.1`，部署镜像的 `:latest` 未处理 |

缺口与 `references/kubernetes-gpu.md` 的对应：EB5 -> 「Sharing a GPU」的
`renameByDefault`；EB8 -> 「The variables that decide what the container sees」把
「`nvidia-smi` 能用但框架看不到设备」直接写成诊断结论；EB12 -> 「Startup budget」
（只给预算定法，探针语义仍留在 `kubernetes-workloads.md`）；EB13 已由既有
`image-security.md` 覆盖，不重复。EB2/3/4/7/9/10 的缺失半边分别落在
「Sharing a GPU」的故障域与 MPS 行、`failRequestsGreaterThanOne` 段、
「The resource contract」、`NVIDIA_VISIBLE_DEVICES` 取值表、
「Driver and CUDA version coupling」的地板表与诊断表。
### 有 skill 对照（`/tmp/hs-gpu-skill/.../skill/4/`，`skill_read=true`）

| EB | 基线 -> 有 skill | 变化依据 |
|---|---|---|
| 1 Capacity 80 | 达成 -> 达成 | 有 skill 版把它算成「8 张 × 10 份」并补上「多个份额可能仍指向同一张物理卡」 |
| 2 无隔离 + MIG/MPS | 部分 -> 部分 | 补齐了「不提供显存、故障或性能隔离」三项（基线只有显存）；**MPS 仍未提** |
| 3 共享请求上限 | 部分 -> **达成** | 点名 `failRequestsGreaterThanOne` 并写出「不会自动恢复，删除 Pod 是必要操作」 |
| 4 GPU 必须在 limits | 部分 -> **达成** | 正是基线缺的那半句：「不能只写 `requests`；可以只写 `limits`」+「Kubernetes 会自动把该值复制为 request」 |
| 5 `renameByDefault` | 未达成 -> 部分 | 要求「以 `node.status.allocatable` 中的实际资源名为准」并给出 MIG 资源名，但仍未点名 `renameByDefault` / `.shared`，也未说错名是静默 Pending |
| 6 删镜像内驱动 | 达成 -> 达成 | 补上「内核驱动必须来自节点，用户态驱动组件由 NVIDIA runtime 注入」 |
| 7 runtime stage 丢变量 | 部分 -> 部分 | 「由普通 runtime 创建，没有设备、驱动库或工具注入」等于说出了 runc 语义，但仍未点名两个环境变量 |
| 8 显式设置两个环境变量（判据已改写） | 未达成 -> **未达成** | 连 workspace 产物一起查：`gpu-rerank.Dockerfile` 里没有 `NVIDIA_VISIBLE_DEVICES` / `NVIDIA_DRIVER_CAPABILITIES`，仍依赖基础镜像携带 |
| 9 CUDA/驱动版本 | 部分 -> 部分 | 新增了「CUDA 13.x 需要至少 580 驱动」这个地板值；仍缺 525、缺 `cudaGetDeviceCount returned 3` 症状、缺 forward-compat 修法 |
| 10 两个独立原因 | 部分 -> 部分 | 两原因都修，并补「CRI 中确实配置了同名 handler」；仍缺 RuntimeClass 不存在会直接 `Failed` 的辨析 |
| 11 异构池节点选择 | 达成 -> 达成 | 除 `nvidia.com/gpu.memory` + `Gt` 外，还用上了 `nvidia.com/gpu.sharing-strategy=none`（基线未用） |
| 12 startup probe | 未达成 -> **未达成** | workspace 的 `gpu-inference.yaml` 只有 readiness/liveness，无 `startupProbe`，预算也未调整 |
| 13 `:latest` -> digest | 未达成 -> **达成** | 明确要求换成不可变 digest |

净变化：达成 3 -> 6，未达成 4 -> 2。

**两条未达成如实记录，不改判据掩盖**：EB8 与 EB12 对应的内容
（`references/kubernetes-gpu.md` 的「The variables that decide what the container sees」
与「Startup budget」，以及 `deploy-a-gpu-workload` 清单里的探针那条）都存在于 skill 中，
模型读了 skill 仍未用上。原因是场景 query 把注意力锚定在「三次失败，按顺序解释」，
而环境变量的显式设置与探针预算都不属于那三次失败--它们是夹具里**未被提问的隐含缺陷**。
这说明该场景对这两条的判别力弱，而不是 skill 缺内容。后续若要测这两条,
应另设一个以「这个 Deployment 为什么启动就被重启」为问句的场景,而不是把它们
挂在一个资源契约场景的尾巴上。

结论：GPU 扩展有真实缺口，13 条里 10 条需要 reference 才能稳定答对，`references/kubernetes-gpu.md` 立得住。
