resource "aws_glue_catalog_database" "electric_mobility_catalog" {
  name = "electric_mobility_catalog"
}

resource "aws_glue_crawler" "electric_mobility_crawler" {
  name          = "electric-mobility-crawler"
  role          = var.glue_crawler_role_name
  database_name = "electric_mobility_catalog"

  s3_target {
    path = "s3://electric-mobility-platform-thierry/processed/"
  }
}
