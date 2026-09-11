<!-- Adapted from hashicorp/agent-skills (MPL-2.0); see NOTICE.md -->

# Refactoring: `moved`, `import`, `removed` and bulk discovery

Verified against: Terraform 1.16, OpenTofu 1.12.

## Contents

- [The one rule](#the-one-rule)
- [`moved`](#moved)
- [`import`](#import)
- [Generating configuration for an import](#generating-configuration-for-an-import)
- [Bulk discovery with `list` blocks](#bulk-discovery-with-list-blocks)
- [`removed`](#removed)
- [When to use `terraform state mv` instead](#when-to-use-terraform-state-mv-instead)
- [Splitting a monolith into modules](#splitting-a-monolith-into-modules)
- [Why `-target` is not the answer](#why--target-is-not-the-answer)

## The one rule

Terraform tracks objects by *address*, not by name or tag. Anything that changes an address —
renaming a resource label, moving it into a module, changing `count` to `for_each`, renaming
the module — is, by default, a destroy of the old address and a create of the new one. The
three refactoring blocks exist to change the address without changing the object:

| Intent | Block | Available |
|---|---|---|
| Same object, new address | `moved` | Terraform 1.1+, OpenTofu 1.6+ |
| Existing object, not yet managed | `import` | Terraform 1.5+, OpenTofu 1.6+ |
| Managed object that should stay but be forgotten | `removed` | Terraform 1.7+, OpenTofu 1.7+ |

All three are configuration, so all three are reviewable in a pull request and reproducible in
CI. The imperative equivalents (`terraform state mv`, `terraform import`, `terraform state rm`)
run on someone's laptop and leave no trace in the repository.

## `moved`

```hcl
moved {
  from = aws_instance.web
  to   = aws_instance.web_api
}

moved {
  from = aws_subnet.public[0]
  to   = module.network.aws_subnet.public["eu-west-1a"]
}

moved {
  from = module.vpc
  to   = module.network
}
```

- `from` is the *old* address as it appears in state; `to` is the new one in the current
  configuration. Get the old address from `terraform state list`, not from memory.
- A `moved` block whose `from` matches nothing in state is silently a no-op, which is why the
  plan is the gate rather than the absence of an error.
- Moving a whole module moves everything inside it; you do not need one block per resource.
- Moving between `count` and `for_each` needs one block per instance, mapping index to key.
- `moved` blocks can chain (A→B in one release, B→C in the next). Keep them for at least one
  release cycle so consumers who skipped a version still get the move, then delete them.
- Inside a published module, `moved` blocks are part of the interface: without them, a
  consumer upgrading the module gets a destroy plan.

**Gate:** the plan reports the moves and `0 to add, 0 to change, 0 to destroy`. Verified on
Terraform 1.16.2: renaming a `for_each` resource with a `moved` block produces
`# local_file.item["a"] has moved to local_file.artifact["a"]` and no create or destroy.

## `import`

```hcl
import {
  to = aws_s3_bucket.assets
  id = "acme-assets-eu-west-1"
}

# Identity form (Terraform 1.12+, OpenTofu 1.12+) — for resources whose identity
# is not a single string
import {
  to       = aws_instance.bastion
  provider = aws
  identity = {
    account_id = "123456789012"
    region     = "eu-west-1"
    id         = "i-0abc123"
  }
}

# Bulk, driven by a variable (Terraform 1.7+, OpenTofu 1.7+)
import {
  for_each = var.existing_buckets
  to       = aws_s3_bucket.legacy[each.key]
  id       = each.value
}
```

- The `id` format is per resource type and is documented on the provider's registry page for
  that resource — it is not always the ARN or the name. Getting it wrong produces an import
  error at plan time, not a wrong object, so it is a safe thing to iterate on.
- An `import` block is inert once the object is in state; the plan simply stops mentioning it.
  Remove the blocks in a follow-up commit to keep the configuration readable.
- Terraform 1.16+ supports `import` blocks inside modules. Below that, they must live in the
  root module even when the target is in a child module (`to = module.x.aws_s3_bucket.y`).
- The plan after an import must show **no changes** to the imported resource. Any diff means
  the configuration you wrote does not match the real object, and applying it would mutate
  production infrastructure that was working a moment ago.

## Generating configuration for an import

```bash
terraform plan -generate-config-out=generated.tf
```

With `import` blocks present but no matching `resource` blocks, this writes a `resource` block
per import containing every attribute the provider reported. That draft is a starting point,
not a commit:

1. Delete the computed/read-only attributes (`arn`, `id`, timestamps, anything the provider
   assigns). Leaving them in produces perpetual diffs or plan errors.
2. Replace hardcoded values with variables and locals.
3. Rename the resource labels to something meaningful — the generator emits `all_0`, `all_1`.
4. Move the blocks into the right files.
5. Re-plan; the diff must be empty.

## Bulk discovery with `list` blocks

Terraform 1.14+ only (no OpenTofu equivalent), and only for resource types whose provider
implements list resources. Check first:

```bash
terraform providers schema -json \
  | jq '.provider_schemas | to_entries
        | map({provider: (.key | split("/")[-1]),
               lists: (.value.list_resource_schemas // {} | keys)})'
```

Then declare queries in a `*.tfquery.hcl` file and run them:

```hcl
# discovery.tfquery.hcl
list "aws_instance" "production" {
  provider = aws

  config {
    filter {
      name   = "tag:Environment"
      values = ["production"]
    }
  }
  limit = 100
}
```

```bash
terraform query                                  # list what matches
terraform query -generate-config-out=imported.tf # resource + import blocks for each match
```

The generated file contains both the `resource` blocks and the identity-form `import` blocks,
so the cleanup above applies to it. Where the provider has no list resource for the type, fall
back to the provider's own CLI to enumerate objects and write the `import` blocks by hand — the
`for_each` form makes that a one-block change driven by a map.

## `removed`

```hcl
removed {
  from = aws_instance.bastion

  lifecycle {
    destroy = false     # forget the object; do not delete it
  }
}
```

- Deleting a resource block without a `removed` block plans a destroy. That is correct when
  you mean it and catastrophic when you do not.
- `destroy = false` removes the object from state and leaves it running — the declarative
  equivalent of `terraform state rm`. `destroy = true` is the same as deleting the block.
- `removed` works for modules too (`from = module.legacy`).
- Use it when handing a resource to another team's state, when adopting a managed service that
  now owns the object, and when the object was deleted outside Terraform and should also leave
  the configuration.

## When to use `terraform state mv` instead

`moved` blocks cannot cross state files. Moving an object from one state to another is still
a CLI operation:

```bash
terraform state pull > backup.tfstate           # always first
terraform state mv -state-out=../other/terraform.tfstate module.data module.data
```

Take the snapshot first, move whole modules where you can, and verify both sides plan empty
afterwards. For large splits, `removed` on the source plus `import` on the destination gives
the same outcome through reviewable configuration and is worth the extra plan cycle.

## Splitting a monolith into modules

The sequence that keeps the plan empty at every step:

1. **Enumerate** — `terraform state list` into a file. This is the authoritative list of old
   addresses.
2. **Group** by shared lifecycle, and decide the module boundary. What differs between the
   copies becomes variables.
3. **Design the interface** — typed variables with descriptions and validation, outputs that
   expose named attributes.
4. **Move the code** into `modules/<name>/`, and call it once per environment from the
   composition.
5. **Fix repetition** at the same time: index-based `count` becomes keyed `for_each`.
6. **Write every `moved` block** — root-to-module and index-to-key — in the same commit.
7. **Plan.** Zero add, zero change, zero destroy, with the moves listed. Anything else is an
   unfinished step 6.
8. **Apply**, which for a pure move is a state write with no provider calls.
9. **Test** the new module (`tests/*.tftest.hcl`), then delete the `moved` blocks a release
   later.

Do steps 5 and 6 together. Changing repetition and moving into a module in separate commits
means two risky plans instead of one, and the intermediate state has neither the old addresses
nor the new ones.

## Why `-target` is not the answer

`-target` restricts the plan to the named addresses and their dependencies. It is documented as
an exceptional measure, and there are two concrete reasons to keep it that way:

- The resulting plan is knowingly incomplete. Terraform tells you so, and any state written
  from it reflects a graph you chose rather than the one the configuration describes.
- The dependency pull is wider than it looks. A `locals` value that references a targeted
  resource makes every consumer of that local an implicit dependent, so a targeted *destroy*
  can take out resources that appear unrelated. Always run `plan -destroy` first and read the
  full list before confirming.

If applying a change is only tractable with `-target`, that is a signal about state size
(split it) or about a dependency cycle in the configuration (break it), not a workflow to
adopt. OpenTofu's `-exclude` (1.9+) is the mirror image — skip these and their dependents —
and carries exactly the same caveat.

<!-- sources: hashicorp-agent-skills, antonbabenko-terraform, opentofu-docs, terraform-docs-site, hashicorp-terraform -->
