# Input Format Analysis - GT Logs Helper

Comprehensive analysis of all possible input formats for S3 upload/download operations.

## Current Support Matrix

### ✅ Currently Supported

#### Download Mode (`parse_s3_path`)

| Format | Example | Status | Notes |
|--------|---------|--------|-------|
| **Full S3 URI** | `s3://gt-logs/zendesk-tickets/ZD-145980/file` | ✅ | AWS |
| **Numeric Ticket ID** | `145980` | ✅ | Auto-formats |
| **Formatted Ticket ID** | `ZD-145980` | ✅ | Direct |
| **Lowercase Ticket ID** | `zd-145980` | ✅ | Case-insensitive |
| **Combined ZD+Jira** | `ZD-145980-RED-172041` | ✅ | Hyphen-sep |
| **Numeric + Jira** | `145980-RED-172041` | ✅ | ZD added |
| **Zendesk Agent URL** ¹ | `https://co.zendesk.com/agent/tickets/123` | ✅ |  |
| **Zendesk Public URL** ¹ | `https://co.zendesk.com/tickets/123456` | ✅ |  |
| **Jira URL** ² | `https://jira.co.com/browse/RED-172041` | ✅ |  |
| **Partial S3 path (ZD)** ² | `zendesk-tickets/ZD-145980/f` | ✅ | Auto-bucket |
| **Partial S3 path (ZD+Jira)** ² | `exa-to-gt/ZD-1-RED-2/f` | ✅ | Auto-bucket |
| **Partial bucket/key** | `bucket-name/path/to/file` | ✅ | Direct split |

¹ Added in v1.6.1
² Added in v1.6.2

#### Upload Mode (Separate Arguments)

| Format | Example | Status | Notes |
|--------|---------|--------|-------|
| **ZD ID (numeric)** | `145980` | ✅ | First arg |
| **ZD ID (formatted)** | `ZD-145980` | ✅ | First arg |
| **Zendesk URL** ¹ | `https://c.zendesk.com/agent/tickets/123` | ✅ | First arg |
| **Jira ID (formatted)** | `RED-172041` | ✅ | Second arg |
| **Jira ID (no hyphen)** | `RED172041` | ✅ | Auto-hyphen |
| **Jira URL** ² | `https://jira.co.com/browse/RED-172041` | ✅ | Second arg |

¹ Added in v1.6.1
² Added in v1.6.2

---

## 🔍 Potential Enhancements

### High Priority - User-Friendly Additions

#### 1. Jira URL Support

**Use Case**: Users copy Jira ticket URLs from browser

**Examples**:

```text
https://jira.redis.com/browse/RED-172041
https://jira.company.com/browse/MOD-12345
https://jira.atlassian.net/browse/RED-172041
```

**Implementation**:

```python
def extract_jira_id_from_url(url: str) -> Optional[str]:
    """Extract Jira ID from Jira URL."""
    jira_pattern = r'/browse/(RED|MOD)-(\d+)'
    match = re.search(jira_pattern, url, re.IGNORECASE)
    if match:
        prefix = match.group(1).upper()
        number = match.group(2)
        return f"{prefix}-{number}"
    return None
```

**Benefits**:

- Consistent with Zendesk URL support
- Natural workflow (copy from Jira, paste into tool)
- Zero learning curve

**Priority**: HIGH - mirrors existing Zendesk URL functionality

---

#### 2. AWS S3 Console URLs

**Use Case**: Users viewing files in AWS Console copy URL from address bar

**Examples**:

```text
# Bucket browser URL
https://s3.console.aws.amazon.com/s3/buckets/gt-logs?prefix=zendesk-tickets/ZD-145980/

# Object detail URL
https://us-west-2.console.aws.amazon.com/s3/object/gt-logs?prefix=zendesk-tickets/ZD-145980/file.tar.gz
https://console.aws.amazon.com/s3/object/gt-logs?region=us-east-1&prefix=zendesk-tickets/ZD-145980/file.tar.gz

# Bucket selection URL with object
https://s3.console.aws.amazon.com/s3/object/gt-logs/zendesk-tickets/ZD-145980/file.tar.gz
```

**Implementation**:

```python
def parse_aws_console_url(url: str) -> Optional[tuple[str, str]]:
    """Extract bucket and key from AWS S3 Console URL."""
    # Pattern 1: ?prefix= parameter
    prefix_match = re.search(r's3/buckets?/([^?/]+)\?.*prefix=([^&]+)', url)
    if prefix_match:
        bucket = prefix_match.group(1)
        key = urllib.parse.unquote(prefix_match.group(2))
        return bucket, key

    # Pattern 2: /object/{bucket}/{key}
    object_match = re.search(r's3/object/([^/]+)/(.+?)(?:\?|$)', url)
    if object_match:
        bucket = object_match.group(1)
        key = urllib.parse.unquote(object_match.group(2))
        return bucket, key

    return None
```

**Benefits**:

- Natural when users are browsing S3 in console
- Eliminates manual path construction
- Reduces copy/paste errors

**Priority**: MEDIUM - useful but less common than Jira URLs

---

#### 3. Partial S3 Paths (Key-Only)

**Use Case**: Users copy just the key from S3 console or logs

**Examples**:

```text
zendesk-tickets/ZD-145980/file.tar.gz
exa-to-gt/ZD-145980-RED-172041/debuginfo.tar.gz
```

**Current Behavior**:

- Would be interpreted as `bucket=zendesk-tickets`, `key=ZD-145980/file.tar.gz` ❌

**Desired Behavior**:

- Recognize known path prefixes
- Auto-prepend `gt-logs` bucket

**Implementation**:

