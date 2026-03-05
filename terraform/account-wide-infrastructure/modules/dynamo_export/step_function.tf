data "aws_iam_policy_document" "step_functions_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "step_functions_role" {
  name               = "${var.name_prefix}-dynamodb-export-sf-role"
  assume_role_policy = data.aws_iam_policy_document.step_functions_assume_role.json
}

data "aws_iam_policy_document" "step_functions_policy" {
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction",
      "lambda:ListFunctions"
    ]
    resources = [
      aws_lambda_function.dynamo_export_trigger.arn,
      aws_lambda_function.dynamo_export_poll.arn,
      aws_lambda_function.ssm_put_param.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "glue:StartJobRun",
      "glue:GetJobRun"
    ]
    resources = [aws_glue_job.glue_job.arn]
  }
}

resource "aws_iam_role_policy" "step_functions_policy" {
  name   = "${var.name_prefix}-dynamodb-export-sf-policy"
  role   = aws_iam_role.step_functions_role.id
  policy = data.aws_iam_policy_document.step_functions_policy.json
}

resource "aws_sfn_state_machine" "dynamo_export" {
  name     = "${var.name_prefix}-dynamodb-export-sf"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = templatefile("${path.module}/dynamo_export_step_function_definition.json", {
    lambda_export_trigger_function_name    = aws_lambda_function.dynamo_export_trigger.function_name
    lambda_export_poll_function_name       = aws_lambda_function.dynamo_export_poll.function_name
    lambda_ssm_put_param_function_name     = aws_lambda_function.ssm_put_param.function_name
    dynamo_export_s3_bucket_name           = aws_s3_bucket.dynamodb_output.id
    dynamo_export_processed_s3_bucket_name = aws_s3_bucket.dynamodb_output_processed.id
    ddb_table_arn                          = data.aws_dynamodb_table.pointer_table.arn
    glue_job_name                          = aws_glue_job.glue_job.name
    glue_crawler_name                      = aws_glue_crawler.log_crawler.name
  })
}
