# Auto-Update Feature Test Plan

## Overview

This document outlines the comprehensive testing strategy for the auto-update mechanism in GT Logs Link Generator v1.0.0.

**Test Environment:**
- macOS (primary)
- Python 3.6+
- Git repository with GitHub access
- Internet connectivity (and ability to simulate offline)

---

## Test Scenarios

### 1. Startup Auto-Update Check (Happy Path)

**Objective:** Verify automatic update check when script starts

**Prerequisites:**
- Current version: v1.0.0
- Available version: v1.0.1 (or newer) published on GitHub

**Steps:**
1. Run script in interactive mode: `./gtlogs-generator.py`
2. Observe startup message: "🔍 Checking for updates..."
3. Verify update prompt appears with correct version numbers
4. Choose 'y' (yes) to install update

**Expected Results:**
- ✅ Update check completes within 5 seconds
- ✅ Prompt shows: "Update available: v1.0.0 → v1.0.1"
- ✅ Release notes displayed (first 3 lines)
- ✅ Download progress shown
- ✅ Backup created: `gtlogs-generator.py.backup`
- ✅ Update successful message displayed
- ✅ Script exits with message to restart
- ✅ After restart, version is v1.0.1
- ✅ Backup file still exists

**Test Data:**
```bash
# Verify version before
./gtlogs-generator.py --version
# Expected: GT Logs Link Generator v1.0.0

# Run update
./gtlogs-generator.py
# Follow prompts, choose 'y'

# Verify version after
./gtlogs-generator.py --version
# Expected: GT Logs Link Generator v1.0.1

# Verify backup exists
ls -la gtlogs-generator.py.backup
```

---

### 2. Manual Update Check via --version Flag

**Objective:** Verify `--version` flag triggers update check

**Steps:**
1. Run: `./gtlogs-generator.py --version`
2. Observe version display and update check
3. If update available, choose 'y' to update

**Expected Results:**
- ✅ Version displayed: "GT Logs Link Generator v1.0.0"
- ✅ Update check message: "🔍 Checking for updates..."
- ✅ If up to date: "✓ You're up to date!"
- ✅ If update available: prompt with version and release notes
- ✅ Update process same as startup check

---

### 3. Manual Update Check via Ctrl+U in Interactive Mode

**Objective:** Verify Ctrl+U works on all interactive prompts

**Steps:**
1. Run: `./gtlogs-generator.py`
2. At "Enter Zendesk ticket ID" prompt, press **Ctrl+U**
3. Verify update check triggers
4. Restart and test Ctrl+U at different prompts:
   - Jira ID prompt
   - File path prompt
   - AWS profile prompt
   - "Try again?" prompt

**Expected Results:**
- ✅ Ctrl+U detected immediately (no Enter needed)
- ✅ Update check runs: "🔍 Checking for updates..."
- ✅ If update available: prompt appears
- ✅ If up to date: "✓ You're up to date! (v1.0.0)"
- ✅ Message: "Please restart the script to continue."
- ✅ Script exits gracefully
- ✅ History saved before exit

**Edge Case:** Test Ctrl+U while typing input
```
Enter Zendesk ticket ID: ZD-1459<Ctrl+U>
# Should trigger update check, current input discarded
```

---

### 4. Update Prompt Options (y/n/s)

**Objective:** Verify all three response options work correctly

**Test 4a: Choose 'y' (yes)**
1. Trigger update check (any method)
2. Enter 'y' when prompted
3. Verify update installs

**Expected Results:**
- ✅ Update downloads and installs
- ✅ Backup created
- ✅ Success message displayed
- ✅ Script exits

**Test 4b: Choose 'n' (no)**
1. Trigger update check
2. Enter 'n' when prompted
3. Continue using script

**Expected Results:**
- ✅ Message: "Update cancelled."
- ✅ Script continues normally
- ✅ Next run will ask again

**Test 4c: Choose 's' (skip this session)**
1. Trigger update check via startup
2. Enter 's' when prompted
3. Script continues to interactive mode
4. Exit and restart script

**Expected Results:**
- ✅ Message: "Skipping update for this session."
- ✅ Script continues to interactive mode
- ✅ Update check does NOT repeat in same session
- ✅ Next script run WILL check again (skip not persisted)

**Test 4d: Invalid response**
1. Trigger update check
2. Enter invalid response (e.g., 'x', '123')

**Expected Results:**
- ✅ Treated same as 'n' (no)
- ✅ Message: "Update cancelled."

---

### 5. Offline Behavior

**Objective:** Verify graceful failure when offline

