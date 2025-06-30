module "firehose__processor" {
  count                = var.use_shared_resources ? 1 : 0
  source               = "./modules/firehose"
  assume_account       = local.aws_account_id
  prefix               = local.prefix
  region               = local.region
  environment          = local.environment
  cloudwatch_kms_arn   = module.kms__cloudwatch.kms_arn
  splunk_environment   = local.splunk_environment
  splunk_index         = local.splunk_index
  destination          = "splunk"
  reporting_bucket_arn = local.reporting_bucket_arn
  reporting_kms_arn    = local.reporting_kms_arn
}
