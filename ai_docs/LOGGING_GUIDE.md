# Logging Guide for Canvas Validator

This document explains the logging structure in the Canvas validator and how to configure and use it for debugging.

## Overview

The Canvas validator (`canvas_validator.py`) includes comprehensive logging at multiple levels to help debug connection and permission issues.

## Log Levels Used

- **INFO** - Major milestones in validation flow (connection success, permission verification)
- **DEBUG** - Detailed step-by-step information (checking specific permissions, fetching data)
- **WARNING** - Non-critical issues (no courses found, metadata collection failed)
- **ERROR** - Critical failures (connection failed, permission denied)
- **EXCEPTION** - Unexpected errors with full stack trace

## Logging Points

### 1. Credential Validation
```
INFO: Validating Canvas credential structure
DEBUG: Cleaned base_url: https://example.com/ -> https://example.com
INFO: Credential structure validation successful for Canvas instance: https://example.com
```

### 2. Connection Testing
```
INFO: Testing connection to Canvas instance: https://example.instructure.com
INFO: Connection successful - authenticated as user: John Doe (ID: 12345)
```

### 3. Permission Checking
```
INFO: Checking Canvas API permissions
DEBUG: Checking 'read_courses' permission
INFO: 'read_courses' permission verified - found 5 course(s)
DEBUG: Using course 'Introduction to Python' (ID: 789) for permission testing
DEBUG: Checking 'read_students' permission
INFO: 'read_students' permission verified
DEBUG: Checking 'read_assignments' permission
INFO: 'read_assignments' permission verified
INFO: All required permissions verified successfully
```

### 4. Metadata Collection
```
INFO: Collecting Canvas connection metadata
DEBUG: Fetching current user information
INFO: Collected user metadata: John Doe (ID: 12345)
DEBUG: Attempting to fetch account information
INFO: Collected account metadata: Example University (ID: 1)
INFO: Metadata collection completed successfully
```

## Configuring Logging

### Basic Configuration (main.py or app startup)

```python
import logging

# Configure logging at application startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/anita.log'),
        logging.StreamHandler()  # Also output to console
    ]
)

# Set specific level for Canvas validator
logging.getLogger('services.lms_validators.canvas_validator').setLevel(logging.DEBUG)
```

### Production Configuration

For production, use INFO level and log to file:

```python
import logging
import logging.handlers

# Create logs directory if it doesn't exist
import os
os.makedirs('logs', exist_ok=True)

# Configure with rotating file handler
handler = logging.handlers.RotatingFileHandler(
    'logs/anita.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

# Configure root logger
logging.basicConfig(level=logging.INFO, handlers=[handler])

# Canvas validator to INFO (less verbose)
logging.getLogger('services.lms_validators.canvas_validator').setLevel(logging.INFO)
```

### Development Configuration

For development, use DEBUG level with detailed console output:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

