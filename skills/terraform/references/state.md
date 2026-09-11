# State: backends, locking, layout and recovery

Verified against: Terraform 1.16, OpenTofu 1.12.

## Contents

- [What is actually in state](#what-is-actually-in-state)
- [Backend selection](#backend-selection)
- [Locking](#locking)
- [Sizing and splitting state](#sizing-and-splitting-state)
- [Workspaces versus directories](#workspaces-versus-directories)
- [Inspecting state safely](#inspecting-state-safely)
- [Drift detection](#drift-detection)
- [Backend migration](#backend-migration)
- [Splitting an existing state](#splitting-an-existing-state)
- [Recovery](#recovery)

## What is actually in state

State is a JSON document mapping configuration addresses to real object IDs plus the last
known value of every attribute. Three consequences drive everything below:

1. **It contains secrets in plaintext.** Every attribute the provider returned is there —
   generated passwords, private keys, connection strings. `sensitive = true` changes the CLI
   output, not the file. Treat the state's storage as you would treat a secrets store.
2. **It is the only record of which real object an address refers to.** Losing it does not
   destroy infrastructure, but it makes Terraform propose to create everything again.
3. **Concurrent writes corrupt it.** Two applies that both read version N and both write
   version N+1 leave one apply's objects unrecorded and unmanaged.

The on-disk format is versioned and internal. Read it through `terraform state list`,
`terraform state show` and `terraform show -json`, not with `jq` against the raw file.

## Backend selection

Pick the backend that lives next to the thing being managed and supports locking. Object
storage (S3, Azure Blob, GCS) with versioning enabled is the default answer for a
self-managed setup; HCP Terraform / Terraform Enterprise is the answer when you also want
runs, policy and an audit trail hosted.

Whichever it is, the configuration must have:

| Requirement | Why |
|---|---|
| Locking enabled | Concurrent applies otherwise race |
| Server-side encryption | The file is plaintext secrets |
| Object versioning | The only cheap undo for a bad `state rm` or a partial write |
| Access scoped per environment | A read grant on the state is a read grant on its secrets |
| A key that names environment and component | `prod/network/terraform.tfstate`, so a new state is an obvious addition |

Backend configuration cannot use variables or expressions in Terraform — the backend is
initialised before the language is evaluated. Supply the varying parts through
`terraform init -backend-config=prod.backend.hcl` (a partial configuration) or
`-backend-config="key=..."`. OpenTofu 1.8+ does allow variables and locals in backend blocks,
which is one of the real divergences between the two runtimes.

On the S3 backend, `use_lockfile = true` enables native locking:

```hcl
terraform {
  backend "s3" {
    bucket       = "acme-tfstate"
    key          = "prod/network/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true   # Terraform 1.11+, OpenTofu 1.10+
  }
}
```

Below those versions the DynamoDB lock table is still required (`dynamodb_table`), and the
two can run side by side during a migration. Recommending a DynamoDB table on a current
runtime is stale advice — the argument is deprecated in favour of the lock file.

## Locking

A lock is taken for the duration of any operation that writes state (`apply`, `destroy`,
`state mv`, `state rm`, `import`) and for `plan` when the backend needs to refresh.

- Never use `-lock=false` to get past a stuck lock. It does not release anything; it just
  means your write ignores whoever else is writing.
- A genuinely orphaned lock (the process died) is released with
  `terraform force-unlock <LOCK_ID>`, and only after confirming the holder is really gone —
  the lock message names the operation, the who and the when.
- In CI, serialise runs per state at the pipeline level as well. Backend locking prevents
  corruption; pipeline concurrency control prevents the queue of blocked jobs that makes
  people reach for `-lock=false`.

## Sizing and splitting state

One state = one blast radius = one plan's runtime. Split when:

- Two environments share a state. This is the first split, always: no apply should be able to
  touch prod and dev in the same transaction.
- Different teams own different parts and review each other's plans out of politeness rather
  than need.
- The lifecycles differ — networking changes quarterly, the application changes hourly.
- The plan is slow enough that people skip reading it. A few hundred resources is where that
  starts.

Keep together what is genuinely coupled: resources created and destroyed as a unit, and
anything where a cross-state reference would be needed on every change. Every split converts
an intra-state dependency into either an input variable or a `terraform_remote_state` read,
and the second of those is a coupling with an access grant attached.

A layout that scales:

```
live/
├── prod/
│   ├── network/      # backend key prod/network
│   ├── data/         # backend key prod/data
│   └── app/          # backend key prod/app
└── staging/
    ├── network/
    ├── data/
    └── app/
modules/
├── network/
├── data/
└── app/
```

The per-environment directories are thin: a backend block, provider configuration, module
calls and the environment's values. Everything else is in `modules/`.

## Workspaces versus directories

CLI workspaces (`terraform workspace new prod`) give one configuration several state files
inside **one backend configuration**, selected by a mutable CLI-local setting. That makes
them a poor fit for environments:

- The wrong workspace is one forgotten `select` away, and nothing in the diff says which one
  you are in.
- Every workspace shares the same backend, so prod state cannot have different access control
  from dev state.
- Per-environment differences end up as `terraform.workspace == "prod" ? ... : ...` conditionals
  scattered through the configuration.

Use separate directories with separate backend keys. Workspaces are still useful for
short-lived parallel copies of the *same* environment — a per-pull-request stack, a scratch
copy for testing a migration.

## Inspecting state safely

```bash
terraform state list                       # every address under management
terraform state show aws_instance.web      # one object's recorded attributes
terraform show -json | jq '.values.root_module'   # resolved values, needs init
terraform state pull > backup.tfstate      # raw snapshot, treat as a secret
```

`terraform show -json` renders values against the provider schemas, so it needs `init` to have
installed the providers. Fall back to `state pull` only when providers are unavailable, or
when you need coarse metadata (`serial`, `lineage`) rather than values. Never echo state
output into a CI log.

## Drift detection

```bash
terraform plan -refresh-only              # what changed outside Terraform, nothing proposed
terraform plan -detailed-exitcode         # exit 0 = no changes, 2 = changes, 1 = error
```

`-refresh-only` is the right first command after an incident: it reports the delta between
state and reality without proposing to undo it. A scheduled job running
`plan -detailed-exitcode` and failing on exit 2 turns drift into a notification instead of a
surprise during the next deploy.

`terraform apply -refresh-only` accepts the observed reality into state without changing
infrastructure — correct when the console change is one you intend to keep *and* have already
written into the configuration, wrong as a way to make an inconvenient diff go away.

## Backend migration

```bash
# 1. Snapshot
terraform state pull > backup-$(date +%F).tfstate

# 2. Edit the backend block, then:
terraform init -migrate-state
```

`-migrate-state` prompts to copy the existing state to the new backend; answer deliberately.
`-reconfigure` does the opposite — it discards the association with the existing state and
starts empty, which is what you want when moving to a backend that *already* holds the state
and what you must not use otherwise.

After migration, `terraform plan` must be empty. A non-empty plan means the new backend is
holding a different (or no) state, and the answer is to stop and re-check, never to apply.

## Splitting an existing state

```bash
# from the source directory, with the destination state as a local file first
terraform state mv -state-out=../new-stack/terraform.tfstate \
  module.data aws_db_instance.main
```

- Take the snapshot first. `state mv` and `state rm` are the two commands that can lose an
  object's identity.
- Move whole modules where possible; moving half a module leaves the other half referencing
  addresses that no longer exist.
- The exit condition is symmetric: both states plan empty, and the union of their
  `state list` output equals the original.
- Where the objects can be re-adopted rather than moved, `removed` blocks on the source plus
  `import` blocks on the destination give the same result through a reviewable pull request
  rather than a pair of local commands. Prefer that when the split is large.

## Recovery

| Symptom | What happened | Fix |
|---|---|---|
| `Error acquiring the state lock` and the holder is gone | Process died mid-operation | Confirm the holder is dead, then `terraform force-unlock <ID>` |
| Plan wants to create everything | Wrong backend key, wrong workspace, or empty state | Check `terraform workspace show` and the backend key before anything else |
| An object exists but Terraform plans to create it | It is not in state | `import` block, not `apply` |
| An object is in state but gone in reality | Deleted outside Terraform | Let the refresh remove it, or `removed` block if it should also leave the configuration |
| State written with a newer runtime than the one you have | State format is forward-only | Upgrade the runtime; downgrading requires the versioned backup |
| `state rm` on the wrong address | Object is now unmanaged | Restore the previous object version from the backend, or re-adopt with `import` |

Object versioning on the backend is what makes half of this table recoverable, which is why it
belongs in the backend setup rather than in a runbook.

<!-- sources: antonbabenko-terraform, hashicorp-agent-skills, opentofu-docs, terraform-docs-site -->
