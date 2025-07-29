"""Unit tests for file_operations module."""

import pytest
import json
import yaml
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from ct600.file_operations import (
    load_file_bytes, load_computations_file, load_accounts_file,
    load_form_values, load_config_file, load_attachments,
    get_schema_refs, validate_schemas, validate_file_exists
)
from ct600.exceptions import FileOperationError, SchemaValidationError


class TestLoadFileFunctions:
    """Test file loading functions."""
    
    def test_load_file_bytes_success(self):
        """Test successful file loading as bytes."""
        test_content = b"Hello, World!"
        
        with patch("builtins.open", mock_open(read_data=test_content)) as mock_file:
            result = load_file_bytes("test.txt")
            assert result == test_content
            mock_file.assert_called_once_with("test.txt", "rb")
    
    def test_load_file_bytes_file_not_found(self):
        """Test file loading when file doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileOperationError) as exc_info:
                load_file_bytes("nonexistent.txt")
            
            assert "Could not read file" in str(exc_info.value)
            assert exc_info.value.filename == "nonexistent.txt"
            assert isinstance(exc_info.value.original_error, FileNotFoundError)
    
    def test_load_computations_file_success(self):
        """Test successful computations file loading."""
        test_content = b"<computations>test</computations>"
        
        with patch("builtins.open", mock_open(read_data=test_content)):
            result = load_computations_file("comps.xml")
            assert result == test_content
    
    def test_load_computations_file_error(self):
        """Test computations file loading error."""
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with pytest.raises(FileOperationError) as exc_info:
                load_computations_file("comps.xml")
            
            assert "Could not read computations file" in str(exc_info.value)
            assert exc_info.value.filename == "comps.xml"
    
    def test_load_accounts_file_success(self):
        """Test successful accounts file loading."""
        test_content = b"<accounts>test</accounts>"
        
        with patch("builtins.open", mock_open(read_data=test_content)):
            result = load_accounts_file("accounts.xml")
            assert result == test_content
    
    def test_load_accounts_file_error(self):
        """Test accounts file loading error."""
        with patch("builtins.open", side_effect=IOError("I/O error")):
            with pytest.raises(FileOperationError) as exc_info:
                load_accounts_file("accounts.xml")
            
            assert "Could not read accounts file" in str(exc_info.value)
            assert exc_info.value.filename == "accounts.xml"


class TestLoadFormValues:
    """Test form values loading."""
    
    def test_load_form_values_yaml(self):
        """Test loading YAML form values."""
        yaml_content = """
        ct600:
          1: "Test Company"
          2: "12345678"
          3: "1234567890"
        """
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_form_values("values.yaml")
            
            assert isinstance(result, dict)
            assert "ct600" in result
            assert result["ct600"][1] == "Test Company"
            assert result["ct600"][2] == "12345678"
    
    def test_load_form_values_json(self):
        """Test loading JSON form values."""
        json_content = {
            "ct600": {
                "1": "Test Company",
                "2": "12345678",
                "3": "1234567890"
            }
        }
        json_string = json.dumps(json_content)
        
        with patch("builtins.open", mock_open(read_data=json_string)):
            result = load_form_values("values.json")
            
            assert isinstance(result, dict)
            assert "ct600" in result
            assert result["ct600"]["1"] == "Test Company"
    
    def test_load_form_values_unknown_extension_yaml_fallback(self):
        """Test loading with unknown extension falls back to YAML."""
        yaml_content = "test: value"
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            result = load_form_values("values.txt")
            
            assert result == {"test": "value"}
    
    def test_load_form_values_unknown_extension_json_fallback(self):
        """Test loading with unknown extension falls back to JSON after YAML fails."""
        json_content = '{"test": "value"}'
        
        with patch("builtins.open", mock_open(read_data=json_content)):
            with patch("yaml.safe_load", side_effect=yaml.YAMLError("Not YAML")):
                result = load_form_values("values.txt")
                
                assert result == {"test": "value"}
    
    def test_load_form_values_file_error(self):
        """Test form values loading file error."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileOperationError) as exc_info:
                load_form_values("values.yaml")
            
            assert "Could not read form values file" in str(exc_info.value)
            assert exc_info.value.filename == "values.yaml"
    
    def test_load_form_values_parse_error(self):
        """Test form values parsing error."""
        invalid_content = "invalid: yaml: content: {"
        
        with patch("builtins.open", mock_open(read_data=invalid_content)):
            with patch("yaml.safe_load", side_effect=yaml.YAMLError("Parse error")):
                with patch("json.loads", side_effect=json.JSONDecodeError("Parse error", "", 0)):
                    with pytest.raises(FileOperationError) as exc_info:
                        load_form_values("values.yaml")
                    
                    assert "Could not read form values file" in str(exc_info.value)


