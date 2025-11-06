# Anita Backend - Architecture Documentation

This document outlines the architecture patterns, conventions, and rules for the Anita backend codebase. All contributors and AI assistants should follow these guidelines.

## 📁 Project Structure

```
backend/
├── models/                      # Pydantic request/response models
│   ├── __init__.py
│   ├── instructor.py
│   └── lms_connection.py
│
├── routers/                     # FastAPI route handlers (thin layer)
│   ├── __init__.py
│   ├── instructors.py
│   └── lms_connections.py
│
├── services/                    # Business logic layer
│   ├── lms_validators/         # LMS-specific validation
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── canvas_validator.py
│   │   ├── validator_factory.py
│   │   └── exceptions.py
│   ├── instructor_service.py
│   └── lms_connection_service.py
│
├── utils/                       # Shared utilities
│   ├── __init__.py
│   ├── exceptions.py
│   └── security.py             # Credential masking & security utils
│
├── config/                      # Configuration
│   ├── __init__.py
│   ├── supabase_config.py
│   └── logging_config.py
│
├── migrations/                  # SQL migrations
│   └── *.sql
│
└── tests/                       # Test suite
    ├── test_models/
    ├── test_routers/
    └── test_services/
```

---

## 🏗️ Architecture Patterns

### 1. **Layered Architecture**

The application follows a strict layered architecture:

```
Router Layer (HTTP) → Service Layer (Business Logic) → Database Layer (Supabase)
```

**Rules:**
- **Routers** only handle HTTP concerns (request parsing, response formatting, status codes)
- **Services** contain all business logic and validation
- **Services** interact directly with Supabase (no ORM or repository layer currently)
- **Models** are for data validation only (Pydantic)

### 2. **Model Organization**

**Location:** `models/` directory

**Convention:**
- One file per entity (e.g., `models/instructor.py`, `models/lms_connection.py`)
- Three model types per entity:
  - `{Entity}Create` - Request model for POST endpoints (required fields)
  - `{Entity}Update` - Request model for PATCH endpoints (all optional fields)
  - `{Entity}Response` - Response model with `from_attributes = True`

**Example:**
```python
# models/instructor.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class InstructorCreate(BaseModel):
    """Request model for creating an instructor."""
    clerk_user_id: str = Field(..., description="Clerk user ID")

class InstructorUpdate(BaseModel):
    """Request model for updating an instructor."""
    onboarding_completed: Optional[bool] = Field(None, description="Onboarding status")

class InstructorResponse(BaseModel):
    """Response model for instructor data."""
    id: str
    clerk_user_id: str
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Export in `models/__init__.py`:**
```python
from .instructor import InstructorCreate, InstructorUpdate, InstructorResponse

__all__ = ["InstructorCreate", "InstructorUpdate", "InstructorResponse"]
```

### 3. **Router Organization**

**Location:** `routers/` directory

**Convention:**
- Import models from `models/` directory
- Keep routers thin - delegate to services
- Handle only HTTP concerns (status codes, exception mapping)
- Use proper HTTP status codes:
  - `201` for resource creation
  - `200` for successful GET/PATCH
  - `204` for successful DELETE
  - `400` for validation errors (client error)
  - `404` for resource not found
  - `409` for conflicts (e.g., duplicate resource)
  - `500` for server errors

**Example:**
```python
# routers/instructors.py
from fastapi import APIRouter, HTTPException
from services import instructor_service
from models.instructor import InstructorCreate, InstructorUpdate, InstructorResponse

router = APIRouter()

@router.post("", response_model=InstructorResponse, status_code=201)
def create_instructor(instructor: InstructorCreate):
    """Create a new instructor."""
    try:
        # Delegate to service
        result = instructor_service.create_instructor(instructor.clerk_user_id)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create")
        return result
    except SomeValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

### 4. **Service Layer**

**Location:** `services/` directory

**Convention:**
- Return `Dict[str, Any]` (matches Supabase response format)
- Contain all business logic and validation
- Raise custom exceptions for error cases
- Use type hints for parameters and return types

**Example:**
```python
# services/instructor_service.py
from typing import Optional, Dict, Any
from config.supabase_config import supabase

def get_instructor(instructor_id: str) -> Optional[Dict[str, Any]]:
    """Get an instructor by ID."""
    response = supabase.table("instructors").select("*").eq("id", instructor_id).execute()
    return response.data[0] if response.data else None
```

### 5. **Validation Strategy Pattern**

**Location:** `services/{domain}_validators/`

