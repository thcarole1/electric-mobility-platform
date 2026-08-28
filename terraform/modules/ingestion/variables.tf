variable "lambda_role_arn" {
  type = string
}

variable "ocm_api_key" {
  type      = string
  sensitive = true
}
