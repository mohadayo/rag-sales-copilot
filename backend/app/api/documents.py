"""資料管理API"""

import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.chunker import chunk_text
from app.core.config import settings
from app.core.extractor import extract_text
from app.db.vector_store import add_chunks, delete_document, list_documents
from app.models.schemas import (
    CategoryType,
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".txt", ".md"}
MAX_FILE_SIZE = settings.max_file_size


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: CategoryType = Form(CategoryType.other),
    industry_tags: str = Form(""),
):
    """資料をアップロードしてベクトルDBに登録"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名が必要です")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"非対応のファイル形式です。対応形式: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # ファイル保存
    doc_id = str(uuid.uuid4())
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, f"{doc_id}{ext}")

    content = await file.read()

    # ファイルサイズバリデーション
    if len(content) > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"ファイルサイズが上限を超えています（最大 {max_mb:.0f}MB）",
        )

    logger.info("ファイルアップロード: filename=%s, size=%d bytes, category=%s", file.filename, len(content), category.value)

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        # テキスト抽出
        text = extract_text(file_path)
        if not text.strip():
            raise HTTPException(status_code=400, detail="テキストを抽出できませんでした")

        # チャンク化
        chunks = chunk_text(text)

        # タグ解析
        tags = [t.strip() for t in industry_tags.split(",") if t.strip()]

        # アップロード日時を記録
        uploaded_at = datetime.now(timezone.utc).isoformat()

        # ベクトルDBに登録
        chunk_count = add_chunks(
            doc_id=doc_id,
            chunks=chunks,
            filename=file.filename,
            category=category.value,
            industry_tags=tags,
            uploaded_at=uploaded_at,
        )

        logger.info("ドキュメント登録完了: doc_id=%s, filename=%s, chunks=%d", doc_id, file.filename, chunk_count)

        return DocumentUploadResponse(
            id=doc_id,
            filename=file.filename,
            chunk_count=chunk_count,
            message=f"{file.filename} を {chunk_count} チャンクで登録しました",
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning("テキスト抽出エラー: %s", e)
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"ファイル処理エラー: {str(e)}")
    except Exception as e:
        # 失敗時はファイルをクリーンアップ
        logger.exception("ドキュメント処理中に予期しないエラーが発生: filename=%s", file.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"処理エラー: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def get_documents():
    """登録済み資料一覧を取得"""
    docs = list_documents()
    return DocumentListResponse(
        documents=[DocumentMetadata(**doc) for doc in docs],
        total=len(docs),
    )


@router.delete("/{doc_id}")
async def remove_document(doc_id: str):
    """資料を削除"""
    logger.info("ドキュメント削除リクエスト: doc_id=%s", doc_id)
    try:
        delete_document(doc_id)
        return {"message": "削除しました", "doc_id": doc_id}
    except Exception as e:
        logger.exception("ドキュメント削除エラー: doc_id=%s", doc_id)
        raise HTTPException(status_code=500, detail=f"削除エラー: {str(e)}")
