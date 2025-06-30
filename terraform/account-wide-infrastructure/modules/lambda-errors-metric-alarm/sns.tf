resource "aws_sns_topic" "sns_topic" {
  name              = "${var.name_prefix}--lambda-errors-sns-topic"
  kms_master_key_id = aws_kms_key.lambda-errors-topic-key.key_id
}

resource "aws_sns_topic_subscription" "sns_subscription" {
  count     = length(var.notification_emails)
  topic_arn = aws_sns_topic.sns_topic.arn
  protocol  = "email"
  endpoint  = var.notification_emails[count.index]
}
