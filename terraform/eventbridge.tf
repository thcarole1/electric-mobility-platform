resource "aws_scheduler_schedule" "openchargemap_daily" {
  name                         = "electric-mobility-ingestion-openchargemap-daily"
  description                  = "Déclenchement quotidien de l'ingestion Open Charge Map"
  schedule_expression          = "cron(0 4 * * ? *)"
  schedule_expression_timezone = "Europe/Paris"

  flexible_time_window {
    mode                       = "FLEXIBLE"
    maximum_window_in_minutes  = 15
  }

  target {
    arn      = "arn:aws:lambda:eu-west-3:312957452752:function:electric-mobility-ingestion-openchargemap"
    role_arn = "arn:aws:iam::312957452752:role/service-role/Amazon_EventBridge_Scheduler_LAMBDA_709afe01ed"

    retry_policy {
      maximum_event_age_in_seconds = 86400
      maximum_retry_attempts       = 2
    }
  }
}

resource "aws_scheduler_schedule" "meteo_daily" {
  name                         = "electric-mobility-ingestion-meteo-daily"
  description                  = "Déclenchement quotidien de l'ingestion météo"
  schedule_expression          = "cron(0 4 * * ? *)"
  schedule_expression_timezone = "Europe/Paris"

  flexible_time_window {
    mode                       = "FLEXIBLE"
    maximum_window_in_minutes  = 15
  }

  target {
    arn      = "arn:aws:lambda:eu-west-3:312957452752:function:electric-mobility-ingestion-meteo"
    role_arn = "arn:aws:iam::312957452752:role/service-role/Amazon_EventBridge_Scheduler_LAMBDA_2206b54b8f"

    retry_policy {
      maximum_event_age_in_seconds = 86400
      maximum_retry_attempts       = 2
    }
  }
}
