resource "aws_iam_role" "instance-role" {
  name = "${local.prefix}-instance-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "instance-profile" {
  name = "${local.prefix}-instance-profile"
  role = aws_iam_role.instance-role.name
}

resource "aws_iam_policy" "dynamodb-table-read" {
  count       = var.dynamodb_table_name != null ? 1 : 0
  name        = "${local.prefix}-allow-table-read"
  description = "Read the ${var.dynamodb_table_name} table"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Effect = "Allow"
        Resource = [
          data.aws_kms_key.dynamodb-table-key[0].arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:GetItem",
        ],
        Resource = [
          "${data.aws_dynamodb_table.dynamodb-table[0].arn}"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "dynamodb-table-write" {
  count       = var.allow_dynamodb_table_write && var.dynamodb_table_name != null ? 1 : 0
  name        = "${local.prefix}-allow-table-write"
  description = "Write to the ${var.dynamodb_table_name} table"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Effect = "Allow"
        Resource = [
          data.aws_kms_key.dynamodb-table-key[0].arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:BatchWriteItem"
        ],
        Resource = [
          "${data.aws_dynamodb_table.dynamodb-table[0].arn}"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "s3-metadata-bucket-readwrite" {
  name        = "${local.prefix}-allow-s3-metadata-bucket-readwrite"
  description = "Read and write access to the S3 metadata bucket"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:HeadObject",
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:DeleteObject"
        ],
        Resource = [
          "arn:aws:s3:::${var.s3_metadata_bucket_name}",
          "arn:aws:s3:::${var.s3_metadata_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_role_policy_ssm" {
  role       = aws_iam_role.instance-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}


resource "aws_iam_role_policy_attachment" "dynamodb-table-read-attachment" {
  count      = var.dynamodb_table_name != null ? 1 : 0
  role       = aws_iam_role.instance-role.name
  policy_arn = aws_iam_policy.dynamodb-table-read[0].arn
}

resource "aws_iam_role_policy_attachment" "dynamodb-table-write-attachment" {
  count      = var.allow_dynamodb_table_write && var.dynamodb_table_name != null ? 1 : 0
  role       = aws_iam_role.instance-role.name
  policy_arn = aws_iam_policy.dynamodb-table-write[0].arn
}

resource "aws_iam_role_policy_attachment" "s3-metadata-bucket-readwrite-attachment" {
  role       = aws_iam_role.instance-role.name
  policy_arn = aws_iam_policy.s3-metadata-bucket-readwrite.arn
}
