output "state_machine_arn" {
  value = aws_sfn_state_machine.pipeline.arn
}

output "lambda_function_names" {
  value = { for k, f in aws_lambda_function.this : k => f.function_name }
}

output "dependencies_layer_arn" {
  value = aws_lambda_layer_version.dependencies.arn
}
