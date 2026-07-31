import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TARGET_MODEL_NAME: str = os.getenv("TARGET_MODEL_NAME", "llama3.2")
    META_MODEL_NAME: str = os.getenv("META_MODEL_NAME", "llama3.2")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    
    DEFAULT_GENERATIONS: int = 3
    DEFAULT_TEMPERATURE: float = 0.2
    
    BASE_DIR: Path = Path(__file__).parent.parent
    BENCHMARKS_DIR: Path = Path(__file__).parent / "benchmarks"

config = Config()
