"""Constants and configuration values for ct600 module."""

# Version information
VERSION = "1.0.0"

# Default configuration
DEFAULT_CONFIG_FILE = "config.json"

# HMRC-specific constants
HMRC_MESSAGE_CLASS = "HMRC-CT-CT600"
SOFTWARE_NAME = "ct600"

# Timeout settings
SUBMISSION_TIMEOUT_SECONDS = 120

# XML namespace constants
XBRL_LINKBASE_NS = "http://www.xbrl.org/2003/linkbase"
XLINK_NS = "http://www.w3.org/1999/xlink"
INLINE_XBRL_NS = "http://www.xbrl.org/2013/inlineXBRL"

# Schema validation patterns
FRC_SCHEMA_PATTERN = "https://xbrl.frc.org.uk/FRS-"
DPL_SCHEMA_PATTERN = "https://xbrl.frc.org.uk/dpl/"
CT_SCHEMA_PATTERN = "http://www.hmrc.gov.uk/schemas/ct/comp/"

# File extensions
YAML_EXTENSIONS = {".yaml", ".yml"}
JSON_EXTENSIONS = {".json"}
XML_EXTENSIONS = {".xml", ".xbrl"}

# Special CT600 box numbers
PAYMENT_ADDRESS_BOX = 960
UTR_BOX = 3

# Output formatting
OUTPUT_LINE_LENGTH = 76
DESCRIPTION_WRAP_WIDTH = 75
VALUE_DISPLAY_WIDTH = 20
DESCRIPTION_DISPLAY_WIDTH = 44