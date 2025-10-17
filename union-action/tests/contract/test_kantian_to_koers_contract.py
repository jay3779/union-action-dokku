"""
Contract test for KantianToKOERSAdapter.

Validates EthicalAnalysisReport → DeploymentReport schema transformation.
Reference: spec.md User Story 2, tasks.md T019
"""

from typing import Any, Dict
import pytest
from unittest.mock import patch

from src.adapters.kantian_to_koers import KantianToKOERSAdapter, ViolationToModuleMapper


@patch('src.adapters.kantian_to_koers.deploy_survey')
def test_kantian_to_koers_contract_valid_ethical_report(mock_deploy_survey):
    """
    Contract test: Valid EthicalAnalysisReport → DeploymentReport.

    Tests that KantianToKOERSAdapter correctly transforms an ethical report
    with violations into a KOERS survey deployment report.
    """
    # Arrange: Valid ethical report with 3 violations
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 15,
        "module_list": ["core", "dignity_instrumentalization", "autonomy_agency", "categorical_imperative"],
        "validation_status": "passed"
    }
    ethical_report = {
        "universalizability_test": {
            "verdict": "FAILURE",
            "rationale": "Organizational maxim cannot be universalized..."
        },
        "humanity_formula_test": {
            "verdict": "VIOLATION",
            "rationale": "Employee treated as mere means..."
        },
        "autonomy_test": {
            "verdict": "VIOLATION",
            "rationale": "Action motivated by external pressure..."
        },
        "summary": "Systematic ethical failure requiring remediation."
    }

    # Act: Transform
    adapter = KantianToKOERSAdapter()
    deployment_report = adapter.transform(ethical_report)

    # Assert: Correct modules are identified
    modules = ViolationToModuleMapper.map_violations(ethical_report)
    assert "categorical_imperative" in modules  # Universalizability failure
    assert "dignity_instrumentalization" in modules  # Humanity Formula violation
    assert "autonomy_agency" in modules  # Autonomy violation


def test_violation_to_module_mapper_humanity_formula_violation():
    """
    Contract test: Humanity Formula violation → dignity_instrumentalization module.

    US2 Acceptance Scenario 1: Ensures correct module mapping for
    "treating employee as mere means" violations.
    """
    # Arrange: Ethical report with Humanity Formula violation
    ethical_report = {
        "humanity_formula_test": {
            "verdict": "VIOLATION",
            "rationale": "Employee treated as mere means to operational efficiency"
        }
    }

    # Act: Map violations to modules
    modules = ViolationToModuleMapper.map_violations(ethical_report)

    # Assert: dignity_instrumentalization module included
    assert "core" in modules
    assert "dignity_instrumentalization" in modules
    assert len(modules) == 2  # core + dignity_instrumentalization


def test_violation_to_module_mapper_autonomy_violation():
    """
    Contract test: Autonomy violation → autonomy_agency module.

    US2 Acceptance Scenario 2: Ensures correct module mapping for
    autonomy violations.
    """
    # Arrange: Ethical report with Autonomy violation
    ethical_report = {
        "autonomy_test": {
            "verdict": "VIOLATION",
            "rationale": "Action from external pressure, not duty"
        }
    }

    # Act: Map violations to modules
    modules = ViolationToModuleMapper.map_violations(ethical_report)

    # Assert: autonomy_agency module included
    assert "core" in modules
    assert "autonomy_agency" in modules


@patch('src.adapters.kantian_to_koers.deploy_survey')
def test_kantian_to_koers_contract_three_violations(mock_deploy_survey):
    """
    Contract test: 3 violations → core + 3 relevant modules.

    US2 Acceptance Scenario 3: Tests that multiple violations are
    correctly mapped to multiple KOERS modules.
    """
    # Arrange: Ethical report with 3 distinct violations
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 22,
        "module_list": ["core", "categorical_imperative", "dignity_instrumentalization", "autonomy_agency"],
        "validation_status": "passed"
    }
    ethical_report = {
        "universalizability_test": {"verdict": "FAILURE"},
        "humanity_formula_test": {"verdict": "VIOLATION"},
        "autonomy_test": {"verdict": "VIOLATION"}
    }

    # Act: Transform
    adapter = KantianToKOERSAdapter()
    deployment_report = adapter.transform(ethical_report)

    # Assert: Correct module list and item count
    assert "categorical_imperative" in deployment_report["module_list"]
    assert "dignity_instrumentalization" in deployment_report["module_list"]
    assert "autonomy_agency" in deployment_report["module_list"]
    assert len(deployment_report["module_list"]) == 4

    # Assert: Valid Typeform URL
    assert "typeform.com" in deployment_report["survey_url"]


@patch('src.adapters.kantian_to_koers.deploy_survey')
def test_kantian_to_koers_contract_deployment_report_structure(mock_deploy_survey):
    """
    Contract test: DeploymentReport contains all required fields.

    US2 Acceptance Scenario 4: Validates that deployment report has
    survey URL, validation status, and module list matching violations.
    """
    # Arrange: Valid ethical report
    mock_deploy_survey.return_value = {
        "survey_id": "tf_xyz789",
        "survey_url": "https://typeform.com/to/abc123",
        "item_count": 12,
        "module_list": ["core", "dignity_instrumentalization"],
        "validation_status": "passed"
    }
    ethical_report = {
        "humanity_formula_test": {"verdict": "VIOLATION"}
    }

    # Act: Transform
    adapter = KantianToKOERSAdapter()
    deployment_report = adapter.transform(ethical_report)

    # Assert: Report has required fields
    assert "survey_id" in deployment_report
    assert "survey_url" in deployment_report
    assert "item_count" in deployment_report
    assert "module_list" in deployment_report
    assert "validation_status" in deployment_report
    assert deployment_report["validation_status"] == "passed"
    assert "dignity_instrumentalization" in deployment_report["module_list"]


def test_kantian_to_koers_contract_no_violations_defaults_to_core():
    """
    Contract test: No violations → core module only.

    Edge case: If ethical report shows no violations (all tests PASS),
    KOERS survey should default to core module only.
    """
    # Arrange: Ethical report with no violations
    ethical_report = {
        "universalizability_test": {"verdict": "PASS"},
        "humanity_formula_test": {"verdict": "PASS"},
        "autonomy_test": {"verdict": "PASS"}
    }

    # Act: Map violations to modules
    modules = ViolationToModuleMapper.map_violations(ethical_report)

    # Assert: Only core module
    assert modules == ["core"]


def test_kantian_to_koers_contract_missing_test_results():
    """
    Contract test: Missing test results should raise ValueError.

    Validates that adapter enforces required structure for KOERS generation.
    """
    # Arrange: Empty ethical report
    ethical_report = {}

    # Act & Assert: Validation should fail
    adapter = KantianToKOERSAdapter()
    with pytest.raises(ValueError, match="test result"):
        adapter.transform(ethical_report)


def test_kantian_to_koers_contract_schema_metadata():
    """
    Contract test: Adapter has correct schema metadata.
    """
    adapter = KantianToKOERSAdapter()

    assert adapter.source_schema == "EthicalAnalysisReport_v1"
    assert adapter.target_schema == "DeploymentReport_v1"
    assert adapter.pydantic_ai_enabled is True  # May need version adaptation

