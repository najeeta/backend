"""
Tests for CanvasValidator using canvasapi library
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from canvasapi.exceptions import InvalidAccessToken, Unauthorized, Forbidden, CanvasException
from services.lms_validators import CanvasValidator, InvalidCredentialsError


class TestCanvasValidatorStructure:
    """Tests for credential structure validation"""

    def test_valid_credentials(self):
        """Test that valid credentials pass structure validation"""
        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "test_token_123"
        }

        validator = CanvasValidator(credentials)

        assert validator.credentials["base_url"] == "https://test.instructure.com"
        assert validator.credentials["api_token"] == "test_token_123"

    def test_missing_base_url(self):
        """Test that missing base_url raises error"""
        credentials = {
            "api_token": "test_token"
        }

        with pytest.raises(InvalidCredentialsError) as exc_info:
            CanvasValidator(credentials)

        assert "base_url" in str(exc_info.value)

    def test_missing_api_token(self):
        """Test that missing api_token raises error"""
        credentials = {
            "base_url": "https://test.instructure.com"
        }

        with pytest.raises(InvalidCredentialsError) as exc_info:
            CanvasValidator(credentials)

        assert "api_token" in str(exc_info.value)

    def test_invalid_url_format(self):
        """Test that invalid URL format raises error"""
        credentials = {
            "base_url": "test.instructure.com",  # Missing http://
            "api_token": "test_token"
        }

        with pytest.raises(InvalidCredentialsError) as exc_info:
            CanvasValidator(credentials)

        assert "http" in str(exc_info.value).lower()

    def test_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url"""
        credentials = {
            "base_url": "https://test.instructure.com/",
            "api_token": "test_token"
        }

        validator = CanvasValidator(credentials)

        assert validator.credentials["base_url"] == "https://test.instructure.com"


class TestCanvasValidatorConnection:
    """Tests for connection testing"""

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_successful_connection(self, mock_canvas_class):
        """Test successful connection to Canvas"""
        # Mock Canvas instance and get_current_user
        mock_canvas = Mock()
        mock_user = Mock()
        mock_canvas.get_current_user.return_value = mock_user
        mock_canvas_class.return_value = mock_canvas

        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "test_token"
        }
        validator = CanvasValidator(credentials)

        success, message = validator.test_connection()

        assert success is True
        assert "successful" in message.lower()
        mock_canvas_class.assert_called_once_with("https://test.instructure.com", "test_token")
        mock_canvas.get_current_user.assert_called_once()

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_invalid_token(self, mock_canvas_class):
        """Test invalid token (InvalidAccessToken)"""
        mock_canvas = Mock()
        mock_canvas.get_current_user.side_effect = InvalidAccessToken("Invalid token")
        mock_canvas_class.return_value = mock_canvas

        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "bad_token"
        }
        validator = CanvasValidator(credentials)

        success, message = validator.test_connection()

        assert success is False
        assert "invalid" in message.lower()

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_unauthorized_connection(self, mock_canvas_class):
        """Test unauthorized connection (Unauthorized)"""
        mock_canvas = Mock()
        mock_canvas.get_current_user.side_effect = Unauthorized("Unauthorized")
        mock_canvas_class.return_value = mock_canvas

        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "test_token"
        }
        validator = CanvasValidator(credentials)

        success, message = validator.test_connection()

        assert success is False
        assert "unauthorized" in message.lower()

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_connection_error(self, mock_canvas_class):
        """Test connection error"""
        mock_canvas_class.side_effect = ConnectionError("Connection failed")

        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "test_token"
        }
        validator = CanvasValidator(credentials)

        success, message = validator.test_connection()

        assert success is False
        assert "connect" in message.lower()


