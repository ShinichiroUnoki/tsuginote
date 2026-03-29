"""LLM Gateway — ローカルLLMファースト（Ollama）+ 外部APIフォールバック

設計意図: Ollamaをプライマリプロバイダーとし、外部APIキーなしで
docker compose upだけで全AI機能が動作する構成にする。
OpenAI/Anthropicはオプショナルフォールバックとして残す。
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ドキュメント生成用のシステムプロンプト
_DOC_SYSTEM_PROMPT = """あなたは業務引き継ぎドキュメントの専門家です。
以下の原則に従って、明確で実用的なドキュメントを生成してください:

1. 構造化: 見出し・箇条書き・番号付きリストを活用
2. 具体性: 曖昧な表現を避け、具体的な手順・数値を記載
3. 再現性: 読み手が初見でも作業を再現できる詳細さ
4. 簡潔性: 冗長な説明を避け、要点を絞る

出力はMarkdown形式で記述してください。"""

# Q&A回答生成用のシステムプロンプト
_QA_SYSTEM_PROMPT = (
    "あなたは社内ナレッジベースのアシスタントです。"
    "以下のコンテキスト情報のみに基づいて質問に回答してください。"
    "コンテキストに含まれない情報は「情報が見つかりませんでした」と回答してください。"
)


@dataclass
class GenerationResult:
    """LLM生成結果のデータクラス"""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMProvider(ABC):
    """LLMプロバイダーの抽象基底クラス"""

    @abstractmethod
    async def generate(
        self, prompt: str, system: str, model: str | None = None
    ) -> GenerationResult:
        ...


class OllamaProvider(LLMProvider):
    """Ollama REST APIプロバイダー — ローカルLLMで外部依存なし"""

    def __init__(self) -> None:
        self._base_url = settings.ollama_base_url
        self._default_model = settings.ollama_model

    async def generate(
        self, prompt: str, system: str, model: str | None = None
    ) -> GenerationResult:
        target_model = model or self._default_model
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": target_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.7},
                },
            )
            resp.raise_for_status()
            data = resp.json()
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        return GenerationResult(
            content=data.get("message", {}).get("content", ""),
            model=target_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )


class OpenAIProvider(LLMProvider):
    """OpenAI APIプロバイダー — オプショナルフォールバック"""

    def __init__(self) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._default_model = "gpt-4o-mini"

    async def generate(
        self, prompt: str, system: str, model: str | None = None
    ) -> GenerationResult:
        target_model = model or self._default_model
        resp = await self._client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7, max_tokens=4096,
        )
        usage = resp.usage
        return GenerationResult(
            content=resp.choices[0].message.content or "",
            model=target_model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )


class AnthropicProvider(LLMProvider):
    """Anthropic APIプロバイダー — オプショナルフォールバック"""

    def __init__(self) -> None:
        from anthropic import AsyncAnthropic
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._default_model = "claude-sonnet-4-20250514"

    async def generate(
        self, prompt: str, system: str, model: str | None = None
    ) -> GenerationResult:
        target_model = model or self._default_model
        resp = await self._client.messages.create(
            model=target_model, max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        content = resp.content[0].text if resp.content else ""
        usage = resp.usage
        return GenerationResult(
            content=content, model=target_model,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            total_tokens=usage.input_tokens + usage.output_tokens,
        )


class AIService:
    """AI生成サービス — Ollama優先、外部APIはオプショナルフォールバック"""

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}
        self._providers["ollama"] = OllamaProvider()
        if settings.openai_api_key:
            self._providers["openai"] = OpenAIProvider()
        if settings.anthropic_api_key:
            self._providers["anthropic"] = AnthropicProvider()

    async def _call(
        self, prompt: str, system: str, model: str | None = None
    ) -> GenerationResult:
        """プロバイダー優先順で呼び出し、失敗時にフォールバック"""
        preferred = settings.ai_provider
        ordered = [preferred] + [k for k in self._providers if k != preferred]
        errors: list[Exception] = []
        for name in ordered:
            provider = self._providers.get(name)
            if provider is None:
                continue
            try:
                return await provider.generate(prompt, system, model)
            except Exception as e:
                logger.warning("LLMプロバイダー[%s]でエラー: %s", name, e)
                errors.append(e)
        if errors:
            raise RuntimeError(f"全LLMプロバイダーでエラー: {[str(e) for e in errors]}")
        raise RuntimeError("利用可能なLLMプロバイダーがありません。Ollamaが起動しているか確認してください。")

    async def generate_document(self, prompt: str, model: str | None = None) -> GenerationResult:
        """ドキュメント生成"""
        return await self._call(prompt, _DOC_SYSTEM_PROMPT, model)

    async def generate_answer(self, question: str, context_chunks: list[str]) -> str:
        """RAG Q&A回答生成 — 検索チャンクをコンテキストとしてLLMに送信"""
        context = "\n\n---\n\n".join(context_chunks)
        prompt = f"コンテキスト:\n{context}\n\n質問: {question}"
        result = await self._call(prompt, _QA_SYSTEM_PROMPT)
        return result.content


# シングルトンインスタンス
ai_service = AIService()
