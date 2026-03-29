"""メール送信サービス — Resend API連携

設計意図: メンバー招待・パスワードリセットなど、
トランザクショナルメールをResend経由で送信する。
テンプレートはサービス内に集約し、呼び出し元を簡潔に保つ。
"""

import httpx

from app.core.config import settings

_RESEND_API_URL = "https://api.resend.com/emails"
_FROM_ADDRESS = "TsugiNote <noreply@tsuginote.app>"


class EmailService:
    """Resend APIを使ったメール送信"""

    def __init__(self) -> None:
        self._api_key = settings.resend_api_key

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def _send(self, to: str, subject: str, html: str) -> dict:
        """Resend APIにPOSTリクエストを送信"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                _RESEND_API_URL,
                headers=self._headers(),
                json={
                    "from": _FROM_ADDRESS,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()

    async def send_invite(
        self, to_email: str, workspace_name: str, inviter_name: str
    ) -> dict:
        """ワークスペース招待メール — メンバー追加時に送信"""
        subject = f"[TsugiNote] {inviter_name}さんから{workspace_name}への招待"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>ワークスペースへの招待</h2>
            <p>{inviter_name}さんがあなたを<strong>{workspace_name}</strong>に招待しました。</p>
            <p>以下のリンクからTsugiNoteにログインして参加してください。</p>
            <a href="https://tsuginote.app/login"
               style="display: inline-block; padding: 12px 24px;
                      background-color: #2563eb; color: white;
                      text-decoration: none; border-radius: 6px;">
                ログインして参加
            </a>
            <p style="color: #6b7280; font-size: 14px; margin-top: 24px;">
                このメールに心当たりがない場合は無視してください。
            </p>
        </div>
        """
        return await self._send(to_email, subject, html)

    async def send_password_reset(self, to_email: str, reset_token: str) -> dict:
        """パスワードリセットメール — リセット要求時に送信"""
        reset_url = f"https://tsuginote.app/reset-password?token={reset_token}"
        subject = "[TsugiNote] パスワードリセット"
        html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>パスワードリセット</h2>
            <p>パスワードリセットのリクエストを受け付けました。</p>
            <p>以下のリンクから新しいパスワードを設定してください（30分間有効）。</p>
            <a href="{reset_url}"
               style="display: inline-block; padding: 12px 24px;
                      background-color: #2563eb; color: white;
                      text-decoration: none; border-radius: 6px;">
                パスワードを再設定
            </a>
            <p style="color: #6b7280; font-size: 14px; margin-top: 24px;">
                このリクエストに心当たりがない場合は無視してください。
                パスワードは変更されません。
            </p>
        </div>
        """
        return await self._send(to_email, subject, html)


# シングルトンインスタンス
email_service = EmailService()
