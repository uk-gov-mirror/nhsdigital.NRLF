module "prod-glue" {
  is_enabled     = var.enable_reporting
  source         = "../modules/glue"
  name_prefix    = "nhsd-nrlf--prod"
  schedule       = true
  python_version = 3
}
