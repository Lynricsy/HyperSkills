# platform/network/main.tf
# Grown by copy-paste over two years. Three environments, three near-identical blocks each.

terraform {
  backend "s3" {
    bucket = "acme-tfstate"
    key    = "network/terraform.tfstate"
    region = "eu-west-1"
  }
}

provider "aws" {
  region = "eu-west-1"
}

variable "azs" {
  default = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
}

variable "db_password" {
  default = "Sup3rSecret!"
}

resource "aws_vpc" "dev" {
  cidr_block           = "10.10.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name = "dev-vpc"
    Env  = "dev"
  }
}

resource "aws_subnet" "dev_public" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.dev.id
  cidr_block        = cidrsubnet("10.10.0.0/16", 8, count.index)
  availability_zone = var.azs[count.index]
  tags = {
    Name = "dev-public-${count.index}"
    Env  = "dev"
  }
}

resource "aws_internet_gateway" "dev" {
  vpc_id = aws_vpc.dev.id
  tags = {
    Name = "dev-igw"
  }
}

resource "aws_vpc" "staging" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name = "staging-vpc"
    Env  = "staging"
  }
}

resource "aws_subnet" "staging_public" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.staging.id
  cidr_block        = cidrsubnet("10.20.0.0/16", 8, count.index)
  availability_zone = var.azs[count.index]
  tags = {
    Name = "staging-public-${count.index}"
    Env  = "staging"
  }
}

resource "aws_internet_gateway" "staging" {
  vpc_id = aws_vpc.staging.id
  tags = {
    Name = "staging-igw"
  }
}

resource "aws_vpc" "prod" {
  cidr_block           = "10.30.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name = "prod-vpc"
    Env  = "prod"
  }
}

resource "aws_subnet" "prod_public" {
  count             = length(var.azs)
  vpc_id            = aws_vpc.prod.id
  cidr_block        = cidrsubnet("10.30.0.0/16", 8, count.index)
  availability_zone = var.azs[count.index]
  tags = {
    Name = "prod-public-${count.index}"
    Env  = "prod"
  }
}

resource "aws_internet_gateway" "prod" {
  vpc_id = aws_vpc.prod.id
  tags = {
    Name = "prod-igw"
  }
}

output "prod_subnets" {
  value = aws_subnet.prod_public.*.id
}
