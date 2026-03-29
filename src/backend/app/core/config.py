"""アプリケーション設定管理 — 環境変数からPydantic Settingsで読み込む"""

import logging
import secrets

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# 本番環境で使用してはいけない危険なデフォルト値
_INSECURE_SECRETS = frozenset({
    "change-me-in-production",
    "secret",
    "password",
    "jwt-secret",
    "",
})


class Settings(BaseSettings):
    """環境変数ベースの設定。.envファイルからも読み込み可能"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # アプリケーション
    app_name: str = "TsugiNote"
    debug: bool = False

    # データベース
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tsuginote"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT — アクセストークン30分、リフレッシュトークン7日
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS — フロントエンドのオリジンを許可
    cors_origins: list[str] = ["http://localhost:3000"]

    # 外部サービス
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    resend_api_key: str = ""

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # セキュリティ: パスワードポリシー
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_digit: bool = True

    # セキュリティ: レート制限
    rate_limit_login: str = "5/minute"
    rate_limit_signup: str = "3/minute"
    rate_limit_ai_generate: str = "10/minute"

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        """本番環境でのセキュリティチェック"""
        if not self.debug and self.jwt_secret_key in _INSECURE_SECRETS:
            logger.critical(
                "JWT_SECRET_KEY が安全でないデフォルト値のままです。"
                "本番環境では必ず強力なシークレットを設定してください。"
                "開発用にランダム値を自動生成します。"
            )
            self.jwt_secret_key = secrets.token_urlsafe(64)
        if self.debug and self.jwt_secret_key in _INSECURE_SECRETS:
            logger.warning(
                "JWT_SECRET_KEY がデフォルト値です（開発環境）。"
                "本番デプロイ前に必ず変更してください。"
            )
        return self


settings = Settings()
