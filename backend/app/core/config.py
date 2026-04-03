import logging
import sys

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_timeout: int = 30
    embedding_dimension: int = 1536
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    cors_origins: str = "http://localhost:3000"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    chroma_persist_dir: str = "./chroma_data"
    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"


settings = Settings()


def validate_settings() -> None:
    """起動時に必須設定を検証する"""
    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY が設定されていません。環境変数または .env ファイルで設定してください。")
        sys.exit(1)
    logger.info(
        "設定検証OK: model=%s, embedding_model=%s, cors_origins=%s",
        settings.openai_model,
        settings.openai_embedding_model,
        settings.cors_origins,
    )
