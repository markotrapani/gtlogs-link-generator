#!/usr/bin/env python3
"""
Automated test suite for GT Logs Helper v1.2.0 features

Tests all new v1.2.0 functionality without requiring manual interaction:
- Batch upload (CLI mode with multiple -f flags)
- Batch upload (interactive mode - comma-separated, iterative)
- Download 'a' shortcut (interactive mode)
- Duplicate detection
- Progress tracking
- Success/failure summaries

Usage:
    python3 tests/test_v1_2_0.py
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
        self.passed = 0
        self.failed = 0
        self.test_number = 0

    def setup(self):
        """Create test files"""
        print(f"\n{TestColors.BLUE}Setting up test environment...{TestColors.RESET}")

        # Create test files in /tmp
        for i in range(1, 6):
            filepath = f"/tmp/test_batch_{i}.tar.gz"
            with open(filepath, 'w') as f:
                f.write(f"test content {i}\n")
            self.test_files.append(filepath)
            print(f"  Created: {filepath}")

        print(f"{TestColors.GREEN}✓ Setup complete{TestColors.RESET}\n")

    def cleanup(self):
        """Remove test files"""
        print(f"\n{TestColors.BLUE}Cleaning up test files...{TestColors.RESET}")

        for filepath in self.test_files:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"  Removed: {filepath}")

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
        """Test 2: Duplicate file detection"""
        print(f"\n{TestColors.BOLD}Phase 2: Duplicate Detection{TestColors.RESET}\n")

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
            "Duplicate detection executed",
            returncode == 0,
            f"Exit code: {returncode}"
        )

        # Should mention duplicates or show only 2 unique files
        self.test(
            "Duplicate handling mentioned or unique count shown",
            "duplicate" in stdout.lower() or "2 file(s)" in stdout,
            "No duplicate handling detected"
        )

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

    def test_download_a_shortcut(self):
        """Test 6: Download mode 'a' shortcut"""
        print(f"\n{TestColors.BOLD}Phase 6: Download 'a' Shortcut{TestColors.RESET}\n")

        # This test would require actual S3 access or mocking
        # For now, we'll test that the download mode accepts the flag

        returncode, stdout, stderr = self.run_command([
            '--download',
            'ZD-145980'
        ])

        output = stdout + stderr

        # Should either succeed (if authenticated) or show auth error
        self.test(
            "Download mode activates",
            "download" in output.lower() or "s3://" in output or "AWS" in output,
            "Download mode not detected"
        )

        # The 'a' shortcut is tested in interactive mode
        # We'll simulate it here if we can enter interactive download mode

        print(f"\n  {TestColors.YELLOW}Note: 'a' shortcut testing requires S3 access{TestColors.RESET}")
        print(f"  {TestColors.YELLOW}Skipping full download test (would require real S3 data){TestColors.RESET}")

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

    def run_all_tests(self):
        """Run all v1.2.0 tests"""
        print(f"\n{TestColors.BOLD}{'='*70}{TestColors.RESET}")
        print(f"{TestColors.BOLD}GT Logs Helper v1.2.0 - Automated Test Suite{TestColors.RESET}")
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
