---
name: terraform
description: "Manages infrastructure as code with Terraform or OpenTofu modules, state and providers."
license: MIT (upstream attributions in NOTICE.md)
metadata:
  author: HyperSkills
  version: "2026.09.12"
  category: framework
---

# terraform

## Scope

Covers the Terraform language and workflow, and OpenTofu as a first-class peer: HCL style
and expressions, variable/output/local design, modules and their interfaces, `count` versus
`for_each` and the resource identity that follows from the choice, state (backends, locking,
splitting, sensitive values, migration), refactoring with `moved`/`import`/`removed`,
provider and runtime version constraints, `terraform test`, policy-as-code and configuration
scanning, environment layering, the concrete feature gaps between the two runtimes, and an
entry point to writing a provider.

The body is written against **Terraform 1.16** and **OpenTofu 1.12** (the current stable
releases). Every rule that needs a newer runtime than 1.6 carries a gate such as
`(Terraform 1.11+)`; where the two runtimes differ the gate names both, because they have
diverged and a single number is now a wrong answer.

Not covered:

- Kubernetes manifests, Helm charts, Dockerfiles and container images — including the
  `kubernetes` and `helm` providers' resource fields. Use the `containers` skill.
- CI platform mechanics: workflow syntax, runners, OIDC federation to a cloud, secret
  storage, environment approvals. Use the `github` skill for GitHub Actions. This skill
  covers only what the pipeline must *run* (`fmt -check`, `validate`, `test`, a saved plan
  artifact) and why.
- The field-level schema, defaults and architecture of any specific provider's resources —
  AWS, Azure, GCP and everything else. Use the `aws`, `azure` or `gcp` skill for the
  service selection, quotas and control-plane behaviour behind those resources; read the
  provider's registry documentation or run `terraform providers schema -json` rather than
  improvising argument names.
- Bicep, CloudFormation, Pulumi, CDK and Terragrunt-style orchestration wrappers.
- HCP Terraform / Terraform Enterprise platform administration, and Stacks beyond noting
  that they exist and are Terraform-only.

Paths below are relative to this skill's directory.

## Core rules

1. Establish which runtime and which version before quoting a rule with a gate:
   `terraform version` or `tofu version`. Terraform and OpenTofu share HCL but no longer
   share features, so "1.9+" without a runtime name is a guess
   (`references/opentofu-differences.md`).
2. `count` addresses instances by list index, so removing or reordering an element renumbers
   everything after it. Measured on Terraform 1.16.2: deleting the middle element of a
   three-item `count` list plans **1 to add, 0 to change, 2 to destroy**; the same edit with
   `for_each` over the same values plans **0 to add, 0 to change, 1 to destroy**. Use
   `for_each` for any collection whose membership can change.
3. Keep `count` for exactly one job: the zero-or-one toggle, `count = var.enabled ? 1 : 0`.
   That is a boolean, not a collection, and the index never shifts.
4. `for_each` keys must be resolvable at plan time. Deriving them from another resource's
   computed attributes fails with `Invalid for_each argument`, and `depends_on` does not fix
   it — that orders apply, not plan-time evaluation. Drive keys from input variables or
   static locals and index the computed values by those keys instead.
5. Renaming a resource, moving it into a module, or switching it from `count` to `for_each`
   changes its address, and a changed address means destroy-and-create unless a `moved` block
   says otherwise (Terraform 1.1+/OpenTofu 1.6+). Emit `moved` in the same change as the
   rename and verify the plan reports moves, not replacements.
6. Adopt existing infrastructure with `import` blocks in the configuration
   (Terraform 1.5+/OpenTofu 1.6+), reviewed in the pull request, not the imperative
   `terraform import` command. Use `plan -generate-config-out=` to draft the HCL, then delete
   the computed attributes it emits before committing.
7. Removing a resource from the configuration destroys the real object. When the object must
   survive, use a `removed` block (Terraform 1.7+/OpenTofu 1.7+) rather than deleting the
   resource block and hoping.
8. `-target` is a recovery tool, not a workflow. It applies a deliberately incomplete graph,
   and a `locals` value that references a targeted resource silently pulls every consumer in
   with it. If a plan is only safe when targeted, the state is too big — split it.
9. `sensitive = true` masks a value in CLI output and nothing more; the value is still in
   state in plaintext. Keep the secret out of state instead: an `ephemeral` variable or
   resource (Terraform 1.10+/OpenTofu 1.11+), a write-only argument (`*_wo`, Terraform
   1.11+/OpenTofu 1.11+), or a runtime lookup outside Terraform.
