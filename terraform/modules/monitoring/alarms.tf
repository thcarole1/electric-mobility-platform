resource "aws_cloudwatch_metric_alarm" "openchargemap_errors" {
  alarm_name          = "electric-mobility-openchargemap-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods   = 1
  metric_name          = "Errors"
  namespace            = "AWS/Lambda"
  period               = 3600
  statistic            = "Sum"
  threshold            = 0
  alarm_description    = "Se déclenche si la Lambda d'ingestion Open Charge Map échoue au moins une fois"
  alarm_actions        = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.openchargemap_lambda_name
  }
}

resource "aws_cloudwatch_metric_alarm" "meteo_errors" {
  alarm_name          = "electric-mobility-meteo-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods   = 1
  metric_name          = "Errors"
  namespace            = "AWS/Lambda"
  period               = 3600
  statistic            = "Sum"
  threshold            = 0
  alarm_description    = "Se déclenche si la Lambda d'ingestion météo échoue au moins une fois"
  alarm_actions        = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = var.meteo_lambda_name
  }
}
