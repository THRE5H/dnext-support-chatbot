"""
Backend configuration - extends V1 config
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """FastAPI Backend Configuration"""
    
    # API Configuration
    API_TITLE = "DNEXT Support Chatbot API"
    API_VERSION = "2.0.0"
    API_DESCRIPTION = "REST API for the DNEXT Support Chatbot"
    
    # Server
    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", "8000"))
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]
    
    # V1 AI Components (inherit from main config)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Models
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
    GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DOCS_FOLDER = os.getenv("DOCS_FOLDER", "docs_md")
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/chatbot.db")
    
    # RAG Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "400"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
    
    # LangSmith Configuration (optional)
    LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "dnext-support-chatbot")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "❌ OPENAI_API_KEY not found!\n"
                "Please set it in .env file or environment variables.\n"
                "Get your key from: https://platform.openai.com/account/api-keys"
            )
        
        # Ensure data directories exist
        data_dir = cls.BASE_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        docs_dir = cls.BASE_DIR / cls.DOCS_FOLDER
        docs_dir.mkdir(parents=True, exist_ok=True)
