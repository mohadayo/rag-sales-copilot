"""テキストチャンク化モジュール"""

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def chunk_text(text: str) -> list[str]:
    """テキストを指定サイズのチャンクに分割する（文単位で分割）"""
    chunk_size = settings.chunk_size
    overlap = settings.chunk_overlap
    logger.info("チャンク化開始: text_length=%d, chunk_size=%d, overlap=%d", len(text), chunk_size, overlap)

    sentences = _split_into_sentences(text)
    chunks = []
    current_chunk: list[str] = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence)
        if current_length + sentence_len > chunk_size and current_chunk:
            chunks.append("".join(current_chunk))
            # オーバーラップ: 末尾の文を次のチャンクに引き継ぐ
            overlap_chunk: list[str] = []
            overlap_len = 0
            for s in reversed(current_chunk):
                if overlap_len + len(s) > overlap:
                    break
                overlap_chunk.insert(0, s)
                overlap_len += len(s)
            current_chunk = overlap_chunk
            current_length = overlap_len

        current_chunk.append(sentence)
        current_length += sentence_len

    if current_chunk:
        chunks.append("".join(current_chunk))

    logger.info("チャンク化完了: %d チャンク生成", len(chunks))
    return chunks


def _split_into_sentences(text: str) -> list[str]:
    """日本語・英語のテキストを文単位で分割"""
    import re

    # 句点・ピリオド・改行で分割しつつ区切り文字を保持
    parts = re.split(r"(。|\.\s|\n)", text)
    sentences = []
    current = ""
    for part in parts:
        current += part
        if part in ("。", "\n") or (part.startswith(".") and len(part) <= 2):
            stripped = current.strip()
            if stripped:
                sentences.append(stripped)
            current = ""
    if current.strip():
        sentences.append(current.strip())
    return sentences
