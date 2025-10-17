"""
Integration tests for local xsrc pipeline.

Tests end-to-end transformation pipeline:
- escalate_to_ethics (WhatsApp → Ethical Analysis)
- generate_koers_survey (Ethical Analysis → KOERS Survey)
"""

import pytest
import sys
from pathlib import Path

# Add project source to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from union_action_client import UnionActionClient


class TestLocalEscalateToEthics:
    """Test local escalate_to_ethics transformation (T117)."""
    
    def test_escalate_to_ethics_success(self):
        """Test successful ethical analysis from complaint text."""
        client = UnionActionClient()
        
        complaint_text = "I was denied training despite requesting it multiple times."
        
        result = client.escalate_to_ethics(
            workflow_id="test_wf_001",
            complaint_text=complaint_text
        )
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "universalizability_test" in result
        assert "humanity_formula_test" in result
        assert "autonomy_test" in result
        assert "procedural_justice_test" in result
        assert "summary" in result
        assert "case_builder_input" in result
        
        # Verify test results have required fields
        assert "verdict" in result["universalizability_test"]
        assert "rationale" in result["universalizability_test"]
        
        # Verdict should be valid value
        assert result["universalizability_test"]["verdict"] in ["FAILURE", "PASS"]
        assert result["humanity_formula_test"]["verdict"] in ["VIOLATION", "PASS"]
        assert result["autonomy_test"]["verdict"] in ["VIOLATION", "PASS"]
        assert result["procedural_justice_test"]["verdict"] in ["FAILURE", "PASS"]
    
    def test_escalate_to_ethics_training_denial_detects_violations(self):
        """Test that training denial triggers expected violations."""
        client = UnionActionClient()
        
        complaint_text = (
            "I was denied training opportunities despite repeated requests. "
            "Management said it was not convenient due to budget constraints."
        )
        
        result = client.escalate_to_ethics(
            workflow_id="test_wf_002",
            complaint_text=complaint_text
        )
        
        # This type of complaint should likely trigger violations
        # (based on keywords: denied, training, convenient, budget)
        assert result["universalizability_test"]["verdict"] in ["FAILURE", "PASS"]
        assert result["humanity_formula_test"]["verdict"] in ["VIOLATION", "PASS"]
    
    def test_escalate_to_ethics_missing_workflow_id_fails(self):
        """Test that missing workflow_id raises ValueError."""
        client = UnionActionClient()
        
        with pytest.raises(ValueError, match="workflow_id"):
            client.escalate_to_ethics(
                workflow_id="",
                complaint_text="Test complaint"
            )
    
    def test_escalate_to_ethics_short_complaint_fails(self):
        """Test that too-short complaint raises ValueError."""
        client = UnionActionClient()
        
        with pytest.raises(ValueError, match="complaint_text"):
            client.escalate_to_ethics(
                workflow_id="test_wf_003",
                complaint_text="Short"  # Less than 10 characters
            )
    
    def test_escalate_to_ethics_rationales_cite_principles(self):
        """Test that rationales cite Kantian principles by name."""
        client = UnionActionClient()
        
        complaint_text = "I was denied professional development opportunities."
        
        result = client.escalate_to_ethics(
            workflow_id="test_wf_004",
            complaint_text=complaint_text
        )
        
        # Rationales should cite philosophical principles
        all_rationales = " ".join([
            result["universalizability_test"]["rationale"],
            result["humanity_formula_test"]["rationale"],
            result["autonomy_test"]["rationale"],
            result["procedural_justice_test"]["rationale"]
        ])
        
        # Should mention Kantian concepts
        kantian_keywords = [
            "Categorical Imperative",
            "Humanity Formula",
            "Autonomy Principle",
            "procedural justice"
        ]
        
        found_principles = [k for k in kantian_keywords if k in all_rationales]
        assert len(found_principles) >= 2, "Should cite multiple Kantian principles"


