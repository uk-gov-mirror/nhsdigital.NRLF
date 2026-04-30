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
