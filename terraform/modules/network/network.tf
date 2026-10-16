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
  name        = "electric-mobility-mwaa-sg"
  vpc_id      = aws_vpc.default.id
}

resource "aws_vpc_endpoint" "s3" {
  tags = {
    Name = "electric-mobility-s3-endpoint"
  }
  vpc_id            = aws_vpc.default.id
  service_name      = "com.amazonaws.eu-west-3.s3"
  vpc_endpoint_type = "Gateway"
}

resource "aws_route_table" "mwaa_private" {
  tags = {
    Name = "electric-mobility-mwaa-private-rt"
  }
  vpc_id = aws_vpc.default.id
}
# Fichier réseau du socle MWAA