class TestCanvasValidatorPermissions:
    """Tests for permission checking"""

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_has_all_permissions(self, mock_canvas_class):
        """Test when token has all required permissions"""
        # Mock Canvas instance
        mock_canvas = Mock()

        # Mock course object
        mock_course = Mock()
        mock_course.get_users.return_value = iter([Mock()])  # Mock PaginatedList with one student
        mock_course.get_assignments.return_value = iter([Mock()])  # Mock PaginatedList with one assignment

        # Mock get_courses to return a list with one course
        mock_canvas.get_courses.return_value = iter([mock_course])

        mock_canvas_class.return_value = mock_canvas

        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "test_token"
        }
        validator = CanvasValidator(credentials)

        has_perms, missing = validator.check_permissions()

        assert has_perms is True
        assert len(missing) == 0

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_missing_courses_permission(self, mock_canvas_class):
        """Test when token cannot read courses"""
        mock_canvas = Mock()
        mock_canvas.get_courses.side_effect = Unauthorized("Cannot read courses")
        mock_canvas_class.return_value = mock_canvas

        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "test_token"
        }
        validator = CanvasValidator(credentials)

        has_perms, missing = validator.check_permissions()

        assert has_perms is False
        assert "read_courses" in missing

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_missing_students_permission(self, mock_canvas_class):
        """Test when token cannot read students"""
        mock_canvas = Mock()

        # Mock course object where get_users fails
        mock_course = Mock()
        mock_course.get_users.side_effect = Forbidden("Cannot read students")
        mock_course.get_assignments.return_value = iter([Mock()])  # Assignments work

        mock_canvas.get_courses.return_value = iter([mock_course])
        mock_canvas_class.return_value = mock_canvas

        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "test_token"
        }
        validator = CanvasValidator(credentials)

        has_perms, missing = validator.check_permissions()

        assert has_perms is False
        assert "read_students" in missing


class TestCanvasValidatorFullValidation:
    """Tests for full validation flow"""

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_successful_validation(self, mock_canvas_class):
        """Test successful full validation"""
        # Mock Canvas instance
        mock_canvas = Mock()

        # Mock user
        mock_user = Mock()
        mock_user.id = 1
        mock_user.name = "Test User"
        mock_user.email = "test@example.com"
        mock_canvas.get_current_user.return_value = mock_user

        # Mock course
        mock_course = Mock()
        mock_course.get_users.return_value = iter([Mock()])
        mock_course.get_assignments.return_value = iter([Mock()])
        mock_canvas.get_courses.return_value = iter([mock_course])

        # Mock accounts
        mock_account = Mock()
        mock_account.id = 1
        mock_account.name = "Test Account"
        mock_canvas.get_accounts.return_value = iter([mock_account])

        mock_canvas_class.return_value = mock_canvas

        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "test_token"
        }
        validator = CanvasValidator(credentials)

        result = validator.validate()

        assert result.is_valid is True
        assert "successful" in result.message.lower()
        assert "canvas_user_id" in result.details
        assert result.details["canvas_user_id"] == 1

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_validation_fails_connection(self, mock_canvas_class):
        """Test validation fails when connection fails"""
        mock_canvas_class.side_effect = ConnectionError("Connection failed")

        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "test_token"
        }
        validator = CanvasValidator(credentials)

        result = validator.validate()

        assert result.is_valid is False
        assert "connect" in result.message.lower() or "connection" in result.message.lower()

    @patch('services.lms_validators.canvas_validator.Canvas')
    def test_validation_fails_permissions(self, mock_canvas_class):
        """Test validation fails when permissions are missing"""
        # Connection succeeds
        mock_canvas = Mock()
        mock_user = Mock()
        mock_canvas.get_current_user.return_value = mock_user

        # But courses endpoint fails
        mock_canvas.get_courses.side_effect = Unauthorized("Cannot read courses")

        mock_canvas_class.return_value = mock_canvas

        credentials = {
            "base_url": "https://test.instructure.com",
            "api_token": "test_token"
        }
        validator = CanvasValidator(credentials)

        result = validator.validate()

        assert result.is_valid is False
        assert "permission" in result.message.lower()
        assert result.missing_permissions is not None
        assert "read_courses" in result.missing_permissions
