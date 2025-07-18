resource "aws_athena_workgroup" "athena" {
  name = "${var.name_prefix}-athena-wg"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena.id}/output/"

      encryption_configuration {
        encryption_option = "SSE_KMS"
        kms_key_arn       = aws_kms_key.athena.arn
      }
    }
  }

}

resource "aws_athena_named_query" "rep_consumer" {
  name      = "rep_consumer"
  workgroup = aws_athena_workgroup.athena.id
  database  = var.glue_database
  query     = file("${path.module}/sql/rep_consumer.sql")
}

resource "aws_athena_named_query" "rep_producer" {
  name      = "rep_producer"
  workgroup = aws_athena_workgroup.athena.id
  database  = var.glue_database
  query     = file("${path.module}/sql/rep_producer.sql")
}
