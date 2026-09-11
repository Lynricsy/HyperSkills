#!/usr/bin/env bash
# deploy/ci-deploy.sh — called from .github/workflows/deploy.yml
# Repository is public (github.com/acme/reports).
set -euo pipefail

# TODO: move these into the CI secret store, they were added in a hurry
export WAREHOUSE_TOKEN="wh_REDACTED"
export STRIPE_SECRET_KEY="sk_live_REDACTED"
export GITHUB_TOKEN="ghp_REDACTED"
export DEPLOY_SSH_KEY_PATH=./deploy/id_ed25519   # also committed, see git log below

IMAGE="ghcr.io/acme/reports:${GITHUB_SHA}"

docker build -t "$IMAGE" .
docker push "$IMAGE"

curl -sS -X POST "https://api.acme.example/deploy" \
  -H "Authorization: Bearer ${WAREHOUSE_TOKEN}" \
  -d "{\"image\":\"${IMAGE}\"}"

echo "deployed $IMAGE with token ${WAREHOUSE_TOKEN}"

# $ git log --oneline -- deploy/ci-deploy.sh deploy/id_ed25519
# 4f1c2ab (2026-06-14) ci: add deploy script
# 9ac7e01 (2026-06-14) ci: add deploy key
# a02bd55 (2026-08-02) ci: bump image tag scheme
#
# $ git log --all --oneline | wc -l
# 3184
#
# The repository has 41 forks and 2 public mirrors.
