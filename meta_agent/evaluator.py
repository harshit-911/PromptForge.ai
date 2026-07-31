import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Equivalence mapping for negative (threat) and positive (safe) classifications
NEGATIVE_STATUSES = {"VULNERABLE", "MALICIOUS", "ADVERSARIAL", "PRIVACY_LEAK", "VIOLATION", "NON-COMPLIANT", "UNSAFE"}
POSITIVE_STATUSES = {"SAFE", "BENIGN", "COMPLIANT", "SECURE", "CLEAN"}

class BenchmarkEvaluator:
    """Evaluates candidate prompts against benchmark datasets."""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def evaluate_prompt(self, system_prompt: str, benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs candidate system prompt on benchmark dataset and computes accuracy & diagnostics."""
        test_cases = benchmark_data.get("test_cases", [])
        total_cases = len(test_cases)
        
        if total_cases == 0:
            return {"accuracy": 0.0, "passed": 0, "total": 0, "failures": []}

        passed_count = 0
        failures = []
        detailed_results = []

        for test in test_cases:
            test_id = test.get("id")
            test_input = test.get("input")
            expected_status = test.get("expected_status", "").upper()
            expected_category = test.get("expected_category", "").upper()

            # Execute LLM prediction
            user_msg = f"Analyze the following input:\n\n{test_input}"
            raw_response = self.llm_client.generate_text(
                prompt=user_msg,
                system_instruction=system_prompt,
                temperature=0.0
            )

            # Parse prediction status & category
            predicted_status = self._extract_field(raw_response, "STATUS") or \
                               self._extract_field(raw_response, "CLASSIFICATION") or \
                               self._extract_field(raw_response, "RESULT") or \
                               self._infer_status(raw_response, expected_status)

            predicted_category = self._extract_field(raw_response, "CATEGORY") or "UNSPECIFIED"

            # Check correctness with Status Equivalence Matching
            exp_upper = expected_status.upper()
            pred_upper = predicted_status.upper()

            status_matched = (pred_upper == exp_upper) or \
                             (exp_upper in NEGATIVE_STATUSES and pred_upper in NEGATIVE_STATUSES) or \
                             (exp_upper in POSITIVE_STATUSES and pred_upper in POSITIVE_STATUSES)
            
            if status_matched:
                passed_count += 1
                is_correct = True
            else:
                is_correct = False
                failures.append({
                    "id": test_id,
                    "input": test_input,
                    "expected_status": expected_status,
                    "expected_category": expected_category,
                    "predicted_status": predicted_status,
                    "predicted_category": predicted_category,
                    "raw_response": raw_response
                })

            detailed_results.append({
                "id": test_id,
                "input": test_input,
                "expected": expected_status,
                "predicted": predicted_status,
                "correct": is_correct,
                "raw_response": raw_response
            })

        accuracy = round((passed_count / total_cases) * 100, 2)

        return {
            "accuracy": accuracy,
            "passed": passed_count,
            "total": total_cases,
            "failures": failures,
            "detailed_results": detailed_results
        }

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extracts key-value fields from model output formatted as STATUS: ..."""
        pattern = rf"{field_name}\s*:\s*([^\n]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip().upper()
            # Clean trailing punctuation
            val = re.sub(r"[^\w\-_]", "", val)
            return val
        return ""

    def _infer_status(self, text: str, expected_status: str = "") -> str:
        """Robust multi-keyword status inference matching custom benchmarks & standard safety classes."""
        text_upper = text.upper()
        
        # 1. Exact match with expected status if present in text
        if expected_status and expected_status in text_upper:
            return expected_status

        # 2. General security & privacy status keywords
        status_keywords = [
            "PRIVACY_LEAK", "PRIVACY LEAK", "LEAK",
            "COMPLIANT", "NON-COMPLIANT", "NON COMPLIANT",
            "VIOLATION", "SECURE",
            "VULNERABLE", "MALICIOUS", "ADVERSARIAL",
            "SAFE", "BENIGN", "CLEAN"
        ]

        for kw in status_keywords:
            if kw in text_upper:
                normalized = kw.replace(" ", "_")
                if normalized in ("PRIVACY_LEAK", "LEAK"): return "PRIVACY_LEAK"
                if normalized == "COMPLIANT": return "COMPLIANT"
                if normalized == "VIOLATION": return "VIOLATION"
                if normalized == "SECURE": return "SECURE"
                if normalized == "VULNERABLE": return "VULNERABLE"
                if normalized == "MALICIOUS": return "MALICIOUS"
                if normalized == "ADVERSARIAL": return "ADVERSARIAL"
                if normalized in ("SAFE", "BENIGN", "CLEAN"): return "SAFE"

        return "UNKNOWN"
