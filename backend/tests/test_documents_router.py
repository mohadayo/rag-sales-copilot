"""documents ルーターのユニットテスト"""

from io import BytesIO
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.documents import router, sanitize_filename


def _create_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestSanitizeFilename:
    """ファイル名サニタイズのテスト"""

    def test_normal_filename_unchanged(self):
        assert sanitize_filename("report.pdf") == "report.pdf"

    def test_japanese_filename_preserved(self):
        assert sanitize_filename("提案書_v2.docx") == "提案書_v2.docx"

    def test_path_traversal_removed(self):
        assert sanitize_filename("../../../etc/passwd.txt") == "passwd.txt"

    def test_backslash_path_replaced(self):
        result = sanitize_filename("C:\\Users\\test\\doc.pdf")
        assert "\\" not in result
        assert result.endswith(".pdf")

    def test_control_characters_replaced(self):
        result = sanitize_filename("file\x00name\x1f.txt")
        assert "\x00" not in result
        assert "\x1f" not in result

    def test_empty_after_strip_returns_unnamed(self):
        assert sanitize_filename("...") == "unnamed"

    def test_special_characters_replaced(self):
        result = sanitize_filename('file<>:"|?*.txt')
        assert "<" not in result
        assert ">" not in result


class TestUploadValidation:
    """アップロードバリデーションのテスト"""

    def test_empty_filename_returns_400(self):
        """空のファイル名で400を返す"""
        client = _create_client()
        response = client.post(
            "/api/documents/upload",
            files={"file": ("", BytesIO(b"test"), "text/plain")},
            data={"category": "その他", "industry_tags": ""},
        )
        assert response.status_code in (400, 422)

    def test_unsupported_extension_returns_400(self):
        """未対応の拡張子で400を返す"""
        client = _create_client()
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.exe", BytesIO(b"MZ"), "application/octet-stream")},
            data={"category": "その他", "industry_tags": ""},
        )
        assert response.status_code == 400
        assert "非対応" in response.json()["detail"]

    def test_file_too_large_returns_400(self):
        """ファイルサイズ超過で400を返す"""
        client = _create_client()
        large = b"x" * (50 * 1024 * 1024 + 1)
        response = client.post(
            "/api/documents/upload",
            files={"file": ("big.txt", BytesIO(large), "text/plain")},
            data={"category": "その他", "industry_tags": ""},
        )
        assert response.status_code == 400
        assert "上限" in response.json()["detail"]

    @patch("app.api.documents.add_chunks", return_value=3)
    @patch("app.api.documents.chunk_text", return_value=["chunk1", "chunk2", "chunk3"])
    @patch("app.api.documents.extract_text", return_value="テスト本文")
    def test_successful_upload(self, mock_extract, mock_chunk, mock_add):
        """正常なアップロードで200を返す"""
        client = _create_client()
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", BytesIO(b"some content"), "text/plain")},
            data={"category": "提案書", "industry_tags": "製造業,IT"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["chunk_count"] == 3
        assert "3 チャンク" in data["message"]

    @patch("app.api.documents.add_chunks", return_value=1)
    @patch("app.api.documents.chunk_text", return_value=["chunk1"])
    @patch("app.api.documents.extract_text", return_value="テスト本文")
    def test_upload_with_default_category(self, mock_extract, mock_chunk, mock_add):
        """カテゴリ未指定時にデフォルト(その他)が使われる"""
        client = _create_client()
        response = client.post(
            "/api/documents/upload",
            files={"file": ("doc.md", BytesIO(b"# Title"), "text/markdown")},
            data={"industry_tags": ""},
        )
        assert response.status_code == 200
        _, kwargs = mock_add.call_args
        assert kwargs["category"] == "その他"

    @patch("app.api.documents.extract_text", return_value="   ")
    def test_empty_text_extraction_returns_400(self, mock_extract):
        """テキスト抽出結果が空の場合に400を返す"""
        client = _create_client()
        response = client.post(
            "/api/documents/upload",
            files={"file": ("empty.txt", BytesIO(b""), "text/plain")},
            data={"category": "その他", "industry_tags": ""},
        )
        assert response.status_code == 400
        assert "テキストを抽出できませんでした" in response.json()["detail"]

    @patch("app.api.documents.extract_text", side_effect=RuntimeError("extract fail"))
    def test_processing_error_returns_500(self, mock_extract):
        """処理エラー時に500を返しファイルがクリーンアップされる"""
        client = _create_client()
        response = client.post(
            "/api/documents/upload",
            files={"file": ("fail.txt", BytesIO(b"content"), "text/plain")},
            data={"category": "その他", "industry_tags": ""},
        )
        assert response.status_code == 500
        assert "ファイル処理中にエラーが発生しました" in response.json()["detail"]

    @patch("app.api.documents.add_chunks", return_value=1)
    @patch("app.api.documents.chunk_text", return_value=["chunk1"])
    @patch("app.api.documents.extract_text", return_value="テスト本文")
    def test_upload_sanitizes_filename(self, mock_extract, mock_chunk, mock_add):
        """パストラバーサルを含むファイル名がサニタイズされる"""
        client = _create_client()
        response = client.post(
            "/api/documents/upload",
            files={"file": ("../../evil.txt", BytesIO(b"content"), "text/plain")},
            data={"category": "その他", "industry_tags": ""},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "evil.txt"
        _, kwargs = mock_add.call_args
        assert kwargs["filename"] == "evil.txt"

    @patch("app.api.documents.extract_text", side_effect=RuntimeError("secret internal error info"))
    def test_error_detail_not_leaked(self, mock_extract):
        """内部エラー詳細がレスポンスに含まれないことを検証"""
        client = _create_client()
        response = client.post(
            "/api/documents/upload",
            files={"file": ("fail.txt", BytesIO(b"content"), "text/plain")},
            data={"category": "その他", "industry_tags": ""},
        )
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "secret internal error info" not in detail
        assert "ファイルの形式をご確認のうえ再度お試しください" in detail


class TestListDocuments:
    """ドキュメント一覧取得のテスト"""

    @patch("app.api.documents.list_documents")
    def test_list_documents_empty(self, mock_list):
        """ドキュメントなしの場合に空リストを返す"""
        mock_list.return_value = ([], 0)
        client = _create_client()
        response = client.get("/api/documents/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["documents"] == []
        assert data["offset"] == 0
        assert data["limit"] == 20

    @patch("app.api.documents.list_documents")
    def test_list_documents_with_data(self, mock_list):
        """ドキュメントが存在する場合にリストを返す"""
        mock_list.return_value = (
            [
                {
                    "id": "uuid-1",
                    "filename": "proposal.pdf",
                    "category": "提案書",
                    "industry_tags": ["製造業"],
                    "uploaded_at": "2026-01-01T00:00:00",
                    "chunk_count": 5,
                },
            ],
            1,
        )
        client = _create_client()
        response = client.get("/api/documents/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["documents"][0]["filename"] == "proposal.pdf"

    @patch("app.api.documents.list_documents")
    def test_list_documents_with_pagination(self, mock_list):
        """offset/limitパラメータが正しく渡される"""
        mock_list.return_value = ([], 10)
        client = _create_client()
        response = client.get("/api/documents/?offset=5&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 5
        assert data["limit"] == 3
        assert data["total"] == 10
        mock_list.assert_called_once_with(offset=5, limit=3)

    @patch("app.api.documents.list_documents")
    def test_list_documents_limit_capped(self, mock_list):
        """limitの上限は100"""
        mock_list.return_value = ([], 0)
        client = _create_client()
        response = client.get("/api/documents/?limit=200")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 100

    @patch("app.api.documents.list_documents")
    def test_list_documents_negative_offset(self, mock_list):
        """負のoffsetは0にクランプされる"""
        mock_list.return_value = ([], 0)
        client = _create_client()
        response = client.get("/api/documents/?offset=-5")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 0


class TestDeleteDocument:
    """ドキュメント削除のテスト"""

    @patch("app.api.documents.delete_document")
    def test_delete_document_success(self, mock_delete):
        """正常削除で成功メッセージを返す"""
        client = _create_client()
        response = client.delete("/api/documents/uuid-1")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "削除しました"
        assert data["doc_id"] == "uuid-1"
        mock_delete.assert_called_once_with("uuid-1")
