# Makefile for zt-monitoring testing and development

.PHONY: all test test-unit test-integration test-e2e test-api test-container clean help setup lint run-monitoring run-api build-container coverage install

# Default target
all: test

# Help
help:
	@echo "Available targets:"
	@echo "  test              - Run all tests"
	@echo "  test-unit         - Run unit tests only"
	@echo "  test-integration  - Run integration tests only"
	@echo "  test-e2e          - Run end-to-end tests only"
	@echo "  test-api          - Run API tests only"
	@echo "  test-container    - Run container tests only"
	@echo "  coverage          - Run tests with coverage report"
	@echo "  setup             - Install dependencies"
	@echo "  install           - Install package in development mode"
	@echo "  lint              - Run code linting"
	@echo "  format            - Format code with black"
	@echo "  clean             - Clean up test artifacts"
	@echo "  run-monitoring    - Run monitoring script"
	@echo "  run-api           - Run API server"
	@echo "  build-container   - Build container image"

# Install package in development mode
install:
	pip install -e .

# Install dependencies
setup:
	pip install --upgrade pip
	pip install -r requirements.txt

#####################################
# TODO fix venv ref here
#####################################

# Run all tests
test:
	pytest

# Run unit tests only
test-unit:
	pytest tests/unit/ -v

# Run integration tests only
test-integration:
	pytest tests/integration/ -v

# Run end-to-end tests only
test-e2e:
	pytest tests/e2e/ -v

# Run API tests only
test-api:
	pytest tests/unit/test_api.py -v

# Run container tests only
test-container:
	@echo "Testing container build..."
	@if command -v podman > /dev/null; then \
		podman build -t zt-monitoring-test . && echo "Container build: PASSED"; \
	elif command -v docker > /dev/null; then \
		docker build -t zt-monitoring-test . && echo "Container build: PASSED"; \
	else \
		echo "Neither podman nor docker found, skipping container tests"; \
	fi

# Run tests with coverage
coverage:
	pytest --cov=. --cov-report=html --cov-report=xml --cov-report=term-missing

# Run tests in parallel
test-parallel:
	pytest -n auto

# Run tests with specific markers
test-slow:
	pytest -m slow

test-fast:
	pytest -m "not slow"

# Code formatting
format:
	black .

# Code linting
lint:
	flake8 .
	mypy . --ignore-missing-imports
	bandit -r . -f json || true
	safety check || true

# Security scan
security:
	bandit -r .
	safety check

# Clean up test artifacts
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf test-results.xml
	rm -rf coverage.xml
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache/
	rm -rf .tox/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

# Run monitoring script
run-monitoring:
	python3 monitoring.py

# Run API server
run-api:
	uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Build container image
build-container:
	@if command -v podman > /dev/null; then \
		podman build -t zt-monitoring .; \
	elif command -v docker > /dev/null; then \
		docker build -t zt-monitoring .; \
	else \
		echo "Neither podman nor docker found"; \
		exit 1; \
	fi

# Run container
run-container:
	@if command -v podman > /dev/null; then \
		podman run --rm -p 8000:8000 zt-monitoring; \
	elif command -v docker > /dev/null; then \
		docker run --rm -p 8000:8000 zt-monitoring; \
	else \
		echo "Neither podman nor docker found"; \
		exit 1; \
	fi

# Development server with auto-reload
dev-server:
	uvicorn api:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# Run tests in watch mode
test-watch:
	pytest-watch

# Generate test report
test-report:
	pytest --html=test-report.html --self-contained-html

# Profiling
profile:
	pytest --profile

# Pre-commit hooks
pre-commit:
	pre-commit run --all-files

# CI target (used by GitHub Actions)
ci: lint test coverage

# Local development setup
dev-setup: setup install
	pre-commit install

# Database operations
db-init:
	python3 -c "import sqlite3; conn = sqlite3.connect('metrics.db'); conn.execute('CREATE TABLE IF NOT EXISTS cpu_usage (id INTEGER PRIMARY KEY, host TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, cpu_usage REAL)'); conn.close()"

db-clean:
	rm -f metrics.db test_metrics.db

# Benchmarking
benchmark:
	pytest tests/ --benchmark-only

# Documentation
docs:
	@echo "Generating documentation..."
	@echo "Documentation available in README.md and TESTING.md"

# Version info
version:
	@echo "zt-monitoring version: $(shell grep version pyproject.toml | cut -d'"' -f2)"
	@echo "Python version: $(shell python3 --version)"
	@echo "Pytest version: $(shell pytest --version)"

# Health check
health:
	@echo "Running health checks..."
	@python3 -c "import sys; print('Python:', sys.version)"
	@python3 -c "import monitoring; print('Monitoring module: OK')"
	@python3 -c "import api; print('API module: OK')"
	@echo "Health check completed"