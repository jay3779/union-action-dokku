"""
Integration test for webhook with local xsrc pipeline.

Tests full WhatsApp webhook → ethical analysis → KOERS survey flow.

Note: This test is simplified for MVP. Full webhook integration tests
should be added when WhatsApp agent main.py is updated to use the
refactored UnionActionClient with local xsrc.
"""

import pytest
import sys
from pathlib import Path

# Add project source to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from union_action_client import UnionActionClient


class TestWebhookWithLocalPipeline:
    """Test webhook integration with local pipeline (T119 - simplified)."""
    
    def test_webhook_simulation_full_pipeline(self):
        """
        Simulate webhook flow: message → ethical analysis → survey URL.
        
        This test simulates what the webhook handler should do:
        1. Extract message from webhook payload
        2. Call escalate_to_ethics
        3. Call generate_koers_survey
        4. Return survey URL to WhatsApp user
        """
        client = UnionActionClient()
        
        # Simulate webhook payload
        webhook_payload = {
            "messages": [{
                "from": "1234567890",
                "body": "I was denied training despite requesting it multiple times."
            }]
        }
        
        # Extract message (this is what webhook handler does)
        phone_number = webhook_payload["messages"][0]["from"]
        complaint_text = webhook_payload["messages"][0]["body"]
        workflow_id = f"whatsapp_{phone_number}"
        
        # Step 1: Escalate to ethics
        ethical_report = client.escalate_to_ethics(
            workflow_id=workflow_id,
            complaint_text=complaint_text
        )
        
        assert ethical_report is not None
        assert "summary" in ethical_report
        
        # Step 2: Generate KOERS survey
        survey = client.generate_koers_survey(
            workflow_id=workflow_id,
            ethical_report=ethical_report
        )
        
        assert survey is not None
        assert "survey_url" in survey
        
        # Step 3: Prepare response (this is what webhook would return)
        response_message = (
            f"Your complaint has been analyzed. "
            f"Ethical assessment: {ethical_report['summary'][:100]}... "
            f"Please complete this survey: {survey['survey_url']}"
        )
        
        assert "survey" in response_message.lower()
        assert "http" in response_message.lower()
    
    def test_webhook_handles_short_message(self):
        """Test that webhook properly handles invalid short messages."""
        client = UnionActionClient()
        
        webhook_payload = {
            "messages": [{
                "from": "1234567890",
                "body": "Short"  # Too short for valid complaint
            }]
        }
        
        phone_number = webhook_payload["messages"][0]["from"]
        complaint_text = webhook_payload["messages"][0]["body"]
        workflow_id = f"whatsapp_{phone_number}"
        
        # Should raise validation error
        with pytest.raises(ValueError):
            client.escalate_to_ethics(
                workflow_id=workflow_id,
                complaint_text=complaint_text
            )
    
    def test_webhook_handles_multiple_violations(self):
        """Test webhook with complaint that triggers multiple violations."""
        client = UnionActionClient()
        
        webhook_payload = {
            "messages": [{
                "from": "1234567890",
                "body": (
                    "I was denied training when it was convenient for management. "
                    "They said budget pressures meant training was optional. "
                    "I felt treated as disposable rather than valued."
                )
            }]
        }
        
        phone_number = webhook_payload["messages"][0]["from"]
        complaint_text = webhook_payload["messages"][0]["body"]
        workflow_id = f"whatsapp_{phone_number}"
        
        # Step 1: Ethical analysis
        ethical_report = client.escalate_to_ethics(
            workflow_id=workflow_id,
            complaint_text=complaint_text
        )
        
        # This complaint has keywords that should trigger violations:
        # - "convenient" → Universalizability FAILURE
        # - "denied training" → Humanity Formula VIOLATION
        # - "budget pressures" → Autonomy VIOLATION
        
        # Step 2: Generate survey
        survey = client.generate_koers_survey(
            workflow_id=workflow_id,
            ethical_report=ethical_report
        )
        
        # Survey should include multiple modules (not just core)
        assert len(survey["module_list"]) > 1
        assert survey["item_count"] > 7  # More than just core


@pytest.mark.skip(reason="Requires main.py webhook handler update - TODO for production")
class TestWebhookEndpoint:
    """
    Full webhook endpoint tests (requires main.py update).
    
    TODO: Uncomment and implement when main.py is updated to use
    refactored UnionActionClient with local xsrc integration.
    """
    
    def test_webhook_endpoint_post(self):
        """Test POST /webhook with local pipeline (requires main.py update)."""
        # TODO: Implement when webhook handler is updated
        # from fastapi.testclient import TestClient
        # from main import app
        # 
        # client = TestClient(app)
        # response = client.post("/webhook", json={
        #     "messages": [{
        #         "from": "123",
        #         "body": "Test complaint"
        #     }]
        # })
        # assert response.status_code == 200
        pass

