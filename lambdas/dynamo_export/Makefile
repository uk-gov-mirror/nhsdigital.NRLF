.PHONY: *

FILE_TO_PACKAGE?=

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build
	@echo "✓ Clean complete"

build-lambda: clean
	$(eval LAMBDA_NAME := $(basename ${FILE_TO_PACKAGE}))
	@echo "Building $(LAMBDA_NAME) Lambda deployment package..."
	mkdir -p build

	# Copy the handler
	cp $(FILE_TO_PACKAGE) build/

	# Create the zip file in root dist
	mkdir -p ../../dist
	cd build && zip -r "../../../dist/${LAMBDA_NAME}.zip" . -x "*.pyc" -x "__pycache__/*" -x ".DS_Store"

	@echo "✓ Lambda package created: ../../dist/${LAMBDA_NAME}.zip"

build-dynamo-export-trigger:
	FILE_TO_PACKAGE=dynamo_export_trigger.py make build-lambda

build-dynamo-export-poll:
	FILE_TO_PACKAGE=dynamo_export_poll.py make build-lambda

build-ssm-put-param:
	FILE_TO_PACKAGE=ssm_put_param.py make build-lambda

build: build-dynamo-export-trigger build-dynamo-export-poll build-ssm-put-param
