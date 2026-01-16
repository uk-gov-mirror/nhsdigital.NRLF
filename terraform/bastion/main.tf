provider "aws" {
  region = local.region
  assume_role {
    role_arn = "arn:aws:iam::${var.assume_account}:role/${var.assume_role}"
  }

  default_tags {
    tags = {
      project_name = local.project
    }
  }
}

terraform {
  backend "s3" {
    encrypt              = true
    region               = "eu-west-2"
    bucket               = "nhsd-nrlf--terraform-state"
    key                  = "terraform-state-bastion"
    workspace_key_prefix = "nhsd-nrlf--bastion"
    dynamodb_table       = "nhsd-nrlf--terraform-state-lock"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
