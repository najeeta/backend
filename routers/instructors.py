from fastapi import APIRouter, HTTPException
from services import instructor_service
from models.instructor import (
    InstructorCreate,
    InstructorUpdate,
    InstructorResponse
)
from config.logging_config import get_logger

# Set up logger for this module
logger = get_logger(__name__)

router = APIRouter()


# Endpoints
@router.post("", response_model=InstructorResponse, status_code=201)
def create_instructor(instructor: InstructorCreate):
    """Create a new instructor.

    Args:
        instructor: InstructorCreate model with clerk_user_id

    Returns:
        InstructorResponse with created instructor data

    Raises:
        HTTPException 409: If an instructor with this clerk_user_id already exists
        HTTPException 500: If creation fails
    """
    logger.info(f"POST /instructors - Creating instructor with clerk_user_id: {instructor.clerk_user_id}")
    try:
        # Check if instructor with this clerk_user_id already exists
        existing_instructor = instructor_service.get_instructor_by_clerk_id(instructor.clerk_user_id)
        if existing_instructor:
            logger.warning(f"Attempted to create duplicate instructor with clerk_user_id: {instructor.clerk_user_id}")
            raise HTTPException(
                status_code=409,
                detail=f"Instructor with clerk_user_id '{instructor.clerk_user_id}' already exists"
            )

        # Create the instructor
        created_instructor = instructor_service.create_instructor(instructor.clerk_user_id)

        if not created_instructor:
            logger.error(f"Failed to create instructor with clerk_user_id: {instructor.clerk_user_id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create instructor"
            )

        logger.info(f"Successfully created instructor (ID: {created_instructor.get('id')}) with clerk_user_id: {instructor.clerk_user_id}")
        return created_instructor

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error creating instructor with clerk_user_id {instructor.clerk_user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{instructor_id}", response_model=InstructorResponse)
def get_instructor(instructor_id: str):
    """Get an instructor by ID.

    Args:
        instructor_id: UUID of the instructor

    Returns:
        InstructorResponse with instructor data

    Raises:
        HTTPException 404: If instructor not found
        HTTPException 500: If retrieval fails
    """
    try:
        instructor = instructor_service.get_instructor(instructor_id)

        if not instructor:
            raise HTTPException(
                status_code=404,
                detail=f"Instructor with id '{instructor_id}' not found"
            )

        return instructor

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/{instructor_id}", response_model=InstructorResponse)
def update_instructor(instructor_id: str, update_data: InstructorUpdate):
    """Update an instructor's information.

    Args:
        instructor_id: UUID of the instructor to update
        update_data: InstructorUpdate model with fields to update

    Returns:
        InstructorResponse with updated instructor data

    Raises:
        HTTPException 404: If instructor not found
        HTTPException 500: If update fails
    """
    try:
        # Check if instructor exists
        instructor = instructor_service.get_instructor(instructor_id)
        if not instructor:
            raise HTTPException(
                status_code=404,
                detail=f"Instructor with id '{instructor_id}' not found"
            )

        # Prepare update data (only include fields that were provided)
        update_fields = update_data.model_dump(exclude_unset=True)

        if not update_fields:
            # No fields to update, return current instructor
            return instructor

        # Update the instructor
        updated_instructor = instructor_service.update_instructor(instructor_id, **update_fields)

        if not updated_instructor:
            raise HTTPException(
                status_code=500,
                detail="Failed to update instructor"
            )

        return updated_instructor

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{instructor_id}", status_code=204)
def delete_instructor(instructor_id: str):
    """Delete an instructor by ID.

    Args:
        instructor_id: UUID of the instructor to delete

    Returns:
        No content (204) on successful deletion

    Raises:
        HTTPException 404: If instructor not found
        HTTPException 500: If deletion fails
    """
    logger.info(f"DELETE /instructors/{instructor_id}")
    try:
        # Check if instructor exists
        instructor = instructor_service.get_instructor(instructor_id)
        if not instructor:
            logger.warning(f"Attempted to delete non-existent instructor: {instructor_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Instructor with id '{instructor_id}' not found"
            )

        # Delete the instructor
        success = instructor_service.delete_instructor(instructor_id)

        if not success:
            logger.error(f"Failed to delete instructor: {instructor_id}")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete instructor"
            )

        logger.info(f"Successfully deleted instructor: {instructor_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting instructor {instructor_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
