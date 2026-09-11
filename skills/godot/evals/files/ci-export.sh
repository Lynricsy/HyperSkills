#!/usr/bin/env bash
# Nightly build. Runs on a fresh clone in a container with no display.
set -euo pipefail

GODOT=/opt/godot/godot

cd "$(dirname "$0")/.."

# Smoke test: boot the game for a few seconds and make sure it does not crash.
$GODOT --headless --quit-after 300
echo "smoke test passed"

# Produce the three builds QA asks for.
$GODOT --headless --export-release "Windows" build/windows/Skyforge.exe
$GODOT --headless --export-release "Web" build/web/index.html
$GODOT --headless --export-release "Linux" build/server/skyforge_server.x86_64

# Publish the web build to the static bucket.
aws s3 sync build/web/ s3://skyforge-play/ --delete
echo "all builds uploaded"
