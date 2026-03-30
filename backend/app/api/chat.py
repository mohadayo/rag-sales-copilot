"""チャットAPI"""

from fastapi import APIRouter, HTTPException

from app.core.rag import generate_rag_response
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """質問に対してRAG回答を生成"""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="質問を入力してください")

    try:
        response = generate_rag_response(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回答生成エラー: {str(e)}")
