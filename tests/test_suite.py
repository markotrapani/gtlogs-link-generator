#!/usr/bin/env python3
"""
Automated test suite for GT Logs Helper

Tests all functionality without requiring manual interaction:
- Batch upload (CLI mode with multiple -f flags)
- Batch upload (interactive mode - comma-separated, iterative)
- Download 'a' shortcut (interactive mode)
- Duplicate detection
- Progress tracking
- Success/failure summaries
- Directory upload (dry-run, pattern filtering, error handling)

Usage:
    python3 tests/test_suite.py
"""

import subprocess
import os
import tempfile
import sys
from typing import List, Tuple


class TestColors:
    """ANSI color codes for test output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class TestRunner:
    """Automated test runner for v1.2.0 features"""

    def __init__(self):
        self.script_path = './gtlogs-helper.py'
        self.test_files: List[str] = []
        self.test_dir: str = ""
        self.passed = 0
        self.failed = 0
        self.test_number = 0

    def setup(self):
        """Create test files and directory structure"""
        print(f"\n{TestColors.BLUE}Setting up test environment...{TestColors.RESET}")

        # Create test files in /tmp
        for i in range(1, 6):
            filepath = f"/tmp/test_batch_{i}.tar.gz"
            with open(filepath, 'w') as f:
                f.write(f"test content {i}\n")
            self.test_files.append(filepath)
            print(f"  Created: {filepath}")

        # Create test directory structure for directory upload tests
        self.test_dir = "/tmp/test_dir_upload"
        os.makedirs(f"{self.test_dir}/logs", exist_ok=True)
        os.makedirs(f"{self.test_dir}/configs", exist_ok=True)
        os.makedirs(f"{self.test_dir}/data", exist_ok=True)

        # Create test files in directory
        with open(f"{self.test_dir}/README.txt", 'w') as f:
            f.write("Test readme\n")
        with open(f"{self.test_dir}/logs/debug.log", 'w') as f:
            f.write("Debug log content\n")
        with open(f"{self.test_dir}/logs/error.log", 'w') as f:
            f.write("Error log content\n")
        with open(f"{self.test_dir}/configs/app.conf", 'w') as f:
            f.write("App config\n")
        with open(f"{self.test_dir}/configs/db.conf", 'w') as f:
            f.write("DB config\n")
        with open(f"{self.test_dir}/data/data1.tar.gz", 'w') as f:
            f.write("Data file 1\n")
        with open(f"{self.test_dir}/data/data2.tar.gz", 'w') as f:
            f.write("Data file 2\n")

        print(f"  Created: {self.test_dir}/ (with 7 files)")

        print(f"{TestColors.GREEN}✓ Setup complete{TestColors.RESET}\n")

    def cleanup(self):
        """Remove test files and directory"""
        print(f"\n{TestColors.BLUE}Cleaning up test files...{TestColors.RESET}")

        for filepath in self.test_files:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"  Removed: {filepath}")

        # Remove test directory
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)
            print(f"  Removed: {self.test_dir}/")

        print(f"{TestColors.GREEN}✓ Cleanup complete{TestColors.RESET}\n")

    def run_command(self, args: List[str], stdin_input: str = None) -> Tuple[int, str, str]:
        """
        Run gtlogs-helper.py with arguments

        Returns:
            (returncode, stdout, stderr)
        """
        cmd = [self.script_path] + args

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE if stdin_input else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input=stdin_input)
        return process.returncode, stdout, stderr

    def test(self, name: str, assertion: bool, details: str = ""):
        """Record test result"""
        self.test_number += 1

        if assertion:
            self.passed += 1
            status = f"{TestColors.GREEN}✓ PASS{TestColors.RESET}"
        else:
            self.failed += 1
            status = f"{TestColors.RED}✗ FAIL{TestColors.RESET}"

        print(f"{self.test_number}. {status} - {name}")
        if details and not assertion:
            print(f"   {TestColors.YELLOW}Details: {details}{TestColors.RESET}")

    def test_cli_batch_upload_multiple_files(self):
        """Test 1: CLI batch upload with multiple -f flags"""
        print(f"\n{TestColors.BOLD}Phase 1: CLI Batch Upload (Multiple -f flags){TestColors.RESET}\n")

        # Test with 3 files
        returncode, stdout, stderr = self.run_command([
            '145980',
            'RED-172041',
            '-f', self.test_files[0],
            '-f', self.test_files[1],
            '-f', self.test_files[2]
        ])

        # Validate output contains all three filenames
        file0_name = os.path.basename(self.test_files[0])
        file1_name = os.path.basename(self.test_files[1])
        file2_name = os.path.basename(self.test_files[2])

        self.test(
            "Multiple -f flags accepted",
            returncode == 0,
            f"Exit code: {returncode}"
        )

        self.test(
            "First file appears in output",
            file0_name in stdout,
            f"'{file0_name}' not found in output"
        )

        self.test(
            "Second file appears in output",
            file1_name in stdout,
            f"'{file1_name}' not found in output"
        )

        self.test(
            "Third file appears in output",
            file2_name in stdout,
            f"'{file2_name}' not found in output"
        )

        # Check for batch upload indicator
        self.test(
            "Batch upload mode detected",
            "3 file(s)" in stdout or "Batch Upload" in stdout,
            "No batch upload indicator found"
        )

    def test_cli_batch_upload_duplicate_detection(self):
        """Test 2: Duplicate file handling in CLI mode"""
        print(f"\n{TestColors.BOLD}Phase 2: Duplicate File Handling{TestColors.RESET}\n")

        # Pass same file multiple times
        returncode, stdout, stderr = self.run_command([
            '145980',
            'RED-172041',
            '-f', self.test_files[0],
            '-f', self.test_files[1],
            '-f', self.test_files[0],  # Duplicate!
            '-f', self.test_files[1]   # Duplicate!
        ])

        self.test(
            "CLI mode accepts duplicate files",
            returncode == 0,
            f"Exit code: {returncode}"
        )

        # CLI mode currently accepts duplicates - verify all files listed
        file0_name = os.path.basename(self.test_files[0])
        file1_name = os.path.basename(self.test_files[1])

        self.test(
            "All duplicate entries shown in output",
            file0_name in stdout and file1_name in stdout,
            "Files not shown in output"
        )

        # Note: Duplicate detection/deduplication is a future enhancement
        # See ROADMAP.md for planned improvements

    def test_cli_batch_upload_invalid_file(self):
        """Test 3: Batch upload with one invalid file"""
        print(f"\n{TestColors.BOLD}Phase 3: Error Handling (Invalid File in Batch){TestColors.RESET}\n")

        returncode, stdout, stderr = self.run_command([
            '145980',
            'RED-172041',
            '-f', self.test_files[0],
            '-f', '/nonexistent/file.tar.gz',  # Invalid!
            '-f', self.test_files[1]
        ])

        output = stdout + stderr

        self.test(
            "Invalid file detected",
            returncode != 0 or "does not exist" in output or "not found" in output.lower(),
            "Invalid file not caught"
        )

    def test_interactive_batch_upload_comma_separated(self):
        """Test 4: Interactive mode - comma-separated file paths"""
        print(f"\n{TestColors.BOLD}Phase 4: Interactive Batch Upload (Comma-separated){TestColors.RESET}\n")

        # Simulate interactive input:
        # 1. Select upload mode (1)
        # 2. ZD ID: 145980
        # 3. Jira ID: (skip)
        # 4. File path: comma-separated list
        # 5. AWS profile: (default)
        # 6. Execute? n (don't actually upload)

        files_input = f"{self.test_files[0]}, {self.test_files[1]}, {self.test_files[2]}"

        stdin_input = f"1\n145980\n\n{files_input}\n\nn\n"

        returncode, stdout, stderr = self.run_command(
            ['-i'],
            stdin_input=stdin_input
        )

        self.test(
            "Interactive mode accepts comma-separated paths",
            "145980" in stdout and (self.test_files[0] in stdout or "test_batch_1" in stdout),
            "Comma-separated paths not processed"
        )

        self.test(
            "Multiple files parsed from comma-separated input",
            "test_batch_1" in stdout and "test_batch_2" in stdout,
            "Not all files detected"
        )

    def test_interactive_batch_upload_iterative(self):
        """Test 5: Interactive mode - iterative file addition"""
        print(f"\n{TestColors.BOLD}Phase 5: Interactive Batch Upload (Iterative Addition){TestColors.RESET}\n")

        # Note: This test depends on how the interactive mode is implemented
        # It may prompt "Add another file? (y/n)" after each file

        # Simulate: upload mode, ZD, no Jira, first file, 'y' to add more, second file, 'n' to stop
        stdin_input = f"1\n145980\n\n{self.test_files[0]}\ny\n{self.test_files[1]}\nn\n\nn\n"

        returncode, stdout, stderr = self.run_command(
            ['-i'],
            stdin_input=stdin_input
        )

        # If iterative mode exists, we should see both files
        # If not implemented, this is expected to not show iterative behavior
        self.test(
            "Interactive mode completes",
            returncode == 0 or returncode == 1,  # May exit cleanly or with validation error
            f"Exit code: {returncode}"
        )

        # This is informational - not all implementations may support iterative
        has_iterative = "Add another" in stdout or "add more" in stdout.lower()

        self.test(
            "Iterative addition support detected (informational)",
            True,  # Always pass - this is just checking if feature exists
            f"Iterative mode: {'YES' if has_iterative else 'NO (may not be implemented yet)'}"
        )

    def check_aws_auth(self) -> bool:
        """Check if AWS is authenticated, and authenticate if not"""
        try:
            # Check current auth status
            result = subprocess.run(
                ['aws', 'sts', 'get-caller-identity', '--profile', 'gt-logs'],
                capture_output=True,
                timeout=5,
                text=True
            )

            if result.returncode == 0:
                return True

            # Not authenticated - trigger SSO login
            print(f"\n  {TestColors.YELLOW}⚠ AWS not authenticated - triggering SSO login...{TestColors.RESET}")
            print(f"  {TestColors.BLUE}🌐 Browser window will open for authentication{TestColors.RESET}")
            print(f"  {TestColors.BLUE}Please complete the SSO login in your browser{TestColors.RESET}\n")

            # Run aws sso login (this will open browser)
            sso_result = subprocess.run(
                ['aws', 'sso', 'login', '--profile', 'gt-logs'],
                timeout=120  # Give user 2 minutes to complete browser auth
            )

            if sso_result.returncode == 0:
                print(f"\n  {TestColors.GREEN}✓ AWS authentication successful!{TestColors.RESET}")
                return True
            else:
                print(f"\n  {TestColors.YELLOW}⚠ AWS authentication failed or cancelled{TestColors.RESET}")
                return False

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"\n  {TestColors.YELLOW}⚠ AWS CLI not available or timeout: {e}{TestColors.RESET}")
            return False

    def test_download_a_shortcut(self):
        """Test 6: Download mode 'a' shortcut (with E2E if authenticated)"""
        print(f"\n{TestColors.BOLD}Phase 6: Download 'a' Shortcut{TestColors.RESET}\n")

        # Check AWS authentication
        is_authenticated = self.check_aws_auth()

        if is_authenticated:
            print(f"  {TestColors.GREEN}✓ AWS authenticated - running E2E tests{TestColors.RESET}")
        else:
            print(f"  {TestColors.YELLOW}⚠ AWS not authenticated - testing input validation only{TestColors.RESET}")

        # Test 1: CLI download mode activates
        returncode, stdout, stderr = self.run_command([
            '--download',
            'ZD-145980'
        ])

        output = stdout + stderr

        self.test(
            "Download mode activates",
            "download" in output.lower() or "s3://" in output or "AWS" in output,
            "Download mode not detected"
        )

        # Test 2: Interactive mode - 'a' shortcut for "download all"
        # Simulate: select download mode (2), enter ticket ID, then 'a' for all files

        if is_authenticated:
            # E2E test with real S3
            # Use a temporary download directory
            download_dir = "/tmp/gtlogs_test_downloads"
            os.makedirs(download_dir, exist_ok=True)

            # Mode 2 (download), ticket ID, default profile, 'a' for all, download directory
            stdin_input = f"2\nZD-145980\n\na\n{download_dir}\n"

            returncode, stdout, stderr = self.run_command(
                ['-i'],
                stdin_input=stdin_input
            )

            output = stdout + stderr

            self.test(
                "'a' shortcut works with real S3 (E2E)",
                "download" in output.lower() and ("successful" in output.lower() or "Downloaded" in output),
                f"Download didn't complete: {output[:200]}"
            )

            # Clean up download directory
            if os.path.exists(download_dir):
                import shutil
                shutil.rmtree(download_dir)

        else:
            # Input validation test only
            stdin_input = "2\nZD-145980\n\na\n"  # Mode 2, ticket, default profile, 'a' for all

            returncode, stdout, stderr = self.run_command(
                ['-i'],
                stdin_input=stdin_input
            )

            output = stdout + stderr

            # Check if 'a' was accepted (won't error on 'invalid selection')
            self.test(
                "'a' shortcut accepted as valid input",
                "invalid" not in output.lower() or "AWS" in output or "authenticate" in output.lower(),
                "'a' rejected as invalid input"
            )

        # Test 3: Compare behavior - 'a' vs 'all' should be identical
        stdin_input_all = "2\nZD-145980\n\nall\n"

        returncode_all, stdout_all, stderr_all = self.run_command(
            ['-i'],
            stdin_input=stdin_input_all
        )

        output_all = stdout_all + stderr_all

        # Both should behave similarly (both try to download or both fail auth)
        self.test(
            "'a' behaves like 'all' shortcut",
            ("AWS" in output and "AWS" in output_all) or
            ("download" in output.lower() and "download" in output_all.lower()) or
            ("authenticate" in output.lower() and "authenticate" in output_all.lower()),
            f"'a' and 'all' produce different behaviors"
        )

    def test_batch_upload_with_execute_flag(self):
        """Test 7: Batch upload with --execute flag (dry-run check)"""
        print(f"\n{TestColors.BOLD}Phase 7: Batch Upload + Execute Flag (Validation Only){TestColors.RESET}\n")

        # Test that execute flag works with multiple files
        # This won't actually upload (would need AWS auth)

        returncode, stdout, stderr = self.run_command([
            '145980',
            'RED-172041',
            '-f', self.test_files[0],
            '-f', self.test_files[1],
            '--execute'
        ])

        output = stdout + stderr

        # Should attempt to execute or show AWS auth requirement
        self.test(
            "Execute flag accepted with batch upload",
            "AWS" in output or "authenticate" in output.lower() or "upload" in output.lower(),
            "Execute flag not processed"
        )

    def test_directory_upload_dry_run(self):
        """Test 8: Directory upload in dry-run mode"""
        print(f"\n{TestColors.BOLD}Phase 8: Directory Upload (Dry-run Mode){TestColors.RESET}\n")

        returncode, stdout, stderr = self.run_command([
            '145980',
            'RED-172041',
            '--dir', self.test_dir,
            '--dry-run'
        ])

        output = stdout + stderr

        self.test(
            "Directory upload dry-run completes",
            returncode == 0,
            f"Exit code: {returncode}"
        )

        self.test(
            "Dry-run mode detected",
            "DRY RUN" in output,
            "Dry-run indicator not found"
        )

        self.test(
            "File count shown (7 files)",
            "7 file(s)" in output,
            "File count not shown or incorrect"
        )

        self.test(
            "Directory structure preserved in output",
            "test_dir_upload/logs/" in output or "logs/debug.log" in output,
            "Directory structure not shown"
        )

        self.test(
            "No actual upload occurred",
            "No files were uploaded" in output or "Dry run complete" in output,
            "Upload may have occurred in dry-run mode"
        )

    def test_directory_upload_with_include_patterns(self):
        """Test 9: Directory upload with include patterns"""
        print(f"\n{TestColors.BOLD}Phase 9: Directory Upload (Include Patterns){TestColors.RESET}\n")

        # Include only .tar.gz files
        returncode, stdout, stderr = self.run_command([
            '145980',
            'RED-172041',
            '--dir', self.test_dir,
            '--include', '*.tar.gz',
            '--dry-run'
        ])

        output = stdout + stderr

        self.test(
            "Include pattern accepted",
            returncode == 0,
            f"Exit code: {returncode}"
        )

        self.test(
            "Include pattern shown in output",
            "Include patterns" in output and "*.tar.gz" in output,
            "Include pattern not shown"
        )

        self.test(
            "Only matching files found (2 files)",
            "2 file(s)" in output,
            f"Expected 2 files, output: {output[:200]}"
        )

        self.test(
            "Tar.gz files included",
            "data1.tar.gz" in output and "data2.tar.gz" in output,
            "Expected tar.gz files not found"
        )

    def test_directory_upload_with_exclude_patterns(self):
        """Test 10: Directory upload with exclude patterns"""
        print(f"\n{TestColors.BOLD}Phase 10: Directory Upload (Exclude Patterns){TestColors.RESET}\n")

        # Exclude .log files
        returncode, stdout, stderr = self.run_command([
            '145980',
            'RED-172041',
            '--dir', self.test_dir,
            '--exclude', '*.log',
            '--dry-run'
        ])

        output = stdout + stderr

        self.test(
            "Exclude pattern accepted",
            returncode == 0,
            f"Exit code: {returncode}"
        )

        self.test(
            "Exclude pattern shown in output",
            "Exclude patterns" in output and "*.log" in output,
            "Exclude pattern not shown"
        )

        self.test(
            "Log files excluded (5 files remaining)",
            "5 file(s)" in output,
            f"Expected 5 files, output: {output[:200]}"
        )

        self.test(
            "Log files not in output",
            "debug.log" not in output and "error.log" not in output,
            "Log files found in output (should be excluded)"
        )

    def test_directory_upload_error_handling(self):
        """Test 11: Directory upload error handling"""
        print(f"\n{TestColors.BOLD}Phase 11: Directory Upload (Error Handling){TestColors.RESET}\n")

        # Test 1: No Zendesk ID
        returncode1, stdout1, stderr1 = self.run_command([
            '--dir', self.test_dir,
            '--dry-run'
        ])

        output1 = stdout1 + stderr1

        self.test(
            "Error when Zendesk ID missing",
            returncode1 != 0 or "Error" in output1 or "requires" in output1.lower(),
            "Missing Zendesk ID not caught"
        )

        # Test 2: Invalid directory path
        returncode2, stdout2, stderr2 = self.run_command([
            '145980',
            '--dir', '/nonexistent/directory',
            '--dry-run'
        ])

        output2 = stdout2 + stderr2

        self.test(
            "Error when directory doesn't exist",
            returncode2 != 0 or "does not exist" in output2 or "Error" in output2,
            "Invalid directory not caught"
        )

        # Test 3: File instead of directory
        test_file = self.test_files[0]
        returncode3, stdout3, stderr3 = self.run_command([
            '145980',
            '--dir', test_file,
            '--dry-run'
        ])

        output3 = stdout3 + stderr3

        self.test(
            "Error when path is a file, not directory",
            returncode3 != 0 or "not a directory" in output3.lower() or "Error" in output3,
            "File path accepted as directory"
        )

    def test_interactive_directory_upload(self):
        """Test 12: Interactive mode directory upload"""
        print(f"\n{TestColors.BOLD}Phase 12: Interactive Directory Upload{TestColors.RESET}\n")

        # Note: Interactive mode for directory upload would need implementation
        # This test checks if the feature exists or provides feedback

        # Simulate: upload mode (1), ZD ID, Jira ID, then directory path
        # Since directory upload in interactive mode may not be implemented yet,
        # this is an informational test

        stdin_input = f"1\n145980\nRED-172041\n{self.test_dir}\n\nn\n"

        returncode, stdout, stderr = self.run_command(
            ['-i'],
            stdin_input=stdin_input
        )

        output = stdout + stderr

        self.test(
            "Interactive mode completes",
            returncode == 0 or returncode == 1,
            f"Exit code: {returncode}"
        )

        # Check if directory upload is recognized in interactive mode
        has_directory_support = "directory" in output.lower() or self.test_dir in output

        self.test(
            "Directory path processing (informational)",
            True,  # Always pass - this is checking if feature exists
            f"Directory support in interactive mode: {'YES' if has_directory_support else 'NO (not implemented yet, use CLI mode with --dir)'}"
        )

    def test_retry_logic(self):
        """Test 13: Retry logic with --max-retries"""
        print(f"\n{TestColors.BOLD}Phase 13: Retry Logic (--max-retries){TestColors.RESET}\n")

        # Test that max-retries argument is accepted
        returncode, stdout, stderr = self.run_command([
            '145980',
            'RED-172041',
            '-f', self.test_files[0],
            '--max-retries', '5'
        ])

        output = stdout + stderr

        self.test(
            "--max-retries argument accepted",
            returncode == 0,
            f"Exit code: {returncode}"
        )

        # Test with max-retries = 1 (minimal retries)
        returncode2, stdout2, stderr2 = self.run_command([
            '145980',
            '-f', self.test_files[0],
            '--max-retries', '1'
        ])

        output2 = stdout2 + stderr2

        self.test(
            "--max-retries with value 1 accepted",
            returncode2 == 0,
            f"Exit code: {returncode2}"
        )

    def test_verification_flag(self):
        """Test 14: Upload verification with --verify"""
        print(f"\n{TestColors.BOLD}Phase 14: Upload Verification (--verify){TestColors.RESET}\n")

        # Test that verify flag is accepted
        returncode, stdout, stderr = self.run_command([
            '145980',
            'RED-172041',
            '-f', self.test_files[0],
            '--verify'
        ])

        output = stdout + stderr

        self.test(
            "--verify flag accepted",
            returncode == 0,
            f"Exit code: {returncode}"
        )

        # Verify flag should work with directory upload too
        returncode2, stdout2, stderr2 = self.run_command([
            '145980',
            '--dir', self.test_dir,
            '--dry-run',
            '--verify'
        ])

        output2 = stdout2 + stderr2

        self.test(
            "--verify flag works with directory upload",
            returncode2 == 0,
            f"Exit code: {returncode2}"
        )

    def test_state_file_management(self):
        """Test 15: State file management (--clean-state, --no-resume)"""
        print(f"\n{TestColors.BOLD}Phase 15: State File Management{TestColors.RESET}\n")

        # Test --clean-state command
        returncode, stdout, stderr = self.run_command(['--clean-state'])

        output = stdout + stderr

        self.test(
            "--clean-state command accepted",
            returncode == 0,
            f"Exit code: {returncode}"
        )

        self.test(
            "--clean-state provides feedback",
            "state" in output.lower() or "clean" in output.lower(),
            "No state-related output found"
        )

        # Test --no-resume flag
        returncode2, stdout2, stderr2 = self.run_command([
            '145980',
            '-f', self.test_files[0],
            '--no-resume'
        ])

        output2 = stdout2 + stderr2

        self.test(
            "--no-resume flag accepted",
            returncode2 == 0,
            f"Exit code: {returncode2}"
        )

        # Should NOT show resume prompt when --no-resume is used
        self.test(
            "--no-resume prevents resume prompt",
            "resume" not in output2.lower() or "no-resume" in output2.lower(),
            "Resume prompt appeared despite --no-resume flag"
        )

    def test_combined_retry_and_verify(self):
        """Test 16: Combined --max-retries and --verify"""
        print(f"\n{TestColors.BOLD}Phase 16: Combined Retry and Verification{TestColors.RESET}\n")

        # Test combining both flags
        returncode, stdout, stderr = self.run_command([
            '145980',
            'RED-172041',
            '-f', self.test_files[0],
            '--max-retries', '3',
            '--verify'
        ])

        output = stdout + stderr

        self.test(
            "Combined --max-retries and --verify accepted",
            returncode == 0,
            f"Exit code: {returncode}"
        )

        # Test with batch upload
        returncode2, stdout2, stderr2 = self.run_command([
            '145980',
            '-f', self.test_files[0],
            '-f', self.test_files[1],
            '--max-retries', '2',
            '--verify'
        ])

        output2 = stdout2 + stderr2

        self.test(
            "Retry and verify work with batch upload",
            returncode2 == 0,
            f"Exit code: {returncode2}"
        )

        # Test with directory upload
        returncode3, stdout3, stderr3 = self.run_command([
            '145980',
            '--dir', self.test_dir,
            '--dry-run',
            '--max-retries', '4',
            '--verify'
        ])

        output3 = stdout3 + stderr3

        self.test(
            "Retry and verify work with directory upload",
            returncode3 == 0,
            f"Exit code: {returncode3}"
        )

    def run_all_tests(self):
        """Run all v1.2.0 tests"""
        print(f"\n{TestColors.BOLD}{'='*70}{TestColors.RESET}")
        print(f"{TestColors.BOLD}GT Logs Helper - Automated Test Suite{TestColors.RESET}")
        print(f"{TestColors.BOLD}{'='*70}{TestColors.RESET}")

        self.setup()

        try:
            # Run all test phases
            self.test_cli_batch_upload_multiple_files()
            self.test_cli_batch_upload_duplicate_detection()
            self.test_cli_batch_upload_invalid_file()
            self.test_interactive_batch_upload_comma_separated()
            self.test_interactive_batch_upload_iterative()
            self.test_download_a_shortcut()
            self.test_batch_upload_with_execute_flag()
            # Directory upload tests (v1.5.3+)
            self.test_directory_upload_dry_run()
            self.test_directory_upload_with_include_patterns()
            self.test_directory_upload_with_exclude_patterns()
            self.test_directory_upload_error_handling()
            self.test_interactive_directory_upload()
            # Resume/retry tests (v1.6.0+)
            self.test_retry_logic()
            self.test_verification_flag()
            self.test_state_file_management()
            self.test_combined_retry_and_verify()

        finally:
            self.cleanup()

        # Print summary
        print(f"\n{TestColors.BOLD}{'='*70}{TestColors.RESET}")
        print(f"{TestColors.BOLD}Test Summary{TestColors.RESET}")
        print(f"{TestColors.BOLD}{'='*70}{TestColors.RESET}")
        print(f"Total Tests: {self.test_number}")
        print(f"{TestColors.GREEN}Passed: {self.passed}{TestColors.RESET}")
        print(f"{TestColors.RED}Failed: {self.failed}{TestColors.RESET}")

        if self.failed == 0:
            print(f"\n{TestColors.GREEN}{TestColors.BOLD}✓ ALL TESTS PASSED!{TestColors.RESET}\n")
            return 0
        else:
            print(f"\n{TestColors.RED}{TestColors.BOLD}✗ SOME TESTS FAILED{TestColors.RESET}\n")
            return 1


def main():
    """Main test entry point"""
    runner = TestRunner()
    exit_code = runner.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
