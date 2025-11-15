# GT Logs Helper

A comprehensive command-line tool for uploading and downloading support
packages to/from the `gt-logs` S3 bucket. This tool streamlines the management
of customer support packages, generates properly formatted S3 paths, and
efficiently transfers files between local systems and AWS S3.

## Purpose

The `gt-logs` S3 bucket is used for storing and sharing customer support
packages. This tool provides a complete solution for:

- **Uploading** support packages with properly formatted S3 paths
- **Downloading** existing packages from S3 (new in v1.1.0!)
- **Generating** AWS CLI commands for manual operations
- **Managing** authentication and profiles

**Two upload scenarios supported:**

1. **Without Jira (ZD-only) - Most Common**
   For Redis Cloud environments without Engineering involvement:
   - S3 path: `s3://gt-logs/zendesk-tickets/ZD-<ticket>/`
   - Stores support packages for internal use

2. **With Jira (ZD + Jira) - Engineering Escalation**
   When sharing support packages with Engineering via Jira tickets:
   - S3 path: `s3://gt-logs/exa-to-gt/ZD-<ticket>-<jira>/`
   - Links Zendesk ticket to Jira issue
   - **Primary use:** Redis Cloud issues escalated to Engineering
   - **Also supports:** Redis Software issues (though less common,
     as @exatogt automation with Files.com handles most Redis Software
     uploads automatically)

## What's New in v1.5.1

**Lightning-Fast Interactive Experience:**

- ⚡ **Auto-submit inputs** - No more waiting for Enter on Y/n or mode selection
- 🎯 **Smart defaults** - Enter key defaults to "Y" for updates, "1" for upload mode
- 🔄 **Instant feedback** - Type 'y', 'n', '1', 'u', '2', or 'd' and go immediately
- 👋 **Graceful exits** - ESC/Ctrl+C handled consistently across all prompts
- ✨ **Enhanced UI** - Cloud emoji icons and cleaner mode selection display

**Previous Releases:**

**v1.4.x - UX Polish:**

- Fixed terminal cursor positioning in raw mode
- Improved error message clarity with grouped equivalent choices
- Enhanced mode selection with U/D keyboard shortcuts

**v1.3.0 - Testing Infrastructure:**

- Comprehensive test suite with 16 automated tests (100% pass rate)
- End-to-end testing with real S3 bucket access
- Automatic AWS SSO authentication in tests
- MIT License and CONTRIBUTING.md for open collaboration

## Key Features

**Upload Mode:**

- Generate properly formatted S3 bucket paths for both scenarios
- Create complete AWS CLI commands for uploading support packages
- **Batch upload multiple files simultaneously** (New in v1.2.0)
- Validate all inputs (Zendesk IDs, Jira IDs, file paths)
- Automatic command execution with AWS SSO authentication handling

**Download Mode (v1.1.0+):**

- Download files from S3 using full paths or ticket IDs
- List and select files from directories
- Batch download multiple files at once
- Smart path parsing (accepts ZD-145980 or full S3 paths)
- Quick shortcut: Press `a` to download all files (v1.2.0+)

**General Features:**

- **Lightning-fast interactive mode** with instant-response prompts (v1.5.x)
  - Auto-submit on Y/n choices - no Enter needed
  - Smart defaults: Enter = Yes for updates, Upload for mode selection
  - Visual mode selection with cloud emoji icons and U/D shortcuts
- **Enhanced terminal experience** (v1.4.x+)
  - Graceful ESC/Ctrl+C handling across all prompts
  - Fixed cursor positioning in raw terminal mode
  - Improved error messages with input validation
- Input history with arrow key navigation
- Automatic AWS SSO authentication
- Configuration persistence for default profiles
- Self-update capability with automatic version checking (Ctrl+U)

## Installation

### Clone the Repository

```bash
git clone https://github.com/markotrapani/gtlogs-helper.git
cd gtlogs-helper
```

### Make Script Executable (if needed)

```bash
chmod +x gtlogs-helper.py
```

### Optional: Add to PATH

For convenient access from anywhere, add an alias to your shell profile:

```bash
# Add to ~/.zshrc or ~/.bashrc
alias gtlogs="/path/to/gtlogs-helper/gtlogs-helper.py"
```

Or create a symbolic link:

```bash
sudo ln -s /path/to/gtlogs-helper/gtlogs-helper.py /usr/local/bin/gtlogs
```

## Quick Start

### Interactive Mode (Recommended)

Run the script without arguments to enter interactive mode:

```bash
./gtlogs-helper.py
```

You'll be prompted to choose between:

1. **Upload Mode** - Generate S3 paths and upload files
2. **Download Mode** - Retrieve files from S3

**Keyboard Controls:**

