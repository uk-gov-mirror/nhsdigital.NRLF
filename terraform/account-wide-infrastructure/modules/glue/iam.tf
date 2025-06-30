resource "aws_iam_role" "glue_service_role" {
  name = "${var.name_prefix}-glue_service_role"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "glue.amazonaws.com"
        },
        "Action" : "sts:AssumeRole"
      }
    ]
  })
}

data "aws_iam_policy_document" "glue_service" {
  statement {
    actions = [
      "s3:AbortMultipartUpload",
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:PutObject",
      "s3:DeleteObject",
    ]

    resources = compact([
      aws_s3_bucket.source-data-bucket.arn,
      "${aws_s3_bucket.source-data-bucket.arn}/*",
      aws_s3_bucket.target-data-bucket.arn,
      "${aws_s3_bucket.target-data-bucket.arn}/*",
      aws_s3_bucket.code-bucket.arn,
      "${aws_s3_bucket.code-bucket.arn}/*",
    ])
    effect = "Allow"
  }

  statement {
    actions = [
      "kms:DescribeKey",
      "kms:GenerateDataKey*",
      "kms:Encrypt",
      "kms:ReEncrypt*",
      "kms:Decrypt",
    ]

    resources = [
      aws_kms_key.glue.arn,
    ]

    effect = "Allow"
  }

  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = [
      "arn:aws:logs:*:*:*:/aws-glue/*",
    ]

    effect = "Allow"
  }

  statement {
    actions = [
      "glue:*",
    ]

    resources = [
      "*"
    ]

    effect = "Allow"
  }

  statement {
    actions = [
      "cloudwatch:Get*",
      "cloudwatch:List*",
      "cloudwatch:Put*",
    ]
    resources = [
      "*"
    ]
    effect = "Allow"
  }

  statement {
    actions = [
      "iam:PassRole",
    ]
    effect = "Allow"
    resources = [
      "arn:aws:iam::*:role/AWSGlueServiceRole*",
      aws_iam_role.glue_service_role.arn,
    ]
  }
}

resource "aws_iam_policy" "glue_service" {
  name   = "${var.name_prefix}-glue"
  policy = data.aws_iam_policy_document.glue_service.json
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_service_role.name
  policy_arn = aws_iam_policy.glue_service.arn
}
