variable "aws_region" {
  description = "AWS region for all resources. Fixed to London for data residency."
  type        = string
  default     = "eu-west-2"
}

variable "environment" {
  description = "Deployment environment name (e.g. dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Short name used as a prefix for resource naming."
  type        = string
  default     = "cmt" # contract-management-tool
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "bedrock_extraction_model_id" {
  description = "Bedrock model id used for field extraction and contract Q&A. Must be a model available in eu-west-2."
  type        = string
  default     = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
}

variable "bedrock_embedding_model_id" {
  description = "Bedrock model id used to generate embeddings for chunk retrieval and reference comparison."
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "embedding_dimensions" {
  description = "Vector dimensionality produced by the embedding model (must match pgvector column definition)."
  type        = number
  default     = 1024
}

variable "aurora_min_capacity" {
  description = "Aurora Serverless v2 minimum ACU. 0 lets the cluster pause fully (and stop billing for compute) after ~5 minutes idle - good for a demo, at the cost of a ~15-30s cold-start on the next connection. Set to 0.5+ for anything latency-sensitive or with steady traffic."
  type        = number
  default     = 0
}

variable "aurora_max_capacity" {
  description = "Aurora Serverless v2 maximum ACU."
  type        = number
  default     = 4
}

variable "db_name" {
  description = "Name of the application database."
  type        = string
  default     = "contracts"
}

variable "alert_email" {
  description = "Email address to notify on pipeline failures. Leave blank to skip."
  type        = string
  default     = ""
}

variable "frontend_origins" {
  description = "Origins allowed to call the API from a browser (CORS) - the demo frontend's dev/hosted URL(s)."
  type        = list(string)
  default     = ["http://localhost:5173"]
}

variable "enable_bastion" {
  description = "Create a temporary SSM-only bastion host (plus the SSM VPC endpoints it needs) for one-off admin access to Aurora, which has no public endpoint. Turn off after initial setup/data-load to stop paying for the endpoints and instance."
  type        = bool
  default     = false
}

variable "allowed_upload_principals" {
  description = "IAM principal ARNs (procurement team roles/users) allowed to upload contracts to the raw S3 bucket."
  type        = list(string)
  default     = []
}
