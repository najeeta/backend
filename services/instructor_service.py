from typing import Optional, Dict, Any
from config.supabase_config import supabase


def create_instructor(clerk_user_id: str) -> Dict[str, Any]:
    """Create a new instructor record.

    Args:
        clerk_user_id: The Clerk user ID for the instructor

    Returns:
        Dict containing the created instructor record
    """
    data = {
        "clerk_user_id": clerk_user_id
    }
    response = supabase.table("instructors").insert(data).execute()
    return response.data[0] if response.data else None


def get_instructor(instructor_id: str) -> Optional[Dict[str, Any]]:
    """Get an instructor by ID.

    Args:
        instructor_id: The UUID of the instructor

    Returns:
        Dict containing the instructor record or None if not found
    """
    response = supabase.table("instructors").select("*").eq("id", instructor_id).execute()
    return response.data[0] if response.data else None


def get_instructor_by_clerk_id(clerk_user_id: str) -> Optional[Dict[str, Any]]:
    """Get an instructor by Clerk user ID.

    Args:
        clerk_user_id: The Clerk user ID

    Returns:
        Dict containing the instructor record or None if not found
    """
    response = (
        supabase.table("instructors")
        .select("*")
        .eq("clerk_user_id", clerk_user_id)
        .execute()
    )
    return response.data[0] if response.data else None


def update_instructor(instructor_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Update an instructor's fields.

    Args:
        instructor_id: The UUID of the instructor to update
        **kwargs: Fields to update (e.g., onboarding_completed=True)

    Returns:
        Dict containing the updated instructor record or None if not found
    """
    if not kwargs:
        return get_instructor(instructor_id)

    response = (
        supabase.table("instructors")
        .update(kwargs)
        .eq("id", instructor_id)
        .execute()
    )
    return response.data[0] if response.data else None


def delete_instructor(instructor_id: str) -> bool:
    """Delete an instructor by ID.

    Args:
        instructor_id: The UUID of the instructor to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    response = supabase.table("instructors").delete().eq("id", instructor_id).execute()
    return len(response.data) > 0
