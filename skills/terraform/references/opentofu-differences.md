# Terraform and OpenTofu: what is actually different

Verified against: Terraform 1.16.2, OpenTofu 1.12.6. Every version in this file was read from
the two projects' `CHANGELOG.md` on the corresponding release branch, not from release notes
summaries.

## Contents

- [The short version](#the-short-version)
- [OpenTofu-only features](#opentofu-only-features)
- [Terraform-only features](#terraform-only-features)
- [Same feature, different version](#same-feature-different-version)
- [Shared and identical](#shared-and-identical)
- [Registries and module sources](#registries-and-module-sources)
- [Licensing, and why it shows up in code review](#licensing-and-why-it-shows-up-in-code-review)
- [Writing for both](#writing-for-both)
- [Migrating between them](#migrating-between-them)

## The short version

OpenTofu forked from Terraform 1.5.x. Through 1.6 the two were interchangeable. They are not
interchangeable now: each has language features the other does not implement, and several
shared features arrived at different versions. A configuration that runs on one may fail to
parse on the other, and a version gate written as "1.9+" without naming the runtime is
usually wrong for one of them.

Practical rule: `required_version` constrains whichever binary is running, so it cannot
express "Terraform 1.11 or OpenTofu 1.10". A module supporting both needs its version floor in
the README and its real proof in a CI job that runs the test suite under both binaries.

## OpenTofu-only features

| Feature | Since | What it is |
|---|---|---|
| Client-side state encryption | 1.7 | Encrypts state and plan files before they reach the backend, with AES-GCM and key providers for passphrase (PBKDF2), AWS KMS, GCP KMS and OpenBao. Terraform relies entirely on backend-side encryption |
| `for_each` on `provider` blocks | 1.9 | An aliased provider configuration can have dynamically many instances, and each resource instance can select one. This is the clean answer to multi-region and multi-account fan-out |
| `-exclude` planning option | 1.9 | The mirror of `-target`: skip these objects and their dependents. Same caveats as `-target` |
| Variables and locals in `module` source/version and in backend blocks | 1.8 | Terraform gained the module-source half in 1.15 and still does not allow it in `backend` blocks |
| `.tofu` file extension | 1.8 | A `.tofu` file overrides the same-named `.tf`, which is how a shared repository carries OpenTofu-specific configuration |
| OCI registries for modules (`oci:` sources) and as a provider mirror | 1.10 | Distribute modules and providers through a container registry |
| `pg` backend with multiple states in one database | 1.10 | `table_name`/`index_name` spread workspaces across tables |
| `lifecycle { enabled = ... }` | 1.11 | A first-class zero-or-one toggle, replacing `count = var.x ? 1 : 0` and its `[0]` indexing |
| `lifecycle { destroy = false }` on a resource | 1.12 | Plan removes the object from state without asking the provider to destroy it |
| `prevent_destroy` referencing other symbols | 1.12 | Terraform requires a literal here |
| Symbol libraries (experimental) | 1.13 | Reusable functions and types in HCL-based libraries |

## Terraform-only features

| Feature | Since | What it is |
|---|---|---|
| Stacks (`terraform stacks`, `component`/`deployment` blocks) | 1.13 | Orchestrates many configurations as one unit. Deployment requires HCP Terraform or Terraform Enterprise |
| List resources, `.tfquery.hcl` files, `terraform query` | 1.14 | Declarative discovery of existing cloud objects and generation of `resource` + `import` blocks for them. Provider must implement list resources |
| Actions (`action` blocks, resource action triggers, `-invoke`) | 1.14 | Provider-defined imperative operations outside the CRUD model, with `on_failure` modes of `halt`/`taint`/`continue` from 1.16 |
| `import` blocks inside child modules | 1.16 | Below 1.16 they must live in the root module even when the target is in a child |
| `terraform_data` `store` block | 1.16 | Holds ephemeral and sensitive values across plan and apply |
| `convert()` function | 1.15 | Precise inline type conversion |
| Explicit type constraints on `output` blocks | 1.15 | |
| Sentinel policy enforcement | — | HCP Terraform / Terraform Enterprise only |

## Same feature, different version

This is the table that catches people, because the feature exists on both and the number does
not transfer:

| Feature | Terraform | OpenTofu |
|---|---|---|
| Mock providers (`mock_provider`, `mock_resource`, `mock_data`) | 1.7 | **1.8** |
| Test overrides (`override_resource`, `override_data`, `override_module`) | 1.7 | **1.8** |
| S3 backend native locking (`use_lockfile`) | **1.11** | 1.10 |
| `ephemeral` variables, outputs and resources | 1.10 | **1.11** |
| `deprecated` on variables and outputs | **1.15** | 1.10 |
| Variables and locals in `module` source/version | **1.15** | 1.8 |
| Identity-based `import` blocks (`identity = {...}`) | 1.12 | 1.12 |
| Write-only arguments (`*_wo`) | 1.11 | 1.11 |

Where a module must support both, the effective floor is the later of the two. A mocked test
suite, for instance, needs Terraform 1.7 **and** OpenTofu 1.8.

## Shared and identical

Everything inherited from Terraform 1.5 and most of what came after: HCL syntax and the
expression language, `moved` / `import` / `removed` / `check` blocks, `terraform test` with
`.tftest.hcl` files and their `run`/`assert`/`expect_failures` structure, provider-defined
functions, the `.terraform.lock.hcl` format, the state file format, `fmt`/`validate`/`plan`/
`apply`/`state`/`workspace` commands and their flags, and the module system.

Verified here: the same module and the same `.tftest.hcl` file pass unchanged under Terraform
1.16.2 and OpenTofu 1.12.6, and both runtimes accept `mock_provider` with `command = apply`.

## Registries and module sources

The public registries are separate (`registry.terraform.io` and `registry.opentofu.org`) and
carry the same community providers under the same namespaces, so a `source = "hashicorp/aws"`
resolves on both. Where they differ:

- The provider *binaries* are the same upstream releases; the registries are different
  distribution points, and `.terraform.lock.hcl` records hashes per registry. A lock file
  generated by one runtime may need regenerating for the other.
- OpenTofu 1.12 serves both `zh:` and `h1:` hashes from its registry, which removes most
  reasons to run `tofu providers lock` for cross-platform CI.
- OpenTofu supports `oci:` module sources and OCI provider mirrors; Terraform does not.

## Licensing, and why it shows up in code review

Terraform is Business Source Licence 1.1 from version 1.6 onward, with an additional use grant
that permits production use but not offering a competing hosted product. OpenTofu is
MPL-2.0. This is not a code-quality question and it is usually decided above the engineer
holding the file, but it does have one practical consequence worth knowing: HashiCorp's
documentation site is covered by the same licence as the product, so its text cannot be
redistributed the way an MPL or Apache document can. Quote it by link, not by paste.

## Writing for both

- Name the runtime whenever you state a version floor. "1.9+" is ambiguous; "Terraform 1.11+
  / OpenTofu 1.10+" is not.
- Prefer the intersection of the two feature sets in a shared module, and keep runtime-specific
  configuration in `.tofu` overrides if you need it.
- Do not use `terraform`/`tofu` in a script's hardcoded path; take the binary name from a
  variable so the same pipeline can run both.
- Run the test suite under both binaries in CI. That is the only thing that actually proves the
  claim; `required_version` cannot express it.

## Migrating between them

Terraform → OpenTofu at a version OpenTofu supports is mechanical: install `tofu`, run
`tofu init` against the same backend, and `tofu plan` should be empty. State format and backend
layout are compatible. Things that will stop you:

- Configuration using a Terraform-only feature (Stacks, list resources, actions, module-level
  `import` blocks).
- Sentinel policies, which have no OpenTofu equivalent — the migration target is Conftest/OPA.
- HCP Terraform's `cloud` block, which is a hosted-platform integration rather than a backend.

Going the other way is the same in reverse, plus removing anything that relies on state
encryption, provider `for_each`, `enabled`, `destroy = false` or `oci:` sources — all of which
have no Terraform equivalent and need rewriting rather than a flag change.

<!-- sources: opentofu, opentofu-docs, hashicorp-terraform, terraform-docs-site, antonbabenko-terraform -->
