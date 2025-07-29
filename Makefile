.PHONY: test test-unit test-integration test-e2e test-contract test-cov install-dev clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-e2e       - Run end-to-end tests only"
	@echo "  test-contract  - Run contract tests only"
	@echo "  test-cov       - Run tests with coverage report"
	@echo "  install-dev    - Install package in development mode"
	@echo "  clean          - Clean build artifacts"
	@echo "  help           - Show this help message"

# Install development dependencies
install-dev:
	pip install -e .
	pip install -r tests/requirements.txt

# Run all tests
test:
	pytest tests/

# Run unit tests only
test-unit:
	pytest tests/unit/ -v

# Run integration tests only
test-integration:
	pytest tests/integration/ -v

# Run end-to-end tests only
test-e2e:
	pytest tests/e2e/ -v

# Run contract tests only
test-contract:
	pytest tests/contract/ -v

# Run tests with coverage
test-cov:
	pytest tests/ --cov=ct600 --cov-report=html --cov-report=term

# Run tests excluding slow ones
test-fast:
	pytest tests/ -m "not slow"

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete