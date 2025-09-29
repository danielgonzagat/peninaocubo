from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    OPENAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    XAI_API_KEY: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
    KAGGLE_USERNAME: Optional[str] = None
    KAGGLE_KEY: Optional[str] = None

    PENIN_MAX_PARALLEL_PROVIDERS: int = 3
    PENIN_MAX_TOKENS_PER_ROUND: int = 30000
    PENIN_BUDGET_DAILY_USD: float = 5.0
    OPENAI_MODEL: str = "gpt-4o"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    MISTRAL_MODEL: str = "mistral-large-latest"
    GEMINI_MODEL: str = "gemini-1.5-pro"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    GROK_MODEL: str = "grok-beta"
    GROK_MODEL: str = "grok-4"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
