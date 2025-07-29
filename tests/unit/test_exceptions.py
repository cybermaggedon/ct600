"""Unit tests for exceptions module."""

import pytest

from ct600.exceptions import (
    CT600Error, FileOperationError, ConfigurationError, SchemaValidationError,
    SubmissionError, SubmissionTimeoutError, ArgumentValidationError, BundleCreationError
)


class TestCT600Error:
    """Test base CT600Error exception."""
    
    def test_ct600_error_inheritance(self):
        """Test CT600Error inherits from Exception."""
        assert issubclass(CT600Error, Exception)
    
    def test_ct600_error_instantiation(self):
        """Test CT600Error can be instantiated."""
        error = CT600Error("Test error")
        assert str(error) == "Test error"


class TestFileOperationError:
    """Test FileOperationError exception."""
    
    def test_file_operation_error_inheritance(self):
        """Test FileOperationError inherits from CT600Error."""
        assert issubclass(FileOperationError, CT600Error)
    
    def test_file_operation_error_basic(self):
        """Test basic FileOperationError instantiation."""
        error = FileOperationError("File not found")
        assert str(error) == "File not found"
        assert error.filename is None
        assert error.original_error is None
    
    def test_file_operation_error_with_filename(self):
        """Test FileOperationError with filename."""
        error = FileOperationError("File not found", filename="test.txt")
        assert str(error) == "File not found"
        assert error.filename == "test.txt"
        assert error.original_error is None
    
    def test_file_operation_error_with_original_error(self):
        """Test FileOperationError with original error."""
        original = IOError("Permission denied")
        error = FileOperationError("File error", filename="test.txt", original_error=original)
        assert str(error) == "File error"
        assert error.filename == "test.txt"
        assert error.original_error is original


class TestConfigurationError:
    """Test ConfigurationError exception."""
    
    def test_configuration_error_inheritance(self):
        """Test ConfigurationError inherits from CT600Error."""
        assert issubclass(ConfigurationError, CT600Error)
    
    def test_configuration_error_basic(self):
        """Test basic ConfigurationError instantiation."""
        error = ConfigurationError("Invalid config")
        assert str(error) == "Invalid config"
        assert error.config_file is None
        assert error.missing_keys == []
    
    def test_configuration_error_with_config_file(self):
        """Test ConfigurationError with config file."""
        error = ConfigurationError("Invalid config", config_file="config.json")
        assert str(error) == "Invalid config"
        assert error.config_file == "config.json"
        assert error.missing_keys == []
    
    def test_configuration_error_with_missing_keys(self):
        """Test ConfigurationError with missing keys."""
        missing_keys = ["username", "password"]
        error = ConfigurationError("Missing keys", missing_keys=missing_keys)
        assert str(error) == "Missing keys"
        assert error.config_file is None
        assert error.missing_keys == missing_keys


class TestSchemaValidationError:
    """Test SchemaValidationError exception."""
    
    def test_schema_validation_error_inheritance(self):
        """Test SchemaValidationError inherits from CT600Error."""
        assert issubclass(SchemaValidationError, CT600Error)
    
    def test_schema_validation_error_basic(self):
        """Test basic SchemaValidationError instantiation."""
        error = SchemaValidationError("Schema validation failed")
        assert str(error) == "Schema validation failed"
        assert error.filename is None
        assert error.missing_schemas == []
    
    def test_schema_validation_error_with_filename(self):
        """Test SchemaValidationError with filename."""
        error = SchemaValidationError("Schema error", filename="test.xml")
        assert str(error) == "Schema error"
        assert error.filename == "test.xml"
        assert error.missing_schemas == []
    
    def test_schema_validation_error_with_missing_schemas(self):
        """Test SchemaValidationError with missing schemas."""
        missing = ["DPL schema", "FRS schema"]
        error = SchemaValidationError("Missing schemas", missing_schemas=missing)
        assert str(error) == "Missing schemas"
        assert error.filename is None
        assert error.missing_schemas == missing


class TestSubmissionError:
    """Test SubmissionError exception."""
    
    def test_submission_error_inheritance(self):
        """Test SubmissionError inherits from CT600Error."""
        assert issubclass(SubmissionError, CT600Error)
    
    def test_submission_error_basic(self):
        """Test basic SubmissionError instantiation."""
        error = SubmissionError("Submission failed")
        assert str(error) == "Submission failed"
        assert error.status_code is None
        assert error.correlation_id is None
    
    def test_submission_error_with_status_code(self):
        """Test SubmissionError with status code."""
        error = SubmissionError("HTTP error", status_code=500)
        assert str(error) == "HTTP error"
        assert error.status_code == 500
        assert error.correlation_id is None
    
    def test_submission_error_with_correlation_id(self):
        """Test SubmissionError with correlation ID."""
        error = SubmissionError("Processing error", correlation_id="12345")
        assert str(error) == "Processing error"
        assert error.status_code is None
        assert error.correlation_id == "12345"


