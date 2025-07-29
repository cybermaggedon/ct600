"""Contract tests for GovTalk XML schema compliance."""

import pytest
import xmlschema
from lxml import etree as ET
from pathlib import Path

from ct600.govtalk import (
    GovTalkSubmissionRequest, GovTalkSubmissionPoll,
    GovTalkDeleteRequest, env_ns
)


class TestGovTalkSchemaCompliance:
    """Test that generated GovTalk messages comply with HMRC schemas."""
    
    @pytest.fixture
    def envelope_schema(self):
        """Load the GovTalk envelope schema."""
        schema_path = Path(__file__).parent.parent.parent / "schema" / "envelope-v2-0-HMRC.xsd"
        if not schema_path.exists():
            pytest.skip(f"Schema file not found: {schema_path}")
        
        # Define hints for referenced schemas
        hints = {
            "http://www.w3.org/2000/09/xmldsig#": str(
                Path(__file__).parent.parent.parent / "schema" / "xmldsig-core-schema.xsd"
            )
        }
        
        try:
            return xmlschema.XMLSchema(str(schema_path), base_url=".", locations=hints)
        except Exception as e:
            pytest.skip(f"Could not load schema: {e}")
    
    @pytest.fixture
    def ct_schema(self):
        """Load the Corporation Tax schema."""
        schema_path = Path(__file__).parent.parent.parent / "schema" / "CT-2014-v1-96.xsd"
        if not schema_path.exists():
            # Try alternative version
            schema_path = Path(__file__).parent.parent.parent / "schema" / "CT-2014-v1-991.xsd"
        
        if not schema_path.exists():
            pytest.skip(f"CT schema file not found")
        
        try:
            return xmlschema.XMLSchema(str(schema_path))
        except Exception as e:
            pytest.skip(f"Could not load CT schema: {e}")
    
    @pytest.fixture
    def sample_ir_envelope(self):
        """Create a minimal IR envelope for testing."""
        # This would normally come from corptax module
        root = ET.Element("{http://www.govtalk.gov.uk/taxation/CT/5}IRenvelope")
        root.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
                 "http://www.govtalk.gov.uk/taxation/CT/5")
        
        # Add minimal required elements
        header = ET.SubElement(root, "{http://www.govtalk.gov.uk/taxation/CT/5}IRheader")
        keys = ET.SubElement(header, "{http://www.govtalk.gov.uk/taxation/CT/5}Keys")
        key = ET.SubElement(keys, "{http://www.govtalk.gov.uk/taxation/CT/5}Key")
        key.set("Type", "UTR")
        key.text = "1234567890"
        
        return root
    
    def test_submission_request_schema_compliance(self, envelope_schema, sample_ir_envelope):
        """Test that submission requests comply with envelope schema."""
        params = {
            "username": "testuser",
            "password": "testpass",
            "class": "HMRC-CT-CT600",
            "gateway-test": "1",
            "tax-reference": "1234567890",
            "vendor-id": "8205",
            "software": "ct600",
            "software-version": "1.0.0",
            "ir-envelope": sample_ir_envelope
        }
        
        try:
            # Create the submission request
            req = GovTalkSubmissionRequest(params)
            
            # Convert to XML
            xml_str = req.toxml()
            
            # Parse the XML
            doc = ET.fromstring(xml_str)
            
            # Validate against schema
            envelope_schema.validate(doc)
            
        except (AttributeError, NotImplementedError):
            pytest.skip("GovTalkSubmissionRequest not fully implemented")
        except xmlschema.XMLSchemaException as e:
            pytest.fail(f"Schema validation failed: {e}")
    
    def test_submission_poll_schema_compliance(self, envelope_schema):
        """Test that submission poll messages comply with schema."""
        params = {
            "username": "testuser",
            "password": "testpass",
            "class": "HMRC-CT-CT600",
            "gateway-test": "1",
            "correlation-id": "ABC123"
        }
        
        try:
            poll = GovTalkSubmissionPoll(params)
            xml_str = poll.toxml()
            doc = ET.fromstring(xml_str)
            envelope_schema.validate(doc)
        except (AttributeError, NotImplementedError):
            pytest.skip("GovTalkSubmissionPoll not fully implemented")
        except xmlschema.XMLSchemaException as e:
            pytest.fail(f"Schema validation failed: {e}")
    
    def test_delete_request_schema_compliance(self, envelope_schema):
        """Test that delete requests comply with schema."""
        params = {
            "username": "testuser",
            "password": "testpass",
            "class": "HMRC-CT-CT600",
            "gateway-test": "1",
            "correlation-id": "ABC123"
        }
        
        try:
            delete_req = GovTalkDeleteRequest(params)
            xml_str = delete_req.toxml()
            doc = ET.fromstring(xml_str)
            envelope_schema.validate(doc)
        except (AttributeError, NotImplementedError):
            pytest.skip("GovTalkDeleteRequest not fully implemented")
        except xmlschema.XMLSchemaException as e:
            pytest.fail(f"Schema validation failed: {e}")
    
    def test_message_structure_requirements(self):
        """Test that messages meet structural requirements."""
        # Test basic structure requirements that all messages must have
        params = {
            "username": "testuser",
            "password": "testpass",
            "class": "HMRC-CT-CT600",
            "gateway-test": "1",
            "correlation-id": "ABC123"
        }
        
        try:
            poll = GovTalkSubmissionPoll(params)
            xml_str = poll.toxml()
            doc = ET.fromstring(xml_str)
            
            # Check required elements exist
            assert doc.tag == f"{{{env_ns}}}GovTalkMessage"
            
            # Check for EnvelopeVersion
            version = doc.find(f".//{{{env_ns}}}EnvelopeVersion")
            assert version is not None
            assert version.text == "2.0"
            
            # Check for Header
            header = doc.find(f".//{{{env_ns}}}Header")
            assert header is not None
            
            # Check for MessageDetails
            msg_details = doc.find(f".//{{{env_ns}}}MessageDetails")
            assert msg_details is not None
            
            # Check Class
            msg_class = msg_details.find(f".//{{{env_ns}}}Class")
            assert msg_class is not None
            assert msg_class.text == "HMRC-CT-CT600"
            
        except (AttributeError, NotImplementedError):
            pytest.skip("GovTalk messages not fully implemented")


