import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    PROJECT_ROOT = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    
    DATABASE_PATH = DATA_DIR / "chat_data.db"
    COCKTAILS_PATH = DATA_DIR / "enriched_cocktails.csv"
    BARS_PATH = DATA_DIR / "bars_vietnam.csv"
    
    # LLM Provider Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").lower().strip() # 'gemini', 'openai', 'openrouter'
    
    # Google Gemini configurations
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    
    # OpenAI configurations
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # OpenRouter configurations
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    
    # Custom API configurations (e.g. beeknoee/9router)
    CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "")
    CUSTOM_API_BASE = os.getenv("CUSTOM_API_BASE", "")
    CUSTOM_MODEL = os.getenv("CUSTOM_MODEL", "beeknoee/gemini-3.5-flash")
    
    # Embedding config
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
