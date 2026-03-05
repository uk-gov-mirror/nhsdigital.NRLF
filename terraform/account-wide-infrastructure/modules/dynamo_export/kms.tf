resource "aws_kms_key" "dynamo" {
}

resource "aws_kms_alias" "dynamo" {
  name          = "alias/${var.name_prefix}-dynamo-output-bucket"
  target_key_id = aws_kms_key.dynamo.key_id
}

resource "aws_kms_key" "dynamo_processed" {
}

resource "aws_kms_alias" "dynamo_processed" {
  name          = "alias/${var.name_prefix}-dynamo-processed-output-bucket"
  target_key_id = aws_kms_key.dynamo_processed.key_id
}
