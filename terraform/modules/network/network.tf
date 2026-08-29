resource "aws_vpc" "default" {
  cidr_block = "172.31.0.0/16"
}

resource "aws_subnet" "mwaa_private_1" {
  tags = {
    Name = "electric-mobility-mwaa-private-1"
  }
  vpc_id            = aws_vpc.default.id
  cidr_block        = "172.31.48.0/20"
  availability_zone = "eu-west-3a"
}

resource "aws_subnet" "mwaa_private_2" {
  tags = {
    Name = "electric-mobility-mwaa-private-2"
  }
  vpc_id            = aws_vpc.default.id
  cidr_block        = "172.31.64.0/20"
  availability_zone = "eu-west-3b"
}

resource "aws_security_group" "mwaa" {
  description = "Security group pour l environnement MWAA"
  name   = "electric-mobility-mwaa-sg"
  vpc_id = aws_vpc.default.id
}

resource "aws_vpc_endpoint" "s3" {
  tags = {
    Name = "electric-mobility-s3-endpoint"
  }
  vpc_id            = aws_vpc.default.id
  service_name      = "com.amazonaws.eu-west-3.s3"
  vpc_endpoint_type = "Gateway"
}

resource "aws_vpc_endpoint" "ecr_api" {
  tags = {
    Name = "electric-mobility-ecr-api-endpoint"
  }
  vpc_id             = aws_vpc.default.id
  service_name       = "com.amazonaws.eu-west-3.ecr.api"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.mwaa_private_1.id, aws_subnet.mwaa_private_2.id]
  security_group_ids = [aws_security_group.mwaa.id]
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  tags = {
    Name = "electric-mobility-ecr-dkr-endpoint"
  }
  vpc_id             = aws_vpc.default.id
  service_name       = "com.amazonaws.eu-west-3.ecr.dkr"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.mwaa_private_1.id, aws_subnet.mwaa_private_2.id]
  security_group_ids = [aws_security_group.mwaa.id]
}

resource "aws_vpc_endpoint" "logs" {
  tags = {
    Name = "electric-mobility-logs-endpoint"
  }
  vpc_id             = aws_vpc.default.id
  service_name       = "com.amazonaws.eu-west-3.logs"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.mwaa_private_1.id, aws_subnet.mwaa_private_2.id]
  security_group_ids = [aws_security_group.mwaa.id]
}

resource "aws_vpc_endpoint" "kms" {
  tags = {
    Name = "electric-mobility-kms-endpoint"
  }
  vpc_id             = aws_vpc.default.id
  service_name       = "com.amazonaws.eu-west-3.kms"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.mwaa_private_1.id, aws_subnet.mwaa_private_2.id]
  security_group_ids = [aws_security_group.mwaa.id]
}

resource "aws_vpc_endpoint" "sqs" {
  tags = {
    Name = "electric-mobility-sqs-endpoint"
  }
  vpc_id             = aws_vpc.default.id
  service_name       = "com.amazonaws.eu-west-3.sqs"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.mwaa_private_1.id, aws_subnet.mwaa_private_2.id]
  security_group_ids = [aws_security_group.mwaa.id]
}

resource "aws_vpc_endpoint" "monitoring" {
  tags = {
    Name = "electric-mobility-monitoring-endpoint"
  }
  vpc_id             = aws_vpc.default.id
  service_name       = "com.amazonaws.eu-west-3.monitoring"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.mwaa_private_1.id, aws_subnet.mwaa_private_2.id]
  security_group_ids = [aws_security_group.mwaa.id]
}

resource "aws_vpc_endpoint" "airflow_api" {
  tags = {
    Name = "electric-mobility-airflow-api-endpoint"
  }
  vpc_id             = aws_vpc.default.id
  service_name       = "com.amazonaws.eu-west-3.airflow.api"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.mwaa_private_1.id, aws_subnet.mwaa_private_2.id]
  security_group_ids = [aws_security_group.mwaa.id]
}

resource "aws_vpc_endpoint" "airflow_env" {
  tags = {
    Name = "electric-mobility-airflow-env-endpoint"
  }
  vpc_id             = aws_vpc.default.id
  service_name       = "com.amazonaws.eu-west-3.airflow.env"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.mwaa_private_1.id, aws_subnet.mwaa_private_2.id]
  security_group_ids = [aws_security_group.mwaa.id]
}

resource "aws_vpc_endpoint" "airflow_ops" {
  tags = {
    Name = "electric-mobility-airflow-ops-endpoint"
  }
  vpc_id             = aws_vpc.default.id
  service_name       = "com.amazonaws.eu-west-3.airflow.ops"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [aws_subnet.mwaa_private_1.id, aws_subnet.mwaa_private_2.id]
  security_group_ids = [aws_security_group.mwaa.id]
}

resource "aws_route_table" "mwaa_private" {
  tags = {
    Name = "electric-mobility-mwaa-private-rt"
  }
  vpc_id = aws_vpc.default.id
}
# Fichier réseau du socle MWAA
