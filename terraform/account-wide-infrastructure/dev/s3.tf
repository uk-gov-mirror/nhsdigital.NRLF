module "dev-permissions-store-bucket" {
  source         = "../modules/permissions-store-bucket"
  name_prefix    = "nhsd-nrlf--dev"
  enable_backups = false
}

module "dev-sandbox-permissions-store-bucket" {
  source      = "../modules/permissions-store-bucket"
  name_prefix = "nhsd-nrlf--dev-sandbox"
}

module "dev-truststore-bucket" {
  source                  = "../modules/truststore-bucket"
  name_prefix             = "nhsd-nrlf--dev"
  server_certificate_file = "../../../truststore/server/dev.pem"
  enable_backups          = false
}

module "dev-sandbox-truststore-bucket" {
  source                  = "../modules/truststore-bucket"
  name_prefix             = "nhsd-nrlf--dev-sandbox"
  server_certificate_file = "../../../truststore/server/dev.pem"
}
