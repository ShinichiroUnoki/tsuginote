"""認証API — サインアップ・ログイン・トークン更新・プロフィール管理"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.auth import (
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["認証"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserCreate, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """新規ユーザー登録 — 同時にデフォルトワークスペースも作成"""
    # メール重複チェック — ユーザー列挙攻撃を防ぐため汎用メッセージを使用
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="アカウントの作成に失敗しました。別のメールアドレスをお試しください",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
    )
    db.add(user)
    await db.flush()

    # デフォルトワークスペースを自動作成
    workspace = Workspace(
        name=f"{body.name}のワークスペース",
        owner_id=user.id,
    )
    db.add(workspace)
    await db.flush()

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role="owner",
    )
    db.add(member)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """ログイン — メール+パスワードでJWTを発行"""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None:
        # タイミング攻撃対策: ユーザーが存在しなくてもハッシュ比較を実行
        verify_password(body.password, "$2b$12$dummy.hash.for.timing.attack.preventionstub")
        logger.warning(f"ログイン失敗: 存在しないメール (email={body.email})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )

    if not verify_password(body.password, user.password_hash):
        logger.warning(f"ログイン失敗: パスワード不一致 (user_id={user.id})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )

    logger.info(f"ログイン成功 (user_id={user.id})")
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    _current_user: User = Depends(get_current_user),
) -> None:
    """ログアウト — ステートレスJWTのためサーバー側は何もしない
    クライアント側でトークンを破棄する想定"""
    return None


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """リフレッシュトークンで新しいトークンペアを発行"""
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なリフレッシュトークンです",
        )

    user_id = payload.get("sub")
    try:
        parsed_user_id = uuid.UUID(user_id) if user_id else None
    except (ValueError, AttributeError):
        parsed_user_id = None
    if parsed_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なリフレッシュトークンです",
        )

    result = await db.execute(select(User).where(User.id == parsed_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません",
        )

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """現在のユーザー情報を取得"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """プロフィール更新 — 送信されたフィールドのみ更新"""
    if body.name is not None:
        current_user.name = body.name
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url
    db.add(current_user)
    return current_user
