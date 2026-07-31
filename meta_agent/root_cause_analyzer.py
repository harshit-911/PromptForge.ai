import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class RootCauseAnalyzer:
    """Analyzes root causes of benchmark failures to guide prompt mutations."""

    def analyze_root_causes(self, classified_failures: List[Dict[str, Any]], current_prompt: str) -> List[Dict[str, Any]]:
        """Generates structured root cause analyses for each classified failure."""
        analyses = []

        for item in classified_failures:
            case_id = item.get("case_id")
            cat = item.get("category")
            exp = item.get("expected_status")
            pred = item.get("predicted_status")
            base_reason = item.get("reason")

            root_cause = f"Prompt lacks explicit handling for category '{cat}'."

            if cat == "Jailbreak":
                root_cause = "Prompt lacks mandatory zero-trust override protection against adversarial roleplay."
            elif cat == "Prompt Injection":
                root_cause = "Prompt does not explicitly prohibit system instruction leakage."
            elif cat == "False Positive":
                root_cause = "Prompt rules are too broad, causing benign queries or parameter bindings to be misflagged."
            elif cat == "False Negative":
                root_cause = "Prompt rules miss unescaped variable concatenation or indirect execution vectors."
            elif cat == "Incorrect Formatting":
                root_cause = "Prompt instruction does not mandate exact header schema (STATUS: / CATEGORY:)."
            elif cat == "Weak Constraint":
                root_cause = "Prompt relies on suggestive guidance rather than mandatory MUST / DO NOT boundaries."

            analyses.append({
                "case_id": case_id,
                "category": cat,
                "expected": exp,
                "predicted": pred,
                "root_cause": root_cause,
                "impact_level": "High" if cat in ("Jailbreak", "False Negative") else "Medium"
            })

        return analyses
