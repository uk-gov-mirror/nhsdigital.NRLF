module "dev-glue" {
  is_enabled     = var.enable_reporting
  source         = "../modules/glue"
  name_prefix    = "nhsd-nrlf--drdev"
  schedule       = false
  python_version = 3
}
