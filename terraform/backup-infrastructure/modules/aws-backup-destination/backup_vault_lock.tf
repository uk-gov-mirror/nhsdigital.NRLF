resource "aws_backup_vault_lock_configuration" "vault_lock" {
  backup_vault_name   = aws_backup_vault.vault.name
  changeable_for_days = var.vault_lock_type == "compliance" ? var.changeable_for_days : null # providing changeable_for_days === enabling compliance mode
  max_retention_days  = var.vault_lock_max_retention_days
  min_retention_days  = var.vault_lock_min_retention_days
}
