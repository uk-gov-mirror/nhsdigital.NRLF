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

module "perftest-2.5m-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-2.5m"
}

module "perftest-7.5m-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-7.5m"
}

module "perftest-15m-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-15m"
}

module "perftest-25m-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-25m"
}

module "perftest-55m-pointers-table" {
  source      = "../modules/pointers-table"
  name_prefix = "nhsd-nrlf--perftest-55m"
}
