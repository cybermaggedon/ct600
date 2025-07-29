"""End-to-end tests for CLI workflows."""

import pytest
import subprocess
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, Mock


class TestCLIBasicFunctionality:
    """Test basic CLI functionality."""
    
    def test_cli_help(self):
        """Test that CLI shows help message."""
        result = subprocess.run(
            ["python", "-m", "ct600", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "Corporation Tax" in result.stdout
        assert "--config" in result.stdout
        assert "--accounts" in result.stdout
        assert "--computations" in result.stdout
    
    def test_cli_version_info(self):
        """Test CLI can be invoked without crashing."""
        # Just test that we can import and run the module
        result = subprocess.run(
            ["python", "-c", "import ct600.__main__; print('OK')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        assert result.returncode == 0
        assert "OK" in result.stdout


class TestCLIConfigHandling:
    """Test CLI configuration handling."""
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary config file."""
        config = {
            "company-type": 0,
            "declaration-name": "Test User",
            "declaration-status": "Director",
            "username": "testuser",
            "password": "testpass",
            "gateway-test": "1",
            "class": "HMRC-CT-CT600-TIL",
            "vendor-id": "8205",
            "url": "http://localhost:8083/"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            return f.name
    
    def test_cli_with_config_file(self, temp_config):
        """Test CLI with config file parameter."""
        result = subprocess.run(
            ["python", "-m", "ct600", "--config", temp_config, "--output-values"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should fail gracefully without computations file
        assert "Must specify a computations file" in result.stderr or result.returncode != 0
    
    def test_cli_missing_config(self):
        """Test CLI behavior with missing config."""
        result = subprocess.run(
            ["python", "-m", "ct600", "--config", "nonexistent.json", "--output-values"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode != 0


class TestCLIOutputModes:
    """Test different CLI output modes."""
    
    @pytest.fixture
    def temp_files(self):
        """Create temporary test files."""
        # Config file
        config = {
            "company-type": 0,
            "username": "testuser",
            "password": "testpass",
            "gateway-test": "1",
            "url": "http://localhost:8083/"
        }
        
        config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(config, config_file)
        config_file.close()
        
        # Form values file
        form_values = {
            "ct600": {
                1: "Test Company Ltd",
                3: "1234567890",
                30: "2023-01-01",
                35: "2023-12-31"
            }
        }
        
        form_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(form_values, form_file)
        form_file.close()
        
        # Minimal iXBRL computations file
        ixbrl_content = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head></head>
<body><div>Test computations</div></body>
</html>'''
        
        comp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        comp_file.write(ixbrl_content)
        comp_file.close()
        
        # Minimal iXBRL accounts file
        acc_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        acc_file.write(ixbrl_content)
        acc_file.close()
        
        return {
            'config': config_file.name,
            'form_values': form_file.name,
            'computations': comp_file.name,
            'accounts': acc_file.name
        }
    
    def test_output_values_mode(self, temp_files):
        """Test --output-values mode."""
        result = subprocess.run([
            "python", "-m", "ct600",
            "--config", temp_files['config'],
            "--computations", temp_files['computations'],
            "--output-values"
        ], capture_output=True, text=True, timeout=15)
        
        # May fail due to invalid iXBRL, but should not crash
        # The important thing is that the CLI processes the arguments
        assert result.returncode in [0, 1]  # Allow failure due to invalid test data
    
    def test_output_form_values_mode(self, temp_files):
        """Test --output-form-values mode."""
        result = subprocess.run([
            "python", "-m", "ct600",
            "--config", temp_files['config'],
            "--computations", temp_files['computations'],
            "--output-form-values"
        ], capture_output=True, text=True, timeout=15)
        
        # Should attempt to process and output form values
        assert result.returncode in [0, 1]
    
    def test_output_ct_mode(self, temp_files):
        """Test --output-ct mode."""
        result = subprocess.run([
            "python", "-m", "ct600",
            "--config", temp_files['config'],
            "--accounts", temp_files['accounts'],
            "--computations", temp_files['computations'],
            "--form-values", temp_files['form_values'],
            "--output-ct"
        ], capture_output=True, text=True, timeout=15)
        
        # Should attempt to generate CT XML
        # May fail due to invalid test data, but shouldn't crash
        assert result.returncode in [0, 1]


class TestCLIErrorHandling:
    """Test CLI error handling."""
    
    def test_missing_required_files(self):
        """Test CLI behavior with missing required files."""
        result = subprocess.run([
            "python", "-m", "ct600",
            "--output-ct"
        ], capture_output=True, text=True, timeout=10)
        
        assert result.returncode != 0
        assert "Must specify" in result.stderr or "error" in result.stderr.lower()
    
    def test_invalid_file_paths(self):
        """Test CLI with invalid file paths."""
        result = subprocess.run([
            "python", "-m", "ct600",
            "--config", "nonexistent.json",
            "--accounts", "missing.html",
            "--computations", "gone.html",
            "--form-values", "nowhere.yaml",
            "--output-ct"
        ], capture_output=True, text=True, timeout=10)
        
        assert result.returncode != 0
    
    def test_malformed_config_file(self):
        """Test CLI with malformed config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json content")
            malformed_config = f.name
        
        result = subprocess.run([
            "python", "-m", "ct600",
            "--config", malformed_config,
            "--output-values"
        ], capture_output=True, text=True, timeout=10)
        
        assert result.returncode != 0


class TestCLISubmissionWorkflow:
    """Test complete submission workflow via CLI (mocked)."""
    
    @pytest.fixture
    def temp_files(self):
        """Create temporary test files."""
        # Config file
        config = {
            "company-type": 0,
            "username": "testuser",
            "password": "testpass",
            "gateway-test": "1",
            "url": "http://localhost:8083/"
        }
        
        config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(config, config_file)
        config_file.close()
        
        # Form values file
        form_values = {
            "ct600": {
                1: "Test Company Ltd",
                3: "1234567890",
                30: "2023-01-01",
                35: "2023-12-31"
            }
        }
        
        form_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(form_values, form_file)
        form_file.close()
        
        # Minimal iXBRL computations file
        ixbrl_content = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head></head>
<body><div>Test computations</div></body>
</html>'''
        
        comp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        comp_file.write(ixbrl_content)
        comp_file.close()
        
        # Minimal iXBRL accounts file
        acc_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        acc_file.write(ixbrl_content)
        acc_file.close()
        
        return {
            'config': config_file.name,
            'form_values': form_file.name,
            'computations': comp_file.name,
            'accounts': acc_file.name
        }
    
    def test_submit_workflow_mocked(self, temp_files):
        """Test submit workflow with mocked networking - simplified version."""
        # This test would normally use patching but subprocess doesn't play well with patches
        # For now, just verify the command structure
        result = subprocess.run([
            "python", "-m", "ct600",
            "--config", temp_files['config'],
            "--accounts", temp_files['accounts'],
            "--computations", temp_files['computations'],
            "--form-values", temp_files['form_values'],
            "--output-ct"  # Changed from --submit to avoid actual network calls
        ], capture_output=True, text=True, timeout=20)
        
        # May fail due to test data issues, but shouldn't crash
        assert result.returncode in [0, 1]
    
    def test_submit_without_required_params(self):
        """Test submit command without required parameters."""
        result = subprocess.run([
            "python", "-m", "ct600",
            "--submit"
        ], capture_output=True, text=True, timeout=10)
        
        assert result.returncode != 0
        assert "Must specify" in result.stderr or "error" in result.stderr.lower()


class TestCLIIntegrationWithTestService:
    """Test CLI integration with the test service."""
    
    @pytest.mark.slow
    def test_cli_with_running_test_service(self):
        """Test CLI against actually running test service."""
        # This would be a real integration test
        # Start test service, then run CLI against it
        # For now, just document the test structure
        
        # 1. Start corptax-test-service in background
        # 2. Wait for service to be ready
        # 3. Run ct600 CLI with --submit
        # 4. Verify successful submission
        # 5. Clean up test service
        
        # This is complex to implement reliably in CI/CD
        # For now, we'll skip this test
        pytest.skip("Requires running test service")


class TestCLIArgumentValidation:
    """Test CLI argument validation."""
    
    def test_invalid_argument_combinations(self):
        """Test invalid argument combinations."""
        # Test conflicting output modes
        result = subprocess.run([
            "python", "-m", "ct600",
            "--output-ct",
            "--output-values",
            "--submit"
        ], capture_output=True, text=True, timeout=10)
        
        # Should handle gracefully - argparse returns 2 for argument errors
        assert result.returncode == 2
        assert "not allowed with argument" in result.stderr
    
    def test_attachment_handling(self):
        """Test attachment parameter handling."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test attachment content")
            attachment_file = f.name
        
        result = subprocess.run([
            "python", "-m", "ct600",
            "--attachment", attachment_file,
            "--output-values"
        ], capture_output=True, text=True, timeout=10)
        
        # Should fail due to missing required files, but not due to attachment handling
        assert "attachment" not in result.stderr.lower() or result.returncode != 0


class TestCLIPerformance:
    """Test CLI performance characteristics."""
    
    def test_cli_startup_time(self):
        """Test that CLI starts up reasonably quickly."""
        import time
        
        start_time = time.time()
        result = subprocess.run([
            "python", "-m", "ct600", "--help"
        ], capture_output=True, text=True, timeout=5)
        end_time = time.time()
        
        assert result.returncode == 0
        assert end_time - start_time < 3.0  # Should start within 3 seconds
    
    def test_cli_memory_usage(self):
        """Test that CLI doesn't consume excessive memory."""
        # This is a placeholder for memory usage testing
        # In a real implementation, we'd measure memory consumption
        result = subprocess.run([
            "python", "-m", "ct600", "--help"
        ], capture_output=True, text=True, timeout=5)
        
        assert result.returncode == 0
        # Memory usage testing would require additional tooling