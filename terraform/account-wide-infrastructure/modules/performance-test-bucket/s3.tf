resource "aws_s3_bucket" "performance_test_bucket" {
  bucket        = "${var.name_prefix}-performance-test"
  force_destroy = false
}

resource "aws_s3_bucket_policy" "performance_test_bucket_policy" {
  bucket = aws_s3_bucket.performance_test_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "performance_test_bucket_policy"
    Statement = [
      {
        Sid       = "HTTPSOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.performance_test_bucket.arn,
          "${aws_s3_bucket.performance_test_bucket.arn}/*",
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

resource "aws_s3_bucket_public_access_block" "performance_test_bucket_public_access_block" {
  bucket = aws_s3_bucket.performance_test_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "performance_test_bucket" {
  bucket = aws_s3_bucket.performance_test_bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "performance_test_bucket" {
  bucket = aws_s3_bucket.performance_test_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}
