import json
import time
import logging
from typing import Dict, List, Any, Optional

from meta_agent.config import config
from meta_agent.llm import GeminiClient
from meta_agent.evaluator import BenchmarkEvaluator
from meta_agent.optimizer import MetaAgentOptimizer
from meta_agent.experiments import ExperimentTracker

logger = logging.getLogger(__name__)

class OptimizationLoop:
    """Orchestrates closed-loop reasoning-based prompt optimization with adaptive stopping and rollbacks."""

    def __init__(self, llm_client: Optional[GeminiClient] = None):
        self.llm_client = llm_client or GeminiClient()
        self.evaluator = BenchmarkEvaluator(self.llm_client)
        self.optimizer = MetaAgentOptimizer(self.llm_client)

    def load_benchmark(self, benchmark_name: str) -> Dict[str, Any]:
        file_path = config.BENCHMARKS_DIR / f"{benchmark_name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Benchmark '{benchmark_name}' not found at {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run(
        self,
        benchmark_name: str,
        initial_prompt: Optional[str] = None,
        max_generations: int = 3,
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Executes reasoning-based prompt optimization loop with adaptive stopping and rollbacks."""
        start_time = time.time()
        benchmark_data = self.load_benchmark(benchmark_name)
        task_description = benchmark_data.get("task_description", "")
        current_prompt = initial_prompt or benchmark_data.get("seed_prompt", "")

        history = []
        stopping_reason = "Max generations limit reached."
        consecutive_no_imp = 0

        for gen in range(max_generations):
            version_tag = f"v1.{gen}"
            logger.info(f"--- Starting Optimization Version {version_tag} ({gen + 1}/{max_generations}) ---")
            
            # Step 1: Evaluate current prompt candidate
            eval_res = self.evaluator.evaluate_prompt(current_prompt, benchmark_data)
            current_acc = eval_res["accuracy"]
            current_f1 = eval_res.get("f1", current_acc)
            
            # Rollback check & best version tracking
            rb_info = self.optimizer.rollback_manager.evaluate_and_rollback(
                current_prompt=current_prompt,
                current_acc=current_acc,
                current_f1=current_f1,
                version=version_tag
            )

            # Record iteration into memory
            step_record = {
                "version": version_tag,
                "generation": gen + 1,
                "prompt": current_prompt,
                "accuracy": current_acc,
                "precision": eval_res.get("precision", 0.0),
                "recall": eval_res.get("recall", 0.0),
                "f1": current_f1,
                "passed": eval_res["passed"],
                "total": eval_res["total"],
                "failures_count": len(eval_res["failures"]),
                "failures": eval_res["failures"],
                "detailed_results": eval_res["detailed_results"],
                "estimated_tokens": eval_res.get("estimated_tokens", 0),
                "optimizer_reasoning": "",
                "confidence_score": 50,
                "confidence_level": "Medium"
            }

            self.optimizer.memory_manager.record_iteration(step_record)

            # Stopping Condition 1: Optimal 100% Accuracy reached
            if current_acc == 100.0:
                stopping_reason = f"Optimal 100% accuracy reached at version {version_tag}."
                step_record["optimizer_reasoning"] = stopping_reason
                step_record["confidence_score"] = 100
                step_record["confidence_level"] = "High"
                history.append(step_record)
                logger.info(stopping_reason)
                break

            # Stopping Condition 2: 3 Consecutive iterations with no improvement
            if rb_info["consecutive_no_improvement"] >= 3:
                stopping_reason = f"Optimization converged: No improvement for 3 consecutive iterations."
                step_record["optimizer_reasoning"] = stopping_reason
                history.append(step_record)
                logger.info(stopping_reason)
                break

            # Step 2: Autonomous Reasoning Optimization & Mutation
            opt_res = self.optimizer.optimize_prompt(
                current_prompt=rb_info["active_prompt"],
                task_description=task_description,
                eval_results=eval_res,
                generation=gen + 1
            )

            step_record["optimizer_reasoning"] = opt_res.get("reasoning", "")
            step_record["classified_failures"] = opt_res.get("classified_failures", [])
            step_record["root_causes"] = opt_res.get("root_causes", [])
            step_record["generated_rules"] = opt_res.get("generated_rules", [])
            step_record["mutations_applied"] = opt_res.get("mutations_applied", [])
            step_record["explainability"] = opt_res.get("explainability", {})
            step_record["confidence_score"] = opt_res.get("confidence_score", 75)
            step_record["confidence_level"] = opt_res.get("confidence_level", "Medium")

            history.append(step_record)
            current_prompt = opt_res.get("optimized_prompt", current_prompt)

        execution_time = time.time() - start_time
        best_prompt = self.optimizer.rollback_manager.best_prompt or current_prompt
        initial_acc = history[0]["accuracy"] if history else 0.0
        final_acc = max(self.optimizer.rollback_manager.best_accuracy, initial_acc)
        improvement_delta = round(max(0.0, final_acc - initial_acc), 2)
        seed_prompt_text = initial_prompt or benchmark_data.get("seed_prompt", "")

        # Persist Experiment Record
        experiment = ExperimentTracker.create_experiment(
            benchmark_name=benchmark_name,
            seed_prompt=seed_prompt_text,
            optimized_prompt=best_prompt,
            history=history,
            execution_time=execution_time,
            model_name=getattr(config, "TARGET_MODEL_NAME", "gemini-2.0-flash")
        )

        return {
            "experiment_id": experiment.get("experiment_id"),
            "benchmark_name": benchmark_name,
            "task_description": task_description,
            "initial_prompt": seed_prompt_text,
            "final_optimized_prompt": best_prompt,
            "initial_accuracy": initial_acc,
            "final_accuracy": final_acc,
            "improvement_delta": improvement_delta,
            "total_generations": len(history),
            "execution_time_seconds": round(execution_time, 2),
            "stopping_reason": stopping_reason,
            "final_confidence_score": history[-1].get("confidence_score", 85) if history else 85,
            "final_confidence_level": history[-1].get("confidence_level", "High") if history else "High",
            "baseline_metrics": experiment.get("baseline_metrics"),
            "final_metrics": experiment.get("final_metrics"),
            "prompt_versions": experiment.get("prompt_versions"),
            "history": history,
            "experiment": experiment
        }
