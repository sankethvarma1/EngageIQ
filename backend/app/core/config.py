from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Populate os.environ from a CWD-relative .env file as well, so modules that
# read os.getenv directly (e.g. the LLM provider) honor the same file that
# pydantic-settings already reads for Settings fields.
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", protected_namespaces=("settings_",))

    # Database
    database_url: str = "sqlite:///./engageiq.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1

    # ML
    risk_model_weights: str = '{"financial": 0.3, "delivery": 0.25, "operational": 0.2, "client": 0.15, "data_quality": 0.1}'

    # LLM
    nemotron_api_key: str = ""
    nemotron_base_url: str = "https://integrate.api.nvidia.com/v1"
    nemotron_model: str = "nvidia/nemotron-3-ultra-550b-a55b"

    # RAG
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_dimension: int = 384
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_retrieval: int = 5

    # Frontend
    frontend_url: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
