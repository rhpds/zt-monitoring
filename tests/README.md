# Test Structure

This directory contains all tests for the zt-monitoring project, organized by test type.

## Directory Structure

```
tests/
├── unit/           # Unit tests for individual functions and classes
├── integration/    # Integration tests for component interactions
├── e2e/           # End-to-end tests for complete workflows
├── conftest.py    # Shared fixtures for all tests
└── README.md      # This file
```

## Running Tests

### All Tests
```bash
pytest
# or
make test
```

### Unit Tests Only
```bash
pytest tests/unit/
# or
make test-unit
```

### Integration Tests Only
```bash
pytest tests/integration/
# or
make test-integration
```

### End-to-End Tests Only
```bash
pytest tests/e2e/
# or
make test-e2e
```

### With Coverage
```bash
pytest --cov=. --cov-report=html
# or
make coverage
```

### Parallel Execution
```bash
pytest -n auto
# or
make test-parallel
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API tests
- `@pytest.mark.slow` - Slow-running tests

### Running Tests by Marker
```bash
# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"

# Run only slow tests
pytest -m slow
```

## Test Configuration

Test configuration is managed through:

- `pyproject.toml` - Main pytest configuration
- `conftest.py` files - Shared fixtures at different levels
- Environment variables for test-specific settings

## Writing Tests

### Unit Tests
- Test individual functions and classes in isolation
- Use mocks for external dependencies
- Fast execution (< 1 second per test)

### Integration Tests
- Test interactions between components
- Use real databases and file systems (in temp directories)
- May take longer to execute

### End-to-End Tests
- Test complete workflows from start to finish
- Use real or realistic test environments
- Include performance and reliability testing

## Fixtures

Common fixtures are available in `conftest.py` files:

- `test_db_path` - Temporary database for testing
- `mock_proc_files` - Mock system /proc files
- `sample_metrics` - Sample metrics data
- `mock_ansible_environment` - Mock Ansible environment

## Best Practices

1. **Use descriptive test names** - Test names should clearly describe what is being tested
2. **One assertion per test** - Each test should verify one specific behavior
3. **Use fixtures for setup** - Avoid repetitive setup code
4. **Mock external dependencies** - Keep tests isolated and fast
5. **Test both success and failure cases** - Include error handling tests
6. **Use parametrized tests** - Test multiple inputs efficiently

## Continuous Integration

Tests are run automatically on:
- Pull requests
- Push to main branch
- Weekly schedule (dependency checks)

The CI pipeline includes:
- Linting and code quality checks
- Unit and integration tests
- Coverage reporting
- Security scanning
- Container building and testing