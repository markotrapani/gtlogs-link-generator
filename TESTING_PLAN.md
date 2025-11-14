# GT Logs Helper v1.1.0 - Comprehensive Testing Plan

## Overview
This testing plan covers all functionality added in v1.1.0, including the new download mode, AWS profile handling fixes, and the rename from GT Logs Link Generator to GT Logs Helper.

---

## 1. Basic Functionality Tests

### 1.1 Version and Help
```bash
# Should show v1.1.0
./gtlogs-helper.py --version

# Should show help with upload/download options
./gtlogs-helper.py -h
```

### 1.2 Configuration
```bash
# Show current config
./gtlogs-helper.py --show-config

# Set default profile
./gtlogs-helper.py --set-profile my-profile

# Verify it was saved
./gtlogs-helper.py --show-config
```

---

## 2. Interactive Mode Tests

### 2.1 Mode Selection
```bash
./gtlogs-helper.py
```
- [ ] Displays mode selection (1. Upload, 2. Download)
- [ ] Accepts input 1 for upload
- [ ] Accepts input 2 for download
- [ ] Rejects invalid input (3, abc, etc.)
- [ ] ESC key exits immediately
- [ ] Ctrl+C exits gracefully

### 2.2 Interactive Upload Mode
```bash
./gtlogs-helper.py
# Choose: 1
```

**Test inputs:**
- [ ] Valid ZD: `145980` → Should format to `ZD-145980`
- [ ] Pre-formatted ZD: `ZD-145980` → Should accept
- [ ] Invalid ZD: `abc123` → Should reject and retry
- [ ] Jira ID (optional): Press Enter → Should skip
- [ ] Valid Jira: `RED-172041` → Should accept
- [ ] Invalid Jira: `ABC-123` → Should reject
- [ ] File path: Enter valid file → Should validate
- [ ] File path: Enter non-existent → Should show error
- [ ] AWS Profile: Press Enter → Should use default/fallback
- [ ] Execute prompt: Y → Should attempt upload

### 2.3 Interactive Download Mode
```bash
./gtlogs-helper.py
# Choose: 2
```

**Test inputs:**
- [ ] Full S3 path: `s3://gt-logs/zendesk-tickets/ZD-145980/file.tar.gz`
- [ ] Ticket ID: `ZD-145980` → Should list files
- [ ] Ticket + Jira: `ZD-145980-RED-172041`
- [ ] Invalid path: `invalid-path` → Should show error
- [ ] File selection: `1,2` → Should parse correctly
- [ ] File selection: `all` → Should select all
- [ ] Output directory: Press Enter → Current directory
- [ ] Output directory: `~/Downloads/` → Should use specified

---

## 3. CLI Upload Mode Tests

### 3.1 Basic Generation
```bash
# ZD-only (no Jira)
./gtlogs-helper.py 145980

# ZD + Jira
./gtlogs-helper.py 145980 RED-172041

# With file path
./gtlogs-helper.py 145980 -f /path/to/file.tar.gz

# With custom profile
./gtlogs-helper.py 145980 -p my-profile

# With execution
echo "test" > test.txt
./gtlogs-helper.py 145980 -f test.txt --execute
rm test.txt
```

### 3.2 Input Validation
```bash
# Invalid ZD (should fail)
./gtlogs-helper.py abc123 RED-172041

# Invalid Jira (should fail)
./gtlogs-helper.py 145980 INVALID-123

# Non-existent file (should fail)
./gtlogs-helper.py 145980 -f /nonexistent/file.tar.gz

# Directory instead of file (should fail)
./gtlogs-helper.py 145980 -f /tmp
```

---

## 4. CLI Download Mode Tests

### 4.1 Download Commands
```bash
# Download specific file
./gtlogs-helper.py --download s3://gt-logs/zendesk-tickets/ZD-145980/file.tar.gz

# List files from ticket
./gtlogs-helper.py --download ZD-145980

# Download to specific directory
./gtlogs-helper.py --download ZD-145980 --output ~/Downloads/

# With custom profile
./gtlogs-helper.py --download ZD-145980 -p my-profile
```

### 4.2 Path Parsing
```bash
# Should parse correctly:
./gtlogs-helper.py --download s3://gt-logs/zendesk-tickets/ZD-145980/
./gtlogs-helper.py --download ZD-145980
./gtlogs-helper.py --download 145980
./gtlogs-helper.py --download ZD-145980-RED-172041
```

---

## 5. AWS Profile Tests

### 5.1 No Configuration
```bash
# Temporarily remove config
mv ~/.gtlogs-config.ini ~/.gtlogs-config.ini.backup

# Should use gt-logs fallback
./gtlogs-helper.py 145980

# Should not crash
./gtlogs-helper.py 145980 -f test.txt --execute

# Restore config
mv ~/.gtlogs-config.ini.backup ~/.gtlogs-config.ini
```

