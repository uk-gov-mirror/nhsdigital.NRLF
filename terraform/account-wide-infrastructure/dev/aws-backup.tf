
# First, we create an S3 bucket for compliance reports.
resource "aws_s3_bucket" "backup_reports" {
  bucket_prefix = "${local.prefix}-backup-reports"
}

resource "aws_s3_bucket_public_access_block" "backup_reports" {
  bucket = aws_s3_bucket.backup_reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backup_reports" {
  bucket = aws_s3_bucket.backup_reports.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_policy" "backup_reports_bucket_policy" {
  bucket = aws_s3_bucket.backup_reports.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "backup_reports_bucket_policy"
    Statement = [
      {
        Sid       = "HTTPSOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.backup_reports.arn,
          "${aws_s3_bucket.backup_reports.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
    ]
  })
}


resource "aws_s3_bucket_ownership_controls" "backup_reports" {
  bucket = aws_s3_bucket.backup_reports.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "backup_reports" {
  depends_on = [aws_s3_bucket_ownership_controls.backup_reports]

  bucket = aws_s3_bucket.backup_reports.id
  acl    = "private"
}

resource "aws_kms_key" "backup_notifications" {
  description             = "KMS key for AWS Backup notifications"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Sid    = "Enable IAM User Permissions"
        Principal = {
          AWS = "arn:aws:iam::${var.assume_account}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action   = ["kms:GenerateDataKey*", "kms:Decrypt"]
        Resource = "*"
      },
    ]
  })
}

module "source" {
  source = "../modules/backup-source"

  backup_copy_vault_account_id = jsondecode(data.aws_secretsmanager_secret_version.backup_destination_parameters.secret_string)["account-id"]
  backup_copy_vault_arn        = jsondecode(data.aws_secretsmanager_secret_version.backup_destination_parameters.secret_string)["vault-arn"]
  environment_name             = local.environment
  bootstrap_kms_key_arn        = aws_kms_key.backup_notifications.arn
  project_name                 = "${local.prefix}-"
  reports_bucket               = aws_s3_bucket.backup_reports.bucket
  terraform_role_arn           = "arn:aws:iam::${var.assume_account}:role/${var.assume_role}"

  notification_target_email_addresses = local.notification_emails

  backup_plan_config = {
    "compliance_resource_types" : [
      "S3"
    ],
    "enable" : true,
    "rules" : [
      {
        "copy_action" : {
          "delete_after" : 4
        },
        "lifecycle" : {
          "delete_after" : 2
        },
        "name" : "daily_kept_for_2_days",
        "schedule" : "cron(0 0 * * ? *)"
      }
    ],
    "selection_tag" : "NHSE-Enable-S3-Backup"
  }

  backup_plan_config_dynamodb = {
    "compliance_resource_types" : [
      "DynamoDB"
    ],
    "enable" : true,
    "rules" : [
      {
        "name" : "daily",
        "schedule" : "cron(0 0 * * ? *)",
        "copy_action" : {
          "delete_after" : 4
        },

        "lifecycle" : {
          "delete_after" : 2
        }
      },
      {
        "name" : "monthly"
        "schedule" : "cron(30 0 * * 4#1)" # first Thursday each month from 00:30
        "copy_action" : {
          "cold_storage_after" : 3,
          "delete_after" : 100 # ensures there will always be min 3
        },
        "lifecycle" : {
          "delete_after" : 2
        }

      },
      {
        "name" : "weekly"               # overlaps with monthly
        "schedule" : "cron(30 0 * * 4)" # every Thursday from 00:30 to precede releases
        "copy_action" : {
          "cold_storage_after" : 14 # ensures 2 warm including one from previous release
          "delete_after" : 100
        },
        "lifecycle" : {
          "delete_after" : 2
        }

      }
    ],
    "selection_tag" : "NHSE-Enable-DDB-Backup"
  }
}
