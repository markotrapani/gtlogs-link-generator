# GT Logs Link Generator

A command-line tool for generating S3 bucket URLs and AWS CLI commands for Redis Support packages. This tool helps Redis Support engineers quickly create properly formatted S3 paths for sharing customer support packages securely with engineering teams.

## Purpose

Redis Support engineers upload customer support packages to the `gt-logs` S3 bucket for storage and sharing. This tool automates the generation of properly formatted S3 paths and AWS CLI upload commands.

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
   - **Also supports:** Redis Software issues (though less common, as @exatogt automation with Files.com handles most Redis Software uploads automatically)

**Key Features:**

This tool automates:

- Properly formatted S3 bucket paths for both scenarios
- Complete AWS CLI commands for uploading support packages
- Validation of all inputs (Zendesk IDs, Jira IDs, file paths)
- **Automatic command execution** with AWS SSO authentication handling (optional)

## Installation

### Clone the Repository

```bash
git clone https://github.com/markotrapani/gtlogs-link-generator.git
cd gtlogs-link-generator
```

### Make Script Executable (if needed)

```bash
chmod +x gtlogs-generator.py
```

### Optional: Add to PATH

For convenient access from anywhere, add an alias to your shell profile:

```bash
# Add to ~/.zshrc or ~/.bashrc
alias gtlogs="/path/to/gtlogs-link-generator/gtlogs-generator.py"
```

Or create a symbolic link:

```bash
sudo ln -s /path/to/gtlogs-link-generator/gtlogs-generator.py /usr/local/bin/gtlogs
```

## Quick Start

### Interactive Mode (Recommended)

Run the script without arguments to enter interactive mode:

```bash
./gtlogs-generator.py
```

**Keyboard Controls:**

