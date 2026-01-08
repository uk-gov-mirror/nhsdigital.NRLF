data "aws_caller_identity" "current" {}

data "aws_s3_object" "api-truststore-certificate" {
  bucket = "${local.shared_prefix}-api-truststore"
  key    = "certificates.pem"
}

data "aws_s3_bucket" "authorization-store" {
  count  = var.use_shared_resources ? 1 : 0
  bucket = "${local.shared_prefix}-authorization-store"
}

data "aws_iam_policy" "auth-store-read-policy" {
  count = var.use_shared_resources ? 1 : 0
  name  = "${local.shared_prefix}-read-s3-authorization-store"
}

data "aws_dynamodb_table" "pointers-table" {
  count = var.use_shared_resources ? 1 : 0
  name  = local.shared_pointers_table_name
}

data "aws_kms_key" "pointers-table-key" {
  count  = var.use_shared_resources ? 1 : 0
  key_id = "alias/${local.shared_pointers_table_name}-key"
}

data "external" "current-info" {
  program = [
    "bash",
    "../../scripts/get-current-info.sh",
  ]
}

data "aws_s3_bucket" "source-data-bucket" {
  bucket = "${local.account_prefix}-source-data-bucket"
}

data "aws_kms_key" "glue" {
  key_id = "alias/${local.account_prefix}-glue"
}