10. Treat the state file as a credential store regardless of what it contains today. It holds
    every attribute in plaintext in every format, so backend encryption, versioning and
    narrow access are part of configuring a backend, not a later hardening pass. OpenTofu
    additionally offers client-side state encryption (OpenTofu 1.7+); Terraform has no
    equivalent.
11. Never run a team or production workflow on local state. A remote backend is what provides
    locking; without it two concurrent applies race and the loser's writes are lost.
12. On the S3 backend, use the native lock file (`use_lockfile = true`) rather than a DynamoDB
    table — generally available in **Terraform 1.11** and **OpenTofu 1.10**. Below those
    versions the DynamoDB table is still required.
13. Pin the runtime with `required_version` and every provider with a `version` constraint,
    and commit `.terraform.lock.hcl`. Without the lock file, CI and a laptop can resolve
    different provider versions and produce different plans from identical configuration.
14. Every variable declares `type` and `description`; every output declares `description`.
    An untyped variable accepts anything and fails deep inside a provider call instead of at
    the boundary. Use `validation` blocks so bad input fails at plan time with a message that
    names the fix.
15. Prefer `optional()` with a typed default inside an `object()` over `map(any)`
    (Terraform 1.3+/OpenTofu 1.6+). `any` defers the type error to the consumer and defeats
    the module's own contract.
16. A module's outputs are its API. Expose the specific attributes callers need, not whole
    provider objects — re-exporting a resource means every provider upgrade is a breaking
    change to the module's interface.
17. Keep the module hierarchy shallow. A module wrapping a single resource adds an
    indirection and no encapsulation; a module three levels deep makes every variable a
    pass-through. Group by shared lifecycle, not by resource type.
18. Pin module sources by exact version for registry and Git sources
    (`version = "5.1.2"` or `?ref=v5.1.2`). A floating module reference makes the plan
    depend on when it was run.
19. Size state by blast radius: one apply should not be able to touch two environments. Split
    by environment first, then by component when teams or change cadence diverge. Separate
    root directories with separate backend keys beat CLI workspaces, which share one backend
    configuration and are easy to apply against by accident.
20. Reserve `terraform_remote_state` for genuine ownership boundaries between separately
    owned stacks. Inside one team's stack it is glue that couples two states without the
    module system's contract.
21. Name resources for the role they play, without repeating the resource type
    (`aws_instance.web_api`, not `aws_instance.web_api_instance`). `main` is the right label
    only when the module has exactly one resource of that type and no role to describe.
22. Order arguments inside a block the way the official style guide does: `count`/`for_each`
    first, then arguments, then nested blocks, then `lifecycle` and `depends_on` last. The
    meta-arguments that control how many instances exist belong where a reader sees them
    first.
23. `ignore_changes` on a named attribute with a comment naming the external system that
    writes it is maintenance; `ignore_changes = all` is abandonment — it hides every future
    drift on that resource.
24. `terraform test` needs no cloud account to be useful. `command = plan` can assert on
    instance counts, values derived from inputs, and outputs; `expect_failures` asserts that
    a `validation` block rejects bad input. Reach for `mock_provider` only when a real
    provider would otherwise be contacted (Terraform 1.7+, **OpenTofu 1.8+**).
25. `command = plan` cannot assert on values that only exist after apply. An assertion on a
    generated identifier or an API-assigned attribute in plan mode is a test that can never
    pass; move that run block to `command = apply` and accept that it creates real objects.
26. Finish with the gate: `terraform fmt -check -recursive`, `terraform validate`,
    `terraform test`, and a `plan` whose diff is what you claimed it would be. `validate`
    checks syntax and internal consistency only — it does not contact a provider, so it
    cannot tell you an argument value is wrong.

## Workflows

### refactor-copy-pasted-config-into-modules

- [ ] Record the current addresses before touching anything: `terraform state list`, and
      `terraform show -json` when you need resolved values. Do not parse the raw state file;
      it is not a stable interface and it contains secrets (`references/state.md`).
- [ ] Group the repeated resources by shared lifecycle and decide the module boundary. What
      differs between the copies becomes variables; what is identical stays inside
      (`references/modules.md`).
- [ ] Design the interface before moving code: typed variables with descriptions and
      `validation`, `optional()` for optional object attributes, outputs that expose named
      attributes rather than whole objects.
- [ ] Replace index-based repetition with `for_each` over a keyed collection, choosing keys
      that are stable properties of the thing (a name, a zone) and never a position.
