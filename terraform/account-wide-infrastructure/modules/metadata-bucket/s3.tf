resource "aws_s3_bucket" "metadata_bucket" { # NOSONAR (S6258) - Logging not required for this bucket
  bucket        = "${var.name_prefix}-metadata"
  force_destroy = false
}

resource "aws_s3_bucket_policy" "metadata_bucket_policy" {
  bucket = aws_s3_bucket.metadata_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "metadata_bucket_policy"
    Statement = [
      {
        Sid       = "HTTPSOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.metadata_bucket.arn,
          "${aws_s3_bucket.metadata_bucket.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
    ]
  })
}

resource "aws_s3_bucket_public_access_block" "metadata_bucket_public_access_block" {
  bucket = aws_s3_bucket.metadata_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "metadata_bucket" {
  bucket = aws_s3_bucket.metadata_bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "metadata_bucket" {
  bucket = aws_s3_bucket.metadata_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}
