#!/usr/bin/env bash
# Runs on the billing VM, both by hand and from the nightly cron entry
#   15 2 * * * deploy /srv/billing/deploy.sh >> /var/log/billing-deploy.log 2>&1
# The systemd unit starts /srv/billing/venv/bin/uvicorn billing_api.main:app
set -eu

cd /srv/billing
git pull --ff-only
uv export --locked --no-dev --no-hashes -o requirements.lock
uv pip install -r requirements.lock
uv pip install --no-deps .
sudo systemctl restart billing
