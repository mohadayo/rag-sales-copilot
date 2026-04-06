"""RAG回答生成モジュール"""

import logging

from openai import OpenAI

from app.core.config import settings
from app.db.vector_store import search
from app.models.schemas import ChatRequest, ChatResponse, OutputFormat, SourceReference

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


FORMAT_INSTRUCTIONS = {
    OutputFormat.bullet: (
        "回答は箇条書き形式で、ポイントごとに整理してください。"
        "各項目は「・」で始めてください。"
    ),
    OutputFormat.summary: (
        "回答は簡潔な要約形式で、3〜5文程度にまとめてください。"
        "全体像が把握できるようにしてください。"
    ),
    OutputFormat.proposal_memo: (
        "回答は営業提案メモの形式で出力してください。"
        "【背景】【課題】【提案ポイント】【期待効果】のセクションに分けて記載してください。"
        "営業担当がそのままコピペして使える文体にしてください。"
    ),
}

SYSTEM_PROMPT = """あなたは営業提案支援AIアシスタントです。
以下のルールに従って回答してください：

1. 提供された参考資料の情報のみに基づいて回答してください
2. 参考資料に情報がない場合は、その旨を正直に伝えてください
3. 回答は「参考情報」として提示し、断定的な表現は避けてください
4. 具体的な数値や事例名がある場合は積極的に引用してください
5. 日本語で回答してください
6. 営業担当がそのままコピペで使える実用的な文章にしてください

{format_instruction}
"""


def generate_rag_response(request: ChatRequest) -> ChatResponse:
    """RAGパイプライン: 検索 → コンテキスト構築 → LLM回答生成"""

    # 1. ベクトル検索
    logger.info("RAGパイプライン開始: query='%s...'", request.query[:50])
    results = search(
        query=request.query,
        category_filter=request.category_filter.value if request.category_filter else None,
        industry_filter=request.industry_filter,
    )

    # 2. 検索結果からコンテキストとソース情報を構築
    context_parts = []
    sources = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    logger.info("ベクトル検索完了: %d 件の参考資料を取得", len(documents))

    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        relevance_score = max(0, 1 - dist)  # cosine距離をスコアに変換
        logger.debug(
            "参考資料 %d: filename=%s, relevance_score=%.3f",
            i + 1,
            meta.get("filename", "不明"),
            relevance_score,
        )
        context_parts.append(
            f"【参考資料{i + 1}: {meta['filename']}（{meta['category']}）】\n{doc}"
        )
        sources.append(
            SourceReference(
                document_name=meta["filename"],
                category=meta["category"],
                chunk_text=doc[:200] + "..." if len(doc) > 200 else doc,
                relevance_score=round(relevance_score, 3),
            )
        )

    context = "\n\n".join(context_parts)

    if not context:
        logger.warning("関連する参考資料が見つかりませんでした: query='%s...'", request.query[:50])

    # 3. LLM回答生成
    format_instruction = FORMAT_INSTRUCTIONS[request.output_format]
    system_message = SYSTEM_PROMPT.format(format_instruction=format_instruction)

    user_message = f"""## 質問
{request.query}

## 参考資料
{context if context else "（関連する資料が見つかりませんでした）"}
"""

    logger.info("LLM回答生成開始: model=%s, output_format=%s", settings.openai_model, request.output_format.value)
    client = _get_client()
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    answer = response.choices[0].message.content or "回答を生成できませんでした。"
    logger.info(
        "LLM回答生成完了: answer_length=%d, usage=%s",
        len(answer),
        response.usage,
    )

    return ChatResponse(
        answer=answer,
        sources=sources,
        output_format=request.output_format,
        query=request.query,
    )
