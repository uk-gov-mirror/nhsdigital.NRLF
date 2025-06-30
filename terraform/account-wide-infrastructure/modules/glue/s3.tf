# S3 Bucket for Raw Data
resource "aws_s3_bucket" "source-data-bucket" {
  bucket = "${var.name_prefix}-source-data-bucket"
}

resource "aws_s3_bucket_policy" "source-data-bucket" {
  bucket = "${var.name_prefix}-source-data-bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "source-data-bucket-policy"
    Statement = [
      {
        Sid    = "HTTPSOnly"
        Effect = "Deny"
        Principal = {
          "AWS" : "*"
        }
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.source-data-bucket.arn,
          "${aws_s3_bucket.source-data-bucket.arn}/*",
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

resource "aws_s3_bucket_server_side_encryption_configuration" "source-data-bucket" {
  bucket = aws_s3_bucket.source-data-bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.glue.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "source-data-bucket-public-access-block" {
  bucket = aws_s3_bucket.source-data-bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "source-data-bucket-lifecycle" {
  bucket = aws_s3_bucket.source-data-bucket.id


  rule {
    id     = "object-auto-delete-rule"
    status = "Enabled"

    expiration {
      days = local.s3.expiration.days
    }
  }
}

resource "aws_s3_bucket_versioning" "source-data-bucket-versioning" {
  bucket = aws_s3_bucket.source-data-bucket.id
  versioning_configuration {
    status = "Disabled"
  }
}


# S3 Bucket for Processed Data
resource "aws_s3_bucket" "target-data-bucket" {
  bucket = "${var.name_prefix}-target-data-bucket"
}

resource "aws_s3_bucket_policy" "target-data-bucket" {
  bucket = "${var.name_prefix}-target-data-bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "target-data-bucket-policy"
    Statement = [
      {
        Sid    = "HTTPSOnly"
        Effect = "Deny"
        Principal = {
          "AWS" : "*"
        }
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.target-data-bucket.arn,
          "${aws_s3_bucket.target-data-bucket.arn}/*",
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

resource "aws_s3_bucket_server_side_encryption_configuration" "target-data-bucket" {
  bucket = aws_s3_bucket.target-data-bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.glue.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "target-data-bucket-public-access-block" {
  bucket = aws_s3_bucket.target-data-bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket for Code
resource "aws_s3_bucket" "code-bucket" {
  bucket = "${var.name_prefix}-code-bucket"
}

resource "aws_s3_bucket_policy" "code-bucket" {
  bucket = "${var.name_prefix}-code-bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "code-bucket-policy"
    Statement = [
      {
        Sid    = "HTTPSOnly"
        Effect = "Deny"
        Principal = {
          "AWS" : "*"
        }
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.code-bucket.arn,
          "${aws_s3_bucket.code-bucket.arn}/*",
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

resource "aws_s3_bucket_server_side_encryption_configuration" "code-bucket" {
  bucket = aws_s3_bucket.code-bucket.bucket

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.glue.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "code-bucket-public-access-block" {
  bucket = aws_s3_bucket.code-bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "script" {
  bucket      = aws_s3_bucket.code-bucket.bucket
  key         = "main.py"
  source      = "${path.module}/src/main.py"
  source_hash = filemd5("${path.module}/src/main.py")
}

data "archive_file" "python" {
  type        = "zip"
  output_path = "${path.module}/files/src.zip"

  source_dir = "${path.module}/src"
}

resource "aws_s3_object" "zip" {
  bucket      = aws_s3_bucket.code-bucket.bucket
  key         = "src.zip"
  source      = data.archive_file.python.output_path
  source_hash = filemd5(data.archive_file.python.output_path)
}
