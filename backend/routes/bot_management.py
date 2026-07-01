"""
Маршруты управления Telegram ботом
"""
import os
from typing import Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from datetime import datetime

from core.config import get_settings
from core.database import get_session
from core.security import require_permission
from core.telegram_auth import (
    TELEGRAM_LINK_TOKEN_TTL_SECONDS,
    create_telegram_link_token,
)
from models.user import User
from models.bot_settings import BotSettings
from models.order import Order
from core.logging import logger

router = APIRouter(prefix="/api/bot", tags=["Telegram бот"])


def telegram_proxy_url() -> Optional[str]:
    return (
        os.getenv("TELEGRAM_BOT_PROXY_URL")
        or os.getenv("ALL_PROXY")
        or os.getenv("TELEGRAM_PROXY_URL")
        or os.getenv("HTTPS_PROXY")
        or os.getenv("HTTP_PROXY")
    )


def telegram_http_client():
    proxy_url = telegram_proxy_url()
    kwargs = {"timeout": 20.0}
    if proxy_url:
        kwargs["proxy"] = proxy_url
        kwargs["trust_env"] = False
    return httpx.AsyncClient(**kwargs)


def telegram_bot_token() -> str:
    token = get_settings().TELEGRAM_BOT_TOKEN
    if not token:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN не настроен на сервере")
    return token


def get_or_create_bot_settings(session: Session) -> BotSettings:
    settings = session.exec(select(BotSettings)).first()
    if not settings:
        settings = BotSettings(is_active=True)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


@router.get("/settings", summary="Настройки бота")
def get_bot_settings(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Получить настройки бота"""
    return get_or_create_bot_settings(session)


@router.patch("/settings", summary="Обновить настройки бота")
def update_bot_settings(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Обновить настройки бота"""
    settings = get_or_create_bot_settings(session)

    for key in [
        "webhook_url", "admin_chat_id", "bot_name", "bot_username", "webhook_domain",
        "notify_new_orders", "notify_status_change", "notify_comments", "notify_warranty", "is_active",
    ]:
        if key in data:
            setattr(settings, key, data[key])

    session.add(settings)
    session.commit()
    session.refresh(settings)
    logger.info("Настройки бота обновлены")
    return settings


@router.post("/webhook/set", summary="Установить webhook")
async def set_webhook(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Установить webhook для бота"""
    settings = get_or_create_bot_settings(session)
    token = telegram_bot_token()
    webhook_url = data.get("webhook_url", "")

    if not webhook_url:
        raise HTTPException(status_code=400, detail="webhook_url обязателен")

    try:
        async with telegram_http_client() as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/setWebhook",
                json={"url": webhook_url, "drop_pending_updates": True},
            )
            result = resp.json()

        if result.get("ok"):
            # Обновляем настройки
            settings.webhook_url = webhook_url
            session.add(settings)
            session.commit()
            logger.info(f"Webhook установлен: {webhook_url}")
            return {"message": "Webhook установлен", "result": result}
        else:
            raise HTTPException(status_code=400, detail=f"Telegram error: {result.get('description')}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.post("/webhook/delete", summary="Удалить webhook")
async def delete_webhook(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Удалить webhook"""
    token = telegram_bot_token()

    try:
        async with telegram_http_client() as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/deleteWebhook",
            )
            result = resp.json()

        if result.get("ok"):
            settings = session.exec(select(BotSettings)).first()
            if settings:
                settings.webhook_url = None
                session.add(settings)
                session.commit()
            logger.info("Webhook удалён")
            return {"message": "Webhook удалён", "result": result}
        else:
            raise HTTPException(status_code=400, detail=f"Telegram error: {result.get('description')}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/webhook/info", summary="Информация о webhook")
async def get_webhook_info(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Получить информацию о текущем webhook"""
    token = telegram_bot_token()

    try:
        async with telegram_http_client() as client:
            resp = await client.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
            result = resp.json()

        if result.get("ok"):
            info = result.get("result", {})
            return {
                "url": info.get("url", ""),
                "has_custom_certificate": info.get("has_custom_certificate", False),
                "pending_update_count": info.get("pending_update_count", 0),
                "last_error_date": info.get("last_error_date"),
                "last_error_message": info.get("last_error_message"),
                "max_connections": info.get("max_connections"),
                "ip_address": info.get("ip_address"),
            }
        else:
            raise HTTPException(status_code=400, detail=f"Telegram error: {result.get('description')}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/bot/info", summary="Информация о боте")
async def get_bot_info(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Получить информацию о боте"""
    token = telegram_bot_token()

    try:
        async with telegram_http_client() as client:
            resp = await client.get(f"https://api.telegram.org/bot{token}/getMe")
            result = resp.json()

        if result.get("ok"):
            bot_info = result.get("result", {})
            settings = get_or_create_bot_settings(session)
            settings.bot_username = bot_info.get("username")
            settings.bot_name = bot_info.get("first_name")
            session.add(settings)
            session.commit()
            return {
                "id": bot_info.get("id"),
                "username": bot_info.get("username"),
                "first_name": bot_info.get("first_name"),
                "can_join_groups": bot_info.get("can_join_groups"),
                "can_read_all_group_messages": bot_info.get("can_read_all_group_messages"),
                "supports_inline_queries": bot_info.get("supports_inline_queries"),
            }
        else:
            raise HTTPException(status_code=400, detail=f"Telegram error: {result.get('description')}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/stats", summary="Статистика бота")
def get_bot_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Получить статистику бота"""
    # Подключённые пользователи (с telegram_chat_id)
    connected = session.exec(
        select(func.count(func.distinct(User.id))).where(User.telegram_chat_id.isnot(None))
    ).one()

    # Всего пользователей
    total_users = session.exec(select(func.count(User.id))).one()

    # Заказы сегодня
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    orders_today = session.exec(
        select(func.count(Order.id)).where(Order.created_at >= today)
    ).one()

    # Готовые к выдаче
    ready_orders = session.exec(
        select(func.count(Order.id)).where(Order.status == "ready")
    ).one()

    return {
        "connected_users": connected,
        "total_users": total_users,
        "orders_today": orders_today,
        "ready_orders": ready_orders,
    }


@router.post("/users/{user_id}/link-token", summary="Создать код привязки Telegram")
def create_user_link_token(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("users:manage")),
):
    """Создать короткоживущий код для привязки Telegram к конкретному пользователю."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь неактивен")

    token, expires_at = create_telegram_link_token(user.id)
    command = f"/start {token}"

    settings = session.exec(select(BotSettings)).first()
    bot_username = settings.bot_username if settings and settings.bot_username else None
    deep_link = f"https://t.me/{bot_username}?start={token}" if bot_username else None

    logger.info(f"Telegram link token created for user_id={user.id} by user_id={current_user.id}")
    return {
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "expires_at": datetime.utcfromtimestamp(expires_at),
        "expires_in_seconds": TELEGRAM_LINK_TOKEN_TTL_SECONDS,
        "command": command,
        "deep_link": deep_link,
    }
