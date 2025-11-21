# GT Logs Helper - Roadmap

This document outlines the development roadmap and feature priorities for
GT Logs Helper.

## Current Version: v1.7.0

### Recently Completed

#### v1.7.0 - Smart Input Detection & URL Decoding

- ✅ **Smart Clipboard Detection** - Automatic format recognition
  - New `detect_input_format()` function analyzes pasted input
  - Detects: Zendesk URLs, Jira URLs, S3 URIs, partial S3 paths, combined IDs,
    ticket IDs
  - Returns structured info: format type, description, parsed value, validity
  - Enables helpful user feedback and better error messages
  - 17 comprehensive test cases covering all input formats

- ✅ **URL Decoding** - Handles special characters in S3 paths
  - Uses `urllib.parse.unquote()` to decode URL-encoded characters
  - Examples: `%20` → space, `%2B` → `+`, `%2F` → `/`
  - Applied to all S3 path parsing operations
  - Seamless handling of paths copied from browsers or AWS console
  - Backward compatible with non-encoded paths

- ✅ **Enhanced Input Validation** - Better parsing and error handling
  - Whitespace trimming before processing
  - Combined URL decoding + format detection
  - All existing input formats remain backward compatible

#### v1.6.2 - Enhanced Input Format Support

- ✅ **Jira URL Support** - Paste Jira ticket URLs directly
  - Automatically extracts Jira ID from URLs
  - Supports `https://jira.company.com/browse/RED-172041` format
  - Works in both interactive and CLI modes
  - Case-insensitive matching

- ✅ **Partial S3 Path Support** - Paste S3 keys without full URIs
  - Recognizes `zendesk-tickets/` and `exa-to-gt/` prefixes
  - Automatically prepends `gt-logs` bucket
  - Examples: `zendesk-tickets/ZD-145980/file.tar.gz`
  - Reduces manual path construction

- ✅ **Tilde Expansion Fix** - `~` character now works in download paths
  - Fixed bug in CLI download output paths (`--output ~/Downloads`)
  - Fixed bug in interactive download directory selection
  - Fixed bug in interactive single file save paths
  - Error messages show both original and expanded paths

- ✅ **Improved Input Parsing** - Better handling of combined ZD+Jira formats
  - Enhanced `parse_s3_path()` to properly split and validate both parts
  - All existing input formats remain backward compatible

#### v1.6.1 - Performance & UX Improvements

- ✅ **Fast SSO Authentication** - Dramatically improved authentication speed
  - Local SSO cache validation (<100ms) before network calls
  - Reduced network timeout from 10s to 5s
  - Smart fallback to AWS STS API when cache is inconclusive

- ✅ **Debug Flag** - New `--debug` flag for troubleshooting
  - Shows detailed timing for authentication checks
  - Displays SSO cache validation steps
  - Optional - only enabled when explicitly requested

- ✅ **Zendesk URL Support** - Paste ticket URLs directly
  - Automatically extracts ticket ID from URLs
  - Supports `/agent/tickets/` and `/tickets/` paths
  - Works with any Zendesk subdomain
  - Clear error messages for invalid URLs

- ✅ **Full Path Display** - Downloads show complete absolute paths
- ✅ **Type Safety** - Fixed all Pylance warnings for better IDE support
- ✅ **Datetime Compatibility** - Fixed deprecation for Python 3.11+

#### v1.6.0 - Upload/Download Resume with Retry and Verification

- ✅ **Resume Capability** - Automatically resume interrupted uploads/downloads
  - JSON-based state management in `~/.gtlogs-state.json`
  - Tracks upload/download progress per file
  - Resume on next execution

- ✅ **Automatic Retry** - Exponential backoff for failed transfers
  - Configurable max retries (default: 3)
  - Retry delays: 1s, 2s, 4s, 8s... (max 60s)
  - New `--max-retries` CLI argument

- ✅ **Upload Verification** - S3 file size validation after upload
  - Verify file exists in S3
  - Compare local vs S3 file sizes
  - New `--verify` CLI flag

- ✅ **State Management** - Persistent tracking across interruptions
  - New `--no-resume` flag to skip saved state
  - New `--clean-state` flag to clean up state file

- ✅ **Critical Bug Fix** - Auto-update now uses proper semantic versioning

#### v1.5.3 - Directory Upload with Pattern Filtering

