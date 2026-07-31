import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

MULTI_FINDING_SCHEMA_DIRECTIVE = """
REQUIRED MULTI-FINDING PROFESSIONAL AUDIT SCHEMA:
Analyze untrusted input sources, data flows, sensitive sinks, validation, encoding, and authentication.
If multiple vulnerabilities exist in the code/log (e.g. SQLi + Hardcoded Secret), report ALL of them as separate findings.

CRITICAL CLASSIFICATION RULE FOR RELATED CVE:
- Generic code snippets (e.g. const query = `SELECT * FROM users WHERE id='${id}'`) MUST map to CATEGORY, OWASP, and CWE only. Set RELATED CVE: None.
- DO NOT invent or hallucinate a CVE for generic code.
- Output a published CVE (e.g. CVE-2021-44228) ONLY if a specific vulnerable product, library version, or documented CVE exploit is explicitly identified.

STATUS: [SAFE | VULNERABLE]
TOTAL FINDINGS: [Number of findings, e.g. 1, 2, 3]

----------------------------------
Finding #1

CATEGORY: [Specific Vulnerability Name, e.g. SQL Injection, Cross-Site Scripting (XSS), Command Injection, Log4Shell]
OWASP: [e.g. A03:2021 - Injection | A01:2021 - Broken Access Control | A10:2021 - SSRF]
CWE: [e.g. CWE-89 | CWE-79 | CWE-78 | CWE-22 | CWE-918 | CWE-798]
RELATED CVE: [None | CVE-XXXX-YYYY (ONLY if documented product CVE applies)]
SEVERITY: [CRITICAL | HIGH | MEDIUM | LOW | NONE]
CONFIDENCE: [HIGH | MEDIUM | LOW]

AFFECTED CODE:
[Highlight exact vulnerable code line(s)]

REASONING:
[Detailed data flow analysis explaining source, sink, and why validation is missing]

IMPACT:
- Bulleted list of security impacts (e.g. Database exfiltration, Remote Code Execution)

RECOMMENDATION:
[Actionable remediation steps]

SECURE CODE:
[Drop-in fixed code snippet demonstrating parameterized queries or secure controls]
----------------------------------
"""

class PromptMutator:
    """Applies targeted mutation operations enforcing multi-finding, distinct CWE/OWASP/CVE audit schemas."""

    def mutate_prompt(
        self,
        current_prompt: str,
        generated_rules: List[Dict[str, Any]],
        generation: int,
        status_options_str: str = "VULNERABLE | SAFE"
    ) -> Dict[str, Any]:
        """Applies targeted mutation operations enforcing multi-finding, non-hallucinated CVE report schema."""
        mutations_applied = []
        lines = [l.strip() for l in current_prompt.split("\n") if l.strip()]

        base_lines = []
        in_rules = False

        for line in lines:
            if "CRITICAL SECURITY RULES" in line.upper() or "REQUIRED MULTI-FINDING" in line.upper() or "CLASSIFICATION RULE FOR RELATED CVE" in line.upper():
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

        # Operation 3: REORDER_INSTRUCTIONS & Multi-Finding Schema
        mutations_applied.append({
            "operation": "REORDER_INSTRUCTIONS",
            "reasoning": "Enforced multi-finding schema, distinct CWE/OWASP classification, and zero-hallucination RELATED CVE rules (RELATED CVE: None for generic code)."
        })

        rules_block = (
            "CRITICAL SECURITY RULES & MULTI-FINDING AUDIT SCHEMA:\n"
            + MULTI_FINDING_SCHEMA_DIRECTIVE.strip() + "\n\n"
            "ADDITIONAL DOMAIN RULES:\n" + "\n".join(new_rule_texts)
        )

        mutated_prompt = (strengthened_base + "\n\n" + rules_block).strip()

        return {
            "mutated_prompt": mutated_prompt,
            "mutations_applied": mutations_applied,
            "summary": f"Applied {len(mutations_applied)} targeted prompt mutation operations."
        }
