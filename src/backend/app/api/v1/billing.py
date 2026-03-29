"""決済API — Stripe Checkout・Customer Portal・Webhook"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PortalResponse,
    SubscriptionResponse,
)

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
    """Stripe Webhook — サブスクリプション状態の同期"""
    # TODO: stripe.Webhook.construct_eventで署名検証
    # イベントタイプに応じてsubscriptionsテーブルを更新
    # - checkout.session.completed → Subscription作成/更新
    # - customer.subscription.updated → status更新
    # - customer.subscription.deleted → status=canceled
    body = await request.body()
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
