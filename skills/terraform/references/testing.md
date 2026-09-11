<!-- Adapted from hashicorp/agent-skills (MPL-2.0); see NOTICE.md -->

# Testing a module with `terraform test`

Verified against: Terraform 1.16.2, OpenTofu 1.12.6 (both run the examples below unchanged).

## Contents

- [What the framework is](#what-the-framework-is)
- [File and directory layout](#file-and-directory-layout)
- [Test file structure](#test-file-structure)
- [`run` block reference](#run-block-reference)
- [`plan` versus `apply`](#plan-versus-apply)
- [Negative tests](#negative-tests)
- [Mock providers and overrides](#mock-providers-and-overrides)
- [Assertion traps](#assertion-traps)
- [Chaining runs](#chaining-runs)
- [Running and filtering](#running-and-filtering)
- [The CI gate](#the-ci-gate)
- [When Terratest is still right](#when-terratest-is-still-right)

## What the framework is

`terraform test` (Terraform 1.6+, OpenTofu 1.6+) executes `*.tftest.hcl` files against the
module in the current directory. Each `run` block is a plan or an apply with its own
variables, and each `assert` is an HCL condition evaluated against the resulting resource and
output values. Anything created by an apply-mode run is destroyed at the end, in reverse run
order.

The framework is worth using because it tests the module's *logic* — the conditionals, the
`for_each` expansion, the value transformations, the validation rules — which is where module
bugs actually live, and it does so without a cloud account whenever the provider can be
mocked or is local.

## File and directory layout

```
modules/network/
├── main.tf
├── variables.tf
├── outputs.tf
└── tests/
    ├── defaults_unit_test.tftest.hcl        # plan mode
    ├── validation_unit_test.tftest.hcl      # plan mode
    └── full_integration_test.tftest.hcl     # apply mode, creates real objects
```

`terraform test` discovers `*.tftest.hcl` under `tests/` by default
(`-test-directory=` changes it). Naming plan-mode and apply-mode suites differently is what
lets CI run the cheap ones on every pull request and the expensive ones on merge.

## Test file structure

```hcl
# Optional: applies to every run in this file
test {
  parallel = true
}

# File-level variables. Highest precedence: these override tfvars and environment.
variables {
  region        = "eu-west-1"
  instance_type = "t3.small"
}

# Optional provider configuration for the tests
provider "aws" {
  region = var.region
}

run "defaults_produce_one_subnet_per_zone" {
  command = plan

  assert {
    condition     = length(aws_subnet.private) == length(var.availability_zones)
    error_message = "Expected one private subnet per availability zone."
  }
}
```

Write `error_message` so a CI log is enough to diagnose the failure. "Assertion failed" costs
a local reproduction; "Expected one private subnet per availability zone" does not.

## `run` block reference

```hcl
run "name" {
  command  = plan          # or apply (default)
  parallel = true          # Terraform 1.9+

  variables {              # overrides the file-level block for this run
    instance_type = "t3.large"
  }

  module {                 # test a different module than the one under test
    source  = "./modules/vpc"   # local paths and registry sources only
    version = "5.0.0"           # registry sources only
  }

  providers = {            # pick an aliased or mocked provider
    aws = provider.aws.secondary
  }

  state_key = "shared"     # Terraform 1.11+: share state between runs

  plan_options {
    mode    = refresh-only
    refresh = true
    replace = [aws_instance.example]
    target  = [aws_instance.example]
  }

  assert {
    condition     = output.vpc_id != null
    error_message = "vpc_id output must be set."
  }

  expect_failures = [var.instance_count]
}
```

`module` sources in test files accept local paths and registry addresses only — not Git or
HTTP. A module that consumes a Git source cannot be substituted in a test; vendor it or
publish it.

## `plan` versus `apply`

| The value you are asserting on | Mode | Why |
|---|---|---|
| Derived from inputs: counts, names, CIDR arithmetic, tags you set | `plan` | Known before anything is created |
| A conditional resource's presence (`length(x) == 0`) | `plan` | Instance expansion happens at plan |
| A variable `validation` rejecting bad input | `plan` | Validation runs at plan |
| Provider-assigned identifiers, ARNs, generated names | `apply`, or a mock with a default | Unknown until the object exists |
| Nested blocks the provider models as a **set** | `apply`, or a `for` expression | See the traps below |

Default to `plan`. An assertion on an apply-time value in plan mode is not a flaky test; it
is a test that can never pass, because the value is `(known after apply)`.

## Negative tests

```hcl
run "rejects_unknown_environment" {
  command = plan

  variables {
    environment = "prd"
  }

  expect_failures = [var.environment]
}
```

`expect_failures` names the *object whose check should fail* — `var.x` for a variable
validation, a resource address for a precondition, `output.y` for an output precondition. The
run passes when that check fails and fails when it passes. Use it instead of matching the
error text, which changes between runtime versions.

Verified on Terraform 1.16.2 and OpenTofu 1.12.6: a `run` with `expect_failures = [var.names]`
against `validation { condition = length(var.names) > 0 }` passes when the caller supplies
an empty set.

## Mock providers and overrides

```hcl
mock_provider "aws" {
  mock_resource "aws_instance" {
    defaults = {
      id        = "i-1234567890abcdef0"
      public_ip = "203.0.113.1"
    }
  }

  mock_data "aws_availability_zones" {
    defaults = {
      names = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
    }
  }
}
```

Availability: **Terraform 1.7+**, **OpenTofu 1.8+**. This is one of the real runtime gaps — a
mocked suite silently fails to load on OpenTofu 1.6 and 1.7.

Mocks work in both `plan` and `apply` mode. Verified on Terraform 1.16.2 and OpenTofu 1.12.6:
a `command = apply` run against `mock_provider "local"` passed its assertion on the mocked
`id` and created no file on disk. Guidance that mocks are plan-mode only is stale; what apply
mode with mocks gives you is the full plan → apply → state cycle without any API call, which
is exactly what you want for asserting on values that are `(known after apply)`.

Finer-grained alternatives to a whole mock provider:

- `override_resource` / `override_data` / `override_module` replace one address's values while
  the rest of the configuration uses the real provider (Terraform 1.7+, OpenTofu 1.8+).
- `override_during = plan` makes the overridden values apply during the plan phase too
  (Terraform 1.11+); the default is `apply`.

The limits are worth stating in the module README: mock defaults are values you invented, so
the suite proves your logic and proves nothing about whether the provider will accept the
configuration.

A module whose only providers are `hashicorp/local`, `hashicorp/null` or the built-in
`terraform_data` needs no mocks at all — it creates nothing outside the working directory.

## Assertion traps

**Set-typed nested blocks cannot be indexed.** Many providers model repeated blocks as sets
(encryption rules, lifecycle rules, policy statements), and `resource.x.rule[0]` is a type
error rather than the first element. Two ways out:

```hcl
# option 1: assert over the whole set
assert {
  condition = anytrue([
    for rule in aws_s3_bucket_lifecycle_configuration.this.rule :
    rule.id == "expire-old-versions"
  ])
  error_message = "Expected an expire-old-versions lifecycle rule."
}

# option 2: assert on a computed output the module already exposes
assert {
  condition     = contains(output.lifecycle_rule_ids, "expire-old-versions")
  error_message = "Expected an expire-old-versions lifecycle rule."
}
```

**Assert on the contract, not the configuration.** An assertion that restates an argument you
just set in the same file (`condition = aws_instance.web.instance_type == "t3.small"` when the
test's own `variables` block set it) proves the framework substitutes variables. Assert on
outputs, on counts that come from expansion logic, and on values the module *computed*.

**Check the attribute exists before writing the test.** `terraform providers schema -json`
prints the real attribute names; guessing produces a test that fails for the wrong reason.

## Chaining runs

```hcl
run "create_network" {
  command = apply
}

run "app_lands_in_that_network" {
  command = plan

  variables {
    vpc_id = run.create_network.vpc_id
  }

  assert {
    condition     = aws_instance.app.subnet_id != ""
    error_message = "App instance must be placed in a subnet."
  }
}
```

`run.<name>.<output>` reads an earlier run's outputs. Each run gets its own state unless
`state_key` says otherwise (Terraform 1.11+), which is what makes `parallel = true` safe for
independent runs and unsafe for dependent ones.

Teardown runs in reverse run order, which matters when one run creates a container and a later
one fills it — the contents are destroyed first.

## Running and filtering

```bash
terraform test                                  # every *.tftest.hcl under tests/
terraform test -filter=tests/defaults_unit_test.tftest.hcl   # by FILE, repeatable
terraform test -test-directory=integration      # a directory other than tests/
terraform test -verbose                         # print the plan or state per run block
terraform test -parallelism=4                   # Terraform only
terraform test -junit-xml=report.xml            # Terraform 1.11+ GA; OpenTofu has -json-into instead
```

`-filter` selects **test files**, not run blocks — guidance that shows
`-filter=<run_block_name>` is wrong, and Terraform 1.16.2's own `-help` says
`-filter=testfile`. To run one scenario, put it in its own file.

There is no `-no-cleanup` flag on Terraform 1.16.2 or OpenTofu 1.12.6 —
`terraform test -no-cleanup` fails with `flag provided but not defined`. Leaving test
infrastructure alive for debugging is an experimental feature in Terraform alpha builds
(a `skip_cleanup` attribute plus a `terraform test cleanup` command), not something to
put in a runbook today. To inspect a failing run on a stable release, use `-verbose` and
read the printed plan or state.

## The CI gate

```bash
terraform fmt -check -recursive
terraform init -backend=false          # providers and modules, no state, no lock
terraform validate
terraform test
```

`-backend=false` matters: a pull-request job that initialises the real backend takes a state
lock and blocks whoever is deploying. Run the unit suite on every pull request; run the
apply-mode suite on merge or on a schedule, in an account that is safe to litter.

For a module that claims to support both runtimes, run the same four commands again with
`tofu`. The test files are accepted by both, so the second pass costs one job and catches the
version gaps (mocks below OpenTofu 1.8, Terraform-only language features) that a
`required_version` constraint cannot express.

## When Terratest is still right

`terraform test` cannot make assertions about the world outside Terraform. When the question
is "does the endpoint answer", "did the message arrive on the queue", "does the failover
actually fail over", the assertion needs a real client — that is Terratest (Go) or an
equivalent harness, driving `apply`, probing, then `destroy`. Keep those tests few and
scheduled; keep the `.tftest.hcl` suite fast and on every commit.

<!-- sources: hashicorp-agent-skills, antonbabenko-terraform, opentofu, opentofu-docs, terraform-docs-site -->
