# Review thread on PR #87 (modules/service_tags)

**Platform (Terraform 1.16.2):** `terraform test` passes on our side. Ready to merge.

**Data team (OpenTofu 1.13.1):** We have not tried it yet, we pick the module up from the
`main` branch on Monday.

**Reviewer A:** `convert()` is a Terraform-only function, OpenTofu does not have it. Replace it
with `tomap()` before this lands, otherwise the data team breaks.

**Reviewer B:** The typed `output` is the nice part of this PR, keep it. And `required_version`
covers us: both binaries understand it.

**Author:** I'd like one answer: what has to change so both teams can use this module, and how
do we stop this from happening again?