- [ ] Write one `moved` block per address that changes — root-to-module, and every
      `[0]`→`["key"]` — in the same commit as the move (`references/refactoring.md`).
- [ ] Split the state if the refactor exposed that several environments share one file, and
      migrate each with `init -migrate-state` against a fresh backend key.
- [ ] **Gate — the refactor moved nothing real:** `terraform plan` reports `0 to add,
      0 to change, 0 to destroy` and lists the moves. Any create or destroy in that plan is an
      unfinished `moved` block, not an acceptable side effect.

### reconcile-state-with-reality

- [ ] Look before acting: `terraform plan -refresh-only` shows what changed outside Terraform
      without proposing to undo it. Do not run a normal `apply` first
      (`references/state.md`).
- [ ] Classify each drift by its remedy — the change is wanted and belongs in the
      configuration; the object was created by hand and must be adopted; or the object is gone
      and must leave the state.
- [ ] Adopt hand-made objects with `import` blocks, generating a first draft via
      `plan -generate-config-out=` and then removing the computed attributes and hardcoded
      values from it (`references/refactoring.md`).
- [ ] Retire objects that must not be destroyed with `removed` blocks; delete the resource
      block only when destroying the object is the intent.
- [ ] Resist `-target` for the partial apply. If the reconciliation is only tractable in
      pieces, do it in ordered commits with full plans instead.
- [ ] Fix what let the drift persist: state locking on the backend, a committed lock file,
      and a scheduled `plan -detailed-exitcode` that fails when the diff is non-empty.
- [ ] **Gate — the diff is empty:** a full `terraform plan` reports no changes, and
      `terraform state list` contains exactly the objects the configuration declares.

### write-tests-for-a-module

- [ ] Put `*.tftest.hcl` files under `tests/` and name them so plan-mode and apply-mode suites
      can be filtered apart in CI (`references/testing.md`).
- [ ] Start with plan-mode runs: default behaviour, each significant input combination, and
      the conditional resources (`length(resource.name) == 0` when disabled).
- [ ] Assert on the module's contract — outputs and the arguments a consumer sets — not on
      every attribute of every resource. A test that restates the configuration fails on every
      refactor and catches nothing.
- [ ] Cover the rejection path with `expect_failures` pointing at the variable whose
      `validation` should fire, rather than matching an error string.
- [ ] Add `mock_provider` only for providers that would otherwise make API calls, and note
      the runtime floor: Terraform 1.7+, OpenTofu 1.8+.
- [ ] Promote to `command = apply` only the assertions that need apply-time values, and say
      in the module README that those runs create real objects.
- [ ] **Gate — the suite runs clean from a cold checkout:** `terraform fmt -check -recursive`,
      `terraform init -backend=false`, `terraform validate`, `terraform test` all exit 0 in a
      directory with no `.terraform/`. Run the same files under both binaries if the module
      claims to support both.

### review-a-terraform-change

- [ ] Read the plan, not just the diff. A configuration change that looks cosmetic and a plan
      that contains a destroy are the same review finding, and only the plan shows it.
- [ ] Check identity first: renamed or re-keyed addresses without `moved`, `count` where the
      collection can change, `for_each` keys derived from computed values.
- [ ] Check the blast radius: what else is in this state, whether the change needs `-target`
      to be safe, whether `prevent_destroy` belongs on anything in the path.
- [ ] Check secrets: plaintext defaults, `sensitive` used as if it protected state, secrets
      passed into arguments that persist (`references/policy-and-security.md`).
- [ ] Check pinning: `required_version`, provider constraints, module `version`, lock file
      updated in the same commit as any provider bump and nothing else in that commit.
- [ ] Run the scanners rather than reasoning about them: `terraform fmt -check`, `tflint`, and
      a policy or security scan over the plan JSON.
- [ ] **Gate — every finding is reproducible:** each one names a file and line and either a
      command that shows it or the plan line that proves it.

### migrate-or-split-state

- [ ] Snapshot first: `terraform state pull > backup.tfstate`, stored where the plaintext is
      as protected as the backend itself.
- [ ] Decide the split by ownership and cadence, not by tidiness, and write down which
      addresses go where before moving anything (`references/state.md`).
- [ ] Move addresses with `terraform state mv` between states (`-state-out`), or by pointing a
      new root at a fresh backend key and importing — whichever leaves a reviewable artefact.
- [ ] Replace cross-state references with explicit inputs where you can, and
      `terraform_remote_state` only where the boundary is a real ownership boundary.
