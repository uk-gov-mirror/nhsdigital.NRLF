output "instance_id" {
  description = "The ID of the PowerBI Gateway EC2 instance."
  value       = aws_instance.powerbi_gw.id
}
