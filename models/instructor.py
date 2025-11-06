"""
Pydantic models for instructors
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InstructorCreate(BaseModel):
    """Request model for creating an instructor."""
    clerk_user_id: str = Field(..., description="Clerk user ID for the instructor")


class InstructorUpdate(BaseModel):
    """Request model for updating an instructor."""
    onboarding_completed: Optional[bool] = Field(None, description="Whether the instructor has completed onboarding")


class InstructorResponse(BaseModel):
    """Response model for instructor data."""
    id: str = Field(..., description="UUID of the instructor")
    clerk_user_id: str = Field(..., description="Clerk user ID")
    onboarding_completed: bool = Field(default=False, description="Whether the instructor has completed onboarding")
    created_at: datetime = Field(..., description="When the instructor was created")
    updated_at: datetime = Field(..., description="When the instructor was last updated")

    class Config:
        from_attributes = True