class TestLoadConfigFile:
    """Test configuration file loading."""
    
    def test_load_config_file_success(self):
        """Test successful config file loading."""
        config_data = {
            "username": "test_user",
            "password": "test_pass",
            "gateway-test": True,
            "vendor-id": "test_vendor",
            "url": "https://example.com"
        }
        json_content = json.dumps(config_data)
        
        with patch("builtins.open", mock_open(read_data=json_content)):
            result = load_config_file("config.json")
            
            assert result == config_data
    
    def test_load_config_file_error(self):
        """Test config file loading error."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileOperationError) as exc_info:
                load_config_file("config.json")
            
            assert "Could not read config file" in str(exc_info.value)
            assert exc_info.value.filename == "config.json"
    
    def test_load_config_file_json_error(self):
        """Test config file JSON parsing error."""
        invalid_json = '{"invalid": json}'
        
        with patch("builtins.open", mock_open(read_data=invalid_json)):
            with patch("json.load", side_effect=json.JSONDecodeError("Parse error", "", 0)):
                with pytest.raises(FileOperationError) as exc_info:
                    load_config_file("config.json")
                
                assert "Could not read config file" in str(exc_info.value)


class TestLoadAttachments:
    """Test attachment loading."""
    
    def test_load_attachments_success(self):
        """Test successful attachment loading."""
        file1_content = b"PDF content"
        file2_content = b"Image content"
        
        def mock_open_side_effect(filename, mode):
            if "file1.pdf" in filename:
                return mock_open(read_data=file1_content)()
            elif "file2.jpg" in filename:
                return mock_open(read_data=file2_content)()
            else:
                raise FileNotFoundError()
        
        with patch("builtins.open", side_effect=mock_open_side_effect):
            result = load_attachments(["/path/to/file1.pdf", "/path/to/file2.jpg"])
            
            assert "file1.pdf" in result
            assert "file2.jpg" in result
            assert result["file1.pdf"] == file1_content
            assert result["file2.jpg"] == file2_content
    
    def test_load_attachments_empty_list(self):
        """Test loading empty attachment list."""
        result = load_attachments([])
        assert result == {}
    
    def test_load_attachments_file_error(self):
        """Test attachment loading file error."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileOperationError) as exc_info:
                load_attachments(["nonexistent.pdf"])
            
            assert "Could not read attachment" in str(exc_info.value)


