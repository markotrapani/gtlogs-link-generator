#!/usr/bin/env python3
"""
GT Logs Link Generator
Generates S3 bucket URLs and AWS CLI commands for Redis Support packages.
"""

import argparse
import configparser
import os
import re
import sys
from pathlib import Path


class GTLogsGenerator:
    """Generates GT Logs S3 URLs and AWS CLI commands."""

    BUCKET_BASE = "s3://gt-logs/exa-to-gt"
    CONFIG_FILE = os.path.expanduser("~/.gtlogs-config.ini")

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from config file."""
        config = configparser.ConfigParser()
        if os.path.exists(self.CONFIG_FILE):
            config.read(self.CONFIG_FILE)
        return config

    def _save_config(self, aws_profile):
        """Save AWS profile to config file."""
        if not self.config.has_section('default'):
            self.config.add_section('default')
        self.config.set('default', 'aws_profile', aws_profile)

        with open(self.CONFIG_FILE, 'w') as f:
            self.config.write(f)
        print(f"✓ Default AWS profile saved to {self.CONFIG_FILE}")

    def get_default_aws_profile(self):
        """Get the default AWS profile from config."""
        try:
            return self.config.get('default', 'aws_profile')
        except (configparser.NoSectionError, configparser.NoOptionError):
            return None

    @staticmethod
    def validate_zendesk_id(zd_id):
        """Validate and format Zendesk ID - must be numerical only."""
        zd_id = str(zd_id).strip()

        # If it starts with ZD- or zd-, extract the number part
        if zd_id.upper().startswith('ZD-'):
            zd_number = zd_id[3:]
        else:
            zd_number = zd_id

        # Validate that it's purely numerical
        if not zd_number.isdigit():
            raise ValueError("Invalid Zendesk ID: must be numerical only (e.g., 145980 or ZD-145980)")

        if len(zd_number) == 0:
            raise ValueError("Invalid Zendesk ID: cannot be empty")

        return f"ZD-{zd_number}"

    @staticmethod
    def validate_jira_id(jira_id):
        """Validate and format Jira ID - must be RED-# or MOD-# with numerical suffix."""
        # Check if it matches RED-# or MOD-# format
        jira_id = jira_id.upper().strip()

        # If it's just a number, we need to know the prefix
        if jira_id.isdigit():
            raise ValueError("Jira ID must include prefix (RED- or MOD-)")

        # Add hyphen if missing (e.g., RED172041 -> RED-172041)
        match = re.match(r'^(RED|MOD)(\d+)$', jira_id)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        # Validate full format - must be RED-# or MOD-# with numerical suffix only
        if not re.match(r'^(RED|MOD)-\d+$', jira_id):
            raise ValueError("Invalid Jira ID: must be in format RED-# or MOD-# with numerical suffix (e.g., RED-172041 or MOD-12345)")

        return jira_id

    @staticmethod
    def validate_file_path(file_path):
        """Validate that the file path exists in the filesystem."""
        if not file_path:
            return None

        file_path = str(file_path).strip()
        if not file_path:
            return None

        # Expand user paths like ~/
        expanded_path = os.path.expanduser(file_path)

        # Check if file exists
        if not os.path.exists(expanded_path):
            raise ValueError(f"File does not exist: {file_path}")

        # Check if it's actually a file (not a directory)
        if not os.path.isfile(expanded_path):
            raise ValueError(f"Path is not a file: {file_path}")

        return expanded_path

    def generate_s3_path(self, zd_id, jira_id):
        """Generate the S3 bucket path."""
        zd_formatted = self.validate_zendesk_id(zd_id)
        jira_formatted = self.validate_jira_id(jira_id)
        return f"{self.BUCKET_BASE}/{zd_formatted}-{jira_formatted}/"

    def generate_aws_command(self, zd_id, jira_id, support_package_path=None,
                           aws_profile=None):
        """Generate the full AWS CLI command."""
        s3_base_path = self.generate_s3_path(zd_id, jira_id)

        # Determine AWS profile
        if aws_profile is None:
            aws_profile = self.get_default_aws_profile()

        # Build command
        if support_package_path:
            # Validate file path - will raise ValueError if file doesn't exist
            validated_path = self.validate_file_path(support_package_path)

            package_path = Path(validated_path)
            package_name = package_path.name
            s3_full_path = f"{s3_base_path}{package_name}"

            cmd = f"aws s3 cp {validated_path} {s3_full_path}"
        else:
            s3_full_path = f"{s3_base_path}<support_package_name>"
            cmd = f"aws s3 cp <support_package_path> {s3_full_path}"

        # Add profile if specified
        if aws_profile:
            cmd += f" --profile {aws_profile}"

        return cmd, s3_full_path


def check_exit_input(user_input):
    """Check if user wants to exit (ESC key or exit commands)."""
    if not user_input:
        return False
    # Check for various ESC representations and exit commands
    # ESC can appear as: \x1b (actual ESC), ^[ (terminal display), or escape sequences
    if ('\x1b' in user_input or
        user_input == '^[' or
        user_input.startswith('\x1b[') or  # Arrow keys and other escape sequences
        user_input.lower() in ['exit', 'quit', 'q']):
        print("\n👋 Exiting...\n")
        sys.exit(0)
    return False


