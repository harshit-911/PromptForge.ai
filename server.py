import os
import json
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from meta_agent.config import config
from meta_agent.llm import GeminiClient
from meta_agent.loop import OptimizationLoop
from meta_agent.evaluator import BenchmarkEvaluator

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Meta-Agent Prompt Optimization Platform",
    description="Automated Prompt Engineering & Optimization for Safety & Security Applications",
    version="1.0.0"
)

# Initialize Gemini & Optimization components
llm_client = GeminiClient()
optimization_loop = OptimizationLoop(llm_client)
evaluator = BenchmarkEvaluator(llm_client)

# Pydantic Request Models
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
    """List available benchmark datasets including all test cases."""
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
    """Create and save a new custom benchmark dataset."""
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
        logger.error(f"Failed to save custom benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/benchmarks/{benchmark_id}")
def get_benchmark_detail(benchmark_id: str):
    """Retrieve full details for a specific benchmark dataset."""
    try:
        data = optimization_loop.load_benchmark(benchmark_id)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found.")

@app.delete("/api/benchmarks/{benchmark_id}")
def delete_benchmark(benchmark_id: str):
    """Delete a benchmark dataset file."""
    safe_name = "".join([c for c in benchmark_id if c.isalnum() or c in ("_", "-")]).lower()
    file_path = config.BENCHMARKS_DIR / f"{safe_name}.json"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Benchmark '{benchmark_id}' not found.")

    try:
        file_path.unlink()
        logger.info(f"Deleted benchmark dataset '{safe_name}.json'")
        return {"status": "success", "message": f"Benchmark '{safe_name}' deleted successfully."}
    except Exception as e:
        logger.error(f"Failed to delete benchmark {safe_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/optimize")
def run_optimization(req: OptimizationRequest):
    """Execute multi-generation automatic prompt optimization loop."""
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
    """Execute candidate prompt against user-provided code/log in playground."""
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

# Serve Web Frontend static files
web_dir = config.BASE_DIR / "web"
web_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
def index_page():
    index_path = web_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Meta-Agent API Server Active. Frontend loading...</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
