"""アプリケーション設定管理 — 環境変数からPydantic Settingsで読み込む"""

from pydantic_settings import BaseSettings, SettingsConfigDict


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


settings = Settings()
