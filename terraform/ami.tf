# ami.tf
#
# WHAT: Dynamically finds the latest Amazon Linux 2023 image
#       ID in each region.
# WHY:  AMI IDs are region-specific and change whenever Amazon
#       releases updates — hardcoding one risks it becoming
#       invalid or outdated. This always fetches whatever is
#       current at the moment you run Terraform.

data "aws_ami" "al2023_primary" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

data "aws_ami" "al2023_secondary" {
  provider    = aws.secondary
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}