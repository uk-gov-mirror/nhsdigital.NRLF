variable "prefix" {}

variable "region" {}

variable "parent_path" {}

variable "name" {}

variable "api_gateway_source_arn" {
  default = []
}

variable "layers" {}

variable "kms_key_id" {}

variable "environment_variables" {}

variable "additional_policies" {
  default = []
}

variable "handler" {}

variable "firehose_subscriptions" {
  description = "The firehose subscriptions to attach to the lambda logs"
  type        = map(any)
  default     = {}
}

variable "vpc" {
  default = {}
}

variable "retention" {
  default = 90
  type    = number
}