**Prerequisites:**
- Disable internet connection OR block GitHub domains

**Test 5a: Startup check while offline**
1. Disable internet
2. Run: `./gtlogs-generator.py`

**Expected Results:**
- ✅ Update check message appears briefly
- ✅ No error message displayed (silent failure)
- ✅ Script continues to interactive mode without delay
- ✅ No interruption to workflow

**Test 5b: --version while offline**
1. Disable internet
2. Run: `./gtlogs-generator.py --version`

**Expected Results:**
- ✅ Version displayed
- ✅ Update check message appears
- ✅ Warning: "⚠️  Could not check for updates (offline or API error)"
- ✅ Script exits normally

**Test 5c: Ctrl+U while offline**
1. Disable internet
2. Run interactive mode, press Ctrl+U

**Expected Results:**
- ✅ Warning: "⚠️  Could not check for updates (offline or API error)"
- ✅ Script exits, prompts restart

---

### 6. Update Failure and Rollback

**Objective:** Verify automatic rollback on update failures

**Test 6a: Simulate download failure**

**Setup:** Manually edit script to use invalid download URL temporarily:
```python
# In check_for_updates(), temporarily change:
download_url = "https://raw.githubusercontent.com/INVALID/..."
```

**Steps:**
1. Trigger update
2. Choose 'y' to update

**Expected Results:**
- ✅ Error message: "❌ Download failed: HTTP 404 Not Found"
- ✅ Rollback message: "✓ Rolled back to previous version"
- ✅ Script file unchanged (still v1.0.0)
- ✅ Temp files cleaned up
- ✅ Can continue using script normally

**Test 6b: Simulate file permission error**

**Setup:**
```bash
# Make script directory read-only
chmod 555 .
```

**Steps:**
1. Trigger update
2. Choose 'y' to update

**Expected Results:**
- ✅ Error message: "❌ File operation failed: [Permission denied]"
- ✅ Rollback attempted
- ✅ Manual recovery message if rollback fails

**Cleanup:**
```bash
chmod 755 .
```

**Test 6c: Corrupted download**

**Objective:** Verify behavior if downloaded file is invalid Python

**Setup:** Requires mocking or intercepting download to return invalid content

**Expected Results:**
- ✅ Update appears to succeed initially
- ✅ On next run, Python execution fails
- ✅ User can manually restore from backup

---

### 7. Backup File Management

**Objective:** Verify backup file handling

**Test 7a: Backup file creation**
1. Trigger update and install
2. Check for backup file

**Expected Results:**
- ✅ Backup file exists: `gtlogs-generator.py.backup`
- ✅ Backup contains previous version (v1.0.0)
- ✅ Backup is executable
- ✅ Backup file size matches original

**Test 7b: Multiple updates (backup overwrite)**
1. Update from v1.0.0 to v1.0.1
2. Later update from v1.0.1 to v1.0.2

**Expected Results:**
- ✅ First update: backup contains v1.0.0
- ✅ Second update: backup contains v1.0.1 (old backup replaced)
- ✅ Only one backup file exists at a time

**Test 7c: Manual rollback**
1. After update, manually rollback:
   ```bash
   mv gtlogs-generator.py.backup gtlogs-generator.py
   chmod +x gtlogs-generator.py
   ./gtlogs-generator.py --version
   ```

**Expected Results:**
- ✅ Script restored to previous version
- ✅ Script executable and functional
- ✅ Version shows previous version number

---

### 8. File Permissions After Update

**Objective:** Verify script remains executable after update

**Steps:**
1. Check permissions before update:
   ```bash
   ls -l gtlogs-generator.py
   # Expected: -rwxr-xr-x (755)
   ```
2. Perform update
3. Check permissions after update:
   ```bash
   ls -l gtlogs-generator.py
   ```

**Expected Results:**
- ✅ Before: `-rwxr-xr-x` (executable)
- ✅ After: `-rwxr-xr-x` (still executable)
- ✅ Script can be run directly: `./gtlogs-generator.py`

---

### 9. Version Comparison Logic

**Objective:** Verify correct version detection

**Test 9a: Versions equal (no update)**
- Current: v1.0.0
- Latest: v1.0.0

**Expected Results:**
- ✅ Message: "✓ You're up to date!"
- ✅ No update prompt

**Test 9b: Newer version available**
- Current: v1.0.0
- Latest: v1.0.1

**Expected Results:**
- ✅ Update prompt appears
- ✅ Shows: "v1.0.0 → v1.0.1"

