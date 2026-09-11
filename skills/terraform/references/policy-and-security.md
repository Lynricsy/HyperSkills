# Secrets, policy-as-code and configuration scanning

Verified against: Terraform 1.16, OpenTofu 1.12.

## Contents

- [The four ways a secret leaks](#the-four-ways-a-secret-leaks)
- [`sensitive` versus `ephemeral` versus write-only](#sensitive-versus-ephemeral-versus-write-only)
- [Where secrets should come from](#where-secrets-should-come-from)
- [Provider credentials](#provider-credentials)
- [Scanners](#scanners)
- [Policy engines](#policy-engines)
- [Writing a policy against plan JSON](#writing-a-policy-against-plan-json)
- [Where each gate belongs in the pipeline](#where-each-gate-belongs-in-the-pipeline)
- [Findings worth automating](#findings-worth-automating)

## The four ways a secret leaks

1. **Committed to the repository** — a `default` on a password variable, a populated
   `.tfvars`, a key inlined in a resource argument.
2. **Written to state** — any attribute a provider returns, including generated passwords and
   private keys. State is plaintext in every format.
3. **Printed in logs** — plan output in a CI job, `terraform output` without `-json`
   redaction, a `local-exec` provisioner echoing its input, `nonsensitive()` used to unwrap a
   value so it can be interpolated.
4. **Handed out with read access** — a `terraform_remote_state` grant, or a backend bucket
   readable by more principals than the environment's operators.

Every rule below exists to close one of these.

## `sensitive` versus `ephemeral` versus write-only

| Mechanism | Available | What it does | What it does not do |
|---|---|---|---|
| `sensitive = true` | Long-standing | Redacts the value in CLI and plan output | Keep it out of state, or out of a plan file |
| `ephemeral` variables, outputs and resources | Terraform 1.10+, **OpenTofu 1.11+** | Value exists only during one phase; never written to state or the plan file | Work in arguments that are persisted |
| Write-only arguments (`*_wo` plus `*_wo_version`) | Terraform 1.11+, OpenTofu 1.11+ | Provider accepts the value and never returns it, so it never reaches state | Exist for every argument — the provider must implement it |

The single most common misconception: `sensitive = true` is a display control. A reviewer who
sees it and concludes the secret is safe is wrong, and the state file proves it.

```hcl
variable "db_password" {
  description = "Initial password for the database admin user."
  type        = string
  sensitive   = true
  ephemeral   = true          # Terraform 1.10+, OpenTofu 1.11+
}

resource "some_database" "main" {
  password_wo         = var.db_password   # write-only: never stored in state
  password_wo_version = 1                 # bump to trigger a rotation
}
```

Where the provider offers neither, keep the secret out of Terraform: have the platform
generate it, store it in a secrets manager, and let the application read it at runtime.
Terraform then manages the *reference*, not the value.

## Where secrets should come from

- A secrets manager, read through an ephemeral resource where the provider has one, so the
  value never lands in state.
- Environment variables (`TF_VAR_*`) for CI-injected values. They are visible to the process
  and to anything that dumps the environment, so they are a step up from a committed file and
  not a vault.
- Never a `default` on the variable. A default is a value in the repository.
- Never a committed `.tfvars`. Commit `terraform.tfvars.example` with placeholders and
  gitignore the real one.

## Provider credentials

Configure providers from the environment, not from HCL. A `provider` block with
`access_key`/`client_secret`/`credentials` arguments puts the credential in the configuration
and, for some providers, in state.

Prefer, in order: workload identity federation from the CI platform (short-lived, no stored
secret), an assumed role or managed identity, a named profile locally, and a static key only
where nothing else exists. The mechanics of federating CI to a cloud belong to the CI
platform — for GitHub Actions, use the `github` skill.

## Scanners

Four different jobs, four different tools. Do not expect one to cover another's ground:

| Tool | Answers | Notes |
|---|---|---|
| `terraform fmt -check -recursive` | Is it formatted | Exit code is the gate |
| `terraform validate` | Is it syntactically valid and internally consistent | Offline; never contacts a provider, so it cannot tell you an argument *value* is wrong |
| `tflint` | Is it valid for the provider, and does it violate configured rules | Provider plugins make it aware of real resource types, argument names and deprecated values |
| `trivy config` / `checkov` | Does it violate a security or compliance rule | Operate on HCL or on plan JSON; plan JSON catches values that come from variables |

`tfsec` is no longer developed separately — it was folded into Trivy, so `trivy config` is the
current spelling of that check.

Scanning plan JSON rather than HCL matters: a rule about an open ingress range cannot see the
range when it arrives through a variable. Generate it once and feed both the policy engine and
the scanner:

```bash
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
```

The plan file and its JSON contain the values being written, including secrets. Treat both as
artefacts with the same protection as state, and never publish them to a pull-request comment
unredacted.

## Policy engines

| Engine | Language | Runs where | Choose when |
|---|---|---|---|
| Conftest (Open Policy Agent) | Rego | Any pipeline, over plan JSON | Self-hosted pipelines; you want the policies in the same repository and testable offline |
| OPA directly | Rego | Any pipeline, or a server | You already run OPA for other things |
| Sentinel | Sentinel | HCP Terraform / Terraform Enterprise only | You are on that platform and want enforcement levels (advisory / soft-mandatory / hard-mandatory) tied to runs |

For a self-managed setup, Conftest is the default: `conftest test tfplan.json` in the same job
that produced the plan, with the policies versioned beside the configuration and unit-tested
with `conftest verify`. Sentinel is not available outside HashiCorp's platform, so a policy
written in it is not portable to OpenTofu.

The `terraform-compliance` BDD project is archived; do not start new work on it.

## Writing a policy against plan JSON

The shape that matters is `resource_changes[]`, each with `type`, `address`, `change.actions`
and `change.after`:

```rego
package terraform.storage

deny contains msg if {
    resource := input.resource_changes[_]
    resource.type == "some_bucket"
    resource.change.actions[_] != "delete"
    not resource.change.after.encryption_enabled
    msg := sprintf("%s must enable encryption at rest", [resource.address])
}
```

Three habits that keep a policy set maintainable:

- Filter out deletions (`actions[_] != "delete"`), or every policy fires on teardown.
- Read from `change.after`, not from the configuration — that is the value that will exist.
- Make the message name the address and the fix. A policy failure that says only "violation"
  gets suppressed rather than fixed.

## Where each gate belongs in the pipeline

```
pre-commit        fmt, validate, tflint            fast, local, no credentials
pull request      fmt -check, validate, test,      plan artifact is the review object
                  plan -out=tfplan, policy + scan
merge / deploy    apply tfplan                     the saved artifact, not a fresh plan
scheduled         plan -detailed-exitcode          exit 2 means drift
```

The one rule that gets broken most often: **apply the plan artifact produced by the review
step**, do not re-run `plan` inside the apply job. A fresh plan can differ from the one that
was approved, which means the approval covered something else.

## Findings worth automating

These recur often enough that a rule pays for itself, and they are provider-independent
enough to state here:

- A variable with a plaintext credential default, or a committed `.tfvars` with real values.
- `sensitive = true` used where the value still lands in state and a write-only argument
  exists.
- No `required_version`, no provider `version`, or no committed `.terraform.lock.hcl`.
- A floating module reference (`?ref=main`, or a registry module with no `version`).
- `ignore_changes = all`.
- Public network exposure expressed as an unrestricted CIDR on an ingress rule.
- Encryption-at-rest arguments left at a provider default that is "off".
- A state backend with no locking, no encryption or no versioning.
- Logging or audit trails disabled on anything that holds data.

Anything more specific than this list is a rule about a particular provider's resource
arguments, which belongs in that provider's policy pack rather than here.

<!-- sources: antonbabenko-terraform, hashicorp-agent-skills, nitinjain-platform-skills, awesome-copilot-terraform, opentofu-docs, terraform-docs-site -->
