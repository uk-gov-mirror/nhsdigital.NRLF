module "qa-pointers-table" {
  source                     = "../modules/pointers-table"
  name_prefix                = "nhsd-nrlf--qa"
  enable_deletion_protection = true
}

module "qa-sandbox-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--qa-sandbox"
}

module "int-pointers-table" {
  source                      = "../modules/pointers-table"
  name_prefix                 = "nhsd-nrlf--int"
  enable_deletion_protection  = true
  enable_pitr                 = true
  kms_deletion_window_in_days = 30
  enable_backups              = true
}

module "int-sandbox-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--int-sandbox"
}

module "ref-pointers-table" {
  source                      = "../modules/pointers-table"
  name_prefix                 = "nhsd-nrlf--ref"
  enable_deletion_protection  = true
  enable_pitr                 = true
  kms_deletion_window_in_days = 30
}

module "perftest-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-baseline"
}

module "perftest-4m-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-4m"
}

module "perftest-8m-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-8m"
}

module "perftest-16m-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-16m"
}

module "perftest-32m-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-32m"
}

module "perftest-64m-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-64m"
}
