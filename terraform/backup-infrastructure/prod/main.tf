provider "aws" {
  region = "eu-west-2"

  assume_role {
    role_arn = "arn:aws:iam::${var.assume_account}:role/${var.assume_role}"
  }

  default_tags {
    tags = {
      project_name = local.project_name
      workspace    = terraform.workspace
    }
  }
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.76.0"
    }
  }

  backend "s3" {
    region               = "eu-west-2"
    bucket               = "nhsd-nrlf--terraform-state"
    dynamodb_table       = "nhsd-nrlf--terraform-state-lock"
    key                  = "terraform-state-backup-infrastructure"
    workspace_key_prefix = "nhsd-nrlf"
    encrypt              = false
  }
}
