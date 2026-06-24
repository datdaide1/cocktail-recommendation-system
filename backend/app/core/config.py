from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cocktail Recommendation System"
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    QDRANT_PATH: str = "backend/data/qdrant"
    DATA_DIR: str = "backend/data"

    class Config:
        env_file = ".env"

settings = Settings()
