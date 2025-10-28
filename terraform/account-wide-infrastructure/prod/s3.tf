module "prod-permissions-store-bucket" {
  source         = "../modules/permissions-store-bucket"
  name_prefix    = "nhsd-nrlf--prod"
  enable_backups = true
}

module "prod-truststore-bucket" {
  source                  = "../modules/truststore-bucket"
  name_prefix             = "nhsd-nrlf--prod"
  server_certificate_file = "../../../truststore/server/prod.pem"
  enable_backups          = true
}
