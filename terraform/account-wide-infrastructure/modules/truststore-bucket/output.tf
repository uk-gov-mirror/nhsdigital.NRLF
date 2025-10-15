output "bucket_name" {
  description = "Name of the truststore S3 bucket"
  value       = aws_s3_bucket.api_truststore.bucket
}

output "certificates_object_key" {
  description = "Key of the truststore certificates object"
  value       = aws_s3_object.api_truststore_certificate.key
}

output "certificates_object_version" {
  description = "Version of the truststore certificates object"
  value       = aws_s3_object.api_truststore_certificate.version_id
}
