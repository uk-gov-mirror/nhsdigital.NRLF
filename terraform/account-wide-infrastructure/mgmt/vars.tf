variable "developer_role_name" {
  description = "Name of the IAM role for developers"
  type        = string
  default     = "AWSReservedSSO_NHSDDeveloperRole_fa10ba0474290a64"
}

variable "private_subnet_cidr_blocks" {
  description = "Available CIDR blocks for private subnets"
  type        = list(string)
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24",
    "10.0.3.0/24",
    "10.0.4.0/24",
  ]
}

variable "subnet_count" {
  description = "Number of subnets"
  type        = map(number)
  default = {
    private = 3
  }
}

variable "vpc_cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "ci_image_tag" {
  description = "Tag for the CI image in ECR"
  type        = string
  default     = "2026-04-09"
}
