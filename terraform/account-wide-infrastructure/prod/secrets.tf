resource "aws_secretsmanager_secret" "identities_account_id" {
  name = "${local.prefix}--nhs-identities-account-id"
}

resource "aws_secretsmanager_secret" "prod_smoke_test_apigee_app" {
  name        = "${local.prefix}--prod--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the PROD environment"
}

resource "aws_secretsmanager_secret" "prod_smoke_test_parameters" {
  name        = "${local.project}--prod--smoke-test-parameters"
  description = "Parameters used to run Smoke Tests against the prod environment"
}

resource "aws_secretsmanager_secret" "prod_splunk_configuration" {
  name        = "${local.project}--prod--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_prod index"
}

resource "aws_secretsmanager_secret" "prod_environment_configuration" {
  name        = "${local.project}--prod--env-config"
  description = "The environment configuration for the Prod environment"
}

resource "aws_secretsmanager_secret" "powerbi_gw_instance_admin_pwd" {
  count       = var.enable_reporting && var.enable_powerbi_auto_push ? 1 : 0
  name        = "${local.project}--prod-powerbi-gw-instance-admin-pwd"
  description = "Admin password for the PowerBI Gateway EC2 instance"
}
resource "aws_secretsmanager_secret" "powerbi_gw_recovery_key" {
  name        = "${local.project}--prod-powerbi-gw-recovery-key"
  description = "Recovery key for the PowerBI Gateway EC2 instance"
}
