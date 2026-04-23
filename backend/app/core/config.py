import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 5
    cors_origins: str = "http://localhost:3000"
    chroma_persist_dir: str = "./chroma_data"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50
    openai_timeout: float = 30.0
    openai_connect_timeout: float = 10.0

    class Config:
        env_file = ".env"


settings = Settings()
