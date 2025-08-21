resource "aws_sns_topic" "backup" {
  name              = "${local.resource_name_prefix}-notifications"
  kms_master_key_id = var.bootstrap_kms_key_arn
}

data "aws_iam_policy_document" "allow_backup_to_sns" {
  policy_id = "backup"

  statement {
    actions = [
      "SNS:Publish",
    ]

    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["backup.amazonaws.com"]
    }

    resources = [
      aws_sns_topic.backup.arn
    ]

    sid = "allow_backup"

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = ["${data.aws_caller_identity.current.account_id}"]
    }
  }
}

resource "aws_sns_topic_policy" "backup_sns_policy" {
  arn    = aws_sns_topic.backup.arn
  policy = data.aws_iam_policy_document.allow_backup_to_sns.json
}

resource "aws_sns_topic_subscription" "aws_backup_notifications_email_target" {
  count         = length(var.notification_target_email_addresses)
  topic_arn     = aws_sns_topic.backup.arn
  protocol      = "email"
  endpoint      = var.notification_target_email_addresses[count.index]
  filter_policy = jsonencode({ "State" : [{ "anything-but" : "COMPLETED" }] })
}
