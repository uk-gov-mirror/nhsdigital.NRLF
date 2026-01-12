variable "assume_account" {
  type        = string
  sensitive   = true
  description = "The AWS account number of the account that contains the role to assume for deploying the bastion"
}

variable "assume_role" {
  type        = string
  sensitive   = true
  description = "The name of the role to assume for deploying the bastion"
}

variable "bastion_name" {
  type        = string
  description = "The name of the bastion"
  default     = "ops"
}

variable "vpc_name" {
  type        = string
  description = "The name of the VPC where the bastion will be deployed"
}

variable "subnet_name" {
  type        = string
  description = "The name of the subnet where the bastion will be deployed"
}

variable "dynamodb_table_name" {
  type        = string
  description = "The name of the DynamoDB table, or null if no access is required"
  default     = null
}

variable "allow_dynamodb_table_write" {
  type        = bool
  description = "Whether to allow write access to the DynamoDB table"
  default     = false
}

variable "ami_name_match" {
  type        = string
  description = "The name or wildecard for the AMI name for the bastion host"
  default     = "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"
}

variable "instance_type" {
  type        = string
  description = "The EC2 instance type for the bastion"
  default     = "t3a.micro"
}
