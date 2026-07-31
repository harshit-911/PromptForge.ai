import os
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from meta_agent.config import config

logger = logging.getLogger(__name__)

EXPERIMENTS_DIR = config.BASE_DIR / "meta_agent" / "experiments"
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

class ExperimentTracker:
    """Manages local experiment tracking, persistence, and versioning for PromptForge."""

    @staticmethod
    def create_experiment(
        benchmark_name: str,
        seed_prompt: str,
        optimized_prompt: str,
        history: List[Dict[str, Any]],
        execution_time: float,
        model_name: str = "gemini-2.0-flash"
    ) -> Dict[str, Any]:
        """Creates, formats, and persists an Experiment record."""
        exp_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        timestamp = datetime.now().isoformat()

        if not history:
            history = []

        baseline_record = history[0] if history else {}
        final_record = history[-1] if history else {}

        # Extract baseline vs final metrics
        baseline_metrics = {
            "accuracy": baseline_record.get("accuracy", 0.0),
            "precision": baseline_record.get("precision", 0.0),
            "recall": baseline_record.get("recall", 0.0),
            "f1": baseline_record.get("f1", 0.0),
            "passed": baseline_record.get("passed", 0),
            "failed": baseline_record.get("failures_count", 0)
        }

        final_metrics = {
            "accuracy": final_record.get("accuracy", 0.0),
            "precision": final_record.get("precision", 0.0),
            "recall": final_record.get("recall", 0.0),
            "f1": final_record.get("f1", 0.0),
            "passed": final_record.get("passed", 0),
            "failed": final_record.get("failures_count", 0)
        }

        # Build prompt version history (v1.0, v1.1, v1.2...)
        prompt_versions = []
        for idx, item in enumerate(history):
            version_str = f"v1.{idx}"
            prompt_versions.append({
                "version": version_str,
                "timestamp": timestamp,
                "prompt_text": item.get("prompt", ""),
                "what_changed": "Baseline Seed Prompt" if idx == 0 else f"Mutated {len(item.get('failures', []))} security rule boundaries",
                "reason_for_change": item.get("optimizer_reasoning", ""),
                "metrics": {
                    "accuracy": item.get("accuracy", 0.0),
                    "precision": item.get("precision", 0.0),
                    "recall": item.get("recall", 0.0),
                    "f1": item.get("f1", 0.0),
                    "passed": item.get("passed", 0),
                    "failed": item.get("failures_count", 0)
                }
            })

        # Calculate total token usage estimation
        total_tokens = 0
        for item in history:
            total_tokens += item.get("estimated_tokens", 0)

        experiment = {
            "experiment_id": exp_id,
            "timestamp": timestamp,
            "benchmark_name": benchmark_name,
            "seed_prompt": seed_prompt,
            "optimized_prompt": optimized_prompt,
            "iterations": len(history),
            "model": model_name,
            "execution_time_seconds": round(execution_time, 2),
            "total_token_usage": total_tokens or len(optimized_prompt.split()) * 4,
            "success_rate": final_metrics["accuracy"],
            "baseline_metrics": baseline_metrics,
            "final_metrics": final_metrics,
            "prompt_versions": prompt_versions,
            "history": history
        }

        # Persist to local JSON file
        file_path = EXPERIMENTS_DIR / f"{exp_id}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(experiment, f, indent=2)
            logger.info(f"Experiment saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save experiment {exp_id}: {e}")

        return experiment

    @staticmethod
    def list_experiments() -> List[Dict[str, Any]]:
        """Lists all local experiments ordered by timestamp descending."""
        experiments = []
        for file in EXPERIMENTS_DIR.glob("exp_*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    experiments.append({
                        "experiment_id": data.get("experiment_id", file.stem),
                        "timestamp": data.get("timestamp", ""),
                        "benchmark_name": data.get("benchmark_name", ""),
                        "model": data.get("model", ""),
                        "iterations": data.get("iterations", 0),
                        "execution_time_seconds": data.get("execution_time_seconds", 0.0),
                        "baseline_accuracy": data.get("baseline_metrics", {}).get("accuracy", 0.0),
                        "final_accuracy": data.get("final_metrics", {}).get("accuracy", 0.0),
                        "delta_accuracy": round(data.get("final_metrics", {}).get("accuracy", 0.0) - data.get("baseline_metrics", {}).get("accuracy", 0.0), 2),
                        "final_f1": data.get("final_metrics", {}).get("f1", 0.0)
                    })
            except Exception as e:
                logger.error(f"Error loading experiment file {file}: {e}")

        experiments.sort(key=lambda x: x["timestamp"], reverse=True)
        return experiments

    @staticmethod
    def get_experiment(exp_id: str) -> Optional[Dict[str, Any]]:
        """Gets full experiment details by ID."""
        file_path = EXPERIMENTS_DIR / f"{exp_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def delete_experiment(exp_id: str) -> bool:
        """Deletes an experiment by ID."""
        file_path = EXPERIMENTS_DIR / f"{exp_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
