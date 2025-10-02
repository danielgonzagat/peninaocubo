"""
Logging utilities with secret redaction for PENIN-Ω system.
"""

import json
import re
from functools import wraps
from typing import Any


class SecretRedactor:
    """Redacts secrets and sensitive information from log data."""

    # Patterns for common secret fields
    SECRET_PATTERNS = [
        r"password",
        r"passwd",
        r"pwd",
        r"token",
        r"key",
        r"secret",
        r"auth",
        r"credential",
        r"api_key",
        r"access_token",
        r"refresh_token",
        r"bearer",
        r"authorization",
        r"private_key",
        r"privatekey",
        r"secret_key",
        r"secretkey",
        r"session_id",
        r"sessionid",
        r"cookie",
        r"jwt",
        r"oauth",
        r"client_secret",
        r"clientsecret",
    ]

    # Compiled regex patterns
    _compiled_patterns = None

    @classmethod
    def _get_compiled_patterns(cls):
        """Get compiled regex patterns for secret detection."""
        if cls._compiled_patterns is None:
            cls._compiled_patterns = [
                re.compile(pattern, re.IGNORECASE) for pattern in cls.SECRET_PATTERNS
            ]
        return cls._compiled_patterns

    @classmethod
    def redact_value(cls, value: Any) -> str:
        """Redact a value if it looks like a secret."""
        if not isinstance(value, str):
            return str(value)

        # Check if the field name suggests it's a secret
        if len(value) > 4:  # Only redact if it's not obviously a placeholder
            return "[REDACTED]"

        return value

    @classmethod
    def redact_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact secrets from a dictionary."""
        if not isinstance(data, dict):
            return data

        redacted = {}
        patterns = cls._get_compiled_patterns()

        for key, value in data.items():
            # Check if key matches any secret pattern
            is_secret = any(pattern.search(key) for pattern in patterns)

            if is_secret:
                redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = cls.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = cls.redact_list(value)
            else:
                redacted[key] = value

        return redacted

    @classmethod
    def redact_list(cls, data: list) -> list:
        """Recursively redact secrets from a list."""
        if not isinstance(data, list):
            return data

        redacted = []
        for item in data:
            if isinstance(item, dict):
                redacted.append(cls.redact_dict(item))
            elif isinstance(item, list):
                redacted.append(cls.redact_list(item))
            else:
                redacted.append(item)

        return redacted

    @classmethod
    def redact(cls, data: Any) -> Any:
        """Redact secrets from any data structure."""
        if isinstance(data, dict):
            return cls.redact_dict(data)
        elif isinstance(data, list):
            return cls.redact_list(data)
        else:
            # Attempt JSON string redaction for string inputs
            if isinstance(data, str):
                try:
                    parsed = json.loads(data)
                    redacted = cls.redact(parsed)
                    return json.dumps(redacted)
                except (json.JSONDecodeError, TypeError):
                    return data
            return data


def redact_secrets(func):
    """Decorator to redact secrets from function arguments and return values."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Redact kwargs
        redacted_kwargs = SecretRedactor.redact(kwargs)

        # Call original function
        result = func(*args, **redacted_kwargs)

        # Redact result if it's a dict
        if isinstance(result, dict):
            result = SecretRedactor.redact(result)

        return result

    return wrapper


class SecureLogger:
    """Logger that automatically redacts secrets."""

    def __init__(self, logger):
        self.logger = logger

    def _redact_message(self, message: str | dict[str, Any]) -> str | dict[str, Any]:
        """Redact secrets from log message."""
        if isinstance(message, dict):
            return SecretRedactor.redact(message)
        elif isinstance(message, str):
            # Try to parse as JSON and redact
            try:
                data = json.loads(message)
                redacted = SecretRedactor.redact(data)
                return json.dumps(redacted, separators=(",", ":"))
            except (json.JSONDecodeError, TypeError):
                return message
        else:
            return message

    def info(self, message: str | dict[str, Any], *args, **kwargs):
        """Log info message with secret redaction."""
        redacted_message = self._redact_message(message)
        self.logger.info(redacted_message, *args, **kwargs)

    def warning(self, message: str | dict[str, Any], *args, **kwargs):
        """Log warning message with secret redaction."""
        redacted_message = self._redact_message(message)
        self.logger.warning(redacted_message, *args, **kwargs)

    def error(self, message: str | dict[str, Any], *args, **kwargs):
        """Log error message with secret redaction."""
        redacted_message = self._redact_message(message)
        self.logger.error(redacted_message, *args, **kwargs)

    def debug(self, message: str | dict[str, Any], *args, **kwargs):
        """Log debug message with secret redaction."""
        redacted_message = self._redact_message(message)
        self.logger.debug(redacted_message, *args, **kwargs)


def create_secure_logger(name: str) -> SecureLogger:
    """Create a secure logger instance."""
    import logging

    logger = logging.getLogger(name)
    return SecureLogger(logger)


# Example usage and testing
if __name__ == "__main__":
    # Test secret redaction
    test_data = {
        "user_id": "12345",
        "api_key": "sk-1234567890abcdef",
        "password": "secretpassword",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "normal_field": "normal_value",
        "nested": {"secret_key": "another_secret", "public_data": "visible"},
    }

    redacted = SecretRedactor.redact(test_data)
    print("Original:", json.dumps(test_data, indent=2))
    print("Redacted:", json.dumps(redacted, indent=2))
