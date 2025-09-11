locals {
  # Adjust these as required
  project_name     = "nrlf-prod-backup"
  environment_name = "prod"

  source_account_id      = var.source_account_id
  destination_account_id = var.assume_account
}
