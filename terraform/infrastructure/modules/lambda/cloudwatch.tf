resource "aws_cloudwatch_log_group" "lambda_cloudwatch_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.lambda_function.function_name}"
  retention_in_days = var.retention
  kms_key_id        = var.kms_key_id
}

resource "aws_cloudwatch_log_subscription_filter" "lambda_log_filter" {
  for_each = var.firehose_subscriptions

  name            = "${aws_lambda_function.lambda_function.function_name}_${each.key}_filter"
  log_group_name  = aws_cloudwatch_log_group.lambda_cloudwatch_log_group.name
  role_arn        = each.value.role.arn
  destination_arn = each.value.destination.arn
  filter_pattern  = each.value.filter.pattern
}
