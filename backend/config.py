import os
from dotenv import load_dotenv

# .envが存在する場合（ローカル開発時）のみ読み込む
load_dotenv()

class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
    
    # DB Configuration
    # App RunnerやRDS導入時に "postgresql://user:password@host/db" に切り替え可能
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/papers.db")

config = Config()
