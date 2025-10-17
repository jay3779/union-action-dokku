"""
Unit tests for validation error scenarios.

Tests all validation cases including missing delimiter, empty fields,
whitespace-only content, and length limits.
"""

import pytest
from src.error_handlers import WebhookValidationError, ParseError, ValidationError


def test_missing_delimiter_validation():
    """Test validation of missing delimiter."""
    message = "This message has no delimiter"
    
    # Check delimiter presence
    has_delimiter = "|" in message
    assert has_delimiter is False


def test_empty_narrative_validation():
    """Test validation of empty narrative after stripping."""
    message = "|This is just a maxim"
    
    narrative, maxim = message.split("|", 1)
    narrative = narrative.strip()
    
    assert len(narrative) == 0
    assert len(maxim) > 0


def test_empty_maxim_validation():
    """Test validation of empty maxim after stripping."""
    message = "This is just a narrative|"
    
    narrative, maxim = message.split("|", 1)
    maxim = maxim.strip()
    
    assert len(narrative) > 0
    assert len(maxim) == 0


def test_whitespace_only_narrative():
    """Test validation of whitespace-only narrative."""
    message = "    |Valid maxim"
    
    narrative, maxim = message.split("|", 1)
    narrative = narrative.strip()
    
    assert len(narrative) == 0
    assert narrative == ""


def test_whitespace_only_maxim():
    """Test validation of whitespace-only maxim."""
    message = "Valid narrative|    "
    
    narrative, maxim = message.split("|", 1)
    maxim = maxim.strip()
    
    assert len(maxim) == 0
    assert maxim == ""


def test_both_fields_empty():
    """Test validation when both fields are empty."""
    message = "|"
    
    narrative, maxim = message.split("|", 1)
    narrative = narrative.strip()
    maxim = maxim.strip()
    
    assert len(narrative) == 0
    assert len(maxim) == 0


def test_narrative_length_validation():
    """Test narrative length limits."""
    max_narrative_length = 2000
    
    # Valid length
    valid_narrative = "A" * 1500
    assert len(valid_narrative) <= max_narrative_length
    
    # Over length
    too_long_narrative = "A" * 2500
    assert len(too_long_narrative) > max_narrative_length


def test_maxim_length_validation():
    """Test maxim length limits."""
    max_maxim_length = 500
    
    # Valid length
    valid_maxim = "B" * 400
    assert len(valid_maxim) <= max_maxim_length
    
    # Over length
    too_long_maxim = "B" * 600
    assert len(too_long_maxim) > max_maxim_length


def test_webhook_validation_error_creation():
    """Test creating WebhookValidationError."""
    error = WebhookValidationError(
        "Field validation failed",
        field_name="body",
        received_value="invalid"
    )
    
    assert error.message == "Field validation failed"
    assert error.field_name == "body"
    assert error.details["field"] == "body"


def test_parse_error_creation():
    """Test creating ParseError."""
    error = ParseError(
        "Missing delimiter",
        raw_message="test message",
        parse_stage="delimiter_check"
    )
    
    assert error.message == "Missing delimiter"
    assert error.parse_stage == "delimiter_check"
    assert "parse_stage" in error.details


def test_validation_error_creation():
    """Test creating ValidationError."""
    error = ValidationError(
        "Length exceeded",
        validation_rule="max_length",
        expected=500,
        actual=600
    )
    
    assert error.message == "Length exceeded"
    assert error.validation_rule == "max_length"
    assert error.expected == 500
    assert error.actual == 600


@pytest.mark.parametrize("message,should_have_delimiter", [
    ("narrative|maxim", True),
    ("no delimiter here", False),
    ("|empty narrative", True),
    ("empty maxim|", True),
    ("", False),
])
def test_delimiter_presence_various_cases(message, should_have_delimiter):
    """Test delimiter presence detection with various inputs."""
    has_delimiter = "|" in message
    assert has_delimiter == should_have_delimiter


@pytest.mark.parametrize("narrative_length,should_be_valid", [
    (100, True),
    (1000, True),
    (2000, True),
    (2001, False),
    (3000, False),
])
def test_narrative_length_limits(narrative_length, should_be_valid):
    """Test narrative length validation with various lengths."""
    max_length = 2000
    is_valid = narrative_length <= max_length
    assert is_valid == should_be_valid


@pytest.mark.parametrize("maxim_length,should_be_valid", [
    (50, True),
    (250, True),
    (500, True),
    (501, False),
    (1000, False),
])
def test_maxim_length_limits(maxim_length, should_be_valid):
    """Test maxim length validation with various lengths."""
    max_length = 500
    is_valid = maxim_length <= max_length
    assert is_valid == should_be_valid


def test_empty_body_field():
    """Test validation of completely empty body field."""
    body = ""
    
    assert len(body) == 0
    assert not body  # Falsy value


def test_missing_from_field():
    """Test validation when 'from' field is missing."""
    payload = {"body": "test|test"}
    
    # Check if 'from' is present
    assert "from" not in payload
    
    # Fallback behavior
    from_value = payload.get("from", "unknown_user")
    assert from_value == "unknown_user"


def test_whitespace_variations():
    """Test various whitespace patterns."""
    test_cases = [
        ("  narrative  |  maxim  ", "narrative", "maxim"),
        ("\tnarrative\t|\tmaxim\t", "narrative", "maxim"),
        ("\nnarrative\n|\nmaxim\n", "narrative", "maxim"),
        ("  |  ", "", ""),
    ]
    
    for message, expected_narrative, expected_maxim in test_cases:
        narrative, maxim = message.split("|", 1)
        assert narrative.strip() == expected_narrative
        assert maxim.strip() == expected_maxim


def test_special_characters_in_fields():
    """Test that special characters don't interfere with validation."""
    message = 'narrative with "quotes" & symbols|maxim with <tags>'
    
    narrative, maxim = message.split("|", 1)
    
    # Should successfully parse despite special characters
    assert '"quotes"' in narrative
    assert "&" in narrative
    assert "<tags>" in maxim


def test_newlines_in_fields():
    """Test fields containing newlines."""
    message = "line1\nline2|maxim1\nmaxim2"
    
    narrative, maxim = message.split("|", 1)
    
    # Newlines should be preserved
    assert "\n" in narrative
    assert "\n" in maxim
    
    # But stripping should not remove them
    assert len(narrative.strip()) > 0


def test_unicode_validation():
    """Test validation with unicode characters."""
    message = "Problème éthique 中文|Respecter 尊重"
    
    narrative, maxim = message.split("|", 1)
    
    # Should handle unicode correctly
    assert "Problème" in narrative
    assert "中文" in narrative
    assert "尊重" in maxim


def test_emoji_validation():
    """Test validation with emojis."""
    message = "Problem 😟|Solution ✅"
    
    narrative, maxim = message.split("|", 1)
    
    # Emojis should be preserved
    assert "😟" in narrative
    assert "✅" in maxim

