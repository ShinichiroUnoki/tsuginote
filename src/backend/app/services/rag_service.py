"""RAGパイプライン — Embedding生成・Qdrant格納・セマンティック検索・Q&A回答生成

設計意図: ドキュメント保存時にチャンク分割→Embedding→Qdrant格納を行い、
検索時にはQdrantで類似チャンクを取得しLLMにコンテキストとして渡す。
"""

import uuid
from dataclasses import dataclass

from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

# 設計書のEmbedding戦略に準拠
_EMBEDDING_MODEL = "text-embedding-3-small"
_EMBEDDING_DIM = 1536
_CHUNK_SIZE = 500  # トークン数（概算: 1トークン≒4文字で換算）
_CHUNK_OVERLAP = 50
_COLLECTION_NAME = "tsuginote_documents"
_CHARS_PER_TOKEN = 4  # 日本語は約2-3文字/トークンだが安全マージンを取る


@dataclass
class SearchResult:
    """ベクトル検索結果"""

    document_id: uuid.UUID
    chunk_text: str
    score: float


def chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """テキストをトークン概算でチャンク分割 — オーバーラップ付きスライディングウィンドウ"""
    char_chunk = chunk_size * _CHARS_PER_TOKEN
    char_overlap = overlap * _CHARS_PER_TOKEN

    if len(text) <= char_chunk:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + char_chunk
        chunks.append(text[start:end])
        start = end - char_overlap

    return chunks


class RAGService:
    """RAGパイプライン — Embedding生成・格納・検索・Q&A"""

    def __init__(self) -> None:
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._qdrant = AsyncQdrantClient(
            host=settings.qdrant_host, port=settings.qdrant_port
        )

    async def ensure_collection(self) -> None:
        """Qdrantコレクションが存在しなければ作成"""
        collections = await self._qdrant.get_collections()
        names = [c.name for c in collections.collections]
        if _COLLECTION_NAME not in names:
            await self._qdrant.create_collection(
                collection_name=_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=_EMBEDDING_DIM, distance=Distance.COSINE
                ),
            )

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        """OpenAI Embeddings APIでベクトル生成"""
        response = await self._openai.embeddings.create(
            model=_EMBEDDING_MODEL, input=texts
        )
        return [item.embedding for item in response.data]

    async def index_document(self, document_id: uuid.UUID, content: str) -> int:
        """ドキュメントをチャンク分割してQdrantに格納。格納チャンク数を返す"""
        await self.ensure_collection()

        # 既存のチャンクを削除（ドキュメント更新時の再インデックス対応）
        await self._qdrant.delete(
            collection_name=_COLLECTION_NAME,
            points_selector={"filter": {
                "must": [{"key": "document_id", "match": {"value": str(document_id)}}]
            }},
        )

        chunks = chunk_text(content)
        if not chunks:
            return 0

        embeddings = await self._embed(chunks)

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "document_id": str(document_id),
                    "chunk_index": i,
                    "text": chunk,
                },
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]

        await self._qdrant.upsert(collection_name=_COLLECTION_NAME, points=points)
        return len(points)

    async def search(
        self, query: str, workspace_document_ids: list[uuid.UUID], top_k: int = 5
    ) -> list[SearchResult]:
        """セマンティック検索 — ワークスペース内のドキュメントに限定"""
        await self.ensure_collection()
        query_embedding = (await self._embed([query]))[0]

        # ワークスペースのドキュメントIDでフィルタ
        doc_id_strs = [str(did) for did in workspace_document_ids]
        results = await self._qdrant.search(
            collection_name=_COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter={
                "must": [{"key": "document_id", "match": {"any": doc_id_strs}}]
            },
            limit=top_k,
        )

        return [
            SearchResult(
                document_id=uuid.UUID(hit.payload["document_id"]),
                chunk_text=hit.payload["text"],
                score=hit.score,
            )
            for hit in results
            if hit.payload
        ]

    async def generate_answer(self, question: str, context_chunks: list[str]) -> str:
        """検索結果のチャンクをコンテキストとしてLLMにQ&A回答を生成させる"""
        context = "\n\n---\n\n".join(context_chunks)
        response = await self._openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "あなたは社内ナレッジベースのアシスタントです。"
                        "以下のコンテキスト情報のみに基づいて質問に回答してください。"
                        "コンテキストに含まれない情報は「情報が見つかりませんでした」と回答してください。"
                    ),
                },
                {"role": "user", "content": f"コンテキスト:\n{context}\n\n質問: {question}"},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""

    async def delete_document(self, document_id: uuid.UUID) -> None:
        """ドキュメント削除時にQdrantからもチャンクを削除"""
        await self._qdrant.delete(
            collection_name=_COLLECTION_NAME,
            points_selector={"filter": {
                "must": [{"key": "document_id", "match": {"value": str(document_id)}}]
            }},
        )


# シングルトンインスタンス
rag_service = RAGService()
