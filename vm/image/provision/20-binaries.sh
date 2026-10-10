#!/usr/bin/env bash
# 上游二进制层：发行版里缺失或明显滞后的工具，按 Dockerfile 的 ARG 钉版本安装。
# 上游公布了 sha256 的一律校验；只有 yq 与 AWS CLI 不提供简单清单，靠 HTTPS 来源。
# shellcheck source-path=SCRIPTDIR
source "$(dirname "$0")/lib.sh"

: "${NODE_VERSION:?}" "${GO_VERSION:?}" "${UV_VERSION:?}" "${TERRAFORM_VERSION:?}"
: "${KUBECTL_VERSION:?}" "${HELM_VERSION:?}" "${YQ_VERSION:?}" "${HADOLINT_VERSION:?}"
: "${DUCKDB_VERSION:?}" "${GRADLE_VERSION:?}" "${TRIVY_VERSION:?}" "${GITLEAKS_VERSION:?}"
: "${FOUNDRY_VERSION:?}" "${DOTNET_CHANNEL:?}"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"
arch=$(deb_arch)    # amd64 | arm64
uarch=$(uname_arch) # x86_64 | aarch64

# Node.js（pi 要求 >= 22.19；用 LTS 线）
node_arch=$([ "$arch" = amd64 ] && echo x64 || echo arm64)
node_tar="node-v${NODE_VERSION}-linux-${node_arch}.tar.xz"
fetch "https://nodejs.org/dist/v${NODE_VERSION}/${node_tar}" "$node_tar"
fetch "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt" node.sums
check_sha256 "$node_tar" "$(sha_from_list node.sums "$node_tar")"
tar -xJf "$node_tar" -C /usr/local --strip-components=1 --no-same-owner \
  --exclude='*/CHANGELOG.md' --exclude='*/README.md' --exclude='*/LICENSE'

# Go
go_tar="go${GO_VERSION}.linux-${arch}.tar.gz"
fetch "https://dl.google.com/go/${go_tar}" "$go_tar"
fetch "https://dl.google.com/go/${go_tar}.sha256" go.sha
check_sha256 "$go_tar" "$(awk '{print $1}' go.sha)"
tar -xzf "$go_tar" -C /usr/local

# uv / uvx
uv_tar="uv-${uarch}-unknown-linux-gnu.tar.gz"
fetch "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/${uv_tar}" "$uv_tar"
fetch "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/${uv_tar}.sha256" uv.sha
check_sha256 "$uv_tar" "$(awk '{print $1}' uv.sha)"
tar -xzf "$uv_tar" --strip-components=1 -C /usr/local/bin

# Terraform
tf_zip="terraform_${TERRAFORM_VERSION}_linux_${arch}.zip"
fetch "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/${tf_zip}" "$tf_zip"
fetch "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_SHA256SUMS" tf.sums
check_sha256 "$tf_zip" "$(sha_from_list tf.sums "$tf_zip")"
unzip -q -o "$tf_zip" terraform -d /usr/local/bin

# kubectl
fetch "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${arch}/kubectl" kubectl
fetch "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/${arch}/kubectl.sha256" kubectl.sha
check_sha256 kubectl "$(awk '{print $1}' kubectl.sha)"
install -m 0755 kubectl /usr/local/bin/kubectl

# Helm
helm_tar="helm-v${HELM_VERSION}-linux-${arch}.tar.gz"
fetch "https://get.helm.sh/${helm_tar}" "$helm_tar"
fetch "https://get.helm.sh/${helm_tar}.sha256sum" helm.sha
check_sha256 "$helm_tar" "$(awk '{print $1}' helm.sha)"
tar -xzf "$helm_tar" --strip-components=1 -C /usr/local/bin "linux-${arch}/helm"

# yq（mikefarah 版；Debian 的 yq 是另一个 Python 包装器）
fetch "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_${arch}" yq
install -m 0755 yq /usr/local/bin/yq

