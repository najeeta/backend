"""
Canvas LMS validator implementation using canvasapi library
"""
import logging
from canvasapi import Canvas
from canvasapi.exceptions import (
    CanvasException,
    Unauthorized,
    InvalidAccessToken,
    Forbidden,
    ResourceDoesNotExist
)
from typing import Dict, Any, Tuple
from datetime import datetime, timezone
from .base import BaseLMSValidator
from .exceptions import InvalidCredentialsError
from utils.security import mask_credential

# Set up logger for this module
logger = logging.getLogger(__name__)


class CanvasValidator(BaseLMSValidator):
    """Validator for Canvas LMS connections using canvasapi library"""

    # Required permissions to check
    REQUIRED_PERMISSIONS = [
        "read_courses",
        "read_students",
        "read_assignments"
    ]

    def validate_credentials_structure(self) -> None:
        """
        Ensure Canvas credentials have required fields

        Raises:
            InvalidCredentialsError: If credentials are malformed
        """
        logger.info("Validating Canvas credential structure")

        if "base_url" not in self.credentials:
            logger.error("Credential validation failed: missing 'base_url'")
            raise InvalidCredentialsError("Missing 'base_url' in credentials")

        if "api_token" not in self.credentials:
            logger.error("Credential validation failed: missing 'api_token'")
            raise InvalidCredentialsError("Missing 'api_token' in credentials")

        # Validate token format
        api_token = self.credentials["api_token"]
        if not api_token or not isinstance(api_token, str):
            logger.error("Credential validation failed: api_token must be a non-empty string")
            raise InvalidCredentialsError("api_token must be a non-empty string")

        # Canvas tokens typically have a specific format (e.g., "7~..." or numeric prefixes)
        # We'll do basic validation to catch common issues
        api_token_stripped = api_token.strip()
        if api_token_stripped != api_token:
            logger.warning(f"API token has leading/trailing whitespace - auto-trimming")
            self.credentials["api_token"] = api_token_stripped
            api_token = api_token_stripped

        if len(api_token) < 10:
            logger.error(f"Credential validation failed: api_token appears too short (length: {len(api_token)})")
            raise InvalidCredentialsError(
                "API token appears to be invalid - Canvas tokens are typically 60+ characters long. "
                "Please verify you copied the complete token from Canvas."
            )

        # Validate URL format
        base_url = self.credentials["base_url"]
        if not base_url.startswith(("http://", "https://")):
            logger.error(f"Credential validation failed: invalid URL format: {base_url}")
            raise InvalidCredentialsError("base_url must start with http:// or https://")

        # Clean up the URL (remove trailing slash)
        cleaned_url = base_url.rstrip("/")
        if cleaned_url != base_url:
            logger.debug(f"Cleaned base_url: {base_url} -> {cleaned_url}")
        self.credentials["base_url"] = cleaned_url

        logger.info(f"Credential structure validation successful for Canvas instance: {cleaned_url}")

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test Canvas API connectivity

        Uses canvasapi to verify the API token is valid and the Canvas
        instance is reachable by fetching the current user.

        Returns:
            Tuple of (success: bool, message: str)
        """
        base_url = self.credentials["base_url"]
        api_token = self.credentials["api_token"]

        logger.info(f"Testing connection to Canvas instance: {base_url}")
        # For debugging purposes only - token is masked for security
        logger.debug(f"Using API token: {mask_credential(api_token)}")

        try:
            # Initialize Canvas client
            canvas = Canvas(base_url, api_token)

            # Test connection by getting current user
            user = canvas.get_current_user()
            logger.info(f"Connection successful - authenticated as user: {user.name} (ID: {user.id})")

            # If we get here, connection is successful
            return True, "Connection successful"

        except InvalidAccessToken as e:
            logger.error(f"Connection failed: Invalid API token - {str(e)}")
            return False, (
                "Invalid API token. Please verify: "
                "1) The token was copied correctly without extra spaces or line breaks. "
                "2) The token has not been deleted or expired in Canvas. "
                "3) The token is for the correct Canvas instance (canvas.instructure.com vs. your school's instance). "
                "To test your token manually, try: curl -H 'Authorization: Bearer YOUR_TOKEN' "
                f"{base_url}/api/v1/users/self"
            )
        except Unauthorized as e:
            logger.error(f"Connection failed: Unauthorized - {str(e)}")
            return False, (
                "Unauthorized - The API token exists but does not have permission to access Canvas. "
                "Please ensure the token was generated from your Canvas account settings and has not been revoked."
            )
        except Forbidden as e:
            logger.error(f"Connection failed: Forbidden - {str(e)}")
            return False, "Forbidden - API token does not have required permissions"
        except ResourceDoesNotExist as e:
            logger.error(f"Connection failed: Resource not found - {str(e)}")
            return False, "Canvas API endpoint not found. Please verify the base URL"
        except ConnectionError as e:
            logger.error(f"Connection failed: Connection error - {str(e)}")
            return False, "Could not connect to Canvas instance. Please verify the base URL"
        except CanvasException as e:
            logger.error(f"Connection failed: Canvas API error - {str(e)}")
            return False, f"Canvas API error: {str(e)}"
        except Exception as e:
            logger.exception(f"Connection failed: Unexpected error - {str(e)}")
            return False, f"Connection error: {str(e)}"

    def check_permissions(self) -> Tuple[bool, list[str]]:
        """
        Check if token has required Canvas permissions

        Uses canvasapi to test actual endpoints to verify permissions.
        Tests ability to read courses, students, and assignments.

        Returns:
            Tuple of (has_permissions: bool, missing_permissions: list[str])
        """
        base_url = self.credentials["base_url"]
        api_token = self.credentials["api_token"]
        missing_permissions = []

        logger.info("Checking Canvas API permissions")

        try:
            # Initialize Canvas client
            canvas = Canvas(base_url, api_token)

            # Test 1: Check if we can read courses
            logger.debug("Checking 'read_courses' permission")
            try:
                courses = list(canvas.get_courses())
                course_count = len(courses)
                logger.info(f"'read_courses' permission verified - found {course_count} course(s)")
                if not courses:
                    logger.warning("No courses found - cannot test student/assignment permissions")
            except (Unauthorized, Forbidden) as e:
                logger.error(f"'read_courses' permission denied: {str(e)}")
                missing_permissions.append("read_courses")
                # If we can't read courses, we can't test other permissions
                return False, missing_permissions

            # Test 2 & 3: Check if we can read students and assignments (requires a course)
            if courses:
                course = courses[0]
                logger.debug(f"Using course '{course.name}' (ID: {course.id}) for permission testing")

                # Test reading students
                logger.debug("Checking 'read_students' permission")
                try:
                    # Attempt to get students - just check if call succeeds
                    students = course.get_users(enrollment_type=['student'])
                    # Iterate once to trigger the API call
                    next(iter(students), None)
                    logger.info("'read_students' permission verified")
                except (Unauthorized, Forbidden) as e:
                    logger.error(f"'read_students' permission denied: {str(e)}")
                    missing_permissions.append("read_students")
                except StopIteration:
                    # No students but permission OK
                    logger.info("'read_students' permission verified (no students found)")

                # Test reading assignments
                logger.debug("Checking 'read_assignments' permission")
                try:
                    # Attempt to get assignments - just check if call succeeds
                    assignments = course.get_assignments()
                    # Iterate once to trigger the API call
                    next(iter(assignments), None)
                    logger.info("'read_assignments' permission verified")
                except (Unauthorized, Forbidden) as e:
                    logger.error(f"'read_assignments' permission denied: {str(e)}")
                    missing_permissions.append("read_assignments")
                except StopIteration:
                    # No assignments but permission OK
                    logger.info("'read_assignments' permission verified (no assignments found)")

            if missing_permissions:
                logger.warning(f"Permission check failed - missing: {', '.join(missing_permissions)}")
                return False, missing_permissions

            logger.info("All required permissions verified successfully")
            return True, []

        except CanvasException as e:
            logger.error(f"Permission check failed with Canvas exception: {str(e)}")
            return False, [f"Permission check failed: {str(e)}"]
        except Exception as e:
            logger.exception(f"Permission check failed with unexpected error: {str(e)}")
            return False, [f"Unexpected error during permission check: {str(e)}"]

    def _get_connection_metadata(self) -> Dict[str, Any]:
        """
        Get Canvas-specific metadata

        Fetches user information and Canvas instance details using canvasapi
        to store as metadata with the validated connection.

        Returns:
            Dictionary with Canvas-specific metadata
        """
        base_url = self.credentials["base_url"]
        api_token = self.credentials["api_token"]
        metadata = {
            "canvas_instance": base_url,
            "validated_at": datetime.now(timezone.utc).isoformat()
        }

        logger.info("Collecting Canvas connection metadata")

        try:
            # Initialize Canvas client
            canvas = Canvas(base_url, api_token)

            # Get current user info
            logger.debug("Fetching current user information")
            user = canvas.get_current_user()
            user_email = getattr(user, 'primary_email', None) or getattr(user, 'email', None)

            metadata.update({
                "canvas_user_id": user.id,
                "canvas_user_name": user.name,
                "canvas_user_email": user_email
            })
            logger.info(f"Collected user metadata: {user.name} (ID: {user.id})")

            # Get account info (Canvas version, etc.)
            # Note: This endpoint might not be available for all Canvas instances
            logger.debug("Attempting to fetch account information")
            try:
                accounts = list(canvas.get_accounts())
                if accounts:
                    account = accounts[0]
                    metadata["canvas_account_id"] = account.id
                    metadata["canvas_account_name"] = account.name
                    logger.info(f"Collected account metadata: {account.name} (ID: {account.id})")
                else:
                    logger.debug("No accounts found")
            except (Unauthorized, Forbidden, CanvasException) as e:
                # Account access might not be available, that's OK
                logger.debug(f"Could not fetch account info (not critical): {str(e)}")

            logger.info("Metadata collection completed successfully")

        except Exception as e:
            # If we can't get metadata, that's ok - connection is still valid
            logger.warning(f"Failed to collect full metadata (non-critical): {str(e)}")

        return metadata
