from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    bullet = "bullet"
    summary = "summary"
    proposal_memo = "proposal_memo"


class CategoryType(str, Enum):
    proposal = "提案書"
    case_study = "導入事例"
    product = "商品資料"
    competitor = "競合比較"
    meeting_note = "商談メモ"
    other = "その他"


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    category: CategoryType = CategoryType.other
    industry_tags: list[str] = Field(default_factory=list)
    uploaded_at: str = ""
    chunk_count: int = 0


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    chunk_count: int
    message: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentMetadata]
    total: int


class ChatRequest(BaseModel):
    query: str
    output_format: OutputFormat = OutputFormat.bullet
    category_filter: CategoryType | None = None
    industry_filter: str | None = None


class SourceReference(BaseModel):
    document_name: str
    category: str
    chunk_text: str
    relevance_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    output_format: OutputFormat
    query: str