# Canvas validator to DEBUG (very verbose)
logging.getLogger('services.lms_validators.canvas_validator').setLevel(logging.DEBUG)
```

## Example Log Output

### Successful Validation

```
2025-01-05 10:30:00,123 - services.lms_validators.canvas_validator - INFO - Validating Canvas credential structure
2025-01-05 10:30:00,125 - services.lms_validators.canvas_validator - INFO - Credential structure validation successful for Canvas instance: https://school.instructure.com
2025-01-05 10:30:00,126 - services.lms_validators.canvas_validator - INFO - Testing connection to Canvas instance: https://school.instructure.com
2025-01-05 10:30:00,450 - services.lms_validators.canvas_validator - INFO - Connection successful - authenticated as user: Jane Smith (ID: 54321)
2025-01-05 10:30:00,451 - services.lms_validators.canvas_validator - INFO - Checking Canvas API permissions
2025-01-05 10:30:00,452 - services.lms_validators.canvas_validator - DEBUG - Checking 'read_courses' permission
2025-01-05 10:30:00,678 - services.lms_validators.canvas_validator - INFO - 'read_courses' permission verified - found 3 course(s)
2025-01-05 10:30:00,679 - services.lms_validators.canvas_validator - DEBUG - Using course 'Data Science 101' (ID: 999) for permission testing
2025-01-05 10:30:00,680 - services.lms_validators.canvas_validator - DEBUG - Checking 'read_students' permission
2025-01-05 10:30:00,892 - services.lms_validators.canvas_validator - INFO - 'read_students' permission verified
2025-01-05 10:30:00,893 - services.lms_validators.canvas_validator - DEBUG - Checking 'read_assignments' permission
2025-01-05 10:30:01,100 - services.lms_validators.canvas_validator - INFO - 'read_assignments' permission verified
2025-01-05 10:30:01,101 - services.lms_validators.canvas_validator - INFO - All required permissions verified successfully
2025-01-05 10:30:01,102 - services.lms_validators.canvas_validator - INFO - Collecting Canvas connection metadata
2025-01-05 10:30:01,103 - services.lms_validators.canvas_validator - DEBUG - Fetching current user information
2025-01-05 10:30:01,250 - services.lms_validators.canvas_validator - INFO - Collected user metadata: Jane Smith (ID: 54321)
2025-01-05 10:30:01,251 - services.lms_validators.canvas_validator - DEBUG - Attempting to fetch account information
2025-01-05 10:30:01,400 - services.lms_validators.canvas_validator - INFO - Collected account metadata: Example School (ID: 5)
2025-01-05 10:30:01,401 - services.lms_validators.canvas_validator - INFO - Metadata collection completed successfully
```

### Failed Validation (Invalid Token)

```
2025-01-05 10:35:00,123 - services.lms_validators.canvas_validator - INFO - Validating Canvas credential structure
2025-01-05 10:35:00,125 - services.lms_validators.canvas_validator - INFO - Credential structure validation successful for Canvas instance: https://school.instructure.com
2025-01-05 10:35:00,126 - services.lms_validators.canvas_validator - INFO - Testing connection to Canvas instance: https://school.instructure.com
2025-01-05 10:35:00,350 - services.lms_validators.canvas_validator - ERROR - Connection failed: Invalid API token - Invalid access token
```

### Failed Validation (Missing Permissions)

```
2025-01-05 10:40:00,123 - services.lms_validators.canvas_validator - INFO - Validating Canvas credential structure
2025-01-05 10:40:00,125 - services.lms_validators.canvas_validator - INFO - Credential structure validation successful for Canvas instance: https://school.instructure.com
2025-01-05 10:40:00,126 - services.lms_validators.canvas_validator - INFO - Testing connection to Canvas instance: https://school.instructure.com
2025-01-05 10:40:00,450 - services.lms_validators.canvas_validator - INFO - Connection successful - authenticated as user: Limited User (ID: 99999)
2025-01-05 10:40:00,451 - services.lms_validators.canvas_validator - INFO - Checking Canvas API permissions
2025-01-05 10:40:00,452 - services.lms_validators.canvas_validator - DEBUG - Checking 'read_courses' permission
2025-01-05 10:40:00,678 - services.lms_validators.canvas_validator - INFO - 'read_courses' permission verified - found 1 course(s)
2025-01-05 10:40:00,679 - services.lms_validators.canvas_validator - DEBUG - Using course 'Restricted Course' (ID: 111) for permission testing
2025-01-05 10:40:00,680 - services.lms_validators.canvas_validator - DEBUG - Checking 'read_students' permission
2025-01-05 10:40:00,892 - services.lms_validators.canvas_validator - ERROR - 'read_students' permission denied: Forbidden
2025-01-05 10:40:00,893 - services.lms_validators.canvas_validator - DEBUG - Checking 'read_assignments' permission
2025-01-05 10:40:01,100 - services.lms_validators.canvas_validator - INFO - 'read_assignments' permission verified
2025-01-05 10:40:01,101 - services.lms_validators.canvas_validator - WARNING - Permission check failed - missing: read_students
```

## Debugging Tips

### 1. Enable DEBUG logging for troubleshooting

```python
import logging
logging.getLogger('services.lms_validators.canvas_validator').setLevel(logging.DEBUG)
```

### 2. Filter logs by validation attempt

Use timestamps and Canvas instance URL to filter logs for specific validation attempts.

### 3. Look for ERROR level logs first

ERROR logs indicate critical failures. Start debugging from there.

### 4. Check permission verification sequence

The validator checks permissions in order:
1. read_courses (required to continue)
2. read_students (if courses exist)
3. read_assignments (if courses exist)

### 5. Verify Canvas instance URL

Check the INFO log line: `Credential structure validation successful for Canvas instance: ...`
Ensure the URL is correct.

## Log Analysis Patterns

### Connection Issues
```
ERROR - Connection failed: Could not connect to Canvas instance
```
**Action**: Verify `base_url` is correct and Canvas instance is reachable

### Authentication Issues
```
ERROR - Connection failed: Invalid API token
ERROR - Connection failed: Unauthorized
```
**Action**: Verify `api_token` is correct and not expired

### Permission Issues
```
ERROR - 'read_students' permission denied
WARNING - Permission check failed - missing: read_students
```
**Action**: Regenerate Canvas API token with required permissions

### Network Issues
```
EXCEPTION - Connection failed: Unexpected error - Timeout
```
**Action**: Check network connectivity, firewall rules

## Integration with Application Logging

### FastAPI Integration

```python
# main.py
import logging
from fastapi import FastAPI

# Configure logging before app starts
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger = logging.getLogger(__name__)
    logger.info("Application starting up")

    # Set Canvas validator log level from environment
    import os
    log_level = os.getenv("CANVAS_VALIDATOR_LOG_LEVEL", "INFO")
    canvas_logger = logging.getLogger('services.lms_validators.canvas_validator')
    canvas_logger.setLevel(getattr(logging, log_level))
    logger.info(f"Canvas validator log level set to: {log_level}")
