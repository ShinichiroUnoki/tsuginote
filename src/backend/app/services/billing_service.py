"""Stripe決済サービス — Checkout・Portal・Webhook処理

設計意図: Stripe SDKの呼び出しをサービス層に集約し、
APIルーターからはビジネスロジックのみを呼び出す。
Webhook処理では署名検証を必ず行い、不正リクエストを排除する。
"""

import uuid

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.subscription import Subscription

# Stripe APIキー設定
stripe.api_key = settings.stripe_secret_key

# プランごとのStripe Price ID — 環境変数で管理すべきだが初期実装では固定
_PRICE_IDS = {
    "pro": "price_pro_monthly",
    "enterprise": "price_enterprise_monthly",
}

_SUCCESS_URL = "https://tsuginote.app/settings/billing?success=true"
_CANCEL_URL = "https://tsuginote.app/settings/billing?canceled=true"


class BillingService:
    """Stripe連携の決済サービス"""

    async def create_checkout_session(
        self, workspace_id: uuid.UUID, plan: str, customer_email: str
    ) -> str:
        """Stripe Checkoutセッションを作成し、URLを返す"""
        price_id = _PRICE_IDS.get(plan)
        if price_id is None:
            raise ValueError(f"不明なプラン: {plan}")

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer_email=customer_email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=_SUCCESS_URL,
            cancel_url=_CANCEL_URL,
            metadata={"workspace_id": str(workspace_id), "plan": plan},
        )
        return session.url or ""

    async def create_portal_session(self, stripe_customer_id: str) -> str:
        """Stripe Customer Portalセッションを作成し、URLを返す"""
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url="https://tsuginote.app/settings/billing",
        )
        return session.url or ""

    async def handle_webhook(
        self, payload: bytes, sig_header: str, db: AsyncSession
    ) -> str:
        """Stripe Webhookイベントを処理 — 署名検証必須"""
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
        event_type = event["type"]

        if event_type == "checkout.session.completed":
            await self._handle_checkout_completed(event["data"]["object"], db)
        elif event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(event["data"]["object"], db)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(event["data"]["object"], db)

        return event_type

    async def _handle_checkout_completed(
        self, session: dict, db: AsyncSession
    ) -> None:
        """Checkout完了 — Subscriptionレコードを作成/更新"""
        workspace_id = uuid.UUID(session["metadata"]["workspace_id"])
        plan = session["metadata"]["plan"]

        result = await db.execute(
            select(Subscription).where(Subscription.workspace_id == workspace_id)
        )
        sub = result.scalar_one_or_none()

        if sub is None:
            sub = Subscription(workspace_id=workspace_id)
            db.add(sub)

        sub.stripe_customer_id = session.get("customer")
        sub.stripe_subscription_id = session.get("subscription")
        sub.plan = plan
        sub.status = "active"

    async def _handle_subscription_updated(
        self, subscription: dict, db: AsyncSession
    ) -> None:
        """サブスクリプション更新 — ステータスと期間終了日を同期"""
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription["id"]
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return

        sub.status = subscription["status"]
        # current_period_endはUNIXタイムスタンプ
        from datetime import datetime, timezone

        period_end = subscription.get("current_period_end")
        if period_end:
            sub.current_period_end = datetime.fromtimestamp(
                period_end, tz=timezone.utc
            )

    async def _handle_subscription_deleted(
        self, subscription: dict, db: AsyncSession
    ) -> None:
        """サブスクリプション解約 — ステータスをcanceledに更新"""
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription["id"]
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return

        sub.status = "canceled"
        sub.plan = "free"


# シングルトンインスタンス
billing_service = BillingService()
