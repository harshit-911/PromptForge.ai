import sys
import json
import argparse
import logging
from meta_agent.loop import OptimizationLoop
from meta_agent.config import config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def print_banner():
    banner = """
  ========================================================================
   META-AGENT: Automatic Prompt Optimization for Safety & Security
   Powered by Google Gemini API | IIIT-Naya Raipur Vocational Training
  ========================================================================
    """
    print(banner)

def list_benchmarks():
    print("\n[Available Benchmark Datasets]:")
    for b_file in config.BENCHMARKS_DIR.glob("*.json"):
        with open(b_file, "r") as f:
            data = json.load(f)
            print(f"  • {data.get('benchmark_name', b_file.stem)}: {data.get('description')}")
    print()

def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Run Meta-Agent Prompt Optimization")
    parser.add_argument("--benchmark", type=str, default="vulnerability_audit", help="Benchmark dataset to run (vulnerability_audit, log_anomaly, prompt_injection)")
    parser.add_argument("--generations", type=int, default=3, help="Number of optimization generations (default: 3)")
    parser.add_argument("--list", action="store_true", help="List available benchmarks")

    args = parser.parse_args()

    if args.list:
        list_benchmarks()
        sys.exit(0)

    print(f"🚀 Running Meta-Agent Optimization on benchmark: '{args.benchmark}' for {args.generations} generation(s)...")

    loop = OptimizationLoop()
    try:
        results = loop.run(benchmark_name=args.benchmark, max_generations=args.generations)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        list_benchmarks()
        sys.exit(1)

    print("\n" + "="*70)
    print("                      OPTIMIZATION RESULTS SUMMARY                     ")
    print("="*70)
    print(f"📌 Benchmark Dataset  : {results['benchmark_name']}")
    print(f"📈 Initial Accuracy   : {results['initial_accuracy']}%")
    print(f"🏆 Final Accuracy     : {results['final_accuracy']}%")
    print(f"⚡ Accuracy Delta     : +{results['improvement_delta']}%")
    print(f"🔄 Total Generations  : {results['total_generations']}")
    print("="*70)

    print("\n--- [SEED PROMPT (Gen 1)] ---")
    print(results['initial_prompt'])

    print("\n--- [OPTIMIZED PROMPT (Final Gen)] ---")
    print(results['final_optimized_prompt'])

    print("\n✨ Optimization trajectory completed successfully!")

if __name__ == "__main__":
    main()
