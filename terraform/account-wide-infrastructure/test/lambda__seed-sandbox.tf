# Lambda to reset specified DynamoDB tables with seed test data on a schedule
# Deployed at account level to avoid duplication across workspaces
# Uses account-wide Lambda layers
# Only deploys if tables are specified

locals {
  seed_table_names = ["nhsd-nrlf--int-sandbox-pointers-table"]
}

data "aws_dynamodb_table" "seed_table_metadata" {
  for_each = toset(local.seed_table_names)
  name     = each.value
}

module "seed_sandbox_lambda" {
  count      = length(local.seed_table_names) > 0 ? 1 : 0
  source     = "../modules/seed_sandbox_lambda"
  region     = local.region
  account_id = local.account_id
  prefix     = local.prefix
  layers = [
    module.shared_lambda_layers.nrlf_layer_arn,
    module.shared_lambda_layers.third_party_layer_arn,
    module.shared_lambda_layers.nrlf_permissions_layer_arn
  ]

  table_names = local.seed_table_names
  kms_key_arns = compact([
    for table in values(data.aws_dynamodb_table.seed_table_metadata) :
    try(table.server_side_encryption[0].kms_key_arn, null)
  ])
  schedule_expression = "cron(0 2 ? * SUN *)" # Every Sunday at 2am UTC

  environment_variables = {
    PREFIX            = "${local.prefix}--"
    ENVIRONMENT       = local.environment
    POINTERS_PER_TYPE = "2"
  }
}
