data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  functions = {
    extraction = {
      description = "Runs Textract over the uploaded PDF and writes plain text to S3"
      source_dir  = "${var.src_root}/extraction"
      handler     = "handler.handler"
      timeout     = 300
      memory      = 512
      env = {
        RAW_BUCKET    = var.raw_bucket_name
        DB_SECRET_ARN = var.db_secret_arn
        DB_HOST       = var.db_host
        DB_PORT       = tostring(var.db_port)
      }
      statements = [
        {
          actions   = ["s3:GetObject"]
          resources = ["${var.raw_bucket_arn}/*"]
        },
        {
          actions   = ["s3:PutObject"]
          resources = ["${var.raw_bucket_arn}/extracted/*"]
        },
        {
          actions   = ["textract:DetectDocumentText", "textract:StartDocumentTextDetection", "textract:GetDocumentTextDetection"]
          resources = ["*"]
        },
        {
          actions   = ["secretsmanager:GetSecretValue"]
          resources = [var.db_secret_arn]
        },
      ]
    }

    chunk_embed = {
      description = "Chunks extracted text and stores embeddings in Aurora/pgvector"
      source_dir  = "${var.src_root}/chunk_embed"
      handler     = "handler.handler"
      timeout     = 300
      memory      = 512
      env = {
        RAW_BUCKET           = var.raw_bucket_name
        DB_SECRET_ARN        = var.db_secret_arn
        DB_HOST              = var.db_host
        DB_PORT              = tostring(var.db_port)
        EMBEDDING_MODEL_ID   = var.bedrock_embedding_model_id
        EMBEDDING_DIMENSIONS = tostring(var.embedding_dimensions)
      }
      statements = [
        { actions = ["s3:GetObject"], resources = ["${var.raw_bucket_arn}/extracted/*"] },
        { actions = ["secretsmanager:GetSecretValue"], resources = [var.db_secret_arn] },
        { actions = ["bedrock:InvokeModel"], resources = ["*"] },
      ]
    }

    field_extraction = {
      description = "Retrieves the relevant chunks and asks the LLM to extract structured contract fields"
      source_dir  = "${var.src_root}/field_extraction"
      handler     = "handler.handler"
      timeout     = 180
      memory      = 512
      env = {
        DB_SECRET_ARN      = var.db_secret_arn
        DB_HOST            = var.db_host
        DB_PORT            = tostring(var.db_port)
        LLM_MODEL_ID       = var.bedrock_extraction_model_id
        EMBEDDING_MODEL_ID = var.bedrock_embedding_model_id
      }
      statements = [
        { actions = ["secretsmanager:GetSecretValue"], resources = [var.db_secret_arn] },
        { actions = ["bedrock:InvokeModel"], resources = ["*"] },
      ]
    }

    store_results = {
      description = "Writes the final structured record to the contracts table"
      source_dir  = "${var.src_root}/store_results"
      handler     = "handler.handler"
      timeout     = 60
      memory      = 256
      env = {
        DB_SECRET_ARN = var.db_secret_arn
        DB_HOST       = var.db_host
        DB_PORT       = tostring(var.db_port)
      }
      statements = [
        { actions = ["secretsmanager:GetSecretValue"], resources = [var.db_secret_arn] },
      ]
    }
  }
}

# Shared dependency layer (pg8000 for pgvector/Postgres access - a pure
# Python driver, deliberately chosen over psycopg2 so the layer builds
# with a plain `pip install` and needs no compiled/platform-specific
# wheel). Build it first with scripts/build_layer.sh.
data "archive_file" "layer" {
  type        = "zip"
  source_dir  = var.layer_build_dir
  output_path = "${path.module}/build/layer.zip"
}

resource "aws_lambda_layer_version" "dependencies" {
  layer_name          = "${var.name_prefix}-deps"
  filename            = data.archive_file.layer.output_path
  source_code_hash    = data.archive_file.layer.output_base64sha256
  compatible_runtimes = ["python3.12"]
}

data "archive_file" "lambda_zip" {
  for_each    = local.functions
  type        = "zip"
  source_dir  = each.value.source_dir
  output_path = "${path.module}/build/${each.key}.zip"
}

resource "aws_iam_role" "lambda" {
  for_each = local.functions
  name     = "${var.name_prefix}-${replace(each.key, "_", "-")}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda" {
  for_each = local.functions
  name     = "${var.name_prefix}-${replace(each.key, "_", "-")}-policy"
  role     = aws_iam_role.lambda[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [for s in each.value.statements : {
        Effect   = "Allow"
        Action   = s.actions
        Resource = s.resources
      }],
      [
        {
          Effect = "Allow"
          Action = [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents",
          ]
          Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
        },
        {
          Effect = "Allow"
          Action = [
            "ec2:CreateNetworkInterface",
            "ec2:DescribeNetworkInterfaces",
            "ec2:DeleteNetworkInterface",
          ]
          Resource = "*"
        },
        {
          Effect   = "Allow"
          Action   = "kms:Decrypt"
          Resource = var.kms_key_arn
        },
      ]
    )
  })
}

