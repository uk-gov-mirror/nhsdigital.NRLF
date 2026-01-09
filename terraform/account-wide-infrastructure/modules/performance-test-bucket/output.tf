output "bucket_name" {
  description = "Name of the performance test S3 bucket"
  value       = aws_s3_bucket.performance_test_bucket.bucket
}
