import pytest
from services import message_service, thread_service, teacher_service
from config.supabase_config import supabase


@pytest.fixture
def test_thread():
    """Create a test teacher and thread for message tests."""
    teacher = teacher_service.create_teacher(
        email="message_test@example.com",
        name="Message Test Teacher"
    )
    thread = thread_service.create_thread(
        teacher_id=teacher["id"],
        title="Test Thread for Messages"
    )
    yield thread
    # Cleanup (cascades to messages)
    supabase.table("teachers").delete().eq("id", teacher["id"]).execute()


def test_create_message(test_thread):
    """Test creating a message."""
    message = message_service.create_message(
        thread_id=test_thread["id"],
        role="user",
        content="Hello, this is a test message",
        external_id="ext_123"
    )

    assert message is not None
    assert message["thread_id"] == test_thread["id"]
    assert message["role"] == "user"
    assert message["content"] == "Hello, this is a test message"
    assert message["external_id"] == "ext_123"
    assert "id" in message


def test_create_message_invalid_role(test_thread):
    """Test that creating a message with invalid role raises error."""
    with pytest.raises(ValueError):
        message_service.create_message(
            thread_id=test_thread["id"],
            role="invalid_role",
            content="This should fail"
        )


def test_get_thread_messages(test_thread):
    """Test retrieving all messages for a thread."""
    # Create multiple messages
    msg1 = message_service.create_message(
        thread_id=test_thread["id"],
        role="user",
        content="First message"
    )
    msg2 = message_service.create_message(
        thread_id=test_thread["id"],
        role="assistant",
        content="Second message"
    )

    # Retrieve messages
    messages = message_service.get_thread_messages(test_thread["id"])

    assert len(messages) >= 2
    assert messages[0]["id"] == msg1["id"]
    assert messages[1]["id"] == msg2["id"]
    # Verify chronological order
    assert messages[0]["content"] == "First message"
    assert messages[1]["content"] == "Second message"


def test_get_message(test_thread):
    """Test retrieving a single message by ID."""
    # Create message
    created_message = message_service.create_message(
        thread_id=test_thread["id"],
        role="user",
        content="Test message content"
    )

    # Retrieve message
    retrieved_message = message_service.get_message(created_message["id"])

    assert retrieved_message is not None
    assert retrieved_message["id"] == created_message["id"]
    assert retrieved_message["content"] == "Test message content"


def test_get_message_by_external_id(test_thread):
    """Test retrieving a message by external ID."""
    external_id = "ext_test_456"

    # Create message
    created_message = message_service.create_message(
        thread_id=test_thread["id"],
        role="user",
        content="Message with external ID",
        external_id=external_id
    )

    # Retrieve by external ID
    retrieved_message = message_service.get_message_by_external_id(external_id)

    assert retrieved_message is not None
    assert retrieved_message["id"] == created_message["id"]
    assert retrieved_message["external_id"] == external_id


def test_message_roles(test_thread):
    """Test all valid message roles."""
    roles = ["user", "assistant", "system"]

    for role in roles:
        message = message_service.create_message(
            thread_id=test_thread["id"],
            role=role,
            content=f"Message with {role} role"
        )
        assert message["role"] == role
