"use client";

import type { CategoryType } from "@/lib/api";

interface Props {
  categoryFilter: CategoryType | "";
  industryFilter: string;
  onCategoryChange: (category: CategoryType | "") => void;
  onIndustryChange: (industry: string) => void;
}

const CATEGORIES: { value: CategoryType | ""; label: string }[] = [
  { value: "", label: "すべて" },
  { value: "提案書", label: "提案書" },
  { value: "導入事例", label: "導入事例" },
  { value: "商品資料", label: "商品資料" },
  { value: "競合比較", label: "競合比較" },
  { value: "商談メモ", label: "商談メモ" },
  { value: "その他", label: "その他" },
];

export default function FilterPanel({
  categoryFilter,
  industryFilter,
  onCategoryChange,
  onIndustryChange,
}: Props) {
  return (
    <div className="flex flex-wrap gap-3 items-center">
      <div className="flex items-center gap-2">
        <label className="text-xs text-gray-500 font-medium">カテゴリ</label>
        <select
          value={categoryFilter}
          onChange={(e) => onCategoryChange(e.target.value as CategoryType | "")}
          className="text-xs border border-gray-300 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <label className="text-xs text-gray-500 font-medium">業界タグ</label>
        <input
          type="text"
          value={industryFilter}
          onChange={(e) => onIndustryChange(e.target.value)}
          placeholder="例: 製造業"
          className="text-xs border border-gray-300 rounded-lg px-2 py-1.5 w-28 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </div>
  );
}
