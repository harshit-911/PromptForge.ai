# PromptForge AI: Automated System Prompt Mutation & Refinement Platform

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LLM Support](https://img.shields.io/badge/LLM-Gemini%202.0%20%7C%20Ollama%20(Llama%203.2)-orange.svg)](https://ai.google.dev/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-emerald.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**PromptForge AI** is an autonomous closed-loop Meta-Agent platform that automatically evaluates, critiques, and mutates LLM system prompts for cybersecurity and AI safety applications (OWASP code auditing, SOC threat log analysis, real CVE records from `cve.org`, and DAN jailbreak defense).

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

## 🌟 Key Features

- **Enterprise AI Security Benchmark Management System**:
  - **Side-Over Drawer**: Interactive drawer with overview, evaluation criteria, and paginated test case preview tables with expandable payloads.
  - **6-Step Creation Wizard**: Step-by-step wizard for building, validating, previewing, and publishing custom security benchmark suites.
  - **Advanced Real-Time Search & Multi-Filters**: Instant client-side filtering by Name, Category, Difficulty, Source, Type, or Favorites (`⭐`).
  - **Multi-Format Dataset Importer**: Drag-and-drop support for `.json`, `.csv`, and `.txt` datasets with live error diagnostics.
- **Enterprise 7-Metric KPI Grid**: Baseline Accuracy, Current Accuracy, Accuracy Gain (+Delta %), Current Generation, Benchmark Size, Execution Latency, and Prompt Security Linter Score.
- **Production Integration Code Exporter**: 1-click code generator for Python (`google-genai`), Python (`openai`), Node.js, cURL, and LangChain.
- **Dual LLM Provider Support**: Native integration with **Google Gemini API** and **Local Ollama (`llama3.2`)** for 100% offline, $0 cost execution.

---

## 📁 Repository Structure

```
PromptForge.ai/
├── meta_agent/
│   ├── benchmarks/               # 13+ Built-in & CVE benchmark JSON datasets
│   ├── config.py                 # Platform configuration loader
│   ├── cve_importer.py           # MITRE cvelistV5 JSON dataset parser
│   ├── evaluator.py              # Multi-metric benchmark evaluator
│   ├── llm.py                    # Dual Gemini API & Local Ollama client wrapper
│   ├── loop.py                   # Optimization loop orchestrator
│   └── optimizer.py              # Meta-Agent prompt optimizer
├── web/
│   ├── index.html                # Enterprise Web Dashboard HTML
│   ├── styles.css                # CSS design system (Dark/Light mode)
│   └── app.js                    # Web Dashboard JavaScript
├── server.py                     # FastAPI REST API server
├── main.py                       # CLI Command Line Interface entry point
├── test_end_to_end.py            # Automated end-to-end system test suite
├── requirements.txt              # Python package dependencies
├── .env.example                  # Environment configuration template
└── PROMPTFORGE_PROJECT_EXPLANATION.txt  # Project architecture explanation
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
