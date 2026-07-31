import sys
import json
import logging
from pathlib import Path
from fastapi.testclient import TestClient

from server import app
from meta_agent.loop import OptimizationLoop
from meta_agent.evaluator import BenchmarkEvaluator
from meta_agent.llm import GeminiClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("e2e_test")

client = TestClient(app)

def test_full_system():
    print("="*60)
    print("🧪 RUNNING COMPLETE END-TO-END SYSTEM AUDIT & BUG CHECK")
    print("="*60)

    # 1. Test Static Frontend & Root Route
    print("\n1. Auditing Root Web Page (GET /)...")
    res_root = client.get("/")
    assert res_root.status_code == 200, f"Root page returned {res_root.status_code}"
    assert "PromptForge" in res_root.text
    assert "code-export-modal" in res_root.text
    assert "bm-drawer-overlay" in res_root.text or "side-drawer" in res_root.text
    assert "bm-wizard-modal" in res_root.text
    assert "linter-audit-results" in res_root.text
    print("   ✅ Root HTML loaded perfectly with all drawer and wizard containers!")

    # 2. Test CSS & JavaScript Assets
    print("\n2. Auditing Static Assets (styles.css & app.js)...")
    res_css = client.get("/static/styles.css?v=7")
    assert res_css.status_code == 200, "styles.css failed to load"
    res_js = client.get("/static/app.js?v=7")
    assert res_js.status_code == 200, "app.js failed to load"
    assert "auditPromptSecurity" in res_js.text
    assert "openSideDrawer" in res_js.text
    assert "openWizardModal" in res_js.text
    assert "processDatasetImport" in res_js.text
    assert "deleteBenchmark" in res_js.text
    print("   ✅ CSS and JS assets loaded cleanly with zero errors!")

    # 3. Test Benchmarks Listing Endpoint
    print("\n3. Auditing GET /api/benchmarks...")
    res_bm = client.get("/api/benchmarks")
    assert res_bm.status_code == 200
    bm_data = res_bm.json()
    benchmarks = bm_data.get("benchmarks", [])
    assert len(benchmarks) >= 10, f"Expected at least 10 benchmarks, found {len(benchmarks)}"
    
    for b in benchmarks:
        assert "id" in b and "name" in b and "test_cases" in b
        assert len(b["test_cases"]) > 0, f"Benchmark {b['id']} has empty test cases list!"
    print(f"   ✅ Successfully verified {len(benchmarks)} security benchmark datasets with full test cases!")

    # 4. Test Single Benchmark Detail Endpoint
    print("\n4. Auditing GET /api/benchmarks/{id}...")
    sample_id = benchmarks[0]["id"]
    res_detail = client.get(f"/api/benchmarks/{sample_id}")
    assert res_detail.status_code == 200
    detail_json = res_detail.json()
    assert "test_cases" in detail_json
    print(f"   ✅ Benchmark detail endpoint for '{sample_id}' operating correctly!")

    # 5. Test Custom Benchmark Creation & Deletion
    print("\n5. Auditing Custom Benchmark Lifecycle (POST & DELETE /api/benchmarks)...")
    custom_id = "e2e_temp_audit_benchmark"
    res_create = client.post("/api/benchmarks", json={
        "benchmark_name": custom_id,
        "description": "Temporary E2E audit benchmark",
        "task_description": "Audit test",
        "seed_prompt": "Audit seed prompt",
        "test_cases": [
            {"id": "tc_01", "input": "test input 1", "expected_status": "VULNERABLE", "expected_category": "AUDIT"},
            {"id": "tc_02", "input": "test input 2", "expected_status": "SAFE", "expected_category": "AUDIT"}
        ]
    })
    assert res_create.status_code == 200, f"Benchmark creation failed: {res_create.text}"
    print(f"   ✅ Created custom benchmark '{custom_id}' successfully!")

    res_del = client.delete(f"/api/benchmarks/{custom_id}")
    assert res_del.status_code == 200, f"Benchmark deletion failed: {res_del.text}"
    print(f"   ✅ Deleted custom benchmark '{custom_id}' cleanly!")

    # 6. Test Optimization Engine
    print("\n6. Auditing Optimization Engine (POST /api/optimize)...")
    res_opt = client.post("/api/optimize", json={
        "benchmark_name": "vulnerability_audit",
        "generations": 2
    })
    assert res_opt.status_code == 200, f"Optimization API failed: {res_opt.text}"
    opt_data = res_opt.json()
    assert "initial_accuracy" in opt_data
    assert "final_accuracy" in opt_data
    assert "history" in opt_data
    assert opt_data["final_accuracy"] >= opt_data["initial_accuracy"]
    print(f"   ✅ Optimization engine run complete: Baseline {opt_data['initial_accuracy']}% ➔ Final {opt_data['final_accuracy']}% (+{opt_data['improvement_delta']}%)")

    # 7. Test Security Playground Engine
    print("\n7. Auditing Security Playground (POST /api/playground)...")
    res_pg = client.post("/api/playground", json={
        "system_prompt": "You are a security auditor. State whether the input is SAFE or VULNERABLE.",
        "test_input": "def query(user): return f'SELECT * FROM users WHERE name = {user}'"
    })
    assert res_pg.status_code == 200, f"Playground API failed: {res_pg.text}"
    pg_data = res_pg.json()
    assert "output" in pg_data
    print(f"   ✅ Playground inference executed cleanly!")

    print("\n" + "="*60)
    print("🎉 ALL END-TO-END AUDITS PASSED WITH ZERO BUGS OR FAILURES!")
    print("="*60)

if __name__ == "__main__":
    test_full_system()
