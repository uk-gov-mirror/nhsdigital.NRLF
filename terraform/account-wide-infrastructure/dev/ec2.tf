module "vpc" {
  count                          = var.enable_reporting && var.enable_powerbi_auto_push ? 1 : 0
  source                         = "../modules/vpc"
  vpc_cidr_block                 = var.vpc_cidr_block
  enable_dns_hostnames           = var.enable_dns_hostnames
  vpc_public_subnets_cidr_block  = var.vpc_public_subnets_cidr_block
  vpc_private_subnets_cidr_block = var.vpc_private_subnets_cidr_block
  aws_azs                        = var.aws_azs
  name_prefix                    = "nhsd-nrlf--dev"
}

module "powerbi_gw_instance" {
  count              = var.enable_reporting && var.enable_powerbi_auto_push ? 1 : 0
  source             = "../modules/powerbi-gw-ec2"
  use_custom_ami     = var.use_powerbi_gw_custom_ami
  instance_type      = var.powerbi_gw_instance_type
  name_prefix        = "nhsd-nrlf--dev-powerbi-gw"
  target_bucket_arn  = module.dev-glue.target_bucket_arn
  glue_kms_key_arn   = module.dev-glue.aws_kms_key_arn
  athena_kms_key_arn = module.dev-athena[0].kms_key_arn
  athena_bucket_arn  = module.dev-athena[0].bucket_arn

  subnet_id       = module.vpc[0].private_subnet_id
  security_groups = [module.vpc[0].powerbi_gw_security_group_id]
}
