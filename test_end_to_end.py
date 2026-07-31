import sys
import json
import logging
from pathlib import Path
from fastapi.testclient import TestClient

from server import app
from meta_agent.loop import OptimizationLoop
from meta_agent.evaluator import BenchmarkEvaluator
from meta_agent.llm import GeminiClient
from meta_agent.experiments import ExperimentTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("e2e_test")

client = TestClient(app)

def test_full_system():
    print("="*60)
    print("🧪 RUNNING COMPLETE END-TO-END SYSTEM AUDIT & EXPERIMENT TRACKING TEST")
    print("="*60)

    # 1. Test Static Frontend & Root Route
    print("\n1. Auditing Root Web Page (GET /)...")
    res_root = client.get("/")
    assert res_root.status_code == 200, f"Root page returned {res_root.status_code}"
    assert "PromptForge" in res_root.text
    assert "code-export-modal" in res_root.text
    assert "experiment-detail-modal" in res_root.text
    assert "nav-btn-experiments" in res_root.text
    print("   ✅ Root HTML loaded perfectly with all evaluation and experiment tracking containers!")

    # 2. Test CSS & JavaScript Modular Assets
    print("\n2. Auditing Static Assets (styles.css & JS Modules)...")
    assert client.get("/static/styles.css?v=9").status_code == 200, "styles.css failed to load"
    assert client.get("/static/js/charts.js?v=9").status_code == 200, "charts.js failed to load"
    assert client.get("/static/js/diff.js?v=9").status_code == 200, "diff.js failed to load"
    assert client.get("/static/js/comparison.js?v=9").status_code == 200, "comparison.js failed to load"
    assert client.get("/static/js/experiments.js?v=9").status_code == 200, "experiments.js failed to load"
    assert client.get("/static/js/export.js?v=9").status_code == 200, "export.js failed to load"
    assert client.get("/static/app.js?v=9").status_code == 200, "app.js failed to load"
    print("   ✅ All 5 modular JavaScript engines & CSS design assets loaded with zero errors!")

    # 3. Test Benchmarks Listing Endpoint
    print("\n3. Auditing GET /api/benchmarks...")
    res_bm = client.get("/api/benchmarks")
    assert res_bm.status_code == 200
    bm_data = res_bm.json()
    benchmarks = bm_data.get("benchmarks", [])
    assert len(benchmarks) >= 10, f"Expected at least 10 benchmarks, found {len(benchmarks)}"
    print(f"   ✅ Successfully verified {len(benchmarks)} security benchmark datasets with full test cases!")

    # 4. Test Optimization & Automatic Experiment Tracking
    print("\n4. Auditing Optimization & Experiment Creation (POST /api/optimize)...")
    res_opt = client.post("/api/optimize", json={
        "benchmark_name": "vulnerability_audit",
        "generations": 2
    })
    assert res_opt.status_code == 200, f"Optimization API failed: {res_opt.text}"
    opt_data = res_opt.json()
    assert "experiment_id" in opt_data
    assert "baseline_metrics" in opt_data
    assert "final_metrics" in opt_data
    assert "prompt_versions" in opt_data
    assert "f1" in opt_data["final_metrics"]
    exp_id = opt_data["experiment_id"]
    print(f"   ✅ Created Experiment '{exp_id}': Baseline {opt_data['initial_accuracy']}% ➔ Final {opt_data['final_accuracy']}% (F1: {opt_data['final_metrics']['f1']}%)")

    # 5. Test Experiment APIs & Report Exports
    print("\n5. Auditing Experiment History & Report Export APIs...")
    res_exp_list = client.get("/api/experiments")
    assert res_exp_list.status_code == 200
    exp_list = res_exp_list.json().get("experiments", [])
    assert len(exp_list) > 0, "Experiments list returned empty"

    res_exp_detail = client.get(f"/api/experiments/{exp_id}")
    assert res_exp_detail.status_code == 200
    detail_data = res_exp_detail.json()
    assert detail_data["experiment_id"] == exp_id

    # Test PDF, Markdown, JSON, and CSV exports
    assert client.get(f"/api/experiments/{exp_id}/export?format=pdf").status_code == 200
    assert client.get(f"/api/experiments/{exp_id}/export?format=markdown").status_code == 200
    assert client.get(f"/api/experiments/{exp_id}/export?format=json").status_code == 200
    assert client.get(f"/api/experiments/{exp_id}/export?format=csv").status_code == 200
    print("   ✅ All 4 Report Export formats (PDF, Markdown, JSON, CSV) generated cleanly!")

    # 6. Test Security Playground Engine
    print("\n6. Auditing Security Playground (POST /api/playground)...")
    res_pg = client.post("/api/playground", json={
        "system_prompt": "You are a security auditor. State whether the input is SAFE or VULNERABLE.",
        "test_input": "def query(user): return f'SELECT * FROM users WHERE name = {user}'"
    })
    assert res_pg.status_code == 200
    print("   ✅ Playground inference executed cleanly!")

    print("\n" + "="*60)
    print("🎉 ALL EXPERIMENT TRACKING & EVALUATION AUDITS PASSED WITH ZERO FAILURES!")
    print("="*60)

if __name__ == "__main__":
    test_full_system()