**Use Case:** Complex validation that requires external API calls or multi-step checks

**Example: LMS Connection Validators**

The LMS validator system uses the **Strategy Pattern** to support multiple LMS types:

```
services/lms_validators/
├── base.py                 # Abstract base class + ValidationResult
├── canvas_validator.py     # Canvas implementation
├── validator_factory.py    # Factory pattern
└── exceptions.py           # Custom exceptions
```

**Base Validator:**
```python
# services/lms_validators/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Standardized validation result"""
    is_valid: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    missing_permissions: Optional[list[str]] = None

class BaseLMSValidator(ABC):
    """Abstract base class for LMS validators"""

    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
        self.validate_credentials_structure()

    @abstractmethod
    def validate_credentials_structure(self) -> None:
        """Validate credential structure"""
        pass

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Test API connectivity"""
        pass

    @abstractmethod
    def check_permissions(self) -> Tuple[bool, list[str]]:
        """Check required permissions"""
        pass

    def validate(self) -> ValidationResult:
        """Full validation orchestration (template method)"""
        # Orchestrates validation flow
        pass
```

**Factory Pattern:**
```python
# services/lms_validators/validator_factory.py
class LMSValidatorFactory:
    _validators = {
        "canvas": CanvasValidator,
        # "moodle": MoodleValidator,  # Future
    }

    @classmethod
    def create(cls, lms_type: str, credentials: Dict[str, Any]) -> BaseLMSValidator:
        validator_class = cls._validators.get(lms_type.lower())
        if not validator_class:
            raise UnsupportedLMSError(f"LMS type '{lms_type}' not supported")
        return validator_class(credentials)
```

**Integration:**
```python
# services/lms_connection_service.py
from services.lms_validators import LMSValidatorFactory, LMSValidationError

def create_lms_connection(...):
    # Step 1: Validate
    validator = LMSValidatorFactory.create(lms_type, credentials)
    result = validator.validate()

    if not result.is_valid:
        raise LMSValidationError(result.message)

    # Step 2: Persist to database
    # ...
```

**Adding New LMS Types:**

To add support for a new LMS (e.g., Moodle):

1. Create `services/lms_validators/moodle_validator.py`:
```python
from .base import BaseLMSValidator

class MoodleValidator(BaseLMSValidator):
    def validate_credentials_structure(self):
        # Implement
        pass

    def test_connection(self):
        # Implement
        pass

    def check_permissions(self):
        # Implement
        pass

    def _get_connection_metadata(self):
        # Implement
        pass
```

2. Register in `validator_factory.py`:
```python
_validators = {
    "canvas": CanvasValidator,
    "moodle": MoodleValidator,  # Add this
}
```

3. Write tests in `tests/test_services/test_lms_validators/test_moodle_validator.py`

### Canvas Validator Implementation Notes

The Canvas validator uses the **`canvasapi`** Python library, which is the official SDK for Instructure's Canvas LMS.

**Key Points:**

1. **Library:** `canvasapi==3.2.0` - Official Canvas LMS Python SDK
2. **Initialization:** `Canvas(base_url, api_token)`
3. **Methods Used:**
   - `canvas.get_current_user()` - Tests connection and gets user info
   - `canvas.get_courses()` - Checks course read permission
   - `course.get_users(enrollment_type=['student'])` - Checks student read permission
   - `course.get_assignments()` - Checks assignment read permission
   - `canvas.get_accounts()` - Gets account metadata (optional)

**Exception Handling:**
```python
from canvasapi.exceptions import (
    InvalidAccessToken,  # Bad API token
    Unauthorized,        # Lacks permission
    Forbidden,           # Access denied
    CanvasException      # Base exception
)
```

**Example Implementation Pattern:**
```python
from canvasapi import Canvas
from canvasapi.exceptions import Unauthorized, Forbidden

def test_connection(self) -> Tuple[bool, str]:
    try:
        canvas = Canvas(base_url, api_token)
        user = canvas.get_current_user()
        return True, "Connection successful"
    except InvalidAccessToken:
        return False, "Invalid API token"
    except Unauthorized:
        return False, "Unauthorized"
    except CanvasException as e:
        return False, f"Canvas API error: {str(e)}"
```

**Testing with canvasapi:**
```python
@patch('services.lms_validators.canvas_validator.Canvas')
def test_successful_connection(self, mock_canvas_class):
    # Mock Canvas instance
    mock_canvas = Mock()
    mock_user = Mock()
    mock_canvas.get_current_user.return_value = mock_user
    mock_canvas_class.return_value = mock_canvas

    validator = CanvasValidator(credentials)
    success, message = validator.test_connection()

    assert success is True
```

