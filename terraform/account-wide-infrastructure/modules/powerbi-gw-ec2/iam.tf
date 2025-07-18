resource "aws_iam_role" "ec2_service_role" {
  name = "${var.name_prefix}-ec2_service_role"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Principal" : {
          "Service" : "ec2.amazonaws.com"
        },
        "Action" : "sts:AssumeRole"
      }
    ]
  })
}

data "aws_iam_policy_document" "ec2_service" {
  statement {
    actions = [
      "s3:GetBucketLocation",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:ListBucketMultipartUploads",
      "s3:ListMultipartUploadParts",
      "s3:AbortMultipartUpload",
      "s3:CreateBucket",
      "s3:PutObject",
      "s3:PutBucketPublicAccessBlock"
    ]

    resources = compact([
      var.target_bucket_arn,
      "${var.target_bucket_arn}/*",
      var.athena_bucket_arn,
      "${var.athena_bucket_arn}/*",
    ])
    effect = "Allow"
  }

  statement {
    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
      "s3:ListAllMyBuckets"
    ]

    resources = compact([
      "*"
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
      var.glue_kms_key_arn,
      var.athena_kms_key_arn,
    ]

    effect = "Allow"
  }

  statement {
    actions = [
      "athena:*",
    ]
    effect = "Allow"
    resources = [
      "*"
    ]
  }

  statement {
    actions = [
      "glue:*",
    ]
    effect = "Allow"
    resources = [
      "*"
    ]
  }
}

resource "aws_iam_policy" "ec2_service" {
  name   = "${var.name_prefix}-ec2"
  policy = data.aws_iam_policy_document.ec2_service.json
}

resource "aws_iam_role_policy_attachment" "ec2_role_policy" {
  role       = aws_iam_role.ec2_service_role.name
  policy_arn = aws_iam_policy.ec2_service.arn
}

resource "aws_iam_role_policy_attachment" "ec2_role_policy_ssm" {
  role       = aws_iam_role.ec2_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "powerbi_profile" {
  name = "${var.name_prefix}-powerbi_instance_profile"
  role = aws_iam_role.ec2_service_role.name
}
