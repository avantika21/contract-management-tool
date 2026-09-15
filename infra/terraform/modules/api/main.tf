data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "archive_file" "query_api" {
  type        = "zip"
  source_dir  = "${var.src_root}/query_api"
  output_path = "${path.module}/build/query_api.zip"
}

resource "aws_iam_role" "query_api" {
  name = "${var.name_prefix}-query-api-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "query_api" {
  name = "${var.name_prefix}-query-api-policy"
  role = aws_iam_role.query_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = [var.db_secret_arn] },
      { Effect = "Allow", Action = ["bedrock:InvokeModel"], Resource = "*" },
      { Effect = "Allow", Action = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"], Resource = ["${var.raw_bucket_arn}/*"] },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect   = "Allow"
        Action   = ["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"]
        Resource = "*"
      },
      { Effect = "Allow", Action = ["kms:Decrypt", "kms:GenerateDataKey"], Resource = var.kms_key_arn },
    ]
  })
}

resource "aws_lambda_function" "query_api" {
  function_name    = "${var.name_prefix}-query-api"
  description      = "Serves procurement-facing read/search endpoints over the contracts table"
  role             = aws_iam_role.query_api.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256
  filename         = data.archive_file.query_api.output_path
  source_code_hash = data.archive_file.query_api.output_base64sha256
  layers           = [var.dependencies_layer_arn]

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }

  environment {
    variables = {
      DB_SECRET_ARN      = var.db_secret_arn
      DB_HOST            = var.db_host
      DB_PORT            = tostring(var.db_port)
      LLM_MODEL_ID       = var.bedrock_extraction_model_id
      EMBEDDING_MODEL_ID = var.bedrock_embedding_model_id
      RAW_BUCKET         = var.raw_bucket_name
    }
  }
}

resource "aws_cloudwatch_log_group" "query_api" {
  name              = "/aws/lambda/${aws_lambda_function.query_api.function_name}"
  retention_in_days = 90
  kms_key_id        = var.kms_key_arn
}

resource "aws_apigatewayv2_api" "this" {
  name          = "${var.name_prefix}-procurement-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.cors_allowed_origins
    allow_methods = ["GET", "POST", "DELETE", "OPTIONS"]
    allow_headers = ["authorization", "content-type"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.this.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "${var.name_prefix}-cognito-authorizer"

  jwt_configuration {
    audience = [var.cognito_app_client_id]
    issuer   = "https://cognito-idp.${data.aws_region.current.name}.amazonaws.com/${var.cognito_user_pool_id}"
  }
}

resource "aws_apigatewayv2_integration" "query_api" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.query_api.invoke_arn
  payload_format_version = "2.0"
}

locals {
  routes = [
    "GET /contracts",
    "GET /contracts/{contract_id}",
    "GET /contracts/{contract_id}/file-url",
    "POST /contracts/{contract_id}/ask",
    "DELETE /contracts/{contract_id}",
    "POST /uploads",
  ]
}

resource "aws_apigatewayv2_route" "this" {
  for_each  = toset(local.routes)
  api_id    = aws_apigatewayv2_api.this.id
  route_key = each.value

  target             = "integrations/${aws_apigatewayv2_integration.query_api.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.query_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

resource "aws_cloudwatch_log_group" "api_access_logs" {
  name              = "/aws/apigateway/${var.name_prefix}-procurement-api"
  retention_in_days = 90
  kms_key_id        = var.kms_key_arn
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      integrationErr = "$context.integrationErrorMessage"
    })
  }
}
