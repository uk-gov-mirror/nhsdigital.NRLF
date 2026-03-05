resource "aws_s3_bucket" "dynamodb_output" {
  bucket = "${var.name_prefix}-${var.environment}-dynamo-output-bucket"
}

# May need to restrict access to specific IAM roles/principals in future, but helps with testing for now.
data "aws_iam_policy_document" "dynamodb_output" {
  statement {
    sid     = "HTTPSOnly"
    effect  = "Deny"
    actions = ["s3:*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    resources = [
      aws_s3_bucket.dynamodb_output.arn,
      "${aws_s3_bucket.dynamodb_output.arn}/*"
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "dynamodb_output" {
  bucket = aws_s3_bucket.dynamodb_output.id
  policy = data.aws_iam_policy_document.dynamodb_output.json
}


resource "aws_s3_bucket_server_side_encryption_configuration" "dynamodb_output" {
  bucket = aws_s3_bucket.dynamodb_output.bucket

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.dynamo.arn
      sse_algorithm     = "aws:kms"
    }
  }
}


resource "aws_s3_bucket_public_access_block" "dynamodb_output_public_access_block" {
  bucket = aws_s3_bucket.dynamodb_output.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "dynamodb_output_lifecycle" {
  bucket = aws_s3_bucket.dynamodb_output.id


  rule {
    id     = "object-auto-delete-rule"
    status = "Enabled"
    filter {}

    expiration {
      days = 2
    }
  }
}

resource "aws_s3_bucket_versioning" "dynamodb_output_versioning" {
  bucket = aws_s3_bucket.dynamodb_output.id
  versioning_configuration {
    status = "Enabled"
  }
}
