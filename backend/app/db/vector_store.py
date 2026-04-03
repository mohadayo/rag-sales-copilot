"""ChromaDB ベクトルストア"""

import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.core.embeddings import generate_embedding, generate_embeddings

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None
COLLECTION_NAME = "sales_documents"


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        logger.info("ChromaDBクライアントを初期化します: persist_dir=%s", settings.chroma_persist_dir)
        _client = chromadb.Client(
            ChromaSettings(
                persist_directory=settings.chroma_persist_dir,
                anonymized_telemetry=False,
            )
        )
    return _client


def get_collection() -> chromadb.Collection:
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def check_health() -> dict:
    """ベクトルDBの接続状態を確認"""
    try:
        collection = get_collection()
        count = collection.count()
        return {"status": "ok", "document_chunks": count}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


def add_chunks(
    doc_id: str,
    chunks: list[str],
    filename: str,
    category: str,
    industry_tags: list[str],
    uploaded_at: str = "",
) -> int:
    """チャンクをベクトルDBに追加"""
    if not chunks:
        logger.warning("空のチャンクリストが渡されました: doc_id=%s", doc_id)
        return 0

    logger.info("チャンク追加開始: doc_id=%s, filename=%s, chunks=%d", doc_id, filename, len(chunks))
    collection = get_collection()
    embeddings = generate_embeddings(chunks)

    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "doc_id": doc_id,
            "filename": filename,
            "category": category,
            "industry_tags": ",".join(industry_tags),
            "chunk_index": i,
            "uploaded_at": uploaded_at,
        }
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )
    logger.info("チャンク追加完了: doc_id=%s, %d チャンク登録", doc_id, len(chunks))
    return len(chunks)


def search(
    query: str,
    top_k: int | None = None,
    category_filter: str | None = None,
    industry_filter: str | None = None,
) -> dict:
    """ベクトル類似度検索"""
    logger.info("ベクトル検索開始: query=%r, category=%s, industry=%s", query[:80], category_filter, industry_filter)
    collection = get_collection()
    query_embedding = generate_embedding(query)

    where_filters = {}
    if category_filter:
        where_filters["category"] = category_filter
    if industry_filter:
        where_filters["industry_tags"] = {"$contains": industry_filter}

    where = where_filters if where_filters else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k or settings.top_k,
        where=where if where else None,
        include=["documents", "metadatas", "distances"],
    )
    num_results = len(results.get("documents", [[]])[0])
    logger.info("ベクトル検索完了: %d 件取得", num_results)
    return results


def delete_document(doc_id: str) -> None:
    """ドキュメントの全チャンクを削除"""
    logger.info("ドキュメント削除開始: doc_id=%s", doc_id)
    collection = get_collection()
    # doc_idに一致するチャンクを検索して削除
    results = collection.get(where={"doc_id": doc_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])
        logger.info("ドキュメント削除完了: doc_id=%s, %d チャンク削除", doc_id, len(results["ids"]))
    else:
        logger.warning("削除対象のチャンクが見つかりません: doc_id=%s", doc_id)


def list_documents() -> list[dict]:
    """登録済みドキュメント一覧を取得"""
    collection = get_collection()
    all_data = collection.get(include=["metadatas"])

    doc_map: dict[str, dict] = {}
    for meta in all_data["metadatas"] or []:
        doc_id = meta["doc_id"]
        if doc_id not in doc_map:
            doc_map[doc_id] = {
                "id": doc_id,
                "filename": meta["filename"],
                "category": meta["category"],
                "industry_tags": meta.get("industry_tags", "").split(",")
                if meta.get("industry_tags")
                else [],
                "uploaded_at": meta.get("uploaded_at", ""),
                "chunk_count": 0,
            }
        doc_map[doc_id]["chunk_count"] += 1

    return list(doc_map.values())
