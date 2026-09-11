<!-- Adapted from hashicorp/agent-skills (MPL-2.0); see NOTICE.md -->

# Modules, repetition and resource identity

Verified against: Terraform 1.16, OpenTofu 1.12.

## Contents

- [When a module earns its keep](#when-a-module-earns-its-keep)
- [The three module scales](#the-three-module-scales)
- [Standard layout](#standard-layout)
- [Interface design](#interface-design)
- [Sources and version pinning](#sources-and-version-pinning)
- [`count` versus `for_each`](#count-versus-for_each)
- [Migrating `count` to `for_each`](#migrating-count-to-for_each)
- [`for_each` keys must be known at plan time](#for_each-keys-must-be-known-at-plan-time)
- [Crossing state boundaries](#crossing-state-boundaries)
- [Release checklist](#release-checklist)

## When a module earns its keep

A module is worth creating when the same group of resources is instantiated more than once,
or when a boundary needs an enforced contract. It is not worth creating for:

- A single resource. `module "bucket"` wrapping one `aws_s3_bucket` adds a variable for every
  argument and hides the provider's documentation from the reader.
- Grouping by resource type ("all the IAM", "all the security groups"). Group by shared
  lifecycle — the things created, changed and destroyed together.
- Depth. Every level of nesting turns real arguments into pass-through variables. Two levels
  (composition → module) is normal; a third needs a reason. [official]

## The three module scales

| Scale | What it contains | Owns |
|---|---|---|
| Resource module | One logical group of directly connected resources — a network and its subnets, a queue and its policy | No environment values |
| Infrastructure module | Several resource modules that together deliver a capability | No environment values |
| Composition (root) | The modules for one environment, plus the concrete values | Backend, provider config, environment values |

The rule that makes this useful: **concrete values live only in the composition.** A module
that hardcodes an account, region, environment name or CIDR cannot be reused, and a
composition that contains resource blocks rather than module calls will be copy-pasted for
the next environment. [community]

## Standard layout

```
modules/network/
├── README.md          # purpose, usage, inputs, outputs (generate with terraform-docs)
├── terraform.tf       # required_version + required_providers, no backend
├── main.tf
├── variables.tf
├── outputs.tf
├── examples/
│   ├── minimal/       # smallest working call
│   └── complete/      # every feature exercised
└── tests/
    └── defaults.tftest.hcl
```

A child module declares `required_providers` but never a `backend` and never a `provider`
block — the provider configuration is the composition's job, passed in via `providers = {}`
when a module needs an aliased one. A module with its own `provider` block cannot be removed
from a configuration cleanly, because Terraform needs the provider configuration to destroy
the resources it created.

`examples/` doubles as documentation and as test fixtures, which is the reason to keep them
runnable rather than illustrative.

## Interface design

- Types and descriptions on everything; `validation` on anything with a shape the module
  depends on, so bad input fails at the boundary rather than inside a provider call.
- Give the caller one obvious way to express each intent. Two variables that can contradict
  each other (`subnet_ids` and `create_subnets`) will eventually be set inconsistently; make
  the second derivable, or validate the combination.
- Outputs are the contract: named attributes, described, with the sensitive ones marked.
  Re-exporting a whole resource object couples your interface to the provider's schema.
- Prefer a map keyed by a caller-meaningful name over a list, everywhere. Lists in a module
  interface become `count` inside it, and `count` is where identity churn comes from.
- Do not accept a `tags` map *and* apply provider-level default tags inside the module; pick
  one and document it, otherwise callers get a merge they did not ask for.

## Sources and version pinning

```hcl
module "network" {
  source  = "app.terraform.io/acme/network/aws"
  version = "5.1.2"          # exact, for anything applied to production
  # ...
}

module "queue" {
  source = "git::https://github.com/acme/tf-modules.git//queue?ref=v2.4.0"
}
```

- Registry sources take a separate `version` argument; Git sources carry the pin in `?ref=`,
  and `?ref=main` is not a pin.
- Exact pins for production. `~> 5.1` on a shared module means a plan's contents depend on
  when it ran, which makes a surprising diff impossible to attribute.
- A local `source = "../../modules/network"` path is unpinned by construction; that is fine
  inside one repository, and it is the reason a module shared across repositories should be
  published rather than submoduled.
- `terraform get -update` refreshes module sources; `init -upgrade` refreshes providers.
  Confusing the two is why "I pinned it and it still changed" happens.
- Terraform 1.15+ and OpenTofu 1.8+ allow variables and locals in `source`/`version`. It works,
  and it makes `init` depend on variable values — use it for a registry hostname, not to
  select between modules.

## `count` versus `for_each`

`count` addresses instances by position. `for_each` addresses them by key. That single
difference decides how a configuration behaves under change, measured on Terraform 1.16.2 with
three instances and the middle one removed:

| Construct | Plan after removing the middle element |
|---|---|
| `count = length(var.names)` | `1 to add, 0 to change, 2 to destroy` — index 1 is updated in place to hold what was index 2, and index 2 is destroyed |
| `for_each = toset(var.names)` | `0 to add, 0 to change, 1 to destroy` — only the removed element |

For a stateless local file that difference is a rounding error. For a database, a static IP or
anything with data on it, it is an outage.

Use `for_each` for every collection. Keep `count` for the zero-or-one toggle:

```hcl
resource "aws_nat_gateway" "main" {
  count = var.create_nat_gateway ? 1 : 0
  # ...
}
```

The toggle's index never shifts, and `length(aws_nat_gateway.main) == 0` is a clean assertion
in tests. Reference it as `aws_nat_gateway.main[0].id` or, where it may be absent,
`try(aws_nat_gateway.main[0].id, null)`.

OpenTofu 1.11+ offers `lifecycle { enabled = ... }` as a first-class spelling of that toggle,
which avoids the `[0]` indexing entirely. Terraform has no equivalent; a module that must run
on both keeps the `count` form.

## Migrating `count` to `for_each`

Do it in one commit, with the `moved` blocks in the same change:

```hcl
# before
resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  availability_zone = var.availability_zones[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
}

# after
resource "aws_subnet" "private" {
  for_each          = toset(var.availability_zones)
  availability_zone = each.key
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, index(var.availability_zones, each.key))
}

moved {
  from = aws_subnet.private[0]
  to   = aws_subnet.private["eu-west-1a"]
}
moved {
  from = aws_subnet.private[1]
  to   = aws_subnet.private["eu-west-1b"]
}
moved {
  from = aws_subnet.private[2]
  to   = aws_subnet.private["eu-west-1c"]
}
```

Two things to notice. The `cidrsubnet` offset still has to come from the *original list order*
or every subnet changes CIDR — `index(var.availability_zones, each.key)` preserves it. And the
gate is the plan: it must report the moves and `0 to add, 0 to change, 0 to destroy`. A plan
that shows creates means a `moved` block is missing or its `from` address is wrong.

Once migrated, adding a zone creates one subnet and removing one destroys one, with no
neighbouring churn.

## `for_each` keys must be known at plan time

`for_each` refuses a key set that Terraform cannot resolve during plan:

```hcl
# fails: Invalid for_each argument - keys come from IDs that only exist after apply
resource "aws_eip" "web" {
  for_each = toset([for i in aws_instance.web : i.id])
}
```

`depends_on` does not fix this; it orders apply, not plan-time evaluation. Drive `for_each`
from the same input that produced the other resource, and index the computed values by key:

```hcl
variable "instances" {
  type = map(object({ instance_type = string }))
}

resource "aws_instance" "web" {
  for_each      = var.instances
  instance_type = each.value.instance_type
}

resource "aws_eip" "web" {
  for_each = var.instances                     # same keys, known at plan
  instance = aws_instance.web[each.key].id     # computed value, looked up by key
}
```

When the key genuinely cannot be known until apply, that is what `count` with a boolean is
for — or split the configuration so the first apply produces the input to the second.

## Crossing state boundaries

`terraform_remote_state` reads another state's outputs. It is the right tool at a genuine
ownership boundary — the networking team's stack feeding the application team's — and the
wrong one inside a single team's configuration, where it couples two states without a
declared interface and makes the read order implicit.

Before reaching for it:

- If both sides are applied together, they belong in one state or one module call.
- If the value is stable (an account ID, a domain), pass it as an input variable from the
  composition.
- If the producing team is willing, a data source that looks the object up by tag or name is
  a looser coupling than reading their state, and does not require read access to it.

`terraform_remote_state` needs read access to the *entire* other state, including its secrets.
That access grant is the main argument against using it casually.

## Release checklist

- [ ] `terraform fmt -check -recursive` and `terraform validate` clean.
- [ ] `terraform test` passes from a cold checkout (`init -backend=false`).
- [ ] `examples/minimal` and `examples/complete` both plan.
- [ ] README inputs/outputs regenerated (`terraform-docs`).
- [ ] `required_version` reflects the oldest runtime actually tested, not the newest feature
      used — and names both runtimes if both are supported.
- [ ] Provider constraints are ranges (`~> 6.0`), not exact pins: a module that pins a provider
      exactly cannot be composed with any other module.
- [ ] Breaking interface changes get a major version, and the changelog names the `moved`
      blocks a consumer will need.

<!-- sources: hashicorp-agent-skills, antonbabenko-terraform, awesome-copilot-terraform, opentofu-docs, terraform-docs-site -->
