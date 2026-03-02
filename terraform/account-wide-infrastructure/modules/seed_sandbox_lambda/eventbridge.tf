resource "aws_cloudwatch_event_rule" "event_rule" {
  name                = "${var.prefix}--event_rule"
  description         = "Rule to clear and reseed sandbox data"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_target" "event_target" {
  target_id = "${var.prefix}--event_target"
  rule      = aws_cloudwatch_event_rule.event_rule.name
  arn       = aws_lambda_function.lambda_function.arn
}


resource "aws_lambda_permission" "allow_execution_from_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.event_rule.arn
}
