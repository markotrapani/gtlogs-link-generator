#!/usr/bin/env python3
"""
GT Logs Helper
Uploads and downloads Redis Support packages to/from S3 buckets.
Generates S3 bucket URLs and AWS CLI commands for Redis Support packages.
"""

VERSION = "1.4.2"

import argparse
import configparser
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, cast

# For immediate keypress detection (ESC without Enter)
if TYPE_CHECKING:
    import termios
    import tty
    IMMEDIATE_INPUT_AVAILABLE: bool
else:
    try:
        import termios
        import tty
        IMMEDIATE_INPUT_AVAILABLE = True
    except ImportError:
        IMMEDIATE_INPUT_AVAILABLE = False
        # Define dummy modules for runtime when not available
        class _DummyModule:
            def __getattr__(self, name: str) -> Any:
                raise ImportError(f"termios/tty not available on this platform")
        termios = _DummyModule()  # type: ignore
        tty = _DummyModule()  # type: ignore


class UserExitException(Exception):
    """Raised when user explicitly exits via ESC or exit commands."""
    pass


class UpdateCheckException(Exception):
    """Raised when Ctrl+U is pressed to trigger update check."""
    pass


def check_for_updates(timeout=5):
    """Check GitHub for latest release version.

    Args:
        timeout: API request timeout in seconds

    Returns:
        dict with 'available', 'latest_version', 'download_url', 'release_notes'
        or None if check fails
    """
    try:
        url = "https://api.github.com/repos/markotrapani/gtlogs-helper/releases/latest"
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')

        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))

        latest_version = data['tag_name'].lstrip('v')  # Remove 'v' prefix if present
        current_version = VERSION

        # Simple version comparison (assumes semantic versioning)
        update_available = latest_version != current_version

        # Get release notes (first 3 lines of body)
        release_notes = []
        if data.get('body'):
            lines = data['body'].strip().split('\n')
            release_notes = [line.strip() for line in lines[:3] if line.strip()]

        # Get download URL for the Python script
        download_url = f"https://raw.githubusercontent.com/markotrapani/gtlogs-helper/{data['tag_name']}/gtlogs-helper.py"

        return {
            'available': update_available,
            'current_version': current_version,
            'latest_version': latest_version,
            'download_url': download_url,
            'release_notes': release_notes
        }
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError) as e:
        # Fail silently - user might be offline
        return None
    except Exception as e:
        # Log unexpected errors but don't crash
        print(f"⚠️  Update check failed: {e}", file=sys.stderr)
        return None


