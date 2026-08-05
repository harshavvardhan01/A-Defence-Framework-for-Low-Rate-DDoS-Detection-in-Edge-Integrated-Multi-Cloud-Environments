# keypair.tf
#
# WHAT: Registers your locally-generated public key with AWS
#       in both regions, so it can be attached to instances.
# WHY:  AWS needs to know your public key BEFORE launching an
#       instance with it — key pairs are region-scoped, so
#       this must be declared once per region, same pattern
#       as the security groups above.

resource "aws_key_pair" "appcd_primary" {
  key_name   = "appcd-key"
  public_key = file("${path.module}/../appcd_key.pub")
}

resource "aws_key_pair" "appcd_secondary" {
  provider   = aws.secondary
  key_name   = "appcd-key"
  public_key = file("${path.module}/../appcd_key.pub")
}