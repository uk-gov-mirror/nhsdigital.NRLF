module "dev-pointers-table" {
  source         = "../modules/pointers-table"
  name_prefix    = "nhsd-nrlf--dev"
  enable_backups = false
}

module "dev-sandbox-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--dev-sandbox"
}