```

### Environment-based Configuration

```bash
# .env file
CANVAS_VALIDATOR_LOG_LEVEL=DEBUG  # For development
# CANVAS_VALIDATOR_LOG_LEVEL=INFO  # For production
```

## Best Practices

1. **Production**: Use INFO level, log to rotating files
2. **Development**: Use DEBUG level, log to console + files
3. **Testing**: Capture logs for failed test cases
4. **Monitoring**: Set up alerts for ERROR level logs
5. **Privacy**: Be careful not to log sensitive data (API tokens are never logged)

## 🔐 Security Note - CRITICAL

### ⚠️ NEVER Log Sensitive Credentials

**CRITICAL SECURITY RULE: Credentials (API tokens, passwords, secrets) must NEVER be logged in plaintext.**

This is a serious security vulnerability that can lead to:
- Credential theft from log files or logging services
- Unauthorized access to Canvas and other systems
- Compliance violations (GDPR, FERPA, etc.)
- Reputational damage

### What NOT to Log

**NEVER log any of the following in plaintext:**
- API tokens (`api_token`, `access_token`, `bearer_token`)
- Passwords (`password`, `passwd`)
- API keys (`api_key`, `secret_key`)
- Client secrets
- Session tokens
- Any other authentication credentials

### What IS Safe to Log

The validator logs the following **non-sensitive** information:
- Canvas instance URLs (`base_url`) - e.g., `https://canvas.instructure.com`
- User names and IDs (after successful authentication) - e.g., "John Doe (ID: 12345)"
- Course names and IDs - e.g., "Introduction to Python (ID: 789)"
- Account names and IDs
- Error messages from Canvas API (which don't contain tokens by default)
- Validation status (success/failure)

### Using Credential Masking for Debugging

If you **absolutely must** log credential information for debugging purposes:

1. **Use the `mask_credential()` utility** from `utils.security`:

```python
from utils.security import mask_credential

api_token = "7~ZPwXKaLZPx633QHXvhfRhQMm3rPkM8EUAK6VunZf6PktwVKeJuPt9VNcAkMTMvra"

# WRONG - NEVER DO THIS:
logger.info(f"API token: {api_token}")  # ❌ SECURITY VULNERABILITY

# CORRECT - Use masking:
logger.debug(f"Using API token: {mask_credential(api_token)}")  # ✅ "Using API token: 7~ZP...Mvra"
```

2. **Only log masked credentials at DEBUG level**, never at INFO or higher
3. **Remove debug logging** before production deployment whenever possible
4. **Use descriptive context** without exposing the actual credential:

```python
# Good examples that don't expose credentials:
logger.info("Testing connection to Canvas instance")
logger.info("Connection successful - authenticated as user")
logger.error("Connection failed: Invalid API token")  # ✅ No actual token shown
```

### Available Security Utilities

The `utils/security.py` module provides helper functions:

```python
from utils.security import mask_credential, mask_url_with_credentials, sanitize_log_data

# Mask a credential (shows first and last 4 chars)
masked_token = mask_credential("sk_test_1234567890abcdef")  # "sk_t...cdef"

# Mask credentials in URLs
safe_url = mask_url_with_credentials("https://user:pass@api.example.com")  # "https://***:***@api.example.com"

# Sanitize a dictionary for logging
safe_data = sanitize_log_data({
    "user": "john",
    "api_token": "secret123"
})  # {"user": "john", "api_token": "***MASKED***"}
```

### Code Review Checklist

When reviewing code, verify:
- [ ] No `logger.*` calls contain credential variables (`token`, `password`, `secret`, `key`)
- [ ] Credentials use `mask_credential()` if absolutely necessary for debugging
- [ ] Masked credential logging is at DEBUG level only
- [ ] Error messages don't inadvertently expose credentials
- [ ] Dictionary/object logging uses `sanitize_log_data()` if it might contain credentials

### Production Recommendations

1. **Set LOG_LEVEL=INFO in production** - This prevents DEBUG logs with masked credentials
2. **Use log monitoring** - Set up alerts for patterns like "token", "password" in logs
3. **Rotate logs securely** - Ensure old log files are encrypted and have limited access
4. **Audit logs regularly** - Check for accidental credential exposure
5. **Never commit logs** - Add `logs/` and `*.log` to `.gitignore`

### If Credentials Are Accidentally Logged

If you discover credentials were logged in plaintext:

1. **Rotate the credentials immediately** - Generate new tokens in Canvas
2. **Revoke the exposed credentials** - Delete old tokens
3. **Review log access** - Determine who may have seen the logs
4. **Notify security team** - Follow your organization's incident response process
5. **Fix the code** - Remove the logging statement and use masking if needed
6. **Purge logs** - Delete or redact the logs containing credentials

---

**Last Updated:** 2025-11-05
**Security Audit:** Fixed credential logging vulnerability (v1.1.0)
