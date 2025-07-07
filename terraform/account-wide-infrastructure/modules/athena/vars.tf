variable "name_prefix" {
  type        = string
  description = "The prefix to apply to all resources in the module."
}

variable "bucket_region" {
  type        = string
  description = "The AWS region where the S3 bucket will be created."
}

variable "target_bucket_name" {
  type = string
}

variable "glue_database" {
  type        = string
  description = "The Glue database in use"
}
