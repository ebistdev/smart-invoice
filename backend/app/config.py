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
    
    # Email (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    from_name: str = "Smart Invoice"
    
    # App
    secret_key: str = "dev-secret-key-change-in-production"
    debug: bool = True
    base_url: str = "http://localhost:5174"  # For payment links
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
