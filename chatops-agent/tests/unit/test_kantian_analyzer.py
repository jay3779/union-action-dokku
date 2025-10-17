"""
Unit tests for KantianEthicalAnalyzer.

Tests Kantian ethical analysis logic including:
- Universalizability test
- Humanity Formula test
- Autonomy test
- Procedural Justice test
- Overall summary generation
"""

import pytest
import sys
from pathlib import Path

# Import xsrc modules
xsrc_path = Path(__file__).parent.parent.parent.parent / "xunion-action-integration"
if xsrc_path.exists():
    sys.path.insert(0, str(xsrc_path))

from xsrc.services.kantian_analyzer import KantianEthicalAnalyzer
from xsrc.models import EthicalAnalysisReport


class TestKantianEthicalAnalyzer:
    """Test KantianEthical Analyzer core functionality."""
    
    def test_analyzer_initialization(self):
        """Analyzer should initialize without errors."""
        analyzer = KantianEthicalAnalyzer()
        assert analyzer is not None
    
    def test_analyze_with_valid_input(self):
        """Analyze should return EthicalAnalysisReport with valid input."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "Training can be denied when convenient",
            "scene": {
                "phenomenal_constraints": "Budget pressures",
                "noumenal_duties": "Professional development"
            },
            "agent": {
                "role": "Employee"
            },
            "action": {
                "description": "I was denied training",
                "moral_worth": "PENDING"
            },
            "employee_experience": "Felt undervalued"
        }
        
        report = analyzer.analyze(case_input)
        
        assert isinstance(report, EthicalAnalysisReport)
        assert report.universalizability_test is not None
        assert report.humanity_formula_test is not None
        assert report.autonomy_test is not None
        assert report.procedural_justice_test is not None
        assert report.summary is not None
    
    def test_analyze_missing_required_fields_fails(self):
        """Analyze should fail with missing required fields."""
        analyzer = KantianEthicalAnalyzer()
        
        # Missing 'maxim' field
        case_input = {
            "scene": {},
            "agent": {},
            "action": {}
        }
        
        with pytest.raises(ValueError, match="maxim"):
            analyzer.analyze(case_input)
    
    def test_universalizability_failure_detected(self):
        """Universalizability test should detect non-universalizable maxims."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "Training can be denied when convenient",  # Contains "convenient"
            "scene": {
                "phenomenal_constraints": "Operational pressures",
                "noumenal_duties": "Professional development duty"
            },
            "agent": {"role": "Employee"},
            "action": {"description": "Denied training"}
        }
        
        report = analyzer.analyze(case_input)
        
        assert report.universalizability_test["verdict"] == "FAILURE"
        assert "universalized" in report.universalizability_test["rationale"].lower()
        assert "Categorical Imperative" in report.universalizability_test["rationale"]
    
    def test_universalizability_pass_with_valid_maxim(self):
        """Universalizability test should pass with consistently applicable maxims."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "All employees must receive equal training opportunities",  # No conditional language
            "scene": {
                "phenomenal_constraints": "Normal operations",
                "noumenal_duties": "Equal treatment"
            },
            "agent": {"role": "Employee"},
            "action": {"description": "Received training"}
        }
        
        report = analyzer.analyze(case_input)
        
        assert report.universalizability_test["verdict"] == "PASS"
    
    def test_humanity_formula_violation_detected(self):
        """Humanity Formula test should detect treatment as mere means."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "Test maxim",
            "scene": {},
            "agent": {"role": "Clinical Support Assistant"},
            "action": {
                "description": "I was denied training despite multiple requests"  # "denied" + "training"
            }
        }
        
        report = analyzer.analyze(case_input)
        
        assert report.humanity_formula_test["verdict"] == "VIOLATION"
        assert "mere means" in report.humanity_formula_test["rationale"].lower()
        assert "Humanity Formula" in report.humanity_formula_test["rationale"]
    
    def test_humanity_formula_pass_without_denial(self):
        """Humanity Formula test should pass without dignity violations."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "Test maxim",
            "scene": {},
            "agent": {"role": "Employee"},
            "action": {
                "description": "I received support and recognition for my work"
            }
        }
        
        report = analyzer.analyze(case_input)
        
        assert report.humanity_formula_test["verdict"] == "PASS"
    
    def test_autonomy_violation_with_external_pressure(self):
        """Autonomy test should detect actions motivated by external pressure."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "Test maxim",
            "scene": {
                "phenomenal_constraints": "Cost reduction pressures",  # Contains "cost"
                "noumenal_duties": "Professional standards"
            },
            "agent": {"role": "Employee"},
            "action": {"description": "Action taken"}
        }
        
        report = analyzer.analyze(case_input)
        
        assert report.autonomy_test["verdict"] == "VIOLATION"
        assert "external pressure" in report.autonomy_test["rationale"].lower()
        assert "Autonomy Principle" in report.autonomy_test["rationale"]
    
    def test_autonomy_pass_without_pressure(self):
        """Autonomy test should pass without external pressures."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "Test maxim",
            "scene": {
                "phenomenal_constraints": "Normal operations",
                "noumenal_duties": "Duty considerations"
            },
            "agent": {"role": "Employee"},
            "action": {"description": "Action taken"}
        }
        
        report = analyzer.analyze(case_input)
        
        assert report.autonomy_test["verdict"] == "PASS"
    
    def test_procedural_justice_failure_detected(self):
        """Procedural Justice test should detect lack of fair procedures."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "Test maxim",
            "scene": {
                "phenomenal_constraints": "Arbitrary decision",  # Contains "arbitrary"
                "noumenal_duties": "Fair process"
            },
            "agent": {"role": "Employee"},
            "action": {"description": "Action taken"}
        }
        
        report = analyzer.analyze(case_input)
        
        assert report.procedural_justice_test["verdict"] == "FAILURE"
        assert "procedural justice" in report.procedural_justice_test["rationale"].lower()
    
    def test_summary_reflects_all_violations(self):
        """Summary should reflect when all tests fail/violate."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "Training can be denied when convenient",  # Universalizability FAILURE
            "scene": {
                "phenomenal_constraints": "Cost pressures arbitrary process",  # Autonomy VIOLATION + Procedural FAILURE
                "noumenal_duties": "Professional development"
            },
            "agent": {"role": "Employee"},
            "action": {
                "description": "I was denied training"  # Humanity Formula VIOLATION
            }
        }
        
        report = analyzer.analyze(case_input)
        
        # All 4 tests should fail/violate
        assert report.universalizability_test["verdict"] == "FAILURE"
        assert report.humanity_formula_test["verdict"] == "VIOLATION"
        assert report.autonomy_test["verdict"] == "VIOLATION"
        assert report.procedural_justice_test["verdict"] == "FAILURE"
        
        # Summary should reflect systematic failure
        assert "systematic" in report.summary.lower() or "all" in report.summary.lower()
    
    def test_summary_reflects_no_violations(self):
        """Summary should be positive when all tests pass."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "All employees receive equal treatment",  # PASS
            "scene": {
                "phenomenal_constraints": "Normal operations",  # PASS
                "noumenal_duties": "Ethical duties"
            },
            "agent": {"role": "Employee"},
            "action": {
                "description": "Received fair treatment and support"  # PASS
            }
        }
        
        report = analyzer.analyze(case_input)
        
        # All tests should pass
        assert report.universalizability_test["verdict"] == "PASS"
        assert report.humanity_formula_test["verdict"] == "PASS"
        assert report.autonomy_test["verdict"] == "PASS"
        
        # Summary should be positive
        assert "satisfies" in report.summary.lower() or "ethical" in report.summary.lower()
    
    def test_case_builder_input_preserved(self):
        """Original case_builder_input should be preserved in report."""
        analyzer = KantianEthicalAnalyzer()
        
        case_input = {
            "maxim": "Test maxim",
            "scene": {"test": "value"},
            "agent": {"role": "Test"},
            "action": {"description": "Test"}
        }
        
        report = analyzer.analyze(case_input)
        
        assert report.case_builder_input == case_input

