"""Unit tests for config module."""

import pytest
import datetime
from unittest.mock import patch, Mock

from ct600.config import CT600Config, load_config
from ct600.exceptions import ConfigurationError


class TestCT600Config:
    """Test CT600Config class."""
    
    def test_valid_config_initialization(self):
        """Test initialization with valid configuration."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        config = CT600Config(config_data)
        assert config.get("username") == "test_user"
        assert config.get("password") == "test_pass"
        assert config.get("gateway-test") == "1"
        assert config.get("vendor-id") == "test_vendor"
        assert config.get("url") == "https://example.com/api"
    
    def test_missing_required_keys(self):
        """Test initialization with missing required keys."""
        config_data = {
            "username": "test_user",
            "password": "test_pass"
            # Missing vendor-id (url and gateway-test are optional)
        }

        with pytest.raises(ConfigurationError) as exc_info:
            CT600Config(config_data)

        assert "Missing required configuration keys" in str(exc_info.value)
        assert "vendor-id" in exc_info.value.missing_keys
    
    def test_invalid_gateway_test_type(self):
        """Test initialization with invalid gateway-test type."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": "true",  # Invalid - must be 0, 1, "0", "1", true, or false
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }

        with pytest.raises(ConfigurationError) as exc_info:
            CT600Config(config_data)

        assert "gateway-test must be" in str(exc_info.value)

    @pytest.mark.parametrize("input_value,expected", [
        (True, "1"),
        (False, "0"),
        (1, "1"),
        (0, "0"),
        ("1", "1"),
        ("0", "0"),
    ])
    def test_gateway_test_normalization(self, input_value, expected):
        """Test gateway-test accepts bool, int, and string formats."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": input_value,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }

        config = CT600Config(config_data)
        assert config.get("gateway-test") == expected

    @pytest.mark.parametrize("invalid_value", [
        "true",
        "false",
        "yes",
        "no",
        2,
        -1,
        None,
        [],
        {},
        0.5,
    ])
    def test_gateway_test_invalid_values(self, invalid_value):
        """Test gateway-test rejects invalid values."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": invalid_value,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }

        with pytest.raises(ConfigurationError) as exc_info:
            CT600Config(config_data)

        assert "gateway-test must be" in str(exc_info.value)

    @pytest.mark.parametrize("input_value,expected_is_test", [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        ("1", True),
        ("0", False),
    ])
    def test_is_test_gateway_with_all_formats(self, input_value, expected_is_test):
        """Test is_test_gateway property works with all accepted formats."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": input_value,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }

        config = CT600Config(config_data)
        assert config.is_test_gateway is expected_is_test

    def test_invalid_url_format(self):
        """Test initialization with invalid URL format."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "ftp://invalid.com"  # Should be HTTP/HTTPS
        }
        
        with pytest.raises(ConfigurationError) as exc_info:
            CT600Config(config_data)
        
        assert "url must be a valid HTTP/HTTPS URL" in str(exc_info.value)
    
    def test_get_method_with_default(self):
        """Test get method with default value."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        config = CT600Config(config_data)
        
        # Existing key
        assert config.get("username") == "test_user"
        
        # Non-existing key with default
        assert config.get("nonexistent", "default_value") == "default_value"
        
        # Non-existing key without default
        assert config.get("nonexistent") is None
    
    def test_get_request_params_basic(self):
        """Test basic request parameters generation."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        config = CT600Config(config_data)
        mock_envelope = Mock()
        
        params = config.get_request_params("1234567890", mock_envelope)
        
        assert params["username"] == "test_user"
        assert params["password"] == "test_pass"
        assert params["class"] == "HMRC-CT-CT600-TIL"  # Default
        assert params["gateway-test"] == "1"
        assert params["tax-reference"] == "1234567890"
        assert params["vendor-id"] == "test_vendor"
        assert params["software"] == "ct600"
        assert params["software-version"] == "1.0.0"
        assert params["ir-envelope"] is mock_envelope
        assert "timestamp" not in params
    
    def test_get_request_params_with_custom_class(self):
        """Test request parameters with custom message class."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "class": "CUSTOM-CLASS",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        config = CT600Config(config_data)
        mock_envelope = Mock()
        
        params = config.get_request_params("1234567890", mock_envelope)
        
        assert params["class"] == "CUSTOM-CLASS"
    
    def test_get_request_params_with_timestamp_override(self):
        """Test request parameters with timestamp override."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        config = CT600Config(config_data)
        mock_envelope = Mock()
        test_timestamp = datetime.datetime(2023, 12, 31, 12, 0, 0)
        
        params = config.get_request_params("1234567890", mock_envelope, timestamp=test_timestamp)
        
        assert params["timestamp"] == test_timestamp
    
    def test_get_request_params_with_config_timestamp(self):
        """Test request parameters with timestamp in config."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api",
            "timestamp": "2023-12-31T12:00:00"
        }
        
        config = CT600Config(config_data)
        mock_envelope = Mock()
        
        params = config.get_request_params("1234567890", mock_envelope)
        
        assert "timestamp" in params
        assert isinstance(params["timestamp"], datetime.datetime)
        assert params["timestamp"].year == 2023
        assert params["timestamp"].month == 12
        assert params["timestamp"].day == 31
    
    def test_get_poll_params(self):
        """Test polling parameters generation."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        config = CT600Config(config_data)
        
        params = config.get_poll_params("correlation-123")
        
        assert params["username"] == "test_user"
        assert params["password"] == "test_pass"
        assert params["class"] == "HMRC-CT-CT600-TIL"
        assert params["gateway-test"] == "1"
        assert params["correlation-id"] == "correlation-123"
        
        # Should not include other params like vendor-id
        assert "vendor-id" not in params
        assert "software" not in params
    
    def test_is_test_gateway_property(self):
        """Test is_test_gateway property."""
        # Test gateway
        test_config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        test_config = CT600Config(test_config_data)
        assert test_config.is_test_gateway is True
        
        # Production gateway
        prod_config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": False,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        prod_config = CT600Config(prod_config_data)
        assert prod_config.is_test_gateway is False
    
    def test_submission_url_property(self):
        """Test submission_url property."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        config = CT600Config(config_data)
        assert config.submission_url == "https://example.com/api"
    
    def test_config_immutability(self):
        """Test that configuration data is copied and not referenced."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        config = CT600Config(config_data)
        
        # Modify original dict
        config_data["username"] = "modified_user"
        
        # Config should not be affected
        assert config.get("username") == "test_user"


