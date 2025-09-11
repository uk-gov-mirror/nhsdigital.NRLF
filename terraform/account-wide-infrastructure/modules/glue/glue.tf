# Create Glue Data Catalog Database
resource "aws_glue_catalog_database" "log_database" {
  count = var.is_enabled ? 1 : 0

  name         = "${var.name_prefix}-reporting"
  location_uri = "${aws_s3_bucket.target-data-bucket.id}/"
}

# Create Glue Crawler
resource "aws_glue_crawler" "log_crawler" {
  count = var.is_enabled ? 1 : 0

  name          = "${var.name_prefix}-log-crawler"
  database_name = aws_glue_catalog_database.log_database[0].name
  role          = aws_iam_role.glue_service_role.name
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/consumer_countDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/consumer_readDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/consumer_searchDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/consumer_searchPostDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/producer_createDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/producer_deleteDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/producer_readDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/producer_searchDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/producer_searchPostDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/producer_updateDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/producer_upsertDocumentReference/"
  }
  s3_target {
    path = "s3://${aws_s3_bucket.target-data-bucket.id}/spine_sspDocumentRetrieval/"
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

resource "aws_glue_trigger" "log_trigger" {
  count = var.is_enabled ? 1 : 0

  name = "${var.name_prefix}-org-report-trigger"
  type = "ON_DEMAND"
  actions {
    crawler_name = aws_glue_crawler.log_crawler[0].name
  }
}

resource "aws_glue_trigger" "glue_trigger" {
  count = var.schedule && var.is_enabled ? 1 : 0

  name     = "${var.name_prefix}-glue-trigger"
  type     = "SCHEDULED"
  schedule = "cron(0 1 * * ? *)"

  actions {
    job_name = aws_glue_job.glue_job[0].name
  }
}

resource "aws_glue_job" "glue_job" {
  count = var.is_enabled ? 1 : 0

  name              = "${var.name_prefix}-glue-job"
  role_arn          = aws_iam_role.glue_service_role.arn
  description       = "Transfer logs from source to bucket"
  glue_version      = "5.0"
  worker_type       = "G.1X"
  execution_class   = "STANDARD"
  timeout           = 60 # minutes
  max_retries       = 0
  number_of_workers = 4
  command {
    name            = "glueetl"
    python_version  = var.python_version
    script_location = "s3://${aws_s3_bucket.code-bucket.id}/main.py"
  }

  default_arguments = {
    "--enable-auto-scaling"             = "true"
    "--enable-continous-cloudwatch-log" = "true"
    "--datalake-formats"                = "delta"
    "--source_path"                     = "s3://${aws_s3_bucket.source-data-bucket.id}/" # Specify the source S3 path
    "--target_path"                     = "s3://${aws_s3_bucket.target-data-bucket.id}/" # Specify the destination S3 path
    "--job_name"                        = "${var.name_prefix}-glue-job"
    "--partition_cols"                  = "date"
    "--enable-continuous-log-filter"    = "true"
    "--enable-metrics"                  = "true"
    "--extra-py-files"                  = "s3://${aws_s3_bucket.code-bucket.id}/src.zip"
    "--enable-job-insights"             = "true"
    "--job-language"                    = "python"
  }
}