**Why canvasapi over raw requests:**
- ✅ Official SDK maintained by Canvas
- ✅ Built-in pagination handling
- ✅ Type hints and better IDE support
- ✅ Cleaner exception handling
- ✅ Automatic response parsing
- ✅ Better documentation

### 6. **Centralized Logging Configuration**

**Location:** `config/logging_config.py`

**Purpose:** Centralized, environment-based logging configuration for the entire application

The application uses Python's standard `logging` module with a centralized configuration system that supports environment-based log levels.

**Configuration Module:**
```python
# config/logging_config.py
import logging
import sys
import os
from typing import Optional

def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure logging for the application

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If None, reads from LOG_LEVEL environment variable (default: INFO)
    """
    # Get log level from parameter or environment variable
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Validate log level
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # Override any existing configuration
    )

    # Set specific log levels for third-party libraries
    # (to reduce noise from verbose libraries)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Set our application modules to use the configured level
    logging.getLogger("services").setLevel(numeric_level)
    logging.getLogger("routers").setLevel(numeric_level)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module

    Args:
        name: Name of the module (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
```

**Initialize Logging on Application Startup:**
```python
# main.py
from fastapi import FastAPI
from config.logging_config import setup_logging, get_logger

# Configure logging before anything else
setup_logging()

# Get logger for this module
logger = get_logger(__name__)

app = FastAPI(
    title="Anita Backend API",
    description="AI Teaching Assistant Backend with Canvas Integration",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info("=" * 60)
    logger.info("Anita Backend API starting up")
    logger.info("Version: 1.0.0")
    logger.info("=" * 60)
```

**Using Logging in Services:**
```python
# services/lms_connection_service.py
from config.logging_config import get_logger

# Set up logger for this module
logger = get_logger(__name__)

def create_lms_connection(...):
    logger.info(f"Validating LMS connection for {instructor_id} - {lms_type}")
    try:
        # ... validation logic
        logger.debug("Validation successful")
    except LMSValidationError as e:
        logger.error(f"Validation failed: {str(e)}")
        raise
```

**Using Logging in Routers:**
```python
# routers/lms_connections.py
from config.logging_config import get_logger

# Set up logger for this module
logger = get_logger(__name__)

@router.post("", response_model=LMSConnectionResponse, status_code=201)
def create_lms_connection(connection: LMSConnectionCreate):
    logger.info(f"POST /lms-connections - Creating LMS connection for instructor: {connection.instructor_id}")
    try:
        # ... endpoint logic
        logger.info(f"Successfully created LMS connection (ID: {created_connection.get('id')})")
        return created_connection
    except LMSValidationError as e:
        logger.warning(f"LMS validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Environment Configuration:**
```bash
# .env file
LOG_LEVEL=DEBUG   # For development (verbose)
# LOG_LEVEL=INFO  # For production (less verbose)
```

**Log Levels:**
- `DEBUG` - Very verbose, step-by-step information (development)
- `INFO` - Major milestones and successful operations
- `WARNING` - Non-critical issues that should be noted
- `ERROR` - Critical failures that prevent operations
- `CRITICAL` - System-level failures

**Example Log Output:**
```
2025-01-05 10:30:00 - __main__ - INFO - ============================================================
2025-01-05 10:30:00 - __main__ - INFO - Anita Backend API starting up
2025-01-05 10:30:00 - __main__ - INFO - Version: 1.0.0
2025-01-05 10:30:00 - __main__ - INFO - ============================================================
2025-01-05 10:30:15 - routers.lms_connections - INFO - POST /lms-connections - Creating LMS connection for instructor: abc123
2025-01-05 10:30:15 - services.lms_connection_service - INFO - Validating LMS connection for abc123 - canvas
2025-01-05 10:30:15 - services.lms_validators.canvas_validator - INFO - Testing connection to Canvas instance: https://school.instructure.com
2025-01-05 10:30:16 - services.lms_validators.canvas_validator - INFO - Connection successful - authenticated as user: Jane Doe (ID: 54321)
2025-01-05 10:30:16 - services.lms_validators.canvas_validator - INFO - All required permissions verified successfully
2025-01-05 10:30:16 - routers.lms_connections - INFO - Successfully created LMS connection (ID: def456)
```

**Best Practices:**
1. **Always use `get_logger(__name__)`** at the module level - this ensures proper logger hierarchy
2. **Use appropriate log levels:**
   - `logger.debug()` for detailed diagnostics
   - `logger.info()` for successful operations and milestones
   - `logger.warning()` for recoverable issues
   - `logger.error()` for failures
   - `logger.exception()` for exceptions (includes stack trace)
3. **Include context** in log messages (IDs, names, relevant parameters)
4. **Never log sensitive data** (passwords, API tokens, personal information)
5. **Use structured log messages** with f-strings for clarity

**See `LOGGING_GUIDE.md` for detailed logging documentation including Canvas validator logs.**

---

## 🗄️ Database Conventions

### Technology Stack
- **Database:** PostgreSQL (via Supabase)
- **Client:** Supabase Python SDK (no ORM)
- **Migrations:** SQL files in `migrations/` directory

### Migration Files

**Naming Convention:** `{number}_{description}.sql`

Example:
```
001_initial_schema.sql
002_add_conversation_tables.sql
003_create_instructors_table.sql
```

### Database Interaction

**Current Pattern:** Direct Supabase calls in services

```python
from config.supabase_config import supabase

