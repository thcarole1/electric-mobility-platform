variable "openchargemap_lambda_name" {
  type = string
}

variable "meteo_lambda_name" {
  type = string
}

variable "alert_email" {
  type        = string
  description = "Adresse email pour recevoir les alertes"
}