### 5.2 Invalid Profile
```bash
# Non-existent profile
./gtlogs-helper.py 145980 -p nonexistent-profile -f test.txt --execute
# Should show helpful error about missing profile
```

### 5.3 Authentication Flow
```bash
# Logout first (if possible)
aws sso logout --profile gt-logs

# Should trigger SSO login
./gtlogs-helper.py 145980 -f test.txt --execute
```

---

## 6. Keyboard Controls Test

### 6.1 ESC Key Handling
In interactive mode:
- [ ] Standalone ESC → Should exit immediately
- [ ] Arrow keys → Should NOT exit (properly ignored)
- [ ] ESC sequences → Should be distinguished from ESC

### 6.2 History Navigation
- [ ] UP arrow → Previous input
- [ ] DOWN arrow → Next input
- [ ] History persists across sessions

### 6.3 Other Controls
- [ ] Ctrl+C → Clean exit
- [ ] Ctrl+U → Check for updates
- [ ] Backspace → Delete character
- [ ] Type 'exit' or 'q' → Exit

---

## 7. Edge Cases

### 7.1 File Handling
```bash
# Spaces in filename
touch "test file with spaces.tar.gz"
./gtlogs-helper.py 145980 -f "test file with spaces.tar.gz"

# Special characters
touch "test@file#2024.tar.gz"
./gtlogs-helper.py 145980 -f "test@file#2024.tar.gz"

# Symlinks
ln -s test.txt test-link.txt
./gtlogs-helper.py 145980 -f test-link.txt
```

### 7.2 Network Issues
- [ ] No internet connection → Update check should fail gracefully
- [ ] AWS timeout → Should show timeout message
- [ ] S3 access denied → Should show clear error

---

## 8. Update Mechanism Test

### 8.1 Version Check
```bash
# Check for updates
./gtlogs-helper.py --version
# Should check GitHub and report if update available
```

### 8.2 Interactive Update (Ctrl+U)
- Start interactive mode
- Press Ctrl+U
- Should check for updates
- If available, should prompt to install

---

## 9. Performance Tests

### 9.1 Large File Handling
```bash
# Create large test file (100MB)
dd if=/dev/zero of=large_test.bin bs=1M count=100

# Test upload
./gtlogs-helper.py 145980 -f large_test.bin --execute

# Clean up
rm large_test.bin
```

### 9.2 Many Files in S3
- Test download mode with directory containing many files
- Verify listing performance
- Test selection of multiple files

---

## 10. Regression Tests

### 10.1 Backward Compatibility
- [ ] Old command formats still work
- [ ] Existing configs are read correctly
- [ ] History from previous versions loads

### 10.2 Core Features
- [ ] ZD-only paths generate correctly
- [ ] ZD+Jira paths generate correctly
- [ ] Input validation remains strict
- [ ] AWS SSO login triggers when needed

---

## Test Execution Checklist

### Phase 1: Basic Tests (No AWS Required)
- [ ] Version display
- [ ] Help output
- [ ] Command generation
- [ ] Input validation
- [ ] Config management

### Phase 2: AWS Tests (Requires Configuration)
- [ ] Authentication flow
- [ ] Actual uploads
- [ ] Actual downloads
- [ ] Profile switching
- [ ] Error handling

### Phase 3: Interactive Tests
- [ ] Mode selection
- [ ] Upload workflow
- [ ] Download workflow
- [ ] Keyboard controls
- [ ] History navigation

### Phase 4: Edge Cases
- [ ] Special characters
- [ ] Large files
- [ ] Network issues
- [ ] Invalid inputs

---

## Known Issues to Watch For

1. **Windows Compatibility**: ESC detection doesn't work on Windows (falls back to regular input)
2. **AWS CLI Required**: Tool requires AWS CLI to be installed
3. **Profile Names**: Some special characters in profile names might cause issues

---

## Success Criteria

- [ ] All basic functionality works as documented
- [ ] No crashes with invalid input
- [ ] Clear error messages for all failure cases
- [ ] AWS profile fallback prevents crashes
- [ ] Download mode works for all path formats
- [ ] Upload mode remains backward compatible
- [ ] Interactive mode is intuitive and responsive
- [ ] Keyboard controls work as expected (except Windows ESC)

---

## Testing Commands Summary

```bash
# Quick smoke test
./gtlogs-helper.py --version
./gtlogs-helper.py 145980 RED-172041
./gtlogs-helper.py --download ZD-145980

# Full test suite
bash run_all_tests.sh  # (if we create an automated test script)
```