**Test 9c: Tag with 'v' prefix**
- GitHub tag: `v1.0.1` (with v)
- Script VERSION: `1.0.0` (without v)

**Expected Results:**
- ✅ Version comparison works correctly (v stripped)
- ✅ Update detected

**Note:** Current implementation uses simple string comparison. If semantic versioning becomes complex (e.g., v1.10.0 vs v1.9.0), this may need improvement.

---

### 10. Integration with Existing Features

**Objective:** Verify auto-update doesn't break other features

**Test 10a: Update check + history saving**
1. Run interactive mode
2. Enter valid Zendesk ID (will be saved to history)
3. Trigger update via Ctrl+U
4. Restart script

**Expected Results:**
- ✅ History saved before exit
- ✅ On restart, UP arrow shows previous Zendesk ID

**Test 10b: Update during command-line mode**
1. Run: `./gtlogs-generator.py 145980 RED-172041`

**Expected Results:**
- ✅ NO update check on command-line mode (only interactive)
- ✅ Command executes normally

**Test 10c: Update with --set-profile**
1. Run: `./gtlogs-generator.py --set-profile gt-logs`

**Expected Results:**
- ✅ NO update check for config commands
- ✅ Config saved successfully

---

### 11. Timeout Handling

**Objective:** Verify timeouts work correctly

**Test 11a: GitHub API timeout (5 seconds)**

**Setup:** Simulate slow network (requires network throttling or firewall rules)

**Expected Results:**
- ✅ Update check fails after 5 seconds
- ✅ Script continues without blocking
- ✅ Warning message (if using --version)
- ✅ Silent failure (if startup check)

**Test 11b: Download timeout (10 seconds)**

**Setup:** Trigger update but simulate slow download

**Expected Results:**
- ✅ Download fails after 10 seconds
- ✅ Error message displayed
- ✅ Rollback performed
- ✅ Script remains functional

---

### 12. Release Notes Display

**Objective:** Verify release notes shown correctly

**Prerequisites:**
- GitHub release with body text:
  ```markdown
  ## What's New
  - Feature 1
  - Bug fix 2
  - Performance improvement
  - Extra line (should not show)
  ```

**Steps:**
1. Trigger update check

**Expected Results:**
- ✅ Shows first 3 non-empty lines:
  ```
  Changes:
  - Feature 1
  - Bug fix 2
  - Performance improvement
  ```
- ✅ Empty lines ignored
- ✅ Lines beyond 3 truncated

---

### 13. Error Logging

**Objective:** Verify error messages are helpful

**Test various failure scenarios and verify error messages:**

| Scenario | Expected Error Message |
|----------|------------------------|
| GitHub API unreachable | `⚠️  Could not check for updates (offline or API error)` |
| Download 404 | `❌ Download failed: HTTP 404 Not Found` |
| Download timeout | `❌ Download failed: ...` |
| File permission error | `❌ File operation failed: [Permission denied]` |
| Unexpected exception | `❌ Unexpected error during update: ...` |
| Rollback failed | `⚠️  Rollback failed: ...` + `⚠️  Manual recovery: restore from ...` |

**Expected Results:**
- ✅ All error messages go to stderr
- ✅ Error messages are clear and actionable
- ✅ User can understand what went wrong

---

## Testing Tools & Commands

### Quick Test Commands

```bash
# Check current version
./gtlogs-generator.py --version

# Test startup check (interactive mode)
./gtlogs-generator.py

# Test Ctrl+U (press Ctrl+U at any prompt)
./gtlogs-generator.py
# (Ctrl+U)

# Verify backup exists
ls -la gtlogs-generator.py.backup

# Manual rollback
mv gtlogs-generator.py.backup gtlogs-generator.py
chmod +x gtlogs-generator.py

# Simulate offline (macOS)
sudo ifconfig en0 down  # Disable WiFi
sudo ifconfig en0 up    # Re-enable WiFi

# Check file permissions
ls -l gtlogs-generator.py

# View GitHub releases
gh release list

# View latest release details
gh release view --json tagName,body

# Test with Python directly (no shebang issues)
python3 gtlogs-generator.py --version
```

### Debugging Commands

```bash
# Enable Python verbose mode
python3 -v gtlogs-generator.py --version

# Run with explicit Python version
python3.9 gtlogs-generator.py --version

# Check for import errors
python3 -c "import urllib.request; import urllib.error; import json"

# Verify GitHub API access
curl -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/markotrapani/gtlogs-link-generator/releases/latest

# Verify raw download URL
curl https://raw.githubusercontent.com/markotrapani/gtlogs-link-generator/v1.0.0/gtlogs-generator.py -I
```

