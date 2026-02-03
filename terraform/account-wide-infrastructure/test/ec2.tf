module "vpc" {
  count                          = var.enable_reporting && var.enable_powerbi_auto_push ? 1 : 0
  source                         = "../modules/vpc"
  vpc_cidr_block                 = var.vpc_cidr_block
  enable_dns_hostnames           = var.enable_dns_hostnames
  vpc_public_subnets_cidr_block  = var.vpc_public_subnets_cidr_block
  vpc_private_subnets_cidr_block = var.vpc_private_subnets_cidr_block
  aws_azs                        = var.aws_azs
  name_prefix                    = "nhsd-nrlf--test"
}

module "powerbi_gw_instance" {
  count              = var.enable_reporting && var.enable_powerbi_auto_push ? 1 : 0
  source             = "../modules/powerbi-gw-ec2"
  use_custom_ami     = var.use_powerbi_gw_custom_ami
  instance_type      = var.powerbi_gw_instance_type
  name_prefix        = "nhsd-nrlf--test-powerbi-gw"
  target_bucket_arn  = module.test-glue.target_bucket_arn
  glue_kms_key_arn   = module.test-glue.aws_kms_key_arn
  athena_kms_key_arn = module.test-athena[0].kms_key_arn
  athena_bucket_arn  = module.test-athena[0].bucket_arn
  root_volume_size   = var.powerbi_gw_root_volume_size
  root_volume_iops   = var.powerbi_gw_root_volume_iops

  subnet_id       = module.vpc[0].private_subnet_id
  security_groups = [module.vpc[0].powerbi_gw_security_group_id]
}
