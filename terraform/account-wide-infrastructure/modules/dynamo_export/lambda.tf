data "aws_dynamodb_table" "pointer_table" {
  name = var.pointer_table_name
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.name_prefix}-dynamodb-export-lambda"

  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_policy" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:ExportTableToPointInTime",
      "dynamodb:DescribeExport",
      "dynamodb:DescribeTable",
      "dynamodb:DescribeContinuousBackups",
    ]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameter"
    ]
    resources = ["arn:aws:ssm:eu-west-2:${data.aws_caller_identity.current.account_id}:*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:AbortMultipartUpload",
      "s3:ListMultipartUploadParts"
    ]
    resources = [
      aws_s3_bucket.dynamodb_output.arn,
      "${aws_s3_bucket.dynamodb_output.arn}/*"
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:GenerateDataKey",
      "kms:Encrypt",
      "kms:Decrypt"
    ]
    resources = [aws_kms_key.dynamo.arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.name_prefix}-dynamodb-export-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = data.aws_iam_policy_document.lambda_policy.json
}

data "aws_s3_object" "dynamo_export_trigger_zip" {
  bucket = var.asset_bucket
  key    = "${var.asset_version}/dynamo_export_trigger.zip"
}

resource "aws_lambda_function" "dynamo_export_trigger" {
  function_name = "${var.name_prefix}-dynamo-export-trigger"
  role          = aws_iam_role.lambda_role.arn
  handler       = "src.lambdas.dynamo_export_trigger.dynamo_export_trigger.lambda_handler"
  runtime       = "python3.13"
  timeout       = 30

  s3_bucket         = data.aws_s3_object.dynamo_export_trigger_zip.bucket
  s3_key            = data.aws_s3_object.dynamo_export_trigger_zip.key
  s3_object_version = data.aws_s3_object.dynamo_export_trigger_zip.version_id

  logging_config {
    log_format = "JSON"
  }

  environment {
    variables = {
      BUCKET         = aws_s3_bucket.dynamodb_output.id
      DDB_TABLE_ARN  = data.aws_dynamodb_table.pointer_table.arn
      KMS_KEY        = aws_kms_key.dynamo.key_id
      ENVIRONMENT    = var.environment
      DDB_TABLE_NAME = var.pointer_table_name
    }
  }
}

data "aws_s3_object" "dynamo_export_poll_zip" {
  bucket = var.asset_bucket
  key    = "${var.asset_version}/dynamo_export_poll.zip"
}

resource "aws_lambda_function" "dynamo_export_poll" {
  function_name = "${var.name_prefix}-dynamo-export-poll"
  role          = aws_iam_role.lambda_role.arn
  handler       = "src.lambdas.dynamo_export_poll.dynamo_export_poll.lambda_handler"
  runtime       = "python3.13"
  timeout       = 30

  s3_bucket         = data.aws_s3_object.dynamo_export_poll_zip.bucket
  s3_key            = data.aws_s3_object.dynamo_export_poll_zip.key
  s3_object_version = data.aws_s3_object.dynamo_export_poll_zip.version_id

  logging_config {
    log_format = "JSON"
  }

  environment {
    variables = {
      BUCKET        = aws_s3_bucket.dynamodb_output.id
      DDB_TABLE_ARN = data.aws_dynamodb_table.pointer_table.arn
      KMS_KEY       = aws_kms_key.dynamo.key_id
      ENVIRONMENT   = var.environment
    }
  }
}

data "aws_iam_policy_document" "ssm_put_param_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ssm_put_param_role" {
  name = "${var.name_prefix}-ssm-put-param-lambda"

  assume_role_policy = data.aws_iam_policy_document.ssm_put_param_assume_role.json
}

data "aws_iam_policy_document" "ssm_put_param_policy" {
  statement {
    effect = "Allow"
    actions = [
      "ssm:PutParameter"
    ]
    resources = ["arn:aws:ssm:eu-west-2:${data.aws_caller_identity.current.account_id}:*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ssm_put_param_policy" {
  name = "${var.name_prefix}-ssm-put-param-lambda-policy"
  role = aws_iam_role.ssm_put_param_role.id

  policy = data.aws_iam_policy_document.ssm_put_param_policy.json
}

data "aws_s3_object" "ssm_put_param_zip" {
  bucket = var.asset_bucket
  key    = "${var.asset_version}/ssm_put_param.zip"
}

resource "aws_lambda_function" "ssm_put_param" {
  function_name = "${var.name_prefix}-ssm-put-param"
  role          = aws_iam_role.ssm_put_param_role.arn
  handler       = "src.lambdas.ssm_put_param.ssm_put_param.lambda_handler"
  runtime       = "python3.13"
  timeout       = 30

  s3_bucket         = data.aws_s3_object.ssm_put_param_zip.bucket
  s3_key            = data.aws_s3_object.ssm_put_param_zip.key
  s3_object_version = data.aws_s3_object.ssm_put_param_zip.version_id

  logging_config {
    log_format = "JSON"
  }

  environment {
    variables = {
      BUCKET        = aws_s3_bucket.dynamodb_output.id
      DDB_TABLE_ARN = data.aws_dynamodb_table.pointer_table.arn
      KMS_KEY       = aws_kms_key.dynamo.key_id
      ENVIRONMENT   = var.environment
    }
  }
}