# hadolint
hadolint_arch=$([ "$arch" = amd64 ] && echo x86_64 || echo arm64)
fetch "https://github.com/hadolint/hadolint/releases/download/v${HADOLINT_VERSION}/hadolint-linux-${hadolint_arch}" "hadolint-linux-${hadolint_arch}"
fetch "https://github.com/hadolint/hadolint/releases/download/v${HADOLINT_VERSION}/checksums.sha256" hadolint.sums
check_sha256 "hadolint-linux-${hadolint_arch}" "$(sha_from_list hadolint.sums "hadolint-linux-${hadolint_arch}")"
install -m 0755 "hadolint-linux-${hadolint_arch}" /usr/local/bin/hadolint

# DuckDB CLI（Python 包另装在 /opt/venv）
fetch "https://github.com/duckdb/duckdb/releases/download/v${DUCKDB_VERSION}/duckdb_cli-linux-${arch}.zip" duckdb.zip
unzip -q -o duckdb.zip duckdb -d /usr/local/bin

# Trivy 与 gitleaks（security-review / containers）
trivy_arch=$([ "$arch" = amd64 ] && echo 64bit || echo ARM64)
trivy_tar="trivy_${TRIVY_VERSION}_Linux-${trivy_arch}.tar.gz"
fetch "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/${trivy_tar}" "$trivy_tar"
fetch "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_checksums.txt" trivy.sums
check_sha256 "$trivy_tar" "$(sha_from_list trivy.sums "$trivy_tar")"
tar -xzf "$trivy_tar" -C /usr/local/bin trivy

gitleaks_arch=$([ "$arch" = amd64 ] && echo x64 || echo arm64)
gitleaks_tar="gitleaks_${GITLEAKS_VERSION}_linux_${gitleaks_arch}.tar.gz"
fetch "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/${gitleaks_tar}" "$gitleaks_tar"
fetch "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_checksums.txt" gitleaks.sums
check_sha256 "$gitleaks_tar" "$(sha_from_list gitleaks.sums "$gitleaks_tar")"
tar -xzf "$gitleaks_tar" -C /usr/local/bin gitleaks

# Foundry（forge / cast / anvil / chisel）：直接装钉版本的发布包，不走 foundryup。
foundry_tar="foundry_v${FOUNDRY_VERSION}_linux_${arch}.tar.gz"
fetch "https://github.com/foundry-rs/foundry/releases/download/v${FOUNDRY_VERSION}/${foundry_tar}" "$foundry_tar"
fetch "https://github.com/foundry-rs/foundry/releases/download/v${FOUNDRY_VERSION}/foundry_v${FOUNDRY_VERSION}_linux_${arch}.sha256" foundry.sha
check_sha256 "$foundry_tar" "$(awk '{print $1}' foundry.sha)"
tar -xzf "$foundry_tar" -C /usr/local/bin

# Gradle（Debian 的 gradle 停在 4.x）
gradle_zip="gradle-${GRADLE_VERSION}-bin.zip"
fetch "https://services.gradle.org/distributions/${gradle_zip}" "$gradle_zip"
fetch "https://services.gradle.org/distributions/${gradle_zip}.sha256" gradle.sha
check_sha256 "$gradle_zip" "$(awk '{print $1}' gradle.sha)"
unzip -q -o "$gradle_zip" -d /opt
ln -sfn "/opt/gradle-${GRADLE_VERSION}" /opt/gradle

# AWS CLI v2（官方只提供 latest 与 PGP 签名，不钉版本）
fetch "https://awscli.amazonaws.com/awscli-exe-linux-${uarch}.zip" awscli.zip
unzip -q awscli.zip
./aws/install --install-dir /usr/local/aws-cli --bin-dir /usr/local/bin

# .NET SDK：官方安装脚本按通道取最新补丁
fetch https://dot.net/v1/dotnet-install.sh dotnet-install.sh
bash dotnet-install.sh --channel "$DOTNET_CHANNEL" --install-dir /usr/share/dotnet --no-path
ln -sf /usr/share/dotnet/dotnet /usr/local/bin/dotnet
