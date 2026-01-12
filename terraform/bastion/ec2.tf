resource "aws_instance" "node" {
  ami                         = data.aws_ami.bastion_ubuntu_ami.id
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnet.bastion_subnet.id
  key_name                    = aws_key_pair.ec2_key_pair.key_name
  associate_public_ip_address = false
  iam_instance_profile        = aws_iam_instance_profile.instance-profile.name

  tags = {
    Name = "${local.prefix}-node"
  }
}

resource "aws_security_group" "node-sg" {
  name        = "${local.prefix}-node-sg"
  description = "Security group for ${aws_instance.node.id} node host"
  vpc_id      = data.aws_vpc.bastion_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "tls_private_key" "instance_key_pair" {
  algorithm = "RSA"
}

resource "aws_key_pair" "ec2_key_pair" {
  key_name   = "${local.prefix}-ec2-key-pair"
  public_key = tls_private_key.instance_key_pair.public_key_openssh
}

resource "aws_secretsmanager_secret" "bastion_ssh_key_secret" {
  name        = "${local.prefix}-ssh-key"
  description = "Private SSH key for accessing the bastion host"
}

resource "aws_secretsmanager_secret_version" "bastion_ssh_key_secret_version" {
  secret_id     = aws_secretsmanager_secret.bastion_ssh_key_secret.id
  secret_string = tls_private_key.instance_key_pair.private_key_pem
}
