#!/usr/bin/env bash
# GitHub Actions step: "Build Android player"
# Runs in unityci/editor:ubuntu-6000.3.12f1-android-3 on a GPU-less runner.
# Symptoms: the job is green even when the build fails, artifacts/ is empty
# about one run in four, and when it does fail the log only says
# "Aborting batchmode due to failure". UNITY_SERIAL is a repo secret.
set -e

UNITY=/opt/unity/Editor/Unity
PROJECT=../MyGame

"$UNITY" \
  -batchmode \
  -quit \
  -projectPath "$PROJECT" \
  -logFile "$PROJECT/Logs/build.log" \
  -serial "$UNITY_SERIAL" \
  -executeMethod CI.BuildScript.BuildAndroid

echo "build finished"
ls -la "$PROJECT/artifacts" || true
