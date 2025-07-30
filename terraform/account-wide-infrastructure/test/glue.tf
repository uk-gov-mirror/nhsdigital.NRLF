module "test-glue" {
  is_enabled     = var.enable_reporting
  source         = "../modules/glue"
  name_prefix    = "nhsd-nrlf--test"
  schedule       = false
  python_version = 3
}
