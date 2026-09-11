# Build, export, headless and CI

Verified against: Godot 4.7.2 (`4.7.2.stable.official.ed1daf0bf`), Linux x86_64, export
templates `4.7.2.stable`. Every command in the CLI sections was run on this machine;
per-platform signing was not.

## Contents

- [Export templates](#export-templates)
- [Export presets](#export-presets)
- [The headless CLI](#the-headless-cli)
- [Error shapes you will hit](#error-shapes-you-will-hit)
- [A CI pipeline that actually fails](#a-ci-pipeline-that-actually-fails)
- [Containers and sandboxes](#containers-and-sandboxes)
- [Web export](#web-export)
- [Dedicated servers](#dedicated-servers)
- [Per-platform requirements](#per-platform-requirements)
- [Feature tags](#feature-tags)
- [Testing](#testing)
- [What cannot be done headlessly](#what-cannot-be-done-headlessly)

## Export templates

Templates must match the engine version **exactly**, including the build suffix. Install
the `.tpz` for your version into
`~/.local/share/godot/export_templates/<version>/`, where `<version>` matches the
`version.txt` inside the archive (for example `4.7.2.stable`). Any mismatch fails the
export with a missing-template error, and upgrading the engine on a CI image without
re-downloading templates is the usual cause.

## Export presets

`export_presets.cfg` lives at the project root and holds one `[preset.N]` block plus a
`[preset.N.options]` block each. The fields that matter for automation:

| Field | Note |
|---|---|
| `name` | What the CLI matches, **exactly**, spaces and slashes included |
| `platform` | `Windows Desktop`, `macOS`, `Linux`, `Web`, `Android`, `iOS` |
| `export_path` | Default output; the CLI's path argument overrides it |
| `dedicated_server` | Adds the `dedicated_server` feature tag and strips visual resources |
| `export_filter` | `all_resources`, `resources` (only those used), `customized` |
| `include_filter` | Comma-separated globs for **non-resource** files (`*.json,*.txt`) |
| `exclude_filter` | Globs to drop |
| `custom_features` | Extra feature tags queryable with `OS.has_feature` |
| `binary_format/embed_pck` | Single-file output instead of binary plus `.pck` |

Non-resource files are the recurring omission: a `.json` data file or a `.txt` licence is
not a Godot resource, so it is absent from the pack unless `include_filter` names it. The
game then works in the editor and fails at runtime on a missing file.

Keep presets in version control. They are the build definition, and a preset that exists
only on one developer's machine is a build nobody else can reproduce.

## The headless CLI

```bash
godot --headless --version
godot --headless --path <project> --import                         # build .godot/, register class_name
godot --headless --path <project> --check-only --script res://x.gd # parse gate, exit 1 on error
godot --headless --path <project> --quit-after 600                 # boot smoke test; N is FRAMES
godot --headless --path <project> --script res://tools/task.gd     # run a SceneTree/MainLoop script
godot --headless --path <project> --export-release "<preset>" build/<dir>/<file>
godot --headless --path <project> --export-debug   "<preset>" build/<dir>/<file>
godot --headless --path <project> --export-pack    "<preset>" build/game.pck
```

Always pass `--path`, so the run does not depend on the working directory, and always
capture both streams (`2>&1 | tee logs/<step>.log`) — the diagnostics are on stderr and
are otherwise lost.

`--import` is not optional on a fresh clone. Without `.godot/global_script_class_cache.cfg`
every `class_name` type fails to resolve:

```
SCRIPT ERROR: Parse Error: Could not find type "EnemyProfile" in the current scope.
ERROR: Failed to load script "res://main.gd" with error "Parse error".
```

`--quit-after N` counts main-loop iterations, not seconds. And without it, a project
whose main scene script failed to parse **never exits** — the scene loads without its
script and the main loop runs forever, so a CI step with no timeout hangs instead of
failing.

## Error shapes you will hit

```console
$ godot --headless --export-release "Linux" build/game.x86_64
ERROR: Invalid export preset name: Linux.
The following presets were detected in this project's `export_presets.cfg`:
```

The preset is named `Server`, or `Linux/X11`. Names are matched exactly and are
case- and space-sensitive; quote them.

```console
$ godot --headless --export-release "Linux/X11" build/linux/game.x86_64
ERROR: Prepare Template: The given export path doesn't exist.
ERROR: Project export for preset "Linux/X11" failed.
```

The **output directory must already exist**. `mkdir -p` before every export.

```console
$ godot --headless --export-release "Linux/X11" build/x
ERROR: This project doesn't have an `export_presets.cfg` file at its root.
Create an export preset from the "Project > Export" dialog and try again.
```

```console
$ godot --headless --check-only --script res://bad.gd
SCRIPT ERROR: Parse Error: Expected ":" after "if" condition.
          at: GDScript::reload (res://bad.gd:6)
ERROR: Failed to load script "res://bad.gd" with error "Parse error".
$ echo $?
1
```

Parsing stops at the **first** syntax error, so `--check-only` is a "does it parse" gate,
not a full type check; earlier type errors in the same file are not reported until the
syntax error is fixed. It does exit non-zero, so it gates reliably.

## A CI pipeline that actually fails

The trap is that a passing exit code proves almost nothing:

```console
$ godot --headless --quit-after 300 ; echo "EXIT=$?"
SCRIPT ERROR: Parse Error: Could not find type "Stats" in the current scope.
EXIT=0
```

Status 0 with a main scene that has no script. A smoke test must therefore assert on the
output, not only on the status:

```bash
#!/usr/bin/env bash
set -euo pipefail
GODOT=${GODOT:-godot}
PROJECT=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p logs build/windows build/web build/server     # export needs the dirs to exist

# 1. Import first: builds .godot/ and registers every class_name.
"$GODOT" --headless --path "$PROJECT" --import 2>&1 | tee logs/import.log

# 2. Parse gate. Non-zero exit on any parse error, unlike a plain run.
find "$PROJECT" -name '*.gd' -not -path '*/addons/*' -print0 \
  | xargs -0 -n1 -I{} sh -c '"$0" --headless --path "$1" --check-only --script "res://${2#$1/}"' \
      "$GODOT" "$PROJECT" {}

# 3. Boot smoke test, and fail on error output rather than on status.
"$GODOT" --headless --path "$PROJECT" --quit-after 300 2>&1 | tee logs/smoke.log
if grep -qE '^(SCRIPT ERROR|ERROR):' logs/smoke.log; then
  echo "smoke test produced engine errors" >&2
  exit 1
fi

# 4. Exports. Preset names must match export_presets.cfg exactly.
"$GODOT" --headless --path "$PROJECT" --export-release "Windows"  build/windows/Game.exe
"$GODOT" --headless --path "$PROJECT" --export-release "Web"      build/web/index.html
"$GODOT" --headless --path "$PROJECT" --export-release "Server"   build/server/game.x86_64
```

Run the exported binary too, not just the editor build: `res://` write bugs, missing
non-resource files and feature-tag branches only appear there.

## Containers and sandboxes

Godot writes editor settings, export templates and `user://` under the XDG directories.
In a container without a real home, or a sandbox that blocks writes, point them at the
project:

```bash
export XDG_DATA_HOME="$PROJECT/.ci/data"
export XDG_CONFIG_HOME="$PROJECT/.ci/config"
export XDG_CACHE_HOME="$PROJECT/.ci/cache"
```

Export templates then live under `$XDG_DATA_HOME/godot/export_templates/<version>/`.
Running as root prints a warning on every invocation
(`Started the engine as root/superuser`); `GODOT_SILENCE_ROOT_WARNING=1` suppresses it,
which matters when a step greps its own log for warnings.

## Web export

Web is Compatibility-only, and the browser requirements are the part that bites:

- `variant/thread_support = true` requires the page to be **cross-origin isolated**: the
  server must send `Cross-Origin-Opener-Policy: same-origin` and
  `Cross-Origin-Embedder-Policy: require-corp`. Without both, `SharedArrayBuffer` is
  unavailable and the page loads blank. Uploading the files to a static bucket does not
  configure headers; the hosting layer has to.
- It must be served over HTTP(S). Opening `index.html` from `file://` never works.
- `progressive_web_app/enabled` adds a service worker, which caches aggressively — expect
  a stale build after redeploying unless you bust the cache.
- Threads can be turned off (`thread_support = false`) to avoid the headers entirely, at
  the cost of threaded loading and some audio behaviour.

## Dedicated servers

Either tick `dedicated_server` on a Linux preset, which strips visual resources and adds
the feature tag, or ship the normal build and run it with `--headless`. Branch at
runtime:

```gdscript
func _ready() -> void:
    if OS.has_feature("dedicated_server") or DisplayServer.get_name() == "headless":
        _start_server_only()
```

A server build still needs its data pack next to the binary unless `embed_pck` is on.

## Per-platform requirements

`[official]` — none of this was reproduced on this machine.

| Platform | Needs |
|---|---|
| Windows | `rcedit` for icon and metadata; a signing tool for authenticode |
| macOS | Signing and notarisation; unsigned bundles are blocked by Gatekeeper. Cross-compiling from Linux produces an unsigned bundle |
| Linux | Nothing beyond templates. `.x86_64` plus `.pck`, or `embed_pck` |
| Android | Android SDK and JDK paths in Editor Settings, a debug or release keystore, and the `INTERNET` permission for anything networked |
| iOS | Xcode, a provisioning profile; the export produces an Xcode project to build |
| Web | See above |

`(Godot 4.6+)` the Android export template's source layout moved to the Android Studio
default (`android/build/src/main/java/...`), so a project with a customised Android build
needs its files relocated.

## Testing

GDScript unit tests run inside the engine; anything that needs real input or rendering
runs outside it.

```bash
# GdUnit4, a third-party addon under res://addons/gdUnit4  [community]
godot --headless --path . -s res://addons/gdUnit4/bin/GdUnitCmdTool.gd --run-tests
```

A no-dependency alternative is a plain script run with `--headless --script`, extending
`SceneTree` or `MainLoop`, that asserts and sets a non-zero exit code:

```gdscript
# res://tests/run_tests.gd — godot --headless --script res://tests/run_tests.gd
extends SceneTree

var failures := 0

func _initialize() -> void:
    _check("integer division truncates", 5 / 2 == 2)
    _check("armour maths is float", is_equal_approx(1.0 - 30 / 100.0, 0.7))
    quit(1 if failures > 0 else 0)

func _check(what: String, ok: bool) -> void:
    if not ok:
        failures += 1
        push_error("FAIL: %s" % what)
    else:
        print("ok: %s" % what)
```

Keep the boot smoke test separate from logic tests: the smoke test answers "does the
project start", the logic tests answer "is the behaviour right", and merging them makes
both failures ambiguous.

## What cannot be done headlessly

LightmapGI, occluder and reflection-probe bakes, `VisualShader` graph editing, and POT
translation-template generation are editor-only operations. So is anything that needs a
rendered frame: there is no RenderingDevice under `--headless`. Report that boundary
rather than describing output you did not produce.

Do not edit `.tscn` or `.tres` as raw text from a build script. A generated scene where
every node carries `parent="."` loads with zero errors and stacks every `Control` at the
origin. Drive scene edits through `--headless --script` and the scene API.

<!-- sources: godot-engine, godot-docs, awesome-gamedev-godot, abagames-headless-godot, haxqer-godot, godot-prompter, randroids-godot -->
