"""
Base validator for LMS connections
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ValidationResult:
    """Standardized validation result across all LMS types"""
    is_valid: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    missing_permissions: Optional[list[str]] = None


class BaseLMSValidator(ABC):
    """Abstract base class for LMS connection validators"""

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize validator with credentials

        Args:
            credentials: Dictionary containing LMS credentials
        """
        self.credentials = credentials
        self.validate_credentials_structure()

    @abstractmethod
    def validate_credentials_structure(self) -> None:
        """
        Validate the credential structure (raises if invalid)

        This method should check that all required credential fields
        are present and have valid formats.

        Raises:
            InvalidCredentialsError: If credentials are malformed or missing required fields
        """
        pass

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test basic connectivity to LMS API

        Returns:
            Tuple of (success: bool, message: str)
        """
        pass

    @abstractmethod
    def check_permissions(self) -> Tuple[bool, list[str]]:
        """
        Check if credentials have required permissions

        Returns:
            Tuple of (has_permissions: bool, missing_permissions: list[str])
        """
        pass

    def validate(self) -> ValidationResult:
        """
        Full validation orchestration (template method)

        This method orchestrates the validation flow:
        1. Credentials structure is already validated in __init__
        2. Test connection to LMS
        3. Check permissions
        4. Return detailed validation result

        Returns:
            ValidationResult with validation status and details
        """
        try:
            # Step 1: Test connection
            connected, conn_msg = self.test_connection()
            if not connected:
                return ValidationResult(
                    is_valid=False,
                    message=conn_msg,
                    details={}
                )

            # Step 2: Check permissions
            has_perms, missing = self.check_permissions()
            if not has_perms:
                return ValidationResult(
                    is_valid=False,
                    message=f"Missing required permissions: {', '.join(missing)}",
                    details={},
                    missing_permissions=missing
                )

            # Step 3: Get connection metadata
            metadata = self._get_connection_metadata()

            return ValidationResult(
                is_valid=True,
                message="Connection validated successfully",
                details=metadata
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Validation failed: {str(e)}",
                details={"error_type": type(e).__name__}
            )

    @abstractmethod
    def _get_connection_metadata(self) -> Dict[str, Any]:
        """
        Get LMS-specific metadata about the connection

        This method should return useful metadata about the validated connection,
        such as user info, LMS version, instance details, etc.

        Returns:
            Dictionary with LMS-specific metadata
        """
        pass
