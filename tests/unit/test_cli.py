"""Unit tests for cli module."""

import pytest
import argparse
import asyncio
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

from ct600.cli import CT600CLI, main
from ct600.exceptions import (
    CT600Error, BundleCreationError, ConfigurationError, FileOperationError
)


class TestCT600CLI:
    """Test CT600CLI class."""
    
    @pytest.fixture
    def cli(self):
        """Create CLI instance."""
        return CT600CLI()
    
    def test_cli_initialization(self, cli):
        """Test CLI initialization."""
        assert cli.parser is not None
        assert isinstance(cli.parser, argparse.ArgumentParser)
    
    def test_parser_configuration(self, cli):
        """Test argument parser configuration."""
        # Test that all expected arguments are configured
        help_text = cli.parser.format_help()
        
        assert "--config" in help_text
        assert "--accounts" in help_text
        assert "--computations" in help_text
        assert "--form-values" in help_text
        assert "--attachment" in help_text
        assert "--output-ct" in help_text
        assert "--output-values" in help_text
        assert "--output-form-values" in help_text
        assert "--submit" in help_text
        assert "--data-request" in help_text
    
    def test_parse_args_output_ct(self, cli):
        """Test parsing arguments for output-ct action."""
        args = cli.parse_args(["--output-ct"])
        
        assert args.output_ct is True
        assert args.config == "config.json"  # Default
        assert args.output_values is False
        assert args.submit is False
    
    def test_parse_args_with_files(self, cli):
        """Test parsing arguments with file specifications."""
        args = cli.parse_args([
            "--config", "test_config.json",
            "--accounts", "test_accounts.xml",
            "--computations", "test_comps.xml",
            "--form-values", "test_values.yaml",
            "--attachment", "file1.pdf",
            "--attachment", "file2.jpg",
            "--submit"
        ])
        
        assert args.config == "test_config.json"
        assert args.accounts == "test_accounts.xml"
        assert args.computations == "test_comps.xml"
        assert args.form_values == "test_values.yaml"
        assert args.attachment == ["file1.pdf", "file2.jpg"]
        assert args.submit is True
    
    def test_parse_args_mutually_exclusive(self, cli):
        """Test that action arguments are mutually exclusive."""
        with pytest.raises(SystemExit):
            cli.parse_args(["--output-ct", "--submit"])
    
    def test_parse_args_no_action(self, cli):
        """Test that at least one action is required."""
        with pytest.raises(SystemExit):
            cli.parse_args(["--config", "test.json"])


class TestCreateBundle:
    """Test create_bundle method."""
    
    @pytest.fixture
    def cli(self):
        """Create CLI instance."""
        return CT600CLI()
    
    @pytest.fixture
    def mock_args(self):
        """Create mock arguments."""
        args = Mock()
        args.accounts = "accounts.xml"
        args.computations = "computations.xml"
        args.form_values = "values.yaml"
        args.config = "config.json"
        args.attachment = ["file1.pdf"]
        return args
    
    @patch('ct600.cli.validate_file_exists')
    @patch('ct600.cli.validate_schemas')
    @patch('ct600.cli.load_accounts_file')
    @patch('ct600.cli.load_computations_file')
    @patch('ct600.cli.load_form_values')
    @patch('ct600.cli.load_config')
    @patch('ct600.cli.load_attachments')
    @patch('ct600.cli.InputBundle')
    def test_create_bundle_success(self, mock_input_bundle, mock_load_attachments,
                                  mock_load_config, mock_load_form_values,
                                  mock_load_computations, mock_load_accounts,
                                  mock_validate_schemas, mock_validate_file_exists,
                                  cli, mock_args):
        """Test successful bundle creation."""
        # Set up mocks
        mock_validate_file_exists.side_effect = lambda path, desc: path
        mock_load_accounts.return_value = b"<accounts>test</accounts>"
        mock_load_computations.return_value = b"<computations>test</computations>"
        mock_load_form_values.return_value = {"ct600": {"1": "Test Company"}}
        mock_config = Mock()
        mock_config._config = {"username": "test"}
        mock_load_config.return_value = mock_config
        mock_load_attachments.return_value = {"file1.pdf": b"PDF content"}
        mock_bundle = Mock()
        mock_input_bundle.return_value = mock_bundle
        
        result = cli.create_bundle(mock_args)
        
        assert result is mock_bundle
        mock_validate_schemas.assert_called_once_with("accounts.xml", "computations.xml")
        mock_input_bundle.assert_called_once()
    
    def test_create_bundle_missing_files(self, cli, mock_args):
        """Test bundle creation with missing files."""
        mock_args.accounts = None
        mock_args.computations = None
        
        with pytest.raises(BundleCreationError) as exc_info:
            cli.create_bundle(mock_args)
        
        assert "accounts" in exc_info.value.missing_files
        assert "computations" in exc_info.value.missing_files
    
    @patch('ct600.cli.validate_file_exists')
    @patch('ct600.cli.validate_schemas')
    def test_create_bundle_schema_validation_error(self, mock_validate_schemas,
                                                  mock_validate_file_exists,
                                                  cli, mock_args):
        """Test bundle creation with schema validation error."""
        mock_validate_file_exists.side_effect = lambda path, desc: path
        mock_validate_schemas.side_effect = Exception("Schema validation failed")
        
        with pytest.raises(BundleCreationError) as exc_info:
            cli.create_bundle(mock_args)
        
        assert "Failed to create bundle" in str(exc_info.value)


