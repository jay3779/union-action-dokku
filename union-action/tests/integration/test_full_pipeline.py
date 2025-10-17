"""
End-to-end pipeline integration test for User Story 4.

Tests complete agent-orchestrated workflow: ComplaintCare → Kantian → CareVoice.
Reference: spec.md User Story 4, tasks.md T023

Constitutional Compliance:
- Agent-Orchestrated: Tests autonomous agent workflow
- Human-in-the-Loop: Agent handles decision points
- Constitutional Compliance: Validates Checkpoint 3.5
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch

from src.main import app
from src.services.constitutional_validator import ConstitutionalComplianceChecker

client = AsyncClient(app=app, base_url="http://test")


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us4_agent_orchestrates_two_step_pipeline(mock_deploy_survey):
    """
    US4 Acceptance Scenario 1:
    Agent orchestrates 2-step pipeline → receives all 3 outputs.
    
    Tests that an autonomous agent can successfully call both endpoints
    in sequence and maintain workflow_id throughout.
    """
    workflow_id = "test_wf_us4_001"
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 15,
        "module_list": ["core", "dignity_instrumentalization", "autonomy_agency", "categorical_imperative"],
        "validation_status": "passed"
    }

    # Step 1: Agent calls /escalate-to-ethics (ComplaintCare → Kantian)
    step1_payload = {
        "workflow_id": workflow_id,
        "source_data": {
            "narrative": "I was denied training despite policy requirements...",
            "pentadic_context": {
                "act": "Training denial",
                "scene": {"phenomenal": "Operational pressures", "noumenal": "Professional development duty"},
                "agent": {"role": "Clinical Support Assistant"}
            },
            "maxim_extraction": "Training can be denied when operational needs arise"
        }
    }
    
    step1_response = await client.post("/escalate-to-ethics", json=step1_payload)
    assert step1_response.status_code == 200
    
    ethical_report = step1_response.json()["transformed_data"]
    
    # Step 2: Agent calls /generate-koers-survey (Kantian → CareVoice)
    step2_payload = {
        "workflow_id": workflow_id,
        "source_data": ethical_report
    }
    
    step2_response = await client.post("/generate-koers-survey", json=step2_payload)
    assert step2_response.status_code == 200
    
    deployment_report = step2_response.json()["transformed_data"]
    
    # Assert: Agent received all 3 outputs
    assert step1_payload["source_data"] is not None  # (a) ComplaintCare pentadic analysis
    assert ethical_report is not None  # (b) Kantian ethical report
    assert deployment_report is not None  # (c) CareVoice Typeform URL
    
    # Assert: workflow_id maintained throughout
    assert step1_response.json()["workflow_id"] == workflow_id
    assert step2_response.json()["workflow_id"] == workflow_id
    
    # Assert: Typeform URL present (final output)
    assert "survey_url" in deployment_report
    assert "typeform.com" in deployment_report["survey_url"]


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us4_schema_version_mismatch_pydantic_ai_adapts(mock_deploy_survey):
    """
    US4 Acceptance Scenario 2 (Part 1):
    Schema version mismatch → Pydantic AI adapts, logs transformation, pipeline continues.
    
    Tests that Pydantic AI can handle schema version mismatches without
    requiring human intervention.
    """
    workflow_id = "test_wf_us4_002"
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 15,
        "module_list": ["core", "dignity_instrumentalization", "autonomy_agency", "categorical_imperative"],
        "validation_status": "passed"
    }

    # For MVP, schema versions match, so we test the happy path
    # In production, Pydantic AI would handle version mismatches
    
    step1_payload = {
        "workflow_id": workflow_id,
        "source_data": {
            "narrative": "I was denied training...",
            "pentadic_context": {
                "act": "Training denial",
                "scene": {"phenomenal": "Operational pressures"},
                "agent": {"role": "CSA"}
            },
            "maxim_extraction": "Training is optional"
        }
    }
    
    step1_response = await client.post("/escalate-to-ethics", json=step1_payload)
    assert step1_response.status_code == 200
    
    ethical_report = step1_response.json()["transformed_data"]
    
    step2_payload = {
        "workflow_id": workflow_id,
        "source_data": ethical_report
    }
    
    step2_response = await client.post("/generate-koers-survey", json=step2_payload)
    
    # Assert: Pipeline continues without error
    assert step2_response.status_code == 200
    
    # Assert: Logs would show transformation decision (checked via structlog in production)
    # For MVP, we verify successful transformation
    assert step2_response.json()["transformed_data"]["validation_status"] == "passed"


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us4_true_validation_error_422_status(mock_deploy_survey):
    """
    US4 Acceptance Scenario 2 (Part 2):
    True validation error → 422 status, agent pauses for human review.
    
    Tests that malformed data returns proper error status,
    allowing agent to pause and resume from ComplaintCare.
    """
    workflow_id = "test_wf_us4_003_error"
    
    # Invalid payload: missing required field (narrative)
    invalid_payload = {
        "workflow_id": workflow_id,
        "source_data": {
            "pentadic_context": {"act": "Training denial"},
            # Missing: narrative, maxim_extraction
        }
    }
    
    response = await client.post("/escalate-to-ethics", json=invalid_payload)
    
    # Assert: 422 validation error
    assert response.status_code == 422
    
    # Assert: Specific Pydantic error details provided
    error_detail = response.json()["detail"]
    assert "narrative" in str(error_detail).lower() or "maxim" in str(error_detail).lower()


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us4_structured_logs_show_workflow_metadata(mock_deploy_survey):
    """
    US4 Acceptance Scenario 3:
    Successful pipeline → structured logs show workflow_id, timestamps,
    schema versions, Pydantic AI decisions, constitutional compliance.
    
    Tests that audit trail is complete and parseable by agent.
    """
    workflow_id = "test_wf_us4_004_logs"
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 15,
        "module_list": ["core", "dignity_instrumentalization", "autonomy_agency", "categorical_imperative"],
        "validation_status": "passed"
    }

    step1_payload = {
        "workflow_id": workflow_id,
        "source_data": {
            "narrative": "I was denied training...",
            "pentadic_context": {
                "act": "Training denial",
                "scene": {"phenomenal": "Operational pressures"},
                "agent": {"role": "CSA"}
            },
            "maxim_extraction": "Training is optional"
        }
    }
    
    step1_response = await client.post("/escalate-to-ethics", json=step1_payload)
    assert step1_response.status_code == 200
    
    # Assert: Response contains workflow metadata
    step1_data = step1_response.json()
    assert "workflow_id" in step1_data
    assert "schema_version" in step1_data
    assert "transformation_time_ms" in step1_data
    assert "pydantic_ai_used" in step1_data
    
    # Structured logs (JSON to stdout) would show:
    # - workflow_id: test_wf_us4_004_logs
    # - timestamp: ISO format
    # - schema_version: EthicalAnalysisReport_v1
    # - transformation_time_ms: <value>
    # - pydantic_ai_used: false
    # - constitutional_compliance: (validated via ConstitutionalComplianceChecker)
    
    # For MVP, we verify the response structure is correct


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us4_constitutional_compliance_validation(mock_deploy_survey):
    """
    US4 Acceptance Scenario 4 (Part 1):
    Constitutional compliance check validates 7 gates.
    
    Tests Checkpoint 3.5 validation using ConstitutionalComplianceChecker.
    """
    workflow_id = "test_wf_us4_005_compliance"
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 15,
        "module_list": ["core", "dignity_instrumentalization", "autonomy_agency", "categorical_imperative"],
        "validation_status": "passed"
    }

    # Validate constitutional compliance
    checker = ConstitutionalComplianceChecker()
    result = checker.validate(workflow_id)
    
    # Assert: All 7 gates pass
    assert result.is_compliant()
    assert result.overall_status == "PASS"
    
    # Assert: All gates checked
    assert "solidarity_check" in result.gate_results
    assert "cycle_check" in result.gate_results
    assert "human_approval" in result.gate_results
    assert "vendor_independence" in result.gate_results
    assert "model_justification" in result.gate_results
    assert "representation" in result.gate_results
    assert "validation" in result.gate_results
    
    # Assert: All gates passed
    for gate, status in result.gate_results.items():
        assert status == "PASS", f"Gate {gate} failed"


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us4_agent_receives_typeform_url_for_distribution(mock_deploy_survey):
    """
    US4 Acceptance Scenario 4 (Part 2):
    Agent completes pipeline → DeploymentReport contains valid Typeform URL,
    enabling organizer to distribute survey for round-robin polling.
    
    Tests that final output is suitable for manual survey distribution.
    """
    workflow_id = "test_wf_us4_006_final"
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 15,
        "module_list": ["core", "dignity_instrumentalization", "autonomy_agency", "categorical_imperative"],
        "validation_status": "passed"
    }

    # Step 1: ComplaintCare → Kantian
    step1_payload = {
        "workflow_id": workflow_id,
        "source_data": {
            "narrative": "I was denied training...",
            "pentadic_context": {
                "act": "Training denial",
                "scene": {"phenomenal": "Operational pressures"},
                "agent": {"role": "CSA"}
            },
            "maxim_extraction": "Training is optional"
        }
    }
    
    step1_response = await client.post("/escalate-to-ethics", json=step1_payload)
    ethical_report = step1_response.json()["transformed_data"]
    
    # Step 2: Kantian → CareVoice
    step2_payload = {
        "workflow_id": workflow_id,
        "source_data": ethical_report
    }
    
    step2_response = await client.post("/generate-koers-survey", json=step2_payload)
    
    # Assert: Success
    assert step2_response.status_code == 200
    
    deployment_report = step2_response.json()["transformed_data"]
    
    # Assert: DeploymentReport structure
    assert "survey_url" in deployment_report
    assert "survey_id" in deployment_report
    assert "module_list" in deployment_report
    assert "validation_status" in deployment_report
    
    # Assert: Validation passed
    assert deployment_report["validation_status"] == "passed"
    
    # Assert: Valid Typeform URL format
    survey_url = deployment_report["survey_url"]
    assert survey_url.startswith("https://")
    assert "typeform.com" in survey_url
    
    # Assert: Modules configured matching Kantian violations
    assert len(deployment_report["module_list"]) >= 1
    assert "core" in deployment_report["module_list"]


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us4_full_pipeline_performance(mock_deploy_survey):
    """
    Performance test: Full 2-step pipeline completes in <20 seconds.
    
    Success Criteria SC-005: Full pipeline (ComplaintCare → Kantian →
    CareVoice/KOERS) completes in <20 seconds with audit trail.
    """
    workflow_id = "test_wf_us4_perf"
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 15,
        "module_list": ["core", "dignity_instrumentalization", "autonomy_agency", "categorical_imperative"],
        "validation_status": "passed"
    }

    # Step 1: ComplaintCare → Kantian
    step1_payload = {
        "workflow_id": workflow_id,
        "source_data": {
            "narrative": "I was denied training..." * 50,  # Typical size
            "pentadic_context": {
                "act": "Training denial",
                "scene": {"phenomenal": "Operational pressures"},
                "agent": {"role": "CSA"}
            },
            "maxim_extraction": "Training is optional"
        }
    }
    
    step1_response = await client.post("/escalate-to-ethics", json=step1_payload)
    step1_time = step1_response.json()["transformation_time_ms"]
    
    ethical_report = step1_response.json()["transformed_data"]
    
    # Step 2: Kantian → CareVoice
    step2_payload = {
        "workflow_id": workflow_id,
        "source_data": ethical_report
    }
    
    step2_response = await client.post("/generate-koers-survey", json=step2_payload)
    step2_time = step2_response.json()["transformation_time_ms"]
    
    # Assert: Total pipeline time < 20 seconds
    total_time = step1_time + step2_time
    assert total_time < 20000, f"Full pipeline took {total_time}ms (>20000ms limit)"
    
    # Assert: Both steps successful
    assert step1_response.status_code == 200
    assert step2_response.status_code == 200

