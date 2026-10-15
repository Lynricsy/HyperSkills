# modules/service_tags — shared by the platform team (Terraform 1.16)
# and the data team (OpenTofu 1.13.1).

terraform {
  required_version = ">= 1.15"
}

variable "service" {
  type        = string
  description = "Service name, used as the Service tag."
}

variable "default_tags" {
  type        = map(string)
  description = "Organisation-wide tags."
  default     = {}
}

variable "extra_tags" {
  type        = any
  description = "Team-specific tags. Callers pass numbers and booleans as well as strings."
  default     = {}
}

locals {
  tags = merge(
    var.default_tags,
    convert(var.extra_tags, map(string)),
    { Service = var.service },
  )
}

output "tags" {
  type        = map(string)
  description = "Merged tags to pass to every resource's tags argument."
  value       = local.tags
}
