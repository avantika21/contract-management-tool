variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "db_name" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "database_security_group_id" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "aurora_min_capacity" {
  type = number
}

variable "aurora_max_capacity" {
  type = number
}
