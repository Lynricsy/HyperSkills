#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Record an Xcode Instruments `.trace` bundle via `xctrace record`.

macOS only — `xctrace` ships with Xcode.

Modes:
  (default)         Record until Ctrl+C, a stop-file appears, or the time limit.
  --list-devices    Connected devices, simulators, and the host, as JSON.
  --list-templates  Available Instruments templates, as JSON.

Template rule: the SwiftUI template only fills the SwiftUI lane on a real
device (a physical iOS/iPadOS device or the host Mac). On the iOS Simulator the
lane comes back empty — pass `--template "Time Profiler"` there. Check the
`kind` field from --list-devices before recording.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# The SwiftUI template is what makes the swiftui and swiftui-causes lanes
# available; every other lane this skill reads is included in it too.
DEFAULT_TEMPLATE = "SwiftUI"
# xctrace needs time to flush and index the bundle after SIGINT. Traces of a few
# minutes finalise well inside this; a longer wait only delays reporting a hang.
FINALISE_TIMEOUT_S = 60
# Polling interval for --stop-file. Fine-grained enough to feel immediate,
# coarse enough to cost nothing over a long recording.
STOP_FILE_POLL_S = 0.5


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 2


def require_xctrace() -> str | None:
    if shutil.which("xctrace") is None:
        return (
            "xctrace not found on PATH. It ships with Xcode on macOS; install Xcode "
            "and run `xcode-select --switch /Applications/Xcode.app`. Recording "
            "cannot run on Linux."
        )
    return None


def run_xctrace(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["xctrace", *args], capture_output=True, text=True, check=False)


def list_devices() -> list[dict[str, str]]:
    """Parse `xctrace list devices` into records with a `kind` discriminator.

    Output is grouped under `== Devices ==`, `== Devices Offline ==`, and
    `== Simulators ==` headings, then one `Name (OS) (UDID)` line per entry.
    """
    proc = run_xctrace(["list", "devices"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "xctrace list devices failed")

    entry = re.compile(r"^(?P<name>.+?)\s+\((?P<os>[^()]+)\)\s+\((?P<udid>[^()]+)\)\s*$")
    kind = "devices"
    out: list[dict[str, str]] = []
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("=="):
            kind = line.strip("= ").lower()
            continue
        match = entry.match(line)
        if match:
            out.append({"kind": kind, **match.groupdict()})
        else:
            # The host Mac is listed without an OS/UDID pair.
            out.append({"kind": kind, "name": line, "os": "", "udid": ""})
    return out


def list_templates() -> list[str]:
    proc = run_xctrace(["list", "templates"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "xctrace list templates failed")
    return [
        line.strip().strip('"')
        for line in proc.stdout.splitlines()
        if line.strip() and not line.startswith("==")
    ]


def build_record_args(args: argparse.Namespace, output: Path) -> list[str]:
    record = ["record", "--template", args.template, "--output", str(output)]
    if args.device:
        record += ["--device", args.device]
    if args.attach:
        record += ["--attach", args.attach]
    elif args.launch:
        record += ["--launch", "--", args.launch]
    else:
        record += ["--all-processes"]
    if args.time_limit:
        record += ["--time-limit", args.time_limit]
    for pair in args.env:
        record += ["--env", pair]
    for instrument in args.instrument:
        record += ["--instrument", instrument]
    return record


def redacted(record_args: list[str]) -> str:
    """Command line with `--env KEY=VALUE` values masked before display."""
    shown: list[str] = []
    mask_next = False
    for token in record_args:
        if mask_next:
            key = token.split("=", 1)[0]
            shown.append(f"{key}=<redacted>")
            mask_next = False
            continue
        shown.append(token)
        mask_next = token == "--env"
    return " ".join(["xctrace", *shown])


def wait_for_stop(proc: subprocess.Popen[bytes], stop_file: Path | None) -> None:
    """Wait for the recording to end, honouring a stop-file if one was given."""
    if stop_file is None:
        proc.wait()
        return

    print(f"recording; `touch {stop_file}` to stop cleanly")
    while proc.poll() is None:
        if stop_file.exists():
            print("stop-file seen; stopping recording")
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=FINALISE_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                print(
                    f"warn: xctrace did not finalise within {FINALISE_TIMEOUT_S}s; "
                    "terminating. The bundle may be unreadable.",
                    file=sys.stderr,
                )
                proc.terminate()
            return
        time.sleep(STOP_FILE_POLL_S)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    listing = parser.add_mutually_exclusive_group()
    listing.add_argument("--list-devices", action="store_true")
    listing.add_argument("--list-templates", action="store_true")

    parser.add_argument("--template", default=DEFAULT_TEMPLATE)
    parser.add_argument("--device", help="Device name or UDID; defaults to the host Mac.")
    parser.add_argument("--output", type=Path, help="Output .trace path.")
    parser.add_argument("--time-limit", help="Self-stop after e.g. 30s, 5m.")
    parser.add_argument("--stop-file", type=Path, help="Stop when this path appears.")
    parser.add_argument(
        "--env", action="append", default=[], metavar="KEY=VALUE",
        help="Environment variable for a launched process. Repeatable.",
    )
    parser.add_argument(
        "--instrument", action="append", default=[],
        help="Extra instrument passed through to xctrace. Repeatable.",
    )
    parser.add_argument(
        "--allow-system-wide-recording", action="store_true",
        help="Acknowledge that recording all processes captures unrelated apps.",
    )

    target = parser.add_mutually_exclusive_group()
    target.add_argument("--attach", help="Attach to a running process by name or pid.")
    target.add_argument("--launch", help="Launch this app bundle or executable.")

    args = parser.parse_args(argv)

    if problem := require_xctrace():
        return fail(problem)

    try:
        if args.list_devices:
            print(json.dumps(list_devices(), indent=2))
            return 0
        if args.list_templates:
            print(json.dumps(list_templates(), indent=2))
            return 0
    except RuntimeError as error:
        return fail(str(error))

    if not args.attach and not args.launch and not args.allow_system_wide_recording:
        return fail(
            "no --attach or --launch given, which records every process on the target "
            "and can capture unrelated applications. Explain that scope to the user, "
            "then pass --allow-system-wide-recording to confirm."
        )

    if args.launch and not Path(args.launch).exists():
        return fail(f"--launch target not found: {args.launch}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = args.output or Path(f"{args.template.replace(' ', '-')}-{stamp}.trace")
    if output.exists():
        return fail(
            f"{output} already exists and xctrace will not overwrite it. "
            "Pass a different --output or delete the existing bundle."
        )
    output.parent.mkdir(parents=True, exist_ok=True)

    if args.stop_file and args.stop_file.exists():
        return fail(
            f"--stop-file {args.stop_file} already exists, so the recording would stop "
            "immediately. Delete it first."
        )

    record_args = build_record_args(args, output)
    print(redacted(record_args))

    proc = subprocess.Popen(["xctrace", *record_args])
    try:
        wait_for_stop(proc, args.stop_file)
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=FINALISE_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            proc.terminate()

    if proc.returncode not in (0, None) and not output.exists():
        return fail(
            f"xctrace exited {proc.returncode} and wrote no trace. Common causes: the "
            "process named by --attach is not running, the device is locked or "
            "untrusted, or the build is not signed for development."
        )

    print(f"trace written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
