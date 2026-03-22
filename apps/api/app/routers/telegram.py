from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/api/v1", tags=["telegram"])


class TelegramLinkRequest(BaseModel):
    email: str
    telegram_chat_id: str


class TelegramTokenRequest(BaseModel):
    telegram_chat_id: str


class TelegramWebhookRequest(BaseModel):
    update_id: int | None = None

    class Config:
        extra = "allow"


@router.post("/telegram/webhook")
async def telegram_webhook(payload: TelegramWebhookRequest) -> dict:
    """Receive a Telegram update JSON and dispatch it to the bot dispatcher.

    This endpoint requires no authentication — Telegram calls it directly.
    """
    # In production this would dispatch to the python-telegram-bot Application.
    # For now we acknowledge receipt.
    return {"ok": True}


@router.post("/auth/telegram/link")
async def link_telegram(
    body: TelegramLinkRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Link a Telegram chat ID to a user account identified by email.

    No authentication required — the bot calls this on behalf of the user.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.telegram_chat_id = body.telegram_chat_id
    await db.commit()
    await db.refresh(user)

    return {"ok": True, "message": f"Linked telegram_chat_id to {body.email}"}


@router.post("/auth/telegram/token")
async def get_telegram_token(
    body: TelegramTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return a short-lived API token for a Telegram-linked user.

    The bot calls this to exchange a telegram_chat_id for a JWT access token.
    """
    result = await db.execute(
        select(User).where(User.telegram_chat_id == body.telegram_chat_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="No account linked to this Telegram chat ID",
        )

    # In production, generate a real JWT here.
    # For this scaffold we return a placeholder token.
    access_token = f"telegram-token-{user.id}"
    return {"access_token": access_token, "token_type": "bearer"}
