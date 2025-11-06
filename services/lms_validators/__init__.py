"""
LMS connection validators

This module provides validation for LMS connections before they are persisted
to the database. It uses the Strategy Pattern to support multiple LMS types.
"""
from .base import BaseLMSValidator, ValidationResult
from .canvas_validator import CanvasValidator
from .validator_factory import LMSValidatorFactory
from .exceptions import (
    LMSValidationError,
    InvalidCredentialsError,
    UnsupportedLMSError,
    ConnectionTestError,
    PermissionError
)

__all__ = [
    # Base classes
    "BaseLMSValidator",
    "ValidationResult",

    # Validators
    "CanvasValidator",

    # Factory
    "LMSValidatorFactory",

    # Exceptions
    "LMSValidationError",
    "InvalidCredentialsError",
    "UnsupportedLMSError",
    "ConnectionTestError",
    "PermissionError"
]
