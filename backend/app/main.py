"""Sales RAG Copilot - FastAPI Backend"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.core.config import settings
from app.db.vector_store import check_health as check_vector_store_health

app = FastAPI(
    title="Sales RAG Copilot API",
    description="営業提案支援AI バックエンドAPI",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/api/health")
async def health():
    vector_store = check_vector_store_health()
    overall_status = "ok" if vector_store["status"] == "ok" else "degraded"
    return {
        "status": overall_status,
        "service": "sales-rag-copilot",
        "version": app.version,
        "components": {
            "vector_store": vector_store,
        },
    }
