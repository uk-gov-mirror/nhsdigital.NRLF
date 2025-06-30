resource "aws_cloudwatch_log_group" "firehose" {
  name              = "/aws/kinesisfirehose/${var.prefix}-firehose"
  retention_in_days = local.cloudwatch.retention.days
}

resource "aws_cloudwatch_log_stream" "firehose" {
  name           = "${var.prefix}-firehose"
  log_group_name = aws_cloudwatch_log_group.firehose.name
}

resource "aws_cloudwatch_log_group" "firehose_reporting" {
  name              = "/aws/kinesisfirehose/${var.prefix}-firehose-reporting"
  retention_in_days = local.cloudwatch.retention.days
}

resource "aws_cloudwatch_log_stream" "firehose_reporting" {
  name           = "${var.prefix}-firehose-reporting"
  log_group_name = aws_cloudwatch_log_group.firehose_reporting.name
}
