# Define a reusable map of allowed methods for each path
data "aws_api_gateway_resource" "resource" {
  for_each    = var.endpoint_allowed_methods
  rest_api_id = aws_api_gateway_rest_api.api_gateway_rest_api.id
  path        = each.key

  depends_on = [aws_api_gateway_rest_api.api_gateway_rest_api]
}

# Add HEAD method to each resource with 405 response
resource "aws_api_gateway_method" "head_method" {
  for_each = var.endpoint_allowed_methods

  rest_api_id   = aws_api_gateway_rest_api.api_gateway_rest_api.id
  resource_id   = data.aws_api_gateway_resource.resource[each.key].id
  http_method   = "HEAD"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "head_integration" {
  for_each = var.endpoint_allowed_methods

  rest_api_id = aws_api_gateway_rest_api.api_gateway_rest_api.id
  resource_id = data.aws_api_gateway_resource.resource[each.key].id
  http_method = aws_api_gateway_method.head_method[each.key].http_method
  type        = "MOCK"
  # passthrough_behavior = "WHEN_NO_TEMPLATES"
  passthrough_behavior = "WHEN_NO_MATCH"

  request_templates = {
    "application/json"      = <<-EOF
      { "statusCode": 405 }
    EOF
    "application/json+fhir" = <<-EOF
      { "statusCode": 405 }
    EOF
    "application/fhir+json" = <<-EOF
      { "statusCode": 405 }
    EOF
  }
}

resource "aws_api_gateway_method_response" "head_method_response" {
  for_each = var.endpoint_allowed_methods

  rest_api_id = aws_api_gateway_rest_api.api_gateway_rest_api.id
  resource_id = data.aws_api_gateway_resource.resource[each.key].id
  http_method = aws_api_gateway_method.head_method[each.key].http_method
  status_code = "405"

  response_parameters = {
    "method.response.header.Allow" = true
  }
}

resource "aws_api_gateway_integration_response" "head_integration_response" {
  for_each = var.endpoint_allowed_methods

  rest_api_id       = aws_api_gateway_rest_api.api_gateway_rest_api.id
  resource_id       = data.aws_api_gateway_resource.resource[each.key].id
  http_method       = aws_api_gateway_method.head_method[each.key].http_method
  status_code       = aws_api_gateway_method_response.head_method_response[each.key].status_code
  selection_pattern = "" # default catch-all

  response_parameters = {
    "method.response.header.Allow" = "'${each.value}'"
  }
}
