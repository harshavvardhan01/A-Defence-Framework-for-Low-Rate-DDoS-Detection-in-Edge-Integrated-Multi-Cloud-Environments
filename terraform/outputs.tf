# Prints the important values after terraform apply
#       finishes — no need to hunt through the AWS Console.

output "coordinator_ip" {
  value = aws_eip.coordinator.public_ip
}

output "node_a_ip" {
  value = aws_eip.node_a.public_ip
}

output "node_b_ip" {
  value = aws_eip.node_b.public_ip
}

output "node_d_ip" {
  value = aws_eip.node_d.public_ip
}

output "ssh_coordinator" {
  value = "ssh -i ../appcd_key ec2-user@${aws_eip.coordinator.public_ip}"
}