
ENV ?= dev
TF_ARGS ?=
ENV_ACCOUNT_NAME ?= $(shell ../../scripts/get-account-name-for-env.sh $(ENV))
ENV_ACCOUNT_ID ?= $(shell aws secretsmanager get-secret-value --secret-id nhsd-nrlf--mgmt--$(ENV_ACCOUNT_NAME)-account-id --query SecretString --output text)
BASTION_VPC_NAME ?= nhsd-nrlf--$(ENV_ACCOUNT_NAME)-vpc
BASTION_SUBNET_NAME ?= nhsd-nrlf--$(ENV_ACCOUNT_NAME)-privsubnet
POINTERS_TABLE_NAME ?= nhsd-nrlf--$(ENV)-pointers-table
S3_METADATA_BUCKET_NAME ?= nhsd-nrlf--$(ENV)-metadata

export ENV ENV_ACCOUNT_NAME POINTERS_TABLE_NAME

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo
	@echo "where [target] can be:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

plan-ro: ## Plan the Terraform changes for a bastion that can perform read-only operations
	terraform plan \
		-var assume_account=$(ENV_ACCOUNT_ID) \
		-var assume_role=terraform \
		-var vpc_name=$(BASTION_VPC_NAME) \
		-var subnet_name=$(BASTION_SUBNET_NAME) \
		-var dynamodb_table_name=$(POINTERS_TABLE_NAME) \
		-var s3_metadata_bucket_name=$(S3_METADATA_BUCKET_NAME) \
		$(TF_ARGS) \
		-out=./bastion.tfplan

plan-rw: ## Plan the Terraform changes for a bastion that can perform write operations
	terraform plan \
		-var assume_account=$(ENV_ACCOUNT_ID) \
		-var assume_role=terraform \
		-var vpc_name=$(BASTION_VPC_NAME) \
		-var subnet_name=$(BASTION_SUBNET_NAME) \
		-var dynamodb_table_name=$(POINTERS_TABLE_NAME) \
		-var allow_dynamodb_table_write=true \
		-var s3_metadata_bucket_name=$(S3_METADATA_BUCKET_NAME) \
		$(TF_ARGS) \
		-out=./bastion.tfplan

destroy: ## Destroy the bastion
	terraform destroy \
		-var assume_account=$(ENV_ACCOUNT_ID) \
		-var assume_role=terraform \
		-var vpc_name=$(BASTION_VPC_NAME) \
		-var subnet_name=$(BASTION_SUBNET_NAME) \
		-var dynamodb_table_name=$(POINTERS_TABLE_NAME) \
		-var s3_metadata_bucket_name=$(S3_METADATA_BUCKET_NAME) \
		$(TF_ARGS)

ssh-connection: ## Connect to the bastion via SSH
	@echo "Connecting to bastion via SSM connect...."
	AWS_ACCOUNT_ID=$(ENV_ACCOUNT_ID) \
	AWS_ROLE_NAME=terraform \
		./scripts/start-bastion-connection.sh $(shell terraform output -raw instance_id)
