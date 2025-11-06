"""
Pydantic models for LMS connections
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class LMSConnectionCreate(BaseModel):
    """Request model for creating an LMS connection."""
    instructor_id: str = Field(..., description="ID of the instructor")
    lms_type: str = Field(..., description="Type of LMS (e.g., 'canvas', 'moodle')")
    name: str = Field(..., description="Friendly name for this connection")
    credentials: Dict[str, Any] = Field(..., description="LMS credentials (API key, token, etc.)")
    is_active: bool = Field(default=True, description="Whether the connection is active")


class LMSConnectionUpdate(BaseModel):
    """Request model for updating an LMS connection."""
    lms_type: Optional[str] = Field(None, description="Type of LMS")
    name: Optional[str] = Field(None, description="Friendly name for this connection")
    credentials: Optional[Dict[str, Any]] = Field(None, description="LMS credentials")
    is_active: Optional[bool] = Field(None, description="Whether the connection is active")


class LMSConnectionResponse(BaseModel):
    """Response model for LMS connection data."""
    id: str = Field(..., description="UUID of the LMS connection")
    instructor_id: str = Field(..., description="ID of the instructor")
    lms_type: str = Field(..., description="Type of LMS")
    name: str = Field(..., description="Friendly name for this connection")
    credentials: Dict[str, Any] = Field(..., description="LMS credentials")
    is_active: bool = Field(..., description="Whether the connection is active")
    last_sync: Optional[datetime] = Field(None, description="Last sync timestamp")
    created_at: datetime = Field(..., description="When the connection was created")
    updated_at: datetime = Field(..., description="When the connection was last updated")

    class Config:
        from_attributes = True
