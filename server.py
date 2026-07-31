import os
import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from meta_agent.config import config
from meta_agent.llm import GeminiClient
from meta_agent.loop import OptimizationLoop
from meta_agent.evaluator import BenchmarkEvaluator
from meta_agent.experiments import ExperimentTracker

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PromptForge AI Evaluation & Experiment Tracking Platform",
    description="Automated Prompt Engineering, Evaluation, and Experiment Tracking Platform",
    version="2.0.0"
)

llm_client = GeminiClient()
optimization_loop = OptimizationLoop(llm_client)
evaluator = BenchmarkEvaluator(llm_client)

class OptimizationRequest(BaseModel):
    benchmark_name: str
    custom_seed_prompt: Optional[str] = None
    generations: int = 3

class PlaygroundRequest(BaseModel):
    system_prompt: str
    test_input: str

class TestCaseModel(BaseModel):
    id: str
    input: str
    expected_status: str
    expected_category: Optional[str] = "GENERAL"

class CreateBenchmarkRequest(BaseModel):
    benchmark_name: str
    description: str
    task_description: str
    seed_prompt: str
    test_cases: List[TestCaseModel]

@app.get("/api/benchmarks")
def get_benchmarks():
    benchmarks = []
    for b_file in config.BENCHMARKS_DIR.glob("*.json"):
        try:
            with open(b_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                benchmarks.append({
                    "id": b_file.stem,
                    "name": data.get("benchmark_name", b_file.stem),
                    "description": data.get("description", ""),
                    "task_description": data.get("task_description", ""),
                    "seed_prompt": data.get("seed_prompt", ""),
                    "test_cases": data.get("test_cases", []),
                    "test_cases_count": len(data.get("test_cases", []))
                })
        except Exception as e:
            logger.error(f"Error reading benchmark file {b_file}: {e}")
    return {"benchmarks": benchmarks}

@app.post("/api/benchmarks")
def create_custom_benchmark(req: CreateBenchmarkRequest):
    safe_name = "".join([c for c in req.benchmark_name if c.isalnum() or c in ("_", "-")]).lower()
    if not safe_name:
        raise HTTPException(status_code=400, detail="Invalid benchmark name.")

    file_path = config.BENCHMARKS_DIR / f"{safe_name}.json"
    benchmark_dict = {
        "benchmark_name": safe_name,
        "description": req.description,
        "task_description": req.task_description,
        "seed_prompt": req.seed_prompt,
        "test_cases": [tc.model_dump() for tc in req.test_cases]
    }

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(benchmark_dict, f, indent=2)
        return {"status": "success", "benchmark_id": safe_name, "message": f"Custom benchmark '{safe_name}' created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/benchmarks/{benchmark_id}")
def get_benchmark_detail(benchmark_id: str):
    try:
        data = optimization_loop.load_benchmark(benchmark_id)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found.")

@app.delete("/api/benchmarks/{benchmark_id}")
def delete_benchmark(benchmark_id: str):
    safe_name = "".join([c for c in benchmark_id if c.isalnum() or c in ("_", "-")]).lower()
    file_path = config.BENCHMARKS_DIR / f"{safe_name}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found.")

    try:
        file_path.unlink()
        return {"status": "success", "message": f"Benchmark '{safe_name}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize")
def run_optimization(req: OptimizationRequest):
    try:
        results = optimization_loop.run(
            benchmark_name=req.benchmark_name,
            initial_prompt=req.custom_seed_prompt,
            max_generations=req.generations
        )
        return results
    except Exception as e:
        logger.error(f"Optimization run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/playground")
