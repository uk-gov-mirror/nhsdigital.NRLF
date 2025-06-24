module "test-athena" {
  count              = var.enable_reporting ? 1 : 0
  source             = "../modules/athena"
  name_prefix        = "nhsd-nrlf--test"
  target_bucket_name = module.test-glue.target_bucket_name
  glue_database      = module.test-glue.glue_database
}
