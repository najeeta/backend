from typing import Optional, List, Dict, Any
from config.supabase_config import supabase


def create_thread(instructor_id: str, title: Optional[str] = None) -> Dict[str, Any]:
    """Create a new conversation thread."""
    data = {
        "instructor_id": instructor_id,
        "title": title or "New Conversation"
    }
    response = supabase.table("threads").insert(data).execute()
    return response.data[0] if response.data else None


def get_thread(thread_id: str) -> Optional[Dict[str, Any]]:
    """Get a thread by ID."""
    response = supabase.table("threads").select("*").eq("id", thread_id).execute()
    return response.data[0] if response.data else None


def get_instructor_threads(instructor_id: str) -> List[Dict[str, Any]]:
    """Get all threads for an instructor, ordered by most recent."""
    response = (
        supabase.table("threads")
        .select("*")
        .eq("instructor_id", instructor_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return response.data if response.data else []


def update_thread(thread_id: str, title: str) -> Dict[str, Any]:
    """Update a thread's title."""
    data = {"title": title}
    response = (
        supabase.table("threads")
        .update(data)
        .eq("id", thread_id)
        .execute()
    )
    return response.data[0] if response.data else None


def delete_thread(thread_id: str) -> bool:
    """Delete a thread (cascades to messages)."""
    response = supabase.table("threads").delete().eq("id", thread_id).execute()
    return True if response.data else False