def perform_self_update(download_url, latest_version):
    """Download and install update, with backup and error handling.

    Args:
        download_url: URL to download new version from
        latest_version: Version string for logging

    Returns:
        True if successful, False otherwise
    """
    script_path = os.path.abspath(__file__)
    backup_path = script_path + '.backup'
    temp_path = script_path + '.tmp'

    try:
        print(f"\n📥 Downloading v{latest_version}...")

        # Download new version to temporary file
        req = urllib.request.Request(download_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            new_content = response.read()

        with open(temp_path, 'wb') as f:
            f.write(new_content)

        print(f"💾 Backing up current version to {os.path.basename(backup_path)}")

        # Backup current version
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(script_path, backup_path)

        # Install new version
        os.rename(temp_path, script_path)

        # Make executable
        os.chmod(script_path, 0o755)

        print(f"✅ Update successful! (v{latest_version})")
        print("Please restart the script to use the new version.\n")
        return True

    except urllib.error.HTTPError as e:
        print(f"❌ Download failed: HTTP {e.code} {e.reason}", file=sys.stderr)
        rollback_update(script_path, backup_path, temp_path)
        return False
    except urllib.error.URLError as e:
        print(f"❌ Download failed: {e.reason}", file=sys.stderr)
        rollback_update(script_path, backup_path, temp_path)
        return False
    except OSError as e:
        print(f"❌ File operation failed: {e}", file=sys.stderr)
        rollback_update(script_path, backup_path, temp_path)
        return False
    except Exception as e:
        print(f"❌ Unexpected error during update: {e}", file=sys.stderr)
        rollback_update(script_path, backup_path, temp_path)
        return False


def rollback_update(script_path, backup_path, temp_path):
    """Rollback failed update by restoring backup.

    Args:
        script_path: Path to the script file
        backup_path: Path to backup file
        temp_path: Path to temporary download file
    """
    try:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Restore backup if we created one
        if os.path.exists(backup_path) and not os.path.exists(script_path):
            os.rename(backup_path, script_path)
            print("✓ Rolled back to previous version", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Rollback failed: {e}", file=sys.stderr)
        print(f"⚠️  Manual recovery: restore from {backup_path}", file=sys.stderr)


def prompt_for_update(update_info):
    """Prompt user to install update.

    Args:
        update_info: Dictionary from check_for_updates()

    Returns:
        True if user wants to update, False otherwise
    """
    print(f"\n📦 Update available: v{update_info['current_version']} → v{update_info['latest_version']}")

    if update_info['release_notes']:
        print("   Changes:")
        for note in update_info['release_notes']:
            print(f"   - {note}")

    response = input_with_esc_detection("\nUpdate now? (y/n): ").strip().lower()

    if response == 'y':
        return perform_self_update(update_info['download_url'], update_info['latest_version'])
    else:
        print("\nUpdate cancelled.\n")
        return False


class GTLogsHelper:
    """Helps with GT Logs S3 uploads, downloads, and URL generation."""

    BUCKET_BASE = "s3://gt-logs/exa-to-gt"
    CONFIG_FILE = os.path.expanduser("~/.gtlogs-config.ini")
    HISTORY_FILE = os.path.expanduser("~/.gtlogs-history.json")
    MAX_HISTORY_ENTRIES = 20

    def __init__(self):
        self.config = self._load_config()
        self.history = self._load_history()

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

    def _load_history(self):
        """Load input history from history file."""
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, start fresh
                pass

        # Default empty history structure
        return {
            'zendesk_id': [],
            'jira_id': [],
            'file_path': [],
            'aws_profile': []
        }

    def _save_history(self):
        """Save input history to history file."""
        try:
            with open(self.HISTORY_FILE, 'w') as f:
                json.dump(self.history, f, indent=2)
        except IOError as e:
            # Non-critical error, just warn
            print(f"⚠️  Warning: Could not save history: {e}")

    def add_to_history(self, field_name, value):
        """Add a validated value to history for a specific field.

        Args:
            field_name: One of 'zendesk_id', 'jira_id', 'file_path', 'aws_profile'
            value: The validated value to add
        """
        if not value or field_name not in self.history:
            return

        # Remove if already exists (to avoid duplicates)
        if value in self.history[field_name]:
            self.history[field_name].remove(value)

        # Add to front of list (most recent first)
        self.history[field_name].insert(0, value)

        # Limit history size
        self.history[field_name] = self.history[field_name][:self.MAX_HISTORY_ENTRIES]

    def get_history(self, field_name):
        """Get history list for a specific field.

        Args:
            field_name: One of 'zendesk_id', 'jira_id', 'file_path', 'aws_profile'

        Returns:
            List of historical values (most recent first)
        """
        return self.history.get(field_name, [])

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
    def validate_file_path(file_path: str | None) -> str | None:
        """Validate that the file path exists in the filesystem.

        Returns:
            str: The expanded file path if valid
            None: If file_path is empty or None

        Raises:
            ValueError: If the file doesn't exist or isn't a file
        """
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

    def generate_s3_path(self, zd_id, jira_id=None):
        """Generate the S3 bucket path.

        If jira_id is provided: s3://gt-logs/exa-to-gt/ZD-#-JIRA-#/
        If jira_id is None: s3://gt-logs/zendesk-tickets/ZD-#/
        """
        zd_formatted = self.validate_zendesk_id(zd_id)

        if jira_id:
            jira_formatted = self.validate_jira_id(jira_id)
            return f"{self.BUCKET_BASE}/{zd_formatted}-{jira_formatted}/"
        else:
            # ZD-only path for tickets without Jira
            return f"s3://gt-logs/zendesk-tickets/{zd_formatted}/"

    def generate_aws_command(self, zd_id, jira_id=None, support_package_path=None,
                           aws_profile=None):
        """Generate the full AWS CLI command."""
        s3_base_path = self.generate_s3_path(zd_id, jira_id)

        # Determine AWS profile with fallback to gt-logs
        if aws_profile is None:
            aws_profile = self.get_default_aws_profile() or "gt-logs"

        # Build command
        if support_package_path:
            # Validate file path - will raise ValueError if file doesn't exist
            validated_path = self.validate_file_path(support_package_path)

            # Type narrowing: validate_file_path returns str when input is non-empty
            # Use cast to tell type checker the value is definitely str here
            assert validated_path is not None, "validate_file_path should not return None for non-empty input"
            validated_path = cast(str, validated_path)

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

    @staticmethod
    def check_aws_authentication(aws_profile):
        """Check if AWS profile is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        try:
            cmd = ['aws', 'sts', 'get-caller-identity']
            if aws_profile:
                cmd.extend(['--profile', aws_profile])

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            # Check if profile doesn't exist
            if result.returncode != 0 and b"could not be found" in result.stderr.lower():
                print(f"⚠️  AWS profile '{aws_profile}' does not exist.")
                print(f"   Please configure it with: aws configure sso --profile {aws_profile}")
                print(f"   Or use a different profile with -p flag")

            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("⚠️  Timeout while checking AWS authentication")
            return False
        except FileNotFoundError:
            print("❌ AWS CLI not found. Please install AWS CLI first.")
            return False

    @staticmethod
    def aws_sso_login(aws_profile):
        """Execute AWS SSO login for the specified profile.

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\n🔐 Authenticating with AWS SSO (profile: {aws_profile})...")
            cmd = ['aws', 'sso', 'login', '--profile', aws_profile]

            result = subprocess.run(cmd, check=False)

            if result.returncode == 0:
                print("✓ AWS SSO authentication successful\n")
                return True
            else:
                print("❌ AWS SSO authentication failed\n")
                return False
        except FileNotFoundError:
            print("❌ AWS CLI not found. Please install AWS CLI first.\n")
            return False
        except Exception as e:
            print(f"❌ Error during AWS SSO login: {e}\n")
            return False

    @staticmethod
    def execute_s3_upload(aws_command):
        """Execute the AWS S3 cp command.

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\n📤 Uploading to S3...")
            print(f"   Running: {aws_command}\n")

            result = subprocess.run(
                aws_command,
                shell=True,
                check=False
            )

            if result.returncode == 0:
                print("\n✅ Upload successful!\n")
                return True
            else:
                print(f"\n❌ Upload failed with exit code {result.returncode}\n")
                return False
        except Exception as e:
            print(f"❌ Error during upload: {e}\n")
            return False

    def execute_batch_upload(self, file_paths, zd_id, jira_id, aws_profile):
        """Execute batch upload of multiple files to the same S3 destination.

        Args:
            file_paths: List of file paths to upload
            zd_id: Zendesk ticket ID (formatted)
            jira_id: Jira ticket ID (formatted, can be None)
            aws_profile: AWS profile to use

        Returns:
            tuple: (success_count, failure_count, results)
        """
        total_files = len(file_paths)
        success_count = 0
        failure_count = 0
        results = []

        print(f"\n{'='*70}")
        print(f"Batch Upload: {total_files} file(s)")
        print(f"{'='*70}\n")

        # Generate S3 path (same for all files)
        s3_path = self.generate_s3_path(zd_id, jira_id)
        print(f"S3 Destination: {s3_path}\n")

        for i, file_path in enumerate(file_paths, 1):
            filename = os.path.basename(file_path)
            print(f"[{i}/{total_files}] Uploading: {filename}")
            print(f"            From: {file_path}")

            # Generate command for this specific file
            cmd, _ = self.generate_aws_command(zd_id, jira_id, file_path, aws_profile)

            # Execute upload
            success = self.execute_s3_upload(cmd)

            if success:
                success_count += 1
                results.append(('success', filename))
            else:
                failure_count += 1
                results.append(('failure', filename))

            # Add separator between uploads (except after last one)
            if i < total_files:
                print(f"{'-'*70}\n")

        # Print summary
        print(f"{'='*70}")
        print(f"Batch Upload Summary")
        print(f"{'='*70}")
        print(f"✅ Successful: {success_count}/{total_files}")
        print(f"❌ Failed: {failure_count}/{total_files}")

        if failure_count > 0:
            print(f"\nFailed files:")
            for status, filename in results:
                if status == 'failure':
                    print(f"  - {filename}")

        print(f"{'='*70}\n")

        return success_count, failure_count, results

    # ========== DOWNLOAD FUNCTIONALITY ==========

    @staticmethod
    def parse_s3_path(s3_path):
        """Parse an S3 path or partial path to extract bucket and key.

        Args:
            s3_path: Full S3 path or partial path (e.g., ZD-145980)

        Returns:
            tuple: (bucket, key) or (None, None) if invalid
        """
        # Handle full S3 paths
        if s3_path.startswith("s3://"):
            parts = s3_path[5:].split("/", 1)
            if len(parts) >= 1:
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ""
                return bucket, key

        # Handle partial paths (ZD-only or ZD+Jira)
        # Try to validate as Zendesk ID
        try:
            zd_id = GTLogsHelper.validate_zendesk_id(s3_path)
            # Check if it contains Jira ID too
            if "-RED-" in s3_path.upper() or "-MOD-" in s3_path.upper():
                # Extract Jira part
                jira_match = re.search(r'(RED|MOD)-\d+', s3_path.upper())
                if jira_match:
                    jira_id = jira_match.group()
                    # ZD+Jira path
                    return "gt-logs", f"exa-to-gt/{zd_id}-{jira_id}/"
            # ZD-only path
            return "gt-logs", f"zendesk-tickets/{zd_id}/"
        except:
            pass

        # Try to parse as direct bucket/key format
        if "/" in s3_path and not s3_path.startswith("/"):
            parts = s3_path.split("/", 1)
            return parts[0], parts[1]

        return None, None

    def list_s3_files(self, bucket, prefix, aws_profile="gt-logs"):
        """List files in an S3 bucket with given prefix.

        Args:
            bucket: S3 bucket name
            prefix: S3 key prefix
            aws_profile: AWS profile to use

        Returns:
            list: List of file keys or empty list if error
        """
        cmd = [
            "aws", "s3", "ls",
            f"s3://{bucket}/{prefix}",
            "--profile", aws_profile,
            "--recursive"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"❌ Error listing files: {result.stderr}")
                return []

            # Parse the output to get file paths
            files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    # AWS S3 ls format: "2024-01-15 10:30:45  12345678  path/to/file.tar.gz"
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        file_key = parts[3]
                        files.append(file_key)

            return files

        except subprocess.TimeoutExpired:
            print("❌ Timeout while listing S3 files")
            return []
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []

    def download_from_s3(self, bucket, key, local_path=None, aws_profile="gt-logs"):
        """Download a file from S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key
            local_path: Local destination path (optional, defaults to current directory)
            aws_profile: AWS profile to use

        Returns:
            bool: True if successful, False otherwise
        """
        if local_path is None:
            # Use current directory with the filename from the key
            local_path = os.path.basename(key)

        # Ensure local directory exists
        local_dir = os.path.dirname(local_path)
        if local_dir and not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        # Build AWS CLI command
        cmd = f'aws s3 cp "s3://{bucket}/{key}" "{local_path}" --profile {aws_profile}'

        try:
            print(f"\n📥 Downloading from S3...")
            print(f"   Source: s3://{bucket}/{key}")
            print(f"   Destination: {local_path}")
            print(f"   Running: {cmd}\n")

            result = subprocess.run(
                cmd,
                shell=True,
                check=False
            )

            if result.returncode == 0:
                print(f"\n✅ Download successful! File saved to: {local_path}\n")
                return True
            else:
                print(f"\n❌ Download failed with exit code {result.returncode}\n")
                return False

        except Exception as e:
            print(f"❌ Error during download: {e}\n")
            return False

    def generate_download_command(self, s3_path, local_path=None, aws_profile="gt-logs"):
        """Generate AWS CLI download command.

        Args:
            s3_path: S3 path to download from
            local_path: Local destination path (optional)
            aws_profile: AWS profile to use

        Returns:
            str: AWS CLI command or None if invalid path
        """
        bucket, key = self.parse_s3_path(s3_path)
        if not bucket or not key:
            return None

        if local_path is None:
            local_path = "."

        # Check if downloading a directory (ends with /)
        if key.endswith("/"):
            return f'aws s3 sync "s3://{bucket}/{key}" "{local_path}" --profile {aws_profile}'
        else:
            return f'aws s3 cp "s3://{bucket}/{key}" "{local_path}" --profile {aws_profile}'


def getch_timeout(timeout=None, fd=None, restore_settings=True):
    """Read a single character from stdin without waiting for Enter.

    Args:
        timeout: Optional timeout in seconds. Returns None if no input within timeout.
        fd: File descriptor (if already in raw mode, reuse it)
        restore_settings: Whether to restore terminal settings after read
    """
    if not IMMEDIATE_INPUT_AVAILABLE:
        return None

    try:
        if fd is None:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)
            should_restore = True
        else:
            old_settings = None
            should_restore = restore_settings

        try:
            if timeout is not None:
                import select
                ready = select.select([sys.stdin], [], [], timeout)
                if not ready[0]:
                    return None  # Timeout

            ch = sys.stdin.read(1)
            return ch
        finally:
            if should_restore and old_settings is not None:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except (OSError, termios.error):
        # Fall back if terminal operations not supported
        return None


def getch():
    """Read a single character from stdin without waiting for Enter."""
    return getch_timeout(timeout=None)


def input_with_esc_detection(prompt: str, history_list: Optional[list] = None) -> str:
    """Enhanced input that detects ESC key immediately without requiring Enter.

    Args:
        prompt: The input prompt to display
        history_list: Optional list of historical values for up/down arrow navigation

    Returns:
        User input string
    """
    # Check if we're in an interactive terminal
    try:
        if not IMMEDIATE_INPUT_AVAILABLE or not sys.stdin.isatty():
            # Fallback to regular input if termios not available or not interactive
            return input(prompt)
    except:
        return input(prompt)

    print(prompt, end='', flush=True)
    user_input = []
    history_index = -1  # -1 means not navigating history, 0+ means index in history_list

    # Enter raw mode ONCE and stay in it for the entire input
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    def clear_line_from_prompt():
        """Clear the current input line and reposition cursor after prompt."""
        # Move cursor to start of line, clear line, reprint prompt
        print('\r\033[K' + prompt, end='', flush=True)

    def display_input():
        """Display the current user_input."""
        clear_line_from_prompt()
        print(''.join(user_input), end='', flush=True)

    try:
        tty.setraw(fd)
        import select

        while True:
            # Read one character while in raw mode
            ch = sys.stdin.read(1)

            # If read fails, fall back to empty input
            if not ch:
                return ""

            # ESC key pressed - check if it's a standalone ESC or part of an escape sequence
            if ch == '\x1b':
                # Arrow keys send: ESC [ A/B/C/D (as 3 separate character events!)
                # Use termios VTIME/VMIN to set a read timeout on the file descriptor
                # This distinguishes standalone ESC from escape sequences

                # Get current settings
                tty_attr = termios.tcgetattr(fd)
                # Set timeout: VTIME = 2 (0.2 seconds), VMIN = 0 (return immediately if no data)
                # termios.tcgetattr returns: [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]
                # cc is index 6, VTIME and VMIN are accessed within cc
                tty_attr[6][termios.VTIME] = 2  # 0.2 second timeout
                tty_attr[6][termios.VMIN] = 0   # Don't wait for any characters
                termios.tcsetattr(fd, termios.TCSANOW, tty_attr)

                # Try to read the next character with timeout
                next_ch = sys.stdin.read(1)

                # Restore raw mode (VMIN=1, VTIME=0 for normal operation)
                tty.setraw(fd)

                if next_ch:
                    # Got another character - this is an escape sequence (arrow key, etc.)
                    if next_ch == '[' or next_ch == 'O':
                        # Standard escape sequence - read the final character
                        # Set timeout again for the final character
                        tty_attr = termios.tcgetattr(fd)
                        tty_attr[6][termios.VTIME] = 2
                        tty_attr[6][termios.VMIN] = 0
                        termios.tcsetattr(fd, termios.TCSANOW, tty_attr)

                        final_ch = sys.stdin.read(1)

                        # Restore raw mode
                        tty.setraw(fd)

                        # Handle arrow keys (if history is available)
                        if history_list and final_ch in ('A', 'B'):
                            if final_ch == 'A':  # Up arrow
                                if history_index < len(history_list) - 1:
                                    history_index += 1
                                    user_input = list(history_list[history_index])
                                    display_input()
                            elif final_ch == 'B':  # Down arrow
                                if history_index > 0:
                                    history_index -= 1
                                    user_input = list(history_list[history_index])
                                    display_input()
                                elif history_index == 0:
                                    # Move past most recent to empty input
                                    history_index = -1
                                    user_input = []
                                    display_input()

                        # Ignore other escape sequences (left/right arrows, etc.)
                        continue
                    else:
                        # Unknown escape sequence, ignore it
                        continue
                else:
                    # Timeout - no more characters, this is a standalone ESC key press
                    # Restore terminal settings BEFORE exiting
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    # Use ANSI escape to clear line from cursor to end, then print exit message
                    print("\r\033[K")
                    # Raise exception instead of sys.exit() to allow cleanup in calling code
                    raise UserExitException()

            # Backspace
            elif ch in ('\x7f', '\x08'):
                if user_input:
                    user_input.pop()
                    # Reset history navigation when user edits
                    history_index = -1
                    # Erase character from terminal
                    print('\b \b', end='', flush=True)

            # Enter key
            elif ch in ('\r', '\n'):
                # Explicitly output carriage return + newline for proper cursor positioning in raw mode
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                result = ''.join(user_input)
                # Check for exit commands
                if result.lower() in ['exit', 'quit', 'q']:
                    raise UserExitException()
                return result

            # Ctrl+C
            elif ch == '\x03':
                # Explicitly output carriage return + newline for proper cursor positioning in raw mode
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                raise KeyboardInterrupt

            # Ctrl+U (update check)
            elif ch == '\x15':
                # Explicitly output carriage return + newline for proper cursor positioning in raw mode
                sys.stdout.write('\r\n')
                sys.stdout.flush()
                raise UpdateCheckException()

            # Regular printable characters
            elif ch.isprintable():
                # Reset history navigation when user types
                history_index = -1
                user_input.append(ch)
                print(ch, end='', flush=True)

    finally:
        # Always restore terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    # Safety fallback (should never reach here as while loop always returns or raises)
    return ""


def check_exit_input(user_input):
    """Check if user wants to exit (exit commands only - ESC handled in input_with_esc_detection).

    Note: This function is now redundant as exit checking is done in input_with_esc_detection(),
    but kept for backward compatibility.
    """
    if not user_input:
        return False
    # Check for exit commands (handled by UserExitException in input_with_esc_detection now)
    if user_input.lower() in ['exit', 'quit', 'q']:
        raise UserExitException()
    return False


def interactive_mode():
    """Run the helper in interactive mode with mode selection."""
    print("\n" + "="*70)
    print(f"GT Logs Helper v{VERSION} - Interactive Mode")
    print("="*70)
    print("\nUpload and download Redis Support packages to/from S3")
    if IMMEDIATE_INPUT_AVAILABLE:
        print("Press ESC to exit, Ctrl+C, or type 'exit'/'q' at any prompt")
        print("Use UP/DOWN arrows for input history, Ctrl+U to check for updates\n")
    else:
        print("Press Ctrl+C to exit, or type 'exit' or 'q' at any prompt\n")

    # Mode selection
    print("Select operation mode:")
    print("☁️ ⬆️  1 or U: UPLOAD to S3 (generate links and upload files)")
    print("☁️ ⬇️  2 or D: DOWNLOAD from S3 (retrieve files from existing paths)")
    print()

    try:
        while True:
            mode_input = input_with_esc_detection("Your choice: ").strip().lower()
            check_exit_input(mode_input)

            if mode_input in ["1", "u"]:
                interactive_upload_mode()
                break
            elif mode_input in ["2", "d"]:
                interactive_download_mode()
                break
            else:
                print("❌ Invalid choice. Please enter 1, U, 2, or D\n")
        return 0
    except UserExitException:
        print("👋 Exiting...\n")
        return 0
    except UpdateCheckException:
        print("🔍 Checking for updates...")
        update_info = check_for_updates()
        if update_info and update_info['available']:
            if prompt_for_update(update_info):
                # Update was installed, exit so user can restart
                return 0
            else:
                # User chose 'n', return to interactive mode
                print("Returning to interactive mode...\n")
                return interactive_mode()
        elif update_info:
            print(f"✓ You're up to date! (v{update_info['current_version']})\n")
            print("Returning to interactive mode...\n")
            return interactive_mode()
        else:
            print("⚠️  Could not check for updates (offline or API error)\n")
            print("Returning to interactive mode...\n")
            return interactive_mode()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...\n")
        return 0


def interactive_upload_mode():
    """Run the upload functionality in interactive mode."""
    generator = GTLogsHelper()

    print("\n" + "-"*50)
    print("Upload Mode - Generate S3 URLs and upload files")
    print("-"*50 + "\n")

    try:
        # Get Zendesk ID
        while True:
            zd_history = generator.get_history('zendesk_id')
            zd_input = input_with_esc_detection("Enter Zendesk ticket ID (e.g., 145980): ", zd_history).strip()
            check_exit_input(zd_input)
            if not zd_input:
                print("❌ Zendesk ID is required\n")
                continue
            try:
                zd_formatted = generator.validate_zendesk_id(zd_input)
                print(f"\n✓ Using: {zd_formatted}\n")
                # Add to history immediately after validation
                generator.add_to_history('zendesk_id', zd_formatted)
                break
            except ValueError as e:
                print(f"❌ {e}\n")

        # Get Jira ID (optional)
        jira_formatted = None
        while True:
            jira_history = generator.get_history('jira_id')
            jira_input = input_with_esc_detection("Enter Jira ID (e.g., RED-172041 or MOD-12345, press Enter to skip): ", jira_history).strip()
            check_exit_input(jira_input)
            if not jira_input:
                print("\n✓ No Jira ID - will use zendesk-tickets path\n")
                break
            try:
                jira_formatted = generator.validate_jira_id(jira_input)
                print(f"\n✓ Using: {jira_formatted}\n")
                # Add to history immediately after validation
                generator.add_to_history('jira_id', jira_formatted)
                break
            except ValueError as e:
                print(f"❌ {e}\n")

        # Get support package path(s) (optional)
        package_paths = []
        while True:
            path_history = generator.get_history('file_path')
            if not package_paths:
                prompt = "Enter support package path(s) (comma-separated for multiple, press Enter to skip): "
            else:
                prompt = f"Add another file? (press Enter to continue with {len(package_paths)} file(s)): "

            package_path = input_with_esc_detection(prompt, path_history).strip()
            check_exit_input(package_path)

            if not package_path:
                if not package_paths:
                    print("\n✓ Will generate template command\n")
                else:
                    print(f"\n✓ Proceeding with {len(package_paths)} file(s)\n")
                break

            # Split by comma for multiple paths
            paths_to_validate = [p.strip() for p in package_path.split(',')]

            for path in paths_to_validate:
                if not path:
                    continue
                try:
                    validated_path = generator.validate_file_path(path)
                    if validated_path not in package_paths:  # Avoid duplicates
                        package_paths.append(validated_path)
                        print(f"✓ File {len(package_paths)}: {validated_path}")
                        # Add to history immediately after validation
                        generator.add_to_history('file_path', validated_path)
                    else:
                        print(f"⚠️  Skipping duplicate: {validated_path}")
                except ValueError as e:
                    print(f"❌ {e}")
                    retry = input_with_esc_detection("Try again? (y/n): ").strip().lower()
                    check_exit_input(retry)
                    if retry not in ['y', 'yes']:
                        if not package_paths:
                            print("✓ Skipping file path, will generate template command\n")
                        break
                    print()
                    break  # Break inner loop to retry the same input
            else:
                # If we processed all paths successfully, ask for more
                continue

            # If retry was 'n', break outer loop
            if not package_paths:
                break

        # Convert to None if empty list for backward compatibility
        package_path = package_paths if package_paths else None

        # Get AWS profile
        default_profile = generator.get_default_aws_profile()
        if default_profile:
            profile_prompt = f"Enter AWS profile (press Enter for default '{default_profile}'): "
        else:
            profile_prompt = "Enter AWS profile (optional, press Enter to skip): "

        profile_history = generator.get_history('aws_profile')
        aws_profile_input = input_with_esc_detection(profile_prompt, profile_history).strip()
        check_exit_input(aws_profile_input)

        if aws_profile_input:
            aws_profile = aws_profile_input
            # Add to history immediately
            generator.add_to_history('aws_profile', aws_profile)
            # Ask if they want to save as default
            save_default = input_with_esc_detection(f"\nSave '{aws_profile}' as default profile? (y/n): ").strip().lower()
            check_exit_input(save_default)
            if save_default in ['y', 'yes']:
                generator._save_config(aws_profile)
                print()
        elif default_profile:
            aws_profile = default_profile
            print(f"\n✓ Using default profile: {default_profile}\n")
        else:
            # Use gt-logs as fallback when no profile is configured
            aws_profile = "gt-logs"
            print("\n✓ Using default profile: gt-logs\n")

        # Handle single vs multiple files
        if package_path:
            # We have file path(s)
            if isinstance(package_path, list) and len(package_path) > 1:
                # Multiple files - use batch upload
                s3_path = generator.generate_s3_path(zd_formatted, jira_formatted)

                # Display batch upload info
                print("="*70)
                print("Batch Upload Configuration")
                print("="*70)
                print(f"\nS3 Destination:\n  {s3_path}")
                print(f"\nFiles to upload ({len(package_path)}):")
                for i, fpath in enumerate(package_path, 1):
                    print(f"  {i}. {os.path.basename(fpath)}")
                print("\n" + "="*70)

                # Offer to execute
                print()
                execute_now = input_with_esc_detection("Execute batch upload now? (Y/n): ").strip().lower()
                check_exit_input(execute_now)

                # Default to 'yes' if user just presses Enter
                if execute_now == '' or execute_now in ['y', 'yes']:
                    # Check authentication
                    is_authenticated = generator.check_aws_authentication(aws_profile)

                    if not is_authenticated:
                        print(f"\n⚠️  AWS profile '{aws_profile}' is not authenticated")
                        # Automatically run AWS SSO login
                        if not generator.aws_sso_login(aws_profile):
                            print("❌ Cannot proceed without authentication\n")
                            return 1
                    else:
                        print(f"\n✓ AWS profile '{aws_profile}' is already authenticated\n")

                    # Execute batch upload
                    success_count, failure_count, _ = generator.execute_batch_upload(
                        package_path, zd_formatted, jira_formatted, aws_profile
                    )
                    return 0 if failure_count == 0 else 1
                else:
                    print()
            else:
                # Single file - use original logic
                single_path = package_path[0] if isinstance(package_path, list) else package_path
                cmd, s3_path = generator.generate_aws_command(
                    zd_input,
                    jira_formatted,  # Can be None for ZD-only uploads
                    single_path,
                    aws_profile
                )

                # Display results
                print("="*70)
                print("Generated Output")
                print("="*70)
                print(f"\nS3 Path:\n  {s3_path}")
                print(f"\nAWS CLI Command:\n  {cmd}")
                print("\n" + "="*70)

                # Offer to execute
                print()
                execute_now = input_with_esc_detection("Execute this command now? (Y/n): ").strip().lower()
                check_exit_input(execute_now)

                # Default to 'yes' if user just presses Enter
                if execute_now == '' or execute_now in ['y', 'yes']:
                    # Check authentication
                    is_authenticated = generator.check_aws_authentication(aws_profile)

                    if not is_authenticated:
                        print(f"\n⚠️  AWS profile '{aws_profile}' is not authenticated")
                        # Automatically run AWS SSO login
                        if not generator.aws_sso_login(aws_profile):
                            print("❌ Cannot proceed without authentication\n")
                            return 1
                    else:
                        print(f"\n✓ AWS profile '{aws_profile}' is already authenticated\n")

                    # Execute the upload
                    success = generator.execute_s3_upload(cmd)
                    return 0 if success else 1
                else:
                    print()
        else:
            # Show AWS SSO login reminder if profile is specified (templated command)
            if aws_profile:
                print(f"\n💡 Reminder: Authenticate with AWS SSO before running the command:")
                print(f"   aws sso login --profile {aws_profile}\n")
            else:
                print(f"\n💡 Reminder: Authenticate with AWS SSO before running the command:")
                print(f"   aws sso login --profile <your-aws-profile>\n")

        # Save history before exiting
        generator._save_history()
        return 0

    except UserExitException:
        print("👋 Exiting...\n")
        # Save history when user exits via ESC or exit command
        generator._save_history()
        return 0
    except UpdateCheckException:
        print("🔍 Checking for updates...")
        update_info = check_for_updates()
        if update_info and update_info['available']:
            if prompt_for_update(update_info):
                # Update was installed, need to restart to use new version
                # Message already printed by perform_self_update()
                generator._save_history()
                return 0
            else:
                # User chose 'n', return to interactive mode
                print("Returning to interactive mode...\n")
                return interactive_mode()
        elif update_info:
            print(f"✓ You're up to date! (v{update_info['current_version']})\n")
            print("Returning to interactive mode...\n")
            # Return to start of interactive mode by recursively calling
            return interactive_mode()
        else:
            print("⚠️  Could not check for updates (offline or API error)\n")
            print("Returning to interactive mode...\n")
            # Return to start of interactive mode by recursively calling
            return interactive_mode()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...\n")
        # Save history even on Ctrl+C
        generator._save_history()
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}\n", file=sys.stderr)
        # Save history even on error
        generator._save_history()
        return 1


def interactive_download_mode():
    """Run the download functionality in interactive mode."""
    helper = GTLogsHelper()

    print("\n" + "-"*50)
    print("Download Mode - Retrieve files from S3")
    print("-"*50 + "\n")

    try:
        # Get S3 path or identifier
        print("Enter S3 path to download from.")
        print("Examples:")
        print("  - Full path: s3://gt-logs/zendesk-tickets/ZD-145980/file.tar.gz")
        print("  - Ticket ID: ZD-145980 (will list available files)")
        print("  - Ticket + Jira: ZD-145980-RED-172041")
        print()

        while True:
            s3_history = helper.get_history('s3_path')
            s3_input = input_with_esc_detection("Enter S3 path or ticket ID: ", s3_history).strip()
            check_exit_input(s3_input)

            if not s3_input:
                print("❌ S3 path or ticket ID is required\n")
                continue

            # Parse the S3 path
            bucket, key = helper.parse_s3_path(s3_input)
            if not bucket or not key:
                print(f"❌ Invalid S3 path or ticket ID: {s3_input}\n")
                continue

            helper.add_to_history('s3_path', s3_input)
            print(f"\n✓ Parsed: s3://{bucket}/{key}")
            break

        # Get AWS profile
        default_profile = helper.get_default_aws_profile()
        if default_profile:
            profile_prompt = f"Enter AWS profile (press Enter for default '{default_profile}'): "
        else:
            profile_prompt = "Enter AWS profile (default: gt-logs): "

        profile_history = helper.get_history('aws_profile')
        aws_profile_input = input_with_esc_detection(profile_prompt, profile_history).strip()
        check_exit_input(aws_profile_input)

        if aws_profile_input:
            aws_profile = aws_profile_input
            helper.add_to_history('aws_profile', aws_profile)
        elif default_profile:
            aws_profile = default_profile
            print(f"\n✓ Using default profile: {default_profile}")
        else:
            aws_profile = "gt-logs"
            print(f"\n✓ Using default profile: gt-logs")

        # Check authentication
        print(f"\nChecking AWS authentication...")
        is_authenticated = helper.check_aws_authentication(aws_profile)

        if not is_authenticated:
            print(f"⚠️  AWS profile '{aws_profile}' is not authenticated")
            if not helper.aws_sso_login(aws_profile):
                print("❌ Cannot proceed without authentication\n")
                return 1
        else:
            print(f"✓ AWS profile '{aws_profile}' is authenticated")

        # If the key is a directory (ends with /), list files
        if key.endswith("/"):
            print(f"\n🔍 Listing files in s3://{bucket}/{key}...\n")
            files = helper.list_s3_files(bucket, key, aws_profile)

            if not files:
                print(f"❌ No files found in s3://{bucket}/{key}")
                return 1

            print(f"Found {len(files)} file(s):")
            for i, file in enumerate(files, 1):
                print(f"  {i}. {file}")

            # Ask which file(s) to download
            print("\nSelect files to download:")
            print("  - Enter file number(s) separated by commas (e.g., 1,3,5)")
            print("  - Enter 'all' or 'a' to download all files")
            print("  - Press Enter to cancel")
            print()

            selection = input_with_esc_detection("Your selection: ").strip()
            check_exit_input(selection)

            if not selection:
                print("\nDownload cancelled\n")
                return 0

            files_to_download = []
            if selection.lower() in ['all', 'a']:
                files_to_download = files
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(',')]
                    files_to_download = [files[i] for i in indices if 0 <= i < len(files)]
                except (ValueError, IndexError):
                    print("❌ Invalid selection\n")
                    return 1

            if not files_to_download:
                print("❌ No valid files selected\n")
                return 1

            # Get local directory
            print("\nWhere to save the files?")
            local_dir = input_with_esc_detection("Local directory (press Enter for current directory): ").strip()
            check_exit_input(local_dir)

            if not local_dir:
                local_dir = "."

            # Create directory if it doesn't exist
            if local_dir != "." and not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
                print(f"✓ Created directory: {local_dir}")

            # Download selected files
            print(f"\n📥 Downloading {len(files_to_download)} file(s)...\n")
            success_count = 0
            for file in files_to_download:
                local_path = os.path.join(local_dir, os.path.basename(file))
                if helper.download_from_s3(bucket, file, local_path, aws_profile):
                    success_count += 1

            print(f"\n✅ Downloaded {success_count}/{len(files_to_download)} file(s) successfully")

        else:
            # Single file download
            print(f"\n📥 Downloading s3://{bucket}/{key}...")

            # Get local path
            default_name = os.path.basename(key) if key else "download"
            local_path = input_with_esc_detection(f"Save as (press Enter for '{default_name}'): ").strip()
            check_exit_input(local_path)

            if not local_path:
                local_path = default_name

            # Download the file
            if helper.download_from_s3(bucket, key, local_path, aws_profile):
                print(f"✅ Successfully downloaded to: {local_path}")
            else:
                print("❌ Download failed")
                return 1

        # Save history
        helper._save_history()
        return 0

    except UserExitException:
        print("👋 Exiting...\n")
        helper._save_history()
        return 0
    except KeyboardInterrupt:
        print("\n👋 Exiting...\n")
        helper._save_history()
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}\n", file=sys.stderr)
        helper._save_history()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='GT Logs Helper - Upload and download Redis Support packages to/from S3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (no arguments) - Choose between upload/download
  %(prog)s

  # UPLOAD MODE:
  # Generate S3 path only
  %(prog)s 145980 RED-172041

  # Upload single file
  %(prog)s 145980 RED-172041 -f /path/to/support_package.tar.gz --execute

  # Batch upload multiple files
  %(prog)s 145980 RED-172041 -f file1.tar.gz -f file2.tar.gz -f file3.tar.gz --execute

  # DOWNLOAD MODE:
  # Download from S3 path
  %(prog)s --download s3://gt-logs/zendesk-tickets/ZD-145980/file.tar.gz

  # Download using ticket ID (lists files, use 'a' to download all)
  %(prog)s --download ZD-145980

  # Download with custom output path
  %(prog)s --download ZD-145980 --output ~/Downloads/

  # CONFIG:
  # Use specific AWS profile
  %(prog)s 145980 RED-172041 -p my-aws-profile

  # Set default AWS profile
  %(prog)s --set-profile my-aws-profile
        """
    )

    parser.add_argument('zendesk_id', nargs='?',
                       help='Zendesk ticket ID (e.g., 145980 or ZD-145980)')
    parser.add_argument('jira_id', nargs='?',
                       help='Jira ticket ID (optional, e.g., RED-172041 or MOD-12345)')
    parser.add_argument('-f', '--file', dest='support_package', action='append',
                       help='Path to support package file (can be used multiple times for batch uploads)')
    parser.add_argument('-p', '--profile', dest='aws_profile',
                       help='AWS profile to use (overrides default)')
    parser.add_argument('--set-profile', dest='set_profile',
                       help='Set default AWS profile')
    parser.add_argument('--show-config', action='store_true',
                       help='Show current configuration')
    parser.add_argument('-v', '--version', action='store_true',
                       help='Show version and check for updates')
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('-e', '--execute', action='store_true',
                       help='Execute the AWS S3 upload command (requires non-templated file path)')

    # Download mode arguments
    parser.add_argument('-d', '--download', dest='download_path',
                       help='Download from S3 (provide S3 path or ticket ID)')
    parser.add_argument('-o', '--output', dest='output_path',
                       help='Output directory for downloads (default: current directory)')

    args = parser.parse_args()

    helper = GTLogsHelper()

    # Handle config commands
    if args.set_profile:
        helper._save_config(args.set_profile)
        return 0

    if args.show_config:
        default_profile = helper.get_default_aws_profile()
        print(f"Configuration file: {helper.CONFIG_FILE}")
        print(f"Default AWS profile: {default_profile if default_profile else '(not set)'}")
        return 0

    if args.version:
        print(f"GT Logs Helper v{VERSION}")
        print("\n🔍 Checking for updates...")
        update_info = check_for_updates()
        if update_info and update_info['available']:
            print(f"📦 Update available: v{update_info['current_version']} → v{update_info['latest_version']}")
            if update_info['release_notes']:
                print("   Changes:")
                for note in update_info['release_notes']:
                    print(f"   - {note}")
            print("\nRun the script in interactive mode to update, or press Ctrl+U during runtime.\n")
        elif update_info:
            print(f"✓ You're up to date!\n")
        else:
            print("⚠️  Could not check for updates (offline or API error)\n")
        return 0

    # Handle download mode
    if args.download_path:
        # Parse the S3 path
        bucket, key = helper.parse_s3_path(args.download_path)
        if not bucket or not key:
            print(f"❌ Invalid S3 path or ticket ID: {args.download_path}")
            return 1

        # Determine AWS profile
        aws_profile = args.aws_profile or helper.get_default_aws_profile() or "gt-logs"

        # Check authentication
        print(f"Checking AWS authentication...")
        if not helper.check_aws_authentication(aws_profile):
            print(f"⚠️  AWS profile '{aws_profile}' is not authenticated")
            if not helper.aws_sso_login(aws_profile):
                print("❌ Cannot proceed without authentication")
                return 1

        # Determine output path
        output_path = args.output_path or "."

        # If downloading a directory, list and prompt
        if key.endswith("/"):
            print(f"\n🔍 Listing files in s3://{bucket}/{key}...\n")
            files = helper.list_s3_files(bucket, key, aws_profile)
            if not files:
                print(f"❌ No files found")
                return 1

            print(f"Found {len(files)} file(s). Downloading all...")
            for file in files:
                local_path = os.path.join(output_path, os.path.basename(file))
                helper.download_from_s3(bucket, file, local_path, aws_profile)
        else:
            # Single file download
            local_path = os.path.join(output_path, os.path.basename(key))
            if helper.download_from_s3(bucket, key, local_path, aws_profile):
                print(f"✅ Downloaded to: {local_path}")
            else:
                return 1
        return 0

    # Interactive mode if no arguments or -i flag
    if args.interactive or (not args.zendesk_id and not args.jira_id and not args.download_path):
        # Check for updates before starting interactive mode
        print("🔍 Checking for updates...")
        update_info = check_for_updates()
        if update_info and update_info['available']:
            if prompt_for_update(update_info):
                # Update was installed, exit so user can restart
                return 0
        elif update_info:
            # Up to date, continue silently
            pass
        # If check failed (offline), continue silently

        return interactive_mode()

    # Require at least Zendesk ID for upload mode (Jira is optional)
    if not args.zendesk_id:
        parser.print_help()
        return 1

    try:
        default_profile = helper.get_default_aws_profile()
        # Use fallback to gt-logs if no profile is specified
        used_profile = args.aws_profile or default_profile or "gt-logs"

        # Validate Zendesk ID
        zd_formatted = helper.validate_zendesk_id(args.zendesk_id)

        # Validate Jira ID if provided
        jira_formatted = None
        if args.jira_id:
            jira_formatted = helper.validate_jira_id(args.jira_id)

        # Validate and collect file paths
        file_paths = []
        if args.support_package:
            for fpath in args.support_package:
                validated = helper.validate_file_path(fpath)
                file_paths.append(validated)

        # Handle multiple files vs single file
        if file_paths and len(file_paths) > 1:
            # Batch upload mode
            s3_path = helper.generate_s3_path(zd_formatted, jira_formatted)

            # Display batch upload info
            print("\n" + "="*70)
            print("GT Logs Helper - Batch Upload")
            print("="*70)
            print(f"\nS3 Destination:\n  {s3_path}")
            print(f"\nFiles to upload ({len(file_paths)}):")
            for i, fpath in enumerate(file_paths, 1):
                print(f"  {i}. {os.path.basename(fpath)}")
            print("\n" + "="*70)

            # Show profile info
            if not args.aws_profile and not default_profile:
                print("\nℹ️  Tip: Set a default AWS profile with --set-profile")
                print(f"ℹ️  Using fallback AWS profile: gt-logs")
            elif default_profile and not args.aws_profile:
                print(f"\nℹ️  Using default AWS profile: {default_profile}")

            # Handle --execute flag
            if args.execute:
                if not used_profile:
                    print("\n❌ Error: --execute requires an AWS profile (use -p or --set-profile)\n")
                    return 1

                print()

                # Check authentication
                is_authenticated = helper.check_aws_authentication(used_profile)

                if not is_authenticated:
                    print(f"⚠️  AWS profile '{used_profile}' is not authenticated")
                    # Automatically run AWS SSO login
                    if not helper.aws_sso_login(used_profile):
                        print("❌ Cannot proceed without authentication\n")
                        return 1
                else:
                    print(f"✓ AWS profile '{used_profile}' is already authenticated\n")

                # Execute batch upload
                success_count, failure_count, _ = helper.execute_batch_upload(
                    file_paths, zd_formatted, jira_formatted, used_profile
                )
                return 0 if failure_count == 0 else 1
            else:
                # Show AWS SSO login reminder
                if used_profile:
                    print(f"\n💡 Reminder: Authenticate with AWS SSO before running uploads:")
                    print(f"   aws sso login --profile {used_profile}")
                print()
                return 0

        else:
            # Single file or no file (template mode)
            single_file = file_paths[0] if file_paths else None

            cmd, s3_path = helper.generate_aws_command(
                args.zendesk_id,
                args.jira_id,
                single_file,
                args.aws_profile
            )

            # Display results
            print("\n" + "="*70)
            print("GT Logs Helper")
            print("="*70)
            print(f"\nS3 Path:\n  {s3_path}")
            print(f"\nAWS CLI Command:\n  {cmd}")
            print("\n" + "="*70)

            # Show helpful info
            if not single_file:
                print("\nℹ️  Tip: Use -f to specify the support package file path")
                print("ℹ️  Tip: Use -f multiple times for batch uploads (e.g., -f file1.tar.gz -f file2.tar.gz)")

            if not args.aws_profile and not default_profile:
                print("ℹ️  Tip: Set a default AWS profile with --set-profile")
                print(f"ℹ️  Using fallback AWS profile: gt-logs")
            elif default_profile and not args.aws_profile:
                print(f"ℹ️  Using default AWS profile: {default_profile}")

            # Handle --execute flag (only if we have a real file path)
            if args.execute:
                if not single_file:
                    print("\n❌ Error: --execute requires a file path (-f/--file)\n")
                    return 1

                if not used_profile:
                    print("\n❌ Error: --execute requires an AWS profile (use -p or --set-profile)\n")
                    return 1

                print()

                # Check authentication
                is_authenticated = helper.check_aws_authentication(used_profile)

                if not is_authenticated:
                    print(f"⚠️  AWS profile '{used_profile}' is not authenticated")
                    # Automatically run AWS SSO login
                    if not helper.aws_sso_login(used_profile):
                        print("❌ Cannot proceed without authentication\n")
                        return 1
                else:
                    print(f"✓ AWS profile '{used_profile}' is already authenticated\n")

                # Execute the upload
                success = helper.execute_s3_upload(cmd)
                return 0 if success else 1

            # Show AWS SSO login reminder (when not executing)
            if used_profile:
                print(f"\n💡 Reminder: Authenticate with AWS SSO before running the command:")
                print(f"   aws sso login --profile {used_profile}")
            else:
                print(f"\n💡 Reminder: Authenticate with AWS SSO before running the command:")
                print(f"   aws sso login --profile <your-aws-profile>")

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
