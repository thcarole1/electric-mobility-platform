module "data_lake" {
  glue_crawler_role_name = module.iam.glue_crawler_role_name
  source = "./modules/data-lake"
}

module "iam" {
  source = "./modules/iam"
}

module "network" {
  source = "./modules/network"
}

module "ingestion" {
  source           = "./modules/ingestion"
  lambda_role_arn  = module.iam.lambda_role_arn
  ocm_api_key      = var.ocm_api_key
}
