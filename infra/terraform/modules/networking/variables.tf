variable "name_prefix" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "enable_ssm_endpoints" {
  description = "Add the ssm/ssmmessages/ec2messages interface endpoints needed to reach a bastion host over SSM (no NAT gateway in this VPC, so these are required whenever a bastion is present)."
  type        = bool
  default     = false
}
