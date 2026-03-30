const API_BASE = "/api";

export type OutputFormat = "bullet" | "summary" | "proposal_memo";

export type CategoryType =
  | "提案書"
  | "導入事例"
  | "商品資料"
  | "競合比較"
  | "商談メモ"
  | "その他";

export interface SourceReference {
  document_name: string;
  category: string;
  chunk_text: string;
  relevance_score: number;
}

export interface ChatResponse {
  answer: string;
  sources: SourceReference[];
  output_format: OutputFormat;
  query: string;
}

export interface DocumentMetadata {
  id: string;
  filename: string;
  category: CategoryType;
  industry_tags: string[];
  uploaded_at: string;
  chunk_count: number;
}

export async function sendChat(
  query: string,
  outputFormat: OutputFormat,
  categoryFilter?: CategoryType,
  industryFilter?: string
): Promise<ChatResponse> {
  const body: Record<string, unknown> = {
    query,
    output_format: outputFormat,
  };
  if (categoryFilter) body.category_filter = categoryFilter;
  if (industryFilter) body.industry_filter = industryFilter;

  const res = await fetch(`${API_BASE}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "エラーが発生しました" }));
    throw new Error(err.detail || "エラーが発生しました");
  }
  return res.json();
}

export async function uploadDocument(
  file: File,
  category: CategoryType,
  industryTags: string
): Promise<{ id: string; filename: string; chunk_count: number; message: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("category", category);
  formData.append("industry_tags", industryTags);

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "アップロードエラー" }));
    throw new Error(err.detail || "アップロードエラー");
  }
  return res.json();
}

export async function getDocuments(): Promise<{
  documents: DocumentMetadata[];
  total: number;
}> {
  const res = await fetch(`${API_BASE}/documents/`);
  if (!res.ok) throw new Error("資料一覧の取得に失敗しました");
  return res.json();
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/documents/${docId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("削除に失敗しました");
}
