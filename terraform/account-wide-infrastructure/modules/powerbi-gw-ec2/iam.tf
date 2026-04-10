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
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:ListMultipartUploadParts",
      "s3:AbortMultipartUpload",
      "s3:PutObject",
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
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:GetWorkGroup",
      "athena:ListTagsForResource",
      "athena:TagResource",
      "athena:UntagResource",
      "athena:GetCatalogs",
      "athena:GetExecutionEngine",
      "athena:GetExecutionEngines",
      "athena:GetNamespace",
      "athena:GetNamespaces",
      "athena:GetQueryExecutions",
      "athena:GetTable",
      "athena:GetTables",
      "athena:ListDatabases",
      "athena:ListDataCatalogs",
      "athena:ListTableMetadata",
      "athena:RunQuery",
      "athena:CancelQueryExecution",
      "athena:StartQueryExecution"
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

  statement {
    effect = "Allow"
    actions = [
      "ssm:GetDeployablePatchSnapshotForInstance",
      "ssm:GetDocument",
      "ssm:GetManifest",
      "ssm:ListAssociations",
      "ssm:ListInstanceAssociations",
      "ssm:PutInventory",
      "ssm:PutComplianceItems",
      "ssm:PutConfigurePackageResult",
      "ssm:UpdateInstanceAssociationStatus",
      "ssm:UpdateInstanceInformation",
      "ec2messages:AcknowledgeMessage",
      "ec2messages:DeleteMessage",
      "ec2messages:FailMessage",
      "ec2messages:GetEndpoint",
      "ec2messages:GetMessages",
      "ec2messages:SendReply",
      "ssmmessages:CreateControlChannel",
      "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel",
      "ssmmessages:OpenDataChannel"
    ]
    resources = [
      "*"
    ]
  }
}

resource "aws_iam_policy" "ec2_role_policy" {
  name   = "${var.name_prefix}-ec2-role-policy"
  policy = data.aws_iam_policy_document.ec2_service.json
}

resource "aws_iam_role_policy_attachment" "ec2_role_policy_attachment" {
  role       = aws_iam_role.ec2_service_role.name
  policy_arn = aws_iam_policy.ec2_role_policy.arn
}

resource "aws_iam_instance_profile" "powerbi_profile" {
  name = "${var.name_prefix}-powerbi_instance_profile"
  role = aws_iam_role.ec2_service_role.name
}
