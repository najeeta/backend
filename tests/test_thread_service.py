import pytest
from services import thread_service, teacher_service
from config.supabase_config import supabase


@pytest.fixture
def test_teacher():
    """Create a test teacher for thread tests."""
    teacher = teacher_service.create_teacher(
        email="thread_test@example.com",
        name="Thread Test Teacher"
    )
    yield teacher
    # Cleanup (cascades to threads)
    supabase.table("teachers").delete().eq("id", teacher["id"]).execute()


def test_create_thread(test_teacher):
    """Test creating a thread."""
    thread = thread_service.create_thread(
        teacher_id=test_teacher["id"],
        title="Test Thread"
    )

    assert thread is not None
    assert thread["teacher_id"] == test_teacher["id"]
    assert thread["title"] == "Test Thread"
    assert "id" in thread


def test_get_thread(test_teacher):
    """Test retrieving a thread by ID."""
    # Create thread
    created_thread = thread_service.create_thread(
        teacher_id=test_teacher["id"],
        title="Test Thread 2"
    )

    # Retrieve thread
    retrieved_thread = thread_service.get_thread(created_thread["id"])

    assert retrieved_thread is not None
    assert retrieved_thread["id"] == created_thread["id"]
    assert retrieved_thread["title"] == "Test Thread 2"


def test_get_teacher_threads(test_teacher):
    """Test retrieving all threads for a teacher."""
    # Create multiple threads
    thread1 = thread_service.create_thread(
        teacher_id=test_teacher["id"],
        title="Thread 1"
    )
    thread2 = thread_service.create_thread(
        teacher_id=test_teacher["id"],
        title="Thread 2"
    )

    # Retrieve threads
    threads = thread_service.get_teacher_threads(test_teacher["id"])

    assert len(threads) >= 2
    thread_ids = [t["id"] for t in threads]
    assert thread1["id"] in thread_ids
    assert thread2["id"] in thread_ids


def test_update_thread(test_teacher):
    """Test updating a thread's title."""
    # Create thread
    thread = thread_service.create_thread(
        teacher_id=test_teacher["id"],
        title="Original Title"
    )

    # Update title
    updated_thread = thread_service.update_thread(
        thread["id"],
        "Updated Title"
    )

    assert updated_thread is not None
    assert updated_thread["title"] == "Updated Title"


def test_delete_thread(test_teacher):
    """Test deleting a thread."""
    # Create thread
    thread = thread_service.create_thread(
        teacher_id=test_teacher["id"],
        title="Thread to Delete"
    )

    # Delete thread
    result = thread_service.delete_thread(thread["id"])

    assert result is True

    # Verify deletion
    deleted_thread = thread_service.get_thread(thread["id"])
    assert deleted_thread is None
