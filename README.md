# Sales RAG Copilot - 営業提案支援AI

営業資料（提案書、導入事例、商品資料、競合比較表、商談メモ等）をアップロードし、自然文で質問すると関連資料を検索して提案に使える情報を整理して返すAIアシスタントです。

## 機能

- PDF / DOCX / PPTX / TXT / Markdown の営業資料アップロード
- テキスト抽出・チャンク化・Embedding生成
- ベクトル類似度検索（ChromaDB）
- チャット形式での質問・RAG回答生成
- 参照資料一覧の表示（根拠明示）
- 出力形式切替（箇条書き / 要約 / 提案メモ風）
- カテゴリ・業界タグでの絞り込み
- 管理者向け資料管理画面

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | Next.js 15, React 19, TypeScript, Tailwind CSS |
| バックエンド | Python, FastAPI |
| ベクトルDB | ChromaDB |
| LLM / Embedding | OpenAI API (GPT-4o-mini, text-embedding-3-small) |
| コンテナ | Docker, Docker Compose |

## ディレクトリ構成

```
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py          # チャットAPI
│   │   │   └── documents.py     # 資料管理API
│   │   ├── core/
│   │   │   ├── config.py        # 設定
│   │   │   ├── chunker.py       # テキストチャンク化
│   │   │   ├── embeddings.py    # Embedding生成
│   │   │   ├── extractor.py     # テキスト抽出
│   │   │   └── rag.py           # RAG回答生成
│   │   ├── db/
│   │   │   └── vector_store.py  # ChromaDB操作
│   │   ├── models/
│   │   │   └── schemas.py       # Pydanticスキーマ
│   │   └── main.py              # FastAPIエントリポイント
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # チャット画面
│   │   │   ├── admin/page.tsx   # 管理画面
│   │   │   ├── layout.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── OutputFormatToggle.tsx
│   │   │   └── FilterPanel.tsx
│   │   └── lib/
│   │       └── api.ts           # APIクライアント
│   ├── Dockerfile
│   └── package.json
├── sample_data/                  # サンプル営業資料
├── docker-compose.yml
└── README.md
```

## ローカル起動方法

### 前提条件

- Python 3.12+
- Node.js 20+
- OpenAI API キー

### 方法1: ローカル直接起動

```bash
# 1. バックエンド
cd backend
cp .env.example .env
# .env に OPENAI_API_KEY を設定

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. フロントエンド（別ターミナル）
cd frontend
npm install
npm run dev
```

http://localhost:3000 でアクセス

### 方法2: Docker Compose

```bash
# .env にOPENAI_API_KEYを設定
echo "OPENAI_API_KEY=sk-your-key" > .env

docker compose up --build
```

### 使い方

1. http://localhost:3000/admin で営業資料をアップロード
2. http://localhost:3000 で質問を入力
3. 出力形式（箇条書き/要約/提案メモ）を切り替えて利用

`sample_data/` フォルダにサンプル資料があります。まずはこれをアップロードしてお試しください。

## API一覧

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/documents/upload` | 資料アップロード |
| GET | `/api/documents/` | 資料一覧取得 |
| DELETE | `/api/documents/{doc_id}` | 資料削除 |
| POST | `/api/chat/` | チャット（RAG回答生成） |
| GET | `/api/health` | ヘルスチェック |

## データ設計

### ChromaDB コレクション: `sales_documents`

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | string | `{doc_id}_chunk_{index}` |
| document | string | チャンクテキスト |
| embedding | float[] | 1536次元ベクトル |
| metadata.doc_id | string | ドキュメントID（UUID） |
| metadata.filename | string | ファイル名 |
| metadata.category | string | カテゴリ |
| metadata.industry_tags | string | 業界タグ（カンマ区切り） |
| metadata.chunk_index | int | チャンク番号 |

## 今後の改善案

- [ ] ユーザー認証・権限管理（NextAuth.js）
- [ ] 提案書ドラフト自動生成機能
- [ ] ストリーミング応答（SSE）
- [ ] チャット履歴の永続化
- [ ] PostgreSQL + pgvector への移行（本番向け）
- [ ] ファイルプレビュー機能
- [ ] Slack / Teams 連携
- [ ] 利用状況ダッシュボード
- [ ] マルチテナント対応
- [ ] RAG精度改善（HyDE, Re-ranking等）
