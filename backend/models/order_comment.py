"""
Модель: Комментарий к заказу
"""

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class OrderComment(SQLModel, table=True):
    __tablename__ = "order_comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    user_id: int = Field(foreign_key="users.id")
    username: str = Field(max_length=100)
    role_name: str = Field(default="", max_length=50)
    text: str = Field(max_length=2000)
    photo_file_id: Optional[str] = Field(
        default=None, max_length=255, description="Telegram file_id для фото"
    )
    is_system: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<OrderComment #{self.id} order={self.order_id} by={self.username}>"
