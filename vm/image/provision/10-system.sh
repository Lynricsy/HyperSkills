#!/usr/bin/env bash
# 系统层：Debian 软件源里足够新的工具一律走 apt（签名校验、体积可控），
# 并创建运行 agent 的非 root 用户。
# shellcheck source-path=SCRIPTDIR
source "$(dirname "$0")/lib.sh"

export DEBIAN_FRONTEND=noninteractive
apt-get update

packages=(
  # 基础与排障
  bash-completion ca-certificates curl wget gnupg git git-lfs openssh-client rsync
  jq ripgrep fd-find tree file less vim-nox nano unzip zip xz-utils zstd bzip2 p7zip-full
  procps psmisc htop lsof strace ltrace gdb valgrind iproute2 iputils-ping dnsutils
  netcat-openbsd socat sudo locales tzdata tmux time bc gettext-base sqlite3
  shellcheck shfmt graphviz
  # C/C++ 与通用构建
  build-essential make cmake ninja-build meson pkg-config autoconf automake libtool
  clang clangd clang-format clang-tidy lldb
  # Python（系统解释器；常用库装在 /opt/venv，见 40-user.sh）
  python3 python3-dev python3-venv python3-pip pipx
  # JVM 与 PHP
  openjdk-21-jdk-headless maven
  php-cli php-xml php-mbstring php-curl php-zip php-sqlite3 php-pgsql php-intl php-bcmath composer
  # 数据库服务端与客户端（不自启，VM 里按需 `sudo service ... start`）
  postgresql postgresql-contrib redis-server
  # 媒体、文档、办公
  ffmpeg imagemagick poppler-utils qpdf ghostscript pandoc
  libreoffice-writer-nogui libreoffice-calc-nogui libreoffice-impress-nogui
  fonts-noto-cjk fonts-noto-color-emoji fonts-dejavu fonts-liberation2
  # 容器：trixie 把 CLI 拆成独立的 docker-cli（docker.io 只是 Recommends 它）
  docker.io docker-cli docker-buildx docker-compose
)
apt-get install -y --no-install-recommends "${packages[@]}"

# Debian 把 fd 装成 fdfind；补上通用名，skill 文档与 agent 习惯都用 `fd`。
ln -sf "$(command -v fdfind)" /usr/local/bin/fd

# GitHub CLI：Debian 版本滞后于上游，改用官方 apt 源。
fetch https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(deb_arch) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  > /etc/apt/sources.list.d/github-cli.list

# Google Cloud CLI：官方 apt 源（与发行版无关的 cloud-sdk 通道）。
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  > /etc/apt/sources.list.d/google-cloud-sdk.list

apt-get update
apt-get install -y --no-install-recommends gh google-cloud-cli

# agent 用户：uid 1000 便于 msb 目录挂载映射属主；免密 sudo 让 agent 能自行装包、起服务。
useradd --create-home --uid 1000 --shell /bin/bash agent
usermod -aG docker agent
echo 'agent ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/agent
chmod 0440 /etc/sudoers.d/agent

# 交给 agent 的可写位置：Python 全局 venv 与评测工作区。
install -d -o agent -g agent /opt/venv /workspace

rm -rf /var/lib/apt/lists/*
