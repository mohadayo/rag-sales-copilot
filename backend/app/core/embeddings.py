"""OpenAI Embedding生成モジュール"""

import logging

import httpx
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=httpx.Timeout(settings.openai_timeout, connect=settings.openai_connect_timeout),
        )
    return _client


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """テキストリストからEmbeddingベクトルを生成"""
    if not texts:
        logger.warning("generate_embeddings: 空のテキストリストが渡されました")
        return []
    logger.debug("Embedding生成開始: texts_count=%d, model=%s", len(texts), settings.openai_embedding_model)
    client = _get_client()
    try:
        response = client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts,
        )
    except APITimeoutError:
        logger.error("Embedding生成タイムアウト: texts_count=%d", len(texts))
        raise
    except RateLimitError:
        logger.error("Embedding生成レート制限超過: texts_count=%d", len(texts))
        raise
    except APIConnectionError:
        logger.error("Embedding生成接続エラー: texts_count=%d", len(texts))
        raise
    logger.debug("Embedding生成完了: embeddings_count=%d", len(response.data))
    return [item.embedding for item in response.data]


def generate_embedding(text: str) -> list[float]:
    """単一テキストからEmbeddingベクトルを生成"""
    if not text.strip():
        raise ValueError("Embeddingを生成するテキストが空です")
    return generate_embeddings([text])[0]
