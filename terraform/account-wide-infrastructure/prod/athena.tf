module "prod-athena" {
  count              = var.enable_reporting ? 1 : 0
  source             = "../modules/athena"
  name_prefix        = "nhsd-nrlf--prod"
  target_bucket_name = module.prod-glue.target_bucket_name
  bucket_region      = data.aws_region.current.region
  glue_database      = module.prod-glue.glue_database
}