- [ ] Re-run `init -migrate-state` for backend changes and answer the copy prompt
      deliberately; `-reconfigure` discards the existing state association instead of moving it.
- [ ] **Gate — both sides are whole:** each state's `terraform plan` is empty, and the union of
      `terraform state list` across the new states equals the original list.

## Topic router

| Topic | Read when | File |
|---|---|---|
| File layout, naming, block and argument ordering, expressions, `for`/`dynamic`/splat, type constraints, `optional()`, `try()`, variable and output contracts, `validation` and `check` | Writing or reviewing HCL, or deciding how a value should be typed and validated | `references/hcl-style.md` |
| Module hierarchy and boundaries, interface design, source and version pinning, nesting depth, `count` versus `for_each` and resource identity, `terraform_remote_state`, module release checklist | Extracting, publishing or consuming a module, or choosing a repetition construct | `references/modules.md` |
| Backend selection and configuration, locking, splitting and sizing state, workspaces versus directories, sensitive values in state, backend migration, drift detection, recovery from a stuck lock or a corrupt state | Configuring a backend, splitting state, or recovering from a state incident | `references/state.md` |
| `moved`, `import` (including `for_each` and identity forms), `removed`, `terraform state mv`, `list` blocks and `terraform query` for bulk discovery, generated-configuration cleanup | Changing addresses, adopting existing infrastructure, or retiring resources without destroying them | `references/refactoring.md` |
| `.tftest.hcl` structure, `run`/`assert`/`expect_failures`/`plan_options`/`module`, plan versus apply mode, mock providers and overrides, set-type assertion traps, the CI command sequence, when Terratest is still the right tool | Writing or fixing tests for a module | `references/testing.md` |
| Secrets that must not reach state, `sensitive` versus `ephemeral` versus write-only, policy engines (OPA/Conftest, Sentinel) and where they belong in the pipeline, configuration scanners, provider credential handling, the recurring findings worth automating | Reviewing for security, or adding a policy or scanning gate | `references/policy-and-security.md` |
| Feature-by-feature differences with the runtime that has each one, state encryption, provider `for_each`, `-exclude`, `enabled`, OCI sources, Stacks, list resources and actions, migration between the two | Supporting both runtimes, or deciding whether a feature exists on the target | `references/opentofu-differences.md` |
| Plugin Framework resource and data-source structure, schema and plan modifiers, not-found and drift handling, waiters for eventually consistent APIs, acceptance tests, SDKv2 muxing and migration, generated documentation | Writing or reviewing a provider rather than a configuration | `references/provider-development.md` |

## Output format

When reviewing configuration, group findings by file and lead each with the location and the
consequence, not the rule name:

```
platform/network/main.tf:34 - identity - aws_subnet.public uses count over var.azs, so
  removing eu-west-1b renumbers [2] into [1]: plan shows 2 destroy + 1 add for subnets that
  did not change. Switch to for_each over toset(var.azs) plus three moved blocks.
```

Order findings by blast radius: anything that plans a destroy or leaks a secret first, then
correctness, then maintainability, then style. Quote the plan line (`# X will be destroyed`,
`Plan: 1 to add, 0 to change, 2 to destroy`) as the evidence for a destructive finding rather
than asserting it, and give the before/after HCL for each fix.

Say explicitly when a configuration is fine as written. Two acceptable spellings of the same
thing — `toset(var.list)` versus a map, `merge()` versus `default_tags` — are not findings,
and reporting them buries the ones that are.

## Environment

- Both runtimes are single static binaries, so pinning the exact version in CI and in the
  developer's environment is cheap and removes a whole class of "works on my machine" plan
  differences. `terraform version` / `tofu version` is the first command of any diagnosis.
- `terraform init -backend=false` initialises providers and modules without touching a
  backend — this is what `validate` and `test` need in CI, and it keeps a pull-request job
  from acquiring a state lock.
- `terraform validate` runs offline against the schemas already downloaded by `init`; it
  never contacts a provider API. `tflint` adds provider-aware linting, and `trivy config` or
  `checkov` add security rules. Each is a separate binary; check it is installed rather than
  writing a pipeline step that silently passes when the tool is missing.
- `terraform-docs` generates the inputs/outputs tables in a module README from the
  configuration itself, so a stale table is a missing pipeline step rather than a writing
  problem.
- A module that depends only on `hashicorp/local`, `hashicorp/null` or `terraform_data` can be
  planned, tested and applied with no credentials at all — useful for reproducing a language
  question in seconds instead of arguing about it.
