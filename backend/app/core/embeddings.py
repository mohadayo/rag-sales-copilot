"""OpenAI Embedding生成モジュール"""

import logging

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """テキストリストからEmbeddingベクトルを生成"""
    if not texts:
        logger.warning("generate_embeddings: 空のテキストリストが渡されました")
        return []
    logger.debug("Embedding生成開始: texts_count=%d, model=%s", len(texts), settings.openai_embedding_model)
    client = _get_client()
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    logger.debug("Embedding生成完了: embeddings_count=%d", len(response.data))
    return [item.embedding for item in response.data]


def generate_embedding(text: str) -> list[float]:
    """単一テキストからEmbeddingベクトルを生成"""
    if not text.strip():
        raise ValueError("Embeddingを生成するテキストが空です")
    return generate_embeddings([text])[0]