# SELECT
response = supabase.table("instructors").select("*").eq("id", instructor_id).execute()
result = response.data[0] if response.data else None

# INSERT
data = {"field": "value"}
response = supabase.table("instructors").insert(data).execute()
result = response.data[0] if response.data else None

# UPDATE
response = supabase.table("instructors").update(data).eq("id", id).execute()
result = response.data[0] if response.data else None

# DELETE
response = supabase.table("instructors").delete().eq("id", id).execute()
success = len(response.data) > 0
```

**Future Consideration:** If complexity grows, consider adding a repository layer to abstract database calls.

---

## 🧪 Testing Conventions

### Test Organization

```
tests/
├── test_models/            # Test Pydantic model validation
├── test_routers/           # Test API endpoints (integration)
└── test_services/          # Test business logic (unit)
    └── test_lms_validators/
```

### Testing Standards

1. **Use pytest** as the test framework
2. **Mock external dependencies** (API calls, database)
3. **Test coverage should include:**
   - Happy path scenarios
   - Error cases
   - Edge cases
   - Validation failures

### Example Test Structure

```python
# tests/test_services/test_lms_validators/test_canvas_validator.py
import pytest
from unittest.mock import Mock, patch
from canvasapi.exceptions import InvalidAccessToken, Unauthorized

class TestCanvasValidatorStructure:
    """Tests for credential structure validation"""

    def test_valid_credentials(self):
        """Test valid credentials pass"""
        credentials = {"base_url": "...", "api_token": "..."}
        validator = CanvasValidator(credentials)
        assert validator.credentials == credentials

    def test_missing_field(self):
        """Test missing required field raises error"""
        with pytest.raises(InvalidCredentialsError):
            CanvasValidator({"api_token": "..."})

class TestCanvasValidatorConnection:
    """Tests for connection testing"""

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_successful_connection(self, mock_canvas_class):
        """Test successful API connection"""
        # Mock Canvas instance
        mock_canvas = Mock()
        mock_user = Mock()
        mock_canvas.get_current_user.return_value = mock_user
        mock_canvas_class.return_value = mock_canvas

        validator = CanvasValidator(valid_credentials)
        success, msg = validator.test_connection()
        assert success is True
```

---

## 🚨 Error Handling

### Exception Hierarchy

```python
# utils/exceptions.py
class AnitaException(Exception):
    """Base exception for Anita application"""
    pass

class DatabaseError(AnitaException):
    """Database operation errors"""
    pass

class ValidationError(AnitaException):
    """Validation errors"""
    pass
```

### Custom Domain Exceptions

Each domain can define its own exceptions:

```python
# services/lms_validators/exceptions.py
class LMSValidationError(Exception):
    """Base for LMS validation errors"""
    pass

class InvalidCredentialsError(LMSValidationError):
    """Credential structure is invalid"""
    pass

class UnsupportedLMSError(LMSValidationError):
    """LMS type is not supported"""
    pass
```

### Router Error Handling Pattern

```python
@router.post("", response_model=EntityResponse, status_code=201)
def create_entity(data: EntityCreate):
    try:
        result = service.create(...)
        return result
    except ValidationError as e:
        # Client errors (400)
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        # Not found (404)
        raise HTTPException(status_code=404, detail=str(e))
    except ConflictError as e:
        # Conflicts (409)
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        # Unexpected errors (500)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

---

## 🔐 Security Best Practices

### Credential Handling

