# PromptForge AI: Automated System Prompt Mutation, Evaluation & Experiment Tracking Platform

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LLM Support](https://img.shields.io/badge/LLM-Gemini%202.0%20%7C%20Ollama%20(Llama%203.2)-orange.svg)](https://ai.google.dev/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-emerald.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**PromptForge AI** is an enterprise closed-loop Meta-Agent platform that transforms prompt engineering into a rigorous, automated prompt evaluation and experiment tracking system for cybersecurity and AI safety applications (OWASP code auditing, SOC threat log analysis, real CVE records from `cve.org`, and DAN jailbreak defense).

---

## 💡 How It Works (Closed-Loop Meta-Agent Architecture)

```
       ┌──────────────────────────────────────────────────────────┐
       │                   CLOSED-LOOP META-AGENT                 │
       └────────────────────────────┬─────────────────────────────┘
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    ▼                               ▼                               ▼
STEP 1: EVALUATE                STEP 2: DIAGNOSE                STEP 3: MUTATE
Run starting seed prompt        Analyze failure reasons         Rewrite system prompt with
against OWASP vulnerabilities,   where the target LLM gave      strict, un-hackable security
server logs, and real CVEs.      the wrong answer.              rules until 100% accuracy.
```

1. **Step 1 • EVALUATE**: Tests candidate system prompts against benchmark test suites (OWASP Top 10, real MITRE CVE records from `cve.org`, SOC attack logs).
2. **Step 2 • DIAGNOSE**: The Meta-Agent pinpoints exact failure diagnostic reasons where the LLM gave incorrect classifications.
3. **Step 3 • MUTATE**: Synthesizes un-hackable security rules directly into the system prompt until baseline accuracy improves to **100%**.

---

## 🌟 Professional Features

### 1. 🧪 Automated Experiment Tracking
- Every optimization run automatically creates and persists an **Experiment** record locally.
- Stores: Experiment ID, Timestamp, Benchmark, Seed Prompt, Final Prompt, LLM Model, Latency, Token Usage, Accuracy, Precision, Recall, F1 Score, Passed Tests, and Failed Tests.

### 2. 📊 Baseline vs. Optimized Comparison
- BEFORE (`v1.0 Seed`) vs. AFTER (`v1.N Mutated`) side-by-side comparison metrics.
- Computes real-time Delta gains: e.g. **Accuracy (61% ➔ 92%)**, **Precision (58% ➔ 91%)**, **Recall (60% ➔ 93%)**, and **F1 Score (59% ➔ 92%)**.

### 3. 🏷️ Prompt Version History
- Version tagging for every mutation step: `v1.0` (Baseline), `v1.1` (Mutation 1), `v1.2` (Mutation 2)...
- Records prompt text, timestamp, change summary, Meta-Agent reasoning critique, and evaluation metrics per version.

### 4. 🔍 Git-Style Prompt Diff Viewer
- Side-by-side line diff viewer displaying:
  - `+ Added instructions` (green line highlight)
  - `- Removed instructions` (red line highlight)
  - `~ Unchanged / Modified rules`

### 5. 📈 Performance Dashboard & Charts
- Zero-dependency SVG chart suite:
  - **Line Chart**: Accuracy, Precision, Recall, and F1 over prompt versions.
  - **Bar Chart**: Passed vs. Failed test cases breakdown per iteration.
  - **Pie Chart**: Error & Threat Categories distribution.
  - **Trend Chart**: Net optimization progress delta.

### 6. 📄 Multi-Format Report Exporter
- Export experiment reports instantly as **PDF** (printable HTML), **Markdown** (`.md`), **JSON** (`.json`), or **CSV** (`.csv`).

---

## 📁 Repository Structure

```
PromptForge.ai/
├── meta_agent/
│   ├── benchmarks/               # 13+ Built-in & CVE benchmark JSON datasets
│   ├── experiments/              # Persisted JSON experiment tracking records
│   ├── config.py                 # Platform configuration loader
│   ├── cve_importer.py           # MITRE cvelistV5 JSON dataset parser
│   ├── evaluator.py              # Precision, Recall, F1 & Benchmark evaluator
│   ├── experiments.py            # Local ExperimentTracker & storage engine
│   ├── llm.py                    # Dual Gemini API & Local Ollama client wrapper
│   ├── loop.py                   # Optimization loop orchestrator with versioning
│   └── optimizer.py              # Meta-Agent prompt optimizer
├── web/
│   ├── js/                       # Modularized frontend engines
│   │   ├── charts.js             # SVG Performance & Progress Charts
│   │   ├── comparison.js         # Baseline vs Optimized Comparison
│   │   ├── diff.js               # Git-Style Line-by-Line Prompt Diff
│   │   ├── experiments.js        # Experiment Tracking & History viewer
│   │   └── export.js             # PDF / Markdown / JSON / CSV Exporter
│   ├── index.html                # Enterprise Web Dashboard HTML
│   ├── styles.css                # CSS design system (Dark/Light mode)
│   └── app.js                    # Main Application Coordinator
├── server.py                     # FastAPI REST API server
├── main.py                       # CLI Command Line Interface entry point
├── test_end_to_end.py            # Automated end-to-end system test suite
├── requirements.txt              # Python package dependencies
├── .env.example                  # Environment configuration template
└── README.md                     # Platform documentation
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
Ensure **Python 3.10+** is installed on your system.

Clone the repository and install dependencies:

```bash
git clone https://github.com/harshit-911/PromptForge.ai.git
cd PromptForge.ai

pip install -r requirements.txt
```

---

## ⚙️ Running PromptForge AI Locally

PromptForge AI supports **two execution modes**: using a **Google Gemini API Key** or running **100% locally for $0 cost via Ollama**.

### Option A: Using Google Gemini API Key

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and insert your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_actual_google_gemini_api_key_here
   TARGET_MODEL_NAME=gemini-2.0-flash
   META_MODEL_NAME=gemini-2.0-flash
   ```

3. Launch the Web Dashboard:
   ```bash
   python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
   ```
   Open your browser at: **`http://127.0.0.1:8000`**

---

### Option B: Running 100% Offline via Local Ollama ($0 Cost)

Run models like **Llama 3.2**, **Mistral**, or **Gemma** locally without hitting cloud API limits or needing an API key.

1. Install **Ollama**:
   - macOS / Linux: `brew install ollama` or download from [https://ollama.com](https://ollama.com)
   - Windows: Download installer from [https://ollama.com/download](https://ollama.com/download)

2. Pull and start Llama 3.2 in your terminal:
   ```bash
   ollama pull llama3.2
   ```

3. Configure `.env` for Ollama:
   ```env
   GEMINI_API_KEY=ollama
   LLM_PROVIDER=ollama
   OLLAMA_HOST=http://127.0.0.1:11434
   TARGET_MODEL_NAME=llama3.2
   META_MODEL_NAME=llama3.2
   ```

4. Start PromptForge AI:
   ```bash
   python3 -m uvicorn server:app --host 0.0.0.0 --port 8000
   ```
   Open your browser at: **`http://127.0.0.1:8000`**

---

## 💻 Command Line Interface (CLI) Usage

You can also run prompt optimizations directly from your terminal:

```bash
# List all available benchmark datasets
python3 main.py --list

# Run 3 generations of prompt optimization on code vulnerability auditing
python3 main.py --benchmark vulnerability_audit --generations 3

# Run on real CVE dataset parsed from cve.org
python3 main.py --benchmark cve_real_vulnerabilities --generations 3
```

---

## 🧪 Automated Testing & Verification

Run the comprehensive end-to-end audit script to verify all REST endpoints, static assets, and optimization loops:

```bash
python3 test_end_to_end.py
```

---

## 📄 License

This project is open-source under the MIT License.
