"use client";

import type { OutputFormat } from "@/lib/api";

interface Props {
  value: OutputFormat;
  onChange: (format: OutputFormat) => void;
}

const OPTIONS: { value: OutputFormat; label: string }[] = [
  { value: "bullet", label: "箇条書き" },
  { value: "summary", label: "要約" },
  { value: "proposal_memo", label: "提案メモ" },
];

export default function OutputFormatToggle({ value, onChange }: Props) {
  return (
    <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
            value === opt.value
              ? "bg-white text-blue-700 shadow-sm font-medium"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
