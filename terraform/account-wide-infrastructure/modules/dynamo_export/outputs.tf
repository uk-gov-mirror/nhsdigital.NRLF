output "dynamo_processed_bucket_arn" {
  value       = aws_s3_bucket.dynamodb_output_processed.arn
  description = "The ARN of the S3 bucket used for processed DynamoDB data."
}
output "dynamo_processed_key_arn" {
  value       = aws_kms_key.dynamo_processed.arn
  description = "The ARN of the KMS key used to encrypt the processed DynamoDB S3 bucket."
}
output "dynamo_export_step_function_arn" {
  value       = aws_sfn_state_machine.dynamo_export.arn
  description = "The ARN of the Step Function for DynamoDB patient history processing."
}