class TestOutputMethods:
    """Test output methods."""
    
    @pytest.fixture
    def cli(self):
        """Create CLI instance."""
        return CT600CLI()
    
    @pytest.fixture
    def mock_args(self):
        """Create mock arguments."""
        args = Mock()
        args.computations = "computations.xml"
        return args
    
    @patch('ct600.cli.validate_file_exists')
    @patch('ct600.cli.load_computations_file')
    @patch('ct600.cli.Computations')
    def test_output_values(self, mock_computations_class, mock_load_computations,
                          mock_validate_file_exists, cli, mock_args):
        """Test output_values method."""
        # Set up mocks
        mock_validate_file_exists.return_value = "computations.xml"
        mock_load_computations.return_value = b"<computations>test</computations>"
        
        mock_definition = Mock()
        mock_definition.box = 100
        mock_definition.description = "Test description"
        mock_definition.value = "Test value"
        
        mock_computations = Mock()
        mock_computations.to_values.return_value = [mock_definition]
        mock_computations_class.return_value = mock_computations
        
        with patch('builtins.print') as mock_print:
            cli.output_values(mock_args)
        
        # Should print the formatted output
        mock_print.assert_called()
        call_args = mock_print.call_args[0][0]
        assert "100" in call_args
        assert "Test description" in call_args
        assert "Test value" in call_args
    
    @patch('ct600.cli.validate_file_exists')
    @patch('ct600.cli.load_computations_file')
    @patch('ct600.cli.Computations')
    def test_output_form_values(self, mock_computations_class, mock_load_computations,
                               mock_validate_file_exists, cli, mock_args):
        """Test output_form_values method."""
        # Set up mocks
        mock_validate_file_exists.return_value = "computations.xml"
        mock_load_computations.return_value = b"<computations>test</computations>"
        
        mock_definition = Mock()
        mock_definition.box = 100
        mock_definition.description = "Test description"
        mock_definition.value = "Test value"
        
        mock_computations = Mock()
        mock_computations.to_values.return_value = [mock_definition]
        mock_computations_class.return_value = mock_computations
        
        with patch('builtins.print') as mock_print:
            cli.output_form_values(mock_args)
        
        # Should print YAML-style output
        mock_print.assert_any_call("ct600:")
        mock_print.assert_any_call("  # Test description")
        mock_print.assert_any_call("  100: Test value")
    
    @patch('ct600.cli.validate_file_exists')
    @patch('ct600.cli.load_computations_file')
    @patch('ct600.cli.Computations')
    def test_output_form_values_address_special_case(self, mock_computations_class,
                                                    mock_load_computations,
                                                    mock_validate_file_exists,
                                                    cli, mock_args):
        """Test output_form_values with address special case."""
        mock_validate_file_exists.return_value = "computations.xml"
        mock_load_computations.return_value = b"<computations>test</computations>"
        
        mock_definition = Mock()
        mock_definition.box = 960  # PAYMENT_ADDRESS_BOX
        mock_definition.description = "Payment address"
        mock_definition.value = None
        
        mock_computations = Mock()
        mock_computations.to_values.return_value = [mock_definition]
        mock_computations_class.return_value = mock_computations
        
        with patch('builtins.print') as mock_print:
            cli.output_form_values(mock_args)
        
        # Should print address lines
        mock_print.assert_any_call("  960:")
        mock_print.assert_any_call("  - Address line 1")
        mock_print.assert_any_call("  - Address line 2")


