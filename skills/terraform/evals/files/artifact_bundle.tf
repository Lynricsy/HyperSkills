# modules/artifact-bundle/main.tf
# A provider-light module we ship internally. It has no tests at all.

terraform {
  required_version = ">= 1.6"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

variable "artifacts" {
  description = "Artifact name to payload."
  type        = map(string)
}

variable "output_dir" {
  description = "Directory the bundle is written to."
  type        = string
  default     = "bundle"
}

variable "emit_manifest" {
  description = "Whether to emit a manifest file listing every artifact."
  type        = bool
  default     = true
}

variable "checksum_algorithm" {
  description = "Algorithm used for the bundle checksum."
  type        = string
  default     = "sha256"
}

locals {
  normalised = { for name, body in var.artifacts : lower(name) => trimspace(body) }
  manifest   = join("\n", sort(keys(local.normalised)))
}

resource "local_file" "artifact" {
  for_each = local.normalised

  filename = "${var.output_dir}/${each.key}.txt"
  content  = each.value
}

resource "local_file" "manifest" {
  count = var.emit_manifest ? 1 : 0

  filename = "${var.output_dir}/manifest.txt"
  content  = local.manifest
}

resource "terraform_data" "checksum" {
  input = var.checksum_algorithm == "sha256" ? sha256(local.manifest) : md5(local.manifest)
}

output "artifact_paths" {
  description = "Artifact name to written path."
  value       = { for k, v in local_file.artifact : k => v.filename }
}

output "checksum" {
  description = "Checksum over the manifest."
  value       = terraform_data.checksum.output
}
