# Security hardening

Verified against: Tauri 2.x

## Contents

- The four boundaries
- Content Security Policy
- HTTP headers
- The command surface is the real attack surface
- Validating what the webview sends
- Asset protocol
- Isolation pattern
- Secrets
- Child processes
- Release checklist

## The four boundaries

Reason about a Tauri app as four layers, because a mitigation at the wrong layer is no
mitigation:

1. webview content, which may be compromised (XSS, a malicious dependency in the frontend
   bundle);
2. the runtime authority and the IPC surface, which decides what layer 1 may call;
3. privileged Rust code, which does the actual work;
4. the operating system — files, keyrings, processes, network.

Capabilities are a layer-2 control. They limit what a compromised layer 1 can reach; they do
nothing about a layer-3 bug. Validation in Rust is a layer-3 control and is not optional
because layer 2 exists.

## Content Security Policy

CSP is off unless configured. Set it:

```json
{
  "app": {
    "security": {
      "csp": "default-src 'self'; connect-src 'self' ipc: http://ipc.localhost https://api.example.com; img-src 'self' asset: http://asset.localhost data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
      "devCsp": "default-src 'self'; connect-src 'self' ipc: http://ipc.localhost ws://localhost:5173 http://localhost:5173 https://api.example.com; img-src 'self' asset: http://asset.localhost data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; object-src 'none'; base-uri 'self'"
    }
  }
}
```

Rules that follow from how Tauri applies it:

- `csp: null` disables the protection entirely. It is the default and it is not a
  configuration.
- `connect-src` must keep `ipc: http://ipc.localhost` or `invoke` itself is blocked. This is
  the single highest-value directive to get right: locking `connect-src` to the IPC plus your
  own API means an injected same-origin script cannot post in-memory tokens to an attacker
  host.
- At compile time Tauri hashes the inline scripts of the bundled frontend and adds nonces for
  styles and external scripts, so a **production** `script-src 'self'` normally boots a hashed
  SPA without `'unsafe-inline'`.
- `devCsp` **replaces** `csp` while running `tauri dev`; it does not extend it. Dev serves
  unhashed scripts from the dev server, so `'unsafe-inline'` (and usually `'unsafe-eval'` for
  HMR) plus the dev-server origins belong there — and every directive you still want has to be
  repeated.
- A Rust/WASM frontend additionally needs `'wasm-unsafe-eval'` in `script-src`.
- Only list `asset:` / `http://asset.localhost` if the asset protocol is actually enabled.
- Loading scripts from a CDN is a new attack vector regardless of the policy that permits it;
  bundle the dependency instead.

Verify by loading the app once under `tauri dev` and once from a release build with the webview
console open. A CSP violation is a console warning, not an error dialog, so it is easy to ship.

## HTTP headers

`app.security.headers` (Tauri 2.1+) adds headers to the responses the webview gets for local
assets — not to IPC messages, not to error responses, and not to anything a remote API sends.
Only a fixed set of names is accepted: the `Access-Control-Allow-Credentials`/`-Headers`/
`-Methods`, `Access-Control-Expose-Headers`, `Access-Control-Max-Age`, the three
`Cross-Origin-*` policies, `Permissions-Policy`, `Service-Worker-Allowed`,
`Timing-Allow-Origin`, `X-Content-Type-Options` and `Tauri-Custom-Header` (test-only). The CSP
is **not** configured here.

Values compose by type: a string is used as-is, an array is joined with `, `, an object becomes
`key value` pairs joined with `; `, and `null` drops the header entirely. The two worth setting
deliberately are `Cross-Origin-Opener-Policy: same-origin` plus
`Cross-Origin-Embedder-Policy: require-corp` when the app needs `SharedArrayBuffer`, and a
`Permissions-Policy` that switches off the webview features the app never uses.

## The command surface is the real attack surface

Design commands as product operations, not primitives. The contrast is the whole point:

| Dangerous | Why | Instead |
|---|---|---|
| `run_shell(cmd: String)` | arbitrary code execution one XSS away | one command per action, fixed program, validated args |
| `read_any_file(path: String)` | reads keys, cookies, other users' files | `load_project(id: String)` rooted in an app-owned directory |
| `write_any_file(path, bytes)` | overwrite anything, including the app | `save_note(id, content)` |
| `sql_query(q: String)` | injection plus schema exposure | named queries with typed parameters |

A narrow command surface is also what makes the capability list meaningful: with two dozen
specific commands, a capability describes what a window can do; with `run_shell`, it does not.

## Validating what the webview sends

Every command argument is attacker-controlled if the frontend can be compromised. Validate in
Rust, in the command:

- maximum lengths and byte sizes, so a hostile caller cannot exhaust memory;
- enum/variant membership rather than free strings;
- identifier character sets — reject path separators and `..` before any join;
- **canonicalise** paths and confirm the result is inside an app-owned root, after resolving
  symlinks;
