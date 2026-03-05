data "aws_iam_policy_document" "glue_service_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue_service_role" {
  name               = "${var.name_prefix}-dynamo-glue-service-role"
  assume_role_policy = data.aws_iam_policy_document.glue_service_assume_role.json
}

data "aws_iam_policy_document" "glue_service_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:GetBucketLocation",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.dynamodb_output.arn,
      "${aws_s3_bucket.dynamodb_output.arn}/*",
      aws_s3_bucket.dynamodb_output_processed.arn,
      "${aws_s3_bucket.dynamodb_output_processed.arn}/*",
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey"
    ]
    resources = [
      aws_kms_key.dynamo.arn,
      aws_kms_key.dynamo_processed.arn,
    ]
  }

  statement {
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:CreateTable",
      "glue:UpdateTable",
      "glue:DeleteTable",
      "glue:GetPartition",
      "glue:GetPartitions",
      "glue:CreatePartition",
      "glue:BatchCreatePartition",
      "glue:UpdatePartition",
    ]

    resources = [
      "arn:aws:glue:eu-west-2:${data.aws_caller_identity.current.account_id}:catalog",
      "arn:aws:glue:eu-west-2:${data.aws_caller_identity.current.account_id}:database/*",
      "arn:aws:glue:eu-west-2:${data.aws_caller_identity.current.account_id}:table/*",
    ]

    effect = "Allow"
  }

  statement {
    actions = [
      "glue:GetCrawler",
      "glue:StartCrawler",
      "glue:GetCrawlerMetrics",
    ]

    resources = [
      aws_glue_crawler.log_crawler.arn,
    ]

    effect = "Allow"
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*:/aws-glue/*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
    ]
    resources = ["arn:aws:ssm:eu-west-2:${data.aws_caller_identity.current.account_id}:*"]
  }
}

resource "aws_iam_role_policy" "glue_service_policy" {
  name   = "${var.name_prefix}-dynamo-glue-service-policy"
  role   = aws_iam_role.glue_service_role.id
  policy = data.aws_iam_policy_document.glue_service_policy.json
}

resource "aws_glue_catalog_database" "log_database" {
  name         = "${var.name_prefix}-dynamo-reporting"
  location_uri = "${aws_s3_bucket.dynamodb_output_processed.id}/"
}

resource "aws_glue_crawler" "log_crawler" {
  name          = "${var.name_prefix}-${var.environment}-dynamo-crawler"
  database_name = aws_glue_catalog_database.log_database.name
  role          = aws_iam_role.glue_service_role.name
  delta_target {
    delta_tables              = ["s3://${aws_s3_bucket.dynamodb_output_processed.id}/processed/dynamo_export_flags"]
    write_manifest            = false
    create_native_delta_table = true
  }
  schema_change_policy {
    delete_behavior = "LOG"
  }
  configuration = jsonencode({
    "Version" : 1.0,
    "Grouping" : {
      "TableGroupingPolicy" : "CombineCompatibleSchemas"
    }
  })
}

resource "aws_glue_trigger" "crawler_trigger" {
  name = "${var.name_prefix}-crawler-trigger"
  type = "ON_DEMAND"
  actions {
    crawler_name = aws_glue_crawler.log_crawler.name
  }
}

resource "aws_s3_object" "script" {
  bucket      = aws_s3_bucket.dynamodb_output_processed.bucket
  key         = "glue_code/glue_job.py"
  source      = "${path.module}/src/glue_job.py"
  source_hash = filemd5("${path.module}/src/glue_job.py")
}

resource "aws_glue_job" "glue_job" {
  name              = "${var.name_prefix}-dynamo-export-glue-job"
  role_arn          = aws_iam_role.glue_service_role.arn
  description       = "Export DynamoDB data to S3"
  glue_version      = "5.0"
  worker_type       = "G.1X"
  timeout           = 48 * 60
  max_retries       = 0
  number_of_workers = 4

  command {
    name            = "glueetl"
    python_version  = 3
    script_location = "s3://${aws_s3_bucket.dynamodb_output_processed.id}/glue_code/glue_job.py"
  }

  default_arguments = {
    "--enable-auto-scaling"              = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--datalake-formats"                 = "delta"
    "--enable-metrics"                   = "true"
    "--enable-glue-datacatalog"          = "true"
    "--conf"                             = "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog --conf spark.delta.logStore.class=org.apache.spark.sql.delta.storage.S3SingleDriverLogStore --conf spark.jars.packages=io.delta:delta-core_2.3:3.3.0"
    # "--SLACK_WEBHOOK_URL_SSM_PARAMETER_NAME" = "/${var.environment}-blue/api_config/slack_service_alert_webhook"
    "--ENVIRONMENT" = var.environment
  }
}
