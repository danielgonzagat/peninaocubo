from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    MISTRAL_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    XAI_API_KEY: str | None = None
    HUGGINGFACE_TOKEN: str | None = None
    GITHUB_TOKEN: str | None = None
    KAGGLE_USERNAME: str | None = None
    KAGGLE_KEY: str | None = None

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
