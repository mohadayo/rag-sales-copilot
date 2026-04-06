"""チャットAPI"""

import logging

from fastapi import APIRouter, HTTPException

from app.core.rag import generate_rag_response
from app.models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """質問に対してRAG回答を生成"""
    # バリデーションはスキーマ側で実施済み。APIレベルでも空文字を弾く
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="質問を入力してください")

    logger.info(
        "チャットリクエスト受信: query_length=%d, output_format=%s, category_filter=%s",
        len(request.query),
        request.output_format.value,
        request.category_filter.value if request.category_filter else "なし",
    )

    try:
        response = generate_rag_response(request)
        logger.info(
            "チャットレスポンス生成完了: sources_count=%d",
            len(response.sources),
        )
        return response
    except Exception as e:
        logger.error("チャット回答生成エラー: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"回答生成エラー: {str(e)}")
