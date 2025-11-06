"""
Security utilities for handling sensitive data

This module provides utilities for safely handling and logging sensitive
credentials such as API tokens, passwords, and other secrets.
"""


def mask_credential(credential: str, visible_chars: int = 4) -> str:
    """
    Mask a credential for safe logging

    Shows only the first and last N characters of a credential,
    replacing the middle with ellipsis. This allows debugging while
    preventing credential exposure in logs.

    Args:
        credential: The sensitive credential to mask
        visible_chars: Number of characters to show at start and end (default: 4)

    Returns:
        Masked credential string (e.g., "sk_t...Mvra")

    Examples:
        >>> mask_credential("sk_test_1234567890abcdef")
        'sk_t...cdef'

        >>> mask_credential("short", visible_chars=2)
        'sh...rt'

        >>> mask_credential("abc")  # Too short
        '***'

        >>> mask_credential("")
        '***'

    Security Notes:
        - NEVER log credentials in plaintext
        - Use this function for debugging connection issues
        - Even masked credentials should only be logged at DEBUG level
        - Consider removing debug logs before production deployment
    """
    if not credential or len(credential) <= visible_chars:
        return "***"

    if len(credential) <= (visible_chars * 2):
        # For very short credentials, just show partial masking
        return f"{credential[:visible_chars]}***"

    return f"{credential[:visible_chars]}...{credential[-visible_chars:]}"


def mask_url_with_credentials(url: str) -> str:
    """
    Mask credentials embedded in URLs

    Some APIs use URL-based authentication (e.g., https://token@api.example.com).
    This function masks the credential portion while preserving the domain.

    Args:
        url: URL that may contain embedded credentials

    Returns:
        URL with credentials masked

    Examples:
        >>> mask_url_with_credentials("https://user:pass@api.example.com/endpoint")
        'https://***:***@api.example.com/endpoint'

        >>> mask_url_with_credentials("https://api.example.com/endpoint")
        'https://api.example.com/endpoint'
    """
    # Check if URL contains credentials (username:password@domain format)
    if "@" in url and "://" in url:
        parts = url.split("://", 1)
        if len(parts) == 2:
            protocol, rest = parts
            if "@" in rest:
                credentials, domain = rest.split("@", 1)
                # Mask the credentials portion
                if ":" in credentials:
                    return f"{protocol}://***:***@{domain}"
                return f"{protocol}://***@{domain}"

    # No credentials in URL, return as-is
    return url


def sanitize_log_data(data: dict) -> dict:
    """
    Sanitize a dictionary by masking sensitive fields

    Automatically detects and masks common sensitive field names like
    'password', 'token', 'api_key', 'secret', etc.

    Args:
        data: Dictionary potentially containing sensitive data

    Returns:
        New dictionary with sensitive fields masked

    Example:
        >>> sanitize_log_data({"user": "john", "api_token": "secret123"})
        {'user': 'john', 'api_token': '***MASKED***'}

    Note:
        This creates a shallow copy. Nested dictionaries are not recursively sanitized.
    """
    # Common sensitive field names (case-insensitive)
    sensitive_fields = {
        'password', 'passwd', 'pwd',
        'token', 'api_token', 'access_token', 'refresh_token', 'bearer_token',
        'api_key', 'apikey', 'key',
        'secret', 'client_secret',
        'credential', 'credentials',
        'authorization', 'auth',
    }

    # Create a copy to avoid modifying original
    sanitized = data.copy()

    for key in sanitized:
        if key.lower() in sensitive_fields:
            sanitized[key] = "***MASKED***"

    return sanitized
