resource "aws_glue_catalog_database" "electric_mobility_catalog" {
  name = "electric_mobility_catalog"
}

resource "aws_glue_crawler" "electric_mobility_crawler" {
  name          = "electric-mobility-crawler"
  role          = "electric-mobility-glue-crawler-role"
  database_name = "electric_mobility_catalog"

  s3_target {
    path = "s3://electric-mobility-platform-thierry/processed/"
  }
}
