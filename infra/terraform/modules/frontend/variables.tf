variable "name_prefix" {
  type = string
}

variable "build_dir" {
  description = "Path to the built frontend assets (output of `npm run build`, i.e. frontend/dist)."
  type        = string
}
