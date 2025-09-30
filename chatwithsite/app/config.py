import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    DATA_DIR: Path = BASE_DIR / "data"

    # Crawler settings
    MAX_CRAWL_DEPTH: int = 3
    MAX_PAGES_PER_SITE: int = 100

    # LLM settings
    MODEL_NAME: str = "gpt-3.5-turbo"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 500

    # Vector store settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    def __init__(self):
        # Ensure directories exist
        self.STORAGE_DIR.mkdir(exist_ok=True)
        self.DATA_DIR.mkdir(exist_ok=True)

settings = Settings()