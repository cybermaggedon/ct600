"""File operations and schema validation for ct600 module."""

import xml.etree.ElementTree as ET
import yaml
import json
from pathlib import Path
from typing import Dict, Set, Any, Optional

from .constants import (
    XBRL_LINKBASE_NS, XLINK_NS, INLINE_XBRL_NS,
    FRC_SCHEMA_PATTERN, DPL_SCHEMA_PATTERN, CT_SCHEMA_PATTERN,
    YAML_EXTENSIONS, JSON_EXTENSIONS
)
from .exceptions import (
    FileOperationError, SchemaValidationError
)


def load_file_bytes(filepath: str) -> bytes:
    """Load a file and return its contents as bytes.
    
    Args:
        filepath: Path to the file to load
        
    Returns:
        File contents as bytes
        
    Raises:
        FileOperationError: If file cannot be read
    """
    try:
        with open(filepath, "rb") as f:
            return f.read()
    except Exception as e:
        raise FileOperationError(
            f"Could not read file: {str(e)}", 
            filename=filepath, 
            original_error=e
        )


def load_computations_file(filepath: str) -> bytes:
    """Load a computations file.
    
    Args:
        filepath: Path to the computations file
        
    Returns:
        File contents as bytes
        
    Raises:
        FileOperationError: If file cannot be read
    """
    try:
        return load_file_bytes(filepath)
    except FileOperationError as e:
        raise FileOperationError(
            f"Could not read computations file: {str(e)}", 
            filename=filepath, 
            original_error=e.original_error
        )


def load_accounts_file(filepath: str) -> bytes:
    """Load an accounts file.
    
    Args:
        filepath: Path to the accounts file
        
    Returns:
        File contents as bytes
        
    Raises:
        FileOperationError: If file cannot be read
    """
    try:
        return load_file_bytes(filepath)
    except FileOperationError as e:
        raise FileOperationError(
            f"Could not read accounts file: {str(e)}", 
            filename=filepath, 
            original_error=e.original_error
        )


def load_form_values(filepath: str) -> Dict[str, Any]:
    """Load form values from YAML or JSON file.
    
    Args:
        filepath: Path to the form values file
        
    Returns:
        Parsed form values as dictionary
        
    Raises:
        FileOperationError: If file cannot be read or parsed
    """
    path = Path(filepath)
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if path.suffix.lower() in YAML_EXTENSIONS:
            return yaml.safe_load(content)
        elif path.suffix.lower() in JSON_EXTENSIONS:
            return json.loads(content)
        else:
            # Try YAML first, then JSON
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError:
                return json.loads(content)
                
    except Exception as e:
        raise FileOperationError(
            f"Could not read form values file: {str(e)}", 
            filename=filepath, 
            original_error=e
        )


def load_config_file(filepath: str) -> Dict[str, Any]:
    """Load configuration from JSON file.
    
    Args:
        filepath: Path to the configuration file
        
    Returns:
        Parsed configuration as dictionary
        
    Raises:
        FileOperationError: If file cannot be read or parsed
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise FileOperationError(
            f"Could not read config file: {str(e)}", 
            filename=filepath, 
            original_error=e
        )


def load_attachments(filepaths: list[str]) -> Dict[str, bytes]:
    """Load attachment files.
    
    Args:
        filepaths: List of paths to attachment files
        
    Returns:
        Dictionary mapping filename to file contents
        
    Raises:
        FileOperationError: If any file cannot be read
    """
    attachments = {}
    
    for filepath in filepaths:
        filename = Path(filepath).name
        try:
            attachments[filename] = load_file_bytes(filepath)
        except FileOperationError as e:
            raise FileOperationError(
                f"Could not read attachment: {str(e)}", 
                filename=filepath, 
                original_error=e.original_error
            )
    
    return attachments


def get_schema_refs(filepath: str) -> Set[str]:
    """Extract schema references from an XBRL file.
    
    Args:
        filepath: Path to the XBRL file
        
    Returns:
        Set of schema reference URLs
        
    Raises:
        FileOperationError: If file cannot be parsed
    """
    try:
        doc = ET.parse(filepath)
        
        schema_refs = set()
        for elt in doc.findall(".//ix:references/link:schemaRef", {
            "link": XBRL_LINKBASE_NS,
            "xlink": XLINK_NS,
            "ix": INLINE_XBRL_NS
        }):
            href = elt.get(f"{{{XLINK_NS}}}href")
            if href:
                schema_refs.add(href)
        
        return schema_refs
        
    except Exception as e:
        raise FileOperationError(
            f"Could not parse schema references: {str(e)}", 
            filename=filepath, 
            original_error=e
        )


def validate_schemas(accounts_file: str, computations_file: str) -> None:
    """Validate that required schemas are present in the files.
    
    Args:
        accounts_file: Path to the accounts file
        computations_file: Path to the computations file
        
    Raises:
        SchemaValidationError: If required schemas are missing
    """
    # Check accounts file schemas
    accounts_schemas = get_schema_refs(accounts_file)
    
    found_frc = any(s.startswith(FRC_SCHEMA_PATTERN) for s in accounts_schemas)
    found_dpl_in_accounts = any(s.startswith(DPL_SCHEMA_PATTERN) for s in accounts_schemas)
    
    # Check computations file schemas
    comps_schemas = get_schema_refs(computations_file)
    
    found_ct = any(s.startswith(CT_SCHEMA_PATTERN) for s in comps_schemas)
    found_dpl_in_comps = any(s.startswith(DPL_SCHEMA_PATTERN) for s in comps_schemas)
    
    # Collect missing schemas
    missing_schemas = []
    
    if not (found_dpl_in_accounts or found_dpl_in_comps):
        missing_schemas.append("DPL schema (not present in either file)")
    
    if not found_frc:
        missing_schemas.append("FRS schema (should be in company accounts)")
    
    if not found_ct:
        missing_schemas.append("CT schema (should be in computations file)")
    
    if missing_schemas:
        error_msg = "Schema validation failed:\n" + "\n".join(f"- {schema}" for schema in missing_schemas)
        raise SchemaValidationError(error_msg, missing_schemas=missing_schemas)


def validate_file_exists(filepath: Optional[str], file_type: str) -> str:
    """Validate that a file exists and return its path.
    
    Args:
        filepath: Path to check (can be None)
        file_type: Description of file type for error messages
        
    Returns:
        The validated filepath
        
    Raises:
        FileOperationError: If file is None or doesn't exist
    """
    if filepath is None:
        raise FileOperationError(f"Must specify a {file_type} file")
    
    if not Path(filepath).exists():
        raise FileOperationError(f"{file_type.title()} file not found", filename=filepath)
    
    return filepath