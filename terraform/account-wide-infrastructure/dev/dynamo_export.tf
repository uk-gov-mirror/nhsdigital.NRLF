module "dynamo_export" {
  source             = "../modules/dynamo_export"
  name_prefix        = "nhsd-nrlf--dev"
  environment        = "dev"
  pointer_table_name = module.dev-pointers-table.table_name
}
