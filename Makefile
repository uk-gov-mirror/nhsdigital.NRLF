.EXPORT_ALL_VARIABLES:
.NOTPARALLEL:
.PHONY: *

MAKEFLAGS := --no-print-directory
SHELL := /bin/bash

DIST_PATH ?= ./dist
TEST_ARGS ?= --cov --cov-report=term-missing --cov-report=xml:$(DIST_PATH)/test-coverage.xml
SMOKE_TEST_ARGS ?=
FEATURE_TEST_ARGS ?= ./tests/features --format progress2
TF_WORKSPACE_NAME ?= $(shell terraform -chdir=terraform/infrastructure workspace show)
ENV ?= dev
ACCOUNT ?= dev
APP_ALIAS ?= default
HOST ?= $(TF_WORKSPACE_NAME).api.record-locator.$(ENV).national.nhs.uk
ENV_TYPE ?= $(ENV)
PERFTEST_TABLE_NAME ?= perftest
PERFTEST_HOST ?= perftest-1.perftest.record-locator.national.nhs.uk
PERFTEST_PATIENTS_WITH_POINTERS ?= 0
PERFTEST_POINTERS_PER_PATIENT ?= 0
PERFTEST_TYPE_DIST_PROFILE ?= default
PERFTEST_CUSTODIAN_DIST_PROFILE ?= default
PERFTEST_TOKEN_REFRESH_PORT ?= 8765

export PATH := $(PATH):$(PWD)/.venv/bin
export USE_SHARED_RESOURCES := $(shell poetry run python scripts/are_resources_shared_for_stack.py $(TF_WORKSPACE_NAME))

default: build

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo
	@echo "where [target] can be:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

asdf-install: ## Install the required tools via ASDF
	@cat .tool-versions | while read tool_version; do \
		tool="$${tool_version% *}"; \
		asdf plugin add "$${tool}"; \
	done
	asdf install

