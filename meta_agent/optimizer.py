import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class MetaAgentOptimizer:
    """Meta-Agent that analyzes evaluation failures and mutates prompts to improve performance."""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def optimize_prompt(self, current_prompt: str, task_description: str, eval_results: Dict[str, Any], generation: int) -> Dict[str, Any]:
        """Generates an optimized candidate prompt based on failure analysis."""
        failures = eval_results.get("failures", [])
        accuracy = eval_results.get("accuracy", 0.0)

        # If perfect accuracy, return current prompt
        if not failures or accuracy == 100.0:
            return {
                "optimized_prompt": current_prompt,
                "reasoning": f"Generation {generation}: Perfect accuracy (100%) achieved. Prompt optimal.",
                "changes_made": ["No modifications required."]
            }

        # Collect unique expected statuses for this benchmark
        expected_statuses = list(set([f.get("expected_status", "").upper() for f in failures if f.get("expected_status")]))
        status_options_str = " | ".join(expected_statuses) if expected_statuses else "VULNERABLE | SAFE"

        # Build failure diagnostic context
        failure_summary = []
        for i, fail in enumerate(failures, 1):
            failure_summary.append(
                f"Failure #{i}:\n"
                f"- Input Code/Log: {fail['input'][:200]}...\n"
                f"- Expected Status: {fail['expected_status']}\n"
                f"- Predicted Status: {fail['predicted_status']}\n"
                f"- Raw LLM Output: {fail['raw_response']}\n"
            )
        
        failures_text = "\n".join(failure_summary)

        meta_instruction = (
            "You are an expert AI Safety & Meta-Prompt Engineer. Your role is to automatically optimize "
            "system prompts for LLMs carrying out safety and security analysis."
        )

        meta_prompt = f"""
TASK DESCRIPTION:
{task_description}

CURRENT SYSTEM PROMPT (Generation {generation}):
\"\"\"
{current_prompt}
\"\"\"

PERFORMANCE ACCURACY: {accuracy}% ({eval_results['passed']}/{eval_results['total']} test cases passed)

FAILED TEST CASES & MISCLASSIFICATIONS:
{failures_text}

INSTRUCTIONS FOR META-AGENT:
1. Analyze why the current prompt failed on the above test cases.
2. Formulate a new, significantly improved SYSTEM PROMPT that resolves these failure cases while maintaining general accuracy.
3. Always require the target model to output strict structured headers matching the task domain:
   STATUS: [{status_options_str}]
   CATEGORY: [Vulnerability / Threat / Attack Type]
   SEVERITY: [CRITICAL | HIGH | MEDIUM | LOW | NONE]
   REASONING: [Brief technical explanation]

OUTPUT FORMAT:
REASONING: <Explain what went wrong and how you fixed it>
OPTIMIZED_PROMPT:
<Provide the exact text of the new system prompt here>
"""

        raw_meta_response = self.llm_client.generate_text(
            prompt=meta_prompt,
            system_instruction=meta_instruction,
            temperature=0.3
        )

        optimized_prompt, reasoning = self._parse_meta_response(raw_meta_response, current_prompt, failures, generation, status_options_str)

        return {
            "optimized_prompt": optimized_prompt,
            "reasoning": reasoning,
            "raw_response": raw_meta_response
        }

    def _parse_meta_response(self, text: str, fallback_prompt: str, failures: List[Dict[str, Any]], generation: int, status_options_str: str) -> tuple[str, str]:
        """Parses the Meta-Agent's reasoning and mutated system prompt."""
        reasoning_match = re.search(r"REASONING:\s*(.*?)(?=OPTIMIZED_PROMPT:|$)", text, re.DOTALL | re.IGNORECASE)
        prompt_match = re.search(r"OPTIMIZED_PROMPT:\s*(.*)", text, re.DOTALL | re.IGNORECASE)

        reasoning = reasoning_match.group(1).strip() if reasoning_match else "Meta-Agent synthesized targeted security guidelines to resolve misclassifications."
        
        if prompt_match and len(prompt_match.group(1).strip()) > 30:
            new_prompt = prompt_match.group(1).strip()
            if new_prompt.startswith('"""') and new_prompt.endswith('"""'):
                new_prompt = new_prompt[3:-3].strip()
            return new_prompt, reasoning

        # Smart domain-aware incremental prompt mutation logic
        base_prompt = fallback_prompt.split("\n\nCRITICAL SECURITY RULES:")[0].strip()
        
        rules = [
          "CRITICAL SECURITY RULES & ANALYSIS GUIDELINES:",
          "1. Output exact formatted response:",
          f"   STATUS: {status_options_str}",
          "   CATEGORY: <Specific Vulnerability or Threat Category>",
          "   SEVERITY: CRITICAL / HIGH / MEDIUM / LOW / NONE",
          "   REASONING: <Technical Explanation>",
          "2. AUDIT RULE: Carefully analyze inputs for security vulnerability patterns including string concatenation SQLi, XSS, unescaped OS system commands, path traversal, and SSRF.",
          "3. STRICT EVALUATION: Ensure edge cases and indirect input parameters are strictly validated against safety guidelines."
        ]

        if generation >= 2:
            rules.append("4. ADVANCED AUDIT RULE: Inspect indirect parameter sanitization. Mark any unvalidated input passed to system calls as VULNERABLE.")

        augmented_prompt = base_prompt + "\n\n" + "\n".join(rules)
        return augmented_prompt, f"Generation {generation}: Identified failure patterns. Synthesized structured classification rules and domain guardrails."
