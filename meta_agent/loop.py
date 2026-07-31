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
    """Orchestrates closed-loop automatic prompt optimization and experiment tracking."""

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
        """Executes automatic prompt optimization loop and tracks Experiment record."""
        start_time = time.time()
        benchmark_data = self.load_benchmark(benchmark_name)
        task_description = benchmark_data.get("task_description", "")
        current_prompt = initial_prompt or benchmark_data.get("seed_prompt", "")

        history = []
        best_prompt = current_prompt
        best_accuracy = -1.0

        for gen in range(max_generations):
            version_tag = f"v1.{gen}"
            logger.info(f"--- Starting Optimization Version {version_tag} ({gen + 1}/{max_generations}) ---")
            
            # Step 1: Evaluate current prompt candidate
            eval_res = self.evaluator.evaluate_prompt(current_prompt, benchmark_data)
            current_acc = eval_res["accuracy"]
            
            logger.info(f"Version {version_tag} Accuracy: {current_acc}% (F1: {eval_res['f1']}%, {eval_res['passed']}/{eval_res['total']} passed)")

            if current_acc >= best_accuracy:
                best_accuracy = current_acc
                best_prompt = current_prompt

            step_record = {
                "version": version_tag,
                "generation": gen + 1,
                "prompt": current_prompt,
                "accuracy": current_acc,
                "precision": eval_res.get("precision", 0.0),
                "recall": eval_res.get("recall", 0.0),
                "f1": eval_res.get("f1", 0.0),
                "passed": eval_res["passed"],
                "total": eval_res["total"],
                "failures_count": len(eval_res["failures"]),
                "failures": eval_res["failures"],
                "detailed_results": eval_res["detailed_results"],
                "estimated_tokens": eval_res.get("estimated_tokens", 0),
                "optimizer_reasoning": ""
            }

            if current_acc == 100.0:
                step_record["optimizer_reasoning"] = f"Version {version_tag}: Optimal 100% accuracy achieved across security test suite."
                history.append(step_record)
                continue

            # Step 2: Meta-Agent optimization & prompt mutation
            opt_res = self.optimizer.optimize_prompt(
                current_prompt=current_prompt,
                task_description=task_description,
                eval_results=eval_res,
                generation=gen + 1
            )

            step_record["optimizer_reasoning"] = opt_res.get("reasoning", "")
            history.append(step_record)

            current_prompt = opt_res.get("optimized_prompt", current_prompt)

        execution_time = time.time() - start_time
        initial_acc = history[0]["accuracy"] if history else 0.0
        final_acc = max(best_accuracy, initial_acc)
        improvement_delta = round(max(0.0, final_acc - initial_acc), 2)

        seed_prompt_text = initial_prompt or benchmark_data.get("seed_prompt", "")

        # Create & persist Experiment record
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
            "baseline_metrics": experiment.get("baseline_metrics"),
            "final_metrics": experiment.get("final_metrics"),
            "prompt_versions": experiment.get("prompt_versions"),
            "history": history,
            "experiment": experiment
        }
