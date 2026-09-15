data "aws_caller_identity" "current" {}

# Single customer-managed key for the whole system (S3, Aurora, Secrets
# Manager, CloudWatch Logs). Using a CMK rather than the AWS-managed key
# means we control the key policy and rotation, and can produce it as
# evidence in a residency/compliance audit.
resource "aws_kms_key" "this" {
  description             = "${var.name_prefix} CMK for contract data at rest"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "RootAccountFullAccess"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid    = "AllowCloudWatchLogsEncryption"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt*",
          "kms:Decrypt*",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:Describe*"
        ]
        Resource = "*"
      }
    ]
  })

  tags = { Name = "${var.name_prefix}-cmk" }
}

resource "aws_kms_alias" "this" {
  name          = "alias/${var.name_prefix}-cmk"
  target_key_id = aws_kms_key.this.key_id
}
