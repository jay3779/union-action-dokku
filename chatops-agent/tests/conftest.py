"""
Pytest fixtures for WhatsApp ChatOps Agent tests.

This module provides shared fixtures for testing including:
- Mock Union Action client
- Test logger configuration
- Sample webhook payloads
- Test utilities
"""

import pytest
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
import structlog
from fastapi.testclient import TestClient


@pytest.fixture
def sample_webhook_payload() -> Dict[str, Any]:
    """
    Provide a sample valid webhook payload.
    
    Returns:
        Valid webhook payload dictionary
    """
    return {
        "from": "1234567890",
        "body": "I observed a colleague taking credit for someone else's work|Always give credit where credit is due",
        "timestamp": 1697212800,
        "chatId": "1234567890@c.us"
    }


@pytest.fixture
def sample_webhook_payload_no_delimiter() -> Dict[str, Any]:
    """
    Provide a sample webhook payload missing the delimiter.
    
    Returns:
        Invalid webhook payload (missing delimiter)
    """
    return {
        "from": "1234567890",
        "body": "This message is missing the delimiter",
        "timestamp": 1697212800
    }


@pytest.fixture
def sample_webhook_payload_empty_narrative() -> Dict[str, Any]:
    """
    Provide a sample webhook payload with empty narrative.
    
    Returns:
        Invalid webhook payload (empty narrative)
    """
    return {
        "from": "1234567890",
        "body": "|Some maxim here",
        "timestamp": 1697212800
    }


@pytest.fixture
def sample_webhook_payload_empty_maxim() -> Dict[str, Any]:
    """
    Provide a sample webhook payload with empty maxim.
    
    Returns:
        Invalid webhook payload (empty maxim)
    """
    return {
        "from": "1234567890",
        "body": "Some narrative here|",
        "timestamp": 1697212800
    }


@pytest.fixture
def sample_union_api_response() -> Dict[str, Any]:
    """
    Provide a sample successful Union Action API response.
    
    Returns:
        Union API response dictionary
    """
    return {
        "workflow_id": "1234567890",
        "status": "escalated",
        "escalated_at": "2025-10-13T14:32:00Z",
        "message": "Ethics case successfully escalated for review"
    }


@pytest.fixture
def mock_union_action_client():
    """
    Provide a mock Union Action client.
    
    Returns:
        Mock UnionActionClient instance
    """
    mock_client = Mock()
    mock_client.escalate_to_ethics = Mock(return_value={
        "workflow_id": "1234567890",
        "status": "escalated",
        "escalated_at": "2025-10-13T14:32:00Z"
    })
    return mock_client


@pytest.fixture
def mock_union_action_client_with_error():
    """
    Provide a mock Union Action client that raises errors.
    
    Returns:
        Mock UnionActionClient that raises RequestException
    """
    import requests
    
    mock_client = Mock()
    mock_client.escalate_to_ethics = Mock(
        side_effect=requests.RequestException("Connection refused")
    )
    return mock_client


@pytest.fixture
def test_logger():
    """
    Provide a test logger with simplified configuration.
    
    Returns:
        Structlog logger for testing
    """
    import logging
    import sys
    
    # Reset structlog configuration for testing
    structlog.reset_defaults()
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG,
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.KeyValueRenderer(key_order=["timestamp", "level", "event"])
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    return structlog.get_logger("test")


@pytest.fixture
def app_client():
    """
    Provide a FastAPI test client.
    
    Returns:
        TestClient for the FastAPI app
    """
    from src.main import app
    return TestClient(app)


@pytest.fixture
def correlation_id():
    """
    Provide a test correlation ID.
    
    Returns:
        Test correlation ID string
    """
    return "test-correlation-id-12345"


@pytest.fixture(autouse=True)
def reset_correlation_id():
    """
    Automatically reset correlation ID before each test.
    """
    from src.logging_config import clear_correlation_id
    clear_correlation_id()
    yield
    clear_correlation_id()


@pytest.fixture
def mock_requests_post(monkeypatch):
    """
    Provide a mock for requests.post.
    
    Returns:
        Mock response object
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "workflow_id": "1234567890",
        "status": "escalated",
        "escalated_at": "2025-10-13T14:32:00Z"
    }
    
    mock_post = Mock(return_value=mock_response)
    monkeypatch.setattr("requests.post", mock_post)
    
    return mock_post


@pytest.fixture
def mock_requests_post_error(monkeypatch):
    """
    Provide a mock for requests.post that raises an error.
    
    Returns:
        Mock that raises RequestException
    """
    import requests
    
    mock_post = Mock(side_effect=requests.RequestException("Connection error"))
    monkeypatch.setattr("requests.post", mock_post)
    
    return mock_post


@pytest.fixture
def mock_requests_post_timeout(monkeypatch):
    """
    Provide a mock for requests.post that raises a timeout.
    
    Returns:
        Mock that raises Timeout
    """
    import requests
    
    mock_post = Mock(side_effect=requests.Timeout("Request timeout"))
    monkeypatch.setattr("requests.post", mock_post)
    
    return mock_post


@pytest.fixture
def mock_requests_post_http_error(monkeypatch):
    """
    Provide a mock for requests.post that returns HTTP error.
    
    Returns:
        Mock response with error status
    """
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    
    mock_post = Mock(return_value=mock_response)
    monkeypatch.setattr("requests.post", mock_post)
    
    return mock_post


@pytest.fixture
def captured_logs(caplog):
    """
    Provide captured log output for assertions.
    
    Args:
        caplog: Pytest's caplog fixture
        
    Returns:
        caplog fixture with DEBUG level set
    """
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


# Helper functions for tests

def assert_error_response(response_data: Dict[str, Any], expected_detail: str) -> None:
    """
    Assert that a response is an error with expected detail.
    
    Args:
        response_data: Response dictionary
        expected_detail: Expected error detail message
    """
    assert response_data["status"] == "error"
    assert expected_detail in response_data["detail"]
    assert "timestamp" in response_data


def assert_success_response(response_data: Dict[str, Any]) -> None:
    """
    Assert that a response is a success.
    
    Args:
        response_data: Response dictionary
    """
    assert response_data["status"] == "received"
    assert "workflow_result" in response_data
    assert "timestamp" in response_data


def assert_correlation_id_present(response_data: Dict[str, Any]) -> None:
    """
    Assert that a response contains a correlation ID.
    
    Args:
        response_data: Response dictionary
    """
    assert "correlation_id" in response_data
    assert response_data["correlation_id"] is not None

