data "aws_ami" "windows-2019" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["Windows_Server-2019-English-Full-Base*"]
  }
}

data "aws_ami" "PowerBI_Gateway" {
  count       = var.use_custom_ami ? 1 : 0
  most_recent = true
  owners      = ["self"]
  filter {
    name   = "name"
    values = ["PowerBI_GW"]
  }
}
