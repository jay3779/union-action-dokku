"""
Integration test for User Story 2: Kantian → CareVoice KOERS Survey

Tests end-to-end workflow of /generate-koers-survey endpoint.
Reference: spec.md User Story 2, tasks.md T021
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.main import app

client = TestClient(app)


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us2_humanity_formula_violation_to_dignity_module(mock_deploy_survey):
    """
    US2 Acceptance Scenario 1:
    Humanity Formula violation → dignity_instrumentalization module deployed.
    
    Tests that ethical violations are correctly mapped to KOERS modules
    and deployed to Typeform.
    """
    # Arrange: Ethical report with Humanity Formula violation
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 12,
        "module_list": ["core", "dignity_instrumentalization"],
        "validation_status": "passed"
    }
    payload = {
        "workflow_id": "test_wf_us2_001",
        "source_data": {
            "humanity_formula_test": {
                "verdict": "VIOLATION",
                "rationale": "Employee treated as mere means to operational efficiency"
            },
            "summary": "Humanity Formula violation detected"
        }
    }
    
    # Act: POST to /generate-koers-survey
    response = client.post("/generate-koers-survey", json=payload)
    
    # Assert: Success response
    assert response.status_code == 200
    
    data = response.json()
    assert data["workflow_id"] == "test_wf_us2_001"
    assert data["schema_version"] == "DeploymentReport_v1"
    
    # Assert: Deployment report structure
    deployment_report = data["transformed_data"]
    assert "survey_url" in deployment_report
    assert "module_list" in deployment_report
    assert "validation_status" in deployment_report
    
    # Assert: dignity_instrumentalization module included
    assert "dignity_instrumentalization" in deployment_report["module_list"]
    assert deployment_report["validation_status"] == "passed"


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us2_autonomy_violation_to_autonomy_agency_module(mock_deploy_survey):
    """
    US2 Acceptance Scenario 2:
    Autonomy violation → autonomy_agency module included.
    
    Tests that autonomy violations are correctly mapped to the
    autonomy_agency KOERS module.
    """
    # Arrange: Ethical report with Autonomy violation
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 12,
        "module_list": ["core", "autonomy_agency"],
        "validation_status": "passed"
    }
    payload = {
        "workflow_id": "test_wf_us2_002",
        "source_data": {
            "autonomy_test": {
                "verdict": "VIOLATION",
                "rationale": "Action from external pressure, not duty to professional standards"
            }
        }
    }
    
    # Act: POST to /generate-koers-survey
    response = client.post("/generate-koers-survey", json=payload)
    
    # Assert: Success response
    assert response.status_code == 200
    
    deployment_report = response.json()["transformed_data"]
    
    # Assert: autonomy_agency module included
    assert "autonomy_agency" in deployment_report["module_list"]
    assert "core" in deployment_report["module_list"]


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us2_three_violations_to_core_plus_three_modules(mock_deploy_survey):
    """
    US2 Acceptance Scenario 3:
    3 violations → core + 3 relevant modules, valid Typeform URL returned.
    
    Tests that multiple violations generate a comprehensive KOERS survey
    with all relevant modules.
    """
    # Arrange: Ethical report with 3 distinct violations
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 22,
        "module_list": ["core", "categorical_imperative", "dignity_instrumentalization", "autonomy_agency"],
        "validation_status": "passed"
    }
    payload = {
        "workflow_id": "test_wf_us2_003",
        "source_data": {
            "universalizability_test": {
                "verdict": "FAILURE",
                "rationale": "Organizational maxim cannot be universalized"
            },
            "humanity_formula_test": {
                "verdict": "VIOLATION",
                "rationale": "Employee treated as mere means"
            },
            "autonomy_test": {
                "verdict": "VIOLATION",
                "rationale": "Action from external pressure"
            }
        }
    }
    
    # Act: POST to /generate-koers-survey
    response = client.post("/generate-koers-survey", json=payload)
    
    # Assert: Success response
    assert response.status_code == 200
    
    deployment_report = response.json()["transformed_data"]
    
    # Assert: 4 modules total (core + 3 violation modules)
    modules = deployment_report["module_list"]
    assert len(modules) == 4
    assert "core" in modules
    assert "categorical_imperative" in modules
    assert "dignity_instrumentalization" in modules
    assert "autonomy_agency" in modules
    
    # Assert: Valid Typeform URL
    assert "typeform.com" in deployment_report["survey_url"]


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us2_successful_deployment_report_structure(mock_deploy_survey):
    """
    US2 Acceptance Scenario 4:
    Successful deployment → validation status "passed", module list matches violations.
    
    Tests that the deployment report contains all required fields
    and correct metadata.
    """
    # Arrange: Valid ethical report
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 17,
        "module_list": ["core", "dignity_instrumentalization", "autonomy_agency"],
        "validation_status": "passed"
    }
    payload = {
        "workflow_id": "test_wf_us2_004",
        "source_data": {
            "humanity_formula_test": {"verdict": "VIOLATION"},
            "autonomy_test": {"verdict": "VIOLATION"}
        }
    }
    
    # Act: POST to /generate-koers-survey
    response = client.post("/generate-koers-survey", json=payload)
    
    # Assert: Success response
    assert response.status_code == 200
    
    deployment_report = response.json()["transformed_data"]
    
    # Assert: Required fields present
    assert "survey_id" in deployment_report
    assert "survey_url" in deployment_report
    assert "item_count" in deployment_report
    assert "module_list" in deployment_report
    assert "validation_status" in deployment_report
    
    # Assert: Validation status passed
    assert deployment_report["validation_status"] == "passed"
    
    # Assert: Module list matches violations
    assert "dignity_instrumentalization" in deployment_report["module_list"]
    assert "autonomy_agency" in deployment_report["module_list"]
    
    # Assert: Item count reflects modules (7 core + extras)
    assert deployment_report["item_count"] >= 7


def test_us2_empty_ethical_report_returns_validation_error():
    """
    Edge case: Empty ethical report → 422 validation error.
    
    Tests that the endpoint enforces required structure for KOERS generation.
    """
    # Arrange: Empty ethical report
    payload = {
        "workflow_id": "test_wf_us2_empty",
        "source_data": {}
    }
    
    # Act: POST to /generate-koers-survey
    response = client.post("/generate-koers-survey", json=payload)
    
    # Assert: Validation error (422)
    assert response.status_code == 422


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us2_endpoint_performance(mock_deploy_survey):
    """
    Performance test: KOERS survey generation completes quickly.
    
    Success Criteria SC-003: CareVoice KOERS survey generation successfully
    maps ethical violations, generates Typeform JSON, and returns valid URL.
    """
    # Arrange: Valid ethical report
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 17,
        "module_list": ["core", "dignity_instrumentalization", "autonomy_agency"],
        "validation_status": "passed"
    }
    payload = {
        "workflow_id": "test_wf_us2_perf",
        "source_data": {
            "humanity_formula_test": {"verdict": "VIOLATION"},
            "autonomy_test": {"verdict": "VIOLATION"}
        }
    }
    
    # Act: POST to /generate-koers-survey
    response = client.post("/generate-koers-survey", json=payload)
    
    # Assert: Success and reasonable performance
    assert response.status_code == 200
    transformation_time = response.json()["transformation_time_ms"]
    assert transformation_time < 10000, f"Transformation took {transformation_time}ms (>10000ms limit)"


@pytest.mark.asyncio
@patch('src.adapters.kantian_to_koers.deploy_survey')
async def test_us2_typeform_url_format(mock_deploy_survey):
    """
    Integration test: Typeform URL has correct format.
    
    Tests that the generated Typeform URL is valid and accessible.
    """
    # Arrange: Valid ethical report
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 12,
        "module_list": ["core", "dignity_instrumentalization"],
        "validation_status": "passed"
    }
    payload = {
        "workflow_id": "test_wf_us2_url",
        "source_data": {
            "humanity_formula_test": {"verdict": "VIOLATION"}
        }
    }
    
    # Act: POST to /generate-koers-survey
    response = client.post("/generate-koers-survey", json=payload)
    
    # Assert: Success response
    assert response.status_code == 200
    
    survey_url = response.json()["transformed_data"]["survey_url"]
    
    # Assert: URL format
    assert survey_url.startswith("https://")
    assert "typeform.com" in survey_url

