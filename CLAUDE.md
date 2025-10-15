# CLAUDE.md - GT Logs Link Generator

**Project Type:** Python CLI Tool (Standalone utility)

This is a command-line tool for generating S3 bucket URLs and AWS CLI commands for Redis Support packages. It helps Redis Support engineers quickly create properly formatted S3 paths for sharing customer support packages securely with engineering teams.

---

## Project Overview

**Purpose:** Automate the generation of properly formatted S3 paths and AWS CLI upload commands for Redis Support packages

**Main Features:**

- Two upload scenarios: ZD-only (most common) and ZD+Jira (Engineering escalation)
- Interactive mode with guided prompts and ESC key support
- Command-line mode for quick generation
- Automatic AWS SSO authentication handling
- Input validation (Zendesk IDs, Jira IDs, file paths)
- Configuration persistence for default AWS profiles

**Technology Stack:**

- Python 3.6+ (standard library only - no external dependencies)
- AWS CLI (for executing generated commands)
- termios/tty (for enhanced keyboard input on Unix-like systems)

---

## Critical Development Guidelines

### 1. Input Validation - NEVER COMPROMISE

**ALL inputs MUST be strictly validated.** Do not bypass or weaken validation logic.

#### Zendesk ID Validation

- **Must be numerical only** (no letters, special chars except hyphen in prefix)
- **Accepted formats:** `145980`, `ZD-145980`, `zd-145980`
- **Output format:** `ZD-145980`
- **Validation function:** `validate_zendesk_id()` in [gtlogs-generator.py:70-87](gtlogs-generator.py#L70-L87)

#### Jira ID Validation

- **Must be RED-# or MOD-# with numerical suffix only**
- **Accepted formats:** `RED-172041`, `MOD-12345`, `RED172041` (auto-adds hyphen)
- **Output format:** `RED-172041` or `MOD-12345`
- **Validation function:** `validate_jira_id()` in [gtlogs-generator.py:90-108](gtlogs-generator.py#L90-L108)

#### File Path Validation

- **File must exist in filesystem**
- **Path must point to a file, not a directory**
- **Supports tilde expansion** (`~/Downloads/file.tar.gz`)
- **Validation function:** `validate_file_path()` in [gtlogs-generator.py:111-139](gtlogs-generator.py#L111-L139)

**WHY THIS MATTERS:**

- Invalid IDs break S3 bucket organization
- Invalid paths could cause upload failures or security issues
- Support engineers rely on consistent, predictable paths

---

### 2. S3 Path Generation Logic - DO NOT MODIFY WITHOUT REVIEW

**Two distinct S3 path structures exist for specific reasons:**

#### Without Jira (ZD-Only) - Most Common

```text
s3://gt-logs/zendesk-tickets/ZD-{ticket}/
```

**Use case:** Redis Cloud environments without Engineering involvement

#### With Jira (ZD + Jira) - Engineering Escalation

```text
s3://gt-logs/exa-to-gt/ZD-{ticket}-{jira}/
```

**Use case:** Sharing support packages with Engineering via Jira tickets

**Path generation function:** `generate_s3_path()` in [gtlogs-generator.py:141-154](gtlogs-generator.py#L141-L154)

**CRITICAL:** Do not change bucket names, path structures, or logic without explicit permission. These paths are relied upon by multiple teams and automation systems.

---

### 3. AWS Authentication Flow - Handle with Care

**Automatic authentication handling** is a key feature. The flow is:

1. **Check authentication** via `check_aws_authentication()` ([gtlogs-generator.py:191-210](gtlogs-generator.py#L191-L210))
2. **If not authenticated**, automatically run `aws_sso_login()` ([gtlogs-generator.py:213-236](gtlogs-generator.py#L213-L236))
3. **If login fails**, abort with clear error message
4. **If authenticated**, proceed with upload

**IMPORTANT:**

- Never skip authentication checks
- Always provide clear user feedback during SSO login
- Handle timeouts and failures gracefully
- Never store credentials or tokens

**Execution points:**

- Interactive mode: [gtlogs-generator.py:548-562](gtlogs-generator.py#L548-L562)
- CLI mode with `--execute`: [gtlogs-generator.py:697-710](gtlogs-generator.py#L697-L710)

---

### 4. Terminal Input Handling - ESC Key Detection

**Enhanced keyboard input** allows immediate ESC key exit without pressing Enter.

**Key implementation:** `input_with_esc_detection()` in [gtlogs-generator.py:309-416](gtlogs-generator.py#L309-L416)

**Features:**

- **ESC key** - Immediate exit (standalone ESC only)
- **Arrow keys** - Properly ignored (won't trigger exit)
- **Backspace** - Character deletion
- **Ctrl+C** - Exit
- **Enter** - Submit input
- Exit commands: `exit`, `quit`, `q`

**CRITICAL IMPLEMENTATION DETAILS:**

- Uses `termios` and `tty` for raw terminal mode (Unix-like systems only)
- **Timeout detection** distinguishes standalone ESC from escape sequences (arrow keys)
- **Always restore terminal settings** in finally block
- **Graceful fallback** to regular `input()` if `termios` unavailable (Windows, non-interactive)

**WHY THIS MATTERS:**

- Poor terminal handling can leave terminal in broken state
- Arrow keys should NOT trigger exit (common user error)
- Must work across different terminal emulators and SSH sessions

---

### 5. Configuration Management

**Default AWS profile** is stored in `~/.gtlogs-config.ini`

**Configuration functions:**

- `_load_config()` - [gtlogs-generator.py:45-50](gtlogs-generator.py#L45-L50)
- `_save_config()` - [gtlogs-generator.py:52-60](gtlogs-generator.py#L52-L60)
- `get_default_aws_profile()` - [gtlogs-generator.py:62-67](gtlogs-generator.py#L62-L67)

**CLI commands:**

- `--set-profile <profile>` - Save default profile
- `--show-config` - Display current config

**Best practices:**

- Never overwrite config without user confirmation
- Handle missing config files gracefully
- Provide clear success messages when saving config

---

## Common Development Tasks

### Adding a New Jira Prefix

**Example:** Add support for `ENG-` prefix in addition to `RED-` and `MOD-`

1. Update `validate_jira_id()` in [gtlogs-generator.py:90-108](gtlogs-generator.py#L90-L108)
2. Add `ENG` to regex patterns (lines 100, 105)
3. Update error messages to mention `ENG-`
4. Update README.md documentation:
   - Input Validation section
   - Jira ID Validation examples
   - Usage examples
5. Test with various formats: `ENG-12345`, `ENG12345`, `eng-12345`

### Adding a New CLI Argument

**Example:** Add `--dry-run` flag to show what would be uploaded without executing

1. Add argument to parser in `main()` ([gtlogs-generator.py:587-631](gtlogs-generator.py#L587-L631))
2. Implement logic in command execution flow
3. Add to README.md "Command Reference" section
4. Add to help text examples
5. Test in both interactive and CLI modes

### Modifying Terminal Input Behavior

**CAUTION:** Terminal input handling is complex and platform-specific

**Before modifying `input_with_esc_detection()`:**

1. Test on macOS, Linux, and if possible, Windows
2. Test in different terminal emulators (Terminal.app, iTerm2, SSH sessions)
3. Verify arrow keys don't trigger exit
4. Ensure terminal always restores to normal mode (even on exceptions)
5. Test fallback behavior when `termios` unavailable

---

## Testing Guidelines

### Manual Testing Checklist

#### Input Validation Testing

```bash
# Valid inputs
./gtlogs-generator.py 145980 RED-172041                    # Should succeed
./gtlogs-generator.py ZD-145980 RED172041                  # Should succeed
./gtlogs-generator.py 145980 MOD-12345                     # Should succeed

# Invalid inputs - must reject
./gtlogs-generator.py 145980abc RED-172041                 # Must fail: non-numerical ZD
./gtlogs-generator.py 145980 ABC-12345                     # Must fail: invalid Jira prefix
./gtlogs-generator.py 145980 RED-172041abc                 # Must fail: non-numerical Jira suffix
./gtlogs-generator.py 145980 12345                         # Must fail: missing Jira prefix
```

#### File Path Testing

```bash
# Create test file
echo "test" > /tmp/test-package.tar.gz

# Valid file path
./gtlogs-generator.py 145980 RED-172041 -f /tmp/test-package.tar.gz   # Should succeed

# Invalid file paths - must reject
./gtlogs-generator.py 145980 RED-172041 -f /nonexistent/file.tar.gz   # Must fail: file doesn't exist
./gtlogs-generator.py 145980 RED-172041 -f /tmp                       # Must fail: directory not file
```

#### Interactive Mode Testing

```bash
# Test keyboard controls
./gtlogs-generator.py
# - Press ESC (should exit immediately)
# - Press arrow keys (should be ignored, not exit)
# - Type "exit" (should exit)
# - Press Ctrl+C (should exit gracefully)
# - Enter invalid ZD (should prompt to retry)
# - Enter invalid file path (should offer retry)
```

#### AWS Authentication Testing

```bash
# Test with authenticated profile
aws sso login --profile gt-logs
./gtlogs-generator.py 145980 RED-172041 -f /tmp/test.tar.gz --execute
# Should: detect authentication, skip login, upload file

# Test with unauthenticated profile
aws sso logout --profile gt-logs  # (if logout command exists)
./gtlogs-generator.py 145980 RED-172041 -f /tmp/test.tar.gz --execute
# Should: detect no auth, run 'aws sso login', then upload
```

---

## Architecture Notes

### Code Organization

```text
gtlogs-generator.py
├── GTLogsGenerator class (main logic)
│   ├── validate_zendesk_id()     - Input validation
│   ├── validate_jira_id()        - Input validation
│   ├── validate_file_path()      - File validation
│   ├── generate_s3_path()        - S3 path generation
│   ├── generate_aws_command()    - AWS CLI command generation
│   ├── check_aws_authentication() - Auth check
│   ├── aws_sso_login()           - SSO login
│   └── execute_s3_upload()       - Upload execution
│
├── Terminal input helpers
│   ├── getch_timeout()           - Low-level char read with timeout
│   ├── getch()                   - Single char read
│   └── input_with_esc_detection() - Enhanced input with ESC support
│
├── User interaction
│   ├── check_exit_input()        - Exit command detection
│   └── interactive_mode()        - Interactive prompts and workflow
│
└── main()                        - CLI argument parsing and routing
```

### Design Decisions

1. **No external dependencies**
   - Easier deployment for support engineers
   - No pip install required
   - Uses only Python standard library

2. **Interactive mode as default**
   - Reduces errors from incorrect command-line args
   - Guides users through validation
   - More user-friendly for occasional use

3. **Automatic execution optional**
   - `--execute` flag or interactive prompt
   - Safety: generates commands first, executes only on confirmation
   - Automatic AWS SSO login reduces friction

4. **Configuration persistence**
   - Default AWS profile saved to `~/.gtlogs-config.ini`
   - Reduces repetitive typing
   - Optional override with `-p` flag

5. **Type annotations**
   - Added for Pylance type checking
   - Improves IDE support and code clarity
   - Recent additions: see commits `6e73fde`, `d60b0b3`, `78061c9`

---

## Known Issues & Limitations

### Current Limitations

1. **Windows Support for ESC Detection**

   - `termios`/`tty` unavailable on Windows
   - Falls back to regular `input()` (no immediate ESC)
   - Exit via Ctrl+C or typing "exit" still works

2. **AWS CLI Required**

   - Tool generates commands, but requires AWS CLI installed
   - No built-in S3 upload capability
   - Relies on user's AWS SSO configuration

3. **Single File Upload Only**

   - No support for batch uploads
   - No support for directory uploads
   - Each file requires separate command

### Future Enhancements (Potential)

- [ ] Batch upload support (multiple files)
- [ ] Progress bar for large file uploads
- [ ] Verification of S3 upload completion (check file exists)
- [ ] Support for additional Jira prefixes if needed
- [ ] Copy S3 path to clipboard after generation
- [ ] Shell completion scripts (bash/zsh)

---

## Debugging Tips

### Enable Debug Output

Add debug prints to key functions:

```python
# In validate_zendesk_id()
print(f"[DEBUG] Input ZD: '{zd_id}', Number part: '{zd_number}'")

# In check_aws_authentication()
print(f"[DEBUG] Running: {' '.join(cmd)}")
print(f"[DEBUG] Return code: {result.returncode}")

# In input_with_esc_detection()
print(f"[DEBUG] Raw char: {repr(ch)}")
```

### Common Issues

**Issue:** Arrow keys trigger exit

- **Cause:** ESC sequence timeout too short
- **Fix:** Increase `VTIME` in [gtlogs-generator.py:349](gtlogs-generator.py#L349)

**Issue:** Terminal broken after script crash

- **Cause:** Terminal settings not restored
- **Fix:** Run `reset` command to restore terminal

**Issue:** AWS authentication fails silently

- **Cause:** Timeout too short or AWS CLI not in PATH
- **Fix:** Check `timeout` in `check_aws_authentication()` ([gtlogs-generator.py:206](gtlogs-generator.py#L206))

**Issue:** File validation fails on valid paths

- **Cause:** Path expansion issue or permissions
- **Fix:** Check `os.path.expanduser()` and `os.path.exists()` results

---

## Git Workflow

### Commit Message Format

Follow conventional commit format:

```text
feat: Add support for ENG- Jira prefix
fix: Handle spaces in file paths correctly
docs: Update README with new --dry-run flag
refactor: Simplify terminal input handling
test: Add validation tests for Jira IDs
```

### Before Committing

**Always ask user permission before creating commits** (per CLAUDE.md guidelines)

**Pre-commit checklist:**

- [ ] All input validation still enforced
- [ ] Terminal input handling tested (ESC, arrow keys)
- [ ] README.md updated if features/usage changed
- [ ] Test with both interactive and CLI modes
- [ ] Test authentication flow if changed
- [ ] No debug print statements left in code

---

## Contact & Support

**Maintainer:** <marko.trapani@redis.com>

**For questions about:**

- S3 bucket structure → Contact Redis Support Engineering
- AWS SSO access → Contact Redis IT/Security
- Feature requests → Contact maintainer
- Bug reports → Contact maintainer

---

## Version History

**Current Status:** Stable production tool

**Recent improvements:**

- ESC key immediate exit support
- Automatic AWS SSO authentication handling
- ZD-only upload path support
- Enhanced type annotations for Pylance
- Improved keyboard controls (arrow keys properly ignored)

**See git history for detailed changes:**

```bash
git log --oneline
```

---

## References

- Main repository CLAUDE.md: [/CLAUDE.md](../CLAUDE.md)
- Project README: [README.md](README.md)
- AWS CLI Documentation: <https://docs.aws.amazon.com/cli/>
- Python termios: <https://docs.python.org/3/library/termios.html>