- **ESC** - Exit immediately (standalone ESC key only - arrow keys won't trigger exit)
- **Ctrl+C** - Exit
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

**Example Interactive Session:**

```text
======================================================================
GT Logs Link Generator - Interactive Mode
======================================================================

Generate S3 URLs and AWS CLI commands for Redis Support packages
Press ESC to exit immediately, Ctrl+C, or type 'exit'/'q' at any prompt
Use UP/DOWN arrows to navigate through input history

Enter Zendesk ticket ID (e.g., 145980): 145980
✓ Using: ZD-145980

Enter Jira ID (e.g., RED-172041 or MOD-12345, press Enter to skip): RED-172041
✓ Using: RED-172041

Enter support package path (optional, press Enter to skip): /path/to/debuginfo.tar.gz
✓ File found: /path/to/debuginfo.tar.gz

Enter AWS profile (press Enter for default 'gt-logs'):
✓ Using default profile: gt-logs

======================================================================
Generated Output
======================================================================

S3 Path:
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/debuginfo.tar.gz

AWS CLI Command:
  aws s3 cp /path/to/debuginfo.tar.gz s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/debuginfo.tar.gz --profile gt-logs

======================================================================

Execute this command now? (Y/n):

🔐 Authenticating with AWS SSO (profile: gt-logs)...
✓ AWS SSO authentication successful

📤 Uploading to S3...
   Running: aws s3 cp /path/to/debuginfo.tar.gz s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/debuginfo.tar.gz --profile gt-logs

✅ Upload successful!
```

**Note:** The tool automatically prompts to execute the command when a file path is provided. Press Enter (default: yes) or 'y' to upload, or 'n' to skip. It will check AWS authentication and run `aws sso login` if needed.

**ZD-Only Example (No Jira):**

```text
Enter Zendesk ticket ID (e.g., 145980): 145980
✓ Using: ZD-145980

Enter Jira ID (e.g., RED-172041 or MOD-12345, press Enter to skip):
✓ No Jira ID - will use zendesk-tickets path

Enter support package path (optional, press Enter to skip): /path/to/debuginfo.tar.gz
✓ File found: /path/to/debuginfo.tar.gz

Enter AWS profile (press Enter for default 'gt-logs'):
✓ Using default profile: gt-logs

======================================================================
Generated Output
======================================================================

S3 Path:
  s3://gt-logs/zendesk-tickets/ZD-145980/debuginfo.tar.gz

AWS CLI Command:
  aws s3 cp /path/to/debuginfo.tar.gz s3://gt-logs/zendesk-tickets/ZD-145980/debuginfo.tar.gz --profile gt-logs

======================================================================

💡 Reminder: Authenticate with AWS SSO before running the command:
   aws sso login --profile gt-logs
```

### Command-Line Mode

For quick one-time usage or scripting:

```bash
./gtlogs-generator.py 145980 RED-172041
```

**Output:**

```text
======================================================================
GT Logs Link Generator
======================================================================

S3 Path:
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/<support_package_name>

AWS CLI Command:
  aws s3 cp <support_package_path> s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/<support_package_name>

======================================================================

ℹ️  Tip: Use -f to specify the support package file path
ℹ️  Tip: Set a default AWS profile with --set-profile

💡 Reminder: Authenticate with AWS SSO before running the command:
   aws sso login --profile <your-aws-profile>
```

### Command-Line Mode with Automatic Execution

Use the `--execute` (or `-e`) flag to automatically upload the file with authentication handling:

```bash
./gtlogs-generator.py 145980 RED-172041 -f /path/to/support_package.tar.gz --execute
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
  aws s3 cp /path/to/support_package.tar.gz s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz --profile gt-logs

======================================================================

ℹ️  Using default AWS profile: gt-logs

✓ AWS profile 'gt-logs' is already authenticated

📤 Uploading to S3...
   Running: aws s3 cp /path/to/support_package.tar.gz s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz --profile gt-logs

✅ Upload successful!
```

### Generate Complete AWS CLI Command

```bash
./gtlogs-generator.py 145980 RED-172041 -f /path/to/support_package.tar.gz
```

**Output:**

```text
======================================================================
GT Logs Link Generator
======================================================================

S3 Path:
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz

AWS CLI Command:
  aws s3 cp /path/to/support_package.tar.gz s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz

======================================================================

ℹ️  Using default AWS profile: gt-logs

💡 Reminder: Authenticate with AWS SSO before running the command:
   aws sso login --profile gt-logs
```

### Using AWS Profile

```bash
# Use specific AWS profile
./gtlogs-generator.py 145980 RED-172041 -f support.tar.gz -p redis-support

# Set default AWS profile (saved to ~/.gtlogs-config.ini)
./gtlogs-generator.py --set-profile redis-support

# Now all future commands will use the default profile
./gtlogs-generator.py 145980 RED-172041 -f support.tar.gz
```

## Usage Examples

### Use Case 1: Redis Cloud Without Jira (Most Common)

For Redis Cloud environments without Engineering escalation.

**Command-line:**

```bash
./gtlogs-generator.py 145980 -f /path/to/support_package.tar.gz
```

**Interactive mode:**

```bash
./gtlogs-generator.py
# Enter ZD: 145980
# Press Enter to skip Jira
# Enter file path: /path/to/support_package.tar.gz
```

**Generates:**

```bash
aws s3 cp /path/to/support_package.tar.gz s3://gt-logs/zendesk-tickets/ZD-145980/support_package.tar.gz --profile gt-logs
```

**When to use:**

- Support package doesn't require Engineering review
- Internal Redis Cloud troubleshooting
- No Jira ticket associated with the issue

---

### Use Case 2: Redis Cloud with Jira (Primary Method for Engineering Escalation)

For Redis Cloud issues escalated to Engineering via RED or MOD Jira tickets.

**Command-line:**

```bash
# Redis Enterprise bug (RED)
./gtlogs-generator.py 147823 RED-172041 -f ./support_pkg_cluster_1.tar.gz

# Module bug (MOD)
./gtlogs-generator.py 145980 MOD-12345 -f /path/to/customer_support.tar.gz
```

**Interactive mode:**

```bash
./gtlogs-generator.py
# Enter ZD: 147823
# Enter Jira: RED-172041
# Enter file path: ./support_pkg_cluster_1.tar.gz
```

**Generates:**

```bash
aws s3 cp ./support_pkg_cluster_1.tar.gz s3://gt-logs/exa-to-gt/ZD-147823-RED-172041/support_pkg_cluster_1.tar.gz --profile gt-logs
```

**When to use:**

- Redis Cloud issues that require Engineering involvement
- Sharing support packages via Jira (RED or MOD tickets)
- **This tool is the primary/best method for this scenario**

---

### Use Case 3: Redis Software with Jira (Alternative Method)

For Redis Software (on-prem) issues escalated to Engineering.

**Command-line:**

```bash
./gtlogs-generator.py 148901 RED-173052 -f /path/to/rs_support_pkg.tar.gz
```

**Interactive mode:**

```bash
./gtlogs-generator.py
# Enter ZD: 148901
# Enter Jira: RED-173052
# Enter file path: /path/to/rs_support_pkg.tar.gz
```

**Generates:**

```bash
aws s3 cp /path/to/rs_support_pkg.tar.gz s3://gt-logs/exa-to-gt/ZD-148901-RED-173052/rs_support_pkg.tar.gz --profile gt-logs
```

**When to use:**

- Redis Software issues that require Engineering involvement
- **Note:** Most Redis Software uploads are handled automatically via @exatogt automation with Files.com
- Use this tool when the automation isn't available or applicable

---

## All Usage Options

### Running Modes Summary

| Mode | Command | When to Use |
|------|---------|-------------|
| **Interactive** | `./gtlogs-generator.py` | First time, or when you want guided prompts |
| **Command-line** | `./gtlogs-generator.py <zd> <jira>` | Quick generation, scripting, or repeated use |
| **Force Interactive** | `./gtlogs-generator.py -i` | Explicitly run interactive mode |

### Complete Usage Options

```bash
# 1. INTERACTIVE MODE (Easiest)
./gtlogs-generator.py                    # Launch interactive mode
./gtlogs-generator.py -i                 # Force interactive mode

# 2. ZD-ONLY (no Jira - for Redis Cloud without Engineering)
./gtlogs-generator.py 145980                                    # Templated output
./gtlogs-generator.py 145980 -f /path/to/package.tar.gz        # With file path

# 3. ZD + JIRA (Engineering escalation)
./gtlogs-generator.py 145980 RED-172041                         # Templated output
./gtlogs-generator.py 145980 RED-172041 -f /path/to/package.tar.gz  # With file path

# 4. WITH CUSTOM AWS PROFILE (overrides default)
./gtlogs-generator.py 145980 -p my-profile                      # ZD-only
./gtlogs-generator.py 145980 RED-172041 -p my-profile          # ZD + Jira

# 5. EXECUTE UPLOAD AUTOMATICALLY (with authentication handling)
./gtlogs-generator.py 145980 -f /path/to/file.tar.gz --execute              # ZD-only
./gtlogs-generator.py 145980 RED-172041 -f /path/to/file.tar.gz --execute  # ZD + Jira

# 6. CONFIGURATION MANAGEMENT
./gtlogs-generator.py --set-profile gt-logs    # Set default AWS profile
./gtlogs-generator.py --show-config            # Show current config

# 7. HELP
./gtlogs-generator.py -h                       # Show help message
```

## Command Reference

### Running Modes

| Mode | Command | Description |
|------|---------|-------------|
| **Interactive** | `./gtlogs-generator.py` | Guided prompts (recommended for first-time users) |
| **Command-line** | `./gtlogs-generator.py <zd> <jira>` | Quick generation with arguments |
| **Force Interactive** | `./gtlogs-generator.py -i` | Explicitly run interactive mode |

### Positional Arguments (Command-line Mode)

- `zendesk_id` - Zendesk ticket ID (e.g., `145980` or `ZD-145980`)
- `jira_id` - Jira ticket ID (e.g., `RED-172041` or `MOD-12345`)

### Optional Arguments

| Flag | Description | Example |
|------|-------------|---------|
| `-i`, `--interactive` | Run in interactive mode | `-i` |
| `-f`, `--file` | Path to support package file | `-f /path/to/package.tar.gz` |
| `-p`, `--profile` | AWS profile to use (overrides default) | `-p my-aws-profile` |
| `-e`, `--execute` | Execute S3 upload with automatic authentication | `--execute` |
| `--set-profile` | Set default AWS profile | `--set-profile gt-logs` |
| `--show-config` | Show current configuration | `--show-config` |
| `-h`, `--help` | Show help message | `-h` |

### Configuration

The tool stores configuration and history in your home directory:

**Configuration file (`~/.gtlogs-config.ini`):**
- Stores your default AWS profile

**History file (`~/.gtlogs-history.json`):**
- Stores your last 20 inputs per field (Zendesk ID, Jira ID, file path, AWS profile)
- Automatically saved after each interactive session
- Used for UP/DOWN arrow navigation in interactive mode

```bash
# View current configuration
./gtlogs-generator.py --show-config

# Set default AWS profile
./gtlogs-generator.py --set-profile redis-support

# View history file
cat ~/.gtlogs-history.json

# Clear history (if needed)
rm ~/.gtlogs-history.json
```

## Input Validation

The tool performs strict validation on all inputs to ensure data integrity:

### Zendesk ID Validation

- ✅ **Must be numerical only**
- ✅ Accepts: `145980`, `ZD-145980`, `zd-145980`
- ❌ Rejects: `145980abc`, `ZD-abc123`, any non-numerical characters
- 📤 **Output format:** `ZD-145980`

**Examples:**

```bash
# Valid
./gtlogs-generator.py 145980 RED-172041        ✓
./gtlogs-generator.py ZD-145980 RED-172041     ✓

# Invalid
./gtlogs-generator.py 145980abc RED-172041     ✗ Error: must be numerical only
./gtlogs-generator.py ZD-abc RED-172041        ✗ Error: must be numerical only
```

### Jira ID Validation

- ✅ **Must be RED-# or MOD-# with numerical suffix only**
- ✅ Accepts: `RED-172041`, `MOD-12345`, `RED172041` (auto-adds hyphen)
- ❌ Rejects: `RED-abc`, `MOD-123abc`, `ABC-123`, numbers without prefix
- 📤 **Output format:** `RED-172041` or `MOD-12345`

**Supported prefixes:**

- `RED-` for Redis Enterprise bugs
- `MOD-` for Module bugs

**Examples:**

```bash
# Valid
./gtlogs-generator.py 145980 RED-172041        ✓
./gtlogs-generator.py 145980 MOD-12345         ✓
./gtlogs-generator.py 145980 RED172041         ✓ (auto-formats to RED-172041)

# Invalid
./gtlogs-generator.py 145980 RED-172041abc     ✗ Error: numerical suffix required
./gtlogs-generator.py 145980 ABC-12345         ✗ Error: must be RED-# or MOD-#
./gtlogs-generator.py 145980 172041            ✗ Error: must include prefix
```

### File Path Validation

- ✅ **File must exist in the filesystem**
- ✅ **Path must point to a file, not a directory**
- ✅ Supports tilde expansion (`~/Downloads/file.tar.gz`)
- ❌ Rejects non-existent files and directories

**Examples:**

```bash
# Valid
./gtlogs-generator.py 145980 RED-172041 -f /path/to/existing/file.tar.gz     ✓
./gtlogs-generator.py 145980 RED-172041 -f ~/Downloads/package.tar.gz        ✓

# Invalid
./gtlogs-generator.py 145980 RED-172041 -f /nonexistent/file.tar.gz          ✗ Error: File does not exist
./gtlogs-generator.py 145980 RED-172041 -f /path/to/directory                ✗ Error: Path is not a file
```

### Interactive Mode Validation

In interactive mode, the tool validates inputs in real-time and allows you to retry:

- **Invalid Zendesk/Jira IDs:** Prompts you to re-enter
- **Invalid file paths:** Asks if you want to try again or skip
- **Helpful error messages:** Shows exactly what went wrong

## ID Format Reference

### Zendesk IDs

- **Accepted formats:** `145980`, `ZD-145980`, `zd-145980` (numerical only)
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
./gtlogs-generator.py

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
./gtlogs-generator.py --set-profile gt-logs

# 2. Generate and execute the upload in one command
./gtlogs-generator.py 145980 RED-172041 -f ~/Downloads/support_package.tar.gz --execute

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
./gtlogs-generator.py --set-profile gt-logs

# 2. Authenticate with AWS SSO (if not already authenticated)
aws sso login --profile gt-logs

# 3. Generate the command with your specific ticket details
./gtlogs-generator.py 145980 RED-172041 -f ~/Downloads/support_package.tar.gz

# 4. Copy the generated AWS CLI command and run it manually
# aws s3 cp ~/Downloads/support_package.tar.gz s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz --profile gt-logs

# 5. Share the S3 path in the Jira ticket
# s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/
```

## Error Handling

The tool performs strict validation and provides clear error messages. **All validations are enforced** - the tool will not generate output for invalid inputs.

### Command-Line Mode Errors

```bash
# Invalid Zendesk ID (non-numerical)
./gtlogs-generator.py 145980abc RED-172041
# ❌ Error: Invalid Zendesk ID: must be numerical only (e.g., 145980 or ZD-145980)

# Invalid Jira format (missing prefix)
./gtlogs-generator.py 145980 12345
# ❌ Error: Jira ID must include prefix (RED- or MOD-)

# Invalid Jira prefix
./gtlogs-generator.py 145980 ABC-12345
# ❌ Error: Invalid Jira ID: must be in format RED-# or MOD-# with numerical suffix

# Invalid Jira suffix (non-numerical)
./gtlogs-generator.py 145980 RED-172041abc
# ❌ Error: Invalid Jira ID: must be in format RED-# or MOD-# with numerical suffix

# File doesn't exist
./gtlogs-generator.py 145980 RED-172041 -f /nonexistent/file.tar.gz
# ❌ Error: File does not exist: /nonexistent/file.tar.gz

# Path is a directory, not a file
./gtlogs-generator.py 145980 RED-172041 -f /Users/username/Downloads
# ❌ Error: Path is not a file: /Users/username/Downloads
```

### Interactive Mode Error Recovery

In interactive mode, validation errors prompt you to retry:

```text
Enter Zendesk ticket ID (e.g., 145980): 145980abc
❌ Invalid Zendesk ID: must be numerical only (e.g., 145980 or ZD-145980)

Enter Zendesk ticket ID (e.g., 145980): 145980
✓ Using: ZD-145980

Enter support package path (optional, press Enter to skip): /nonexistent/file.tar.gz
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

**IMPORTANT:** Before running the generated `aws s3 cp` commands, you must authenticate with AWS SSO:

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
aws s3 cp /path/to/support_package.tar.gz s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz --profile gt-logs
```

**Note:** AWS SSO sessions expire after a period of time. If you get authentication errors, run `aws sso login` again.

## S3 Bucket Structure

Files are organized in the `gt-logs` bucket with two different path structures:

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

The script includes input validation and error handling. Test with various inputs:

```bash
# Test different ID formats
./gtlogs-generator.py 145980 RED-172041
./gtlogs-generator.py ZD-145980 RED172041
./gtlogs-generator.py 145980 MOD-12345

# Test with file paths
./gtlogs-generator.py 145980 RED-172041 -f test.tar.gz
./gtlogs-generator.py 145980 RED-172041 -f /path/to/file.tar.gz -p my-profile
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
# Error: The SSO session associated with this profile has expired or is otherwise invalid
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
- Check AWS profile configuration: `aws configure list --profile <profile-name>`
- Test AWS access: `aws sts get-caller-identity --profile gt-logs`
- Verify SSO session: `aws sso login --profile gt-logs`

## Contributing

This is an internal Redis Support tool. For issues or feature requests, please contact the maintainer.

## License

Internal Redis tool - not for public distribution.

## Support

For questions or issues, contact: <marko.trapani@redis.com>