**CRITICAL RULE: Never log, print, or expose sensitive credentials in plaintext.**

This includes:
- API tokens (Canvas, OpenAI, etc.)
- Database credentials
- API keys and secrets
- Session tokens
- Passwords

### Using Security Utilities

The `utils/security.py` module provides utilities for safe credential handling:

```python
from utils.security import mask_credential, sanitize_log_data

# WRONG - NEVER DO THIS:
logger.info(f"API token: {api_token}")  # ❌ SECURITY VULNERABILITY

# CORRECT - Use masking for debugging:
logger.debug(f"Using API token: {mask_credential(api_token)}")  # ✅ Safe

# Sanitize dictionaries before logging:
safe_data = sanitize_log_data(request_data)
logger.info(f"Request data: {safe_data}")  # ✅ Credentials masked
```

### Security Rules for Logging

1. **NEVER log credentials at INFO or higher** - Only use DEBUG level with masking if absolutely necessary
2. **Always use `mask_credential()`** when logging tokens for debugging
3. **Remove debug credential logs** before production deployment
4. **Use descriptive messages** without exposing actual values:
   - ✅ `"Connection successful - authenticated as user"`
   - ❌ `"Connection successful with token: {token}"`

### Credential Storage

- **Database**: Credentials stored in database should be encrypted at rest
- **Environment Variables**: Use `.env` file for local development (never commit)
- **Code**: Never hardcode credentials in source code
- **Logs**: Ensure log files have restricted access and are rotated securely

### Error Messages

When handling errors, ensure error messages don't expose credentials:

```python
# WRONG:
except Exception as e:
    logger.error(f"Failed with credentials: {credentials}")  # ❌

# CORRECT:
except Exception as e:
    logger.error(f"Failed to connect: {str(e)}")  # ✅
    logger.debug(f"Used instance: {base_url}")    # ✅
```

### Code Review Security Checklist

When reviewing code for security:

- [ ] No credentials logged in plaintext
- [ ] Credentials use `mask_credential()` if logged at DEBUG level
- [ ] Error messages don't expose sensitive data
- [ ] No hardcoded credentials
- [ ] Environment variables used for secrets
- [ ] Database credentials encrypted at rest
- [ ] API responses don't include credentials
- [ ] Test data doesn't use real credentials

### Incident Response

If credentials are accidentally exposed:

1. **Rotate immediately** - Generate new credentials
2. **Revoke old credentials** - Delete/disable exposed credentials
3. **Review access** - Check who may have seen the logs
4. **Fix the code** - Remove insecure logging
5. **Purge logs** - Delete or redact logs with exposed credentials

### Additional Resources

- See `LOGGING_GUIDE.md` for detailed security guidelines
- See `utils/security.py` for available security utilities

---

## 📦 Dependencies

### Managing Requirements

**File:** `requirements.txt`

**Convention:**
- Pin major and minor versions (e.g., `fastapi==0.110.0`)
- Keep dependencies organized by category (commented)
- Update dependencies thoughtfully to avoid breaking changes

**Current Stack:**
```txt
# Web Framework
fastapi==0.110.0
uvicorn==0.27.1
pydantic==2.11.0

# Database
supabase==2.21.1

# External APIs & LMS
openai==1.66.3
canvasapi==3.2.0        # Canvas LMS Python SDK
requests==2.31.0        # HTTP library (for future validators)

# Testing
pytest==8.4.2
httpx==0.28.1

# Utilities
python-dotenv==1.0.1
```

---

## 🔐 Environment Variables

### Configuration

**File:** `.env` (never commit this file)

**Convention:**
- Use uppercase with underscores (e.g., `SUPABASE_URL`)
- Document all required environment variables
- Use `python-dotenv` to load environment variables

**Required Variables:**
```bash
# Logging
LOG_LEVEL=DEBUG          # DEBUG for development, INFO for production

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx

# Authentication
CLERK_SECRET_KEY=xxx

# Environment
ENVIRONMENT=development
```

### Loading Configuration

```python
# config/supabase_config.py
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
```

---

## 📝 Code Style Guidelines

### General Rules

1. **Follow PEP 8** Python style guide
2. **Use type hints** for function parameters and return types
3. **Write docstrings** for all public functions and classes
4. **Keep functions focused** - each function should do one thing well
5. **Avoid deep nesting** - max 3 levels of indentation

### Naming Conventions

- **Functions/Variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private methods:** `_leading_underscore`

### Imports

**Order:**
1. Standard library imports
2. Third-party imports
3. Local application imports

