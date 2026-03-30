"use client";

import ReactMarkdown from "react-markdown";
import type { SourceReference } from "@/lib/api";

interface Props {
  role: "user" | "assistant";
  content: string;
  sources?: SourceReference[];
}

export default function ChatMessage({ role, content, sources }: Props) {
  if (role === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div className="bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-3 max-w-[75%]">
          <p className="whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-4">
      <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 max-w-[85%] shadow-sm">
        <div className="markdown-content text-sm leading-relaxed">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
        {sources && sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <p className="text-xs font-semibold text-gray-500 mb-2">
              参照資料
            </p>
            <div className="space-y-1.5">
              {sources.map((src, i) => (
                <div
                  key={i}
                  className="text-xs bg-gray-50 rounded-lg p-2 border border-gray-100"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-blue-700">
                      {src.document_name}
                    </span>
                    <span className="text-gray-400 ml-2">
                      {src.category} | 関連度{" "}
                      {Math.round(src.relevance_score * 100)}%
                    </span>
                  </div>
                  <p className="text-gray-500 line-clamp-2">{src.chunk_text}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
