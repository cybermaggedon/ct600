# Test Strategy for CT600

## Overview

This document outlines the testing strategy for the CT600 (UK HMRC Corporation Tax submission) Python package. The application handles sensitive tax data and communicates with government APIs, making comprehensive testing critical for reliability and compliance.

## Testing Scope

### Core Components to Test

1. **Tax Computations Processing** (`computations.py`)
   - iXBRL parsing and value extraction
   - Form field mapping and validation
   - Mathematical calculations and totals

2. **Government API Communication** (`govtalk.py`)
   - XML message creation and parsing
   - Digital signature (IRmark) generation/verification
   - HTTP submission and response handling
   - Polling mechanisms for async operations

3. **Corporation Tax Logic** (`corptax.py`)
   - Tax return assembly
   - Document bundling (accounts, computations, attachments)
   - Schema validation

4. **iXBRL Processing** (`ixbrl.py`)
   - Document parsing
   - Fact extraction
   - Schema validation

5. **Command Line Interface** (`__main__.py`)
   - Argument parsing
   - File handling
   - Output formatting

6. **Test Service** (`test_service.py`)
   - Mock HMRC API responses
   - Request validation
   - Schema compliance

## Testing Levels

### Unit Tests
- **Scope**: Individual functions and classes
- **Framework**: pytest
- **Coverage Target**: 90%+ for core business logic
- **Focus Areas**:
  - Tax calculation accuracy
  - XML parsing/generation
  - Data validation
  - Error handling

### Integration Tests
- **Scope**: Component interactions
- **Focus Areas**:
  - File processing workflows
  - API message flows
  - Schema validation chains
  - Configuration loading

### End-to-End Tests
- **Scope**: Complete user workflows
- **Test Environment**: Local test service + real file samples
- **Scenarios**:
  - Full submission workflow (accounts → computations → submission)
  - Error handling paths
  - Different company types/scenarios

### Contract Tests
- **Scope**: HMRC API compliance
- **Purpose**: Ensure compatibility with government schemas
- **Approach**: Test against official XSD schemas and sample data

## Test Data Strategy

### Test Data Categories

1. **Sample iXBRL Files**
   - Valid accounts documents (different company sizes)
   - Valid computations documents
   - Invalid/malformed documents for error testing
   - Edge cases (nil values, unusual structures)

2. **Configuration Files**
   - Valid authentication configs
   - Invalid/incomplete configs
   - Different gateway environments (test/live)

3. **Form Values**
   - Typical company scenarios
   - Edge cases (losses, R&D, etc.)
   - Invalid data for validation testing

4. **Expected Outputs**
   - Golden files for XML generation
   - Expected calculation results
   - Error message expectations

### Data Management
- Store test data in `tests/fixtures/` directory
- Use factory patterns for generating test data
- Sanitize any real data (remove actual company details)
- Version control all test data

## Testing Infrastructure

### Test Framework Setup
```
tests/
├── unit/
│   ├── test_computations.py
│   ├── test_govtalk.py
│   ├── test_corptax.py
│   ├── test_ixbrl.py
│   └── test_irmark.py
├── integration/
│   ├── test_submission_workflow.py
│   ├── test_file_processing.py
│   └── test_api_communication.py
├── e2e/
│   ├── test_full_submission.py
│   └── test_cli_workflows.py
├── fixtures/
│   ├── accounts/
│   ├── computations/
│   ├── configs/
│   └── expected_outputs/
├── conftest.py
└── requirements.txt
```

### Test Dependencies
- **pytest**: Main testing framework
- **pytest-asyncio**: For async test support
- **pytest-mock**: Mocking capabilities
- **pytest-cov**: Coverage reporting
- **responses**: HTTP request mocking
- **xmlschema**: Schema validation testing
- **lxml**: XML processing for tests

### Continuous Integration
- Run full test suite on every commit
- Separate test environments for different Python versions
- Code coverage reporting and enforcement
- Performance regression testing

## Security Testing

### Sensitive Data Handling
- Test that secrets (passwords, keys) are never logged
- Verify secure transmission of data
- Test authentication failure scenarios

### Input Validation
- Test against malicious XML inputs
- Validate file size limits
- Test path traversal protections

## Performance Testing

### Load Testing
- Test with large iXBRL documents
- Multiple concurrent submissions
- Memory usage monitoring

### Benchmark Testing
- Establish baseline performance metrics
- Monitor regression in processing times
- Test timeout scenarios

## Mock Strategy

### External Dependencies
- **HMRC API**: Mock all HTTP calls in unit/integration tests
- **File System**: Mock file operations where appropriate
- **Time-dependent operations**: Mock datetime for consistent testing

### Mock Levels
- **Unit Tests**: Mock all external dependencies
- **Integration Tests**: Use test service, mock file system
- **E2E Tests**: Real files, local test service

## Test Execution Strategy

### Local Development
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ct600 --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run performance tests
pytest -m performance
```

### Automated Testing
- Pre-commit hooks for fast tests
- Full test suite in CI/CD pipeline
- Nightly runs with extended test scenarios

## Quality Gates

### Code Coverage
- Minimum 85% overall coverage
- 95% coverage for core calculation logic
- No decrease in coverage for new commits

### Test Quality Metrics
- All tests must pass
- No flaky tests (>95% pass rate)
- Test execution time under 5 minutes for full suite

### Compliance Requirements
- All schema validation tests must pass
- IRmark generation must be bit-perfect
- No data leakage in test logs

## Risk-Based Testing Priorities

### High Risk (Critical Testing)
1. Tax calculation accuracy
2. IRmark generation/validation
3. XML schema compliance
4. Data security/privacy

### Medium Risk (Important Testing)
1. Error handling and recovery
2. File format validation
3. Configuration management
4. CLI usability

### Low Risk (Nice to Have)
1. Performance optimization
2. Code style consistency
3. Documentation accuracy

## Maintenance Strategy

### Test Maintenance
- Review and update tests when requirements change
- Regular cleanup of obsolete tests
- Update test data when schemas change
- Monitor and fix flaky tests

### Documentation
- Keep TEST_STRATEGY.md updated
- Document test data sources and expectations
- Maintain troubleshooting guides for test failures

## Success Criteria

The testing strategy is successful when:
- Bugs are caught before production deployment
- Confidence in code changes is high
- HMRC schema compliance is maintained
- Test suite provides fast feedback to developers
- Production incidents related to untested scenarios are minimized