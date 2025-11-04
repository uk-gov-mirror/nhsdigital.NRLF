variable "assume_account" {
  sensitive = true
}

variable "assume_role" {}

variable "qa_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the QA environment"
  default     = "api.qa.record-locator.national.nhs.uk"
}

variable "qasandbox_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the QA sandbox environment"
  default     = "api-sandbox.qa.record-locator.national.nhs.uk"
}

variable "int_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the int environment"
  default     = "int.api.record-locator.int.national.nhs.uk"
}

variable "intsandbox_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the int sandbox environment"
  default     = "int-sandbox.api.record-locator.int.national.nhs.uk"
}

variable "ref_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the ref environment"
  default     = "ref.api.record-locator.ref.national.nhs.uk"
}

variable "perftest_api_domain_name" {
  description = "The internal DNS name of the API Gateway for the perftest environment"
  default     = "api.perftest.record-locator.national.nhs.uk"
}

variable "enable_reporting" {
  type        = bool
  description = "Enable account-wide reporting processes in the test account"
  default     = true
}

variable "aws_azs" {
  type        = string
  description = "AWS Availability Zones"
  default     = "eu-west-2a"
}

variable "enable_dns_hostnames" {
  type        = bool
  description = "Enable DNS hostnames in VPC"
  default     = true
}

variable "vpc_cidr_block" {
  type        = string
  description = "Base CIDR Block for VPC"
  default     = "10.0.0.0/16"
}

variable "vpc_public_subnets_cidr_block" {
  type        = string
  description = "CIDR Block for Public Subnets in VPC"
  default     = "10.0.0.0/24"
}

variable "vpc_private_subnets_cidr_block" {
  type        = string
  description = "CIDR Block for Private Subnets in VPC"
  default     = "10.0.1.0/24"
}

variable "enable_powerbi_auto_push" {
  type        = bool
  description = "Enable automatic pushing of info into PowerBI"
  default     = true
}

variable "powerbi_gw_instance_type" {
  type        = string
  description = "Type for PowerBI GW EC2 Instance"
  default     = "t2.medium"
}

variable "use_powerbi_gw_custom_ami" {
  type        = bool
  description = "Use custom image for PowerBI GW instance"
  default     = true
}
