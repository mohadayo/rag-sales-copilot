"""チャットAPI"""

import logging

from fastapi import APIRouter, HTTPException
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

from app.core.rag import generate_rag_response
from app.models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 2000

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """質問に対してRAG回答を生成"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="質問を入力してください")

    if len(request.query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"質問が長すぎます（最大{MAX_QUERY_LENGTH}文字）",
        )

    logger.info("チャットリクエスト受信: query_length=%d, format=%s", len(request.query), request.output_format.value)

    try:
        response = generate_rag_response(request)
        if not response.sources:
            logger.warning("検索結果が0件でした: query=%r", request.query[:80])
        return response
    except AuthenticationError:
        logger.error("OpenAI認証エラー: APIキーを確認してください")
        raise HTTPException(status_code=500, detail="AI サービスの認証に失敗しました。管理者に連絡してください。")
    except RateLimitError:
        logger.warning("OpenAI レート制限に到達しました")
        raise HTTPException(status_code=429, detail="リクエストが集中しています。しばらく待ってから再試行してください。")
    except (APITimeoutError, APIConnectionError) as e:
        logger.error("OpenAI接続エラー: %s", e)
        raise HTTPException(status_code=503, detail="AI サービスに接続できません。しばらく待ってから再試行してください。")
    except Exception as e:
        logger.exception("予期しないエラーが発生しました")
        raise HTTPException(status_code=500, detail=f"回答生成エラー: {str(e)}")
