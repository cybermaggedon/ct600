"""Unit tests for constants module."""

import pytest

from ct600.constants import (
    VERSION, DEFAULT_CONFIG_FILE, HMRC_MESSAGE_CLASS, SOFTWARE_NAME,
    SUBMISSION_TIMEOUT_SECONDS, XBRL_LINKBASE_NS, XLINK_NS, INLINE_XBRL_NS,
    FRC_SCHEMA_PATTERN, DPL_SCHEMA_PATTERN, CT_SCHEMA_PATTERN,
    YAML_EXTENSIONS, JSON_EXTENSIONS, XML_EXTENSIONS,
    PAYMENT_ADDRESS_BOX, UTR_BOX, OUTPUT_LINE_LENGTH,
    DESCRIPTION_WRAP_WIDTH, VALUE_DISPLAY_WIDTH, DESCRIPTION_DISPLAY_WIDTH
)


class TestConstants:
    """Test constant values are properly defined."""
    
    def test_version_constant(self):
        """Test version constant is defined."""
        assert isinstance(VERSION, str)
        assert len(VERSION) > 0
        assert VERSION == "1.0.0"
    
    def test_config_constants(self):
        """Test configuration-related constants."""
        assert DEFAULT_CONFIG_FILE == "config.json"
        assert HMRC_MESSAGE_CLASS == "HMRC-CT-CT600"
        assert SOFTWARE_NAME == "ct600"
    
    def test_timeout_constants(self):
        """Test timeout constants."""
        assert isinstance(SUBMISSION_TIMEOUT_SECONDS, int)
        assert SUBMISSION_TIMEOUT_SECONDS > 0
        assert SUBMISSION_TIMEOUT_SECONDS == 120
    
    def test_namespace_constants(self):
        """Test XML namespace constants."""
        assert XBRL_LINKBASE_NS == "http://www.xbrl.org/2003/linkbase"
        assert XLINK_NS == "http://www.w3.org/1999/xlink"
        assert INLINE_XBRL_NS == "http://www.xbrl.org/2013/inlineXBRL"
    
    def test_schema_pattern_constants(self):
        """Test schema validation pattern constants."""
        assert FRC_SCHEMA_PATTERN == "https://xbrl.frc.org.uk/FRS-"
        assert DPL_SCHEMA_PATTERN == "https://xbrl.frc.org.uk/dpl/"
        assert CT_SCHEMA_PATTERN == "http://www.hmrc.gov.uk/schemas/ct/comp/"
    
    def test_file_extension_constants(self):
        """Test file extension constants."""
        assert isinstance(YAML_EXTENSIONS, set)
        assert ".yaml" in YAML_EXTENSIONS
        assert ".yml" in YAML_EXTENSIONS
        
        assert isinstance(JSON_EXTENSIONS, set)
        assert ".json" in JSON_EXTENSIONS
        
        assert isinstance(XML_EXTENSIONS, set)
        assert ".xml" in XML_EXTENSIONS
        assert ".xbrl" in XML_EXTENSIONS
    
    def test_box_number_constants(self):
        """Test CT600 box number constants."""
        assert isinstance(PAYMENT_ADDRESS_BOX, int)
        assert PAYMENT_ADDRESS_BOX == 960
        
        assert isinstance(UTR_BOX, int)
        assert UTR_BOX == 3
    
    def test_formatting_constants(self):
        """Test output formatting constants."""
        assert isinstance(OUTPUT_LINE_LENGTH, int)
        assert OUTPUT_LINE_LENGTH > 0
        assert OUTPUT_LINE_LENGTH == 76
        
        assert isinstance(DESCRIPTION_WRAP_WIDTH, int)
        assert DESCRIPTION_WRAP_WIDTH > 0
        assert DESCRIPTION_WRAP_WIDTH == 75
        
        assert isinstance(VALUE_DISPLAY_WIDTH, int)
        assert VALUE_DISPLAY_WIDTH > 0
        assert VALUE_DISPLAY_WIDTH == 20
        
        assert isinstance(DESCRIPTION_DISPLAY_WIDTH, int)
        assert DESCRIPTION_DISPLAY_WIDTH > 0
        assert DESCRIPTION_DISPLAY_WIDTH == 44
    
    def test_constants_are_immutable_types(self):
        """Test that constants use immutable types where appropriate."""
        # String constants should be strings
        string_constants = [
            VERSION, DEFAULT_CONFIG_FILE, HMRC_MESSAGE_CLASS, SOFTWARE_NAME,
            XBRL_LINKBASE_NS, XLINK_NS, INLINE_XBRL_NS,
            FRC_SCHEMA_PATTERN, DPL_SCHEMA_PATTERN, CT_SCHEMA_PATTERN
        ]
        
        for constant in string_constants:
            assert isinstance(constant, str)
        
        # Integer constants should be integers
        int_constants = [
            SUBMISSION_TIMEOUT_SECONDS, PAYMENT_ADDRESS_BOX, UTR_BOX,
            OUTPUT_LINE_LENGTH, DESCRIPTION_WRAP_WIDTH, 
            VALUE_DISPLAY_WIDTH, DESCRIPTION_DISPLAY_WIDTH
        ]
        
        for constant in int_constants:
            assert isinstance(constant, int)
        
        # Set constants should be sets (frozen sets would be better but sets are fine)
        set_constants = [YAML_EXTENSIONS, JSON_EXTENSIONS, XML_EXTENSIONS]
        
        for constant in set_constants:
            assert isinstance(constant, set)
    
    def test_logical_relationships_between_constants(self):
        """Test logical relationships between related constants."""
        # Description wrap width should be close to but less than output line length
        assert DESCRIPTION_WRAP_WIDTH < OUTPUT_LINE_LENGTH
        
        # Display widths should be reasonable for formatting
        assert DESCRIPTION_DISPLAY_WIDTH + VALUE_DISPLAY_WIDTH < OUTPUT_LINE_LENGTH
        
        # Box numbers should be positive
        assert PAYMENT_ADDRESS_BOX > 0
        assert UTR_BOX > 0
        
        # Timeout should be reasonable (between 1 minute and 10 minutes)
        assert 60 <= SUBMISSION_TIMEOUT_SECONDS <= 600