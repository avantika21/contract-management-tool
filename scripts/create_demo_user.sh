#!/usr/bin/env bash
# Creates a Cognito user for the demo frontend with a permanent password
# (skips the forced first-login password change, which the SPA doesn't
# implement a flow for). Run after `terraform apply`.
#
# Usage: ./scripts/create_demo_user.sh <email> <password>
set -euo pipefail

EMAIL="${1:?Usage: $0 <email> <password>}"
PASSWORD="${2:?Usage: $0 <email> <password>}"

cd "$(dirname "${BASH_SOURCE[0]}")/../infra/terraform"
USER_POOL_ID="$(terraform output -raw cognito_user_pool_id)"
REGION="${AWS_REGION:-eu-west-2}"

aws cognito-idp admin-create-user \
  --region "$REGION" \
  --user-pool-id "$USER_POOL_ID" \
  --username "$EMAIL" \
  --user-attributes Name=email,Value="$EMAIL" Name=email_verified,Value=true \
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password \
  --region "$REGION" \
  --user-pool-id "$USER_POOL_ID" \
  --username "$EMAIL" \
  --password "$PASSWORD" \
  --permanent

echo "Demo user $EMAIL created in pool $USER_POOL_ID."
