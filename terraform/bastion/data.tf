data "aws_caller_identity" "current" {}

data "aws_vpc" "bastion_vpc" {
  filter {
    name   = "tag:Name"
    values = [var.vpc_name]
  }
}

data "aws_subnet" "bastion_subnet" {
  filter {
    name   = "tag:Name"
    values = [var.subnet_name]
  }

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.bastion_vpc.id]
  }
}

data "aws_dynamodb_table" "dynamodb-table" {
  count = var.dynamodb_table_name != null ? 1 : 0
  name  = var.dynamodb_table_name
}

data "aws_kms_key" "dynamodb-table-key" {
  count  = var.dynamodb_table_name != null ? 1 : 0
  key_id = "alias/${data.aws_dynamodb_table.dynamodb-table[0].name}-key"
}

data "aws_ami" "bastion_ubuntu_ami" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = [var.ami_name_match]
  }
}
