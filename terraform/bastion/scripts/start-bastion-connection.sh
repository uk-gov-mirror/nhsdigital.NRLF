#!/bin/bash
# Script to start a bastion host connection using SSH
set -o errexit -o nounset -o pipefail

: "${AWS_ACCOUNT_ID:=""}"
: "${AWS_ROLE_NAME:=""}"

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <bastion-instance-id>"
  exit 1
fi
bastion_instance_id="$1"

CREDS=$(aws sts assume-role \
  --role-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:role/${AWS_ROLE_NAME}" \
  --role-session-name "bastion-connect" \
  --query 'Credentials' \
  --output json)

export AWS_ACCESS_KEY_ID=$(echo $CREDS | jq -r '.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo $CREDS | jq -r '.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo $CREDS | jq -r '.SessionToken')

exec aws ssm start-session --target "$bastion_instance_id"
