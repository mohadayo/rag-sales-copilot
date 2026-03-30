"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  uploadDocument,
  getDocuments,
  deleteDocument,
  type DocumentMetadata,
  type CategoryType,
} from "@/lib/api";

const CATEGORIES: CategoryType[] = [
  "提案書",
  "導入事例",
  "商品資料",
  "競合比較",
  "商談メモ",
  "その他",
];

export default function AdminPage() {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [category, setCategory] = useState<CategoryType>("その他");
  const [industryTags, setIndustryTags] = useState("");

  const fetchDocs = useCallback(async () => {
    try {
      const data = await getDocuments();
      setDocuments(data.documents);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setMessage("");
    try {
      const res = await uploadDocument(file, category, industryTags);
      setMessage(res.message);
      fetchDocs();
    } catch (err) {
      setMessage(
        err instanceof Error ? err.message : "アップロードに失敗しました"
      );
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`「${filename}」を削除しますか？`)) return;
    try {
      await deleteDocument(docId);
      setMessage(`${filename} を削除しました`);
      fetchDocs();
    } catch {
      setMessage("削除に失敗しました");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-gray-800">資料管理</h1>
          <p className="text-xs text-gray-400">
            営業資料のアップロード・管理
          </p>
        </div>
        <Link
          href="/"
          className="text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-3 py-2 transition-colors"
        >
          チャットに戻る
        </Link>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Upload section */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="text-sm font-bold text-gray-700 mb-4">
            資料アップロード
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                カテゴリ
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as CategoryType)}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                業界タグ（カンマ区切り）
              </label>
              <input
                type="text"
                value={industryTags}
                onChange={(e) => setIndustryTags(e.target.value)}
                placeholder="例: 製造業, IT"
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                ファイル
              </label>
              <input
                type="file"
                accept=".pdf,.docx,.doc,.pptx,.txt,.md"
                onChange={handleUpload}
                disabled={uploading}
                className="w-full text-sm file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
          </div>
          {uploading && (
            <p className="text-xs text-blue-600">アップロード中...</p>
          )}
          {message && (
            <p className="text-xs text-green-600 mt-2">{message}</p>
          )}
        </div>

        {/* Document list */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-bold text-gray-700 mb-4">
            登録済み資料（{documents.length}件）
          </h2>
          {documents.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">
              資料がまだ登録されていません
            </p>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between border border-gray-100 rounded-lg px-4 py-3 hover:bg-gray-50"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">
                      {doc.filename}
                    </p>
                    <div className="flex gap-2 mt-1">
                      <span className="text-xs bg-blue-50 text-blue-700 rounded px-2 py-0.5">
                        {doc.category}
                      </span>
                      {doc.industry_tags.filter(Boolean).map((tag) => (
                        <span
                          key={tag}
                          className="text-xs bg-gray-100 text-gray-600 rounded px-2 py-0.5"
                        >
                          {tag}
                        </span>
                      ))}
                      <span className="text-xs text-gray-400">
                        {doc.chunk_count} チャンク
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(doc.id, doc.filename)}
                    className="text-xs text-red-500 hover:text-red-700 ml-4"
                  >
                    削除
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
