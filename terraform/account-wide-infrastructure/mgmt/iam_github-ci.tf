resource "aws_iam_openid_connect_provider" "github_action" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = [
    # pragma: allowlist nextline secret
    "6938fd4d98bab03faadb97b34396831e3780aea1"
  ]
}

resource "aws_iam_role" "github_ci" {
  name = "${local.prefix}--github-ci"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_action.arn
        }
        Condition = {
          StringLike = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = "repo:NHSDigital/NRLF:*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_policy" "github_ci_policy" {
  name = "${local.prefix}--github-ci-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObject",
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:DeleteItem",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          data.aws_dynamodb_table.terraform_state_lock.arn,
          data.aws_s3_bucket.terraform_state.arn,
          "${data.aws_s3_bucket.terraform_state.arn}/*"
        ]
      },
      {
        Action = [
          "sts:AssumeRole",
          "sts:TagSession"
        ],
        Effect = "Allow"
        Resource = [
          "arn:aws:iam::${data.aws_secretsmanager_secret_version.dev_account_id.secret_string}:role/terraform",
          "arn:aws:iam::${data.aws_secretsmanager_secret_version.test_account_id.secret_string}:role/terraform",
          "arn:aws:iam::${data.aws_secretsmanager_secret_version.prod_account_id.secret_string}:role/terraform"
        ]
      },
      {
        Action = [
          "secretsmanager:GetResourcePolicy",
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
          "secretsmanager:ListSecretVersionIds"
        ]
        Effect = "Allow"
        Resource = [
          data.aws_secretsmanager_secret.dev_account_id.arn,
          data.aws_secretsmanager_secret.test_account_id.arn,
          data.aws_secretsmanager_secret.prod_account_id.arn
        ]
      },
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          data.aws_s3_bucket.truststore.arn,
          "${data.aws_s3_bucket.truststore.arn}/*"
        ]
      },
      {
        Action = [
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          aws_s3_bucket.ci_data.arn,
          "${aws_s3_bucket.ci_data.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "github_ci_policy_attachment" {
  role       = aws_iam_role.github_ci.name
  policy_arn = aws_iam_policy.github_ci_policy.arn
}
