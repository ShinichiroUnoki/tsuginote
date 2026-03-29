"""TsugiNote FastAPIアプリケーション — エントリーポイント"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.documents import router as documents_router
from app.api.v1.ai import router as ai_router
from app.api.v1.checklists import router as checklists_router
from app.api.v1.billing import router as billing_router
from app.api.v1.dashboard import router as dashboard_router
from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダーを全レスポンスに付与"""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        response = await call_next(request)
        # XSS対策
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # HTTPS強制（本番環境用）
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        # CSP — APIサーバーなのでスクリプト不要
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'"
        )
        # リファラー制御
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # パーミッションポリシー
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        return response


# 本番環境ではAPIドキュメントを無効化
docs_url = "/api/docs" if settings.debug else None
redoc_url = "/api/redoc" if settings.debug else None

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
)

# セキュリティヘッダーミドルウェア（最初に追加 = 最後に実行）
app.add_middleware(SecurityHeadersMiddleware)

# CORS — フロントエンドからのリクエストを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ルーター登録
app.include_router(auth_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(checklists_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """ヘルスチェック — 死活監視用"""
    return {"status": "ok"}