def interactive_mode():
    """Run the generator in interactive mode."""
    generator = GTLogsGenerator()

    print("\n" + "="*70)
    print("GT Logs Link Generator - Interactive Mode")
    print("="*70)
    print("\nGenerate S3 URLs and AWS CLI commands for Redis Support packages")
    print("Press Ctrl+C or ESC to exit, or type 'exit' or 'q' at any prompt\n")

    try:
        # Get Zendesk ID
        while True:
            zd_input = input("Enter Zendesk ticket ID (e.g., 145980): ").strip()
            check_exit_input(zd_input)
            if not zd_input:
                print("❌ Zendesk ID is required\n")
                continue
            try:
                zd_formatted = generator.validate_zendesk_id(zd_input)
                print(f"✓ Using: {zd_formatted}\n")
                break
            except ValueError as e:
                print(f"❌ {e}\n")

        # Get Jira ID
        while True:
            jira_input = input("Enter Jira ID (e.g., RED-172041 or MOD-12345): ").strip()
            check_exit_input(jira_input)
            if not jira_input:
                print("❌ Jira ID is required\n")
                continue
            try:
                jira_formatted = generator.validate_jira_id(jira_input)
                print(f"✓ Using: {jira_formatted}\n")
                break
            except ValueError as e:
                print(f"❌ {e}\n")

        # Get support package path (optional)
        while True:
            package_path = input("Enter support package path (optional, press Enter to skip): ").strip()
            check_exit_input(package_path)
            if not package_path:
                package_path = None
                print("✓ Will generate template command\n")
                break
            try:
                validated_path = generator.validate_file_path(package_path)
                print(f"✓ File found: {validated_path}\n")
                package_path = validated_path
                break
            except ValueError as e:
                print(f"❌ {e}")
                retry = input("Try again? (y/n): ").strip().lower()
                check_exit_input(retry)
                if retry not in ['y', 'yes']:
                    package_path = None
                    print("✓ Skipping file path, will generate template command\n")
                    break
                print()

        # Get AWS profile
        default_profile = generator.get_default_aws_profile()
        if default_profile:
            profile_prompt = f"Enter AWS profile (press Enter for default '{default_profile}'): "
        else:
            profile_prompt = "Enter AWS profile (optional, press Enter to skip): "

        aws_profile_input = input(profile_prompt).strip()
        check_exit_input(aws_profile_input)

        if aws_profile_input:
            aws_profile = aws_profile_input
            # Ask if they want to save as default
            save_default = input(f"\nSave '{aws_profile}' as default profile? (y/n): ").strip().lower()
            check_exit_input(save_default)
            if save_default in ['y', 'yes']:
                generator._save_config(aws_profile)
                print()
        elif default_profile:
            aws_profile = default_profile
            print(f"✓ Using default profile: {default_profile}\n")
        else:
            aws_profile = None
            print("✓ No AWS profile specified\n")

        # Generate the command
        cmd, s3_path = generator.generate_aws_command(
            zd_input,
            jira_input,
            package_path,
            aws_profile
        )

        # Display results
        print("="*70)
        print("Generated Output")
        print("="*70)
        print(f"\nS3 Path:\n  {s3_path}")
        print(f"\nAWS CLI Command:\n  {cmd}")
        print("\n" + "="*70 + "\n")

        return 0

    except KeyboardInterrupt:
        print("\n\n👋 Exiting...\n")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}\n", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate GT Logs S3 URLs and AWS CLI commands for Redis Support packages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (no arguments)
  %(prog)s

  # Generate S3 path only
  %(prog)s 145980 RED-172041

  # Generate full AWS CLI command with file path
  %(prog)s 145980 RED-172041 -f /path/to/support_package.tar.gz

  # Use specific AWS profile
  %(prog)s 145980 RED-172041 -f /path/to/support_package.tar.gz -p my-aws-profile

  # Set default AWS profile
  %(prog)s --set-profile my-aws-profile
        """
    )

    parser.add_argument('zendesk_id', nargs='?',
                       help='Zendesk ticket ID (e.g., 145980 or ZD-145980)')
    parser.add_argument('jira_id', nargs='?',
                       help='Jira ticket ID (e.g., RED-172041 or MOD-12345)')
    parser.add_argument('-f', '--file', dest='support_package',
                       help='Path to support package file (optional)')
    parser.add_argument('-p', '--profile', dest='aws_profile',
                       help='AWS profile to use (overrides default)')
    parser.add_argument('--set-profile', dest='set_profile',
                       help='Set default AWS profile')
    parser.add_argument('--show-config', action='store_true',
                       help='Show current configuration')
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Run in interactive mode')

    args = parser.parse_args()

    generator = GTLogsGenerator()

    # Handle config commands
    if args.set_profile:
        generator._save_config(args.set_profile)
        return 0

    if args.show_config:
        default_profile = generator.get_default_aws_profile()
        print(f"Configuration file: {generator.CONFIG_FILE}")
        print(f"Default AWS profile: {default_profile if default_profile else '(not set)'}")
        return 0

    # Interactive mode if no arguments or -i flag
    if args.interactive or (not args.zendesk_id and not args.jira_id):
        return interactive_mode()

    # Require both IDs for generation
    if not args.zendesk_id or not args.jira_id:
        parser.print_help()
        return 1

    try:
        # Generate outputs
        cmd, s3_path = generator.generate_aws_command(
            args.zendesk_id,
            args.jira_id,
            args.support_package,
            args.aws_profile
        )

        # Display results
        print("\n" + "="*70)
        print("GT Logs Link Generator")
        print("="*70)
        print(f"\nS3 Path:\n  {s3_path}")
        print(f"\nAWS CLI Command:\n  {cmd}")
        print("\n" + "="*70)

        # Show helpful info
        if not args.support_package:
            print("\nℹ️  Tip: Use -f to specify the support package file path")

        default_profile = generator.get_default_aws_profile()
        if not args.aws_profile and not default_profile:
            print("ℹ️  Tip: Set a default AWS profile with --set-profile")
        elif default_profile and not args.aws_profile:
            print(f"ℹ️  Using default AWS profile: {default_profile}")

        print()
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