class TestLoadConfig:
    """Test load_config function."""
    
    @patch('ct600.file_operations.load_config_file')
    def test_load_config_success(self, mock_load_config_file):
        """Test successful config loading."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        mock_load_config_file.return_value = config_data
        
        config = load_config("test_config.json")
        
        assert isinstance(config, CT600Config)
        assert config.get("username") == "test_user"
        mock_load_config_file.assert_called_once_with("test_config.json")
    
    @patch('ct600.file_operations.load_config_file')
    def test_load_config_default_file(self, mock_load_config_file):
        """Test config loading with default file."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        mock_load_config_file.return_value = config_data
        
        config = load_config()  # No file specified
        
        assert isinstance(config, CT600Config)
        mock_load_config_file.assert_called_once_with("config.json")  # Default
    
    @patch('ct600.file_operations.load_config_file')
    def test_load_config_configuration_error(self, mock_load_config_file):
        """Test config loading with configuration error."""
        config_data = {
            "username": "test_user",
            "password": "test_pass"
            # Missing required keys
        }
        
        mock_load_config_file.return_value = config_data
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_config("test_config.json")
        
        assert exc_info.value.config_file == "test_config.json"
        assert "Missing required configuration keys" in str(exc_info.value)
    
    @patch('ct600.file_operations.load_config_file')
    def test_load_config_file_operation_error(self, mock_load_config_file):
        """Test config loading with file operation error."""
        from ct600.exceptions import FileOperationError
        
        mock_load_config_file.side_effect = FileOperationError("File not found")
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_config("nonexistent.json")
        
        assert exc_info.value.config_file == "nonexistent.json"
        assert "Failed to load configuration" in str(exc_info.value)


