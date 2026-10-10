#!/usr/bin/env bash
# 用户层：以 agent 身份安装，产物归 agent 所有，agent 在 VM 里可以继续增删而无需 sudo。
# shellcheck source-path=SCRIPTDIR
source "$(dirname "$0")/lib.sh"

[ "$(id -un)" = agent ] || { echo "40-user.sh must run as agent" >&2; exit 1; }
cd "$HOME"

# 全局 Python 环境：/opt/venv 位于 PATH 最前，`python`/`pip` 即它，
# 绕开 Debian 的 externally-managed 限制，又不污染系统解释器。
python3 -m venv /opt/venv
uv pip install --python /opt/venv/bin/python \
  numpy pandas polars pyarrow duckdb scipy scikit-learn matplotlib \
  openpyxl xlsxwriter python-docx python-pptx pypdf pdfplumber reportlab pillow \
  requests httpx pyyaml jinja2 rich tiktoken \
  pytest pytest-asyncio hypothesis ipython \
  fastapi uvicorn pydantic sqlalchemy alembic "psycopg[binary]" redis pymongo elasticsearch \
  boto3 openai anthropic mcp

# 独立隔离的 Python CLI
for tool in ruff mypy pre-commit semgrep azure-cli; do
  uv tool install "$tool"
done

# Rust：rustup 管理的 stable 工具链（Debian 的 rustc 太旧）。
curl --proto '=https' --tlsv1.2 -fsSL https://sh.rustup.rs \
  | sh -s -- -y --profile minimal --default-toolchain stable \
      --component clippy --component rustfmt --no-modify-path

uv cache clean
