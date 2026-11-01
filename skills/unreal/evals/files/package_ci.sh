#!/usr/bin/env bash
# CI packaging step for ArenaGame (Windows agent, Git Bash).
# Worked on UE 5.6. After the project moved to UE 5.8 the uploaded artifact
# shrank from ~9 GB to a few KB and only contains a file called ue.projectstore.
# The new build agent image also fails earlier with a toolchain error on
# Visual Studio 2022 17.10 / Windows SDK 10.0.19041.0.
set -euo pipefail

UE_ROOT="C:/Program Files/Epic Games/UE_5.8"
PROJECT="$PWD/ArenaGame.uproject"

"$UE_ROOT/Engine/Build/BatchFiles/RunUAT.bat" BuildCookRun \
  -project="$PROJECT" -noP4 -platform=Win64 -clientconfig=Shipping \
  -build -cook -allmaps -stage -pak -unattended

# Artifact: the cooked content plus the binaries.
7z a ArenaGame-Win64.zip "Saved/Cooked/Windows" "Binaries/Win64"

# Each pipeline step starts and stops zenserver; agents are wiped after every job.
