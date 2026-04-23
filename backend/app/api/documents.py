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

    # ファイルサイズチェック
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"ファイルサイズが上限 ({settings.max_file_size_mb}MB) を超えています",
        )

    logger.info(
        "ファイルアップロード開始: filename=%s, size=%d bytes, category=%s",
        file.filename,
        len(content),
        category.value,
    )

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

        logger.info(
            "ファイルアップロード完了: doc_id=%s, filename=%s, chunk_count=%d",
            doc_id,
            file.filename,
            chunk_count,
        )
        return DocumentUploadResponse(
            id=doc_id,
            filename=file.filename,
            chunk_count=chunk_count,
            message=f"{file.filename} を {chunk_count} チャンクで登録しました",
        )
    except HTTPException:
        raise
    except Exception as e:
        # 失敗時はファイルをクリーンアップ
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.error(
            "ファイルアップロードエラー: filename=%s, error=%s",
            file.filename,
            str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="ファイル処理中にエラーが発生しました。ファイルの形式をご確認のうえ再度お試しください。")


@router.get("/", response_model=DocumentListResponse)
async def get_documents(offset: int = 0, limit: int = 20):
    """登録済み資料一覧を取得（ページネーション対応）"""
    if limit > 100:
        limit = 100
    if offset < 0:
        offset = 0

    logger.debug("ドキュメント一覧取得リクエスト: offset=%d, limit=%d", offset, limit)
    docs, total = list_documents(offset=offset, limit=limit)
    logger.info("ドキュメント一覧取得: %d/%d 件", len(docs), total)
    return DocumentListResponse(
        documents=[DocumentMetadata(**doc) for doc in docs],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.delete("/{doc_id}")
async def remove_document(doc_id: str):
    """資料を削除"""
    logger.info("ドキュメント削除リクエスト: doc_id=%s", doc_id)
    delete_document(doc_id)
    logger.info("ドキュメント削除完了: doc_id=%s", doc_id)
    return {"message": "削除しました", "doc_id": doc_id}