class TestSubmissionTimeoutError:
    """Test SubmissionTimeoutError exception."""
    
    def test_submission_timeout_error_inheritance(self):
        """Test SubmissionTimeoutError inherits from SubmissionError."""
        assert issubclass(SubmissionTimeoutError, SubmissionError)
    
    def test_submission_timeout_error_basic(self):
        """Test basic SubmissionTimeoutError instantiation."""
        error = SubmissionTimeoutError("Timeout occurred")
        assert str(error) == "Timeout occurred"
        assert error.status_code is None  # Inherited from SubmissionError
        assert error.correlation_id is None
        assert error.timeout_seconds is None
    
    def test_submission_timeout_error_with_correlation_id(self):
        """Test SubmissionTimeoutError with correlation ID."""
        error = SubmissionTimeoutError("Timeout", correlation_id="12345")
        assert str(error) == "Timeout"
        assert error.correlation_id == "12345"
        assert error.timeout_seconds is None
    
    def test_submission_timeout_error_with_timeout_seconds(self):
        """Test SubmissionTimeoutError with timeout seconds."""
        error = SubmissionTimeoutError("Timeout", timeout_seconds=120)
        assert str(error) == "Timeout"
        assert error.correlation_id is None
        assert error.timeout_seconds == 120


class TestArgumentValidationError:
    """Test ArgumentValidationError exception."""
    
    def test_argument_validation_error_inheritance(self):
        """Test ArgumentValidationError inherits from CT600Error."""
        assert issubclass(ArgumentValidationError, CT600Error)
    
    def test_argument_validation_error_basic(self):
        """Test basic ArgumentValidationError instantiation."""
        error = ArgumentValidationError("Invalid argument")
        assert str(error) == "Invalid argument"
        assert error.argument_name is None
    
    def test_argument_validation_error_with_argument_name(self):
        """Test ArgumentValidationError with argument name."""
        error = ArgumentValidationError("Invalid value", argument_name="--config")
        assert str(error) == "Invalid value"
        assert error.argument_name == "--config"


class TestBundleCreationError:
    """Test BundleCreationError exception."""
    
    def test_bundle_creation_error_inheritance(self):
        """Test BundleCreationError inherits from CT600Error."""
        assert issubclass(BundleCreationError, CT600Error)
    
    def test_bundle_creation_error_basic(self):
        """Test basic BundleCreationError instantiation."""
        error = BundleCreationError("Bundle creation failed")
        assert str(error) == "Bundle creation failed"
        assert error.missing_files == []
    
    def test_bundle_creation_error_with_missing_files(self):
        """Test BundleCreationError with missing files."""
        missing_files = ["accounts.xml", "computations.xml"]
        error = BundleCreationError("Missing files", missing_files=missing_files)
        assert str(error) == "Missing files"
        assert error.missing_files == missing_files


class TestExceptionChaining:
    """Test exception chaining and inheritance relationships."""
    
    def test_all_custom_exceptions_inherit_from_ct600_error(self):
        """Test all custom exceptions inherit from CT600Error."""
        custom_exceptions = [
            FileOperationError, ConfigurationError, SchemaValidationError,
            SubmissionError, SubmissionTimeoutError, ArgumentValidationError, 
            BundleCreationError
        ]
        
        for exception_class in custom_exceptions:
            assert issubclass(exception_class, CT600Error)
    
    def test_submission_timeout_inherits_from_submission_error(self):
        """Test SubmissionTimeoutError inherits from SubmissionError."""
        assert issubclass(SubmissionTimeoutError, SubmissionError)
        
        # Test that it also inherits SubmissionError attributes
        error = SubmissionTimeoutError("Timeout", correlation_id="12345", timeout_seconds=120)
        assert hasattr(error, 'status_code')  # From SubmissionError
        assert hasattr(error, 'correlation_id')  # From SubmissionError
        assert hasattr(error, 'timeout_seconds')  # From SubmissionTimeoutError
    
    def test_exception_can_be_caught_by_base_class(self):
        """Test that specific exceptions can be caught by base class."""
        try:
            raise FileOperationError("Test error")
        except CT600Error as e:
            assert isinstance(e, FileOperationError)
            assert isinstance(e, CT600Error)
        
        try:
            raise SubmissionTimeoutError("Test timeout")
        except SubmissionError as e:
            assert isinstance(e, SubmissionTimeoutError)
            assert isinstance(e, SubmissionError)
            assert isinstance(e, CT600Error)