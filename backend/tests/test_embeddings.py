"""app/core/embeddings.py のユニットテスト"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch  # noqa: E402

import pytest  # noqa: E402
from openai import APIConnectionError, APITimeoutError, RateLimitError  # noqa: E402


class TestGenerateEmbeddings:
    """generate_embeddings のテスト"""

    def setup_method(self):
        import app.core.embeddings as mod
        mod._client = None

    @patch("app.core.embeddings._get_client")
    def test_returns_embeddings_for_valid_texts(self, mock_get_client):
        """有効なテキストリストに対してEmbeddingリストを返す"""
        from app.core.embeddings import generate_embeddings

        mock_client = MagicMock()
        mock_data = [MagicMock(embedding=[0.1, 0.2, 0.3]), MagicMock(embedding=[0.4, 0.5, 0.6])]
        mock_client.embeddings.create.return_value = MagicMock(data=mock_data)
        mock_get_client.return_value = mock_client

        result = generate_embeddings(["テスト1", "テスト2"])

        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        mock_client.embeddings.create.assert_called_once()

    def test_empty_list_returns_empty(self):
        """空のリストに対して空リストを返す"""
        from app.core.embeddings import generate_embeddings

        result = generate_embeddings([])
        assert result == []

    @patch("app.core.embeddings._get_client")
    def test_api_timeout_raises_and_logs(self, mock_get_client):
        """APIタイムアウト時に例外を再送出する"""
        from app.core.embeddings import generate_embeddings

        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = APITimeoutError(request=MagicMock())
        mock_get_client.return_value = mock_client

        with pytest.raises(APITimeoutError):
            generate_embeddings(["テスト"])

    @patch("app.core.embeddings._get_client")
    def test_rate_limit_raises_and_logs(self, mock_get_client):
        """レート制限超過時に例外を再送出する"""
        from app.core.embeddings import generate_embeddings

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_client.embeddings.create.side_effect = RateLimitError(
            message="rate limit",
            response=mock_response,
            body=None,
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(RateLimitError):
            generate_embeddings(["テスト"])

    @patch("app.core.embeddings._get_client")
    def test_connection_error_raises_and_logs(self, mock_get_client):
        """接続エラー時に例外を再送出する"""
        from app.core.embeddings import generate_embeddings

        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = APIConnectionError(request=MagicMock())
        mock_get_client.return_value = mock_client

        with pytest.raises(APIConnectionError):
            generate_embeddings(["テスト"])


class TestGenerateEmbedding:
    """generate_embedding のテスト"""

    @patch("app.core.embeddings._get_client")
    def test_returns_single_embedding(self, mock_get_client):
        """単一テキストのEmbeddingを返す"""
        from app.core.embeddings import generate_embedding

        mock_client = MagicMock()
        mock_data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = MagicMock(data=mock_data)
        mock_get_client.return_value = mock_client

        result = generate_embedding("テスト")
        assert result == [0.1, 0.2, 0.3]

    def test_empty_text_raises_value_error(self):
        """空テキストでValueErrorを送出する"""
        from app.core.embeddings import generate_embedding

        with pytest.raises(ValueError, match="空です"):
            generate_embedding("   ")


class TestEmbeddingClientTimeout:
    """クライアントのタイムアウト設定テスト"""

    def setup_method(self):
        import app.core.embeddings as mod
        mod._client = None

    @patch("app.core.embeddings.OpenAI")
    def test_client_has_timeout(self, mock_openai_cls):
        """クライアントにタイムアウトが設定される"""
        from app.core.embeddings import _get_client

        _get_client()

        mock_openai_cls.assert_called_once()
        call_kwargs = mock_openai_cls.call_args[1]
        assert "timeout" in call_kwargs
