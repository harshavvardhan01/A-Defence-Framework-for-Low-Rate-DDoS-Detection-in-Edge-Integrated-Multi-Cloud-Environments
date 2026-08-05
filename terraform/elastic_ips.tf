# elastic_ips.tf
#
# WHAT: A permanent public IP for each instance, unaffected
#       by stop/start cycles.
# WHY:  Without these, every reboot would assign a NEW random
#       public IP, breaking the coordinator's configured
#       AGENT_* URLs and requiring manual reconfiguration —
#       exactly the "5-minute ritual" problem flagged earlier.
#       On a personal account these also cost nothing extra
#       while attached to a running instance.

resource "aws_eip" "coordinator" {
  instance = aws_instance.coordinator.id
  domain   = "vpc"
  tags     = { Name = "appcd-coordinator-eip" }
}

resource "aws_eip" "node_a" {
  instance = aws_instance.node_a.id
  domain   = "vpc"
  tags     = { Name = "appcd-node-a-eip" }
}

resource "aws_eip" "node_b" {
  instance = aws_instance.node_b.id
  domain   = "vpc"
  tags     = { Name = "appcd-node-b-eip" }
}

resource "aws_eip" "node_d" {
  provider = aws.secondary
  instance = aws_instance.node_d.id
  domain   = "vpc"
  tags     = { Name = "appcd-node-d-eip" }
}