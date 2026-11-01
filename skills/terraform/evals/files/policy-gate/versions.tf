# Shared module "edge-cache", consumed by platform (Terraform 1.17.1, HCP Terraform agents)
# and by the data team (OpenTofu 1.13.2, self-hosted CI). Change in PR #212.

variable "aws_provider_version" {
  description = "Provider constraint, so each consumer can move at its own pace."
  type        = string
  default     = "~> 6.4"
}

terraform {
  required_version = ">= 1.16"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = var.aws_provider_version
    }
  }
}
