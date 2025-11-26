output "powerbi_gw_instance_id" {
  description = "The ID of the PowerBI Gateway EC2 instance."
  value       = var.enable_powerbi_auto_push ? module.powerbi_gw_instance[0].instance_id : null
}

output "reporting_database_name" {
  description = "Name of the reporting Athena database"
  value       = var.enable_reporting ? module.prod-glue.glue_database : null
}

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = var.enable_reporting ? module.prod-athena[0].workgroup_name : null
}

output "athena_s3_output_location" {
  description = "S3 output location for Athena queries"
  value       = var.enable_reporting ? "s3://${module.prod-athena[0].bucket.id}/" : null
}

output "athena_kms_key_arn" {
  description = "KMS key ARN for Athena encryption"
  value       = var.enable_reporting ? module.prod-athena[0].kms_key_arn : null
}

output "version" {
  value = data.external.current-info.result.version
}