resource "aws_lambda_function" "this" {
  for_each = local.functions

  function_name    = "${var.name_prefix}-${replace(each.key, "_", "-")}"
  description      = each.value.description
  role             = aws_iam_role.lambda[each.key].arn
  handler          = each.value.handler
  runtime          = "python3.12"
  timeout          = each.value.timeout
  memory_size      = each.value.memory
  filename         = data.archive_file.lambda_zip[each.key].output_path
  source_code_hash = data.archive_file.lambda_zip[each.key].output_base64sha256
  layers           = [aws_lambda_layer_version.dependencies.arn]

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }

  environment {
    variables = each.value.env
  }

  tracing_config {
    mode = "Active"
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  for_each          = local.functions
  name              = "/aws/lambda/${aws_lambda_function.this[each.key].function_name}"
  retention_in_days = 90
  kms_key_id        = var.kms_key_arn
}

# --- Step Functions -----------------------------------------------------

resource "aws_iam_role" "state_machine" {
  name = "${var.name_prefix}-pipeline-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "state_machine" {
  name = "${var.name_prefix}-pipeline-sfn-policy"
  role = aws_iam_role.state_machine.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat(
      [
        {
          Effect   = "Allow"
          Action   = "lambda:InvokeFunction"
          Resource = [for f in aws_lambda_function.this : f.arn]
        },
        {
          Effect = "Allow"
          Action = [
            "logs:CreateLogDelivery",
            "logs:GetLogDelivery",
            "logs:UpdateLogDelivery",
            "logs:DeleteLogDelivery",
            "logs:ListLogDeliveries",
            "logs:PutResourcePolicy",
            "logs:DescribeResourcePolicies",
            "logs:DescribeLogGroups",
          ]
          Resource = "*"
        },
      ],
      var.alert_topic_arn == "" ? [] : [{
        Effect   = "Allow"
        Action   = "sns:Publish"
        Resource = var.alert_topic_arn
      }]
    )
  })
}

resource "aws_cloudwatch_log_group" "state_machine" {
  name              = "/aws/vendedlogs/states/${var.name_prefix}-contract-pipeline"
  retention_in_days = 90
  kms_key_id        = var.kms_key_arn
}

resource "aws_sfn_state_machine" "pipeline" {
  name     = "${var.name_prefix}-contract-pipeline"
  role_arn = aws_iam_role.state_machine.arn

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.state_machine.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  definition = jsonencode({
    Comment = "Contract ingestion: extract text -> chunk & embed -> extract fields -> store"
    StartAt = "ExtractText"
    States = {
      ExtractText = {
        Type     = "Task"
        Resource = aws_lambda_function.this["extraction"].arn
        Retry    = [{ ErrorEquals = ["States.TaskFailed"], IntervalSeconds = 5, MaxAttempts = 3, BackoffRate = 2 }]
        Catch    = [{ ErrorEquals = ["States.ALL"], ResultPath = "$.error", Next = "PipelineFailed" }]
        Next     = "ChunkAndEmbed"
      }
      ChunkAndEmbed = {
        Type     = "Task"
        Resource = aws_lambda_function.this["chunk_embed"].arn
        Retry    = [{ ErrorEquals = ["States.TaskFailed"], IntervalSeconds = 5, MaxAttempts = 3, BackoffRate = 2 }]
        Catch    = [{ ErrorEquals = ["States.ALL"], ResultPath = "$.error", Next = "PipelineFailed" }]
        Next     = "ExtractFields"
      }
      ExtractFields = {
        Type     = "Task"
        Resource = aws_lambda_function.this["field_extraction"].arn
        Retry    = [{ ErrorEquals = ["States.TaskFailed"], IntervalSeconds = 5, MaxAttempts = 2, BackoffRate = 2 }]
        Catch    = [{ ErrorEquals = ["States.ALL"], ResultPath = "$.error", Next = "PipelineFailed" }]
        Next     = "StoreResults"
      }
      StoreResults = {
        Type     = "Task"
        Resource = aws_lambda_function.this["store_results"].arn
        Retry    = [{ ErrorEquals = ["States.TaskFailed"], IntervalSeconds = 5, MaxAttempts = 3, BackoffRate = 2 }]
        Catch    = [{ ErrorEquals = ["States.ALL"], ResultPath = "$.error", Next = "PipelineFailed" }]
        End      = true
      }
      PipelineFailed = {
        Type  = "Fail"
        Error = "ContractPipelineFailed"
      }
    }
  })
}

# --- Trigger: new object in the raw bucket starts the state machine ----

resource "aws_cloudwatch_event_rule" "on_upload" {
  name        = "${var.name_prefix}-contract-uploaded"
  description = "Fires when a new contract PDF lands in the raw bucket"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = { name = [var.raw_bucket_name] }
      object = { key = [{ prefix = "raw/" }] }
    }
  })
}

resource "aws_iam_role" "eventbridge_sfn" {
  name = "${var.name_prefix}-eventbridge-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_sfn" {
  name = "${var.name_prefix}-eventbridge-sfn-policy"
  role = aws_iam_role.eventbridge_sfn.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "states:StartExecution"
      Resource = aws_sfn_state_machine.pipeline.arn
    }]
  })
}

resource "aws_cloudwatch_event_target" "start_pipeline" {
  rule     = aws_cloudwatch_event_rule.on_upload.name
  arn      = aws_sfn_state_machine.pipeline.arn
  role_arn = aws_iam_role.eventbridge_sfn.arn

  input_transformer {
    input_paths = {
      bucket = "$.detail.bucket.name"
      key    = "$.detail.object.key"
    }
    input_template = "{\"bucket\": <bucket>, \"key\": <key>}"
  }
}
