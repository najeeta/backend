from fastapi import APIRouter, HTTPException
from typing import List
from services import lms_connection_service
from services.lms_validators import LMSValidationError
from models.lms_connection import (
    LMSConnectionCreate,
    LMSConnectionUpdate,
    LMSConnectionResponse
)
from config.logging_config import get_logger

# Set up logger for this module
logger = get_logger(__name__)

router = APIRouter()


# Endpoints
@router.post("", response_model=LMSConnectionResponse, status_code=201)
def create_lms_connection(connection: LMSConnectionCreate):
    """Create a new LMS connection.

    Args:
        connection: LMSConnectionCreate model with connection details

    Returns:
        LMSConnectionResponse with created connection data

    Raises:
        HTTPException 400: If validation fails
        HTTPException 500: If creation fails
    """
    logger.info(f"POST /lms-connections - Creating LMS connection for instructor: {connection.instructor_id}, type: {connection.lms_type}")
    try:
        created_connection = lms_connection_service.create_lms_connection(
            instructor_id=connection.instructor_id,
            lms_type=connection.lms_type,
            name=connection.name,
            credentials=connection.credentials,
            is_active=connection.is_active
        )

        if not created_connection:
            logger.error(f"Failed to create LMS connection for instructor: {connection.instructor_id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create LMS connection"
            )

        logger.info(f"Successfully created LMS connection (ID: {created_connection.get('id')}) for instructor: {connection.instructor_id}")
        return created_connection

    except LMSValidationError as e:
        # Return 400 for validation errors (client errors)
        logger.warning(f"LMS validation failed for instructor {connection.instructor_id}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error creating LMS connection for instructor {connection.instructor_id}: {str(e)}")
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
    logger.debug(f"GET /lms-connections/{connection_id}")
    try:
        connection = lms_connection_service.get_lms_connection(connection_id)

        if not connection:
            logger.warning(f"LMS connection not found: {connection_id}")
            raise HTTPException(
                status_code=404,
                detail=f"LMS connection with id '{connection_id}' not found"
            )

        return connection

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving LMS connection {connection_id}: {str(e)}")
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
    logger.info(f"DELETE /lms-connections/{connection_id}")
    try:
        # Check if connection exists
        connection = lms_connection_service.get_lms_connection(connection_id)
        if not connection:
            logger.warning(f"Attempted to delete non-existent LMS connection: {connection_id}")
            raise HTTPException(
                status_code=404,
                detail=f"LMS connection with id '{connection_id}' not found"
            )

        # Delete the connection
        success = lms_connection_service.delete_lms_connection(connection_id)

        if not success:
            logger.error(f"Failed to delete LMS connection: {connection_id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete LMS connection"
            )

        logger.info(f"Successfully deleted LMS connection: {connection_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting LMS connection {connection_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
