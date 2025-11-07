variable "account_name" {
  type        = string
  description = "The name of the AWS environment in the account, e.g. dev, qa, int, prod"
}

variable "aws_account_name" {
  type        = string
  description = "The name of the AWS account, e.g. dev, test, prod"
  default     = "dev"
}

variable "assume_role_arn" {
  type      = string
  sensitive = true
}

# What domain should the APIs be hosted under
variable "domain" {
  type = string
}

variable "public_domain" {
  type        = string
  description = "The public domain for the persistent environment"
}

variable "public_sandbox_domain" {
  type        = string
  description = "The public domain for the sandbox environment (optional)"
  nullable    = true
  default     = null
}

variable "consumer_api_path" {
  type    = string
  default = "consumer"
}

variable "producer_api_path" {
  type    = string
  default = "producer"
}

variable "deletion_protection" {
  type    = bool
  default = false
}

variable "use_shared_resources" {
  type    = bool
  default = false
}

variable "log_retention_period" {
  default = 90
  type    = number
}

variable "enable_reporting" {
  type        = bool
  description = "Enable reporting for this environment"
  default     = false
}

variable "disable_firehose_lambda_subscriptions" {
  description = "Disable firehose lambda subscriptions (e.g: splunk, reporting) for shared environments (e.g: perftest). This doesn't affect ephemeral environments as the firehose subscriptions are disabled regardless of this setting"
  type        = bool
  default     = false
}
