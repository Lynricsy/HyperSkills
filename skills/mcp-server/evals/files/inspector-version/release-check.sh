#!/usr/bin/env bash
# Release gate for notes-mcp, run by CI after `npm ci` in the repo root.
set -euo pipefail

echo "== inspector version (recorded in the release notes)"
npx @modelcontextprotocol/inspector --cli --version | tee inspector-version.txt

echo "== tools/list smoke test"
npx @modelcontextprotocol/inspector --cli node dist/server.js --method tools/list > tools.json
jq -e '.tools | length > 0' tools.json