- ✅ **Directory Upload** - Upload entire directories recursively
  - Preserve directory structure in S3
  - Recursive file discovery
  - New `-D/--dir` CLI argument

- ✅ **Pattern Filtering** - Include/exclude files with wildcards
  - `--include` flag for whitelist patterns (e.g., `*.tar.gz`)
  - `--exclude` flag for blacklist patterns (e.g., `*.log`)
  - Multiple patterns supported

- ✅ **Dry-Run Mode** - Preview uploads before execution
  - Shows files that would be uploaded
  - Displays total file count and size
  - New `--dry-run` flag

- ✅ **Batch Progress** - Track upload progress for all files in directory

#### v1.5.2 - Real-Time Progress Tracking

- ✅ **Progress Bars** - Visual progress for uploads and downloads
  - Live progress display with percentage completion
  - File size tracking (completed/total bytes)
  - Transfer speed indicators (MB/s, KB/s)
  - Estimated time remaining (ETA) calculation
  - Graceful handling of small files (< 10MB)
  - No external dependencies (uses AWS CLI output parsing)

#### v1.5.x - Lightning-Fast UX + Documentation Overhaul

- ✅ **Auto-Submit Prompts** - Instant response without Enter key
  - Update prompt: Type 'y' or 'n' and go immediately
  - Mode selection: Type '1', 'u', '2', or 'd' without waiting
  - Smart defaults: Enter = Yes for updates, Upload for mode selection
  - Invalid input still validates and re-prompts

- ✅ **Enhanced Visual Design**
  - Cloud emoji icons for upload (☁️ ⬆️ ) and download (☁️ ⬇️ )
  - Clear mode selection with keyboard shortcuts
  - Consistent graceful exits (ESC/Ctrl+C → "👋 Exiting...")

- ✅ **Documentation Overhaul**
  - README reduced from 1315 to 415 lines (68% reduction)
  - Comprehensive GitHub wiki with 7 pages
  - Expand/collapse sections for better UX
  - Moved "What's New" section lower in README

### Previously Completed (v1.4.x - UX Polish)

- ✅ **Terminal Experience Improvements**
  - Fixed cursor positioning in raw terminal mode
  - Proper carriage return handling for all outputs
  - Consistent exit behavior across all prompts

- ✅ **Input Validation Enhancements**
  - Grouped equivalent choices in error messages (1/U or 2/D)
  - Re-prompting on invalid input instead of canceling
  - U/D keyboard shortcuts for mode selection

### Previously Completed (v1.3.0 - Testing Infrastructure)

- ✅ **Automated Testing Infrastructure** - Complete test suite with zero
  manual intervention
  - 16 automated tests with 100% pass rate
  - End-to-end (E2E) testing with real S3 bucket access
  - Automatic AWS SSO authentication in tests
  - Test file: `tests/test_suite.py`

- ✅ **Developer Experience Improvements** - Professional development workflow
  - Strict markdown linting enforced (80-character line limit)
  - MIT License for open collaboration
  - Complete CONTRIBUTING.md with guidelines
  - Comprehensive testing documentation

### Previously Completed (v1.2.0)

- ✅ **Batch Upload Support** - Upload multiple files simultaneously to the
  same S3 destination
  - Interactive mode: Comma-separated paths or add files one at a time
  - CLI mode: Multiple `-f` flags
  - Progress tracking with success/failure summary
  - Automatic duplicate detection

- ✅ **Download UX Improvements** - Press `a` as shortcut for downloading all files

### Previously Completed (v1.1.0)

- ✅ **Download Mode** - Complete S3 download functionality
  - Download from full S3 paths or ticket IDs
  - List and select files from directories
  - Batch download multiple files
  - Smart path parsing

- ✅ **Self-Update Capability** - Automatic version checking and updates
- ✅ **Input History** - Arrow key navigation through previous inputs
- ✅ **Enhanced Terminal Controls** - ESC key detection without Enter

## Planned Features

### High Priority

**Feature Development:**

_No high-priority features currently planned. Recent releases (v1.5.3 - v1.6.1)
completed directory upload, resume/retry, verification, and performance
improvements._

---

### Medium Priority

Enhancements that improve usability and automation:

- **[ ] Presigned URL Generation** - Shareable S3 download links
  - Generate temporary download URLs that expire after X hours
  - Share files with people who don't have AWS access (customers, external teams)
  - New `--generate-url` flag after successful upload
  - Note: Core verification (file size) completed in v1.6.0

