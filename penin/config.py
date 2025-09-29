from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    OPENAI_API_KEY: Optional[str] = Field(None, min_length=1)
    DEEPSEEK_API_KEY: Optional[str] = Field(None, min_length=1)
    MISTRAL_API_KEY: Optional[str] = Field(None, min_length=1)
    GEMINI_API_KEY: Optional[str] = Field(None, min_length=1)
    ANTHROPIC_API_KEY: Optional[str] = Field(None, min_length=1)
    XAI_API_KEY: Optional[str] = Field(None, min_length=1)
    HUGGINGFACE_TOKEN: Optional[str] = Field(None, min_length=1)
    GITHUB_TOKEN: Optional[str] = Field(None, min_length=1)
    KAGGLE_USERNAME: Optional[str] = Field(None, min_length=1)
    KAGGLE_KEY: Optional[str] = Field(None, min_length=1)

    PENIN_MAX_PARALLEL_PROVIDERS: int = 3
    PENIN_MAX_TOKENS_PER_ROUND: int = 30000
    PENIN_BUDGET_DAILY_USD: float = 5.0
    OPENAI_MODEL: str = "gpt-4o"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    MISTRAL_MODEL: str = "mistral-large-latest"
    GEMINI_MODEL: str = "gemini-1.5-pro"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    GROK_MODEL: str = "grok-beta"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
