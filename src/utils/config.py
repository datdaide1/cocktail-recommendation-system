import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    PROJECT_ROOT = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    
    COCKTAILS_PATH = DATA_DIR / "enriched_cocktails.csv"
    BARS_PATH = DATA_DIR / "bars_vietnam.csv"
    
    # Gemini configurations
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    # Default model
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Embedding config
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
