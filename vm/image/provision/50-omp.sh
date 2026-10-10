#!/usr/bin/env bash
# 评测 agent 层：omp（oh-my-pi）官方发布的单文件二进制，钉版本并校验 sha256。
# shellcheck source-path=SCRIPTDIR
source "$(dirname "$0")/lib.sh"

: "${OMP_VERSION:?}"

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"

omp_arch=$([ "$(deb_arch)" = amd64 ] && echo x64 || echo arm64)
asset="omp-linux-${omp_arch}"
base="https://github.com/can1357/oh-my-pi/releases/download/v${OMP_VERSION}"
fetch "${base}/${asset}" "$asset"
fetch "${base}/SHA256SUMS.txt" omp.sums
check_sha256 "$asset" "$(sha_from_list omp.sums "$asset")"
install -m 0755 "$asset" /usr/local/bin/omp
