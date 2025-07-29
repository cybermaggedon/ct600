"""Command line interface for ct600 module."""

import argparse
import asyncio
import sys
import textwrap
from typing import Optional, List

from .constants import (
    DEFAULT_CONFIG_FILE, PAYMENT_ADDRESS_BOX, UTR_BOX,
    DESCRIPTION_WRAP_WIDTH, DESCRIPTION_DISPLAY_WIDTH, VALUE_DISPLAY_WIDTH
)
from .config import load_config
from .corptax import InputBundle
from .computations import Computations
from .file_operations import (
    load_computations_file, load_accounts_file, load_form_values,
    load_attachments, validate_schemas, validate_file_exists
)
from .submission import create_submission_request, submit_to_hmrc
from .exceptions import (
    CT600Error, ArgumentValidationError, BundleCreationError
)


class CT600CLI:
    """Command line interface for CT600 operations."""
    
    def __init__(self):
        """Initialize CLI."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser.
        
        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Submission to HMRC Corporation Tax API"
        )
        
        # File arguments
        parser.add_argument(
            '--config', '-c',
            default=DEFAULT_CONFIG_FILE,
            help=f'Configuration file (default: {DEFAULT_CONFIG_FILE})'
        )
        parser.add_argument(
            '--accounts', '-a',
            required=False,
            help='Company accounts iXBRL file'
        )
        parser.add_argument(
            '--computations', '--comps', '-t',
            required=False,
            help='Corporation tax computations iXBRL file'
        )
        parser.add_argument(
            '--form-values', '--ct600', '-f',
            required=False,
            help='CT600 form values YAML file'
        )
        parser.add_argument(
            '--attachment', '-m',
            required=False,
            action='append',
            help='Extra attachment to include with filing e.g. PDF'
        )
        
        # Action arguments (mutually exclusive)
        action_group = parser.add_mutually_exclusive_group(required=True)
        action_group.add_argument(
            '--output-ct', '-p',
            action="store_true",
            help='Just output CT message, no submission'
        )
        action_group.add_argument(
            '--output-values',
            action="store_true",
            help='Just output some data values (debug)'
        )
        action_group.add_argument(
            '--output-form-values',
            action="store_true",
            help='Output CT600 form values from computations'
        )
        action_group.add_argument(
            '--submit',
            action="store_true",
            help='Submit the CT message'
        )
        action_group.add_argument(
            '--data-request',
            action="store_true",
            help='Perform a data request for outstanding items (not implemented)'
        )
        
        return parser
    
    def parse_args(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Parse command line arguments.
        
        Args:
            args: Optional list of arguments (defaults to sys.argv)
            
        Returns:
            Parsed arguments namespace
        """
        return self.parser.parse_args(args)
    
    def create_bundle(self, args: argparse.Namespace) -> InputBundle:
        """Create InputBundle from command line arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Created InputBundle
            
        Raises:
            BundleCreationError: If bundle creation fails
        """
        missing_files = []
        
        # Validate required files for bundle creation
        try:
            accounts_file = validate_file_exists(args.accounts, "accounts")
        except Exception:
            missing_files.append("accounts")
            accounts_file = None
        
        try:
            computations_file = validate_file_exists(args.computations, "computations")
        except Exception:
            missing_files.append("computations")
            computations_file = None
        
        try:
            form_values_file = validate_file_exists(args.form_values, "form-values")
        except Exception:
            missing_files.append("form-values")
            form_values_file = None
        
        try:
            config_file = validate_file_exists(args.config, "config")
        except Exception:
            missing_files.append("config")
            config_file = None
        
        if missing_files:
            raise BundleCreationError(
                f"Required files missing: {', '.join(missing_files)}",
                missing_files=missing_files
            )
        
        try:
            # Validate schemas
            validate_schemas(accounts_file, computations_file)
            
            # Load files
            accounts_data = load_accounts_file(accounts_file)
            computations_data = load_computations_file(computations_file)
            form_values = load_form_values(form_values_file)
            config = load_config(config_file)
            
            # Load attachments if specified
            attachments = {}
            if args.attachment:
                attachments = load_attachments(args.attachment)
            
            return InputBundle(
                computations_data, accounts_data, form_values, 
                config._config, attachments
            )
            
        except Exception as e:
            raise BundleCreationError(f"Failed to create bundle: {str(e)}")
    
    def output_values(self, args: argparse.Namespace) -> None:
        """Output computed values for debugging.
        
        Args:
            args: Parsed command line arguments
        """
        computations_file = validate_file_exists(args.computations, "computations")
        computations_data = load_computations_file(computations_file)
        computations = Computations(computations_data)
        
        for definition in computations.to_values():
            if definition.value is None:
                continue
            
            print(
                f"{definition.box:>4d} {definition.description[:DESCRIPTION_DISPLAY_WIDTH]:<{DESCRIPTION_DISPLAY_WIDTH}}: "
                f"{str(definition.value)[:VALUE_DISPLAY_WIDTH]}"
            )
    
    def output_form_values(self, args: argparse.Namespace) -> None:
        """Output CT600 form values template.
        
        Args:
            args: Parsed command line arguments
        """
        computations_file = validate_file_exists(args.computations, "computations")
        computations_data = load_computations_file(computations_file)
        computations = Computations(computations_data)
        
        print("ct600:")
        
        for definition in computations.to_values():
            print()
            
            # Wrap description text
            help_text = "\n  # ".join(
                textwrap.wrap(definition.description, width=DESCRIPTION_WRAP_WIDTH)
            )
            print(f"  # {help_text}")
            
            # Special case for address field
            if definition.box == PAYMENT_ADDRESS_BOX:
                print(f"  {PAYMENT_ADDRESS_BOX}:")
                print("  - Address line 1")
                print("  - Address line 2")
                continue
            
            # Output box with value or placeholder
            if definition.value is None:
                print(f"  {definition.box}: ")
            else:
                print(f"  {definition.box}: {definition.value}")
        
        print()
    
    def output_ct_message(self, args: argparse.Namespace) -> None:
        """Output CT message XML without submitting.
        
        Args:
            args: Parsed command line arguments
        """
        bundle = self.create_bundle(args)
        config = load_config(args.config)
        
        ct_return = bundle.get_return()
        utr = str(bundle.form_values["ct600"][UTR_BOX])
        
        request = create_submission_request(config, utr, ct_return)
        print(request.toprettyxml())
    
    def submit_ct_message(self, args: argparse.Namespace) -> None:
        """Submit CT message to HMRC.
        
        Args:
            args: Parsed command line arguments
        """
        bundle = self.create_bundle(args)
        config = load_config(args.config)
        
        ct_return = bundle.get_return()
        utr = str(bundle.form_values["ct600"][UTR_BOX])
        
        request = create_submission_request(config, utr, ct_return)
        
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(submit_to_hmrc(config, request))
        except Exception as e:
            print(f"Exception: {str(e)}")
            raise
    
    def data_request(self, args: argparse.Namespace) -> None:
        """Perform data request (not implemented).
        
        Args:
            args: Parsed command line arguments
            
        Raises:
            NotImplementedError: Always, as this feature is not implemented
        """
        raise NotImplementedError("Data request functionality not implemented")
    
    def run(self, args: Optional[List[str]] = None) -> None:
        """Run the CLI with given arguments.
        
        Args:
            args: Optional list of arguments (defaults to sys.argv)
        """
        try:
            parsed_args = self.parse_args(args)
            
            # Dispatch to appropriate action
            if parsed_args.output_values:
                self.output_values(parsed_args)
            elif parsed_args.output_form_values:
                self.output_form_values(parsed_args)
            elif parsed_args.output_ct:
                self.output_ct_message(parsed_args)
            elif parsed_args.submit:
                self.submit_ct_message(parsed_args)
            elif parsed_args.data_request:
                self.data_request(parsed_args)
                
        except CT600Error as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {str(e)}", file=sys.stderr)
            sys.exit(1)


def main(args: Optional[List[str]] = None) -> None:
    """Main CLI entry point.
    
    Args:
        args: Optional list of arguments (defaults to sys.argv)
    """
    cli = CT600CLI()
    cli.run(args)