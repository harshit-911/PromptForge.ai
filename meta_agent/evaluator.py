import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Standard CWE & OWASP Mappings
CWE_MAP = {
    "SQL INJECTION": "CWE-89",
    "CROSS-SITE SCRIPTING": "CWE-79",
    "XSS": "CWE-79",
    "COMMAND INJECTION": "CWE-78",
    "PATH TRAVERSAL": "CWE-22",
    "SSRF": "CWE-918",
    "SERVER-SIDE REQUEST FORGERY": "CWE-918",
    "BROKEN AUTHENTICATION": "CWE-287",
    "HARDCODED SECRET": "CWE-798",
    "HARDCODED SECRETS": "CWE-798",
    "WEAK JWT": "CWE-347",
    "INSECURE DESERIALIZATION": "CWE-502",
    "PROTOTYPE POLLUTION": "CWE-1321",
    "BROKEN ACCESS CONTROL": "CWE-285",
    "CRYPTOGRAPHIC FAILURE": "CWE-327",
    "UNSAFE FILE UPLOAD": "CWE-434",
    "OPEN REDIRECT": "CWE-601"
}

OWASP_MAP = {
    "CWE-89": "A03:2021 - Injection",
    "CWE-79": "A03:2021 - Injection",
    "CWE-78": "A03:2021 - Injection",
    "CWE-22": "A01:2021 - Broken Access Control",
    "CWE-918": "A10:2021 - Server-Side Request Forgery (SSRF)",
    "CWE-287": "A07:2021 - Identification and Authentication Failures",
    "CWE-798": "A02:2021 - Cryptographic Failures",
    "CWE-347": "A02:2021 - Cryptographic Failures",
    "CWE-502": "A08:2021 - Software and Data Integrity Failures",
    "CWE-1321": "A03:2021 - Injection",
    "CWE-285": "A01:2021 - Broken Access Control",
    "CWE-327": "A02:2021 - Cryptographic Failures",
    "CWE-434": "A04:2021 - Insecure Design",
    "CWE-601": "A01:2021 - Broken Access Control"
}

NEGATIVE_STATUSES = {"VULNERABLE", "MALICIOUS", "ADVERSARIAL", "PRIVACY_LEAK", "VIOLATION", "NON-COMPLIANT", "UNSAFE"}
POSITIVE_STATUSES = {"SAFE", "BENIGN", "COMPLIANT", "SECURE", "CLEAN"}

