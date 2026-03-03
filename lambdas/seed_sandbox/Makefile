.PHONY: build clean

build: clean
	@echo "Building Lambda deployment package..."
	mkdir -p build

	# Copy the handler
	cp index.py build/

	# Copy the required scripts
	mkdir -p build/scripts
	cp ../../scripts/delete_all_table_items.py build/scripts/
	cp ../../scripts/seed_sandbox_table.py build/scripts/
	cp ../../scripts/seed_utils.py build/scripts/

	# Copy the pointer template data
	mkdir -p build/tests/data/samples
	cp -r ../../tests/data/samples/*.json build/tests/data/samples/

	# Create the zip file in root dist
	mkdir -p ../../dist
	cd build && zip -r ../../../dist/seed_sandbox.zip . -x "*.pyc" -x "__pycache__/*" -x ".DS_Store"

	@echo "✓ Lambda package created: ../../dist/seed_sandbox.zip"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build
	@echo "✓ Clean complete"
