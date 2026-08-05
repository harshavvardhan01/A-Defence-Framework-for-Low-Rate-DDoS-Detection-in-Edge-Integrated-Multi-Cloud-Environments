# iam.tf
#
# WHAT: Grants EC2 instances permission to write to S3,
#       DynamoDB, and CloudWatch Logs via an attached
#       instance profile -- no access keys ever embedded
#       in the Docker image or environment variables.

resource "aws_iam_role" "appcd_role" {
  name = "appcd-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "appcd_policy" {
  name = "appcd-s3-dynamodb-cloudwatch"
  role = aws_iam_role.appcd_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
        Resource = [
          aws_s3_bucket.appcd_registry.arn,
          "${aws_s3_bucket.appcd_registry.arn}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query", "dynamodb:UpdateItem"]
        Resource = "arn:aws:dynamodb:*:*:table/appcd-round-state"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "appcd_profile" {
  name = "appcd-instance-profile"
  role = aws_iam_role.appcd_role.name
}