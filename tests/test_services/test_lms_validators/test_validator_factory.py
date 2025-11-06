"""
Tests for LMSValidatorFactory
"""
import pytest
from services.lms_validators import LMSValidatorFactory, CanvasValidator, UnsupportedLMSError


def test_create_canvas_validator():
    """Test creating a Canvas validator"""
    credentials = {
        "base_url": "https://test.instructure.com",
        "api_token": "test_token"
    }

    validator = LMSValidatorFactory.create("canvas", credentials)

    assert isinstance(validator, CanvasValidator)
    assert validator.credentials == credentials


def test_create_canvas_validator_case_insensitive():
    """Test that LMS type matching is case-insensitive"""
    credentials = {
        "base_url": "https://test.instructure.com",
        "api_token": "test_token"
    }

    validator = LMSValidatorFactory.create("CANVAS", credentials)

    assert isinstance(validator, CanvasValidator)


def test_create_unsupported_lms():
    """Test that creating an unsupported LMS type raises error"""
    credentials = {"some": "credentials"}

    with pytest.raises(UnsupportedLMSError) as exc_info:
        LMSValidatorFactory.create("moodle", credentials)

    assert "not supported" in str(exc_info.value).lower()
    assert "canvas" in str(exc_info.value).lower()


def test_supported_lms_types():
    """Test getting list of supported LMS types"""
    supported = LMSValidatorFactory.supported_lms_types()

    assert "canvas" in supported
    assert isinstance(supported, list)


def test_is_supported():
    """Test checking if LMS type is supported"""
    assert LMSValidatorFactory.is_supported("canvas") is True
    assert LMSValidatorFactory.is_supported("CANVAS") is True
    assert LMSValidatorFactory.is_supported("moodle") is False