---

## Test Execution Checklist

### Pre-Testing Setup
- [ ] Ensure v1.0.0 is current version
- [ ] Create v1.0.1 test release on GitHub
- [ ] Verify internet connectivity
- [ ] Backup current script (copy to safe location)

### Core Functionality Tests
- [ ] Test 1: Startup auto-update check (happy path)
- [ ] Test 2: Manual check via --version
- [ ] Test 3: Manual check via Ctrl+U
- [ ] Test 4: All prompt options (y/n/s)
- [ ] Test 5: Offline behavior
- [ ] Test 6: Update failure & rollback
- [ ] Test 7: Backup file management
- [ ] Test 8: File permissions after update
- [ ] Test 9: Version comparison logic

### Integration Tests
- [ ] Test 10: Integration with history feature
- [ ] Test 11: Timeout handling
- [ ] Test 12: Release notes display
- [ ] Test 13: Error logging

### Post-Testing Cleanup
- [ ] Remove test releases from GitHub
- [ ] Restore original script if needed
- [ ] Document any issues found
- [ ] Update test plan based on findings

---

## Known Limitations & Future Improvements

### Current Limitations
1. **Simple version comparison** - Uses string equality, not semantic versioning
2. **No progress bar** - Large downloads show no progress indicator
3. **No checksum verification** - Downloaded file not verified for integrity
4. **Single backup** - Only keeps most recent backup, not multiple versions
5. **No automatic restart** - User must manually restart after update

### Potential Improvements
1. Implement proper semantic version comparison
2. Add download progress indicator for large files
3. Verify downloaded file checksum/signature
4. Keep last N backups instead of just one
5. Add option to automatically restart script after update
6. Add `--no-update-check` flag to skip check on demand
7. Cache update check results for X minutes to avoid repeated API calls

---

## Success Criteria

The auto-update feature is considered **production-ready** if:

✅ All happy path tests pass (Tests 1-3)
✅ All prompt options work correctly (Test 4)
✅ Offline behavior is graceful (Test 5)
✅ Rollback works on failures (Test 6)
✅ Backups created correctly (Test 7)
✅ Permissions maintained (Test 8)
✅ No breaking changes to existing features (Test 10)
✅ Error messages are clear and helpful (Test 13)

---

## Test Results Template

```markdown
## Test Execution Results - [Date]

**Tester:** [Name]
**Environment:** [OS, Python version]
**Test Duration:** [Time]

### Test Results Summary
- Total Tests: 13
- Passed: X
- Failed: X
- Blocked: X

### Individual Test Results

#### Test 1: Startup Auto-Update Check
- Status: ✅ PASS / ❌ FAIL
- Notes: [Any observations]

#### Test 2: Manual Update via --version
- Status: ✅ PASS / ❌ FAIL
- Notes: [Any observations]

[... continue for all tests ...]

### Issues Found
1. [Issue description]
   - Severity: High/Medium/Low
   - Steps to reproduce: ...
   - Expected: ...
   - Actual: ...

### Recommendations
- [Any recommendations based on testing]
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-12
**Author:** Claude Code

---

## Test Releases

### v1.0.8
This version fixes the duplicate "Please restart the script to use the new version" message that appeared when updating via Ctrl+U. The message is now only printed once by `perform_self_update()`.

### v1.0.7
This version is a test release to enable end-to-end testing of the complete update flow from v1.0.6.

### v1.0.6
This version fixed the Ctrl+U behavior when user chooses 'n' - the script now returns to interactive mode instead of forcing a restart.

### v1.0.5
This version fixed the Ctrl+U behavior when no update is available or when offline - the script now returns to interactive mode instead of forcing a restart.

### v1.0.4
This version is a test release to enable testing the improved update UX from v1.0.3. Use this to test:
- Update flow from v1.0.3 → v1.0.4
- --version / -v flag shows update without prompting
- Ctrl+U functionality during interactive mode
- Simplified y/n update prompt behavior in interactive mode

### v1.0.3
This version improved the update UX:
- Simplified update prompt from y/n/s to y/n only
- --version flag now informational only (no interactive prompt)
- Added -v shorthand flag
- 'n' option continues to interactive mode without exiting

### v1.0.2
This version simplified the update prompt from y/n/s to y/n only. The 'n' option continues to interactive mode without exiting.

### v1.0.1
This version is a test release to verify the auto-update mechanism works correctly. The only change from v1.0.0 is the VERSION constant and test plan notes.
