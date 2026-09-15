variable "name_prefix" {
  type = string
}

variable "kms_key_arn" {
  type = string
}

variable "cors_allowed_origins" {
  description = "Origins allowed to PUT/GET directly against the raw contracts bucket via presigned URLs."
  type        = list(string)
}
