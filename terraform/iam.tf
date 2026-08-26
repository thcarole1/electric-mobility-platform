resource "aws_iam_user" "pipeline_service_account" {
  name = "electric-mobility-pipeline"
}

resource "aws_iam_user" "admin_account" {
  name = "emp-admin"
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "electric-mobility-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role" "glue_crawler_role" {
  name = "electric-mobility-glue-crawler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "s3_readwrite_policy" {
  name = "electric-mobility-s3-readwrite"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::electric-mobility-platform-thierry/*"
      }
    ]
  })
}

resource "aws_iam_policy" "s3_readonly_processed_policy" {
  name = "electric-mobility-s3-readonly-processed"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject"]
        Resource = "arn:aws:s3:::electric-mobility-platform-thierry/processed/*"
      },
      {
        Effect = "Allow"
        Action = "s3:ListBucket"
        Resource = "arn:aws:s3:::electric-mobility-platform-thierry"
      }
    ]
  })
}
