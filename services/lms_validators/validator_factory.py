"""
Factory for creating LMS validators
"""
from typing import Dict, Any
from .base import BaseLMSValidator
from .canvas_validator import CanvasValidator
from .exceptions import UnsupportedLMSError


class LMSValidatorFactory:
    """Factory to create appropriate LMS validator based on LMS type"""

    # Registry of available validators
    _validators = {
        "canvas": CanvasValidator,
        # Future LMS types can be added here:
        # "moodle": MoodleValidator,
        # "blackboard": BlackboardValidator,
        # "schoology": SchoologyValidator,
    }

    @classmethod
    def create(cls, lms_type: str, credentials: Dict[str, Any]) -> BaseLMSValidator:
        """
        Create validator instance for given LMS type

        Args:
            lms_type: The type of LMS (e.g., 'canvas', 'moodle')
            credentials: Dictionary containing LMS credentials

        Returns:
            Instance of appropriate validator class

        Raises:
            UnsupportedLMSError: If LMS type is not supported
        """
        validator_class = cls._validators.get(lms_type.lower())

        if not validator_class:
            supported = ", ".join(cls._validators.keys())
            raise UnsupportedLMSError(
                f"LMS type '{lms_type}' is not supported. "
                f"Supported types: {supported}"
            )

        return validator_class(credentials)

    @classmethod
    def register_validator(cls, lms_type: str, validator_class: type) -> None:
        """
        Register a new LMS validator (for extensibility)

        This allows external code to register new validator implementations
        without modifying this file.

        Args:
            lms_type: The LMS type identifier (e.g., 'moodle')
            validator_class: The validator class (must extend BaseLMSValidator)
        """
        if not issubclass(validator_class, BaseLMSValidator):
            raise ValueError(
                f"Validator class must extend BaseLMSValidator, "
                f"got {validator_class.__name__}"
            )

        cls._validators[lms_type.lower()] = validator_class

    @classmethod
    def supported_lms_types(cls) -> list[str]:
        """
        Get list of supported LMS types

        Returns:
            List of supported LMS type identifiers
        """
        return list(cls._validators.keys())

    @classmethod
    def is_supported(cls, lms_type: str) -> bool:
        """
        Check if an LMS type is supported

        Args:
            lms_type: The LMS type to check

        Returns:
            True if supported, False otherwise
        """
        return lms_type.lower() in cls._validators
