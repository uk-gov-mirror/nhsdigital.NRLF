variable "prefix" {}

variable "region" {}

variable "account_id" {}

variable "layers" {}

variable "environment_variables" {}

variable "table_names" {
  description = "List of DynamoDB table names to reset"
  type        = list(string)
}

variable "schedule_expression" {
  description = "EventBridge schedule expression for the Lambda trigger"
  type        = string
  default     = "cron(0 2 ? * SUN *)" # 2am UTC, every Sunday
}

variable "kms_key_arns" {
  description = "List of KMS key ARNs used to encrypt the DynamoDB tables to be seeded"
  type        = list(string)
}
