"""Test configuration and fixtures."""

import pytest
import asyncio
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import AsyncMock

from ct600.test_service import Api


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Sample test configuration."""
    return {
        "company-type": 0,
        "declaration-name": "Test User",
        "declaration-status": "Director",
        "username": "testuser",
        "password": "testpass",
        "gateway-test": "1",
        "class": "HMRC-CT-CT600-TIL",
        "vendor-id": "8205",
        "software": "ct600",
        "software-version": "1.0.0",
        "url": "http://localhost:8082/",
        "title": "Mr",
        "first-name": "Test",
        "second-name": "User",
        "email": "test@example.com",
        "phone": "447000123456"
    }


@pytest.fixture
def test_form_values():
    """Sample form values for CT600."""
    return {
        "ct600": {
            1: "Test Company Ltd",
            2: "12345678",
            3: "1234567890",
            4: 6,
            30: "2023-01-01",
            35: "2023-12-31",
            40: True,
            50: None,
            55: None,
            470: 100000.00,
            475: 19000.00,
            960: ["123 Test Street", "Test City"]
        }
    }


@pytest.fixture
def temp_config_file(test_config):
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f)
        return f.name


@pytest.fixture
def temp_form_values_file(test_form_values):
    """Create a temporary form values file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_form_values, f)
        return f.name


@pytest.fixture
def sample_ixbrl_computations():
    """Sample iXBRL computations document."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:ct="http://www.hmrc.gov.uk/schemas/ct/comp/2021-10-14">
<head>
    <ix:references>
        <link:schemaRef xlink:type="simple"
                       xlink:href="http://www.hmrc.gov.uk/schemas/ct/comp/2021-10-14/CT-Comp-2021-10-14.xsd"/>
    </ix:references>
</head>
<body>
    <div>
        <p>Turnover: <ix:nonFraction name="ct:Turnover" contextRef="c1" unitRef="GBP" decimals="0">500000</ix:nonFraction></p>
        <p>Tax: <ix:nonFraction name="ct:TaxPayable" contextRef="c1" unitRef="GBP" decimals="0">95000</ix:nonFraction></p>
    </div>
</body>
</html>'''


@pytest.fixture
def sample_ixbrl_accounts():
    """Sample iXBRL accounts document."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:uk-bus="http://xbrl.frc.org.uk/cd/2021-01-01/business">
<head>
    <ix:references>
        <link:schemaRef xlink:type="simple"
                       xlink:href="https://xbrl.frc.org.uk/FRS-102-2021-01-01/FRS-102-2021-01-01.xsd"/>
    </ix:references>
</head>
<body>
    <div>
        <p>Company: <ix:nonNumeric name="uk-bus:EntityCurrentLegalOrRegisteredName" contextRef="c1">Test Company Ltd</ix:nonNumeric></p>
        <p>Turnover: <ix:nonFraction name="uk-bus:Turnover" contextRef="c1" unitRef="GBP" decimals="0">500000</ix:nonFraction></p>
    </div>
</body>
</html>'''


@pytest.fixture
def temp_ixbrl_files(sample_ixbrl_computations, sample_ixbrl_accounts):
    """Create temporary iXBRL files."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as comp_file:
        comp_file.write(sample_ixbrl_computations)
        comp_path = comp_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as acc_file:
        acc_file.write(sample_ixbrl_accounts)
        acc_path = acc_file.name
    
    return comp_path, acc_path


@pytest.fixture
async def test_api_server():
    """Start test API server for integration tests."""
    api = Api(["localhost:8083"])
    
    # Mock the serve_web method to avoid actual server startup
    api.serve_web = AsyncMock()
    
    return api


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_received_dir(tmp_path):
    """Create a temporary received directory for test outputs."""
    received_dir = tmp_path / "received"
    received_dir.mkdir()
    return received_dir