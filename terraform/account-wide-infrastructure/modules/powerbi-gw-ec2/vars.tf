variable "name_prefix" {}
variable "instance_type" {}
variable "security_groups" {}
variable "subnet_id" {}
variable "glue_kms_key_arn" {}
variable "athena_kms_key_arn" {}
variable "target_bucket_arn" {}
variable "athena_bucket_arn" {}
variable "use_custom_ami" {}
variable "root_volume_size" {
  type        = number
  description = "Size of the root EBS volume in GB"
  default     = 120
}
variable "root_volume_iops" {
  type        = number
  description = "IOPS for the root EBS volume if using io1 or gp3 volume type"
  default     = 3000
}
