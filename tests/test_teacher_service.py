import pytest
from services import teacher_service
from config.supabase_config import supabase


@pytest.fixture
def cleanup_test_teachers():
    """Cleanup test teachers after each test."""
    test_emails = []
    yield test_emails
    # Cleanup
    for email in test_emails:
        try:
            teacher = teacher_service.get_teacher_by_email(email)
            if teacher:
                supabase.table("teachers").delete().eq("id", teacher["id"]).execute()
        except:
            pass


def test_create_teacher(cleanup_test_teachers):
    """Test creating a teacher."""
    test_email = "test_teacher@example.com"
    cleanup_test_teachers.append(test_email)

    teacher = teacher_service.create_teacher(
        email=test_email,
        name="Test Teacher",
        canvas_user_id="canvas_123"
    )

    assert teacher is not None
    assert teacher["email"] == test_email
    assert teacher["name"] == "Test Teacher"
    assert teacher["canvas_user_id"] == "canvas_123"
    assert "id" in teacher


def test_get_teacher_by_email(cleanup_test_teachers):
    """Test retrieving a teacher by email."""
    test_email = "test_teacher2@example.com"
    cleanup_test_teachers.append(test_email)

    # Create teacher
    created_teacher = teacher_service.create_teacher(
        email=test_email,
        name="Test Teacher 2"
    )

    # Retrieve teacher
    retrieved_teacher = teacher_service.get_teacher_by_email(test_email)

    assert retrieved_teacher is not None
    assert retrieved_teacher["id"] == created_teacher["id"]
    assert retrieved_teacher["email"] == test_email


def test_get_teacher_by_canvas_id(cleanup_test_teachers):
    """Test retrieving a teacher by Canvas user ID."""
    test_email = "test_teacher3@example.com"
    canvas_id = "canvas_test_456"
    cleanup_test_teachers.append(test_email)

    # Create teacher
    created_teacher = teacher_service.create_teacher(
        email=test_email,
        name="Test Teacher 3",
        canvas_user_id=canvas_id
    )

    # Retrieve teacher
    retrieved_teacher = teacher_service.get_teacher_by_canvas_id(canvas_id)

    assert retrieved_teacher is not None
    assert retrieved_teacher["id"] == created_teacher["id"]
    assert retrieved_teacher["canvas_user_id"] == canvas_id


def test_update_teacher_token(cleanup_test_teachers):
    """Test updating a teacher's Canvas access token."""
    test_email = "test_teacher4@example.com"
    cleanup_test_teachers.append(test_email)

    # Create teacher
    teacher = teacher_service.create_teacher(email=test_email)

    # Update token
    new_token = "new_canvas_token_xyz"
    updated_teacher = teacher_service.update_teacher_token(
        teacher["id"],
        new_token
    )

    assert updated_teacher is not None
    assert updated_teacher["canvas_access_token"] == new_token
