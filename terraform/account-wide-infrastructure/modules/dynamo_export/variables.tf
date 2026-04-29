variable "name_prefix" {
  type        = string
  description = "The prefix to apply to all resources in the module"
}

variable "environment" {
  type        = string
  description = "Environment in use"
}

variable "pointer_table_name" {
  type        = string
  description = "Name of the pointer table to export"
}

variable "asset_bucket" {
  type        = string
  description = "Name of the bucket that holds lambda zips"
}

variable "asset_version" {
  type        = string
  description = "Version for the lambda zips to use during deployment"
}
