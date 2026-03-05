terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.9.0, < 7.0.0"
    }
  }

  required_version = ">= 1.14"
}

data "aws_caller_identity" "current" {}
