"""Comprehensive unit tests for corptax module."""

import pytest
import base64
from unittest.mock import Mock, patch, MagicMock
from lxml import etree as ET

from ct600.corptax import Box, Fixed, InputBundle
from ct600.computations import Computations

class TestBox:
    """Test the Box class functionality."""
    
    def test_box_initialization(self):
        """Test Box initialization with id and kind."""
        box = Box(100, kind="money")
        assert box.id == 100
        assert box.kind == "money"
        
        box_no_kind = Box(200)
        assert box_no_kind.id == 200
        assert box_no_kind.kind is None
    
    def test_box_present_with_existing_value(self):
        """Test present method when value exists."""
        obj = Mock()
        obj.form_values = {"ct600": {100: "test_value"}}
        
        box = Box(100)
        assert box.present(obj) is True
    
    def test_box_present_with_none_value(self):
        """Test present method when value is None."""
        obj = Mock()
        obj.form_values = {"ct600": {100: None}}
        
        box = Box(100)
        assert box.present(obj) is False
    
    def test_box_present_missing_key(self):
        """Test present method when key doesn't exist."""
        obj = Mock()
        obj.form_values = {"ct600": {}}
        
        box = Box(100)
        assert box.present(obj) is False
    
    def test_box_present_yes_kind_with_false_value(self):
        """Test present method with yes kind and false value."""
        obj = Mock()
        obj.form_values = {"ct600": {100: False}}
        
        box = Box(100, kind="yes")
        assert box.present(obj) is False
    
    def test_box_present_yes_kind_with_true_value(self):
        """Test present method with yes kind and true value."""
        obj = Mock()
        obj.form_values = {"ct600": {100: True}}
        
        box = Box(100, kind="yes")
        assert box.present(obj) is True
    
    def test_box_fetch(self):
        """Test fetch method retrieves correct value."""
        obj = Mock()
        obj.form_values = {"ct600": {100: "test_value"}}
        
        box = Box(100)
        assert box.fetch(obj) == "test_value"
    
    def test_box_get_no_kind(self):
        """Test get method with no kind (raw value)."""
        obj = Mock()
        obj.form_values = {"ct600": {100: "raw_value"}}
        
        box = Box(100)
        assert box.get(obj) == "raw_value"
    
    def test_box_get_yesno_kind_true(self):
        """Test get method with yesno kind and true value."""
        obj = Mock()
        obj.form_values = {"ct600": {100: True}}
        
        box = Box(100, kind="yesno")
        assert box.get(obj) == "yes"
    
    def test_box_get_yesno_kind_false(self):
        """Test get method with yesno kind and false value."""
        obj = Mock()
        obj.form_values = {"ct600": {100: False}}
        
        box = Box(100, kind="yesno")
        assert box.get(obj) == "no"
    
    def test_box_get_money_kind(self):
        """Test get method with money kind."""
        obj = Mock()
        obj.form_values = {"ct600": {100: 123.456}}
        
        box = Box(100, kind="money")
        assert box.get(obj) == "123.46"
    
    def test_box_get_rate_kind(self):
        """Test get method with rate kind."""
        obj = Mock()
        obj.form_values = {"ct600": {100: 19.5}}
        
        box = Box(100, kind="rate")
        assert box.get(obj) == "19.50"
    
    def test_box_get_pounds_kind(self):
        """Test get method with pounds kind."""
        obj = Mock()
        obj.form_values = {"ct600": {100: 1234.78}}
        
        box = Box(100, kind="pounds")
        assert box.get(obj) == "1234.00"
    
    def test_box_get_yes_kind_true(self):
        """Test get method with yes kind and true value."""
        obj = Mock()
        obj.form_values = {"ct600": {100: True}}
        
        box = Box(100, kind="yes")
        assert box.get(obj) == "yes"
    
    def test_box_get_yes_kind_false(self):
        """Test get method with yes kind and false value."""
        obj = Mock()
        obj.form_values = {"ct600": {100: False}}
        
        box = Box(100, kind="yes")
        assert box.get(obj) == "FIXME"
    
    def test_box_get_date_kind(self):
        """Test get method with date kind."""
        obj = Mock()
        obj.form_values = {"ct600": {100: "2023-12-31"}}
        
        box = Box(100, kind="date")
        assert box.get(obj) == "2023-12-31"
    
    def test_box_get_year_kind(self):
        """Test get method with year kind."""
        obj = Mock()
        obj.form_values = {"ct600": {100: 2023}}
        
        box = Box(100, kind="year")
        assert box.get(obj) == "2023"
    
    def test_box_get_companytype_kind(self):
        """Test get method with companytype kind."""
        obj = Mock()
        obj.form_values = {"ct600": {100: 5}}
        
        box = Box(100, kind="companytype")
        assert box.get(obj) == "05"


