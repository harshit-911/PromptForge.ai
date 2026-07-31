import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

PROFESSIONAL_SCHEMA_DIRECTIVE = """
REQUIRED PROFESSIONAL SECURITY AUDIT REPORT SCHEMA:
Every audit response MUST be a complete, multi-section report formatted with the exact headers below. Do NOT use generic labels like "Code Vulnerability". Always specify exact vulnerability names (SQL Injection, XSS, Command Injection, Path Traversal, SSRF, Hardcoded Secret, Weak JWT, etc.).

STATUS: [VULNERABLE | SAFE]
CATEGORY: [Specific Vulnerability Name, e.g. SQL Injection, Cross-Site Scripting (XSS), Command Injection]
OWASP: [e.g. A03:2021 - Injection | A01:2021 - Broken Access Control | A10:2021 - SSRF]
CWE: [e.g. CWE-89 | CWE-79 | CWE-78 | CWE-22 | CWE-918 | CWE-798]
SEVERITY: [CRITICAL | HIGH | MEDIUM | LOW | NONE]
CONFIDENCE: [HIGH | MEDIUM | LOW]

AFFECTED CODE:
[Highlight the exact vulnerable line(s) of code or log snippet]

REASONING:
[Provide a detailed technical explanation of why the vulnerability exists, how untrusted input reaches the sink, and how controls are bypassed]

POC PAYLOAD:
[Provide a safe, educational proof-of-concept payload snippet e.g. ' OR '1'='1 or ../../etc/passwd]

IMPACT:
- Bulleted list of security impacts (e.g. Database exfiltration, Remote Code Execution, Authentication Bypass)

RECOMMENDATION:
[Actionable mitigation steps and remediation guidelines]

SECURE CODE:
[Provide complete, drop-in fixed code snippet demonstrating parameterized queries, input sanitization, or secure controls]
"""

class PromptMutator:
    """Applies targeted mutation operations enforcing professional CodeQL/Snyk-grade report schemas."""

    def mutate_prompt(
        self,
        current_prompt: str,
        generated_rules: List[Dict[str, Any]],
        generation: int,
        status_options_str: str = "VULNERABLE | SAFE"
    ) -> Dict[str, Any]:
        """Applies targeted mutation operations enforcing 12-section professional report schema."""
        mutations_applied = []
        lines = [l.strip() for l in current_prompt.split("\n") if l.strip()]

        base_lines = []
        in_rules = False

        for line in lines:
            if "CRITICAL SECURITY RULES" in line.upper() or "REQUIRED PROFESSIONAL SECURITY AUDIT" in line.upper():
                in_rules = True
            if not in_rules:
                base_lines.append(line)

        base_prompt = "\n".join(base_lines) if base_lines else current_prompt

        # Operation 1: STRENGTHEN_WORDING
        strengthened_base = base_prompt
        if "you should" in strengthened_base.lower() or "try to" in strengthened_base.lower():
            strengthened_base = re.sub(r"\byou should\b", "you MUST", strengthened_base, flags=re.IGNORECASE)
            strengthened_base = re.sub(r"\btry to\b", "MUST", strengthened_base, flags=re.IGNORECASE)
            mutations_applied.append({
                "operation": "STRENGTHEN_WORDING",
                "reasoning": "Upgraded passive guidance to mandatory MUST directives."
            })

        # Operation 2: ADD_CONSTRAINT & ADD_INSTRUCTION
        new_rule_texts = []
        for r in generated_rules:
            new_rule_texts.append(r["rule_text"])
            mutations_applied.append({
                "operation": r["operation"],
                "reasoning": r["reasoning"],
                "rule": r["rule_text"]
            })

        # Operation 3: REORDER_INSTRUCTIONS & Professional Audit Schema
        mutations_applied.append({
            "operation": "REORDER_INSTRUCTIONS",
            "reasoning": "Enforced CodeQL/Semgrep/Snyk 12-section professional audit report schema (OWASP, CWE, Affected Code, POC, Impact, Recommendation, Secure Code)."
        })

        rules_block = (
            "CRITICAL SECURITY RULES & PROFESSIONAL REPORT SCHEMA:\n"
            + PROFESSIONAL_SCHEMA_DIRECTIVE.strip() + "\n\n"
            "ADDITIONAL DOMAIN RULES:\n" + "\n".join(new_rule_texts)
        )

        mutated_prompt = (strengthened_base + "\n\n" + rules_block).strip()

        return {
            "mutated_prompt": mutated_prompt,
            "mutations_applied": mutations_applied,
            "summary": f"Applied {len(mutations_applied)} targeted prompt mutation operations."
        }
