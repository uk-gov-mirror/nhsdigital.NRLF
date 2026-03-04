output "nrlf_layer_arn" {
  description = "ARN of the NRLF Lambda layer"
  value       = aws_lambda_layer_version.nrlf.arn
}

output "third_party_layer_arn" {
  description = "ARN of the third party dependencies Lambda layer"
  value       = aws_lambda_layer_version.third_party.arn
}