class TestSchemaOperations:
    """Test schema-related operations."""
    
    @patch("ct600.file_operations.ET.parse")
    def test_get_schema_refs_success(self, mock_parse):
        """Test successful schema reference extraction."""
        # Mock XML document with schema references
        mock_element = type('MockElement', (), {})()
        mock_element.get = lambda attr: "https://xbrl.frc.org.uk/FRS-102/2023-01-01.xsd"
        
        mock_doc = type('MockDoc', (), {})()
        mock_doc.findall = lambda xpath, ns: [mock_element]
        
        mock_parse.return_value = mock_doc
        
        result = get_schema_refs("test.xml")
        
        assert isinstance(result, set)
        assert "https://xbrl.frc.org.uk/FRS-102/2023-01-01.xsd" in result
        mock_parse.assert_called_once_with("test.xml")
    
    @patch("ct600.file_operations.ET.parse")
    def test_get_schema_refs_parse_error(self, mock_parse):
        """Test schema reference extraction with parse error."""
        mock_parse.side_effect = Exception("Parse error")
        
        with pytest.raises(FileOperationError) as exc_info:
            get_schema_refs("invalid.xml")
        
        assert "Could not parse schema references" in str(exc_info.value)
        assert exc_info.value.filename == "invalid.xml"
    
    @patch("ct600.file_operations.get_schema_refs")
    def test_validate_schemas_success(self, mock_get_schema_refs):
        """Test successful schema validation."""
        # Mock schema references for accounts and computations
        def schema_side_effect(filename):
            if "accounts" in filename:
                return {
                    "https://xbrl.frc.org.uk/FRS-102/2023-01-01.xsd",
                    "https://xbrl.frc.org.uk/dpl/2023-01-01.xsd"
                }
            elif "computations" in filename:
                return {
                    "http://www.hmrc.gov.uk/schemas/ct/comp/2023-01-01.xsd",
                    "https://xbrl.frc.org.uk/dpl/2023-01-01.xsd"
                }
            return set()
        
        mock_get_schema_refs.side_effect = schema_side_effect
        
        # Should not raise exception
        validate_schemas("accounts.xml", "computations.xml")
        
        assert mock_get_schema_refs.call_count == 2
    
    @patch("ct600.file_operations.get_schema_refs")
    def test_validate_schemas_missing_dpl(self, mock_get_schema_refs):
        """Test schema validation with missing DPL schema."""
        def schema_side_effect(filename):
            if "accounts" in filename:
                return {"https://xbrl.frc.org.uk/FRS-102/2023-01-01.xsd"}
            elif "computations" in filename:
                return {"http://www.hmrc.gov.uk/schemas/ct/comp/2023-01-01.xsd"}
            return set()
        
        mock_get_schema_refs.side_effect = schema_side_effect
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schemas("accounts.xml", "computations.xml")
        
        assert "DPL schema" in str(exc_info.value)
        assert "DPL schema (not present in either file)" in exc_info.value.missing_schemas
    
    @patch("ct600.file_operations.get_schema_refs")
    def test_validate_schemas_missing_frs(self, mock_get_schema_refs):
        """Test schema validation with missing FRS schema."""
        def schema_side_effect(filename):
            if "accounts" in filename:
                return {"https://xbrl.frc.org.uk/dpl/2023-01-01.xsd"}  # Missing FRS
            elif "computations" in filename:
                return {"http://www.hmrc.gov.uk/schemas/ct/comp/2023-01-01.xsd"}
            return set()
        
        mock_get_schema_refs.side_effect = schema_side_effect
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schemas("accounts.xml", "computations.xml")
        
        assert "FRS schema" in str(exc_info.value)
        assert "FRS schema (should be in company accounts)" in exc_info.value.missing_schemas
    
    @patch("ct600.file_operations.get_schema_refs")
    def test_validate_schemas_missing_ct(self, mock_get_schema_refs):
        """Test schema validation with missing CT schema."""
        def schema_side_effect(filename):
            if "accounts" in filename:
                return {
                    "https://xbrl.frc.org.uk/FRS-102/2023-01-01.xsd",
                    "https://xbrl.frc.org.uk/dpl/2023-01-01.xsd"
                }
            elif "computations" in filename:
                return {"https://xbrl.frc.org.uk/dpl/2023-01-01.xsd"}  # Missing CT
            return set()
        
        mock_get_schema_refs.side_effect = schema_side_effect
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schemas("accounts.xml", "computations.xml")
        
        assert "CT schema" in str(exc_info.value)
        assert "CT schema (should be in computations file)" in exc_info.value.missing_schemas


class TestValidateFileExists:
    """Test file existence validation."""
    
    def test_validate_file_exists_success(self):
        """Test successful file existence validation."""
        with patch("pathlib.Path.exists", return_value=True):
            result = validate_file_exists("test.txt", "test")
            assert result == "test.txt"
    
    def test_validate_file_exists_none_filepath(self):
        """Test file existence validation with None filepath."""
        with pytest.raises(FileOperationError) as exc_info:
            validate_file_exists(None, "test")
        
        assert "Must specify a test file" in str(exc_info.value)
    
    def test_validate_file_exists_file_not_found(self):
        """Test file existence validation when file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileOperationError) as exc_info:
                validate_file_exists("nonexistent.txt", "test")
            
            assert "Test file not found" in str(exc_info.value)
            assert exc_info.value.filename == "nonexistent.txt"


class TestIntegration:
    """Integration tests for file operations."""
    
    def test_load_form_values_with_real_files(self):
        """Test form values loading with real temporary files."""
        yaml_data = {"ct600": {"1": "Test Company", "2": "12345678"}}
        json_data = {"ct600": {"1": "Test Company", "2": "12345678"}}
        
        # Test YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_data, f)
            yaml_file = f.name
        
        try:
            result = load_form_values(yaml_file)
            assert result == yaml_data
        finally:
            os.unlink(yaml_file)
        
        # Test JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_file = f.name
        
        try:
            result = load_form_values(json_file)
            assert result == json_data
        finally:
            os.unlink(json_file)
    
    def test_load_config_with_real_file(self):
        """Test config loading with real temporary file."""
        config_data = {
            "username": "test",
            "password": "pass",
            "gateway-test": True,
            "vendor-id": "vendor",
            "url": "https://example.com"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            result = load_config_file(config_file)
            assert result == config_data
        finally:
            os.unlink(config_file)