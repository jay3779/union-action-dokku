"""
Contract test for ComplaintToKantianAdapter.

Validates NHSComplaintDocument → CaseBuilder schema transformation.
Reference: quickstart.md Contract Tests section, spec.md User Story 1
"""

import pytest
from src.adapters.complaint_to_kantian import ComplaintToKantianAdapter


def test_complaint_to_kantian_contract_valid_document():
    """
    Contract test: Valid NHSComplaintDocument → CaseBuilder.
    
    Tests that ComplaintToKantianAdapter correctly transforms a valid
    complaint document with all required fields.
    """
    # Arrange: Valid ComplaintCare document
    complaint = {
        "narrative": "I was denied training despite policy requirements...",
        "pentadic_context": {
            "act": "Training denial",
            "scene": {
                "phenomenal": "Operational pressures",
                "noumenal": "Professional development duty"
            },
            "agent": {
                "role": "Clinical Support Assistant"
            },
            "agency": "Management directive",
            "purpose": "Cost reduction"
        },
        "maxim_extraction": "Training can be denied when operational needs arise",
        "rhetorical_context": {
            "experience": "Felt undervalued and unsupported"
        }
    }
    
    # Act: Transform
    adapter = ComplaintToKantianAdapter()
    case_builder_input = adapter.transform(complaint)
    
    # Assert: Valid CaseBuilder input
    assert "action" in case_builder_input
    assert case_builder_input["action"]["description"] == complaint["narrative"]
    assert case_builder_input["action"]["moral_worth"] == "PENDING"
    
    assert "scene" in case_builder_input
    assert case_builder_input["scene"]["phenomenal_constraints"] == "Operational pressures"
    assert case_builder_input["scene"]["noumenal_duties"] == "Professional development duty"
    
    assert "agent" in case_builder_input
    assert case_builder_input["agent"]["role"] == "Clinical Support Assistant"
    assert case_builder_input["agent"]["categorical_status"] == "PENDING"
    
    assert case_builder_input["maxim"] == complaint["maxim_extraction"]
    assert case_builder_input["employee_experience"] == "Felt undervalued and unsupported"


def test_complaint_to_kantian_contract_missing_narrative():
    """
    Contract test: Missing narrative field should raise ValueError.
    
    Validates that adapter enforces required fields for Kantian analysis.
    """
    # Arrange: Complaint missing narrative
    complaint = {
        "pentadic_context": {
            "act": "Training denial",
            "scene": {"phenomenal": "Operational pressures"},
            "agent": {"role": "CSA"}
        },
        "maxim_extraction": "Training is optional"
    }
    
    # Act & Assert: Validation should fail
    adapter = ComplaintToKantianAdapter()
    with pytest.raises(ValueError, match="narrative"):
        adapter.transform(complaint)


def test_complaint_to_kantian_contract_missing_maxim():
    """
    Contract test: Missing maxim extraction should raise ValueError.
    
    Kantian analysis cannot proceed without explicit organizational maxim.
    """
    # Arrange: Complaint missing maxim
    complaint = {
        "narrative": "I was denied training...",
        "pentadic_context": {
            "act": "Training denial",
            "scene": {"phenomenal": "Operational pressures"},
            "agent": {"role": "CSA"}
        }
    }
    
    # Act & Assert: Validation should fail
    adapter = ComplaintToKantianAdapter()
    with pytest.raises(ValueError, match="maxim_extraction"):
        adapter.transform(complaint)


def test_complaint_to_kantian_contract_validation_passes():
    """
    Contract test: validate() method returns True for valid document.
    """
    # Arrange: Valid complaint
    complaint = {
        "narrative": "I was denied training...",
        "pentadic_context": {
            "act": "Training denial",
            "scene": {"phenomenal": "Operational pressures"},
            "agent": {"role": "CSA"}
        },
        "maxim_extraction": "Training is optional"
    }
    
    # Act: Validate
    adapter = ComplaintToKantianAdapter()
    result = adapter.validate(complaint)
    
    # Assert: Validation passes
    assert result is True


def test_complaint_to_kantian_contract_schema_metadata():
    """
    Contract test: Adapter has correct schema metadata.
    """
    adapter = ComplaintToKantianAdapter()
    
    assert adapter.source_schema == "NHSComplaintDocument_v1"
    assert adapter.target_schema == "CaseBuilder_v1"
    assert adapter.pydantic_ai_enabled is False  # Direct mapping, no AI needed

