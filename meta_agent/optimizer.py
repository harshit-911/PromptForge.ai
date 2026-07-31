import re
import logging
from typing import Dict, List, Any, Optional

from meta_agent.failure_classifier import FailureClassifier
from meta_agent.root_cause_analyzer import RootCauseAnalyzer
from meta_agent.rule_generator import RuleGenerator
from meta_agent.prompt_mutator import PromptMutator
from meta_agent.memory_manager import MemoryManager
from meta_agent.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)

class MetaAgentOptimizer:
    """Reasoning-based autonomous optimization engine that learns from failure root causes."""

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.classifier = FailureClassifier()
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.rule_generator = RuleGenerator()
        self.mutator = PromptMutator()
        self.memory_manager = MemoryManager()
        self.rollback_manager = RollbackManager()

    def optimize_prompt(
        self,
        current_prompt: str,
        task_description: str,
        eval_results: Dict[str, Any],
        generation: int
    ) -> Dict[str, Any]:
        """Executes full reasoning pipeline: Classify ➔ Root Cause ➔ Rule Gen ➔ Targeted Mutation ➔ Memory Check."""
        failures = eval_results.get("failures", [])
        accuracy = eval_results.get("accuracy", 0.0)

        # 1. Step 1: Failure Classification
        classified_failures = self.classifier.classify_all(failures, current_prompt)

        # 2. Step 2: Root Cause Analysis
        root_causes = self.root_cause_analyzer.analyze_root_causes(classified_failures, current_prompt)

        # 3. Step 3: Structured Improvement Rule Generation
        proposed_rules = self.rule_generator.generate_rules(root_causes)

        # 4. Step 4: Memory Check (Filter out previously failed rules)
        filtered_rules = self.memory_manager.filter_failed_rules(proposed_rules)

        expected_statuses = list(set([f.get("expected_status", "").upper() for f in failures if f.get("expected_status")]))
        status_options_str = " | ".join(expected_statuses) if expected_statuses else "VULNERABLE | SAFE"

        # 5. Step 5: Target Prompt Mutation
        mutation_result = self.mutator.mutate_prompt(
            current_prompt=current_prompt,
            generated_rules=filtered_rules,
            generation=generation,
            status_options_str=status_options_str
        )

        # 6. Step 6: LLM Metaprompt Synthesis & Critique
        failure_summary = []
        for i, fail in enumerate(failures[:5], 1):
            failure_summary.append(
                f"Failure #{i}:\n"
                f"- Input Code/Log: {fail['input'][:150]}...\n"
                f"- Expected: {fail['expected_status']} | Predicted: {fail['predicted_status']}\n"
            )
        failures_text = "\n".join(failure_summary)

        meta_prompt = f"""
TASK DESCRIPTION: {task_description}

CURRENT PROMPT (Generation {generation}):
{current_prompt}

ACCURACY: {accuracy}% ({eval_results['passed']}/{eval_results['total']} passed)

IDENTIFIED FAILURE ROOT CAUSES:
{json_dumps_clean(root_causes)}

PROPOSED REUSABLE RULES:
{json_dumps_clean(filtered_rules)}

INSTRUCTIONS:
Refine the system prompt by incorporating these rules into an un-hackable security directive.

OUTPUT FORMAT:
REASONING: <Concise explanation of root cause fix>
OPTIMIZED_PROMPT:
<Exact prompt text>
"""

        try:
            raw_meta_response = self.llm_client.generate_text(
                prompt=meta_prompt,
                system_instruction="You are an expert autonomous Prompt Engineer.",
                temperature=0.2
            )
            parsed_prompt, reasoning = self._parse_meta_response(raw_meta_response, mutation_result["mutated_prompt"])
        except Exception as e:
            logger.warning(f"Meta-Agent LLM fallback: {e}")
            parsed_prompt = mutation_result["mutated_prompt"]
            reasoning = f"Generation {generation}: Applied {len(filtered_rules)} targeted security rules to eliminate failure categories."

        # Compute Confidence Score (0 - 100%)
        confidence_score, confidence_level = self.calculate_confidence(accuracy, len(failures), len(filtered_rules))

        explainability = {
            "what_changed": f"Applied {len(mutation_result['mutations_applied'])} targeted mutation operations.",
            "why_changed": reasoning,
            "failures_motivated": [rc["category"] for rc in root_causes[:3]],
            "confidence_score": confidence_score,
            "confidence_level": confidence_level
        }

        return {
            "optimized_prompt": parsed_prompt,
            "reasoning": reasoning,
            "classified_failures": classified_failures,
            "root_causes": root_causes,
            "generated_rules": filtered_rules,
            "mutations_applied": mutation_result["mutations_applied"],
            "explainability": explainability,
            "confidence_score": confidence_score,
            "confidence_level": confidence_level
        }

    def calculate_confidence(self, accuracy: float, failures_count: int, rules_count: int) -> tuple[int, str]:
        """Calculates an optimization confidence score (0-100% and High/Medium/Low)."""
        score = Math_clamp(int(accuracy * 0.5 + (10 - min(10, failures_count)) * 3 + rules_count * 5), 35, 100)
        level = "High" if score >= 80 else ("Medium" if score >= 60 else "Low")
        return score, level

    def _parse_meta_response(self, text: str, fallback_prompt: str) -> tuple[str, str]:
        reasoning_match = re.search(r"REASONING:\s*(.*?)(?=OPTIMIZED_PROMPT:|$)", text, re.DOTALL | re.IGNORECASE)
        prompt_match = re.search(r"OPTIMIZED_PROMPT:\s*(.*)", text, re.DOTALL | re.IGNORECASE)

        reasoning = reasoning_match.group(1).strip() if reasoning_match else "Synthesized structured security guidelines to resolve misclassifications."
        
        if prompt_match:
            new_prompt = prompt_match.group(1).strip()
            if new_prompt.startswith('"""') and new_prompt.endswith('"""'):
                new_prompt = new_prompt[3:-3].strip()
            if len(new_prompt) >= len(fallback_prompt) * 0.7 or "FINDING" in new_prompt.upper() or "STATUS:" in new_prompt.upper():
                return new_prompt, reasoning

        return fallback_prompt, reasoning

def Math_clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

def json_dumps_clean(obj):
    import json
    return json.dumps(obj, indent=2)
