"""Custom exception classes for ct600 module."""


class CT600Error(Exception):
    """Base exception for ct600 module."""
    pass


class FileOperationError(CT600Error):
    """Exception raised for file operation errors."""
    
    def __init__(self, message, filename=None, original_error=None):
        super().__init__(message)
        self.filename = filename
        self.original_error = original_error


class ConfigurationError(CT600Error):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message, config_file=None, missing_keys=None):
        super().__init__(message)
        self.config_file = config_file
        self.missing_keys = missing_keys or []


class SchemaValidationError(CT600Error):
    """Exception raised for schema validation errors."""
    
    def __init__(self, message, filename=None, missing_schemas=None):
        super().__init__(message)
        self.filename = filename
        self.missing_schemas = missing_schemas or []


class SubmissionError(CT600Error):
    """Exception raised for HMRC submission errors."""
    
    def __init__(self, message, status_code=None, correlation_id=None):
        super().__init__(message)
        self.status_code = status_code
        self.correlation_id = correlation_id


class SubmissionTimeoutError(SubmissionError):
    """Exception raised when submission polling times out."""
    
    def __init__(self, message, correlation_id=None, timeout_seconds=None):
        super().__init__(message, correlation_id=correlation_id)
        self.timeout_seconds = timeout_seconds


class ArgumentValidationError(CT600Error):
    """Exception raised for command-line argument validation errors."""
    
    def __init__(self, message, argument_name=None):
        super().__init__(message)
        self.argument_name = argument_name


class BundleCreationError(CT600Error):
    """Exception raised when creating InputBundle fails."""
    
    def __init__(self, message, missing_files=None):
        super().__init__(message)
        self.missing_files = missing_files or []