output "version" {
  value = data.external.current-info.result.version
}

output "caller_identity" {
  value = data.aws_caller_identity.current
}
