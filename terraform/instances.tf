# instances.tf
#
# WHAT: The four real EC2 instances — coordinator + Node A +
#       Node B in the primary region, Node D alone in the
#       secondary region.
# WHY:  This grouping matches your experimental design: Node A
#       and Node D share the same underlying BCCC data source
#       (so their SEPARATION across regions demonstrates
#       architecture, not data lineage), while Node B is a
#       genuinely distinct real capture environment
#       (CIC-DDoS2019) that earns its physical distance.
#
# The user_data script installs Docker automatically on first
# boot, so instances are ready to run your containers the
# moment they finish launching — no manual setup step needed.

locals {
  docker_install = <<-EOF
    #!/bin/bash
    growpart /dev/nvme0n1 1
    xfs_growfs -d /
    dnf update -y
    dnf install -y docker
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ec2-user
  EOF
}

# ── PRIMARY REGION (eu-west-1) ────────────────────────────

resource "aws_instance" "coordinator" {
  ami                    = data.aws_ami.al2023_primary.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.appcd_primary.key_name
  vpc_security_group_ids = [aws_security_group.appcd_primary.id]
  iam_instance_profile = aws_iam_instance_profile.appcd_profile.name
  user_data              = local.docker_install
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = { Name = "appcd-coordinator" }
}

resource "aws_instance" "node_a" {
  ami                    = data.aws_ami.al2023_primary.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.appcd_primary.key_name
  vpc_security_group_ids = [aws_security_group.appcd_primary.id]
  iam_instance_profile = aws_iam_instance_profile.appcd_profile.name
  user_data              = local.docker_install
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = { Name = "appcd-node-a" }
}

resource "aws_instance" "node_b" {
  ami                    = data.aws_ami.al2023_primary.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.appcd_primary.key_name
  vpc_security_group_ids = [aws_security_group.appcd_primary.id]
  iam_instance_profile = aws_iam_instance_profile.appcd_profile.name
  user_data              = local.docker_install
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = { Name = "appcd-node-b" }
}

# ── SECONDARY REGION (us-east-1) ──────────────────────────

resource "aws_instance" "node_d" {
  provider               = aws.secondary
  ami                    = data.aws_ami.al2023_secondary.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.appcd_secondary.key_name
  vpc_security_group_ids = [aws_security_group.appcd_secondary.id]
  iam_instance_profile = aws_iam_instance_profile.appcd_profile.name
  user_data              = local.docker_install
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = { Name = "appcd-node-d" }
}