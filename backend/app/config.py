from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://smartinvoice:smartinvoice_dev@localhost:5433/smartinvoice"
    redis_url: str = "redis://localhost:6379/0"
    
    # AI
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_provider: str = "anthropic"  # or "openai"
    llm_model: str = "claude-3-5-sonnet-20241022"
    
    # App
    secret_key: str = "dev-secret-key-change-in-production"
    debug: bool = True
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
