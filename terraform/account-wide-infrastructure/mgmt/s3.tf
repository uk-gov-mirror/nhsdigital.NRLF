resource "aws_s3_bucket" "ci_data" {
  bucket = "${local.prefix}--ci-data"
}

resource "aws_s3_bucket_acl" "ci_data" {
  bucket = aws_s3_bucket.ci_data.id
  acl    = "private"

  depends_on = [
    aws_s3_bucket.ci_data
  ]
}

resource "aws_s3_bucket_public_access_block" "ci_data" {
  bucket = aws_s3_bucket.ci_data.id

  block_public_acls       = true
  block_public_policy     = true
  restrict_public_buckets = true
  ignore_public_acls      = true

  depends_on = [
    aws_s3_bucket.ci_data
  ]
}

resource "aws_s3_bucket_versioning" "ci_data" {
  bucket = aws_s3_bucket.ci_data.id
  versioning_configuration {
    status = "Enabled"
  }

  depends_on = [
    aws_s3_bucket.ci_data
  ]
}

resource "aws_s3_bucket_policy" "ci_data" {
  bucket = aws_s3_bucket.ci_data.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "${local.prefix}--ci-data-bucket-policy"
    Statement = [
      {
        Sid       = "HTTPSOnly"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.ci_data.arn,
          "${aws_s3_bucket.ci_data.arn}/*",
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
