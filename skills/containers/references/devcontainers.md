# Dev containers

Verified against: the Dev Container Specification and its JSON property reference (containers.dev).

## Contents

- [What the file proves, and what it does not](#what-the-file-proves-and-what-it-does-not)
- [Lifecycle commands](#lifecycle-commands)
- [Image, Dockerfile or Compose](#image-dockerfile-or-compose)
- [Features](#features)
- [User and file ownership](#user-and-file-ownership)
- [Environment variables](#environment-variables)
- [Ports](#ports)
- [Deprecated properties](#deprecated-properties)
- [A reviewed configuration](#a-reviewed-configuration)

## What the file proves, and what it does not

At start-up, `devcontainer.json` is merged with the `devcontainer.metadata` label baked
into the image, and the specification states that when order matters, `devcontainer.json`
is considered **last**. [official]

The consequence for review is asymmetric and worth stating precisely:

- A value **present** in the file wins the merge. You can rely on it and report on it.
- A value **absent** from the file may still be supplied by the image label. The file
  alone cannot prove it is absent.

So report what the file states, and where the label could still change the outcome. Do
not report the absence of a lifecycle command, `remoteUser`, `containerUser`,
`remoteEnv`, `containerEnv`, `mounts`, `updateRemoteUserUID`, `waitFor` or
`userEnvProbe` as proof that the behaviour is missing.

Some properties are documented as not storable in the image label (`features`,
`overrideFeatureInstallOrder`, `appPort` have untagged rows in the property reference).
Others — the VS Code-specific top-level `extensions`, `settings`, `devPort` — have no
row at all, and silence is not immunity. Do not derive immunity by subtracting one list
from another; the specification declares its enumerations open.

This is why the rules below are written to report only what is *visible in the file*.
Such a finding can be missed, but it cannot be false.

## Lifecycle commands

Order of execution: `initializeCommand` (on the host, before the container exists) →
`onCreateCommand` → `updateContentCommand` → `postCreateCommand` → `postStartCommand`
→ `postAttachCommand`.

The split that matters:

**Cacheable setup belongs in `onCreateCommand` or `updateContentCommand`, never in
`postCreateCommand`.** A Codespaces prebuild performs setup up to and including
`onCreateCommand` and `updateContentCommand`; it does not run `postCreateCommand`. The
reference CLI's `--prebuild` behaves the same way. Dependency installation left in
`postCreateCommand` is therefore never baked into the prebuild and is paid again on
every start.

Look for expensive, cacheable work in `postCreateCommand` — `npm ci`, `npm install`,
`pnpm install`, `pip install`, `poetry install`, `bundle install`, `go mod download`,
`cargo fetch`, `apt-get install`, `make`, `mvn`, `gradle` — while `onCreateCommand` and
`updateContentCommand` are absent or trivial. Check the object form entry by entry, not
only the string form.

Other points:

- The object form runs its entries **in parallel**. Two entries that both write the
  same file, or one that depends on another, is a race. Sequence them in one entry.
- A lifecycle command that fails does not always stop the container; a broken setup can
  present as a mysteriously missing tool later.
- `waitFor` decides which command the editor waits for before considering the container
  usable; it defaults to `updateContentCommand`. Moving work later than `waitFor` means
  the editor attaches before that work finishes.
- `postStartCommand` runs on every start, including resumes. Anything idempotent and
  cheap belongs there; anything expensive does not.

## Image, Dockerfile or Compose

- `image:` — fastest, and the right choice when a published image already matches.
- `build.dockerfile:` — when the environment needs its own layers. Cache ordering
  matters here as much as in a production image; a dev container that rebuilds slowly
  is usually a `COPY . .` placed before the dependency install.
- `dockerComposeFile:` + `service:` + `workspaceFolder:` — when the environment is
  several containers. `runServices:` limits what starts. Note that the dev container's
  lifecycle now depends on the Compose file, and `shutdownAction: stopCompose` decides
  whether closing the editor stops the whole stack.

Pin the base image or the Feature versions; an unpinned dev container is
irreproducible in exactly the way a dev container exists to prevent.

## Features

```jsonc
"features": {
  "ghcr.io/devcontainers/features/node:1": { "version": "22" },
  "ghcr.io/devcontainers/features/docker-in-docker:2": {}
}
```

- Features are installed as root, in an order the resolver decides from their declared
  `installsAfter`. When the order actually matters, state it with
  `overrideFeatureInstallOrder` rather than relying on the resolution.
- A Feature's `install.sh` runs arbitrary code from a third party at build time. Review
  the ones outside `ghcr.io/devcontainers/*` the way you would review a dependency.
- `docker-in-docker` and `docker-outside-of-docker` are different: the second mounts
  the host's Docker socket, which gives the dev container root on the host.
- Pin the major version (`:1`, `:2`); a Feature reference without one floats.

## User and file ownership

- `remoteUser` is who the editor and terminals run as; `containerUser` is who the
  container's processes run as. Setting only one is a frequent cause of root-owned
  files appearing in the workspace.
- `updateRemoteUserUID` (default true on Linux) rewrites the container user's uid to
  match the host user's, so bind-mounted files are writable. **Do not report its
  absence as a problem** — the default is the helpful behaviour, and it is only worth
  flagging when it is explicitly set to `false` alongside a bind-mounted workspace.
- On macOS and Windows the uid question does not arise the same way, so a configuration
  that works there can still produce unwritable files on Linux.

## Environment variables

- `containerEnv` is set when the container is created (available to every process);
  `remoteEnv` is applied to the editor's processes only and can reference host
  variables with `${localEnv:NAME}`.
- **Do not report `${localEnv:...}` in `remoteEnv` as a leaked secret.** Referencing a
  host environment variable is the mechanism for *not* committing a secret. What is
  worth reporting is a literal value that looks like a credential.
- `secrets` (in Codespaces) and a mounted file are the supported ways to get real
  secrets in; a value pasted into `containerEnv` is in version control.

## Ports

`forwardPorts` forwards after the container starts and is the current property.
`appPort` publishes at container creation and is only needed when something outside
the editor must reach the port; it also cannot be supplied by the image label.
`otherPortsAttributes` and `portsAttributes` control the label, protocol and
auto-forward behaviour.

## Deprecated properties

Report these when they are *present*, since a value in the file wins the merge:

| Deprecated | Current |
|---|---|
| top-level `extensions` | `customizations.vscode.extensions` |
| top-level `settings` | `customizations.vscode.settings` |
| top-level `devPort` | `forwardPorts` / `portsAttributes` |
| `"dockerFile"` at top level | `build.dockerfile` |

## A reviewed configuration

```jsonc
{
  "name": "acme-api",
  "build": { "dockerfile": "Dockerfile", "context": ".." },
  "features": {
    "ghcr.io/devcontainers/features/node:1": { "version": "22" }
  },
  "remoteUser": "node",
  "onCreateCommand": "npm ci",
  "updateContentCommand": "npm ci",
  "postCreateCommand": "npm run prepare",
  "postStartCommand": "git config --local core.hooksPath .githooks",
  "waitFor": "updateContentCommand",
  "forwardPorts": [3000],
  "portsAttributes": { "3000": { "label": "api", "onAutoForward": "notify" } },
  "remoteEnv": { "NPM_TOKEN": "${localEnv:NPM_TOKEN}" },
  "customizations": {
    "vscode": { "extensions": ["dbaeumer.vscode-eslint"] }
  }
}
```

`npm ci` appears in both `onCreateCommand` and `updateContentCommand` deliberately: the
first runs once at creation, the second re-runs when the prebuild refreshes content, and
both are inside the prebuild boundary. The expensive step is therefore cached; only the
cheap `prepare` hook is paid on start.

<!-- sources: awesome-copilot, devcontainers-spec -->
