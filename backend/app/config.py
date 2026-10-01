from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://dev:devpass@localhost:5432/bridge"
    groq_api_key: str = ""
    clerk_jwks_url: str = ""
    allowed_origins: str = "http://localhost:3000"
    max_file_size_mb: int = 10
    max_text_chars: int = 50000
    max_gaps_to_fill: int = 25
    rate_limit_analyses_per_hour: int = 5
    rate_limit_reads_per_minute: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
