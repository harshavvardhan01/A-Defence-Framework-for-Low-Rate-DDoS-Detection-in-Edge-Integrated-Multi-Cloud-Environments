# security.tf
#
# WHAT: Firewall rules (AWS calls these "security groups"),
#       duplicated once per region since a security group is
#       always scoped to a single region's network.
# WHY:  Without these, EITHER nothing can reach your instances
#       at all (too restrictive, breaks everything) OR
#       everything on the internet can reach them (way too
#       permissive, a real security problem). This is the
#       precise middle ground: SSH only from YOUR IP, the
#       application port open for the nodes/coordinator to
#       talk to each other, dashboard port reserved for later.

resource "aws_security_group" "appcd_primary" {
  name        = "appcd-sg-primary"
  description = "APPCD prototype - primary region (eu-west-1)"

  ingress {
    description = "SSH from my IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "FastAPI service port - nodes and coordinator"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # token-authenticated at app level
  }

  ingress {
    description = "Streamlit dashboard, later stage"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "appcd-sg-primary" }
}

resource "aws_security_group" "appcd_secondary" {
  provider    = aws.secondary
  name        = "appcd-sg-secondary"
  description = "APPCD prototype - secondary region (us-east-1)"

  ingress {
    description = "SSH from my IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "FastAPI service port - nodes and coordinator"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "appcd-sg-secondary" }
}