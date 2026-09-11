# ops/platform/backend.tf  (as committed today)

terraform {
  required_version = ">= 1.5"

  backend "s3" {
    bucket = "acme-tfstate"
    key    = "platform/terraform.tfstate"
    region = "eu-west-1"
  }

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

# Someone opened the console during last week's incident and:
#   - changed the desired_count on the api service from 4 to 12
#   - created a second security group by hand ("api-hotfix-sg", sg-0f31aa9c)
#     and attached it to the service
#   - deleted the old bastion instance entirely
#
# `terraform plan` output this morning (abridged, run from a laptop):
#
#   Note: Objects have changed outside of Terraform
#     # aws_ecs_service.api has changed
#       ~ desired_count = 4 -> 12
#     # aws_instance.bastion has been deleted
#
#   Terraform will perform the following actions:
#     # aws_ecs_service.api will be updated in-place
#       ~ desired_count = 12 -> 4
#     # aws_instance.bastion will be created
#
#   Plan: 1 to add, 1 to change, 0 to destroy.
#
# There is no .terraform.lock.hcl in the repo. Two engineers ran `apply`
# at the same time yesterday and one of them got a state-version conflict
# from S3 after the fact.

resource "aws_ecs_service" "api" {
  name            = "api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 4
}

resource "aws_instance" "bastion" {
  ami           = "ami-0abc1234def567890"
  instance_type = "t3.micro"
}