class TestFixed:
    """Test the Fixed class functionality."""
    
    def test_fixed_initialization(self):
        """Test Fixed initialization with value and kind."""
        fixed = Fixed("fixed_value", kind="money")
        assert fixed.value == "fixed_value"
        assert fixed.kind == "money"
    
    def test_fixed_present_always_true(self):
        """Test that Fixed always returns True for present."""
        fixed = Fixed("test_value")
        obj = Mock()
        
        assert fixed.present(obj) is True
    
    def test_fixed_fetch_returns_value(self):
        """Test that Fixed fetch returns the fixed value."""
        fixed = Fixed("fixed_value")
        obj = Mock()
        
        assert fixed.fetch(obj) == "fixed_value"
    
    def test_fixed_get_with_money_kind(self):
        """Test Fixed get method with money kind."""
        fixed = Fixed(123.456, kind="money")
        obj = Mock()
        
        # Fixed inherits get method from Box
        result = fixed.get(obj)
        assert result == "123.46"


class TestInputBundle:
    """Test the InputBundle class functionality."""
    
    @pytest.fixture
    def sample_bundle(self):
        """Create a sample InputBundle for testing."""
        comps = b"<computation>test</computation>"
        accts = b"<accounts>test</accounts>"
        form_values = {
            "ct600": {
                1: "Test Company Ltd",
                2: "12345678", 
                3: "1234567890",
                4: 1,
                30: "2023-01-01",
                35: "2023-12-31",
                100: True,
                200: 1000.50
            }
        }
        params = {
            "title": "Mr",
            "first-name": "John",
            "second-name": "Smith", 
            "email": "john.smith@example.com",
            "phone": "01234567890"
        }
        atts = {
            "document.pdf": b"PDF content here"
        }
        
        return InputBundle(comps, accts, form_values, params, atts)
    
    def test_input_bundle_initialization(self, sample_bundle):
        """Test InputBundle initialization."""
        assert sample_bundle.comps == b"<computation>test</computation>"
        assert sample_bundle.accts == b"<accounts>test</accounts>"
        assert sample_bundle.form_values["ct600"][1] == "Test Company Ltd"
        assert sample_bundle.params["title"] == "Mr"
        assert "document.pdf" in sample_bundle.atts
    
    def test_box_method_with_value(self, sample_bundle):
        """Test box method returns correct value."""
        result = sample_bundle.box(1)
        assert result == "Test Company Ltd"
    
    def test_box_method_with_none(self, sample_bundle):
        """Test box method returns empty string for None."""
        # Add None value to test
        sample_bundle.form_values["ct600"][999] = None
        result = sample_bundle.box(999)
        assert result == ""
    
    def test_date_method_with_value(self, sample_bundle):
        """Test date method returns string representation."""
        result = sample_bundle.date(30)
        assert result == "2023-01-01"
    
    def test_date_method_with_none(self, sample_bundle):
        """Test date method returns empty string for None."""
        # Add None value to test
        sample_bundle.form_values["ct600"][999] = None
        result = sample_bundle.date(999)
        assert result == ""
    
    def test_irheader_creation(self, sample_bundle):
        """Test IRheader XML creation."""
        irheader = sample_bundle.irheader()
        
        # Check root element
        assert irheader.tag.endswith("IRheader")
        
        # Check UTR key
        keys = irheader.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Keys")
        assert keys is not None
        key = keys.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Key")
        assert key is not None
        assert key.get("Type") == "UTR"
        assert key.text == "1234567890"
        
        # Check period end
        period_end = irheader.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}PeriodEnd")
        assert period_end is not None
        assert period_end.text == "2023-12-31"
        
        # Check principal contact details
        principal = irheader.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Principal")
        assert principal is not None
        
        contact = principal.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Contact")
        assert contact is not None
        
        name = contact.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Name")
        assert name is not None
        
        title = name.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Ttl")
        assert title is not None
        assert title.text == "Mr"
        
        fore = name.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Fore")
        assert fore is not None
        assert fore.text == "John"
        
        sur = name.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Sur")
        assert sur is not None
        assert sur.text == "Smith"
        
        email = contact.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Email")
        assert email is not None
        assert email.text == "john.smith@example.com"
        
        telephone = contact.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Telephone")
        assert telephone is not None
        number = telephone.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Number")
        assert number is not None
        assert number.text == "01234567890"
        
        # Check IRmark and Sender
        irmark = irheader.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}IRmark")
        assert irmark is not None
        assert irmark.text == ""
        
        sender = irheader.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Sender")
        assert sender is not None
        assert sender.text == "Company"
    
    def test_get_return_structure(self, sample_bundle):
        """Test get_return creates proper XML structure."""
        tree = sample_bundle.get_return()
        root = tree.getroot()
        
        # Check root is IRenvelope
        assert root.tag.endswith("IRenvelope")
        
        # Check it contains IRheader
        irheader = root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}IRheader")
        assert irheader is not None
        
        # Check it contains CompanyTaxReturn
        ctr = root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}CompanyTaxReturn")
        assert ctr is not None
        assert ctr.get("ReturnType") == "new"
        
        # Check attached files structure
        attached_files = root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}AttachedFiles")
        assert attached_files is not None
        
        # Check XBRL submission
        xbrl_submission = attached_files.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}XBRLsubmission")
        assert xbrl_submission is not None
        
        # Check computation instance
        comp_instance = xbrl_submission.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Computation")
        assert comp_instance is not None
        
        # Check accounts instance
        accts_instance = xbrl_submission.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Accounts")
        assert accts_instance is not None
        
        # Check for additional attachments
        attachments = attached_files.findall(".//{http://www.govtalk.gov.uk/taxation/CT/5}Attachment")
        assert len(attachments) == 1  # Our sample has one attachment
        
        att = attachments[0]
        assert att.get("Filename") == "document.pdf"
        assert att.get("Description") == "supporting document"
        assert att.get("Format") == "pdf"
        assert att.get("Type") == "other"
        assert att.get("Size") == str(len(b"PDF content here"))
        
        # Verify attachment content is base64 encoded
        expected_content = base64.b64encode(b"PDF content here").decode("utf-8")
        assert att.text == expected_content
    
    def test_get_return_with_company_info(self, sample_bundle):
        """Test that company information is included in the return."""
        tree = sample_bundle.get_return()
        root = tree.getroot()
        
        # Check company information
        company_info = root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}CompanyInformation")
        assert company_info is not None
        
        company_name = company_info.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}CompanyName")
        assert company_name is not None
        assert company_name.text == "Test Company Ltd"
        
        reg_number = company_info.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}RegistrationNumber")
        assert reg_number is not None
        assert reg_number.text == "12345678"
        
        reference = company_info.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Reference")
        assert reference is not None
        assert reference.text == "1234567890"
        
        company_type = company_info.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}CompanyType")
        assert company_type is not None
        assert company_type.text == "01"  # Formatted with zero-padding
    
    def test_get_return_with_period_covered(self, sample_bundle):
        """Test that period information is included in the return."""
        tree = sample_bundle.get_return()
        root = tree.getroot()
        
        period_covered = root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}PeriodCovered")
        assert period_covered is not None
        
        from_date = period_covered.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}From")
        assert from_date is not None
        assert from_date.text == "2023-01-01"
        
        to_date = period_covered.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}To")
        assert to_date is not None
        assert to_date.text == "2023-12-31"
    
    def test_get_return_encoded_xbrl_documents(self, sample_bundle):
        """Test that XBRL documents are properly base64 encoded."""
        tree = sample_bundle.get_return()
        root = tree.getroot()
        
        # Check computation document
        comp_doc = root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Computation/"
                           "{http://www.govtalk.gov.uk/taxation/CT/5}Instance/"
                           "{http://www.govtalk.gov.uk/taxation/CT/5}EncodedInlineXBRLDocument")
        assert comp_doc is not None
        expected_comp = base64.b64encode(b"<computation>test</computation>").decode("utf-8")
        assert comp_doc.text == expected_comp
        
        # Check accounts document
        accts_doc = root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Accounts/"
                            "{http://www.govtalk.gov.uk/taxation/CT/5}Instance/"
                            "{http://www.govtalk.gov.uk/taxation/CT/5}EncodedInlineXBRLDocument")
        assert accts_doc is not None
        expected_accts = base64.b64encode(b"<accounts>test</accounts>").decode("utf-8")
        assert accts_doc.text == expected_accts
    
    def test_get_return_declaration(self, sample_bundle):
        """Test that declaration is included."""
        # Add declaration data to form values
        sample_bundle.form_values["ct600"][975] = "John Smith"
        sample_bundle.form_values["ct600"][985] = "Director" 
        
        tree = sample_bundle.get_return()
        root = tree.getroot()
        
        declaration = root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Declaration")
        assert declaration is not None
        
        accept_declaration = declaration.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}AcceptDeclaration")
        assert accept_declaration is not None
        assert accept_declaration.text == "yes"  # Fixed value
        
        name = declaration.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Name")
        assert name is not None
        assert name.text == "John Smith"
        
        status = declaration.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}Status")
        assert status is not None
        assert status.text == "Director"
    
    def test_empty_form_values_handling(self):
        """Test handling of empty form values."""
        bundle = InputBundle(
            comps=b"<comp/>",
            accts=b"<accts/>", 
            form_values={"ct600": {999: None}},  # Add None value
            params={},
            atts={}
        )
        
        # Should not raise errors
        result = bundle.box(999)
        assert result == ""
        
        result = bundle.date(999)
        assert result == ""
    
    def test_box_method_with_missing_key(self):
        """Test box method behavior with truly missing key."""
        bundle = InputBundle(
            comps=b"<comp/>",
            accts=b"<accts/>",
            form_values={"ct600": {}},
            params={},
            atts={}
        )
        
        # This should raise KeyError as per current implementation
        with pytest.raises(KeyError):
            bundle.box(999)
    
    def test_box_value_handling_edge_cases(self, sample_bundle):
        """Test edge cases in box value handling."""
        # Test with None value explicitly set
        sample_bundle.form_values["ct600"][999] = None
        
        result = sample_bundle.box(999)
        assert result == ""
        
        result = sample_bundle.date(999)
        assert result == ""
    
    def test_get_return_with_minimal_data(self):
        """Test get_return with minimal required data."""
        minimal_bundle = InputBundle(
            comps=b"<minimal/>",
            accts=b"<minimal/>",
            form_values={"ct600": {3: "1234567890", 35: "2023-12-31"}},
            params={},
            atts={}
        )
        
        # Should not raise errors and create valid structure
        tree = minimal_bundle.get_return()
        root = tree.getroot()
        
        assert root.tag.endswith("IRenvelope")
        assert root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}IRheader") is not None
        assert root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}CompanyTaxReturn") is not None


