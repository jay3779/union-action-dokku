"""
KantianEthicalAnalyzer: Kantian ethical analysis service.

Executes 4 Kantian ethical tests on organizational actions:
1. Universalizability Test (Categorical Imperative)
2. Humanity Formula Test (treating people as ends vs. means)
3. Autonomy Test (duty vs. external pressure)
4. Procedural Justice Test (organizational fairness)

Reference: escalate.py TODO:74 - "Import and use actual Kantian EthicalAnalyzer"
Constitutional Compliance: Zero technical jargon, cite philosophical principles by name
"""

from typing import Dict, Any
import structlog
from datetime import datetime

from ..models.domain import EthicalAnalysisReport

logger = structlog.get_logger(__name__)


class KantianEthicalAnalyzer:
    """
    Kantian ethical analysis engine.
    
    Analyzes organizational actions through Kantian ethical framework:
    - Tests maxims for universalizability
    - Evaluates treatment of employees as ends vs. means
    - Assesses moral worth of actions (duty vs. inclination)
    - Examines procedural justice
    
    Returns human-readable reports citing philosophical principles.
    """
    
    def __init__(self):
        """Initialize analyzer with diagnostic logging."""
        logger.info(
            "kantian_analyzer_initialized",
            tests=["universalizability", "humanity_formula", "autonomy", "procedural_justice"]
        )
    
    def analyze(self, case_builder_input: Dict[str, Any]) -> EthicalAnalysisReport:
        """
        Execute complete Kantian ethical analysis.
        
        Args:
            case_builder_input: Kantian CaseBuilder input from ComplaintToKantianAdapter
                Required keys:
                - action: {description, moral_worth}
                - scene: {phenomenal_constraints, noumenal_duties}
                - agent: {role, categorical_status}
                - maxim: str (organizational maxim being tested)
                - employee_experience: str
        
        Returns:
            EthicalAnalysisReport with all 4 test results and summary
        
        Raises:
            ValueError: If case_builder_input is malformed
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "kantian_analysis_started",
            maxim=case_builder_input.get("maxim", "UNKNOWN"),
            agent_role=case_builder_input.get("agent", {}).get("role", "UNKNOWN")
        )
        
        # Validate input structure
        self._validate_case_input(case_builder_input)
        
        # Extract components
        maxim = case_builder_input["maxim"]
        scene = case_builder_input["scene"]
        agent = case_builder_input["agent"]
        action = case_builder_input["action"]
        
        # Execute 4 Kantian tests
        universalizability_result = self._test_universalizability(maxim, scene)
        humanity_result = self._test_humanity_formula(agent, action)
        autonomy_result = self._test_autonomy(action, scene)
        procedural_justice_result = self._test_procedural_justice(scene, agent)
        
        # Generate summary
        summary = self._generate_summary(
            universalizability_result,
            humanity_result,
            autonomy_result,
            procedural_justice_result
        )
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            "kantian_analysis_complete",
            elapsed_seconds=elapsed,
            verdicts={
                "universalizability": universalizability_result["verdict"],
                "humanity_formula": humanity_result["verdict"],
                "autonomy": autonomy_result["verdict"],
                "procedural_justice": procedural_justice_result["verdict"]
            }
        )
        
        return EthicalAnalysisReport(
            universalizability_test=universalizability_result,
            humanity_formula_test=humanity_result,
            autonomy_test=autonomy_result,
            procedural_justice_test=procedural_justice_result,
            summary=summary,
            case_builder_input=case_builder_input
        )
    
    def _validate_case_input(self, case_input: Dict[str, Any]) -> None:
        """
        Validate case_builder_input has required structure.
        
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["maxim", "scene", "agent", "action"]
        for field in required_fields:
            if field not in case_input:
                raise ValueError(f"case_builder_input missing required field: {field}")
        
        # Validate nested structures
        if not isinstance(case_input["scene"], dict):
            raise ValueError("case_builder_input['scene'] must be a dict")
        
        if not isinstance(case_input["agent"], dict):
            raise ValueError("case_builder_input['agent'] must be a dict")
        
        if not isinstance(case_input["action"], dict):
            raise ValueError("case_builder_input['action'] must be a dict")
    
    def _test_universalizability(self, maxim: str, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test Categorical Imperative: Can the maxim be universalized?
        
        Kantian test: If everyone acted on this maxim, would it create a
        logical contradiction or undermine the very possibility of the action?
        
        Args:
            maxim: Organizational principle being questioned
            scene: Context (phenomenal constraints + noumenal duties)
        
        Returns:
            {
                "verdict": "FAILURE" | "PASS",
                "rationale": "Human-readable explanation citing Categorical Imperative"
            }
        """
        logger.info("universalizability_test_started", maxim=maxim)
        
        # MVP heuristic: Check for keywords indicating non-universalizable maxims
        # Production TODO: Use AI reasoning or more sophisticated heuristics
        
        non_universalizable_keywords = [
            "convenient", "when necessary", "optional", "discretionary",
            "at will", "if needed", "can be", "may be"
        ]
        
        maxim_lower = maxim.lower()
        is_problematic = any(keyword in maxim_lower for keyword in non_universalizable_keywords)
        
        if is_problematic:
            # Check if scene indicates fundamental rights/duties being violated
            noumenal_duties = scene.get("noumenal_duties", "")
            
            if noumenal_duties and len(noumenal_duties) > 0:
                verdict = "FAILURE"
                rationale = (
                    f"If all organizations applied the maxim '{maxim}', "
                    f"the practice would undermine itself and create logical contradiction. "
                    f"The stated duty ({noumenal_duties}) would cease to exist as a concept "
                    f"if exceptions were universalized. This violates the Categorical Imperative: "
                    f"'Act only according to that maxim whereby you can at the same time will "
                    f"that it should become a universal law.'"
                )
            else:
                verdict = "FAILURE"
                rationale = (
                    f"The maxim '{maxim}' contains conditional language suggesting "
                    f"inconsistent application. If universalized, this would create organizational "
                    f"chaos where no employee could rely on consistent standards. "
                    f"This violates the Categorical Imperative's requirement for universal law."
                )
        else:
            verdict = "PASS"
            rationale = (
                f"The maxim '{maxim}' can be consistently universalized without logical "
                f"contradiction. It represents a principle that could be applied "
                f"consistently across all similar situations, satisfying the Categorical Imperative."
            )
        
        logger.info("universalizability_test_complete", verdict=verdict)
        
        return {
            "verdict": verdict,
            "rationale": rationale
        }
    
    def _test_humanity_formula(self, agent: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test Humanity Formula: Is the employee treated as an end-in-themselves?
        
        Kantian test: Does the action treat the person merely as a means to an end,
        or as an end-in-themselves with inherent dignity and worth?
        
        Args:
            agent: Employee information (role, status)
            action: Action being analyzed (description)
        
        Returns:
            {
                "verdict": "VIOLATION" | "PASS",
                "rationale": "Human-readable explanation citing Humanity Formula"
            }
        """
        logger.info(
            "humanity_formula_test_started",
            agent_role=agent.get("role", "UNKNOWN")
        )
        
        # MVP heuristic: Check action description for dignity-violating keywords
        # Production TODO: Use AI reasoning or more sophisticated analysis
        
        action_description = action.get("description", "")
        action_lower = action_description.lower()
        
        dignity_violation_keywords = [
            "denied", "refused", "rejected", "dismissed", "ignored",
            "overlooked", "excluded", "prevented", "blocked"
        ]
        
        development_keywords = [
            "training", "development", "learning", "education",
            "progression", "advancement", "opportunity", "growth"
        ]
        
        has_denial = any(keyword in action_lower for keyword in dignity_violation_keywords)
        affects_development = any(keyword in action_lower for keyword in development_keywords)
        
        if has_denial and affects_development:
            verdict = "VIOLATION"
            role = agent.get("role", "Employee")
            rationale = (
                f"The {role} is treated as a mere means to organizational efficiency "
                f"rather than as an end-in-themselves with inherent dignity and professional "
                f"development rights. Denying professional development opportunities treats "
                f"the employee as interchangeable resource rather than as a person with "
                f"intrinsic worth and autonomous goals. This violates the Humanity Formula: "
                f"'Act in such a way that you treat humanity, whether in your own person or "
                f"in the person of any other, never merely as a means to an end, but always "
                f"at the same time as an end.'"
            )
        elif has_denial:
            verdict = "VIOLATION"
            rationale = (
                f"The action shows patterns of treating the employee instrumentally, "
                f"prioritizing organizational convenience over individual dignity. "
                f"This violates the Humanity Formula's requirement to treat all persons "
                f"as ends-in-themselves, not merely as means to organizational goals."
            )
        else:
            verdict = "PASS"
            rationale = (
                f"The action does not exhibit clear patterns of treating the employee "
                f"merely as a means. The employee's dignity and autonomous goals appear "
                f"to be recognized, satisfying the Humanity Formula."
            )
        
        logger.info("humanity_formula_test_complete", verdict=verdict)
        
        return {
            "verdict": verdict,
            "rationale": rationale
        }
    
    def _test_autonomy(self, action: Dict[str, Any], scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test Autonomy Principle: Is the action motivated by duty or external pressure?
        
        Kantian test: Does the action have moral worth (motivated by duty) or is it
        motivated by external pressures (inclination/hypothetical imperative)?
        
        Args:
            action: Action being analyzed (description, moral_worth)
            scene: Context including phenomenal pressures
        
        Returns:
            {
                "verdict": "VIOLATION" | "PASS",
                "rationale": "Human-readable explanation citing Autonomy Principle"
            }
        """
        logger.info("autonomy_test_started")
        
        # MVP heuristic: Check if action is motivated by external pressures vs. duty
        # Production TODO: Use AI reasoning for nuanced motivation analysis
        
        phenomenal_constraints = scene.get("phenomenal_constraints", "")
        noumenal_duties = scene.get("noumenal_duties", "")
        
        # Check for external pressure keywords in phenomenal constraints
        pressure_keywords = [
            "pressure", "cost", "budget", "efficiency", "convenient",
            "reduction", "constraint", "operational", "deadline"
        ]
        
        phenomenal_lower = phenomenal_constraints.lower()
        has_external_pressure = any(keyword in phenomenal_lower for keyword in pressure_keywords)
        
        # Check if noumenal duties were acknowledged
        has_duty_consideration = noumenal_duties and len(noumenal_duties) > 10
        
        if has_external_pressure and has_duty_consideration:
            verdict = "VIOLATION"
            rationale = (
                f"The action appears motivated by external pressures ({phenomenal_constraints}) "
                f"rather than by duty to professional standards ({noumenal_duties}). "
                f"Actions motivated by inclination (cost reduction, operational convenience) "
                f"rather than duty lack moral worth under Kantian ethics. "
                f"The Autonomy Principle requires that moral actions be motivated by "
                f"categorical imperatives (duty) rather than hypothetical imperatives "
                f"(if-then conditions based on desired outcomes)."
            )
        elif has_external_pressure:
            verdict = "VIOLATION"
            rationale = (
                f"The action shows evidence of motivation by external pressures "
                f"({phenomenal_constraints}) rather than moral duty. "
                f"This violates the Kantian Autonomy Principle, which requires that "
                f"truly moral actions be motivated by respect for moral law, not by "
                f"desired outcomes or external circumstances."
            )
        else:
            verdict = "PASS"
            rationale = (
                f"The action does not exhibit clear patterns of being motivated solely "
                f"by external pressures. There is evidence of consideration for moral duty, "
                f"satisfying the Autonomy Principle's requirement for categorical motivation."
            )
        
        logger.info("autonomy_test_complete", verdict=verdict)
        
        return {
            "verdict": verdict,
            "rationale": rationale
        }
    
    def _test_procedural_justice(self, scene: Dict[str, Any], agent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test Procedural Justice: Are organizational processes fair and transparent?
        
        Examines whether organizational procedures are:
        - Consistent (applied equally)
        - Transparent (reasoning is clear)
        - Appealable (recourse mechanisms exist)
        
        Args:
            scene: Context including organizational procedures
            agent: Employee information
        
        Returns:
            {
                "verdict": "FAILURE" | "PASS",
                "rationale": "Human-readable explanation citing procedural justice principles"
            }
        """
        logger.info("procedural_justice_test_started")
        
        # MVP heuristic: Check for procedural justice indicators
        # Production TODO: More sophisticated procedural analysis
        
        phenomenal = scene.get("phenomenal_constraints", "")
        noumenal = scene.get("noumenal_duties", "")
        
        # Combine scene context for analysis
        scene_context = f"{phenomenal} {noumenal}".lower()
        
        # Keywords indicating procedural justice violations
        violation_keywords = [
            "arbitrary", "inconsistent", "unclear", "no explanation",
            "denied without", "refused without", "no appeal", "no recourse"
        ]
        
        # Keywords indicating procedural justice
        justice_keywords = [
            "consistent", "transparent", "appeal", "review", "fair process",
            "explanation provided", "documented procedure"
        ]
        
        has_violations = any(keyword in scene_context for keyword in violation_keywords)
        has_justice_indicators = any(keyword in scene_context for keyword in justice_keywords)
        
        if has_violations or not has_justice_indicators:
            verdict = "FAILURE"
            rationale = (
                f"The organizational process lacks transparency, consistency, or appeal "
                f"mechanisms required by procedural justice principles. Procedural justice "
                f"requires that decisions affecting employees must: (1) follow consistent "
                f"and predictable rules, (2) provide clear reasoning and transparency, "
                f"(3) offer mechanisms for appeal and review, and (4) be applied equally "
                f"across similar cases. The absence of these elements represents a "
                f"systematic organizational ethics failure."
            )
        else:
            verdict = "PASS"
            rationale = (
                f"The organizational process exhibits procedural justice characteristics "
                f"including consistency, transparency, and fairness. The process satisfies "
                f"core procedural justice requirements for organizational ethics."
            )
        
        logger.info("procedural_justice_test_complete", verdict=verdict)
        
        return {
            "verdict": verdict,
            "rationale": rationale
        }
    
    def _generate_summary(
        self,
        universalizability: Dict[str, Any],
        humanity: Dict[str, Any],
        autonomy: Dict[str, Any],
        procedural_justice: Dict[str, Any]
    ) -> str:
        """
        Generate overall ethical assessment summary.
        
        Args:
            universalizability: Universalizability test result
            humanity: Humanity Formula test result
            autonomy: Autonomy test result
            procedural_justice: Procedural Justice test result
        
        Returns:
            Human-readable summary with zero technical jargon
        """
        # Count violations/failures
        violations = []
        
        if universalizability["verdict"] == "FAILURE":
            violations.append("Categorical Imperative")
        
        if humanity["verdict"] == "VIOLATION":
            violations.append("Humanity Formula")
        
        if autonomy["verdict"] == "VIOLATION":
            violations.append("Autonomy Principle")
        
        if procedural_justice["verdict"] == "FAILURE":
            violations.append("Procedural Justice")
        
        if len(violations) == 4:
            summary = (
                "This organizational practice violates all four formulations tested: "
                f"{', '.join(violations)}. This represents a systematic ethical failure "
                "requiring immediate remediation and comprehensive policy reform. "
                "The organization demonstrates a pattern of treating employees instrumentally, "
                "applying inconsistent principles, and failing to establish fair procedures."
            )
        elif len(violations) >= 2:
            summary = (
                f"This organizational practice violates {len(violations)} core ethical principles: "
                f"{', '.join(violations)}. This indicates significant ethical problems requiring "
                "corrective action and policy review. The violations suggest systemic issues "
                "in how the organization approaches employee treatment and organizational justice."
            )
        elif len(violations) == 1:
            summary = (
                f"This organizational practice violates one core ethical principle: "
                f"{violations[0]}. While some aspects of the situation satisfy ethical "
                "requirements, this violation indicates a need for targeted policy improvement "
                "and heightened awareness of ethical obligations in this area."
            )
        else:
            summary = (
                "This organizational practice satisfies all four Kantian ethical tests examined: "
                "Categorical Imperative, Humanity Formula, Autonomy Principle, and Procedural Justice. "
                "The organization demonstrates ethical treatment of employees and sound ethical "
                "principles in this situation."
            )
        
        logger.info(
            "summary_generated",
            violation_count=len(violations),
            violations=violations
        )
        
        return summary

