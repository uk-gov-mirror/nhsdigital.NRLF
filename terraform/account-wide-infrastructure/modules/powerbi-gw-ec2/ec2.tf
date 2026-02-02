resource "aws_instance" "powerbi_gw" {
  associate_public_ip_address = false
  iam_instance_profile        = aws_iam_instance_profile.powerbi_profile.name
  ami                         = local.selected_ami_id
  instance_type               = var.instance_type
  key_name                    = aws_key_pair.ec2_key_pair.key_name
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = var.security_groups

  root_block_device {
    volume_size = var.root_volume_size
    volume_type = "gp3"
    iops        = var.root_volume_iops
  }

  user_data = file("${path.module}/scripts/user_data.tpl")

  tags = {
    Name       = "${var.name_prefix}-ec2"
    PatchGroup = local.windows_patching_tag
  }

}

resource "aws_ssm_maintenance_window" "updates" {
  name     = "windows-updates"
  schedule = "cron(0 2 ? * MON *)" # Monday 2am UTC
  duration = 3
  cutoff   = 1
}

resource "aws_ssm_maintenance_window_target" "windows_instances" {
  window_id     = aws_ssm_maintenance_window.updates.id
  resource_type = "INSTANCE"

  targets {
    key    = "tag:PatchGroup"
    values = [local.windows_patching_tag]
  }
}

resource "aws_ssm_maintenance_window_task" "patch_task" {
  window_id        = aws_ssm_maintenance_window.updates.id
  task_type        = "RUN_COMMAND"
  task_arn         = "AWS-RunPatchBaseline"
  priority         = 1
  max_concurrency  = 1
  max_errors       = 1
  service_role_arn = aws_iam_role.maintenance_window_role.arn

  targets {
    key    = "WindowTargetIds"
    values = [aws_ssm_maintenance_window_target.windows_instances.id]
  }

  task_invocation_parameters {
    run_command_parameters {
      parameter {
        name   = "Operation"
        values = ["Install"]
      }
    }
  }
}

resource "aws_iam_role" "maintenance_window_role" {
  name = "maintenance-window-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ssm.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "maintenance_window_policy" {
  role       = aws_iam_role.maintenance_window_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonSSMMaintenanceWindowRole"
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
