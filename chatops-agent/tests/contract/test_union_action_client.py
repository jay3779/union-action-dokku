"""
Contract tests for Union Action API client.

These tests verify the contract between the WhatsApp ChatOps Agent and the
Union Action API, including successful submissions and error scenarios.
"""

import pytest
import requests
from unittest.mock import Mock, patch
from src.union_action_client import UnionActionClient


@pytest.fixture
def union_client():
    """Provide a Union Action client instance."""
    return UnionActionClient(base_url="http://test-api:8000")


def test_escalate_to_ethics_success(union_client, mock_requests_post):
    """Test successful ethics escalation."""
    # Arrange
    workflow_id = "1234567890"
    narrative = "I observed unethical behavior"
    maxim = "Always act with integrity"
    
    # Act
    result = union_client.escalate_to_ethics(
        workflow_id=workflow_id,
        narrative=narrative,
        maxim=maxim
    )
    
    # Assert
    assert result["workflow_id"] == "1234567890"
    assert result["status"] == "escalated"
    assert "escalated_at" in result
    
    # Verify the request was made correctly
    mock_requests_post.assert_called_once()
    call_args = mock_requests_post.call_args
    assert call_args[0][0] == "http://test-api:8000/escalate-to-ethics"
    
    # Verify payload structure
    payload = call_args[1]["json"]
    assert payload["workflow_id"] == workflow_id
    assert payload["source_data"]["narrative"] == narrative
    assert payload["source_data"]["maxim_extraction"] == maxim
    assert "pentadic_context" in payload["source_data"]


def test_escalate_to_ethics_pentadic_context(union_client, mock_requests_post):
    """Test that pentadic context is correctly structured."""
    # Act
    union_client.escalate_to_ethics(
        workflow_id="test123",
        narrative="Test narrative",
        maxim="Test maxim"
    )
    
    # Assert
    payload = mock_requests_post.call_args[1]["json"]
    pentadic = payload["source_data"]["pentadic_context"]
    
    assert pentadic["act"] == "Narrative submission"
    assert pentadic["scene"]["phenomenal"] == "WhatsApp chat"
    assert pentadic["scene"]["noumenal"] == "Ethical concern"
    assert pentadic["agent"]["role"] == "Participant"


def test_escalate_to_ethics_http_error(union_client, mock_requests_post_http_error):
    """Test handling of HTTP errors from Union Action API."""
    # Act & Assert
    with pytest.raises(requests.HTTPError):
        union_client.escalate_to_ethics(
            workflow_id="test",
            narrative="test",
            maxim="test"
        )


def test_escalate_to_ethics_connection_error(union_client, mock_requests_post_error):
    """Test handling of connection errors."""
    # Act & Assert
    with pytest.raises(requests.RequestException):
        union_client.escalate_to_ethics(
            workflow_id="test",
            narrative="test",
            maxim="test"
        )


def test_escalate_to_ethics_timeout(union_client, mock_requests_post_timeout):
    """Test handling of timeout errors."""
    # Act & Assert
    with pytest.raises(requests.Timeout):
        union_client.escalate_to_ethics(
            workflow_id="test",
            narrative="test",
            maxim="test"
        )


def test_escalate_to_ethics_logs_error(union_client, mock_requests_post_error, captured_logs):
    """Test that errors are logged with proper context."""
    # Act
    with pytest.raises(requests.RequestException):
        union_client.escalate_to_ethics(
            workflow_id="test123",
            narrative="test",
            maxim="test"
        )
    
    # Assert - verify error was logged
    assert "escalate_to_ethics_failed" in captured_logs.text


def test_escalate_to_ethics_empty_values(union_client, mock_requests_post):
    """Test escalation with empty but valid strings."""
    # Act
    result = union_client.escalate_to_ethics(
        workflow_id="test",
        narrative="",
        maxim=""
    )
    
    # Assert - should still make the request
    assert mock_requests_post.called
    payload = mock_requests_post.call_args[1]["json"]
    assert payload["source_data"]["narrative"] == ""
    assert payload["source_data"]["maxim_extraction"] == ""


def test_escalate_to_ethics_special_characters(union_client, mock_requests_post):
    """Test escalation with special characters in content."""
    # Arrange
    narrative = "User said \"this is wrong\" & it's problematic"
    maxim = "Always be honest & transparent"
    
    # Act
    union_client.escalate_to_ethics(
        workflow_id="test",
        narrative=narrative,
        maxim=maxim
    )
    
    # Assert
    payload = mock_requests_post.call_args[1]["json"]
    assert payload["source_data"]["narrative"] == narrative
    assert payload["source_data"]["maxim_extraction"] == maxim


def test_escalate_to_ethics_unicode_content(union_client, mock_requests_post):
    """Test escalation with unicode characters."""
    # Arrange
    narrative = "Observé un problème éthique 中文测试 🤔"
    maxim = "Toujours respecter les autres 尊重"
    
    # Act
    union_client.escalate_to_ethics(
        workflow_id="test",
        narrative=narrative,
        maxim=maxim
    )
    
    # Assert
    payload = mock_requests_post.call_args[1]["json"]
    assert payload["source_data"]["narrative"] == narrative
    assert payload["source_data"]["maxim_extraction"] == maxim


@pytest.mark.parametrize("status_code,should_raise", [
    (200, False),
    (201, False),
    (400, True),
    (401, True),
    (403, True),
    (404, True),
    (500, True),
    (502, True),
    (503, True),
])
def test_escalate_to_ethics_various_status_codes(union_client, monkeypatch, status_code, should_raise):
    """Test handling of various HTTP status codes."""
    # Arrange
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = {"status": "ok"}
    
    if should_raise:
        mock_response.raise_for_status.side_effect = requests.HTTPError(f"{status_code} Error")
    else:
        mock_response.raise_for_status.return_value = None
    
    mock_post = Mock(return_value=mock_response)
    monkeypatch.setattr("requests.post", mock_post)
    
    # Act & Assert
    if should_raise:
        with pytest.raises(requests.HTTPError):
            union_client.escalate_to_ethics("test", "test", "test")
    else:
        result = union_client.escalate_to_ethics("test", "test", "test")
        assert result == {"status": "ok"}

