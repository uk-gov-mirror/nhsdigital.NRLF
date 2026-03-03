resource "aws_lambda_function" "lambda_function" {
  function_name    = "${var.prefix}--sandbox-seeder"
  runtime          = "python3.12"
  handler          = "index.handler"
  role             = aws_iam_role.lambda_role.arn
  filename         = "${path.module}/../../../../dist/seed_sandbox.zip"
  source_code_hash = filebase64sha256("${path.module}/../../../../dist/seed_sandbox.zip")
  timeout          = local.lambda_timeout
  memory_size      = 128

  environment {
    variables = merge(var.environment_variables, {
      TABLE_NAMES = join(",", var.table_names)
    })
  }

  layers = var.layers

  depends_on = [
    aws_iam_role.lambda_role
  ]
}
