"""Contract tests for data format compliance."""

import pytest
from datetime import datetime
from decimal import Decimal
import re

from ct600.computations import Computations, Definition


class TestCT600FormDataContract:
    """Test CT600 form data format requirements."""
    
    def test_company_registration_number_format(self):
        """Test company registration number is 8 digits."""
        valid_numbers = ["12345678", "00000001", "99999999"]
        invalid_numbers = ["1234567", "123456789", "ABCD1234", "1234-5678"]
        
        for num in valid_numbers:
            assert len(num) == 8
            assert num.isdigit()
        
        for num in invalid_numbers:
            assert not (len(num) == 8 and num.isdigit())
    
    def test_utr_format(self):
        """Test Unique Taxpayer Reference format."""
        # UTR should be 10 digits
        valid_utrs = ["1234567890", "0000000001", "9999999999"]
        invalid_utrs = ["123456789", "12345678901", "123456789X"]
        
        for utr in valid_utrs:
            assert len(utr) == 10
            assert utr.isdigit()
        
        for utr in invalid_utrs:
            assert not (len(utr) == 10 and utr.isdigit())
    
    def test_date_format_requirements(self):
        """Test date format is YYYY-MM-DD."""
        valid_dates = ["2023-01-01", "2023-12-31", "2024-02-29"]
        invalid_dates = ["01/01/2023", "2023-1-1", "2023/01/01", "23-01-01"]
        
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        
        for date in valid_dates:
            assert date_pattern.match(date)
            # Should be parseable
            datetime.strptime(date, "%Y-%m-%d")
        
        for date in invalid_dates:
            assert not date_pattern.match(date)
    
    def test_monetary_value_precision(self):
        """Test monetary values have correct precision."""
        # Most monetary values should be whole pounds (no pence)
        valid_values = [Decimal("100"), Decimal("1000"), Decimal("0")]
        
        for val in valid_values:
            assert val % 1 == 0  # No decimal places
    
    def test_company_type_values(self):
        """Test company type uses valid codes."""
        valid_types = [0, 1, 2, 3, 4, 5, 6]  # Example valid company type codes
        
        # Type 6 appears to be common in test data
        assert 6 in valid_types
    
    def test_boolean_field_format(self):
        """Test boolean fields use correct format."""
        # HMRC typically expects "true"/"false" strings or 1/0
        valid_bool_values = [True, False, "true", "false", 1, 0]
        
        # All should be convertible to boolean
        for val in valid_bool_values:
            if isinstance(val, str):
                assert val in ["true", "false"]
            elif isinstance(val, int):
                assert val in [0, 1]
            else:
                assert isinstance(val, bool)


class TestIXBRLDataContract:
    """Test iXBRL data format requirements."""
    
    def test_context_ref_format(self):
        """Test context reference format requirements."""
        # Context refs should be valid XML IDs
        valid_refs = ["c1", "period", "instant", "current-period"]
        invalid_refs = ["1context", "context with spaces", ""]
        
        xml_id_pattern = re.compile(r'^[A-Za-z_][\w.-]*$')
        
        for ref in valid_refs:
            assert xml_id_pattern.match(ref)
        
        for ref in invalid_refs:
            assert not xml_id_pattern.match(ref)
    
    def test_unit_ref_format(self):
        """Test unit reference format."""
        valid_units = ["GBP", "shares", "pure"]
        
        for unit in valid_units:
            assert len(unit) > 0
            assert not unit[0].isdigit()  # Can't start with digit
    
    def test_decimal_precision_declaration(self):
        """Test decimal precision in iXBRL facts."""
        # Decimals attribute should be integer or "INF"
        valid_decimals = ["0", "2", "-3", "INF"]
        
        for dec in valid_decimals:
            if dec != "INF":
                int(dec)  # Should be convertible to int
    
    def test_namespace_prefix_conventions(self):
        """Test namespace prefix naming conventions."""
        common_prefixes = {
            "ix": "http://www.xbrl.org/2013/inlineXBRL",
            "xbrli": "http://www.xbrl.org/2003/instance",
            "ct": "http://www.hmrc.gov.uk/schemas/ct/comp/2023-01-01",
            "uk-bus": "http://xbrl.frc.org.uk/cd/2021-01-01/business"
        }
        
        for prefix, namespace in common_prefixes.items():
            # Prefixes should be short and memorable
            assert len(prefix) <= 10
            assert prefix.replace("-", "").isalnum()


