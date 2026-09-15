data "aws_caller_identity" "current" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  repo_root   = abspath("${path.module}/../..")
}

module "networking" {
  source = "./modules/networking"

  name_prefix          = local.name_prefix
  aws_region           = var.aws_region
  vpc_cidr             = var.vpc_cidr
  enable_ssm_endpoints = var.enable_bastion
}

module "security" {
  source = "./modules/security"

  name_prefix = local.name_prefix
  aws_region  = var.aws_region
}

module "storage" {
  source = "./modules/storage"

  name_prefix          = local.name_prefix
  kms_key_arn          = module.security.kms_key_arn
  cors_allowed_origins = distinct(concat(var.frontend_origins, ["https://${module.frontend.cloudfront_domain_name}"]))
}

module "database" {
  source = "./modules/database"

  name_prefix                = local.name_prefix
  environment                = var.environment
  db_name                    = var.db_name
  private_subnet_ids         = module.networking.private_subnet_ids
  database_security_group_id = module.networking.database_security_group_id
  kms_key_arn                = module.security.kms_key_arn
  aurora_min_capacity        = var.aurora_min_capacity
  aurora_max_capacity        = var.aurora_max_capacity
}

module "auth" {
  source = "./modules/auth"

  name_prefix = local.name_prefix
  account_id  = data.aws_caller_identity.current.account_id
}

resource "aws_sns_topic" "alerts" {
  count             = var.alert_email == "" ? 0 : 1
  name              = "${local.name_prefix}-pipeline-alerts"
  kms_master_key_id = module.security.kms_key_id
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count     = var.alert_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

module "pipeline" {
  source = "./modules/pipeline"

  name_prefix                 = local.name_prefix
  src_root                    = "${local.repo_root}/src"
  layer_build_dir             = "${local.repo_root}/build/layer"
  private_subnet_ids          = module.networking.private_subnet_ids
  lambda_security_group_id    = module.networking.lambda_security_group_id
  kms_key_arn                 = module.security.kms_key_arn
  raw_bucket_name             = module.storage.raw_bucket_name
  raw_bucket_arn              = module.storage.raw_bucket_arn
  db_secret_arn               = module.database.secret_arn
  db_host                     = module.database.cluster_endpoint
  db_port                     = module.database.cluster_port
  bedrock_embedding_model_id  = var.bedrock_embedding_model_id
  bedrock_extraction_model_id = var.bedrock_extraction_model_id
  embedding_dimensions        = var.embedding_dimensions
  alert_topic_arn             = var.alert_email == "" ? "" : aws_sns_topic.alerts[0].arn
}

module "bastion" {
  count  = var.enable_bastion ? 1 : 0
  source = "./modules/bastion"

  name_prefix       = local.name_prefix
  vpc_id            = module.networking.vpc_id
  private_subnet_id = module.networking.private_subnet_ids[0]
}

resource "aws_security_group_rule" "db_from_bastion" {
  count                    = var.enable_bastion ? 1 : 0
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = module.networking.database_security_group_id
  source_security_group_id = module.bastion[0].security_group_id
  description              = "PostgreSQL from the temporary admin bastion"
}

resource "aws_iam_role_policy" "bastion_db_secret" {
  count = var.enable_bastion ? 1 : 0
  name  = "${local.name_prefix}-bastion-db-secret"
  role  = module.bastion[0].iam_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = [module.database.secret_arn] },
      { Effect = "Allow", Action = ["kms:Decrypt"], Resource = [module.security.kms_key_arn] },
    ]
  })
}

module "frontend" {
  source = "./modules/frontend"

  name_prefix = local.name_prefix
  build_dir   = "${local.repo_root}/frontend/dist"
}

module "api" {
  source = "./modules/api"

  name_prefix                 = local.name_prefix
  src_root                    = "${local.repo_root}/src"
  private_subnet_ids          = module.networking.private_subnet_ids
  lambda_security_group_id    = module.networking.lambda_security_group_id
  kms_key_arn                 = module.security.kms_key_arn
  db_secret_arn               = module.database.secret_arn
  db_host                     = module.database.cluster_endpoint
  db_port                     = module.database.cluster_port
  bedrock_extraction_model_id = var.bedrock_extraction_model_id
  bedrock_embedding_model_id  = var.bedrock_embedding_model_id
  dependencies_layer_arn      = module.pipeline.dependencies_layer_arn
  cognito_user_pool_id        = module.auth.user_pool_id
  cognito_app_client_id       = module.auth.app_client_id
  raw_bucket_name             = module.storage.raw_bucket_name
  raw_bucket_arn              = module.storage.raw_bucket_arn
  cors_allowed_origins        = distinct(concat(var.frontend_origins, ["https://${module.frontend.cloudfront_domain_name}"]))
}
