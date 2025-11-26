data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_secretsmanager_secret_version" "identities_account_id" {
  secret_id = aws_secretsmanager_secret.identities_account_id.name
}

data "aws_secretsmanager_secret" "emails" {
  name = "${local.prefix}-emails"
}

data "aws_secretsmanager_secret_version" "emails" {
  secret_id = data.aws_secretsmanager_secret.emails.id
}

data "aws_secretsmanager_secret_version" "backup_destination_parameters" {
  secret_id = aws_secretsmanager_secret.backup_destination_parameters.name
}

data "external" "current-info" {
  program = [
    "bash",
    "../../../scripts/get-current-info.sh",
  ]
}
