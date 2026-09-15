output "raw_bucket_name" {
  value = aws_s3_bucket.this["raw"].bucket
}

output "raw_bucket_arn" {
  value = aws_s3_bucket.this["raw"].arn
}
