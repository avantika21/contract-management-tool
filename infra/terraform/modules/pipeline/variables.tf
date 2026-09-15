variable "name_prefix" {
  type = string
}

variable "src_root" {
  description = "Absolute path to the repo's src/ directory containing one folder per Lambda."
  type        = string
}

variable "layer_build_dir" {
  description = "Path to the built Python dependency layer (see scripts/build_layer.sh)."
  type        = string
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

variable "raw_bucket_name" {
  type = string
}

variable "raw_bucket_arn" {
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

variable "bedrock_embedding_model_id" {
  type = string
}

variable "bedrock_extraction_model_id" {
  type = string
}

variable "embedding_dimensions" {
  type = number
}

variable "alert_topic_arn" {
  type    = string
  default = ""
}
