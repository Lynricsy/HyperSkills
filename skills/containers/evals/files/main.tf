provider "aws" {
  region = "eu-west-1"
}

resource "aws_s3_bucket" "reports_eu" {
  bucket = "acme-reports-eu"
  tags = {
    team = "data"
    env  = "prod"
  }
}

resource "aws_s3_bucket_versioning" "reports_eu" {
  bucket = aws_s3_bucket.reports_eu.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "reports_us" {
  bucket = "acme-reports-us"
  tags = {
    team = "data"
    env  = "prod"
  }
}

resource "aws_s3_bucket_versioning" "reports_us" {
  bucket = aws_s3_bucket.reports_us.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "reports_ap" {
  bucket = "acme-reports-ap"
  tags = {
    team = "data"
    env  = "staging"
  }
}

resource "aws_s3_bucket_versioning" "reports_ap" {
  bucket = aws_s3_bucket.reports_ap.id
  versioning_configuration {
    status = "Suspended"
  }
}
