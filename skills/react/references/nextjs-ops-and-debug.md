# Next.js bundling, deployment and debugging

Read this for a build or runtime import error, a bundle-size investigation, a
self-hosting question, or a React Server Components security advisory.

Verified against: Next.js 16.3; bundle analysis and RSC security releases
against Next.js 16.4 and React 19.3.

## Contents

- Server-incompatible packages
- Native bindings and ESM/CommonJS
- Commonly problematic packages
- CSS and polyfills
- Bundle analysis
- Turbopack migration
- Self-hosting essentials
- RSC security releases
- Dev-server debugging
- Rebuilding one route

---

## Server-incompatible packages

The signature errors:

```
ReferenceError: window is not defined
ReferenceError: document is not defined
ReferenceError: localStorage is not defined
Module not found: Can't resolve 'fs'
```

They mean a package touching browser globals was pulled into a Server
Component. Three fixes, in order of preference:

```tsx
// 1. Client-only: load it dynamically with SSR disabled
const Chart = dynamic(() => import('some-chart-library'), { ssr: false })
```

```tsx
// 2. Client wrapper: keep the boundary in your own code
'use client'
import { Chart } from 'chart-library'
export function ChartWrapper(props: Props) { return <Chart {...props} /> }
```

```js
// 3. Genuinely server-side, but does not bundle: keep it external
module.exports = { serverExternalPackages: ['problematic-package'] }
```

---

## Native bindings and ESM/CommonJS

`serverExternalPackages` is the answer for native bindings (`sharp`, `bcrypt`,
`canvas`) and for packages with circular dependencies that break the bundler.

For an ESM package that a CommonJS consumer chokes on —
`SyntaxError: Cannot use import statement outside a module`, or
`Error: require() of ES Module` — add it to `transpilePackages`.

---

## Commonly problematic packages

| Package | Problem | Fix |
|---|---|---|
| `sharp`, `bcrypt`, `canvas` | native bindings | `serverExternalPackages` (or `bcryptjs` for `bcrypt`) |
| `recharts`, `mapbox-gl` | uses `window` | `dynamic(..., { ssr: false })` |
| `react-quill`, `lottie-web` | uses `document` | `dynamic(..., { ssr: false })` |
| `@monaco-editor/react` | uses `window`, and is large | `dynamic(..., { ssr: false })` |

---

## CSS and polyfills

Import CSS files (`import './styles.css'`, or a CSS module) instead of writing a
`<link rel="stylesheet">`; only the import path gets bundled, hashed and
optimized.

Next.js already ships the common polyfills — `Array.from`, `Object.assign`,
`Promise`, `fetch`, `Map`, `Set`, `Symbol`, `URLSearchParams` and dozens more.
A polyfill service script in the document is pure dead weight.

---

## Bundle analysis

```bash
next analyze            # Next.js 16.4+, interactive UI
next analyze --output   # writes .next/diagnostics/analyze, no server, for comparison
```

On Next.js 16.1–16.3 the command is `next experimental-analyze` (`--output` works the same);
16.4 renamed it and keeps the old name as an alias, so check the installed
version before writing it into a script.

Filter by route, environment and type; inspect module sizes and import chains.
Take a baseline before optimizing so the improvement is measurable, and check
the *server* environment too — a barrel import inflates server cold starts as
well as the client bundle.

---

## Turbopack migration

Turbopack is the default bundler for `next dev` and `next build` from Next.js 16
(stable for `dev` since 15.0). A `webpack: (config) => ...` block in
`next.config.js` does not run under it. Most real uses translate to
`serverExternalPackages` or `transpilePackages`; keep webpack only for a
loader with no Turbopack equivalent, and note that this opts the project out of
the default toolchain.

---

## Self-hosting essentials

Three facts decide whether a self-hosted deployment works:

1. `output: 'standalone'` produces `.next/standalone` with only production
   dependencies and a `server.js` entry point. Run it with `node server.js`.
2. `.next/static` and `public/` are **not** inside the standalone folder. Copy
   both explicitly, or every asset 404s.
3. Incremental Static Regeneration caches to the filesystem by default, which
   breaks across multiple instances — one instance revalidates and the others
   keep serving stale content. Configure a shared cache handler for any
   multi-instance deployment.

Everything else (base image choice, process manager, reverse proxy, health
checks) is ordinary deployment work and outside this skill.

---

## RSC security releases

The server half of React Server Components — `react-server-dom-webpack`,
`-turbopack` and `-parcel` — deserializes Server Function arguments and Flight
replies from the network, and it has taken a steady run of advisories (remote
code execution, denial of service, source exposure). Each fix ships as a patch
on **every** supported line at once (19.0.x, 19.1.x, 19.2.x, 19.3.x), so:

- The target is "the latest patch of the line in use", re-checked against the
  advisory at the time, never a number remembered from an earlier incident.
  The `.0` of a newer line is not automatically fixed.
- In a custom RSC setup, the `react-server-dom-*` package is the one to bump;
  keep `react` and `react-dom` on the same version. An exact pin on the RSC
  package survives a `react` upgrade and keeps the hole open.
- In Next.js the App Router runs the React build vendored inside `next`
  (`next/dist/compiled/react-server-dom-*`), whatever `react` version the app
  declares. The fix is upgrading `next` to the release its own advisory lists
  as patched for the line; adding a top-level `react-server-dom-*` dependency
  does nothing.
- Close the ticket on evidence: the resolved versions in the lockfile
  (`npm ls next react-server-dom-webpack`, or the pnpm/yarn equivalent), a
  clean `npm audit` for those packages, and a redeploy that replaced the old
  instances. Green builds and tests prove compatibility, not remediation.

---

## Dev-server debugging

The dev server exposes an MCP endpoint at `/_next/mcp` — enabled by default
from Next.js 16, and behind `experimental.mcpServer: true` before that. It
speaks JSON-RPC 2.0 over HTTP POST.

Find the real port from the dev-server output or the `dev` script; do not
assume 3000.

```bash
curl -X POST http://localhost:<port>/_next/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"get_errors","arguments":{}}}'
```

| Tool | Returns |
|---|---|
| `get_errors` | current build and runtime errors with source-mapped stacks |
| `get_routes` | every route, discovered from the filesystem |
| `get_project_metadata` | project path and dev-server URL |
| `get_page_metadata` | the render tree of the current page (needs a live browser session) |
| `get_logs` | path to the dev log file |
| `get_server_action_by_id` | the source location of a Server Action |

`get_errors` is the reason to use this at all: it beats reading the terminal,
because the stacks are source-mapped and it reports runtime errors the terminal
may have scrolled past.

Pair it with a real browser when the question is "what actually rendered" — a
clean build says nothing about what ended up in the static shell versus what
streamed in.

---

## Rebuilding one route

```bash
next build --debug-build-paths "/dashboard"     # one route
next build --debug-build-paths "/api/*"         # a glob
next build --debug-prerender                    # full stacks, and past the first failure
```

`--debug-build-paths` turns a multi-minute verification loop into seconds when
you are iterating on one route's build or prerender error.
`--debug-prerender` matters because the default build stops at the first
blocking route and often prints no usable frame.

<!-- sources: openai-plugins-nextjs, nextjs-docs, nextjs-cache-components, react-security-advisories -->
