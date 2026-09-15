variable "name_prefix" {
  type = string
}

variable "account_id" {
  type = string
}

variable "callback_urls" {
  type    = list(string)
  default = ["http://localhost:3000/callback"]
}

variable "logout_urls" {
  type    = list(string)
  default = ["http://localhost:3000/"]
}
