"""決済関連のPydanticスキーマ"""

from datetime import datetime

from pydantic import BaseModel, Field


class CheckoutRequest(BaseModel):
    """Stripe Checkoutセッション作成リクエスト"""

    plan: str = Field(pattern="^(pro|enterprise)$")


class CheckoutResponse(BaseModel):
    """Checkoutセッションレスポンス"""

    checkout_url: str


class PortalResponse(BaseModel):
    """Customer Portalレスポンス"""

    portal_url: str


class SubscriptionResponse(BaseModel):
    """サブスクリプション情報レスポンス"""

    plan: str
    status: str
    current_period_end: datetime | None

    model_config = {"from_attributes": True}
