"""
Unit tests for xsrc domain models.

Tests NHSComplaintDocument, EthicalAnalysisReport, and DeploymentReport
Pydantic models for validation, required fields, and structure.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

# Import xsrc models via union_action_client path setup
import sys
from pathlib import Path
xsrc_path = Path(__file__).parent.parent.parent.parent / "xunion-action-integration"
if xsrc_path.exists():
    sys.path.insert(0, str(xsrc_path))

from xsrc.models import (
    NHSComplaintDocument,
    EthicalAnalysisReport,
    DeploymentReport,
)


class TestNHSComplaintDocument:
    """Test NHSComplaintDocument validation and structure."""
    
    def test_valid_complaint_document(self):
        """Valid NHSComplaintDocument should pass validation."""
        doc = NHSComplaintDocument(
            narrative="I was denied training despite requesting it multiple times.",
            pentadic_context={
                "act": "Training denial",
                "scene": {
                    "phenomenal": "Budget constraints",
                    "noumenal": "Professional development duty"
                },
                "agent": {
                    "role": "Clinical Support Assistant"
                },
                "agency": "Management directive",
                "purpose": "Cost reduction"
            },
            maxim_extraction="Training can be denied when convenient",
            rhetorical_context={
                "experience": "Felt undervalued and unsupported"
            }
        )
        
        assert doc.narrative == "I was denied training despite requesting it multiple times."
        assert doc.pentadic_context["act"] == "Training denial"
        assert doc.maxim_extraction == "Training can be denied when convenient"
    
    def test_missing_narrative_fails(self):
        """Missing narrative should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            NHSComplaintDocument(
                pentadic_context={"act": "Test", "scene": {}, "agent": {}},
                maxim_extraction="Test",
                rhetorical_context={"experience": "Test"}
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("narrative",) for error in errors)
    
    def test_missing_pentadic_context_fails(self):
        """Missing pentadic_context should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            NHSComplaintDocument(
                narrative="Test narrative",
                maxim_extraction="Test",
                rhetorical_context={"experience": "Test"}
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("pentadic_context",) for error in errors)
    
    def test_pentadic_context_missing_scene_fails(self):
        """pentadic_context without 'scene' key should fail."""
        with pytest.raises(ValidationError) as exc_info:
            NHSComplaintDocument(
                narrative="Test narrative",
                pentadic_context={
                    "act": "Test",
                    "agent": {"role": "Test"}
                },
                maxim_extraction="Test",
                rhetorical_context={"experience": "Test"}
            )
        
        errors = exc_info.value.errors()
        # Check for ValueError in validation
        assert any("scene" in str(error) for error in errors)
    
    def test_pentadic_context_missing_agent_fails(self):
        """pentadic_context without 'agent' key should fail."""
        with pytest.raises(ValidationError) as exc_info:
            NHSComplaintDocument(
                narrative="Test narrative",
                pentadic_context={
                    "act": "Test",
                    "scene": {"phenomenal": "Test", "noumenal": "Test"}
                },
                maxim_extraction="Test",
                rhetorical_context={"experience": "Test"}
            )
        
        errors = exc_info.value.errors()
        assert any("agent" in str(error) for error in errors)
    
    def test_rhetorical_context_missing_experience_fails(self):
        """rhetorical_context without 'experience' key should fail."""
        with pytest.raises(ValidationError) as exc_info:
            NHSComplaintDocument(
                narrative="Test narrative",
                pentadic_context={
                    "act": "Test",
                    "scene": {},
                    "agent": {"role": "Test"}
                },
                maxim_extraction="Test",
                rhetorical_context={}
            )
        
        errors = exc_info.value.errors()
        assert any("experience" in str(error) for error in errors)
    
    def test_short_narrative_fails(self):
        """Narrative shorter than min_length should fail."""
        with pytest.raises(ValidationError) as exc_info:
            NHSComplaintDocument(
                narrative="Short",  # Less than 10 characters
                pentadic_context={
                    "act": "Test",
                    "scene": {},
                    "agent": {"role": "Test"}
                },
                maxim_extraction="Test maxim",
                rhetorical_context={"experience": "Test"}
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("narrative",) for error in errors)


class TestEthicalAnalysisReport:
    """Test EthicalAnalysisReport validation and structure."""
    
    def test_valid_ethical_report(self):
        """Valid EthicalAnalysisReport should pass validation."""
        report = EthicalAnalysisReport(
            universalizability_test={
                "verdict": "FAILURE",
                "rationale": "Cannot be universalized"
            },
            humanity_formula_test={
                "verdict": "VIOLATION",
                "rationale": "Treated as mere means"
            },
            autonomy_test={
                "verdict": "VIOLATION",
                "rationale": "Motivated by external pressure"
            },
            procedural_justice_test={
                "verdict": "FAILURE",
                "rationale": "Lacks transparency"
            },
            summary="Systematic ethical failure",
            case_builder_input={"maxim": "Test", "action": {}, "scene": {}, "agent": {}}
        )
        
        assert report.universalizability_test["verdict"] == "FAILURE"
        assert report.humanity_formula_test["verdict"] == "VIOLATION"
        assert "Systematic" in report.summary
    
    def test_missing_summary_fails(self):
        """Missing summary should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            EthicalAnalysisReport(
                case_builder_input={}
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("summary",) for error in errors)
    
    def test_missing_case_builder_input_fails(self):
        """Missing case_builder_input should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            EthicalAnalysisReport(
                summary="Test summary that is long enough"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("case_builder_input",) for error in errors)
    
    def test_invalid_verdict_fails(self):
        """Invalid verdict value should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            EthicalAnalysisReport(
                universalizability_test={
                    "verdict": "INVALID",  # Not in [FAILURE, VIOLATION, PASS]
                    "rationale": "Test"
                },
                summary="Test summary that is long enough",
                case_builder_input={}
            )
        
        errors = exc_info.value.errors()
        assert any("verdict" in str(error).lower() for error in errors)
    
    def test_test_result_missing_rationale_fails(self):
        """Test result without rationale should fail."""
        with pytest.raises(ValidationError) as exc_info:
            EthicalAnalysisReport(
                universalizability_test={
                    "verdict": "FAILURE"
                    # Missing rationale
                },
                summary="Test summary that is long enough",
                case_builder_input={}
            )
        
        errors = exc_info.value.errors()
        assert any("rationale" in str(error).lower() for error in errors)


