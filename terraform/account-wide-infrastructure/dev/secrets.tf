resource "aws_secretsmanager_secret" "backup_destination_parameters" {
  name        = "${local.prefix}--backup-destination-parameters"
  description = "Parameters used to configure the backup destination"
}

resource "aws_secretsmanager_secret" "dev_smoke_test_apigee_app" {
  name        = "${local.prefix}--dev--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the DEV environment"
}

resource "aws_secretsmanager_secret" "dev_smoke_test_parameters" {
  name        = "${local.project}--dev--smoke-test-parameters"
  description = "Parameters used to run Smoke Tests against the dev environment"
}

resource "aws_secretsmanager_secret" "devsandbox_smoke_test_parameters" {
  name        = "${local.project}--dev-sandbox--smoke-test-parameters"
  description = "Parameters used to run Smoke Tests against the dev-sandbox environment"
}

resource "aws_secretsmanager_secret" "dev_splunk_configuration" {
  name        = "${local.project}--dev--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_dev index"
}

resource "aws_secretsmanager_secret" "devsandbox_splunk_configuration" {
  name        = "${local.project}--devsandbox--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_devsandbox index"
}

resource "aws_secretsmanager_secret" "dev_environment_configuration" {
  name        = "${local.project}--dev--env-config"
  description = "The environment configuration for the Dev environment"
}

resource "aws_secretsmanager_secret" "devsandbox_environment_configuration" {
  name        = "${local.project}--dev-sandbox--env-config"
  description = "The environment configuration for the Dev Sandbox environment"
}

resource "aws_secretsmanager_secret" "powerbi_gw_instance_admin_pwd" {
  name        = "${local.project}--dev-powerbi-gw-instance-admin-pwd"
  description = "Admin password for the PowerBI Gateway EC2 instance"
}
resource "aws_secretsmanager_secret" "powerbi_gw_recovery_key" {
  name        = "${local.project}--dev-powerbi-gw-recovery-key"
  description = "Recovery key for the PowerBI Gateway EC2 instance"
}
