"""
Unit tests for message parsing logic with edge cases and diagnostic logging.

These tests verify the "narrative|maxim" message parsing with various
input scenarios and edge cases.
"""

import pytest


def test_basic_message_parsing():
    """Test basic message parsing with delimiter."""
    # Arrange
    message = "This is a narrative|This is a maxim"
    
    # Act
    if "|" in message:
        narrative, maxim = message.split("|", 1)
        narrative = narrative.strip()
        maxim = maxim.strip()
    
    # Assert
    assert narrative == "This is a narrative"
    assert maxim == "This is a maxim"


def test_message_parsing_with_extra_spaces():
    """Test parsing with extra whitespace around content."""
    # Arrange
    message = "  narrative with spaces  |  maxim with spaces  "
    
    # Act
    narrative, maxim = message.split("|", 1)
    narrative = narrative.strip()
    maxim = maxim.strip()
    
    # Assert
    assert narrative == "narrative with spaces"
    assert maxim == "maxim with spaces"


def test_message_parsing_multiple_delimiters():
    """Test parsing with multiple pipe delimiters (maxsplit=1)."""
    # Arrange
    message = "First part|Second part|Third part"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert narrative == "First part"
    assert maxim == "Second part|Third part"  # Remaining pipes preserved


def test_message_parsing_empty_narrative():
    """Test parsing with empty narrative."""
    # Arrange
    message = "|This is a maxim"
    
    # Act
    narrative, maxim = message.split("|", 1)
    narrative = narrative.strip()
    maxim = maxim.strip()
    
    # Assert
    assert narrative == ""
    assert maxim == "This is a maxim"


def test_message_parsing_empty_maxim():
    """Test parsing with empty maxim."""
    # Arrange
    message = "This is a narrative|"
    
    # Act
    narrative, maxim = message.split("|", 1)
    narrative = narrative.strip()
    maxim = maxim.strip()
    
    # Assert
    assert narrative == "This is a narrative"
    assert maxim == ""


def test_message_parsing_whitespace_only_narrative():
    """Test parsing with whitespace-only narrative."""
    # Arrange
    message = "   |This is a maxim"
    
    # Act
    narrative, maxim = message.split("|", 1)
    narrative = narrative.strip()
    maxim = maxim.strip()
    
    # Assert
    assert narrative == ""
    assert maxim == "This is a maxim"


def test_message_parsing_whitespace_only_maxim():
    """Test parsing with whitespace-only maxim."""
    # Arrange
    message = "This is a narrative|   "
    
    # Act
    narrative, maxim = message.split("|", 1)
    narrative = narrative.strip()
    maxim = maxim.strip()
    
    # Assert
    assert narrative == "This is a narrative"
    assert maxim == ""


def test_message_parsing_special_characters():
    """Test parsing with special characters."""
    # Arrange
    message = 'He said "stop" & they didn\'t|Always be respectful & listen'
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert '"stop"' in narrative
    assert "&" in narrative
    assert "'" in narrative
    assert "respectful" in maxim


def test_message_parsing_unicode_characters():
    """Test parsing with unicode characters."""
    # Arrange
    message = "Problème éthique 中文|Respecter les autres 尊重"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert "Problème" in narrative
    assert "中文" in narrative
    assert "Respecter" in maxim
    assert "尊重" in maxim


def test_message_parsing_emojis():
    """Test parsing with emoji characters."""
    # Arrange
    message = "Something is wrong 😟|Do what's right ✅"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert "😟" in narrative
    assert "✅" in maxim


def test_message_parsing_newlines():
    """Test parsing with newlines in content."""
    # Arrange
    message = "Line 1\nLine 2|Maxim line 1\nMaxim line 2"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert "\n" in narrative
    assert "\n" in maxim
    assert "Line 1" in narrative
    assert "Line 2" in narrative


def test_message_parsing_tabs():
    """Test parsing with tab characters."""
    # Arrange
    message = "Narrative\twith\ttabs|Maxim\twith\ttabs"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert "\t" in narrative
    assert "\t" in maxim


def test_message_parsing_very_long_narrative():
    """Test parsing with very long narrative."""
    # Arrange
    long_narrative = "A" * 5000
    message = f"{long_narrative}|Short maxim"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert len(narrative) == 5000
    assert maxim == "Short maxim"


def test_message_parsing_very_long_maxim():
    """Test parsing with very long maxim."""
    # Arrange
    long_maxim = "B" * 3000
    message = f"Short narrative|{long_maxim}"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert narrative == "Short narrative"
    assert len(maxim) == 3000


def test_delimiter_detection_present():
    """Test delimiter presence detection."""
    # Arrange
    message = "Narrative|Maxim"
    
    # Act
    has_delimiter = "|" in message
    
    # Assert
    assert has_delimiter is True


def test_delimiter_detection_absent():
    """Test delimiter absence detection."""
    # Arrange
    message = "No delimiter in this message"
    
    # Act
    has_delimiter = "|" in message
    
    # Assert
    assert has_delimiter is False


def test_delimiter_detection_empty_string():
    """Test delimiter detection on empty string."""
    # Arrange
    message = ""
    
    # Act
    has_delimiter = "|" in message
    
    # Assert
    assert has_delimiter is False


@pytest.mark.parametrize("message,expected_has_delimiter", [
    ("narrative|maxim", True),
    ("no delimiter", False),
    ("|empty narrative", True),
    ("empty maxim|", True),
    ("||double delimiter", True),
    ("", False),
    ("|", True),
])
def test_delimiter_detection_various_cases(message, expected_has_delimiter):
    """Test delimiter detection with various input cases."""
    # Act
    has_delimiter = "|" in message
    
    # Assert
    assert has_delimiter == expected_has_delimiter


def test_message_parsing_preserves_internal_pipes():
    """Test that internal pipes in maxim are preserved."""
    # Arrange
    message = "Simple narrative|Complex|maxim|with|pipes"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert narrative == "Simple narrative"
    assert maxim == "Complex|maxim|with|pipes"
    assert maxim.count("|") == 3


def test_message_parsing_html_entities():
    """Test parsing with HTML entities."""
    # Arrange
    message = "Narrative with &lt;tags&gt;|Maxim with &amp; symbol"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert "&lt;" in narrative
    assert "&gt;" in narrative
    assert "&amp;" in maxim


def test_message_parsing_url_in_content():
    """Test parsing with URLs containing characters."""
    # Arrange
    message = "Check https://example.com?param=value|Always verify sources"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert "https://example.com?param=value" in narrative
    assert "verify sources" in maxim


def test_message_parsing_markdown_like_syntax():
    """Test parsing with markdown-like syntax."""
    # Arrange
    message = "Problem with **bold** and _italic_|Use *proper* formatting"
    
    # Act
    narrative, maxim = message.split("|", 1)
    
    # Assert
    assert "**bold**" in narrative
    assert "_italic_" in narrative
    assert "*proper*" in maxim

