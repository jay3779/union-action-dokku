"""
Integration test for User Story 1: ComplaintCare → Kantian Ethics

Tests end-to-end workflow of /escalate-to-ethics endpoint.
Reference: spec.md User Story 1, tasks.md T016
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_us1_valid_complaint_with_maxim():
    """
    US1 Acceptance Scenario 1:
    Valid complaint with maxim → ethical report in <5 seconds.
    
    Tests that a valid NHSComplaintDocument is successfully transformed
    into an EthicalAnalysisReport with all three Kantian tests.
    """
    # Arrange: Valid complaint payload
    payload = {
        "workflow_id": "test_wf_001",
        "source_data": {
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
    }
    
    # Act: POST to /escalate-to-ethics
    response = client.post("/escalate-to-ethics", json=payload)
    
    # Assert: Success response
    assert response.status_code == 200
    
    data = response.json()
    assert data["workflow_id"] == "test_wf_001"
    assert data["schema_version"] == "EthicalAnalysisReport_v1"
    assert data["transformation_time_ms"] < 5000  # <5 seconds
    assert data["pydantic_ai_used"] is False
    
    # Assert: Ethical report structure
    ethical_report = data["transformed_data"]
    assert "universalizability_test" in ethical_report
    assert "humanity_formula_test" in ethical_report
    assert "autonomy_test" in ethical_report
    assert "summary" in ethical_report
    
    # Assert: Verdicts present
    assert "verdict" in ethical_report["universalizability_test"]
    assert "verdict" in ethical_report["humanity_formula_test"]
    assert "verdict" in ethical_report["autonomy_test"]


def test_us1_policy_gap_analysis_to_humanity_formula_violation():
    """
    US1 Acceptance Scenario 2:
    Policy gap analysis (Scene-Act tension) → Humanity Formula violation.
    
    Tests that the adapter correctly maps pentadic tensions to
    Kantian ethical violations.
    """
    # Arrange: Complaint with Scene-Act tension
    payload = {
        "workflow_id": "test_wf_002",
        "source_data": {
            "narrative": "Management forced me to work without proper equipment...",
            "pentadic_context": {
                "act": "Unsafe work directive",
                "scene": {
                    "phenomenal": "Equipment shortage",
                    "noumenal": "Worker safety duty"
                },
                "agent": {
                    "role": "Healthcare Worker"
                }
            },
            "maxim_extraction": "Worker safety can be compromised for operational efficiency"
        }
    }
    
    # Act: POST to /escalate-to-ethics
    response = client.post("/escalate-to-ethics", json=payload)
    
    # Assert: Success with Humanity Formula violation
    assert response.status_code == 200
    ethical_report = response.json()["transformed_data"]
    
    # Assert: Humanity Formula test present (treating employee as mere means)
    assert ethical_report["humanity_formula_test"]["verdict"] == "VIOLATION"
    assert "mere means" in ethical_report["humanity_formula_test"]["rationale"].lower()


def test_us1_missing_maxim_returns_validation_error():
    """
    US1 Acceptance Scenario 3:
    Missing maxim → Pydantic validation error (422).
    
    Tests that the endpoint enforces required fields for Kantian analysis.
    """
    # Arrange: Complaint missing maxim
    payload = {
        "workflow_id": "test_wf_003",
        "source_data": {
            "narrative": "I was denied training...",
            "pentadic_context": {
                "act": "Training denial",
                "scene": {"phenomenal": "Operational pressures"},
                "agent": {"role": "CSA"}
            }
            # Missing: maxim_extraction
        }
    }
    
    # Act: POST to /escalate-to-ethics
    response = client.post("/escalate-to-ethics", json=payload)
    
    # Assert: Validation error (422)
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert "maxim" in str(error_detail).lower()


def test_us1_universalizability_failure_contains_no_technical_jargon():
    """
    US1 Acceptance Scenario 4:
    Universalizability failure → zero technical jargon, philosophical principles cited.
    
    Tests that the ethical report is human-readable and cites principles by name.
    """
    # Arrange: Valid complaint
    payload = {
        "workflow_id": "test_wf_004",
        "source_data": {
            "narrative": "I was denied training despite policy requirements...",
            "pentadic_context": {
                "act": "Training denial",
                "scene": {"phenomenal": "Operational pressures"},
                "agent": {"role": "CSA"}
            },
            "maxim_extraction": "Training can be denied when operational needs arise"
        }
    }
    
    # Act: POST to /escalate-to-ethics
    response = client.post("/escalate-to-ethics", json=payload)
    
    # Assert: Success
    assert response.status_code == 200
    ethical_report = response.json()["transformed_data"]
    
    # Assert: No technical jargon (blacklist)
    jargon_blacklist = ["pydantic", "jinja", "template", "schema", "json", "api"]
    report_text = str(ethical_report).lower()
    
    for jargon in jargon_blacklist:
        assert jargon not in report_text, f"Technical jargon '{jargon}' found in ethical report"
    
    # Assert: Philosophical principles cited by name
    principles = ["categorical imperative", "autonomy", "humanity"]
    
    found_principle = False
    for principle in principles:
        if principle in report_text:
            found_principle = True
            break
    
    assert found_principle, "No philosophical principles cited by name in ethical report"


def test_us1_endpoint_performance_under_5_seconds():
    """
    Performance test: Transformation completes in <5 seconds.
    
    Success Criteria SC-001: ComplaintCare → Kantian transformation
    completes in <5 seconds for typical complaint document (500-2000 words).
    """
    # Arrange: Typical complaint (500-2000 words simulated)
    payload = {
        "workflow_id": "test_wf_perf",
        "source_data": {
            "narrative": "I was denied training despite policy requirements..." * 50,  # ~500 words
            "pentadic_context": {
                "act": "Training denial",
                "scene": {"phenomenal": "Operational pressures"},
                "agent": {"role": "CSA"}
            },
            "maxim_extraction": "Training can be denied when operational needs arise"
        }
    }
    
    # Act: POST to /escalate-to-ethics
    response = client.post("/escalate-to-ethics", json=payload)
    
    # Assert: Performance requirement met
    assert response.status_code == 200
    transformation_time = response.json()["transformation_time_ms"]
    assert transformation_time < 5000, f"Transformation took {transformation_time}ms (>5000ms limit)"

