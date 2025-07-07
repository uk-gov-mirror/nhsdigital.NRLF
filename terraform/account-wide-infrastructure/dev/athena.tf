module "dev-athena" {
  count              = var.enable_reporting ? 1 : 0
  source             = "../modules/athena"
  name_prefix        = "nhsd-nrlf--dev"
  target_bucket_name = module.dev-glue.target_bucket_name
  bucket_region      = data.aws_region.current.region
  glue_database      = module.dev-glue.glue_database
}