class TestConfigurationValidation:
    """Test configuration validation edge cases."""
    
    def test_empty_config(self):
        """Test validation with empty configuration."""
        with pytest.raises(ConfigurationError) as exc_info:
            CT600Config({})

        assert len(exc_info.value.missing_keys) == 3  # All required keys missing (url and gateway-test are optional)
        assert "username" in exc_info.value.missing_keys
        assert "password" in exc_info.value.missing_keys
        assert "vendor-id" in exc_info.value.missing_keys
    
    def test_none_values_in_config(self):
        """Test validation with None values."""
        config_data = {
            "username": None,
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }
        
        # Should not raise error - None values are allowed
        config = CT600Config(config_data)
        assert config.get("username") is None
    
    def test_extra_config_keys(self):
        """Test configuration with extra keys (should be allowed)."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com/api",
            "extra_key": "extra_value",
            "another_key": 12345
        }
        
        config = CT600Config(config_data)
        assert config.get("extra_key") == "extra_value"
        assert config.get("another_key") == 12345
    
    def test_url_validation_edge_cases(self):
        """Test URL validation edge cases."""
        base_config = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor"
        }

        # Valid URLs
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "http://example.com/path",
            "https://example.com:8080/path?query=value",
        ]

        for url in valid_urls:
            config_data = base_config.copy()
            config_data["url"] = url
            config = CT600Config(config_data)  # Should not raise
            assert config.get("url") == url

        # Invalid URLs (non-HTTP/HTTPS schemes)
        invalid_urls = [
            "ftp://example.com",
            "example.com",
            "//example.com",
        ]

        for url in invalid_urls:
            config_data = base_config.copy()
            config_data["url"] = url
            with pytest.raises(ConfigurationError):
                CT600Config(config_data)

        # Empty/None URLs are allowed (will use default)
        for url in ["", None]:
            config_data = base_config.copy()
            config_data["url"] = url
            config = CT600Config(config_data)  # Should not raise
            # submission_url returns default when url is empty/None
            assert config.submission_url == "http://localhost:8081/"


    def test_gateway_test_defaults_when_missing(self):
        """Test that gateway-test defaults to '1' when not provided."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "vendor-id": "test_vendor",
            "url": "https://example.com/api"
        }

        config = CT600Config(config_data)
        assert config.get("gateway-test") == "1"
        assert config.is_test_gateway is True

    def test_default_submission_url_when_no_url(self):
        """Test that submission_url defaults to localhost when no URL provided."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "vendor-id": "test_vendor",
        }

        config = CT600Config(config_data)
        assert config.submission_url == "http://localhost:8081/"


class TestConfigurationIntegration:
    """Integration tests for configuration handling."""
    
    def test_full_request_params_generation(self):
        """Test complete request parameters generation workflow."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": False,
            "vendor-id": "vendor_123",
            "url": "https://api.hmrc.gov.uk/submission",
            "class": "HMRC-CT-CT600-CUSTOM",
            "timestamp": "2023-12-31T15:30:00"
        }
        
        config = CT600Config(config_data)
        mock_envelope = Mock()
        mock_envelope.tag = "IRenvelope"
        
        # Test request params
        request_params = config.get_request_params("9876543210", mock_envelope)
        
        expected_keys = {
            "username", "password", "class", "gateway-test", "tax-reference",
            "vendor-id", "software", "software-version", "ir-envelope", "timestamp"
        }
        
        assert set(request_params.keys()) == expected_keys
        assert request_params["username"] == "test_user"
        assert request_params["password"] == "test_pass"
        assert request_params["class"] == "HMRC-CT-CT600-CUSTOM"
        assert request_params["gateway-test"] == "0"
        assert request_params["tax-reference"] == "9876543210"
        assert request_params["vendor-id"] == "vendor_123"
        assert request_params["software"] == "ct600"
        assert request_params["software-version"] == "1.0.0"
        assert request_params["ir-envelope"] is mock_envelope
        assert isinstance(request_params["timestamp"], datetime.datetime)
        
        # Test poll params
        poll_params = config.get_poll_params("correlation_456")
        
        expected_poll_keys = {
            "username", "password", "class", "gateway-test", "correlation-id"
        }
        
        assert set(poll_params.keys()) == expected_poll_keys
        assert poll_params["correlation-id"] == "correlation_456"