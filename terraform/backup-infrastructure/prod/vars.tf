variable "assume_account" {
  description = "The account id to deploy the infrastructure to"
  sensitive   = true
}

variable "assume_role" {
  description = "Name of the role to assume to deploy the infrastructure"
  type        = string
}

variable "source_account_id" {
  description = "The account id of the backup source account"
  type        = string
  sensitive   = true
}