- **[ ] S3 File Management** - Basic file operations
  - List all files in a ticket's directory (partially done - works in download mode)
  - Delete files from S3
  - Copy/move between S3 paths

- **[ ] Template Configurations** - Save common upload scenarios
  - Save ZD+Jira combinations
  - Quick recall of frequent paths
  - Export/import configurations

- **[ ] Shell Completion** - Tab completion support
  - Bash completion script
  - Zsh completion script
  - Fish completion script

---

### Low Priority

Nice-to-have features for advanced use cases:

- **[ ] Custom S3 Buckets** - Support for non-gt-logs buckets
  - Configurable bucket names
  - Custom path structures
  - Multi-bucket profiles

- **[ ] Logging and Audit Trail** - Track all operations
  - Log all uploads/downloads with timestamps
  - Export logs for auditing
  - Integration with centralized logging

- **[ ] GUI Mode** - Optional graphical interface
  - Simple desktop app wrapper
  - Drag-and-drop file selection
  - Visual progress tracking

- **[ ] Clipboard Integration** - Quick S3 path copying
  - Auto-copy generated S3 paths to clipboard
  - Paste S3 paths for downloads

---

## Future Considerations

Ideas under evaluation for future versions:

- Multi-region S3 support
- Encryption at rest/in-transit options
- Integration with Zendesk API for automatic ticket attachment
- Parallel uploads for batch operations
- Compression before upload option
- Smart file naming (auto-append timestamps)

---

## Completed Milestones

### v1.0.0 (Initial Release)

- ✅ Upload mode with ZD-only and ZD+Jira paths
- ✅ Input validation (Zendesk IDs, Jira IDs, file paths)
- ✅ Interactive and CLI modes
- ✅ AWS SSO authentication handling
- ✅ Configuration persistence

### v1.1.0 (Download Support)

- ✅ S3 download functionality
- ✅ Mode selection (Upload/Download)
- ✅ Batch download support
- ✅ Self-update capability
- ✅ Input history with arrow keys

### v1.2.0 (Batch Upload)

- ✅ Multi-file batch upload
- ✅ Download UX improvements (quick 'a' shortcut)

### v1.3.0 (Testing Infrastructure)

- ✅ Comprehensive automated test suite (16 tests)
- ✅ E2E testing with automatic AWS SSO authentication
- ✅ Strict markdown linting across all documentation
- ✅ MIT License and CONTRIBUTING.md

### v1.4.x (UX Polish)

- ✅ Terminal cursor positioning fixes in raw mode
- ✅ Improved error message clarity with grouped choices
- ✅ Enhanced mode selection with U/D keyboard shortcuts
- ✅ Cloud emoji icons for visual clarity
- ✅ Consistent ESC/Ctrl+C exit handling

### v1.5.x (Lightning-Fast UX + Documentation Overhaul)

- ✅ Auto-submit for update prompt (Y/n)
- ✅ Auto-submit for mode selection (1/U/2/D)
- ✅ Smart defaults (Enter = Yes/Upload)
- ✅ Instant feedback on valid inputs
- ✅ Enhanced exit message spacing
- ✅ README overhaul - 68% reduction (1315 → 415 lines)
- ✅ Comprehensive GitHub wiki with 7 pages
- ✅ Expand/collapse sections for better UX
- ✅ Moved "What's New" section lower in README

### v1.5.2 (Real-Time Progress Tracking)

- ✅ Progress bars for uploads and downloads
- ✅ Live transfer speed indicators (MB/s, KB/s)
- ✅ ETA calculation for file transfers
- ✅ File size tracking (completed/total bytes)
- ✅ Graceful handling of small files
- ✅ No external dependencies (AWS CLI output parsing)

## Contributing Ideas

Have a feature request or idea? Please:

1. Check if it's already on the roadmap
2. Open an issue on GitHub with:
   - Clear use case description
   - Expected behavior
   - Priority/impact assessment
3. For major features, discuss before implementation

## Roadmap Updates

This roadmap is reviewed and updated with each release. Priorities may shift
based on:

- User feedback and feature requests
- Critical bugs or security issues
- Changes in AWS S3 APIs or authentication
- Team workflow changes

---

**Last Updated:** 2025-01-17 (v1.6.1 release - Performance & UX improvements)
