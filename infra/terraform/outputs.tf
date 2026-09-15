output "raw_contracts_bucket" {
  value = module.storage.raw_bucket_name
}

output "db_cluster_endpoint" {
  value = module.database.cluster_endpoint
}

output "db_secret_arn" {
  value = module.database.secret_arn
}

output "state_machine_arn" {
  value = module.pipeline.state_machine_arn
}

output "api_endpoint" {
  value = module.api.api_endpoint
}

output "cognito_user_pool_id" {
  value = module.auth.user_pool_id
}

output "cognito_app_client_id" {
  value = module.auth.app_client_id
}

output "frontend_url" {
  value = module.frontend.url
}

output "frontend_bucket" {
  value = module.frontend.bucket_name
}

output "frontend_cloudfront_distribution_id" {
  value = module.frontend.cloudfront_distribution_id
}

output "bastion_instance_id" {
  value = var.enable_bastion ? module.bastion[0].instance_id : null
}
