"""chat ルーターのユニットテスト"""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.chat import router


def _create_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestChatErrorSanitization:
    """チャットAPIエラーメッセージサニタイズのテスト"""

    @patch("app.api.chat.generate_rag_response", side_effect=RuntimeError("OpenAI API key invalid"))
    def test_internal_error_details_not_leaked(self, mock_rag):
        """内部エラー詳細がレスポンスに含まれないことを検証"""
        client = _create_client()
        response = client.post(
            "/api/chat/",
            json={"query": "テスト質問"},
        )
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "OpenAI API key invalid" not in detail
        assert "回答生成中にエラーが発生しました" in detail

    @patch("app.api.chat.generate_rag_response", side_effect=ValueError("secret db connection string"))
    def test_sanitized_message_for_various_exceptions(self, mock_rag):
        """さまざまな例外でもサニタイズされたメッセージが返される"""
        client = _create_client()
        response = client.post(
            "/api/chat/",
            json={"query": "テスト質問"},
        )
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "secret db connection string" not in detail
        assert "しばらく経ってから再度お試しください" in detail

    def test_empty_query_returns_400(self):
        """空のクエリで400を返す"""
        client = _create_client()
        response = client.post(
            "/api/chat/",
            json={"query": "   "},
        )
        assert response.status_code in (400, 422)
