import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MemoryManager:
    """Maintains memory between optimization iterations to avoid repeating failed modifications."""

    def __init__(self):
        self.iteration_history = []
        self.successful_rules = set()
        self.failed_rules = set()
        self.previous_prompts = set()

    def record_iteration(self, iteration_data: Dict[str, Any]):
        """Records an iteration into memory."""
        prompt = iteration_data.get("prompt", "")
        self.previous_prompts.add(prompt)
        self.iteration_history.append(iteration_data)

        # Track rule success
        acc = iteration_data.get("accuracy", 0.0)
        rules = iteration_data.get("generated_rules", [])

        if acc > (self.iteration_history[0].get("accuracy", 0.0) if self.iteration_history else 0.0):
            for r in rules:
                self.successful_rules.add(r.get("rule_text"))
        else:
            for r in rules:
                self.failed_rules.add(r.get("rule_text"))

    def filter_failed_rules(self, proposed_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters out previously unsuccessful rules to prevent repeating failed modifications."""
        valid_rules = []
        for r in proposed_rules:
            text = r.get("rule_text")
            if text in self.failed_rules and text not in self.successful_rules:
                logger.info(f"MemoryManager: Skipping previously failed rule '{text}'")
                continue
            valid_rules.append(r)
        return valid_rules

    def get_memory_summary(self) -> Dict[str, Any]:
        return {
            "total_iterations_remembered": len(self.iteration_history),
            "successful_rules_count": len(self.successful_rules),
            "failed_rules_count": len(self.failed_rules)
        }