def run_playground(req: PlaygroundRequest):
    try:
        user_msg = f"Analyze the following input:\n\n{req.test_input}"
        response_text = llm_client.generate_text(
            prompt=user_msg,
            system_instruction=req.system_prompt,
            temperature=0.0
        )
        return {"output": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# EXPERIMENT TRACKING & REPORT EXPORT ENDPOINTS (REQUIREMENT #1, #7)
@app.get("/api/experiments")
def get_experiments():
    """List all saved experiment runs."""
    return {"experiments": ExperimentTracker.list_experiments()}

@app.get("/api/experiments/{exp_id}")
def get_experiment_detail(exp_id: str):
    """Retrieve full experiment report by ID."""
    exp = ExperimentTracker.get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{exp_id}' not found.")
    return exp

@app.delete("/api/experiments/{exp_id}")
def delete_experiment_record(exp_id: str):
    """Delete an experiment record."""
    success = ExperimentTracker.delete_experiment(exp_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Experiment '{exp_id}' not found.")
    return {"status": "success", "message": f"Experiment '{exp_id}' deleted successfully."}

@app.get("/api/experiments/{exp_id}/export")
def export_experiment_report(exp_id: str, format: str = Query("json")):
    """Export experiment report in PDF (HTML printable), Markdown, JSON, or CSV format."""
    exp = ExperimentTracker.get_experiment(exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{exp_id}' not found.")

    fmt = format.lower()

    if fmt == "json":
        return Response(content=json.dumps(exp, indent=2), media_type="application/json", headers={"Content-Disposition": f"attachment; filename={exp_id}.json"})

    elif fmt == "csv":
        csv_content = "Version,Accuracy,Precision,Recall,F1_Score,Passed,Failed,Reasoning\n"
        for v in exp.get("prompt_versions", []):
            m = v.get("metrics", {})
            reason = f"\"{v.get('reason_for_change', '').replace('\"', '\"\"')}\""
            csv_content += f"{v.get('version')},{m.get('accuracy')},{m.get('precision')},{m.get('recall')},{m.get('f1')},{m.get('passed')},{m.get('failed')},{reason}\n"
        return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={exp_id}.csv"})

    elif fmt in ("markdown", "md"):
        md = f"# PromptForge AI Experiment Report: {exp.get('experiment_id')}\n\n"
        md += f"**Benchmark:** {exp.get('benchmark_name')}\n"
        md += f"**Timestamp:** {exp.get('timestamp')}\n"
        md += f"**Model:** {exp.get('model')}\n"
        md += f"**Execution Latency:** {exp.get('execution_time_seconds')}s\n\n"
        md += "## Evaluation Summary Metrics (BEFORE vs AFTER)\n\n"
        md += "| Metric | Baseline (v1.0) | Optimized (Final) | Improvement |\n"
        md += "| :--- | :--- | :--- | :--- |\n"
        b = exp.get("baseline_metrics", {})
        f = exp.get("final_metrics", {})
        md += f"| Accuracy | {b.get('accuracy')}% | {f.get('accuracy')}% | +{round(f.get('accuracy',0)-b.get('accuracy',0),2)}% |\n"
        md += f"| Precision | {b.get('precision')}% | {f.get('precision')}% | +{round(f.get('precision',0)-b.get('precision',0),2)}% |\n"
        md += f"| Recall | {b.get('recall')}% | {f.get('recall')}% | +{round(f.get('recall',0)-b.get('recall',0),2)}% |\n"
        md += f"| F1 Score | {b.get('f1')}% | {f.get('f1')}% | +{round(f.get('f1',0)-b.get('f1',0),2)}% |\n\n"
        md += "## Final Mutated System Prompt\n\n```text\n" + exp.get("optimized_prompt", "") + "\n```\n"
        return Response(content=md, media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename={exp_id}.md"})

    elif fmt == "pdf":
        html = f"""<!DOCTYPE html>
<html>
<head>
<title>Experiment Report {exp.get('experiment_id')}</title>
<style>
body {{ font-family: 'Helvetica Neue', Arial, sans-serif; padding: 40px; color: #1e293b; line-height: 1.6; }}
h1 {{ color: #0f172a; border-bottom: 2px solid #38bdf8; padding-bottom: 10px; }}
.metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
.metric-box {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; text-align: center; }}
.metric-val {{ font-size: 24px; font-weight: bold; color: #0284c7; margin-top: 5px; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: left; }}
th {{ background: #f1f5f9; }}
pre {{ background: #0f172a; color: #38bdf8; padding: 15px; border-radius: 8px; white-space: pre-wrap; }}
</style>
</head>
<body>
<h1>PromptForge Experiment Report</h1>
<p><strong>Experiment ID:</strong> {exp.get('experiment_id')}<br>
<strong>Benchmark:</strong> {exp.get('benchmark_name')} | <strong>Model:</strong> {exp.get('model')} | <strong>Latency:</strong> {exp.get('execution_time_seconds')}s</p>

<h2>Baseline vs Optimized Performance</h2>
<div class="metrics-grid">
<div class="metric-box"><div>Accuracy</div><div class="metric-val">{exp.get('baseline_metrics',{}).get('accuracy')}% ➔ {exp.get('final_metrics',{}).get('accuracy')}%</div></div>
<div class="metric-box"><div>Precision</div><div class="metric-val">{exp.get('baseline_metrics',{}).get('precision')}% ➔ {exp.get('final_metrics',{}).get('precision')}%</div></div>
<div class="metric-box"><div>Recall</div><div class="metric-val">{exp.get('baseline_metrics',{}).get('recall')}% ➔ {exp.get('final_metrics',{}).get('recall')}%</div></div>
<div class="metric-box"><div>F1 Score</div><div class="metric-val">{exp.get('baseline_metrics',{}).get('f1')}% ➔ {exp.get('final_metrics',{}).get('f1')}%</div></div>
</div>

<h2>Prompt Version Trajectory</h2>
<table>
<thead><tr><th>Version</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th><th>Passed/Failed</th></tr></thead>
<tbody>
"""
        for v in exp.get("prompt_versions", []):
            m = v.get("metrics", {})
            html += f"<tr><td><strong>{v.get('version')}</strong></td><td>{m.get('accuracy')}%</td><td>{m.get('precision')}%</td><td>{m.get('recall')}%</td><td>{m.get('f1')}%</td><td>{m.get('passed')}/{m.get('failed')}</td></tr>"
        html += f"""</tbody></table>

<h2>Final Optimized System Prompt</h2>
<pre>{exp.get('optimized_prompt', '')}</pre>
</body>
</html>"""
        return Response(content=html, media_type="text/html", headers={"Content-Disposition": f"inline; filename={exp_id}.html"})

    raise HTTPException(status_code=400, detail=f"Unsupported format '{format}'. Supported formats: pdf, markdown, json, csv.")

web_dir = config.BASE_DIR / "web"
web_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
def index_page():
    index_path = web_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>PromptForge API Server Active.</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
