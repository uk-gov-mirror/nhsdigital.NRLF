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
  name_prefix = "nhsd-nrlf--perftest"
}

module "perftest-pointers-baseline-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-baseline"
}

module "perftest-pointers-15m-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-15m"
}

module "perftest-pointers-55m-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-55m"
}