- **ESC** - Exit immediately (standalone ESC key only -
  arrow keys won't trigger exit)
- **Ctrl+C** - Exit
- **Ctrl+U** - Check for updates and install if available
- **UP/DOWN arrows** - Navigate through input history from previous sessions
- **Backspace** - Delete characters
- **Enter** - Submit input
- Type `exit`, `quit`, or `q` at any prompt - Exit

The script will guide you through entering:

1. Zendesk ticket ID (required)
2. Jira ID (optional - press Enter to skip for ZD-only uploads)
3. Support package path (optional)
4. AWS profile (optional, uses default if configured)
5. Execute upload? (default: yes - press Enter to upload)

**Input History:**

The tool remembers your previous inputs and allows you to quickly reuse them:

- Press **UP arrow** to cycle backwards through your input history
- Press **DOWN arrow** to cycle forwards through your history
- Each field (Zendesk ID, Jira ID, file path, AWS profile) has its own history
- History is saved to `~/.gtlogs-history.json` (last 20 entries per field)
- Only validated inputs are saved to history
- **History is preserved regardless of how you exit** (ESC, Ctrl+C,
  exit commands, or normal completion)

**Example Interactive Session - Upload Mode:**

```text
======================================================================
GT Logs Helper v1.1.0 - Interactive Mode
======================================================================

Upload and download Redis Support packages to/from S3
Press ESC to exit immediately, Ctrl+C, or type 'exit'/'q' at any prompt
Use UP/DOWN arrows to navigate through input history
Press Ctrl+U to check for updates

Select operation mode:
  1. Upload to S3 (generate links and upload files)
  2. Download from S3 (retrieve files from existing paths)

Enter choice (1 or 2): 1

--------------------------------------------------
Upload Mode - Generate S3 URLs and upload files
--------------------------------------------------

Enter Zendesk ticket ID (e.g., 145980): 145980
✓ Using: ZD-145980

Enter Jira ID (e.g., RED-172041 or MOD-12345, press Enter to skip): RED-172041
✓ Using: RED-172041

Enter support package path (optional, press Enter to skip):
  /path/to/debuginfo.tar.gz
✓ File found: /path/to/debuginfo.tar.gz

Enter AWS profile (press Enter for default 'gt-logs'):
✓ Using default profile: gt-logs

======================================================================
Generated Output
======================================================================

S3 Path:
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/debuginfo.tar.gz

AWS CLI Command:
  aws s3 cp /path/to/debuginfo.tar.gz \
    s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/debuginfo.tar.gz \
    --profile gt-logs

======================================================================

Execute this command now? (Y/n):

🔐 Authenticating with AWS SSO (profile: gt-logs)...
✓ AWS SSO authentication successful

📤 Uploading to S3...
   Running: aws s3 cp /path/to/debuginfo.tar.gz \
     s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/debuginfo.tar.gz \
     --profile gt-logs

✅ Upload successful!
```

**Note:** The tool automatically prompts to execute the command when a file
path is provided. Press Enter (default: yes) or 'y' to upload, or 'n' to
skip. It will check AWS authentication and run `aws sso login` if needed.

**ZD-Only Example (No Jira):**

```text
Enter Zendesk ticket ID (e.g., 145980): 145980
✓ Using: ZD-145980

Enter Jira ID (e.g., RED-172041 or MOD-12345, press Enter to skip):
✓ No Jira ID - will use zendesk-tickets path

Enter support package path (optional, press Enter to skip):
  /path/to/debuginfo.tar.gz
✓ File found: /path/to/debuginfo.tar.gz

Enter AWS profile (press Enter for default 'gt-logs'):
✓ Using default profile: gt-logs

======================================================================
Generated Output
======================================================================

S3 Path:
  s3://gt-logs/zendesk-tickets/ZD-145980/debuginfo.tar.gz

AWS CLI Command:
  aws s3 cp /path/to/debuginfo.tar.gz \
    s3://gt-logs/zendesk-tickets/ZD-145980/debuginfo.tar.gz \
    --profile gt-logs

======================================================================

💡 Reminder: Authenticate with AWS SSO before running the command:
   aws sso login --profile gt-logs
```

**Example Interactive Session - Download Mode:**

```text
======================================================================
GT Logs Helper v1.1.0 - Interactive Mode
======================================================================

Select operation mode:
  1. Upload to S3 (generate links and upload files)
  2. Download from S3 (retrieve files from existing paths)

Enter choice (1 or 2): 2

--------------------------------------------------
Download Mode - Retrieve files from S3
--------------------------------------------------

Enter S3 path to download from.
Examples:
  - Full path: s3://gt-logs/zendesk-tickets/ZD-145980/file.tar.gz
  - Ticket ID: ZD-145980 (will list available files)
  - Ticket + Jira: ZD-145980-RED-172041

Enter S3 path or ticket ID: ZD-145980
✓ Parsed: s3://gt-logs/zendesk-tickets/ZD-145980/

Enter AWS profile (press Enter for default 'gt-logs'):
✓ Using default profile: gt-logs

Checking AWS authentication...
✓ AWS profile 'gt-logs' is authenticated

🔍 Listing files in s3://gt-logs/zendesk-tickets/ZD-145980/...

Found 3 file(s):
  1. zendesk-tickets/ZD-145980/debuginfo-20240115.tar.gz
  2. zendesk-tickets/ZD-145980/logs-20240115.tar.gz
  3. zendesk-tickets/ZD-145980/metrics-20240115.csv

Select files to download:
  - Enter file number(s) separated by commas (e.g., 1,3,5)
  - Enter 'all' to download all files
  - Press Enter to cancel

Your selection: 1,2

Where to save the files?
Local directory (press Enter for current directory): ~/Downloads

📥 Downloading 2 file(s)...

📥 Downloading from S3...
   Source: s3://gt-logs/zendesk-tickets/ZD-145980/debuginfo-20240115.tar.gz
   Destination: ~/Downloads/debuginfo-20240115.tar.gz
   Running: aws s3 cp "s3://gt-logs/..." "~/Downloads/..." --profile gt-logs

✅ Download successful! File saved to: ~/Downloads/debuginfo-20240115.tar.gz

📥 Downloading from S3...
   Source: s3://gt-logs/zendesk-tickets/ZD-145980/logs-20240115.tar.gz
   Destination: ~/Downloads/logs-20240115.tar.gz
   Running: aws s3 cp "s3://gt-logs/..." "~/Downloads/..." --profile gt-logs

✅ Download successful! File saved to: ~/Downloads/logs-20240115.tar.gz

✅ Downloaded 2/2 file(s) successfully
```

### Command-Line Mode - Upload

For quick one-time usage or scripting:

```bash
# Generate S3 path for upload
./gtlogs-helper.py 145980 RED-172041
```

**Output:**

```text
======================================================================
GT Logs Helper
======================================================================

S3 Path:
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/<support_package_name>

AWS CLI Command:
  aws s3 cp <support_package_path> \
    s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/<support_package_name>

======================================================================

ℹ️  Tip: Use -f to specify the support package file path
ℹ️  Tip: Set a default AWS profile with --set-profile

💡 Reminder: Authenticate with AWS SSO before running the command:
   aws sso login --profile <your-aws-profile>
```

### Command-Line Mode - Download

Download files from S3:

```bash
# Download a specific file
./gtlogs-helper.py --download \
  s3://gt-logs/zendesk-tickets/ZD-145980/debuginfo.tar.gz

# Download using ticket ID (lists files)
./gtlogs-helper.py --download ZD-145980

# Download to specific directory
./gtlogs-helper.py --download ZD-145980 --output ~/Downloads/
```

### Command-Line Mode with Automatic Execution

Use the `--execute` (or `-e`) flag to automatically upload the file with
authentication handling:

```bash
./gtlogs-helper.py 145980 RED-172041 \
  -f /path/to/support_package.tar.gz --execute
```

**What happens:**

1. Generates the S3 path and AWS CLI command
2. Checks if your AWS profile is authenticated
3. If not authenticated, runs `aws sso login --profile <profile>` automatically
4. Executes the `aws s3 cp` command
5. Shows upload progress and success/failure status

**Output:**

```text
======================================================================
GT Logs Link Generator
======================================================================

S3 Path:
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz

AWS CLI Command:
  aws s3 cp /path/to/support_package.tar.gz \
    s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz \
    --profile gt-logs

======================================================================

ℹ️  Using default AWS profile: gt-logs

✓ AWS profile 'gt-logs' is already authenticated

📤 Uploading to S3...
   Running: aws s3 cp /path/to/support_package.tar.gz \
     s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz \
     --profile gt-logs

✅ Upload successful!
```

### Batch Upload Multiple Files (New in v1.2.0)

Upload multiple files to the same S3 destination simultaneously:

```bash
# Upload 3 files in one command
./gtlogs-helper.py 145980 RED-172041 \
  -f file1.tar.gz -f file2.tar.gz -f file3.tar.gz --execute
```

**Output:**

```text
======================================================================
GT Logs Helper - Batch Upload
======================================================================

S3 Destination:
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/

Files to upload (3):
  1. file1.tar.gz
  2. file2.tar.gz
  3. file3.tar.gz

======================================================================

ℹ️  Using default AWS profile: gt-logs

✓ AWS profile 'gt-logs' is already authenticated

======================================================================
Batch Upload: 3 file(s)
======================================================================

S3 Destination: s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/

[1/3] Uploading: file1.tar.gz
            From: /path/to/file1.tar.gz
📤 Uploading to S3...
   Running: aws s3 cp /path/to/file1.tar.gz s3://gt-logs/...

✅ Upload successful!

----------------------------------------------------------------------

[2/3] Uploading: file2.tar.gz
            From: /path/to/file2.tar.gz
📤 Uploading to S3...
   Running: aws s3 cp /path/to/file2.tar.gz s3://gt-logs/...

✅ Upload successful!

----------------------------------------------------------------------

[3/3] Uploading: file3.tar.gz
            From: /path/to/file3.tar.gz
📤 Uploading to S3...
   Running: aws s3 cp /path/to/file3.tar.gz s3://gt-logs/...

✅ Upload successful!

======================================================================
Batch Upload Summary
======================================================================
✅ Successful: 3/3
❌ Failed: 0/3
======================================================================
```

**Interactive Mode Batch Upload:**

In interactive mode, you can also upload multiple files:

1. Enter comma-separated paths:
   `/path/to/file1.tar.gz, /path/to/file2.tar.gz`
2. Or add files one at a time (keep pressing Enter to add more)
3. The tool automatically detects duplicates and validates all files
   before uploading

### Generate Complete AWS CLI Command

```bash
./gtlogs-helper.py 145980 RED-172041 -f /path/to/support_package.tar.gz
```

**Output:**

```text
======================================================================
GT Logs Link Generator
======================================================================

S3 Path:
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz

AWS CLI Command:
  aws s3 cp /path/to/support_package.tar.gz \
    s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz

======================================================================

ℹ️  Using default AWS profile: gt-logs

💡 Reminder: Authenticate with AWS SSO before running the command:
   aws sso login --profile gt-logs
```

### Using AWS Profile

```bash
# Use specific AWS profile
./gtlogs-helper.py 145980 RED-172041 -f support.tar.gz -p redis-support

# Set default AWS profile (saved to ~/.gtlogs-config.ini)
./gtlogs-helper.py --set-profile redis-support

# Now all future commands will use the default profile
./gtlogs-helper.py 145980 RED-172041 -f support.tar.gz
```

## Usage Examples

### Use Case 1: Upload - Redis Cloud Without Jira (Most Common)

For Redis Cloud environments without Engineering escalation.

**Command-line:**

```bash
./gtlogs-helper.py 145980 -f /path/to/support_package.tar.gz
```

**Interactive mode:**

```bash
./gtlogs-helper.py
# Choose: 1 (Upload)
# Enter ZD: 145980
# Press Enter to skip Jira
# Enter file path: /path/to/support_package.tar.gz
```

**Generates:**

```bash
aws s3 cp /path/to/support_package.tar.gz \
  s3://gt-logs/zendesk-tickets/ZD-145980/support_package.tar.gz \
  --profile gt-logs
```

**When to use:**

- Support package doesn't require Engineering review
- Internal Redis Cloud troubleshooting
- No Jira ticket associated with the issue

---

### Use Case 2: Upload - Redis Cloud with Jira (Engineering Escalation)

For Redis Cloud issues escalated to Engineering via RED or MOD Jira tickets.

**Command-line:**

```bash
# Redis Enterprise bug (RED)
./gtlogs-helper.py 147823 RED-172041 \
  -f ./support_pkg_cluster_1.tar.gz

# Module bug (MOD)
./gtlogs-helper.py 145980 MOD-12345 \
  -f /path/to/customer_support.tar.gz
```

**Interactive mode:**

```bash
./gtlogs-helper.py
# Choose: 1 (Upload)
# Enter ZD: 147823
# Enter Jira: RED-172041
# Enter file path: ./support_pkg_cluster_1.tar.gz
```

**Generates:**

```bash
aws s3 cp ./support_pkg_cluster_1.tar.gz \
  s3://gt-logs/exa-to-gt/ZD-147823-RED-172041/support_pkg_cluster_1.tar.gz \
  --profile gt-logs
```

**When to use:**

- Redis Cloud issues that require Engineering involvement
- Sharing support packages via Jira (RED or MOD tickets)
- **This tool is the primary/best method for this scenario**

---

### Use Case 3: Download - Retrieve Support Packages

Download existing packages from S3 for analysis or sharing.

**Command-line:**

```bash
# Download specific file
./gtlogs-helper.py --download \
  s3://gt-logs/zendesk-tickets/ZD-145980/debuginfo.tar.gz

# List and download from ticket
./gtlogs-helper.py --download ZD-145980 --output ~/Downloads/
```

**Interactive mode:**

```bash
./gtlogs-helper.py
# Choose: 2 (Download)
# Enter: ZD-145980
# Select files to download
# Enter local directory
```

**When to use:**

- Need to retrieve previously uploaded packages
- Analyzing packages from other engineers
- Downloading for local debugging

---

### Use Case 4: Redis Software with Jira (Alternative Method)

For Redis Software (on-prem) issues escalated to Engineering.

**Command-line:**

```bash
./gtlogs-helper.py 148901 RED-173052 -f /path/to/rs_support_pkg.tar.gz
```

**Interactive mode:**

```bash
./gtlogs-helper.py
# Choose: 1 (Upload)
# Enter ZD: 148901
# Enter Jira: RED-173052
# Enter file path: /path/to/rs_support_pkg.tar.gz
```

**Generates:**

```bash
aws s3 cp /path/to/rs_support_pkg.tar.gz \
  s3://gt-logs/exa-to-gt/ZD-148901-RED-173052/rs_support_pkg.tar.gz \
  --profile gt-logs
```

**When to use:**

- Redis Software issues that require Engineering involvement
- **Note:** Most Redis Software uploads are handled automatically
  via @exatogt automation with Files.com
- Use this tool when the automation isn't available or applicable

---

## All Usage Options

### Running Modes Summary

| Mode | Command | When to Use |
|------|---------|-------------|
| **Interactive** | `./gtlogs-helper.py` | Choose upload/download mode |
| **Upload (CLI)** | `./gtlogs-helper.py <zd> [jira]` | Quick upload |
| **Download (CLI)** | `./gtlogs-helper.py --download <path>` | Quick download |
| **Force Interactive** | `./gtlogs-helper.py -i` | Explicit interactive |

### Complete Usage Options

```bash
# 1. INTERACTIVE MODE (Easiest - Choose Upload or Download)
# Launch interactive mode with mode selection
./gtlogs-helper.py
./gtlogs-helper.py -i                    # Force interactive mode

# 2. UPLOAD MODE - ZD-ONLY (no Jira)
./gtlogs-helper.py 145980                              # Templated output
./gtlogs-helper.py 145980 -f /path/to/package.tar.gz   # With file path
# Auto-upload
./gtlogs-helper.py 145980 -f /path/to/package.tar.gz --execute

# 3. UPLOAD MODE - ZD + JIRA (Engineering escalation)
./gtlogs-helper.py 145980 RED-172041                     # Templated output
# With file path
./gtlogs-helper.py 145980 RED-172041 -f /path/to/package.tar.gz
# Auto-upload
./gtlogs-helper.py 145980 RED-172041 -f /path/to/pkg.tar.gz -e

# 4. DOWNLOAD MODE
./gtlogs-helper.py --download \
  s3://gt-logs/zendesk-tickets/ZD-145980/file.tar.gz
./gtlogs-helper.py --download ZD-145980            # List files
# Custom output dir
./gtlogs-helper.py --download ZD-145980 --output ~/Downloads/
# Download from Jira path
./gtlogs-helper.py -d ZD-145980-RED-172041

# 5. WITH CUSTOM AWS PROFILE
./gtlogs-helper.py 145980 -p my-profile              # Upload with profile
# Download with profile
./gtlogs-helper.py --download ZD-145980 -p my-profile

# 6. CONFIGURATION MANAGEMENT
./gtlogs-helper.py --set-profile gt-logs    # Set default AWS profile
./gtlogs-helper.py --show-config            # Show current config

# 7. VERSION & HELP
./gtlogs-helper.py --version                # Show version and check for updates
./gtlogs-helper.py -h                       # Show help message
```

## Command Reference

### Running Modes

| Mode | Command | Description |
|------|---------|-------------|
| **Interactive** | `./gtlogs-helper.py` | Choose upload/download mode |
| **Upload (CLI)** | `./gtlogs-helper.py <zd> [jira]` | Quick upload |
| **Download (CLI)** | `./gtlogs-helper.py --download <path>` | Quick download |
| **Force Interactive** | `./gtlogs-helper.py -i` | Explicit interactive |

### Positional Arguments (Upload Mode)

- `zendesk_id` - Zendesk ticket ID (e.g., `145980` or `ZD-145980`)
- `jira_id` - Jira ticket ID (optional,
  e.g., `RED-172041` or `MOD-12345`)

### Optional Arguments

| Flag | Description | Example |
|------|-------------|---------|
| `-i`, `--interactive` | Run in interactive mode | `-i` |
| `-f`, `--file` | Path to support package | `-f file.tar.gz` |
| `-p`, `--profile` | AWS profile (overrides default) | `-p my-profile` |
| `-e`, `--execute` | Execute S3 upload with auth | `--execute` |
| `-d`, `--download` | Download from S3 | `--download ZD-145980` |
| `-o`, `--output` | Output dir for downloads | `--output ~/Downloads/` |
| `--set-profile` | Set default AWS profile | `--set-profile gt-logs` |
| `--show-config` | Show current config | `--show-config` |
| `-v`, `--version` | Display version | `-v` or `--version` |
| `-h`, `--help` | Show help message | `-h` |

### Configuration

The tool stores configuration and history in your home directory:

**Configuration file (`~/.gtlogs-config.ini`):**

- Stores your default AWS profile

**History file (`~/.gtlogs-history.json`):**

- Stores your last 20 inputs per field (Zendesk ID, Jira ID,
  file path, AWS profile)
- Automatically saved after each interactive session
  (regardless of exit method)
- Saved even when exiting with ESC, Ctrl+C, or exit commands
- Used for UP/DOWN arrow navigation in interactive mode
- Only validated inputs are saved (invalid entries are never added)

```bash
# View current configuration
./gtlogs-helper.py --show-config

# Set default AWS profile
./gtlogs-helper.py --set-profile redis-support

# View history file
cat ~/.gtlogs-history.json

# Clear history (if needed)
rm ~/.gtlogs-history.json
```

### Automatic Updates

The tool includes a built-in auto-update mechanism that keeps your
installation up to date with the latest features and bug fixes.

**How it works:**

1. **Automatic update checks on startup** - Every time you run the script,
   it checks GitHub for new releases
2. **User permission required** - Updates are never installed without your
   explicit approval
3. **Safe updates with automatic backup** - Your current version is backed
   up before updating
4. **Automatic rollback on failure** - If an update fails, your previous
   version is automatically restored

**Update options when prompted:**

```text
🔍 Checking for updates...
📦 Update available: v1.0.0 → v1.1.0

Release highlights:
- Added new feature X
- Fixed bug Y
- Performance improvements

Update now? (y/n):
  y - Yes, install the update now (script will exit,
      restart to use new version)
  n - No, continue without updating (continues to interactive mode)
```

**Note:** If you choose 'n', the script continues normally. You can trigger
an update check later by pressing **Ctrl+U** during interactive mode, or
you'll be asked again next time you run the script.

**Manual update check:**

You can manually check for updates at any time:

```bash
# Check version and updates
./gtlogs-helper.py -v
# or
./gtlogs-helper.py --version

# Or during interactive mode, press Ctrl+U at any prompt
./gtlogs-helper.py
# (Press Ctrl+U during any input prompt)
```

**Update process:**

1. Script downloads the latest release from GitHub (5-second timeout)
2. Creates backup of current version: `gtlogs-helper.py.backup`
3. Downloads new version to temporary file
4. Replaces current script with new version
5. Sets executable permissions automatically
6. On success: backup remains for manual rollback if needed
7. On failure: automatically restores from backup

**Error handling:**

If the update fails for any reason (network timeout, download error, etc.):

- Error message is displayed with details
- Your current version is automatically restored from backup
- You can continue using the tool without interruption

**Offline behavior:**

- Update checks fail silently if you're offline or GitHub is unreachable
- Script continues normally without blocking or errors
- No interruption to your workflow

**Manual rollback:**

If you need to revert to a previous version:

```bash
# Your previous version is saved as a backup
mv gtlogs-helper.py.backup gtlogs-generator.py
chmod +x gtlogs-generator.py
```

**Disabling update checks:**

Update checks happen automatically on startup but fail silently if offline.
If you want to avoid updating:

- Choose 'n' when prompted - continues to interactive mode
- Run in an environment without internet access - checks will fail silently
  and continue
- There is no persistent "never check" option by design
  (ensures you stay up to date)

## Input Validation

The tool performs strict validation on all inputs to ensure data
integrity:

### Zendesk ID Validation

- ✅ **Must be numerical only**
- ✅ Accepts: `145980`, `ZD-145980`, `zd-145980`
- ❌ Rejects: `145980abc`, `ZD-abc123`, any non-numerical characters
- 📤 **Output format:** `ZD-145980`

**Examples:**

```bash
# Valid
./gtlogs-helper.py 145980 RED-172041        ✓
./gtlogs-helper.py ZD-145980 RED-172041     ✓

# Invalid
./gtlogs-helper.py 145980abc RED-172041
  ✗ Error: must be numerical only
./gtlogs-helper.py ZD-abc RED-172041
  ✗ Error: must be numerical only
```

### Jira ID Validation

- ✅ **Must be RED-# or MOD-# with numerical suffix only**
- ✅ Accepts: `RED-172041`, `MOD-12345`, `RED172041`
  (auto-adds hyphen)
- ❌ Rejects: `RED-abc`, `MOD-123abc`, `ABC-123`,
  numbers without prefix
- 📤 **Output format:** `RED-172041` or `MOD-12345`

**Supported prefixes:**

- `RED-` for Redis Enterprise bugs
- `MOD-` for Module bugs

**Examples:**

```bash
# Valid
./gtlogs-helper.py 145980 RED-172041        ✓
./gtlogs-helper.py 145980 MOD-12345         ✓
./gtlogs-helper.py 145980 RED172041
  ✓ (auto-formats to RED-172041)

# Invalid
./gtlogs-helper.py 145980 RED-172041abc
  ✗ Error: numerical suffix required
./gtlogs-helper.py 145980 ABC-12345
  ✗ Error: must be RED-# or MOD-#
./gtlogs-helper.py 145980 172041
  ✗ Error: must include prefix
```

### File Path Validation

- ✅ **File must exist in the filesystem**
- ✅ **Path must point to a file, not a directory**
- ✅ Supports tilde expansion (`~/Downloads/file.tar.gz`)
- ❌ Rejects non-existent files and directories

**Examples:**

```bash
# Valid
./gtlogs-helper.py 145980 RED-172041 -f /path/to/existing/file.tar.gz
  ✓
./gtlogs-helper.py 145980 RED-172041 -f ~/Downloads/package.tar.gz
  ✓

# Invalid
./gtlogs-helper.py 145980 RED-172041 -f /nonexistent/file.tar.gz
  ✗ Error: File does not exist
./gtlogs-helper.py 145980 RED-172041 -f /path/to/directory
  ✗ Error: Path is not a file
```

### Interactive Mode Validation

In interactive mode, the tool validates inputs in real-time and allows you
to retry:

- **Invalid Zendesk/Jira IDs:** Prompts you to re-enter
- **Invalid file paths:** Asks if you want to try again or skip
- **Helpful error messages:** Shows exactly what went wrong

## ID Format Reference

### Zendesk IDs

- **Accepted formats:** `145980`, `ZD-145980`, `zd-145980`
  (numerical only)
- **Output format:** `ZD-145980`

### Jira IDs

- **Accepted formats:**
  - `RED-172041` (Redis Enterprise bugs)
  - `MOD-12345` (Module bugs)
  - `RED172041` (auto-adds hyphen)
- **Must have numerical suffix only**
- **Output format:** `RED-172041` or `MOD-12345`

## Workflow Examples

### Workflow 1: Interactive Mode (Easiest - with Automatic Upload)

```bash
# 1. Run the interactive tool
./gtlogs-helper.py

# 2. Follow the prompts:
#    - Enter Zendesk ID: 145980
#    - Enter Jira ID: RED-172041
#    - Enter file path: ~/Downloads/support_package.tar.gz
#    - Press Enter to use default AWS profile (gt-logs)

# 3. When prompted "Execute this command now? (Y/n):", press Enter or 'y'
#    - Default is 'yes' - just press Enter to upload
#    - Tool automatically checks authentication
#    - Runs 'aws sso login' if needed
#    - Uploads the file to S3

# 4. Share the S3 path in the Jira ticket
```

### Workflow 2: Command-Line Mode with Automatic Upload

```bash
# 1. Set your default AWS profile (one-time setup)
./gtlogs-helper.py --set-profile gt-logs

# 2. Generate and execute the upload in one command
./gtlogs-helper.py 145980 RED-172041 \
  -f ~/Downloads/support_package.tar.gz --execute

# 3. Tool automatically:
#    - Checks authentication
#    - Runs 'aws sso login' if needed
#    - Uploads the file to S3

# 4. Share the S3 path in the Jira ticket
# s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz
```

### Workflow 3: Command-Line Mode (Generate Only)

```bash
# 1. Set your default AWS profile (one-time setup)
./gtlogs-helper.py --set-profile gt-logs

# 2. Authenticate with AWS SSO (if not already authenticated)
aws sso login --profile gt-logs

# 3. Generate the command with your specific ticket details
./gtlogs-helper.py 145980 RED-172041 -f ~/Downloads/support_package.tar.gz

# 4. Copy the generated AWS CLI command and run it manually
# aws s3 cp ~/Downloads/support_package.tar.gz \
#   s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz \
#   --profile gt-logs

# 5. Share the S3 path in the Jira ticket
# s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/
```

## Error Handling

The tool performs strict validation and provides clear error messages.
**All validations are enforced** - the tool will not generate output for
invalid inputs.

### Command-Line Mode Errors

```bash
# Invalid Zendesk ID (non-numerical)
./gtlogs-helper.py 145980abc RED-172041
# ❌ Error: Invalid Zendesk ID: must be numerical only
#    (e.g., 145980 or ZD-145980)

# Invalid Jira format (missing prefix)
./gtlogs-helper.py 145980 12345
# ❌ Error: Jira ID must include prefix (RED- or MOD-)

# Invalid Jira prefix
./gtlogs-helper.py 145980 ABC-12345
# ❌ Error: Invalid Jira ID: must be in format RED-# or MOD-#
#    with numerical suffix

# Invalid Jira suffix (non-numerical)
./gtlogs-helper.py 145980 RED-172041abc
# ❌ Error: Invalid Jira ID: must be in format RED-# or MOD-#
#    with numerical suffix

# File doesn't exist
./gtlogs-helper.py 145980 RED-172041 -f /nonexistent/file.tar.gz
# ❌ Error: File does not exist: /nonexistent/file.tar.gz

# Path is a directory, not a file
./gtlogs-helper.py 145980 RED-172041 -f /Users/username/Downloads
# ❌ Error: Path is not a file: /Users/username/Downloads
```

### Interactive Mode Error Recovery

In interactive mode, validation errors prompt you to retry:

```text
Enter Zendesk ticket ID (e.g., 145980): 145980abc
❌ Invalid Zendesk ID: must be numerical only
   (e.g., 145980 or ZD-145980)

Enter Zendesk ticket ID (e.g., 145980): 145980
✓ Using: ZD-145980

Enter support package path (optional, press Enter to skip):
  /nonexistent/file.tar.gz
❌ File does not exist: /nonexistent/file.tar.gz
Try again? (y/n): n
✓ Skipping file path, will generate template command
```

## Requirements

- Python 3.6 or higher
- No external dependencies (uses Python standard library only)
- AWS CLI (for executing the generated commands)
- AWS SSO access configured for the `gt-logs` bucket

### AWS Authentication

**IMPORTANT:** Before running the generated `aws s3 cp` commands, you must
authenticate with AWS SSO:

```bash
# Authenticate with your AWS profile
aws sso login --profile <aws_profile>

# Example with default profile
aws sso login --profile gt-logs
```

**Complete workflow:**

```bash
# 1. Authenticate with AWS SSO
aws sso login --profile gt-logs

# 2. Generate the upload command
gtlogs 145980 RED-172041 -f /path/to/support_package.tar.gz

# 3. Copy and run the generated command
aws s3 cp /path/to/support_package.tar.gz \
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz \
  --profile gt-logs
```

**Note:** AWS SSO sessions expire after a period of time. If you get
authentication errors, run `aws sso login` again.

## S3 Bucket Structure

Files are organized in the `gt-logs` bucket with two different path
structures:

### 1. Without Jira (ZD-Only) - Most Common

```text
s3://gt-logs/
└── zendesk-tickets/
    ├── ZD-145980/
    │   └── debuginfo.tar.gz
    ├── ZD-147823/
    │   └── support_package.tar.gz
    └── ZD-148901/
        └── cluster_logs.tar.gz
```

### 2. With Jira (Engineering Escalation)

```text
s3://gt-logs/
└── exa-to-gt/
    ├── ZD-145980-RED-172041/
    │   └── support_package.tar.gz
    ├── ZD-147823-MOD-12345/
    │   └── customer_logs.tar.gz
    └── ZD-148901-RED-173052/
        └── cluster_data.tar.gz
```

## Development

### Project Structure

```text
gtlogs-link-generator/
├── .gitignore
├── README.md
├── requirements.txt
└── gtlogs-generator.py
```

### Running Tests

The script includes input validation and error handling. Test with various
inputs:

```bash
# Test different ID formats
./gtlogs-helper.py 145980 RED-172041
./gtlogs-helper.py ZD-145980 RED172041
./gtlogs-helper.py 145980 MOD-12345

# Test with file paths
./gtlogs-helper.py 145980 RED-172041 -f test.tar.gz
./gtlogs-helper.py 145980 RED-172041 \
  -f /path/to/file.tar.gz -p my-profile
```

## Troubleshooting

### Script not executable

```bash
chmod +x gtlogs-generator.py
```

### Python not found

Ensure Python 3 is installed:

```bash
python3 --version
```

If using the shebang directly, verify Python 3 location:

```bash
which python3
```

### AWS CLI command fails

**Authentication Errors:**

```bash
# Error: The SSO session associated with this profile has expired
#        or is otherwise invalid
# Solution: Re-authenticate with AWS SSO
aws sso login --profile gt-logs
```

**Permission Errors:**

```bash
# Error: Access Denied or 403 Forbidden
# Solutions:
# 1. Verify you have permissions to write to the gt-logs bucket
# 2. Check you're using the correct AWS profile
# 3. Ensure your SSO session is still valid
aws sso login --profile gt-logs
```

**General Troubleshooting:**

- Verify AWS CLI is installed: `aws --version`
- Check AWS profile configuration:
  `aws configure list --profile <profile-name>`
- Test AWS access: `aws sts get-caller-identity --profile gt-logs`
- Verify SSO session: `aws sso login --profile gt-logs`

## Documentation

Additional documentation is available in the [docs/](docs/) directory:

- **[CLAUDE.md](CLAUDE.md)** - Development guidelines and architecture notes
- **[docs/ROADMAP.md](docs/ROADMAP.md)** - Feature roadmap and future
  enhancements
- **[docs/TESTING.md](docs/TESTING.md)** - Comprehensive testing
  documentation

## Contributing

This is an internal Redis Support tool. For issues or feature requests,
please contact the maintainer.

## License

Internal Redis tool - not for public distribution.

## Support

For questions or issues, contact: <marko.trapani@redis.com>