**Example:**
```python
# Standard library
from typing import Dict, Any, Optional
from datetime import datetime

# Third-party
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Local
from services import instructor_service
from models.instructor import InstructorCreate
```

### Docstrings

**Convention:** Google-style docstrings

```python
def create_instructor(clerk_user_id: str) -> Dict[str, Any]:
    """Create a new instructor record.

    Args:
        clerk_user_id: The Clerk user ID for authentication

    Returns:
        Dict containing the created instructor record

    Raises:
        ValidationError: If clerk_user_id is invalid
        DatabaseError: If database operation fails
    """
    pass
```

---

## 🔄 Git Workflow

### Branch Strategy

- `main` - Production-ready code
- Feature branches - Use descriptive names (e.g., `feature/lms-validation`)

### Commit Messages

**Format:** `<type>: <description>`

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring
- `test:` Adding tests
- `docs:` Documentation changes
- `chore:` Maintenance tasks

**Examples:**
```
feat: add Canvas LMS validation
fix: handle missing credentials in validator
refactor: extract models to models/ directory
test: add tests for Canvas validator
docs: update CLAUDE.md with architecture patterns
```

---

## ✅ Checklist for New Features

When adding a new feature, ensure:

- [ ] **Models** are defined in `models/` directory
- [ ] **Router** imports models from `models/`
- [ ] **Service** contains business logic
- [ ] **Service** returns `Dict[str, Any]`
- [ ] **Logging** is added using `get_logger(__name__)` with appropriate log levels
- [ ] **Security** - No credentials logged in plaintext (use `mask_credential()` if needed)
- [ ] **Security** - Error messages don't expose sensitive data
- [ ] **Type hints** are used throughout
- [ ] **Docstrings** are written for public functions
- [ ] **Error handling** follows established patterns
- [ ] **Tests** are written (aim for >80% coverage)
- [ ] **Migration** is created if database changes are needed
- [ ] **Dependencies** are added to `requirements.txt` if needed
- [ ] **Environment variables** are documented if added

---

## 🎯 Examples & Templates

### Adding a New Entity (e.g., "Course")

**1. Create Model:**
```python
# models/course.py
from pydantic import BaseModel, Field
from datetime import datetime

class CourseCreate(BaseModel):
    name: str = Field(..., description="Course name")
    instructor_id: str = Field(..., description="Instructor ID")

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None)

class CourseResponse(BaseModel):
    id: str
    name: str
    instructor_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**2. Create Service:**
```python
# services/course_service.py
from typing import Optional, Dict, Any
from config.supabase_config import supabase

def create_course(name: str, instructor_id: str) -> Dict[str, Any]:
    """Create a new course."""
    data = {"name": name, "instructor_id": instructor_id}
    response = supabase.table("courses").insert(data).execute()
    return response.data[0] if response.data else None

def get_course(course_id: str) -> Optional[Dict[str, Any]]:
    """Get a course by ID."""
    response = supabase.table("courses").select("*").eq("id", course_id).execute()
    return response.data[0] if response.data else None
```

**3. Create Router:**
```python
# routers/courses.py
from fastapi import APIRouter, HTTPException
from services import course_service
from models.course import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter()

@router.post("", response_model=CourseResponse, status_code=201)
def create_course(course: CourseCreate):
    """Create a new course."""
    try:
        result = course_service.create_course(course.name, course.instructor_id)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create course")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

**4. Create Migration:**
```sql
-- migrations/007_create_courses_table.sql
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    instructor_id UUID REFERENCES instructors(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add RLS policies
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
```

**5. Write Tests:**
```python
# tests/test_services/test_course_service.py
import pytest
from services import course_service

def test_create_course():
    """Test course creation"""
    # Implement test
    pass
```

---

## 🚀 Future Architecture Considerations

### When to Add Repository Layer

Consider adding a repository layer when:
- Database queries become complex
- Need to support multiple databases
- Want better testability (easier to mock database)

```python
# database/course_repository.py
class CourseRepository:
    def get_by_id(self, course_id: str) -> Optional[Dict[str, Any]]:
        response = supabase.table("courses").select("*").eq("id", course_id).execute()
        return response.data[0] if response.data else None
```

### When to Use Domain-Driven Design

Consider DDD patterns when:
- Business logic becomes very complex
- Need rich domain models with behavior
- Multiple bounded contexts emerge

---

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [PEP 8 Style Guide](https://pep8.org/)

---

**Last Updated:** 2025-01-05
**Maintainers:** Anita Development Team
