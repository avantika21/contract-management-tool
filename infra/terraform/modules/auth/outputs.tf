output "user_pool_id" {
  value = aws_cognito_user_pool.procurement.id
}

output "user_pool_arn" {
  value = aws_cognito_user_pool.procurement.arn
}

output "app_client_id" {
  value = aws_cognito_user_pool_client.app.id
}
