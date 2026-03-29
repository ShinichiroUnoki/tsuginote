# TsugiNote（ツギノート）

AI属人化解消・ナレッジ管理SaaS

## 概要

TsugiNoteは、日本の中小企業が抱える最大の課題「属人化」を解決するAIナレッジ管理プラットフォームです。

散在する業務知識（担当者の頭の中、バラバラなExcel、属人的なメモ）をAIが自動で構造化・検索可能にし、誰でも・いつでも・すぐに業務を引き継げる状態を実現します。

## 主要機能

- **AI自動ドキュメント生成**: チャットログ・音声・テキストからSOP/マニュアルを自動生成
- **ナレッジQ&A**: RAGベースの社内知識検索
- **引き継ぎチェックリスト**: ロール変更・退職時の自動引き継ぎ支援
- **ナレッジギャップ検出**: ドキュメント化されていない業務の自動検出
- **日報→ナレッジ変換**: 日次報告から再利用可能なナレッジへの変換

## 技術スタック

- **Backend**: Python / FastAPI
- **Frontend**: Next.js / TypeScript
- **Database**: PostgreSQL
- **Cache**: Redis
- **AI**: Ollama（ローカルLLM / デフォルト）— OpenAI / Anthropic APIもオプション対応
- **Vector DB**: Qdrant
- **Infrastructure**: Docker / GitHub Actions

## クイックスタート

```bash
# 1. リポジトリクローン
git clone https://github.com/ShinichiroUnoki/tsuginote.git
cd tsuginote

# 2. 全サービスをローカル起動（AI含む、外部APIキー不要）
docker compose -f infra/docker/docker-compose.yml up -d

# 3. Ollamaモデルをダウンロード（初回のみ）
docker compose -f infra/docker/docker-compose.yml exec ollama ollama pull llama3.2
docker compose -f infra/docker/docker-compose.yml exec ollama ollama pull nomic-embed-text

# 4. バックエンド起動
cd src/backend && uv run fastapi dev app/main.py

# 5. フロントエンド起動
cd src/frontend && npm run dev
```

> **外部APIキーは不要です。** `docker compose up` だけでAI機能を含む全機能がローカルで動作します。
> 高品質な生成が必要な場合は `.env` で `AI_PROVIDER=openai` に切り替えてAPIキーを設定してください。

## ライセンス

MIT License
