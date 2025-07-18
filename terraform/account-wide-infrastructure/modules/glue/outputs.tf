output "target_bucket_name" {
  description = "Name of destination bucket"
  value       = aws_s3_bucket.target-data-bucket.id
}

output "target_bucket_arn" {
  description = "Arn of destination bucket"
  value       = aws_s3_bucket.target-data-bucket.arn
}

output "source_bucket_name" {
  description = "Name of source bucket"
  value       = aws_s3_bucket.source-data-bucket.id
}

output "aws_kms_key_arn" {
  description = "Arn of kms key"
  value       = aws_kms_key.glue.arn
}

output "glue_crawler_name" {
  value = "s3//${aws_s3_bucket.source-data-bucket.id}/"
}

output "glue_database" {
  value = var.is_enabled ? aws_glue_catalog_database.log_database[0].name : ""
}
