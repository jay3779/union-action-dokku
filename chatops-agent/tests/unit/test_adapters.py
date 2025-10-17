"""
Unit tests for xsrc transformation adapters.

Tests ComplaintToKantianAdapter transformation logic.
"""

import pytest
import sys
from pathlib import Path

# Import xsrc modules
xsrc_path = Path(__file__).parent.parent.parent.parent / "xunion-action-integration"
if xsrc_path.exists():
    sys.path.insert(0, str(xsrc_path))

from xsrc.adapters.complaint_to_kantian import ComplaintToKantianAdapter


class TestComplaintToKantianAdapter:
    """Test ComplaintToKantianAdapter transformation."""
    
    def test_valid_transformation(self):
        """Test successful transformation of complaint to Kantian input."""
        adapter = ComplaintToKantianAdapter()
        
        complaint = {
            "narrative": "I was denied training despite requesting it",
            "pentadic_context": {
                "act": "Training denial",
                "scene": {
                    "phenomenal": "Budget pressures",
                    "noumenal": "Professional development duty"
                },
                "agent": {
                    "role": "Clinical Support Assistant"
                },
                "agency": "Management directive",
                "purpose": "Cost reduction"
            },
            "maxim_extraction": "Training is optional when convenient",
            "rhetorical_context": {
                "experience": "Felt undervalued"
            }
        }
        
        result = adapter.transform(complaint)
        
        assert result["action"]["description"] == "I was denied training despite requesting it"
        assert result["maxim"] == "Training is optional when convenient"
        assert result["agent"]["role"] == "Clinical Support Assistant"
        assert result["scene"]["phenomenal_constraints"] == "Budget pressures"
        assert result["scene"]["noumenal_duties"] == "Professional development duty"
        assert result["employee_experience"] == "Felt undervalued"
    
    def test_missing_narrative_fails(self):
        """Missing narrative should raise ValueError."""
        adapter = ComplaintToKantianAdapter()
        
        complaint = {
            "pentadic_context": {
                "act": "Test",
                "scene": {},
                "agent": {"role": "Test"}
            },
            "maxim_extraction": "Test"
        }
        
        with pytest.raises(ValueError, match="narrative"):
            adapter.transform(complaint)
    
    def test_missing_maxim_fails(self):
        """Missing maxim_extraction should raise ValueError."""
        adapter = ComplaintToKantianAdapter()
        
        complaint = {
            "narrative": "Test narrative",
            "pentadic_context": {
                "act": "Test",
                "scene": {},
                "agent": {"role": "Test"}
            },
            "rhetorical_context": {"experience": "Test"}
        }
        
        with pytest.raises(ValueError, match="maxim"):
            adapter.transform(complaint)
    
    def test_missing_pentadic_scene_fails(self):
        """Missing scene in pentadic_context should raise ValueError."""
        adapter = ComplaintToKantianAdapter()
        
        complaint = {
            "narrative": "Test narrative",
            "pentadic_context": {
                "act": "Test",
                "agent": {"role": "Test"}
            },
            "maxim_extraction": "Test",
            "rhetorical_context": {"experience": "Test"}
        }
        
        with pytest.raises(ValueError, match="scene"):
            adapter.transform(complaint)
    
    def test_missing_pentadic_agent_fails(self):
        """Missing agent in pentadic_context should raise ValueError."""
        adapter = ComplaintToKantianAdapter()
        
        complaint = {
            "narrative": "Test narrative",
            "pentadic_context": {
                "act": "Test",
                "scene": {"phenomenal": "Test", "noumenal": "Test"}
            },
            "maxim_extraction": "Test",
            "rhetorical_context": {"experience": "Test"}
        }
        
        with pytest.raises(ValueError, match="agent"):
            adapter.transform(complaint)
    
    def test_adapter_schema_metadata(self):
        """Adapter should have correct schema metadata."""
        adapter = ComplaintToKantianAdapter()
        
        assert adapter.source_schema == "NHSComplaintDocument_v1"
        assert adapter.target_schema == "CaseBuilder_v1"
        assert adapter.pydantic_ai_enabled is False  # Direct mapping, no AI

