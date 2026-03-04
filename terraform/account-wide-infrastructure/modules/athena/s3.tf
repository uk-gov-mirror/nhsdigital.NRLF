resource "aws_s3_bucket" "athena" { # NOSONAR (S6258) - Logging not required for this bucket
  bucket = "${var.name_prefix}-athena"
}

resource "aws_s3_bucket_policy" "athena-https-only" {
  bucket = aws_s3_bucket.athena.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "athena-https-only-policy"
    Statement = [
      {
        Sid    = "HTTPSOnly"
        Effect = "Deny"
        Principal = {
          "AWS" : "*"
        }
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.athena.arn,
          "${aws_s3_bucket.athena.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_policy" "athena-access" {
  bucket = aws_s3_bucket.athena.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "athena-access-policy"
    Statement = [
      {
        Sid : "AllowAthenaAccess",
        Effect : "Allow",
        Principal : {
          Service : "athena.amazonaws.com"
        },
        Action : [
          "s3:PutObject",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource : [
          aws_s3_bucket.athena.arn,
          "${aws_s3_bucket.athena.arn}/*",
        ]
      },
    ]
  })
}

resource "aws_s3_bucket_public_access_block" "athena-public-access-block" {
  bucket = aws_s3_bucket.athena.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


resource "aws_s3_bucket_server_side_encryption_configuration" "athena" {
  bucket = aws_s3_bucket.athena.bucket
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.athena.arn
    }
  }

}
