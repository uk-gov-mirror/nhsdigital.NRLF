resource "aws_iam_policy" "pointers-table-read" {
  count       = var.use_shared_resources ? 1 : 0
  name        = "${local.prefix}-allow-pointers-table-read"
  description = "Read the pointers-table"
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
          data.aws_kms_key.pointers-table-key[0].arn
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
          "${data.aws_dynamodb_table.pointers-table[0].arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "pointers-table-write" {
  count       = var.use_shared_resources ? 1 : 0
  name        = "${local.prefix}-allow-pointers-table-write"
  description = "Write to the pointers-table"
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
          data.aws_kms_key.pointers-table-key[0].arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
        ],
        Resource = [
          "${data.aws_dynamodb_table.pointers-table[0].arn}*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "pointers-kms-read-write" {
  count       = var.use_shared_resources ? 1 : 0
  name        = "${local.prefix}-allow-pointers-kms-read-write"
  description = "Encrypt and decrypt with the pointers table kms key"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey"
        ]
        Effect = "Allow"
        Resource = [
          data.aws_kms_key.pointers-table-key[0].arn
        ]
      }
    ]
  })
}
