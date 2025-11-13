#!/usr/bin/env python3
"""
GT Logs Link Generator
Generates S3 bucket URLs and AWS CLI commands for Redis Support packages.
"""

VERSION = "1.0.6"

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
from typing import TYPE_CHECKING, Any, cast

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
        url = "https://api.github.com/repos/markotrapani/gtlogs-link-generator/releases/latest"
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
        download_url = f"https://raw.githubusercontent.com/markotrapani/gtlogs-link-generator/{data['tag_name']}/gtlogs-generator.py"

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
        print(f"📥 Downloading v{latest_version}...")

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

    except urllib.error.URLError as e:
        print(f"❌ Download failed: {e.reason}", file=sys.stderr)
        rollback_update(script_path, backup_path, temp_path)
        return False
    except urllib.error.HTTPError as e:
        print(f"❌ Download failed: HTTP {e.code} {e.reason}", file=sys.stderr)
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

    response = input("\nUpdate now? (y/n): ").strip().lower()

    if response == 'y':
        return perform_self_update(update_info['download_url'], update_info['latest_version'])
    else:
        print("Update cancelled.\n")
        return False


class GTLogsGenerator:
    """Generates GT Logs S3 URLs and AWS CLI commands."""

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

        # Determine AWS profile
        if aws_profile is None:
            aws_profile = self.get_default_aws_profile()

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
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
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
            print(f"📤 Uploading to S3...")
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


def input_with_esc_detection(prompt: str, history_list: list = None) -> str:
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

            # If read fails, fall back
            if not ch:
                break

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
                print()
                result = ''.join(user_input)
                # Check for exit commands
                if result.lower() in ['exit', 'quit', 'q']:
                    raise UserExitException()
                return result

            # Ctrl+C
            elif ch == '\x03':
                print()
                raise KeyboardInterrupt

            # Ctrl+U (update check)
            elif ch == '\x15':
                print()
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
    """Run the generator in interactive mode."""
    generator = GTLogsGenerator()

    print("\n" + "="*70)
    print(f"GT Logs Link Generator v{VERSION} - Interactive Mode")
    print("="*70)
    print("\nGenerate S3 URLs and AWS CLI commands for Redis Support packages")
    if IMMEDIATE_INPUT_AVAILABLE:
        print("Press ESC to exit, Ctrl+C, or type 'exit'/'q' at any prompt")
        print("Use UP/DOWN arrows for input history, Ctrl+U to check for updates\n")
    else:
        print("Press Ctrl+C to exit, or type 'exit' or 'q' at any prompt\n")

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

        # Get support package path (optional)
        while True:
            path_history = generator.get_history('file_path')
            package_path = input_with_esc_detection("Enter support package path (optional, press Enter to skip): ", path_history).strip()
            check_exit_input(package_path)
            if not package_path:
                package_path = None
                print("\n✓ Will generate template command\n")
                break
            try:
                validated_path = generator.validate_file_path(package_path)
                print(f"\n✓ File found: {validated_path}\n")
                # Add to history immediately after validation
                generator.add_to_history('file_path', validated_path)
                package_path = validated_path
                break
            except ValueError as e:
                print(f"❌ {e}")
                retry = input_with_esc_detection("Try again? (y/n): ").strip().lower()
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
            aws_profile = None
            print("\n✓ No AWS profile specified\n")

        # Generate the command
        cmd, s3_path = generator.generate_aws_command(
            zd_input,
            jira_formatted,  # Can be None for ZD-only uploads
            package_path,
            aws_profile
        )

        # Display results
        print("="*70)
        print("Generated Output")
        print("="*70)
        print(f"\nS3 Path:\n  {s3_path}")
        print(f"\nAWS CLI Command:\n  {cmd}")
        print("\n" + "="*70)

        # If we have a real file path (not templated), offer to execute
        if package_path:
            print()
            execute_now = input_with_esc_detection("Execute this command now? (Y/n): ").strip().lower()
            check_exit_input(execute_now)

            # Default to 'yes' if user just presses Enter
            if execute_now == '' or execute_now in ['y', 'yes']:
                # Determine which profile to use
                profile_to_use = aws_profile

                # Check authentication
                if profile_to_use:
                    is_authenticated = generator.check_aws_authentication(profile_to_use)

                    if not is_authenticated:
                        print(f"\n⚠️  AWS profile '{profile_to_use}' is not authenticated")
                        # Automatically run AWS SSO login
                        if not generator.aws_sso_login(profile_to_use):
                            print("❌ Cannot proceed without authentication\n")
                            return 1
                    else:
                        print(f"\n✓ AWS profile '{profile_to_use}' is already authenticated\n")

                    # Execute the upload
                    success = generator.execute_s3_upload(cmd)
                    return 0 if success else 1
                else:
                    print("\n⚠️  No AWS profile specified. Please configure a profile first.\n")
                    return 1
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
                print("Please restart the script to use the new version.\n")
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

  # Execute the upload automatically (checks auth and runs command)
  %(prog)s 145980 RED-172041 -f /path/to/support_package.tar.gz --execute

  # Use specific AWS profile
  %(prog)s 145980 RED-172041 -f /path/to/support_package.tar.gz -p my-aws-profile

  # Set default AWS profile
  %(prog)s --set-profile my-aws-profile
        """
    )

    parser.add_argument('zendesk_id', nargs='?',
                       help='Zendesk ticket ID (e.g., 145980 or ZD-145980)')
    parser.add_argument('jira_id', nargs='?',
                       help='Jira ticket ID (optional, e.g., RED-172041 or MOD-12345)')
    parser.add_argument('-f', '--file', dest='support_package',
                       help='Path to support package file (optional)')
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

    if args.version:
        print(f"GT Logs Link Generator v{VERSION}")
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

    # Interactive mode if no arguments or -i flag
    if args.interactive or (not args.zendesk_id and not args.jira_id):
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

    # Require at least Zendesk ID for generation (Jira is now optional)
    if not args.zendesk_id:
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
        used_profile = args.aws_profile or default_profile

        if not args.aws_profile and not default_profile:
            print("ℹ️  Tip: Set a default AWS profile with --set-profile")
        elif default_profile and not args.aws_profile:
            print(f"ℹ️  Using default AWS profile: {default_profile}")

        # Handle --execute flag (only if we have a real file path)
        if args.execute:
            if not args.support_package:
                print("\n❌ Error: --execute requires a file path (-f/--file)\n")
                return 1

            if not used_profile:
                print("\n❌ Error: --execute requires an AWS profile (use -p or --set-profile)\n")
                return 1

            print()

            # Check authentication
            is_authenticated = generator.check_aws_authentication(used_profile)

            if not is_authenticated:
                print(f"⚠️  AWS profile '{used_profile}' is not authenticated")
                # Automatically run AWS SSO login
                if not generator.aws_sso_login(used_profile):
                    print("❌ Cannot proceed without authentication\n")
                    return 1
            else:
                print(f"✓ AWS profile '{used_profile}' is already authenticated\n")

            # Execute the upload
            success = generator.execute_s3_upload(cmd)
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