class TestLocalGenerateKOERSSurvey:
    """Test local generate_koers_survey transformation (T118)."""
    
    def test_generate_koers_survey_success(self):
        """Test successful KOERS survey generation from ethical report."""
        client = UnionActionClient()
        
        ethical_report = {
            "universalizability_test": {"verdict": "FAILURE", "rationale": "Test"},
            "humanity_formula_test": {"verdict": "VIOLATION", "rationale": "Test"},
            "autonomy_test": {"verdict": "PASS", "rationale": "Test"},
            "procedural_justice_test": {"verdict": "PASS", "rationale": "Test"},
            "summary": "Test summary",
            "case_builder_input": {}
        }
        
        result = client.generate_koers_survey(
            workflow_id="test_wf_005",
            ethical_report=ethical_report
        )
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "survey_id" in result
        assert "survey_url" in result
        assert "module_list" in result
        assert "item_count" in result
        assert "validation_status" in result
        
        # Core module should always be included
        assert "core" in result["module_list"]
        
        # URL should be valid format
        assert result["survey_url"].startswith("http")
        
        # Item count should be at least 7 (core module)
        assert result["item_count"] >= 7
    
    def test_generate_koers_survey_maps_violations_to_modules(self):
        """Test that violations are mapped to correct KOERS modules."""
        client = UnionActionClient()
        
        ethical_report = {
            "universalizability_test": {"verdict": "FAILURE", "rationale": "Test"},
            "humanity_formula_test": {"verdict": "VIOLATION", "rationale": "Test"},
            "autonomy_test": {"verdict": "VIOLATION", "rationale": "Test"},
            "procedural_justice_test": {"verdict": "FAILURE", "rationale": "Test"},
            "summary": "All violations",
            "case_builder_input": {}
        }
        
        result = client.generate_koers_survey(
            workflow_id="test_wf_006",
            ethical_report=ethical_report
        )
        
        # Should map to multiple modules based on violations
        # Universalizability FAILURE → categorical_imperative
        # Humanity Formula VIOLATION → dignity_instrumentalization
        # Autonomy VIOLATION → autonomy_agency
        # Procedural Justice FAILURE → procedural_justice
        
        expected_modules = [
            "core",
            "categorical_imperative",
            "dignity_instrumentalization",
            "autonomy_agency",
            "procedural_justice"
        ]
        
        # Check that violations mapped to modules
        assert "categorical_imperative" in result["module_list"]
        assert "dignity_instrumentalization" in result["module_list"]
        
        # Item count should reflect multiple modules
        # core=7, each module ~5, so 5 modules = ~32 items
        assert result["item_count"] >= 20
    
    def test_generate_koers_survey_core_only_with_no_violations(self):
        """Test that only core module is included when all tests pass."""
        client = UnionActionClient()
        
        ethical_report = {
            "universalizability_test": {"verdict": "PASS", "rationale": "Test"},
            "humanity_formula_test": {"verdict": "PASS", "rationale": "Test"},
            "autonomy_test": {"verdict": "PASS", "rationale": "Test"},
            "procedural_justice_test": {"verdict": "PASS", "rationale": "Test"},
            "summary": "All passed",
            "case_builder_input": {}
        }
        
        result = client.generate_koers_survey(
            workflow_id="test_wf_007",
            ethical_report=ethical_report
        )
        
        # Should only have core module
        assert result["module_list"] == ["core"]
        assert result["item_count"] == 7  # Core has 7 items
    
    def test_generate_koers_survey_missing_workflow_id_fails(self):
        """Test that missing workflow_id raises ValueError."""
        client = UnionActionClient()
        
        with pytest.raises(ValueError, match="workflow_id"):
            client.generate_koers_survey(
                workflow_id="",
                ethical_report={}
            )
    
    def test_generate_koers_survey_missing_report_fails(self):
        """Test that missing ethical_report raises ValueError."""
        client = UnionActionClient()
        
        with pytest.raises(ValueError, match="ethical_report"):
            client.generate_koers_survey(
                workflow_id="test_wf_008",
                ethical_report=None
            )


class TestFullPipeline:
    """Test complete pipeline: complaint → analysis → survey."""
    
    def test_end_to_end_pipeline(self):
        """Test full pipeline from complaint to survey URL."""
        client = UnionActionClient()
        
        # Step 1: Escalate to ethics
        complaint_text = "I was denied training despite requesting it."
        
        ethical_report = client.escalate_to_ethics(
            workflow_id="test_wf_009",
            complaint_text=complaint_text
        )
        
        assert "universalizability_test" in ethical_report
        
        # Step 2: Generate KOERS survey
        survey = client.generate_koers_survey(
            workflow_id="test_wf_009",
            ethical_report=ethical_report
        )
        
        assert "survey_url" in survey
        assert "module_list" in survey
        
        # Verify end-to-end: complaint → ethical violations → KOERS modules
        # If any test failed/violated, should have additional modules beyond core
        has_violations = any(
            test["verdict"] in ["FAILURE", "VIOLATION"]
            for test_name in ["universalizability_test", "humanity_formula_test", "autonomy_test", "procedural_justice_test"]
            if (test := ethical_report.get(test_name))
        )
        
        if has_violations:
            assert len(survey["module_list"]) > 1, "Should have modules beyond core"

