"""OpenAI Embedding生成モジュール"""

import logging

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        logger.info("Embedding用OpenAIクライアントを初期化します (model=%s)", settings.openai_embedding_model)
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """テキストリストからEmbeddingベクトルを生成"""
    logger.info("Embedding生成開始: %d テキスト", len(texts))
    client = _get_client()
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    logger.debug("Embedding生成完了: %d ベクトル", len(response.data))
    return [item.embedding for item in response.data]


def generate_embedding(text: str) -> list[float]:
    """単一テキストからEmbeddingベクトルを生成"""
    logger.debug("単一Embedding生成: text_length=%d", len(text))
    return generate_embeddings([text])[0]
