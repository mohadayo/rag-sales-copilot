"""rag モジュールのユニットテスト"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.rag import FORMAT_INSTRUCTIONS, _get_client, generate_rag_response
from app.models.schemas import (
    CategoryType,
    ChatRequest,
    ChatResponse,
    OutputFormat,
)


def _make_mock_search_results(
    documents: list[str] | None = None,
    metadatas: list[dict] | None = None,
    distances: list[float] | None = None,
) -> dict:
    """テスト用のベクトル検索結果を生成するヘルパー"""
    if documents is None:
        documents = ["テスト資料の内容です。競合他社と比較してコストが低いです。"]
    if metadatas is None:
        metadatas = [
            {
                "filename": "test_doc.pdf",
                "category": "提案書",
            }
        ]
    if distances is None:
        distances = [0.2]
    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances],
    }


def _make_mock_openai_response(content: str = "モックLLM回答") -> MagicMock:
    """テスト用のOpenAI APIレスポンスを生成するヘルパー"""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = content
    mock_response.usage = MagicMock()
    return mock_response


class TestGenerateRagResponseWithResults:
    """検索結果が存在する場合のRAG回答生成テスト"""

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_returns_chat_response(self, mock_get_client, mock_search):
        """正常系: ChatResponseオブジェクトが返される"""
        mock_search.return_value = _make_mock_search_results()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="競合比較を教えてください")
        response = generate_rag_response(request)

        assert isinstance(response, ChatResponse)
        assert response.answer == "モックLLM回答"
        assert response.query == "競合比較を教えてください"
        assert response.output_format == OutputFormat.bullet

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_sources_constructed_correctly(self, mock_get_client, mock_search):
        """SourceReferenceが正しく構築される"""
        mock_search.return_value = _make_mock_search_results(
            documents=["詳細な提案内容です。"],
            metadatas=[{"filename": "proposal.pdf", "category": "提案書"}],
            distances=[0.1],
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="提案内容について")
        response = generate_rag_response(request)

        assert len(response.sources) == 1
        source = response.sources[0]
        assert source.document_name == "proposal.pdf"
        assert source.category == "提案書"
        assert "詳細な提案内容" in source.chunk_text

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_relevance_score_calculation(self, mock_get_client, mock_search):
        """関連度スコアが正しく計算される（1 - distance）"""
        mock_search.return_value = _make_mock_search_results(distances=[0.3])
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト質問")
        response = generate_rag_response(request)

        assert len(response.sources) == 1
        assert response.sources[0].relevance_score == pytest.approx(0.7, abs=0.001)

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_relevance_score_clamped_to_zero_for_large_distance(self, mock_get_client, mock_search):
        """距離が1以上の場合、関連度スコアは0にクランプされる"""
        mock_search.return_value = _make_mock_search_results(distances=[1.5])
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト質問")
        response = generate_rag_response(request)

        assert response.sources[0].relevance_score == 0.0

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_long_chunk_text_truncated(self, mock_get_client, mock_search):
        """200文字を超えるチャンクテキストは省略される"""
        long_text = "あ" * 300
        mock_search.return_value = _make_mock_search_results(
            documents=[long_text],
            metadatas=[{"filename": "long.pdf", "category": "商品資料"}],
            distances=[0.2],
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト質問")
        response = generate_rag_response(request)

        assert response.sources[0].chunk_text.endswith("...")
        assert len(response.sources[0].chunk_text) == 203  # 200文字 + "..."

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_short_chunk_text_not_truncated(self, mock_get_client, mock_search):
        """200文字以内のチャンクテキストは省略されない"""
        short_text = "短いテキスト"
        mock_search.return_value = _make_mock_search_results(
            documents=[short_text],
            metadatas=[{"filename": "short.pdf", "category": "商品資料"}],
            distances=[0.2],
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト質問")
        response = generate_rag_response(request)

        assert response.sources[0].chunk_text == short_text
        assert not response.sources[0].chunk_text.endswith("...")

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_multiple_sources_returned(self, mock_get_client, mock_search):
        """複数の検索結果がすべてソースに含まれる"""
        mock_search.return_value = _make_mock_search_results(
            documents=["資料1の内容", "資料2の内容", "資料3の内容"],
            metadatas=[
                {"filename": "doc1.pdf", "category": "提案書"},
                {"filename": "doc2.pdf", "category": "導入事例"},
                {"filename": "doc3.pdf", "category": "商品資料"},
            ],
            distances=[0.1, 0.2, 0.3],
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="複数資料について")
        response = generate_rag_response(request)

        assert len(response.sources) == 3
        assert response.sources[0].document_name == "doc1.pdf"
        assert response.sources[1].document_name == "doc2.pdf"
        assert response.sources[2].document_name == "doc3.pdf"


class TestGenerateRagResponseNoResults:
    """検索結果が存在しない場合のRAG回答生成テスト"""

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_empty_sources_when_no_results(self, mock_get_client, mock_search):
        """検索結果なしの場合、sourcesは空リストになる"""
        mock_search.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response(
            "関連する資料が見つかりませんでした。"
        )
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="存在しない情報について")
        response = generate_rag_response(request)

        assert len(response.sources) == 0
        assert isinstance(response, ChatResponse)

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_llm_called_even_with_no_results(self, mock_get_client, mock_search):
        """検索結果なしの場合もLLMが呼ばれる"""
        mock_search.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト質問")
        generate_rag_response(request)

        mock_client.chat.completions.create.assert_called_once()


class TestOutputFormatInstructions:
    """出力フォーマット別のプロンプト検証テスト"""

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_bullet_format_instruction_used(self, mock_get_client, mock_search):
        """bullet形式のフォーマット指示がシステムプロンプトに含まれる"""
        mock_search.return_value = _make_mock_search_results()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト", output_format=OutputFormat.bullet)
        generate_rag_response(request)

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_message = messages[0]["content"]
        assert "箇条書き" in system_message

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_summary_format_instruction_used(self, mock_get_client, mock_search):
        """summary形式のフォーマット指示がシステムプロンプトに含まれる"""
        mock_search.return_value = _make_mock_search_results()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト", output_format=OutputFormat.summary)
        generate_rag_response(request)

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_message = messages[0]["content"]
        assert "要約" in system_message

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_proposal_memo_format_instruction_used(self, mock_get_client, mock_search):
        """proposal_memo形式のフォーマット指示がシステムプロンプトに含まれる"""
        mock_search.return_value = _make_mock_search_results()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト", output_format=OutputFormat.proposal_memo)
        generate_rag_response(request)

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_message = messages[0]["content"]
        assert "提案メモ" in system_message

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_output_format_preserved_in_response(self, mock_get_client, mock_search):
        """レスポンスにリクエストと同じoutput_formatが設定される"""
        mock_search.return_value = _make_mock_search_results()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        for fmt in OutputFormat:
            request = ChatRequest(query="テスト", output_format=fmt)
            response = generate_rag_response(request)
            assert response.output_format == fmt


class TestSearchFilterPassing:
    """ベクトル検索へのフィルター引数が正しく渡されるテスト"""

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_category_filter_passed_to_search(self, mock_get_client, mock_search):
        """category_filterがsearch関数に正しく渡される"""
        mock_search.return_value = _make_mock_search_results()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト", category_filter=CategoryType.proposal)
        generate_rag_response(request)

        mock_search.assert_called_once_with(
            query="テスト",
            category_filter="提案書",
            industry_filter=None,
        )

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_no_filter_passes_none(self, mock_get_client, mock_search):
        """フィルターなしの場合、Noneがsearch関数に渡される"""
        mock_search.return_value = _make_mock_search_results()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト")
        generate_rag_response(request)

        mock_search.assert_called_once_with(
            query="テスト",
            category_filter=None,
            industry_filter=None,
        )

    @patch("app.core.rag.search")
    @patch("app.core.rag._get_client")
    def test_industry_filter_passed_to_search(self, mock_get_client, mock_search):
        """industry_filterがsearch関数に正しく渡される"""
        mock_search.return_value = _make_mock_search_results()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_openai_response()
        mock_get_client.return_value = mock_client

        request = ChatRequest(query="テスト", industry_filter="製造業")
        generate_rag_response(request)

        mock_search.assert_called_once_with(
            query="テスト",
            category_filter=None,
            industry_filter="製造業",
        )


class TestFormatInstructionsDict:
    """FORMAT_INSTRUCTIONS辞書の内容検証"""

    def test_all_formats_have_instructions(self):
        """すべての出力フォーマットに対してフォーマット指示が定義されている"""
        for fmt in OutputFormat:
            assert fmt in FORMAT_INSTRUCTIONS
            assert isinstance(FORMAT_INSTRUCTIONS[fmt], str)
            assert len(FORMAT_INSTRUCTIONS[fmt]) > 0

    def test_bullet_instruction_mentions_bullet_character(self):
        """bullet形式の指示に「・」が含まれる"""
        assert "・" in FORMAT_INSTRUCTIONS[OutputFormat.bullet]

    def test_proposal_memo_instruction_mentions_sections(self):
        """proposal_memo形式の指示に主要セクションが含まれる"""
        instruction = FORMAT_INSTRUCTIONS[OutputFormat.proposal_memo]
        assert "背景" in instruction
        assert "課題" in instruction
        assert "提案ポイント" in instruction
        assert "期待効果" in instruction


class TestOpenAIClientTimeout:
    """OpenAIクライアントのタイムアウト設定テスト"""

    @patch("app.core.rag.OpenAI")
    def test_client_created_with_timeout(self, mock_openai_cls):
        """OpenAIクライアントがタイムアウト付きで生成される"""
        import app.core.rag as rag_module
        # シングルトンをリセット
        rag_module._client = None

        _get_client()

        mock_openai_cls.assert_called_once()
        call_kwargs = mock_openai_cls.call_args.kwargs
        assert "timeout" in call_kwargs
        timeout = call_kwargs["timeout"]
        assert isinstance(timeout, httpx.Timeout)

        # リセットして後続テストに影響を与えない
        rag_module._client = None

    @patch("app.core.rag.OpenAI")
    def test_client_singleton_pattern(self, mock_openai_cls):
        """_get_clientがシングルトンパターンで動作する"""
        import app.core.rag as rag_module
        rag_module._client = None

        client1 = _get_client()
        client2 = _get_client()

        # OpenAIは1回だけ呼ばれる
        mock_openai_cls.assert_called_once()
        assert client1 is client2

        rag_module._client = None
