resource "aws_secretsmanager_secret" "identities_account_id" {
  name = "${local.prefix}--nhs-identities-account-id"
}

resource "aws_secretsmanager_secret" "qa_smoke_test_apigee_app" {
  name        = "${local.prefix}--qa--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the QA environment"
}

resource "aws_secretsmanager_secret" "int_smoke_test_apigee_app" {
  name        = "${local.prefix}--int--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the INT/UAT environment"
}

resource "aws_secretsmanager_secret" "ref_smoke_test_apigee_app" {
  name        = "${local.prefix}--ref--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the REF environment"
}

resource "aws_secretsmanager_secret" "perftest_smoke_test_apigee_app" {
  name        = "${local.prefix}--perftest--apigee-app--smoke-test"
  description = "APIGEE App used to run Smoke Tests against the perftest environment"
}

resource "aws_secretsmanager_secret" "backup_destination_parameters" {
  name        = "${local.prefix}--backup-destination-parameters"
  description = "Parameters used to configure the backup destination"
}

#
# Smoke test parameters secrets
#
resource "aws_secretsmanager_secret" "qa_smoke_test_parameters" {
  name        = "${local.project}--qa--smoke-test-parameters"
  description = "Parameters used to run Smoke Tests against the QA environment"
}

resource "aws_secretsmanager_secret" "qasandbox_smoke_test_parameters" {
  name        = "${local.project}--qa-sandbox--smoke-test-parameters"
  description = "Parameters used to run Smoke Tests against the QA sandbox environment"
}

resource "aws_secretsmanager_secret" "int_smoke_test_parameters" {
  name        = "${local.project}--int--smoke-test-parameters"
  description = "Parameters used to run Smoke Tests against the int environment"
}

resource "aws_secretsmanager_secret" "intsandbox_smoke_test_parameters" {
  name        = "${local.project}--int-sandbox--smoke-test-parameters"
  description = "Parameters used to run Smoke Tests against the int sandbox environment"
}

resource "aws_secretsmanager_secret" "ref_smoke_test_parameters" {
  name        = "${local.project}--ref--smoke-test-parameters"
  description = "Parameters used to run Smoke Tests against the ref environment"
}

resource "aws_secretsmanager_secret" "perftest_smoke_test_parameters" {
  name        = "${local.project}--perftest--smoke-test-parameters"
  description = "Parameters used to run Smoke Tests against the perftest environment"
}


#
# Splunk Configuration secrets
#
resource "aws_secretsmanager_secret" "qa_splunk_configuration" {
  name        = "${local.project}--qa--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_qa index"
}

resource "aws_secretsmanager_secret" "qa_sandbox_splunk_configuration" {
  name        = "${local.project}--qasandbox--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_qasandbox index"
}

resource "aws_secretsmanager_secret" "int_splunk_configuration" {
  name        = "${local.project}--int--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_int index"
}

resource "aws_secretsmanager_secret" "int_sandbox_splunk_configuration" {
  name        = "${local.project}--intsandbox--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_intsandbox index"
}

resource "aws_secretsmanager_secret" "ref_splunk_configuration" {
  name        = "${local.project}--ref--splunk-configuration"
  description = "Splunk configuration for the aws_recordlocator_ref index"
}

#
# Environment Configuration secrets
#
resource "aws_secretsmanager_secret" "qa_environment_configuration" {
  name        = "${local.project}--qa--env-config"
  description = "The environment configuration for the QA environment"
}

resource "aws_secretsmanager_secret" "qasandbox_environment_configuration" {
  name        = "${local.project}--qa-sandbox--env-config"
  description = "The environment configuration for the QA Sandbox environment"
}

resource "aws_secretsmanager_secret" "int_environment_configuration" {
  name        = "${local.project}--int--env-config"
  description = "The environment configuration for the Int environment"
}

resource "aws_secretsmanager_secret" "intsandbox_environment_configuration" {
  name        = "${local.project}--int-sandbox--env-config"
  description = "The environment configuration for the Int Sandbox environment"
}

resource "aws_secretsmanager_secret" "ref_environment_configuration" {
  name        = "${local.project}--ref--env-config"
  description = "The environment configuration for the Ref environment"
}

resource "aws_secretsmanager_secret" "perftest_environment_configuration" {
  name        = "${local.project}--perftest--env-config"
  description = "The environment configuration for the Perftest environment"
}

#
# PowerBI secrets
#
resource "aws_secretsmanager_secret" "powerbi_gw_instance_admin_pwd" {
  name        = "${local.project}--test-powerbi-gw-instance-admin-pwd"
  description = "Admin password for the PowerBI Gateway EC2 instance"
}
resource "aws_secretsmanager_secret" "powerbi_gw_recovery_key" {
  name        = "${local.project}--test-powerbi-gw-recovery-key"
  description = "Recovery key for the PowerBI Gateway EC2 instance"
}
