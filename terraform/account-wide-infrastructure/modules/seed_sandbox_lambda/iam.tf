resource "aws_iam_role" "lambda_role" {
  name = "${var.prefix}--sandbox-seeder"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

  depends_on = [
    aws_iam_role.lambda_role
  ]
}

resource "aws_iam_role_policy" "seed_sandbox_additional_permissions" {
  name = "${var.prefix}--sandbox-seeder-additional"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Effect = "Allow"
          Action = [
            "dynamodb:DescribeTable",
            "dynamodb:Scan",
            "dynamodb:Query",
            "dynamodb:GetItem",
            "dynamodb:PutItem",
            "dynamodb:DeleteItem",
            "dynamodb:BatchWriteItem"
          ]
          Resource = [for table_name in var.table_names : "arn:aws:dynamodb:${var.region}:${var.account_id}:table/${table_name}"]
        }
      ],
      length(var.kms_key_arns) > 0 ? [
        {
          Effect = "Allow"
          Action = [
            "kms:Decrypt",
            "kms:DescribeKey"
          ]
          Resource = var.kms_key_arns
        }
      ] : []
    )
  })
}
