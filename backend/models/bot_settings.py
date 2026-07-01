"""
Модель: Настройки Telegram бота
"""
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column


class BotSettings(SQLModel, table=True):
    __tablename__ = "bot_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    webhook_url: Optional[str] = Field(default=None, max_length=500)
    admin_chat_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    bot_name: Optional[str] = Field(default=None, max_length=100)
    notify_new_orders: bool = Field(default=True)
    notify_status_change: bool = Field(default=True)
    notify_comments: bool = Field(default=True)
    notify_warranty: bool = Field(default=True)
    is_active: bool = Field(default=False)
    bot_username: Optional[str] = Field(default=None, max_length=100)
    webhook_domain: Optional[str] = Field(default=None, max_length=200)

    def __repr__(self):
        return f"<BotSettings active={self.is_active}>"
