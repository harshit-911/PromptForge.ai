import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class RollbackManager:
    """Manages adaptive optimization intensity and rollbacks to best prompt versions."""

    def __init__(self):
        self.best_prompt = ""
        self.best_accuracy = -1.0
        self.best_f1 = -1.0
        self.best_version = "v1.0"
        self.consecutive_no_improvement = 0

    def evaluate_and_rollback(
        self,
        current_prompt: str,
        current_acc: float,
        current_f1: float,
        version: str
    ) -> Dict[str, Any]:
        """Evaluates metrics and rolls back to best prompt if performance decreased."""
        rolled_back = False

        if current_acc > self.best_accuracy:
            self.best_accuracy = current_acc
            self.best_f1 = current_f1
            self.best_prompt = current_prompt
            self.best_version = version
            self.consecutive_no_improvement = 0
            exploration_mode = "REDUCE_MUTATION_INTENSITY"
        elif current_acc == self.best_accuracy:
            self.consecutive_no_improvement += 1
            exploration_mode = "INCREASE_EXPLORATION"
        else:
            # Performance decreased! Rollback to best prompt!
            rolled_back = True
            self.consecutive_no_improvement += 1
            exploration_mode = "ROLLBACK_TO_BEST"
            logger.warning(f"RollbackManager: Accuracy dropped ({current_acc}% < {self.best_accuracy}%). Rolling back to {self.best_version}.")

        active_prompt = self.best_prompt if rolled_back else current_prompt

        return {
            "active_prompt": active_prompt,
            "best_prompt": self.best_prompt,
            "best_accuracy": self.best_accuracy,
            "best_version": self.best_version,
            "rolled_back": rolled_back,
            "exploration_mode": exploration_mode,
            "consecutive_no_improvement": self.consecutive_no_improvement
        }
