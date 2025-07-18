locals {
  selected_ami_id = var.use_custom_ami ? data.aws_ami.PowerBI_Gateway[0].id : data.aws_ami.windows-2019.id
}
