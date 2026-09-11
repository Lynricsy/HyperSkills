<!-- Adapted from hashicorp/agent-skills (MPL-2.0); see NOTICE.md -->

# HCL style, expressions and value contracts

Verified against: Terraform 1.16, OpenTofu 1.12.

## Contents

- [File layout](#file-layout)
- [Naming](#naming)
- [Block and argument order](#block-and-argument-order)
- [Variables](#variables)
- [Outputs](#outputs)
- [Locals](#locals)
- [Type constraints](#type-constraints)
- [Expressions worth knowing](#expressions-worth-knowing)
- [`dynamic` blocks](#dynamic-blocks)
- [`lifecycle` and `check`](#lifecycle-and-check)
- [Formatting gate](#formatting-gate)

## File layout

One conventional split, applied at every level (root module and each child module):

| File | Contents |
|---|---|
| `terraform.tf` | The `terraform {}` block only: `required_version`, `required_providers`, `backend` |
| `providers.tf` | `provider` blocks, including aliased ones |
| `main.tf` | Resources and data sources; split into topic files (`network.tf`, `database.tf`) once it passes a few hundred lines |
| `variables.tf` | Input variables, alphabetical |
| `outputs.tf` | Outputs, alphabetical |
| `locals.tf` | `locals` blocks, when there are enough to be worth finding |

Terraform reads every `.tf` file in the directory and does not care which one a block is in,
so the value here is purely that a reader knows where to look. Keeping `required_version`
and `required_providers` in their own file also makes the version-bump commit trivially
reviewable. [official]

`.gitignore` must exclude `.terraform/`, `terraform.tfstate*`, `*.tfplan` and any `.tfvars`
holding real values. It must **not** exclude `.terraform.lock.hcl`: the lock file is the
record of which provider versions were verified, and it belongs in the repository. [official]

## Naming

- Lowercase with underscores for every identifier: resources, data sources, variables,
  outputs, locals, modules.
- The label describes the *role*, not the type: `aws_instance.web_api`, not
  `aws_instance.web_api_instance` or `aws_instance.webAPI`.
- Singular labels even when the resource has `count` or `for_each` — the label names the kind
  of thing, the key names the instance.
- `main` is correct only when the module has exactly one resource of that type and the role is
  already implied by the module (`aws_vpc.main` inside a `vpc` module). A configuration where
  every resource is called `main` has thrown away the only naming affordance HCL gives. [official]
- Prefix variables with what they qualify (`vpc_cidr_block`, not `cidr`) so a caller reading
  the module invocation can tell what a value is for. [community]

## Block and argument order

Inside a `resource` or `module` block: [official]

```hcl
resource "aws_instance" "web_api" {
  # 1. meta-arguments that control instance count
  for_each = var.instances

  # 2. arguments, required before optional
  ami           = each.value.ami
  instance_type = each.value.instance_type

  # 3. nested blocks
  root_block_device {
    volume_size = 20
  }

  # 4. lifecycle and depends_on, last
  lifecycle {
    create_before_destroy = true
  }
}
```

Some community guidance puts `depends_on` at the top of the block. Follow the order above
instead: `for_each`/`count` decide whether the block produces one object or fifty, which is
what a reader needs first, and the trailing meta-arguments are exceptional enough to belong
at the end where they stand out.

Inside a `variable` block: `description`, `type`, `default`, `nullable`, `sensitive`,
`ephemeral`, then `validation`.

## Variables

Every variable gets a `type` and a `description`. An untyped variable accepts anything and
surfaces the mistake as a provider error hundreds of lines away from the caller that made it.

```hcl
variable "environment" {
  description = "Deployment environment; selects sizing and retention defaults."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of dev, staging, prod."
  }
}
```

- `nullable = false` (Terraform 1.1+/OpenTofu 1.6+) stops an explicit `null` from a caller
  overriding the default with nothing. Without it, `environment = null` silently produces a
  null value rather than the default. [official]
- `validation` runs at plan time. Write the `error_message` as an instruction, not a
  restatement: the message is the only thing the caller sees.
- A `validation` block may reference other variables from Terraform 1.9+/OpenTofu 1.9+, which
  is how you express "if `enable_ha` then `subnet_ids` must have at least two entries" without
  a postcondition on a resource.
- `sensitive = true` affects display only. It does not keep the value out of state; use an
  `ephemeral` variable or a write-only argument when the value must never be persisted.
- A variable with no `default` is required. Use that rather than a default that is a plausible
  wrong answer; a missing value should fail, not deploy to the wrong place.

## Outputs

```hcl
output "subnet_ids" {
  description = "Map of availability zone to subnet ID."
  value       = { for zone, subnet in aws_subnet.public : zone => subnet.id }
}
```

- Every output needs a `description`; it is what `terraform-docs` renders and what a consumer
  reads.
- Export named attributes, not whole resource objects. `value = aws_instance.web` makes every
  attribute of that resource part of your module's public interface, so a provider upgrade
  that renames one becomes a breaking change to your module.
- Mark outputs `sensitive` when they carry a secret, and remember that a sensitive output can
  still be consumed by a caller — it is a display guard, not an access control.
- Terraform 1.15+ allows an explicit type constraint on an output, which is worth using on a
  module's headline outputs so a refactor that changes the shape fails in the module rather
  than in the caller.
- Outputs can be marked `deprecated` (Terraform 1.15+, **OpenTofu 1.10+**) to warn consumers
  before removal.

## Locals

Locals are for a value used more than once, or for an expression complex enough that naming
it is the documentation. A local used once and named `local.tmp` is noise.

One high-value pattern: a local that prefers a conditional resource's attribute and falls back
to its parent forces the correct destroy order without an explicit `depends_on`, because the
dependency is expressed through the value rather than declared beside it.

```hcl
locals {
  # Reading through the association when it exists makes every consumer depend on it,
  # so the association is destroyed before the VPC it extends.
  vpc_cidr = try(aws_vpc_ipv4_cidr_block_association.secondary[0].cidr_block, aws_vpc.main.cidr_block)
}
```

## Type constraints

Prefer the simplest type that expresses the contract. Reach for `object()` when the module
needs to validate the shape, and use `optional()` with a default rather than accepting
`map(any)`:

```hcl
variable "instances" {
  description = "Instance name to configuration."
  type = map(object({
    instance_type = string
    volume_size   = optional(number, 20)
    public        = optional(bool, false)
  }))
  default = {}
}
```

`optional(number, 20)` (Terraform 1.3+/OpenTofu 1.6+) fills the default during type
conversion, so the module body can read `each.value.volume_size` without a `coalesce`. With
`map(any)` the caller's typo becomes a runtime error inside a provider instead of a type
error at the boundary. [official]

`convert()` (Terraform 1.15+, Terraform-only) performs a precise inline conversion where the
implicit rules would guess wrong.

## Expressions worth knowing

| Instead of | Write | Why |
|---|---|---|
| `element(concat(aws_x.y.*.id, [""]), 0)` | `try(aws_x.y[0].id, null)` | `try` (0.12.20+) states the fallback; the concat idiom hides an index bug |
| `aws_subnet.public.*.id` | `[for s in aws_subnet.public : s.id]` or `values(...)` | Splat on a `for_each` resource returns values in map-key order and reads as if it were a list; the `for` expression says what it does |
| `lookup(var.m, "k", d)` | `var.m["k"]` with `optional()` in the type, or `try(var.m.k, d)` | `lookup` with a default silently accepts a map missing required keys |
| `join("-", [var.a, var.b])` | `"${var.a}-${var.b}"` | Interpolation is clearer for a fixed number of parts |
| `count = var.list == [] ? 0 : 1` | `count = length(var.list) > 0 ? 1 : 0` | Collection equality on an empty tuple is a common source of `Inconsistent conditional result types` |

Do not wrap a whole expression in `"${...}"`. `ami = "${var.ami}"` is the same as
`ami = var.ami`, and `terraform fmt` will not remove it for you.

## `dynamic` blocks

`dynamic` generates repeated nested blocks from a collection. It is the right tool exactly
when the provider models something as a repeatable block and the count is data-driven:

```hcl
dynamic "ingress" {
  for_each = var.ingress_rules
  content {
    from_port   = ingress.value.from_port
    to_port     = ingress.value.to_port
    cidr_blocks = ingress.value.cidr_blocks
  }
}
```

Two caveats. A `dynamic` block over a set produces instances the plan cannot address
individually, so a one-element change can render as a whole-block replacement in the diff.
And where the provider offers separate rule *resources* instead of nested blocks, use those —
a nested-block rule set is replaced wholesale on any change, while separate resources are
planned individually. [community]

## `lifecycle` and `check`

- `create_before_destroy = true` is required whenever a replacement cannot coexist with its
  predecessor's name or attachment; it propagates to everything the resource depends on, so
  expect the plan to grow.
- `prevent_destroy = true` turns an accidental destroy into a plan error. It cannot stop a
  destroy that comes from removing the block itself. OpenTofu 1.12+ allows the argument to
  reference other symbols such as input variables; Terraform requires a literal.
- `ignore_changes = [tags["LastScanned"]]` with a comment naming the system that writes the
  attribute is maintenance. `ignore_changes = all` stops Terraform managing the resource in
  all but name.
- `replace_triggered_by` replaces a resource when a referenced object changes — the declarative
  form of the old `null_resource` trigger hack.
- `check` blocks (Terraform 1.5+/OpenTofu 1.6+) assert post-apply conditions and emit warnings
  rather than failing the apply, which makes them right for continuous assertions ("the
  health endpoint answers") and wrong for input validation. Input validation belongs in the
  variable.

## Formatting gate

```bash
terraform fmt -recursive          # rewrite
terraform fmt -check -recursive   # CI: non-zero exit if anything is unformatted
terraform validate                # syntax + internal consistency, offline
```

`validate` needs `terraform init` to have run so the provider schemas are present; use
`init -backend=false` in CI so validation never takes a state lock. `validate` does not call
any provider API, so it cannot tell you that an argument's *value* is invalid — that is what
`plan` and `tflint` are for.

<!-- sources: hashicorp-agent-skills, antonbabenko-terraform, awesome-copilot-terraform, opentofu-docs, terraform-docs-site -->
