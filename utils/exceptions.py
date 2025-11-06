"""
Global custom exceptions for the Anita backend
"""


class AnitaException(Exception):
    """Base exception for Anita application"""
    pass


class DatabaseError(AnitaException):
    """Database operation errors"""
    pass


class ValidationError(AnitaException):
    """Validation errors"""
    pass
