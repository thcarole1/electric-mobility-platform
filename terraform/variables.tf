variable "ocm_api_key" {
  description = "Clé API Open Charge Map"
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Adresse email pour recevoir les alertes de monitoring"
  type        = string
}
