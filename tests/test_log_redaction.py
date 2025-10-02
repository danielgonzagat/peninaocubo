import json

from penin.logging import SecretRedactor, SecureLogger, redact_secrets


def test_secret_redaction_dict():
    """Test redaction of secrets in dictionaries."""
    test_data = {
        "user_id": "12345",
        "api_key": "sk-1234567890abcdef",
        "password": "secretpassword",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "normal_field": "normal_value",
        "nested": {"secret_key": "another_secret", "public_data": "visible"},
    }

    redacted = SecretRedactor.redact(test_data)

    # Check that secrets are redacted
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["token"] == "[REDACTED]"
    assert redacted["nested"]["secret_key"] == "[REDACTED]"

    # Check that non-secrets are preserved
    assert redacted["user_id"] == "12345"
    assert redacted["normal_field"] == "normal_value"
    assert redacted["nested"]["public_data"] == "visible"


def test_secret_redaction_list():
    """Test redaction of secrets in lists."""
    test_data = [{"api_key": "secret1", "name": "test1"}, {"password": "secret2", "id": "test2"}, {"normal": "value"}]

    redacted = SecretRedactor.redact(test_data)

    assert redacted[0]["api_key"] == "[REDACTED]"
    assert redacted[0]["name"] == "test1"
    assert redacted[1]["password"] == "[REDACTED]"
    assert redacted[1]["id"] == "test2"
    assert redacted[2]["normal"] == "value"


def test_secret_patterns():
    """Test various secret field patterns."""
    test_cases = [
        "api_key",
        "API_KEY",
        "password",
        "PASSWORD",
        "access_token",
        "ACCESS_TOKEN",
        "secret_key",
        "SECRET_KEY",
        "bearer_token",
        "BEARER_TOKEN",
        "client_secret",
        "CLIENT_SECRET",
        "private_key",
        "PRIVATE_KEY",
        "session_id",
        "SESSION_ID",
        "oauth_token",
        "OAUTH_TOKEN",
        "jwt_token",
        "JWT_TOKEN",
    ]

    for field_name in test_cases:
        test_data = {field_name: "secret_value"}
        redacted = SecretRedactor.redact(test_data)
        assert redacted[field_name] == "[REDACTED]", f"Failed to redact {field_name}"


def test_non_secret_fields():
    """Test that non-secret fields are not redacted."""
    test_cases = [
        "user_id",
        "username",
        "email",
        "name",
        "description",
        "title",
        "content",
        "message",
        "data",
        "value",
        "count",
        "status",
        "type",
        "category",
        "id",
    ]

    for field_name in test_cases:
        test_data = {field_name: "some_value"}
        redacted = SecretRedactor.redact(test_data)
        assert redacted[field_name] == "some_value", f"Incorrectly redacted {field_name}"


def test_redact_decorator():
    """Test the redact_secrets decorator."""

    @redact_secrets
    def test_function(api_key, password, normal_param):
        return {"api_key": api_key, "password": password, "normal_param": normal_param, "result": "success"}

    result = test_function(api_key="sk-1234567890abcdef", password="secretpassword", normal_param="normal_value")

    # The function should receive redacted values
    assert result["api_key"] == "[REDACTED]"
    assert result["password"] == "[REDACTED]"
    assert result["normal_param"] == "normal_value"
    assert result["result"] == "success"


def test_secure_logger():
    """Test SecureLogger functionality."""
    import logging

    # Create a test logger
    logger = logging.getLogger("test_secure_logger")
    logger.setLevel(logging.INFO)

    # Capture log output
    import io

    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    logger.addHandler(handler)

    # Create secure logger
    secure_logger = SecureLogger(logger)

    # Test logging with secrets
    test_data = {"api_key": "sk-1234567890abcdef", "password": "secretpassword", "user_id": "12345"}

    secure_logger.info(test_data)

    # Check that secrets are redacted in log output
    log_output = log_capture.getvalue()
    assert "[REDACTED]" in log_output
    assert "sk-1234567890abcdef" not in log_output
    assert "secretpassword" not in log_output
    assert "12345" in log_output  # Non-secret should remain


def test_json_string_redaction():
    """Test redaction of JSON strings."""
    test_json = json.dumps({"api_key": "sk-1234567890abcdef", "password": "secretpassword", "user_id": "12345"})

    redacted = SecretRedactor.redact(test_json)

    # Should be a JSON string with redacted values
    parsed = json.loads(redacted)
    assert parsed["api_key"] == "[REDACTED]"
    assert parsed["password"] == "[REDACTED]"
    assert parsed["user_id"] == "12345"


def test_nested_redaction():
    """Test redaction in deeply nested structures."""
    test_data = {"level1": {"level2": {"level3": {"api_key": "secret", "normal_field": "value"}}}}

    redacted = SecretRedactor.redact(test_data)

    assert redacted["level1"]["level2"]["level3"]["api_key"] == "[REDACTED]"
    assert redacted["level1"]["level2"]["level3"]["normal_field"] == "value"


def test_edge_cases():
    """Test edge cases for redaction."""
    # Empty dict
    assert SecretRedactor.redact({}) == {}

    # None value
    assert SecretRedactor.redact(None) is None

    # String that's not JSON
    assert SecretRedactor.redact("plain string") == "plain string"

    # List with mixed types
    mixed_list = [{"api_key": "secret"}, "plain string", {"normal": "value"}]
    redacted = SecretRedactor.redact(mixed_list)
    assert redacted[0]["api_key"] == "[REDACTED]"
    assert redacted[1] == "plain string"
    assert redacted[2]["normal"] == "value"
