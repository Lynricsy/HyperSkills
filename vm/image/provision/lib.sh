# shellcheck shell=bash
# 各 provision 脚本共享的辅助函数；只被 source，不直接执行。
set -euo pipefail

# Debian 架构名（amd64/arm64），apt 与多数上游下载名都用它。
deb_arch() { dpkg --print-architecture; }

# 上游二进制常用的另一套架构名（x86_64/aarch64）。
uname_arch() {
  case "$(deb_arch)" in
    amd64) echo x86_64 ;;
    arm64) echo aarch64 ;;
    *) echo "unsupported architecture: $(deb_arch)" >&2; return 1 ;;
  esac
}

# 下载到指定路径；失败立即退出，避免把 HTML 错误页当成二进制装进镜像。
fetch() {
  local url=$1 dest=$2
  curl -fsSL --retry 3 --retry-delay 2 -o "$dest" "$url"
}

# 校验 sha256；上游公布了校验和的下载都必须走这里。
check_sha256() {
  local file=$1 expected=$2
  echo "${expected}  ${file}" | sha256sum -c --quiet -
}

# 上游 checksums 清单里按文件名取出 sha256（格式：`<sha>  <name>`）。
sha_from_list() {
  local list=$1 name=$2
  awk -v n="$name" '$2 == n || $2 == "*"n { print $1; exit }' "$list"
}
