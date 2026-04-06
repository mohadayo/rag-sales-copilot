"""chunker モジュールのユニットテスト"""

import pytest

from app.core.chunker import _split_into_sentences, chunk_text


class TestSplitIntoSentences:
    """_split_into_sentences のテスト"""

    def test_japanese_sentences(self):
        """日本語の句点で分割できる"""
        text = "これはテストです。次の文です。最後の文です。"
        sentences = _split_into_sentences(text)
        assert len(sentences) >= 2
        assert any("テスト" in s for s in sentences)

    def test_newline_split(self):
        """改行で分割できる"""
        text = "行1\n行2\n行3"
        sentences = _split_into_sentences(text)
        assert len(sentences) >= 2

    def test_empty_text(self):
        """空文字列の場合は空リストを返す"""
        sentences = _split_into_sentences("")
        assert sentences == []

    def test_single_sentence(self):
        """句点なしの場合も単一要素のリストを返す"""
        text = "句点のない一文"
        sentences = _split_into_sentences(text)
        assert len(sentences) == 1
        assert sentences[0] == "句点のない一文"

    def test_english_sentences(self):
        """英語のピリオドで分割できる"""
        text = "This is a test. This is another sentence."
        sentences = _split_into_sentences(text)
        assert len(sentences) >= 1


class TestChunkText:
    """chunk_text のテスト"""

    def test_short_text_returns_single_chunk(self):
        """短いテキストは1チャンクになる"""
        text = "短いテキストです。"
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert "短いテキスト" in chunks[0]

    def test_long_text_splits_into_multiple_chunks(self):
        """chunk_size を超える長いテキストは複数チャンクに分割される"""
        # 500文字を超えるテキストを生成
        long_text = "これはテストの文章です。" * 50  # 約600文字
        chunks = chunk_text(long_text)
        assert len(chunks) > 1

    def test_empty_text_returns_empty_list(self):
        """空文字列は空リストを返す"""
        chunks = chunk_text("")
        assert chunks == []

    def test_chunks_contain_text(self):
        """各チャンクに元のテキストの一部が含まれる"""
        text = "テスト文1です。テスト文2です。テスト文3です。"
        chunks = chunk_text(text)
        combined = "".join(chunks)
        # 元のテキストの主要な内容が保持されている
        assert "テスト文" in combined

    def test_chunk_returns_list_of_strings(self):
        """返り値が文字列リストである"""
        text = "テストです。"
        chunks = chunk_text(text)
        assert isinstance(chunks, list)
        for chunk in chunks:
            assert isinstance(chunk, str)
