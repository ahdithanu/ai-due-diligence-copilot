import os
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Investment Due Diligence Copilot"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Database & Storage (Default to /tmp if running on Vercel serverless)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:////tmp/diligence_copilot.db" if os.getenv("VERCEL") else "sqlite+aiosqlite:///./diligence_copilot.db"
    )
    
    # Upload Storage
    UPLOAD_DIR: str = os.getenv(
        "UPLOAD_DIR",
        "/tmp/uploads" if os.getenv("VERCEL") else "./storage/uploads"
    )
    
    # LLM Settings (Abstracted behind adapter)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

settings = Settings()


