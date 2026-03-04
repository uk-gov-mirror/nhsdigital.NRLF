resource "aws_s3_bucket" "authorization-store" { # NOSONAR (S6258) - Logging not required for this bucket
  bucket        = "${var.name_prefix}-authorization-store"
  force_destroy = var.enable_bucket_force_destroy

  tags = {
    Name                  = "authorization store"
    Environment           = "${var.name_prefix}"
    NHSE-Enable-S3-Backup = var.enable_backups ? "True" : "False"
  }
}

resource "aws_s3_bucket_policy" "authorization_store_bucket_policy" {
  bucket = aws_s3_bucket.authorization-store.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "authorization_store_bucket_policy"
    Statement = [
      {
        Sid       = "HTTPSOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.authorization-store.arn,
          "${aws_s3_bucket.authorization-store.arn}/*",
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

resource "aws_s3_bucket_public_access_block" "authorization-store-public-access-block" {
  bucket = aws_s3_bucket.authorization-store.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "authorization-store" {
  bucket = aws_s3_bucket.authorization-store.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "authorization-store" {
  bucket = aws_s3_bucket.authorization-store.id
  versioning_configuration {
    status = "Enabled"
  }
}
# Need to pull these into state if they already exist
resource "aws_s3_object" "consumer-object" {
  bucket = aws_s3_bucket.authorization-store.id
  key    = "consumer/"
}

resource "aws_s3_object" "producer-object" {
  bucket = aws_s3_bucket.authorization-store.id
  key    = "producer/"
}
