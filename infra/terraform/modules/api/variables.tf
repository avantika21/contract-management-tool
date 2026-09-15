variable "name_prefix" {
  type = string
}

variable "src_root" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "lambda_security_group_id" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "db_secret_arn" {
  type = string
}

variable "db_host" {
  type = string
}

variable "db_port" {
  type = number
}

variable "bedrock_extraction_model_id" {
  type = string
}

variable "bedrock_embedding_model_id" {
  type = string
}

variable "dependencies_layer_arn" {
  type = string
}

variable "cognito_user_pool_id" {
  type = string
}

variable "cognito_app_client_id" {
  type = string
}

variable "raw_bucket_name" {
  type = string
}

variable "raw_bucket_arn" {
  type = string
}

variable "cors_allowed_origins" {
  description = "Origins allowed to call the API from a browser (the frontend's dev/hosted URL)."
  type        = list(string)
  default     = ["http://localhost:5173"]
}
