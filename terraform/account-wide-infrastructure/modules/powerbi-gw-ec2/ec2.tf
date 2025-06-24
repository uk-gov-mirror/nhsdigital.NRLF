resource "aws_instance" "powerbi_gw" {
  associate_public_ip_address = false
  iam_instance_profile        = aws_iam_instance_profile.powerbi_profile.name
  ami                         = local.selected_ami_id
  instance_type               = var.instance_type
  key_name                    = aws_key_pair.ec2_key_pair.key_name
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = var.security_groups

  root_block_device {
    volume_size = 40
    volume_type = "gp2"
  }

  user_data = file("${path.module}/scripts/user_data.tpl")

  tags = {
    Name = "${var.name_prefix}-ec2"
  }

}

resource "tls_private_key" "instance_key_pair" {
  algorithm = "RSA"
}

resource "aws_key_pair" "ec2_key_pair" {
  key_name   = "${var.name_prefix}_PowerBI-GateWay-Key"
  public_key = tls_private_key.instance_key_pair.public_key_openssh
}

resource "local_file" "ssh_key_priv" {
  filename = "${path.module}/keys/${aws_key_pair.ec2_key_pair.key_name}.pem"
  content  = tls_private_key.instance_key_pair.private_key_pem
}
