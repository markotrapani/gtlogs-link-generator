# GT Logs Link Generator

A command-line tool for generating S3 bucket URLs and AWS CLI commands for Redis Support packages. This tool helps Redis Support engineers quickly create properly formatted S3 paths for sharing customer support packages securely with engineering teams.

## Purpose

When Redis Support needs to share customer support packages with Engineering (via Jira tickets), files are uploaded to the `gt-logs` S3 bucket with a specific naming convention that links the Zendesk ticket to the Jira issue.

This tool automates the generation of:
- S3 bucket paths in the format: `s3://gt-logs/exa-to-gt/ZD-<ticket>-<jira>/`
- Complete AWS CLI commands for uploading support packages

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

### Basic Usage - Generate S3 Path

```bash
./gtlogs-generator.py 145980 RED-172041
```

**Output:**
```
======================================================================
GT Logs Link Generator
======================================================================

S3 Path:
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/

AWS CLI Command:
  aws s3 cp <support_package_path> s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/<support_package_name>

======================================================================

ℹ️  Tip: Use -f to specify the support package file path
ℹ️  Tip: Set a default AWS profile with --set-profile
```

### Generate Complete AWS CLI Command

```bash
./gtlogs-generator.py 145980 RED-172041 -f /path/to/support_package.tar.gz
```

**Output:**
```
======================================================================
GT Logs Link Generator
======================================================================

S3 Path:
  s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/

AWS CLI Command:
  aws s3 cp /path/to/support_package.tar.gz s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz

======================================================================
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

### Example 1: Module Bug (MOD Jira)

```bash
./gtlogs-generator.py 145980 MOD-12345 -f /Downloads/customer_support.tar.gz
```

Generates:
```bash
aws s3 cp /Downloads/customer_support.tar.gz s3://gt-logs/exa-to-gt/ZD-145980-MOD-12345/customer_support.tar.gz --profile redis-support
```

### Example 2: Redis Enterprise Bug (RED Jira)

```bash
./gtlogs-generator.py 147823 RED-172041 -f ./support_pkg_cluster_1.tar.gz
```

Generates:
```bash
aws s3 cp ./support_pkg_cluster_1.tar.gz s3://gt-logs/exa-to-gt/ZD-147823-RED-172041/support_pkg_cluster_1.tar.gz
```

### Example 3: Flexible ID Formats

The tool accepts various input formats:

```bash
# Just numbers
./gtlogs-generator.py 145980 RED-172041

# With ZD prefix
./gtlogs-generator.py ZD-145980 RED-172041

# Jira without hyphen (auto-formats)
./gtlogs-generator.py 145980 RED172041
```

All produce the same output: `s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/`

## Command Reference

### Positional Arguments

- `zendesk_id` - Zendesk ticket ID (e.g., `145980` or `ZD-145980`)
- `jira_id` - Jira ticket ID (e.g., `RED-172041` or `MOD-12345`)

### Optional Arguments

| Flag | Description | Example |
|------|-------------|---------|
| `-f`, `--file` | Path to support package file | `-f /path/to/package.tar.gz` |
| `-p`, `--profile` | AWS profile to use (overrides default) | `-p my-aws-profile` |
| `--set-profile` | Set default AWS profile | `--set-profile redis-support` |
| `--show-config` | Show current configuration | `--show-config` |
| `-h`, `--help` | Show help message | `-h` |

### Configuration

The tool stores configuration in `~/.gtlogs-config.ini`:

```bash
# View current configuration
./gtlogs-generator.py --show-config

# Set default AWS profile
./gtlogs-generator.py --set-profile redis-support
```

## ID Format Reference

### Zendesk IDs

- **Accepted formats:** `145980`, `ZD-145980`, `zd-145980`
- **Output format:** `ZD-145980`

### Jira IDs

- **Accepted formats:**
  - `RED-172041` (Redis Enterprise bugs)
  - `MOD-12345` (Module bugs)
  - `RED172041` (auto-adds hyphen)
- **Output format:** `RED-172041` or `MOD-12345`

## Workflow Example

Here's a typical workflow for uploading a support package:

```bash
# 1. Set your default AWS profile (one-time setup)
./gtlogs-generator.py --set-profile redis-support

# 2. Generate the command with your specific ticket details
./gtlogs-generator.py 145980 RED-172041 -f ~/Downloads/support_package.tar.gz

# 3. Copy the generated AWS CLI command and run it
# aws s3 cp ~/Downloads/support_package.tar.gz s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/support_package.tar.gz --profile redis-support

# 4. Share the S3 path in the Jira ticket
# s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/
```

## Error Handling

The tool validates inputs and provides helpful error messages:

```bash
# Invalid Jira format
./gtlogs-generator.py 145980 12345
# Error: Jira ID must include prefix (RED- or MOD-)

# Invalid Jira prefix
./gtlogs-generator.py 145980 ABC-12345
# Error: Invalid Jira ID: must be in format RED-# or MOD-#

# File doesn't exist (warning only)
./gtlogs-generator.py 145980 RED-172041 -f /nonexistent/file.tar.gz
# ⚠️  Warning: File does not exist: /nonexistent/file.tar.gz
# (still generates the command)
```

## Requirements

- Python 3.6 or higher
- No external dependencies (uses Python standard library only)
- AWS CLI (for executing the generated commands)

## S3 Bucket Structure

Files are organized in the `gt-logs` bucket as:

```
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

```
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

- Verify AWS CLI is installed: `aws --version`
- Check AWS profile configuration: `aws configure list --profile <profile-name>`
- Ensure you have permissions to write to the `gt-logs` bucket

## Contributing

This is an internal Redis Support tool. For issues or feature requests, please contact the maintainer.

## License

Internal Redis tool - not for public distribution.

## Support

For questions or issues, contact: marko.trapani@redis.com
