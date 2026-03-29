"""AI機能関連のPydanticスキーマ"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AIGenerateRequest(BaseModel):
    """ドキュメント自動生成リクエスト"""

    prompt: str = Field(min_length=1, max_length=5000)
    category: str | None = Field(None, max_length=100)
    # 使用するモデルの指定（デフォルトはサーバー側で決定）
    model: str | None = None


class AIGenerateResponse(BaseModel):
    """AI生成結果"""

    id: uuid.UUID
    generated_content: str
    model_used: str
    tokens_used: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AISearchRequest(BaseModel):
    """セマンティック検索リクエスト"""

    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class AISearchResult(BaseModel):
    """検索結果の個別アイテム"""

    document_id: uuid.UUID
    title: str
    content_snippet: str
    score: float


class AISearchResponse(BaseModel):
    """セマンティック検索レスポンス"""

    query: str
    results: list[AISearchResult]
    results_count: int


class AIAskRequest(BaseModel):
    """Q&Aリクエスト — RAGで回答生成"""

    question: str = Field(min_length=1, max_length=2000)


class AIAskResponse(BaseModel):
    """Q&Aレスポンス"""

    answer: str
    sources: list[AISearchResult]


class AIUsageResponse(BaseModel):
    """AI利用状況"""

    total_generations: int
    total_searches: int
    total_tokens_used: int
    period: str
