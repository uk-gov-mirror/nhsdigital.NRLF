locals {
  region      = "eu-west-2"
  project     = "nhsd-nrlf"
  environment = terraform.workspace
  prefix      = "${local.project}--${local.environment}"
  account_id  = data.aws_caller_identity.current.account_id

  notification_emails = tolist(jsondecode(data.aws_secretsmanager_secret_version.emails.secret_string))
}