- existence and ownership of the record being addressed;
- authorisation for destructive operations, re-checked immediately before the destructive step
  rather than at the start of a flow.

Prefer app-owned identifiers over frontend-supplied paths wherever Rust owns the data: pass a
note id, not a filename. When the user genuinely picks a file, use the native dialog (which
carries its own scope) and still check the metadata and size in Rust.

Bound what comes back too: a command returning a child process's stderr should truncate it, or
a broken subprocess floods the IPC and the logs.

## Asset protocol

`app.security.assetProtocol` enables `asset:`/`http://asset.localhost`, and
`convertFileSrc` on the frontend turns a filesystem path into such a URL. It has its own
`FsScope`, independent of the fs plugin's permissions, so a broad scope here is a second and
much quieter filesystem read grant. Keep `enable: false` unless the app really displays local
media; when enabling it, allow one narrow directory (`$APPCACHE/**/*`, `$RESOURCE/**/*`, a
single subfolder) rather than `$HOME/**/*`.

Three glob behaviours account for most "asset protocol not configured to allow the path"
reports:

- resolved paths are **absolute**, so a pattern like `*/**` never matches — start from a
  base-directory variable (`$APPCACHE`, `$RESOURCE`, `$HOME`) or a literal `/`;
- prefer `**/*` over bare `**` for "every file under this tree";
- on Unix `requireLiteralLeadingDot` defaults to `true`, so wildcards do **not** match a path
  component beginning with `.` — `$HOME/**/*` will not serve `~/.cache/app/preview.png`. Name
  the segment literally (`$HOME/.cache/app/**/*`), or set `requireLiteralLeadingDot: false`,
  which requires the object form of `scope` (the array form cannot express it) and widens
  exposure to every hidden directory.

`deny` beats `allow` here as everywhere. Paths the user picks at runtime are not covered by
static config; persisting them across restarts needs the persisted-scope plugin with its
`protocol-asset` Cargo feature.

## Isolation pattern

`app.security.pattern.use: "isolation"` injects a small sandboxed application between the
frontend and Tauri Core:

```json
{
  "build": { "frontendDist": "../dist" },
  "app": { "security": { "pattern": { "use": "isolation",
    "options": { "dir": "../dist-isolation" } } } }
}
```

```js
// ../dist-isolation/index.js
window.__TAURI_ISOLATION_HOOK__ = (payload) => {
  // inspect, reject or normalise every IPC message before Core sees it
  return payload;
};
```

Every IPC message is routed through the hook, then encrypted with a key generated per app run
before reaching Core. It exists for the development-threat model — a frontend with a large,
deeply nested dependency tree — and it is the only place where "check every message" can be
implemented once. Two constraints: keep the isolation app dependency-free and build-step-free
(otherwise it inherits the supply-chain risk it is meant to contain), and remember ES modules
do not load inside the sandboxed iframe on Windows, so its scripts must be plain inlined
scripts.

## Secrets

Do not put secrets in `localStorage`, in the app's JSON config, or in a command's return value
that the frontend keeps around. Use the OS vault (Secret Service on Linux, Keychain on macOS,
Credential Manager on Windows) through a maintained crate, and store only a service/account key
plus a boolean for "a value exists" in your own config. Wrap secret strings in `Zeroizing`
where practical, and reject empty, oversized or multiline values when the consumer expects one
line. Be precise in user-facing copy: an OS vault protects against another user and against
file exfiltration, not against a process running as the same unlocked desktop user.

## Child processes

Prefer a typed `std::process::Command` (or the shell plugin's sidecar API) with a fixed program
and validated arguments over any shell string. Never concatenate user input into a shell
command. Do not pass secrets as command-line arguments (visible in the process list) or in the
child's environment (inherited and inspectable); hand them over a private channel the child
authenticates on instead. Never disable host or certificate verification to make a connection
work.

## Release checklist

- [ ] `csp` and `devCsp` both set, app loaded once in each mode with no console violations.
- [ ] `app.security.capabilities` listed explicitly; every permission traceable to a call site.
- [ ] No `windows: ["*"]`; window creation restricted to the highest-privilege window.
- [ ] Scopes on every path/URL permission, with the webview-data deny entries kept.
- [ ] Asset protocol disabled, or scoped to one media directory.
- [ ] No primitive commands (`run_shell`, `read_any_file`, raw SQL).
- [ ] Every command validates its arguments and bounds its output.
- [ ] No secrets in config, arguments, environment or frontend storage.
- [ ] `devtools` Cargo feature **not** enabled for the release build.
- [ ] Dependencies audited (`cargo audit`, the JS equivalent) and lockfiles committed.
- [ ] Updater configured with signing keys and HTTPS endpoints.

<!-- sources: tauri-docs, pinkpixel-tauri, hairyf-tauri, epicenter-tauri -->
