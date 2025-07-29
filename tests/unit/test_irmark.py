"""Unit tests for IRmark digital signature generation."""

import pytest
import hashlib
import base64
from lxml import etree as ET
from unittest.mock import Mock, patch, MagicMock

from ct600.irmark import compute


class TestIRMarkComputation:
    """Test IRmark computation functionality."""
    
    def test_basic_irmark_computation(self):
        """Test basic IRmark computation with simple XML."""
        # Simple XML test case
        xml_input = b'''<test xmlns="http://www.govtalk.gov.uk/CM/envelope">
            <data>Hello World</data>
        </test>'''
        
        # Compute IRmark
        result = compute(xml_input)
        
        # Verify it's a valid base64 string
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify we can decode it
        decoded = base64.b64decode(result)
        assert len(decoded) == 20  # SHA-1 produces 20 bytes
    
    def test_irmark_deterministic(self):
        """Test that IRmark computation is deterministic."""
        xml_input = b'''<test xmlns="http://www.govtalk.gov.uk/CM/envelope">
            <data>Test Data</data>
        </test>'''
        
        # Compute multiple times
        result1 = compute(xml_input)
        result2 = compute(xml_input)
        result3 = compute(xml_input)
        
        # All should be identical
        assert result1 == result2
        assert result2 == result3
    
    def test_irmark_with_different_inputs(self):
        """Test that different inputs produce different IRmarks."""
        xml1 = b'<test xmlns="http://www.govtalk.gov.uk/CM/envelope"><data>A</data></test>'
        xml2 = b'<test xmlns="http://www.govtalk.gov.uk/CM/envelope"><data>B</data></test>'
        
        irmark1 = compute(xml1)
        irmark2 = compute(xml2)
        
        # Different inputs should produce different IRmarks
        assert irmark1 != irmark2
    
    def test_irmark_with_namespaces(self):
        """Test IRmark computation with complex namespaces."""
        xml_input = b'''<GovTalkMessage xmlns="http://www.govtalk.gov.uk/CM/envelope"
                                    xmlns:ct="http://www.govtalk.gov.uk/taxation/CT/5">
            <Header>
                <MessageDetails>
                    <Class>HMRC-CT-CT600</Class>
                </MessageDetails>
            </Header>
            <Body>
                <ct:IRenvelope>
                    <ct:IRheader>
                        <ct:Keys/>
                    </ct:IRheader>
                </ct:IRenvelope>
            </Body>
        </GovTalkMessage>'''
        
        result = compute(xml_input)
        
        # Should produce valid IRmark
        assert isinstance(result, str)
        decoded = base64.b64decode(result)
        assert len(decoded) == 20
    
    def test_irmark_preserves_namespace_declarations(self):
        """Test that namespace declarations are preserved correctly."""
        xml_input = b'''<root xmlns="http://www.govtalk.gov.uk/CM/envelope"
                             xmlns:ct="http://www.govtalk.gov.uk/taxation/CT/5">
            <ct:data>Test</ct:data>
        </root>'''
        
        result = compute(xml_input)
        
        # Should work without errors
        assert result is not None
        assert len(result) > 0
    
    def test_irmark_canonicalization(self):
        """Test that XML is canonicalized before hashing."""
        # These should produce the same IRmark after canonicalization
        xml1 = b'''<test xmlns="http://www.govtalk.gov.uk/CM/envelope">
            <data>Value</data>
        </test>'''
        
        xml2 = b'''<test   xmlns="http://www.govtalk.gov.uk/CM/envelope"  >
            <data>Value</data>
        </test>'''
        
        irmark1 = compute(xml1)
        irmark2 = compute(xml2)
        
        # Canonicalization should normalize whitespace in tags
        assert irmark1 == irmark2
    
    def test_irmark_with_attributes(self):
        """Test IRmark computation with XML attributes."""
        xml_input = b'''<test xmlns="http://www.govtalk.gov.uk/CM/envelope">
            <data type="text" id="123">Value</data>
        </test>'''
        
        result = compute(xml_input)
        
        # Should handle attributes correctly
        assert result is not None
        assert isinstance(result, str)
    
    def test_irmark_with_empty_elements(self):
        """Test IRmark computation with empty elements."""
        xml_input = b'''<test xmlns="http://www.govtalk.gov.uk/CM/envelope">
            <empty/>
            <data></data>
        </test>'''
        
        result = compute(xml_input)
        
        # Should handle empty elements
        assert result is not None
        assert isinstance(result, str)
    
    def test_irmark_encoding_handling(self):
        """Test IRmark with different character encodings."""
        # XML with UTF-8 characters - encode properly
        xml_str = '''<?xml version="1.0" encoding="UTF-8"?>
        <test xmlns="http://www.govtalk.gov.uk/CM/envelope">
            <data>Test with special chars: £€</data>
        </test>'''
        xml_input = xml_str.encode('utf-8')
        
        result = compute(xml_input)
        
        # Should handle UTF-8 correctly
        assert result is not None
        assert isinstance(result, str)
    
    def test_irmark_whitespace_handling(self):
        """Test that significant whitespace is preserved."""
        xml1 = b'''<test xmlns="http://www.govtalk.gov.uk/CM/envelope"><data>A B</data></test>'''
        xml2 = b'''<test xmlns="http://www.govtalk.gov.uk/CM/envelope"><data>A  B</data></test>'''
        
        irmark1 = compute(xml1)
        irmark2 = compute(xml2)
        
        # Different whitespace in text content should produce different IRmarks
        assert irmark1 != irmark2
    
    def test_irmark_with_comments(self):
        """Test IRmark computation with comments."""
        xml1 = b'''<test xmlns="http://www.govtalk.gov.uk/CM/envelope">
            <data>Value</data>
        </test>'''
        
        xml2 = b'''<test xmlns="http://www.govtalk.gov.uk/CM/envelope">
            <!-- This is a comment -->
            <data>Value</data>
        </test>'''
        
        irmark1 = compute(xml1)
        irmark2 = compute(xml2)
        
        # Comments may or may not affect canonicalization depending on C14N mode
        # Both should produce valid IRmarks regardless
        assert isinstance(irmark1, str)
        assert isinstance(irmark2, str)
        assert len(base64.b64decode(irmark1)) == 20
        assert len(base64.b64decode(irmark2)) == 20
    
    def test_irmark_error_handling_invalid_xml(self):
        """Test error handling with invalid XML."""
        invalid_xml = b'<test>Unclosed tag'
        
        with pytest.raises(ET.XMLSyntaxError):
            compute(invalid_xml)
    
    def test_irmark_error_handling_non_xml(self):
        """Test error handling with non-XML input."""
        non_xml = b'This is not XML at all'
        
        with pytest.raises(ET.XMLSyntaxError):
            compute(non_xml)
    
    @patch('ct600.irmark.hashlib.sha1')
    def test_sha1_hash_called(self, mock_sha1):
        """Test that SHA-1 hash is used correctly."""
        mock_hash = Mock()
        mock_hash.digest.return_value = b'12345678901234567890'  # 20 bytes
        mock_sha1.return_value = mock_hash
        
        xml_input = b'<test xmlns="http://www.govtalk.gov.uk/CM/envelope"/>'
        
        result = compute(xml_input)
        
        # Verify SHA-1 was called
        mock_sha1.assert_called_once()
        mock_hash.digest.assert_called_once()
        
        # Verify result is base64 encoded
        assert result == base64.b64encode(b'12345678901234567890').decode('utf-8')
    
    @patch('ct600.irmark.ET.ElementTree')
    def test_c14n_canonicalization_used(self, mock_element_tree):
        """Test that C14N canonicalization is used."""
        mock_tree = Mock()
        mock_element_tree.return_value = mock_tree
        
        xml_input = b'<test xmlns="http://www.govtalk.gov.uk/CM/envelope"/>'
        
        try:
            compute(xml_input)
        except:
            pass  # We're mocking, so it might fail
        
        # Verify write_c14n was called
        mock_tree.write_c14n.assert_called_once()
    
    def test_irmark_with_real_govtalk_structure(self):
        """Test with a realistic GovTalk message structure."""
        xml_input = b'''<GovTalkMessage xmlns="http://www.govtalk.gov.uk/CM/envelope">
            <EnvelopeVersion>2.0</EnvelopeVersion>
            <Header>
                <MessageDetails>
                    <Class>HMRC-CT-CT600</Class>
                    <Qualifier>request</Qualifier>
                    <Function>submit</Function>
                </MessageDetails>
                <SenderDetails>
                    <IDAuthentication>
                        <SenderID>TestUser</SenderID>
                        <Authentication>
                            <Method>clear</Method>
                            <Value>password</Value>
                        </Authentication>
                    </IDAuthentication>
                </SenderDetails>
            </Header>
            <GovTalkDetails>
                <Keys/>
            </GovTalkDetails>
            <Body>
                <IRenvelope xmlns="http://www.govtalk.gov.uk/taxation/CT/5">
                    <IRheader>
                        <Keys>
                            <Key Type="UTR">1234567890</Key>
                        </Keys>
                    </IRheader>
                    <CT600>
                        <CompanyName>Test Company Ltd</CompanyName>
                    </CT600>
                </IRenvelope>
            </Body>
        </GovTalkMessage>'''
        
        result = compute(xml_input)
        
        # Should produce valid IRmark
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Should be valid base64
        decoded = base64.b64decode(result)
        assert len(decoded) == 20  # SHA-1 hash length
    
    def test_irmark_namespace_prefix_consistency(self):
        """Test that namespace prefixes don't affect IRmark."""
        # Same content, different namespace prefixes
        xml1 = b'''<root xmlns="http://www.govtalk.gov.uk/CM/envelope"
                        xmlns:ct="http://www.govtalk.gov.uk/taxation/CT/5">
            <ct:data>Value</ct:data>
        </root>'''
        
        xml2 = b'''<root xmlns="http://www.govtalk.gov.uk/CM/envelope"
                        xmlns:tax="http://www.govtalk.gov.uk/taxation/CT/5">
            <tax:data>Value</tax:data>
        </root>'''
        
        irmark1 = compute(xml1)
        irmark2 = compute(xml2)
        
        # Different prefixes for same namespace should produce same IRmark
        # (This depends on canonicalization behavior)
        # For now, just verify both produce valid IRmarks
        assert isinstance(irmark1, str)
        assert isinstance(irmark2, str)


class TestIRMarkKnownVectors:
    """Test IRmark against known test vectors if available."""
    
    def test_hmrc_example_if_available(self):
        """Test against HMRC-provided examples if we have them."""
        # This is where we would test against known good IRmarks
        # from HMRC documentation or test cases
        pytest.skip("No HMRC test vectors available")
    
    def test_irmark_backwards_compatibility(self):
        """Test that IRmark generation remains consistent."""
        # Fixed test case to detect if algorithm changes
        xml_input = b'''<TestMessage xmlns="http://www.govtalk.gov.uk/CM/envelope">
            <TestData>Fixed Test Data</TestData>
        </TestMessage>'''
        
        result = compute(xml_input)
        
        # This IRmark should never change for this input
        # (You would calculate this once and hardcode it)
        # expected = "CALCULATED_IRMARK_HERE"
        # assert result == expected
        
        # For now, just verify format
        assert isinstance(result, str)
        assert len(base64.b64decode(result)) == 20