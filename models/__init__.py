"""
Pydantic models for API request/response validation
"""
from .lms_connection import (
    LMSConnectionCreate,
    LMSConnectionUpdate,
    LMSConnectionResponse
)
from .instructor import (
    InstructorCreate,
    InstructorUpdate,
    InstructorResponse
)

__all__ = [
    # LMS Connection models
    "LMSConnectionCreate",
    "LMSConnectionUpdate",
    "LMSConnectionResponse",

    # Instructor models
    "InstructorCreate",
    "InstructorUpdate",
    "InstructorResponse"
]