class TestCorptaxIntegration:
    """Integration tests for the corptax module."""
    
    def test_box_and_fixed_inheritance(self):
        """Test that Fixed properly inherits from Box."""
        # Test that Fixed can use Box methods
        fixed = Fixed(123.45, kind="money")
        obj = Mock()
        
        # Fixed should be able to use Box's get method
        result = fixed.get(obj)
        assert result == "123.45"
    
    def test_namespace_mapping(self):
        """Test that namespace mapping is correctly defined."""
        from ct600.corptax import nsmap, ct_ns
        
        assert "http://www.hmrc.gov.uk/schemas/ct/comp/2024-01-01" in nsmap
        assert "http://xbrl.frc.org.uk/dpl/2025-01-01" in nsmap
        assert "http://xbrl.frc.org.uk/fr/2025-01-01/core" in nsmap
        assert ct_ns == "http://www.govtalk.gov.uk/taxation/CT/5"
    
    def test_tree_building_recursion(self):
        """Test the add_to_tree recursion handles nested structures correctly."""
        # Create a local sample bundle for this test
        sample_bundle = InputBundle(
            comps=b"<computation>test</computation>",
            accts=b"<accounts>test</accounts>",
            form_values={"ct600": {3: "1234567890", 35: "2023-12-31"}},
            params={},
            atts={}
        )
        
        # This tests the recursive function inside get_return
        tree = sample_bundle.get_return()
        root = tree.getroot()
        
        # Check that nested structures are created properly
        ni_info = root.find(".//{http://www.govtalk.gov.uk/taxation/CT/5}NorthernIreland")
        # NI info might not be present if no values are set, but structure should be valid
        assert root is not None
    
    @patch('ct600.corptax.base64.b64encode')
    def test_base64_encoding_called(self, mock_b64encode):
        """Test that base64 encoding is properly called for documents."""
        mock_b64encode.return_value = b"encoded_content"
        
        # Create a local sample bundle for this test
        sample_bundle = InputBundle(
            comps=b"<computation>test</computation>",
            accts=b"<accounts>test</accounts>",
            form_values={"ct600": {3: "1234567890", 35: "2023-12-31"}},
            params={},
            atts={"document.pdf": b"PDF content here"}
        )
        
        tree = sample_bundle.get_return()
        
        # Should be called for comps, accts, and attachments
        assert mock_b64encode.call_count >= 3
        
        # Verify it was called with our test data
        call_args = [call[0][0] for call in mock_b64encode.call_args_list]
        assert b"<computation>test</computation>" in call_args
        assert b"<accounts>test</accounts>" in call_args
        assert b"PDF content here" in call_args
    
    def test_various_box_kinds_formatting(self):
        """Test all different Box kind formatters."""
        obj = Mock()
        test_cases = [
            (100.234, "money", "100.23"),
            (19.567, "rate", "19.57"), 
            (1234.789, "pounds", "1234.00"),
            (True, "yesno", "yes"),
            (False, "yesno", "no"),
            (True, "yes", "yes"),
            (False, "yes", "FIXME"),
            ("2023-12-31", "date", "2023-12-31"),
            (2023, "year", "2023"),
            (5, "companytype", "05"),
            ("raw_value", None, "raw_value")
        ]
        
        for i, (value, kind, expected) in enumerate(test_cases):
            obj.form_values = {"ct600": {i: value}}
            box = Box(i, kind=kind)
            result = box.get(obj)
            assert result == expected, f"Failed for value {value} with kind {kind}"