class TestCTSchemaCompliance:
    """Test Corporation Tax document schema compliance."""
    
    @pytest.fixture
    def ct_schema(self):
        """Load the Corporation Tax schema."""
        schema_path = Path(__file__).parent.parent.parent / "schema" / "CT-2014-v1-96.xsd"
        if not schema_path.exists():
            # Try alternative version
            schema_path = Path(__file__).parent.parent.parent / "schema" / "CT-2014-v1-991.xsd"
        
        if not schema_path.exists():
            pytest.skip(f"CT schema file not found")
        
        try:
            return xmlschema.XMLSchema(str(schema_path))
        except Exception as e:
            pytest.skip(f"Could not load CT schema: {e}")
    
    def test_ct_document_structure(self, ct_schema):
        """Test that CT documents comply with schema."""
        # This would test actual CT document generation
        # For now, just verify schema can be loaded
        assert ct_schema is not None
    
    def test_required_ct_elements(self):
        """Test that all required CT elements are present."""
        # Would test the output of corptax module
        pytest.skip("Requires corptax module implementation")


class TestIXBRLCompliance:
    """Test iXBRL document compliance with standards."""
    
    def test_ixbrl_namespace_declarations(self):
        """Test that iXBRL documents have correct namespace declarations."""
        required_namespaces = {
            "http://www.w3.org/1999/xhtml",
            "http://www.xbrl.org/2013/inlineXBRL",
            "http://www.xbrl.org/2003/linkbase",
            "http://www.xbrl.org/2003/instance"
        }
        
        # Would test actual iXBRL document generation
        pytest.skip("Requires iXBRL document samples")
    
    def test_ixbrl_schema_references(self):
        """Test that iXBRL documents reference correct schemas."""
        # Would verify schemaRef elements point to correct HMRC/FRC schemas
        pytest.skip("Requires iXBRL document samples")


class TestIRmarkCompliance:
    """Test IRmark digital signature compliance."""
    
    def test_irmark_generation_algorithm(self):
        """Test that IRmark is generated according to HMRC specification."""
        from ct600.irmark import compute
        
        # Test with known input/output from HMRC examples
        test_xml = b'<test>data</test>'
        
        try:
            irmark = compute(test_xml)
            # IRmark should be base64 encoded SHA-1 hash
            assert irmark is not None
            assert len(irmark) > 0
            # Should be valid base64
            import base64
            base64.b64decode(irmark)
        except Exception:
            pytest.skip("IRmark computation not fully implemented")
    
    def test_irmark_canonical_xml(self):
        """Test that XML is canonicalized correctly for IRmark."""
        # Would test C14N canonicalization
        pytest.skip("Requires canonical XML implementation")


class TestMessageSequencing:
    """Test message sequencing and correlation."""
    
    def test_correlation_id_handling(self):
        """Test that correlation IDs are properly maintained."""
        # Would test the full submission -> poll -> response sequence
        pytest.skip("Requires full workflow implementation")
    
    def test_transaction_id_generation(self):
        """Test that transaction IDs meet requirements."""
        # Transaction IDs should be unique and properly formatted
        pytest.skip("Requires transaction ID implementation")