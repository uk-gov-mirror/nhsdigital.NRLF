resource "aws_s3_bucket" "dynamodb_output_processed" {
  bucket = "${var.name_prefix}-${var.environment}-dynamo-output-processed-bucket"
}

data "aws_iam_policy_document" "dynamodb_output_processed" {
  statement {
    sid     = "HTTPSOnly"
    effect  = "Deny"
    actions = ["s3:*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    resources = [
      aws_s3_bucket.dynamodb_output_processed.arn,
      "${aws_s3_bucket.dynamodb_output_processed.arn}/*"
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "dynamodb_output_processed" {
  bucket = aws_s3_bucket.dynamodb_output_processed.id
  policy = data.aws_iam_policy_document.dynamodb_output_processed.json
}


resource "aws_s3_bucket_server_side_encryption_configuration" "dynamodb_output_processed" {
  bucket = aws_s3_bucket.dynamodb_output_processed.bucket

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.dynamo_processed.arn
      sse_algorithm     = "aws:kms"
    }
  }
}


resource "aws_s3_bucket_public_access_block" "dynamodb_output_processed_public_access_block" {
  bucket = aws_s3_bucket.dynamodb_output_processed.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "dynamodb_output_processed_lifecycle" {
  bucket = aws_s3_bucket.dynamodb_output_processed.id


  rule {
    id     = "object-auto-delete-rule"
    status = "Enabled"
    filter {}

    expiration {
      days = 3 * 365
    }
  }
}

resource "aws_s3_bucket_versioning" "dynamodb_output_processed_versioning" {
  bucket = aws_s3_bucket.dynamodb_output_processed.id
  versioning_configuration {
    status = "Enabled"
  }
}
