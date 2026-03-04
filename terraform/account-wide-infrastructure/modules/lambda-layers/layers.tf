# Account-wide Lambda layers for shared infrastructure
# These reference the same pre-built zips as workspace layers
# but are deployed once per account rather than per workspace

locals {
  layer_config = jsondecode(file("${path.module}/../../../../layer-config.json"))
  dist_dir     = "${path.module}/../../../../${local.layer_config.dist_directory}"
  layer_zips   = local.layer_config.layer_filenames
}

resource "aws_lambda_layer_version" "nrlf" {
  layer_name          = "${var.name_prefix}--nrlf-layer"
  filename            = "${local.dist_dir}/${local.layer_zips.nrlf}"
  source_code_hash    = filebase64sha256("${local.dist_dir}/${local.layer_zips.nrlf}")
  compatible_runtimes = ["python3.12"]
  description         = "NRLF core library layer (account-wide)"
}

resource "aws_lambda_layer_version" "third_party" {
  layer_name          = "${var.name_prefix}--dependency-layer"
  filename            = "${local.dist_dir}/${local.layer_zips.third_party}"
  source_code_hash    = filebase64sha256("${local.dist_dir}/${local.layer_zips.third_party}")
  compatible_runtimes = ["python3.12"]
  description         = "Third party dependencies layer (account-wide)"
}
