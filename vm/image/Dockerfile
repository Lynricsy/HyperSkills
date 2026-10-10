# syntax=docker/dockerfile:1
# HyperSkills skill 测试 VM 镜像：Docker 只负责分层构建，产物导入 microsandbox 以 microVM 运行。
# 构建入口：uv run tools/vm.py build（见 vm/README.md）。
#
# 每层的 ARG 紧贴各自的 RUN 声明：改一个版本号只让该层及其后续层失效。
FROM buildpack-deps:trixie

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive

# 1. 系统包、第三方 apt 源（gh、gcloud）、agent 用户
RUN --mount=type=bind,source=provision,target=/provision \
    bash /provision/10-system.sh

# 2. 钉版本的上游二进制
ARG NODE_VERSION=24.21.0 \
    GO_VERSION=1.27.2 \
    UV_VERSION=0.13.0 \
    TERRAFORM_VERSION=1.16.5 \
    KUBECTL_VERSION=1.37.1 \
    HELM_VERSION=4.3.0 \
    YQ_VERSION=4.54.1 \
    HADOLINT_VERSION=2.15.1 \
    DUCKDB_VERSION=1.5.6 \
    GRADLE_VERSION=9.8.1 \
    TRIVY_VERSION=0.75.0 \
    GITLEAKS_VERSION=8.30.1 \
    FOUNDRY_VERSION=1.8.5 \
    DOTNET_CHANNEL=10.0
RUN --mount=type=bind,source=provision,target=/provision \
    bash /provision/20-binaries.sh

# 3. Node 生态：pi、全局 CLI、Playwright Chromium
ARG PI_VERSION=1.1.0 \
    PLAYWRIGHT_VERSION=1.64.0
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright
RUN --mount=type=bind,source=provision,target=/provision \
    bash /provision/30-node.sh

# 4. agent 用户自有的工具链：Python venv、uv tools、Rust
USER agent
RUN --mount=type=bind,source=provision,target=/provision \
    bash /provision/40-user.sh

# 5. 预置文件（pi 默认设置、自检脚本）。放在最后，改动不触发重装。
COPY --chown=agent:agent rootfs/home/agent/ /home/agent/
COPY rootfs/usr/local/bin/ /usr/local/bin/

# PATH 顺序：全局 venv 优先，其次 agent 自有工具，最后系统路径。
# npm 全局前缀指向用户目录：agent 自装的全局包无需 sudo，也不覆盖镜像预装的那批。
ENV PATH=/opt/venv/bin:/home/agent/.local/bin:/home/agent/.cargo/bin:/home/agent/.npm-global/bin:/home/agent/go/bin:/usr/local/go/bin:/opt/gradle/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    VIRTUAL_ENV=/opt/venv \
    NPM_CONFIG_PREFIX=/home/agent/.npm-global \
    DOTNET_ROOT=/usr/share/dotnet \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 \
    DOTNET_NOLOGO=1 \
    PI_TELEMETRY=0 \
    PI_SKIP_VERSION_CHECK=1
# Debian 的 /etc/profile 会把登录 shell 的 PATH 重置为默认值；从上面的 ENV 生成
# profile.d 片段补回，保证 `bash -l` 与非登录 shell 看到同一个 PATH。
USER root
RUN printf 'export PATH="%s"\n' "$PATH" > /etc/profile.d/hyperskills-vm.sh

USER agent
WORKDIR /workspace
CMD ["bash", "-l"]