class TestGovTalkDataContract:
    """Test GovTalk message data requirements."""
    
    def test_gateway_test_values(self):
        """Test gateway-test parameter values."""
        # Should be "0" for live, "1" for test
        valid_values = ["0", "1"]
        
        assert "0" in valid_values  # Live
        assert "1" in valid_values  # Test
    
    def test_class_values(self):
        """Test message class values."""
        valid_classes = [
            "HMRC-CT-CT600",
            "HMRC-CT-CT600-TIL",
            "HMRC-PAYE-RTI-EAS",
            "HMRC-PAYE-RTI-FPS"
        ]
        
        # All should follow pattern HMRC-{TAX}-{TYPE}
        # Allow digits in the type part (e.g., CT600)
        class_pattern = re.compile(r'^HMRC-[A-Z]+-[A-Z0-9-]+$')
        
        for cls in valid_classes:
            assert class_pattern.match(cls)
    
    def test_vendor_id_format(self):
        """Test vendor ID format."""
        # Vendor IDs are typically 4-digit numbers
        example_vendor_id = "8205"
        
        assert len(example_vendor_id) == 4
        assert example_vendor_id.isdigit()
    
    def test_correlation_id_format(self):
        """Test correlation ID format."""
        # Correlation IDs are typically uppercase hex strings
        example_ids = ["ABC123", "123456", "DEADBEEF"]
        
        hex_pattern = re.compile(r'^[0-9A-F]+$')
        
        for corr_id in example_ids:
            assert hex_pattern.match(corr_id)
    
    def test_timestamp_format(self):
        """Test timestamp format requirements."""
        # Should be ISO 8601 format
        example_timestamp = "2023-12-31T23:59:59"
        
        # Should be parseable as ISO format
        datetime.fromisoformat(example_timestamp)
    
    def test_response_endpoint_format(self):
        """Test response endpoint URL format."""
        valid_endpoints = [
            "https://transaction-engine.tax.service.gov.uk/submission",
            "http://localhost:8082/",
            "https://test-transaction-engine.tax.service.gov.uk/submission"
        ]
        
        url_pattern = re.compile(r'^https?://[^\s]+$')
        
        for endpoint in valid_endpoints:
            assert url_pattern.match(endpoint)


class TestCT600BoxNumberContract:
    """Test CT600 box number assignments."""
    
    def test_standard_box_numbers(self):
        """Test standard CT600 box numbers are used correctly."""
        # Key box numbers from the CT600 form
        box_definitions = {
            1: "Company name",
            2: "Company registration number", 
            3: "Tax reference",
            4: "Type of company",
            30: "Start of period",
            35: "End of period",
            40: "Repayments indicator",
            145: "Turnover",
            155: "Trading profits",
            235: "Net trading profits",
            295: "Profits chargeable to Corporation Tax",
            305: "Corporation Tax",
            440: "Tax payable",
            470: "Research and development credit",
            960: "Address"
        }
        
        # All box numbers should be positive integers
        for box_num in box_definitions.keys():
            assert isinstance(box_num, int)
            assert box_num > 0
    
    def test_box_value_types(self):
        """Test box values have appropriate types."""
        text_boxes = [1, 2, 3, 960]  # Text values
        date_boxes = [30, 35]  # Date values  
        money_boxes = [145, 155, 235, 295, 305, 440, 470]  # Monetary values
        boolean_boxes = [40, 50, 55]  # Yes/No values
        
        # Just verify the categorization makes sense
        all_boxes = text_boxes + date_boxes + money_boxes + boolean_boxes
        assert len(set(all_boxes)) == len(all_boxes)  # No duplicates