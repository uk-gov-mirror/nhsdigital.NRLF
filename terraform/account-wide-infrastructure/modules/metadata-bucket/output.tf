output "bucket_name" {
  description = "Name of the metadata S3 bucket"
  value       = aws_s3_bucket.metadata_bucket.bucket
}
