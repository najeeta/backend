from typing import Optional, Dict, Any, List
from config.supabase_config import supabase


def create_lms_connection(
    instructor_id: str,
    lms_type: str,
    name: str,
    credentials: Dict[str, Any],
    is_active: bool = True
) -> Dict[str, Any]:
    """Create a new LMS connection record.

    Args:
        instructor_id: The ID of the instructor
        lms_type: The type of LMS (e.g., 'canvas', 'moodle')
        name: A friendly name for this connection
        credentials: JSONB credentials for the LMS
        is_active: Whether the connection is active (default: True)

    Returns:
        Dict containing the created LMS connection record
    """
    data = {
        "instructor_id": instructor_id,
        "lms_type": lms_type,
        "name": name,
        "credentials": credentials,
        "is_active": is_active
    }
    response = supabase.table("lms_connections").insert(data).execute()
    return response.data[0] if response.data else None


def get_lms_connection(connection_id: str) -> Optional[Dict[str, Any]]:
    """Get an LMS connection by ID.

    Args:
        connection_id: The UUID of the LMS connection

    Returns:
        Dict containing the LMS connection record or None if not found
    """
    response = supabase.table("lms_connections").select("*").eq("id", connection_id).execute()
    return response.data[0] if response.data else None


def get_lms_connections_by_instructor(instructor_id: str) -> List[Dict[str, Any]]:
    """Get all LMS connections for an instructor.

    Args:
        instructor_id: The ID of the instructor

    Returns:
        List of LMS connection records
    """
    response = (
        supabase.table("lms_connections")
        .select("*")
        .eq("instructor_id", instructor_id)
        .execute()
    )
    return response.data if response.data else []


def get_active_lms_connections_by_instructor(instructor_id: str) -> List[Dict[str, Any]]:
    """Get all active LMS connections for an instructor.

    Args:
        instructor_id: The ID of the instructor

    Returns:
        List of active LMS connection records
    """
    response = (
        supabase.table("lms_connections")
        .select("*")
        .eq("instructor_id", instructor_id)
        .eq("is_active", True)
        .execute()
    )
    return response.data if response.data else []


def update_lms_connection(connection_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Update an LMS connection's fields.

    Args:
        connection_id: The UUID of the LMS connection to update
        **kwargs: Fields to update (e.g., name="New Name", is_active=False)

    Returns:
        Dict containing the updated LMS connection record or None if not found
    """
    if not kwargs:
        return get_lms_connection(connection_id)

    response = (
        supabase.table("lms_connections")
        .update(kwargs)
        .eq("id", connection_id)
        .execute()
    )
    return response.data[0] if response.data else None


def update_last_sync(connection_id: str) -> Optional[Dict[str, Any]]:
    """Update the last_sync timestamp for an LMS connection.

    Args:
        connection_id: The UUID of the LMS connection

    Returns:
        Dict containing the updated LMS connection record or None if not found
    """
    from datetime import datetime, timezone

    response = (
        supabase.table("lms_connections")
        .update({"last_sync": datetime.now(timezone.utc).isoformat()})
        .eq("id", connection_id)
        .execute()
    )
    return response.data[0] if response.data else None


def delete_lms_connection(connection_id: str) -> bool:
    """Delete an LMS connection by ID.

    Args:
        connection_id: The UUID of the LMS connection to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    response = supabase.table("lms_connections").delete().eq("id", connection_id).execute()
    return len(response.data) > 0
