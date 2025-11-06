from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from services import lms_connection_service

router = APIRouter()


# Pydantic Models
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


# Endpoints
@router.post("", response_model=LMSConnectionResponse, status_code=201)
def create_lms_connection(connection: LMSConnectionCreate):
    """Create a new LMS connection.

    Args:
        connection: LMSConnectionCreate model with connection details

    Returns:
        LMSConnectionResponse with created connection data

    Raises:
        HTTPException 500: If creation fails
    """
    try:
        created_connection = lms_connection_service.create_lms_connection(
            instructor_id=connection.instructor_id,
            lms_type=connection.lms_type,
            name=connection.name,
            credentials=connection.credentials,
            is_active=connection.is_active
        )

        if not created_connection:
            raise HTTPException(
                status_code=500,
                detail="Failed to create LMS connection"
            )

        return created_connection

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{connection_id}", response_model=LMSConnectionResponse)
def get_lms_connection(connection_id: str):
    """Get an LMS connection by ID.

    Args:
        connection_id: UUID of the LMS connection

    Returns:
        LMSConnectionResponse with connection data

    Raises:
        HTTPException 404: If connection not found
        HTTPException 500: If retrieval fails
    """
    try:
        connection = lms_connection_service.get_lms_connection(connection_id)

        if not connection:
            raise HTTPException(
                status_code=404,
                detail=f"LMS connection with id '{connection_id}' not found"
            )

        return connection

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/instructor/{instructor_id}", response_model=List[LMSConnectionResponse])
def get_instructor_lms_connections(instructor_id: str, active_only: bool = False):
    """Get all LMS connections for an instructor.

    Args:
        instructor_id: ID of the instructor
        active_only: If True, only return active connections (default: False)

    Returns:
        List of LMSConnectionResponse with connection data

    Raises:
        HTTPException 500: If retrieval fails
    """
    try:
        if active_only:
            connections = lms_connection_service.get_active_lms_connections_by_instructor(instructor_id)
        else:
            connections = lms_connection_service.get_lms_connections_by_instructor(instructor_id)

        return connections

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/{connection_id}", response_model=LMSConnectionResponse)
def update_lms_connection(connection_id: str, update_data: LMSConnectionUpdate):
    """Update an LMS connection's information.

    Args:
        connection_id: UUID of the LMS connection to update
        update_data: LMSConnectionUpdate model with fields to update

    Returns:
        LMSConnectionResponse with updated connection data

    Raises:
        HTTPException 404: If connection not found
        HTTPException 500: If update fails
    """
    try:
        # Check if connection exists
        connection = lms_connection_service.get_lms_connection(connection_id)
        if not connection:
            raise HTTPException(
                status_code=404,
                detail=f"LMS connection with id '{connection_id}' not found"
            )

        # Prepare update data (only include fields that were provided)
        update_fields = update_data.model_dump(exclude_unset=True)

        if not update_fields:
            # No fields to update, return current connection
            return connection

        # Update the connection
        updated_connection = lms_connection_service.update_lms_connection(connection_id, **update_fields)

        if not updated_connection:
            raise HTTPException(
                status_code=500,
                detail="Failed to update LMS connection"
            )

        return updated_connection

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/{connection_id}/sync", response_model=LMSConnectionResponse)
def update_last_sync(connection_id: str):
    """Update the last_sync timestamp for an LMS connection.

    Args:
        connection_id: UUID of the LMS connection

    Returns:
        LMSConnectionResponse with updated connection data

    Raises:
        HTTPException 404: If connection not found
        HTTPException 500: If update fails
    """
    try:
        # Check if connection exists
        connection = lms_connection_service.get_lms_connection(connection_id)
        if not connection:
            raise HTTPException(
                status_code=404,
                detail=f"LMS connection with id '{connection_id}' not found"
            )

        # Update last_sync
        updated_connection = lms_connection_service.update_last_sync(connection_id)

        if not updated_connection:
            raise HTTPException(
                status_code=500,
                detail="Failed to update last_sync timestamp"
            )

        return updated_connection

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{connection_id}", status_code=204)
def delete_lms_connection(connection_id: str):
    """Delete an LMS connection by ID.

    Args:
        connection_id: UUID of the LMS connection to delete

    Returns:
        No content (204) on successful deletion

    Raises:
        HTTPException 404: If connection not found
        HTTPException 500: If deletion fails
    """
    try:
        # Check if connection exists
        connection = lms_connection_service.get_lms_connection(connection_id)
        if not connection:
            raise HTTPException(
                status_code=404,
                detail=f"LMS connection with id '{connection_id}' not found"
            )

        # Delete the connection
        success = lms_connection_service.delete_lms_connection(connection_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete LMS connection"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
