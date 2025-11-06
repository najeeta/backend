from typing import Optional, List, Dict, Any
from config.supabase_config import supabase


def create_message(
    thread_id: str,
    role: str,
    content: str,
    external_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new message in a thread."""
    if role not in ['user', 'assistant', 'system']:
        raise ValueError(f"Invalid role: {role}. Must be 'user', 'assistant', or 'system'")

    data = {
        "thread_id": thread_id,
        "role": role,
        "content": content,
        "external_id": external_id
    }
    response = supabase.table("messages").insert(data).execute()

    # Update thread's updated_at timestamp
    supabase.table("threads").update({"updated_at": "now()"}).eq("id", thread_id).execute()

    return response.data[0] if response.data else None


def get_thread_messages(thread_id: str) -> List[Dict[str, Any]]:
    """Get all messages for a thread, ordered chronologically."""
    response = (
        supabase.table("messages")
        .select("*")
        .eq("thread_id", thread_id)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data if response.data else []


def get_message(message_id: str) -> Optional[Dict[str, Any]]:
    """Get a single message by ID."""
    response = supabase.table("messages").select("*").eq("id", message_id).execute()
    return response.data[0] if response.data else None


def get_message_by_external_id(external_id: str) -> Optional[Dict[str, Any]]:
    """Get a message by its external/client-side ID."""
    response = (
        supabase.table("messages")
        .select("*")
        .eq("external_id", external_id)
        .execute()
    )
    return response.data[0] if response.data else None