class TestDeploymentReport:
    """Test DeploymentReport validation and structure."""
    
    def test_valid_deployment_report(self):
        """Valid DeploymentReport should pass validation."""
        report = DeploymentReport(
            survey_id="tf_xyz789",
            survey_url="https://typeform.com/to/abc123",
            item_count=22,
            module_list=["core", "categorical_imperative", "dignity_instrumentalization"],
            validation_status="passed"
        )
        
        assert report.survey_id == "tf_xyz789"
        assert report.item_count == 22
        assert "core" in report.module_list
    
    def test_missing_survey_url_fails(self):
        """Missing survey_url should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            DeploymentReport(
                survey_id="tf_test",
                item_count=10,
                module_list=["core"],
                validation_status="passed"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("survey_url",) for error in errors)
    
    def test_invalid_url_pattern_fails(self):
        """Invalid URL pattern should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            DeploymentReport(
                survey_id="tf_test",
                survey_url="not-a-valid-url",  # Missing http(s)://
                item_count=10,
                module_list=["core"],
                validation_status="passed"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("survey_url",) for error in errors)
    
    def test_module_list_without_core_fails(self):
        """module_list without 'core' should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            DeploymentReport(
                survey_id="tf_test",
                survey_url="https://typeform.com/to/test",
                item_count=10,
                module_list=["categorical_imperative"],  # Missing core
                validation_status="passed"
            )
        
        errors = exc_info.value.errors()
        assert any("core" in str(error).lower() for error in errors)
    
    def test_item_count_less_than_7_fails(self):
        """item_count less than 7 (core minimum) should fail."""
        with pytest.raises(ValidationError) as exc_info:
            DeploymentReport(
                survey_id="tf_test",
                survey_url="https://typeform.com/to/test",
                item_count=5,  # Less than core minimum of 7
                module_list=["core"],
                validation_status="passed"
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("item_count",) for error in errors)
    
    def test_invalid_validation_status_fails(self):
        """Invalid validation_status should fail."""
        with pytest.raises(ValidationError) as exc_info:
            DeploymentReport(
                survey_id="tf_test",
                survey_url="https://typeform.com/to/test",
                item_count=10,
                module_list=["core"],
                validation_status="invalid_status"  # Not 'passed' or 'failed'
            )
        
        errors = exc_info.value.errors()
        assert any("validation_status" in str(error).lower() for error in errors)