```python
def parse_s3_path(s3_path: str):
    # ... existing code ...

    # Check for known path prefixes (key-only format)
    if s3_path.startswith("zendesk-tickets/") or s3_path.startswith("exa-to-gt/"):
        return "gt-logs", s3_path

    # ... rest of function ...
```

**Benefits**:

- Handles partial copies from logs/console
- Works with both upload paths

**Priority**: MEDIUM - nice-to-have for power users

---

### Medium Priority - Convenience Features

#### 4. Space-Separated Combined Input

**Use Case**: More natural input for some users

**Examples**:

```text
145980 RED-172041
ZD-145980 RED-172041
```

**Current Behavior**: Treated as single string, fails Jira extraction ❌

**Implementation**:

```python
def parse_s3_path(s3_path: str):
    # Normalize spaces to hyphens if it looks like "ZD JIRA"
    if ' ' in s3_path:
        parts = s3_path.split()
        if len(parts) == 2:
            # Check if second part looks like Jira ID
            if re.match(r'(RED|MOD)-?\d+', parts[1], re.IGNORECASE):
                s3_path = '-'.join(parts)

    # ... continue with existing logic ...
```

**Benefits**:

- More forgiving input parsing
- Handles accidental spaces

**Drawbacks**:

- Could introduce ambiguity
- May confuse users about correct format

**Priority**: LOW - risk of confusion outweighs benefit

---

#### 5. Alternative Separators

**Use Case**: Users using different separator conventions

**Examples**:

```text
145980/RED-172041  (slash separator)
145980_RED-172041  (underscore)
```

**Recommendation**: **DON'T IMPLEMENT**

**Reasoning**:

- Slashes conflict with S3 paths
- Creates ambiguity in parsing
- No clear user benefit
- Better to enforce single standard (hyphen)

**Priority**: REJECTED

---

### Low Priority - Edge Cases

#### 6. URL-Encoded Paths

**Use Case**: Paths copied from URLs with special characters

**Examples**:

```text
s3://gt-logs/zendesk-tickets/ZD-145980/file%20with%20spaces.tar.gz
```

**Implementation**:

```python
import urllib.parse

def parse_s3_path(s3_path: str):
    # URL-decode the path first
    s3_path = urllib.parse.unquote(s3_path)

    # ... continue with existing logic ...
```

**Benefits**:

- Handles URL-encoded special characters
- Works with browser copy/paste

**Priority**: LOW - rare in practice (S3 keys should avoid spaces)

---

#### 7. Case-Insensitive Everything

**Use Case**: Users typing quickly or from mobile

**Examples**:

```text
zd-145980-red-172041
ZD-145980-RED-172041
Zd-145980-Red-172041
```

**Current Support**: Works (validation functions uppercase internally)

**Recommendation**: Already handled ✅

---

## 📊 Recommended Implementation Priority

### ✅ Completed

1. **Jira URL Support** ⭐⭐⭐ - **IMPLEMENTED in v1.6.2**
   - Mirrors existing Zendesk URL feature
   - Clear user benefit
   - Low implementation complexity
   - No breaking changes

2. **Partial S3 Paths (Key-Only)** ⭐⭐ - **IMPLEMENTED in v1.6.2**
   - Helpful for log parsing scenarios
   - Low complexity
   - Careful validation implemented (avoids false positives)

### Phase 2: Useful Additions (v1.7.0)

1. **AWS S3 Console URL Support** ⭐ - **SKIPPED**
   - User feedback: "people using this script will never be getting those URLs"
   - Not implementing

### Phase 3: Optional Enhancements (Future)

1. **URL Decoding** ⭐
   - Edge case handling
   - Trivial implementation
   - Almost never needed in practice

### ❌ Not Recommended

- Space-separated input (too ambiguous)
- Alternative separators (conflicts with S3 paths)

---

## 🧪 Testing Strategy

For each new format:

1. **Unit tests** with valid/invalid examples
2. **Integration tests** with real S3 paths
3. **Error message clarity** when format not recognized
4. **Documentation updates** with examples

### Example Test Cases (Jira URL)

```python
test_cases = [
    ("https://jira.redis.com/browse/RED-172041", "RED-172041"),
    ("https://jira.company.com/browse/MOD-12345", "MOD-12345"),
    ("https://atlassian.net/browse/red-99999", "RED-99999"),
    ("https://jira.com/browse/INVALID-123", None),  # Wrong prefix
    ("https://not-jira.com/browse/RED-123", None),  # Not a Jira URL
]
```

---

## 💡 User Education

For each supported format, update:

1. **Interactive mode prompts** with examples
2. **README.md** examples section
3. **Wiki** usage documentation
4. **Error messages** showing accepted formats

### Example Updated Prompt

```text
Enter S3 path, ticket ID, or URL:
Examples:
  - Full path: s3://gt-logs/zendesk-tickets/ZD-145980/file.tar.gz
  - Ticket ID: 145980 or ZD-145980
  - Combined: ZD-145980-RED-172041
  - Zendesk URL: https://redislabs.zendesk.com/agent/tickets/150002
  - Jira URL: https://jira.redis.com/browse/RED-172041      <-- NEW
  - AWS Console URL: https://s3.console.aws.amazon.com/...  <-- NEW
```

---

## 🎯 Summary Recommendation

**✅ Implemented in v1.6.2**:

- ✅ Jira URL support (high value, low risk) - COMPLETE
- ✅ Partial S3 paths (key-only) - COMPLETE

**Skipped based on user feedback**:

- ❌ AWS S3 Console URL support (users don't encounter these URLs)

**Consider for future versions**:

- Smart clipboard detection (user requested: "would be great!")
- URL decoding (low priority edge case)

**Do NOT implement**:

- Space-separated input (too ambiguous)
- Alternative separators (conflicts with S3 paths)

This approach maximizes user convenience while maintaining code clarity
and avoiding ambiguous parsing.
