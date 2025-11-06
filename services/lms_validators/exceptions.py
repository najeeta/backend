"""
Custom exceptions for LMS validation
"""


class LMSValidationError(Exception):
    """Base exception for LMS validation errors"""
    pass


class InvalidCredentialsError(LMSValidationError):
    """Raised when credential structure is invalid"""
    pass


class UnsupportedLMSError(LMSValidationError):
    """Raised when LMS type is not supported"""
    pass


class ConnectionTestError(LMSValidationError):
    """Raised when connection test fails"""
    pass


class PermissionError(LMSValidationError):
    """Raised when required permissions are missing"""
    pass
