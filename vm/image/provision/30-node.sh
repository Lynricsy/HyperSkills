#!/usr/bin/env bash
# Node 生态层：常用全局 CLI、Playwright Chromium（共享浏览器目录）。
# shellcheck source-path=SCRIPTDIR
source "$(dirname "$0")/lib.sh"

: "${PLAYWRIGHT_VERSION:?}" "${PLAYWRIGHT_BROWSERS_PATH:?}"

export npm_config_fund=false npm_config_audit=false npm_config_update_notifier=false

npm install -g \
  pnpm yarn bun \
  typescript tsx prettier eslint pyright \
  "playwright@${PLAYWRIGHT_VERSION}" \
  mongosh wrangler

# 浏览器装到共享目录，agent 用户与 skill 自带的 playwright 依赖都能复用。
playwright install --with-deps chromium
chmod -R a+rX "$PLAYWRIGHT_BROWSERS_PATH"

npm cache clean --force
rm -rf /var/lib/apt/lists/*
