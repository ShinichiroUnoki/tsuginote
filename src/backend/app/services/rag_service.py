"""RAGパイプライン — ローカルLLMファースト（Ollama Embedding）

設計意図: OllamaのEmbedding API（nomic-embed-text）をプライマリとし、
外部APIキーなしでセマンティック検索が動作する構成にする。
Q&A回答生成はai_serviceに委譲（LLMプロバイダー統一管理）。
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50
_COLLECTION_NAME = "tsuginote_documents"
_CHARS_PER_TOKEN = 4


@dataclass
class SearchResult:
    """ベクトル検索結果"""
    document_id: uuid.UUID
    chunk_text: str
    score: float


def chunk_text(
    text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP
) -> list[str]:
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


class EmbeddingProvider(ABC):
    """Embeddingプロバイダーの抽象基底クラス"""
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama /api/embed エンドポイントでローカルEmbedding生成"""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/embed",
                json={"model": settings.ollama_embed_model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
        return data["embeddings"]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI Embeddings API — オプショナルフォールバック"""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(
            model="text-embedding-3-small", input=texts
        )
        return [item.embedding for item in response.data]


class RAGService:
    """RAGパイプライン — Embedding生成・格納・検索・Q&A"""

    def __init__(self) -> None:
        self._qdrant = AsyncQdrantClient(
            host=settings.qdrant_host, port=settings.qdrant_port
        )
        # Embeddingプロバイダーを設定に基づいて選択
        self._embedder = self._build_embedder()
        self._embedding_dim = settings.embedding_dim

    def _build_embedder(self) -> EmbeddingProvider:
        """設定に基づいてEmbeddingプロバイダーを構築"""
        if settings.embedding_provider == "openai" and settings.openai_api_key:
            return OpenAIEmbeddingProvider()
        # デフォルト: Ollama（外部APIキー不要）
        return OllamaEmbeddingProvider()

    async def ensure_collection(self) -> None:
        """Qdrantコレクションが存在しなければ作成"""
        collections = await self._qdrant.get_collections()
        names = [c.name for c in collections.collections]
        if _COLLECTION_NAME not in names:
            await self._qdrant.create_collection(
                collection_name=_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self._embedding_dim, distance=Distance.COSINE
                ),
            )

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        """設定されたプロバイダーでEmbedding生成、失敗時フォールバック"""
        try:
            return await self._embedder.embed(texts)
        except Exception as e:
            # Ollamaプライマリ → OpenAIフォールバック
            if isinstance(self._embedder, OllamaEmbeddingProvider) and settings.openai_api_key:
                logger.warning("Ollama Embedding失敗、OpenAIにフォールバック: %s", e)
                return await OpenAIEmbeddingProvider().embed(texts)
            raise

    async def index_document(self, document_id: uuid.UUID, content: str) -> int:
        """ドキュメントをチャンク分割してQdrantに格納"""
        await self.ensure_collection()
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
                id=str(uuid.uuid4()), vector=emb,
                payload={"document_id": str(document_id), "chunk_index": i, "text": chunk},
            )
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        await self._qdrant.upsert(collection_name=_COLLECTION_NAME, points=points)
        return len(points)

    async def search(
        self, query: str, workspace_document_ids: list[uuid.UUID], top_k: int = 5
    ) -> list[SearchResult]:
        """セマンティック検索 — ワークスペース内のドキュメントに限定"""
        await self.ensure_collection()
        query_embedding = (await self._embed([query]))[0]
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
            for hit in results if hit.payload
        ]

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
