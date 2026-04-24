"""app/db/vector_store.py のユニットテスト"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch  # noqa: E402


class TestGetCollection:
    """get_collection 関数のテスト"""

    def setup_method(self):
        import app.db.vector_store as vs
        vs._client = None

    @patch("app.db.vector_store.chromadb")
    def test_creates_persistent_client_on_first_call(self, mock_chromadb):
        """初回呼び出しでPersistentClientが生成される"""
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        from app.db.vector_store import get_collection
        result = get_collection()

        mock_chromadb.PersistentClient.assert_called_once()
        mock_client.get_or_create_collection.assert_called_once_with(
            name="sales_documents",
            metadata={"hnsw:space": "cosine"},
        )
        assert result == mock_collection

    @patch("app.db.vector_store.chromadb")
    def test_reuses_cached_client(self, mock_chromadb):
        """2回目以降はキャッシュされたクライアントを使用する"""
        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client

        from app.db.vector_store import get_collection
        get_collection()
        get_collection()

        mock_chromadb.PersistentClient.assert_called_once()


class TestCheckHealth:
    """check_health 関数のテスト"""

    @patch("app.db.vector_store.get_collection")
    def test_healthy_returns_ok_and_count(self, mock_get_collection):
        """正常時はstatus=okとドキュメント数を返す"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 42
        mock_get_collection.return_value = mock_collection

        from app.db.vector_store import check_health
        result = check_health()

        assert result["status"] == "ok"
        assert result["document_chunks"] == 42

    @patch("app.db.vector_store.get_collection")
    def test_error_returns_error_status(self, mock_get_collection):
        """エラー時はstatus=errorを返す"""
        mock_get_collection.side_effect = Exception("接続失敗")

        from app.db.vector_store import check_health
        result = check_health()

        assert result["status"] == "error"
        assert "接続失敗" in result["detail"]


class TestAddChunks:
    """add_chunks 関数のテスト"""

    @patch("app.db.vector_store.generate_embeddings")
    @patch("app.db.vector_store.get_collection")
    def test_creates_correct_ids_and_metadatas(self, mock_get_collection, mock_embeddings):
        """チャンク追加時に正しいID・メタデータが生成される"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_embeddings.return_value = [[0.1] * 10, [0.2] * 10]

        from app.db.vector_store import add_chunks

        result = add_chunks(
            doc_id="doc-001",
            chunks=["チャンク1", "チャンク2"],
            filename="report.pdf",
            category="proposal",
            industry_tags=["manufacturing", "retail"],
            uploaded_at="2026-01-01",
        )

        assert result == 2
        mock_collection.add.assert_called_once()
        call_kwargs = mock_collection.add.call_args[1]

        assert call_kwargs["ids"] == ["doc-001_chunk_0", "doc-001_chunk_1"]
        assert call_kwargs["documents"] == ["チャンク1", "チャンク2"]
        assert call_kwargs["metadatas"][0]["doc_id"] == "doc-001"
        assert call_kwargs["metadatas"][0]["filename"] == "report.pdf"
        assert call_kwargs["metadatas"][0]["category"] == "proposal"
        assert call_kwargs["metadatas"][0]["industry_tags"] == "manufacturing,retail"
        assert call_kwargs["metadatas"][0]["chunk_index"] == 0
        assert call_kwargs["metadatas"][0]["uploaded_at"] == "2026-01-01"

    @patch("app.db.vector_store.generate_embeddings")
    @patch("app.db.vector_store.get_collection")
    def test_empty_chunks_returns_zero(self, mock_get_collection, mock_embeddings):
        """空チャンクリストの場合は0を返しコレクションに追加しない"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection

        from app.db.vector_store import add_chunks

        result = add_chunks(
            doc_id="doc-002", chunks=[], filename="empty.txt",
            category="other", industry_tags=[],
        )

        assert result == 0
        mock_collection.add.assert_not_called()
        mock_embeddings.assert_not_called()


