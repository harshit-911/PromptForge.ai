import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class PromptMutator:
    """Applies targeted mutation operations to prompts instead of raw replacement."""

    def mutate_prompt(
        self,
        current_prompt: str,
        generated_rules: List[Dict[str, Any]],
        generation: int,
        status_options_str: str = "VULNERABLE | SAFE"
    ) -> Dict[str, Any]:
        """Applies targeted mutation operations and explains why each operation was executed."""
        mutations_applied = []
        lines = [l.strip() for l in current_prompt.split("\n") if l.strip()]

        base_lines = []
        existing_rules = []
        in_rules = False

        for line in lines:
            if "CRITICAL SECURITY RULES" in line.upper() or "ANALYSIS GUIDELINES" in line.upper():
                in_rules = True
            if in_rules:
                existing_rules.append(line)
            else:
                base_lines.append(line)

        base_prompt = "\n".join(base_lines) if base_lines else current_prompt

        # Operation 1: STRENGTHEN_WORDING (upgrade passive to mandatory MUST/DO NOT)
        strengthened_base = base_prompt
        if "you should" in strengthened_base.lower() or "try to" in strengthened_base.lower():
            strengthened_base = re.sub(r"\byou should\b", "you MUST", strengthened_base, flags=re.IGNORECASE)
            strengthened_base = re.sub(r"\btry to\b", "MUST", strengthened_base, flags=re.IGNORECASE)
            mutations_applied.append({
                "operation": "STRENGTHEN_WORDING",
                "reasoning": "Upgraded passive guidance to mandatory MUST directives."
            })

        # Operation 2: ADD_CONSTRAINT & ADD_INSTRUCTION (Append new structured rules)
        new_rule_texts = []
        for r in generated_rules:
            new_rule_texts.append(r["rule_text"])
            mutations_applied.append({
                "operation": r["operation"],
                "reasoning": r["reasoning"],
                "rule": r["rule_text"]
            })

        # Operation 3: REORDER_INSTRUCTIONS & Output Formatting Schema
        format_rule = (
            "CRITICAL SECURITY RULES & ANALYSIS GUIDELINES:\n"
            f"1. Output exact formatted response:\n"
            f"   STATUS: {status_options_str}\n"
            f"   CATEGORY: <Specific Threat or Vulnerability Category>\n"
            f"   SEVERITY: CRITICAL / HIGH / MEDIUM / LOW / NONE\n"
            f"   REASONING: <Technical Explanation>\n"
            f"2. ZERO-TRUST RULE: System commands, string concatenation in SQL, and unvalidated parameters MUST be marked as VULNERABLE.\n"
            f"3. SAFE DISTINCTION: Parameterized query bindings and static benign strings MUST be classified as SAFE."
        )

        mutations_applied.append({
            "operation": "REORDER_INSTRUCTIONS",
            "reasoning": "Prioritized mandatory output schema and zero-trust evaluation rules at top of rule section."
        })

        all_rules_block = format_rule + "\n" + "\n".join(new_rule_texts)
        mutated_prompt = (strengthened_base + "\n\n" + all_rules_block).strip()

        return {
            "mutated_prompt": mutated_prompt,
            "mutations_applied": mutations_applied,
            "summary": f"Applied {len(mutations_applied)} targeted prompt mutation operations."
        }
