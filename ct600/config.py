"""Configuration handling and validation for ct600 module."""

import datetime
from typing import Dict, Any, Optional

from .constants import DEFAULT_CONFIG_FILE, HMRC_MESSAGE_CLASS, SOFTWARE_NAME, DEFAULT_SUBMISSION_URL, DEFAULT_GATEWAY_TEST
from . import __version__ as VERSION
from .exceptions import ConfigurationError


class CT600Config:
    """Configuration container for CT600 operations."""
    
    REQUIRED_KEYS = {
        "username", "password", "vendor-id"
    }
    
    def __init__(self, config_data: Dict[str, Any]):
        """Initialize configuration from dictionary.
        
        Args:
            config_data: Configuration dictionary
            
        Raises:
            ConfigurationError: If required keys are missing or invalid
        """
        self._validate_config(config_data)
        self._config = config_data.copy()
    
    def _validate_config(self, config_data: Dict[str, Any]) -> None:
        """Validate configuration data.
        
        Args:
            config_data: Configuration to validate
            
        Raises:
            ConfigurationError: If validation fails
        """
        missing_keys = self.REQUIRED_KEYS - set(config_data.keys())
        if missing_keys:
            raise ConfigurationError(
                f"Missing required configuration keys: {', '.join(sorted(missing_keys))}",
                missing_keys=list(missing_keys)
            )
        
        # Apply safe default for gateway-test if not provided
        if "gateway-test" not in config_data:
            config_data["gateway-test"] = DEFAULT_GATEWAY_TEST

        # Normalize gateway-test to string "0" or "1" for XML compatibility
        # Accept: bool (true/false), int (0/1), string ("0"/"1")
        gateway_test = config_data.get("gateway-test")
        if isinstance(gateway_test, bool):
            config_data["gateway-test"] = "1" if gateway_test else "0"
        elif gateway_test in (0, 1):
            config_data["gateway-test"] = str(gateway_test)
        elif gateway_test not in ("0", "1"):
            raise ConfigurationError(
                "gateway-test must be 0, 1, '0', '1', true, or false"
            )
        
        # Validate URL format if provided
        url = config_data.get("url")
        if url and not str(url).startswith(("http://", "https://")):
            raise ConfigurationError("url must be a valid HTTP/HTTPS URL")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def get_request_params(self, utr: str, ir_envelope: Any, 
                          timestamp: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """Get parameters for HMRC request.
        
        Args:
            utr: Unique Taxpayer Reference
            ir_envelope: IR envelope element
            timestamp: Optional timestamp override
            
        Returns:
            Dictionary of request parameters
        """
        params = {
            "username": self.get("username"),
            "password": self.get("password"),
            "class": self.get("class", HMRC_MESSAGE_CLASS),
            "gateway-test": self.get("gateway-test"),
            "tax-reference": utr,
            "vendor-id": self.get("vendor-id"),
            "software": SOFTWARE_NAME,
            "software-version": VERSION,
            "ir-envelope": ir_envelope
        }
        
        if timestamp:
            params["timestamp"] = timestamp
        elif "timestamp" in self._config:
            params["timestamp"] = datetime.datetime.fromisoformat(
                self._config["timestamp"]
            )
        
        return params
    
    def get_poll_params(self, correlation_id: str) -> Dict[str, Any]:
        """Get parameters for polling request.
        
        Args:
            correlation_id: Correlation ID from initial submission
            
        Returns:
            Dictionary of polling parameters
        """
        return {
            "username": self.get("username"),
            "password": self.get("password"),
            "class": self.get("class", HMRC_MESSAGE_CLASS),
            "gateway-test": self.get("gateway-test"),
            "correlation-id": correlation_id
        }
    
    @property
    def is_test_gateway(self) -> bool:
        """Check if using test gateway."""
        return self.get("gateway-test") == "1"
    
    @property
    def submission_url(self) -> str:
        """Get the submission URL."""
        return self.get("url") or DEFAULT_SUBMISSION_URL


def load_config(config_file: Optional[str] = None) -> CT600Config:
    """Load and validate configuration.
    
    Args:
        config_file: Path to configuration file (optional)
        
    Returns:
        Validated configuration object
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    from .file_operations import load_config_file
    
    if config_file is None:
        config_file = DEFAULT_CONFIG_FILE
    
    try:
        config_data = load_config_file(config_file)
        return CT600Config(config_data)
    except Exception as e:
        if isinstance(e, ConfigurationError):
            e.config_file = config_file
            raise
        else:
            raise ConfigurationError(
                f"Failed to load configuration: {str(e)}",
                config_file=config_file
            )