class TestCTMessageMethods:
    """Test CT message methods."""
    
    @pytest.fixture
    def cli(self):
        """Create CLI instance."""
        return CT600CLI()
    
    @pytest.fixture
    def mock_args(self):
        """Create mock arguments."""
        args = Mock()
        args.accounts = "accounts.xml"
        args.computations = "computations.xml"
        args.form_values = "values.yaml"
        args.config = "config.json"
        args.attachment = None
        return args
    
    @patch('ct600.cli.CT600CLI.create_bundle')
    @patch('ct600.cli.load_config')
    @patch('ct600.cli.create_submission_request')
    def test_output_ct_message(self, mock_create_submission_request, mock_load_config,
                              mock_create_bundle, cli, mock_args):
        """Test output_ct_message method."""
        # Set up mocks
        mock_bundle = Mock()
        mock_bundle.form_values = {"ct600": {3: "1234567890"}}
        mock_bundle.get_return.return_value = Mock()
        mock_create_bundle.return_value = mock_bundle
        
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_request = Mock()
        mock_request.toprettyxml.return_value = "<xml>pretty</xml>"
        mock_create_submission_request.return_value = mock_request
        
        with patch('builtins.print') as mock_print:
            cli.output_ct_message(mock_args)
        
        mock_print.assert_called_with("<xml>pretty</xml>")
    
    @patch('ct600.cli.CT600CLI.create_bundle')
    @patch('ct600.cli.load_config')
    @patch('ct600.cli.create_submission_request')
    @patch('ct600.cli.submit_to_hmrc')
    def test_submit_ct_message(self, mock_submit_to_hmrc, mock_create_submission_request,
                              mock_load_config, mock_create_bundle, cli, mock_args):
        """Test submit_ct_message method."""
        # Set up mocks
        mock_bundle = Mock()
        mock_bundle.form_values = {"ct600": {3: "1234567890"}}
        mock_bundle.get_return.return_value = Mock()
        mock_create_bundle.return_value = mock_bundle
        
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_request = Mock()
        mock_create_submission_request.return_value = mock_request
        
        # Mock asyncio operations - submit_to_hmrc is async so we need AsyncMock
        mock_loop = Mock()
        mock_submit_to_hmrc.return_value = AsyncMock()()  # Create an actual coroutine
        
        with patch('asyncio.new_event_loop', return_value=mock_loop):
            cli.submit_ct_message(mock_args)
        
        # The call should pass the actual coroutine, not the AsyncMock
        mock_loop.run_until_complete.assert_called_once()
    
    def test_data_request_not_implemented(self, cli, mock_args):
        """Test data_request method raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            cli.data_request(mock_args)


class TestCLIRun:
    """Test CLI run method."""
    
    @pytest.fixture
    def cli(self):
        """Create CLI instance."""
        return CT600CLI()
    
    def test_run_output_values(self, cli):
        """Test run with output-values action."""
        with patch.object(cli, 'parse_args') as mock_parse:
            with patch.object(cli, 'output_values') as mock_output_values:
                mock_args = Mock()
                mock_args.output_values = True
                mock_args.output_form_values = False
                mock_args.output_ct = False
                mock_args.submit = False
                mock_args.data_request = False
                mock_parse.return_value = mock_args
                
                cli.run(["--output-values"])
                
                mock_output_values.assert_called_once_with(mock_args)
    
    def test_run_output_form_values(self, cli):
        """Test run with output-form-values action."""
        with patch.object(cli, 'parse_args') as mock_parse:
            with patch.object(cli, 'output_form_values') as mock_output_form_values:
                mock_args = Mock()
                mock_args.output_values = False
                mock_args.output_form_values = True
                mock_args.output_ct = False
                mock_args.submit = False
                mock_args.data_request = False
                mock_parse.return_value = mock_args
                
                cli.run(["--output-form-values"])
                
                mock_output_form_values.assert_called_once_with(mock_args)
    
    def test_run_output_ct(self, cli):
        """Test run with output-ct action."""
        with patch.object(cli, 'parse_args') as mock_parse:
            with patch.object(cli, 'output_ct_message') as mock_output_ct:
                mock_args = Mock()
                mock_args.output_values = False
                mock_args.output_form_values = False
                mock_args.output_ct = True
                mock_args.submit = False
                mock_args.data_request = False
                mock_parse.return_value = mock_args
                
                cli.run(["--output-ct"])
                
                mock_output_ct.assert_called_once_with(mock_args)
    
    def test_run_submit(self, cli):
        """Test run with submit action."""
        with patch.object(cli, 'parse_args') as mock_parse:
            with patch.object(cli, 'submit_ct_message') as mock_submit:
                mock_args = Mock()
                mock_args.output_values = False
                mock_args.output_form_values = False
                mock_args.output_ct = False
                mock_args.submit = True
                mock_args.data_request = False
                mock_parse.return_value = mock_args
                
                cli.run(["--submit"])
                
                mock_submit.assert_called_once_with(mock_args)
    
    def test_run_data_request(self, cli):
        """Test run with data-request action."""
        with patch.object(cli, 'parse_args') as mock_parse:
            mock_args = Mock()
            mock_args.output_values = False
            mock_args.output_form_values = False
            mock_args.output_ct = False
            mock_args.submit = False
            mock_args.data_request = True
            mock_parse.return_value = mock_args
            
            with pytest.raises(NotImplementedError):
                cli.run(["--data-request"])
    
    def test_run_ct600_error(self, cli):
        """Test run with CT600Error."""
        with patch.object(cli, 'parse_args') as mock_parse:
            with patch.object(cli, 'output_values') as mock_output_values:
                mock_args = Mock()
                mock_args.output_values = True
                mock_args.output_form_values = False
                mock_args.output_ct = False
                mock_args.submit = False
                mock_args.data_request = False
                mock_parse.return_value = mock_args
                
                mock_output_values.side_effect = CT600Error("Test error")
                
                with patch('sys.exit') as mock_exit:
                    with patch('builtins.print') as mock_print:
                        cli.run(["--output-values"])
                
                mock_print.assert_called_with("Error: Test error", file=sys.stderr)
                mock_exit.assert_called_with(1)
    
    def test_run_keyboard_interrupt(self, cli):
        """Test run with KeyboardInterrupt."""
        with patch.object(cli, 'parse_args') as mock_parse:
            with patch.object(cli, 'output_values') as mock_output_values:
                mock_args = Mock()
                mock_args.output_values = True
                mock_args.output_form_values = False
                mock_args.output_ct = False
                mock_args.submit = False
                mock_args.data_request = False
                mock_parse.return_value = mock_args
                
                mock_output_values.side_effect = KeyboardInterrupt()
                
                with patch('sys.exit') as mock_exit:
                    with patch('builtins.print') as mock_print:
                        cli.run(["--output-values"])
                
                mock_print.assert_called_with("\nOperation cancelled by user", file=sys.stderr)
                mock_exit.assert_called_with(1)
    
    def test_run_unexpected_error(self, cli):
        """Test run with unexpected error."""
        with patch.object(cli, 'parse_args') as mock_parse:
            with patch.object(cli, 'output_values') as mock_output_values:
                mock_args = Mock()
                mock_args.output_values = True
                mock_args.output_form_values = False
                mock_args.output_ct = False
                mock_args.submit = False
                mock_args.data_request = False
                mock_parse.return_value = mock_args
                
                mock_output_values.side_effect = ValueError("Unexpected error")
                
                with patch('sys.exit') as mock_exit:
                    with patch('builtins.print') as mock_print:
                        cli.run(["--output-values"])
                
                mock_print.assert_called_with("Unexpected error: Unexpected error", file=sys.stderr)
                mock_exit.assert_called_with(1)


class TestMainFunction:
    """Test main function."""
    
    def test_main_function(self):
        """Test main function creates CLI and runs it."""
        with patch('ct600.cli.CT600CLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli
            
            main(["--output-values"])
            
            mock_cli_class.assert_called_once()
            mock_cli.run.assert_called_once_with(["--output-values"])
    
    def test_main_function_no_args(self):
        """Test main function with no arguments."""
        with patch('ct600.cli.CT600CLI') as mock_cli_class:
            mock_cli = Mock()
            mock_cli_class.return_value = mock_cli
            
            main()
            
            mock_cli.run.assert_called_once_with(None)


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    def test_argument_validation_integration(self):
        """Test argument validation with real parser."""
        cli = CT600CLI()
        
        # Test valid arguments
        args = cli.parse_args(["--output-ct", "--config", "test.json"])
        assert args.output_ct is True
        assert args.config == "test.json"
        
        # Test short form arguments
        args = cli.parse_args(["-p", "-c", "test.json"])
        assert args.output_ct is True
        assert args.config == "test.json"
        
        # Test attachment arguments
        args = cli.parse_args(["--submit", "-m", "file1.pdf", "-m", "file2.jpg"])
        assert args.submit is True
        assert args.attachment == ["file1.pdf", "file2.jpg"]
    
    def test_error_handling_integration(self):
        """Test error handling with real CLI instance."""
        cli = CT600CLI()
        
        # Mock stdout and stderr for testing
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with patch('sys.exit') as mock_exit:
                    with patch.object(cli, 'output_values', side_effect=FileOperationError("File not found")):
                        cli.run(["--output-values"])
                
                assert "Error: File not found" in mock_stderr.getvalue()
                mock_exit.assert_called_with(1)
    
    def test_bundle_creation_integration(self):
        """Test bundle creation with mocked file operations."""
        cli = CT600CLI()
        
        mock_args = Mock()
        mock_args.accounts = "accounts.xml"
        mock_args.computations = "computations.xml"
        mock_args.form_values = "values.yaml"
        mock_args.config = "config.json"
        mock_args.attachment = None
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('ct600.cli.validate_schemas'):
                with patch('ct600.cli.load_accounts_file', return_value=b"<accounts/>"):
                    with patch('ct600.cli.load_computations_file', return_value=b"<computations/>"):
                        with patch('ct600.cli.load_form_values', return_value={"ct600": {}}):
                            with patch('ct600.cli.load_config') as mock_load_config:
                                with patch('ct600.cli.InputBundle') as mock_input_bundle:
                                    mock_config = Mock()
                                    mock_config._config = {}
                                    mock_load_config.return_value = mock_config
                                    mock_bundle = Mock()
                                    mock_input_bundle.return_value = mock_bundle
                                    
                                    result = cli.create_bundle(mock_args)
                                    
                                    assert result is mock_bundle
                                    mock_input_bundle.assert_called_once()
    
    def test_output_formatting_integration(self):
        """Test output formatting with real data structures."""
        cli = CT600CLI()
        
        # Create a mock definition that resembles real data
        mock_definition = Mock()
        mock_definition.box = 145
        mock_definition.description = "Turnover - total turnover from trade"
        mock_definition.value = 1000000
        
        with patch('ct600.cli.validate_file_exists', return_value="test.xml"):
            with patch('ct600.cli.load_computations_file', return_value=b"<xml/>"):
                with patch('ct600.cli.Computations') as mock_computations_class:
                    mock_computations = Mock()
                    mock_computations.to_values.return_value = [mock_definition]
                    mock_computations_class.return_value = mock_computations
                    
                    with patch('builtins.print') as mock_print:
                        mock_args = Mock()
                        mock_args.computations = "test.xml"
                        
                        cli.output_values(mock_args)
                        
                        # Verify formatting includes box number, description, and value
                        printed_output = mock_print.call_args[0][0]
                        assert "145" in printed_output
                        assert "Turnover - total turnover from trade" in printed_output
                        assert "1000000" in printed_output