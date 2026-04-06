"""schemas モジュールのユニットテスト"""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    CategoryType,
    ChatRequest,
    ChatResponse,
    DocumentMetadata,
    DocumentUploadResponse,
    OutputFormat,
    SourceReference,
)


class TestChatRequest:
    """ChatRequest バリデーションのテスト"""

    def test_valid_request(self):
        """正常なリクエストが作成できる"""
        req = ChatRequest(query="競合他社との比較を教えてください")
        assert req.query == "競合他社との比較を教えてください"
        assert req.output_format == OutputFormat.bullet

    def test_query_stripped_of_whitespace(self):
        """クエリの前後の空白が除去される"""
        req = ChatRequest(query="  テスト質問  ")
        assert req.query == "テスト質問"

    def test_empty_query_raises_validation_error(self):
        """空のクエリはバリデーションエラーになる"""
        with pytest.raises(ValidationError):
            ChatRequest(query="")

    def test_blank_query_raises_validation_error(self):
        """空白のみのクエリはバリデーションエラーになる"""
        with pytest.raises(ValidationError):
            ChatRequest(query="   ")

    def test_query_too_long_raises_validation_error(self):
        """2000文字超のクエリはバリデーションエラーになる"""
        long_query = "あ" * 2001
        with pytest.raises(ValidationError):
            ChatRequest(query=long_query)

    def test_query_max_length_is_accepted(self):
        """2000文字のクエリは受け付ける"""
        max_query = "あ" * 2000
        req = ChatRequest(query=max_query)
        assert len(req.query) == 2000

    def test_output_format_options(self):
        """各出力フォーマットが正常に設定できる"""
        for fmt in OutputFormat:
            req = ChatRequest(query="テスト", output_format=fmt)
            assert req.output_format == fmt

    def test_category_filter_optional(self):
        """category_filterはオプションである"""
        req = ChatRequest(query="テスト", category_filter=None)
        assert req.category_filter is None

    def test_category_filter_valid_value(self):
        """有効なcategory_filterが設定できる"""
        req = ChatRequest(query="テスト", category_filter=CategoryType.proposal)
        assert req.category_filter == CategoryType.proposal

    def test_industry_filter_optional(self):
        """industry_filterはオプションである"""
        req = ChatRequest(query="テスト", industry_filter=None)
        assert req.industry_filter is None


class TestDocumentMetadata:
    """DocumentMetadata のテスト"""

    def test_valid_metadata(self):
        """正常なメタデータが作成できる"""
        meta = DocumentMetadata(
            id="test-id",
            filename="test.pdf",
            category=CategoryType.proposal,
        )
        assert meta.id == "test-id"
        assert meta.filename == "test.pdf"
        assert meta.chunk_count == 0

    def test_default_values(self):
        """デフォルト値が正しく設定される"""
        meta = DocumentMetadata(id="id", filename="file.pdf")
        assert meta.category == CategoryType.other
        assert meta.industry_tags == []
        assert meta.uploaded_at == ""
        assert meta.chunk_count == 0


class TestOutputFormat:
    """OutputFormat Enum のテスト"""

    def test_all_formats_exist(self):
        """すべての出力フォーマットが存在する"""
        assert OutputFormat.bullet == "bullet"
        assert OutputFormat.summary == "summary"
        assert OutputFormat.proposal_memo == "proposal_memo"


class TestCategoryType:
    """CategoryType Enum のテスト"""

    def test_all_categories_exist(self):
        """すべてのカテゴリが存在する"""
        assert CategoryType.proposal == "提案書"
        assert CategoryType.case_study == "導入事例"
        assert CategoryType.product == "商品資料"
        assert CategoryType.competitor == "競合比較"
        assert CategoryType.meeting_note == "商談メモ"
        assert CategoryType.other == "その他"
