import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sales RAG Copilot - 営業提案支援AI",
  description: "営業資料をもとに提案に使える情報を整理して返すAIアシスタント",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <body className="bg-gray-50 text-gray-900 min-h-screen">{children}</body>
    </html>
  );
}
