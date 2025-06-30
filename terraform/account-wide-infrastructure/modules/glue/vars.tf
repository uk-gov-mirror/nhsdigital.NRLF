variable "name_prefix" {
  type        = string
  description = "The prefix to apply to all resources in the module."
}

variable "python_version" {
  type        = number
  description = "Python version to run in script"
}

variable "source_bucket" {
  description = "S3 bucket for source data"
  default     = "source-data-bucket"
}

variable "target_bucket" {
  description = "S3 bucket for target data"
  default     = "target-data-bucket"
}

variable "code_bucket" {
  description = "S3 bucket for Glue job scripts"
  default     = "code-bucket"
}

variable "is_enabled" {
  type        = bool
  description = "Flag to enable or disable the Glue module"
  default     = true
}
