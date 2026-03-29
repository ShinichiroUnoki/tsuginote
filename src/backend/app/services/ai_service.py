"""LLM Gateway — マルチプロバイダー対応のAIドキュメント生成サービス

設計意図: プロバイダーを抽象化し、OpenAI/Anthropicを切り替え可能にする。
現時点ではOpenAI gpt-4o-miniをデフォルトとし、将来的にAnthropicを追加。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.core.config import settings

# 日本語SOP生成用のシステムプロンプト
_SYSTEM_PROMPT = """あなたは業務引き継ぎドキュメントの専門家です。
以下の原則に従って、明確で実用的なドキュメントを生成してください:

1. 構造化: 見出し・箇条書き・番号付きリストを活用
2. 具体性: 曖昧な表現を避け、具体的な手順・数値を記載
3. 再現性: 読み手が初見でも作業を再現できる詳細さ
4. 簡潔性: 冗長な説明を避け、要点を絞る

出力はMarkdown形式で記述してください。"""


@dataclass
class GenerationResult:
    """LLM生成結果のデータクラス"""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMProvider(ABC):
    """LLMプロバイダーの抽象基底クラス — 将来のマルチプロバイダー対応"""

    @abstractmethod
    async def generate(self, prompt: str, model: str | None = None) -> GenerationResult:
        ...


class OpenAIProvider(LLMProvider):
    """OpenAI APIプロバイダー"""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._default_model = "gpt-4o-mini"

    async def generate(self, prompt: str, model: str | None = None) -> GenerationResult:
        """OpenAI Chat Completions APIでドキュメント生成"""
        target_model = model or self._default_model
        response = await self._client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        choice = response.choices[0]
        usage = response.usage

        return GenerationResult(
            content=choice.message.content or "",
            model=target_model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )


class AnthropicProvider(LLMProvider):
    """Anthropic APIプロバイダー — 将来の拡張用"""

    def __init__(self) -> None:
        # Anthropic SDKのインポートは使用時にのみ行う
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._default_model = "claude-sonnet-4-20250514"

    async def generate(self, prompt: str, model: str | None = None) -> GenerationResult:
        """Anthropic Messages APIでドキュメント生成"""
        target_model = model or self._default_model
        response = await self._client.messages.create(
            model=target_model,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text if response.content else ""
        usage = response.usage

        return GenerationResult(
            content=content,
            model=target_model,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            total_tokens=usage.input_tokens + usage.output_tokens,
        )


class AIService:
    """AI生成サービス — プロバイダー選択とフォールバックを管理"""

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}
        # APIキーが設定されているプロバイダーのみ有効化
        if settings.openai_api_key:
            self._providers["openai"] = OpenAIProvider()
        if settings.anthropic_api_key:
            self._providers["anthropic"] = AnthropicProvider()

    async def generate_document(
        self, prompt: str, model: str | None = None
    ) -> GenerationResult:
        """ドキュメント生成 — OpenAI優先、失敗時にAnthropicフォールバック"""
        errors: list[Exception] = []

        for name, provider in self._providers.items():
            try:
                return await provider.generate(prompt, model)
            except Exception as e:
                errors.append(e)
                continue

        if errors:
            raise RuntimeError(
                f"全LLMプロバイダーでエラー: {[str(e) for e in errors]}"
            )
        raise RuntimeError("利用可能なLLMプロバイダーがありません。APIキーを設定してください。")


# シングルトンインスタンス
ai_service = AIService()
