# GT Logs Helper - Roadmap

This document outlines the development roadmap and feature priorities for GT Logs Helper.

## Current Version: v1.2.0

### Recently Completed (v1.2.0)

- ✅ **Batch Upload Support** - Upload multiple files simultaneously to the same S3 destination
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

These features address common user requests and workflow improvements:

- **[ ] Directory Upload** - Upload entire directories recursively
  - Preserve directory structure in S3
  - Pattern-based filtering (e.g., exclude *.log files)
  - Dry-run mode to preview uploads

- **[ ] Upload Resume/Retry** - Handle interrupted uploads
  - Detect partially uploaded files
  - Resume from last successful file in batch
  - Automatic retry with exponential backoff

- **[ ] Progress Bars** - Visual progress for large file transfers
  - Show transfer speed and ETA
  - Support for concurrent uploads

### Medium Priority

Enhancements that improve usability and automation:

- **[ ] S3 File Management** - Basic file operations
  - List all files in a ticket's directory
  - Delete files from S3
  - Copy/move between S3 paths

- **[ ] Template Configurations** - Save common upload scenarios
  - Save ZD+Jira combinations
  - Quick recall of frequent paths
  - Export/import configurations

- **[ ] Verification** - Post-upload validation
  - Verify file exists in S3 after upload
  - Compare file sizes/checksums
  - Generate shareable S3 presigned URLs

- **[ ] Shell Completion** - Tab completion support
  - Bash completion script
  - Zsh completion script
  - Fish completion script

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

## Future Considerations

Ideas under evaluation for future versions:

- Multi-region S3 support
- Encryption at rest/in-transit options
- Integration with Zendesk API for automatic ticket attachment
- Parallel uploads for batch operations
- Compression before upload option
- Smart file naming (auto-append timestamps)

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

## Contributing Ideas

Have a feature request or idea? Please:

1. Check if it's already on the roadmap
2. Open an issue on GitHub with:
   - Clear use case description
   - Expected behavior
   - Priority/impact assessment
3. For major features, discuss before implementation

## Roadmap Updates

This roadmap is reviewed and updated with each release. Priorities may shift based on:

- User feedback and feature requests
- Critical bugs or security issues
- Changes in AWS S3 APIs or authentication
- Team workflow changes

---

**Last Updated:** 2025-01-13 (v1.2.0 release)