class TestSearch:
    """search 関数のテスト"""

    @patch("app.db.vector_store.generate_embedding")
    @patch("app.db.vector_store.get_collection")
    def test_search_without_filters(self, mock_get_collection, mock_gen_embedding):
        """フィルタなしの検索が正常に動作する"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_gen_embedding.return_value = [0.1] * 10

        expected = {
            "documents": [["doc1"]],
            "metadatas": [[{"filename": "a.txt"}]],
            "distances": [[0.1]],
        }
        mock_collection.query.return_value = expected

        from app.db.vector_store import search
        results = search("テスト質問")

        assert results == expected
        call_kwargs = mock_collection.query.call_args[1]
        assert call_kwargs["query_embeddings"] == [[0.1] * 10]
        assert call_kwargs["where"] is None

    @patch("app.db.vector_store.generate_embedding")
    @patch("app.db.vector_store.get_collection")
    def test_search_with_category_filter(self, mock_get_collection, mock_gen_embedding):
        """カテゴリフィルタ付き検索が正しいwhere句を渡す"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_gen_embedding.return_value = [0.1] * 10
        mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        from app.db.vector_store import search
        search("質問", category_filter="proposal")

        call_kwargs = mock_collection.query.call_args[1]
        assert call_kwargs["where"]["category"] == "proposal"

    @patch("app.db.vector_store.generate_embedding")
    @patch("app.db.vector_store.get_collection")
    def test_search_with_industry_filter(self, mock_get_collection, mock_gen_embedding):
        """業種フィルタ付き検索が正しいwhere句を渡す"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_gen_embedding.return_value = [0.1] * 10
        mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        from app.db.vector_store import search
        search("質問", industry_filter="manufacturing")

        call_kwargs = mock_collection.query.call_args[1]
        assert call_kwargs["where"]["industry_tags"] == {"$contains": "manufacturing"}


class TestDeleteDocument:
    """delete_document 関数のテスト"""

    @patch("app.db.vector_store.get_collection")
    def test_deletes_existing_document_chunks(self, mock_get_collection):
        """既存ドキュメントのチャンクが全て削除される"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.get.return_value = {
            "ids": ["doc-001_chunk_0", "doc-001_chunk_1", "doc-001_chunk_2"],
        }

        from app.db.vector_store import delete_document
        delete_document("doc-001")

        mock_collection.get.assert_called_once_with(where={"doc_id": "doc-001"})
        mock_collection.delete.assert_called_once_with(
            ids=["doc-001_chunk_0", "doc-001_chunk_1", "doc-001_chunk_2"],
        )

    @patch("app.db.vector_store.get_collection")
    def test_nonexistent_document_skips_delete(self, mock_get_collection):
        """存在しないドキュメントの削除はdeleteを呼ばない"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.get.return_value = {"ids": []}

        from app.db.vector_store import delete_document
        delete_document("nonexistent")

        mock_collection.delete.assert_not_called()


class TestListDocuments:
    """list_documents 関数のテスト"""

    @patch("app.db.vector_store.get_collection")
    def test_groups_chunks_by_doc_id(self, mock_get_collection):
        """チャンクがdoc_idごとにグループ化される"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.get.return_value = {
            "metadatas": [
                {"doc_id": "d1", "filename": "a.txt", "category": "memo",
                 "industry_tags": "retail", "uploaded_at": "2026-01-02", "chunk_index": 0},
                {"doc_id": "d1", "filename": "a.txt", "category": "memo",
                 "industry_tags": "retail", "uploaded_at": "2026-01-02", "chunk_index": 1},
                {"doc_id": "d2", "filename": "b.pdf", "category": "proposal",
                 "industry_tags": "manufacturing", "uploaded_at": "2026-01-01", "chunk_index": 0},
            ],
        }

        from app.db.vector_store import list_documents
        docs, total = list_documents(offset=0, limit=20)

        assert total == 2
        assert len(docs) == 2
        d1 = next(d for d in docs if d["id"] == "d1")
        assert d1["chunk_count"] == 2
        assert d1["filename"] == "a.txt"

    @patch("app.db.vector_store.get_collection")
    def test_pagination(self, mock_get_collection):
        """ページネーションが正しく動作する"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.get.return_value = {
            "metadatas": [
                {"doc_id": f"d{i}", "filename": f"f{i}.txt", "category": "memo",
                 "industry_tags": "", "uploaded_at": f"2026-01-{i+1:02d}", "chunk_index": 0}
                for i in range(5)
            ],
        }

        from app.db.vector_store import list_documents
        docs, total = list_documents(offset=1, limit=2)

        assert total == 5
        assert len(docs) == 2

    @patch("app.db.vector_store.get_collection")
    def test_empty_collection(self, mock_get_collection):
        """空コレクションの場合は空リストと0を返す"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.get.return_value = {"metadatas": []}

        from app.db.vector_store import list_documents
        docs, total = list_documents()

        assert total == 0
        assert docs == []
