# Account-wide Lambda layers for shared infrastructure
# Built once per account, used by account-wide Lambdas like the seed Lambda
module "shared_lambda_layers" {
  source      = "../modules/lambda-layers"
  name_prefix = local.prefix
}
