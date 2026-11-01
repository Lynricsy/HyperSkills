## .github/workflows/plan.yml (relevant step, runs on our self-hosted runner)

    - run: terraform version          # Terraform v1.17.1
    - run: terraform init -input=false
    - run: terraform plan -input=false -out=tfplan -policies=./policies
      # job fails if a policy fails; green = all policies passed

## Notes from PR #212 (Sven)

- The `policies/` directory holds our new HCL policies (`require_encryption.policy.hcl`,
  `deny_public_buckets.policy.hcl`), written last week and tested with `tfpolicy test`.
  Since Terraform 1.17 made `-policies` generally available we can drop Conftest: the plan job
  has been green on every PR since we switched, so the policies are being enforced.
- Runner image: `ubuntu-24.04` + Terraform 1.17.1 from releases.hashicorp.com. Nothing else
  installed.
- The data team can use the same policies in their OpenTofu pipeline, it is all HCL anyway.
- `versions.tf` now takes the AWS provider constraint from a variable. `terraform validate`
  passes on my laptop (Terraform 1.17.1). Ready to merge?
