resource "aws_lambda_function" "openchargemap_ingestion" {
  function_name = "electric-mobility-ingestion-openchargemap"
  role           = "arn:aws:iam::312957452752:role/electric-mobility-lambda-role"
  handler        = "lambda_function.lambda_handler"
  runtime        = "python3.12"
  filename       = "placeholder.zip"
  timeout        = 30
  layers         = ["arn:aws:lambda:eu-west-3:312957452752:layer:electric-mobility-ingestion-deps:1"]

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  environment {
    variables = {
      OCM_API_KEY = var.ocm_api_key
    }
  }
}

resource "aws_lambda_function" "meteo_ingestion" {
  function_name = "electric-mobility-ingestion-meteo"
  role           = "arn:aws:iam::312957452752:role/electric-mobility-lambda-role"
  handler        = "lambda_function.lambda_handler"
  runtime        = "python3.12"
  filename       = "placeholder.zip"
  timeout        = 30
  layers         = ["arn:aws:lambda:eu-west-3:312957452752:layer:electric-mobility-ingestion-deps:1"]

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}