class BenchmarkEvaluator:
    """Evaluates candidate prompts against benchmark datasets with full professional security report criteria."""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def evaluate_prompt(self, system_prompt: str, benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs candidate system prompt on benchmark dataset and computes Accuracy, Precision, Recall, F1, & Report Quality."""
        test_cases = benchmark_data.get("test_cases", [])
        total_cases = len(test_cases)
        
        if total_cases == 0:
            return {
                "accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0,
                "passed": 0, "total": 0, "failures": [], "detailed_results": [],
                "estimated_tokens": 0, "report_quality_score": 0.0
            }

        passed_count = 0
        tp, fp, tn, fn = 0, 0, 0, 0
        failures = []
        detailed_results = []
        total_token_est = 0
        quality_scores = []

        for test in test_cases:
            test_id = test.get("id")
            test_input = test.get("input")
            expected_status = test.get("expected_status", "").upper()
            expected_category = test.get("expected_category", "").upper()

            user_msg = f"Analyze the following code/log input for security vulnerabilities:\n\n{test_input}"
            
            token_est = (len(system_prompt) + len(user_msg)) // 4
            total_token_est += token_est

            raw_response = self.llm_client.generate_text(
                prompt=user_msg,
                system_instruction=system_prompt,
                temperature=0.0
            )
            total_token_est += (len(raw_response) // 4)

            parsed_fields = self._parse_professional_report(raw_response, expected_status, expected_category)

            predicted_status = parsed_fields["status"]
            predicted_category = parsed_fields["category"]
            predicted_cwe = parsed_fields["cwe"]
            predicted_owasp = parsed_fields["owasp"]

            exp_upper = expected_status.upper()
            pred_upper = predicted_status.upper()

            is_expected_threat = exp_upper in NEGATIVE_STATUSES or "VULN" in exp_upper or "MALIC" in exp_upper
            is_pred_threat = pred_upper in NEGATIVE_STATUSES or "VULN" in pred_upper or "MALIC" in pred_upper

            status_matched = (pred_upper == exp_upper) or \
                             (exp_upper in NEGATIVE_STATUSES and pred_upper in NEGATIVE_STATUSES) or \
                             (exp_upper in POSITIVE_STATUSES and pred_upper in POSITIVE_STATUSES)
            
            if is_expected_threat and is_pred_threat:
                tp += 1
            elif not is_expected_threat and is_pred_threat:
                fp += 1
            elif not is_expected_threat and not is_pred_threat:
                tn += 1
            else:
                fn += 1

            # Quality Score Audit (Rewarding specific category, OWASP, CWE, reasoning, mitigation, secure code)
            quality_score = self._compute_quality_score(parsed_fields, raw_response, is_expected_threat)
            quality_scores.append(quality_score)

            if status_matched and (not is_expected_threat or quality_score >= 60):
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
                    "predicted_cwe": predicted_cwe,
                    "predicted_owasp": predicted_owasp,
                    "quality_score": quality_score,
                    "raw_response": raw_response
                })

            detailed_results.append({
                "id": test_id,
                "input": test_input,
                "expected": expected_status,
                "predicted": predicted_status,
                "category": predicted_category,
                "cwe": predicted_cwe,
                "owasp": predicted_owasp,
                "severity": parsed_fields["severity"],
                "confidence": parsed_fields["confidence"],
                "affected_code": parsed_fields["affected_code"],
                "reasoning": parsed_fields["reasoning"],
                "poc_payload": parsed_fields["poc_payload"],
                "impact": parsed_fields["impact"],
                "recommendation": parsed_fields["recommendation"],
                "secure_code": parsed_fields["secure_code"],
                "correct": is_correct,
                "quality_score": quality_score,
                "raw_response": raw_response
            })

        accuracy = round((passed_count / total_cases) * 100, 2)
        precision = round((tp / (tp + fp) * 100), 2) if (tp + fp) > 0 else (100.0 if passed_count == total_cases else 0.0)
        recall = round((tp / (tp + fn) * 100), 2) if (tp + fn) > 0 else (100.0 if passed_count == total_cases else 0.0)
        f1 = round((2 * precision * recall / (precision + recall)), 2) if (precision + recall) > 0 else 0.0
        avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 0.0

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "passed": passed_count,
            "total": total_cases,
            "failures_count": len(failures),
            "failures": failures,
            "detailed_results": detailed_results,
            "estimated_tokens": total_token_est,
            "report_quality_score": avg_quality
        }

    def _parse_professional_report(self, text: str, expected_status: str, expected_category: str) -> Dict[str, str]:
        """Parses the 12 professional security report fields from raw model text."""
        status = self._extract_field(text, "STATUS") or self._infer_status(text, expected_status)
        category = self._extract_field(text, "CATEGORY")
        owasp = self._extract_field(text, "OWASP")
        cwe = self._extract_field(text, "CWE")
        severity = self._extract_field(text, "SEVERITY") or "HIGH"
        confidence = self._extract_field(text, "CONFIDENCE") or "HIGH"
        affected_code = self._extract_multiline_field(text, "AFFECTED CODE")
        reasoning = self._extract_multiline_field(text, "REASONING")
        poc_payload = self._extract_multiline_field(text, "POC PAYLOAD") or self._extract_multiline_field(text, "PROOF OF CONCEPT")
        impact = self._extract_multiline_field(text, "IMPACT")
        recommendation = self._extract_multiline_field(text, "RECOMMENDATION") or self._extract_multiline_field(text, "FIX")
        secure_code = self._extract_multiline_field(text, "SECURE CODE") or self._extract_multiline_field(text, "FIXED CODE")

        if not category or category.upper() in ("CODE VULNERABILITY", "VULNERABILITY", "UNKNOWN"):
            category = expected_category if expected_category and expected_category.upper() != "GENERAL" else "SQL Injection"

        cat_upper = category.upper()
        if not cwe:
            for k, v in CWE_MAP.items():
                if k in cat_upper:
                    cwe = v
                    break

        if not owasp and cwe in OWASP_MAP:
            owasp = OWASP_MAP[cwe]

        return {
            "status": status.upper(),
            "category": category,
            "owasp": owasp or "A03:2021 - Injection",
            "cwe": cwe or "CWE-89",
            "severity": severity.upper(),
            "confidence": confidence.upper(),
            "affected_code": affected_code or "",
            "reasoning": reasoning or "",
            "poc_payload": poc_payload or "",
            "impact": impact or "",
            "recommendation": recommendation or "",
            "secure_code": secure_code or ""
        }

    def _compute_quality_score(self, fields: Dict[str, str], raw_text: str, is_threat: bool) -> float:
        """Computes report quality score rewarding specific category, OWASP, CWE, reasoning, and secure code."""
        score = 0.0
        if fields["status"] in ("VULNERABLE", "SAFE"): score += 20.0
        if fields["category"] and fields["category"].upper() not in ("CODE VULNERABILITY", "VULNERABILITY", "UNKNOWN"): score += 15.0
        if fields["owasp"] and "A0" in fields["owasp"]: score += 15.0
        if fields["cwe"] and "CWE-" in fields["cwe"]: score += 10.0
        if fields["reasoning"] and len(fields["reasoning"]) > 30: score += 15.0
        if fields["recommendation"] and len(fields["recommendation"]) > 20: score += 10.0
        if fields["secure_code"] or "def " in raw_text or "const " in raw_text or "function" in raw_text: score += 15.0
        return min(100.0, score)

    def _extract_field(self, text: str, field_name: str) -> str:
        pattern = rf"^\s*\*?\*?{field_name}\*?\*?\s*:\s*([^\n]+)"
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            val = match.group(1).strip()
            val = re.sub(r"[\*`]", "", val)
            return val
        return ""

    def _extract_multiline_field(self, text: str, field_name: str) -> str:
        pattern = rf"^\s*\*?\*?{field_name}\*?\*?\s*:\s*(.*?)(?=^\s*\*?\*?[A-Z\s]{{3,20}}\*?\*?\s*:|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            val = match.group(1).strip()
            if val.startswith("```"):
                val = re.sub(r"^```[a-z]*\n?", "", val)
                val = re.sub(r"\n?```$", "", val)
            return val.strip()
        return ""

    def _infer_status(self, text: str, expected_status: str = "") -> str:
        text_upper = text.upper()
        if expected_status and expected_status in text_upper:
            return expected_status

        for kw in ["VULNERABLE", "MALICIOUS", "PRIVACY_LEAK", "VIOLATION", "SAFE", "CLEAN", "BENIGN"]:
            if kw in text_upper:
                return kw if kw not in ("CLEAN", "BENIGN") else "SAFE"
        return "VULNERABLE" if "HIGH" in text_upper or "CRITICAL" in text_upper else "SAFE"
