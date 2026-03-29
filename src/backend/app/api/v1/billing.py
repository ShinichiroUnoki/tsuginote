"""決済API — Stripe Checkout・Customer Portal・Webhook"""

import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.subscription import Subscription
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PortalResponse,
    SubscriptionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["決済"])


async def _get_user_owned_workspace(
    db: AsyncSession, user: User
) -> Workspace:
    """ユーザーがオーナーのワークスペースを取得"""
    result = await db.execute(
        select(Workspace).where(Workspace.owner_id == user.id).limit(1)
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="ワークスペースが見つかりません")
    return workspace


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Stripe Checkoutセッション作成"""
    workspace = await _get_user_owned_workspace(db, current_user)

    # TODO: stripe.checkout.Session.createを呼び出す
    # 現時点ではプレースホルダー
    checkout_url = f"https://checkout.stripe.com/placeholder?plan={body.plan}&ws={workspace.id}"

    return CheckoutResponse(checkout_url=checkout_url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortalResponse:
    """Stripe Customer Portalセッション作成"""
    workspace = await _get_user_owned_workspace(db, current_user)

    # サブスクリプション情報を取得
    result = await db.execute(
        select(Subscription).where(
            Subscription.workspace_id == workspace.id
        )
    )
    sub = result.scalar_one_or_none()
    if sub is None or sub.stripe_customer_id is None:
        raise HTTPException(status_code=404, detail="サブスクリプションが見つかりません")

    # TODO: stripe.billing_portal.Session.createを呼び出す
    portal_url = f"https://billing.stripe.com/placeholder?customer={sub.stripe_customer_id}"

    return PortalResponse(portal_url=portal_url)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Stripe Webhook — 署名検証必須でサブスクリプション状態を同期"""
    body = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        logger.warning("Stripe webhook: 署名ヘッダーが存在しません")
        raise HTTPException(status_code=400, detail="署名ヘッダーがありません")

    if not settings.stripe_webhook_secret:
        logger.error("Stripe webhook: webhook secretが設定されていません")
        raise HTTPException(status_code=500, detail="Webhook設定エラー")

    try:
        event = stripe.Webhook.construct_event(
            body, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        logger.warning("Stripe webhook: 不正なペイロード")
        raise HTTPException(status_code=400, detail="不正なペイロード")
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook: 署名検証失敗")
        raise HTTPException(status_code=400, detail="署名検証に失敗しました")

    event_type = event["type"]
    logger.info(f"Stripe webhook received: {event_type}")

    # イベントタイプに応じてsubscriptionsテーブルを更新
    if event_type == "checkout.session.completed":
        session_data = event["data"]["object"]
        workspace_id_str = session_data.get("metadata", {}).get("workspace_id")
        plan = session_data.get("metadata", {}).get("plan", "pro")
        if workspace_id_str:
            import uuid
            workspace_id = uuid.UUID(workspace_id_str)
            result = await db.execute(
                select(Subscription).where(Subscription.workspace_id == workspace_id)
            )
            sub = result.scalar_one_or_none()
            if sub is None:
                sub = Subscription(workspace_id=workspace_id)
                db.add(sub)
            sub.stripe_customer_id = session_data.get("customer")
            sub.stripe_subscription_id = session_data.get("subscription")
            sub.plan = plan
            sub.status = "active"

    elif event_type == "customer.subscription.updated":
        sub_data = event["data"]["object"]
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == sub_data["id"]
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = sub_data["status"]
            from datetime import datetime, timezone
            period_end = sub_data.get("current_period_end")
            if period_end:
                sub.current_period_end = datetime.fromtimestamp(
                    period_end, tz=timezone.utc
                )

    elif event_type == "customer.subscription.deleted":
        sub_data = event["data"]["object"]
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == sub_data["id"]
            )
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = "canceled"
            sub.plan = "free"

    return {"status": "received"}


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """現在のサブスクリプション情報"""
    workspace = await _get_user_owned_workspace(db, current_user)

    result = await db.execute(
        select(Subscription).where(
            Subscription.workspace_id == workspace.id
        )
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        # サブスクリプション未作成 = フリープラン
        return SubscriptionResponse(
            plan="free", status="active", current_period_end=None
        )
    return SubscriptionResponse(
        plan=sub.plan,
        status=sub.status,
        current_period_end=sub.current_period_end,
    )