configure: asdf-install check-warn ## Configure this project repo, including install dependencies
	cp scripts/commit-msg.py .git/hooks/prepare-commit-msg && chmod ug+x .git/hooks/*
	poetry install
	poetry run pre-commit install

check: ## Check the build environment is setup correctly
	@./scripts/check-build-environment.sh

check-warn:
	@SHOULD_WARN_ONLY=true ./scripts/check-build-environment.sh

check-deploy: ## check the deploy environment is setup correctly
	@./scripts/check-deploy-environment.sh

check-deploy-warn:
	@SHOULD_WARN_ONLY=true ./scripts/check-deploy-environment.sh

build: check-warn build-api-packages build-layers build-dependency-layer ## Build the project

build-dependency-layer:
	@echo "Building Lambda dependency layer"
	@mkdir -p $(DIST_PATH)
	./scripts/build-lambda-dependency-layer.sh $(DIST_PATH)

build-layers: ./layer/*
	@echo "Building Lambda layers"
	@mkdir -p $(DIST_PATH)
	for layer in $^; do \
		[ ! -d "$$layer" ] && continue; \
		./scripts/build-lambda-layer.sh $${layer} $(DIST_PATH); \
	done

build-api-packages: ./api/consumer/* ./api/producer/*
	@echo "Building API packages"
	@mkdir -p $(DIST_PATH)
	for api in $^; do \
		[ ! -d "$$api" ] && continue; \
		./scripts/build-lambda-package.sh $${api} $(DIST_PATH); \
	done

build-ci-image: ## Build the CI image
	@echo "Building the CI image"
	docker build \
		-t nhsd-nrlf-ci-build:latest \
		-f Dockerfile.ci-build

ecr-login: ## Login to NRLF ECR repo
	@echo "Logging into ECR"
	$(eval AWS_REGION := $(shell aws configure get region))
	$(eval AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity | jq -r .Account))
	@aws ecr get-login-password --region "$(AWS_REGION)" \
		| docker login --username AWS --password-stdin \
			$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

publish-ci-image: ## Publish the CI image
	@echo "Publishing the CI image"
	$(eval AWS_REGION := $(shell aws configure get region))
	$(eval AWS_ACCOUNT_ID := $(shell aws sts get-caller-identity | jq -r .Account))
	@docker tag nhsd-nrlf-ci-build:latest \
		$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/nhsd-nrlf-ci-build:latest
	@docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/nhsd-nrlf-ci-build:latest

test: check-warn ## Run the unit tests
	@echo "Running unit tests"
	PYTHONPATH=. poetry run pytest --ignore tests/smoke $(TEST_ARGS)

test-features-integration: check-warn ## Run the BDD feature tests in the integration environment
	@echo "Running feature tests in the integration environment ${TF_WORKSPACE_NAME}"
	behave --define="integration_test=true" \
		--define="env=$(TF_WORKSPACE_NAME)" \
		--define="account_name=$(ENV)" \
		--define="use_shared_resources=${USE_SHARED_RESOURCES}" \
		$(FEATURE_TEST_ARGS)

integration-test-with-custom_tag:
	@echo "Running feature tests in the integration environment ${TF_WORKSPACE_NAME}"
	behave --define="integration_test=true" --tags=@custom_tag \
		--define="env=$(TF_WORKSPACE_NAME)" \
		--define="account_name=$(ENV)" \
		--define="use_shared_resources=${USE_SHARED_RESOURCES}" \
		$(FEATURE_TEST_ARGS)

test-features-integration-report: check-warn ## Run the BDD feature tests in the integration environment and generate allure report therafter
	@echo "Cleaning previous Allure results and reports"
	rm -rf ./allure-results
	rm -rf ./allure-report
	@echo "Running feature tests in the integration environment"
	behave --define="integration_test=true" \
		--define="env=$(TF_WORKSPACE_NAME)" \
		--define="account_name=$(ENV)" \
		--define="use_shared_resources=${USE_SHARED_RESOURCES}" \
		$(FEATURE_TEST_ARGS)
	@echo "Generating Allure report"
	allure generate ./allure-results -o ./allure-report --clean
	@echo "Opening Allure report"
	allure open ./allure-report

test-smoke-internal: check-warn ## Run the smoke tests against the internal environment
	@echo "Running smoke tests against the internal environment ${TF_WORKSPACE_NAME}"
	TEST_ENVIRONMENT_NAME=$(ENV) \
	TEST_STACK_NAME=$(TF_WORKSPACE_NAME) \
	TEST_STACK_DOMAIN=$(shell terraform -chdir=terraform/infrastructure output -raw domain 2>/dev/null) \
	TEST_CONNECT_MODE="internal" \
		pytest ./tests/smoke/scenarios/* $(SMOKE_TEST_ARGS)

test-smoke-public: check-warn ## Run the smoke tests for the external access points
	@echo "Running smoke tests for the public endpoints ${ENV}"
	TEST_ENVIRONMENT_NAME=$(ENV) \
	TEST_STACK_NAME=$(TF_WORKSPACE_NAME) \
	TEST_CONNECT_MODE="public" \
		pytest ./tests/smoke/scenarios/* $(SMOKE_TEST_ARGS)

test-performance-prepare:
	mkdir -p $(DIST_PATH)
	PYTHONPATH=. poetry run python tests/performance/environment.py setup $(TF_WORKSPACE_NAME)

test-performance-internal: check-warn test-performance-baseline-internal test-performance-stress-internal ## Run the performance tests against the internal access points

test-performance-baseline-internal: check-warn ## Run the performance baseline tests for the internal access points
	@echo "Running internal consumer performance baseline test"
	TEST_CONNECT_MODE=internal \
	TEST_STACK_DOMAIN=$(shell terraform -chdir=terraform/infrastructure output -raw domain 2>/dev/null) \
		k6 run --out csv=$(DIST_PATH)/consumer-baseline.csv tests/performance/consumer/baseline.js -e HOST=$(HOST) -e ENV_TYPE=$(ENV_TYPE)

test-performance-baseline-public: check-warn ## Run the baseline performance tests for the external access points
	@echo "Fetching public mode configuration and bearer token..."
	@CONFIG_FILE=$$(mktemp /tmp/perf_config_XXXXXX); \
	trap "rm -f $$CONFIG_FILE" EXIT; \
	PYTHONPATH=. python3 tests/performance/get_test_config.py $(ENV_TYPE) 2>&1 | tail -n 1 > $$CONFIG_FILE; \
	PUBLIC_BASE_URL=$$(jq -r '.public_base_url' $$CONFIG_FILE); \
	echo "Running consumer performance baseline test against the external access points"; \
	TEST_CONNECT_MODE=public \
	TEST_PUBLIC_BASE_URL=$$PUBLIC_BASE_URL \
	TEST_CONFIG_FILE=$$CONFIG_FILE \
		k6 run --out csv=$(DIST_PATH)/consumer-baseline-public.csv tests/performance/consumer/baseline.js -e ENV_TYPE=$(ENV_TYPE)

test-performance-stress-internal: ## Run the performance stress tests for the internal access points
	@echo "Running internal consumer performance stress test"
	k6 run --out csv=$(DIST_PATH)/consumer-stress.csv tests/performance/consumer/stress.js -e HOST=$(HOST) -e ENV_TYPE=$(ENV_TYPE)

test-performance-stress-public: check-warn ## Run the stress performance tests for the external access points
	@echo "Fetching public mode configuration and bearer token..."
	@CONFIG_FILE=$$(mktemp /tmp/perf_config_XXXXXX); \
	trap "rm -f $$CONFIG_FILE" EXIT; \
	PYTHONPATH=. python3 tests/performance/get_test_config.py $(ENV_TYPE) 2>&1 | tail -n 1 > $$CONFIG_FILE; \
	PUBLIC_BASE_URL=$$(jq -r '.public_base_url' $$CONFIG_FILE); \
	echo "Running consumer performance stress test against the external access points"; \
	TEST_CONNECT_MODE=public \
	TEST_PUBLIC_BASE_URL=$$PUBLIC_BASE_URL \
	TEST_CONFIG_FILE=$$CONFIG_FILE \
		k6 run --out csv=$(DIST_PATH)/consumer-stress-public.csv tests/performance/consumer/stress.js -e ENV_TYPE=$(ENV_TYPE)

test-performance-soak-internal:
	@echo "Running internal consumer performance soak test"
	k6 run --out csv=$(DIST_PATH)/consumer-soak.csv tests/performance/consumer/soak.js -e HOST=$(HOST) -e ENV_TYPE=$(ENV_TYPE)

test-performance-soak-public: check-warn ## Run the soak performance tests for the external access points
	@echo "Fetching public mode configuration and bearer token..."
	@CONFIG_FILE=$$(mktemp /tmp/perf_config_XXXXXX); \
	trap "rm -f $$CONFIG_FILE" EXIT; \
	PYTHONPATH=. python3 tests/performance/get_test_config.py $(ENV_TYPE) 2>&1 | tail -n 1 > $$CONFIG_FILE; \
	PUBLIC_BASE_URL=$$(jq -r '.public_base_url' $$CONFIG_FILE); \
	echo "Running consumer performance soak test against the external access points"; \
	TEST_CONNECT_MODE=public \
	TEST_PUBLIC_BASE_URL=$$PUBLIC_BASE_URL \
	TEST_CONFIG_FILE=$$CONFIG_FILE \
		k6 run --out csv=$(DIST_PATH)/consumer-soak-public.csv tests/performance/consumer/soak.js -e ENV_TYPE=$(ENV_TYPE)

test-performance-output: ## Process outputs from the performance tests
	@echo "Processing performance test outputs"
	poetry run python tests/performance/process_results.py baseline $(DIST_PATH)/consumer-baseline.csv
	poetry run python tests/performance/process_results.py stress $(DIST_PATH)/consumer-stress.csv

test-performance-cleanup:
	PYTHONPATH=. poetry run python tests/performance/environment.py cleanup $(TF_WORKSPACE_NAME)

lint: check-warn ## Lint the project
	SKIP="no-commit-to-branch" pre-commit run --all-files

clean: ## Remove all generated and temporary files
	[ -n "$(DIST_PATH)" ] && \
		rm -rf $(DIST_PATH)/*.zip && \
		rmdir $(DIST_PATH) 2>/dev/null || true

get-access-token: check-warn ## Get an access token for an environment
	@poetry run python tests/utilities/get_access_token.py $(ENV) $(APP_ALIAS)

get-s3-perms: check-warn ## Get s3 permissions for an environment
	poetry run python scripts/get_s3_permissions.py ${USE_SHARED_RESOURCES} $(ENV) $(TF_WORKSPACE_NAME) "$(DIST_PATH)"
	@echo "Creating new Lambda NRLF permissions layer zip"
	./scripts/add-perms-to-lambda.sh $(DIST_PATH)

set-smoketest-perms: check-warn ## Set the permissions for the smoke tests
	@echo "Setting permissions for smoke tests of env=$(ENV) stack=$(TF_WORKSPACE_NAME)...."
	poetry run python scripts/set_smoketest_permissions.py $(ENV) $(TF_WORKSPACE_NAME) $(ENV)

truststore-build-all: check-warn ## Build all truststore resources
	@./scripts/truststore.sh build-all

truststore-build-ca: check-warn ## Build a CA (Certificate Authority)
	@./scripts/truststore.sh build-ca "$(CA_NAME)" "$(CA_SUBJECT)"

truststore-build-cert: check-warn ## Build a certificate
	@./scripts/truststore.sh build-cert "$(CA_NAME)" "$(CERT_NAME)" "$(CERT_SUBJECT)"

truststore-pull-all-for-account: check-warn ## Pull all certificates for each environment in a given account
	@./scripts/truststore.sh pull-all-for-account "$(ACCOUNT)"

truststore-pull-all: check-warn ## Pull all certificates
	@./scripts/truststore.sh pull-all "$(ENV)"

truststore-pull-server: check-warn ## Pull a server certificate
	@./scripts/truststore.sh pull-server "$(ENV)"

truststore-pull-client: check-warn ## Pull a client certificate
	@./scripts/truststore.sh pull-client "$(ENV)"

truststore-pull-ca: check-warn ## Pull a CA certificate
	@./scripts/truststore.sh pull-ca "$(ENV)"

swagger-merge: check-warn ## Generate Swagger Documentation
	@./scripts/swagger.sh merge "$(TYPE)"

generate-models: check-warn ## Generate Pydantic Models
	@echo "Generating producer models"
	mkdir -p ./layer/nrlf/producer/fhir/r4
	poetry run datamodel-codegen \
		--input ./api/producer/swagger.yaml \
		--input-file-type openapi \
		--output ./layer/nrlf/producer/fhir/r4/model.py \
		--output-model-type "pydantic_v2.BaseModel" \
		--base-class nrlf.core.parent_model.Parent
	poetry run datamodel-codegen \
		--strict-types {str,bytes,int,float,bool} \
		--input ./api/producer/swagger.yaml \
		--input-file-type openapi \
		--output ./layer/nrlf/producer/fhir/r4/strict_model.py \
		--base-class nrlf.core.parent_model.Parent \
		--output-model-type "pydantic_v2.BaseModel"


	@echo "Generating consumer model"
	mkdir -p ./layer/nrlf/consumer/fhir/r4
	poetry run datamodel-codegen \
		--input ./api/consumer/swagger.yaml \
		--input-file-type openapi \
		--output ./layer/nrlf/consumer/fhir/r4/model.py \
		--base-class nrlf.core.parent_model.Parent \
		--output-model-type "pydantic_v2.BaseModel"


perftest-generate-permissions: ## Generate perftest permissions and add to nrlf_permissions
	@echo "Generating permissions for performance tests with DIST_PATH=$(DIST_PATH)"
	PYTHONPATH=. poetry run python tests/performance/producer/generate_permissions.py --output_dir="$(DIST_PATH)/nrlf_permissions/K6PerformanceTest"

perftest-seed-tables:	## Seed tables and upload generated perftest input files to s3
	@echo "Seeding performance test pointer tables with ENV=$(ENV) and PERFTEST_TABLE_NAME=$(PERFTEST_TABLE_NAME) and PERFTEST_PATIENTS_WITH_POINTERS=$(PERFTEST_PATIENTS_WITH_POINTERS) and PERFTEST_POINTERS_PER_PATIENT=$(PERFTEST_POINTERS_PER_PATIENT) and PERFTEST_TYPE_DIST_PROFILE=$(PERFTEST_TYPE_DIST_PROFILE) and PERFTEST_CUSTODIAN_DIST_PROFILE=$(PERFTEST_CUSTODIAN_DIST_PROFILE)"
	rm -rf "${DIST_PATH}/nft"
	mkdir -p "${DIST_PATH}/nft"
	PYTHONPATH=. poetry run python ./scripts/seed_nft_tables.py --table_name=$(PERFTEST_TABLE_NAME) --patients_with_pointers=$(PERFTEST_PATIENTS_WITH_POINTERS) --pointers_per_patient=$(PERFTEST_POINTERS_PER_PATIENT) --type_dist_profile=$(PERFTEST_TYPE_DIST_PROFILE) --custodian_dist_profile=$(PERFTEST_CUSTODIAN_DIST_PROFILE)
	zip -r "${DIST_PATH}/pointer_extract-${PERFTEST_TABLE_NAME}.zip" "${DIST_PATH}/nft"
	aws s3 cp "${DIST_PATH}/pointer_extract-${PERFTEST_TABLE_NAME}.zip" "s3://nhsd-nrlf--${ENV}-metadata/performance/seed-pointers-extract-${PERFTEST_TABLE_NAME}.zip"

perftest-prepare:	## Prepare input files for producer & consumer perf tests
	@echo "Preparing performance tests with ENV=$(ENV) and PERFTEST_TABLE_NAME=$(PERFTEST_TABLE_NAME) and DIST_PATH=$(DIST_PATH)"
	rm -rf "${DIST_PATH}/nft"
	mkdir -p "${DIST_PATH}/nft"
	aws s3 cp "s3://nhsd-nrlf--${ENV}-metadata/performance/seed-pointers-extract-${PERFTEST_TABLE_NAME}.zip" "${DIST_PATH}/pointer_extract-${PERFTEST_TABLE_NAME}.zip"
	unzip "${DIST_PATH}/pointer_extract-${PERFTEST_TABLE_NAME}.zip"
	PYTHONPATH=. poetry run python ./tests/performance/generate_producer_distributions.py

perftest-producer-internal:	## Run producer perf tests
	@echo "Running producer performance tests with HOST=$(PERFTEST_HOST) and ENV_TYPE=$(ENV_TYPE) and DIST_PATH=$(DIST_PATH)"
	k6 run tests/performance/producer/perftest.js --summary-mode=full --out json=$(DIST_PATH)/producer-internal-$$(date +%Y%m%d%H%M%S).json -e HOST=$(PERFTEST_HOST) -e ENV_TYPE=$(ENV_TYPE) -e DIST_PATH=$(DIST_PATH)

perftest-producer-public: check-warn ## Run the producer perftests for the external access points
	@echo "Starting token refresher in background with ENV=$(ENV) PERFTEST_TOKEN_REFRESH_PORT=$(PERFTEST_TOKEN_REFRESH_PORT)"
	ENV=$(ENV) TOKEN_REFRESH_PORT=$(PERFTEST_TOKEN_REFRESH_PORT) PYTHONPATH=. poetry run python ./tests/performance/token_refresher.py &
	trap "kill $$(lsof -t -i :$(PERFTEST_TOKEN_REFRESH_PORT)) 2>/dev/null" EXIT
	@echo "Fetching public mode configuration..."
	@CONFIG_FILE=$$(mktemp /tmp/perf_config_XXXXXX); \
	trap "rm -f $$CONFIG_FILE" EXIT; \
	PYTHONPATH=. poetry run python tests/performance/get_test_config.py $(ENV_TYPE) 2>&1 | tail -n 1 > $$CONFIG_FILE; \
	PUBLIC_BASE_URL=$$(jq -r '.public_base_url' $$CONFIG_FILE); \
	echo "Running public producer perftests with ENV_TYPE=$(ENV_TYPE) and DIST_PATH=$(DIST_PATH)"; \
	TEST_CONNECT_MODE=public \
	TEST_PUBLIC_BASE_URL=$$PUBLIC_BASE_URL \
	TEST_CONFIG_FILE=$$CONFIG_FILE \
		k6 run tests/performance/producer/perftest.js --summary-mode=full --out json=$(DIST_PATH)/producer-public-$$(date +%Y%m%d%H%M%S).json -e ENV_TYPE=$(ENV_TYPE) -e DIST_PATH=$(DIST_PATH)
	kill $$(lsof -t -i :$(PERFTEST_TOKEN_REFRESH_PORT))

perftest-consumer-internal:
	@echo "Running consumer performance tests with HOST=$(PERFTEST_HOST) and ENV_TYPE=$(ENV_TYPE) and DIST_PATH=$(DIST_PATH)"
	k6 run tests/performance/consumer/perftest.js --summary-mode=full --out json=$(DIST_PATH)/consumer-internal-$$(date +%Y%m%d%H%M%S).json -e HOST=$(PERFTEST_HOST) -e ENV_TYPE=$(ENV_TYPE) -e DIST_PATH=$(DIST_PATH)

perftest-consumer-public: check-warn ## Run the consumer perftests for the external access points
	@echo "Starting token refresher in background with ENV=$(ENV) PERFTEST_TOKEN_REFRESH_PORT=$(PERFTEST_TOKEN_REFRESH_PORT)"
	ENV=$(ENV) TOKEN_REFRESH_PORT=$(PERFTEST_TOKEN_REFRESH_PORT) PYTHONPATH=. poetry run python ./tests/performance/token_refresher.py &
	trap "kill $$(lsof -t -i :$(PERFTEST_TOKEN_REFRESH_PORT)) 2>/dev/null" EXIT
	@echo "Fetching public mode configuration..."
	@CONFIG_FILE=$$(mktemp /tmp/perf_config_XXXXXX); \
	trap "rm -f $$CONFIG_FILE" EXIT; \
	PYTHONPATH=. poetry run python tests/performance/get_test_config.py $(ENV_TYPE) 2>&1 | tail -n 1 > $$CONFIG_FILE; \
	PUBLIC_BASE_URL=$$(jq -r '.public_base_url' $$CONFIG_FILE); \
	echo "Running public consumer perftests with ENV_TYPE=$(ENV_TYPE) and DIST_PATH=$(DIST_PATH)"; \
	TEST_CONNECT_MODE=public \
	TEST_PUBLIC_BASE_URL=$$PUBLIC_BASE_URL \
	TEST_CONFIG_FILE=$$CONFIG_FILE \
		k6 run tests/performance/consumer/perftest.js --summary-mode=full --out json=$(DIST_PATH)/consumer-public-$$(date +%Y%m%d%H%M%S).json -e ENV_TYPE=$(ENV_TYPE) -e DIST_PATH=$(DIST_PATH)
	kill $$(lsof -t -i :$(PERFTEST_TOKEN_REFRESH_PORT))

perftest-generate-pointer-table-extract:
	@echo "Generating pointer table extract with PERFTEST_TABLE_NAME=$(PERFTEST_TABLE_NAME) and ENV=$(ENV) and DIST_PATH=$(DIST_PATH)"
	rm -rf "${DIST_PATH}/nft"
	mkdir -p "${DIST_PATH}/nft"
	PYTHONPATH=. poetry run python tests/performance/perftest_environment.py generate_pointer_table_extract --output_dir="${DIST_PATH}/nft" --extract-size=2000000
	./scripts/get-current-info.sh > "${DIST_PATH}/nft/info.json"
	zip -r "${DIST_PATH}/pointer_extract-${PERFTEST_TABLE_NAME}.zip" "${DIST_PATH}/nft"
	aws s3 cp "${DIST_PATH}/pointer_extract-${PERFTEST_TABLE_NAME}.zip" "s3://nhsd-nrlf--${ENV}-metadata/performance/seed-pointers-extract-${PERFTEST_TABLE_NAME}.zip"
