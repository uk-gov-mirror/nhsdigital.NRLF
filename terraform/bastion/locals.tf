locals {
  region  = "eu-west-2"
  project = "nhsd-nrlf--${var.bastion_name}-bastion"
  prefix  = local.project
}
