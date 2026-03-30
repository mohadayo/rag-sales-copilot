"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import OutputFormatToggle from "@/components/OutputFormatToggle";
import FilterPanel from "@/components/FilterPanel";
import {
  sendChat,
  type OutputFormat,
  type CategoryType,
  type SourceReference,
} from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: SourceReference[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("bullet");
  const [categoryFilter, setCategoryFilter] = useState<CategoryType | "">("");
  const [industryFilter, setIndustryFilter] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const handleSend = async (query: string) => {
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setLoading(true);

    try {
      const res = await sendChat(
        query,
        outputFormat,
        categoryFilter || undefined,
        industryFilter || undefined
      );
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "エラーが発生しました";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `エラー: ${message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-lg font-bold text-gray-800">
            Sales RAG Copilot
          </h1>
          <p className="text-xs text-gray-400">営業提案支援AI</p>
        </div>
        <div className="flex items-center gap-4">
          <OutputFormatToggle
            value={outputFormat}
            onChange={setOutputFormat}
          />
          <Link
            href="/admin"
            className="text-xs bg-gray-100 hover:bg-gray-200 rounded-lg px-3 py-2 text-gray-600 transition-colors"
          >
            資料管理
          </Link>
        </div>
      </header>

      {/* Filters */}
      <div className="bg-white border-b border-gray-100 px-6 py-2 shrink-0">
        <FilterPanel
          categoryFilter={categoryFilter}
          industryFilter={industryFilter}
          onCategoryChange={setCategoryFilter}
          onIndustryChange={setIndustryFilter}
        />
      </div>

      {/* Chat area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="text-5xl mb-4">&#128269;</div>
            <p className="text-base font-medium mb-2">
              営業資料から情報を検索できます
            </p>
            <div className="text-xs space-y-1 text-center">
              <p>「製造業向けの導入事例を探したい」</p>
              <p>「競合Aとの差別化ポイントをまとめて」</p>
              <p>「初回商談前の準備メモを作りたい」</p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage
            key={i}
            role={msg.role}
            content={msg.content}
            sources={msg.sources}
          />
        ))}
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.15s]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.3s]" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4 shrink-0">
        <ChatInput onSend={handleSend} disabled={loading} />
      </div>
    </div>
  );
}
