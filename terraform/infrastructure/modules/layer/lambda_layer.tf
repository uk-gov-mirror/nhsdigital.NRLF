# Workspace-level Lambda layer module
# Creates layers per workspace for API Lambdas
#
# Layer filenames are defined in layer-config.json at the workspace root
# This ensures consistency between workspace and account-wide layers

locals {
  layer_config = jsondecode(file("${path.module}/../../../../layer-config.json"))
  dist_dir     = "${path.module}/../../../../${local.layer_config.dist_directory}"
}

resource "aws_lambda_layer_version" "lambda_layer" {
  layer_name          = "${var.prefix}--${replace(var.name, "_", "-")}"
  filename            = "${local.dist_dir}/${lookup(local.layer_config.layer_filenames, var.name, "${var.name}.zip")}"
  source_code_hash    = filebase64sha256("${local.dist_dir}/${lookup(local.layer_config.layer_filenames, var.name, "${var.name}.zip")}")
  compatible_runtimes = ["python3.12"]
}
