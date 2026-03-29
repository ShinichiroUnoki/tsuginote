"""入力サニタイズ — プロンプトインジェクション対策

設計意図: ユーザー入力をLLMに渡す前に危険なパターンを除去し、
システムプロンプトとユーザー入力の境界を維持する。
"""

import re

# プロンプトインジェクションで使われる典型的パターン
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|above|prior)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"new\s+instructions?:", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*:", re.IGNORECASE),
    re.compile(r"<\s*/?\s*system\s*>", re.IGNORECASE),
]

# LLM出力から除去すべきパターン（不適切なシステム情報の漏洩）
_OUTPUT_FILTER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"<\s*/?\s*system\s*>", re.IGNORECASE),
    re.compile(r"my\s+system\s+prompt\s+is", re.IGNORECASE),
]


def sanitize_user_input(text: str) -> str:
    """ユーザー入力からプロンプトインジェクションパターンを除去"""
    sanitized = text
    for pattern in _INJECTION_PATTERNS:
        sanitized = pattern.sub("[FILTERED]", sanitized)
    return sanitized.strip()


def filter_llm_output(text: str) -> str:
    """LLM出力から不適切なシステム情報漏洩を除去"""
    filtered = text
    for pattern in _OUTPUT_FILTER_PATTERNS:
        filtered = pattern.sub("", filtered)
    return filtered.strip()


def truncate_for_token_limit(text: str, max_chars: int = 16000) -> str:
    """トークン上限超過対策 — 入力テキストを文字数で制限

    概算: 日本語1トークン≒2-3文字、max_tokens=4096の場合
    入力は約4000トークン（≒16000文字）に制限
    """
    if len(text) <= max_chars:
        return text
    # 末尾を切り捨てて省略記号を付加
    return text[:max_chars] + "\n\n…（入力が長すぎるため省略されました）"
