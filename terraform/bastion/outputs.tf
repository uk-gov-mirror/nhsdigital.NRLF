
output "instance_id" {
  description = "The ID of the bastion EC2 instance"
  value       = aws_instance.node.id
}
