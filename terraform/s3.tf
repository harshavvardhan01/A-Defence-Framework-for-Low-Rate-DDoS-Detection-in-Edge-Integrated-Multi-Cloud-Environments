# An S3 bucket mirroring the coordinator's local model
#       registry, plus a data source resolving the current
#       AWS account ID to guarantee a globally unique bucket
#       name without guesswork.
# registry.py already has a working S3 upload code path,
#       written but never exercised in the deployed evaluation
#       because S3_BUCKET was never set. This step enables it.

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "appcd_registry" {
  bucket = "appcd-registry-${data.aws_caller_identity.current.account_id}"

  tags = { Name = "appcd-model-registry" }
}

resource "aws_s3_bucket_versioning" "appcd_registry_versioning" {
  bucket = aws_s3_bucket.appcd_registry.id
  versioning_configuration {
    status = "Enabled"
  }
}

output "s3_bucket_name" {
  value = aws_s3_bucket.appcd_registry.bucket
}