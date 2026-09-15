resource "random_password" "master" {
  length  = 32
  special = false # avoid chars that need escaping in connection strings
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-db-subnets"
  subnet_ids = var.private_subnet_ids
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name       = "${var.name_prefix}/db/master-credentials"
  kms_key_id = var.kms_key_arn
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = "cmt_admin"
    password = random_password.master.result
    dbname   = var.db_name
    engine   = "postgres"
    port     = 5432
  })
}

# Aurora Serverless v2, PostgreSQL 16 - pgvector (>= 0.5) ships with the
# engine from 15.4 / 16.1 onwards, so no custom extension bootstrap is
# needed beyond `CREATE EXTENSION vector` in scripts/init_db.sql.
resource "aws_rds_cluster" "this" {
  cluster_identifier     = "${var.name_prefix}-cluster"
  engine                 = "aurora-postgresql"
  engine_mode            = "provisioned"
  engine_version         = "16.14"
  database_name          = var.db_name
  master_username        = "cmt_admin"
  master_password        = random_password.master.result
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [var.database_security_group_id]

  storage_encrypted         = true
  kms_key_id                = var.kms_key_arn
  deletion_protection       = var.environment == "prod"
  skip_final_snapshot       = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${var.name_prefix}-final-snapshot" : null
  backup_retention_period   = 14
  preferred_backup_window   = "02:00-03:00"

  serverlessv2_scaling_configuration {
    min_capacity = var.aurora_min_capacity
    max_capacity = var.aurora_max_capacity
  }
}

resource "aws_rds_cluster_instance" "this" {
  cluster_identifier   = aws_rds_cluster.this.id
  instance_class       = "db.serverless"
  engine               = aws_rds_cluster.this.engine
  engine_version       = aws_rds_cluster.this.engine_version
  db_subnet_group_name = aws_db_subnet_group.this.name
}
