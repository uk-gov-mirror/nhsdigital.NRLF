data "aws_iam_policy_document" "codebuild_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }

    actions = [
      "sts:AssumeRole",
      "sts:AssumeRoleWithWebIdentity",
      "sts:TagSession"
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = ["${data.aws_caller_identity.current.account_id}"]
    }
  }
}

resource "aws_iam_role" "codebuild_service_role" {
  name               = "${local.project}-codebuild-service-role"
  assume_role_policy = data.aws_iam_policy_document.codebuild_assume_role.json
}

data "aws_iam_policy_document" "codebuild_policy" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "codeconnections:GetConnectionToken",
      "codeconnections:GetConnection"
    ]
    resources = ["arn:aws:codestar-connections:us-east-1:123456789012:connection/guid-string"]
  }

  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret",
      "secretsmanager:ListSecretVersionIds"
    ]
    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:secret:${local.project}--codebuild-github-pat-*",
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:BatchCheckLayerAvailability"
    ]
    resources = [
      "${aws_ecr_repository.repository.arn}",
      "${aws_ecr_repository.repository.arn}:*"
    ]
  }
}

resource "aws_iam_role_policy" "codebuild_policy" {
  role   = aws_iam_role.codebuild_service_role.name
  policy = data.aws_iam_policy_document.codebuild_policy.json
}

resource "aws_codebuild_project" "project" {
  name         = "${local.project}-ci-build-project"
  description  = "NRLF CI Build Project"
  service_role = aws_iam_role.codebuild_service_role.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "${aws_ecr_repository.repository.repository_url}:${var.ci_image_tag}"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "${local.project}-ci-build-logs"
      stream_name = "build-log-stream"
    }
  }

  source {
    type            = "GITHUB"
    location        = "https://github.com/NHSDigital/NRLF"
    git_clone_depth = 1
  }

  source_version     = "main"
  project_visibility = "PRIVATE"
}

resource "aws_codebuild_webhook" "github_workflow" {
  project_name = aws_codebuild_project.project.name
  build_type   = "BUILD"
  filter_group {
    filter {
      type    = "EVENT"
      pattern = "WORKFLOW_JOB_QUEUED"
    }
  }
  depends_on = [aws_codebuild_project.project, aws_iam_role.codebuild_service_role]
}
