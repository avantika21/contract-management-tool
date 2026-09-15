data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${var.name_prefix}-vpc" }
}

# Private subnets only. Nothing in this system needs a public IP or an
# internet gateway/NAT - all AWS service traffic (S3, Textract, Bedrock,
# Secrets Manager) is reached over VPC endpoints so data never leaves
# the AWS network, let alone the region.
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = { Name = "${var.name_prefix}-private-${count.index}" }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.name_prefix}-private-rt" }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# --- Security groups ----------------------------------------------------

resource "aws_security_group" "lambda" {
  name_prefix = "${var.name_prefix}-lambda-"
  description = "Pipeline and API Lambdas"
  vpc_id      = aws_vpc.this.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.name_prefix}-lambda-sg" }
}

resource "aws_security_group" "database" {
  name_prefix = "${var.name_prefix}-db-"
  description = "Aurora PostgreSQL cluster"
  vpc_id      = aws_vpc.this.id

  tags = { Name = "${var.name_prefix}-db-sg" }
}

# Standalone rule resources rather than an inline `ingress` block on the
# security group above - inline blocks are authoritative for the whole
# rule set, so mixing them with a rule added elsewhere (e.g. the root
# module's temporary bastion access) causes Terraform to revoke that
# externally-added rule on every apply.
resource "aws_security_group_rule" "database_from_lambda" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.database.id
  source_security_group_id = aws_security_group.lambda.id
  description              = "PostgreSQL from pipeline/API Lambdas"
}

# --- VPC Endpoints -----------------------------------------------------

resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "${var.name_prefix}-vpce-"
  description = "Allow HTTPS from Lambdas to interface VPC endpoints"
  vpc_id      = aws_vpc.this.id

  # Scoped to the VPC CIDR rather than a single security group so an
  # occasional admin bastion can also reach these endpoints (e.g. for SSM)
  # without a cross-module security group reference - the VPC has no
  # internet exposure regardless.
  ingress {
    description = "HTTPS from within the VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.name_prefix}-vpce-sg" }
}

# S3 is reached via a gateway endpoint (no ENI cost, routes at the route-table level)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id]
}

locals {
  # Only what the in-VPC Lambdas actually call. Step Functions invokes
  # these Lambdas (not the other way round), so no "states" endpoint is
  # needed - that's one fewer interface endpoint (~$14.60/month at 2 AZs).
  interface_endpoints = concat(
    [
      "textract",
      "bedrock-runtime",
      "secretsmanager",
      "logs",
    ],
    var.enable_ssm_endpoints ? ["ssm", "ssmmessages", "ec2messages"] : []
  )
}

resource "aws_vpc_endpoint" "interface" {
  for_each            = toset(local.interface_endpoints)
  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${var.aws_region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = { Name = "${var.name_prefix}-vpce-${each.value}" }
}
