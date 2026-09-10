#!/usr/bin/env bash
# Human-in-the-loop reproduction loop.
#
# Use when the symptom can only be triggered by a person, and nothing else can
# drive the loop. Copy this file, edit the block between the EDIT markers, and
# run it:
#
#   bash hitl_loop_template.sh
#
# The person follows the prompts in their terminal; every captured answer is
# printed back at the end as KEY=value lines, which is what the agent reads.
#
# Two helpers:
#   step "<instruction>"        show an instruction, wait for Enter
#   capture VAR "<question>"    ask a question, record the answer in VAR
#
# Ask for observations, never for interpretations: "what did the banner say?"
# is answerable, "did it look wrong?" is not. Leave actions that need no
# observation (signing in, opening a page) as `step` calls.
#
# Anything the person pastes ends up on your screen and in your transcript. Do
# not ask for tokens, cookies or auth headers; if an answer might contain one,
# ask for the shape ("does it start with acmepay_live?") instead of the value.

set -euo pipefail

# Prompts must reach the human even when this script's stdout is captured by
# the caller, so read from the controlling terminal rather than stdin.
if [ ! -r /dev/tty ]; then
  echo "error: no controlling terminal. Run this script directly in the" >&2
  echo "       person's terminal, not through a pipe or a background job." >&2
  exit 1
fi

# Names of every variable filled in by `capture`, in order, so the summary
# needs no maintenance when steps are added or removed.
CAPTURED_VARS=()

step() {
  printf '\n>>> %s\n' "$1" >/dev/tty
  printf '    [Enter when done] ' >/dev/tty
  read -r _ </dev/tty
}

capture() {
  local var="$1" question="$2" answer
  printf '\n>>> %s\n' "$question" >/dev/tty
  printf '    > ' >/dev/tty
  read -r answer </dev/tty
  printf -v "$var" '%s' "$answer"
  CAPTURED_VARS+=("$var")
}

summary() {
  printf '\n--- Captured ---\n'
  local var
  for var in "${CAPTURED_VARS[@]}"; do
    printf '%s=%s\n' "$var" "${!var}"
  done
}

# Print whatever was captured even if the person interrupts partway through:
# a half-finished round is still evidence.
trap summary EXIT

# --- EDIT BELOW ---------------------------------------------------------

step "Open the app at http://localhost:3000 and sign in."

capture EXPORT_FAILED "Click Export. Did it fail? (y/n)"

capture EXPORT_MESSAGE "Paste the message shown on screen, or type none:"

# --- EDIT ABOVE ---------------------------------------------------------
